package com.particlesdevs.photoncamera.spektra;

import android.graphics.ImageFormat;
import android.media.Image;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Immutable Camera2 RAW carrier owned only by Spektra. */
public final class SpektraRawFrame {
    static { System.loadLibrary("spektra_iris"); }

    /** Processing/output dimensions. Preview is VF-S size; saved still equals source RAW size. */
    public final int width;
    public final int height;
    private final int sourceWidth;
    private final int sourceHeight;
    public final int sourceFormat;
    public final int rowStride;
    public final int pixelStride;
    public final long timestampNs;
    /** Durable original packed RAW bytes. Present only for saved stills/recovery. */
    public final byte[] packedRaw;
    /** Reduced native-endian U16 Bayer meter. CPU use is restricted to AE/Bayer discovery. */
    public final byte[] mosaic16;
    /** Scene-linear RGBA16F VF-S image produced by the Spektra-owned native RAW developer. */
    public final byte[] previewLinearRgba16f;

    /**
     * One reusable direct staging allocation per preview-decode thread. Camera2 Images are copied
     * here and closed before native RAW development, so processing can never retain a camera buffer.
     */
    private static final ThreadLocal<ByteBuffer> PREVIEW_RAW_STAGING =
            ThreadLocal.withInitial(() -> ByteBuffer.allocateDirect(1).order(ByteOrder.nativeOrder()));

    private SpektraRawFrame(int width, int height, int sourceWidth, int sourceHeight,
            int sourceFormat, int rowStride, int pixelStride, long timestampNs,
            byte[] packedRaw, byte[] mosaic16, byte[] previewLinearRgba16f) {
        this.width = width;
        this.height = height;
        this.sourceWidth = sourceWidth;
        this.sourceHeight = sourceHeight;
        this.sourceFormat = sourceFormat;
        this.rowStride = rowStride;
        this.pixelStride = pixelStride;
        this.timestampNs = timestampNs;
        this.packedRaw = packedRaw;
        this.mosaic16 = mosaic16;
        this.previewLinearRgba16f = previewLinearRgba16f;
    }

    static SpektraRawFrame restore(int sourceWidth, int sourceHeight, int sourceFormat,
            int rowStride, int pixelStride, long timestampNs, byte[] packedRaw) {
        validatePacked(sourceWidth, sourceHeight, sourceFormat, rowStride, pixelStride, packedRaw);
        return new SpektraRawFrame(sourceWidth, sourceHeight, sourceWidth, sourceHeight,
                sourceFormat, rowStride, pixelStride, timestampNs, packedRaw.clone(), null, null);
    }

    public int sourceWidth() { return sourceWidth; }
    public int sourceHeight() { return sourceHeight; }

    /**
     * VF-S live contract. Packed RAW is detached into Spektra-owned reusable staging and the
     * Camera2 Image is closed before native RAW development. Native then reconstructs sensor
     * RGB/linear RGB in the source lattice and reduces only after reconstruction.
     */
    public static SpektraRawFrame copyPreviewFrom(Image image, int previewShortEdge,
            SpektraFrameMetadata metadata, float[] sensorToLinearSrgb) {
        if (previewShortEdge <= 0) throw new IllegalArgumentException("Invalid Spektra preview short edge");
        final int srcWidth = requireImageWidth(image);
        final int srcHeight = image.getHeight();
        final int format = image.getFormat();
        final long timestampNs = image.getTimestamp();
        final int[] out = previewDimensions(srcWidth, srcHeight, previewShortEdge);
        final RawPlane plane;
        try {
            plane = detachedRawPlane(image);
        } finally {
            // This is deliberately before processLivePreview/nativeDecodeMeter. Native processing
            // therefore cannot own or exhaust Camera2 ImageReader buffers.
            try { image.close(); } catch (Throwable ignored) {}
        }

        byte[] linear = null;
        final boolean geometryReady = metadata != null && metadata.bayerOffset >= 0 && metadata.bayerOffset <= 3
                && metadata.cfaArrangement >= 0 && metadata.cfaArrangement <= 3
                && sensorToLinearSrgb != null && sensorToLinearSrgb.length == 9;
        if (geometryReady) {
            linear = SpektraRawProcessor.processLivePreview(plane.buffer, plane.offset, plane.bytes,
                    srcWidth, srcHeight, plane.rowStride, plane.pixelStride, format,
                    metadata, sensorToLinearSrgb, out[0], out[1]);
            validatePreviewLinear(out[0], out[1], linear);
            if (linear == null) {
                return new SpektraRawFrame(out[0], out[1], srcWidth, srcHeight, format,
                        plane.rowStride, plane.pixelStride, timestampNs, null, null, null);
            }
        }
        byte[] meter = nativeDecodeMeter(plane.buffer, plane.offset, plane.bytes,
                srcWidth, srcHeight, plane.rowStride, plane.pixelStride, format, out[0], out[1]);
        validateMeter(out[0], out[1], format, meter);
        return new SpektraRawFrame(out[0], out[1], srcWidth, srcHeight, format,
                plane.rowStride, plane.pixelStride, timestampNs, null, meter, linear);
    }

