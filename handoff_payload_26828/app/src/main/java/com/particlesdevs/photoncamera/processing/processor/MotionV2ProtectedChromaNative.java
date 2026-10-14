package com.particlesdevs.photoncamera.processing.processor;

import java.nio.ByteBuffer;

/** IRIS_26828_NATIVE_PROTECTED_CHROMA_CLASSIFIER
 * JNI traversal of the exact inherited 26728/26795 protected-chroma classifier.
 * The Kotlin implementation remains the controlled fallback in PhotonMotionMgc1271Bridge.
 */
final class MotionV2ProtectedChromaNative {
    static final class CaptureResult {
        final int[] pixelIndices;
        final byte[] floorCodes;
        final double preVgnSum;
        final double postVgnSum;

        CaptureResult(int[] pixelIndices, byte[] floorCodes, double preVgnSum, double postVgnSum) {
            this.pixelIndices = pixelIndices;
            this.floorCodes = floorCodes;
            this.preVgnSum = preVgnSum;
            this.postVgnSum = postVgnSum;
        }
    }

    static {
        System.loadLibrary("motionv2jpeg");
    }

    private MotionV2ProtectedChromaNative() {}

    static CaptureResult capture(ByteBuffer buffer, int width, int height) {
        if (buffer == null || !buffer.isDirect() || width <= 0 || height <= 0) {
            throw new IllegalArgumentException("26828 protected-chroma capture requires direct RGBA16F buffer");
        }
        final long pixelsLong = (long) width * (long) height;
        if (pixelsLong > Integer.MAX_VALUE || buffer.capacity() < pixelsLong * 8L) {
            throw new IllegalArgumentException("26828 protected-chroma capture dimensions/buffer mismatch");
        }
        final int pixels = (int) pixelsLong;
        final int count = countCaptureNative(buffer, pixels);
        if (count < 0 || count > pixels) {
            throw new IllegalStateException("26828 protected-chroma native count failed: " + count);
        }
        final int[] indices = new int[count];
        final byte[] codes = new byte[count];
        final double[] sums = new double[2];
        final int filled = fillCaptureNative(buffer, pixels, indices, codes, sums);
        if (filled != count) {
            throw new IllegalStateException("26828 protected-chroma native fill mismatch: " + filled + "/" + count);
        }
        return new CaptureResult(indices, codes, sums[0], sums[1]);
    }

    static double[] apply(ByteBuffer buffer, int width, int height, int[] indices, byte[] floorCodes) {
        if (buffer == null || !buffer.isDirect() || width <= 0 || height <= 0 ||
                indices == null || floorCodes == null || indices.length != floorCodes.length) {
            throw new IllegalArgumentException("26828 protected-chroma apply arguments invalid");
        }
        final long pixelsLong = (long) width * (long) height;
        if (pixelsLong > Integer.MAX_VALUE || buffer.capacity() < pixelsLong * 8L) {
            throw new IllegalArgumentException("26828 protected-chroma apply dimensions/buffer mismatch");
        }
        // Allocate the complete result carrier before native code can mutate RGB. Native returns
        // false only before the first write, so Kotlin fallback is always safe if this throws.
        final double[] metrics = new double[21];
        if (!applyNative(buffer, width, height, indices, floorCodes, metrics)) {
            throw new IllegalStateException("26828 protected-chroma native apply failed before mutation");
        }
        return metrics;
    }

    private static native int countCaptureNative(ByteBuffer buffer, int pixels);
    private static native int fillCaptureNative(ByteBuffer buffer, int pixels, int[] indices, byte[] codes, double[] sums);
    private static native boolean applyNative(ByteBuffer buffer, int width, int height, int[] indices, byte[] codes, double[] metrics);
}
