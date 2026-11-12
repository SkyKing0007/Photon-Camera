package com.hinnka.mycamera.processor;

/** Experiment B Super Res ON only, synchronous same-thread Vulkan dispatch arm. */
public final class Iris26920NativeProbe {
    private Iris26920NativeProbe() { }
    static { System.loadLibrary("iris26856amaze"); }
    /** Must be paired with finally { clear(); }; no whole-merge fallback when ON. */
    public static void arm(boolean enabled, long lensIdentity, long referenceTimestamp) {
        nativeArm(enabled, lensIdentity, referenceTimestamp);
    }
    public static void clear() { nativeClear(); }
    public static String takeLastReport() { return nativeTakeLastReport(); }
    private static native void nativeArm(boolean enabled, long lensIdentity, long referenceTimestamp);
    private static native void nativeClear();
    private static native String nativeTakeLastReport();
}
