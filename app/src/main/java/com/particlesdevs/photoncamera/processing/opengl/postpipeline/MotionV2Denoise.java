package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26430_MOTION_V2_OWNED_RESIDUAL_CLEANUP
 *
 * 26411's reference-era denoiser is retired.
 *
 * 26430 consumes only Motion V2's measured effective temporal support.
 * It does NOT consume basePipeline.noiseS/noiseO, Photon noiseRstr,
 * ESD strengths, or generic post-processing denoise controls.
 *
 * The temporal reconstruction is now the primary denoiser. This stage performs
 * only light residual 3x3 cleanup and never sharpens.
 */
public final class MotionV2Denoise extends Node {
    public MotionV2Denoise() { super("", "MotionV2Denoise"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2Denoise used outside Motion V2");
        }

        float effectiveSupport = Math.max(
                1.0f, basePipeline.mParameters.motionV2EffectiveSupport);

        glProg.useAssetProgram("motionv2/denoise");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("effectiveSupport", effectiveSupport);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP"
                + " effectiveSupport=" + effectiveSupport
                + " kernel=3x3"
                + " referenceEdgeAnchor=true"
                + " whitePointOwnedHighlights=true"
                + " residualCleanupReduced=true"
                + " photonNoiseStateConsumed=false"
                + " noiseRstrConsumed=false"
                + " temporalReconstructionPrimaryDenoiser=true"
                + " sharpening=false");
    }
}
