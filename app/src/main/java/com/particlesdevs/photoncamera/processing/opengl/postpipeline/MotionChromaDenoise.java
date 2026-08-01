package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
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
            defaultValue = 0.34f,
            step = 0.01f
    )
    float motionChromaCleanupMaximum = 0.34f;

    @Tunable(
            title = "Motion chroma radius",
            description = "Requested full-resolution chroma radius in pixels. Internally rounded to the nearest four-pixel step.",
            category = "Motion Noise Tuning",
            min = 4,
            max = 48,
            defaultValue = 16,
            step = 1
    )
    int motionChromaRadiusPixels = 16;

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

        float highIsoBlend =
                Math2.clamp(
                        (motionIso - 600.0f) / 2600.0f,
                        0.0f,
                        1.0f
                );

        float strength =
                motionChromaCleanupMaximum
                        * highIsoBlend;

        if (strength <= 0.001f) {
            Log.d(
                    Name,
                    "MOTION_26171_CHROMA_TUNABLE"
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
                        0.040f,
                        motionChromaGuideSigmaMaximum,
                        highIsoBlend
                );

        int sampleStep =
                Math.max(
                        1,
                        Math.round(
                                motionChromaRadiusPixels
                                        / 4.0f
                        )
                );

        int actualRadiusPixels =
                sampleStep * 4;

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
                "MOTION_26171_CHROMA_TUNABLE"
                        + " iso=" + motionIso
                        + " enabled=true"
                        + " highIsoBlend=" + highIsoBlend
                        + " strength=" + strength
                        + " guideSigma=" + guideSigma
                        + " passes=2"
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
                        + " deepestShadowNeutralityGuard="
                        + motionShadowNeutralization
                        + " representation=Y_RminusG_BminusG"
                        + " lumaPreserved=true"
                        + " noiseAwareFlatMask=true"
                        + " placement=afterLumaBeforeAutoExposure"
        );
    }
}
