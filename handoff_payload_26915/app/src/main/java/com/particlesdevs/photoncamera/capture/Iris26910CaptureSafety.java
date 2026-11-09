package com.particlesdevs.photoncamera.capture;

/** IRIS_26910_B_PREVIEW_OWNERSHIP_AND_QUEUE_SAFETY.
 * Pure policies; never reads or mutates Camera2/RAW state. Call only from B-owned paths.
 */
public final class Iris26910CaptureSafety {
    private Iris26910CaptureSafety() { }
    /** A recipe is relative to the HAL reference that existed when it was measured.
     * Once B owns a manual shutter-first sensor pair, use the current physical
     * exposure as the reference, retaining any deliberately negative highlight EV.
     * This prevents an old absolute HAL recipe from silently rejecting valid ZSL RAWs.
     */
    public static double targetEnergy(double physicalEnergy, float recipeRelativeEv) {
        if (!Double.isFinite(physicalEnergy) || physicalEnergy <= 0.0
                || !Float.isFinite(recipeRelativeEv)) return Double.NaN;
        double boundedEv = Math.max(-3.0, Math.min(0.0, recipeRelativeEv));
        return physicalEnergy * Math.pow(2.0, boundedEv);
    }

    /** The completion bound accounts for sensor cadence and queued first results.
     * It is NOT a capture pacing instruction or permission to silently drop frames.
     */
    public static long completionTimeoutMs(int missingNormals, long exposureNs,
                                            boolean auxExpected) {
        if (missingNormals <= 0 && !auxExpected) return 1400L;
        long n = Math.max(0, Math.min(30, missingNormals));
        long frameMs = Math.max(125L, Math.min(1000L, (exposureNs + 999999L) / 1000000L + 25L));
        long safe = 1200L + n * frameMs + (auxExpected ? 1600L : 700L);
        return Math.max(3500L, Math.min(12000L, safe));
    }

    /** A Camera2 submission is not a sensor start. Never retire a queued request
     * just because an earlier frame has a long readout. Only a started exposure
     * or a completed result waiting for its exact RAW buffer is watchdog-eligible.
     */
    public static boolean attemptStalled(boolean started, boolean completed,
                                         boolean ready, long elapsedSinceProgressMs) {
        if (ready || elapsedSinceProgressMs < 0L) return false;
        if (completed) return elapsedSinceProgressMs >= 1500L;
        return started && elapsedSinceProgressMs >= 1600L;
    }

    /** IRIS_26915_EARLY_FROZEN_NORMAL_PAIR
     * Test the sensor-applied NORMAL exposure, never the submitted request.
     * Mirrors B's later motionExposurePairMatches: energy delta plus separate
     * physical shutter delta. A deliberately retains energy-only matching.
     * This is an early admission guard, not permission to drop a frame:
     * rejected logical top-up slots use their existing bounded replacement.
     */
    public static boolean frozenNormalPairMatches(long actualShutterNs, int actualIso,
                                                   long frozenShutterNs, int frozenIso,
                                                   double halfWindowEv,
                                                   boolean requireShutter) {
        if (actualShutterNs <= 0L || actualIso <= 0 || frozenShutterNs <= 0L
                || frozenIso <= 0 || !Double.isFinite(halfWindowEv)
                || halfWindowEv < 0.0) return false;
        double actualEnergy = (double) actualShutterNs * actualIso;
        double frozenEnergy = (double) frozenShutterNs * frozenIso;
        double energyEv = Math.log(actualEnergy / frozenEnergy) / Math.log(2.0);
        if (!Double.isFinite(energyEv) || Math.abs(energyEv) > halfWindowEv) return false;
        if (!requireShutter) return true;
        double shutterEv = Math.log((double) actualShutterNs / frozenShutterNs)
                / Math.log(2.0);
        return Double.isFinite(shutterEv) && Math.abs(shutterEv) <= halfWindowEv;
    }

    /** Preview-only low-light midtone lift, never sensor AE or RAW/JPEG gain.
     * RAW p99.5 and actual ISO exclude bright scenes and strongly clipped scenes.
     * The already-existing white-anchored shader leaves display white unchanged.
     */
    public static float lowLightPreviewLiftEv(long physicalShutterNs, int actualIso,
                                               float rawP995, float rawClippedFraction) {
        if (physicalShutterNs < 45000000L || actualIso < 500
                || !Float.isFinite(rawP995) || !Float.isFinite(rawClippedFraction)
                || rawP995 < 0.0f || rawClippedFraction < 0.0f
                || rawP995 >= 0.60f || rawClippedFraction >= 0.003f) return 0f;
        float shutterWeight = Math.min(1f, Math.max(0f,
                (physicalShutterNs - 45000000L) / 35000000f));
        float isoWeight = Math.min(1f, Math.max(0f,(actualIso - 500f) / 500f));
        float sceneWeight = Math.min(1f, Math.max(0f,(0.60f - rawP995) / 0.40f));
        float highlightWeight = Math.min(1f, Math.max(0f,
                (0.003f - rawClippedFraction) / 0.003f));
        return 0.75f * shutterWeight * isoWeight * sceneWeight * highlightWeight;
    }
}
