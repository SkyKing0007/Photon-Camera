// SPDX-License-Identifier: Apache-2.0
// IRIS_26931_PINNED_ORIGINAL_RAWLENS_2_2_86_BINARY_JNI_ABI
// The Java signature matches the published liblkrpipeline.so exactly.
// This is an Iris-owned JNI adapter, not a copy of RawLens GPL app code.
package com.matthew.rawlens;

import java.nio.ByteBuffer;

public final class LkrBridge {
    private LkrBridge() {}
    static {
        System.loadLibrary("srpipeline");
        System.loadLibrary("lkrpipeline");
    }
    public static native double nativeSharpness(ByteBuffer raw, int width, int height,
        int rowStridePx, int[] cfa, float[] phaseBlack);
    public static native ByteBuffer nativeMerge(
        ByteBuffer[] frames, int width, int height, int rowStridePx,
        int[] cfa, float[] black, float white, float[] wb,
        int scale, int tile, int overlap, int[] crop,
        boolean dctPrior, float[] stats, float[] tuning, int outW, int outH);
    public static native void nativeSetCacheDir(String cacheDir);
    public static native void nativeSetNoiseModel(String modelPath, float iso);
    public static native float[] nativeTuningDefaults();
}
