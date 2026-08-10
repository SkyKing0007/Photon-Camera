package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/** IRIS_26420_MOTION_V2_CANONICAL_TONE_ONLY */
public final class MotionV2Render extends Node {
    public MotionV2Render() { super("", "MotionV2Render"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2Render used outside Motion V2");
        }
        glProg.useAssetProgram("motionv2/render");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        Log.d(Name, "IRIS_26420_V2_RENDER colorTransform=false canonicalSignalAlreadyApplied=true toneOnly=true"
                + " secondExposureGain=false localTone=false sharpening=false");
    }
}