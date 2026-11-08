package com.particlesdevs.photoncamera.processing.parameters;

import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.util.Range;

import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.util.Log;

/** IRIS_26552_NIGHT_DYNAMIC_EXPOSURE_SOLE_OWNER
 * Night exposure classes are frozen once at shutter time. SHORT frames preserve the proven
 * 26540 highlight/motion-safe target and own geometry. When the frozen frame plan requests LONG
 * evidence, LONG keeps the same ISO and adds real integration time, bounded by shake/sensor limits.
 * No Photon IsoExpoSelector, Motion ZSL state, or pre-shutter RAW participates.
 */
public final class IrisNightExposureSelector {
    private static final String TAG = "IrisNightExposure";
    private static final double LONG_TARGET_MULTIPLIER = 4.0; // +2 EV nominal; capped adaptively.
    private static final long IRIS_26908_AUTO_SHUTTER_CEILING_NS = 100_000_000L; // 1/10 s

    public static final class Plan {
        // Compatibility aliases: the reference/short cohort remains the primary Night exposure.
        public final long exposureNs;
        public final int iso;
        public final long shortExposureNs;
        public final int shortIso;
        public final long longExposureNs;
        public final int longIso;
        public final double longToShortEnergyRatio;
        public final long exposureLowNs;
        public final long exposureHighNs;
        public final int isoLow;
        public final int isoHigh;
        public final int analogIso;
        public final boolean tripod;
        public final int shakiness;
        public final int antibandingMode;

        Plan(long shortExposureNs, int shortIso, long longExposureNs, int longIso,
             long exposureLowNs, long exposureHighNs, int isoLow, int isoHigh, int analogIso,
             boolean tripod, int shakiness, int antibandingMode) {
            this.exposureNs = shortExposureNs;
            this.iso = shortIso;
            this.shortExposureNs = shortExposureNs;
            this.shortIso = shortIso;
            this.longExposureNs = longExposureNs;
            this.longIso = longIso;
            this.longToShortEnergyRatio =
                    (longExposureNs * (double) longIso) /
                    Math.max(1.0, shortExposureNs * (double) shortIso);
            this.exposureLowNs = exposureLowNs;
            this.exposureHighNs = exposureHighNs;
            this.isoLow = isoLow;
            this.isoHigh = isoHigh;
            this.analogIso = analogIso;
            this.tripod = tripod;
            this.shakiness = shakiness;
            this.antibandingMode = antibandingMode;
        }
    }

    private IrisNightExposureSelector() {}

