package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * C-only request-admission policy for historical RAW ZSL samples.
 * Camera2 request keys are immutable; only an actual producer request can
 * prove HAL NR/EDGE were OFF. Missing keys are NOT implicitly OFF.
 *
 * Constants match CameraMetadata NOISE_REDUCTION_MODE_OFF and EDGE_MODE_OFF,
 * both defined as zero. This pure Java check never modifies A/B preview
 * capture settings or attempts to infer HAL behavior from image pixels.
 */
public final class Iris26975COffModePolicy {
    private Iris26975COffModePolicy() { }
    public static boolean acceptZslRequest(Integer noiseReduction, Integer edgeMode) {
        return noiseReduction != null && edgeMode != null &&
                noiseReduction == 0 && edgeMode == 0;
    }
}
