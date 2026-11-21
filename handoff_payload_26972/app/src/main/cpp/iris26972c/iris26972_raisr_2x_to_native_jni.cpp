#include "iris26972_raisr_2x_to_native.h"
#include <jni.h>
#include <cstdint>
#include <limits>

// Private 26972 C JNI symbol, not loaded by any A/B owner.
extern "C" JNIEXPORT jboolean JNICALL
Java_com_particlesdevs_photoncamera_processing_experimentc_Iris26972CNativeDownsample_downsampleNative(
        JNIEnv* env, jclass, jobject input, jint tileWidth, jint tileHeight,
        jint tileStride, jint tileX, jint tileY, jint fullWidth, jint fullHeight,
        jint outputX, jint outputY, jint outputWidth, jint outputHeight,
        jobject output, jint outputStride) {
    if (env == nullptr || input == nullptr || output == nullptr ||
        tileWidth <= 0 || tileHeight <= 0 || outputWidth <= 0 || outputHeight <= 0 ||
        tileStride <= 0 || outputStride <= 0 || fullWidth <= 0 || fullHeight <= 0) {
        return JNI_FALSE;
    }
    const auto inputCapacity = env->GetDirectBufferCapacity(input);
    const auto outputCapacity = env->GetDirectBufferCapacity(output);
    const auto* inputPixels = static_cast<const uint8_t*>(env->GetDirectBufferAddress(input));
    auto* outputPixels = static_cast<uint8_t*>(env->GetDirectBufferAddress(output));
    if (inputCapacity < 0 || outputCapacity < 0 || inputPixels == nullptr || outputPixels == nullptr ||
        inputPixels == outputPixels || tileWidth > std::numeric_limits<jint>::max() / 4 ||
        outputWidth > std::numeric_limits<jint>::max() / 4 ||
        tileStride < tileWidth * 4 || outputStride < outputWidth * 4) {
        return JNI_FALSE;
    }
    const auto inputNeeded = static_cast<int64_t>(tileHeight - 1) * tileStride +
            static_cast<int64_t>(tileWidth) * 4;
    const auto outputNeeded = static_cast<int64_t>(outputHeight - 1) * outputStride +
            static_cast<int64_t>(outputWidth) * 4;
    if (inputNeeded <= 0 || outputNeeded <= 0 ||
        inputNeeded > inputCapacity || outputNeeded > outputCapacity) return JNI_FALSE;
    // Do not allow overlap between two distinct direct-buffer views of one allocation.
    const auto inputBegin = reinterpret_cast<uintptr_t>(inputPixels);
    const auto outputBegin = reinterpret_cast<uintptr_t>(outputPixels);
    if (inputBegin <= outputBegin && static_cast<uint64_t>(outputBegin - inputBegin) <
                                       static_cast<uint64_t>(inputNeeded)) return JNI_FALSE;
    if (outputBegin < inputBegin && static_cast<uint64_t>(inputBegin - outputBegin) <
                                       static_cast<uint64_t>(outputNeeded)) return JNI_FALSE;
    iris26972c::Raisr2xTile tile{
        inputPixels, tileWidth, tileHeight, tileStride,
        tileX, tileY, fullWidth, fullHeight
    };
    return iris26972c::downsampleRaisr2xToNative(
            tile, outputX, outputY, outputWidth, outputHeight,
            outputPixels, outputStride) ? JNI_TRUE : JNI_FALSE;
}
