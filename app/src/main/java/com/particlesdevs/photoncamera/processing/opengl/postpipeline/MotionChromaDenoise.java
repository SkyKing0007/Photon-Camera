package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.MotionLensNoiseProfile;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Math2;

public class MotionChromaDenoise extends Node {
    @Tunable(
            title = "Motion chroma cleanup enable",
            description = "Enable broad dark-area chroma-cloud cleanup.",
            category = "Motion Noise Tuning",
            min = 0,
            max = 1,
            defaultValue = 1,
            step = 1
    )
    boolean motionChromaCleanupEnable = true;

    @Tunable(
            title = "Motion chroma cleanup strength",
            description = "Maximum broad chroma cleanup at ISO 3200. 26176 raises cleanup moderately to suppress the remaining broad color clouds without using shadow desaturation.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.30f,
            step = 0.01f
    )
    float motionChromaCleanupMaximum = 0.30f;

    /*
     * Build 26222:
     * Extra cleanup reserved for extreme low-light Motion captures. The
     * shader still gates it with dark, flat and saturation protection.
     */
    float motionExtremeNightChromaMaximum = 0.46f;

    @Tunable(
            title = "Motion chroma radius",
            description = "Requested full-resolution chroma radius in pixels. Internally rounded to the nearest four-pixel step.",
            category = "Motion Noise Tuning",
            min = 4,
            max = 48,
            defaultValue = 8,
            step = 1
    )
    int motionChromaRadiusPixels = 8;

    @Tunable(
            title = "Motion chroma guide tolerance",
            description = "Luma difference allowed across the broad chroma filter. Lower values protect object boundaries and color separation.",
            category = "Motion Noise Tuning",
            min = 0.02f,
            max = 0.15f,
            defaultValue = 0.055f,
            step = 0.01f
    )
    float motionChromaGuideSigmaMaximum = 0.055f;

    @Tunable(
            title = "Motion shadow color neutralization",
            description = "Additional deepest-shadow desaturation. Default is zero because 26170 removed legitimate color.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.20f,
            defaultValue = 0.0f,
            step = 0.01f
    )
    float motionShadowNeutralization = 0.0f;

    public MotionChromaDenoise() {
        super("", "MotionChromaDenoise");
    }

    @Override
    public void Compile() {
    }

    private void configurePass(
            int direction,
            int sampleStep,
            float strength,
            float guideSigma
    ) {
        glProg.setDefine("DIRECTION", direction);
        glProg.setDefine("KSIZE", 4);
        glProg.setDefine("SAMPLESTEP", sampleStep);
        glProg.setDefine("CHROMASTRENGTH", strength);
        glProg.setDefine("GUIDESIGMA", guideSigma);
        glProg.setDefine(
                "SHADOWNEUTRALIZATION",
                motionShadowNeutralization
        );
        glProg.setDefine("NOISES", basePipeline.noiseS);
        glProg.setDefine("NOISEO", basePipeline.noiseO);

        /* Build 26270: protect bright textured color without global saturation. */
        glProg.setDefine("BRIGHTPROTECTSTART", 0.42f);
        glProg.setDefine("BRIGHTPROTECTEND", 0.76f);
        glProg.setDefine("CHROMAEDGELOW", 0.018f);
        glProg.setDefine("CHROMAEDGEHIGH", 0.105f);
        glProg.setDefine("CHROMASIMILARITYMIN", 0.028f);
        glProg.setDefine("CHROMASIMILARITYMAX", 0.145f);
    }

    @Override
    public void Run() {
        if (PhotonCamera.getSettings().selectedMode
                != CameraMode.MOTION
                || !motionChromaCleanupEnable) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float motionIso =
                Math.max(
                        1.0f,
                        basePipeline.mParameters.iso
                );

        /*
         * Build 26261:
         * The old curve produced only about 0.096 chroma strength near
         * ISO 1600 on telephoto. Start earlier and ramp faster now that
         * alignment corruption is no longer masquerading as color detail.
         */
        float highIsoBlend =
                Math2.clamp(
                        (motionIso - 250.0f) / 1700.0f,
                        0.0f,
                        1.0f
                );

        float measuredRatio =
                basePipeline.mParameters.localContributionMeasured
                        ? basePipeline.mParameters.effectiveStackRatio
                        : 1.0f;

        float lowConfidence =
                Math2.clamp(
                        1.0f - measuredRatio,
                        0.0f,
                        1.0f
                );

        float extremeNightBlend =
                Math2.clamp(
                        (motionIso - 2800.0f) / 2400.0f,
                        0.0f,
                        1.0f
                );

        MotionLensNoiseProfile.Resolved automaticLensProfile =
                MotionLensNoiseProfile.resolve(
                        PreferenceKeys.getFloat(
                                PreferenceKeys.Key.KEY_MOTION_LUMA_STRENGTH
                        ),
                        PreferenceKeys.getFloat(
                                PreferenceKeys.Key.KEY_MOTION_CHROMA_STRENGTH
                        ),
                        PreferenceKeys.getFloat(
                                PreferenceKeys.Key.KEY_MOTION_TEXTURE_PRESERVATION
                        ),
                        PreferenceKeys.getFloat(
                                PreferenceKeys.Key.KEY_MOTION_SPATIAL_DENOISE
                        ),
                        PreferenceKeys.getFloat(
                                PreferenceKeys.Key.KEY_MOTION_SHADOW_CLEANUP
                        )
                );

        float perLensChromaMaximum =
                Math2.clamp(
                        automaticLensProfile.chroma,
                        0.0f,
                        0.60f
                );

        float perLensExtremeNightMaximum =
                Math.min(
                        0.76f,
                        perLensChromaMaximum + 0.16f
                );

        float maximumStrength =
                Math2.mix(
                        perLensChromaMaximum,
                        perLensExtremeNightMaximum,
                        extremeNightBlend
                );

        float sceneShadowLift = Math2.clamp(((PostPipeline)basePipeline).motionShadowSceneStrength, 0.0f, 1.0f);
        float displayGainEstimate = Math.max(1.0f, ((PostPipeline)basePipeline).motionAppliedDisplayGain);
        float lowerMidLift = Math2.clamp(((PostPipeline)basePipeline).motionAppliedLowerMidLift, 0.0f, 0.50f);
        float displayLiftBlend = Math2.clamp((displayGainEstimate - 1.0f) / 2.55f + 0.55f * lowerMidLift, 0.0f, 1.0f);
        float visibleNoiseBlend = Math.max(
                highIsoBlend,
                Math.max(lowConfidence, displayLiftBlend));
        float strength = Math.min(
                0.88f,
                maximumStrength * Math2.mix(highIsoBlend, 1.0f, 0.72f * displayLiftBlend));
        strength *= Math2.mix(0.82f, 1.16f, visibleNoiseBlend);

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26272_HDR_SHADOW_ARTIFACT_REPAIR"
                            + " iso=" + motionIso
                            + " enabled=false"
                            + " reason=belowIso600"
                            + " lumaPreserved=true"
            );

            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        float guideSigma =
                Math2.mix(
                        0.038f,
                        Math.min(
                                motionChromaGuideSigmaMaximum,
                                0.052f
                        ),
                        highIsoBlend
                );

