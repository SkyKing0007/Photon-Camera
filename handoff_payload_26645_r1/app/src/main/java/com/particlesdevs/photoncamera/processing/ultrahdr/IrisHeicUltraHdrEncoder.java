package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
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

    /* IRIS_26645_ANDROID_HEIC_ULTRAHDR_READBACK_CONTRACT
     * Publication is successful only if Android decodes the exact saved HEIC as Ultra HDR and
     * reconstructs the same gain-map metadata/content geometry. This converts 26642's asynchronous
     * diagnostic into a fail-closed file contract without recomputing or retuning the gain map. */
    private static boolean iris26645NearlyEqual(float a, float b) {
        if (!Float.isFinite(a) || !Float.isFinite(b)) return false;
        float scale = Math.max(1.0f, Math.max(Math.abs(a), Math.abs(b)));
        return Math.abs(a - b) <= 0.025f * scale;
    }

    private static boolean iris26645ArrayEquivalent(float[] expected, float[] actual) {
        if (expected == null || actual == null || expected.length < 3 || actual.length < 3) return false;
        for (int i = 0; i < 3; ++i) {
            if (!iris26645NearlyEqual(expected[i], actual[i])) return false;
        }
        return true;
    }

    private static boolean iris26645VerifyPlatformReadback(Path output, Gainmap expected) {
        Bitmap decoded = null;
        try {
            decoded = BitmapFactory.decodeFile(output.toAbsolutePath().toString());
            if (decoded == null || decoded.isRecycled() || !decoded.hasGainmap()) {
                Log.e(TAG, "IRIS_26645_HEIC_READBACK missing Android Gainmap");
                return false;
            }
            ColorSpace cs = decoded.getColorSpace();
            if (cs == null || !cs.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3))) {
                Log.e(TAG, "IRIS_26645_HEIC_READBACK base colorSpace="
                        + (cs == null ? "null" : cs.getName()));
                return false;
            }
            Gainmap actual = decoded.getGainmap();
            Bitmap expectedContents = expected.getGainmapContents();
            Bitmap actualContents = actual == null ? null : actual.getGainmapContents();
            boolean geometry = expectedContents != null && actualContents != null
                    && expectedContents.getWidth() == actualContents.getWidth()
                    && expectedContents.getHeight() == actualContents.getHeight();
            boolean metadata = actual != null
                    && iris26645ArrayEquivalent(expected.getRatioMin(), actual.getRatioMin())
                    && iris26645ArrayEquivalent(expected.getRatioMax(), actual.getRatioMax())
                    && iris26645ArrayEquivalent(expected.getGamma(), actual.getGamma())
                    && iris26645ArrayEquivalent(expected.getEpsilonSdr(), actual.getEpsilonSdr())
                    && iris26645ArrayEquivalent(expected.getEpsilonHdr(), actual.getEpsilonHdr())
                    && iris26645NearlyEqual(expected.getMinDisplayRatioForHdrTransition(),
                            actual.getMinDisplayRatioForHdrTransition())
                    && iris26645NearlyEqual(expected.getDisplayRatioForFullHdr(),
                            actual.getDisplayRatioForFullHdr());
            boolean ok = geometry && metadata;
            Log.critical(TAG, "IRIS_26645_HEIC_READBACK decoded=true hasGainmap=true"
                    + " p3=true geometry=" + geometry + " metadata=" + metadata
                    + " expectedRatioMax=" + java.util.Arrays.toString(expected.getRatioMax())
                    + " actualRatioMax=" + java.util.Arrays.toString(actual.getRatioMax())
                    + " expectedFull=" + expected.getDisplayRatioForFullHdr()
                    + " actualFull=" + actual.getDisplayRatioForFullHdr()
                    + " gainmap=" + (actualContents == null ? "null"
                    : actualContents.getWidth() + "x" + actualContents.getHeight())
                    + " saved=" + ok);
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26645_HEIC_READBACK_FAILED", t);
            return false;
        } finally {
            if (decoded != null && !decoded.isRecycled()) decoded.recycle();
        }
    }

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
            if (ok) ok = iris26645VerifyPlatformReadback(output, gm);
            if (!ok) Files.deleteIfExists(output);
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
