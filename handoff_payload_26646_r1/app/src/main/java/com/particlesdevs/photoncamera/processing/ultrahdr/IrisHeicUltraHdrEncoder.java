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

    /* IRIS_26646_ANDROID_HEIC_ULTRAHDR_READBACK_PROOF
     * Android recognition remains an end-to-end proof, but never destroys a successfully encoded
     * camera photo.  Log every individual contract field so a vendor/container mismatch is directly
     * actionable.  Super-Res supplies its expected half-linear gain-map geometry explicitly. */
    private static boolean iris26646NearlyEqual(float a, float b) {
        if (!Float.isFinite(a) || !Float.isFinite(b)) return false;
        float scale = Math.max(1.0f, Math.max(Math.abs(a), Math.abs(b)));
        return Math.abs(a - b) <= 0.025f * scale;
    }

    private static boolean iris26646ArrayEquivalent(float[] expected, float[] actual) {
        if (expected == null || actual == null || expected.length < 3 || actual.length < 3) return false;
        for (int i = 0; i < 3; ++i) if (!iris26646NearlyEqual(expected[i], actual[i])) return false;
        return true;
    }

    private static boolean iris26646VerifyPlatformReadback(
            Path output, Gainmap expected, int expectedGainWidth, int expectedGainHeight,
            String publication) {
        Bitmap decoded = null;
        try {
            decoded = BitmapFactory.decodeFile(output.toAbsolutePath().toString());
            boolean decodedOk = decoded != null && !decoded.isRecycled();
            boolean hasGainmap = decodedOk && decoded.hasGainmap();
            ColorSpace cs = decodedOk ? decoded.getColorSpace() : null;
            boolean p3 = cs != null && cs.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            Gainmap actual = hasGainmap ? decoded.getGainmap() : null;
            Bitmap actualContents = actual == null ? null : actual.getGainmapContents();
            boolean geometry = actualContents != null
                    && actualContents.getWidth() == expectedGainWidth
                    && actualContents.getHeight() == expectedGainHeight;
            boolean ratioMin = actual != null && iris26646ArrayEquivalent(expected.getRatioMin(), actual.getRatioMin());
            boolean ratioMax = actual != null && iris26646ArrayEquivalent(expected.getRatioMax(), actual.getRatioMax());
            boolean gamma = actual != null && iris26646ArrayEquivalent(expected.getGamma(), actual.getGamma());
            boolean epsilonSdr = actual != null && iris26646ArrayEquivalent(expected.getEpsilonSdr(), actual.getEpsilonSdr());
            boolean epsilonHdr = actual != null && iris26646ArrayEquivalent(expected.getEpsilonHdr(), actual.getEpsilonHdr());
            boolean transition = actual != null && iris26646NearlyEqual(
                    expected.getMinDisplayRatioForHdrTransition(), actual.getMinDisplayRatioForHdrTransition());
            boolean full = actual != null && iris26646NearlyEqual(
                    expected.getDisplayRatioForFullHdr(), actual.getDisplayRatioForFullHdr());
            boolean metadata = ratioMin && ratioMax && gamma && epsilonSdr && epsilonHdr && transition && full;
            boolean recognized = decodedOk && hasGainmap && p3 && geometry && metadata;
            Log.critical(TAG, "IRIS_26646_HEIC_ANDROID_READBACK publication=" + publication
                    + " decoded=" + decodedOk + " hasGainmap=" + hasGainmap + " p3=" + p3
                    + " colorSpace=" + (cs == null ? "null" : cs.getName())
                    + " geometry=" + geometry + " expectedGain=" + expectedGainWidth + "x" + expectedGainHeight
                    + " actualGain=" + (actualContents == null ? "null"
                    : actualContents.getWidth() + "x" + actualContents.getHeight())
                    + " ratioMin=" + ratioMin + " ratioMax=" + ratioMax + " gamma=" + gamma
                    + " epsilonSdr=" + epsilonSdr + " epsilonHdr=" + epsilonHdr
                    + " transition=" + transition + " full=" + full
                    + " expectedRatioMax=" + java.util.Arrays.toString(expected.getRatioMax())
                    + " actualRatioMax=" + (actual == null ? "null" : java.util.Arrays.toString(actual.getRatioMax()))
                    + " expectedFull=" + expected.getDisplayRatioForFullHdr()
                    + " actualFull=" + (actual == null ? Float.NaN : actual.getDisplayRatioForFullHdr())
                    + " recognizedUltraHdr=" + recognized + " destructiveFailure=false");
            return recognized;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26646_HEIC_ANDROID_READBACK_FAILED publication=" + publication
                    + " destructiveFailure=false", t);
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
            boolean recognized = false;
            if (ok) {
                Bitmap gainContents = gm.getGainmapContents();
                recognized = iris26646VerifyPlatformReadback(output, gm,
                        gainContents.getWidth(), gainContents.getHeight(), "MOTION_1X");
            }
            Log.i(TAG, "IRIS_26646_HEIC_ULTRAHDR_RESULT saved=" + ok
                    + " androidRecognizedUltraHdr=" + recognized
                    + " readbackFailureNonDestructive=true p3=true existingGainmap=true"
                    + " recomputedGainmap=false path=" + output);
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26636_HEIC_ULTRAHDR_FAILED", t);
            try { Files.deleteIfExists(output); } catch (Throwable ignored) {}
            return false;
        } finally {
            if (!p3.isRecycled()) p3.recycle();
        }
    }

    /** IRIS_26646_TRUE2X_HEIC_ULTRAHDR_GRID_PUBLICATION
     * Consumes the already-rendered true-2x Display-P3 SDR JPEG and its true-2x logarithmic gain
     * JPEG. Native publication tiles only the SDR base for hardware HEVC limits and box-filters the
     * logarithmic gain codes to half-linear primary resolution. No scene reconstruction occurs here. */
    public static boolean writeSuperResGrid(
            Path output, Path displayP3BaseJpeg, Path true2xGainJpeg,
            int width, int height, Gainmap metadataOwner, int quality, ParseExif.ExifData exif) {
        if (Build.VERSION.SDK_INT < 36 || output == null || displayP3BaseJpeg == null
                || true2xGainJpeg == null || metadataOwner == null
                || width <= 0 || height <= 0 || (width & 3) != 0 || (height & 3) != 0
                || !Files.isRegularFile(displayP3BaseJpeg) || !Files.isRegularFile(true2xGainJpeg)
                || !IrisHardwareHevcEncoder.isHeicUltraHdrAvailable()) return false;
        float[] rmin = metadataOwner.getRatioMin();
        float[] rmax = metadataOwner.getRatioMax();
        float[] gamma = metadataOwner.getGamma();
        float[] es = metadataOwner.getEpsilonSdr();
        float[] eh = metadataOwner.getEpsilonHdr();
        if (rmin.length < 3 || rmax.length < 3 || gamma.length < 3 || es.length < 3 || eh.length < 3)
            return false;
        try {
            Path parent = output.toAbsolutePath().getParent();
            if (parent != null) Files.createDirectories(parent);
            Files.deleteIfExists(output);
            boolean saved = writeSuperResGridNative(
                    displayP3BaseJpeg.toAbsolutePath().toString(),
                    true2xGainJpeg.toAbsolutePath().toString(),
                    width, height, output.toAbsolutePath().toString(),
                    Math.max(1, Math.min(100, quality)), rmin, rmax, gamma, es, eh,
                    metadataOwner.getMinDisplayRatioForHdrTransition(),
                    metadataOwner.getDisplayRatioForFullHdr(),
                    exif == null ? null : exif.PHOTOGRAPHIC_SENSITIVITY,
                    exif == null ? null : exif.F_NUMBER,
                    exif == null ? null : exif.FOCAL_LENGTH,
                    exif == null ? null : exif.EXPOSURE_TIME,
                    exif == null ? null : exif.DATETIME,
                    exif == null ? null : exif.MAKE,
                    exif == null ? null : exif.MODEL);
            saved &= Files.isRegularFile(output) && Files.size(output) > 0L;
            boolean recognized = saved && iris26646VerifyPlatformReadback(
                    output, metadataOwner, width / 2, height / 2, "MOTION_TRUE2X_GRID");
            Log.critical(TAG, "IRIS_26646_TRUE2X_HEIC_RESULT saved=" + saved
                    + " grid=2x2 base=" + width + "x" + height
                    + " gain=" + (width / 2) + "x" + (height / 2)
                    + " androidRecognizedUltraHdr=" + recognized
                    + " readbackFailureNonDestructive=true hardwareHevc=true");
            return saved;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26646_TRUE2X_HEIC_FAILED", t);
            return false;
        }
    }

    private static native boolean writeSuperResGridNative(
            String displayP3BaseJpeg, String true2xGainJpeg,
            int width, int height, String path, int quality,
            float[] ratioMin, float[] ratioMax, float[] gamma,
            float[] epsilonSdr, float[] epsilonHdr,
            float minDisplayRatio, float fullDisplayRatio,
            String iso, String fNumber, String focalLength, String exposureTime,
            String dateTime, String make, String model);

    private static native boolean writeNative(
            Bitmap displayP3Base, Bitmap gainMap, String path, int quality,
            float[] ratioMin, float[] ratioMax, float[] gamma,
            float[] epsilonSdr, float[] epsilonHdr,
            float minDisplayRatio, float fullDisplayRatio,
            String iso, String fNumber, String focalLength, String exposureTime,
            String dateTime, String make, String model);
}
