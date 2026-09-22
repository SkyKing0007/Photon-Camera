#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/bitmap.h>
#include <android/log.h>

#include "SpektraRenderer.h"
#include "SpektraParameters.h"
#include "SpektraProfileDataBridge.h"
#include "SpektraEmbeddedShaders.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <sys/stat.h>
#include <errno.h>

#define LOG_TAG "IrisSpektraNative"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

namespace {
std::mutex gRendererMutex;
std::unique_ptr<spektrafilm::Renderer> gRenderer;
std::string gLastError;
std::string gResourceRoot;

std::string jstringToString(JNIEnv *env, jstring value) {
    if (!value) return {};
    const char *chars = env->GetStringUTFChars(value, nullptr);
    std::string out = chars ? chars : "";
    if (chars) env->ReleaseStringUTFChars(value, chars);
    return out;
}

bool mkdirOne(const std::string &path) {
    return ::mkdir(path.c_str(), 0700) == 0 || errno == EEXIST;
}

bool copyAsset(AAssetManager *manager, const char *assetName, const std::string &dst, std::string *error) {
    AAsset *asset = AAssetManager_open(manager, assetName, AASSET_MODE_STREAMING);
    if (!asset) {
        if (error) *error = std::string("Missing Spektra asset ") + assetName;
        return false;
    }
    FILE *f = std::fopen(dst.c_str(), "wb");
    if (!f) {
        AAsset_close(asset);
        if (error) *error = std::string("Unable to create ") + dst;
        return false;
    }
    std::vector<uint8_t> buffer(64u * 1024u);
    bool ok = true;
    for (;;) {
        const int n = AAsset_read(asset, buffer.data(), buffer.size());
        if (n < 0) { ok = false; break; }
        if (n == 0) break;
        if (std::fwrite(buffer.data(), 1, static_cast<size_t>(n), f) != static_cast<size_t>(n)) {
            ok = false; break;
        }
    }
    const int closeResult = std::fclose(f);
    AAsset_close(asset);
    if (!ok || closeResult != 0) {
        if (error) *error = std::string("Unable to materialize ") + assetName;
        return false;
    }
    return true;
}

float halfToFloat(uint16_t h) {
    const uint32_t sign = static_cast<uint32_t>(h & 0x8000u) << 16u;
    const uint32_t exponent = (h >> 10u) & 0x1fu;
    uint32_t mantissa = h & 0x03ffu;
    uint32_t bits;
    if (exponent == 0u) {
        if (mantissa == 0u) {
            bits = sign;
        } else {
            int e = -14;
            while ((mantissa & 0x0400u) == 0u) { mantissa <<= 1u; --e; }
            mantissa &= 0x03ffu;
            bits = sign | (static_cast<uint32_t>(e + 127) << 23u) | (mantissa << 13u);
        }
    } else if (exponent == 31u) {
        bits = sign | 0x7f800000u | (mantissa << 13u);
    } else {
        bits = sign | ((exponent + (127u - 15u)) << 23u) | (mantissa << 13u);
    }
    float f;
    std::memcpy(&f, &bits, sizeof(f));
    return f;
}

uint8_t toByte(uint16_t h) {
    float v = halfToFloat(h);
    if (!std::isfinite(v)) v = 0.0f;
    v = std::max(0.0f, std::min(1.0f, v));
    return static_cast<uint8_t>(std::floor(v * 255.0f + 0.5f));
}

uint16_t floatToHalf(float value) {
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    const uint32_t sign = (bits >> 16u) & 0x8000u;
    int32_t exp = static_cast<int32_t>((bits >> 23u) & 0xffu) - 127 + 15;
    uint32_t mantissa = bits & 0x7fffffu;
    if (exp <= 0) {
        if (exp < -10) return static_cast<uint16_t>(sign);
        mantissa = (mantissa | 0x800000u) >> static_cast<uint32_t>(1 - exp);
        return static_cast<uint16_t>(sign | ((mantissa + 0x1000u) >> 13u));
    }
    if (exp >= 31) return static_cast<uint16_t>(sign | 0x7c00u);
    return static_cast<uint16_t>(sign | (static_cast<uint32_t>(exp) << 10u)
            | ((mantissa + 0x1000u) >> 13u));
}

constexpr int kAndroidRawSensor = 32;
constexpr int kAndroidRaw10 = 37;
constexpr int kAndroidRaw12 = 38;

bool throwIllegalArgument(JNIEnv *env, const std::string &message) {
    jclass cls = env->FindClass("java/lang/IllegalArgumentException");
    if (cls) env->ThrowNew(cls, message.c_str());
    return false;
}

int minRawRowBytes(int format, int width, int pixelStride) {
    if (format == kAndroidRaw10) return ((width + 3) / 4) * 5;
    if (format == kAndroidRaw12) return ((width + 1) / 2) * 3;
    if (format == kAndroidRawSensor) return width * std::max(2, pixelStride);
    return -1;
}

bool readRawSample(const uint8_t *src, size_t sourceBytes, int format, int width, int height,
                   int rowStride, int pixelStride, int x, int y, uint16_t *sample) {
    if (!src || !sample || x < 0 || y < 0 || x >= width || y >= height) return false;
    const size_t row = static_cast<size_t>(y) * static_cast<size_t>(rowStride);
    size_t p = 0;
    if (format == kAndroidRaw10) {
        p = row + static_cast<size_t>(x / 4) * 5u;
        if (p + 4u >= sourceBytes) return false;
        const int lane = x & 3;
        const uint8_t packed = src[p + 4u];
        *sample = static_cast<uint16_t>((static_cast<uint16_t>(src[p + static_cast<size_t>(lane)]) << 2u)
                | ((packed >> (lane * 2)) & 0x03u));
        return true;
    }
    if (format == kAndroidRaw12) {
        p = row + static_cast<size_t>(x / 2) * 3u;
        if (p + 2u >= sourceBytes) return false;
        const int lane = x & 1;
        const uint8_t packed = src[p + 2u];
        *sample = static_cast<uint16_t>((static_cast<uint16_t>(src[p + static_cast<size_t>(lane)]) << 4u)
                | (lane == 0 ? (packed & 0x0fu) : ((packed >> 4u) & 0x0fu)));
        return true;
    }
    if (format == kAndroidRawSensor) {
        const int stride = std::max(2, pixelStride);
        p = row + static_cast<size_t>(x) * static_cast<size_t>(stride);
        if (p + 1u >= sourceBytes) return false;
        *sample = static_cast<uint16_t>(static_cast<uint16_t>(src[p])
                | (static_cast<uint16_t>(src[p + 1u]) << 8u));
        return true;
    }
    return false;
}

int alignedParity(int v, int parity, int lo, int hi) {
    v = std::max(lo, std::min(hi, v));
    if ((v & 1) == parity) return v;
    if (v + 1 <= hi) return v + 1;
    if (v - 1 >= lo) return v - 1;
    return v;
}

bool averageRawPhaseBox(const uint8_t *src, size_t sourceBytes, int format,
                        int sourceWidth, int sourceHeight, int rowStride, int pixelStride,
                        int outputX, int outputY, int outputWidth, int outputHeight,
                        uint16_t *sample) {
    if (!sample || outputWidth <= 0 || outputHeight <= 0) return false;
    int x0 = static_cast<int>((static_cast<int64_t>(outputX) * sourceWidth) / outputWidth);
    int x1 = static_cast<int>((static_cast<int64_t>(outputX + 1) * sourceWidth) / outputWidth) - 1;
    int y0 = static_cast<int>((static_cast<int64_t>(outputY) * sourceHeight) / outputHeight);
    int y1 = static_cast<int>((static_cast<int64_t>(outputY + 1) * sourceHeight) / outputHeight) - 1;
    x0 = std::max(0, std::min(sourceWidth - 1, x0));
    x1 = std::max(x0, std::min(sourceWidth - 1, x1));
    y0 = std::max(0, std::min(sourceHeight - 1, y0));
    y1 = std::max(y0, std::min(sourceHeight - 1, y1));
    const int px = outputX & 1;
    const int py = outputY & 1;
    int sx0 = alignedParity(x0, px, x0, x1);
    int sy0 = alignedParity(y0, py, y0, y1);
    uint64_t sum = 0;
    uint32_t count = 0;
    for (int sy = sy0; sy <= y1; sy += 2) {
        for (int sx = sx0; sx <= x1; sx += 2) {
            uint16_t v = 0;
            if (!readRawSample(src, sourceBytes, format, sourceWidth, sourceHeight,
                    rowStride, pixelStride, sx, sy, &v)) return false;
            sum += v;
            ++count;
        }
    }
    if (count == 0) {
        int cx = alignedParity((x0 + x1) / 2, px, 0, sourceWidth - 1);
        int cy = alignedParity((y0 + y1) / 2, py, 0, sourceHeight - 1);
        return readRawSample(src, sourceBytes, format, sourceWidth, sourceHeight,
                rowStride, pixelStride, cx, cy, sample);
    }
    *sample = static_cast<uint16_t>((sum + count / 2u) / count);
    return true;
}


int rawColorAt(int x, int y, int cfaPattern) {
    const int q = (x & 1) | ((y & 1) << 1);
    if (cfaPattern == 0) return q == 0 ? 0 : (q == 3 ? 2 : 1); // RGGB
    if (cfaPattern == 1) return q == 1 ? 0 : (q == 2 ? 2 : 1); // GRBG
    if (cfaPattern == 2) return q == 2 ? 0 : (q == 1 ? 2 : 1); // GBRG
    return q == 3 ? 0 : (q == 0 ? 2 : 1);                      // BGGR
}

bool normalizedRaw(const uint8_t *src, size_t sourceBytes, int format,
                   int width, int height, int rowStride, int pixelStride,
                   int x, int y, const int black4[4], int whiteLevel, float *out) {
    x = std::max(0, std::min(width - 1, x));
    y = std::max(0, std::min(height - 1, y));
    uint16_t sample = 0;
    if (!readRawSample(src, sourceBytes, format, width, height, rowStride, pixelStride, x, y, &sample)) {
        return false;
    }
    const int q = (x & 1) | ((y & 1) << 1);
    const int black = black4[q];
    const float denom = static_cast<float>(std::max(1, whiteLevel - black));
    *out = std::max(0.0f, (static_cast<float>(sample) - static_cast<float>(black)) / denom);
    return true;
}

bool demosaicCameraRgb(const uint8_t *src, size_t sourceBytes, int format,
                       int width, int height, int rowStride, int pixelStride,
                       int x, int y, int cfaPattern, const int black4[4], int whiteLevel,
                       float rgb[3]) {
    // Bilinear reconstruction in the original sensor lattice. This is intentionally performed
    // before VF-S reduction so the 640x480 preview never pretends distant photosites are adjacent.
    for (int target = 0; target < 3; ++target) {
        float center = 0.0f;
        if (rawColorAt(x, y, cfaPattern) == target) {
            if (!normalizedRaw(src, sourceBytes, format, width, height, rowStride, pixelStride,
                    x, y, black4, whiteLevel, &center)) return false;
            rgb[target] = center;
            continue;
        }
        float sum = 0.0f;
        int count = 0;
        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                if (dx == 0 && dy == 0) continue;
                const int sx = std::max(0, std::min(width - 1, x + dx));
                const int sy = std::max(0, std::min(height - 1, y + dy));
                if (rawColorAt(sx, sy, cfaPattern) != target) continue;
                float v = 0.0f;
                if (!normalizedRaw(src, sourceBytes, format, width, height, rowStride, pixelStride,
                        sx, sy, black4, whiteLevel, &v)) return false;
                sum += v;
                ++count;
            }
        }
        if (count == 0) return false;
        rgb[target] = sum / static_cast<float>(count);
    }
    return true;
}

