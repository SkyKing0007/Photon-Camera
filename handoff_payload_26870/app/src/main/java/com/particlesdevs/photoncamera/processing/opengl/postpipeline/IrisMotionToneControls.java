package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26514_LINEAR_PRESENTATION_CONTROLS
 * Optional post-reconstruction/pre-render photographic controls. This node is never inserted at
 * neutral 0/0/0, preserving the exact 26513 render input when the new controls are untouched.
 */
public final class IrisMotionToneControls extends Node {
    private final float exposureEv;
    private final float shadows;
    private final float contrast;

    public IrisMotionToneControls(IrisMotionSettings.Snapshot settings) {
        super("", "IrisMotionToneControls");
        exposureEv = settings.exposureEv;
        shadows = settings.shadows;
        contrast = settings.contrast;
    }

    private static float smoothstep26870(float lo,float hi,float value) {
        float t = Math.max(0f,Math.min(1f,(value-lo)/(hi-lo)));
        return t*t*(3f-2f*t);
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("IrisMotionToneControls used outside Motion");
        }
        /* IRIS_26870_B_SCENE_EVIDENCE_TOE.
         * ViewfinderExposureMatcher runs before this node and publishes the
         * true guide percentiles.  No user preference and no arbitrary mode
         * toggle; unsupported/very dark low-signal scenes preserve 26868.
         * This is one optional scalar in the existing shared tone-control
         * shader, not another independent global HDR tone mapper.
         */
        float autoToe26870 = 0.0f;
        if (basePipeline.mParameters.motionV2ReconstructionOwner ==
                com.particlesdevs.photoncamera.processing.render.Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE
                && !basePipeline.mParameters.irisNightActive) {
            float p25 = basePipeline.mParameters.motionV2ToneP25Guide;
            float p50 = basePipeline.mParameters.motionV2ToneP50Guide;
            float gain = basePipeline.mParameters.motionV2DisplayGain;
            if (Float.isFinite(p25) && Float.isFinite(p50) && Float.isFinite(gain)
                    && p25 >= 0f && p50 > 0f && gain > 0f) {
                float lower = p25 * gain;
                float middle = p50 * gain;
                float illuminated = smoothstep26870(0.025f,0.13f,lower);
                float body = smoothstep26870(0.10f,0.35f,middle);
                float avoidBrightShadow = 1f-smoothstep26870(0.35f,0.60f,lower);
                autoToe26870 = 0.65f * illuminated * body * avoidBrightShadow;
            }
        }
        glProg.useAssetProgram("motionv2/iris_tone_controls");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("exposureEv", exposureEv);
        glProg.setVar("shadowsControl", shadows);
        glProg.setVar("contrastControl", contrast);
        glProg.setVar("brightnessTargetGain", basePipeline.mParameters.motionV2DisplayGain);
        glProg.setVar("bAutoShadowToe26870", autoToe26870);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        Log.d(Name, "IRIS_26514_PRESENTATION exposureEv=" + exposureEv
                + " shadows=" + shadows + " contrast=" + contrast
                + " brightnessTargetGain=" + basePipeline.mParameters.motionV2DisplayGain
                + " bAutoShadowToe26870=" + autoToe26870
                + " virtualPresentedDomain=true imageMultiplier=false"
                + " beforeMotionRender=true sdrUhDrCommonSource=true");
    }
}
