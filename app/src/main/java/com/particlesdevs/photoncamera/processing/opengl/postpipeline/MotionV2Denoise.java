package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26411_MOTION_V2_LUMA_CHROMA_RECONSTRUCTION
 * Reference-only residual cleanup. Structural/luma evidence is protected;
 * R-G and B-G chroma residuals are cleaned more strongly.
 */
public final class MotionV2Denoise extends Node {
    public MotionV2Denoise() { super("", "MotionV2Denoise"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2Denoise used outside Motion V2");
        }
        glProg.useAssetProgram("motionv2/denoise");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("noiseS", Math.max(basePipeline.noiseS, 1.0e-8f));
        glProg.setVar("noiseO", Math.max(basePipeline.noiseO, 1.0e-8f));
        glProg.setVar("effectiveSupport",
                Math.max(1.0f, basePipeline.mParameters.motionV2EffectiveSupport));
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        Log.d(Name, "IRIS_26411_V2_LUMA_CHROMA_RECONSTRUCTION"
                + " luma=detailGatedResidual chroma=greenGuidedOpponent"
                + " sharpening=false effectiveSupport="
                + basePipeline.mParameters.motionV2EffectiveSupport);
    }
}