package com.particlesdevs.photoncamera.capture;

/**
 * IRIS_26909_B_SHUTTER_FIRST_PURE_ALLOCATION.
 * Allocate the existing highlight-safe AE exposure energy over the longest
 * legal sensor shutter (up to 1/10s) and the lowest legal physical ISO.
 * Motion/focal length/FPS preference are deliberately not shutter ceilings.
 * This class does not read Camera2 or write exposure requests; the caller
 * must verify MANUAL_SENSOR and echo of the actually applied sensor pair.
 */
public final class Iris26909ShutterIsoMath {
    public static final long MAX_AUTO_SHUTTER_NS = 100_000_000L;
    public static final long BASE_PREVIEW_FRAME_NS = 33_333_333L;

    public static final class Plan {
        public final long shutterNs;
        public final int iso;
        public final long frameDurationNs;
        public final double targetEnergy;
        public final boolean shutterFirstUseful;

        private Plan(long shutterNs, int iso, long frameDurationNs, double targetEnergy,
                     boolean shutterFirstUseful) {
            this.shutterNs = shutterNs;
            this.iso = iso;
            this.frameDurationNs = frameDurationNs;
            this.targetEnergy = targetEnergy;
            this.shutterFirstUseful = shutterFirstUseful;
        }
    }

    private Iris26909ShutterIsoMath() {}
    /**
     * IRIS_26970_B_SCENE_RAW_GUIDED_1_14_POLICY_ONLY.
     * Separate from every frozen historical 26909/26913/26964 solver.
     * Underlying preview RAW signal (NOT display-processed viewfinder pixels)
     * adjusts the shutter-versus-noise tradeoff, never the metered exposure energy.
     * Camera2 HAL establishes highlight-safe exposure, not the final sensor pair.
     * A positively verified modulation period limits the discrete candidate set.
     * Lack of a period is an unknown constraint, NOT evidence that there is no PWM;
     * CaptureController must remain in HAL antibanding if its row detector is active.
     */
    public static final long MAX_26970_AUTO_SHUTTER_NS = 71_428_571L;
    /** RAW rather than display-viewfinder change detection; three distinct
     * sensor-timestamp samples are required by the CaptureController caller. */
    public static boolean rawSceneRemeter26970(float initialMean, float currentMean,
                                               float clippedFraction, int freshSamples) {
        if (freshSamples < 3 || !Float.isFinite(initialMean)
                || !Float.isFinite(currentMean) || initialMean < 0.003f
                || currentMean < 0f) return false;
        if (Float.isFinite(clippedFraction) && clippedFraction >= 0.012f) return true;
        double ratio = Math.max(0.003f, currentMean) / initialMean;
        return ratio > 1.65 || ratio < (1.0 / 1.65);
    }