    /** Saved path keeps the Camera2 plane packed; Java never expands the full Bayer raster. */
    public static SpektraRawFrame copyStillFrom(Image image) {
        final int srcWidth = requireImageWidth(image);
        final int srcHeight = image.getHeight();
        RawPlane plane = rawPlane(image);
        byte[] packed = new byte[plane.bytes];
        ByteBuffer src = plane.buffer.duplicate();
        src.position(plane.offset);
        src.limit(plane.offset + plane.bytes);
        src.get(packed);
        validatePacked(srcWidth, srcHeight, image.getFormat(), plane.rowStride, plane.pixelStride, packed);
        return new SpektraRawFrame(srcWidth, srcHeight, srcWidth, srcHeight, image.getFormat(),
                plane.rowStride, plane.pixelStride, image.getTimestamp(), packed, null, null);
    }

    public static SpektraRawFrame copyFrom(Image image) { return copyStillFrom(image); }

    private static int requireImageWidth(Image image) {
        if (image == null || image.getPlanes() == null || image.getPlanes().length == 0) {
            throw new IllegalArgumentException("RAW image missing plane");
        }
        if (image.getWidth() <= 0 || image.getHeight() <= 0) {
            throw new IllegalArgumentException("RAW image has invalid dimensions");
        }
        int format = image.getFormat();
        if (format != ImageFormat.RAW_SENSOR && format != ImageFormat.RAW10 && format != ImageFormat.RAW12) {
            throw new IllegalArgumentException("Unsupported Spektra RAW format " + format);
        }
        return image.getWidth();
    }

    private static int[] previewDimensions(int srcWidth, int srcHeight, int previewShortEdge) {
        int outWidth, outHeight;
        if (srcWidth >= srcHeight) {
            outHeight = Math.min(srcHeight, previewShortEdge);
            outWidth = Math.max(2, (int) Math.round((double) srcWidth * outHeight / srcHeight));
        } else {
            outWidth = Math.min(srcWidth, previewShortEdge);
            outHeight = Math.max(2, (int) Math.round((double) srcHeight * outWidth / srcWidth));
        }
        outWidth &= ~1;
        outHeight &= ~1;
        if (outWidth <= 0 || outHeight <= 0) throw new IllegalArgumentException("Invalid Spektra preview geometry");
        return new int[]{outWidth, outHeight};
    }

    private static final class RawPlane {
        final ByteBuffer buffer;
        final int offset, bytes, rowStride, pixelStride;
        RawPlane(ByteBuffer buffer, int offset, int bytes, int rowStride, int pixelStride) {
            this.buffer = buffer; this.offset = offset; this.bytes = bytes;
            this.rowStride = rowStride; this.pixelStride = pixelStride;
        }
    }

    private static RawPlane detachedRawPlane(Image image) {
        RawPlane live = rawPlane(image);
        ByteBuffer staging = PREVIEW_RAW_STAGING.get();
        if (staging.capacity() < live.bytes) {
            int capacity = 1;
            while (capacity < live.bytes && capacity <= (Integer.MAX_VALUE >>> 1)) capacity <<= 1;
            if (capacity < live.bytes) capacity = live.bytes;
            staging = ByteBuffer.allocateDirect(capacity).order(ByteOrder.nativeOrder());
            PREVIEW_RAW_STAGING.set(staging);
        }
        ByteBuffer src = live.buffer.duplicate();
        src.position(live.offset);
        src.limit(live.offset + live.bytes);
        staging.clear();
        staging.limit(live.bytes);
        staging.put(src);
        staging.flip();
        return new RawPlane(staging, 0, live.bytes, live.rowStride, live.pixelStride);
    }

