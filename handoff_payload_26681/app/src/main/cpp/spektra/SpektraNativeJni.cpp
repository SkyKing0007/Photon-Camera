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