    public static Plan solve26970(long halShutterNs, int halIso, int isoMin, int isoMax,
                                  long shutterMin, long shutterMax, long frameMax,
                                  double focal35mm, boolean oisAvailable,
                                  boolean cameraMoving, float rawMean,
                                  float clippedFraction, long verifiedPeriodNs) {
        if (halShutterNs <= 0L || halIso <= 0 || isoMin <= 0 || isoMax < isoMin
                || shutterMin <= 0L || shutterMax < shutterMin
                || !Float.isFinite(rawMean) || rawMean < 0f
                || !Float.isFinite(clippedFraction) || clippedFraction < 0f
                || clippedFraction > 0.015f || verifiedPeriodNs < 0L) return null;
        final long cap = Math.min(MAX_26970_AUTO_SHUTTER_NS,
                Math.min(shutterMax, frameMax > 0L ? frameMax : Long.MAX_VALUE));
        if (cap < shutterMin) return null;
        final double energy = (double)halShutterNs * (double)halIso;
        if (!Double.isFinite(energy) || energy <= 0.0
                || energy > (double)cap * isoMax * 1.001) return null;
        final double focal = Double.isFinite(focal35mm) && focal35mm >= 8 && focal35mm <= 500
                ? focal35mm : 35.0;
        // Focal length is continuous (no device or lens name switches).
        // OIS availability only mildly affects the preference; it is not proof
        // stabilization was enabled or that the subject was stationary.
        final double frameSafeNs = 38_000_000.0
                / Math.pow(focal / 35.0, 0.42)
                * (oisAvailable ? 1.08 : 1.0)
                * (cameraMoving ? 0.64 : 1.0);
        final double quietIso = Math.max(100.0, isoMin);
        // RAW signal changes how strongly we penalize sensor noise in shadows,
        // without changing AE's target brightness or double brightening RAW.
        final double darkness = 1.0 - Math.max(0.0, Math.min(1.0,
                (rawMean - 0.045) / 0.26));
        final double bestNoiseWeight = 0.85 + 0.75 * darkness;
        final double blurWeight = cameraMoving ? 0.34 : 0.18;
        final double[] shutterSec = {
                1.0/200,1.0/160,1.0/120,1.0/100,1.0/80,1.0/60,
                1.0/50,1.0/40,1.0/33,1.0/30,1.0/25,1.0/22,
                1.0/20,1.0/18,1.0/16,1.0/14
        };
        double bestScore = Double.POSITIVE_INFINITY;
        long bestShutter = 0L;
        int bestIso = 0;
        // HAL time is also a candidate; do not force a long shutter when
        // the scene is bright and the HAL already chose a clean exposure.
        for (int i=0;i<=shutterSec.length;i++) {
            long candidate = i == shutterSec.length ? halShutterNs
                    : Math.round(1e9 * shutterSec[i]);
            if (verifiedPeriodNs > 0L) {
                long n = Math.round((double)candidate / verifiedPeriodNs);
                if (n <= 0L || n > Long.MAX_VALUE / verifiedPeriodNs) continue;
                candidate = n * verifiedPeriodNs;
            }
            if (candidate < shutterMin || candidate > cap) continue;
            final int iso = (int)Math.round(energy / candidate);
            if (iso < isoMin || iso > isoMax) continue;
            final double e = Math.abs(Math.log(candidate * (double)iso / energy));
            if (!Double.isFinite(e) || e > 0.025) continue;
            final double noise = Math.log(Math.max(1.0, iso / quietIso));
            final double blur = candidate / frameSafeNs;
            final double score = bestNoiseWeight * noise
                    + blurWeight * blur * blur
                    + 0.20 * Math.abs(Math.log(candidate / (double)halShutterNs))
                    + 4.0 * e;
            if (score < bestScore) {
                bestScore = score;
                bestShutter = candidate;
                bestIso = iso;
            }
        }
        if (bestShutter == 0L) return null;
        long duration = Math.max(BASE_PREVIEW_FRAME_NS, bestShutter);
        if (frameMax > 0L && duration > frameMax) return null;
        boolean useful = Math.abs(Math.log((double)bestShutter / halShutterNs)) > 0.12;
        return new Plan(bestShutter, bestIso, duration, energy, useful);
    }


