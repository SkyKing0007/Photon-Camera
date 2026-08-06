package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.hardware.camera2.CaptureResult;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;

public class Sharpen2 extends Node {
    public Sharpen2() {
        super("", "Sharpening");
    }

    @Override
    public void Compile() {
    }
    
    @Tunable(
            title = "Sharp Size", description = "Size parameter for sharpening",
            category = "Sharpening", min = 0.0f, max = 2.0f, defaultValue = 0.9f, step = 0.01f
    )
    float sharpSize;
    
    @Tunable(
            title = "Sharp Min", description = "Minimum sharpening threshold",
            category = "Sharpening", min = 0.0f, max = 2.0f, defaultValue = 0.4f, step = 0.01f
    )
    float sharpMin;
    
    @Tunable(
            title = "Sharp Max", description = "Maximum sharpening threshold",
            category = "Sharpening", min = 0.0f, max = 2.0f, defaultValue = 1.0f, step = 0.01f
    )
    float sharpMax;
    
    @Tunable(
            title = "Denoise Activity", description = "Denoise intensity parameter",
            category = "Sharpening", min = 0.0f, max = 1.0f, defaultValue = 0.0f, step = 0.01f)
    float denoiseActivity;
    
    @Override
    public void Run() {
        /*
         * IRIS_26348_MOTION_ZERO_SHARPENING
         * Motion bypasses the final sharpening stage as well, producing true
         * zero added sharpening over the whole Motion image.
         */
        if (com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26348_MOTION_ZERO_SHARPENING stage=Sharpen2 action=bypass");
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "SHARPENING", "stage=Sharpen2 action=bypass");
            return;
        }
        glProg.setDefine("INTENSE",denoiseActivity);
        glProg.setDefine("INSIZE",basePipeline.mParameters.rawSize);
        glProg.setDefine("SHARPSIZE",sharpSize);
        glProg.setDefine("SHARPMIN",sharpMin);
        glProg.setDefine("SHARPMAX",sharpMax);
        glProg.setDefine("NOISES",basePipeline.noiseS);
        glProg.setDefine("NOISEO",basePipeline.noiseO);
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
        glProg.useAssetProgram("sharpening/lsharpening3");
        glProg.setVar("size", sharpSize);
        float sharpness = Math.max(PreferenceKeys.getSharpnessValue(), 0.0f);
        glProg.setVar("strength", sharpness);
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setTexture("BlurBuffer",previousNode.WorkingTexture);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
