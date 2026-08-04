package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.MotionLensNoiseProfile;
import com.particlesdevs.photoncamera.processing.render.NoiseModeler;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Math2;

import org.w3c.dom.Text;

public class ESD3D2 extends Node {
    @Tunable(
            title = "Chroma Strength",
            category = "Denoise",
            defaultValue = 1.0f,
            min = 0.0f,
            max = 1.0f,
            step = 0.05f,
            description = "Chroma denoise strength. Lower preserves more color (try 0.3-0.7)"
    )
    float chromaStrength = 0.78f;

    @Tunable(
            title = "Shadow Boost",
            category = "Denoise",
            defaultValue = 0.5f,
            min = 0.0f,
            max = 2.0f,
            step = 0.01f,
            description = "Boost denoising in deep shadows to prevent noise amplification after tonemap"
    )
    float shadowBoost = 0.5f;

    @Tunable(
            title = "Motion ESD luma-edge blend",
            description = "Maximum high-ISO use of luma instead of RGB for ESD edge detection. Lower preserves colored fine detail.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.30f,
            defaultValue = 0.05f,
            step = 0.01f
    )
    float motionLumaEdgeBlendMaximum = 0.02f;

    @Tunable(
            title = "Motion ESD stable-weight blend",
            description = "Maximum high-ISO blend toward dense bilateral weights. High values can make foliage and grass mushy.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.65f,
            defaultValue = 0.04f,
            step = 0.01f
    )
    /*
     * Build 26261:
     * Restore a small high-ISO stable-weight contribution. Zero left
     * connected luma/chroma residuals as worm-like patterns; 0.08 is
     * intentionally far below the earlier softness-producing range.
     */
    float motionStableWeightBlendMaximum = 0.12f;

    @Tunable(
            title = "Motion ESD shadow boost maximum",
            description = "Maximum ESD shadow-noise tolerance reached at ISO 3200.",
            category = "Motion Noise Tuning",
            min = 0.50f,
            max = 1.20f,
            defaultValue = 0.55f,
            step = 0.01f
    )
    float motionShadowBoostMaximum = 0.52f;

    boolean needClose = false;
    public ESD3D2(boolean closing) {
        super("", "ES3D");
        needClose = closing;
    }

    @Override
    public void Compile() {
    }
    @Tunable(title = "Enable", category = "Denoise", defaultValue = 1, min = 0, max = 1, step = 1, description = "Enable ESD3D Denoising")
    boolean enable;

    @Tunable(title = "Noise To Kernel Size", category = "Denoise", max = 50.0f, defaultValue = 24.0f)
    float noiseToKernelSize = 24.0f;

    @Tunable(title = "Noise Target", category = "Denoise", max = 0.1f, defaultValue = 0.00390625f, step = 0.0001f,
            description = "Target noise level to map to minimum kernel size (1/256 = 0.00390625)"
    )
    float noiseTarget = 1.0f/256.f;

    @Tunable(title = "Luma", category = "Denoise", max = 2.0f, defaultValue = 0.8f,
            description = "Luma strength multiplier for denoising"
    )
    float luma = 0.8f;

    @Tunable(title = "Max Kernel", category = "Denoise", min = 1.0f, max = 51.0f, defaultValue = 21.0f, step = 1.0f,
            description = "Maximum kernel size for denoising"
    )
    int maxSize = 21;

    @Tunable(title = "Min Kernel", category = "Denoise", min = 1.0f, max = 21.0f, defaultValue = 7.0f, step = 1.0f,
            description = "Minimum kernel size for denoising"
    )
    int minSize = 7;

    @Tunable(title = "Moire Reduction", category = "Denoise", max = 5.0f, defaultValue = 1.5f, step = 0.1f,
            description = "Moire reduction strength"
    )
    float moire = 1.5f;

    @Tunable(title = "Use Color Denoising", category = "Denoise", defaultValue = 1, min = 0, max = 1, step = 1,
            description = "Whether to apply subsampling denoising to color channels (in addition to luma)"
    )
    boolean useColorDenoising;

