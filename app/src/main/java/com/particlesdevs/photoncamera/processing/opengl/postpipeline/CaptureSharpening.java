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
            defaultValue = 0.45f,
            step = 0.05f
    )
    float motionCaptureSharpeningFloor = 0.45f;

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
        float temporalConfidenceScale = 1.0f;

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

            if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            float measuredRatio =
                    basePipeline.mParameters.localContributionMeasured
                            ? basePipeline.mParameters.effectiveStackRatio
                            : 1.0f;

            temporalConfidenceScale =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            0.25f + 0.75f * measuredRatio,
                            0.25f,
                            1.0f
                    );
        }

        float sceneShadowLift = com.particlesdevs.photoncamera.util.Math2.clamp(((PostPipeline)basePipeline).motionShadowSceneStrength, 0.0f, 1.0f);
        float actualDisplayGain = Math.max(1.0f, ((PostPipeline)basePipeline).motionAppliedDisplayGain);
        float actualLowerMidLift = com.particlesdevs.photoncamera.util.Math2.clamp(((PostPipeline)basePipeline).motionAppliedLowerMidLift, 0.0f, 0.50f);
        float visibleLiftBlend = com.particlesdevs.photoncamera.util.Math2.clamp((actualDisplayGain - 1.0f) / 2.55f + 0.50f * actualLowerMidLift, 0.0f, 1.0f);
        float displayGainSharpenScale = com.particlesdevs.photoncamera.util.Math2.mix(
                1.0f,
                0.16f,
                visibleLiftBlend
                        * (
                                1.0f
                                        - 0.48f
                                        * basePipeline.mParameters.effectiveStackRatio
                          )
        );
        strength *= motionSharpScale;
        strength *= temporalConfidenceScale;
        strength *= displayGainSharpenScale;

        Log.d(
                Name,
                "MOTION_26286_CAPTURE_HALO_RESTRAINT"
                        + " effectiveRatio="
                        + basePipeline.mParameters.effectiveStackRatio
                        + " measured="
                        + basePipeline.mParameters.localContributionMeasured
                        + " confidenceScale="
                        + temporalConfidenceScale
                        + " sceneShadowLift=" + sceneShadowLift
                        + " displayGainSharpenScale=" + displayGainSharpenScale
        );

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

        float motionResidualNoiseScale = 1.0f;

        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            float effectiveRatio =
                    basePipeline.mParameters.localContributionMeasured
                            ? Math.max(
                                0.0f,
                                Math.min(
                                    1.0f,
                                    basePipeline.mParameters.effectiveStackRatio
                                )
                            )
                            : 1.0f;
            float lowerRatio =
                    basePipeline.mParameters.localContributionMeasured
                            ? Math.max(
                                0.0f,
                                Math.min(
                                    1.0f,
                                    basePipeline.mParameters.localContributionP25
                                )
                            )
                            : effectiveRatio;
            float stackSupport =
                    Math.max(
                            0.0f,
                            Math.min(
                                    1.0f,
                                    0.65f * effectiveRatio
                                            + 0.35f * lowerRatio
                            )
                    );
            float sceneShadowLift =
                    Math.max(
                            0.0f,
                            Math.min(
                                    1.0f,
                                    ((PostPipeline) basePipeline)
                                            .motionShadowSceneStrength
                            )
                    );
            motionResidualNoiseScale =
                    Math.max(
                            1.0f,
                            Math.min(
                                    2.60f,
                                    1.0f
                                            + 1.15f * (1.0f - stackSupport)
                                            + 0.85f * sceneShadowLift
                            )
                    );
        }

        /*
         * Build 26294:
         * Do not turn weak-stack shadow residuals into worms, colored rims,
         * or false carpet texture.
         * MOTION_26294_CAPTURE_WEAK_STACK_SHARPEN_RESTRAINT
         */
        if (basePipeline.mParameters.motionCapture
                && basePipeline.mParameters.localContributionMeasured) {

            float support =
                    Math.max(
                            0.0f,
                            Math.min(
                                    1.0f,
                                    (
                                        basePipeline.mParameters
                                                .localContributionP10
                                                - 3.0f
                                    ) / 5.0f
                            )
                    );

            float weakStackSharpScale =
                    0.72f + (1.0f - 0.72f) * support;

            strength *= weakStackSharpScale;

            Log.d(
                    Name,
                    "MOTION_26294_CAPTURE_WEAK_STACK_SHARPEN_RESTRAINT"
                            + " localP10="
                            + basePipeline.mParameters
                                    .localContributionP10
                            + " scale="
                            + weakStackSharpScale
                            + " appliedStrength="
                            + strength
            );
        }

        /* MOTION_26295_CAPTURE_RESIDUAL_RESTRAINT */
        if (basePipeline.mParameters.motionCapture) {
            float isoResidual = com.particlesdevs.photoncamera.util.Math2.clamp(
                    (basePipeline.mParameters.iso - 500.0f) / 2200.0f, 0.0f, 1.0f);
            float liftResidual = com.particlesdevs.photoncamera.util.Math2.clamp(
                    ((PostPipeline) basePipeline).motionAppliedLowerMidLift / 0.34f, 0.0f, 1.0f);
            strength *= com.particlesdevs.photoncamera.util.Math2.mix(
                    1.0f, 0.84f, Math.max(isoResidual, liftResidual));
        }
        glProg.setDefine("SHARPSTR",strength);
        glProg.setDefine("SHARPSIZEKER",size);
        glProg.setDefine("INSIZE",basePipeline.workSize);
        glProg.setDefine("NOISES",basePipeline.noiseS);
        glProg.setDefine("NOISEO",basePipeline.noiseO);
        glProg.setDefine(
                "MOTIONRESIDUALNOISESCALE",
                motionResidualNoiseScale
        );
        glProg.setDefine(
                "MOTIONHALORESTRAINT",
                com.particlesdevs.photoncamera.app.PhotonCamera
                                .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION
        );
        glProg.useAssetProgram("capturesharpening");
        glProg.setTexture("InputBuffer",previousNode.WorkingTexture);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);

        glProg.closed = true;
    }
}