    /**
     * IRIS_26913_BRIGHTNESS_AWARE_LOW_ISO_ALLOCATION.
     * This is intentionally separate from the frozen 26909 shutter-first
     * calculation.  Camera2 AE supplies only a measured, highlight-protected
     * exposure-energy reference; it never selects our physical sensor pair.
     * Neither motion/gyro nor viewfinder FPS can demand a faster shutter.
     *
     * Equivalent scene exposure at a quiet physical ISO increases as the
     * available scene light decreases.  The shallow, continuous curve gives
     * a scene at 1/120s * ISO1114 about 1/24s * ISO240 on sensors with ISO50
     * minimum, while reserving 1/10s for darker scenes. In brighter scenes,
     * the curve becomes shorter without raising ISO above a bounded budget.
     * There are no new shutter-press waits or re-metering owners.
     */
    public static Plan solveBrightnessAware(long halShutterNs, int halIso,
                                           int sensorIsoMin, int sensorIsoMax,
                                           long sensorShutterMinNs, long sensorShutterMaxNs,
                                           long maxSensorFrameDurationNs, long flickerPeriodNs) {
        if (halShutterNs <= 0L || halIso <= 0 || sensorIsoMin <= 0
                || sensorIsoMax < sensorIsoMin || sensorShutterMinNs <= 0L
                || sensorShutterMaxNs < sensorShutterMinNs) return null;
        long cap = Math.min(MAX_AUTO_SHUTTER_NS, sensorShutterMaxNs);
        if (maxSensorFrameDurationNs > 0L) cap = Math.min(cap, maxSensorFrameDurationNs);
        if (cap < sensorShutterMinNs) return null;
        final double energy = (double)halShutterNs * (double)halIso;
        if (!Double.isFinite(energy) || energy <= 0.0
                || energy > (double)cap * sensorIsoMax * 1.01) return null;

        // At very low hardware ISOs (<100), using the absolute floor as the
        // brightness anchor incorrectly calls an ISO93, 1/10s room "dark".
        // ISO100 is only an internal quiet-reference scale, NOT a hard ISO
        // request or a fixed camera-wide lower sensitivity limit.
        final double quietIso = Math.min(sensorIsoMax,
                Math.max(sensorIsoMin, 100));
        final double equivalentNs = energy / quietIso;
        // Smooth transition from ISO-first in true daylight (<~8 ms at
        // quiet ISO) to an at-most-2.4x quiet-ISO allocation above 40 ms.
        // This deliberately refuses the HAL's common 1/120s + high ISO
        // preference in ordinary indoor rooms.
        final double x = Math.max(0.0, Math.min(1.0,
                (equivalentNs - 8_000_000.0) / 32_000_000.0));
        final double smooth = x * x * (3.0 - 2.0 * x);
        final double multiplier = 1.0 + 1.4 * smooth;
        final double wantedNs = equivalentNs / multiplier;
        long shutter = (long)Math.round(Math.min((double)cap,
                Math.max((double)sensorShutterMinNs, wantedNs)));
        // Historical antibanding contract: never quantize shorter than one
        // confirmed period. No blind 50/60Hz detection is introduced here.
        if (flickerPeriodNs > 0L && shutter >= flickerPeriodNs) {
            long periods = shutter / flickerPeriodNs;
            if (periods > 0L && periods <= Long.MAX_VALUE / flickerPeriodNs) {
                long snapped = periods * flickerPeriodNs;
                if (snapped >= sensorShutterMinNs && snapped <= cap) shutter = snapped;
            }
        }
        double isoReal = energy / shutter;
        if (isoReal > (double)sensorIsoMax * 1.001) return null;
        // Allow a modest increase above physical-ISO-minimum in usable light,
        // but never accept a large gain to mimic HAL high-FPS AE. The quiet
        // ISO scale and bounded curve limit cost independently of HAL choice.
        final double isoBudget = Math.min(sensorIsoMax, quietIso * 2.5);
        if (isoReal > isoBudget * 1.01 && shutter < cap) {
            double rescued = energy / isoBudget;
            if (rescued > cap) return null;
            shutter = (long)Math.ceil(Math.max(shutter, rescued));
            if (flickerPeriodNs > 0L && shutter >= flickerPeriodNs) {
                long periods = shutter / flickerPeriodNs;
                if (shutter % flickerPeriodNs != 0L) periods++;
                if (periods > Long.MAX_VALUE / flickerPeriodNs) return null;
                shutter = periods * flickerPeriodNs;
            }
        }
        if (shutter < sensorShutterMinNs || shutter > cap) return null;
        int iso = (int)Math.round(energy / shutter);
        if (iso < sensorIsoMin || iso > sensorIsoMax) return null;
        // A clipped/rounded ISO is not permission to make exposure visibly
        // darker or brighter. Require the same physical energy as Camera2 AE.
        final double error = Math.abs(Math.log((double)shutter * iso / energy));
        if (!Double.isFinite(error) || error >= 0.045) return null;
        long duration = Math.max(BASE_PREVIEW_FRAME_NS, shutter);
        if (maxSensorFrameDurationNs > 0L && duration > maxSensorFrameDurationNs) return null;
        // Meaningful change can shorten OR lengthen HAL's choice: it is Iris,
        // not HAL FPS or the gyro, that owns the scene-brightness allocation.
        boolean useful = shutter >= halShutterNs * 1.20
                || shutter <= halShutterNs * 0.80;
        return new Plan(shutter, iso, duration, energy, useful);
    }

