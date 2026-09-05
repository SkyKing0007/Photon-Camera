package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26516_VIEWFINDER_PRESENTATION_EXPOSURE_OWNER
 * Applies only the post-color presentation gain solved from the shutter-time viewfinder.
 * When Spatial/Bento BaselineExposure exists, source restoration is owned by
 * MotionV2MgcSourceExposure instead. Sabre has no such source-domain pass.
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
