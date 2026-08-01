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

    @Tunable(
            title = "Motion final sharpening floor",
            description = "Fraction of the selected final sharpening retained at ISO 3200. 26176 lowers the floor to avoid re-amplifying residual luma and chroma noise.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.60f,
            step = 0.05f
    )
    float motionFinalSharpeningFloor = 0.60f;
    @Override
    public void Run() {
        glProg.setDefine("INTENSE",denoiseActivity);
        glProg.setDefine("INSIZE",basePipeline.mParameters.rawSize);
        glProg.setDefine("SHARPSIZE",sharpSize);
        glProg.setDefine("SHARPMIN",sharpMin);
        glProg.setDefine("SHARPMAX",sharpMax);
        glProg.setDefine("NOISES",basePipeline.noiseS);
        glProg.setDefine("NOISEO",basePipeline.noiseO);
        glProg.useAssetProgram("sharpening/lsharpening3");
        glProg.setVar("size", sharpSize);
        float sharpness = Math.max(PreferenceKeys.getSharpnessValue(), 0.0f);

        float motionSharpScale = 1.0f;

        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

            float motionIso =
                    Math.max(
                            1.0f,
                            basePipeline.mParameters.iso
                    );

            float highIsoBlend =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            motionSharpScale =
                    1.0f
                            - (
                                    1.0f
                                            - motionFinalSharpeningFloor
                              )
                            * highIsoBlend;

            sharpness *= motionSharpScale;

            Log.d(
                    Name,
                    "MOTION_26171_FINAL_SHARPEN_TUNABLE"
                            + " iso=" + motionIso
                            + " scale=" + motionSharpScale
                            + " configuredFloor="
                            + motionFinalSharpeningFloor
                            + " appliedStrength=" + sharpness
            );
        }

        glProg.setVar("strength", sharpness);
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setTexture("BlurBuffer",previousNode.WorkingTexture);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
