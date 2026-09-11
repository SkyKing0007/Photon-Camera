package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26628_RESTRAINED_COLOR_PRESENTATION
 *
 * Motion/Night-only Iris aesthetic layer.  Correct camera/profile color is already established by
 * MotionV2ColorTransform.  This stage contains no restorative/adaptive saturation authority: it
 * performs one fixed, pixel-local, luminance/hue-preserving chroma contraction chosen to retain the
 * slightly restrained 26626 presentation.  It can never amplify a residual colored edge.
 */
public final class MotionV2AdaptiveColorAppearance extends Node {
    public static final float IRIS_26628_PRESENTATION_CHROMA_SCALE = 0.95f;

    public MotionV2AdaptiveColorAppearance() { super("", "MotionV2AdaptiveColorAppearance"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2AdaptiveColorAppearance outside Iris Motion/Night");
        }
        glProg.useAssetProgram("motionv2/adaptive_color_appearance_26563");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("presentationChromaScale", IRIS_26628_PRESENTATION_CHROMA_SCALE);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.i(Name, "IRIS_26628_RESTRAINED_COLOR_PRESENTATION"
                + " mode=" + (basePipeline.mParameters.irisNightActive ? "NIGHT" : "MOTION")
                + " chromaScale=" + IRIS_26628_PRESENTATION_CHROMA_SCALE
                + " adaptiveBoost=false"
                + " neighborColorBorrowing=false"
                + " huePreserving=true"
                + " luminancePreserving=true"
                + " chromaExpansionImpossible=true"
                + " beforeExistingToneHighlightGamut=true"
                + " superRes=" + basePipeline.mParameters.motionV2SuperResOutputEnabled
                + " legacyPhotonColorAffected=false"
                + " dngAffected=false");
    }
}
