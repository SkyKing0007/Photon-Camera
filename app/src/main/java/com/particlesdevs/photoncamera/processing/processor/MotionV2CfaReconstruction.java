package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.MotionMetrics;
import com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing;
import com.particlesdevs.photoncamera.processing.opengl.GLBuffer;
import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLOneScript;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_NEAREST;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26413_MOTION_V2_REFERENCE_PRESERVING_CFA
 * IRIS_26429_SHARED_GUIDE_ROBUSTNESS_REFERENCE_STRUCTURE
 *
 * Native-resolution deterministic same-exposure burst reconstruction.
 *
 * Invariant:
 *   output = currentReferenceEstimate + trusted auxiliary evidence
 * and local confidence -> 0 leaves the reference estimate unchanged.
 *
 * MotionV2Alignment owns the fractional displacement field.
 * Legacy PyramidAlignment/PyramidMerging/merge0/merge11 are not used by V2.
 */
/* IRIS_26474_DIRECT_WRONSKI_SUPPORT_MAP_AUTHORITY */
public final class MotionV2CfaReconstruction extends GLOneScript {
    /* IRIS_26487_CAMERA2_PER_CFA_NOISE_AUTHORITY */
    private static final float IRIS26487_CLIP_THRESHOLD = 250.0f / 255.0f;
    /* IRIS_26488_PHYSICAL_COLOR_CLIP_AUTHORITY: bjzhou RCD soft highlight reconstruction begins only at true near-saturation. */
    private static final float IRIS26488_HIGHLIGHT_CLIP_THRESHOLD = 0.985f;
    private static final float IRIS26488_HIGHLIGHT_CEILING = 8.0f;
    private static final class Iris26487Noise {
        final float[] shot = new float[4];
        final float[] read = new float[4];
    }
    private static int iris26487ColorForPhase(int cfaPattern,int phase){
        if(cfaPattern==0){if(phase==0)return 0;if(phase==3)return 2;return 1;}
        if(cfaPattern==1){if(phase==1)return 0;if(phase==2)return 2;return 1;}
        if(cfaPattern==2){if(phase==2)return 0;if(phase==1)return 2;return 1;}
        if(phase==3)return 0;if(phase==0)return 2;return 1;
    }
    private static Iris26487Noise iris26487FrameNoise(ImageFrame f,float fallbackS,float fallbackO){
        Iris26487Noise out=new Iris26487Noise();
        boolean valid=f!=null&&f.motionV2NoiseProfileValid&&f.motionV2NoiseProfile!=null&&f.motionV2NoiseProfile.length>=8;
        for(int phase=0;phase<4;phase++){
            float s=valid?f.motionV2NoiseProfile[2*phase]:fallbackS;
            float o=valid?f.motionV2NoiseProfile[2*phase+1]:fallbackO;
            out.shot[phase]=Math.max(Float.isFinite(s)?s:fallbackS,1.0e-9f);
            out.read[phase]=Math.max(Float.isFinite(o)?o:fallbackO,1.0e-12f);
        }
        return out;
    }
    /* For y = wb * exposure * x and Var(x)=S*x+O:
     * Var(y)=(wb*exposure*S)*y + (wb*exposure)^2*O.
     */
    /* Exact MGC noise-LUT coefficients in the WB/exposure calculation domain.
     * R/B each own one CFA phase. The LUT green channel is the variance of
     * 0.5*(Gr+Gb): 0.25*(Var(Gr)+Var(Gb)). Guide/covariance multiply this
     * LUT-green variance by 2 exactly as the recovered MGC shaders do.
     */
    private static float[] iris26487WbNoiseRgb(Iris26487Noise n,int cfaPattern,float exposure,float wbR,float wbB){
        float[] shot=new float[3],read=new float[3],count=new float[3];
        float e=Math.max(exposure,1.0e-6f);
        for(int phase=0;phase<4;phase++){
            int color=iris26487ColorForPhase(cfaPattern,phase);
            float wb=color==0?wbR:(color==2?wbB:1.0f);
            float g=e*Math.max(wb,1.0e-6f);
            shot[color]+=g*n.shot[phase];
            read[color]+=g*g*n.read[phase];
            count[color]+=1.0f;
        }
        for(int c=0;c<3;c++){
            if(c==1 && count[c]>=2.0f){shot[c]*=0.25f;read[c]*=0.25f;}
            else {float k=Math.max(count[c],1.0f);shot[c]/=k;read[c]/=k;}
        }
        return new float[]{shot[0],shot[1],shot[2],read[0],read[1],read[2]};
    }
    private static float[] iris26487GreenPhysicalNoise(Iris26487Noise n,int cfaPattern){
        float s=0.0f,o=0.0f,c=0.0f;
        for(int phase=0;phase<4;phase++)if(iris26487ColorForPhase(cfaPattern,phase)==1){s+=n.shot[phase];o+=n.read[phase];c+=1.0f;}
        if(c>=2.0f)return new float[]{0.25f*s,0.25f*o};
        return new float[]{s,o};
    }
    private static final String TAG = "MotionV2CfaRecon";

    /* IRIS_26488_V4_READBACK_FRAMEBUFFER_LIFETIME_OWNER
     * GLTexture.BufferLoad() allocates an OpenGL framebuffer, while the shared historical
     * GLTexture.close() path deletes mBuffer with glDeleteBuffers(). Do not modify shared GLTexture
     * in this Motion-only correction. Release MotionV2 readback framebuffers with the matching GLES
     * object API, reset the public ownership flags, then let GLTexture.close() delete only the texture.
     */
    private static void iris26488ReleaseReadbackFramebuffer(GLTexture texture) {
        if (texture == null || !texture.isBuffered || texture.mBuffer == 0) return;
        int framebuffer = texture.mBuffer;
        texture.mBuffer = 0;
        texture.isBuffered = false;
        try {
            android.opengl.GLES30.glDeleteFramebuffers(1, new int[]{framebuffer}, 0);
        } catch (Throwable cleanupError) {
            Log.w(TAG, "IRIS_26488_V4_FRAMEBUFFER_RELEASE_WARNING id=" + framebuffer, cleanupError);
        }
    }