    void ESD3DRun(GLTexture inputTexture, GLTexture outputTexture, float moire, float scale) {
        {
            float NoiseS = basePipeline.noiseS;
            float NoiseO = basePipeline.noiseO;
            float motionDisplayGainEstimate = 1.0f;
            float motionVisibleNoiseVarianceScale = 1.0f;
            float motionEffectiveWeakness = 0.0f;

            if (com.particlesdevs.photoncamera.app.PhotonCamera.getSettings().selectedMode
                    == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
                float sceneShadowLift = Math2.clamp(
                        ((PostPipeline) basePipeline).motionShadowSceneStrength,
                        0.0f,
                        1.0f);
                float measuredRatio = basePipeline.mParameters.localContributionMeasured
                        ? Math2.clamp(basePipeline.mParameters.effectiveStackRatio, 0.0f, 1.0f)
                        : 1.0f;
                float lowerPercentileRatio = basePipeline.mParameters.localContributionMeasured
                        ? Math2.clamp(basePipeline.mParameters.localContributionP25, 0.0f, 1.0f)
                        : measuredRatio;
                float mixedStackSupport = Math2.clamp(0.65f * measuredRatio + 0.35f * lowerPercentileRatio, 0.0f, 1.0f);
                motionEffectiveWeakness = 1.0f - mixedStackSupport;
                float lowIsoLiftPotential = 1.0f - Math2.smoothstep(500.0f, 2200.0f, basePipeline.mParameters.iso);
                motionDisplayGainEstimate = 1.0f + 1.55f * Math.max(sceneShadowLift, 0.45f * lowIsoLiftPotential);
                float visibleAmplitudeScale = motionDisplayGainEstimate
                        * (1.0f + 0.40f * motionEffectiveWeakness);
                motionVisibleNoiseVarianceScale = Math2.clamp(
                        visibleAmplitudeScale * visibleAmplitudeScale,
                        1.0f,
                        4.25f);
                NoiseS *= motionVisibleNoiseVarianceScale;
                NoiseO *= motionVisibleNoiseVarianceScale;
            }

            NoiseS /= scale;
            NoiseO /= scale;
            Log.d(Name, "MOTION_26269_VISIBLE_NOISE_MODEL"
                    + " capturedIso=" + basePipeline.mParameters.iso
                    + " physicalNoiseS=" + basePipeline.noiseS
                    + " physicalNoiseO=" + basePipeline.noiseO
                    + " displayGainEstimate=" + motionDisplayGainEstimate
                    + " effectiveWeakness=" + motionEffectiveWeakness
                    + " visibleVarianceScale=" + motionVisibleNoiseVarianceScale
                    + " modeledNoiseS=" + NoiseS
                    + " modeledNoiseO=" + NoiseO
                    + " exifIsoNotUsed=true");
            glProg.setDefine("NOISES", NoiseS);
            glProg.setDefine("NOISEO", NoiseO);
            float appliedShadowBoost =
                    shadowBoost;

            float motionNoiseBlend =
                    0.0f;

            float motionStableWeights =
                    0.0f;

            float storedLuma =
                    PreferenceKeys.getFloat(
                            PreferenceKeys.Key.KEY_MOTION_LUMA_STRENGTH
                    );
            float storedChroma =
                    PreferenceKeys.getFloat(
                            PreferenceKeys.Key.KEY_MOTION_CHROMA_STRENGTH
                    );
            float storedTexture =
                    PreferenceKeys.getFloat(
                            PreferenceKeys.Key.KEY_MOTION_TEXTURE_PRESERVATION
                    );
            float storedSpatial =
                    PreferenceKeys.getFloat(
                            PreferenceKeys.Key.KEY_MOTION_SPATIAL_DENOISE
                    );
            float storedShadow =
                    PreferenceKeys.getFloat(
                            PreferenceKeys.Key.KEY_MOTION_SHADOW_CLEANUP
                    );

            MotionLensNoiseProfile.Resolved automaticLensProfile =
                    MotionLensNoiseProfile.resolve(
                            storedLuma,
                            storedChroma,
                            storedTexture,
                            storedSpatial,
                            storedShadow
                    );

            if (com.particlesdevs.photoncamera.app.PhotonCamera
                    .getSettings().selectedMode
                    == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

                float motionIso =
                        Math.max(
                                1.0f,
                                basePipeline.mParameters.iso
                        );

                float highIsoBlend =
                        Math2.clamp(
                                (motionIso - 400.0f) / 2800.0f,
                                0.0f,
                                1.0f
                        );

                /*
                 * Build 26169:
                 * Keep ESD3D2 primarily RGB-edge aware. The dedicated
                 * MotionChromaDenoise node handles broad chroma blotches
                 * without widening the luma-detail filter globally.
                 */
                /*
                 * Build 26170:
                 * Stable bilateral weights suppress connected noise worms
                 * without restoring the broad luma softness from 26168.
                 */
                motionNoiseBlend =
                        motionLumaEdgeBlendMaximum
                                * highIsoBlend;

                /*
                 * Build 26289:
                 * Sparse SNN weights can connect residual noise into worms.
                 * Retain the established high-ISO base blend, then add only a
                 * confidence-derived stable-weight contribution when measured
                 * temporal support is weak. Strong stacks remain unchanged.
                 */
                /*
                 * Build 26295: sparse-SNN anti-worm baseline for healthy and
                 * weak Motion stacks alike.
                 * MOTION_26295_ESD_HEALTHY_STACK_ANTI_WORM
                 */
                motionStableWeights =
                        Math2.clamp(
                                0.08f
                                        + motionStableWeightBlendMaximum * highIsoBlend
                                        + 0.16f * motionEffectiveWeakness,
                                0.0f,
                                0.28f
                        );

                /*
                 * Build 26222:
                 * Keep the established base ESD luma strength at 0.8.
                 * Reduce only Motion luma shadow expansion at low/moderate
                 * ISO, then smoothly restore established high-ISO protection.
                 */
                float lowIsoMotionShadowBoost = 0.15f;

                float perLensShadowCleanup =
                        Math2.clamp(
                                automaticLensProfile.shadow,
                                0.50f,
                                1.50f
                        );

                appliedShadowBoost =
                        Math2.mix(
                                lowIsoMotionShadowBoost,
                                Math.max(
                                        shadowBoost,
                                        motionShadowBoostMaximum
                                ),
                                highIsoBlend
                        ) * perLensShadowCleanup;

                Log.d(
                        Name,
                        "MOTION_26171_ESD3D2_TUNABLE"
                                + " iso=" + motionIso
                                + " scale=" + scale
                                + " NoiseS=" + NoiseS
                                + " NoiseO=" + NoiseO
                                + " chromaStrength="
                                + chromaStrength
                                + " shadowBoostConfigured="
                                + shadowBoost
                                + " shadowBoostApplied="
                                + appliedShadowBoost
                                + " motionNoiseBlend="
                                + motionNoiseBlend
                                + " motionNoiseBlendMaximum="
                                + motionLumaEdgeBlendMaximum
                                + " stableWeightBlend="
                                + motionStableWeights
                                + " stableWeightBlendMaximum="
                                + motionStableWeightBlendMaximum
                                + " motionShadowBoostMaximum="
                                + motionShadowBoostMaximum
                                + " chromaMinimumIndependent=true"
                                + " edgeMetric="
                                + "rgbDominant"
                                + " dedicatedLumaStage=true"
                                + " dedicatedCoarseChromaStage=true"
                                + " readNoiseSource=NOISEO"
                );
            }

            float indoorHdrStrength =
                    ((PostPipeline) basePipeline)
                            .indoorHdrSceneStrength;

            /*
             * Build 26230:
             * Use immutable capture identity rather than the live UI mode.
             */
            boolean motionNoiseProfile =
                    basePipeline.mParameters.motionCapture;

            float configuredLuma =
                    motionNoiseProfile
                            ? Math2.clamp(
                                automaticLensProfile.luma,
                                0.40f,
                                1.00f
                            )
                            : luma;

            float appliedLuma =
                    Math2.mix(
                            configuredLuma,
                            Math.min(
                                    1.10f,
                                    configuredLuma * 1.12f
                            ),
                            indoorHdrStrength
                    );

            float texturePreservation =
                    motionNoiseProfile
                            ? Math2.clamp(
                                automaticLensProfile.texture,
                                0.50f,
                                2.00f
                            )
                            : 1.00f;

            /*
             * Build 26230:
             * Do not increase texture preservation globally. The global stack
             * measurements only authorize a small spatially local edge gate in
             * esd3d2.glsl. Flat/noisy regions keep the exact 26227/26229 ESD
             * settings.
             */
            float lowLightScene =
                    motionNoiseProfile
                            ? Math2.clamp(
                                (
                                        basePipeline.mParameters.iso
                                                - 1600.0f
                                ) / 3200.0f,
                                0.0f,
                                1.0f
                            )
                            : 0.0f;

            float effectiveRatioConfidence =
                    motionNoiseProfile
                                    && basePipeline.mParameters
                                            .localContributionMeasured
                            ? Math2.clamp(
                                (
                                        basePipeline.mParameters
                                                .effectiveStackRatio
                                                - 0.50f
                                ) / 0.30f,
                                0.0f,
                                1.0f
                            )
                            : 0.0f;

            float lowerPercentileConfidence =
                    motionNoiseProfile
                                    && basePipeline.mParameters
                                            .localContributionMeasured
                            ? Math2.clamp(
                                (
                                        basePipeline.mParameters
                                                .localContributionP25
                                                - 0.40f
                                ) / 0.30f,
                                0.0f,
                                1.0f
                            )
                            : 0.0f;

            /*
             * Build 26246:
             * Real low-contrast fabric, foliage, fur and bark can have weak
             * contribution-map confidence even when local structure is valid.
             * Keep the shader's local edge/noise test as the primary gate.
             * Contribution confidence now adds protection instead of being a
             * hard requirement. Taper the baseline in extreme low light so
             * flat dark noise still receives strong cleanup.
             */
            float contributionConfidence =
                    Math.min(
                            effectiveRatioConfidence,
                            lowerPercentileConfidence
                    );

            float localStructureBaseline =
                    Math2.mix(
                            0.55f,
                            0.28f,
                            lowLightScene
                    );

            float sceneShadowLiftForTexture =
                    motionNoiseProfile
                            ? Math2.clamp(
                                    ((PostPipeline) basePipeline).motionShadowSceneStrength,
                                    0.0f,
                                    1.0f)
                            : 0.0f;

            float temporalEdgeAuthorization =
                    Math2.clamp(
                            localStructureBaseline
                                    + 0.30f * contributionConfidence
                                    - 0.20f * sceneShadowLiftForTexture
                                            * (1.0f - contributionConfidence),
                            0.0f,
                            0.85f
                    );

            glProg.setDefine(
                    "MOTIONLOWLIGHTSCENE",
                    lowLightScene
            );
            glProg.setDefine(
                    "MOTIONEDGECONFIDENCE",
                    temporalEdgeAuthorization
            );

            Log.w(
                    Name,
                    "MOTION_26232_EDGE_TEXTURE"
                            + " enabled=" + motionNoiseProfile
                            + " immutableMotionCapture="
                            + basePipeline.mParameters.motionCapture
                            + " measured="
                            + basePipeline.mParameters
                                    .localContributionMeasured
                            + " iso="
                            + basePipeline.mParameters.iso
                            + " retainedFrames="
                            + basePipeline.mParameters
                                    .retainedFrameCount
                            + " effectiveFrames="
                            + basePipeline.mParameters
                                    .effectiveFrameCount
                            + " effectiveRatio="
                            + basePipeline.mParameters
                                    .effectiveStackRatio
                            + " contributionP25="
                            + basePipeline.mParameters
                                    .localContributionP25
                            + " lowLightScene="
                            + lowLightScene
                            + " edgeAuthorization="
                            + temporalEdgeAuthorization
                            + " maxLocalSmoothingReduction=0.30"
                            + " brightSceneTextureAllowance=1.00"
                            + " extremeLowLightTextureAllowance=0.45"
                            + " shadowBoostExcludedFromTextureThreshold=true"
                            + " pictureDrivenClosetTexture=true"
                            + " fixedIsoRangeUsed=false"
                            + " directionalNoiseMultiplier=0.90"
                            + " directionalFloor=0.0075"
                            + " directionalActivation=0.22"
                            + " globalTextureBoost=0"
                            + " sharpeningChanged=true"
                            + " hdrShadowDenoisePreserved=true"
                            + " connectedWormSuppression=true"
            );

            glProg.setDefine("TEXTUREPRESERVATION", texturePreservation);
            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", appliedLuma);
            glProg.setDefine("CHROMASTRENGTH", chromaStrength);
            glProg.setDefine(
                    "SHADOWBOOST",
                    appliedShadowBoost
            );
            glProg.setDefine(
                    "MOTIONNOISEBLEND",
                    motionNoiseBlend
            );
            glProg.setDefine(
                    "MOTIONSTABLEWEIGHTS",
                    motionStableWeights
            );

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
            //float ks = 1.0f + Math.min((basePipeline.noiseS+basePipeline.noiseO) * 3.0f * noiseToKernelSize, 34.f);
            //int msize = 7 + (int)ks - (int)ks%2;
            double noiseMpy = Math.max((NoiseS+NoiseO)/noiseTarget, 0.0000001);
            double kernelSize =
                    1.0f
                            + Math.sqrt(noiseMpy)
                            * noiseToKernelSize;

            kernelSize =
                    Math2.mix(
                            (float) kernelSize,
                            (float) kernelSize * 1.18f,
                            indoorHdrStrength
                    );

            float spatialDenoiseStrength =
                    motionNoiseProfile
                            ? Math2.clamp(
                                automaticLensProfile.spatial,
                                0.50f,
                                1.50f
                            )
                            : 1.00f;

            kernelSize *= spatialDenoiseStrength;

            int msize;
            boolean motionMode =
                    com.particlesdevs.photoncamera.app.PhotonCamera
                            .getSettings().selectedMode
                            == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

            float motionIso =
                    motionMode
                            ? Math.max(
                                    1.0f,
                                    basePipeline.mParameters.iso
                            )
                            : 0.0f;

            int appliedMinSize =
                    motionMode
                            ? (
                                motionIso < 800.0f
                                        ? 3
                                        : (
                                            motionIso < 1600.0f
                                                    ? 5
                                                    : 7
                                        )
                            )
                            : minSize;

            int appliedMaxSize =
                    motionMode
                            ? (
                                motionIso < 800.0f
                                        ? 7
                                        : (
                                            motionIso < 1600.0f
                                                    ? 13
                                                    : (
                                                        motionIso < 3200.0f
                                                                ? 17
                                                                : maxSize
                                                    )
                                        )
                            )
                            : maxSize;

            msize =
                    Math.min(
                            appliedMinSize
                                    + (int) kernelSize
                                    - (int) kernelSize % 2,
                            appliedMaxSize
                    );

            Log.d(
                    "ESD3D",
                    "MOTION_26221_ESD_DETAIL"
                            + " kernelSize=" + kernelSize
                            + " MSIZE=" + msize
                            + " appliedMinSize=" + appliedMinSize
                            + " appliedMaxSize=" + appliedMaxSize
                            + " motionMode=" + motionMode
                            + " motionIso=" + motionIso
                            + " indoorHdrStrength="
                            + indoorHdrStrength
                            + " lumaConfigured=" + luma
                            + " lumaApplied=" + appliedLuma
                            + " lowIsoShadowBoost=0.15"
                            + " shadowBoostApplied=" + appliedShadowBoost
                            + " nightHighIsoProtectionRetained=true"
                            + " textureLumaModerateFactor=0.84"
                            + " textureLumaStrongFactor=0.74"
                            + " flatLumaUnchanged=true"
                            + " perLensLuma=" + configuredLuma
                            + " perLensTexturePreservation=" + texturePreservation
                            + " perLensSpatialDenoise=" + spatialDenoiseStrength
                            + " perLensShadowCleanup="
                            + (
                                motionNoiseProfile
                                        ? automaticLensProfile.shadow
                                        : 1.0f
                            )
                            + " autoLensType="
                            + (
                                motionNoiseProfile
                                        ? automaticLensProfile.lensType
                                        : MotionLensNoiseProfile.LensType.STANDARD
                            )
                            + " autoEquivalentMm="
                            + (
                                motionNoiseProfile
                                        ? automaticLensProfile.equivalentFocalLengthMm
                                        : Float.NaN
                            )
                            + " chromaIndependent=true"
                            + " nightModeAffected=false"
            );
            glProg.setDefine("KERNELSIZE", (float)(kernelSize));
            glProg.setDefine("MSIZE", msize);
            glProg.useAssetProgram("denoise/esd3d2");
            //glProg.setTexture("NoiseMap", basePipeline.main4);
            glProg.setTexture("InputBuffer", inputTexture);
            //glProg.setTexture("GradBuffer", grad);
            glProg.drawBlocks(outputTexture);
        }
    }
    public void guidedUpsample(GLTexture lowresInput, GLTexture guide, GLTexture guideHigh, GLTexture output, int scaling) {
        //glProg.setDefine("USE_GUIDE_BRIGHTNESS", useGuideBrightness);
        glProg.setDefine("SCALE", scaling);
        glProg.useAssetProgram("denoise/guidedupsample", false);
        glProg.setTexture("LowresInput", lowresInput);
        glProg.setTexture("Guide", guide);
        glProg.setTexture("GuideHigh", guideHigh);
        glProg.setVar("noiseS", basePipeline.noiseS);
        glProg.setVar("noiseO", basePipeline.noiseO);
        glProg.drawBlocks(output, output.mSize);
        glProg.closed = true;
    }

