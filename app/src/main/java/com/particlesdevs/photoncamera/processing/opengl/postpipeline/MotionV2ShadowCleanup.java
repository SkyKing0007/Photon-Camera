package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26419_MOTION_V2_SHADOW_UNIFORMITY
 *
 * V2-owned residual low-signal cleanup. The temporal reconstructor remains the
 * primary denoiser and MotionV2Denoise remains the support/noise-aware residual
 * stage. This node specifically suppresses coarse chroma/CFA-periodic residue
 * that becomes visible after extreme shadow lifting.
 */
public final class MotionV2ShadowCleanup extends Node {
    public MotionV2ShadowCleanup() {
        super("", "MotionV2ShadowCleanup");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2ShadowCleanup used outside Motion V2");
        }

        glProg.useAssetProgram("motionv2/shadow_cleanup");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name,
                "IRIS_26419_V2_SHADOW_UNIFORMITY"
                + " lowSignalOnly=true"
                + " chromaCleanup=strong"
                + " lumaCleanup=restrained"
                + " edgeAware=true"
                + " sharpening=false");
    }
}