    /**
     * IRIS_26964_B_SCENE_LENS_SENSOR_EXPOSURE_ALLOCATION.
     * Use the actual converged, highlight-safe Camera2 AE exposure energy;
     * never use display-brightened preview pixels as a sensor light meter.
     * A continuous focal-length shutter preference is traded against the
     * camera's own analog gain capability and the same physical scene energy.
     * The 1/10 second cap is retained as a last resort for truly dark scenes.
     * Unknown/malformed lens or analog metadata falls back conservatively.
     * This only returns a candidate; CaptureController retains manual request
     * echo, highlight-full-well guard, scene continuity and anti-flicker rules.
     */
    public static Plan solveSceneLensAware(long halShutterNs, int halIso,
                                           int sensorIsoMin, int sensorIsoMax,
                                           long sensorShutterMinNs, long sensorShutterMaxNs,
                                           long maxSensorFrameDurationNs,
                                           double equivalentFocalMm, int analogIsoMax,
                                           boolean oisAvailable, boolean cameraMoving) {
        if (halShutterNs <= 0L || halIso <= 0 || sensorIsoMin <= 0
                || sensorIsoMax < sensorIsoMin || sensorShutterMinNs <= 0L
                || sensorShutterMaxNs < sensorShutterMinNs) return null;
        long cap = Math.min(MAX_AUTO_SHUTTER_NS, sensorShutterMaxNs);
        if (maxSensorFrameDurationNs > 0L) cap = Math.min(cap, maxSensorFrameDurationNs);
        if (cap < sensorShutterMinNs) return null;
        double energy = (double)halShutterNs * (double)halIso;
        if (!Double.isFinite(energy) || energy <= 0.0
                || energy > (double)cap * sensorIsoMax * 1.01) return null;
        double focal = Double.isFinite(equivalentFocalMm)
                && equivalentFocalMm >= 8.0 && equivalentFocalMm <= 500.0
                ? equivalentFocalMm : 30.0;
        // Focal-length dependence is gradual, not a telephoto mode switch.
        double fps = 30.0 * Math.pow(focal / 30.0, 0.37);
        if (oisAvailable) fps *= 0.94; // OIS helps camera shake, not subject motion.
        if (cameraMoving) fps *= 1.15; // bounded hint, never overrides noise limits.
        double wantedNs = 1.0e9 / Math.max(12.0, Math.min(100.0, fps));
        // Max analog sensitivity is a *capability*, not a measured SNR curve.
        // Permit less ISO than the sensor's max; absent metadata fail soft to
        // a modest physical ISO ratio. No device-brand or lens-type guesses.
        double analog = analogIsoMax >= sensorIsoMin
                ? Math.min(sensorIsoMax, analogIsoMax)
                : Math.min(sensorIsoMax, Math.max(1200.0, 20.0 * sensorIsoMin));
        double quiet = Math.max(100.0, (double)sensorIsoMin);
        double qualityIsoCeiling = Math.min(sensorIsoMax,
                Math.max(4.0 * quiet, 0.65 * analog));
        qualityIsoCeiling = Math.max(sensorIsoMin, qualityIsoCeiling);
        // Dark scenes that need more ISO than this soft budget may still reach
        // 1/10s; unlike a hard noise ceiling we never sacrifice AE brightness.
        wantedNs = Math.max(wantedNs, energy / qualityIsoCeiling);
        wantedNs = Math.min(wantedNs, energy / sensorIsoMin);
        long shutter = (long)Math.round(Math.min((double)cap,
                Math.max((double)sensorShutterMinNs, wantedNs)));
        shutter = Math.max(sensorShutterMinNs, Math.min(cap, shutter));
        double isoReal = energy / shutter;
        if (!Double.isFinite(isoReal) || isoReal < sensorIsoMin * 0.999
                || isoReal > sensorIsoMax * 1.001) return null;
        int iso = (int)Math.round(isoReal);
        if (iso < sensorIsoMin || iso > sensorIsoMax) return null;
        double error = Math.abs(Math.log((double)shutter * iso / energy));
        if (!Double.isFinite(error) || error >= 0.045) return null;
        long duration = Math.max(BASE_PREVIEW_FRAME_NS, shutter);
        if (maxSensorFrameDurationNs > 0L && duration > maxSensorFrameDurationNs) return null;
        boolean useful = shutter >= halShutterNs * 1.20
                || shutter <= halShutterNs * 0.80;
        return new Plan(shutter, iso, duration, energy, useful);
    }

    public static Plan solve(long halShutterNs, int halIso, int sensorIsoMin, int sensorIsoMax,
                             long sensorShutterMinNs, long sensorShutterMaxNs,
                             long maxSensorFrameDurationNs, long flickerPeriodNs) {
        if (halShutterNs <= 0L || halIso <= 0 || sensorIsoMin <= 0
                || sensorIsoMax < sensorIsoMin || sensorShutterMinNs <= 0L
                || sensorShutterMaxNs < sensorShutterMinNs) return null;
        long cap = Math.min(MAX_AUTO_SHUTTER_NS, sensorShutterMaxNs);
        if (maxSensorFrameDurationNs > 0L) cap = Math.min(cap, maxSensorFrameDurationNs);
        if (cap < sensorShutterMinNs) return null;
        final double energy = (double) halShutterNs * (double) halIso;
        if (!Double.isFinite(energy) || energy <= 0.0) return null;
        // Reject scenes the sensor cannot cover under the hard 1/10s cap;
        // otherwise reducing shutter to satisfy a nonexistent ISO is darker.
        if (energy > (double)cap * sensorIsoMax * 1.01) return null;
        final double target = energy / sensorIsoMin;
        long shutter = (long)Math.round(Math.min(cap,
                Math.max(sensorShutterMinNs, target)));
        if (flickerPeriodNs > 0L && shutter >= flickerPeriodNs) {
            final long periods = Math.max(1L, shutter / flickerPeriodNs);
            final long snapped = periods * flickerPeriodNs;
            if (snapped >= sensorShutterMinNs && snapped <= cap) shutter = snapped;
        }
        int iso = (int)Math.round(energy / Math.max(1.0, shutter));
        iso = Math.max(sensorIsoMin, Math.min(sensorIsoMax, iso));
        final long duration = Math.max(BASE_PREVIEW_FRAME_NS, shutter);
        if (maxSensorFrameDurationNs > 0L && duration > maxSensorFrameDurationNs) return null;
        // The real, frozen HAL target includes any 26841 protection. Require
        // meaningful ISO savings so the sensor is not switched in bright light.
        final boolean useful = shutter >= halShutterNs * 1.20
                && iso <= halIso * 0.85
                && Math.abs(Math.log(((double)shutter * iso) / energy)) < 0.045;
        return new Plan(shutter, iso, duration, energy, useful);
    }