    @Override
    public void Run() {
        if (!enable) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }

        boolean motionMode =
                com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

        float N =
                (float) Math.sqrt(
                        0.5 * basePipeline.noiseS
                                + basePipeline.noiseO
                );

        float targetN = noiseTarget;
        float scaleF;

        if (motionMode) {
            /*
             * Build 26221:
             * PostPipeline forces noiseO to at least 1/4096. The old N/targetN
             * formula therefore forced scale 4 even at moderate ISO.
             * Remove that known floor before mapping excess noise to scale.
             */
            float forcedReadNoiseFloor =
                    (float) Math.sqrt(1.0f / 4096.0f);

            float excessNoise =
                    Math.max(
                            0.0f,
                            N - forcedReadNoiseFloor
                    );

            scaleF =
                    Math2.clamp(
                            1.0f + excessNoise / targetN,
                            1.0f,
                            4.0f
                    );
        } else {
            scaleF =
                    Math2.clamp(
                            N / targetN,
                            1.0f,
                            4.0f
                    );
        }

        int scale = (int) (scaleF + 0.5f);

        Log.d(
                Name,
                "MOTION_26221_ESD_SCALE"
                        + " motionMode=" + motionMode
                        + " N=" + N
                        + " targetN=" + targetN
                        + " scaleF=" + scaleF
                        + " scale=" + scale
                        + " singlePassMotion=true"
        );

