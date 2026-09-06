package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26604_TONE_TARGET_ONLY_PRESENTATION_OWNER
 * Motion keeps the solved viewfinder response only as a target consumed by the single final
 * tone owner. It must never multiply the common HDR source texture. Night intentionally retains
 * its proven 26516 scalar path. This removes the 26603 RGB*displayGain -> late-shoulder split that
 * flattened clouds/curtains while preserving the same requested body brightness target.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2DisplayExposure used outside Motion V2");
        }
        float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid viewfinder presentation gain: " + displayGain);
        }

        if (basePipeline.mParameters.motionV2Active) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26604_VIEWFINDER_TONE_TARGET"
                    + " brightnessTargetGain=" + displayGain
                    + " imageMultiplier=false passThrough=true"
                    + " canonicalToneOwner=MotionV2Render"
                    + " superResSameTone=true camera2Write=false");
            return;
        }

        if (Math.abs(displayGain - 1.0f) < 1.0e-5f) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN displayGain=1.0 passSkipped=true"
                    + " sourceRestoreHere=false camera2Write=false");
            return;
        }

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", displayGain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN"
                + " displayGain=" + displayGain
                + " sourceRestoreHere=false"
                + " afterProfileColor=true"
                + " beforeManualIrisControls=true"
                + " extremeLift=" + (displayGain >= 4.0f)
                + " headroomOwner=MotionV2RenderCommonRgbScalar"
                + " duplicateHeadroomLimiter=false"
                + " camera2Write=false");
    }
}
