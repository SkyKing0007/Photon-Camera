package com.particlesdevs.photoncamera.processing.parameters;

import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.graphics.Rect;
import android.util.SizeF;
import com.particlesdevs.photoncamera.util.Log;
import android.util.Range;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public class IsoExpoSelector {
    public static final int baseFrame = 1;
    private static final String TAG = "IsoExpoSelector";
    public static boolean HDR = false;
    public static boolean useTripod = false;
    public static final int patternSize = 3;
    public static ArrayList<ExpoPair> pairs = new ArrayList<>();
    public static ArrayList<ExpoPair> fullpairs = new ArrayList<>();
    public static long lastSelectedExposure = 0;

    // Shutter-Priority AE Curve Constants (Google Camera style)
    private static final long HANDHELD_PHOTO_LIMIT = ExposureIndex.sec / 10;  // 1/10s
    private static final long HANDHELD_MOTION_LIMIT = ExposureIndex.sec / 15; // 1/15s
    private static final long HANDHELD_NIGHT_LIMIT = ExposureIndex.sec / 10;  // 1/10s

    private static final long TRIPOD_PHOTO_LIMIT = ExposureIndex.sec;      // 1s
    private static final long TRIPOD_NIGHT_LIMIT = ExposureIndex.sec;      // 1s
    private static final long TRIPOD_MOTION_LIMIT = ExposureIndex.sec / 4; // 1/4s

    public static void setExpo(CaptureRequest.Builder builder, int step, CaptureController captureController) {
        Log.v(TAG, "InputParams: " +
                "expo time:" + ExposureIndex.sec2string(ExposureIndex.time2sec(captureController.mPreviewExposureTime)) +
                " iso:" + captureController.mPreviewIso+ " analog:"+getISOAnalog());
        if(step == 0) fullpairs.clear();
        ExpoPair pair = GenerateExpoPair(step,captureController);
        fullpairs.add(pair);
        Log.v(TAG, "IsoSelected:" + pair.iso +
                " ExpoSelected:" + ExposureIndex.sec2string(ExposureIndex.time2sec(pair.exposure)) + " sec step:" + step + " HDR:" + HDR + " total exposure:" + ExposureIndex.time2sec(pair.exposure)*pair.iso);

        builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
        builder.set(CaptureRequest.SENSOR_EXPOSURE_TIME, pair.exposure);
        builder.set(CaptureRequest.SENSOR_SENSITIVITY, (int)pair.iso);
        lastSelectedExposure = pair.exposure;
    }
    private static final double FULL_FRAME_DIAGONAL_MM =
            Math.hypot(36.0, 24.0);

    private static final Set<String> MAINS_60_HZ_COUNTRIES =
            new HashSet<>(Arrays.asList(
                    "US", "CA", "MX", "BR", "CO", "CR", "CU",
                    "DO", "EC", "GT", "HN", "NI", "PA", "PE",
                    "PR", "SV", "TW", "KR", "PH", "SA"
            ));

    /**
     * Calculates effective 35 mm-equivalent focal length from the active
     * physical camera metadata and its current crop region.
     */
    private static double getEffective35mmFocalLength(
            CaptureController captureController
    ) {
        try {
            CameraCharacteristics characteristics =
                    CaptureController.getActiveCameraCharacteristics();

            if (characteristics == null) {
                return Double.NaN;
            }

            SizeF sensorSize = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE
            );

            if (sensorSize == null
                    || sensorSize.getWidth() <= 0.0f
                    || sensorSize.getHeight() <= 0.0f) {
                return Double.NaN;
            }

            Float focalLength = null;

            if (CaptureController.mPreviewCaptureResult != null) {
                focalLength = CaptureController.mPreviewCaptureResult.get(
                        CaptureResult.LENS_FOCAL_LENGTH
                );
            }

            if (focalLength == null || focalLength <= 0.0f) {
                float[] focalLengths = characteristics.get(
                        CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS
                );

                if (focalLengths == null
                        || focalLengths.length == 0
                        || focalLengths[0] <= 0.0f) {
                    return Double.NaN;
                }

                focalLength = focalLengths[0];
            }

            double sensorDiagonal = Math.hypot(
                    sensorSize.getWidth(),
                    sensorSize.getHeight()
            );

            if (!Double.isFinite(sensorDiagonal)
                    || sensorDiagonal <= 0.0) {
                return Double.NaN;
            }

            double nativeEquivalent =
                    focalLength
                            * FULL_FRAME_DIAGONAL_MM
                            / sensorDiagonal;

            double residualCropZoom = 1.0;

            Rect activeArray = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE
            );

            Rect cropRegion = null;

            if (CaptureController.mPreviewCaptureResult != null) {
                cropRegion = CaptureController.mPreviewCaptureResult.get(
                        CaptureResult.SCALER_CROP_REGION
                );
            }

            if (activeArray != null
                    && cropRegion != null
                    && activeArray.width() > 0
                    && cropRegion.width() > 0) {
                residualCropZoom = Math.max(
                        1.0,
                        (double) activeArray.width()
                                / cropRegion.width()
                );

                // Guard against broken vendor crop metadata.
                residualCropZoom = Math.min(
                        residualCropZoom,
                        20.0
                );
            }

            double effectiveEquivalent =
                    nativeEquivalent * residualCropZoom;

            if (!Double.isFinite(effectiveEquivalent)
                    || effectiveEquivalent < 8.0
                    || effectiveEquivalent > 500.0) {
                return Double.NaN;
            }

            return effectiveEquivalent;
        } catch (Exception exception) {
            Log.w(
                    TAG,
                    "Unable to calculate effective focal length",
                    exception
            );
            return Double.NaN;
        }
    }

    /**
     * Creates a deliberately permissive handheld shutter ceiling that still
     * becomes faster as effective focal length increases.
     */
    private static long getFocalLengthAwareLimit(
            CameraMode selectedMode,
            double equivalentFocalLength,
            long fallbackLimit
    ) {
        if (!Double.isFinite(equivalentFocalLength)) {
            return fallbackLimit;
        }

        double denominator;

        if (selectedMode == CameraMode.MOTION) {
            denominator = clamp(
                    equivalentFocalLength / 3.0,
                    15.0,
                    80.0
            );
        } else {
            denominator = clamp(
                    equivalentFocalLength / 4.0,
                    10.0,
                    60.0
            );
        }

        long limit = (long) (
                ExposureIndex.sec / denominator
        );

        Log.d(
                TAG,
                "Focal-aware AE: mode=" + selectedMode
                        + " equivalent="
                        + String.format(
                                Locale.US,
                                "%.1fmm",
                                equivalentFocalLength
                        )
                        + " shutterLimit="
                        + ExposureIndex.sec2string(
                                ExposureIndex.time2sec(limit)
                        )
        );

        return limit;
    }

    /**
     * Reads the preview AE anti-banding result where possible. If the HAL
     * reports AUTO or nothing, use a locale-based fallback.
     */
    private static int detectMainsFrequencyHz() {
        try {
            if (CaptureController.mPreviewCaptureResult != null) {
                Integer antiBanding =
                        CaptureController.mPreviewCaptureResult.get(
                                CaptureResult.CONTROL_AE_ANTIBANDING_MODE
                        );

                if (antiBanding != null) {
                    if (antiBanding
                            == CaptureResult
                            .CONTROL_AE_ANTIBANDING_MODE_50HZ) {
                        return 50;
                    }

                    if (antiBanding
                            == CaptureResult
                            .CONTROL_AE_ANTIBANDING_MODE_60HZ) {
                        return 60;
                    }
                }
            }
        } catch (Exception ignored) {
        }

        String country = Locale.getDefault().getCountry();

        return MAINS_60_HZ_COUNTRIES.contains(country)
                ? 60
                : 50;
    }

    /**
     * For most mains-powered lighting, brightness modulation occurs at twice
     * mains frequency. Round down to a whole modulation period so the snapped
     * exposure is never slower than the blur-safe limit.
     */
    private static long snapExposureForFlicker(
            long exposureLimit,
            int mainsFrequencyHz
    ) {
        if (exposureLimit <= 0
                || (mainsFrequencyHz != 50
                && mainsFrequencyHz != 60)) {
            return exposureLimit;
        }

        long flickerPeriodNs = Math.round(
                1_000_000_000.0
                        / (2.0 * mainsFrequencyHz)
        );

        // If the focal-length limit is faster than one full flicker period,
        // retain it rather than making the exposure slower.
        if (exposureLimit < flickerPeriodNs) {
            return exposureLimit;
        }

        long periods = Math.max(
                1L,
                exposureLimit / flickerPeriodNs
        );

        long snapped = periods * flickerPeriodNs;

        Log.d(
                TAG,
                "Anti-flicker AE: mains="
                        + mainsFrequencyHz
                        + "Hz requested="
                        + ExposureIndex.sec2string(
                                ExposureIndex.time2sec(exposureLimit)
                        )
                        + " snapped="
                        + ExposureIndex.sec2string(
                                ExposureIndex.time2sec(snapped)
                        )
        );

        return Math.min(snapped, exposureLimit);
    }

    private static double clamp(
            double value,
            double minimum,
            double maximum
    ) {
        return Math.max(
                minimum,
                Math.min(maximum, value)
        );
    }

    private static double mpy1 = 1.0;
    public static ExpoPair GenerateExpoPair(int step, CaptureController captureController) {
        ExpoPair pair = new ExpoPair(captureController.mPreviewExposureTime, getEXPLOW(), getEXPHIGH(),
                captureController.mPreviewIso, getISOLOW(), getISOHIGH(),getISOAnalog());
        double compensation = Math.pow(2.0,PhotonCamera.getSettings().exposureCompensation);
        pair.normalizeiso100();
        pair.ExpoCompensateLower(1.0/compensation);

        // Apply Shutter-Priority AE Curve (HDR+ E behavior)
        CameraMode selectedMode = PhotonCamera.getSettings().selectedMode;
        long fallbackHandheldLimit;
        long tripodLimit;

        if (selectedMode == CameraMode.NIGHT) {
            fallbackHandheldLimit = HANDHELD_NIGHT_LIMIT;
            tripodLimit = TRIPOD_NIGHT_LIMIT;
        } else if (selectedMode == CameraMode.MOTION) {
            fallbackHandheldLimit = HANDHELD_MOTION_LIMIT;
            tripodLimit = TRIPOD_MOTION_LIMIT;
        } else {
            fallbackHandheldLimit = HANDHELD_PHOTO_LIMIT;
            tripodLimit = TRIPOD_PHOTO_LIMIT;
        }

        // Calculate the effective 35 mm-equivalent focal length of the
        // currently active camera, including residual digital crop.
        double equivalentFocalLength =
                getEffective35mmFocalLength(captureController);

        long focalLengthLimit = getFocalLengthAwareLimit(
                selectedMode,
                equivalentFocalLength,
                fallbackHandheldLimit
        );

        // RAW video keeps its existing exposure behavior and must not inherit
        // long tripod exposure ceilings intended for computational photos.
        boolean tripodAllowed =
                useTripod && selectedMode != CameraMode.RAWVIDEO;

        long maxExposure =
                tripodAllowed ? tripodLimit : focalLengthLimit;

        // Snap manual exposure to the local lighting flicker period without
        // ever selecting a slower shutter than the calculated blur ceiling.
        int mainsFrequencyHz = detectMainsFrequencyHz();
        maxExposure = snapExposureForFlicker(
                maxExposure,
                mainsFrequencyHz
        );

        Log.d(TAG, "AE stability: mode=" + selectedMode
                + " tripodDetected=" + useTripod
                + " tripodAllowed=" + tripodAllowed
                + " maxExposure="
                + ExposureIndex.sec2string(
                        ExposureIndex.time2sec(maxExposure)));

        pair.applyShutterPriorityCurve(maxExposure);

        if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT)
        {
            mpy1 = 7000.0;
            //if(step%3 == 2) mpy = 1.1;
            //mpy = mpy*1.5;
        } else {
             /*else if(PhotonCamera.getSettings().alignAlgorithm == 1){
                if(step%3 == 1) {
                    pair.curlayer = ExpoPair.exposureLayer.High;
                    mpy = 1.0/1.5;
                }
                if(step%3 == 2) {
                    pair.curlayer = ExpoPair.exposureLayer.Normal;
                    mpy = 1.0;
                }
                if(step%3 == 0) {
                    pair.curlayer = ExpoPair.exposureLayer.Low;
                    mpy = 1.5;
                }
            }*/
            mpy1 = 3000.0;
        }
        if(PhotonCamera.getSettings().selectedMode == CameraMode.MOTION || PhotonCamera.getSettings().selectedMode == CameraMode.RAWVIDEO){
            //mpy1 = 0.0;
            pair.denormalizeSystem();
            return pair;
        }

        if (pair.normalizedIso() >= 12700.0/mpy1) {
            pair.ReduceIso();
        }
        if (useTripod) {
            // pair.UseIso(Math.max(pair.isoanalog/6.0,101)); // Replaced by applyShutterPriorityCurve
        }

        double currentManExp = captureController.getParamController().getCurrentExposureValue();
        double currentManISO = captureController.getParamController().getCurrentISOValue();
        pair.exposure = currentManExp != 0 ? (long) currentManExp : pair.exposure;
        pair.iso = currentManISO != 0 ? (int) (currentManISO * 100.0 / pair.isolow) : pair.iso;
        pair.curlayer = ExpoPair.exposureLayer.Normal;
        /*if (step%patternSize == 1 && HDR) {
            pair.ExpoCompensateLower(2.0 / 1.0);
            pair.curlayer = ExpoPair.exposureLayer.Low;
        }*/
        /*if(HDR) {
            pair.ExpoCompensateLowerExpo(2.f);
            pair.ExpoCompensateLower(1.f/2.f);
        }*/
        if (step%patternSize == 0 && HDR) {
            // Set multiplier based on bracketing mode (0=Off, 1=Normal, 2=High)
            int bracketingMode = PreferenceKeys.getBracketingMode();
            pair.layerMpy = 1.f;
            if (bracketingMode == 1) {
                // Normal bracketing (1x, 4x)
                pair.layerMpy = 4.f;
            } else if (bracketingMode == 2) {
                // High bracketing (1x, 8x)
                pair.layerMpy = 8.f;
            }
            
            if (pair.layerMpy > 1.f) {
                pair.curlayer = ExpoPair.exposureLayer.High;
                if (pair.ExpoCompensateLowerExpo2(1.0 / pair.layerMpy)) {
                    pair.layerMpy = 1.f;
                    pair.curlayer = ExpoPair.exposureLayer.Normal;
                }
            } else {
                pair.curlayer = ExpoPair.exposureLayer.Normal;
            }
        }
        if ((step%patternSize == 1) && HDR) {
            pair.layerMpy = 1.f;
            pair.ExpoCompensateLowerExpo2(1.0 / pair.layerMpy);
            pair.curlayer = ExpoPair.exposureLayer.Normal;
        }
        if (step%patternSize == 2 && HDR) {
            pair.layerMpy = 1.f;
            pair.ExpoCompensateLowerExpo2(1.0 / pair.layerMpy);
            pair.curlayer = ExpoPair.exposureLayer.Normal;
        }

        if (pair.exposure < ExposureIndex.sec / 90 && PhotonCamera.getSettings().eisPhoto) {
            //HDR = true;
        }
        
        if(step != -1) {
            if (step == 0) pairs.clear();
            if (pairs.size() < patternSize) {
                Log.d(TAG, "Added pair:" + pairs.size());
                pairs.add(pair);
            }
        }
        pair.denormalizeSystem();
        return pair;
    }

    public static double getMPY() {
        return 100.0 / getISOLOW();
    }

    private static int mpyIso(int in) {
        return (int) (in * getMPY());
    }

    private static int getISOHIGH() {
        Object key = CaptureController.getActiveCameraCharacteristics().get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        if (key == null) return 3200;
        else {
            return (int) ((Range) (key)).getUpper();
        }
    }

    public static int getISOHIGHExt() {
        return mpyIso(getISOHIGH());
    }

    private static int getISOLOW() {
        Object key = CaptureController.getActiveCameraCharacteristics().get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        if (key == null) return 100;
        else {
            return (int) ((Range) (key)).getLower();
        }
    }
    public static int getISOAnalog() {
        Object key = CaptureController.getActiveCameraCharacteristics().get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
        if (key == null) return 100;
        else {
            return (int)(key);
        }
    }

    public static int getISOLOWExt() {
        return mpyIso(getISOLOW());
    }

    public static long getEXPHIGH() {
        Object key = CaptureController.getActiveCameraCharacteristics().get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        if (key == null) return ExposureIndex.sec;
        else {
            return (long) ((Range) (key)).getUpper();
        }
    }

    public static long getEXPLOW() {
        Object key = CaptureController.getActiveCameraCharacteristics().get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        if (key == null) return ExposureIndex.sec / 1000;
        else {
            return (long) ((Range) (key)).getLower();
        }
    }


    //==================================Class : ExpoPair==================================//

    public static class ExpoPair {
        public enum exposureLayer{
            Low,
            Normal,
            High
        }
        public exposureLayer curlayer;
        public float layerMpy = 1.f;
        public long exposure;
        public int iso;
        long exposurehigh, exposurelow;
        int isolow, isohigh,isoanalog;

        public ExpoPair(ExpoPair pair) {
            copyfrom(pair);
        }

        public ExpoPair(long expo, long expl, long exph, int is, int islow, int ishigh, int analog) {
            exposure = expo;
            iso = is;
            exposurehigh = exph;
            exposurelow = expl;
            isolow = islow;
            isohigh = ishigh;
            isoanalog = analog;
        }
        public double Exposure(){
            return ExposureIndex.time2sec(exposure)*iso;
        }
        public void copyfrom(ExpoPair pair) {
            exposure = pair.exposure;
            exposurelow = pair.exposurelow;
            exposurehigh = pair.exposurehigh;
            iso = pair.iso;
            isolow = pair.isolow;
            isohigh = pair.isohigh;
            isoanalog = pair.isoanalog;
        }

        public void normalizeiso100() {
            double mpy = 100.0 / isolow;
            iso *= mpy;
            isoanalog *=mpy;
        }

        public void denormalizeSystem() {
            double div = 100.0 / isolow;
            iso /= div;
            isoanalog /=div;
        }
        public float normalizedIso(){
            return (float)iso/isoanalog;
        }
        public void normalize() {
            double div = 100.0 / isolow;
            if (iso / div > isohigh) iso = isohigh;
            if (iso / div < isolow) iso = isolow;
            if (exposure > exposurehigh) exposure = exposurehigh;
            if (exposure < exposurelow) exposure = exposurelow;
        }

        public boolean normalizeCheck() {
            double div = 100.0 / isolow;
            boolean wrongparams = false;
            if (iso / div > isohigh) wrongparams = true;
            if (iso / div < isolow) wrongparams = true;
            if (exposure > exposurehigh) wrongparams = true;
            if (exposure < exposurelow) wrongparams = true;
            return wrongparams;
        }

        public void normalizeISO(){
            double div = 100.0 / isolow;
            if (iso / div > isohigh) {
                double mpy = (iso / div) / isohigh;
                exposure = (long) (exposure * mpy);
                iso = isohigh;
            }
        }

        public void ExpoCompensateLower(double k) {
            iso /= k;
            normalizeISO();
            if (normalizeCheck()) {
                iso *= k;
                exposure /= k;
                if (normalizeCheck()) {
                    exposure *= k;
                    layerMpy = 1.f;
                }
            }
        }

        /**
         * Redistributes total exposure energy using a Shutter-Priority strategy.
         * Prioritizes increasing exposure time up to maxExposure before increasing ISO.
         */
        public void applyShutterPriorityCurve(long maxExposure) {
            double totalExposureEnergy = (double) exposure * iso;
            
            // Step 1: Set ISO to minimum to prioritize photon capture quality
            // Note: 100 is the base for normalized ISO (corresponds to sensor's isolow)
            iso = 100; 
            
            // Step 2: Calculate required exposure time at minimum ISO
            exposure = (long) (totalExposureEnergy / iso);
            
            // Step 3: If calculated exposure exceeds limit, cap it and increase ISO
            if (exposure > maxExposure) {
                exposure = Math.min(maxExposure, exposurehigh);
                iso = (int) (totalExposureEnergy / exposure);
            }
            
            // Final safety normalization
            normalize();
            Log.v("IsoExpoSelector", "Applied Curve: Energy=" + (long)totalExposureEnergy + 
                " -> Result: Exp=" + ExposureIndex.sec2string(ExposureIndex.time2sec(exposure)) + 
                " ISO=" + iso);
        }

        public void ExpoCompensateLowerExpo(double k) {
            iso /= k;
            if (normalizeCheck()) {
                iso *= k;
                exposure /= k;
                if(normalizeCheck()){
                    exposure *= k;
                    exposure /= Math.sqrt(k);
                    iso /= Math.sqrt(k);
                    if (normalizeCheck()) {
                        exposure *= Math.sqrt(k);
                        iso *= Math.sqrt(k);
                    }
                }
            }
        }

        public boolean ExpoCompensateLowerExpo2(double k) {
            exposure /= k;
            if (normalizeCheck()) {
                exposure *= k;
                iso /= k;
                if(normalizeCheck()){
                    iso *= k;
                    iso /= Math.sqrt(k);
                    exposure /= Math.sqrt(k);
                    if (normalizeCheck()) {
                        iso *= Math.sqrt(k);
                        exposure *= Math.sqrt(k);
                    }
                }
            }
            return normalizeCheck();
        }

        public void MinIso() {
            UseIso(100);
        }

        public void UseIso(double isoUsed) {
            double k = iso / isoUsed;
            ReduceIso(k);
            if (normalizeCheck()) {
                iso *= (double) (exposure) / exposurehigh;
                exposure = exposurehigh;
                if (normalizeCheck()) {
                    iso = isohigh;
                }
            }
        }

        public void ReduceIso() {
            ReduceIso(2.0);
            if (normalizeCheck()) {
                ReduceIso(1.0 / 2);
            }
        }

        public void ReduceIso(double k) {
            iso /= k;
            exposure *= k;
        }

        public void ReduceExpo() {
            ReduceExpo(2.0);
            if (normalizeCheck()) ReduceExpo(1.0 / 2);
        }

        public void ReduceExpo(double k) {
            Log.d(TAG, "ExpoReducing iso:" + iso + " expo:" + ExposureIndex.sec2string(ExposureIndex.time2sec(exposure)));
            iso *= k;
            exposure /= k;
            Log.d(TAG, "ExpoReducing done iso:" + iso + " expo:" + ExposureIndex.sec2string(ExposureIndex.time2sec(exposure)));
        }

        public void FixedExpo(double expo) {
            long expol = ExposureIndex.sec2time(expo);
            double k = (double) exposure / expol;
            ReduceExpo(k);
            Log.d(TAG, "ExpoFixating iso:" + iso + " expo:" + ExposureIndex.sec2string(ExposureIndex.time2sec(exposure)));
            if (normalizeCheck()) ReduceExpo(1 / k);
        }

        public String ExposureString() {
            return ExposureIndex.sec2string(ExposureIndex.time2sec(exposure));
        }
    }
}