    private static RawPlane rawPlane(Image image) {
        Image.Plane plane = image.getPlanes()[0];
        ByteBuffer src = plane.getBuffer().duplicate();
        int offset;
        int bytes;
        if (src.isDirect()) {
            offset = src.position();
            bytes = src.remaining();
        } else {
            ByteBuffer direct = ByteBuffer.allocateDirect(src.remaining()).order(ByteOrder.nativeOrder());
            direct.put(src).flip();
            src = direct;
            offset = 0;
            bytes = direct.remaining();
        }
        if (bytes <= 0 || plane.getRowStride() <= 0) throw new IllegalArgumentException("RAW plane is empty");
        return new RawPlane(src, offset, bytes, plane.getRowStride(), plane.getPixelStride());
    }

    private static void validatePreviewLinear(int width, int height, byte[] rgba16f) {
        if (rgba16f == null) return; // Preview may deliberately drop while saved RAW work owns the native developer.
        long expected = (long) width * (long) height * 8L;
        if (expected > Integer.MAX_VALUE || rgba16f.length != (int) expected) {
            throw new IllegalArgumentException("Spektra VF-S RGBA16F byte count mismatch");
        }
    }

    private static void validateMeter(int width, int height, int sourceFormat, byte[] mosaic16) {
        if (width <= 0 || height <= 0 || mosaic16 == null) throw new IllegalArgumentException("Invalid Spektra meter");
        long expected = (long) width * (long) height * 2L;
        if (expected > Integer.MAX_VALUE || mosaic16.length != (int) expected) {
            throw new IllegalArgumentException("Spektra meter byte count mismatch");
        }
        if (sourceFormat != ImageFormat.RAW_SENSOR && sourceFormat != ImageFormat.RAW10
                && sourceFormat != ImageFormat.RAW12) {
            throw new IllegalArgumentException("Invalid Spektra RAW format " + sourceFormat);
        }
    }

    private static void validatePacked(int width, int height, int sourceFormat,
            int rowStride, int pixelStride, byte[] packed) {
        if (width <= 0 || height <= 0 || rowStride <= 0 || packed == null || packed.length <= 0) {
            throw new IllegalArgumentException("Invalid packed Spektra RAW");
        }
        if (sourceFormat != ImageFormat.RAW_SENSOR && sourceFormat != ImageFormat.RAW10
                && sourceFormat != ImageFormat.RAW12) {
            throw new IllegalArgumentException("Invalid frozen Spektra RAW format " + sourceFormat);
        }
        long minimum;
        if (sourceFormat == ImageFormat.RAW10) minimum = (long) ((width + 3) / 4) * 5L;
        else if (sourceFormat == ImageFormat.RAW12) minimum = (long) ((width + 1) / 2) * 3L;
        else minimum = (long) width * Math.max(2, pixelStride);
        long required = (long) (height - 1) * rowStride + minimum;
        if (required > packed.length) throw new IllegalArgumentException("Packed Spektra RAW byte count mismatch");
    }