        if (motionMode) {
            /*
             * Motion receives exactly one ESD pass.
             *
             * scale 1: one full-resolution pass.
             * scale 2-4: one low-resolution pass followed by guided upsample.
             * Do not denoise the reconstructed full-resolution image again.
             */
            if (!useColorDenoising || scale == 1) {
                WorkingTexture = basePipeline.getMain();
                ESD3DRun(
                        previousNode.WorkingTexture,
                        WorkingTexture,
                        moire,
                        1.0f
                );
            } else {
                basePipeline.main4 =
                        glUtils.gaussdown(
                                previousNode.WorkingTexture,
                                scale
                        );

                GLTexture lowDenoised = basePipeline.getMain();

                ESD3DRun(
                        basePipeline.main4,
                        lowDenoised,
                        moire,
                        scaleF * 0.75f
                );

                WorkingTexture = basePipeline.getMain();

                guidedUpsample(
                        lowDenoised,
                        basePipeline.main4,
                        previousNode.WorkingTexture,
                        WorkingTexture,
                        scale
                );
            }
        } else {
            /*
             * Preserve established behavior for all non-Motion modes.
             */
            GLTexture outp;

            if (!useColorDenoising) {
                outp = previousNode.WorkingTexture;
            } else {
                if (scale != 1) {
                    basePipeline.main4 =
                            glUtils.gaussdown(
                                    previousNode.WorkingTexture,
                                    scale
                            );

                    WorkingTexture = basePipeline.getMain();

                    ESD3DRun(
                            basePipeline.main4,
                            WorkingTexture,
                            0.0f,
                            scaleF * 0.75f
                    );

                    outp = basePipeline.getMain();

                    guidedUpsample(
                            WorkingTexture,
                            basePipeline.main4,
                            previousNode.WorkingTexture,
                            outp,
                            scale
                    );
                } else {
                    WorkingTexture = basePipeline.getMain();

                    ESD3DRun(
                            previousNode.WorkingTexture,
                            WorkingTexture,
                            0.0f,
                            1.0f
                    );

                    outp = basePipeline.getMain();

                    guidedUpsample(
                            WorkingTexture,
                            previousNode.WorkingTexture,
                            previousNode.WorkingTexture,
                            outp,
                            scale
                    );
                }
            }

            WorkingTexture = basePipeline.getMain();
            ESD3DRun(outp, WorkingTexture, moire, 1.0f);
        }

        glProg.closed = true;

        if (basePipeline.main4 != null) {
            basePipeline.main4.close();
            basePipeline.main4 = null;
        }
    }
}