        int adaptiveRadiusPixels;

        if (motionIso >= 3600.0f || displayLiftBlend >= 0.82f) {
            adaptiveRadiusPixels = 16;
        } else if (lowConfidence >= 0.30f || displayLiftBlend >= 0.55f) {
            adaptiveRadiusPixels = 12;
        } else if (motionIso >= 1000.0f || lowConfidence >= 0.14f || displayLiftBlend >= 0.25f) {
            adaptiveRadiusPixels = 8;
        } else {
            adaptiveRadiusPixels = 4;
        }

        adaptiveRadiusPixels =
                Math.min(
                        motionChromaRadiusPixels + 8,
                        adaptiveRadiusPixels
                );

        int sampleStep =
                Math.max(
                        1,
                        Math.round(
                                adaptiveRadiusPixels / 4.0f
                        )
                );

        int actualRadiusPixels = sampleStep * 4;

        boolean useSecondPass =
                motionIso >= 1800.0f
                        || lowConfidence >= 0.20f
                        || displayLiftBlend >= 0.30f;

        configurePass(
                0,
                sampleStep,
                strength,
                guideSigma
        );

        glProg.useAssetProgram(
                "denoise/motionchromadenoise"
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

        if (!useSecondPass) {
            WorkingTexture = basePipeline.main3;

            Log.d(
                    Name,
                    "MOTION_26272_HDR_SHADOW_ARTIFACT_REPAIR"
                            + " iso=" + motionIso
                            + " effectiveRatio=" + measuredRatio
                            + " lowConfidence=" + lowConfidence
                            + " strength=" + strength
                            + " sceneShadowLift=" + sceneShadowLift
                            + " displayGainEstimate=" + displayGainEstimate
                            + " displayLiftBlend=" + displayLiftBlend
                            + " visibleNoiseBlend=" + visibleNoiseBlend
                            + " radiusPixels=" + actualRadiusPixels
                            + " passes=1"
                            + " perLensChromaMaximum=" + perLensChromaMaximum
                            + " autoLensType=" + automaticLensProfile.lensType
                            + " autoEquivalentMm="
                            + automaticLensProfile.equivalentFocalLengthMm
                            + " perLensExtremeNightMaximum="
                            + perLensExtremeNightMaximum
                            + " brightProtection=0.42..0.76"
                            + " chromaEdgeProtection=0.018..0.105"
                            + " highlightColorfulnessPreservation=centerChroma"
                            + " detailPreserving=true"
            );

            return;
        }

        configurePass(
                1,
                sampleStep,
                strength,
                guideSigma
        );

        glProg.useAssetProgram(
                "denoise/motionchromadenoise"
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
                "MOTION_26272_HDR_SHADOW_ARTIFACT_REPAIR"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " guideSigma=" + guideSigma
                        + " passes=" + (useSecondPass ? 2 : 1)
                        + " kernelRadiusSamples=4"
                        + " sampleStepPixels=" + sampleStep
                        + " requestedRadiusPixels="
                        + motionChromaRadiusPixels
                        + " actualRadiusPixels="
                        + actualRadiusPixels
                        + " actualDiameterPixels="
                        + actualRadiusPixels * 2
                        + " centerChromaSimilarityUsed=false"
                        + " sampleSaturationProtected=true"
                        + " brightProtection=0.42..0.76"
                        + " chromaEdgeProtection=0.018..0.105"
                        + " highlightColorfulnessPreservation=centerChroma"
                        + " deepestShadowNeutralityGuard="
                        + motionShadowNeutralization
                        + " representation=Y_RminusG_BminusG"
                        + " lumaPreserved=true"
                        + " noiseAwareFlatMask=true"
                        + " placement=afterAutoExposure"
        );
    }
}
