package com.particlesdevs.photoncamera.spektra;

import android.graphics.ImageFormat;
import android.media.Image;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Immutable packed sensor frame owned only by Spektra. */
public final class SpektraRawFrame {
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
        return new SpektraRawFrame(width, height, sourceFormat, timestampNs, mosaic16.clone());
    }

    public static SpektraRawFrame copyFrom(Image image) {
        if (image == null || image.getPlanes().length == 0) throw new IllegalArgumentException("RAW image missing plane");
        final int format = image.getFormat();
        final int width = image.getWidth();
        final int height = image.getHeight();
        final Image.Plane plane = image.getPlanes()[0];
        final ByteBuffer src = plane.getBuffer().duplicate();
        final int rowStride = plane.getRowStride();
        final int pixelStride = plane.getPixelStride();
        final byte[] out = new byte[width * height * 2];
        final ByteBuffer dst = ByteBuffer.wrap(out).order(ByteOrder.nativeOrder());
        if (format == ImageFormat.RAW_SENSOR) {
            copyRaw16(src, dst, width, height, rowStride, pixelStride <= 0 ? 2 : pixelStride);
        } else if (format == ImageFormat.RAW10) {
            unpackRaw10(src, dst, width, height, rowStride);
        } else if (format == ImageFormat.RAW12) {
            unpackRaw12(src, dst, width, height, rowStride);
        } else {
            throw new IllegalArgumentException("Unsupported Spektra RAW format " + format);
        }
        return new SpektraRawFrame(width, height, format, image.getTimestamp(), out);
    }

    private static void copyRaw16(ByteBuffer src, ByteBuffer dst, int width, int height, int rowStride, int pixelStride) {
        for (int y = 0; y < height; y++) {
            int row = y * rowStride;
            for (int x = 0; x < width; x++) {
                int p = row + x * pixelStride;
                int lo = src.get(p) & 0xff;
                int hi = src.get(p + 1) & 0xff;
                dst.putShort((short)((hi << 8) | lo));
            }
        }
    }

    private static void unpackRaw10(ByteBuffer src, ByteBuffer dst, int width, int height, int rowStride) {
        // Android RAW10: groups of four 10-bit pixels occupy five bytes.
        for (int y = 0; y < height; y++) {
            int row = y * rowStride;
            int x = 0;
            for (; x + 3 < width; x += 4) {
                int p = row + (x / 4) * 5;
                int b0 = src.get(p) & 0xff;
                int b1 = src.get(p + 1) & 0xff;
                int b2 = src.get(p + 2) & 0xff;
                int b3 = src.get(p + 3) & 0xff;
                int b4 = src.get(p + 4) & 0xff;
                dst.putShort((short)((b0 << 2) | (b4 & 0x03)));
                dst.putShort((short)((b1 << 2) | ((b4 >> 2) & 0x03)));
                dst.putShort((short)((b2 << 2) | ((b4 >> 4) & 0x03)));
                dst.putShort((short)((b3 << 2) | ((b4 >> 6) & 0x03)));
            }
            if (x < width) {
                int p = row + (x / 4) * 5;
                int packed = src.get(p + 4) & 0xff;
                for (int i = 0; x + i < width && i < 4; i++) {
                    int msb = src.get(p + i) & 0xff;
                    dst.putShort((short)((msb << 2) | ((packed >> (i * 2)) & 0x03)));
                }
            }
        }
    }

    private static void unpackRaw12(ByteBuffer src, ByteBuffer dst, int width, int height, int rowStride) {
        // Android RAW12: groups of two 12-bit pixels occupy three bytes.
        for (int y = 0; y < height; y++) {
            int row = y * rowStride;
            int x = 0;
            for (; x + 1 < width; x += 2) {
                int p = row + (x / 2) * 3;
                int b0 = src.get(p) & 0xff;
                int b1 = src.get(p + 1) & 0xff;
                int b2 = src.get(p + 2) & 0xff;
                dst.putShort((short)((b0 << 4) | (b2 & 0x0f)));
                dst.putShort((short)((b1 << 4) | ((b2 >> 4) & 0x0f)));
            }
            if (x < width) {
                int p = row + (x / 2) * 3;
                int b0 = src.get(p) & 0xff;
                int b2 = src.get(p + 2) & 0xff;
                dst.putShort((short)((b0 << 4) | (b2 & 0x0f)));
            }
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
}
