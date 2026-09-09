package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26616_RETIRED_MOTION_SPATIAL_OWNER
 *
 * 26615 Motion spatial exposure is intentionally gone. This class is now only the exact successful
 * Night scalar presentation node. Any attempt to route Motion through it is a hard failure, which
 * prevents a future hybrid from silently reactivating the retired 96-grid owner.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() { super("", "MotionV2DisplayExposure"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "26616 Motion must use MotionV2WronskiLtm; legacy DisplayExposure retired");
        }
        if (!basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("MotionV2DisplayExposure used outside Iris Night");
        }
        float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid Night presentation gain: " + displayGain);
        }
        if (Math.abs(displayGain - 1.0f) < 1.0e-5f) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN displayGain=1.0 passSkipped=true"
                    + " sourceRestoreHere=false camera2Write=false irisNight=true");
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
                + " sourceRestoreHere=false afterProfileColor=true"
                + " beforeManualIrisControls=true irisNight=true"
                + " camera2Write=false");
    }
}
