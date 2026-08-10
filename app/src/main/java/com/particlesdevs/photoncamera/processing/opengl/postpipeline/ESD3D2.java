package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.MotionMetrics;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.util.BufferUtils;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.NoiseModeler;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Math2;

import org.w3c.dom.Text;

public class ESD3D2 extends Node {
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

            if (com.particlesdevs.photoncamera.app.PhotonCamera
                    .getSettings().selectedMode
                    == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
                // IRIS_26371_ESD3D2_DIAGNOSTIC_COMPILE_REPAIR
                String iris26370EsdDetails =
                        "noiseS=" + NoiseS
                                + " noiseO=" + NoiseO
                                + " scale=" + scale
                                + " luma=" + luma
                                + " moire=" + moire
                                + " useColorDenoising=" + useColorDenoising
                                + " noiseTarget=" + noiseTarget
                                + " noiseToKernelSize=" + noiseToKernelSize
                                + " minSize=" + minSize
                                + " maxSize=" + maxSize
                                + " iso="
                                + basePipeline.mParameters.iso
                                + " effectiveRatio="
                                + (com.particlesdevs.photoncamera.processing
                                        .MotionMetrics.isActive()
                                        ? com.particlesdevs.photoncamera
                                                .processing.MotionMetrics
                                                .effectiveStackRatio()
                                        : 1.0f)
                                + " diagnosticOnly26370=true";

                Log.i(
                        Name,
                        "IRIS_26370_ESD3D2_DIAGNOSTIC "
                                + iris26370EsdDetails);

                try {
                    com.particlesdevs.photoncamera.util.MotionTrace
                            .processingState(
                                    "ESD3D2_DIAGNOSTIC_26370",
                                    iris26370EsdDetails);
                } catch (Throwable iris26370TraceFailure) {
                    Log.e(
                            Name,
                            "26370 ESD trace failed: "
                                    + iris26370TraceFailure
                                            .getClass()
                                            .getSimpleName());
                }
            }
            final boolean iris26372Motion =
                    com.particlesdevs.photoncamera.app.PhotonCamera
                            .getSettings().selectedMode
                            == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

            float iris26372EffectiveRatio = 1.0f;
            if (iris26372Motion
                    && com.particlesdevs.photoncamera.processing
                            .MotionMetrics.isActive()) {
                iris26372EffectiveRatio =
                        com.particlesdevs.photoncamera.processing
                                .MotionMetrics.effectiveStackRatio();
            }

            /*
             * IRIS_26372_TEMPORAL_STACK_AWARE_LUMA
             *
             * Strong Motion temporal stacks have already averaged random
             * luma noise. Reduce final ESD luma replacement and spatial
             * support instead of repainting reference microtexture.
             *
             * The measured noiseS/noiseO model itself is left unchanged.
             */
            float iris26372StackQuality =
                    Math2.clamp(
                            (iris26372EffectiveRatio - 0.50f) / 0.50f,
                            0.0f,
                            1.0f);

            float iris26372AppliedLuma = luma;
            int iris26372MaxSize = maxSize;
            double iris26372KernelSigmaCap = Double.MAX_VALUE;

            if (iris26372Motion) {
                iris26372AppliedLuma =
                        Math2.mix(0.65f, 0.40f, iris26372StackQuality);
                if (com.particlesdevs.photoncamera.settings.MotionIqLab.active()) {
                    iris26372AppliedLuma *= Math2.clamp(
                            com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                    "esd_luma_scale", 1.0f),
                            0.0f, 2.0f);
                }

                if (iris26372StackQuality >= 0.80f) {
                    iris26372MaxSize = Math.min(maxSize, 13);
                } else if (iris26372StackQuality >= 0.40f) {
                    iris26372MaxSize = Math.min(maxSize, 15);
                } else {
                    iris26372MaxSize = Math.min(maxSize, 17);
                }