    private static float[] iris26488ReadDiagnosticFloatRgba(GLTexture texture) {
        if (texture == null) throw new IllegalArgumentException("diagnostic texture is null");
        try {
            texture.BufferLoad();
            return iris26440CopyFloatBuffer(
                    texture.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_32, 4), true));
        } finally {
            iris26488ReleaseReadbackFramebuffer(texture);
        }
    }

    private static void iris26488CloseDiagnosticTexture(GLTexture texture) {
        if (texture == null) return;
        iris26488ReleaseReadbackFramebuffer(texture);
        try {
            texture.close();
        } catch (Throwable cleanupError) {
            Log.w(TAG, "IRIS_26488_V4_DIAGNOSTIC_TEXTURE_CLOSE_WARNING", cleanupError);
        }
    }

    /* IRIS_26501_PROPER_PER_FRAME_SPATIAL_RGB_FBO_OWNER
     * Two RGBA16F render targets survive the whole burst. Every admitted frame adds
     * semantic sums and their independent weights with GL_ONE/GL_ONE blending.
     * No accumulator is sampled while attached and no RGBA32F read/write image is used.
     */
    private static int iris26501CreateRgbAccumulatorFramebuffer(
            GLTexture semanticAccumulator, GLTexture opponentWeightAccumulator) {
        int[] ids = new int[1];
        android.opengl.GLES30.glGenFramebuffers(1, ids, 0);
        int framebuffer = ids[0];
        if (framebuffer == 0) {
            throw new IllegalStateException("26501 RGB accumulator framebuffer allocation failed");
        }
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, framebuffer);
        android.opengl.GLES30.glFramebufferTexture2D(
                android.opengl.GLES30.GL_FRAMEBUFFER, android.opengl.GLES30.GL_COLOR_ATTACHMENT0,
                android.opengl.GLES30.GL_TEXTURE_2D, semanticAccumulator.mTextureID, 0);
        android.opengl.GLES30.glFramebufferTexture2D(
                android.opengl.GLES30.GL_FRAMEBUFFER, android.opengl.GLES30.GL_COLOR_ATTACHMENT1,
                android.opengl.GLES30.GL_TEXTURE_2D, opponentWeightAccumulator.mTextureID, 0);
        android.opengl.GLES30.glDrawBuffers(
                2, new int[]{
                        android.opengl.GLES30.GL_COLOR_ATTACHMENT0,
                        android.opengl.GLES30.GL_COLOR_ATTACHMENT1}, 0);
        int status = android.opengl.GLES30.glCheckFramebufferStatus(android.opengl.GLES30.GL_FRAMEBUFFER);
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
        if (status != android.opengl.GLES30.GL_FRAMEBUFFER_COMPLETE) {
            android.opengl.GLES30.glDeleteFramebuffers(1, new int[]{framebuffer}, 0);
            throw new IllegalStateException(
                    "26501 RGB accumulator framebuffer incomplete status=0x"
                            + Integer.toHexString(status));
        }
        return framebuffer;
    }

    private static void iris26501ClearRgbAccumulators(int framebuffer, Point raw) {
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, framebuffer);
        android.opengl.GLES30.glViewport(0, 0, raw.x, raw.y);
        android.opengl.GLES30.glDisable(android.opengl.GLES30.GL_BLEND);
        android.opengl.GLES30.glClearBufferfv(
                android.opengl.GLES30.GL_COLOR, 0, new float[]{0f, 0f, 0f, 0f}, 0);
        android.opengl.GLES30.glClearBufferfv(
                android.opengl.GLES30.GL_COLOR, 1, new float[]{0f, 0f, 0f, 0f}, 0);
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
    }

    private static void iris26501RenderChromaGuide(
            GLProg glProg, Point raw, GLTexture rawTexture, GLTexture guideTexture,
            int cfaPattern, float[] blackLevel, float whiteLevel, float exposureScale,
            float wbR, float wbB) {
        glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_chroma_guide_26501");
        glProg.setVar("rawSize", raw);
        glProg.setVar("cfaPattern", cfaPattern);
        glProg.setVar("blackLevel", blackLevel);
        glProg.setVar("whiteLevel", whiteLevel);
        glProg.setVar("exposureScale", exposureScale);
        glProg.setVar("wbR", wbR);
        glProg.setVar("wbB", wbB);
        glProg.setTexture("rawTexture", rawTexture);
        android.opengl.GLES30.glDisable(android.opengl.GLES30.GL_BLEND);
        guideTexture.BufferLoad();
        glProg.drawBlocks(raw.x, raw.y);
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
    }

    private static void iris26501RenderRgbCovariance(
            GLProg glProg, Point raw, Point rawHalf, Point guideSize,
            GLTexture rawTexture, GLTexture covarianceTexture,
            int cfaPattern, float[] blackLevel, float whiteLevel, float exposureScale,
            float wbR, float wbB, float greenNoiseS, float greenNoiseO) {
        glProg.setLayout(8, 8, 1);
        glProg.useAssetProgram("motionv2/mfsr_mgc_covariance", true);
        glProg.setVar("rawSize", raw);
        glProg.setVar("rawHalf", rawHalf);
        glProg.setVar("guideSize", guideSize);
        glProg.setVar("noiseS", greenNoiseS);
        glProg.setVar("noiseO", greenNoiseO);
        glProg.setVar("cfaPattern", cfaPattern);
        glProg.setVar("blackLevel", blackLevel);
        glProg.setVar("whiteLevel", whiteLevel);
        glProg.setVar("exposureScale", exposureScale);
        glProg.setVar("wbR", wbR);
        glProg.setVar("wbB", wbB);
        glProg.setTexture("rawTexture", rawTexture);
        glProg.setTextureCompute("outputCov", covarianceTexture, true);
        glProg.computeAutoDeferred(guideSize, 1);
    }

    private static void iris26501ContributeRgbFrame(
            GLProg glProg, int framebuffer, Point raw, Point packed,
            GLTexture rawTexture, GLTexture chromaGuide, GLTexture flowTexture,
            GLTexture robustnessTexture, GLTexture covarianceTexture,
            GLTexture semanticPhaseWeightTexture,
            int cfaPattern, float[] blackLevel, float whiteLevel, float exposureScale,
            float wbR, float wbB, float greenNoiseS, float greenNoiseO,
            boolean referenceFrame, boolean useFrameWeight, boolean useSemanticPhaseWeight) {
        glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_contribute_26501");
        glProg.setVar("rawSize", raw);
        glProg.setVar("packedSize", packed);
        glProg.setVar("cfaPattern", cfaPattern);
        glProg.setVar("blackLevel", blackLevel);
        glProg.setVar("whiteLevel", whiteLevel);
        glProg.setVar("exposureScale", exposureScale);
        glProg.setVar("wbR", wbR);
        glProg.setVar("wbB", wbB);
        glProg.setVar("greenNoise", greenNoiseS, greenNoiseO);
        /* Same ownership as 1.27.1: noise controls edge agreement, never a post-merge
         * chroma survival threshold. The floor prevents a zero-width edge kernel. */
        /* PhotonCamera 1.27.1 current Spatial RGB constants. */
        glProg.setVar("chromaEdgeNoiseSigmas", 2.5f);
        glProg.setVar("chromaEdgeSigmaFloor", 1.0f / 160.0f);
        glProg.setVar("referenceFrame", referenceFrame ? 1 : 0);
        glProg.setVar("useFrameWeight", useFrameWeight ? 1 : 0);
        glProg.setVar("useSemanticPhaseWeight", useSemanticPhaseWeight ? 1 : 0);
        glProg.setVar("physicalClipThreshold", IRIS26488_HIGHLIGHT_CLIP_THRESHOLD);
        glProg.setTexture("rawTexture", rawTexture);
        glProg.setTexture("chromaGuide", chromaGuide);
        glProg.setTexture("flowTexture", flowTexture);
        glProg.setTexture("robustnessTexture", robustnessTexture);
        glProg.setTexture("covarianceTexture", covarianceTexture);
        glProg.setTexture("semanticPhaseWeightTexture", semanticPhaseWeightTexture);
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, framebuffer);
        android.opengl.GLES30.glEnable(android.opengl.GLES30.GL_BLEND);
        android.opengl.GLES30.glBlendEquation(android.opengl.GLES30.GL_FUNC_ADD);
        android.opengl.GLES30.glBlendFunc(android.opengl.GLES30.GL_ONE, android.opengl.GLES30.GL_ONE);
        glProg.drawBlocks(raw.x, raw.y);
        android.opengl.GLES30.glDisable(android.opengl.GLES30.GL_BLEND);
        android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
    }

    private final ArrayList<ImageFrame> images;
    private final long referenceTimestamp;
    /* IRIS_26480_RECON_FRAME_OWNERSHIP_V3 */
    private final ImageFrame referenceFrame;
    private final MotionBatch.ShortHighlightSlot shortHighlightSlot;
    private Parameters parameters;
    private GLProg glProg;

    private ByteBuffer output;
    /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_BRIDGE */
    private ByteBuffer highlightProvenanceOutput;
    private float effectiveSupport = 1.0f;
    private float supportP10 = 1.0f;
    private float supportP50 = 1.0f;
    private float supportP90 = 1.0f;

    /*
     * IRIS_26440_V2_DIAGNOSTIC_ONLY_LOCAL_OWNERSHIP
     * Diagnostics only. These values never feed reconstruction/image math.
     */
    private static final int IRIS26440_GRID_W = 12;
    private static final int IRIS26440_GRID_H = 8;

    private MotionV2CfaReconstruction(
            Point size,
            ArrayList<ImageFrame> orderedImages,
            long referenceTimestamp,
            Parameters parameters,
            ImageFrame referenceFrame,
            MotionBatch.ShortHighlightSlot shortHighlightSlot) {
        /* IRIS_26488_V4_DISABLE_UNUSED_TUNING_FILE_IO
         * MotionV2CfaReconstruction has no runtime-tunable consumers. Keeping tuning enabled only
         * attempted to create PhotonCameraTuning.ini on every shot, which Android rejected with
         * EACCES/Operation-not-permitted. Disable that unused file I/O; reconstruction constants
         * and image math remain unchanged.
         */
        super(
                size,
                new GLCoreBlockProcessing(
                        size,
                        new GLFormat(GLFormat.DataType.UNSIGNED_16),
                        GLDrawParams.Allocate.Direct),
                "",
                "MotionV2CfaReconstruction",
                false);
        this.images = orderedImages;
        this.referenceTimestamp = referenceTimestamp;
        this.referenceFrame = referenceFrame;
        this.shortHighlightSlot = shortHighlightSlot;
        this.parameters = parameters;
        this.glProg = glOne.glProgram;
    }

    @Override
    public void Compile() {}

    public static MotionV2Merger.Result reconstruct(
            Point size,
            ArrayList<ImageFrame> inputImages,
            long referenceTimestamp,
            Parameters parameters,
            MotionBatch.ShortHighlightSlot shortHighlightSlot) {
        if (inputImages == null || inputImages.isEmpty()) {
            throw new IllegalStateException("Motion V2 reconstruction received no RAW frames");
        }
        ImageFrame reference = null;
        ArrayList<ImageFrame> ordered = new ArrayList<>(inputImages.size());
        for (ImageFrame frame : inputImages) {
            if (frame != null && frame.timestamp == referenceTimestamp) {
                reference = frame;
                break;
            }
        }
        if (reference == null || reference.buffer == null) {
            throw new IllegalStateException(
                    "Motion V2 owned reference missing from retained burst: "
                            + referenceTimestamp);
        }

        ordered.add(reference);
        for (ImageFrame frame : inputImages) {
            if (frame != null && frame != reference) ordered.add(frame);
        }

        /* IRIS_26436_REFERENCE_TIME_ORDERED_TEMPORAL_CONSENSUS */
        if (ordered.size() > 2) {
            ordered.subList(1, ordered.size()).sort(
                    (a, b) -> Long.compare(
                            Math.abs(a.timestamp - referenceTimestamp),
                            Math.abs(b.timestamp - referenceTimestamp)));
        }
        StringBuilder temporalOrder = new StringBuilder();
        for (int oi = 1; oi < ordered.size(); oi++) {
            if (oi > 1) temporalOrder.append(',');
            temporalOrder.append(Math.abs(
                    ordered.get(oi).timestamp - referenceTimestamp));
        }
        Log.d(TAG, "IRIS_26436_REFERENCE_TIME_ORDER"
                + " auxiliaryDeltaNs=" + temporalOrder
                + " allFramesRetained=true"
                + " nearestReferenceFirst=true");

        /*
         * IRIS_26414_REFERENCE_RAW_NORMALIZATION_BEFORE_FLOAT_RECON
         * Histogram/scene normalization remains owned by the physical reference
         * RAW, not by the reconstructed float carrier.
         */
        /*
         * IRIS_26423_KNOWN_HOT_PIXEL_SANITIZE
         *
         * Camera2 already gives us STATISTICS_HOT_PIXEL_MAP in Parameters.
         * Correct only explicitly mapped sites before RAW->CFA, alignment and
         * fusion. Two-pixel neighbours stay on the same Bayer/CFA component.
         */
        /*
         * IRIS_26477_STRICT_WRONSKI_NO_PHOTON_PREMERGE_REPAIR
         * No Photon/Iris RAW mutation before Wronski reconstruction.
         */
        int mappedHotPixelsCorrected = 0;
        Log.d(TAG, "IRIS_26477_STRICT_WRONSKI_NO_PHOTON_PREMERGE_REPAIR"
                + " mappedHotPixelMutation=false"
                + " corrected=0"
                + " frames=" + ordered.size());

        /* IRIS_26490_EXPLICIT_DISPLAY_GAIN_OWNER
         * This percentile estimator is a rendering decision. Wronski/RCD remain in physical
         * sensor-normalized space where sensor white == 1.0.
         */
        parameters.motionCanonicalExposureGain = 1.0f;
        parameters.motionV2ShortHighlightRecoveryExecuted = false;
        parameters.motionV2DisplayGain =
                MotionV2Merger.computeDisplayGain(
                        reference.buffer,
                        size.x,
                        size.y,
                        parameters,
                        reference.motionV2ExposureEnergy);

        MotionV2CfaReconstruction script = null;
        try {
            script = new MotionV2CfaReconstruction(
                    size, ordered, referenceTimestamp, parameters, reference, shortHighlightSlot);
            script.Run();
            if (script.output == null) {
                throw new IllegalStateException("Motion V2 reconstruction returned null RAW");
            }
            return new MotionV2Merger.Result(
                    script.output,
                    referenceTimestamp,
                    ordered.size(),
                    script.effectiveSupport,
                    script.highlightProvenanceOutput);
        } finally {
            if (script != null) {
                try { script.close(); } catch (Throwable ignored) {}
            }
            for (ImageFrame frame : inputImages) {
                if (frame != null) {
                    try { frame.close(); } catch (Throwable ignored) {}
                }
            }
            if (shortHighlightSlot != null) shortHighlightSlot.sealAndClose();
        }
    }

    @Override
    public void Run() {

        final Point raw = parameters.rawSize;
        final Point rawHalf = new Point(raw.x / 2, raw.y / 2);
        final Point iris26487GuideSize = new Point(Math.max(1,rawHalf.x/2),Math.max(1,rawHalf.y/2));
        final Point iris26487RejectSmallSize = new Point(Math.max(1,(rawHalf.x+3)/4),Math.max(1,(rawHalf.y+3)/4));
        final Point iris26487MergeWeightSize = new Point(Math.max(1,(rawHalf.x+1)/2),Math.max(1,(rawHalf.y+1)/2));
        final Point iris26487UnblockerSize = new Point(Math.max(1,(rawHalf.x+7)/8),Math.max(1,(rawHalf.y+7)/8));
        final int frameCount = images.size();
        final int tile = 8;
        /* IRIS_26487_PROCESSING_BUDGET_OWNER
         * Attempt every retained pre-shutter RAW, but submit the dependent Motion GPU chain
         * asynchronously. A single explicit drain occurs only when CPU ownership of the final
         * image is required. Target on-device wall time for a 15-frame attempted burst: <=5 s.
         */
        final long iris26487RunStartNs = System.nanoTime();
        long iris26487GpuDrainMs = 0L;
        long iris26487OutputReadbackMs = 0L;
        glProg.resetDeferredComputeStats();

        if (frameCount == 1) {
            Log.d(TAG, "IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE"
                    + " retainedFrames=1"
                    + " auxiliaryAlignment=false"
                    + " directRgbReconstruction=true"
                    + " downstreamMotionPostPipeline=true"
                    + " diagnosticControl=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE",
                        "retainedFrames=1 auxiliaryAlignment=false"
                                + " directRgbReconstruction=true"
                                + " downstreamMotionPostPipeline=true");
            } catch (Throwable ignored) {}
        }

        /*
         * IRIS_26420_MOTION_V2_CANONICAL_GAIN_APPLIED_ONCE
         * computeDisplayGain() owns scene brightness normalization, but that normalization is
         * explicitly deferred until MotionV2DisplayExposure after Wronski + RCD.
         */
        /*
         * IRIS_26477_WRONSKI_CANONICAL_SENSOR_DOMAIN
         * Display normalization is downstream of Wronski.
         */
        final float canonicalGain = 1.0f;

        /*
         * IRIS_26418_MOTION_V2_RAW_CODE_DOMAIN
         *
         * Parameters.blackLevel and whiteLevel are copied from Camera2 RAW
         * metadata in sensor code values. raw_to_cfa reads UNSIGNED_16 sensor
         * code values. Therefore V2 uses black level in the same code domain:
         * no inherited 0.5 scale is permitted.
         */
        final float[] blackLevel = new float[] {
                parameters.blackLevel[0],
                parameters.blackLevel[1],
                parameters.blackLevel[2],
                parameters.blackLevel[3]
        };

        if (!parameters.motionV2StrictWronskiSensorValid) {
            throw new IllegalStateException(
                    "26477 Wronski missing strict Camera2 sensor authority");
        }
        float noiseS = Math.max(parameters.motionV2WronskiNoiseS, 1.0e-7f);
        float noiseO = Math.max(parameters.motionV2WronskiNoiseO, 1.0e-8f);
        Log.d(TAG, "IRIS_26477_WRONSKI_NOISE_AUTHORITY"
                + " source=CaptureResult.SENSOR_NOISE_PROFILE"
                + " photonNoiseModeler=false"
                + " dynamicNoiseStore=false"
                + " adaptiveNoiseTunable=false"
                + " noiseRstr=false"
                + " displayGainInsideWronski=false"
                + " noiseS=" + noiseS
                + " noiseO=" + noiseO);

        /* IRIS_26486_NO_IPOL_MONTE_CARLO_ACTIVE_PATH
         * Camera2 affine sensor noise is already authoritative. Use the
         * published-style analytic SNR proxy only for static kernel sizing;
         * rejection itself is the GPU MGC graph below.
         */
        final float mfsrSnr = Math.max(6.0f, Math.min(30.0f,
                0.18f / (float)Math.sqrt(Math.max(
                        noiseS * 0.18f + noiseO, 1.0e-8f))));
        final float mfsrT = (mfsrSnr - 6.0f) / 24.0f;
        final float mfsrKDetail = 0.33f + mfsrT * (0.25f - 0.33f);
        final float mfsrKDenoise = 5.0f + mfsrT * (3.0f - 5.0f);
        final float mfsrDth = 0.81f + mfsrT * (0.71f - 0.81f);
        final float mfsrDtr = 1.24f + mfsrT * (1.00f - 1.24f);
        final float mfsrKStretch = 4.0f;
        final float mfsrKShrink = 2.0f;
        final int mfsrTileSize =
                mfsrSnr <= 14.0f ? 64 : (mfsrSnr <= 22.0f ? 32 : 16);

        Log.d(TAG, "IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY"
                + " reconstructionOwner=Wronski_BJZHOU_MGC"
                + " sensorDomainGain=1.0"
                + " displayGain=" + parameters.motionV2DisplayGain
                + " legacyPyramidAlignment=false"
                + " legacyPyramidMerge=false"
                + " photonAdaptiveNoise=false"
                + " photonNoiseRstr=false"
                + " photonHotPixelPremerge=false"
                + " mfsrSnr=" + mfsrSnr
                + " kDetail=" + mfsrKDetail
                + " kDenoise=" + mfsrKDenoise
                + " Dth=" + mfsrDth
                + " Dtr=" + mfsrDtr);

        GLTexture referenceRaw = null;
        GLTexture referenceCfa = null;
        /* IRIS_26463_WRONSKI_WB_DOMAIN_REFERENCE */
        GLTexture wronskiReferenceCfa = null;
        GLTexture wronskiReferenceCov = null;
        GLTexture wronskiReferenceChromaGuide = null;
        GLTexture wronskiReferenceGuide = null;
        GLTexture iris26488ReferenceGray = null;
        GLTexture iris26488StageDiagA = null;
        GLTexture iris26488StageDiagB = null;
        GLTexture iris26488StageDiagC = null;
        GLTexture iris26488LensShading = null;
        MotionV2WronskiAlignment.PreparedReference wronskiPreparedAlignment = null;
        GLTexture mergedA = null;
        GLTexture mergedB = null;
        GLTexture supportA = null;
        GLTexture supportB = null;
        GLTexture result = null;

        /* IRIS_26424_DIRECT_MULTIFRAME_RGB_TEXTURES */
        GLTexture directRgbA = null;
        GLTexture directRgbB = null;
        GLTexture directSupportA = null;
        GLTexture directSupportB = null;

        /*
         * IRIS_26446_TRUE_FRAME_SUPPORT_TEXTURES
         * Separate from normalized-convolution kernel support.
         * Units: reference=1.0 + sum of accepted auxiliary observation
         * confidences, bounded to retained frame count.
         */
        GLTexture directFrameSupportA = null;
        GLTexture directFrameSupportB = null;

        /* IRIS_26501_PROPER_PER_FRAME_SPATIAL_RGB_OWNER */
        GLTexture iris26501SemanticAccumulator = null;
        GLTexture iris26501OpponentWeightAccumulator = null;
        GLTexture iris26501ChromaGuideScratch = null;
        GLTexture iris26501RgbCovScratch = null;
        GLTexture iris26501RgbOutput = null;
        GLTexture iris26501LensShading = null;
        int iris26501RgbFramebuffer = 0;
        int iris26501SemanticContributedFrames = 0;
        int iris26501SemanticHdrContributedFrames = 0;
        /*
         * IRIS_26462_HAL_STANDARD_BAYER_WRONSKI_GUARD
         * Published direct-RGB reconstruction is enabled only for standard
         * Bayer and exact even physical RAW dimensions.
         */
        final boolean directBayer =
                parameters.cfaPattern >= 0
                        && parameters.cfaPattern <= 3
                        && raw.x > 0
                        && raw.y > 0
                        && (raw.x % 2) == 0
                        && (raw.y % 2) == 0
                        && rawHalf.x * 2 == raw.x
                        && rawHalf.y * 2 == raw.y;

        /*
         * IRIS_26426_DIRECT_RGB_SENSOR_GAIN_AUTHORITY
         * Keep timestamp-owned HAL gains in method scope because both the
         * reference initializer and every auxiliary accumulator use them.
         */
        final float[] directGains = parameters.motionV2ColorGains;
        final float directGreenGain =
                directGains != null && directGains.length == 4
                        ? 0.5f * (directGains[1] + directGains[2])
                        : 1.0f;
        final float[] directSensorGains =
                directGains != null && directGains.length == 4
                        ? new float[]{
                                directGains[0],
                                directGreenGain,
                                directGains[3]}
                        : new float[]{1.0f, 1.0f, 1.0f};
        final float wronskiGlobalWbR = directSensorGains[0]
                / Math.max(directSensorGains[1], 1.0e-6f);
        final float wronskiGlobalWbG = 1.0f;
        final float wronskiGlobalWbB = directSensorGains[2]
                / Math.max(directSensorGains[1], 1.0e-6f);
        Iris26487Noise iris26487ReferenceSensorNoise = null;
        float[] iris26487ReferenceWbNoise = null;

        /*
         * IRIS_26447_TRUE_SENSOR_NEUTRAL_HIGHLIGHT_OWNER
         *
         * SENSOR_NEUTRAL_COLOR_POINT is a captured sensor-RGB chromatic
         * direction, not a saturation level and not another white-balance
         * transform. Normalize it to G=1 and expose it only to the reference
         * initializer's missing-channel highlight fallback.
         *
         * Normal measured CFA color remains authoritative. Camera2
         * COLOR_CORRECTION_GAINS + TRANSFORM remain the actual downstream
         * white-balance/color transform and are not replaced or multiplied
         * twice.
         */
        final float[] directWhitePoint = parameters.whitePoint;
        final boolean directWhitePointValid =
                directWhitePoint != null
                        && directWhitePoint.length == 3
                        && Float.isFinite(directWhitePoint[0])
                        && Float.isFinite(directWhitePoint[1])
                        && Float.isFinite(directWhitePoint[2])
                        && directWhitePoint[0] > 1.0e-6f
                        && directWhitePoint[1] > 1.0e-6f
                        && directWhitePoint[2] > 1.0e-6f;
        final float[] directSensorNeutralPoint =
                directWhitePointValid
                        ? new float[]{
                                directWhitePoint[0] / directWhitePoint[1],
                                1.0f,
                                directWhitePoint[2] / directWhitePoint[1]}
                        : new float[]{
                                directGreenGain
                                        / Math.max(directSensorGains[0], 1.0e-6f),
                                1.0f,
                                directGreenGain
                                        / Math.max(directSensorGains[2], 1.0e-6f)};

        try {
            /* IRIS_26486_GPU_REJECTION_NO_CPU_MC_SETUP */

            /*
             * IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT
             * Motion V2 now owns the geometric producer and consumer.
             */
            Log.d(TAG, "IRIS_26420_V2_ALIGNMENT_ARCH"
                    + " v2Owned=true"
                    + " legacyPyramidAlignment=false"
                    + " legacyTileAtlas=false"
                    + " continuousFlow=true");

            referenceRaw = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                    images.get(0).buffer,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            referenceCfa = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);

            glProg.setLayout(tile, tile, 1);
            glProg.useAssetProgram("motionv2/raw_to_cfa", true);
            glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
            glProg.setVar("blackLevel", blackLevel);
            final float iris26487ReferenceExposureScale = canonicalGain * (
                    images.get(0).pair != null
                            ? 1.0f / Math.max(images.get(0).pair.layerMpy, 1.0e-6f)
                            : 1.0f);
            glProg.setVar("exposure", iris26487ReferenceExposureScale);
            glProg.setTexture("inTexture", referenceRaw);
            glProg.setTextureCompute("outTexture", referenceCfa, true);
            glProg.computeAutoDeferred(rawHalf, 1);

            if (directBayer) {
                /*
                 * IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN
                 * Public implementation normalizes RAW then applies camera WB
                 * before alignment/kernel/merge. Camera2 gains are normalized
                 * to green so Wronski sees the same signal convention.
                 */
                final float wronskiWbR = directSensorGains[0]
                        / Math.max(directSensorGains[1], 1.0e-6f);
                final float wronskiWbG = 1.0f;
                final float wronskiWbB = directSensorGains[2]
                        / Math.max(directSensorGains[1], 1.0e-6f);

                wronskiReferenceCfa = new GLTexture(
                        rawHalf,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_wb_cfa", true);
                glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                glProg.setVar("wbR", wronskiWbR);
                glProg.setVar("wbG", wronskiWbG);
                glProg.setVar("wbB", wronskiWbB);
                /* IRIS_26487_WB_LINEAR_ONLY_NO_CLIP_REPAIR */
                glProg.setTextureCompute("inputCfa", referenceCfa, false);
                glProg.setTextureCompute("outputCfa", wronskiReferenceCfa, true);
                glProg.computeAutoDeferred(rawHalf, 1);

                iris26487ReferenceSensorNoise = iris26487FrameNoise(images.get(0),noiseS,noiseO);
                iris26487ReferenceWbNoise = iris26487WbNoiseRgb(
                        iris26487ReferenceSensorNoise,(int)parameters.cfaPattern,iris26487ReferenceExposureScale,wronskiWbR,wronskiWbB);
                /* IRIS_26487_BJZHOU_SAMPLER_FILTER_CONTRACT */
                wronskiReferenceCov = new GLTexture(
                        iris26487GuideSize,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                /* IRIS_26488_NATIVE_RAW_MGC_PRODUCERS
                 * Covariance, chroma guide and rejection guide now share the same native R16UI
                 * calibration contract as bjzhou MergeRgb. FLOAT16 WB CFA is retained only for
                 * Wronski alignment; it is no longer authoritative color/rejection evidence.
                 */
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_mgc_covariance", true);
                glProg.setVar("rawSize", raw);
                glProg.setVar("rawHalf", rawHalf);
                glProg.setVar("guideSize", iris26487GuideSize);
                glProg.setVar("noiseS", iris26487ReferenceWbNoise[1]);
                glProg.setVar("noiseO", iris26487ReferenceWbNoise[4]);
                glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                glProg.setVar("blackLevel", blackLevel);
                glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
                glProg.setVar("exposureScale", iris26487ReferenceExposureScale);
                glProg.setVar("wbR", wronskiWbR);
                glProg.setVar("wbB", wronskiWbB);
                glProg.setTexture("rawTexture", referenceRaw);
                glProg.setTextureCompute("outputCov", wronskiReferenceCov, true);
                glProg.computeAutoDeferred(iris26487GuideSize, 1);

                /* IRIS_26489_REMOVE_PREMERGE_COLOR_SYNTHESIS_REFERENCE
                 * No chroma/highlight synthesis runs in the temporal host.
                 */

                wronskiReferenceGuide = new GLTexture(iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile,tile,1);
                glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);
                glProg.setVar("rawSize",raw);
                glProg.setVar("guideSize",iris26487GuideSize);
                glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                glProg.setVar("blackLevel",blackLevel);
                glProg.setVar("whiteLevel",(float)parameters.whiteLevel);
                glProg.setVar("exposureScale",iris26487ReferenceExposureScale);
                glProg.setVar("wbR",wronskiWbR);
                glProg.setVar("wbB",wronskiWbB);
                glProg.setVar("noiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});
                glProg.setVar("noiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});
                glProg.setTexture("rawTexture",referenceRaw);
                glProg.setTextureCompute("outputGuide",wronskiReferenceGuide,true);
                glProg.computeAutoDeferred(iris26487GuideSize,1);

                iris26488ReferenceGray = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.UNSIGNED_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile,tile,1);
                glProg.useAssetProgram("motionv2/mfsr_mgc_reference_gray",true);
                glProg.setVar("rawSize",raw);
                glProg.setVar("graySize",rawHalf);
                glProg.setVar("blackLevel",blackLevel);
                glProg.setVar("gain",iris26487ReferenceExposureScale);
                glProg.setTexture("rawTexture",referenceRaw);
                glProg.setTextureCompute("outGray",iris26488ReferenceGray,true);
                glProg.computeAutoDeferred(rawHalf,1);
            }

            if (directBayer) {
                /*
                 * IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE
                 * Reference geometry is immutable for this burst. Prepare its
                 * guide/pyramid once instead of rebuilding it for every
                 * auxiliary frame.
                 */
                wronskiPreparedAlignment =
                        MotionV2WronskiAlignment.prepareReference(
                                rawHalf,
                                parameters.cfaPattern,
                                canonicalGain,
                                mfsrSnr,
                                glProg,
                                wronskiReferenceCfa);
            }

            /* IRIS_26483_REMOVE_UNUSED_DIRECT_BAYER_LEGACY_CFA_MERGE
             * Standard-Bayer Motion publishes only the direct Wronski RGB owner.  The old
             * packed-CFA merge/support chain was still dispatched every auxiliary solely for
             * telemetry.  Keep it only for the non-standard fallback path.
             */
            GLTexture currentMerged = null;
            GLTexture nextMerged = null;
            GLTexture currentSupport = null;
            GLTexture nextSupport = null;
            if (!directBayer) {
                mergedA = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                mergedB = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                supportA = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                supportB = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/cfa_reconstruct_init",true);
                glProg.setTextureCompute("referenceTexture",referenceCfa,false);glProg.setTextureCompute("outTexture",mergedA,true);
                glProg.setTextureCompute("outSupport",supportA,true);glProg.computeAutoDeferred(rawHalf,1);
                currentMerged=mergedA;nextMerged=mergedB;currentSupport=supportA;nextSupport=supportB;
            }

            GLTexture currentDirectRgb = null;
            GLTexture nextDirectRgb = null;
            GLTexture currentDirectSupport = null;
            GLTexture nextDirectSupport = null;
            GLTexture currentDirectFrameSupport = null;
            GLTexture nextDirectFrameSupport = null;

            int iris26489AdmittedFrames = 0;
            int iris26489ContributedFrames = 0;
            int iris26489ExpectedAdmittedFrames = 0;
            for (int iris26489Index = 0; iris26489Index < frameCount; ++iris26489Index) {
                ImageFrame iris26489Frame = images.get(iris26489Index);
                if (iris26489Frame != null && iris26489Frame.buffer != null) {
                    iris26489ExpectedAdmittedFrames++;
                }
            }

            if (directBayer) {
                /* IRIS_26489_BJZHOU_PERSISTENT_BAYER_HOST
                 * Persistent burst-wide accumulators. They are never normalized between frames.
                 * Frame 0 is admitted first through the exact same accumulation shader as every
                 * auxiliary, then one normalize pass runs after the final auxiliary.
                 */
                /* IRIS_26489_V3_GLES_LEGAL_R32F_ACCUMULATOR_CARRIER
                 * Preserve four FLOAT32 CFA phase values per logical packed cell by storing
                 * them at their corresponding 2x2 positions in raw-sized R32F textures.
                 * R32F is the GLES image format that can legally be bound GL_READ_WRITE; the
                 * prior RGBA32F read/write image was illegal. For an even Bayer mosaic the byte
                 * footprint is unchanged: rawW*rawH*1*4 == halfW*halfH*4*4.
                 */
                if ((raw.x & 1) != 0 || (raw.y & 1) != 0
                        || rawHalf.x * 2 != raw.x || rawHalf.y * 2 != raw.y) {
                    throw new IllegalStateException("26489 R32F Bayer accumulator requires exact even 2x2 CFA geometry"
                            + " raw=" + raw.x + "x" + raw.y
                            + " packed=" + rawHalf.x + "x" + rawHalf.y);
                }
                Point iris26489AccumulatorSize = new Point(raw.x, raw.y);
                directRgbA = new GLTexture(
                        iris26489AccumulatorSize, new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                directSupportA = new GLTexture(
                        iris26489AccumulatorSize, new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                directFrameSupportA = new GLTexture(
                        iris26489AccumulatorSize, new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                /* IRIS_26501_DELAY_HELPER_BAYER_OUTPUT_ALLOCATION
                 * The RGBA32F helper fused Bayer is not needed until all normal frames have
                 * contributed. Delay its 50 MiB-class allocation so the proper full-resolution
                 * semantic RGB accumulators do not overlap it during the whole burst.
                 */

                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_bayer_accumulator_clear", true);
                glProg.setVar("accumulatorSize", iris26489AccumulatorSize);
                glProg.setTextureCompute("accumulatorNumerator", directRgbA, true);
                glProg.setTextureCompute("accumulatorDenominator", directSupportA, true);
                glProg.setTextureCompute("accumulatorFrameSupport", directFrameSupportA, true);
                glProg.computeAutoDeferred(iris26489AccumulatorSize, 1);

                currentDirectRgb = directRgbA;
                currentDirectSupport = directSupportA;
                currentDirectFrameSupport = directFrameSupportA;
                nextDirectRgb = null;

                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_bayer_accumulate", true);
                glProg.setVar("rawSize", raw);
                glProg.setVar("packedSize", rawHalf);
                glProg.setVar("guideSize", iris26487GuideSize);
                glProg.setVar("blackLevel", blackLevel);
                glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
                glProg.setVar("exposureScale", iris26487ReferenceExposureScale);
                glProg.setVar("referenceFrame", 1);
                glProg.setTexture("rawTexture", referenceRaw);
                glProg.setTexture("flowTexture", wronskiReferenceGuide);
                glProg.setTexture("robustnessTexture", wronskiReferenceGuide);
                glProg.setTextureCompute("alterCov", wronskiReferenceCov, false);
                glProg.setTextureCompute(
                        "accumulatorNumerator", currentDirectRgb, android.opengl.GLES31.GL_READ_WRITE);
                glProg.setTextureCompute(
                        "accumulatorDenominator", currentDirectSupport, android.opengl.GLES31.GL_READ_WRITE);
                glProg.setTextureCompute(
                        "accumulatorFrameSupport", currentDirectFrameSupport, android.opengl.GLES31.GL_READ_WRITE);
                iris26489AdmittedFrames++;
                glProg.computeAutoDeferred(rawHalf, 1);
                iris26489ContributedFrames++;
                Log.d(TAG, "IRIS_26489_BAYER_REFERENCE_CONTRIBUTED frame=0 referenceIdentity=true");

                /* IRIS_26501_REFERENCE_SEMANTIC_CONTRIBUTION
                 * Keep the proven Bayer accumulator alive only for Short-A/provenance diagnostics.
                 * Final RGB ownership starts here and frame 0 executes the same semantic path as
                 * every auxiliary. Two RGBA16F accumulators survive until one final normalization.
                 */
                iris26501SemanticAccumulator = new GLTexture(
                        raw, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                iris26501OpponentWeightAccumulator = new GLTexture(
                        raw, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                iris26501ChromaGuideScratch = new GLTexture(
                        raw, new GLFormat(GLFormat.DataType.FLOAT_16, 1),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                iris26501RgbCovScratch = new GLTexture(
                        iris26487GuideSize, new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                iris26501RgbFramebuffer = iris26501CreateRgbAccumulatorFramebuffer(
                        iris26501SemanticAccumulator, iris26501OpponentWeightAccumulator);
                iris26501ClearRgbAccumulators(iris26501RgbFramebuffer, raw);
                float[] iris26501ReferenceBlack = images.get(0).motionV2BlackLevelValid
                        ? images.get(0).motionV2BlackLevel : blackLevel;
                float iris26501ReferenceWhite = images.get(0).motionV2WhiteLevelValid
                        ? images.get(0).motionV2WhiteLevel : (float) parameters.whiteLevel;
                iris26501RenderChromaGuide(
                        glProg, raw, referenceRaw, iris26501ChromaGuideScratch,
                        (int) parameters.cfaPattern, iris26501ReferenceBlack, iris26501ReferenceWhite,
                        iris26487ReferenceExposureScale, wronskiGlobalWbR, wronskiGlobalWbB);
                iris26501RenderRgbCovariance(
                        glProg, raw, rawHalf, iris26487GuideSize,
                        referenceRaw, iris26501RgbCovScratch,
                        (int) parameters.cfaPattern, iris26501ReferenceBlack, iris26501ReferenceWhite,
                        iris26487ReferenceExposureScale, wronskiGlobalWbR, wronskiGlobalWbB,
                        iris26487ReferenceWbNoise[1], iris26487ReferenceWbNoise[4]);
                iris26501ContributeRgbFrame(
                        glProg, iris26501RgbFramebuffer, raw, rawHalf,
                        referenceRaw, iris26501ChromaGuideScratch, wronskiReferenceGuide,
                        wronskiReferenceGuide, iris26501RgbCovScratch, wronskiReferenceGuide,
                        (int) parameters.cfaPattern, iris26501ReferenceBlack, iris26501ReferenceWhite,
                        iris26487ReferenceExposureScale, wronskiGlobalWbR, wronskiGlobalWbB,
                        iris26487ReferenceWbNoise[1], iris26487ReferenceWbNoise[4],
                        true, false, false);
                iris26501SemanticContributedFrames++;
                Log.i(TAG, "IRIS_26501_SPATIAL_RGB_REFERENCE_CONTRIBUTED"
                        + " frame=0 semantic=G,R-G,B-G"
                        + " additiveBlend=true normalizeNow=false"
                        + " rgba16fAccumulators=2");
            }

            /*
             * IRIS_26440_REFERENCE_FIRST_TELEMETRY_INIT
             *
             * Read the reference initializer support before any auxiliary frame
             * can modify it. This is diagnostic-only and reuses the proven
             * FLOAT32 V2 readback contract.
             */
            float[] iris26440PreviousDirectSupport = null;
            Iris26440ReferenceSummary iris26440ReferenceSummary = null;
            Iris26440TemporalSummary iris26440TemporalSummary =
                    new Iris26440TemporalSummary(
                            IRIS26440_GRID_W,
                            IRIS26440_GRID_H);
            if (false && /* IRIS_26442_DISABLE_REFERENCE_SUPPORT_GPU_READBACK */ (directBayer && currentDirectSupport != null)) {
                currentDirectSupport.BufferLoad();
                ByteBuffer iris26440ReferenceSupportBytes =
                        currentDirectSupport.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                iris26440PreviousDirectSupport =
                        iris26440CopyFloatBuffer(
                                iris26440ReferenceSupportBytes);
                iris26440ReferenceSummary =
                        iris26440SummarizeReferenceSupport(
                                iris26440PreviousDirectSupport,
                                raw.x,
                                raw.y,
                                IRIS26440_GRID_W,
                                IRIS26440_GRID_H);
                Log.d(TAG, "IRIS_26440_REFERENCE_SUPPORT"
                        + " meanRGB="
                        + iris26440ReferenceSummary.meanR + ","
                        + iris26440ReferenceSummary.meanG + ","
                        + iris26440ReferenceSummary.meanB
                        + " fallbackFractionRGB="
                        + iris26440ReferenceSummary.fallbackR + ","
                        + iris26440ReferenceSummary.fallbackG + ","
                        + iris26440ReferenceSummary.fallbackB
                        + " fallbackRBGrid12x8="
                        + iris26440FormatGrid(
                                iris26440ReferenceSummary.fallbackRbGrid)
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_REFERENCE_SUPPORT",
                            "meanR=" + iris26440ReferenceSummary.meanR
                                    + " meanG=" + iris26440ReferenceSummary.meanG
                                    + " meanB=" + iris26440ReferenceSummary.meanB
                                    + " fallbackR=" + iris26440ReferenceSummary.fallbackR
                                    + " fallbackG=" + iris26440ReferenceSummary.fallbackG
                                    + " fallbackB=" + iris26440ReferenceSummary.fallbackB
                                    + " fallbackRBGrid12x8="
                                    + iris26440FormatGrid(
                                            iris26440ReferenceSummary.fallbackRbGrid));
                } catch (Throwable ignored) {}
            }

            /*
             * Also inspect the immutable reference CFA before merging. This is
             * read-only telemetry for clipped/thin-structure diagnosis.
             */
            if (false && /* IRIS_26442_DISABLE_REFERENCE_CFA_CLIP_GPU_READBACK */ (directBayer && referenceCfa != null)) {
                referenceCfa.BufferLoad();
                ByteBuffer iris26440ReferenceCfaBytes =
                        referenceCfa.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                Iris26440ClipSummary iris26440ClipSummary =
                        iris26440SummarizeReferenceClip(
                                iris26440ReferenceCfaBytes,
                                rawHalf.x,
                                rawHalf.y,
                                canonicalGain,
                                IRIS26440_GRID_W,
                                IRIS26440_GRID_H);
                Log.d(TAG, "IRIS_26440_REFERENCE_CFA_CLIP"
                        + " nearClipComponentFraction="
                        + iris26440ClipSummary.c0 + ","
                        + iris26440ClipSummary.c1 + ","
                        + iris26440ClipSummary.c2 + ","
                        + iris26440ClipSummary.c3
                        + " anyNearClipGrid12x8="
                        + iris26440FormatGrid(
                                iris26440ClipSummary.anyClipGrid)
                        + " thresholdRelative=0.93"
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_REFERENCE_CFA_CLIP",
                            "componentFractions="
                                    + iris26440ClipSummary.c0 + ","
                                    + iris26440ClipSummary.c1 + ","
                                    + iris26440ClipSummary.c2 + ","
                                    + iris26440ClipSummary.c3
                                    + " anyNearClipGrid12x8="
                                    + iris26440FormatGrid(
                                            iris26440ClipSummary.anyClipGrid));
                } catch (Throwable ignored) {}
            }

            /* IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE
     * IRIS_26483_BJZHOU_ONLINE_FRAME_SEQUENTIAL_MERGE
             * One auxiliary upload -> WB/CFA -> covariance -> cached-reference LK ->
             * half-res robustness -> immediate semantic accumulation -> scratch reuse.
             */
            GLTexture iris26480RawScratch=null,iris26480CfaScratch=null,iris26480WbCfaScratch=null;
            GLTexture iris26480CovScratch=null,iris26480ChromaGuideScratch=null;
            GLTexture iris26487RejectFullA=null,iris26487RejectFullB=null,iris26487RejectFullC=null;
            GLTexture iris26487RejectSmallLuma=null,iris26487RejectSmallRaw=null,iris26487RejectSmallFiltered=null;
            GLTexture iris26487GuideScratch=null,iris26487UnblockerScratch=null,iris26487FinalWeightScratch=null;
            final Point iris26488StageDiagSize = new Point(24,18);
            final Point iris26488StageAtlasSize = new Point(24,18*Math.max(1,frameCount-1));
            if (directBayer && frameCount > 1) {
                try {
                    iris26488StageDiagA = new GLTexture(iris26488StageAtlasSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26488StageDiagB = new GLTexture(iris26488StageAtlasSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26488StageDiagC = new GLTexture(iris26488StageAtlasSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                } catch (Throwable diagnosticAllocationError) {
                    Log.w(TAG,"IRIS_26488_V4_STAGE_DIAGNOSTIC_ALLOCATION_SKIPPED",diagnosticAllocationError);
                    iris26488CloseDiagnosticTexture(iris26488StageDiagC);
                    iris26488CloseDiagnosticTexture(iris26488StageDiagB);
                    iris26488CloseDiagnosticTexture(iris26488StageDiagA);
                    iris26488StageDiagA = null; iris26488StageDiagB = null; iris26488StageDiagC = null;
                }
            }
            for (int i = 1; i < frameCount; i++) {
                ImageFrame frame = images.get(i);
                if (frame == null || frame.buffer == null) continue;

                /*
                 * IRIS_26439_V2_TEMPORAL_OWNERSHIP_PRODUCER
                 *
                 * V2 previously retained frame timestamps in Java but never
                 * delivered temporal distance to the local CFA accumulator.
                 * Keep every RAW available; make age explicit so local
                 * evidence can become stricter as it moves farther from the
                 * immutable reference instant.
                 */
                final float temporalDistanceMs =
                        referenceTimestamp > 0L && frame.timestamp > 0L
                                ? Math.min(
                                        1000.0f,
                                        Math.abs(
                                                frame.timestamp
                                                        - referenceTimestamp)
                                                / 1_000_000.0f)
                                : 1000.0f;

                /*
                 * IRIS_26441_CRASH_SAFE_TEMPORAL_AGE
                 *
                 * Diagnostic-only CPU telemetry. No GPU readback and no image
                 * math dependency. This preserves temporal-distance visibility
                 * after disabling the crashing per-frame support texture readback.
                 */
                final String iris26441AgeBin =
                        temporalDistanceMs < 50.0f
                                ? "LT50"
                                : temporalDistanceMs < 120.0f
                                        ? "50_120"
                                        : temporalDistanceMs < 200.0f
                                                ? "120_200"
                                                : "GT200";
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26441_TEMPORAL_FRAME_AGE",
                            "frameIndex=" + i
                                    + " temporalDistanceMs=" + temporalDistanceMs
                                    + " ageBin=" + iris26441AgeBin
                                    + " gpuReadback=false"
                                    + " imageMathUnchanged=true");
                } catch (Throwable ignored) {}

                GLTexture rawInput = null;
                GLTexture alterCfa = null;
                GLTexture wronskiAlterCfa = null;
                GLTexture wronskiAlterCov = null;
                GLTexture wronskiAlterChromaGuide = null;
                try {
                    if(iris26480RawScratch==null)iris26480RawScratch=new GLTexture(raw,
                            new GLFormat(GLFormat.DataType.UNSIGNED_16,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    ByteBuffer iris26480FrameView=frame.buffer.duplicate();iris26480FrameView.position(0);
                    iris26480RawScratch.loadData(iris26480FrameView);rawInput=iris26480RawScratch;
                    if(iris26480CfaScratch==null)iris26480CfaScratch=new GLTexture(rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    alterCfa=iris26480CfaScratch;

                    float exposure = canonicalGain * (
                            frame.pair != null
                                    ? 1.0f / Math.max(
                                            frame.pair.layerMpy, 1.0e-6f)
                                    : 1.0f);
                    Iris26487Noise iris26487SensorNoise=iris26487FrameNoise(frame,noiseS,noiseO);
                    float[] iris26487WbNoise=iris26487WbNoiseRgb(iris26487SensorNoise,(int)parameters.cfaPattern,exposure,wronskiGlobalWbR,wronskiGlobalWbB);
                    float[] iris26487GreenPhysicalNoise=iris26487GreenPhysicalNoise(iris26487SensorNoise,(int)parameters.cfaPattern);
                    float[] iris26501FrameBlack = frame.motionV2BlackLevelValid
                            ? frame.motionV2BlackLevel : blackLevel;
                    float iris26501FrameWhite = frame.motionV2WhiteLevelValid
                            ? frame.motionV2WhiteLevel : (float) parameters.whiteLevel;

                    long iris26468RawToCfaStart = System.currentTimeMillis();
                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/raw_to_cfa", true);
                    glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
                    glProg.setVar("blackLevel", blackLevel);
                    glProg.setVar("exposure", exposure);
                    glProg.setTexture("inTexture", rawInput);
                    glProg.setTextureCompute("outTexture", alterCfa, true);
                    glProg.computeAutoDeferred(rawHalf, 1);
                    long iris26468RawToCfaMs =
                            System.currentTimeMillis() - iris26468RawToCfaStart;

                    if (directBayer) {
                        long iris26468WbStart = System.currentTimeMillis();
                        final float wronskiWbR = directSensorGains[0]
                                / Math.max(directSensorGains[1], 1.0e-6f);
                        final float wronskiWbB = directSensorGains[2]
                                / Math.max(directSensorGains[1], 1.0e-6f);
                        if(iris26480WbCfaScratch==null)iris26480WbCfaScratch=new GLTexture(rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        wronskiAlterCfa=iris26480WbCfaScratch;
                        glProg.setLayout(tile, tile, 1);
                        glProg.useAssetProgram("motionv2/mfsr_wb_cfa", true);
                        glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                        glProg.setVar("wbR", wronskiWbR);
                        glProg.setVar("wbG", 1.0f);
                        glProg.setVar("wbB", wronskiWbB);
                        /* IRIS_26487_WB_LINEAR_ONLY_NO_CLIP_REPAIR */
                        glProg.setTextureCompute("inputCfa", alterCfa, false);
                        glProg.setTextureCompute("outputCfa", wronskiAlterCfa, true);
                        glProg.computeAutoDeferred(rawHalf, 1);
                        long iris26468WbMs =
                                System.currentTimeMillis() - iris26468WbStart;

                        long iris26468CovStart = System.currentTimeMillis();
                        if(iris26480CovScratch==null)iris26480CovScratch=new GLTexture(iris26487GuideSize,
                                new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        wronskiAlterCov=iris26480CovScratch;
                        glProg.setLayout(tile, tile, 1);
                        glProg.useAssetProgram("motionv2/mfsr_mgc_covariance", true);
                        glProg.setVar("rawSize", raw);
                        glProg.setVar("rawHalf", rawHalf);
                        glProg.setVar("guideSize", iris26487GuideSize);
                        glProg.setVar("noiseS", iris26487WbNoise[1]);
                        glProg.setVar("noiseO", iris26487WbNoise[4]);
                        glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                        glProg.setVar("blackLevel",blackLevel);
                        glProg.setVar("whiteLevel",(float)parameters.whiteLevel);
                        glProg.setVar("exposureScale",exposure);
                        glProg.setVar("wbR",wronskiWbR);
                        glProg.setVar("wbB",wronskiWbB);
                        glProg.setTexture("rawTexture",rawInput);
                        glProg.setTextureCompute("outputCov", wronskiAlterCov, true);
                        glProg.computeAutoDeferred(iris26487GuideSize, 1);

                        /* IRIS_26501_PER_FRAME_CHROMA_GUIDE
                         * Built while this frame's native RAW and calculation-domain calibration
                         * are still authoritative. It is consumed after Wronski rejection finalizes
                         * this same frame's contribution weight.
                         */
                        iris26501RenderChromaGuide(
                                glProg, raw, rawInput, iris26501ChromaGuideScratch,
                                (int) parameters.cfaPattern, iris26501FrameBlack, iris26501FrameWhite,
                                exposure, wronskiWbR, wronskiWbB);
                        iris26501RenderRgbCovariance(
                                glProg, raw, rawHalf, iris26487GuideSize,
                                rawInput, iris26501RgbCovScratch,
                                (int) parameters.cfaPattern, iris26501FrameBlack, iris26501FrameWhite,
                                exposure, wronskiWbR, wronskiWbB,
                                iris26487WbNoise[1], iris26487WbNoise[4]);
                        /* IRIS_26489_REMOVE_PREMERGE_COLOR_SYNTHESIS_AUX
                         * Covariance/rejection remain; chroma/highlight synthesis is post-merge only.
                         */

                        long iris26468CovMs =
                                System.currentTimeMillis() - iris26468CovStart;
                        Log.d(TAG, "IRIS_26468_STAGE_TIMING"
                                + " frame=" + i
                                + " rawToCfaMs=" + iris26468RawToCfaMs
                                + " wbCfaMs=" + iris26468WbMs
                                + " covarianceMs=" + iris26468CovMs);
                    }

                    MotionV2Alignment.Result ownedAlignment = null;
                    try {
                        long frameProcessingStart = System.currentTimeMillis();
                        long alignmentOnlyStart = System.currentTimeMillis();
                        ownedAlignment =
                                directBayer
                                        ? MotionV2WronskiAlignment.alignPrepared(
                                                wronskiPreparedAlignment,
                                                glProg,
                                                wronskiAlterCfa)
                                        : MotionV2Alignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                glProg,
                                                referenceCfa,
                                                alterCfa);
                        long alignmentOnlyMs =
                                System.currentTimeMillis() - alignmentOnlyStart;

                        if (!directBayer) {
                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/cfa_reconstruct_accumulate",true);
                            glProg.setVar("rawHalf",rawHalf);glProg.setVar("rawSize",raw);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                            glProg.setVar("temporalDistanceMs",temporalDistanceMs);glProg.setVar("noiseS",noiseS);glProg.setVar("noiseO",noiseO);
                            glProg.setVar("maximumSupport",(float)frameCount);glProg.setVar("sensorClipLevel",canonicalGain);
                            glProg.setTexture("flowTexture",ownedAlignment.flowTexture);glProg.setTextureCompute("referenceTexture",referenceCfa,false);
                            glProg.setTextureCompute("currentTexture",currentMerged,false);glProg.setTextureCompute("alterTexture",alterCfa,false);
                            glProg.setTextureCompute("currentSupport",currentSupport,false);glProg.setTextureCompute("outTexture",nextMerged,true);
                            glProg.setTextureCompute("outSupport",nextSupport,true);glProg.computeAutoDeferred(rawHalf,1);
                        }

                        if (directBayer) {
                            /* IRIS_26487_RECONSTRUCTION_CORRECTNESS_BJZHOU_GRAPH
                             * Exact stage semantics: guide -> native-content unblocker ->
                             * reverseWeight+pixelDifference -> 20-tap clipped Gaussian ->
                             * 4x downsample -> 7x7 bilateral -> conditional postprocess ->
                             * recovered 5x5 dilation mapping -> joint G/R-G/B-G accumulation.
                             */
                            long iris26487RejectStart=System.currentTimeMillis();
                            if(iris26487GuideScratch==null)iris26487GuideScratch=new GLTexture(iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                            if(iris26487UnblockerScratch==null)iris26487UnblockerScratch=new GLTexture(iris26487UnblockerSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectFullA==null)iris26487RejectFullA=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectFullB==null)iris26487RejectFullB=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectFullC==null)iris26487RejectFullC=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectSmallLuma==null)iris26487RejectSmallLuma=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectSmallRaw==null)iris26487RejectSmallRaw=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26487RejectSmallFiltered==null)iris26487RejectSmallFiltered=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                            if(iris26487FinalWeightScratch==null)iris26487FinalWeightScratch=new GLTexture(iris26487MergeWeightSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);
                            glProg.setVar("rawSize",raw);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                            glProg.setVar("blackLevel",blackLevel);glProg.setVar("whiteLevel",(float)parameters.whiteLevel);glProg.setVar("exposureScale",exposure);
                            glProg.setVar("wbR",wronskiGlobalWbR);glProg.setVar("wbB",wronskiGlobalWbB);
                            glProg.setVar("noiseShot",new float[]{iris26487WbNoise[0],iris26487WbNoise[1],iris26487WbNoise[2]});
                            glProg.setVar("noiseRead",new float[]{iris26487WbNoise[3],iris26487WbNoise[4],iris26487WbNoise[5]});
                            glProg.setTexture("rawTexture",rawInput);glProg.setTextureCompute("outputGuide",iris26487GuideScratch,true);glProg.computeAutoDeferred(iris26487GuideSize,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);
                            glProg.setVar("rawHalf",rawHalf);glProg.setVar("unblockerSize",iris26487UnblockerSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("physicalExposureScale",exposure);
                            glProg.setVar("greenShot",iris26487GreenPhysicalNoise[0]);glProg.setVar("greenRead",iris26487GreenPhysicalNoise[1]);
                            glProg.setTexture("physicalCfa",alterCfa);glProg.setTextureCompute("outUnblocker",iris26487UnblockerScratch,true);glProg.computeAutoDeferred(iris26487UnblockerSize,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);
                            glProg.setVar("rawHalf",rawHalf);glProg.setVar("guideSize",iris26487GuideSize);
                            glProg.setVar("referenceNoiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});
                            glProg.setVar("referenceNoiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});
                            glProg.setVar("currentNoiseShot",new float[]{iris26487WbNoise[0],iris26487WbNoise[1],iris26487WbNoise[2]});
                            glProg.setVar("currentNoiseRead",new float[]{iris26487WbNoise[3],iris26487WbNoise[4],iris26487WbNoise[5]});
                            glProg.setTexture("referenceGuide",wronskiReferenceGuide);glProg.setTexture("currentGuide",iris26487GuideScratch);glProg.setTexture("flowTexture",ownedAlignment.flowTexture);glProg.setTexture("unblockerTexture",iris26487UnblockerScratch);
                            glProg.setTextureCompute("outReverseWeight",iris26487RejectFullA,true);glProg.setTextureCompute("outPixelDifference",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullB);glProg.setTextureCompute("outEvidence",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);
                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26487RejectFullC);glProg.setTextureCompute("outEvidence",iris26487RejectFullB,true);glProg.computeAutoDeferred(rawHalf,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487RejectSmallSize);glProg.setTexture("referenceGray",iris26488ReferenceGray);glProg.setTexture("inputRejection",iris26487RejectFullA);glProg.setTextureCompute("outLuma",iris26487RejectSmallLuma,true);glProg.setTextureCompute("outRejection",iris26487RejectSmallRaw,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("inputLuma",iris26487RejectSmallLuma);glProg.setTexture("inputRejection",iris26487RejectSmallRaw);glProg.setTextureCompute("outFiltered",iris26487RejectSmallFiltered,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);glProg.setVar("fullSize",rawHalf);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("originalRejection",iris26487RejectFullA);glProg.setTexture("filteredRejection",iris26487RejectSmallFiltered);glProg.setTexture("pixelDifference",iris26487RejectFullB);glProg.setTextureCompute("outRejection",iris26487RejectFullC,true);glProg.computeAutoDeferred(rawHalf,1);

                            glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487MergeWeightSize);glProg.setTexture("inputRejection",iris26487RejectFullC);glProg.setTextureCompute("outWeight",iris26487FinalWeightScratch,true);glProg.computeAutoDeferred(iris26487MergeWeightSize,1);

                            if (iris26488StageDiagA != null) {
                                try {
                                    glProg.setLayout(tile,tile,1);
                                    glProg.useAssetProgram("motionv2/mfsr_26488_stage_diag",true);
                                    glProg.setVar("rawSize",raw);
                                    glProg.setVar("diagSize",iris26488StageDiagSize);
                                    glProg.setVar("frameSlot",i-1);
                                    glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                                    glProg.setVar("blackLevel",blackLevel);
                                    glProg.setVar("whiteLevel",(float)parameters.whiteLevel);
                                    glProg.setVar("clipThreshold",IRIS26488_HIGHLIGHT_CLIP_THRESHOLD);
                                    glProg.setTexture("flowTexture",ownedAlignment.flowTexture);
                                    glProg.setTexture("unblockerTexture",iris26487UnblockerScratch);
                                    glProg.setTexture("reverseWeightTexture",iris26487RejectFullA);
                                    glProg.setTexture("pixelDifferenceTexture",iris26487RejectFullB);
                                    glProg.setTexture("postRejectionTexture",iris26487RejectFullC);
                                    glProg.setTexture("finalWeightTexture",iris26487FinalWeightScratch);
                                    glProg.setTexture("rawTexture",rawInput);
                                    glProg.setTextureCompute("outStageA",iris26488StageDiagA,true);
                                    glProg.setTextureCompute("outStageB",iris26488StageDiagB,true);
                                    glProg.setTextureCompute("outStageC",iris26488StageDiagC,true);
                                    glProg.computeAutoDeferred(iris26488StageDiagSize,1);
                                } catch (Throwable diagnosticDispatchError) {
                                    Log.w(TAG,"IRIS_26488_V4_STAGE_DIAGNOSTIC_DISPATCH_SKIPPED frame="+i,diagnosticDispatchError);
                                    iris26488CloseDiagnosticTexture(iris26488StageDiagC);
                                    iris26488CloseDiagnosticTexture(iris26488StageDiagB);
                                    iris26488CloseDiagnosticTexture(iris26488StageDiagA);
                                    iris26488StageDiagA = null; iris26488StageDiagB = null; iris26488StageDiagC = null;
                                }
                            }
                            long iris26487RejectMs=System.currentTimeMillis()-iris26487RejectStart;

                            /* IRIS_26501_PER_FRAME_SEMANTIC_ACCUMULATION
                             * Wronski flow/covariance/final rejection remain the frame authority.
                             * RGB evidence is accumulated now, before the helper Bayer stack can
                             * collapse temporal colour information.
                             */
                            long iris26501RgbAccumulateStart=System.currentTimeMillis();
                            iris26501ContributeRgbFrame(
                                    glProg, iris26501RgbFramebuffer, raw, rawHalf,
                                    rawInput, iris26501ChromaGuideScratch, ownedAlignment.flowTexture,
                                    iris26487FinalWeightScratch, iris26501RgbCovScratch,
                                    iris26487FinalWeightScratch,
                                    (int) parameters.cfaPattern, iris26501FrameBlack, iris26501FrameWhite,
                                    exposure, wronskiGlobalWbR, wronskiGlobalWbB,
                                    iris26487WbNoise[1], iris26487WbNoise[4],
                                    false, true, false);
                            iris26501SemanticContributedFrames++;
                            long iris26501RgbAccumulateMs=
                                    System.currentTimeMillis()-iris26501RgbAccumulateStart;

                            long iris26487AccumulateStart=System.currentTimeMillis();
                            glProg.setLayout(tile,tile,1);
                            glProg.useAssetProgram("motionv2/mfsr_bayer_accumulate",true);
                            glProg.setVar("rawSize",raw);
                            glProg.setVar("packedSize",rawHalf);
                            glProg.setVar("guideSize",iris26487GuideSize);
                            glProg.setVar("blackLevel",blackLevel);
                            glProg.setVar("whiteLevel",(float)parameters.whiteLevel);
                            glProg.setVar("exposureScale",exposure);
                            glProg.setVar("referenceFrame",0);
                            glProg.setTexture("rawTexture",rawInput);
                            glProg.setTexture("flowTexture",ownedAlignment.flowTexture);
                            glProg.setTexture("robustnessTexture",iris26487FinalWeightScratch);
                            glProg.setTextureCompute("alterCov",wronskiAlterCov,false);
                            glProg.setTextureCompute(
                                    "accumulatorNumerator",currentDirectRgb,android.opengl.GLES31.GL_READ_WRITE);
                            glProg.setTextureCompute(
                                    "accumulatorDenominator",currentDirectSupport,android.opengl.GLES31.GL_READ_WRITE);
                            glProg.setTextureCompute(
                                    "accumulatorFrameSupport",currentDirectFrameSupport,android.opengl.GLES31.GL_READ_WRITE);
                            iris26489AdmittedFrames++;
                            glProg.computeAutoDeferred(rawHalf,1);
                            iris26489ContributedFrames++;
                            long iris26487AccumulateMs=System.currentTimeMillis()-iris26487AccumulateStart;
                            Log.d(TAG,"IRIS_26489_BJZHOU_BAYER_ACCUMULATE frame="+i
                                    +" rejectionMs="+iris26487RejectMs
                                    +" accumulateMs="+iris26487AccumulateMs
                                    +" spatialRgbAccumulateMs="+iris26501RgbAccumulateMs
                                    +" persistentAccumulator=true normalizeNow=false"
                                    +" semanticRgbBeforeBayerCollapse=true");


                            /*
                             * IRIS_26440_PER_FRAME_TEMPORAL_SUPPORT_DELTA
                             *
                             * The output support after THIS auxiliary is
                             * subtracted from the previous support snapshot.
                             * Therefore the telemetry retains frame/source
                             * identity without altering shader/image math.
                             */
                            if (false && /* IRIS_26441_DISABLE_PER_FRAME_SUPPORT_READBACK */ (iris26440PreviousDirectSupport != null)) {
                                nextDirectSupport.BufferLoad();
                                ByteBuffer iris26440NextSupportBytes =
                                        nextDirectSupport.textureBuffer(
                                                new GLFormat(
                                                        GLFormat.DataType.FLOAT_32,
                                                        4),
                                                true);
                                float[] iris26440NextSupport =
                                        iris26440CopyFloatBuffer(
                                                iris26440NextSupportBytes);
                                Iris26440FrameDelta iris26440Delta =
                                        iris26440SummarizeFrameDelta(
                                                iris26440PreviousDirectSupport,
                                                iris26440NextSupport,
                                                raw.x,
                                                raw.y,
                                                temporalDistanceMs,
                                                IRIS26440_GRID_W,
                                                IRIS26440_GRID_H);
                                iris26440TemporalSummary.add(
                                        temporalDistanceMs,
                                        iris26440Delta);
                                Log.d(TAG, "IRIS_26440_FRAME_SUPPORT_DELTA"
                                        + " frame=" + i
                                        + " ageMs=" + temporalDistanceMs
                                        + " ageBin="
                                        + iris26440AgeBinName(
                                                temporalDistanceMs)
                                        + " meanDeltaRGB="
                                        + iris26440Delta.meanR + ","
                                        + iris26440Delta.meanG + ","
                                        + iris26440Delta.meanB
                                        + " positivePixelFraction="
                                        + iris26440Delta.positiveFraction
                                        + " grid12x8="
                                        + iris26440FormatGrid(
                                                iris26440Delta.grid)
                                        + " imageMathUnchanged=true");
                                try {
                                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                            "IRIS_26440_FRAME_SUPPORT_DELTA",
                                            "frame=" + i
                                                    + " ageMs=" + temporalDistanceMs
                                                    + " ageBin="
                                                    + iris26440AgeBinName(
                                                            temporalDistanceMs)
                                                    + " meanR="
                                                    + iris26440Delta.meanR
                                                    + " meanG="
                                                    + iris26440Delta.meanG
                                                    + " meanB="
                                                    + iris26440Delta.meanB
                                                    + " positiveFraction="
                                                    + iris26440Delta.positiveFraction
                                                    + " grid12x8="
                                                    + iris26440FormatGrid(
                                                            iris26440Delta.grid));
                                } catch (Throwable ignored) {}
                                iris26440PreviousDirectSupport =
                                        iris26440NextSupport;
                            }

                            /* IRIS_26489_PERSISTENT_ACCUMULATOR_NO_PING_PONG
                             * The same three images remain authoritative for the whole burst.
                             */

                        }

                        Log.d(TAG, "IRIS_26420_V2_ALIGNMENT_FRAME"
                                + " frame=" + i
                                + " elapsedMs="
                                + (System.currentTimeMillis()-frameProcessingStart)
                                + " alignmentOnlyMs=" + alignmentOnlyMs
                                + " referencePreparedOnce=" + directBayer
                                + " globalDxPacked="
                                + ownedAlignment.globalDxPacked
                                + " globalDyPacked="
                                + ownedAlignment.globalDyPacked
                                + " meanConfidence="
                                + ownedAlignment.meanConfidence
                                + " lowConfidenceFraction="
                                + ownedAlignment.lowConfidenceFraction
                                + " temporalDistanceMs="
                                + temporalDistanceMs);
                    } finally {
                        if (ownedAlignment != null) ownedAlignment.close();
                    }

                    if (!directBayer) {
                        GLTexture swapMerged=currentMerged;currentMerged=nextMerged;nextMerged=swapMerged;
                        GLTexture swapSupport=currentSupport;currentSupport=nextSupport;nextSupport=swapSupport;
                    }
                    /* IRIS_26483_ONLINE_COMMAND_STREAM_UI_YIELD
                     * Keep one ordered GLES stream like RAWmax/MGC.  Avoid forcing a flush after
                     * every auxiliary; submit a breathing checkpoint every fourth frame only.
                     */
                    if ((i & 3) == 0) android.opengl.GLES30.glFlush();
                    Thread.yield();
                } finally {
                    wronskiAlterCov=null; /* persistent */
                    wronskiAlterCfa=null; /* persistent */
                    alterCfa=null; /* persistent */
                    rawInput=null; /* persistent */
                }
            }

            if(iris26487FinalWeightScratch!=null)iris26487FinalWeightScratch.close();
            if(iris26487UnblockerScratch!=null)iris26487UnblockerScratch.close();
            if(iris26487GuideScratch!=null)iris26487GuideScratch.close();
            if(iris26487RejectSmallFiltered!=null)iris26487RejectSmallFiltered.close();
            if(iris26487RejectSmallRaw!=null)iris26487RejectSmallRaw.close();
            if(iris26487RejectSmallLuma!=null)iris26487RejectSmallLuma.close();
            if(iris26487RejectFullC!=null)iris26487RejectFullC.close();
            if(iris26487RejectFullB!=null)iris26487RejectFullB.close();
            if(iris26487RejectFullA!=null)iris26487RejectFullA.close();
            if(iris26480CovScratch!=null)iris26480CovScratch.close();
            if(iris26480ChromaGuideScratch!=null)iris26480ChromaGuideScratch.close();
            if(iris26480WbCfaScratch!=null)iris26480WbCfaScratch.close();
            if(iris26480CfaScratch!=null)iris26480CfaScratch.close();
            if(iris26480RawScratch!=null)iris26480RawScratch.close();
            Log.d(TAG,"IRIS_26483_ONLINE_MERGE_COMPLETE frames="+frameCount
                    +" alignment=levelwiseLK referenceProductsAllLevels=true robustnessResolution=bjzhouMergeWeight"
                    +" legacyDirectBayerCfaMergePasses=0 perFrameGlFlush=false jointSemantic=G,R-G,B-G");

            /*
             * IRIS_26440_TEMPORAL_BIN_SUMMARY
             *
             * Reference-first decision telemetry:
             *   <50 ms, 50-120 ms, 120-200 ms, >200 ms.
             * These are measured support additions, not requested frames.
             */
            if (false && /* IRIS_26442_DISABLE_DIRECT_RGB_SUPPORT_GPU_READBACK */ (directBayer)) {
                Log.d(TAG, "IRIS_26440_TEMPORAL_BIN_SUMMARY"
                        + " lt50MeanRGB="
                        + iris26440TemporalSummary.meanRgb(0)
                        + " ms50to120MeanRGB="
                        + iris26440TemporalSummary.meanRgb(1)
                        + " ms120to200MeanRGB="
                        + iris26440TemporalSummary.meanRgb(2)
                        + " gt200MeanRGB="
                        + iris26440TemporalSummary.meanRgb(3)
                        + " lt50Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(0))
                        + " ms50to120Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(1))
                        + " ms120to200Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(2))
                        + " gt200Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(3))
                        + " referenceFirstTarget=true"
                        + " staticOnlyTemporalEnrichmentTarget=true"
                        + " naturalReferenceMotionBlurPreserved=true"
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_TEMPORAL_BIN_SUMMARY",
                            "lt50=" + iris26440TemporalSummary.meanRgb(0)
                                    + " 50to120="
                                    + iris26440TemporalSummary.meanRgb(1)
                                    + " 120to200="
                                    + iris26440TemporalSummary.meanRgb(2)
                                    + " gt200="
                                    + iris26440TemporalSummary.meanRgb(3)
                                    + " gt200Grid12x8="
                                    + iris26440FormatGrid(
                                            iris26440TemporalSummary.grid(3))
                                    + " referenceFirstTarget=true");
                } catch (Throwable ignored) {}
            }

            /* IRIS_26489_ADMISSION_EQUALS_ACCUMULATOR_CONTRIBUTION_INVARIANT
             * A frame cannot silently disappear between host admission and accumulator execution.
             * Per-pixel rejection is still legal; whole-frame host collapse is not.
             */
            if (directBayer) {
                if (iris26489AdmittedFrames != iris26489ContributedFrames
                        || iris26489AdmittedFrames != iris26489ExpectedAdmittedFrames) {
                    throw new IllegalStateException(
                            "IRIS_26489_ACCUMULATOR_INVARIANT_FAILED admitted="
                                    + iris26489AdmittedFrames
                                    + " contributed=" + iris26489ContributedFrames
                                    + " expected=" + iris26489ExpectedAdmittedFrames);
                }
                Log.i(TAG, "IRIS_26489_ACCUMULATOR_INVARIANT_PASS admitted="
                        + iris26489AdmittedFrames
                        + " contributed=" + iris26489ContributedFrames
                        + " expected=" + iris26489ExpectedAdmittedFrames
                        + " referenceFrame0=true normalizeCount=1");
                if (iris26501SemanticContributedFrames != iris26489AdmittedFrames) {
                    throw new IllegalStateException(
                            "IRIS_26501_SPATIAL_RGB_CONTRIBUTION_INVARIANT_FAILED semantic="
                                    + iris26501SemanticContributedFrames
                                    + " admitted=" + iris26489AdmittedFrames);
                }
                Log.i(TAG, "IRIS_26501_SPATIAL_RGB_CONTRIBUTION_INVARIANT_PASS"
                        + " admitted=" + iris26489AdmittedFrames
                        + " semanticContributed=" + iris26501SemanticContributedFrames
                        + " referenceFrame0=true normalizeCountPending=1");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26489_ACCUMULATOR_INVARIANT_PASS",
                            "admitted=" + iris26489AdmittedFrames
                                    + " contributed=" + iris26489ContributedFrames
                                    + " expected=" + iris26489ExpectedAdmittedFrames);
                } catch (Throwable ignored) {}
            }

            /* IRIS_26416_MOTION_V2_PROVEN_FLOAT32_BRIDGE
             * The proven four-byte FLOAT32 transfer remains the cross-context stabilization
             * boundary. 26501 keeps the 26499 packed Bayer result only as a helper carrier for
             * HDR provenance/neutral fallback; the final public carrier is full-resolution
             * camera-linear RGB from the per-frame semantic accumulator.
             */
            GLTexture imageOutput;
            if (directBayer) {
                /* IRIS_26501_DELAY_HELPER_BAYER_OUTPUT_ALLOCATION */
                directRgbB = new GLTexture(
                        rawHalf, new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                nextDirectRgb = directRgbB;
                /* IRIS_26489_BJZHOU_BAYER_NORMALIZE_EXACTLY_ONCE */
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_bayer_normalize", true);
                glProg.setVar("packedSize", rawHalf);
                glProg.setTextureCompute("accumulatorNumerator", currentDirectRgb, false);
                glProg.setTextureCompute("accumulatorDenominator", currentDirectSupport, false);
                glProg.setTextureCompute("outCfa", nextDirectRgb, true);
                glProg.computeAutoDeferred(rawHalf, 1);
                imageOutput = nextDirectRgb;
                Log.d(TAG, "IRIS_26489_FUSED_BAYER_HELPER_OUTPUT"
                        + " frame0Reference=true"
                        + " persistentAccumulator=true"
                        + " admitted=" + iris26489AdmittedFrames
                        + " contributed=" + iris26489ContributedFrames
                        + " normalizeCount=1"
                        + " ordinaryColorAuthority=false"
                        + " hdrProvenanceBrightnessHelper=true"
                        + " packedSize=" + rawHalf.x + "x" + rawHalf.y);
            } else {
                imageOutput = currentMerged;
            }

            /* IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_OWNER
             * Classify R/G1/G2/B clipping independently before short substitution. The four ternary
             * phase states are base-3 packed into the existing R32F carrier, preserving bandwidth.
             */
            GLTexture iris26492BaseProvenance = null;
            GLTexture iris26492RecoveredProvenance = null;
            GLTexture iris26492ReadbackProvenance = null;
            if (directBayer) {
                iris26492BaseProvenance = new GLTexture(
                        rawHalf, new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/highlight_provenance_init", true);
                glProg.setVar("packedSize", rawHalf);
                glProg.setVar("referenceExposureScale", iris26487ReferenceExposureScale);
                glProg.setVar("physicalClipThreshold", IRIS26487_CLIP_THRESHOLD);
                glProg.setTexture("normalCfa", imageOutput);
                glProg.setTextureCompute("outProvenance", iris26492BaseProvenance, true);
                glProg.computeAutoDeferred(rawHalf, 1);
                iris26492ReadbackProvenance = iris26492BaseProvenance;
            }

            /* IRIS_26498_V13_SEPARATE_AUXILIARY_OWNERS */
            ImageFrame irisV13ShadowAuxFrame = shortHighlightSlot == null
                    ? null : shortHighlightSlot.shadowAuxSlot.takeAndSeal();
            /* IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE */
            ImageFrame shortHighlightFrame = shortHighlightSlot == null
                    ? null : shortHighlightSlot.takeAndSeal();
            Log.d(TAG, "IRIS_26490_SHORT_RECONSTRUCTION_BOUNDARY"
                    + " present=" + (shortHighlightFrame != null)
                    + " timestamp=" + (shortHighlightFrame == null ? -1L : shortHighlightFrame.timestamp)
                    + " exposureNs=" + (shortHighlightFrame == null ? 0L : shortHighlightFrame.motionV2ActualExposureNs)
                    + " iso=" + (shortHighlightFrame == null ? 0 : shortHighlightFrame.motionV2ActualIso)
                    + " exposureEnergy=" + (shortHighlightFrame == null ? 0.0 : shortHighlightFrame.motionV2ExposureEnergy)
                    + " slotSealedAtRecoveryBoundary=true");
            /* IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY_V2 */
            GLTexture iris26480ReadbackOutput=imageOutput,iris26480ShortRaw=null,iris26480ShortCfa=null;
            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;
            GLTexture irisV13ShadowRaw=null,irisV13ShadowCfa=null,irisV13ShadowWbCfa=null,irisV13ShadowRecovered=null;
            GLTexture iris26501ShadowWeight=null,iris26501ShadowCov=null;
            GLTexture iris26501ShortWeight=null,iris26501ShortCov=null;
            MotionV2Alignment.Result irisV13ShadowAlignment=null; GLBuffer irisV13ShadowDiag=null;
            long irisV13ShadowAlignDispatchMs=0L,irisV13ShadowFuseDispatchMs=0L;
            /* IRIS_26496_SHORT_FAILURE_DIAGNOSTIC_OWNER
             * Tiny 64-uint SSBO only; no full-frame diagnostic carrier. It is read after the
             * existing one-and-only final GPU drain and cannot affect reconstruction math.
             */
            GLBuffer iris26496ShortDiag = null;
            /* IRIS_26488_V3_DIAGNOSTIC_SCOPE_OWNER
             * The coarse diagnostic resources must survive the short-recovery try/finally because
             * their readback occurs after that block. Keep ownership in the enclosing reconstruction
             * scope while preserving the same one-drain GPU ordering.
             */
            final Point iris26487DiagSize = new Point(48,36);
            GLTexture iris26487DiagTexture = null;
            GLTexture iris26488DenominatorDiagTexture = null;
            try{
                /* IRIS_26498_V13_SHADOW_AUX_REFERENCE_OWNED_ALIGNMENT
                 * One pre-shutter auxiliary, never in the accumulator. It writes a separate packed
                 * CFA only when local reference correspondence and a per-phase exposure/support SNR proof pass.
                 */
                if(directBayer&&irisV13ShadowAuxFrame!=null&&irisV13ShadowAuxFrame.buffer!=null
                        &&referenceFrame!=null&&referenceFrame.motionV2ExposureEnergy>0.0
                        &&irisV13ShadowAuxFrame.motionV2ExposureEnergy>referenceFrame.motionV2ExposureEnergy
                        &&wronskiPreparedAlignment!=null&&currentDirectFrameSupport!=null
                        ){
                    float irisV13ShadowToNormal=(float)(referenceFrame.motionV2ExposureEnergy
                            /irisV13ShadowAuxFrame.motionV2ExposureEnergy);
                    if(irisV13ShadowToNormal>=0.25f&&irisV13ShadowToNormal<=0.84f){
                        long irisV13AlignStart=System.nanoTime();
                        irisV13ShadowRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),
                                irisV13ShadowAuxFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        irisV13ShadowCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        float[] shadowBlack=irisV13ShadowAuxFrame.motionV2BlackLevelValid
                                ?irisV13ShadowAuxFrame.motionV2BlackLevel:blackLevel;
                        float shadowWhite=irisV13ShadowAuxFrame.motionV2WhiteLevelValid
                                ?irisV13ShadowAuxFrame.motionV2WhiteLevel:(float)parameters.whiteLevel;
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);
                        glProg.setVar("whiteLevel",shadowWhite);glProg.setVar("blackLevel",shadowBlack);glProg.setVar("exposure",1.0f);
                        glProg.setTexture("inTexture",irisV13ShadowRaw);glProg.setTextureCompute("outTexture",irisV13ShadowCfa,true);
                        glProg.computeAutoDeferred(rawHalf,1);
                        float rr=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f);
                        float bb=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);
                        float alignmentScale=irisV13ShadowToNormal*iris26487ReferenceExposureScale;
                        irisV13ShadowWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);
                        glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("wbR",rr*alignmentScale);
                        glProg.setVar("wbG",alignmentScale);glProg.setVar("wbB",bb*alignmentScale);
                        glProg.setTextureCompute("inputCfa",irisV13ShadowCfa,false);glProg.setTextureCompute("outputCfa",irisV13ShadowWbCfa,true);
                        glProg.computeAutoDeferred(rawHalf,1);
                        irisV13ShadowAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,irisV13ShadowWbCfa);
                        irisV13ShadowAlignDispatchMs=(System.nanoTime()-irisV13AlignStart)/1000000L;

                        /* IRIS_26501_SHADOW_AUX_SEMANTIC_PREP
                         * Build the same per-frame green/covariance evidence as every normal frame.
                         * The shadow validation shader below alone decides where this frame is allowed
                         * to contribute; no helper-Bayer color is consumed by the RGB owner.
                         */
                        Iris26487Noise iris26501ShadowSensorNoise=
                                iris26487FrameNoise(irisV13ShadowAuxFrame,noiseS,noiseO);
                        float[] iris26501ShadowWbNoise=iris26487WbNoiseRgb(
                                iris26501ShadowSensorNoise,(int)parameters.cfaPattern,
                                alignmentScale,rr,bb);
                        iris26501ShadowCov=new GLTexture(
                                iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),
                                null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        iris26501RenderRgbCovariance(
                                glProg,raw,rawHalf,iris26487GuideSize,
                                irisV13ShadowRaw,iris26501ShadowCov,
                                (int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,
                                iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4]);
                        iris26501RenderChromaGuide(
                                glProg,raw,irisV13ShadowRaw,iris26501ChromaGuideScratch,
                                (int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb);

                        long irisV13FuseStart=System.nanoTime();
                        irisV13ShadowRecovered=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        iris26501ShadowWeight=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        irisV13ShadowDiag=new GLBuffer(32,new GLFormat(GLFormat.DataType.UNSIGNED_32));
                        irisV13ShadowDiag.uploadBuffer(new int[32],32);
                        
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/shadow_aux_bayer_fuse",true);
                        glProg.setVar("packedSize",rawHalf);glProg.setVar("referenceExposureScale",iris26487ReferenceExposureScale);
                        glProg.setVar("shadowToNormalScale",irisV13ShadowToNormal);glProg.setVar("shadowClipThreshold",IRIS26487_CLIP_THRESHOLD);
                        glProg.setVar("minimumFlowConfidence",0.40f);glProg.setVar("deepShadowThreshold",0.10f);
                        glProg.setVar("deepShadowPackCeiling",0.18f);glProg.setVar("minimumShadowSignal",0.004f);glProg.setVar("requiredExposureSupportRatio",1.15f);
                        glProg.setVar("shadowExposureRatio",1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f));glProg.setVar("maxShadowBlend",0.20f);
                        
                        
                        glProg.setTexture("mergedCfa",imageOutput);glProg.setTexture("referenceCfa",referenceCfa);
                        glProg.setTexture("shadowCfa",irisV13ShadowCfa);glProg.setTexture("flowTexture",irisV13ShadowAlignment.flowTexture);
                        glProg.setTexture("frameSupport",currentDirectFrameSupport);glProg.setTextureCompute("outCfa",irisV13ShadowRecovered,true);
                        glProg.setTextureCompute("outSemanticWeight",iris26501ShadowWeight,true);
                        glProg.setBufferCompute("ShadowDiagBuf",irisV13ShadowDiag);glProg.computeAutoDeferred(rawHalf,1);
                        irisV13ShadowFuseDispatchMs=(System.nanoTime()-irisV13FuseStart)/1000000L;
                        iris26501ContributeRgbFrame(
                                glProg,iris26501RgbFramebuffer,raw,rawHalf,
                                irisV13ShadowRaw,iris26501ChromaGuideScratch,
                                irisV13ShadowAlignment.flowTexture,iris26501ShadowWeight,iris26501ShadowCov,
                                iris26501ShadowWeight,
                                (int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,
                                iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4],
                                false,false,true);
                        iris26501SemanticHdrContributedFrames++;
                        imageOutput=irisV13ShadowRecovered;iris26480ReadbackOutput=irisV13ShadowRecovered;
                        Log.i(TAG,"IRIS_26498_V13_SHADOW_AUX_DISPATCH"
                                +" shadowToNormalScale="+irisV13ShadowToNormal
                                +" shadowAuxExposureRatio="+(1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f))
                                +" shadowAuxTimestampDelta="+(irisV13ShadowAuxFrame.timestamp-referenceFrame.timestamp)
                                +" shadowAuxAlignMs="+irisV13ShadowAlignDispatchMs
                                +" shadowAuxFuseMs="+irisV13ShadowFuseDispatchMs
                                +" shadowAuxTotalMs="+(irisV13ShadowAlignDispatchMs+irisV13ShadowFuseDispatchMs)
                                +" normalAccumulatorAdmission=false secondDemosaic=false extraGpuDrain=false");
                    }
                }
                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&referenceFrame!=null
                        &&referenceFrame.motionV2ExposureEnergy>0.0&&shortHighlightFrame.motionV2ExposureEnergy>0.0
                        &&shortHighlightFrame.motionV2ExposureEnergy<referenceFrame.motionV2ExposureEnergy
                        &&wronskiPreparedAlignment!=null){
                    float shortToNormalScale=(float)Math.max(1.0,Math.min(8.0,
                            referenceFrame.motionV2ExposureEnergy/shortHighlightFrame.motionV2ExposureEnergy));
                    iris26480ShortRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),
                            shortHighlightFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26480ShortCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    float[] iris26490ShortBlack = shortHighlightFrame.motionV2BlackLevelValid
                            ? shortHighlightFrame.motionV2BlackLevel
                            : blackLevel;
                    float iris26490ShortWhite = shortHighlightFrame.motionV2WhiteLevelValid
                            ? shortHighlightFrame.motionV2WhiteLevel
                            : (float)parameters.whiteLevel;
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);
                    glProg.setVar("whiteLevel",iris26490ShortWhite);glProg.setVar("blackLevel",iris26490ShortBlack);
                    glProg.setVar("exposure",1.0f);glProg.setTexture("inTexture",iris26480ShortRaw);
                    glProg.setTextureCompute("outTexture",iris26480ShortCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                    float r=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f),b=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);
                    iris26480ShortWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    /* IRIS_26490_SHORT_ALIGNMENT_RADIOMETRIC_NORMALIZATION
                     * LK uses a brightness-constancy residual. Normalize only the temporary short
                     * alignment proxy into the normal-reference radiance domain using measured
                     * exposure energy. The physical short CFA above remains unscaled for clipping
                     * tests and real highlight replacement.
                     */
                    float iris26490ShortAlignmentScale=shortToNormalScale*iris26487ReferenceExposureScale;
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                    glProg.setVar("wbR",r*iris26490ShortAlignmentScale);
                    glProg.setVar("wbG",iris26490ShortAlignmentScale);
                    glProg.setVar("wbB",b*iris26490ShortAlignmentScale);
                    /* IRIS_26487_SHORT_WB_LINEAR_ONLY */
                    glProg.setTextureCompute("inputCfa",iris26480ShortCfa,false);glProg.setTextureCompute("outputCfa",iris26480ShortWbCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                    iris26480ShortAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,iris26480ShortWbCfa);
                    Iris26487Noise iris26501ShortSensorNoise=
                            iris26487FrameNoise(shortHighlightFrame,noiseS,noiseO);
                    float[] iris26501ShortWbNoise=iris26487WbNoiseRgb(
                            iris26501ShortSensorNoise,(int)parameters.cfaPattern,
                            iris26490ShortAlignmentScale,r,b);
                    iris26501ShortCov=new GLTexture(
                            iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),
                            null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                    iris26501RenderRgbCovariance(
                            glProg,raw,rawHalf,iris26487GuideSize,
                            iris26480ShortRaw,iris26501ShortCov,
                            (int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,
                            iris26490ShortAlignmentScale,r,b,
                            iris26501ShortWbNoise[1],iris26501ShortWbNoise[4]);
                    iris26501RenderChromaGuide(
                            glProg,raw,iris26480ShortRaw,iris26501ChromaGuideScratch,
                            (int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,
                            iris26490ShortAlignmentScale,r,b);

                    iris26480Recovered=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26492RecoveredProvenance=new GLTexture(
                            rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26496ShortDiag = new GLBuffer(
                            64, new GLFormat(GLFormat.DataType.UNSIGNED_32));
                    iris26496ShortDiag.uploadBuffer(new int[64], 64);
                    glProg.setLayout(tile,tile,1);
                    glProg.useAssetProgram("motionv2/short_highlight_bayer_recover",true);
                    glProg.setVar("packedSize",rawHalf);
                    glProg.setVar("shortToNormalScale",shortToNormalScale);
                    glProg.setVar("physicalClipThreshold",IRIS26487_CLIP_THRESHOLD);
                    glProg.setVar("shortClipThreshold",IRIS26487_CLIP_THRESHOLD);
                    /* IRIS_26497_SHORT_CORRESPONDENCE_HOST
                     * Keep the proven variation floor, but the shader now interprets
                     * mfsr_flow_expand.w correctly: interpolation cancellation preserves
                     * the whole base tile vector and is not itself an invalid warp.
                     * Structured clipped sites receive a bounded local correspondence
                     * refinement before any short sample can become color authority.
                     */
                    glProg.setVar("minimumFlowConfidence",0.30f);
                    glProg.setVar("referenceExposureScale",iris26487ReferenceExposureScale);
                    glProg.setTexture("normalCfa",imageOutput);
                    /* IRIS_26498_V13_SHORT_REFERENCE_OWNS_CORRESPONDENCE; merged CFA owns need/target. */
                    glProg.setTexture("referenceCfa",referenceCfa);
                    glProg.setTexture("shortCfa",iris26480ShortCfa);
                    glProg.setTexture("flowTexture",iris26480ShortAlignment.flowTexture);
                    glProg.setTextureCompute("outCfa",iris26480Recovered,true);
                    glProg.setTextureCompute("outProvenance",iris26492RecoveredProvenance,true);
                    glProg.setBufferCompute("ShortDiagBuf", iris26496ShortDiag);
                    glProg.computeAutoDeferred(rawHalf,1);

                    /* IRIS_26501_SHORT_A_SEMANTIC_CONTRIBUTION
                     * Existing Short-A validation produces the admission mask; the actual camera
                     * color comes directly from the aligned native short RAW through the same
                     * G/R-G/B-G semantic path as normal frames.
                     */
                    iris26501ShortWeight=new GLTexture(
                            rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),
                            null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);
                    glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_short_weight_26501",true);
                    glProg.setVar("packedSize",rawHalf);
                    glProg.setTexture("highlightProvenance",iris26492RecoveredProvenance);
                    glProg.setTextureCompute("outWeight",iris26501ShortWeight,true);
                    glProg.computeAutoDeferred(rawHalf,1);
                    iris26501ContributeRgbFrame(
                            glProg,iris26501RgbFramebuffer,raw,rawHalf,
                            iris26480ShortRaw,iris26501ChromaGuideScratch,
                            iris26480ShortAlignment.flowTexture,iris26501ShortWeight,iris26501ShortCov,
                            iris26501ShortWeight,
                            (int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,
                            iris26490ShortAlignmentScale,r,b,
                            iris26501ShortWbNoise[1],iris26501ShortWbNoise[4],
                            false,false,true);
                    iris26501SemanticHdrContributedFrames++;
                    iris26480ReadbackOutput=iris26480Recovered;
                    iris26492ReadbackProvenance=iris26492RecoveredProvenance;
                    parameters.motionV2ShortHighlightRecoveryExecuted = true;
                    Log.d(TAG,"IRIS_26490_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY"
                            +" shortToNormalScale="+shortToNormalScale
                            +" shortAlignmentScale="+iris26490ShortAlignmentScale
                            +" shortAlignmentRadiometricallyNormalized=true"
                            +" referenceExposureScale="+iris26487ReferenceExposureScale
                            +" shortWhiteLevel="+iris26490ShortWhite
                            +" normalWhiteLevel="+parameters.whiteLevel
                            +" shortBlack="+java.util.Arrays.toString(iris26490ShortBlack)
                            +" normalBlack="+java.util.Arrays.toString(blackLevel)
                            +" timestamp="+shortHighlightFrame.timestamp
                            +" shortExcludedFromNormalAccumulator=true"
                            +" shortExtendedRadianceState=true"
                            +" recoveredBeforeDemosaic=true rgbRepair=false"
                            +" interpolationCancelMeansBaseFlow=true"
                            +" localCorrespondenceRefine=3x3HalfPacked"
                            +" structuredUniqueMatchRequired=true");

                }

                if (directBayer) {
                    /* IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION
                     * Normal equal-exposure frames already live in the semantic accumulators.
                     * The helper fused/recovered Bayer carrier is now brightness/provenance only:
                     * it can provide a neutral value when physical colour is censored, but it can
                     * never become ordinary RGB/chroma authority.
                     */
                    if (iris26501SemanticAccumulator == null
                            || iris26501OpponentWeightAccumulator == null
                            || iris26492ReadbackProvenance == null
                            || iris26480ReadbackOutput == null) {
                        throw new IllegalStateException(
                                "26501 proper Spatial RGB finalization is missing an owner");
                    }
                    boolean iris26501HasLsc = parameters.hasGainMap
                            && parameters.mapSize != null
                            && parameters.mapSize.x > 0
                            && parameters.mapSize.y > 0
                            && parameters.gainMap != null
                            && parameters.gainMap.length
                                    >= parameters.mapSize.x * parameters.mapSize.y * 4;
                    Point iris26501LscSize = iris26501HasLsc
                            ? new Point(parameters.mapSize) : new Point(1, 1);
                    float[] iris26501LscValues = iris26501HasLsc
                            ? parameters.gainMap : new float[]{1f, 1f, 1f, 1f};
                    int iris26501LscFloatCount = iris26501LscSize.x * iris26501LscSize.y * 4;
                    ByteBuffer iris26501LscUpload = ByteBuffer
                            .allocateDirect(iris26501LscFloatCount * Float.BYTES)
                            .order(ByteOrder.nativeOrder());
                    iris26501LscUpload.asFloatBuffer().put(
                            iris26501LscValues, 0, iris26501LscFloatCount);
                    iris26501LscUpload.position(0);
                    iris26501LensShading = new GLTexture(
                            iris26501LscSize, new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                            iris26501LscUpload, GL_LINEAR, GL_CLAMP_TO_EDGE);

                    iris26501RgbOutput = new GLTexture(
                            raw, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                    glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_normalize_26501");
                    glProg.setVar("rawSize", raw);
                    glProg.setVar("packedSize", rawHalf);
                    glProg.setVar(
                            "cameraDomainScale",
                            1.0f / Math.max(wronskiGlobalWbR, 1.0e-6f),
                            1.0f,
                            1.0f / Math.max(wronskiGlobalWbB, 1.0e-6f));
                    glProg.setVar("useLensShading", iris26501HasLsc ? 1 : 0);
                    glProg.setTexture("semanticAccumulator", iris26501SemanticAccumulator);
                    glProg.setTexture(
                            "opponentWeightAccumulator", iris26501OpponentWeightAccumulator);
                    glProg.setTexture("fallbackCfa", iris26480ReadbackOutput);
                    glProg.setTexture("highlightProvenance", iris26492ReadbackProvenance);
                    glProg.setTexture("lensShadingMap", iris26501LensShading);
                    android.opengl.GLES30.glDisable(android.opengl.GLES30.GL_BLEND);
                    iris26501RgbOutput.BufferLoad();
                    glProg.drawBlocks(raw.x, raw.y);
                    android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
                    iris26480ReadbackOutput = iris26501RgbOutput;
                    Log.i(TAG, "IRIS_26502_STACK_AWARE_RGB_OUTPUT"
                            + " semanticFrames=" + iris26501SemanticContributedFrames
                            + " normalizeCount=1"
                            + " fullResolution=" + raw.x + "x" + raw.y
                            + " lensShadingAfterRgb=" + iris26501HasLsc
                            + " calculationWbRemovedExactlyOnce=true"
                            + " helperBayerColorAuthority=false"
                            + " semanticHdrContributions=" + iris26501SemanticHdrContributedFrames
                            + " shortValidatedColorFromNativeRaw="
                            + parameters.motionV2ShortHighlightRecoveryExecuted);
                    try {
                        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                "IRIS_26502_STACK_AWARE_RGB_OUTPUT",
                                "semanticFrames=" + iris26501SemanticContributedFrames
                                        + " normalizeCount=1"
                                        + " fullRes=true"
                                        + " lscAfterRgb=" + iris26501HasLsc
                                        + " helperBayerColorAuthority=false"
                                        + " semanticHdrContributions=" + iris26501SemanticHdrContributedFrames);
                    } catch (Throwable ignored) {}
                }
                /* IRIS_26488_TINY_DIAGNOSTICS_BEFORE_SINGLE_GPU_DRAIN
                 * Queue the coarse support/semantic-denominator diagnostic BEFORE the existing
                 * single Motion ownership drain. It is read only after that same drain, so 26488
                 * preserves one glFinish per photo instead of adding a second diagnostic stall.
                 */
                try {
                    iris26487DiagTexture = new GLTexture(
                            iris26487DiagSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26488DenominatorDiagTexture = new GLTexture(
                            iris26487DiagSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);
                    glProg.useAssetProgram("motionv2/mfsr_26489_bayer_diag_sample",true);
                    glProg.setVar("packedSize",rawHalf);
                    glProg.setVar("diagSize",iris26487DiagSize);
                    glProg.setTexture("frameSupport",currentDirectFrameSupport);
                    glProg.setTexture("denominator",currentDirectSupport);
                    glProg.setTextureCompute("outSupportDiag",iris26487DiagTexture,true);
                    glProg.setTextureCompute("outDenominatorDiag",iris26488DenominatorDiagTexture,true);
                    glProg.computeAutoDeferred(iris26487DiagSize,1);
                } catch (Throwable diagnosticDispatchError) {
                    Log.w(TAG,"IRIS_26488_V4_COARSE_DIAGNOSTIC_DISPATCH_SKIPPED",diagnosticDispatchError);
                    iris26488CloseDiagnosticTexture(iris26488DenominatorDiagTexture);
                    iris26488CloseDiagnosticTexture(iris26487DiagTexture);
                    iris26488DenominatorDiagTexture = null; iris26487DiagTexture = null;
                }

                /* IRIS_26487_SINGLE_GPU_OWNERSHIP_DRAIN
                 * All Motion alignment/rejection/accumulation/diagnostic commands are ordered on
                 * one GLES context. Wait once, immediately before CPU ownership/readback.
                 */
                iris26487GpuDrainMs = glProg.finishDeferredCompute("MotionV2 final image");
                long iris26487ReadbackStartNs = System.nanoTime();
                try {
                    iris26480ReadbackOutput.BufferLoad();
                    output=iris26480ReadbackOutput.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_32,4),true);
                } finally {
                    iris26488ReleaseReadbackFramebuffer(iris26480ReadbackOutput);
                }
                iris26487OutputReadbackMs = (System.nanoTime()-iris26487ReadbackStartNs)/1000000L;
                if (irisV13ShadowDiag != null) {
                    try {
                        int[] sd=irisV13ShadowDiag.readBufferIntegers(false);
                        if(sd!=null&&sd.length>=20){
                            Log.i(TAG,"IRIS_26498_V13_SHADOW_AUX_RESULT"
                                    +" shadowAuxCandidatePixels="+Integer.toUnsignedLong(sd[0])
                                    +" shadowAuxLowSignalCandidates="+Integer.toUnsignedLong(sd[1])
                                    +" shadowAuxCorrespondencePassed="+Integer.toUnsignedLong(sd[2])
                                    +" shadowAuxMotionRejected="+Integer.toUnsignedLong(sd[3])
                                    +" shadowAuxSaturationRejected="+Integer.toUnsignedLong(sd[4])
                                    +" shadowAuxContributedPixels="+Integer.toUnsignedLong(sd[5])
                                    +" outOfBounds="+Integer.toUnsignedLong(sd[6])
                                    +" correspondenceRejected="+Integer.toUnsignedLong(sd[7])
                                    +" radiometryRejected="+Integer.toUnsignedLong(sd[8])
                                    +" supportSnrRejected="+Integer.toUnsignedLong(sd[9])
                                    +" supportLe1="+Integer.toUnsignedLong(sd[10])
                                    +" support2to4="+Integer.toUnsignedLong(sd[11])
                                    +" supportGt4="+Integer.toUnsignedLong(sd[12])+" packsWithFusion="+Integer.toUnsignedLong(sd[13])
                                    +" fusedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(sd,16,20))
                                    +" shadowAuxAlignMs="+irisV13ShadowAlignDispatchMs
                                    +" shadowAuxFuseMs="+irisV13ShadowFuseDispatchMs
                                +" shadowAuxTotalMs="+(irisV13ShadowAlignDispatchMs+irisV13ShadowFuseDispatchMs)
                                    +" oneGpuDrain=true");
                        }
                    } catch(Throwable shadowDiagError){Log.w(TAG,"IRIS_26498_V13_SHADOW_DIAG_SKIPPED",shadowDiagError);}
                }
                if (iris26496ShortDiag != null) {
                    try {
                        int[] d = iris26496ShortDiag.readBufferIntegers(false);
                        if (d != null && d.length >= 44) {
                            long total = Integer.toUnsignedLong(d[0]);
                            long safe = Integer.toUnsignedLong(d[1]);
                            long shortClipped = Integer.toUnsignedLong(d[2]);
                            long flowRejected = Integer.toUnsignedLong(d[3]);
                            long correspondenceRejected = Integer.toUnsignedLong(d[4]);
                            long radiometryRejected = Integer.toUnsignedLong(d[5]);
                            long validated = Integer.toUnsignedLong(d[6]);
                            long stillCensored = Integer.toUnsignedLong(d[7]);
                            float coverage = total > 0L ? validated / (float) total : 0.0f;
                            Log.d(TAG, "IRIS_26496_SHORT_FAILURE_REASONS"
                                    + " totalNormalClipped=" + total
                                    + " shortSafeCandidate=" + safe
                                    + " shortPhysicallyClipped=" + shortClipped
                                    + " flowRejected=" + flowRejected
                                    + " correspondenceRejected=" + correspondenceRejected
                                    + " radiometryRejected=" + radiometryRejected
                                    + " shortValidated=" + validated
                                    + " stillCensored=" + stillCensored
                                    + " recoveryCoverage=" + coverage
                                    + " shortValueBinsLt50_50to70_70to85_85to95_95toClip="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 8, 13))
                                    + " clippedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 16, 20))
                                    + " validatedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 20, 24))
                                    + " shortClippedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 24, 28))
                                    + " flowRejectedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 28, 32))
                                    + " correspondenceRejectedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 32, 36))
                                    + " radiometryRejectedByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 36, 40))
                                    + " stillCensoredByPhase="
                                    + java.util.Arrays.toString(java.util.Arrays.copyOfRange(d, 40, 44))
                                    + " imageMathUnchangedByTelemetry=true"
                                    + " oneGpuDrain=true");
                            if (total != validated + stillCensored) {
                                Log.w(TAG, "IRIS_26496_SHORT_DIAGNOSTIC_ACCOUNTING_MISMATCH"
                                        + " total=" + total
                                        + " validatedPlusStill=" + (validated + stillCensored));
                            }
                            try {
                                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                        "IRIS_26496_SHORT_FAILURE_REASONS",
                                        "total=" + total
                                                + " shortClipped=" + shortClipped
                                                + " flowRejected=" + flowRejected
                                                + " corrRejected=" + correspondenceRejected
                                                + " radiometryRejected=" + radiometryRejected
                                                + " validated=" + validated
                                                + " stillCensored=" + stillCensored
                                                + " coverage=" + coverage);
                            } catch (Throwable ignored) {}
                        }
                    } catch (Throwable shortDiagError) {
                        Log.w(TAG, "IRIS_26496_SHORT_DIAGNOSTIC_READBACK_SKIPPED", shortDiagError);
                    }
                }
                if (directBayer && iris26492ReadbackProvenance != null) {
                    try {
                        iris26492ReadbackProvenance.BufferLoad();
                        highlightProvenanceOutput = iris26492ReadbackProvenance.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 1), true);
                    } finally {
                        iris26488ReleaseReadbackFramebuffer(iris26492ReadbackProvenance);
                    }
                    int normalPhases = 0, censoredPhases = 0, shortPhases = 0, invalidPhases = 0;
                    int[] censoredByPackedPhase = new int[4];
                    int[] shortByPackedPhase = new int[4];
                    int[] affectedPackHistogram = new int[5];
                    int packsWithShort = 0;
                    ByteBuffer provenanceView = highlightProvenanceOutput.duplicate()
                            .order(ByteOrder.nativeOrder());
                    provenanceView.position(0);
                    while (provenanceView.remaining() >= Float.BYTES) {
                        float encoded = provenanceView.getFloat();
                        int code = Math.round(encoded);
                        if (!Float.isFinite(encoded) || Math.abs(encoded - code) > 0.01f
                                || code < 0 || code > 80) {
                            invalidPhases += 4;
                            continue;
                        }
                        int affected = 0;
                        boolean anyShort = false;
                        int remaining = code;
                        for (int phase = 0; phase < 4; ++phase) {
                            int state = remaining % 3;
                            remaining /= 3;
                            if (state == 0) {
                                normalPhases++;
                            } else if (state == 1) {
                                censoredPhases++; censoredByPackedPhase[phase]++; affected++;
                            } else {
                                shortPhases++; shortByPackedPhase[phase]++; affected++; anyShort = true;
                            }
                        }
                        affectedPackHistogram[affected]++;
                        if (anyShort) packsWithShort++;
                    }
                    Log.d(TAG, "IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE"
                            + " encoding=R32F_BASE3_PHASES"
                            + " normalPhases=" + normalPhases
                            + " censoredPhases=" + censoredPhases
                            + " shortValidatedPhases=" + shortPhases
                            + " invalidPhases=" + invalidPhases
                            + " censoredByPackedPhase=" + java.util.Arrays.toString(censoredByPackedPhase)
                            + " shortByPackedPhase=" + java.util.Arrays.toString(shortByPackedPhase)
                            + " affectedPackHistogram0to4=" + java.util.Arrays.toString(affectedPackHistogram)
                            + " packsWithShort=" + packsWithShort
                            + " extraFullFrameCarrier=false"
                            + " oneGpuDrain=true");
                    try {
                        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                "IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE",
                                "normalPhases=" + normalPhases
                                        + " censoredPhases=" + censoredPhases
                                        + " shortPhases=" + shortPhases
                                        + " invalidPhases=" + invalidPhases
                                        + " affectedPacks0to4=" + java.util.Arrays.toString(affectedPackHistogram));
                    } catch (Throwable ignored) {}
                }
                if (iris26488StageDiagA != null) {
                    try {
                        float[] stageA = iris26488ReadDiagnosticFloatRgba(iris26488StageDiagA);
                        float[] stageB = iris26488ReadDiagnosticFloatRgba(iris26488StageDiagB);
                        float[] stageC = iris26488ReadDiagnosticFloatRgba(iris26488StageDiagC);
                        iris26488LogStageDiagnostics(stageA,stageB,stageC,iris26488StageDiagSize,Math.max(0,frameCount-1));
                    } catch (Throwable diagnosticReadbackError) {
                        Log.w(TAG,"IRIS_26488_V4_STAGE_DIAGNOSTIC_READBACK_SKIPPED",diagnosticReadbackError);
                    }
                }
            }finally{
                if(iris26480ShortAlignment!=null)iris26480ShortAlignment.close();if(iris26480ShortWbCfa!=null)iris26480ShortWbCfa.close();
                if(iris26501ShortWeight!=null)iris26501ShortWeight.close();if(iris26501ShortCov!=null)iris26501ShortCov.close();
                if(iris26501ShadowWeight!=null)iris26501ShadowWeight.close();if(iris26501ShadowCov!=null)iris26501ShadowCov.close();
                if(iris26480ShortCfa!=null)iris26480ShortCfa.close();if(iris26480ShortRaw!=null)iris26480ShortRaw.close();
                if(iris26480Recovered!=null)iris26480Recovered.close();
                if(irisV13ShadowAlignment!=null)irisV13ShadowAlignment.close();if(irisV13ShadowWbCfa!=null)irisV13ShadowWbCfa.close();
                if(irisV13ShadowCfa!=null)irisV13ShadowCfa.close();if(irisV13ShadowRaw!=null)irisV13ShadowRaw.close();
                if(irisV13ShadowRecovered!=null)irisV13ShadowRecovered.close();if(irisV13ShadowDiag!=null)irisV13ShadowDiag.close();
                /* IRIS_26498_V13_TAKEN_AUX_CPU_BUFFER_LIFETIME_FIX */
                if(shortHighlightFrame!=null)try{shortHighlightFrame.close();}catch(Throwable ignored){}
                if(irisV13ShadowAuxFrame!=null)try{irisV13ShadowAuxFrame.close();}catch(Throwable ignored){}
                if(iris26496ShortDiag!=null)iris26496ShortDiag.close();
                if(iris26492RecoveredProvenance!=null)iris26492RecoveredProvenance.close();
                if(iris26492BaseProvenance!=null)iris26492BaseProvenance.close();
            }

            Log.d(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE"
                    + " sourceInternal=rgba16f"
                    + " transfer=rgba32f"
                    + " bytesPerChannel=4"
                    + " glType=GL_FLOAT"
                    + " size=" + raw.x + "x" + raw.y
                    + " raw16Repack=false"
                    + " finalFloat16Storage=true"
                    + " legacyMerge00=false"
                    + " directMultiframeRgb=" + directBayer
                    + " helperFusedBayerCanonical=" + directBayer
                    + " helperBayerColorAuthority=false"
                    + " semanticAccumulator=2xRGBA16F_additive"
                    + " semanticFrames=" + iris26501SemanticContributedFrames
                    + " semanticHdrFrames=" + iris26501SemanticHdrContributedFrames
                    + " divideOnceAfterBurst=" + directBayer
                    + " perFrameCovariance=" + directBayer
                    + " perFrameRgbEvidence=" + directBayer
                    + " anisotropicKernel=true"
                    + " postSnrChromaErase=false"
                    + " lensShadingAfterRgb=true"
                    + " calculationWbRemovedExactlyOnce=true"
                    + " chromaEdgeNoiseSigmas=2.5"
                    + " chromaEdgeSigmaFloor=0.00625"
                    + " separateDemosaic=true"
                    + " hdrHeadroomPreserved=true");

            /*
             * IRIS_26426_DIRECT_RGB_CHANNEL_SUPPORT_TELEMETRY
             *
             * Diagnostic-only readback of the NEW direct RGB support carrier.
             * It does not feed image math. This tells us whether R/G/B are
             * actually receiving burst support in the difficult highlight/edge
             * pixels rather than relying on the legacy packed-CFA support map.
             */
            if (false && /* IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2 */ directBayer && currentDirectSupport != null) {
                currentDirectSupport.BufferLoad();
                ByteBuffer directSupportBytes =
                        currentDirectSupport.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                DirectRgbSupportSummary directSummary =
                        summarizeDirectRgbSupport(
                                directSupportBytes,
                                raw.x,
                                raw.y);
                Log.d(TAG, "IRIS_26426_DIRECT_RGB_SUPPORT"
                        + " meanRGB=" + directSummary.meanR + ","
                                + directSummary.meanG + ","
                                + directSummary.meanB
                        + " lowSupportRGB=" + directSummary.lowR + ","
                                + directSummary.lowG + ","
                                + directSummary.lowB
                        + " imbalanceP95=" + directSummary.imbalanceP95
                        + " sampledPixels=" + directSummary.samples
                        + " semanticChannels=G,RminusG,BminusG"
                        + " imageMathUnchangedByTelemetry=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26426_DIRECT_RGB_SUPPORT",
                            "meanR=" + directSummary.meanR
                                    + " meanG=" + directSummary.meanG
                                    + " meanB=" + directSummary.meanB
                                    + " lowR=" + directSummary.lowR
                                    + " lowG=" + directSummary.lowG
                                    + " lowB=" + directSummary.lowB
                                    + " imbalanceP95=" + directSummary.imbalanceP95
                                    + " samples=" + directSummary.samples);
                } catch (Throwable ignored) {}
            }

            /* IRIS_26488_COARSE_SUPPORT_AND_DENOMINATOR_TELEMETRY
             * Tiny 48x36 readback after the ONE final GPU drain. The diagnostic dispatch was
             * queued before that drain, so telemetry adds no second glFinish. Support and semantic
             * denominators are measured independently and no full-resolution readback is restored.
             */
            float[] iris26488FallbackSupportGrid = new float[iris26487DiagSize.x * iris26487DiagSize.y];
            java.util.Arrays.fill(iris26488FallbackSupportGrid, 1.0f);
            SupportSummary summary = new SupportSummary(1.0f,1.0f,1.0f,1.0f,
                    iris26488FallbackSupportGrid,iris26487DiagSize.x,iris26487DiagSize.y);
            try {
                if (iris26487DiagTexture == null || iris26488DenominatorDiagTexture == null)
                    throw new IllegalStateException("coarse diagnostics unavailable");
                long diagReadStart=System.nanoTime();
                float[] supportValues=iris26488ReadDiagnosticFloatRgba(iris26487DiagTexture);
                float[] denominatorValues=iris26488ReadDiagnosticFloatRgba(iris26488DenominatorDiagTexture);
                long diagReadMs=(System.nanoTime()-diagReadStart)/1000000L;
                summary=iris26487SummarizeCoarseDiag(supportValues,frameCount,iris26487DiagSize.x,iris26487DiagSize.y);
                float minPhaseSupport=0f,maxPhaseSupport=0f,denP0=0f,denP1=0f,denP2=0f,denP3=0f;int n=0;
                for(int k=0;k+3<supportValues.length&&k+3<denominatorValues.length;k+=4){
                    minPhaseSupport+=supportValues[k+1];maxPhaseSupport+=supportValues[k+2];
                    denP0+=denominatorValues[k];denP1+=denominatorValues[k+1];
                    denP2+=denominatorValues[k+2];denP3+=denominatorValues[k+3];n++;
                }
                if(n>0){minPhaseSupport/=n;maxPhaseSupport/=n;denP0/=n;denP1/=n;denP2/=n;denP3/=n;}
                Log.d(TAG,"IRIS_26489_BAYER_RECON_DIAGNOSTICS sampledMeanSupport="+summary.mean
                        +" minPhaseSupport="+minPhaseSupport+" maxPhaseSupport="+maxPhaseSupport
                        +" denominatorPhases="+denP0+","+denP1+","+denP2+","+denP3
                        +" admittedFrames="+iris26489AdmittedFrames
                        +" contributedFrames="+iris26489ContributedFrames
                        +" grid=48x36 readbackMs="+diagReadMs
                        +" fullResolutionReadback=false");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26489_BAYER_RECON_DIAGNOSTICS",
                            "sampledMeanSupport="+summary.mean+" minPhaseSupport="+minPhaseSupport
                                    +" maxPhaseSupport="+maxPhaseSupport+" denominatorPhases="
                                    +denP0+","+denP1+","+denP2+","+denP3
                                    +" admitted="+iris26489AdmittedFrames+" contributed="+iris26489ContributedFrames
                                    +" grid=48x36 readbackMs="+diagReadMs);
                } catch(Throwable ignored) {}
            } catch (Throwable diagnosticReadbackError) {
                Log.w(TAG,"IRIS_26488_V4_COARSE_DIAGNOSTIC_READBACK_SKIPPED referenceOnlyTelemetry=true",diagnosticReadbackError);
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26488_RECON_DIAGNOSTICS",
                            "telemetryUnavailable=true referenceOnlyFallback=true imageMathUnchanged=true");
                } catch(Throwable ignored) {}
            } finally {
                iris26488CloseDiagnosticTexture(iris26488DenominatorDiagTexture);
                iris26488CloseDiagnosticTexture(iris26487DiagTexture);
            }

            effectiveSupport = summary.mean;
            supportP10 = summary.p10;
            supportP50 = summary.p50;
            supportP90 = summary.p90;

            MotionMetrics.publishV2Support(
                    effectiveSupport,
                    summary.coarseGrid,
                    summary.gridWidth,
                    summary.gridHeight);
            long iris26487ReconstructionWallMs=(System.nanoTime()-iris26487RunStartNs)/1000000L;
            Log.d(TAG,"IRIS_26487_PROCESSING_BUDGET"
                    +" attemptedFrames="+frameCount
                    +" effectiveSupport="+effectiveSupport
                    +" reconstructionWallMs="+iris26487ReconstructionWallMs
                    +" gpuDrainMs="+iris26487GpuDrainMs
                    +" outputReadbackMs="+iris26487OutputReadbackMs
                    +" targetMs=5000"
                    +" targetMet="+(iris26487ReconstructionWallMs<=5000L)
                    +" preShutterBatch=true"
                    +" noNormalTopUpWait=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26487_PROCESSING_BUDGET",
                        "attemptedFrames="+frameCount
                                +" effectiveSupport="+effectiveSupport
                                +" reconstructionWallMs="+iris26487ReconstructionWallMs
                                +" gpuDrainMs="+iris26487GpuDrainMs
                                +" outputReadbackMs="+iris26487OutputReadbackMs
                                +" targetMs=5000 targetMet="+(iris26487ReconstructionWallMs<=5000L));
            } catch(Throwable ignored) {}

            /*
             * IRIS_26436_PERMANENT_SPATIAL_SUPPORT_TELEMETRY
             * Logging only; never participates in reconstruction.
             */
            StringBuilder supportGrid12x8 = new StringBuilder();
            float supportRoughness = 0.0f;
            int supportRoughCount = 0;
            float iris26468StrongestSeamDelta = 0.0f;
            int iris26468SeamX = -1;
            int iris26468SeamY = -1;
            String iris26468SeamOrientation = "none";
            for (int y = 0; y < summary.gridHeight; y++) {
                for (int x = 0; x < summary.gridWidth; x++) {
                    int idx = y * summary.gridWidth + x;
                    float c = summary.coarseGrid[idx];
                    if (x + 1 < summary.gridWidth) {
                        float d = Math.abs(c - summary.coarseGrid[idx + 1]);
                        supportRoughness += d;
                        supportRoughCount++;
                        if (d > iris26468StrongestSeamDelta) {
                            iris26468StrongestSeamDelta = d;
                            iris26468SeamX = x;
                            iris26468SeamY = y;
                            iris26468SeamOrientation = "verticalBoundary";
                        }
                    }
                    if (y + 1 < summary.gridHeight) {
                        float d = Math.abs(
                                c - summary.coarseGrid[idx + summary.gridWidth]);
                        supportRoughness += d;
                        supportRoughCount++;
                        if (d > iris26468StrongestSeamDelta) {
                            iris26468StrongestSeamDelta = d;
                            iris26468SeamX = x;
                            iris26468SeamY = y;
                            iris26468SeamOrientation = "horizontalBoundary";
                        }
                    }
                }
            }
            supportRoughness = supportRoughCount > 0
                    ? supportRoughness / supportRoughCount
                    : 0.0f;
            for (int gy = 0; gy < 8; gy++) {
                if (gy > 0) supportGrid12x8.append('/');
                int sy = Math.min(
                        summary.gridHeight - 1,
                        (int)(((gy + 0.5f) * summary.gridHeight) / 8.0f));
                for (int gx = 0; gx < 12; gx++) {
                    int sx = Math.min(
                            summary.gridWidth - 1,
                            (int)(((gx + 0.5f) * summary.gridWidth) / 12.0f));
                    float value = summary.coarseGrid[
                            sy * summary.gridWidth + sx];
                    int code = Math.max(0, Math.min(
                            255,
                            Math.round(
                                    value / Math.max(1, frameCount)
                                            * 255.0f)));
                    if (code < 16) supportGrid12x8.append('0');
                    supportGrid12x8.append(Integer.toHexString(code));
                }
            }
            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");
            Log.d(TAG, "IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC"
                    + " strongestSupportDelta=" + iris26468StrongestSeamDelta
                    + " gridX=" + iris26468SeamX
                    + " gridY=" + iris26468SeamY
                    + " orientation=" + iris26468SeamOrientation
                    + " grid=" + summary.gridWidth + "x" + summary.gridHeight
                    + " geometryUnchanged=true");
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC",
                        "strongestSupportDelta=" + iris26468StrongestSeamDelta
                                + " gridX=" + iris26468SeamX
                                + " gridY=" + iris26468SeamY
                                + " orientation=" + iris26468SeamOrientation
                                + " geometryUnchanged=true");
            } catch (Throwable ignored) {}
            /* IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V2
             * The 26478 scene-specific CPU edge/color correlation is retired.
             * Existing support summary remains logging-only.
             */

            Log.d(TAG, "IRIS_26413_V2_CFA_RECONSTRUCTION"
                    + " referenceTimestamp=" + referenceTimestamp
                    + " retainedFrames=" + frameCount
                    + " effectiveSupport=" + effectiveSupport
                    + " supportP10=" + supportP10
                    + " supportP50=" + supportP50
                    + " supportP90=" + supportP90
                    + " allRetainedFramesConsidered=true"
                    + " referenceGeometryAuthoritative=true"
                    + " confidenceZeroReturnsReference=true"
                    + " sharedCfaFlow=true"
                    + " subpixelSampling=truePerObservationNormalizedConvolution"
                    + " directMultiframeRgb=" + directBayer
                    + " properPerFrameSpatialRgb=" + directBayer
                    + " helperFusedBayerOnly=" + directBayer
                    + " helperBayerColorAuthority=false"
                    + " semanticFrames=" + iris26501SemanticContributedFrames
                    + " semanticHdrFrames=" + iris26501SemanticHdrContributedFrames
                    + " legacyPyramidMerge=false"
                    + " legacyPyramidAlignment=false"
                    + " v2OwnedContinuousAlignment=true"
                    + " sharpening=false");

            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26413_MOTION_V2_CFA_RECONSTRUCTION",
                        "referenceTimestamp=" + referenceTimestamp
                                + " retained=" + frameCount
                                + " effectiveSupport=" + effectiveSupport
                                + " p10=" + supportP10
                                + " p50=" + supportP50
                                + " p90=" + supportP90
                                + " localSupportGrid="
                                + summary.gridWidth + "x" + summary.gridHeight
                                + " referenceOwned=true"
                                + " fractionalAlignment=true"
                                + " alignmentOwner=MotionV2"
                                + " legacyPyramidAlignment=false"
                                + " sharedFlow=true"
                                + " confidenceZeroReferenceFallback=true");
            } catch (Throwable ignored) {}
        } finally {
            /* IRIS_26501_PROPER_SPATIAL_RGB_LIFETIME_OWNER
             * Custom MRT framebuffer must be deleted as a framebuffer before its attached
             * textures are closed. BufferLoad-created framebuffers use the matching helper.
             */
            if (iris26501RgbFramebuffer != 0) {
                try {
                    android.opengl.GLES30.glDeleteFramebuffers(
                            1, new int[]{iris26501RgbFramebuffer}, 0);
                } catch (Throwable cleanupError) {
                    Log.w(TAG, "IRIS_26501_RGB_FBO_RELEASE_WARNING", cleanupError);
                }
                iris26501RgbFramebuffer = 0;
            }
            iris26488ReleaseReadbackFramebuffer(iris26501ChromaGuideScratch);
            iris26488ReleaseReadbackFramebuffer(iris26501RgbOutput);
            if (iris26501LensShading != null) iris26501LensShading.close();
            if (iris26501RgbOutput != null) iris26501RgbOutput.close();
            if (iris26501ChromaGuideScratch != null) iris26501ChromaGuideScratch.close();
            if (iris26501RgbCovScratch != null) iris26501RgbCovScratch.close();
            if (iris26501OpponentWeightAccumulator != null) iris26501OpponentWeightAccumulator.close();
            if (iris26501SemanticAccumulator != null) iris26501SemanticAccumulator.close();
            /* IRIS_26413 pack-fix: no temporary uint16 result texture is allocated. */
            if (directFrameSupportB != null) directFrameSupportB.close();
            if (directFrameSupportA != null) directFrameSupportA.close();
            if (directSupportB != null) directSupportB.close();
            if (directSupportA != null) directSupportA.close();
            if (directRgbB != null) directRgbB.close();
            if (directRgbA != null) directRgbA.close();
            if (supportB != null) supportB.close();
            if (supportA != null) supportA.close();
            if (mergedB != null) mergedB.close();
            if (mergedA != null) mergedA.close();
            iris26488CloseDiagnosticTexture(iris26488StageDiagC);
            iris26488CloseDiagnosticTexture(iris26488StageDiagB);
            iris26488CloseDiagnosticTexture(iris26488StageDiagA);
            if (iris26488LensShading != null) iris26488LensShading.close();
            if (iris26488ReferenceGray != null) iris26488ReferenceGray.close();
            if (wronskiReferenceGuide != null) wronskiReferenceGuide.close();
            if (wronskiReferenceCov != null) wronskiReferenceCov.close();
            if (wronskiReferenceChromaGuide != null) wronskiReferenceChromaGuide.close();
            if (wronskiPreparedAlignment != null) wronskiPreparedAlignment.close();
            if (wronskiReferenceCfa != null) wronskiReferenceCfa.close();
            if (referenceCfa != null) referenceCfa.close();
            if (referenceRaw != null) referenceRaw.close();
        }
    }

    /*
     * Only Camera2-declared defective sites are altered here. Coordinates from
     * STATISTICS_HOT_PIXEL_MAP are normally in sensor active-array space; map
     * through sensorPix when available and retain a direct-coordinate fallback
     * for HALs that already report RAW-buffer-relative points.
     */
    private static int correctKnownHotPixels(
            ByteBuffer buffer,
            int width,
            int height,
            Parameters parameters) {
        if (buffer == null || width <= 4 || height <= 4
                || parameters == null
                || parameters.hotPixels == null
                || parameters.hotPixels.length == 0) {
            return 0;
        }

        ByteBuffer view = buffer.duplicate().order(ByteOrder.nativeOrder());
        int sampleCapacity = view.capacity() / 2;
        int corrected = 0;

        for (Point hot : parameters.hotPixels) {
            if (hot == null) continue;

            int x = hot.x;
            int y = hot.y;

            if (parameters.sensorPix != null) {
                int translatedX = hot.x - parameters.sensorPix.left;
                int translatedY = hot.y - parameters.sensorPix.top;
                if (translatedX >= 0 && translatedX < width
                        && translatedY >= 0 && translatedY < height) {
                    x = translatedX;
                    y = translatedY;
                }
            }

            if (x < 0 || x >= width || y < 0 || y >= height) continue;

            int[] values = new int[4];
            int n = 0;
            int[][] offsets = new int[][]{
                    {-2, 0}, {2, 0}, {0, -2}, {0, 2}
            };

            for (int[] d : offsets) {
                int nx = x + d[0];
                int ny = y + d[1];
                if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
                int index = ny * width + nx;
                if (index < 0 || index >= sampleCapacity) continue;
                values[n++] = Short.toUnsignedInt(view.getShort(index * 2));
            }

            if (n < 2) continue;

            for (int i = 1; i < n; i++) {
                int v = values[i];
                int j = i - 1;
                while (j >= 0 && values[j] > v) {
                    values[j + 1] = values[j];
                    j--;
                }
                values[j + 1] = v;
            }

            int replacement = (n & 1) != 0
                    ? values[n / 2]
                    : (values[n / 2 - 1] + values[n / 2]) / 2;

            int target = y * width + x;
            if (target < 0 || target >= sampleCapacity) continue;
            view.putShort(target * 2, (short)(replacement & 0xffff));
            corrected++;
        }
        return corrected;
    }
    /*
     * IRIS_26440_DIAGNOSTIC_HELPERS
     * No method below feeds reconstruction/image math.
     */
    private static float[] iris26440CopyFloatBuffer(ByteBuffer bytes) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();
        float[] out = new float[values.capacity()];
        for (int i = 0; i < out.length; i++) {
            float v = values.get(i);
            out[i] = Float.isFinite(v) ? v : 0.0f;
        }
        return out;
    }

    private static int iris26440AgeBin(float ageMs) {
        if (ageMs < 50.0f) return 0;
        if (ageMs < 120.0f) return 1;
        if (ageMs < 200.0f) return 2;
        return 3;
    }

    private static String iris26440AgeBinName(float ageMs) {
        int bin = iris26440AgeBin(ageMs);
        if (bin == 0) return "lt50";
        if (bin == 1) return "50to120";
        if (bin == 2) return "120to200";
        return "gt200";
    }

    private static String iris26440FormatGrid(float[] grid) {
        if (grid == null) return "null";
        StringBuilder sb = new StringBuilder(grid.length * 7);
        for (int i = 0; i < grid.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(String.format(java.util.Locale.US, "%.3f", grid[i]));
        }
        return sb.toString();
    }

    private static final class Iris26440ReferenceSummary {
        final float meanR;
        final float meanG;
        final float meanB;
        final float fallbackR;
        final float fallbackG;
        final float fallbackB;
        final float[] fallbackRbGrid;

        Iris26440ReferenceSummary(
                float meanR,
                float meanG,
                float meanB,
                float fallbackR,
                float fallbackG,
                float fallbackB,
                float[] fallbackRbGrid) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.fallbackR = fallbackR;
            this.fallbackG = fallbackG;
            this.fallbackB = fallbackB;
            this.fallbackRbGrid = fallbackRbGrid;
        }
    }

    private static Iris26440ReferenceSummary iris26440SummarizeReferenceSupport(
            float[] support,
            int width,
            int height,
            int gridW,
            int gridH) {
        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        long fallbackR = 0L;
        long fallbackG = 0L;
        long fallbackB = 0L;
        long count = 0L;
        double[] gridFallback = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];

        int pixels = Math.min(width * height, support.length / 4);
        for (int p = 0; p < pixels; p++) {
            float r = Math.max(0.0f, support[4 * p]);
            float g = Math.max(0.0f, support[4 * p + 1]);
            float b = Math.max(0.0f, support[4 * p + 2]);
            boolean fr = r <= 0.00015f;
            boolean fg = g <= 0.00015f;
            boolean fb = b <= 0.00015f;
            sumR += r;
            sumG += g;
            sumB += b;
            if (fr) fallbackR++;
            if (fg) fallbackG++;
            if (fb) fallbackB++;
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            if (fr || fb) gridFallback[gi] += 1.0;
            gridCount[gi]++;
            count++;
        }

        float[] grid = new float[gridFallback.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridFallback[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1L, count);
        return new Iris26440ReferenceSummary(
                (float) (sumR / denom),
                (float) (sumG / denom),
                (float) (sumB / denom),
                fallbackR / (float) denom,
                fallbackG / (float) denom,
                fallbackB / (float) denom,
                grid);
    }

    private static final class Iris26440ClipSummary {
        final float c0;
        final float c1;
        final float c2;
        final float c3;
        final float[] anyClipGrid;

        Iris26440ClipSummary(
                float c0,
                float c1,
                float c2,
                float c3,
                float[] anyClipGrid) {
            this.c0 = c0;
            this.c1 = c1;
            this.c2 = c2;
            this.c3 = c3;
            this.anyClipGrid = anyClipGrid;
        }
    }

    private static Iris26440ClipSummary iris26440SummarizeReferenceClip(
            ByteBuffer bytes,
            int width,
            int height,
            float clip,
            int gridW,
            int gridH) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer v = bytes.asFloatBuffer();
        int pixels = Math.min(width * height, v.capacity() / 4);
        long[] clipped = new long[4];
        double[] gridClip = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];
        float threshold = 0.93f * Math.max(clip, 1.0e-6f);

        for (int p = 0; p < pixels; p++) {
            boolean any = false;
            for (int c = 0; c < 4; c++) {
                float value = v.get(4 * p + c);
                if (Float.isFinite(value) && value >= threshold) {
                    clipped[c]++;
                    any = true;
                }
            }
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            if (any) gridClip[gi] += 1.0;
            gridCount[gi]++;
        }

        float[] grid = new float[gridClip.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridClip[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1, pixels);
        return new Iris26440ClipSummary(
                clipped[0] / denom,
                clipped[1] / denom,
                clipped[2] / denom,
                clipped[3] / denom,
                grid);
    }

    private static final class Iris26440FrameDelta {
        final float meanR;
        final float meanG;
        final float meanB;
        final float positiveFraction;
        final float[] grid;

        Iris26440FrameDelta(
                float meanR,
                float meanG,
                float meanB,
                float positiveFraction,
                float[] grid) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.positiveFraction = positiveFraction;
            this.grid = grid;
        }
    }

    private static Iris26440FrameDelta iris26440SummarizeFrameDelta(
            float[] before,
            float[] after,
            int width,
            int height,
            float ageMs,
            int gridW,
            int gridH) {
        int floats = Math.min(before.length, after.length);
        int pixels = Math.min(width * height, floats / 4);
        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        long positive = 0L;
        double[] gridSum = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];

        for (int p = 0; p < pixels; p++) {
            float dr = Math.max(0.0f, after[4 * p] - before[4 * p]);
            float dg = Math.max(0.0f, after[4 * p + 1] - before[4 * p + 1]);
            float db = Math.max(0.0f, after[4 * p + 2] - before[4 * p + 2]);
            float d = (dr + dg + db) / 3.0f;
            sumR += dr;
            sumG += dg;
            sumB += db;
            if (d > 1.0e-5f) positive++;
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            gridSum[gi] += d;
            gridCount[gi]++;
        }

        float[] grid = new float[gridSum.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridSum[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1, pixels);
        return new Iris26440FrameDelta(
                (float) (sumR / denom),
                (float) (sumG / denom),
                (float) (sumB / denom),
                positive / denom,
                grid);
    }

    private static final class Iris26440TemporalSummary {
        private final double[][] gridSum;
        private final int[] frameCount;
        private final double[][] rgbSum;
        private final int gridSize;

        Iris26440TemporalSummary(int gridW, int gridH) {
            gridSize = gridW * gridH;
            gridSum = new double[4][gridSize];
            frameCount = new int[4];
            rgbSum = new double[4][3];
        }

        void add(float ageMs, Iris26440FrameDelta delta) {
            int bin = iris26440AgeBin(ageMs);
            frameCount[bin]++;
            rgbSum[bin][0] += delta.meanR;
            rgbSum[bin][1] += delta.meanG;
            rgbSum[bin][2] += delta.meanB;
            for (int i = 0; i < gridSize && i < delta.grid.length; i++) {
                gridSum[bin][i] += delta.grid[i];
            }
        }

        String meanRgb(int bin) {
            int n = Math.max(1, frameCount[bin]);
            return String.format(
                    java.util.Locale.US,
                    "%.5f,%.5f,%.5f",
                    rgbSum[bin][0] / n,
                    rgbSum[bin][1] / n,
                    rgbSum[bin][2] / n);
        }

        float[] grid(int bin) {
            float[] out = new float[gridSize];
            int n = Math.max(1, frameCount[bin]);
            for (int i = 0; i < gridSize; i++) {
                out[i] = (float) (gridSum[bin][i] / n);
            }
            return out;
        }
    }

    /* IRIS_26488_STAGE_REJECTION_DIAGNOSTICS
     * One tiny atlas readback after the final GPU drain. No values feed image math.
     */
    private static void iris26488LogStageDiagnostics(
            float[] stageA,
            float[] stageB,
            float[] stageC,
            Point diagSize,
            int auxiliaryCount) {
        if (stageA == null || stageB == null || stageC == null
                || diagSize == null || diagSize.x <= 0 || diagSize.y <= 0
                || auxiliaryCount <= 0) {
            return;
        }
        final int cells = diagSize.x * diagSize.y;
        final int stride = cells * 4;
        double aggregateWeight = 0.0;
        double aggregateClipAny = 0.0;
        int aggregateSamples = 0;
        for (int frame = 0; frame < auxiliaryCount; frame++) {
            final int base = frame * stride;
            if (base + stride > stageA.length
                    || base + stride > stageB.length
                    || base + stride > stageC.length) {
                break;
            }
            double flowVar=0.0,cancel=0.0,unblock=0.0,reverse=0.0;
            double pixelDifference=0.0,postRejection=0.0,baseAccept=0.0;
            double clipR=0.0,clipG=0.0,clipB=0.0,clipAny=0.0;
            float[] finalWeights = new float[cells];
            int n=0;
            for (int cell=0; cell<cells; cell++) {
                int k=base+4*cell;
                float fv=stageA[k], ca=stageA[k+1], ub=stageA[k+2], rv=stageA[k+3];
                float pd=stageB[k], pr=stageB[k+1], fw=stageB[k+2], ba=stageB[k+3];
                float cr=stageC[k], cg=stageC[k+1], cb=stageC[k+2], cc=stageC[k+3];
                if (!Float.isFinite(fv)||!Float.isFinite(ca)||!Float.isFinite(ub)||!Float.isFinite(rv)
                        ||!Float.isFinite(pd)||!Float.isFinite(pr)||!Float.isFinite(fw)||!Float.isFinite(ba)
                        ||!Float.isFinite(cr)||!Float.isFinite(cg)||!Float.isFinite(cb)||!Float.isFinite(cc)) {
                    continue;
                }
                flowVar+=fv; cancel+=ca; unblock+=ub; reverse+=rv;
                pixelDifference+=pd; postRejection+=pr; baseAccept+=ba;
                clipR+=cr; clipG+=cg; clipB+=cb; clipAny+=cc;
                finalWeights[n++]=Math.max(0.0f,Math.min(1.0f,fw));
            }
            if (n<=0) continue;
            java.util.Arrays.sort(finalWeights,0,n);
            float p10=finalWeights[Math.min(n-1,Math.max(0,Math.round(0.10f*(n-1))))];
            float p50=finalWeights[Math.min(n-1,Math.max(0,Math.round(0.50f*(n-1))))];
            float p90=finalWeights[Math.min(n-1,Math.max(0,Math.round(0.90f*(n-1))))];
            double meanWeight=0.0;
            for(int i=0;i<n;i++)meanWeight+=finalWeights[i];
            meanWeight/=n;
            aggregateWeight+=meanWeight*n;
            aggregateClipAny+=(clipAny/n)*n;
            aggregateSamples+=n;
            Log.d(TAG,"IRIS_26488_REJECTION_STAGE"
                    +" frame="+(frame+1)
                    +" flowVariationMean="+(flowVar/n)
                    +" interpolationCancelFraction="+(cancel/n)
                    +" unblockerMean="+(unblock/n)
                    +" initialReverseWeightMean="+(reverse/n)
                    +" initialAcceptMean="+(baseAccept/n)
                    +" pixelDifferenceMean="+(pixelDifference/n)
                    +" postRejectionMean="+(postRejection/n)
                    +" finalWeightMean="+meanWeight
                    +" finalWeightP10="+p10
                    +" finalWeightP50="+p50
                    +" finalWeightP90="+p90
                    +" physicalClipRGB="+(clipR/n)+","+(clipG/n)+","+(clipB/n)
                    +" quadAnyNearClip="+(clipAny/n));
        }
        if (aggregateSamples>0) {
            Log.d(TAG,"IRIS_26488_REJECTION_STAGE_AGGREGATE"
                    +" auxiliaryCount="+auxiliaryCount
                    +" finalWeightMean="+(aggregateWeight/aggregateSamples)
                    +" quadAnyNearClipMean="+(aggregateClipAny/aggregateSamples)
                    +" diagnosticsOnly=true fullResolutionReadback=false");
        }
    }

    private static final class SupportSummary {
        final float mean;
        final float p10;
        final float p50;
        final float p90;
        final float[] coarseGrid;
        final int gridWidth;
        final int gridHeight;

        SupportSummary(
                float mean,
                float p10,
                float p50,
                float p90,
                float[] coarseGrid,
                int gridWidth,
                int gridHeight) {
            this.mean = mean;
            this.p10 = p10;
            this.p50 = p50;
            this.p90 = p90;
            this.coarseGrid = coarseGrid;
            this.gridWidth = gridWidth;
            this.gridHeight = gridHeight;
        }
    }

    private static final class DirectRgbSupportSummary {
        final float meanR;
        final float meanG;
        final float meanB;
        final float lowR;
        final float lowG;
        final float lowB;
        final float imbalanceP95;
        final int samples;

        DirectRgbSupportSummary(
                float meanR,
                float meanG,
                float meanB,
                float lowR,
                float lowG,
                float lowB,
                float imbalanceP95,
                int samples) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.lowR = lowR;
            this.lowG = lowG;
            this.lowB = lowB;
            this.imbalanceP95 = imbalanceP95;
            this.samples = samples;
        }
    }

    /*
     * IRIS_26426_DIRECT_RGB_CHANNEL_SUPPORT_TELEMETRY
     * Sample every eighth pixel to keep diagnostics inexpensive.
     */
    private static DirectRgbSupportSummary summarizeDirectRgbSupport(
            ByteBuffer bytes,
            int width,
            int height) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();

        final int stride = 8;
        final int maxSamples =
                Math.max(1, ((width + stride - 1) / stride)
                        * ((height + stride - 1) / stride));
        float[] imbalance = new float[maxSamples];

        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        int lowR = 0;
        int lowG = 0;
        int lowB = 0;
        int n = 0;

        for (int y = 0; y < height; y += stride) {
            for (int x = 0; x < width; x += stride) {
                int base = (y * width + x) * 4;
                if (base + 2 >= values.limit()) continue;

                float r = Math.max(0.0f, values.get(base));
                float g = Math.max(0.0f, values.get(base + 1));
                float b = Math.max(0.0f, values.get(base + 2));

                sumR += r;
                sumG += g;
                sumB += b;

                if (r < 1.25f) lowR++;
                if (g < 1.25f) lowG++;
                if (b < 1.25f) lowB++;

                float max = Math.max(r, Math.max(g, b));
                float min = Math.min(r, Math.min(g, b));
                imbalance[n] =
                        max > 1.0e-6f ? (max - min) / max : 0.0f;
                n++;
            }
        }

        if (n <= 0) {
            return new DirectRgbSupportSummary(
                    0,0,0,1,1,1,0,0);
        }

        java.util.Arrays.sort(imbalance, 0, n);
        int p95Index = Math.min(n - 1, Math.max(0, (int)Math.floor(0.95 * (n - 1))));
        return new DirectRgbSupportSummary(
                (float)(sumR / n),
                (float)(sumG / n),
                (float)(sumB / n),
                lowR / (float)n,
                lowG / (float)n,
                lowB / (float)n,
                imbalance[p95Index],
                n);
    }

    private static float[] iris26478SampleFinalDirectRgb(
            FloatBuffer values,
            int width,
            int height,
            int x,
            int y) {
        int sx = Math.max(0, Math.min(width - 1, x));
        int sy = Math.max(0, Math.min(height - 1, y));
        int base = (sy * width + sx) * 4;
        if (base + 3 >= values.limit()) {
            return new float[]{Float.NaN, Float.NaN, Float.NaN, Float.NaN};
        }
        return new float[]{
                values.get(base),
                values.get(base + 1),
                values.get(base + 2),
                values.get(base + 3)};
    }

    /*
     * Exact linear diagnostic mirror:
     * MotionV2DisplayExposure -> Camera2 gains -> Camera2 3x3 matrix.
     * The active pipeline remains authoritative; this result is logging only.
     */
    private static float[] iris26478PredictActiveColor(
            float[] direct,
            Parameters parameters,
            float displayGain) {
        if (direct == null
                || direct.length < 3
                || parameters == null
                || parameters.motionV2ColorGains == null
                || parameters.motionV2ColorGains.length != 4
                || parameters.motionV2ColorTransform == null
                || parameters.motionV2ColorTransform.length != 9) {
            return new float[]{Float.NaN, Float.NaN, Float.NaN};
        }

        float[] g = parameters.motionV2ColorGains;
        float[] m = parameters.motionV2ColorTransform;
        float greenGain = 0.5f * (g[1] + g[2]);

        float r = Math.max(0.0f, direct[0]) * displayGain * g[0];
        float gg = Math.max(0.0f, direct[1]) * displayGain * greenGain;
        float b = Math.max(0.0f, direct[2]) * displayGain * g[3];

        return new float[]{
                Math.max(0.0f, m[0] * r + m[1] * gg + m[2] * b),
                Math.max(0.0f, m[3] * r + m[4] * gg + m[5] * b),
                Math.max(0.0f, m[6] * r + m[7] * gg + m[8] * b)};
    }

    /*
     * IRIS_26478_SPEAKER_SUPPORT_DIAGNOSTIC
     * Uses the exact existing SupportSummary from IRIS_26436 and reports
     * the four strongest adjacent support discontinuities.
     */
    private static void iris26478LogSpeakerSupportEdges(
            SupportSummary summary,
            String grid12x8,
            ByteBuffer rgbaBytes,
            int width,
            int height,
            int frameCount,
            Parameters parameters) {
        if (summary == null
                || summary.coarseGrid == null
                || rgbaBytes == null
                || width <= 0
                || height <= 0) {
            return;
        }

        String mapMessage =
                "grid12x8=" + grid12x8
                        + " mean=" + summary.mean
                        + " p10=" + summary.p10
                        + " p50=" + summary.p50
                        + " p90=" + summary.p90
                        + " retainedFrames=" + frameCount
                        + " source=existingIRIS_26436LocalSupport"
                        + " sameLocalSupportMap=true"
                        + " diagnosticOnly=true"
                        + " feedsImageMath=false";
        Log.d(TAG, "IRIS_26478_SPEAKER_SUPPORT_MAP " + mapMessage);
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26478_SPEAKER_SUPPORT_MAP",
                    mapMessage);
        } catch (Throwable ignored) {}

        final int topN = 4;
        float[] bestDelta = new float[topN];
        int[] axGrid = new int[topN];
        int[] ayGrid = new int[topN];
        int[] bxGrid = new int[topN];
        int[] byGrid = new int[topN];
        String[] orientation = new String[topN];

        for (int gy = 0; gy < summary.gridHeight; gy++) {
            for (int gx = 0; gx < summary.gridWidth; gx++) {
                int gi = gy * summary.gridWidth + gx;

                if (gx + 1 < summary.gridWidth) {
                    iris26478InsertSupportEdge(
                            Math.abs(
                                    summary.coarseGrid[gi]
                                            - summary.coarseGrid[gi + 1]),
                            gx,
                            gy,
                            gx + 1,
                            gy,
                            "verticalBoundary",
                            bestDelta,
                            axGrid,
                            ayGrid,
                            bxGrid,
                            byGrid,
                            orientation);
                }
                if (gy + 1 < summary.gridHeight) {
                    iris26478InsertSupportEdge(
                            Math.abs(
                                    summary.coarseGrid[gi]
                                            - summary.coarseGrid[
                                                    gi + summary.gridWidth]),
                            gx,
                            gy,
                            gx,
                            gy + 1,
                            "horizontalBoundary",
                            bestDelta,
                            axGrid,
                            ayGrid,
                            bxGrid,
                            byGrid,
                            orientation);
                }
            }
        }

        FloatBuffer values =
                rgbaBytes.duplicate()
                        .order(ByteOrder.nativeOrder())
                        .asFloatBuffer();

        float displayGain =
                Math.max(
                        1.0f,
                        parameters != null
                                ? parameters.motionV2DisplayGain
                                : 1.0f);

        for (int rank = 0; rank < topN; rank++) {
            if (!(bestDelta[rank] > 0.0f) || orientation[rank] == null) {
                continue;
            }

            int ax =
                    iris26478GridCenterToPixel(
                            axGrid[rank],
                            summary.gridWidth,
                            width);
            int ay =
                    iris26478GridCenterToPixel(
                            ayGrid[rank],
                            summary.gridHeight,
                            height);
            int bx =
                    iris26478GridCenterToPixel(
                            bxGrid[rank],
                            summary.gridWidth,
                            width);
            int by =
                    iris26478GridCenterToPixel(
                            byGrid[rank],
                            summary.gridHeight,
                            height);

            float[] directA =
                    iris26478SampleFinalDirectRgb(
                            values,
                            width,
                            height,
                            ax,
                            ay);
            float[] directB =
                    iris26478SampleFinalDirectRgb(
                            values,
                            width,
                            height,
                            bx,
                            by);
            float[] colorA =
                    iris26478PredictActiveColor(
                            directA,
                            parameters,
                            displayGain);
            float[] colorB =
                    iris26478PredictActiveColor(
                            directB,
                            parameters,
                            displayGain);

            float supportA =
                    summary.coarseGrid[
                            ayGrid[rank] * summary.gridWidth
                                    + axGrid[rank]];
            float supportB =
                    summary.coarseGrid[
                            byGrid[rank] * summary.gridWidth
                                    + bxGrid[rank]];

            String edgeMessage =
                    "rank=" + (rank + 1)
                            + " supportDelta=" + bestDelta[rank]
                            + " orientation=" + orientation[rank]
                            + " gridA=" + axGrid[rank] + "," + ayGrid[rank]
                            + " gridB=" + bxGrid[rank] + "," + byGrid[rank]
                            + " supportA=" + supportA
                            + " supportB=" + supportB
                            + " pixelA=" + ax + "," + ay
                            + " pixelB=" + bx + "," + by
                            + " xNormA=" + ax / (float)Math.max(1, width - 1)
                            + " yNormA=" + ay / (float)Math.max(1, height - 1)
                            + " xNormB=" + bx / (float)Math.max(1, width - 1)
                            + " yNormB=" + by / (float)Math.max(1, height - 1)
                            + " directA="
                            + directA[0] + "," + directA[1] + "," + directA[2]
                            + " directB="
                            + directB[0] + "," + directB[1] + "," + directB[2]
                            + " finalAlphaA=" + directA[3]
                            + " finalAlphaB=" + directB[3]
                            + " displayGain=" + displayGain
                            + " colorA="
                            + colorA[0] + "," + colorA[1] + "," + colorA[2]
                            + " colorB="
                            + colorB[0] + "," + colorB[1] + "," + colorB[2]
                            + " colorPrediction=MotionV2DisplayExposure_then_Camera2GainsMatrix"
                            + " sameLocalSupportMap=true"
                            + " diagnosticOnly=true"
                            + " feedsImageMath=false";

            Log.d(TAG, "IRIS_26478_SPEAKER_SUPPORT_EDGE " + edgeMessage);
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26478_SPEAKER_SUPPORT_EDGE",
                        edgeMessage);
            } catch (Throwable ignored) {}
        }
    }

    private static int iris26478GridCenterToPixel(
            int cell,
            int gridExtent,
            int imageExtent) {
        return Math.max(
                0,
                Math.min(
                        imageExtent - 1,
                        Math.round(
                                (cell + 0.5f)
                                        * imageExtent
                                        / gridExtent
                                        - 0.5f)));
    }

    private static void iris26478InsertSupportEdge(
            float delta,
            int ax,
            int ay,
            int bx,
            int by,
            String edgeOrientation,
            float[] bestDelta,
            int[] axGrid,
            int[] ayGrid,
            int[] bxGrid,
            int[] byGrid,
            String[] orientation) {
        for (int rank = 0; rank < bestDelta.length; rank++) {
            if (delta <= bestDelta[rank]) continue;

            for (int shift = bestDelta.length - 1;
                    shift > rank;
                    shift--) {
                bestDelta[shift] = bestDelta[shift - 1];
                axGrid[shift] = axGrid[shift - 1];
                ayGrid[shift] = ayGrid[shift - 1];
                bxGrid[shift] = bxGrid[shift - 1];
                byGrid[shift] = byGrid[shift - 1];
                orientation[shift] = orientation[shift - 1];
            }

            bestDelta[rank] = delta;
            axGrid[rank] = ax;
            ayGrid[rank] = ay;
            bxGrid[rank] = bx;
            byGrid[rank] = by;
            orientation[rank] = edgeOrientation;
            return;
        }
    }

    private static SupportSummary iris26487SummarizeCoarseDiag(
            float[] rgba,
            int frameCount,
            int gridWidth,
            int gridHeight) {
        final int cells = Math.max(1,gridWidth*gridHeight);
        float[] grid = new float[cells];
        int[] histogram = new int[256];
        double sum=0.0;
        long count=0L;
        for(int i=0;i<cells;i++){
            int base=i*4;
            float value=base<rgba.length?rgba[base]:1.0f;
            if(!Float.isFinite(value))value=1.0f;
            value=Math.max(1.0f,Math.min(frameCount,value));
            grid[i]=value;
            int bin=frameCount<=1?0:Math.max(0,Math.min(255,Math.round(
                    255.0f*(value-1.0f)/(frameCount-1.0f))));
            histogram[bin]++;sum+=value;count++;
        }
        float mean=count>0?(float)(sum/count):1.0f;
        return new SupportSummary(
                mean,
                supportQuantile(histogram,count,frameCount,0.10f),
                supportQuantile(histogram,count,frameCount,0.50f),
                supportQuantile(histogram,count,frameCount,0.90f),
                grid,gridWidth,gridHeight);
    }

    private static SupportSummary summarizeSupport(
            ByteBuffer bytes,
            int width,
            int height,
            int frameCount) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();

        final int gridWidth = 48;
        final int gridHeight = 36;
        float[] sums = new float[gridWidth * gridHeight];
        int[] counts = new int[gridWidth * gridHeight];
        int[] histogram = new int[256];

        double sum = 0.0;
        long count = 0L;
        int total = Math.min(values.capacity(), width * height);

        for (int index = 0; index < total; index++) {
            float value = values.get(index);
            if (!Float.isFinite(value)) value = 1.0f;
            value = Math.max(1.0f, Math.min(frameCount, value));

            int x = index % width;
            int y = index / width;
            int gx = Math.min(gridWidth - 1, x * gridWidth / Math.max(1, width));
            int gy = Math.min(gridHeight - 1, y * gridHeight / Math.max(1, height));
            int gi = gy * gridWidth + gx;
            sums[gi] += value;
            counts[gi]++;

            int bin;
            if (frameCount <= 1) {
                bin = 0;
            } else {
                bin = Math.max(
                        0,
                        Math.min(
                                255,
                                Math.round(
                                        255.0f * (value - 1.0f)
                                                / (frameCount - 1.0f))));
            }
            histogram[bin]++;
            sum += value;
            count++;
        }

        float[] grid = new float[sums.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = counts[i] > 0 ? sums[i] / counts[i] : 1.0f;
        }

        float mean = count > 0 ? (float) (sum / count) : 1.0f;
        return new SupportSummary(
                mean,
                supportQuantile(histogram, count, frameCount, 0.10f),
                supportQuantile(histogram, count, frameCount, 0.50f),
                supportQuantile(histogram, count, frameCount, 0.90f),
                grid,
                gridWidth,
                gridHeight);
    }

    private static float supportQuantile(
            int[] histogram,
            long total,
            int frameCount,
            float q) {
        if (total <= 0L || frameCount <= 1) return 1.0f;
        long target = Math.max(1L, (long) Math.ceil(total * q));
        long cumulative = 0L;
        for (int i = 0; i < histogram.length; i++) {
            cumulative += histogram[i];
            if (cumulative >= target) {
                return 1.0f
                        + (frameCount - 1.0f)
                        * ((float) i / (histogram.length - 1.0f));
            }
        }
        return frameCount;
    }
}