    private static long clamp(long v, long lo, long hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    // Exact 26540 short/reference motion cap.
    private static long shortMotionCap(boolean tripod, int shakiness, long sensorHigh) {
        if (tripod) return Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS);
        if (shakiness <= 30) return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 4L);
        if (shakiness <= 70) return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 8L);
        if (shakiness <= 150) return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 15L);
        return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 30L);
    }

    // Long frames are deliberately allowed more integration, but shake still bounds them.
    private static long longMotionCap(boolean tripod, int shakiness, long sensorHigh) {
        if (tripod) return Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS);
        if (shakiness <= 30) return Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS);
        if (shakiness <= 70) return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 2L);
        if (shakiness <= 150) return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 4L);
        return Math.min(Math.min(sensorHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS), ExposureIndex.sec / 8L);
    }

    private static long antiFlicker(long desired, long cap, int antibandingMode) {
        long q = antibandingMode == CaptureResult.CONTROL_AE_ANTIBANDING_MODE_50HZ
                ? ExposureIndex.sec / 100L : ExposureIndex.sec / 120L;
        desired = Math.min(desired, cap);
        if (desired < q) return desired;
        long n = Math.max(1L, Math.round((double) desired / q));
        while (n * q > cap && n > 1L) n--;
        return n * q;
    }

    public static Plan freezePlan(CaptureController controller,
                                  CameraCharacteristics characteristics,
                                  float exposureCompensationEv,
                                  boolean tripod,
                                  int shakiness,
                                  CaptureResult previewResult) {
        return freezePlan(controller, characteristics, exposureCompensationEv, tripod, shakiness,
                previewResult, true, false);
    }

    public static Plan freezePlan(CaptureController controller,
                                  CameraCharacteristics characteristics,
                                  float exposureCompensationEv,
                                  boolean tripod,
                                  int shakiness,
                                  CaptureResult previewResult,
                                  boolean requireLongExposure) {
        return freezePlan(controller, characteristics, exposureCompensationEv, tripod, shakiness,
                previewResult, requireLongExposure, false);
    }

    /** IRIS_26906_NIGHT_B_EXPOSURE: no fixed Night-A-only -0.70EV; NORMAL-only plan. */
    public static Plan freezeNormalOnlyB(CaptureController controller,
                                         CameraCharacteristics characteristics,
                                         float exposureCompensationEv,
                                         boolean tripod, int shakiness,
                                         CaptureResult previewResult) {
        return freezePlan(controller, characteristics, exposureCompensationEv, tripod, shakiness,
                previewResult, false, true);
    }

    private static Plan freezePlan(CaptureController controller,
                                   CameraCharacteristics characteristics,
                                   float exposureCompensationEv,
                                   boolean tripod, int shakiness,
                                   CaptureResult previewResult,
                                   boolean requireLongExposure,
                                   boolean experimentB) {
        if (experimentB && requireLongExposure)
            throw new IllegalArgumentException("26906 Night B must not request LONG");
        Range<Long> exposureRange = characteristics == null ? null
                : characteristics.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        Range<Integer> isoRange = characteristics == null ? null
                : characteristics.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        Integer analogObj = characteristics == null ? null
                : characteristics.get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
        long exposureLow = exposureRange == null ? ExposureIndex.sec / 1000L : exposureRange.getLower();
        long exposureHigh = exposureRange == null ? ExposureIndex.sec : exposureRange.getUpper();
        int isoLow = isoRange == null ? 100 : isoRange.getLower();
        int isoHigh = isoRange == null ? 3200 : isoRange.getUpper();
        int analogIso = analogObj == null ? 100 : analogObj;
        Integer ab = previewResult == null ? null
                : previewResult.get(CaptureResult.CONTROL_AE_ANTIBANDING_MODE);
        int antibanding = ab == null ? CaptureResult.CONTROL_AE_ANTIBANDING_MODE_AUTO : ab;
        int safeShakiness = Math.max(0, shakiness);

        double compensation = Math.pow(2.0, exposureCompensationEv);
        /* IRIS_26906_B_NIGHT_NO_FIXED_MINUS_070EV
         * Experiment B follows actual HAL-metered exposure energy (+ user EV);
         * keep Night A's historical -0.70EV exactly, including its short/long split.
         * Camera2 shutter motion cap and adaptive ISO remain the sole physical owners.
         */
        double meteredEnergy = Math.max(1.0,
                controller.mPreviewExposureTime * (double) Math.max(1, controller.mPreviewIso));
        double targetEnergy = meteredEnergy * compensation
                / (experimentB ? 1.0 : Math.pow(2.0, 0.70));
        /* IRIS_26909_B_NIGHT_SHUTTER_OVER_MOTION
         * Experiment B NORMAL-only has no A short/LONG bracket or shaky-phone
         * restriction. Preserve existing highlight-metered energy; spend up to
         * 1/10 s on photons before raising the ISO, on every physical lens.
         * A's historical short/long split remains untouched. */
        long shortCap = experimentB
                ? Math.min(exposureHigh, IRIS_26908_AUTO_SHUTTER_CEILING_NS)
                : shortMotionCap(tripod, safeShakiness, exposureHigh);
        if (requireLongExposure) {
            // Night A's independent physical LONG still needs up to +2 EV of
            // integration. Reserve headroom below the same 1/10s total ceiling;
            // never silently collapse LONG onto SHORT or drop its cohort.
            final long longCeiling = longMotionCap(tripod, safeShakiness, exposureHigh);
            final long reservedShort = Math.max(exposureLow,
                    (long)Math.floor(longCeiling / LONG_TARGET_MULTIPLIER));
            shortCap = Math.min(shortCap, reservedShort);
        }
        // B uses the sensor's real lowest reported ISO, never a hard-coded ISO 100.
        long shortDesired = (long) Math.round(targetEnergy /
                (experimentB ? Math.max(1, isoLow) : Math.max(100, isoLow)));
        long shortExposure = clamp(
                antiFlicker(clamp(shortDesired, exposureLow, shortCap), shortCap, antibanding),
                exposureLow, exposureHigh);
        int shortIso = (int) Math.round(targetEnergy / Math.max(1.0, shortExposure));
        shortIso = Math.max(isoLow, Math.min(isoHigh, shortIso));

        double manualExposure = controller.getParamController().getCurrentExposureValue();
        double manualIso = controller.getParamController().getCurrentISOValue();
        if (manualExposure != 0.0)
            shortExposure = clamp((long) manualExposure, exposureLow, exposureHigh);
        if (manualIso != 0.0)
            shortIso = Math.max(isoLow, Math.min(isoHigh, (int) manualIso));

        if (!requireLongExposure) {
            Plan shortOnly = new Plan(shortExposure, shortIso, shortExposure, shortIso,
                    exposureLow, exposureHigh, isoLow, isoHigh, analogIso, tripod, safeShakiness, antibanding);
            Log.i(TAG, (experimentB
                    ? "IRIS_26906_B_NIGHT_ALL_NORMAL_METERED_EXPOSURE"
                    : "IRIS_26552_NIGHT_2_SHORT_ONLY_EXPOSURE")
                    + " shortNs=" + shortOnly.shortExposureNs + " shortIso=" + shortOnly.shortIso
                    + " longRequested=false fixedNightUnderexposureEv="
                    + (experimentB ? 0.0 : -0.70)
                    + " shutterPriority=true adaptiveIso=true autoShutterCeilingNs=" + IRIS_26908_AUTO_SHUTTER_CEILING_NS
                    + " motionCapBypassedForB=" + experimentB
                    + " freshPostShutter=true zsl=false"
                    + " photonIsoExpoSelector=false planFrozenAtShutter=true");
            return shortOnly;
        }

        long longCap = Math.max(shortExposure, longMotionCap(tripod, safeShakiness, exposureHigh));
        long desiredLong = (long) Math.ceil(shortExposure * LONG_TARGET_MULTIPLIER);
        long longExposure = clamp(
                antiFlicker(clamp(desiredLong, exposureLow, longCap), longCap, antibanding),
                exposureLow, exposureHigh);
        int longIso = shortIso; // integration time, not ISO amplification, provides the extra photons.
        if (longExposure <= shortExposure) {
            // Try the smallest physically longer exposure if anti-flicker quantization collapsed it.
            long oneStep = Math.min(exposureHigh, shortExposure + Math.max(1L, exposureLow));
            if (oneStep > shortExposure && oneStep <= longCap) longExposure = oneStep;
        }
        if (longExposure <= shortExposure) {
            throw new IllegalStateException(
                    "26541 Night cannot form a physically longer shadow exposure: short="
                            + shortExposure + " sensorHigh=" + exposureHigh + " longCap=" + longCap);
        }

        Plan plan = new Plan(shortExposure, shortIso, longExposure, longIso,
                exposureLow, exposureHigh, isoLow, isoHigh, analogIso, tripod, safeShakiness, antibanding);
        Log.i(TAG, "IRIS_26552_NIGHT_DYNAMIC_EXPOSURE"
                + " shortNs=" + plan.shortExposureNs + " shortIso=" + plan.shortIso
                + " longNs=" + plan.longExposureNs + " longIso=" + plan.longIso
                + " longToShortEnergy=" + plan.longToShortEnergyRatio
                + " shortCapNs=" + shortCap + " longCapNs=" + longCap
                + " autoShutterCeilingNs=" + IRIS_26908_AUTO_SHUTTER_CEILING_NS
                + " tripod=" + tripod + " shakiness=" + safeShakiness
                + " freshPostShutter=true zsl=false photonIsoExpoSelector=false planFrozenAtShutter=true");
        return plan;
    }

    private static void apply(CaptureRequest.Builder builder, long exposureNs, int iso, String label) {
        if (builder == null) throw new IllegalArgumentException("26541 Night " + label + " builder is null");
        builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
        builder.set(CaptureRequest.SENSOR_EXPOSURE_TIME, exposureNs);
        builder.set(CaptureRequest.SENSOR_SENSITIVITY, iso);
    }

    public static void applyShortPlan(CaptureRequest.Builder builder, Plan plan) {
        if (plan == null) throw new IllegalArgumentException("26541 Night exposure plan is null");
        apply(builder, plan.shortExposureNs, plan.shortIso, "short");
    }

    public static void applyLongPlan(CaptureRequest.Builder builder, Plan plan) {
        if (plan == null) throw new IllegalArgumentException("26541 Night exposure plan is null");
        apply(builder, plan.longExposureNs, plan.longIso, "long");
    }

    // Compatibility alias: callers that mean the reference cohort get the short plan.
    public static void applyPlan(CaptureRequest.Builder builder, Plan plan) {
        applyShortPlan(builder, plan);
    }
}
