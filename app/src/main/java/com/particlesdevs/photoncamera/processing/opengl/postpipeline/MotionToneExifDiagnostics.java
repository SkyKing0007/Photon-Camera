package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import java.util.Locale;

/**
 * Build 26251 diagnostic bridge.
 *
 * Stores one compact Motion tone record for the JPEG EXIF UserComment field.
 * It is diagnostic-only and does not change image processing.
 */
public final class MotionToneExifDiagnostics {
    private static final Object LOCK = new Object();

    private static boolean motion;
    private static float iso;
    private static float effectiveFrames;
    private static float effectiveRatio;
    private static boolean localContributionMeasured;
    private static float noiseS;
    private static float noiseO;

    private static float overexposure;
    private static float underexposure;
    private static float shadowNeed;
    private static float highlightNeed;
    private static float dynamicRangeNeed;
    private static float sceneStrength;

    private static float configuredShadows;
    private static float appliedShadows;
    private static float configuredLtm;
    private static float appliedLtm;

    private static float histogramAverage;
    private static float gainBeforeGuard;
    private static float gainAfterGuard;
    private static float reinhardGain;
    private static float whiteMax;
    private static float lowerMidLift;
    private static float highlightCompression;

    private static float separatedShadowStrength;
    private static float separatedFusionHighlightStrength;
    private static float histogramBrightTail90;
    private static float histogramBrightTail98;
    private static float histogramShadowStrength;
    private static float histogramHighlightStrength;
    private static float shadowStackConfidence;

    private MotionToneExifDiagnostics() {}

    public static void reset(
            boolean isMotion,
            float captureIso,
            float measuredEffectiveFrames,
            float measuredEffectiveRatio,
            boolean measuredLocalContribution,
            float modeledNoiseS,
            float modeledNoiseO) {
        synchronized (LOCK) {
            motion = isMotion;
            iso = captureIso;
            effectiveFrames = measuredEffectiveFrames;
            effectiveRatio = measuredEffectiveRatio;
            localContributionMeasured = measuredLocalContribution;
            noiseS = modeledNoiseS;
            noiseO = modeledNoiseO;

            overexposure = Float.NaN;
            underexposure = Float.NaN;
            shadowNeed = Float.NaN;
            highlightNeed = Float.NaN;
            dynamicRangeNeed = Float.NaN;
            sceneStrength = Float.NaN;
            configuredShadows = Float.NaN;
            appliedShadows = Float.NaN;
            configuredLtm = Float.NaN;
            appliedLtm = Float.NaN;
            histogramAverage = Float.NaN;
            gainBeforeGuard = Float.NaN;
            gainAfterGuard = Float.NaN;
            reinhardGain = Float.NaN;
            whiteMax = Float.NaN;
            lowerMidLift = Float.NaN;
            highlightCompression = Float.NaN;
            separatedShadowStrength = Float.NaN;
            separatedFusionHighlightStrength = Float.NaN;
            histogramBrightTail90 = Float.NaN;
            histogramBrightTail98 = Float.NaN;
            histogramShadowStrength = Float.NaN;
            histogramHighlightStrength = Float.NaN;
            shadowStackConfidence = Float.NaN;
        }
    }

    public static void recordDetector(
            float exposureOver,
            float exposureUnder,
            float measuredShadowNeed,
            float measuredHighlightNeed,
            float measuredDynamicRangeNeed,
            float measuredSceneStrength) {
        synchronized (LOCK) {
            overexposure = exposureOver;
            underexposure = exposureUnder;
            shadowNeed = measuredShadowNeed;
            highlightNeed = measuredHighlightNeed;
            dynamicRangeNeed = measuredDynamicRangeNeed;
            sceneStrength = measuredSceneStrength;
        }
    }

    public static void recordSeparatedStrengths(
            float shadowStrength,
            float fusionHighlightStrength) {
        synchronized (LOCK) {
            separatedShadowStrength = shadowStrength;
            separatedFusionHighlightStrength = fusionHighlightStrength;
        }
    }

    public static void recordHistogramTone(
            float brightTail90,
            float brightTail98,
            float shadowStrength,
            float highlightStrength,
            float stackConfidence) {
        synchronized (LOCK) {
            histogramBrightTail90 = brightTail90;
            histogramBrightTail98 = brightTail98;
            histogramShadowStrength = shadowStrength;
            histogramHighlightStrength = highlightStrength;
            shadowStackConfidence = stackConfidence;
        }
    }

    public static void recordInitial(
            float sourceShadows,
            float finalShadows,
            float sourceLtm,
            float finalLtm) {
        synchronized (LOCK) {
            configuredShadows = sourceShadows;
            appliedShadows = finalShadows;
            configuredLtm = sourceLtm;
            appliedLtm = finalLtm;
        }
    }

