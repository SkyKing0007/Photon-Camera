package com.hinnka.mycamera.processor;

import android.content.Context;
import android.content.res.AssetManager;

/**
 * IRIS_26856_B_ONLY_NATIVE_AMAZE_GL_VK_ENTRY.
 * Exact RAWR 19-pass AMaZE on a current GLES context. This is never a Photon
 * fallback. The caller owns both RGBA16F textures and their release; input
 * is packed canonical Bayer at half native dimensions, output is full-size
 * camera-linear RGB. Pixel contents are not copied through the CPU.
 *
 * The full B producer/SHORT/HDR/JPEG return path must be present before this
 * method can be activated by the high-level Experiment B selection.
 */
public final class GlesIris26856AmazeNative {
    private GlesIris26856AmazeNative() {}
    static { System.loadLibrary("iris26856amaze"); }

    public static void execute(Context context, int packedCfaTexture,
                               int outputLinearRgbTexture, int rawWidth, int rawHeight,
                               int bayerPattern, float[] whiteBalance) {
        if (context == null || packedCfaTexture == 0 || outputLinearRgbTexture == 0
                || packedCfaTexture == outputLinearRgbTexture
                || rawWidth < 32 || rawHeight < 32 || (rawWidth & 1) != 0
                || (rawHeight & 1) != 0 || bayerPattern < 0 || bayerPattern > 3
                || whiteBalance == null || whiteBalance.length != 3) {
            throw new IllegalArgumentException("26856 AMaZE JNI requires exact CFA/RGB input and Bayer domain");
        }
        for (float gain : whiteBalance) {
            if (!(gain > 0.0f) || !Float.isFinite(gain))
                throw new IllegalArgumentException("26856 invalid AMaZE white balance");
        }
        nativeExecute(context.getAssets(), packedCfaTexture, outputLinearRgbTexture,
                rawWidth, rawHeight, bayerPattern, whiteBalance);
    }

    private static native void nativeExecute(AssetManager assets, int packedCfaTexture,
                                              int outputLinearRgbTexture, int rawWidth,
                                              int rawHeight, int bayerPattern,
                                              float[] whiteBalance);
}
