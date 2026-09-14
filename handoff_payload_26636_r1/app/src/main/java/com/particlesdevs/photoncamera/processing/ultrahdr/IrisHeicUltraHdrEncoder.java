package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.ColorSpace;
import android.graphics.Gainmap;
import android.os.Build;

import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.file.Files;
import java.nio.file.Path;

/**
 * IRIS_26636_ISOLATED_HEIC_ULTRA_HDR_PUBLISHER
 * Consumes only the completed 26635 SDR Bitmap + its already-attached Iris Gainmap. It never
 * computes/rebases/tunes a gain map and cannot feed any publication decision upstream.
 */
public final class IrisHeicUltraHdrEncoder {
    private static final String TAG = "IrisHeicUltraHdr";
    static {
        System.loadLibrary("irisheic");
    }

    private IrisHeicUltraHdrEncoder() {}

    public static boolean write(Path output, Bitmap completedSdr, int quality, ParseExif.ExifData exif) {
        if (Build.VERSION.SDK_INT < 36 || output == null || completedSdr == null
                || completedSdr.isRecycled() || !completedSdr.hasGainmap()) return false;
        if (!IrisHardwareHevcEncoder.isHeicUltraHdrAvailable()) return false;
        Gainmap gm = completedSdr.getGainmap();
        if (gm == null || gm.getGainmapContents() == null) return false;

        Bitmap p3 = MotionV2Jpeg444Encoder.toDisplayP3BitmapCopy(completedSdr);
        if (p3 == null) return false;
        try {
            ColorSpace cs = p3.getColorSpace();
            if (cs == null || !cs.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3))) {
                Log.e(TAG, "IRIS_26636_HEIC_P3_AUTHORITY_FAILED");
                return false;
            }
            float[] rmin = gm.getRatioMin();
            float[] rmax = gm.getRatioMax();
            float[] gamma = gm.getGamma();
            float[] es = gm.getEpsilonSdr();
            float[] eh = gm.getEpsilonHdr();
            if (rmin.length < 3 || rmax.length < 3 || gamma.length < 3 || es.length < 3 || eh.length < 3)
                return false;
            Path parent = output.toAbsolutePath().getParent();
            if (parent != null) Files.createDirectories(parent);
            Files.deleteIfExists(output);
            boolean ok = writeNative(
                    p3, gm.getGainmapContents(), output.toAbsolutePath().toString(),
                    Math.max(1, Math.min(100, quality)), rmin, rmax, gamma, es, eh,
                    gm.getMinDisplayRatioForHdrTransition(), gm.getDisplayRatioForFullHdr(),
                    exif == null ? null : exif.PHOTOGRAPHIC_SENSITIVITY,
                    exif == null ? null : exif.F_NUMBER,
                    exif == null ? null : exif.FOCAL_LENGTH,
                    exif == null ? null : exif.EXPOSURE_TIME,
                    exif == null ? null : exif.DATETIME,
                    exif == null ? null : exif.MAKE,
                    exif == null ? null : exif.MODEL);
            ok &= Files.isRegularFile(output) && Files.size(output) > 0L;
            Log.i(TAG, "IRIS_26636_HEIC_ULTRAHDR_RESULT saved=" + ok
                    + " p3=true existingGainmap=true recomputedGainmap=false path=" + output);
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26636_HEIC_ULTRAHDR_FAILED", t);
            try { Files.deleteIfExists(output); } catch (Throwable ignored) {}
            return false;
        } finally {
            if (!p3.isRecycled()) p3.recycle();
        }
    }

    private static native boolean writeNative(
            Bitmap displayP3Base, Bitmap gainMap, String path, int quality,
            float[] ratioMin, float[] ratioMax, float[] gamma,
            float[] epsilonSdr, float[] epsilonHdr,
            float minDisplayRatio, float fullDisplayRatio,
            String iso, String fNumber, String focalLength, String exposureTime,
            String dateTime, String make, String model);
}
