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

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("IrisMotionToneControls used outside Motion");
        }
        glProg.useAssetProgram("motionv2/iris_tone_controls");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("exposureEv", exposureEv);
        glProg.setVar("shadowsControl", shadows);
        glProg.setVar("contrastControl", contrast);
        glProg.setVar("brightnessTargetGain", basePipeline.mParameters.motionV2DisplayGain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        Log.d(Name, "IRIS_26514_PRESENTATION exposureEv=" + exposureEv
                + " shadows=" + shadows + " contrast=" + contrast
                + " brightnessTargetGain=" + basePipeline.mParameters.motionV2DisplayGain
                + " virtualPresentedDomain=true imageMultiplier=false"
                + " beforeMotionRender=true sdrUhDrCommonSource=true");
    }
}
