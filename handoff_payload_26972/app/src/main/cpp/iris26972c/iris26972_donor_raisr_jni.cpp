#include "iris26972_donor_raisr.h"
#include <jni.h>
#include <cstdint>

extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CActualRaisr_processNative(
        JNIEnv* env, jclass, jobject encodedInput, jint nativeWidth,
        jint nativeHeight, jint sourceLeft, jint sourceTop, jint sourceWidth,
        jint sourceHeight, jint sourceStride, jint coreLeft, jint coreTop,
        jint coreWidth, jint coreHeight, jobject nativeOutput, jint outputStride) {
    if (!encodedInput || !nativeOutput) return JNI_FALSE;
    const auto inputCapacity=env->GetDirectBufferCapacity(encodedInput);
    const auto outputCapacity=env->GetDirectBufferCapacity(nativeOutput);
    auto* input=static_cast<const float*>(env->GetDirectBufferAddress(encodedInput));
    auto* output=static_cast<uint8_t*>(env->GetDirectBufferAddress(nativeOutput));
    if (!input || !output || inputCapacity < 0 || outputCapacity < 0) return JNI_FALSE;
    const iris26972c::DonorRaisrTile tile{input,static_cast<size_t>(inputCapacity),
        sourceStride,sourceLeft,sourceTop,sourceWidth,sourceHeight,nativeWidth,
        nativeHeight,coreLeft,coreTop,coreWidth,coreHeight};
    return iris26972c::ProcessRealDonorRaisrTile(tile,output,
        static_cast<size_t>(outputCapacity),outputStride) ? JNI_TRUE : JNI_FALSE;
}
