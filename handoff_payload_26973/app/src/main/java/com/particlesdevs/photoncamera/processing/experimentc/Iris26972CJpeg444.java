package com.particlesdevs.photoncamera.processing.experimentc;

import java.io.File;
import java.nio.ByteBuffer;

/**
 * C-only JPEG444 quality95 publisher for an already finalized, native-1x,
 * genuine donor Sabre/RAISR image. No A/B/YUV/HEIC/4:2:0 fallback.
 *
 * The C-only finish now connects this encoder to genuine RAW/RAISR and JPEG/R
 * stages; production shutter integration and Android build/device proof are pending.
 */
public final class Iris26972CJpeg444 {
    private Iris26972CJpeg444() {}
    static { System.loadLibrary("iris26972c"); }

    public static boolean writeFromFinalCNativeRgba(
            ByteBuffer finalRgba, int width, int height, int rowStride,
            File output, byte[] iccProfile) {
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED ||
                finalRgba == null || !finalRgba.isDirect() ||
                output == null || width < 1 || height < 1 ||
                rowStride < (long) width * 4 ||
                output.exists()) return false;
        // Must not silently produce an SDR-only file when the agreed C
        // gainmap is mandatory. The future C publisher will handle JPEG/R
        // packaging explicitly; this codec writes the base JPEG444 only.
        return writeNative(finalRgba, width, height, rowStride,
                           output.getAbsolutePath(), iccProfile);
    }

    /**
     * Bounded-memory native 1x JPEG encoder. The C producer must deliver only
     * actual finalized sRGB pixels, already passed through real Sabre and donor
     * RAISR; this interface never constructs or guesses those pixels.
     * The native side owns at most 256 RGBA rows plus one RGB JPEG scanline,
     * not a 50MP bitmap. A callback failure deletes the temporary output.
     */
    public interface FinalizedRgbaBandSource {
        boolean fillBand(int top, int rows, ByteBuffer rgba, int rowStrideBytes);
    }

    public static boolean writeFromFinalCBands(
            int width, int height, int rowsPerBand,
            FinalizedRgbaBandSource source, File output, byte[] iccProfile) {
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED || source == null ||
                output == null || output.exists() || width < 1 || height < 1 ||
                width > 20000 || height > 20000 || rowsPerBand < 1 || rowsPerBand > 256)
            return false;
        return writeBandsNative(width,height,rowsPerBand,source,
                output.getAbsolutePath(),iccProfile);
    }

    private static native boolean writeBandsNative(
            int width, int height, int rowsPerBand,
            FinalizedRgbaBandSource source, String outputPath, byte[] iccProfile);

    private static native boolean writeNative(
            ByteBuffer rgba, int width, int height, int stride,
            String outputPath, byte[] iccProfile);
}
