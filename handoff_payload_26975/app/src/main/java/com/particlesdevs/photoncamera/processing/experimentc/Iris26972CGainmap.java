package com.particlesdevs.photoncamera.processing.experimentc;

import java.io.File;
import java.nio.ByteBuffer;

/**
 * Isolated C-only measured HDR gainmap. Requires genuinely rendered, registered
 * native-size SDR sRGB and extended-linear-sRGB HDR. This is NOT an HDR estimator,
 * RAW developer, RAISR substitute or complete C capture path.
 *
 * For 50MP, process even-grid tiles and reuse the two tile input buffers.
 * Only the single-channel (ceil(W/2)*ceil(H/2)) gainmap remains resident.
 * JPEG/R packaging is owned separately by Iris26972CUltraHdr.
 */
public final class Iris26972CGainmap {
    public static final int DOWNSAMPLE = 2;
    public static final float MIN_RATIO = 0.25f;
    public static final float MAX_RATIO = 4.0f;
    public static final float OFFSET = 1e-4f;
    // Pinned donor HdrGainmapStrength MIN/MAX; default is 1.0.
    public static final float STRENGTH_MIN = 0.25f;
    public static final float STRENGTH_MAX = 2.0f;
    public static final int JPEG_QUALITY = 95;
    private Iris26972CGainmap() {}
    static { System.loadLibrary("iris26972c"); }

    public static int width(int nativeWidth) {
        if (nativeWidth < 2 || nativeWidth > 20000)
            throw new IllegalArgumentException("26972 C invalid native width");
        return (nativeWidth + 1) / 2;
    }
    public static int height(int nativeHeight) { return width(nativeHeight); }

    /** Caller provides all three direct buffers; no allocation or fallback. */
    public static boolean writeTile(ByteBuffer sdrRgba8, ByteBuffer hdrLinearRgbF32,
                                    ByteBuffer fullGainmapGray8, int nativeWidth,
                                    int nativeHeight, int left, int top, int tileWidth,
                                    int tileHeight, int sdrStride, int hdrStride,
                                    int gainStride, float strength) {
        if (sdrRgba8 == null || hdrLinearRgbF32 == null || fullGainmapGray8 == null ||
            !sdrRgba8.isDirect() || !hdrLinearRgbF32.isDirect() ||
            !fullGainmapGray8.isDirect() || fullGainmapGray8.isReadOnly() ||
            !Float.isFinite(strength) || strength < STRENGTH_MIN ||
            strength > STRENGTH_MAX) return false;
        return writeTileNative(sdrRgba8, hdrLinearRgbF32, fullGainmapGray8,
            nativeWidth, nativeHeight, left, top, tileWidth, tileHeight,
            sdrStride, hdrStride, gainStride, strength);
    }

    /** Writes only a temporary grayscale JPEG; it does not publish a photo. */
    public static boolean encodeIntermediateJpeg(ByteBuffer fullGray,
                                                 int nativeWidth, int nativeHeight,
                                                 File intermediate) {
        if (fullGray == null || !fullGray.isDirect() || intermediate == null ||
            intermediate.exists()) return false;
        final int w = width(nativeWidth);
        final int h = height(nativeHeight);
        return encodeJpegNative(fullGray, w, h, w,
            intermediate.getAbsolutePath());
    }

    /** Exact paired JPEG/R metadata for the measured luminance ratio. */
    public static Iris26972CUltraHdr.Metadata jpegRMetadata() {
        final float[] min = {MIN_RATIO, MIN_RATIO, MIN_RATIO};
        final float[] max = {MAX_RATIO, MAX_RATIO, MAX_RATIO};
        final float[] gamma = {1f, 1f, 1f};
        final float[] offset = {OFFSET, OFFSET, OFFSET};
        return new Iris26972CUltraHdr.Metadata(min, max, gamma, offset, offset,
             1f, MAX_RATIO, true, Iris26972CUltraHdr.GAMUT_BT709);
    }

    private static native boolean writeTileNative(ByteBuffer sdr, ByteBuffer hdr,
        ByteBuffer output, int fullWidth, int fullHeight, int left, int top,
        int width, int height, int sdrStride, int hdrStride, int gainStride,
        float strength);
    private static native boolean encodeJpegNative(ByteBuffer gray, int width,
        int height, int stride, String path);
}
