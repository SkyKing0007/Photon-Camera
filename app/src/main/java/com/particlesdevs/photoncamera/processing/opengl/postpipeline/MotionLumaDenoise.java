package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Math2;

public class MotionLumaDenoise extends Node {
    @Tunable(
            title = "Motion luma cleanup enable",
            description = "Enable the additional dark flat-area luma residual cleanup.",
            category = "Motion Noise Tuning",
            min = 0,
            max = 1,
            defaultValue = 1,
            step = 1
    )
    boolean motionLumaCleanupEnable = true;

    @Tunable(
            title = "Motion luma cleanup strength",
            description = "Maximum cleanup strength at ISO 3200. 26176 increases flat-area cleanup while retaining the existing noise gate and detail protection.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.60f,
            defaultValue = 0.14f,
            step = 0.01f
    )
    float motionLumaCleanupMaximum = 0.14f;

    @Tunable(
            title = "Motion luma noise threshold",
            description = "Multiplier applied to the modeled noise threshold. Higher values classify more texture as noise.",
            category = "Motion Noise Tuning",
            min = 0.50f,
            max = 2.00f,
            defaultValue = 1.00f,
            step = 0.05f
    )
    float motionLumaNoiseGain = 1.00f;

    @Tunable(
            title = "Motion luma kernel radius",
            description = "Radius of each separable luma pass in pixels.",
            category = "Motion Noise Tuning",
            min = 1,
            max = 3,
            defaultValue = 2,
            step = 1
    )
    int motionLumaKernelRadius = 2;

    public MotionLumaDenoise() {
        super("", "MotionLumaDenoise");
    }

    @Override
    public void Compile() {
    }

    private void configurePass(
            int direction,
            float strength,
            float noiseGain
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine(
                "KSIZE",
                motionLumaKernelRadius
        );
        glProg.setDefine("STRENGTH", strength);
        glProg.setDefine("NOISEGAIN", noiseGain);
        glProg.setDefine("NOISES", basePipeline.noiseS);
        glProg.setDefine("NOISEO", basePipeline.noiseO);
    }

    @Override
    public void Run() {
        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION
                || !motionLumaCleanupEnable) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float motionIso =
                Math.max(
                        1.0f,
                        basePipeline.mParameters.iso
                );

        float highIsoBlend =
                Math2.clamp(
                        (motionIso - 800.0f) / 2400.0f,
                        0.0f,
                        1.0f
                );

        float indoorHdrStrength =
                ((PostPipeline) basePipeline)
                        .indoorHdrSceneStrength;

        float strength =
                motionLumaCleanupMaximum
                        * highIsoBlend
                        * (
                                1.0f
                                        - 0.75f
                                        * indoorHdrStrength
                        );

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26171_LUMA_TUNABLE"
                            + " iso=" + motionIso
                            + " enabled=false"
                            + " reason=belowIso800"
                            + " chromaPreserved=true"
            );

            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float noiseGain =
                motionLumaNoiseGain;

        configurePass(
                0,
                strength,
                noiseGain
        );

        glProg.useAssetProgram(
                "denoise/motionlumadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                previousNode.WorkingTexture
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        glProg.drawBlocks(
                basePipeline.main3
        );

        glProg.closed = true;

        configurePass(
                1,
                strength,
                noiseGain
        );

        glProg.useAssetProgram(
                "denoise/motionlumadenoise"
        );

        glProg.setTexture(
                "InputBuffer",
                basePipeline.main3
        );

        glProg.setTexture(
                "GuideBuffer",
                previousNode.WorkingTexture
        );

        WorkingTexture =
                basePipeline.getMain();

        glProg.drawBlocks(
                WorkingTexture
        );

        glProg.closed = true;

        Log.d(
                Name,
                "MOTION_26171_LUMA_TUNABLE"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " indoorHdrStrength="
                        + indoorHdrStrength
                        + " sceneGatedLumaReduction="
                        + (0.75f * indoorHdrStrength)
                        + " noiseGain=" + noiseGain
                        + " passes=2"
                        + " kernelRadiusPixels=" + motionLumaKernelRadius
                        + " policy=noiseThresholdedFlatDarkOnly"
                        + " chromaPreserved=true"
                        + " strongEdgesPreserved=true"
                        + " placement=afterInitialBeforeCoarseChroma"
        );
    }
}
