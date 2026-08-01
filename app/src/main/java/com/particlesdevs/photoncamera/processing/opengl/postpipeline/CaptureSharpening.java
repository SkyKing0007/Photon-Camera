package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;

public class CaptureSharpening extends Node {
    @Tunable(
            title = "Motion capture sharpening floor",
            description = "Fraction of normal capture sharpening retained at ISO 3200. 26176 reduces high-ISO sharpening so residual noise is not enlarged into clumps.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.25f,
            step = 0.05f
    )
    float motionCaptureSharpeningFloor = 0.25f;

    public CaptureSharpening() {
        super("", "CaptureSharpening");
    }

    @Override
    public void Compile() {}

    @Override
    public void Run() {
        Log.d(Name,"CaptureSharpening specific:"+basePipeline.mParameters.sensorSpecifics);
        if(basePipeline.mParameters.sensorSpecifics == null){
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            return;
        }
        float str = (0.2f + Math.min(PreferenceKeys.getSharpnessValue(), 0.0f))/0.2f;
        float size = basePipeline.mParameters.sensorSpecifics.captureSharpeningS;
        float strength = basePipeline.mParameters.sensorSpecifics.captureSharpeningIntense*str;

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
                                            - motionCaptureSharpeningFloor
                              )
                            * highIsoBlend;

            strength *= motionSharpScale;

            Log.d(
                    Name,
                    "MOTION_26171_CAPTURE_SHARPEN_TUNABLE"
                            + " iso=" + motionIso
                            + " scale=" + motionSharpScale
                            + " configuredFloor="
                            + motionCaptureSharpeningFloor
                            + " appliedStrength=" + strength
            );
        }

        glProg.setDefine("SHARPSTR",strength);
        glProg.setDefine("SHARPSIZEKER",size);
        glProg.setDefine("INSIZE",basePipeline.workSize);
        glProg.useAssetProgram("capturesharpening");
        glProg.setTexture("InputBuffer",previousNode.WorkingTexture);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);

        glProg.closed = true;
    }
}
