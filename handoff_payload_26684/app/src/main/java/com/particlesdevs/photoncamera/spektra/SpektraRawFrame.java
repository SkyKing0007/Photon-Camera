package com.particlesdevs.photoncamera.spektra;

import android.graphics.ImageFormat;
import android.media.Image;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Immutable Bayer frame owned only by Spektra. Packed Camera2 RAW decoding is native. */
public final class SpektraRawFrame {
    static { System.loadLibrary("spektra_iris"); }

    public final int width;
    public final int height;
    public final int sourceFormat;
    public final long timestampNs;
    /** Native-endian unsigned 16-bit Bayer samples, one sample per pixel. */
    public final byte[] mosaic16;

    private SpektraRawFrame(int width, int height, int sourceFormat, long timestampNs, byte[] mosaic16) {
        this.width = width;
        this.height = height;
        this.sourceFormat = sourceFormat;
        this.timestampNs = timestampNs;
        this.mosaic16 = mosaic16;
    }

    static SpektraRawFrame restore(int width, int height, int sourceFormat, long timestampNs, byte[] mosaic16) {
        validateFrozen(width, height, sourceFormat, mosaic16);
        return new SpektraRawFrame(width, height, sourceFormat, timestampNs, mosaic16.clone());
    }

    /**
     * Unspektrawesome-compatible live contract: retain the full Camera2 RAW stream, but decode only
     * the LOW-quality preview lattice (default short edge 480 -> 640x480 for a 4:3 sensor).
     * No full-frame Java RAW10/RAW12 expansion is permitted on the Camera2 callback thread.
     */
    public static SpektraRawFrame copyPreviewFrom(Image image, int previewShortEdge) {
        if (previewShortEdge <= 0) throw new IllegalArgumentException("Invalid Spektra preview short edge");
        final int srcWidth = requireImageWidth(image);
        final int srcHeight = image.getHeight();
        int outWidth;
        int outHeight;
        if (srcWidth >= srcHeight) {
            outHeight = Math.min(srcHeight, previewShortEdge);
            outWidth = Math.max(2, (int)Math.round((double)srcWidth * outHeight / srcHeight));
        } else {
            outWidth = Math.min(srcWidth, previewShortEdge);
            outHeight = Math.max(2, (int)Math.round((double)srcHeight * outWidth / srcWidth));
        }
        outWidth &= ~1;
        outHeight &= ~1;
        if (outWidth <= 0 || outHeight <= 0) throw new IllegalArgumentException("Invalid Spektra preview geometry");
        return decodeNative(image, outWidth, outHeight);
    }

    /** Full-resolution single-frame decode used only for the shutter capture. */
    public static SpektraRawFrame copyStillFrom(Image image) {
        final int width = requireImageWidth(image);
        return decodeNative(image, width, image.getHeight());
    }

    /** Kept as a compatibility alias for frozen single-frame callers; live preview must not call it. */
    public static SpektraRawFrame copyFrom(Image image) {
        return copyStillFrom(image);
    }

    private static int requireImageWidth(Image image) {
        if (image == null || image.getPlanes() == null || image.getPlanes().length == 0) {
            throw new IllegalArgumentException("RAW image missing plane");
        }
        if (image.getWidth() <= 0 || image.getHeight() <= 0) {
            throw new IllegalArgumentException("RAW image has invalid dimensions");
        }
        return image.getWidth();
    }

