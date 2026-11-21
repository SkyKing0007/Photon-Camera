#include "iris26972_jpegr.h"

#include <jni.h>

#include <array>
#include <cstdint>

namespace {
struct Utf {
    JNIEnv* env;
    jstring source;
    const char* data;
    Utf(JNIEnv* e, jstring s): env(e), source(s),
        data(s ? e->GetStringUTFChars(s, nullptr) : nullptr) {}
    ~Utf() { if (data) env->ReleaseStringUTFChars(source, data); }
    Utf(const Utf&) = delete;
    Utf& operator=(const Utf&) = delete;
};

bool Get3(JNIEnv* env, jfloatArray array, float output[3]) {
    if (!array || env->GetArrayLength(array) != 3) return false;
    env->GetFloatArrayRegion(array, 0, 3, output);
    return !env->ExceptionCheck();
}
}  // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CUltraHdr_packageNative(
        JNIEnv* env, jclass, jstring baseJpeg, jstring gainJpeg, jstring outputJpegR,
        jfloatArray minBoost, jfloatArray maxBoost, jfloatArray gamma,
        jfloatArray offsetSdr, jfloatArray offsetHdr,
        jfloat capacityMin, jfloat capacityMax, jboolean useBaseColorSpace,
        jint baseGamut) {
    Utf base(env, baseJpeg), gain(env, gainJpeg), output(env, outputJpegR);
    if (!base.data || !gain.data || !output.data) return JNI_FALSE;
    iris26972c::JpegRGainmapMetadata m{};
    if (!Get3(env, minBoost, m.minContentBoost) ||
        !Get3(env, maxBoost, m.maxContentBoost) ||
        !Get3(env, gamma, m.gamma) ||
        !Get3(env, offsetSdr, m.offsetSdr) ||
        !Get3(env, offsetHdr, m.offsetHdr)) return JNI_FALSE;
    m.capacityMin = capacityMin;
    m.capacityMax = capacityMax;
    m.useBaseColorSpace = useBaseColorSpace == JNI_TRUE;
    m.baseColorGamut = baseGamut;
    return iris26972c::PublishJpegRFromEncodedJpegs(
        base.data, gain.data, output.data, m) ? JNI_TRUE : JNI_FALSE;
}