    public static void recordAutoExposure(
            float avg,
            float beforeGuard,
            float afterGuard,
            float finalGain,
            float finalWhiteMax,
            float lift,
            float shoulder) {
        synchronized (LOCK) {
            histogramAverage = avg;
            gainBeforeGuard = beforeGuard;
            gainAfterGuard = afterGuard;
            reinhardGain = finalGain;
            whiteMax = finalWhiteMax;
            lowerMidLift = lift;
            highlightCompression = shoulder;
        }
    }

    private static float smoothstep(float edge0, float edge1, float value) {
        float x = Math.max(0.0f, Math.min(1.0f, (value - edge0) / (edge1 - edge0)));
        return x * x * (3.0f - 2.0f * x);
    }

    private static float predictedToeGain(float luma) {
        if (!Float.isFinite(lowerMidLift)) {
            return Float.NaN;
        }

        float blackProtection = smoothstep(0.006f, 0.040f, luma);
        float upperMidProtection = 1.0f - smoothstep(0.28f, 0.62f, luma);
        float lowerMidMask = blackProtection * upperMidProtection;
        float deepShadowWeight = 1.0f - smoothstep(0.045f, 0.22f, luma);
        float midShadowWeight =
                smoothstep(0.05f, 0.18f, luma)
                        * (1.0f - smoothstep(0.30f, 0.60f, luma));

        return 1.0f
                + lowerMidLift
                * lowerMidMask
                * (0.70f + 1.85f * deepShadowWeight + 0.35f * midShadowWeight);
    }

    private static String f(float value) {
        if (!Float.isFinite(value)) {
            return "NA";
        }
        return String.format(Locale.US, "%.6f", value);
    }

    public static String imageDescription() {
        synchronized (LOCK) {
            if (!motion) {
                return "Photon 26251 tone diagnostics: non-Motion capture";
            }
            return "Photon 26260 balanced tone and safe alignment-grid diagnostics; shader=autoexposure/apply; see UserComment";
        }
    }

    public static String userComment() {
        synchronized (LOCK) {
            return "PHOTON_MOTION_TONE_MERGE_V26260"
                    + ";motion=" + motion
                    + ";shader=autoexposure/apply"
                    + ";shaderMarker=BUILD_26260_SAFE_ALIGNMENT_GRID_WARP"
                    + ";iso=" + f(iso)
                    + ";effectiveFrames=" + f(effectiveFrames)
                    + ";effectiveRatio=" + f(effectiveRatio)
                    + ";localContributionMeasured=" + localContributionMeasured
                    + ";noiseS=" + f(noiseS)
                    + ";noiseO=" + f(noiseO)
                    + ";overexposure=" + f(overexposure)
                    + ";underexposure=" + f(underexposure)
                    + ";shadowNeed=" + f(shadowNeed)
                    + ";highlightNeed=" + f(highlightNeed)
                    + ";dynamicRangeNeed=" + f(dynamicRangeNeed)
                    + ";sceneStrengthLegacy=" + f(sceneStrength)
                    + ";shadowStrength=" + f(separatedShadowStrength)
                    + ";fusionHighlightStrength="
                    + f(separatedFusionHighlightStrength)
                    + ";brightTail90=" + f(histogramBrightTail90)
                    + ";brightTail98=" + f(histogramBrightTail98)
                    + ";histShadowStrength=" + f(histogramShadowStrength)
                    + ";histHighlightStrength="
                    + f(histogramHighlightStrength)
                    + ";shadowStackConfidence="
                    + f(shadowStackConfidence)
                    + ";mergeGuard=darkStructureHardReferenceLockV5;alignment=floatBilinearQuadraticV1;warp=safeSharedGridValidatedWarpV3;alignmentInput=initializedMildHighPassV1"
                    + ";configuredShadows=" + f(configuredShadows)
                    + ";appliedShadows=" + f(appliedShadows)
                    + ";configuredLtm=" + f(configuredLtm)
                    + ";appliedLtm=" + f(appliedLtm)
                    + ";histAvg=" + f(histogramAverage)
                    + ";gainBeforeGuard=" + f(gainBeforeGuard)
                    + ";gainAfterGuard=" + f(gainAfterGuard)
                    + ";reinhardGain=" + f(reinhardGain)
                    + ";whiteMax=" + f(whiteMax)
                    + ";lowerMidLift=" + f(lowerMidLift)
                    + ";highlightCompression=" + f(highlightCompression)
                    + ";toeGainL003=" + f(predictedToeGain(0.003f))
                    + ";toeGainL006=" + f(predictedToeGain(0.006f))
                    + ";toeGainL010=" + f(predictedToeGain(0.010f))
                    + ";toeGainL020=" + f(predictedToeGain(0.020f))
                    + ";toeGainL050=" + f(predictedToeGain(0.050f))
                    + ";toeGainL100=" + f(predictedToeGain(0.100f))
                    + ";toeGainL200=" + f(predictedToeGain(0.200f))
                    + ";toeGainL400=" + f(predictedToeGain(0.400f))
                    + ";diagnosticOnly=true";
        }
    }
}