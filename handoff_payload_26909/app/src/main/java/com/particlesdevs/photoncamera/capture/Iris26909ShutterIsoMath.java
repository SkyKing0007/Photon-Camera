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
