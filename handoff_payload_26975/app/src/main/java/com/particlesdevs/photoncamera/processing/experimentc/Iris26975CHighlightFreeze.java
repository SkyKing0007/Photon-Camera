package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * C-only shutter-time adapter for the existing Iris highlight exposure decision.
 * Reads an already-computed, sensor-timestamped Iris recipe; never invokes A/B
 * image processing, recalculates scene highlights, or creates an extra bracket.
 * Every NORMAL RAW in C receives this single immutable SS/ISO pair.
 */
public final class Iris26975CHighlightFreeze {
    private static final long MAX_RECIPE_AGE_NS = 750_000_000L;
    private static final float MAX_PROTECTION_EV = 1.50f;

    public static final class Decision {
        public final long exposureNs;
        public final int iso;
        public final float appliedProtectionEv;
        public final String authority;
        private Decision(long exposureNs, int iso, float ev, String authority) {
            this.exposureNs = exposureNs;
            this.iso = iso;
            this.appliedProtectionEv = ev;
            this.authority = authority;
        }
    }

    private Iris26975CHighlightFreeze() {}

    public static Decision freeze(boolean userManual, long previewExposureNs, int previewIso,
            long physicalPreviewTimestampNs, long currentCameraGeneration,
            boolean irisRecipeReady, long recipeGeneration, long recipeTimestampNs,
            double recipeEnergy, float recipeOffsetEv,
            long sensorMinExposureNs, long sensorMaxExposureNs,
            int sensorMinIso, int sensorMaxIso) {
        if (previewExposureNs <= 0 || previewIso <= 0 ||
                sensorMinExposureNs <= 0 || sensorMaxExposureNs < sensorMinExposureNs ||
                sensorMinIso <= 0 || sensorMaxIso < sensorMinIso ||
                previewExposureNs < sensorMinExposureNs || previewExposureNs > sensorMaxExposureNs ||
                previewIso < sensorMinIso || previewIso > sensorMaxIso) {
            throw new IllegalArgumentException("C shutter requires in-range physical SS/ISO");
        }
        Decision unchanged = new Decision(previewExposureNs, previewIso, 0f,
                userManual ? "IRIS_MANUAL" : "PHYSICAL_PREVIEW");
        // User manual choices outrank all automatic Iris highlight recipes.
        if (userManual || !irisRecipeReady || recipeGeneration != currentCameraGeneration ||
                physicalPreviewTimestampNs <= 0 || recipeTimestampNs <= 0 ||
                Math.abs((double) physicalPreviewTimestampNs - recipeTimestampNs) > MAX_RECIPE_AGE_NS ||
                !Float.isFinite(recipeOffsetEv) || recipeOffsetEv >= -0.03f ||
                recipeOffsetEv < -MAX_PROTECTION_EV - 0.01f ||
                !Double.isFinite(recipeEnergy) || recipeEnergy <= 0.0) return unchanged;

        final double baselineEnergy = (double) previewExposureNs * previewIso;
        // The preview may ALREADY carry Iris highlight protection. Compare with
        // its absolute recipe rather than subtracting the EV offset a second time.
        // Never create a brighter C capture than the physical HAL reference.
        if (recipeEnergy >= baselineEnergy * 0.985) return unchanged;
        final double minimumEnergy = baselineEnergy * Math.pow(2.0, -MAX_PROTECTION_EV);
        final double targetEnergy = Math.max(minimumEnergy, recipeEnergy);
        // Saturated photoelectrons are not restored by lowering digital/analog gain.
        // Protect the sensor highlight by shortening integration time FIRST,
        // preserving the exact pre-shutter Iris recipe energy and manual override.
        long selectedShutter = Math.min(previewExposureNs,
                Math.max(sensorMinExposureNs, (long) Math.floor(targetEnergy / previewIso)));
        int selectedIso = previewIso;
        // A sensor already at minimum integration time has no remaining optical
        // headroom; only then trim gain, without claiming recovered RAW detail.
        if ((double) selectedShutter * selectedIso > targetEnergy * 1.015) {
            selectedIso = Math.min(previewIso,
                    Math.max(sensorMinIso,(int)Math.floor(targetEnergy / selectedShutter)));
        }
        if (selectedShutter <= 0 || selectedIso <= 0 ||
                (selectedShutter == previewExposureNs && selectedIso == previewIso))
            return unchanged;
        final double actualEnergy = (double) selectedShutter * selectedIso;
        if (actualEnergy > baselineEnergy || actualEnergy < baselineEnergy *
                Math.pow(2.0, -MAX_PROTECTION_EV) * 0.985) return unchanged;
        float actualEv = (float) (Math.log(baselineEnergy / actualEnergy) / Math.log(2.0));
        return new Decision(selectedShutter, selectedIso, actualEv,
                "IRIS_HIGHLIGHT_RECIPE_FROZEN");
    }
}
