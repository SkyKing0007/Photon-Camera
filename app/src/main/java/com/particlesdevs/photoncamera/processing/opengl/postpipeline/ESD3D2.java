package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
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
    float chromaStrength = 1.0f;

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
    float motionLumaEdgeBlendMaximum = 0.05f;

    @Tunable(
            title = "Motion ESD stable-weight blend",
            description = "Maximum high-ISO blend toward dense bilateral weights. High values can make foliage and grass mushy.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 0.65f,
            defaultValue = 0.10f,
            step = 0.01f
    )
    float motionStableWeightBlendMaximum = 0.10f;

    @Tunable(
            title = "Motion ESD shadow boost maximum",
            description = "Maximum ESD shadow-noise tolerance reached at ISO 3200.",
            category = "Motion Noise Tuning",
            min = 0.50f,
            max = 1.20f,
            defaultValue = 0.55f,
            step = 0.01f
    )
    float motionShadowBoostMaximum = 0.55f;

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
            NoiseS /= scale;
            NoiseO /= scale;
            Log.d(Name, "NoiseS:" + NoiseS + ", NoiseO:" + NoiseO);
            glProg.setDefine("NOISES", NoiseS);
            glProg.setDefine("NOISEO", NoiseO);
            float appliedShadowBoost =
                    shadowBoost;

            float motionNoiseBlend =
                    0.0f;

            float motionStableWeights =
                    0.0f;

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

                motionStableWeights =
                        motionStableWeightBlendMaximum
                                * highIsoBlend;

                appliedShadowBoost =
                        Math.max(
                                shadowBoost,
                                Math2.mix(
                                        shadowBoost,
                                        motionShadowBoostMaximum,
                                        highIsoBlend
                                )
                        );

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

            float appliedLuma =
                    Math2.mix(
                            luma,
                            luma * 0.72f,
                            indoorHdrStrength
                    );

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
                            (float) kernelSize * 0.78f,
                            indoorHdrStrength
                    );

            int msize =
                    Math.min(
                            minSize
                                    + (int) kernelSize
                                    - (int) kernelSize % 2,
                            maxSize
                    );

            Log.d(
                    "ESD3D",
                    "MOTION_26179_INDOOR_HDR_DETAIL"
                            + " kernelSize=" + kernelSize
                            + " MSIZE=" + msize
                            + " indoorHdrStrength="
                            + indoorHdrStrength
                            + " lumaConfigured=" + luma
                            + " lumaApplied=" + appliedLuma
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
        float N = (float) Math.sqrt(0.5 * basePipeline.noiseS + basePipeline.noiseO);
        float targetN = noiseTarget;
        float scaleF = Math2.clamp(N/targetN, 1.0f, 4.0f);
        int scale = (int)(scaleF + 0.5f);
        GLTexture outp;
        Log.d(Name, "Scaling factor:" + scale);
        if(!useColorDenoising){
            outp = previousNode.WorkingTexture;
        } else {
            if (scale != 1) {
                basePipeline.main4 = glUtils.gaussdown(previousNode.WorkingTexture, scale);
                WorkingTexture = basePipeline.getMain();
                ESD3DRun(basePipeline.main4, WorkingTexture, 0.0f, scaleF * 0.75f);
                outp = basePipeline.getMain();
                guidedUpsample(WorkingTexture, basePipeline.main4, previousNode.WorkingTexture, outp, scale);
            } else {
                WorkingTexture = basePipeline.getMain();
                ESD3DRun(previousNode.WorkingTexture, WorkingTexture, 0.0f, 1.0f);
                outp = basePipeline.getMain();
                guidedUpsample(WorkingTexture, previousNode.WorkingTexture, previousNode.WorkingTexture, outp, scale);
            }
        }
        WorkingTexture = basePipeline.getMain();
        ESD3DRun(outp, WorkingTexture, moire, 1.0f);
        glProg.closed = true;
        if(basePipeline.main4 != null){
            basePipeline.main4.close();
            basePipeline.main4 = null;
        }
    }
}
