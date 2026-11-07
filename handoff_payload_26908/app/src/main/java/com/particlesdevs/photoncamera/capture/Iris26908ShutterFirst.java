package com.particlesdevs.photoncamera.capture;

/**
 * IRIS_26908_SENSOR_EXPOSURE_PRIORITY_MATH_ONLY.
 * Pure shutter/ISO allocation: the HAL remains responsible for sensor ISO,
 * AE brightness/compensation, AWB, antibanding, FPS and existing highlight EV.
 * The result is only a requested shutter for API36 AE exposure-time priority.
 */
public final class Iris26908ShutterFirst {
    public static final long AUTO_SLOWEST_NS = 100_000_000L; // 1/10s absolute cap

    private Iris26908ShutterFirst() {}

    public static long choose(long observedShutterNs, int observedIso, int minIso,
                              long sensorMinNs, long sensorMaxNs, int fpsFloor,
                              long motionCeilingNs, long antiFlickerPeriodNs) {
        if (observedShutterNs <= 0L || observedIso <= 0 || minIso <= 0
                || sensorMinNs <= 0L || sensorMaxNs < sensorMinNs
                || fpsFloor <= 0 || motionCeilingNs <= 0L) return 0L;
        long fpsCap = 1_000_000_000L / fpsFloor;
        long ceiling = Math.min(Math.min(AUTO_SLOWEST_NS, sensorMaxNs),
                Math.min(fpsCap, motionCeilingNs));
        if (ceiling < sensorMinNs) return 0L;
        double wanted = observedShutterNs * (double)observedIso / (double)minIso;
        long shutter = (long)Math.rint(Math.min((double)ceiling,
                Math.max((double)sensorMinNs, wanted)));
        shutter = Math.max(sensorMinNs, Math.min(ceiling, shutter));
        if (antiFlickerPeriodNs > 0 && shutter >= antiFlickerPeriodNs) {
            long periods = Math.max(1L, shutter / antiFlickerPeriodNs);
            long snapped = periods * antiFlickerPeriodNs;
            if (snapped >= sensorMinNs && snapped <= ceiling) shutter = snapped;
        }
        return shutter;
    }
}
