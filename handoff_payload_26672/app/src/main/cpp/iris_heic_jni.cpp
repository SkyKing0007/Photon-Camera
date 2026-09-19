#include <jni.h>
#include <android/bitmap.h>
#include <android/log.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <new>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <string>
#include <utility>
#include <vector>
#include <jpeglib.h>

#include <libheif/heif.h>
#include <libheif/heif_plugin.h>
#include "plugin_registry.h"
#include "codecs/hevc_boxes.h"
#include <ultrahdr/icc.h>
#include <ultrahdr/gainmapmetadata.h>
#include <ultrahdr/jpegr.h>
#include <ultrahdr/jpegrutils.h>
#include <ultrahdr/ultrahdrcommon.h>

#define IRIS26636_TAG "IrisHeicNative"
#define IRIS26636_LOGE(...) __android_log_print(ANDROID_LOG_ERROR, IRIS26636_TAG, __VA_ARGS__)
#define IRIS26636_LOGI(...) __android_log_print(ANDROID_LOG_INFO, IRIS26636_TAG, __VA_ARGS__)

namespace {

thread_local JNIEnv* gIris26636Env = nullptr;

struct Iris26636EncoderState {
    int quality = 95;
    int logging = 0;
    bool lossless = false;
    std::vector<std::vector<uint8_t>> nals;
    size_t nextNal = 0;
};

static const char* iris26636PluginName() { return "Iris Android hardware MediaCodec HEVC"; }
static void iris26636PluginInit() {}
static void iris26636PluginCleanup() {}

static heif_error iris26636NewEncoder(void** out) {
    if (!out) return heif_error_unsupported_parameter;
    *out = new (std::nothrow) Iris26636EncoderState();
    if (!*out) {
        return {heif_error_Memory_allocation_error, heif_suberror_Unspecified,
                "Iris hardware HEVC encoder allocation failed"};
    }
    return heif_error_ok;
}

static void iris26636FreeEncoder(void* p) { delete static_cast<Iris26636EncoderState*>(p); }

static heif_error iris26636SetQuality(void* p, int q) {
    if (!p || q < 0 || q > 100) return heif_error_invalid_parameter_value;
    static_cast<Iris26636EncoderState*>(p)->quality = q;
    return heif_error_ok;
}
static heif_error iris26636GetQuality(void* p, int* q) {
    if (!p || !q) return heif_error_unsupported_parameter;
    *q = static_cast<Iris26636EncoderState*>(p)->quality;
    return heif_error_ok;
}
static heif_error iris26636SetLossless(void* p, int v) {
    if (!p) return heif_error_unsupported_parameter;
    if (v) return heif_error_unsupported_parameter;
    static_cast<Iris26636EncoderState*>(p)->lossless = false;
    return heif_error_ok;
}
static heif_error iris26636GetLossless(void* p, int* v) {
    if (!p || !v) return heif_error_unsupported_parameter;
    *v = 0;
    return heif_error_ok;
}
static heif_error iris26636SetLogging(void* p, int v) {
    if (!p) return heif_error_unsupported_parameter;
    static_cast<Iris26636EncoderState*>(p)->logging = v;
    return heif_error_ok;
}
static heif_error iris26636GetLogging(void* p, int* v) {
    if (!p || !v) return heif_error_unsupported_parameter;
    *v = static_cast<Iris26636EncoderState*>(p)->logging;
    return heif_error_ok;
}
static const heif_encoder_parameter** iris26636ListParameters(void*) { return nullptr; }
static heif_error iris26636SetInteger(void*, const char*, int) { return heif_error_unsupported_parameter; }
static heif_error iris26636GetInteger(void*, const char*, int*) { return heif_error_unsupported_parameter; }
static heif_error iris26636SetBoolean(void*, const char*, int) { return heif_error_unsupported_parameter; }
static heif_error iris26636GetBoolean(void*, const char*, int*) { return heif_error_unsupported_parameter; }
static heif_error iris26636SetString(void*, const char*, const char*) { return heif_error_unsupported_parameter; }
static heif_error iris26636GetString(void*, const char*, char*, int) { return heif_error_unsupported_parameter; }

static void iris26636QueryColor(heif_colorspace* cs, heif_chroma* chroma) {
    if (cs) *cs = heif_colorspace_YCbCr;
    if (chroma) *chroma = heif_chroma_420;
}
static void iris26636QueryColor2(void*, heif_colorspace* cs, heif_chroma* chroma) {
    iris26636QueryColor(cs, chroma);
}
static void iris26636QueryEncodedSize(void*, uint32_t iw, uint32_t ih, uint32_t* ow, uint32_t* oh) {
    if (ow) *ow = (iw + 1u) & ~1u;
    if (oh) *oh = (ih + 1u) & ~1u;
}

static bool iris26636CopyPlane(const heif_image* image, heif_channel channel,
                               int width, int height, uint8_t* dst, int dstStride,
                               uint8_t fillValue) {
    int srcStride = 0;
    const uint8_t* src = heif_image_get_plane_readonly(image, channel, &srcStride);
    if (!src) {
        for (int y = 0; y < height; ++y) std::memset(dst + static_cast<size_t>(y) * dstStride, fillValue, width);
        return true;
    }
    if (srcStride < width) return false;
    for (int y = 0; y < height; ++y) {
        std::memcpy(dst + static_cast<size_t>(y) * dstStride,
                    src + static_cast<size_t>(y) * srcStride, width);
    }
    return true;
}

static bool iris26636CallHardwareEncoder(int width, int height, const std::vector<uint8_t>& i420,
                                         int quality, bool gainMap,
                                         std::vector<std::vector<uint8_t>>& out) {
    JNIEnv* env = gIris26636Env;
    if (!env) return false;
    jclass cls = env->FindClass(
        "com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder");
    if (!cls || env->ExceptionCheck()) {
        env->ExceptionClear();
        return false;
    }
    jmethodID method = env->GetStaticMethodID(cls, "encodeI420", "(II[BIZ)[[B");
    if (!method || env->ExceptionCheck()) {
        env->ExceptionClear();
        env->DeleteLocalRef(cls);
        return false;
    }
    jbyteArray data = env->NewByteArray(static_cast<jsize>(i420.size()));
    if (!data) {
        env->DeleteLocalRef(cls);
        return false;
    }
    env->SetByteArrayRegion(data, 0, static_cast<jsize>(i420.size()),
                            reinterpret_cast<const jbyte*>(i420.data()));
    jobjectArray array = static_cast<jobjectArray>(
        env->CallStaticObjectMethod(cls, method, width, height, data, quality,
                                    gainMap ? JNI_TRUE : JNI_FALSE));
    env->DeleteLocalRef(data);
    env->DeleteLocalRef(cls);
    if (env->ExceptionCheck()) {
        env->ExceptionDescribe();
        env->ExceptionClear();
        return false;
    }
    if (!array) return false;
    const jsize count = env->GetArrayLength(array);
    out.clear();
    out.reserve(static_cast<size_t>(count));
    for (jsize i = 0; i < count; ++i) {
        auto nal = static_cast<jbyteArray>(env->GetObjectArrayElement(array, i));
        if (!nal) continue;
        const jsize n = env->GetArrayLength(nal);
        if (n > 0) {
            std::vector<uint8_t> bytes(static_cast<size_t>(n));
            env->GetByteArrayRegion(nal, 0, n, reinterpret_cast<jbyte*>(bytes.data()));
            if (!env->ExceptionCheck()) out.emplace_back(std::move(bytes));
            else env->ExceptionClear();
        }
        env->DeleteLocalRef(nal);
    }
    env->DeleteLocalRef(array);
    return !out.empty();
}

static heif_error iris26636EncodeImage(void* p, const heif_image* image,
                                       heif_image_input_class inputClass) {
    auto* state = static_cast<Iris26636EncoderState*>(p);
    if (!state || !image || !gIris26636Env) return heif_error_unsupported_parameter;
    const int width = heif_image_get_width(image, heif_channel_Y);
    const int height = heif_image_get_height(image, heif_channel_Y);
    if (width <= 0 || height <= 0 || (width & 1) || (height & 1)) {
        return {heif_error_Encoder_plugin_error, heif_suberror_Invalid_parameter_value,
                "Iris hardware HEVC requires positive even YUV420 dimensions"};
    }
    const int cw = width / 2;
    const int ch = height / 2;
    const size_t ySize = static_cast<size_t>(width) * height;
    std::vector<uint8_t> i420(ySize + 2u * static_cast<size_t>(cw) * ch, 128u);
    if (!iris26636CopyPlane(image, heif_channel_Y, width, height, i420.data(), width, 0) ||
        !iris26636CopyPlane(image, heif_channel_Cb, cw, ch, i420.data() + ySize, cw, 128) ||
        !iris26636CopyPlane(image, heif_channel_Cr, cw, ch,
                           i420.data() + ySize + static_cast<size_t>(cw) * ch, cw, 128)) {
        return {heif_error_Encoder_plugin_error, heif_suberror_Unspecified,
                "Iris failed to copy libheif YUV420 planes"};
    }
    state->nals.clear();
    state->nextNal = 0;
    const bool gainMap = inputClass == heif_image_input_class_gain_map;
    if (!iris26636CallHardwareEncoder(width, height, i420, state->quality, gainMap, state->nals)) {
        return {heif_error_Encoder_plugin_error, heif_suberror_Unspecified,
                "Android hardware MediaCodec HEVC encoding failed"};
    }
    // IRIS_26637_HEVC_ACTUAL_OUTPUT_PROOF
    // Parse the emitted SPS with the same pinned libheif parser that builds hvcC. Diagnostic only:
    // never changes encoder selection, input format, quality, or the returned NAL stream.
    for (const auto& nal : state->nals) {
        if (nal.size() < 3u || (((nal[0] >> 1) & 0x3f) != 33)) continue;
        Box_hvcC::configuration cfg{};
        int codedWidth = 0, codedHeight = 0;
        const Error parseErr = parse_sps_for_hvcC_configuration(
                nal.data(), nal.size(), &cfg, &codedWidth, &codedHeight);
        if (!parseErr) {
            IRIS26636_LOGI(
                    "IRIS_26637_HEVC_OUTPUT gainMap=%s chromaFormat=%u bitDepthLuma=%u "
                    "bitDepthChroma=%u profile=%u level=%u coded=%dx%d",
                    gainMap ? "true" : "false", static_cast<unsigned>(cfg.chroma_format),
                    static_cast<unsigned>(cfg.bit_depth_luma),
                    static_cast<unsigned>(cfg.bit_depth_chroma),
                    static_cast<unsigned>(cfg.general_profile_idc),
                    static_cast<unsigned>(cfg.general_level_idc), codedWidth, codedHeight);
        } else {
            IRIS26636_LOGE("IRIS_26637_HEVC_OUTPUT SPS parse failed");
        }
        break;
    }
    return heif_error_ok;
}

static heif_error iris26636GetCompressedData(void* p, uint8_t** data, int* size,
                                             heif_encoded_data_type* type) {
    auto* state = static_cast<Iris26636EncoderState*>(p);
    if (!state || !data || !size) return heif_error_unsupported_parameter;
    if (state->nextNal >= state->nals.size()) {
        *data = nullptr;
        *size = 0;
        return heif_error_ok;
    }
    auto& nal = state->nals[state->nextNal++];
    *data = nal.data();
    *size = static_cast<int>(nal.size());
    if (type) {
        int nalType = nal.size() >= 2 ? ((nal[0] >> 1) & 0x3f) : -1;
        *type = (nalType == 32 || nalType == 33 || nalType == 34)
                    ? heif_encoded_data_type_HEVC_header
                    : heif_encoded_data_type_HEVC_image;
    }
    return heif_error_ok;
}

static const heif_encoder_plugin kIris26636MediaCodecHevcPlugin = {
    /* plugin_api_version */ 3,
    /* compression_format */ heif_compression_HEVC,
    /* id_name */ "iris-mediacodec-hevc",
    /* priority */ 1000,
    /* supports_lossy_compression */ 1,
    /* supports_lossless_compression */ 0,
    /* get_plugin_name */ iris26636PluginName,
    /* init_plugin */ iris26636PluginInit,
    /* cleanup_plugin */ iris26636PluginCleanup,
    /* new_encoder */ iris26636NewEncoder,
    /* free_encoder */ iris26636FreeEncoder,
    /* set_parameter_quality */ iris26636SetQuality,
    /* get_parameter_quality */ iris26636GetQuality,
    /* set_parameter_lossless */ iris26636SetLossless,
    /* get_parameter_lossless */ iris26636GetLossless,
    /* set_parameter_logging_level */ iris26636SetLogging,
    /* get_parameter_logging_level */ iris26636GetLogging,
    /* list_parameters */ iris26636ListParameters,
    /* set_parameter_integer */ iris26636SetInteger,
    /* get_parameter_integer */ iris26636GetInteger,
    /* set_parameter_boolean */ iris26636SetBoolean,
    /* get_parameter_boolean */ iris26636GetBoolean,
    /* set_parameter_string */ iris26636SetString,
    /* get_parameter_string */ iris26636GetString,
    /* query_input_colorspace */ iris26636QueryColor,
    /* encode_image */ iris26636EncodeImage,
    /* get_compressed_data */ iris26636GetCompressedData,
    /* query_input_colorspace2 */ iris26636QueryColor2,
    /* query_encoded_size */ iris26636QueryEncodedSize,
};

static bool iris26636RegisterEncoder() {
    // IRIS_26636_PINNED_LIBHEIF_STATIC_ENCODER_REGISTRY
    // Pinned libheif 4a3f74bc... has no public static encoder-registration API in this
    // static/no-plugin-loading configuration. Use its compiled-in registry and prove selection.
    static std::once_flag once;
    static bool ok = false;
    std::call_once(once, [] {
        register_encoder(&kIris26636MediaCodecHevcPlugin);
        ok = get_encoder(heif_compression_HEVC) == &kIris26636MediaCodecHevcPlugin;
        if (!ok) IRIS26636_LOGE("pinned libheif did not select Iris hardware HEVC encoder");
    });
    return ok;
}

struct Iris26636MemoryWriter {
    std::vector<uint8_t> bytes;
};
static heif_error iris26636WriteCallback(heif_context*, const void* data, size_t size, void* userdata) {
    auto* w = static_cast<Iris26636MemoryWriter*>(userdata);
    if (!w || (!data && size)) return heif_error_unsupported_parameter;
    const auto* p = static_cast<const uint8_t*>(data);
    w->bytes.insert(w->bytes.end(), p, p + size);
    return heif_error_ok;
}

static bool iris26636WriteFile(const std::string& path, const std::vector<uint8_t>& data) {
    if (path.empty() || data.empty()) return false;
    FILE* f = std::fopen(path.c_str(), "wb");
    if (!f) return false;
    const size_t n = std::fwrite(data.data(), 1, data.size(), f);
    const int flush = std::fflush(f);
    const int close = std::fclose(f);
    if (n != data.size() || flush != 0 || close != 0) {
        std::remove(path.c_str());
        return false;
    }
    return true;
}

static bool iris26636GetFloat3(JNIEnv* env, jfloatArray a, std::array<float, 3>& out) {
    if (!env || !a || env->GetArrayLength(a) != 3) return false;
    env->GetFloatArrayRegion(a, 0, 3, out.data());
    return !env->ExceptionCheck();
}

static std::string iris26636JString(JNIEnv* env, jstring s) {
    if (!env || !s) return {};
    const char* p = env->GetStringUTFChars(s, nullptr);
    if (!p) return {};
    std::string out(p);
    env->ReleaseStringUTFChars(s, p);
    return out;
}

static void iris26636AppendLe16(std::vector<uint8_t>& v, uint16_t x) {
    v.push_back(static_cast<uint8_t>(x)); v.push_back(static_cast<uint8_t>(x >> 8));
}
static void iris26636AppendLe32(std::vector<uint8_t>& v, uint32_t x) {
    v.push_back(static_cast<uint8_t>(x)); v.push_back(static_cast<uint8_t>(x >> 8));
    v.push_back(static_cast<uint8_t>(x >> 16)); v.push_back(static_cast<uint8_t>(x >> 24));
}
static void iris26636PutLe32(std::vector<uint8_t>& v, size_t pos, uint32_t x) {
    if (pos + 4 > v.size()) return;
    v[pos] = static_cast<uint8_t>(x); v[pos + 1] = static_cast<uint8_t>(x >> 8);
    v[pos + 2] = static_cast<uint8_t>(x >> 16); v[pos + 3] = static_cast<uint8_t>(x >> 24);
}

static bool iris26636ParseDouble(const std::string& s, double& out) {
    // IRIS_26636_EXIF_RATIONAL_PARSE
    // Photon focal length is intentionally stored as e.g. "234/100". Parse both that rational
    // form and ordinary decimal EXIF strings without accepting trailing junk or zero denominators.
    if (s.empty()) return false;
    char* end = nullptr;
    errno = 0;
    double v = std::strtod(s.c_str(), &end);
    if (errno || end == s.c_str() || !std::isfinite(v) || v < 0.0) return false;
    if (*end == '/') {
        char* denEnd = nullptr;
        errno = 0;
        const double den = std::strtod(end + 1, &denEnd);
        if (errno || denEnd == end + 1 || *denEnd != '\0' || !std::isfinite(den) || den <= 0.0)
            return false;
        v /= den;
    } else if (*end != '\0') {
        return false;
    }
    if (!std::isfinite(v)) return false;
    out = v;
    return true;
}
static std::pair<uint32_t, uint32_t> iris26636Rational(double v) {
    constexpr uint32_t den = 1000000u;
    double scaled = std::round(std::max(0.0, std::min(v, 4294.0)) * den);
    return {static_cast<uint32_t>(scaled), den};
}

struct Iris26636TiffEntry {
    uint16_t tag;
    uint16_t type;
    uint32_t count;
    std::vector<uint8_t> payload;
    bool subIfdPointer = false;
};

static std::vector<uint8_t> iris26636BuildExif(const std::string& iso,
                                               const std::string& fNumber,
                                               const std::string& focalLength,
                                               const std::string& exposureTime,
                                               const std::string& dateTime,
                                               const std::string& make,
                                               const std::string& model) {
    auto ascii = [](const std::string& s) {
        std::vector<uint8_t> p(s.begin(), s.end()); p.push_back(0); return p;
    };
    auto rationalPayload = [](std::pair<uint32_t,uint32_t> r) {
        std::vector<uint8_t> p; p.reserve(8); iris26636AppendLe32(p, r.first); iris26636AppendLe32(p, r.second); return p;
    };

    std::vector<Iris26636TiffEntry> ifd0;
    if (!make.empty()) ifd0.push_back({0x010F, 2, static_cast<uint32_t>(make.size() + 1), ascii(make)});
    if (!model.empty()) ifd0.push_back({0x0110, 2, static_cast<uint32_t>(model.size() + 1), ascii(model)});
    if (!dateTime.empty()) ifd0.push_back({0x0132, 2, static_cast<uint32_t>(dateTime.size() + 1), ascii(dateTime)});

    std::vector<Iris26636TiffEntry> exif;
    double v = 0.0;
    if (iris26636ParseDouble(exposureTime, v) && v > 0.0)
        exif.push_back({0x829A, 5, 1, rationalPayload(iris26636Rational(v))});
    if (iris26636ParseDouble(fNumber, v) && v > 0.0)
        exif.push_back({0x829D, 5, 1, rationalPayload(iris26636Rational(v))});
    if (iris26636ParseDouble(focalLength, v) && v > 0.0)
        exif.push_back({0x920A, 5, 1, rationalPayload(iris26636Rational(v))});
    if (iris26636ParseDouble(iso, v) && v > 0.0) {
        uint16_t iv = static_cast<uint16_t>(std::min(65535.0, std::round(v)));
        std::vector<uint8_t> p; iris26636AppendLe16(p, iv); p.resize(4, 0);
        exif.push_back({0x8827, 3, 1, p});
    }
    if (!exif.empty()) ifd0.push_back({0x8769, 4, 1, std::vector<uint8_t>(4, 0), true});

    std::sort(ifd0.begin(), ifd0.end(), [](const auto& a, const auto& b){ return a.tag < b.tag; });
    std::sort(exif.begin(), exif.end(), [](const auto& a, const auto& b){ return a.tag < b.tag; });

    std::vector<uint8_t> tiff;
    tiff.push_back('I'); tiff.push_back('I'); iris26636AppendLe16(tiff, 42); iris26636AppendLe32(tiff, 8);

    iris26636AppendLe16(tiff, static_cast<uint16_t>(ifd0.size()));
    const size_t ifd0EntriesStart = tiff.size();
    tiff.resize(tiff.size() + ifd0.size() * 12 + 4, 0);
    std::vector<std::pair<size_t, std::vector<uint8_t>>> deferred;
    size_t exifPointerPos = 0;
    for (size_t i = 0; i < ifd0.size(); ++i) {
        const auto& e = ifd0[i];
        size_t p = ifd0EntriesStart + i * 12;
        tiff[p] = static_cast<uint8_t>(e.tag); tiff[p+1] = static_cast<uint8_t>(e.tag >> 8);
        tiff[p+2] = static_cast<uint8_t>(e.type); tiff[p+3] = static_cast<uint8_t>(e.type >> 8);
        iris26636PutLe32(tiff, p + 4, e.count);
        if (e.subIfdPointer) { exifPointerPos = p + 8; }
        else if (e.payload.size() <= 4) std::copy(e.payload.begin(), e.payload.end(), tiff.begin() + static_cast<long>(p + 8));
        else deferred.emplace_back(p + 8, e.payload);
    }
    for (auto& d : deferred) {
        if (tiff.size() & 1u) tiff.push_back(0);
        iris26636PutLe32(tiff, d.first, static_cast<uint32_t>(tiff.size()));
        tiff.insert(tiff.end(), d.second.begin(), d.second.end());
    }

    if (!exif.empty()) {
        if (tiff.size() & 1u) tiff.push_back(0);
        const uint32_t exifOffset = static_cast<uint32_t>(tiff.size());
        iris26636PutLe32(tiff, exifPointerPos, exifOffset);
        iris26636AppendLe16(tiff, static_cast<uint16_t>(exif.size()));
        const size_t entriesStart = tiff.size();
        tiff.resize(tiff.size() + exif.size() * 12 + 4, 0);
        std::vector<std::pair<size_t, std::vector<uint8_t>>> exifDeferred;
        for (size_t i = 0; i < exif.size(); ++i) {
            const auto& e = exif[i];
            size_t p = entriesStart + i * 12;
            tiff[p] = static_cast<uint8_t>(e.tag); tiff[p+1] = static_cast<uint8_t>(e.tag >> 8);
            tiff[p+2] = static_cast<uint8_t>(e.type); tiff[p+3] = static_cast<uint8_t>(e.type >> 8);
            iris26636PutLe32(tiff, p + 4, e.count);
            if (e.payload.size() <= 4) std::copy(e.payload.begin(), e.payload.end(), tiff.begin() + static_cast<long>(p + 8));
            else exifDeferred.emplace_back(p + 8, e.payload);
        }
        for (auto& d : exifDeferred) {
            if (tiff.size() & 1u) tiff.push_back(0);
            iris26636PutLe32(tiff, d.first, static_cast<uint32_t>(tiff.size()));
            tiff.insert(tiff.end(), d.second.begin(), d.second.end());
        }
    }

    std::vector<uint8_t> heifExif(4, 0); // TIFF header begins immediately after HEIF's 4-byte offset field.
    heifExif.insert(heifExif.end(), tiff.begin(), tiff.end());
    return heifExif;
}

static bool iris26636FillBaseImage(JNIEnv* env, jobject bitmap, heif_image** out) {
    AndroidBitmapInfo info{};
    if (!bitmap || !out || AndroidBitmap_getInfo(env, bitmap, &info) != ANDROID_BITMAP_RESULT_SUCCESS ||
        info.format != ANDROID_BITMAP_FORMAT_RGBA_8888 || info.width == 0 || info.height == 0) return false;
    void* pixels = nullptr;
    if (AndroidBitmap_lockPixels(env, bitmap, &pixels) != ANDROID_BITMAP_RESULT_SUCCESS || !pixels) return false;
    heif_image* image = nullptr;
    // IRIS_26637_OPAQUE_RGB_HEIC_BASE_OWNER
    // Android Bitmap remains RGBA_8888 at the JNI boundary, but HEIC camera stills are opaque.
    // Publish only RGB so libheif cannot synthesize an auxiliary alpha image/item.
    heif_error err = heif_image_create(info.width, info.height, heif_colorspace_RGB,
                                       heif_chroma_interleaved_RGB, &image);
    if (err.code == heif_error_Ok)
        err = heif_image_add_plane(image, heif_channel_interleaved, info.width, info.height, 8);
    if (err.code == heif_error_Ok) {
        int stride = 0;
        uint8_t* dst = heif_image_get_plane(image, heif_channel_interleaved, &stride);
        if (!dst || stride < static_cast<int>(info.width * 3u)) err = heif_error_unsupported_parameter;
        else {
            const auto* src = static_cast<const uint8_t*>(pixels);
            for (uint32_t y = 0; y < info.height; ++y) {
                uint8_t* outRow = dst + static_cast<size_t>(y) * stride;
                const uint8_t* inRow = src + static_cast<size_t>(y) * info.stride;
                for (uint32_t x = 0; x < info.width; ++x) {
                    outRow[x * 3u + 0u] = inRow[x * 4u + 0u];
                    outRow[x * 3u + 1u] = inRow[x * 4u + 1u];
                    outRow[x * 3u + 2u] = inRow[x * 4u + 2u];
                }
            }
        }
    }
    AndroidBitmap_unlockPixels(env, bitmap);
    if (err.code != heif_error_Ok) { if (image) heif_image_release(image); return false; }
    *out = image;
    return true;
}

static bool iris26636FillGainmapImage(JNIEnv* env, jobject bitmap, heif_image** out) {
    AndroidBitmapInfo info{};
    if (!bitmap || !out || AndroidBitmap_getInfo(env, bitmap, &info) != ANDROID_BITMAP_RESULT_SUCCESS ||
        (info.format != ANDROID_BITMAP_FORMAT_A_8 && info.format != ANDROID_BITMAP_FORMAT_RGBA_8888) ||
        info.width == 0 || info.height == 0) return false;
    void* pixels = nullptr;
    if (AndroidBitmap_lockPixels(env, bitmap, &pixels) != ANDROID_BITMAP_RESULT_SUCCESS || !pixels) return false;
    heif_image* image = nullptr;
    heif_error err = heif_image_create(info.width, info.height, heif_colorspace_monochrome,
                                       heif_chroma_monochrome, &image);
    if (err.code == heif_error_Ok) err = heif_image_add_plane(image, heif_channel_Y, info.width, info.height, 8);
    if (err.code == heif_error_Ok) {
        int stride = 0;
        uint8_t* dst = heif_image_get_plane(image, heif_channel_Y, &stride);
        if (!dst || stride < static_cast<int>(info.width)) err = heif_error_unsupported_parameter;
        else {
            const auto* src = static_cast<const uint8_t*>(pixels);
            for (uint32_t y = 0; y < info.height; ++y) {
                uint8_t* row = dst + static_cast<size_t>(y) * stride;
                const uint8_t* in = src + static_cast<size_t>(y) * info.stride;
                if (info.format == ANDROID_BITMAP_FORMAT_A_8) std::memcpy(row, in, info.width);
                else for (uint32_t x = 0; x < info.width; ++x) row[x] = in[x * 4u];
            }
        }
    }
    AndroidBitmap_unlockPixels(env, bitmap);
    if (err.code != heif_error_Ok) { if (image) heif_image_release(image); return false; }
    *out = image;
    return true;
}


/* IRIS_26646_TRUE2X_HEIF_GRID_SOURCE_READER
 * Decode only one true-2x JPEG tile at a time. The source is the trusted JPEG produced by the
 * existing true-2x renderer, so this stage performs no scene/tone/color reconstruction; libjpeg
 * merely returns the already-encoded Display-P3 samples for hardware-HEVC tile publication. */
static bool iris26646DecodeJpegRegionRgb(const std::string& path, int expectedW, int expectedH,
                                         int x0, int y0, int w, int h,
                                         std::vector<uint8_t>* rgb) {
    if (!rgb || x0 < 0 || y0 < 0 || w <= 0 || h <= 0 || x0 + w > expectedW || y0 + h > expectedH)
        return false;
    FILE* f = std::fopen(path.c_str(), "rb");
    if (!f) return false;
    jpeg_decompress_struct c{};
    jpeg_error_mgr jerr{};
    c.err = jpeg_std_error(&jerr);
    jpeg_create_decompress(&c);
    jpeg_stdio_src(&c, f);
    bool ok = false;
    do {
        if (jpeg_read_header(&c, TRUE) != JPEG_HEADER_OK) break;
        c.out_color_space = JCS_RGB;
        if (!jpeg_start_decompress(&c)) break;
        if (static_cast<int>(c.output_width) != expectedW || static_cast<int>(c.output_height) != expectedH
                || c.output_components != 3) break;
        if (y0 > 0 && jpeg_skip_scanlines(&c, static_cast<JDIMENSION>(y0)) != static_cast<JDIMENSION>(y0)) break;
        rgb->assign(static_cast<size_t>(w) * h * 3u, 0u);
        std::vector<uint8_t> row(static_cast<size_t>(expectedW) * 3u);
        for (int y = 0; y < h; ++y) {
            JSAMPROW rp = row.data();
            if (jpeg_read_scanlines(&c, &rp, 1) != 1) { rgb->clear(); break; }
            std::memcpy(rgb->data() + static_cast<size_t>(y) * w * 3u,
                        row.data() + static_cast<size_t>(x0) * 3u,
                        static_cast<size_t>(w) * 3u);
        }
        if (rgb->size() != static_cast<size_t>(w) * h * 3u) break;
        ok = true;
    } while (false);
    jpeg_destroy_decompress(&c);
    std::fclose(f);
    return ok;
}

/* Gain codes are logarithmic. A 2x2 arithmetic average in code space therefore preserves the
 * local geometric-mean gain while reducing the true-2x 1:1 map to Android/AOSP-style half-linear
 * gain-map resolution without inventing new HDR amplitude. */
static bool iris26646DecodeGainHalf(const std::string& path, int expectedW, int expectedH,
                                    std::vector<uint8_t>* gain, int* outW, int* outH) {
    if (!gain || !outW || !outH || expectedW <= 0 || expectedH <= 0 || (expectedW & 1) || (expectedH & 1))
        return false;
    FILE* f = std::fopen(path.c_str(), "rb");
    if (!f) return false;
    jpeg_decompress_struct c{};
    jpeg_error_mgr jerr{};
    c.err = jpeg_std_error(&jerr);
    jpeg_create_decompress(&c);
    jpeg_stdio_src(&c, f);
    bool ok = false;
    do {
        if (jpeg_read_header(&c, TRUE) != JPEG_HEADER_OK) break;
        c.out_color_space = JCS_GRAYSCALE;
        if (!jpeg_start_decompress(&c)) break;
        if (static_cast<int>(c.output_width) != expectedW || static_cast<int>(c.output_height) != expectedH
                || c.output_components != 1) break;
        const int gw = expectedW / 2, gh = expectedH / 2;
        gain->assign(static_cast<size_t>(gw) * gh, 0u);
        std::vector<uint8_t> row0(static_cast<size_t>(expectedW));
        std::vector<uint8_t> row1(static_cast<size_t>(expectedW));
        for (int y = 0; y < gh; ++y) {
            JSAMPROW r0 = row0.data(), r1 = row1.data();
            if (jpeg_read_scanlines(&c, &r0, 1) != 1 || jpeg_read_scanlines(&c, &r1, 1) != 1) {
                gain->clear(); break;
            }
            for (int x = 0; x < gw; ++x) {
                unsigned sum = row0[static_cast<size_t>(2*x)] + row0[static_cast<size_t>(2*x+1)]
                             + row1[static_cast<size_t>(2*x)] + row1[static_cast<size_t>(2*x+1)];
                (*gain)[static_cast<size_t>(y) * gw + x] = static_cast<uint8_t>((sum + 2u) / 4u);
            }
        }
        if (gain->size() != static_cast<size_t>(gw) * gh) break;
        *outW = gw; *outH = gh; ok = true;
    } while (false);
    jpeg_destroy_decompress(&c);
    std::fclose(f);
    return ok;
}

static bool iris26646FillRgbImage(const std::vector<uint8_t>& rgb, int w, int h, heif_image** out) {
    if (!out || w <= 0 || h <= 0 || rgb.size() != static_cast<size_t>(w) * h * 3u) return false;
    heif_image* image = nullptr;
    heif_error err = heif_image_create(w, h, heif_colorspace_RGB, heif_chroma_interleaved_RGB, &image);
    if (err.code == heif_error_Ok) err = heif_image_add_plane(image, heif_channel_interleaved, w, h, 8);
    if (err.code == heif_error_Ok) {
        int stride = 0;
        uint8_t* dst = heif_image_get_plane(image, heif_channel_interleaved, &stride);
        if (!dst || stride < w * 3) { heif_image_release(image); return false; }
        for (int y = 0; y < h; ++y)
            std::memcpy(dst + static_cast<size_t>(y) * stride,
                        rgb.data() + static_cast<size_t>(y) * w * 3u,
                        static_cast<size_t>(w) * 3u);
    }
    if (err.code != heif_error_Ok) { if (image) heif_image_release(image); return false; }
    *out = image; return true;
}

static bool iris26646FillMonoImage(const std::vector<uint8_t>& mono, int w, int h, heif_image** out) {
    if (!out || w <= 0 || h <= 0 || mono.size() != static_cast<size_t>(w) * h) return false;
    heif_image* image = nullptr;
    heif_error err = heif_image_create(w, h, heif_colorspace_monochrome, heif_chroma_monochrome, &image);
    if (err.code == heif_error_Ok) err = heif_image_add_plane(image, heif_channel_Y, w, h, 8);
    if (err.code == heif_error_Ok) {
        int stride = 0;
        uint8_t* dst = heif_image_get_plane(image, heif_channel_Y, &stride);
        if (!dst || stride < w) { heif_image_release(image); return false; }
        for (int y = 0; y < h; ++y)
            std::memcpy(dst + static_cast<size_t>(y) * stride,
                        mono.data() + static_cast<size_t>(y) * w,
                        static_cast<size_t>(w));
    }
    if (err.code != heif_error_Ok) { if (image) heif_image_release(image); return false; }
    *out = image; return true;
}


} // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeNative(
    JNIEnv* env, jclass, jobject baseBitmap, jobject gainmapBitmap, jstring outputPath, jint quality,
    jfloatArray ratioMin, jfloatArray ratioMax, jfloatArray gamma, jfloatArray epsilonSdr,
    jfloatArray epsilonHdr, jfloat minDisplayRatio, jfloat fullDisplayRatio,
    jstring iso, jstring fNumber, jstring focalLength, jstring exposureTime,
    jstring dateTime, jstring make, jstring model) {

    if (!env || !baseBitmap || !gainmapBitmap || !outputPath || !iris26636RegisterEncoder()) return JNI_FALSE;
    std::array<float,3> rmin{}, rmax{}, g{}, es{}, eh{};
    if (!iris26636GetFloat3(env, ratioMin, rmin) || !iris26636GetFloat3(env, ratioMax, rmax) ||
        !iris26636GetFloat3(env, gamma, g) || !iris26636GetFloat3(env, epsilonSdr, es) ||
        !iris26636GetFloat3(env, epsilonHdr, eh)) return JNI_FALSE;
    if (!(std::isfinite(minDisplayRatio) && std::isfinite(fullDisplayRatio) &&
          minDisplayRatio > 0.f && fullDisplayRatio >= minDisplayRatio)) return JNI_FALSE;

    const std::string path = iris26636JString(env, outputPath);
    if (path.empty()) return JNI_FALSE;

    heif_context* ctx = nullptr;
    heif_encoder* encoder = nullptr;
    heif_image* baseImage = nullptr;
    heif_image* gainImage = nullptr;
    heif_image_handle* baseHandle = nullptr;
    heif_image_handle* gainHandle = nullptr;
    heif_encoding_options* options = nullptr;
    heif_color_profile_nclx* baseNclx = nullptr;
    heif_color_profile_nclx* gainmapNclx = nullptr;
    heif_color_profile_nclx* alternateNclx = nullptr;
    bool ok = false;
    gIris26636Env = env;

    do {
        ctx = heif_context_alloc();
        if (!ctx) break;
        heif_error err = heif_context_get_encoder_for_format(ctx, heif_compression_HEVC, &encoder);
        if (err.code != heif_error_Ok || !encoder) break;
        if (heif_encoder_set_lossy_quality(encoder, std::clamp(static_cast<int>(quality), 1, 100)).code != heif_error_Ok) break;

        if (!iris26636FillBaseImage(env, baseBitmap, &baseImage)) break;
        options = heif_encoding_options_alloc();
        if (!options) break;
        baseNclx = heif_nclx_color_profile_alloc();
        if (!baseNclx) break;
        // IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_BASE_PUBLICATION
        // Keep Iris' completed Display-P3 SDR pixels byte-owned upstream, but publish their color
        // description the same way Google's libultrahdr v2.0.0 HEIF writer does: a Display-P3 ICC
        // profile in parallel with NCLX, BT.709 transfer signalling for UHDR_CT_SRGB, BT.601 matrix,
        // and full range. This is publication-only; no SDR pixels or gain values are recomputed.
        std::shared_ptr<ultrahdr::DataStruct> baseIcc =
                ultrahdr::IccHelper::writeIccProfile(UHDR_CT_SRGB, UHDR_CG_DISPLAY_P3);
        if (!baseIcc || baseIcc->getLength() <= ultrahdr::kICCIdentifierSize) break;
        uint8_t* baseIccBytes = static_cast<uint8_t*>(baseIcc->getData());
        if (!baseIccBytes || heif_image_set_raw_color_profile(
                baseImage, "prof", baseIccBytes + ultrahdr::kICCIdentifierSize,
                baseIcc->getLength() - ultrahdr::kICCIdentifierSize).code != heif_error_Ok) break;
        if (heif_nclx_color_profile_set_color_primaries(baseNclx, heif_color_primaries_SMPTE_EG_432_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(baseNclx, heif_transfer_characteristic_ITU_R_BT_709_5).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(baseNclx, heif_matrix_coefficients_ITU_R_BT_601_6).code != heif_error_Ok) break;
        baseNclx->full_range_flag = true;
        if (heif_image_set_nclx_color_profile(baseImage, baseNclx).code != heif_error_Ok) break;
        options->save_two_colr_boxes_when_ICC_and_nclx_available = 1;
        options->output_nclx_profile = baseNclx;
        if (heif_context_encode_image(ctx, baseImage, encoder, options, &baseHandle).code != heif_error_Ok || !baseHandle) break;

        const auto exifBytes = iris26636BuildExif(
            iris26636JString(env, iso), iris26636JString(env, fNumber),
            iris26636JString(env, focalLength), iris26636JString(env, exposureTime),
            iris26636JString(env, dateTime), iris26636JString(env, make), iris26636JString(env, model));
        if (exifBytes.size() > 12) {
            const heif_error exifErr = heif_context_add_exif_metadata(
                ctx, baseHandle, exifBytes.data(), static_cast<int>(exifBytes.size()));
            if (exifErr.code != heif_error_Ok) {
                IRIS26636_LOGE("Exif insertion failed but image encoding remains valid: %s",
                               exifErr.message ? exifErr.message : "unknown");
            }
        }

        if (!iris26636FillGainmapImage(env, gainmapBitmap, &gainImage)) break;
        // IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_GAINMAP_PUBLICATION
        // Google's v2 HEIF writer keeps monochrome gain-map primaries/transfer unspecified while
        // carrying the item through BT.601 matrix signalling. The stored Iris gain bytes and ISO
        // 21496 metadata remain exactly the upstream values.
        gainmapNclx = heif_nclx_color_profile_alloc();
        if (!gainmapNclx) break;
        if (heif_nclx_color_profile_set_color_primaries(
                    gainmapNclx, heif_color_primaries_unspecified).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(
                    gainmapNclx, heif_transfer_characteristic_unspecified).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(
                    gainmapNclx, heif_matrix_coefficients_ITU_R_BT_601_6).code != heif_error_Ok) break;
        gainmapNclx->full_range_flag = true;
        if (heif_image_set_nclx_color_profile(gainImage, gainmapNclx).code != heif_error_Ok) break;
        options->output_nclx_profile = gainmapNclx;

        ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);
        for (int c = 0; c < 3; ++c) {
            metadata.min_content_boost[c] = rmin[c];
            metadata.max_content_boost[c] = rmax[c];
            metadata.gamma[c] = g[c];
            metadata.offset_sdr[c] = es[c];
            metadata.offset_hdr[c] = eh[c];
        }
        metadata.hdr_capacity_min = minDisplayRatio;
        metadata.hdr_capacity_max = fullDisplayRatio;
        metadata.use_base_cg = 1;
        ultrahdr::uhdr_gainmap_metadata_frac frac{};
        std::vector<uint8_t> isoMetadata;
        auto st = ultrahdr::uhdr_gainmap_metadata_frac::gainmapMetadataFloatToFraction(&metadata, &frac);
        if (st.error_code != UHDR_CODEC_OK) break;
        st = ultrahdr::uhdr_gainmap_metadata_frac::encodeGainmapMetadata(&frac, isoMetadata);
        if (st.error_code != UHDR_CODEC_OK || isoMetadata.empty()) break;

        alternateNclx = heif_nclx_color_profile_alloc();
        if (!alternateNclx) break;
        // IRIS_26672_GOOGLE_LIBULTRAHDR_V2_TMAP_HDR_INTENT_AUTHORITY
        // libultrahdr v2 publishes tmap color properties from the HDR intent, not by re-labelling
        // the alternate rendition as SDR. Iris' matched HDR intent is extended-linear Display-P3,
        // so advertise P3 + linear transfer + the P3 chromaticity-derived matrix. This changes only
        // HEIF interpretation; gain-map math, capacity and pixels remain untouched.
        if (heif_nclx_color_profile_set_color_primaries(alternateNclx, heif_color_primaries_SMPTE_EG_432_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(alternateNclx, heif_transfer_characteristic_linear).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(alternateNclx, heif_matrix_coefficients_chromaticity_derived_non_constant_luminance).code != heif_error_Ok) break;
        alternateNclx->full_range_flag = true;

        // Keep the established Iris gain-map publication quality authority.
        if (heif_encoder_set_lossy_quality(encoder, 95).code != heif_error_Ok) break;
        if (heif_context_encode_gain_map_image(ctx, baseHandle, encoder, gainImage, options,
                isoMetadata.data(), static_cast<int>(isoMetadata.size()), alternateNclx,
                &gainHandle).code != heif_error_Ok || !gainHandle) break;

        Iris26636MemoryWriter memory;
        heif_writer writer{1, iris26636WriteCallback};
        if (heif_context_write(ctx, &writer, &memory).code != heif_error_Ok || memory.bytes.empty()) break;
        ok = iris26636WriteFile(path, memory.bytes);
        if (ok) IRIS26636_LOGI("IRIS_26672_HEIC_GOOGLE_V2_PUBLICATION hardwareHevc=true opaqueRgb=true baseP3Icc=true baseNclxP3Bt709TransferBt601Matrix=true tmapP3Linear=true gainmapUnspecifiedPrimariesTransferBt601Matrix=true gainmapVisible=true gainmapReused=true recomputedGainmap=false bytes=%zu", memory.bytes.size());
    } while (false);

    gIris26636Env = nullptr;
    if (gainHandle) heif_image_handle_release(gainHandle);
    if (baseHandle) heif_image_handle_release(baseHandle);
    if (gainImage) heif_image_release(gainImage);
    if (baseImage) heif_image_release(baseImage);
    if (alternateNclx) heif_nclx_color_profile_free(alternateNclx);
    if (gainmapNclx) heif_nclx_color_profile_free(gainmapNclx);
    if (baseNclx) heif_nclx_color_profile_free(baseNclx);
    if (options) heif_encoding_options_free(options);
    if (encoder) heif_encoder_release(encoder);
    if (ctx) heif_context_free(ctx);
    if (!ok) std::remove(path.c_str());
    return ok ? JNI_TRUE : JNI_FALSE;
}

/* IRIS_26646_TRUE2X_HEIC_GRID_OWNER
 * Proper Super-Res HEIC publication: preserve the proven true-2x rendered SDR pixels, encode the
 * 50MP-class primary as a 2x2 HEIF grid of hardware-HEVC tiles, reduce only the logarithmic gain
 * carrier to half-linear resolution, and attach the same ISO 21496 metadata/tmap relationship.
 * No scene reconstruction, tone adjustment, hue reconstruction or 12MP fallback occurs here. */
extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeSuperResGridNative(
    JNIEnv* env, jclass, jstring baseJpegPath, jstring gainJpegPath,
    jint imageWidth, jint imageHeight, jstring outputPath, jint quality,
    jfloatArray ratioMin, jfloatArray ratioMax, jfloatArray gamma, jfloatArray epsilonSdr,
    jfloatArray epsilonHdr, jfloat minDisplayRatio, jfloat fullDisplayRatio,
    jstring iso, jstring fNumber, jstring focalLength, jstring exposureTime,
    jstring dateTime, jstring make, jstring model) {

    if (!env || !baseJpegPath || !gainJpegPath || !outputPath || !iris26636RegisterEncoder()) return JNI_FALSE;
    const int fullW = static_cast<int>(imageWidth);
    const int fullH = static_cast<int>(imageHeight);
    if (fullW <= 0 || fullH <= 0 || (fullW & 3) || (fullH & 3)) return JNI_FALSE;
    const int tileW = fullW / 2;
    const int tileH = fullH / 2;
    if ((tileW & 1) || (tileH & 1)) return JNI_FALSE;

    std::array<float,3> rmin{}, rmax{}, g{}, es{}, eh{};
    if (!iris26636GetFloat3(env, ratioMin, rmin) || !iris26636GetFloat3(env, ratioMax, rmax) ||
        !iris26636GetFloat3(env, gamma, g) || !iris26636GetFloat3(env, epsilonSdr, es) ||
        !iris26636GetFloat3(env, epsilonHdr, eh)) return JNI_FALSE;
    if (!(std::isfinite(minDisplayRatio) && std::isfinite(fullDisplayRatio) &&
          minDisplayRatio > 0.f && fullDisplayRatio >= minDisplayRatio)) return JNI_FALSE;

    const std::string basePath = iris26636JString(env, baseJpegPath);
    const std::string gainPath = iris26636JString(env, gainJpegPath);
    const std::string path = iris26636JString(env, outputPath);
    if (basePath.empty() || gainPath.empty() || path.empty()) return JNI_FALSE;

    heif_context* ctx = nullptr;
    heif_encoder* encoder = nullptr;
    heif_image_handle* baseHandle = nullptr;
    heif_image_handle* gainHandle = nullptr;
    heif_image* gainImage = nullptr;
    heif_encoding_options* options = nullptr;
    heif_color_profile_nclx* baseNclx = nullptr;
    heif_color_profile_nclx* gainmapNclx = nullptr;
    heif_color_profile_nclx* alternateNclx = nullptr;
    bool ok = false;
    gIris26636Env = env;

    do {
        ctx = heif_context_alloc();
        if (!ctx) break;
        heif_error err = heif_context_get_encoder_for_format(ctx, heif_compression_HEVC, &encoder);
        if (err.code != heif_error_Ok || !encoder) break;
        if (heif_encoder_set_lossy_quality(encoder, std::clamp(static_cast<int>(quality), 1, 100)).code != heif_error_Ok) break;

        options = heif_encoding_options_alloc();
        if (!options) break;
        baseNclx = heif_nclx_color_profile_alloc();
        if (!baseNclx) break;
        if (heif_nclx_color_profile_set_color_primaries(baseNclx, heif_color_primaries_SMPTE_EG_432_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(baseNclx, heif_transfer_characteristic_IEC_61966_2_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(baseNclx, heif_matrix_coefficients_ITU_R_BT_601_6).code != heif_error_Ok) break;
        baseNclx->full_range_flag = true;
        options->save_two_colr_boxes_when_ICC_and_nclx_available = 0;
        options->output_nclx_profile = baseNclx;

        err = heif_context_add_grid_image(ctx, static_cast<uint32_t>(fullW), static_cast<uint32_t>(fullH),
                                          2u, 2u, options, &baseHandle);
        if (err.code != heif_error_Ok || !baseHandle) {
            IRIS26636_LOGE("IRIS_26646 grid create failed: %s", err.message ? err.message : "unknown");
            break;
        }
        if (heif_context_set_primary_image(ctx, baseHandle).code != heif_error_Ok) break;

        bool tilesOk = true;
        for (int ty = 0; ty < 2 && tilesOk; ++ty) {
            for (int tx = 0; tx < 2 && tilesOk; ++tx) {
                std::vector<uint8_t> rgb;
                if (!iris26646DecodeJpegRegionRgb(basePath, fullW, fullH,
                                                   tx * tileW, ty * tileH, tileW, tileH, &rgb)) {
                    IRIS26636_LOGE("IRIS_26646 base tile decode failed tile=%d,%d", tx, ty);
                    tilesOk = false;
                    break;
                }
                heif_image* tileImage = nullptr;
                if (!iris26646FillRgbImage(rgb, tileW, tileH, &tileImage) || !tileImage) {
                    tilesOk = false;
                    break;
                }
                if (heif_image_set_nclx_color_profile(tileImage, baseNclx).code != heif_error_Ok) {
                    heif_image_release(tileImage);
                    tilesOk = false;
                    break;
                }
                const heif_error tileErr = heif_context_add_image_tile(
                        ctx, baseHandle, static_cast<uint32_t>(tx), static_cast<uint32_t>(ty), tileImage, encoder);
                heif_image_release(tileImage);
                if (tileErr.code != heif_error_Ok) {
                    IRIS26636_LOGE("IRIS_26646 base tile encode failed tile=%d,%d error=%s",
                                   tx, ty, tileErr.message ? tileErr.message : "unknown");
                    tilesOk = false;
                    break;
                }
            }
        }
        if (!tilesOk) break;

        const auto exifBytes = iris26636BuildExif(
            iris26636JString(env, iso), iris26636JString(env, fNumber),
            iris26636JString(env, focalLength), iris26636JString(env, exposureTime),
            iris26636JString(env, dateTime), iris26636JString(env, make), iris26636JString(env, model));
        if (exifBytes.size() > 12) {
            const heif_error exifErr = heif_context_add_exif_metadata(
                    ctx, baseHandle, exifBytes.data(), static_cast<int>(exifBytes.size()));
            if (exifErr.code != heif_error_Ok) {
                IRIS26636_LOGE("IRIS_26646 grid Exif insertion nonfatal: %s",
                               exifErr.message ? exifErr.message : "unknown");
            }
        }

        std::vector<uint8_t> halfGain;
        int gainW = 0, gainH = 0;
        if (!iris26646DecodeGainHalf(gainPath, fullW, fullH, &halfGain, &gainW, &gainH)
                || gainW != fullW / 2 || gainH != fullH / 2) break;
        if (!iris26646FillMonoImage(halfGain, gainW, gainH, &gainImage) || !gainImage) break;

        gainmapNclx = heif_nclx_color_profile_alloc();
        if (!gainmapNclx) break;
        if (heif_nclx_color_profile_set_color_primaries(gainmapNclx, heif_color_primaries_unspecified).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(gainmapNclx, heif_transfer_characteristic_unspecified).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(gainmapNclx, heif_matrix_coefficients_unspecified).code != heif_error_Ok) break;
        gainmapNclx->full_range_flag = true;
        if (heif_image_set_nclx_color_profile(gainImage, gainmapNclx).code != heif_error_Ok) break;
        options->output_nclx_profile = gainmapNclx;

        ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);
        for (int c = 0; c < 3; ++c) {
            metadata.min_content_boost[c] = rmin[c];
            metadata.max_content_boost[c] = rmax[c];
            metadata.gamma[c] = g[c];
            metadata.offset_sdr[c] = es[c];
            metadata.offset_hdr[c] = eh[c];
        }
        metadata.hdr_capacity_min = minDisplayRatio;
        metadata.hdr_capacity_max = fullDisplayRatio;
        metadata.use_base_cg = 1;
        ultrahdr::uhdr_gainmap_metadata_frac frac{};
        std::vector<uint8_t> isoMetadata;
        auto st = ultrahdr::uhdr_gainmap_metadata_frac::gainmapMetadataFloatToFraction(&metadata, &frac);
        if (st.error_code != UHDR_CODEC_OK) break;
        st = ultrahdr::uhdr_gainmap_metadata_frac::encodeGainmapMetadata(&frac, isoMetadata);
        if (st.error_code != UHDR_CODEC_OK || isoMetadata.empty()) break;

        alternateNclx = heif_nclx_color_profile_alloc();
        if (!alternateNclx) break;
        if (heif_nclx_color_profile_set_color_primaries(alternateNclx, heif_color_primaries_SMPTE_EG_432_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_transfer_characteristics(alternateNclx, heif_transfer_characteristic_IEC_61966_2_1).code != heif_error_Ok ||
            heif_nclx_color_profile_set_matrix_coefficients(alternateNclx, heif_matrix_coefficients_ITU_R_BT_601_6).code != heif_error_Ok) break;
        alternateNclx->full_range_flag = true;

        if (heif_encoder_set_lossy_quality(encoder, 95).code != heif_error_Ok) break;
        if (heif_context_encode_gain_map_image(ctx, baseHandle, encoder, gainImage, options,
                isoMetadata.data(), static_cast<int>(isoMetadata.size()), alternateNclx,
                &gainHandle).code != heif_error_Ok || !gainHandle) break;

        Iris26636MemoryWriter memory;
        heif_writer writer{1, iris26636WriteCallback};
        if (heif_context_write(ctx, &writer, &memory).code != heif_error_Ok || memory.bytes.empty()) break;
        ok = iris26636WriteFile(path, memory.bytes);
        if (ok) {
            IRIS26636_LOGI("IRIS_26646_TRUE2X_HEIC_GRID hardwareHevc=true grid=2x2 base=%dx%d tile=%dx%d gain=%dx%d halfLinearGain=true iso21496=true bytes=%zu",
                           fullW, fullH, tileW, tileH, gainW, gainH, memory.bytes.size());
        }
    } while (false);

    gIris26636Env = nullptr;
    if (gainHandle) heif_image_handle_release(gainHandle);
    if (baseHandle) heif_image_handle_release(baseHandle);
    if (gainImage) heif_image_release(gainImage);
    if (alternateNclx) heif_nclx_color_profile_free(alternateNclx);
    if (gainmapNclx) heif_nclx_color_profile_free(gainmapNclx);
    if (baseNclx) heif_nclx_color_profile_free(baseNclx);
    if (options) heif_encoding_options_free(options);
    if (encoder) heif_encoder_release(encoder);
    if (ctx) heif_context_free(ctx);
    if (!ok) std::remove(path.c_str());
    return ok ? JNI_TRUE : JNI_FALSE;
}
