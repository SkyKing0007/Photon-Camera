package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26446_TRUE_LOCAL_SUPPORT_DENOISE_NODE
 *
 * Consumes the frame-equivalent support encoded in direct-RGB alpha before
 * MotionV2ColorTransform. No rejected auxiliary image is available to this
 * node, so spatial cleanup cannot reintroduce a temporal pose.
 */
public final class MotionV2LocalSupportDenoise extends Node {
    public MotionV2LocalSupportDenoise() {
        super("", "MotionV2LocalSupportDenoise");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2LocalSupportDenoise outside Motion V2");
        }

        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3;
        if (!directBayer) {
            throw new IllegalStateException(
                    "MotionV2LocalSupportDenoise requires direct RGB carrier");
        }

        float effectiveSupport=Math.max(
                1.0f,
                basePipeline.mParameters.motionV2EffectiveSupport);
        float sensorClipLevel=Math.max(
                1.0f,
                basePipeline.mParameters.motionCanonicalExposureGain);

        glProg.useAssetProgram("motionv2/local_support_denoise");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("effectiveSupport", effectiveSupport);
        glProg.setVar("sensorClipLevel", sensorClipLevel);

        WorkingTexture=basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed=true;

        Log.d(Name, "IRIS_26446_TRUE_LOCAL_SUPPORT_DENOISE"
                + " localSupportUnits=frameEquivalent"
                + " effectiveSupport=" + effectiveSupport
                + " supportSource=directRgbAlpha"
                + " edgeAware=true"
                + " highlightProtected=true"
                + " rejectedAuxPixelsAvailable=false"
                + " sharpening=false");
    }
}