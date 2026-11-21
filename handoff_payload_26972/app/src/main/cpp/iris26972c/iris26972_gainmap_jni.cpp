#include "iris26972_gainmap.h"

#include <jni.h>
#include <cstddef>
#include <cstdint>

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CGainmap_writeTileNative(
        JNIEnv* env, jclass,
        jobject sdrRGBA, jobject hdrLinearRgb, jobject gainmapGray,
        jint fullWidth, jint fullHeight, jint left, jint top,
        jint width, jint height, jint sdrStride, jint hdrStride,
        jint gainStride, jfloat strength) {
    auto* sdr = static_cast<const uint8_t*>(env->GetDirectBufferAddress(sdrRGBA));
    auto* hdr = static_cast<const float*>(env->GetDirectBufferAddress(hdrLinearRgb));
    auto* out = static_cast<uint8_t*>(env->GetDirectBufferAddress(gainmapGray));
    const jlong sdrCapacity = env->GetDirectBufferCapacity(sdrRGBA);
    const jlong hdrCapacity = env->GetDirectBufferCapacity(hdrLinearRgb);
    const jlong outCapacity = env->GetDirectBufferCapacity(gainmapGray);
    if (!sdr || !hdr || !out || sdrCapacity < 0 || hdrCapacity < 0 || outCapacity < 0)
        return JNI_FALSE;
    const iris26972c::GainmapTile tile{
        sdr, hdr, static_cast<size_t>(sdrCapacity), static_cast<size_t>(hdrCapacity),
        sdrStride, hdrStride, fullWidth, fullHeight, left, top, width, height,
    };
    return iris26972c::WriteGainmapTile(
        tile, out, static_cast<size_t>(outCapacity), gainStride, strength) ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CGainmap_encodeJpegNative(
        JNIEnv* env, jclass, jobject gray, jint width, jint height,
        jint stride, jstring path) {
    if (!gray || !path) return JNI_FALSE;
    auto* bytes = static_cast<const uint8_t*>(env->GetDirectBufferAddress(gray));
    const jlong cap = env->GetDirectBufferCapacity(gray);
    if (!bytes || cap < 0) return JNI_FALSE;
    const char* p = env->GetStringUTFChars(path, nullptr);
    if (!p) return JNI_FALSE;
    const bool ok = iris26972c::WriteGainmapJpeg(bytes, static_cast<size_t>(cap),
                                                   width, height, stride, p);
    env->ReleaseStringUTFChars(path, p);
    return ok ? JNI_TRUE : JNI_FALSE;
}
