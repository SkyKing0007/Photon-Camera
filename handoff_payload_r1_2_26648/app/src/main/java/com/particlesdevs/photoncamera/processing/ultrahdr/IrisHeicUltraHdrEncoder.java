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

    private static final class Iris26648HdrStats {
        final double meanSdr;
        final double meanHdr;
        final double peakHdr;
        final int samples;
        Iris26648HdrStats(double meanSdr, double meanHdr, double peakHdr, int samples) {
            this.meanSdr = meanSdr; this.meanHdr = meanHdr; this.peakHdr = peakHdr; this.samples = samples;
        }
        double expansion() { return meanHdr / Math.max(meanSdr, 1.0e-8); }
    }

    private static double iris26648SrgbToLinear(int code) {
        double x = Math.max(0.0, Math.min(1.0, code / 255.0));
        return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    }

    private static double iris26648ApplyGain(double sdr, int gainCode, int channel, Gainmap metadata) {
        float[] rmin = metadata.getRatioMin();
        float[] rmax = metadata.getRatioMax();
        float[] gamma = metadata.getGamma();
        float[] es = metadata.getEpsilonSdr();
        float[] eh = metadata.getEpsilonHdr();
        int c = Math.max(0, Math.min(2, channel));
        double encoded = Math.max(0.0, Math.min(1.0, gainCode / 255.0));
        double shaped = Math.pow(encoded, Math.max(1.0e-6, gamma[c]));
        double lo = Math.log(Math.max(rmin[c], 1.0e-6));
        double hi = Math.log(Math.max(rmax[c], 1.0e-6));
        double gain = Math.exp(lo + shaped * (hi - lo));
        return Math.max(0.0, (sdr + es[c]) * gain - eh[c]);
    }

    /* IRIS_26648_NUMERICAL_ANDROID_GAINMAP_RECONSTRUCTION
     * Reconstruct a bounded grid of actual HDR samples using the Android Gainmap metadata equation.
     * This proves brightness expansion from decoded base+gain pixels rather than stopping at
     * hasGainmap=true. Display-P3 linear luma coefficients are used only for aggregate comparison. */
    private static Iris26648HdrStats iris26648HdrStats(Bitmap base, Bitmap gain, Gainmap metadata) {
        if (base == null || gain == null || metadata == null || base.isRecycled() || gain.isRecycled()) return null;
        int nx = Math.min(32, Math.max(4, base.getWidth()));
        int ny = Math.min(32, Math.max(4, base.getHeight()));
        double sdrSum = 0.0, hdrSum = 0.0, peak = 0.0;
        int count = 0;
        for (int iy = 0; iy < ny; ++iy) {
            int by = Math.min(base.getHeight() - 1, (int) (((iy + 0.5) * base.getHeight()) / ny));
            int gy = Math.min(gain.getHeight() - 1, (int) (((iy + 0.5) * gain.getHeight()) / ny));
            for (int ix = 0; ix < nx; ++ix) {
                int bx = Math.min(base.getWidth() - 1, (int) (((ix + 0.5) * base.getWidth()) / nx));
                int gx = Math.min(gain.getWidth() - 1, (int) (((ix + 0.5) * gain.getWidth()) / nx));
                int bp = base.getPixel(bx, by);
                int gp = gain.getPixel(gx, gy);
                double sr = iris26648SrgbToLinear((bp >>> 16) & 0xff);
                double sg = iris26648SrgbToLinear((bp >>> 8) & 0xff);
                double sb = iris26648SrgbToLinear(bp & 0xff);
                double hr = iris26648ApplyGain(sr, (gp >>> 16) & 0xff, 0, metadata);
                double hg = iris26648ApplyGain(sg, (gp >>> 8) & 0xff, 1, metadata);
                double hb = iris26648ApplyGain(sb, gp & 0xff, 2, metadata);
                double sdrY = 0.2289746 * sr + 0.6917385 * sg + 0.0792869 * sb;
                double hdrY = 0.2289746 * hr + 0.6917385 * hg + 0.0792869 * hb;
                sdrSum += sdrY; hdrSum += hdrY; peak = Math.max(peak, hdrY); count++;
            }
        }
        return count == 0 ? null : new Iris26648HdrStats(sdrSum / count, hdrSum / count, peak, count);
    }

    private static boolean iris26648HdrStatsAgree(Iris26648HdrStats expected, Iris26648HdrStats actual) {
        if (expected == null || actual == null || expected.samples == 0 || actual.samples == 0) return false;
        double meanScale = Math.max(0.02, expected.meanHdr);
        double peakScale = Math.max(0.05, expected.peakHdr);
        double expectedExpansion = expected.expansion();
        double actualExpansion = actual.expansion();
        boolean expectedNeedsExpansion = expectedExpansion > 1.005;
        boolean expansionConsistent = !expectedNeedsExpansion || actualExpansion > 1.005;
        return Math.abs(actual.meanHdr - expected.meanHdr) <= 0.15 * meanScale &&
                Math.abs(actual.peakHdr - expected.peakHdr) <= 0.25 * peakScale &&
                expansionConsistent;
    }

    private static boolean iris26646VerifyPlatformReadback(
            Path output, Gainmap expected, int expectedGainWidth, int expectedGainHeight,
            String publication, Bitmap expectedBasePreview, Bitmap expectedGainPreview) {
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
            boolean direction = actual != null && expected.getGainmapDirection() == Gainmap.GAINMAP_DIRECTION_SDR_TO_HDR
                    && actual.getGainmapDirection() == Gainmap.GAINMAP_DIRECTION_SDR_TO_HDR;
            ColorSpace actualAlternative = actual == null ? null : actual.getAlternativeImagePrimaries();
            boolean alternativePrimaries = actual != null && (actualAlternative == null ||
                    actualAlternative.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3)));
            boolean metadata = ratioMin && ratioMax && gamma && epsilonSdr && epsilonHdr && transition && full
                    && direction && alternativePrimaries;
            Iris26648HdrStats decodedHdr = actual == null || actualContents == null ? null
                    : iris26648HdrStats(decoded, actualContents, actual);
            Iris26648HdrStats expectedHdr = expectedBasePreview == null || expectedGainPreview == null ? null
                    : iris26648HdrStats(expectedBasePreview, expectedGainPreview, expected);
            boolean numericExpansion = decodedHdr != null && decodedHdr.expansion() > 1.005;
            boolean expectedNumericProof = expectedHdr != null;
            boolean expectedNeedsExpansion = expectedHdr != null && expectedHdr.expansion() > 1.005;
            boolean numericAgreement = expectedNumericProof && iris26648HdrStatsAgree(expectedHdr, decodedHdr);
            boolean recognized = decodedOk && hasGainmap && p3 && geometry && metadata && numericAgreement;
            Log.critical(TAG, "IRIS_26648_HEIC_NUMERICAL_HDR publication=" + publication
                    + " numericExpansion=" + numericExpansion + " expectedNumericProof=" + expectedNumericProof
                    + " expectedNeedsExpansion=" + expectedNeedsExpansion + " numericAgreement=" + numericAgreement
                    + " decodedMeanSdr=" + (decodedHdr == null ? Double.NaN : decodedHdr.meanSdr)
                    + " decodedMeanHdr=" + (decodedHdr == null ? Double.NaN : decodedHdr.meanHdr)
                    + " decodedPeakHdr=" + (decodedHdr == null ? Double.NaN : decodedHdr.peakHdr)
                    + " decodedExpansion=" + (decodedHdr == null ? Double.NaN : decodedHdr.expansion())
                    + " expectedMeanHdr=" + (expectedHdr == null ? Double.NaN : expectedHdr.meanHdr)
                    + " expectedPeakHdr=" + (expectedHdr == null ? Double.NaN : expectedHdr.peakHdr)
                    + " presentationProof=NUMERIC_ANDROID_RECONSTRUCTION externalViewerPresentation=SEPARATE");
            Log.critical(TAG, "IRIS_26646_HEIC_ANDROID_READBACK publication=" + publication
                    + " decoded=" + decodedOk + " hasGainmap=" + hasGainmap + " p3=" + p3
                    + " colorSpace=" + (cs == null ? "null" : cs.getName())
                    + " geometry=" + geometry + " expectedGain=" + expectedGainWidth + "x" + expectedGainHeight
                    + " actualGain=" + (actualContents == null ? "null"
                    : actualContents.getWidth() + "x" + actualContents.getHeight())
                    + " ratioMin=" + ratioMin + " ratioMax=" + ratioMax + " gamma=" + gamma
                    + " epsilonSdr=" + epsilonSdr + " epsilonHdr=" + epsilonHdr
                    + " transition=" + transition + " full=" + full
                    + " directionSdrToHdr=" + direction + " alternativePrimaries=" + alternativePrimaries
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
                        gainContents.getWidth(), gainContents.getHeight(), "MOTION_1X",
                        p3, gainContents);
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
            Bitmap expectedBasePreview = null;
            Bitmap expectedGainPreview = null;
            boolean recognized;
            try {
                BitmapFactory.Options preview = new BitmapFactory.Options();
                preview.inSampleSize = 16;
                expectedBasePreview = BitmapFactory.decodeFile(displayP3BaseJpeg.toString(), preview);
                BitmapFactory.Options gainPreview = new BitmapFactory.Options();
                gainPreview.inSampleSize = 16;
                expectedGainPreview = BitmapFactory.decodeFile(true2xGainJpeg.toString(), gainPreview);
                recognized = saved && iris26646VerifyPlatformReadback(
                        output, metadataOwner, width / 2, height / 2, "MOTION_TRUE2X_GRID",
                        expectedBasePreview, expectedGainPreview);
            } finally {
                if (expectedBasePreview != null && !expectedBasePreview.isRecycled()) expectedBasePreview.recycle();
                if (expectedGainPreview != null && !expectedGainPreview.isRecycled()) expectedGainPreview.recycle();
            }
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