bool reducedPreviewRgb(const uint8_t *src, size_t sourceBytes, int format,
                       int sourceWidth, int sourceHeight, int rowStride, int pixelStride,
                       int outputX, int outputY, int outputWidth, int outputHeight,
                       int cfaPattern, const int black4[4], int whiteLevel, float rgb[3]) {
    const double sx0 = static_cast<double>(outputX) * sourceWidth / outputWidth;
    const double sx1 = static_cast<double>(outputX + 1) * sourceWidth / outputWidth;
    const double sy0 = static_cast<double>(outputY) * sourceHeight / outputHeight;
    const double sy1 = static_cast<double>(outputY + 1) * sourceHeight / outputHeight;
    // Four source-domain taps approximate a box reduction, but every tap is first demosaiced from
    // physically adjacent Bayer samples. This is the key ownership difference from 26684.
    const double fx[2] = {0.25, 0.75};
    const double fy[2] = {0.25, 0.75};
    rgb[0] = rgb[1] = rgb[2] = 0.0f;
    int count = 0;
    for (double py : fy) {
        for (double px : fx) {
            int sx = static_cast<int>(std::floor(sx0 + (sx1 - sx0) * px));
            int sy = static_cast<int>(std::floor(sy0 + (sy1 - sy0) * py));
            sx = std::max(1, std::min(sourceWidth - 2, sx));
            sy = std::max(1, std::min(sourceHeight - 2, sy));
            float tap[3] = {0.0f, 0.0f, 0.0f};
            if (!demosaicCameraRgb(src, sourceBytes, format, sourceWidth, sourceHeight,
                    rowStride, pixelStride, sx, sy, cfaPattern, black4, whiteLevel, tap)) return false;
            rgb[0] += tap[0]; rgb[1] += tap[1]; rgb[2] += tap[2];
            ++count;
        }
    }
    if (count == 0) return false;
    rgb[0] /= count; rgb[1] /= count; rgb[2] /= count;
    return true;
}