    /* IRIS_26968_B_VERIFIED_PERIOD_MANUAL_SAFETY_GATE
     * Pure, fail-closed final check after snapping. Never release HAL AUTO
     * for an unverified or unsnappable light period. This is tested on host
     * without Android dependencies and shared by all B physical cameras. */
    public static boolean isVerifiedPeriodLockedBPlan26968(Plan plan, long verifiedPeriodNs) {
        if (plan == null || (verifiedPeriodNs != 8_333_333L && verifiedPeriodNs != 10_000_000L))
            return false;
        if (!plan.shutterFirstUseful || plan.shutterNs < verifiedPeriodNs
                || plan.shutterNs % verifiedPeriodNs != 0L || plan.iso < 1
                || plan.frameDurationNs < plan.shutterNs
                || !Double.isFinite(plan.targetEnergy) || plan.targetEnergy <= 0.0)
            return false;
        double e = Math.abs(Math.log(plan.shutterNs * (double)plan.iso / plan.targetEnergy));
        return Double.isFinite(e) && e < 0.045;
    }

    /* IRIS_26948_B_VERIFIED_MANUAL_FLICKER_PERIOD_ONLY
     * A spatial row harmonic is NOT itself a lighting frequency. Convert it
     * only with a valid exact Camera2 rolling-shutter skew and the fraction
     * of the sensor actually sampled. Conservative acceptance avoids
     * mistaking foliage, static venetian blinds or display PWM for 50/60 Hz
     * mains. No inference from regional mains defaults.
     */
    public static long verifiedMainsPeriodNs(int harmonic, long skewNs,
                                              double sampledSpanFraction) {
        if (harmonic < 1 || harmonic > 6 || skewNs < 2_000_000L
                || skewNs > 80_000_000L || !Double.isFinite(sampledSpanFraction)
                || sampledSpanFraction < 0.80 || sampledSpanFraction > 1.0) return 0L;
        double hz = harmonic * 1.0e9 / (skewNs * sampledSpanFraction);
        if (Math.abs(hz - 100.0) <= 6.0) return 10_000_000L;
        if (Math.abs(hz - 120.0) <= 7.2) return 8_333_333L;
        return 0L;
    }

    /* Keep 26913's selected shutter/ISO target and highlight energy. Only
     * snap DOWN when the existing chosen shutter contains >=1 whole verified
     * flicker cycle; never extend exposure into clipping to force a period.
     * If energy/ISO cannot be preserved, return the original manual plan.
     * Shorter-than-cycle shutter remains exact, with measured GPU burst
     * correction as the separate residual path (never fake a mains lock).
     */
    public static Plan snapVerifiedBPlan(Plan original, long periodNs,
            long sensorShutterMinNs, int sensorIsoMin, int sensorIsoMax,
            long sensorFrameDurationMaxNs) {
        if (original == null || periodNs <= 0L || original.shutterNs < periodNs
                || sensorIsoMin < 1 || sensorIsoMax < sensorIsoMin) return original;
        long count = original.shutterNs / periodNs;
        if (count < 1L || count > Long.MAX_VALUE / periodNs) return original;
        long snapped = count * periodNs;
        if (snapped < sensorShutterMinNs || snapped > original.shutterNs) return original;
        int iso = (int)Math.round(original.targetEnergy / (double)snapped);
        if (iso < sensorIsoMin || iso > sensorIsoMax) return original;
        double error = Math.abs(Math.log((double)snapped * iso / original.targetEnergy));
        if (!Double.isFinite(error) || error >= 0.045) return original;
        long duration = Math.max(BASE_PREVIEW_FRAME_NS, snapped);
        if (sensorFrameDurationMaxNs > 0L && duration > sensorFrameDurationMaxNs) return original;
        return new Plan(snapped, iso, duration, original.targetEnergy,
                original.shutterFirstUseful);
    }
}
