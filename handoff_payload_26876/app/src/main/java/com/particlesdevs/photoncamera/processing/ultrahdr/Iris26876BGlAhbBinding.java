package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.hardware.HardwareBuffer;

/**
 * IRIS_26876_B_AHB_EGLIMAGE_SINGLE_CONTEXT_OWNER
 * Only usable with a current GLES3.1 context. Native resources and the
 * EGLImage MUST be destroyed before that context or its display is released.
 * A failed import aborts B; it never silently copies from an RGB16F file.
 */
final class Iris26876BGlAhbBinding implements AutoCloseable {
    static { System.loadLibrary("motionv2jpeg"); }
    private long handle;
    private Iris26876BGlAhbBinding(long h) { handle = h; }

    static Iris26876BGlAhbBinding bind(HardwareBuffer source, int w, int h,
                                      boolean rgba8FinalOutput) {
        if (source == null || w <= 0 || h <= 0) return null;
        long hnd = bindNative(source, w, h, rgba8FinalOutput);
        return hnd == 0L ? null : new Iris26876BGlAhbBinding(hnd);
    }

    int textureId() { return handle == 0L ? 0 : textureNative(handle); }

    @Override public void close() {
        long h = handle;
        handle = 0L;
        if (h != 0L) releaseNative(h);
    }

    private static native long bindNative(HardwareBuffer source, int w, int h,
                                          boolean rgba8FinalOutput);
    private static native int textureNative(long handle);
    private static native void releaseNative(long handle);
}
