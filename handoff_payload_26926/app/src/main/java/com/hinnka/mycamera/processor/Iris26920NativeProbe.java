package com.hinnka.mycamera.processor;

/** Experiment B Super Res ON only, synchronous same-thread Vulkan dispatch arm. */
public final class Iris26920NativeProbe {
    private Iris26920NativeProbe() { }
    static { System.loadLibrary("iris26856amaze"); }
    /** Must be paired with finally { clear(); }; no whole-merge fallback when ON. */
    public static void arm(boolean enabled, long lensIdentity, long referenceTimestamp, float[] fallback) {
        if (fallback == null || fallback.length != 3)
            throw new IllegalArgumentException("26926 missing frozen fallback triple");
        nativeArm(enabled, lensIdentity, referenceTimestamp, fallback);
    }
    public static void clear() { nativeClear(); }
    public static String takeLastReport() { return nativeTakeLastReport(); }
    /** One-shot source, actual contributing NORMAL count, four CFA-site (shot,read) pairs.
     * [0]=0 RAW burst,1 custom .c; [1]=frame count; [2..9] = shot/read x4. */
    public static float[] takeLastNoise() { return nativeTakeLastNoise(); }
    private static native float[] nativeTakeLastNoise();
    private static native void nativeArm(boolean enabled, long lensIdentity,
                                         long referenceTimestamp, float[] fallback);
    private static native void nativeClear();
    private static native String nativeTakeLastReport();
}