    /**
     * Infer only the Bayer-origin parity left ambiguous by Camera2 stream geometry. The active RAW
     * domain remains the geometry authority; image statistics may reject it but never invent R/B phase.
     */
    public int estimateBayerOffset(int cfaArrangement, int[] black4, int whiteLevel, int geometryHint) {
        if (mosaic16 == null || cfaArrangement < 0 || cfaArrangement > 3
                || black4 == null || black4.length < 4 || whiteLevel <= 0) {
            return geometryHint >= 0 && geometryHint <= 3 ? geometryHint : -1;
        }
        ByteBuffer b = ByteBuffer.wrap(mosaic16).order(ByteOrder.nativeOrder());
        double[] sum = new double[4];
        double[] sumSq = new double[4];
        long[] count = new long[4];
        final int borderX = Math.max(2, width / 16);
        final int borderY = Math.max(2, height / 16);
        int phaseStep = Math.max(4, Math.min(width, height) / 120);
        if ((phaseStep & 1) != 0) phaseStep++;
        for (int q = 0; q < 4; ++q) {
            final int qx = q & 1, qy = (q >> 1) & 1;
            int startX = borderX, startY = borderY;
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
        double[] classScore = {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
        for (int offset = 0; offset < 4; ++offset) {
            int effectiveCfa = cfaArrangement ^ offset;
            int red = effectiveCfa, blue = effectiveCfa ^ 3, g0 = -1, g1 = -1;
            for (int q = 0; q < 4; ++q) {
                if (q == red || q == blue) continue;
                if (g0 < 0) g0 = q; else g1 = q;
            }
            if (g0 < 0 || g1 < 0 || count[g0] == 0 || count[g1] == 0) continue;
            double m0raw = sum[g0] / count[g0], m1raw = sum[g1] / count[g1];
            double m0 = Math.max(0.0, m0raw - black4[g0 ^ offset]) / Math.max(1.0, whiteLevel - black4[g0 ^ offset]);
            double m1 = Math.max(0.0, m1raw - black4[g1 ^ offset]) / Math.max(1.0, whiteLevel - black4[g1 ^ offset]);
            double v0 = Math.max(0.0, sumSq[g0] / count[g0] - m0raw * m0raw);
            double v1 = Math.max(0.0, sumSq[g1] / count[g1] - m1raw * m1raw);
            double score = Math.abs(Math.log((m0 + 1e-6) / (m1 + 1e-6)))
                    + 0.15 * Math.abs(Math.log((Math.sqrt(v0) + 1.0) / (Math.sqrt(v1) + 1.0)));
            int klass = (offset == 0 || offset == 3) ? 0 : 1;
            classScore[klass] = Math.min(classScore[klass], score);
        }
        if (geometryHint < 0 || geometryHint > 3) return -1;
        int geometryClass = (geometryHint == 0 || geometryHint == 3) ? 0 : 1;
        int otherClass = 1 - geometryClass;
        if (!Double.isFinite(classScore[geometryClass])) return -1;
        if (Double.isFinite(classScore[otherClass]) && classScore[otherClass] + 0.08 < classScore[geometryClass]) return -1;
        return geometryHint;
    }

    public double centerWeightedMeter(int[] black4, int whiteLevel) {
        return centerWeightedMeter(black4, whiteLevel, 0.5, 0.5, false);
    }

    public double centerWeightedMeter(int[] black4, int whiteLevel,
            double touchX, double touchY, boolean touchActive) {
        if (mosaic16 == null || whiteLevel <= 0) return 0.18;
        ByteBuffer b = ByteBuffer.wrap(mosaic16).order(ByteOrder.nativeOrder());
        final int step = Math.max(2, Math.min(width, height) / 96);
        double weighted = 0.0, weightSum = 0.0;
        for (int y = step / 2; y < height; y += step) {
            double ny = (2.0 * y / Math.max(1.0, height - 1.0)) - 1.0;
            for (int x = step / 2; x < width; x += step) {
                double nx = (2.0 * x / Math.max(1.0, width - 1.0)) - 1.0;
                double sceneWeight = 0.25 + 0.75 * Math.exp(-1.5 * (nx * nx + ny * ny));
                double w = sceneWeight;
                if (touchActive) {
                    double px = x / Math.max(1.0, width - 1.0), py = y / Math.max(1.0, height - 1.0);
                    double dx = px - touchX, dy = py - touchY;
                    double local = Math.exp(-24.0 * (dx * dx + dy * dy));
                    w = 0.35 * sceneWeight + 0.65 * (0.20 + 0.80 * local);
                }
                int q = ((y & 1) << 1) | (x & 1);
                int black = black4 == null || black4.length < 4 ? 0 : black4[q];
                int sample = b.getShort((y * width + x) * 2) & 0xffff;
                double normalized = Math.max(0.0, sample - black) / Math.max(1.0, whiteLevel - black);
                weighted += w * normalized;
                weightSum += w;
            }
        }
        return weightSum > 0.0 ? weighted / weightSum : 0.18;
    }

    private static native byte[] nativeDecodeMeter(ByteBuffer source, int sourceOffset, int sourceBytes,
            int sourceWidth, int sourceHeight, int rowStride, int pixelStride, int format,
            int outputWidth, int outputHeight);
}
