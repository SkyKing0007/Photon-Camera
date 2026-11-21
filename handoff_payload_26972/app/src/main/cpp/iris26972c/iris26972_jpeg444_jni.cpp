#include "iris26972_jpeg444.h"

#include <jni.h>
#include <cstdint>
#include <limits>
#include <vector>

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CJpeg444_writeNative(
        JNIEnv* env, jclass, jobject rgba, jint width, jint height,
        jint stride, jstring outputPath, jbyteArray iccProfile) {
    if (!rgba || !outputPath) return JNI_FALSE;
    const jlong length = env->GetDirectBufferCapacity(rgba);
    auto* pixels = static_cast<uint8_t*>(env->GetDirectBufferAddress(rgba));
    if (!pixels || length < 0) return JNI_FALSE;
    const char* path = env->GetStringUTFChars(outputPath, nullptr);
    if (!path) return JNI_FALSE;
    std::vector<uint8_t> icc;
    if (iccProfile) {
        const jsize size = env->GetArrayLength(iccProfile);
        if (size <= 0 || size > 4 * 1024 * 1024) {
            env->ReleaseStringUTFChars(outputPath, path);
            return JNI_FALSE;
        }
        icc.resize(static_cast<size_t>(size));
        env->GetByteArrayRegion(iccProfile, 0, size,
                                reinterpret_cast<jbyte*>(icc.data()));
        if (env->ExceptionCheck()) {
            env->ReleaseStringUTFChars(outputPath, path);
            return JNI_FALSE;
        }
    }
    const iris26972c::Jpeg444Input input{
        pixels, static_cast<size_t>(length), width, height, stride,
        icc.empty() ? nullptr : icc.data(), icc.size()
    };
    const bool result = iris26972c::EncodeJpeg444Native1x(input, path);
    env->ReleaseStringUTFChars(outputPath, path);
    return result ? JNI_TRUE : JNI_FALSE;
}
