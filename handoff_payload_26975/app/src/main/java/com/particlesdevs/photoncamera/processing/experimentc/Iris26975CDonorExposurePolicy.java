package com.particlesdevs.photoncamera.processing.experimentc;

/** C-private adapter for pinned bjzhou Camera2Controller.kt applyExposureSettings and
 * applyMultiFrameCaptureConsistency (ordinary same-exposure RAWmax). No invented
 * shutter-first/noise/mains allocator. The original optional RAW minimum shutter
 * setting defaults to 0L and is not exposed by the minimal Iris C shell. */
public final class Iris26975CDonorExposurePolicy {
    private Iris26975CDonorExposurePolicy() {}
    public static final class Pair {
        public final long shutterNs;
        public final int iso;
        private Pair(long shutterNs, int iso) { this.shutterNs=shutterNs; this.iso=iso; }
    }
    /** Optional Iris highlight exception: preserve the donor's metered integration if
     * HAL has detected flicker or its observation is unavailable with antibanding enabled/unknown. No frequency guessing.
     * Camera2 values: antibanding OFF=0; STATISTICS_SCENE_FLICKER_NONE=0.
     * A reported flicker takes precedence even if antibanding is OFF. */
    public static boolean allowHighlightAdjustment(Integer antibanding, Integer sceneFlicker) {
        if (sceneFlicker != null) return sceneFlicker == 0;
        return antibanding != null && antibanding == 0;
    }
    public static Pair freeze(double userShutter, double userIso, Long actualShutter, Integer actualIso,
            Long requestedShutter, Integer requestedIso, long minShutter, long maxShutter,
            int minIso, int maxIso, Long maxFrame) {
        if (!Double.isFinite(userShutter) || !Double.isFinite(userIso) || userShutter < 0 || userIso < 0 || userIso > Integer.MAX_VALUE || userShutter > Long.MAX_VALUE ||
                minShutter <= 0 || maxShutter < minShutter || minIso <= 0 || maxIso < minIso)
            throw new IllegalArgumentException("invalid donor exposure inputs");
        boolean manual = userShutter != 0.0 || userIso != 0.0;
        Long shutter = manual ? requestedShutter : actualShutter;
        Integer iso = manual ? requestedIso : actualIso;
        if (shutter == null || iso == null || shutter <= 0 || iso <= 0)
            throw new IllegalArgumentException("missing donor base exposure");
        // Explicit user shutter is not the capped preview shutter. Donor uses full still value.
        long fullShutter = userShutter > 0 ? Math.round(userShutter) : shutter;
        int fullIso = userIso > 0 ? (int)Math.round(userIso) : iso;
        if (fullShutter < minShutter || fullShutter > maxShutter || fullIso < minIso || fullIso > maxIso ||
                (maxFrame != null && maxFrame > 0 && fullShutter > maxFrame))
            throw new IllegalArgumentException("donor exposure outside physical limits");
        return new Pair(fullShutter, fullIso);
    }
}
