package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import java.nio.ByteBuffer;

/** IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP
 * Native byte traversal only. Java still owns the exact 256-entry exp/log/round LUT, so gain-map
 * math and stored codes are unchanged; this removes multi-million-element Java boxing/copies.
 */
final class MotionV2GainMapNative {
    static { System.loadLibrary("motionv2jpeg"); }

    static final class Scan {
        final int nonUnity;
        final int peakCode;
        Scan(int nonUnity, int peakCode) { this.nonUnity = nonUnity; this.peakCode = peakCode; }
    }

    static Scan scan(ByteBuffer codes, int pixels) {
        long packed = scanNative(codes, pixels);
        if (packed < 0L) throw new IllegalStateException("26827 native gain-map scan unavailable");
        return new Scan((int)(packed >>> 32), (int)(packed & 0xffffffffL));
    }

    static int remap(ByteBuffer codes, int pixels, int[] lut) {
        int peak = remapNative(codes, pixels, lut);
        if (peak < 0) throw new IllegalStateException("26827 native gain-map remap unavailable");
        return peak;
    }

    private static native long scanNative(ByteBuffer codes, int pixels);
    private static native int remapNative(ByteBuffer codes, int pixels, int[] lut);

    private MotionV2GainMapNative() {}
}
