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
    /** Native-endian unsigned 16-bit Bayer samples, one sample per pixel. Saved stills own the full raster;
     * VF-S owns only a reduced Bayer meter used for AE/profile verification. */
    public final byte[] mosaic16;
    /** Optional native-order RGBA16F camera-RGB VF-S image reconstructed in the source RAW lattice
     * before reduction. Never serialized into the durable .shot capture recipe. */
    public final byte[] previewCameraRgb16f;

    private SpektraRawFrame(int width, int height, int sourceFormat, long timestampNs, byte[] mosaic16,
            byte[] previewCameraRgb16f) {
        this.width = width;
        this.height = height;
        this.sourceFormat = sourceFormat;
        this.timestampNs = timestampNs;
        this.mosaic16 = mosaic16;
        this.previewCameraRgb16f = previewCameraRgb16f;
    }

    static SpektraRawFrame restore(int width, int height, int sourceFormat, long timestampNs, byte[] mosaic16) {
        validateFrozen(width, height, sourceFormat, mosaic16);
        return new SpektraRawFrame(width, height, sourceFormat, timestampNs, mosaic16.clone(), null);
    }

    /**
     * VF-S live contract. Camera2 continues to provide the verified full-resolution RAW stream,
     * while the display path reconstructs camera RGB from physically adjacent source photosites
     * before reducing to the requested LOW preview size. The reduced Bayer carrier exists only
     * for exposure/profile verification; it is never demosaiced for display.
     */
    public static SpektraRawFrame copyPreviewFrom(Image image, int previewShortEdge, int sensorCfa,
            int[] sensorBlack4, int whiteLevel, int bayerOffset) {
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
        return decodePreviewNative(image, outWidth, outHeight, sensorCfa, sensorBlack4, whiteLevel, bayerOffset);
    }

    /** Full-resolution single-frame decode used only for the shutter capture. */
    public static SpektraRawFrame copyStillFrom(Image image) {
        final int width = requireImageWidth(image);
        return decodeStillNative(image, width, image.getHeight());
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

    private static SpektraRawFrame decodeStillNative(Image image, int outWidth, int outHeight) {
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
        return new SpektraRawFrame(outWidth, outHeight, format, image.getTimestamp(), out, null);
    }

    private static SpektraRawFrame decodePreviewNative(Image image, int outWidth, int outHeight,
            int sensorCfa, int[] sensorBlack4, int whiteLevel, int bayerOffset) {
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
            ByteBuffer direct = ByteBuffer.allocateDirect(src.remaining()).order(ByteOrder.nativeOrder());
            direct.put(src);
            direct.flip();
            src = direct;
            sourceOffset = 0;
            sourceBytes = direct.remaining();
        }
        // Keep a reduced raw meter for Unspektra AE and for first-run Bayer-origin verification.
        // It is never consumed by the display demosaic owner.
        byte[] meter = nativeDecodeRaw(src, sourceOffset, sourceBytes, image.getWidth(), image.getHeight(),
                rowStride, pixelStride, format, outWidth, outHeight);
        validateFrozen(outWidth, outHeight, format, meter);

        byte[] rgb = null;
        if (sensorCfa >= 0 && sensorCfa <= 3 && sensorBlack4 != null && sensorBlack4.length >= 4
                && whiteLevel > 0 && bayerOffset >= 0 && bayerOffset <= 3) {
            rgb = nativeDecodePreviewRgb16f(src, sourceOffset, sourceBytes, image.getWidth(), image.getHeight(),
                    rowStride, pixelStride, format, outWidth, outHeight, sensorCfa, bayerOffset,
                    sensorBlack4, whiteLevel);
            validatePreviewRgb(outWidth, outHeight, rgb);
        }
        return new SpektraRawFrame(outWidth, outHeight, format, image.getTimestamp(), meter, rgb);
    }

    private static void validatePreviewRgb(int width, int height, byte[] rgba16f) {
        if (rgba16f == null) return;
        long expected = (long) width * (long) height * 8L;
        if (expected > Integer.MAX_VALUE || rgba16f.length != (int) expected) {
            throw new IllegalArgumentException("Spektra VF-S RGB16F byte count mismatch");
        }
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


    /**
     * IRIS_26685_SPEKTRA_BAYER_PHASE_DISCOVERY
     * Infer only the Bayer-origin parity that Camera2 stream/crop geometry leaves ambiguous.
     * The Camera2 CFA enum remains authority for the color ordering; this routine chooses the
     * buffer-origin parity whose two green phases have the most similar normalized statistics.
     * Ties stay on the geometry hint so this cannot casually swap red/blue on saturated scenes.
     */
    public int estimateBayerOffset(int cfaArrangement, int[] black4, int whiteLevel, int geometryHint) {
        if (cfaArrangement < 0 || cfaArrangement > 3 || black4 == null || black4.length < 4 || whiteLevel <= 0) {
            return geometryHint >= 0 && geometryHint <= 3 ? geometryHint : -1;
        }
        ByteBuffer b = ByteBuffer.wrap(mosaic16).order(ByteOrder.nativeOrder());
        double[] sum = new double[4];
        double[] sumSq = new double[4];
        long[] count = new long[4];
        final int borderX = Math.max(2, width / 16);
        final int borderY = Math.max(2, height / 16);
        // Regression: sample every CFA phase independently. A single even-stride walk can remain
        // forever on q0 and make Bayer-origin discovery silently degenerate.
        int phaseStep = Math.max(4, Math.min(width, height) / 120);
        if ((phaseStep & 1) != 0) phaseStep++;
        for (int q = 0; q < 4; ++q) {
            final int qx = q & 1;
            final int qy = (q >> 1) & 1;
            int startX = borderX;
            int startY = borderY;
            if ((startX & 1) != qx) startX++;
            if ((startY & 1) != qy) startY++;
            for (int y = startY; y < height - borderY; y += phaseStep) {
                for (int x = startX; x < width - borderX; x += phaseStep) {
                    int sample = b.getShort((y * width + x) * 2) & 0xffff;
                    sum[q] += sample;
                    sumSq[q] += (double) sample * sample;
                    count[q]++;
                }
            }
        }

        // Image statistics can identify which diagonal contains the two green photosites, but they
        // cannot distinguish R/B orientation within that diagonal (0 vs 3 or 1 vs 2). The exact
        // X/Y origin therefore comes from Camera2 geometry. If geometry is unresolved or strongly
        // contradicts the observed green diagonal, fail closed instead of guessing a red/blue swap.
        double[] classScore = new double[] {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
        for (int offset = 0; offset < 4; ++offset) {
            int effectiveCfa = cfaArrangement ^ offset;
            int red = effectiveCfa;
            int blue = effectiveCfa ^ 3;
            int g0 = -1, g1 = -1;
            for (int q = 0; q < 4; ++q) {
                if (q == red || q == blue) continue;
                if (g0 < 0) g0 = q; else g1 = q;
            }
            if (g0 < 0 || g1 < 0 || count[g0] == 0 || count[g1] == 0) continue;
            double m0raw = sum[g0] / count[g0];
            double m1raw = sum[g1] / count[g1];
            double m0 = Math.max(0.0, m0raw - black4[g0 ^ offset])
                    / Math.max(1.0, whiteLevel - black4[g0 ^ offset]);
            double m1 = Math.max(0.0, m1raw - black4[g1 ^ offset])
                    / Math.max(1.0, whiteLevel - black4[g1 ^ offset]);
            double v0 = Math.max(0.0, sumSq[g0] / count[g0] - m0raw * m0raw);
            double v1 = Math.max(0.0, sumSq[g1] / count[g1] - m1raw * m1raw);
            double meanScore = Math.abs(Math.log((m0 + 1.0e-6) / (m1 + 1.0e-6)));
            double varScore = Math.abs(Math.log((Math.sqrt(v0) + 1.0) / (Math.sqrt(v1) + 1.0)));
            int diagonalClass = (offset == 0 || offset == 3) ? 0 : 1;
            classScore[diagonalClass] = Math.min(classScore[diagonalClass], meanScore + 0.15 * varScore);
        }
        if (geometryHint < 0 || geometryHint > 3) return -1;
        final int geometryClass = (geometryHint == 0 || geometryHint == 3) ? 0 : 1;
        final int otherClass = 1 - geometryClass;
        if (!Double.isFinite(classScore[geometryClass])) return -1;
        // Require only a meaningful contradiction to reject geometry; nearly equal class scores are
        // common in low-detail/neutral scenes and geometry remains the exact origin authority there.
        if (Double.isFinite(classScore[otherClass])
                && classScore[otherClass] + 0.08 < classScore[geometryClass]) {
            return -1;
        }
        return geometryHint;
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

    private static native byte[] nativeDecodePreviewRgb16f(ByteBuffer source, int sourceOffset, int sourceBytes,
            int sourceWidth, int sourceHeight, int rowStride, int pixelStride, int format,
            int outputWidth, int outputHeight, int sensorCfa, int bayerOffset, int[] sensorBlack4,
            int whiteLevel);
}
