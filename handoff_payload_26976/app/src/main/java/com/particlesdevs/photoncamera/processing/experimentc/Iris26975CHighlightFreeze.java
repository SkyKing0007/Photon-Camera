package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * C-only shutter-time negative exposure application. The active route uses only
 * the shutter-local C RAW meter, never A/B recipe state or extra brackets.
 * The legacy pure arithmetic method is retained for historical host regressions.
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

    public static Decision freezeOwnMeter(boolean manual, long shutter, int iso,
            float protectionEv, long minShutter, long maxShutter, int minIso, int maxIso) {
        if (shutter<=0L || iso<=0) throw new IllegalArgumentException("C missing actual physical SS/ISO");
        // Bounds can be absent or contradict an actual HAL result. In that case
        // donor exposure remains authoritative and optional protection is deferred.
        if (minShutter<=0L || maxShutter<minShutter || minIso<=0 || maxIso<minIso)
            return new Decision(shutter,iso,0f,"C_NO_SAFE_HIGHLIGHT_BOUNDS");
        // A missing C observation is NOT a zero-clipping measurement.
        boolean measured = Float.isFinite(protectionEv) && protectionEv >= 0f && protectionEv <= MAX_PROTECTION_EV;
        double energy = (double)shutter * iso;
        double target = measured ? energy * Math.pow(2.0, -protectionEv) : energy;
        // Reuse the same negative-only capture arithmetic, with a local same-sample
        // decision instead of an external recipe. No fake sensor timestamp is used.
        return apply(manual, shutter, iso, measured && protectionEv > .03f,
                target, minShutter, maxShutter, minIso, maxIso,
                "C_PRIVATE_RAW_METER");
    }

    public static Decision freeze(boolean userManual, long previewExposureNs, int previewIso,
            long physicalPreviewTimestampNs, long currentCameraGeneration,
            boolean irisRecipeReady, long recipeGeneration, long recipeTimestampNs,
            double recipeEnergy, float recipeOffsetEv,
            long sensorMinExposureNs, long sensorMaxExposureNs,
            int sensorMinIso, int sensorMaxIso) {
        // User manual choices outrank all automatic Iris highlight recipes.
        boolean usable = !(userManual || !irisRecipeReady || recipeGeneration != currentCameraGeneration ||
                physicalPreviewTimestampNs <= 0 || recipeTimestampNs <= 0 ||
                Math.abs((double) physicalPreviewTimestampNs - recipeTimestampNs) > MAX_RECIPE_AGE_NS ||
                !Float.isFinite(recipeOffsetEv) || recipeOffsetEv >= -0.03f ||
                recipeOffsetEv < -MAX_PROTECTION_EV - 0.01f ||
                !Double.isFinite(recipeEnergy) || recipeEnergy <= 0.0);

        return apply(userManual, previewExposureNs, previewIso, usable, recipeEnergy,
                sensorMinExposureNs, sensorMaxExposureNs, sensorMinIso, sensorMaxIso,
                "IRIS_HIGHLIGHT_RECIPE_FROZEN");
    }

    private static Decision apply(boolean userManual, long previewExposureNs, int previewIso,
            boolean usable, double recipeEnergy, long sensorMinExposureNs, long sensorMaxExposureNs,
            int sensorMinIso, int sensorMaxIso, String authority) {
        if (previewExposureNs <= 0 || previewIso <= 0 ||
                sensorMinExposureNs <= 0 || sensorMaxExposureNs < sensorMinExposureNs ||
                sensorMinIso <= 0 || sensorMaxIso < sensorMinIso) {
            throw new IllegalArgumentException("C shutter requires positive physical SS/ISO and valid ranges");
        }
        Decision unchanged = new Decision(previewExposureNs, previewIso, 0f,
                userManual ? "IRIS_MANUAL" : "PHYSICAL_PREVIEW");
        // A real measured pair is valid evidence even if static bounds disagree.
        // Without safe adjustment bounds, preserve it rather than rejecting capture.
        if (userManual || !usable || previewExposureNs < sensorMinExposureNs ||
                previewExposureNs > sensorMaxExposureNs || previewIso < sensorMinIso ||
                previewIso > sensorMaxIso) return unchanged;
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
        return new Decision(selectedShutter, selectedIso, actualEv, authority);
    }
}