    private static SpektraRawFrame decodeNative(Image image, int outWidth, int outHeight) {
        final int format = image.getFormat();
        if (format != ImageFormat.RAW_SENSOR && format != ImageFormat.RAW10 && format != ImageFormat.RAW12) {
            throw new IllegalArgumentException("Unsupported Spektra RAW format " + format);
        }
        final Image.Plane plane = image.getPlanes()[0];
        ByteBuffer src = plane.getBuffer().duplicate();
        final int rowStride = plane.getRowStride();
        final int pixelStride = plane.getPixelStride();
        final int sourceOffset;
        final int sourceBytes;
        if (src.isDirect()) {
            sourceOffset = src.position();
            sourceBytes = src.remaining();
        } else {
            // Android RAW planes are normally direct. Keep a strict fallback for unusual devices,
            // but still decode packed RAW in native code rather than expanding it in Java.
            ByteBuffer direct = ByteBuffer.allocateDirect(src.remaining()).order(ByteOrder.nativeOrder());
            direct.put(src);
            direct.flip();
            src = direct;
            sourceOffset = 0;
            sourceBytes = direct.remaining();
        }
        byte[] out = nativeDecodeRaw(src, sourceOffset, sourceBytes, image.getWidth(), image.getHeight(),
                rowStride, pixelStride, format, outWidth, outHeight);
        validateFrozen(outWidth, outHeight, format, out);
        return new SpektraRawFrame(outWidth, outHeight, format, image.getTimestamp(), out);
    }

    private static void validateFrozen(int width, int height, int sourceFormat, byte[] mosaic16) {
        if (width <= 0 || height <= 0 || mosaic16 == null) {
            throw new IllegalArgumentException("Invalid frozen Spektra RAW");
        }
        long expected = (long) width * (long) height * 2L;
        if (expected > Integer.MAX_VALUE || mosaic16.length != (int) expected) {
            throw new IllegalArgumentException("Frozen Spektra RAW byte count mismatch");
        }
        if (sourceFormat != ImageFormat.RAW_SENSOR && sourceFormat != ImageFormat.RAW10
                && sourceFormat != ImageFormat.RAW12) {
            throw new IllegalArgumentException("Invalid frozen Spektra RAW format " + sourceFormat);
        }
    }

    public double centerWeightedMeter(int[] black4, int whiteLevel) {
        return centerWeightedMeter(black4, whiteLevel, 0.5, 0.5, false);
    }

    /** Touch metering favors the tapped subject while retaining a whole-scene center-weighted reading. */
    public double centerWeightedMeter(int[] black4, int whiteLevel, double touchX, double touchY, boolean touchActive) {
        if (whiteLevel <= 0) return 0.18;
        ByteBuffer b = ByteBuffer.wrap(mosaic16).order(ByteOrder.nativeOrder());
        final int step = Math.max(2, Math.min(width, height) / 96);
        double weighted = 0.0;
        double weightSum = 0.0;
        for (int y = step / 2; y < height; y += step) {
            double ny = (2.0 * y / Math.max(1.0, height - 1.0)) - 1.0;
            for (int x = step / 2; x < width; x += step) {
                double nx = (2.0 * x / Math.max(1.0, width - 1.0)) - 1.0;
                double r2 = nx * nx + ny * ny;
                double sceneWeight = 0.25 + 0.75 * Math.exp(-1.5 * r2);
                double w = sceneWeight;
                if (touchActive) {
                    double px = x / Math.max(1.0, width - 1.0);
                    double py = y / Math.max(1.0, height - 1.0);
                    double dx = px - touchX;
                    double dy = py - touchY;
                    double local = Math.exp(-24.0 * (dx * dx + dy * dy));
                    w = 0.35 * sceneWeight + 0.65 * (0.20 + 0.80 * local);
                }
                int cfa = ((y & 1) << 1) | (x & 1);
                int black = black4 == null || black4.length < 4 ? 0 : black4[cfa];
                int sample = b.getShort((y * width + x) * 2) & 0xffff;
                double normalized = Math.max(0.0, sample - black) / Math.max(1.0, whiteLevel - black);
                weighted += w * normalized;
                weightSum += w;
            }
        }
        return weightSum > 0.0 ? weighted / weightSum : 0.18;
    }

    private static native byte[] nativeDecodeRaw(ByteBuffer source, int sourceOffset, int sourceBytes,
            int sourceWidth, int sourceHeight, int rowStride, int pixelStride, int format,
            int outputWidth, int outputHeight);
}
