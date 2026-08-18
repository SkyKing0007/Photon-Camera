package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY
 * Applies the existing scalar display normalization only after Wronski.
 * This stage is intentionally non-tunable.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2DisplayExposure used outside Motion V2");
        }

        float gain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", gain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY"
                + " displayGain=" + gain
                + " insideWronski=false"
                + " photonAutoExposure=false"
                + " photonExposureFusion=false"
                + " tunable=false");
    }
}
