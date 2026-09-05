package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26563_UNIVERSAL_ADAPTIVE_COLOR_APPEARANCE
 *
 * Shared Motion/Night JPEG/UHDR appearance owner. Runs only after the device-specific
 * DNG/Camera2 profile transform and the viewfinder exposure solver, while pixels are still in
 * common extended linear-Display-P3 and before the solved display gain/tone/highlight/gamut render.
 *
 * This is deliberately separate from IRIS_26561_UNIVERSAL_ADAPTIVE_COLOR, which is a camera-RGB
 * unsupported-chroma cleanup and never boosts saturation. This stage can restore weak legitimate
 * colorfulness, but only through a hue/luminance-preserving chroma-axis scalar with reliability,
 * highlight, edge and gamut gates. DNG outputs never traverse this node.
 */
public final class MotionV2AdaptiveColorAppearance extends Node {
    private static final float MAX_WEAK_CHROMA_GAIN = 1.32f;
    private static final float MAX_HIGHLIGHT_CHROMA_GAIN = 1.12f;

    public MotionV2AdaptiveColorAppearance() {
        super("", "MotionV2AdaptiveColorAppearance");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException(
                    "MotionV2AdaptiveColorAppearance outside Iris Motion/Night");
        }
        final float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid display gain before adaptive color appearance: " + displayGain);
        }

        final boolean calibratedProfile = basePipeline.mParameters.HSVMap != null
                && basePipeline.mParameters.HSVMapSize != null
                && basePipeline.mParameters.HSVMapSize.length >= 2
                && basePipeline.mParameters.HSVMapSize[0] > 0
                && basePipeline.mParameters.HSVMapSize[1] > 0
                && basePipeline.mParameters.HSVMap.length >=
                        basePipeline.mParameters.HSVMapSize[0]
                                * basePipeline.mParameters.HSVMapSize[1] * 3;
        if (calibratedProfile) glProg.setDefine("CALIBRATED_PROFILE", 1);
        glProg.useAssetProgram("motionv2/adaptive_color_appearance_26563");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", displayGain);
        float sceneWhite = MotionV2Render.iris26598PublicationSceneWhite(basePipeline.mParameters);
        glProg.setVar("sceneWhite", sceneWhite);
        glProg.setVar("iris26598MotionPublication",
                basePipeline.mParameters.motionV2Active ? 1 : 0);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.i(Name, "IRIS_26567_SHARED_JPEG_COLOR_APPEARANCE"
                + " commonLinearDisplayP3=true"
                + " profileSource=" + (calibratedProfile ? "CALIBRATED_HUESAT" : "UNIVERSAL")
                + " afterDeviceProfileColor=true"
                + " afterViewfinderExposureSolve=true"
                + " beforeDisplayExposure=true"
                + " beforeToneHighlightGamut=true"
                + " dngAffected=false"
                + " maxWeakChromaGain=" + MAX_WEAK_CHROMA_GAIN
                + " maxHighlightChromaGain=" + MAX_HIGHLIGHT_CHROMA_GAIN
                + " sceneWhite=" + sceneWhite
                + " adaptiveSceneWhite=" + basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite
                + " publicationSceneWhiteSource="
                    + (basePipeline.mParameters.motionV2Active ? "BASE_26598_MOTION" : "ADAPTIVE_26591_NIGHT")
                + " publicationCurvePredictor="
                    + (basePipeline.mParameters.motionV2Active ? "EXACT_26597_MOTION" : "PRESERVED_26585_NIGHT")
                + " IRIS_26598_SEMANTIC_AUTHORITY=true"
                + " toneAwareHighlightChroma=true"
                + " displayGain=" + displayGain
                + " irisNight=" + basePipeline.mParameters.irisNightActive
                + " superRes=" + basePipeline.mParameters.motionV2SuperResOutputEnabled
                + " superResScale=" + basePipeline.mParameters.motionV2SuperResOutputScale
                + " huePreservingChromaAxis=true"
                + " luminancePreserving=true"
                + " clippedBorderBoost=false"
                + " manufacturerSpecific=false");
    }
}
