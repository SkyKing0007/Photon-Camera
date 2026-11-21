package com.particlesdevs.photoncamera.processing.experimentc;

import java.nio.ByteBuffer;

/**
 * C-only genuine bjzhou 1.29.0 RAISR AOT, then native 1x anti-aliased transfer.
 * The pinned ARM64 Actions binary supplies actual learned filters and five AOT
 * kernels; never uses a synthetic or alternate RAISR implementation.
 *
 * The source buffer is genuine FINALIZED sRGB float RGBA, in a bounded ROI
 * with donor-16px and decimator-3px halos; not linear RAW or untonemapped RGB.
 * The output is caller-owned native-size RGBA8 for a max 256x256 core.
 * Fail closed on 32-bit/unsupported devices and when the sidecar is unavailable.
 */
public final class Iris26972CActualRaisr {
    public static final int DONOR_HALO_NATIVE = 16;
    public static final int FINAL_DECIMATION_HALO_NATIVE = 3;
    public static final int MAX_CORE_SIZE = 256;
    private Iris26972CActualRaisr() {}
    static { System.loadLibrary("iris26972c"); }

    public static boolean render(ByteBuffer sourceEncodedSrgbRgbaF32,
                                 int nativeWidth, int nativeHeight,
                                 int sourceGlobalLeft, int sourceGlobalTop,
                                 int sourceWidth, int sourceHeight, int sourceStrideBytes,
                                 int coreLeft, int coreTop, int coreWidth, int coreHeight,
                                 ByteBuffer nativeRgbaOutput, int outputStrideBytes) {
        if (sourceEncodedSrgbRgbaF32 == null || nativeRgbaOutput == null ||
            !sourceEncodedSrgbRgbaF32.isDirect() || !nativeRgbaOutput.isDirect() ||
            nativeRgbaOutput.isReadOnly()) return false;
        // All geometry, source halo and color-domain validation is duplicated
        // in C++ before the first donor/GL allocation or output write.
        return processNative(sourceEncodedSrgbRgbaF32, nativeWidth, nativeHeight,
            sourceGlobalLeft,sourceGlobalTop,sourceWidth,sourceHeight,sourceStrideBytes,
            coreLeft,coreTop,coreWidth,coreHeight,nativeRgbaOutput,outputStrideBytes);
    }

    private static native boolean processNative(ByteBuffer encodedInput,
        int nativeWidth, int nativeHeight, int sourceLeft, int sourceTop,
        int sourceWidth, int sourceHeight, int sourceStride, int coreLeft,
        int coreTop, int coreWidth, int coreHeight, ByteBuffer nativeOutput,
        int outputStride);
}
