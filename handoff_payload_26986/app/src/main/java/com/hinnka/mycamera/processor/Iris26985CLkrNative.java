// SPDX-License-Identifier: Apache-2.0
package com.hinnka.mycamera.processor;
import java.nio.ByteBuffer;
/** Experiment C only. RawLens 2.4.20 pinned JNI, privately linked SRP and TinyDNG. */
public final class Iris26985CLkrNative {
    private Iris26985CLkrNative() {}
    static { System.loadLibrary("iris26985clkr2420"); }
    public static native double nativeSharpness(ByteBuffer raw,int width,int height,int rowStridePx,int[] cfa,float[] black);
    public static native ByteBuffer nativeMerge(ByteBuffer[] frames,int width,int height,int rowStridePx,int[] cfa,float[] black,float white,float[] wb,int scale,int tile,int overlap,int[] crop,boolean dctPrior,float[] stats,float[] tuning,int outW,int outH);
    public static native ByteBuffer nativeStage(ByteBuffer src,int w,int h,int stridePx,int bits);
    public static native ByteBuffer nativeMergeStaged(ByteBuffer[] frames,int width,int height,int packedBits,int[] cfa,float[] black,float white,float[] wb,int scale,int tile,int overlap,int[] crop,boolean dctPrior,float[] stats,float[] tuning,int outW,int outH);
    public static native String nativeLastProfile();
    public static native void nativeSetCacheDir(String dir);
    public static native void nativeSetNoiseModel(String path,float iso);
    public static native float[] nativeTuningDefaults();
    public static native int nativeAutoTileSize(int width,int height,int scale);
    public static native void nativeSetExposures(float[] exposures);
    public static native void nativeSetPrior(boolean enabled);
    public static native long nativePrewarm(String dir);
    public static native void nativeFree(ByteBuffer buffer);
}
