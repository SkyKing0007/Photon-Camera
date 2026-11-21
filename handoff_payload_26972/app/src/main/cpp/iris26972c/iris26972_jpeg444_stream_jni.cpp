#include "iris26972_jpeg444.h"

#include <jni.h>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace {
struct BandContext {
    JNIEnv* env;
    jobject source;
    jmethodID method;
};

bool AskJavaForFinalizedBand(int top, int rows, uint8_t* rgba, int stride,
                             void* context) {
    auto* caller=static_cast<BandContext*>(context);
    if (!caller || rows <= 0 || stride <= 0 ||
        rows > std::numeric_limits<jlong>::max() / stride) return false;
    jobject direct=caller->env->NewDirectByteBuffer(
        rgba, static_cast<jlong>(rows)*stride);
    if (!direct || caller->env->ExceptionCheck()) return false;
    // Callback must provide POST-GENUINE-RAISR, finalized sRGB pixels. It is
    // called synchronously on the C producer thread; no Java object escapes.
    const jboolean ok=caller->env->CallBooleanMethod(
        caller->source,caller->method,top,rows,direct,stride);
    const bool success=(ok==JNI_TRUE && !caller->env->ExceptionCheck());
    caller->env->DeleteLocalRef(direct);
    return success;
}
} // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CJpeg444_writeBandsNative(
        JNIEnv* env, jclass, jint width, jint height, jint rowsPerBand,
        jobject source, jstring path, jbyteArray icc) {
    if (!source || !path || width<=0 || height<=0 ||
        rowsPerBand<1 || rowsPerBand>256) return JNI_FALSE;
    jclass clazz=env->GetObjectClass(source);
    if (!clazz || env->ExceptionCheck()) return JNI_FALSE;
    jmethodID fill=env->GetMethodID(
        clazz,"fillBand","(IILjava/nio/ByteBuffer;I)Z");
    env->DeleteLocalRef(clazz);
    if (!fill || env->ExceptionCheck()) return JNI_FALSE;
    std::vector<uint8_t> iccBytes;
    if (icc) {
        const jsize count=env->GetArrayLength(icc);
        if(count<1 || count>4*1024*1024) return JNI_FALSE;
        try { iccBytes.resize(static_cast<size_t>(count)); }
        catch (...) { return JNI_FALSE; }
        env->GetByteArrayRegion(icc,0,count,
            reinterpret_cast<jbyte*>(iccBytes.data()));
        if(env->ExceptionCheck()) return JNI_FALSE;
    }
    const char* destination=env->GetStringUTFChars(path,nullptr);
    if(!destination || env->ExceptionCheck())return JNI_FALSE;
    BandContext context{env,source,fill};
    const iris26972c::Jpeg444BandInput params{
        width,height,rowsPerBand,AskJavaForFinalizedBand,&context,
        iccBytes.empty()?nullptr:iccBytes.data(),iccBytes.size(),
    };
    const bool okay=iris26972c::EncodeJpeg444Native1xFromBands(params,destination);
    env->ReleaseStringUTFChars(path,destination);
    return okay ? JNI_TRUE : JNI_FALSE;
}
