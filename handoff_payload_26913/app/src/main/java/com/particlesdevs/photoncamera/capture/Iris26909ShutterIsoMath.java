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
}
