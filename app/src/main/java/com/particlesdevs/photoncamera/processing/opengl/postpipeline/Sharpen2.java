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
            defaultValue = 0.45f,
            step = 0.05f
    )
    float motionFinalSharpeningFloor = 0.45f;
    @Override
    public void Run() {
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

        glProg.setDefine("INTENSE",denoiseActivity);
        glProg.setDefine("INSIZE",basePipeline.mParameters.rawSize);
        glProg.setDefine("SHARPSIZE",sharpSize);
        glProg.setDefine("SHARPMIN",sharpMin);
        glProg.setDefine("SHARPMAX",sharpMax);
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
        glProg.useAssetProgram("sharpening/lsharpening3");
        glProg.setVar("size", sharpSize);
        float sharpness = Math.max(PreferenceKeys.getSharpnessValue(), 0.0f);

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
                                            - motionFinalSharpeningFloor
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
                            0.20f + 0.80f * measuredRatio,
                            0.20f,
                            1.0f
                    );
        }

        float sceneShadowLift = com.particlesdevs.photoncamera.util.Math2.clamp(((PostPipeline)basePipeline).motionShadowSceneStrength, 0.0f, 1.0f);
        float actualDisplayGain = Math.max(1.0f, ((PostPipeline)basePipeline).motionAppliedDisplayGain);
        float actualLowerMidLift = com.particlesdevs.photoncamera.util.Math2.clamp(((PostPipeline)basePipeline).motionAppliedLowerMidLift, 0.0f, 0.50f);
        float visibleLiftBlend = com.particlesdevs.photoncamera.util.Math2.clamp((actualDisplayGain - 1.0f) / 2.55f + 0.50f * actualLowerMidLift, 0.0f, 1.0f);
        float displayGainSharpenScale = com.particlesdevs.photoncamera.util.Math2.mix(
                1.0f,
                0.10f,
                visibleLiftBlend
                        * (
                                1.0f
                                        - 0.46f
                                        * basePipeline.mParameters.effectiveStackRatio
                          )
        );
        sharpness *= motionSharpScale;
        sharpness *= temporalConfidenceScale;
        sharpness *= displayGainSharpenScale;

        Log.d(
                Name,
                "MOTION_26286_FINAL_HALO_RESTRAINT"
                        + " effectiveRatio="
                        + basePipeline.mParameters.effectiveStackRatio
                        + " measured="
                        + basePipeline.mParameters.localContributionMeasured
                        + " confidenceScale="
                        + temporalConfidenceScale
                        + " sceneShadowLift=" + sceneShadowLift
                        + " displayGainSharpenScale=" + displayGainSharpenScale
                        + " appliedStrength="
                        + sharpness
        );

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

        /*
         * Build 26294:
         * Do not turn weak-stack shadow residuals into worms, colored rims,
         * or false carpet texture.
         * MOTION_26294_FINAL_WEAK_STACK_SHARPEN_RESTRAINT
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

            sharpness *= weakStackSharpScale;

            Log.d(
                    Name,
                    "MOTION_26294_FINAL_WEAK_STACK_SHARPEN_RESTRAINT"
                            + " localP10="
                            + basePipeline.mParameters
                                    .localContributionP10
                            + " scale="
                            + weakStackSharpScale
                            + " appliedStrength="
                            + sharpness
            );
        }

        /* MOTION_26295_FINAL_RESIDUAL_RESTRAINT */
        if (basePipeline.mParameters.motionCapture) {
            float isoResidual = com.particlesdevs.photoncamera.util.Math2.clamp(
                    (basePipeline.mParameters.iso - 500.0f) / 2200.0f, 0.0f, 1.0f);
            float liftResidual = com.particlesdevs.photoncamera.util.Math2.clamp(
                    ((PostPipeline) basePipeline).motionAppliedLowerMidLift / 0.34f, 0.0f, 1.0f);
            sharpness *= com.particlesdevs.photoncamera.util.Math2.mix(
                    1.0f, 0.82f, Math.max(isoResidual, liftResidual));
        }
        glProg.setVar("strength", sharpness);
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setTexture("BlurBuffer",previousNode.WorkingTexture);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
