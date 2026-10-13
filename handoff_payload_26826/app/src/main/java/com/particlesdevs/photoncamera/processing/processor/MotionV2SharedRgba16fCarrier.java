package com.particlesdevs.photoncamera.processing.processor;

import android.hardware.HardwareBuffer;
import android.os.Build;

import com.particlesdevs.photoncamera.util.Allocator;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * IRIS_26826_SHARED_RGBA16F_CARRIER
 *
 * Motion-only cross-context transport for the already-accepted RGBA16F Sabre/VGN carrier.
 * The CPU residual denoiser still edits the exact half-float bytes in place. HardwareBuffer only
 * removes the 26825 full-frame glReadPixels + glTexSubImage round-trip. Any allocation/import/map
 * failure returns control to the exact 26825 ByteBuffer route.
 */
public final class MotionV2SharedRgba16fCarrier implements AutoCloseable {
    private static final String TAG = "MotionV2SharedRgba16f";
    private static final long BYTES_PER_PIXEL = 8L;
    private HardwareBuffer buffer;
    public final int width;
    public final int height;
    private boolean cpuLocked;

    static { System.loadLibrary("motionv2jpeg"); }

    private MotionV2SharedRgba16fCarrier(HardwareBuffer buffer, int width, int height) {
        this.buffer = buffer;
        this.width = width;
        this.height = height;
    }

    public static MotionV2SharedRgba16fCarrier tryCreate(int width, int height) {
        if (Build.VERSION.SDK_INT < 26 || width <= 0 || height <= 0) return null;
        final long usage = HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE
                | HardwareBuffer.USAGE_GPU_COLOR_OUTPUT
                | HardwareBuffer.USAGE_CPU_READ_OFTEN
                | HardwareBuffer.USAGE_CPU_WRITE_OFTEN;
        try {
            if (Build.VERSION.SDK_INT >= 29
                    && !HardwareBuffer.isSupported(width, height, HardwareBuffer.RGBA_FP16, 1, usage)) {
                Log.w(TAG, "IRIS_26826_SHARED_RGBA16F_UNAVAILABLE reason=unsupported size="
                        + width + "x" + height);
                return null;
            }
            HardwareBuffer hb = HardwareBuffer.create(
                    width, height, HardwareBuffer.RGBA_FP16, 1, usage);
            if (hb == null) return null;
            return new MotionV2SharedRgba16fCarrier(hb, width, height);
        } catch (Throwable t) {
            Log.w(TAG, "IRIS_26826_SHARED_RGBA16F_UNAVAILABLE reason="
                    + t.getClass().getSimpleName());
            return null;
        }
    }

    public long expectedBytes() {
        return (long) width * (long) height * BYTES_PER_PIXEL;
    }

    public boolean copyFromCurrentGlTexture(int sourceTextureId) {
        HardwareBuffer hb = buffer;
        return hb != null && sourceTextureId != 0
                && copyFromCurrentGlTextureNative(hb, sourceTextureId, width, height);
    }

    public boolean copyToCurrentGlTexture(int destinationTextureId) {
        HardwareBuffer hb = buffer;
        return hb != null && destinationTextureId != 0
                && copyToCurrentGlTextureNative(hb, destinationTextureId, width, height);
    }

    public ByteBuffer lockCpu() {
        if (cpuLocked || buffer == null) return null;
        ByteBuffer mapped = lockCpuNative(buffer, width, height);
        if (mapped == null || mapped.capacity() != expectedBytes()) return null;
        mapped.order(ByteOrder.nativeOrder());
        mapped.position(0);
        mapped.limit(mapped.capacity());
        cpuLocked = true;
        return mapped;
    }

    public boolean unlockCpu() {
        if (!cpuLocked || buffer == null) return false;
        boolean ok = unlockCpuNative(buffer);
        if (ok) cpuLocked = false;
        return ok;
    }

    /** Lazily recreates the exact 26825 CPU carrier only if the consumer-side GPU import fails. */
    public ByteBuffer copyTo26825FallbackBuffer() {
        ByteBuffer mapped = lockCpu();
        if (mapped == null) return null;
        try {
            if (expectedBytes() > Integer.MAX_VALUE) return null;
            mapped.position(0);
            ByteBuffer copy = Allocator.allocateAndCopy((int) expectedBytes(), mapped, 0);
            if (copy != null) {
                copy.order(ByteOrder.nativeOrder());
                copy.position(0);
            }
            return copy;
        } finally {
            if (!unlockCpu()) {
                Log.e(TAG, "IRIS_26826_SHARED_RGBA16F_FALLBACK_UNLOCK_FAILED");
            }
        }
    }

    @Override
    public void close() {
        HardwareBuffer hb = buffer;
        buffer = null;
        if (hb == null) return;
        if (cpuLocked) {
            try { unlockCpuNative(hb); } catch (Throwable ignored) {}
            cpuLocked = false;
        }
        try { hb.close(); } catch (Throwable ignored) {}
    }

    private static native boolean copyFromCurrentGlTextureNative(
            HardwareBuffer buffer, int sourceTextureId, int width, int height);
    private static native boolean copyToCurrentGlTextureNative(
            HardwareBuffer buffer, int destinationTextureId, int width, int height);
    private static native ByteBuffer lockCpuNative(HardwareBuffer buffer, int width, int height);
    private static native boolean unlockCpuNative(HardwareBuffer buffer);
}