spektrafilm::RenderParams factoryParams(bool preview) {
    spektrafilm::RenderParams p;
    p.process = spektrafilm::ProcessMode::PrintSimulation;
    p.scanNegativeInvert = false;
    p.renderOutput = spektrafilm::RenderOutputMode::FinalPreview;
    p.rgbToRawMethod = spektrafilm::RgbToRawMethod::Hanatos2026;
    p.inputColorSpace = spektrafilm::ColorSpace::LinearRec709;
    p.outputColorSpace = spektrafilm::ColorSpace::Srgb;
    p.outputRole = spektrafilm::OutputRole::DisplaySdr;
    p.colorAdaptation = false;
    p.film = 2;
    p.paper = 3;
    p.printTiming = spektrafilm::PrintTimingMode::FilteredEnlarger;
    p.filmExposureEv = 0.0f;
    p.autoExposure = false;
    p.printExposureEv = 0.0f;
    p.printerLightCalibration = true;
    p.grainEnabled = false;
    p.halationEnabled = false;
    p.cameraDiffusionEnabled = false;
    p.printDiffusionEnabled = false;
    p.scannerEnabled = false;
    p.gpuRenderTiling = spektrafilm::GpuRenderTilingMode::Tiled;
    (void)preview;
    return p;
}

bool ensureRenderer(AAssetManager *manager, const std::string &root, std::string *error) {
    if (gRenderer && root == gResourceRoot && gRenderer->isAvailable()) return true;
    if (!mkdirOne(root)) {
        if (error) *error = "Unable to create Spektra runtime directory";
        return false;
    }
    if (!iris_spektra::initializeProfileData(manager, error)) return false;
    if (!iris_spektra::materializeEmbeddedShaders(root, error)) return false;
    if (!copyAsset(manager, "spektra/data/SpektraHanatos2025Spectra.f32",
                   root + "/SpektraHanatos2025Spectra.f32", error)) return false;
    if (!copyAsset(manager, "spektra/data/SpektraOutputGamutCompression.f32",
                   root + "/SpektraOutputGamutCompression.f32", error)) return false;
    if (::setenv("SPEKTRAFILM_RESOURCE_DIR", root.c_str(), 1) != 0) {
        if (error) *error = "Unable to set Spektra resource directory";
        return false;
    }
    gRenderer = spektrafilm::createNativeRenderer();
    if (!gRenderer || !gRenderer->isAvailable()) {
        if (error) *error = gRenderer ? gRenderer->lastError() : "Unable to create Spektra Vulkan renderer";
        gRenderer.reset();
        return false;
    }
    gResourceRoot = root;
    return true;
}
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraRawFrame_nativeDecodePreviewRgb16f(
        JNIEnv *env, jclass, jobject source, jint sourceOffset, jint sourceBytes,
        jint sourceWidth, jint sourceHeight, jint rowStride, jint pixelStride, jint format,
        jint outputWidth, jint outputHeight, jint sensorCfa, jint bayerOffset,
        jintArray sensorBlackArray, jint whiteLevel) {
    auto *base = static_cast<uint8_t *>(env->GetDirectBufferAddress(source));
    const jlong capacity = env->GetDirectBufferCapacity(source);
    if (!base || capacity < 0 || sourceOffset < 0 || sourceBytes <= 0
            || static_cast<jlong>(sourceOffset) + sourceBytes > capacity) {
        throwIllegalArgument(env, "Spektra VF-S RAW direct-buffer bounds are invalid");
        return nullptr;
    }
    if (sourceWidth <= 2 || sourceHeight <= 2 || outputWidth <= 0 || outputHeight <= 0
            || outputWidth > sourceWidth || outputHeight > sourceHeight || rowStride <= 0
            || sensorCfa < 0 || sensorCfa > 3 || bayerOffset < 0 || bayerOffset > 3
            || whiteLevel <= 0 || !sensorBlackArray || env->GetArrayLength(sensorBlackArray) < 4) {
        throwIllegalArgument(env, "Spektra VF-S geometry/CFA contract is invalid");
        return nullptr;
    }
    const int effectivePixelStride = format == kAndroidRawSensor ? std::max(2, static_cast<int>(pixelStride)) : 0;
    const int minimumRow = minRawRowBytes(format, sourceWidth, effectivePixelStride);
    const uint64_t minimumBytes = static_cast<uint64_t>(sourceHeight - 1) * static_cast<uint64_t>(rowStride)
            + static_cast<uint64_t>(std::max(0, minimumRow));
    if (minimumRow < 0 || rowStride < minimumRow || static_cast<uint64_t>(sourceBytes) < minimumBytes) {
        throwIllegalArgument(env, "Spektra VF-S row-stride/buffer contract is invalid");
        return nullptr;
    }
    jint sensorBlack[4] = {0, 0, 0, 0};
    env->GetIntArrayRegion(sensorBlackArray, 0, 4, sensorBlack);
    if (env->ExceptionCheck()) return nullptr;
    int black4[4];
    for (int q = 0; q < 4; ++q) black4[q] = sensorBlack[q ^ (bayerOffset & 3)];
    const int effectiveCfa = sensorCfa ^ (bayerOffset & 3);
    const uint64_t outBytes64 = static_cast<uint64_t>(outputWidth) * static_cast<uint64_t>(outputHeight) * 8u;
    if (outBytes64 > 0x7fffffffull) {
        throwIllegalArgument(env, "Spektra VF-S RGB16F output is too large");
        return nullptr;
    }
    jbyteArray output = env->NewByteArray(static_cast<jsize>(outBytes64));
    if (!output) return nullptr;
    jboolean isCopy = JNI_FALSE;
    jbyte *outBytes = env->GetByteArrayElements(output, &isCopy);
    if (!outBytes) return nullptr;
    auto *out = reinterpret_cast<uint16_t *>(outBytes);
    const uint8_t *src = base + sourceOffset;
    bool ok = true;
    for (int y = 0; y < outputHeight && ok; ++y) {
        for (int x = 0; x < outputWidth; ++x) {
            float rgb[3] = {0.0f, 0.0f, 0.0f};
            if (!reducedPreviewRgb(src, static_cast<size_t>(sourceBytes), format,
                    sourceWidth, sourceHeight, rowStride, effectivePixelStride,
                    x, y, outputWidth, outputHeight, effectiveCfa, black4, whiteLevel, rgb)) {
                ok = false;
                break;
            }
            const size_t d = (static_cast<size_t>(y) * static_cast<size_t>(outputWidth)
                    + static_cast<size_t>(x)) * 4u;
            out[d] = floatToHalf(rgb[0]);
            out[d + 1u] = floatToHalf(rgb[1]);
            out[d + 2u] = floatToHalf(rgb[2]);
            out[d + 3u] = floatToHalf(1.0f);
        }
    }
    env->ReleaseByteArrayElements(output, outBytes, ok ? 0 : JNI_ABORT);
    if (!ok) {
        throwIllegalArgument(env, "Spektra VF-S reconstruction reached an invalid RAW sample");
        return nullptr;
    }
    return output;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraRawFrame_nativeDecodeRaw(
        JNIEnv *env, jclass, jobject source, jint sourceOffset, jint sourceBytes,
        jint sourceWidth, jint sourceHeight, jint rowStride, jint pixelStride, jint format,
        jint outputWidth, jint outputHeight) {
    auto *base = static_cast<uint8_t *>(env->GetDirectBufferAddress(source));
    const jlong capacity = env->GetDirectBufferCapacity(source);
    if (!base || capacity < 0) {
        throwIllegalArgument(env, "Spektra RAW plane must be a direct ByteBuffer");
        return nullptr;
    }
    if (sourceOffset < 0 || sourceBytes <= 0 || static_cast<jlong>(sourceOffset) + sourceBytes > capacity) {
        throwIllegalArgument(env, "Spektra RAW direct-buffer bounds are invalid");
        return nullptr;
    }
    const bool packedWidthInvalid = (format == kAndroidRaw10 || format == kAndroidRaw12)
            && (sourceWidth & 3) != 0;
    if (sourceWidth <= 0 || sourceHeight <= 0 || outputWidth <= 0 || outputHeight <= 0
            || (sourceWidth & 1) != 0 || (sourceHeight & 1) != 0 || packedWidthInvalid
            || (outputWidth & 1) != 0 || (outputHeight & 1) != 0
            || outputWidth > sourceWidth || outputHeight > sourceHeight || rowStride <= 0) {
        throwIllegalArgument(env, "Spektra RAW dimensions are invalid");
        return nullptr;
    }
    const int effectivePixelStride = format == kAndroidRawSensor ? std::max(2, static_cast<int>(pixelStride)) : 0;
    const int minimumRow = minRawRowBytes(format, sourceWidth, effectivePixelStride);
    if (minimumRow < 0) {
        throwIllegalArgument(env, "Spektra RAW format is unsupported");
        return nullptr;
    }
    const uint64_t minimumBytes = static_cast<uint64_t>(sourceHeight - 1) * static_cast<uint64_t>(rowStride)
            + static_cast<uint64_t>(minimumRow);
    if (rowStride < minimumRow || static_cast<uint64_t>(sourceBytes) < minimumBytes) {
        throwIllegalArgument(env, "Spektra RAW row-stride/buffer contract is invalid");
        return nullptr;
    }
    const uint64_t outputBytes64 = static_cast<uint64_t>(outputWidth) * static_cast<uint64_t>(outputHeight) * 2u;
    if (outputBytes64 > 0x7fffffffull) {
        throwIllegalArgument(env, "Spektra decoded RAW is too large");
        return nullptr;
    }
    jbyteArray output = env->NewByteArray(static_cast<jsize>(outputBytes64));
    if (!output) return nullptr;
    jboolean isCopy = JNI_FALSE;
    jbyte *out = env->GetByteArrayElements(output, &isCopy);
    if (!out) return nullptr;
    const uint8_t *src = base + sourceOffset;
    bool ok = true;
    const bool fullResolution = outputWidth == sourceWidth && outputHeight == sourceHeight;
    for (int y = 0; y < outputHeight && ok; ++y) {
        for (int x = 0; x < outputWidth; ++x) {
            uint16_t sample = 0;
            const bool sampleOk = fullResolution
                    ? readRawSample(src, static_cast<size_t>(sourceBytes), format, sourceWidth, sourceHeight,
                            rowStride, effectivePixelStride, x, y, &sample)
                    : averageRawPhaseBox(src, static_cast<size_t>(sourceBytes), format,
                            sourceWidth, sourceHeight, rowStride, effectivePixelStride,
                            x, y, outputWidth, outputHeight, &sample);
            if (!sampleOk) {
                ok = false;
                break;
            }
            const size_t dst = (static_cast<size_t>(y) * static_cast<size_t>(outputWidth)
                    + static_cast<size_t>(x)) * 2u;
            out[dst] = static_cast<jbyte>(sample & 0xffu);
            out[dst + 1u] = static_cast<jbyte>((sample >> 8u) & 0xffu);
        }
    }
    env->ReleaseByteArrayElements(output, out, ok ? 0 : JNI_ABORT);
    if (!ok) {
        throwIllegalArgument(env, "Spektra RAW decoder reached an invalid packed offset");
        return nullptr;
    }
    return output;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraFilmRenderer_nativeInitialize(
        JNIEnv *env, jclass, jobject assetManager, jstring resourceRoot) {
    std::lock_guard<std::mutex> lock(gRendererMutex);
    AAssetManager *manager = AAssetManager_fromJava(env, assetManager);
    const std::string root = jstringToString(env, resourceRoot);
    std::string error;
    const bool ok = ensureRenderer(manager, root, &error);
    gLastError = error;
    if (ok) LOGI("IRIS_26681_SPEKTRA_VULKAN_READY root=%s", root.c_str());
    else LOGE("IRIS_26681_SPEKTRA_VULKAN_INIT_FAILED %s", error.c_str());
    return ok ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraFilmRenderer_nativeRenderToBitmap(
        JNIEnv *env, jclass, jobject rgba16f, jint width, jint height,
        jobject bitmap, jboolean preview, jdouble timeSeconds) {
    std::lock_guard<std::mutex> lock(gRendererMutex);
    if (!gRenderer || !gRenderer->isAvailable()) {
        gLastError = "Spektra renderer is not initialized";
        return JNI_FALSE;
    }
    void *src = env->GetDirectBufferAddress(rgba16f);
    const jlong capacity = env->GetDirectBufferCapacity(rgba16f);
    const uint64_t expected = static_cast<uint64_t>(width) * static_cast<uint64_t>(height) * 8u;
    if (!src || capacity < 0 || static_cast<uint64_t>(capacity) < expected || width <= 0 || height <= 0) {
        gLastError = "Invalid Spektra RGBA16F source buffer";
        return JNI_FALSE;
    }
    AndroidBitmapInfo info{};
    if (AndroidBitmap_getInfo(env, bitmap, &info) != ANDROID_BITMAP_RESULT_SUCCESS ||
        info.format != ANDROID_BITMAP_FORMAT_RGBA_8888 ||
        info.width != static_cast<uint32_t>(width) || info.height != static_cast<uint32_t>(height)) {
        gLastError = "Spektra destination bitmap must be RGBA_8888 and match source dimensions";
        return JNI_FALSE;
    }
    // The upstream Vulkan renderer uploads source bytes before command submission and writes the
    // destination view only after the fence completes, so host source/destination may alias safely.
    // Reuse the direct RGBA16F carrier to avoid a second full-resolution half-float allocation.
    spektrafilm::ImageView in{};
    in.data = src; in.width = width; in.height = height; in.rowBytes = width * 8; in.components = 4; in.bytesPerComponent = 2;
    spektrafilm::MutableImageView out{};
    out.data = src; out.width = width; out.height = height; out.rowBytes = width * 8; out.components = 4; out.bytesPerComponent = 2;
    spektrafilm::RenderWindow window{0, 0, width, height};
    const spektrafilm::RenderParams params = factoryParams(preview == JNI_TRUE);
    if (!gRenderer->render(in, out, window, params, timeSeconds)) {
        gLastError = gRenderer->lastError();
        LOGE("IRIS_26681_SPEKTRA_RENDER_FAILED %s", gLastError.c_str());
        return JNI_FALSE;
    }
    void *pixels = nullptr;
    if (AndroidBitmap_lockPixels(env, bitmap, &pixels) != ANDROID_BITMAP_RESULT_SUCCESS || !pixels) {
        gLastError = "Unable to lock Spektra destination bitmap";
        return JNI_FALSE;
    }
    auto *dst = static_cast<uint8_t *>(pixels);
    for (int y = 0; y < height; ++y) {
        uint8_t *row = dst + static_cast<size_t>(y) * info.stride;
        const uint16_t *srcRow = static_cast<const uint16_t *>(src)
            + static_cast<size_t>(y) * static_cast<size_t>(width) * 4u;
        for (int x = 0; x < width; ++x) {
            row[x * 4 + 0] = toByte(srcRow[x * 4 + 0]);
            row[x * 4 + 1] = toByte(srcRow[x * 4 + 1]);
            row[x * 4 + 2] = toByte(srcRow[x * 4 + 2]);
            row[x * 4 + 3] = 255u;
        }
    }
    AndroidBitmap_unlockPixels(env, bitmap);
    gLastError.clear();
    return JNI_TRUE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraFilmRenderer_nativeLastError(
        JNIEnv *env, jclass) {
    std::lock_guard<std::mutex> lock(gRendererMutex);
    return env->NewStringUTF(gLastError.c_str());
}

extern "C" JNIEXPORT void JNICALL
Java_com_particlesdevs_photoncamera_spektra_SpektraFilmRenderer_nativeRelease(
        JNIEnv *, jclass) {
    std::lock_guard<std::mutex> lock(gRendererMutex);
    if (gRenderer) gRenderer->releaseTransientResources();
    gRenderer.reset();
    gResourceRoot.clear();
    gLastError.clear();
}
