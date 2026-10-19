package com.particlesdevs.photoncamera.processing.processor;

import android.hardware.HardwareBuffer;
import android.os.Build;

/**
 * IRIS_26856_B_ONLY_VULKAN_AHB_ALLOCATION_OWNER.
 *
 * A and the existing 26855 carrier must not use this allocator. Vulkan's
 * STORAGE_IMAGE usage requires GPU_DATA_BUFFER-backed hardware-buffer memory;
 * a GLES render-target-only allocation does not establish that capability.
 * Both buffers are RGBA_FP16, independently owned, and never CPU-locked.
 * The caller must retain each buffer until GL/Vulkan fences prove completion.
 */
public final class Iris26856AmazeBuffer implements AutoCloseable {
    private HardwareBuffer hardwareBuffer;
    public final int width;
    public final int height;
    public final boolean writableByVulkan;

    private Iris26856AmazeBuffer(HardwareBuffer hb, int width, int height,
                                boolean writableByVulkan) {
        this.hardwareBuffer = hb;
        this.width = width;
        this.height = height;
        this.writableByVulkan = writableByVulkan;
    }

    public static Iris26856AmazeBuffer create(int width, int height,
                                              boolean writableByVulkan) {
        if (Build.VERSION.SDK_INT < 29 || width < 1 || height < 1 ||
                (long) width * (long) height > Integer.MAX_VALUE / 8L) {
            throw new IllegalArgumentException("26856 invalid RGBA16F Vulkan AHB dimensions/API");
        }
        final long usage = HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE
                | HardwareBuffer.USAGE_GPU_COLOR_OUTPUT
                | (writableByVulkan ? HardwareBuffer.USAGE_GPU_DATA_BUFFER : 0L);
        if (!HardwareBuffer.isSupported(width, height, HardwareBuffer.RGBA_FP16, 1, usage)) {
            throw new IllegalStateException("26856 device has no exact Vulkan-compatible RGBA16F AHB");
        }
        final HardwareBuffer hb = HardwareBuffer.create(
                width, height, HardwareBuffer.RGBA_FP16, 1, usage);
        if (hb == null) throw new IllegalStateException("26856 Vulkan AHB allocation failed");
        return new Iris26856AmazeBuffer(hb, width, height, writableByVulkan);
    }

    public synchronized HardwareBuffer requireOpen() {
        if (hardwareBuffer == null) throw new IllegalStateException("26856 AHB already closed");
        return hardwareBuffer;
    }

    @Override public synchronized void close() {
        if (hardwareBuffer != null) {
            hardwareBuffer.close();
            hardwareBuffer = null;
        }
    }
}
