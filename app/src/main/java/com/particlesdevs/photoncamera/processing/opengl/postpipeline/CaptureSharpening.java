package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;

public class CaptureSharpening extends Node {
    public CaptureSharpening() {
        super("", "CaptureSharpening");
    }

    @Override
    public void Compile() {}

    @Override
    public void Run() {
        /*
         * IRIS_26348_MOTION_ZERO_SHARPENING
         * Motion bypasses this entire sharpening stage. The image is passed
         * through unchanged. Photo and other modes remain unchanged.
         */
        if (com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26348_MOTION_ZERO_SHARPENING stage=CaptureSharpening action=bypass");
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "SHARPENING", "stage=CaptureSharpening action=bypass");
            return;
        }
        Log.d(Name,"CaptureSharpening specific:"+basePipeline.mParameters.sensorSpecifics);
        if(basePipeline.mParameters.sensorSpecifics == null){
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            return;
        }
        float str = (0.2f + Math.min(PreferenceKeys.getSharpnessValue(), 0.0f))/0.2f;
        float size = basePipeline.mParameters.sensorSpecifics.captureSharpeningS;
        float strength = basePipeline.mParameters.sensorSpecifics.captureSharpeningIntense*str;
        glProg.setDefine("SHARPSTR",strength);
        float iris26347ShadowProtect = 0.0f;
        if (com.particlesdevs.photoncamera.app.PhotonCamera.getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            float iris26347IsoRisk = com.particlesdevs.photoncamera.util.Math2.smoothstep(
                    800.0f, 6400.0f, Math.max(1.0f, basePipeline.mParameters.iso));
            float iris26347StackRatio =
                    com.particlesdevs.photoncamera.processing.MotionMetrics.isActive()
                            ? com.particlesdevs.photoncamera.processing.MotionMetrics.effectiveStackRatio()
                            : 1.0f;
            iris26347ShadowProtect = com.particlesdevs.photoncamera.util.Math2.clamp(
                    0.58f * iris26347IsoRisk + 0.42f * (1.0f - iris26347StackRatio),
                    0.0f, 0.90f);
        }
        glProg.setDefine("MOTION_SHADOW_PROTECT", iris26347ShadowProtect);
        glProg.setDefine("SHARPSIZEKER",size);
        glProg.setDefine("INSIZE",basePipeline.workSize);
        glProg.useAssetProgram("capturesharpening");
        glProg.setTexture("InputBuffer",previousNode.WorkingTexture);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);

        glProg.closed = true;
    }
}