                iris26372KernelSigmaCap =
                        7.0 - 2.0 * iris26372StackQuality;
            }

            /*
             * IRIS_26373_SIGNAL_AWARE_RESIDUAL_NR
             *
             * Keep the 26372 global temporal-stack prior, but expose Motion
             * state and stack quality so the shader can decide luma/chroma
             * cleanup from actual local signal versus modeled residual noise.
             * ISO is not used as a hard denoise switch.
             */
            glProg.setDefine("NOISES", NoiseS);
            glProg.setDefine("NOISEO", NoiseO);
            glProg.setDefine("MOIRE", moire);
            glProg.setDefine("LUMA", iris26372AppliedLuma);
            glProg.setDefine("IRIS_MOTION_26373", iris26372Motion ? 1 : 0);
            glProg.setDefine(
                    "IRIS_STACK_QUALITY_26373",
                    iris26372StackQuality);

            glProg.setDefine("INSIZE", basePipeline.mParameters.rawSize);
            //float ks = 1.0f + Math.min((basePipeline.noiseS+basePipeline.noiseO) * 3.0f * noiseToKernelSize, 34.f);
            //int msize = 7 + (int)ks - (int)ks%2;
            double noiseMpy = Math.max((NoiseS+NoiseO)/noiseTarget, 0.0000001);
            double iris26372RawKernelSize =
                    1.0f + Math.sqrt(noiseMpy) * noiseToKernelSize;
            double kernelSize =
                    iris26372Motion
                            ? Math.min(
                                    iris26372RawKernelSize,
                                    iris26372KernelSigmaCap)
                            : iris26372RawKernelSize;
            int msize =
                    Math.min(
                            minSize + (int)kernelSize
                                    - (int)kernelSize%2,
                            iris26372MaxSize);

            if ((msize & 1) == 0) {
                msize = Math.max(minSize, msize - 1);
            }

            Log.d(
                    "ESD3D",
                    "KernelSize:" + kernelSize
                            + " RawKernelSize:" + iris26372RawKernelSize
                            + " MSIZE:" + msize
                            + " AppliedLuma:" + iris26372AppliedLuma
                            + " EffectiveRatio:" + iris26372EffectiveRatio
                            + " StackQuality:" + iris26372StackQuality
                            + " Motion:" + iris26372Motion);

            if (iris26372Motion) {
                String iris26372Details =
                        "effectiveRatio=" + iris26372EffectiveRatio
                                + " stackQuality=" + iris26372StackQuality
                                + " configuredLuma=" + luma
                                + " appliedLuma=" + iris26372AppliedLuma
                                + " rawKernel=" + iris26372RawKernelSize
                                + " appliedKernel=" + kernelSize
                                + " appliedMsize=" + msize
                                + " configuredMaxSize=" + maxSize
                                + " moire=" + moire
                                + " useColorDenoising=" + useColorDenoising
                                + " signalAware26373=true"
                                + " independentChroma26373=true"
                                + " protectedChromaMottle26374=true"
                                + " multiscaleChroma26375=true"
                                + " denimDetailProtected26375=true";

                Log.i(
                        Name,
                        "IRIS_26372_TEMPORAL_STACK_AWARE_LUMA "
                                + iris26372Details);

                try {
                    com.particlesdevs.photoncamera.util.MotionTrace
                            .processingState(
                                    "ESD3D2_DETAIL_RETENTION_26372",
                                    iris26372Details);
                } catch (Throwable iris26372TraceFailure) {
                    Log.e(
                            Name,
                            "26372 ESD detail trace failed: "
                                    + iris26372TraceFailure
                                            .getClass()
                                            .getSimpleName());
                }
            }

            glProg.setDefine("KERNELSIZE", (float)(kernelSize));
            glProg.setDefine("MSIZE", msize);
            GLTexture iris26383LocalSupportTexture = null;
            if (MotionMetrics.hasLocalSupportGrid()) {
                float[] iris26383SupportGrid = MotionMetrics.localSupportGridCopy();
                int iris26383SupportW = MotionMetrics.localSupportWidth();
                int iris26383SupportH = MotionMetrics.localSupportHeight();
                if (iris26383SupportGrid != null
                        && iris26383SupportW > 0
                        && iris26383SupportH > 0) {
                    iris26383LocalSupportTexture = new GLTexture(
                            new Point(iris26383SupportW, iris26383SupportH),
                            new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                            BufferUtils.getFrom(iris26383SupportGrid),
                            android.opengl.GLES20.GL_LINEAR,
                            android.opengl.GLES20.GL_CLAMP_TO_EDGE);
                    glProg.setDefine("IRIS_LOCAL_SUPPORT_26383", 1);
                    glProg.setDefine(
                            "IRIS_LOCAL_SUPPORT_RETAINED_26383",
                            (float)Math.max(1, MotionMetrics.retainedFrames()));
                }
            }

            glProg.useAssetProgram("denoise/esd3d2");
            //glProg.setTexture("NoiseMap", basePipeline.main4);
            glProg.setTexture("InputBuffer", inputTexture);
            if (iris26383LocalSupportTexture != null) {
                glProg.setTexture("MotionLocalSupportMap", iris26383LocalSupportTexture);
            }
            //glProg.setTexture("GradBuffer", grad);
            glProg.drawBlocks(outputTexture);
            if (iris26383LocalSupportTexture != null) {
                iris26383LocalSupportTexture.close();
            }
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
        /*
         * IRIS_26396_MOTION_RESIDUAL_CHROMA_OWNER
         *
         * Motion's signal-aware final ESD shader is the sole residual-chroma
         * authority. Do not let a persisted global tunable silently add/remove
         * the legacy broad color prepass. Photo/Night retain old behavior.
         */
        final boolean iris26396MotionResidualChromaOwner =
                com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;
        final boolean iris26396UseLegacyColorPrepass =
                !iris26396MotionResidualChromaOwner && useColorDenoising;

        if(!iris26396UseLegacyColorPrepass){
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
