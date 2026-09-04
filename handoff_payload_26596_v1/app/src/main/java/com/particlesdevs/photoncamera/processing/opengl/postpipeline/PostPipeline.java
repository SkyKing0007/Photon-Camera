package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.ColorSpace;
import android.os.Build;
import android.graphics.Point;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.opengl.GLBasePipeline;
import com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing;
import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLImage;
import com.particlesdevs.photoncamera.processing.opengl.GLInterface;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.parameters.ResolutionSolution;
import com.particlesdevs.photoncamera.processing.render.NoiseModeler;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.ultrahdr.MotionV2UltraHdr;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;
import java.util.ArrayList;

public class PostPipeline extends GLBasePipeline {
    public ByteBuffer stackFrame;

    /* IRIS_26414_MOTION_V2_FLOAT_CFA_HANDOFF */
    public ByteBuffer motionV2FloatCfa;
    /* IRIS_26548 Night uses Motion's proven RGBA32F cross-context CPU carrier;
     * Night capture/reconstruction/post ownership remains separate. */
    public ByteBuffer irisNightRgba32f;
    /* IRIS_26501_FULL_RES_CAMERA_RGB_BRIDGE */
    public boolean motionV2DirectRgbCarrier = false;
    /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_BRIDGE */
    public ByteBuffer motionV2HighlightProvenance;
    /* IRIS_26533_MOTION_RCD_CARRIER */
    public boolean irisMotionRcdActive=false;
    public ByteBuffer irisMotionDirectRgbAuxiliary;
    public GLTexture irisMotionDirectRgbTexture;
    public GLTexture motionV2HighlightProvenanceTexture;

    /* IRIS_26432_TRUE_V2_GAINMAP_HANDOFF */
    public Bitmap motionV2GainMapBitmap;
    public float motionV2GainMapMaxRatio = 1.0f;
    public float motionV2GainMapFullHdrDisplayRatio = 1.0f;
    /* IRIS_26564_TRUE2X_FROZEN_TONE_STATE
     * The true-2x streamed renderer must consume the exact same settings snapshot as the native
     * post graph. Never reread live UI settings after the graph has completed.
     */
    public IrisMotionSettings.Snapshot motionV2ToneSettingsSnapshot;
    /* IRIS_26564_TRUE2X_FROZEN_WATERMARK_STATE
     * The streamed true-2x renderer must see the same watermark decision as RotateWatermark.
     */
    public boolean motionV2WatermarkEnabled = false;
    public ByteBuffer lowFrame;
    public ByteBuffer highFrame;
    public GLTexture FusionMap;
    public GLTexture GainMap;
    public ArrayList<Bitmap> debugData = new ArrayList<>();
    public ArrayList<ImageFrame> SAGAIN;
    public Point cropSize;
    public float[] analyzedBL = new float[]{0.f, 0.f, 0.f};
    float regenerationSense = 1.f;
    float totalGain = 1.f;
    float AecCorr = 1.f;
    float fusionGain = 1.f;
    float softLight = 1.f;

    public PostPipeline() {
        super("PostPipeline");
    }

    /* IRIS_26540_NIGHT_POST_CONSTRUCTOR */
    public PostPipeline(boolean irisNightOwned) {
        super("PostPipeline", irisNightOwned);
    }

    /* IRIS_26545_V1_2_EXPLICIT_RECONSTRUCTION_OWNER */
    private static String motionReconstructionOwnerName(int owner) {
        if (owner == Parameters.MOTION_V2_RECONSTRUCTION_SABRE) return "SABRE";
        return "NONE_OR_INVALID(" + owner + ")";
    }

    /* IRIS_26562_SABRE_SR_POST_OWNER_CONTRACT
     * Motion and Night have one legal reconstruction owner. Spatial-RGB reliability/source-restore
     * payloads no longer exist at this boundary.
     */
    private void validateIrisReconstructionOwnership() {
        if (!(mParameters.motionV2Active || mParameters.irisNightActive)) return;
        final int owner = mParameters.motionV2ReconstructionOwner;
        final String pipeline = mParameters.irisNightActive ? "Night" : "Motion";
        if (owner != Parameters.MOTION_V2_RECONSTRUCTION_SABRE) {
            throw new IllegalStateException("26560 missing/invalid " + pipeline
                    + " Sabre reconstruction owner=" + owner);
        }
        final float expectedOutputScale = mParameters.motionV2SuperResOutputEnabled ? 2.0f : 1.0f;
        if (Math.abs(mParameters.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f
                || Math.abs(mParameters.motionV2SpatialReconstructionZoom - 1.0f) > 1.0e-5f
                || Math.abs(mParameters.motionV2SuperResOutputScale - expectedOutputScale) > 1.0e-5f) {
            throw new IllegalStateException("26562 " + pipeline
                    + " invalid Sabre SR geometry reconstructionZoom="
                    + mParameters.motionV2ReconstructionZoom
                    + " spatialZoom=" + mParameters.motionV2SpatialReconstructionZoom
                    + " srEnabled=" + mParameters.motionV2SuperResOutputEnabled
                    + " outputScale=" + mParameters.motionV2SuperResOutputScale
                    + " expectedOutputScale=" + expectedOutputScale);
        }
        if (Math.abs(mParameters.motionV2MgcSourceExposureGain - 1.0f) > 1.0e-5f) {
            throw new IllegalStateException("26560 " + pipeline
                    + " inherited obsolete Spatial/Bento source exposure");
        }
        Log.i("PostPipeline", "IRIS_26562_SABRE_SR_RECONSTRUCTION_OWNER_VALID"
                + " pipeline=" + pipeline
                + " owner=" + motionReconstructionOwnerName(owner)
                + " sourceGain=" + mParameters.motionV2MgcSourceExposureGain
                + " reconstructionZoom=" + mParameters.motionV2ReconstructionZoom
                + " superResRequested=" + mParameters.motionV2SuperResOutputEnabled
                + " superResScale=" + mParameters.motionV2SuperResOutputScale);
    }

    public int getRotation() {
        int rotation = mParameters.cameraRotation;
        String TAG = "ParseExif";
        if (mParameters == null || !mParameters.irisNightActive) {
            Log.d(TAG, "Gravity rotation:" + PhotonCamera.getGravity().getRotation());
            Log.d(TAG, "Sensor rotation:" + PhotonCamera.getCaptureController().mSensorOrientation);
        } else {
            Log.d(TAG, "IRIS_26540_NIGHT_FROZEN_ROTATION rotation=" + rotation
                    + " livePhotonRotationReads=false");
        }
        return rotation;
    }

    @SuppressWarnings("SuspiciousNameCombination")
    private Point getRotatedCoords(Point in) {
        switch (getRotation()) {
            case 0:
            case 180:
                return in;
            case 90:
            case 270:
                return new Point(in.y, in.x);
        }
        return in;
    }

    float constShift = 0.0f;
    
    @Tunable(
        title = "Demosaicing Method",
        description = "0 = Demosaic (compatibility mode), 1 = Demosaic3 (better quality)",
        category = "Demosaic",
        min = 0.0f,
        max = 1.0f,
        defaultValue = 1.0f,
        step = 1.0f
    )
    int demosaicingMethod = 1;

    /*
     * IRIS_26414_MOTION_V2_FLOAT_CFA_HANDOFF
     * Motion V2 enters PostPipeline already normalized into FLOAT16 CFA planes.
     */
    public Bitmap RunMotionV2FloatCfa(
            ByteBuffer reconstructedCfa,
            ByteBuffer highlightProvenance,
            Parameters parameters) {
        if (reconstructedCfa == null) {
            throw new IllegalArgumentException(
                    "Motion V2 reconstructed CFA buffer is null");
        }
        motionV2FloatCfa = reconstructedCfa;
        /* IRIS_26501_EXPLICIT_RGB_CARRIER_CONTRACT
         * Standard Bayer reconstruction publishes full-resolution camera-linear RGB.
         * Do not infer carrier semantics from whether a diagnostic provenance buffer happened
         * to be returned; provenance was already consumed inside the reconstruction owner.
         */
        motionV2DirectRgbCarrier = parameters != null
                && parameters.cfaPattern >= 0 && parameters.cfaPattern <= 3;
        motionV2HighlightProvenance = motionV2DirectRgbCarrier ? null : highlightProvenance;
        if (parameters == null) {
            throw new IllegalArgumentException("26545 V1.2 Motion parameters are null");
        }
        Log.d("PostPipeline", "IRIS_26545_V1_2_RGB_BRIDGE_CONTRACT directRgbCarrier="
                + motionV2DirectRgbCarrier
                + " reconstructionOwner=" + motionReconstructionOwnerName(parameters.motionV2ReconstructionOwner)
                + " carrierAuthority=explicitSelectedReconstruction"
                + " provenanceConsumedUpstream=" + motionV2DirectRgbCarrier);
        return Run(null, parameters);
    }

    public Bitmap RunIrisNightRgb(ByteBuffer sabreRgb, Parameters parameters) {
        if (sabreRgb == null) throw new IllegalArgumentException("26560 Iris Night Sabre RGB is null");
        irisNightRgba32f = sabreRgb;
        motionV2FloatCfa = null;
        motionV2DirectRgbCarrier = false;
        motionV2HighlightProvenance = null;
        parameters.irisNightActive = true;
        parameters.motionV2Active = false;
        irisMotionRcdActive = false;
        irisMotionDirectRgbAuxiliary = null;
        Log.processState("PostPipeline", "NIGHT_POST_PIPELINE_ENTER");
        Log.critical("PostPipeline", "IRIS_26560_NIGHT_SABRE_RGB_POST_ENTRY carrier=RGBA32F"
                + " bytes=" + sabreRgb.capacity()
                + " dedicatedNightInput=true motionParityLifecycle=true rcd=false demosaic=false"
                + " lifecycleOwner=night_self_closing");
        try {
            Log.processState("PostPipeline", "NIGHT_POST_RUN_BEGIN");
            Log.critical("PostPipeline", "IRIS_26544_NIGHT_POST_RUN_BEGIN");
            Bitmap result = Run(null, parameters);
            Log.processState("PostPipeline", "NIGHT_POST_RUN_COMPLETE");
            Log.critical("PostPipeline", "IRIS_26544_NIGHT_POST_RUN_COMPLETE bitmap="
                    + (result == null ? "null" : (result.getWidth() + "x" + result.getHeight())));
            return result;
        } finally {
            // IRIS_26548_NIGHT_RGBA32F_POST_OWNERSHIP
            // RunIrisNightRgb owns the carrier once entered. IrisNightRgbInput frees it immediately
            // after successful upload; if setup fails earlier, this fallback is the sole release.
            ByteBuffer unreleasedNightCarrier = irisNightRgba32f;
            irisNightRgba32f = null;
            if (unreleasedNightCarrier != null) {
                try {
                    Allocator.free(unreleasedNightCarrier);
                    Log.critical("PostPipeline", "IRIS_26548_NIGHT_CPU_RGBA32F_FALLBACK_RELEASE bytes="
                            + unreleasedNightCarrier.capacity());
                } catch (Throwable releaseFailure) {
                    Log.e("PostPipeline", "IRIS_26548_NIGHT_CPU_RGBA32F_FALLBACK_RELEASE_FAILED", releaseFailure);
                }
            }
            // IRIS_26539_NIGHT_POST_OWNER_CLOSE_BEFORE_JIN
            // The returned Bitmap owns a copied ARGB_8888 image. Night must destroy the EGL/Post
            // owner before ORT/Jin begins, even when a post node throws. Motion keeps its existing
            // caller-owned lifecycle unchanged.
            Log.processState("PostPipeline", "NIGHT_POST_CLOSE_BEGIN");
            Log.critical("PostPipeline", "IRIS_26544_NIGHT_POST_CLOSE_BEGIN");
            try { close(); }
            catch (Throwable closeFailure) {
                Log.e("PostPipeline", "IRIS_26539_NIGHT_POST_CLOSE_FAILED", closeFailure);
            }
            Log.processState("PostPipeline", "NIGHT_POST_CLOSE_COMPLETE");
            Log.critical("PostPipeline", "IRIS_26544_NIGHT_POST_OWNER_CLOSED beforeJin=true"
                    + " carrierReferenceCleared=true");
        }
    }
    /** Legacy guard: Night production must not return to the 26534 Bayer/RCD route. */
    public Bitmap RunIrisNightBayer(ByteBuffer fusedBayer, Parameters parameters) {
        throw new IllegalStateException("26560 architecture guard: Night production must use Sabre linear RGB");
    }
    public Bitmap RunMotionV2FusedBayerRcd(ByteBuffer fusedBayer,ByteBuffer directRgb,ByteBuffer provenance,Parameters parameters){
        /* IRIS_26534_FORBID_MOTION_DNG_BAYER_PRODUCTION
         * Motion production is Sabre Resolve linear RGB. The normalized16 Bayer carrier is DNG/export
         * evidence and must never replace the production RGB carrier again.
         */
        throw new IllegalStateException(
                "26534 architecture guard: Motion JPEG cannot consume fused/DNG Bayer through RCD");
    }

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
        mParameters = parameters;
        mSettings = mParameters.irisNightActive ? null : PhotonCamera.getSettings();
        motionV2WatermarkEnabled = mParameters.irisNightActive
                ? mParameters.irisNightWatermarkEnabled
                : (mSettings != null && mSettings.watermark);
        workSize = new Point(mParameters.rawSize.x, mParameters.rawSize.y);
        if (mParameters.motionV2Active || mParameters.irisNightActive) {
            /*
             * IRIS_26477_NO_PHOTON_POST_NOISE_STATE
             * Active Motion V2 nodes do not consume generic Photon noise state.
             */
            noiseS = 0.0f;
            noiseO = 0.0f;
            Log.d("PostPipeline",
                    "IRIS_26477_NO_PHOTON_POST_NOISE_STATE"
                            + " noiseModeler=false"
                            + " noiseRstr=false"
                            + " esd=false"
                            + " residualSpatialDenoise=false");
        } else {
            NoiseModeler modeler = mParameters.noiseModeler;
            noiseS = modeler.computeModel[0].first.floatValue() +
                    modeler.computeModel[1].first.floatValue() +
                    modeler.computeModel[2].first.floatValue();
            noiseO = modeler.computeModel[0].second.floatValue() +
                    modeler.computeModel[1].second.floatValue() +
                    modeler.computeModel[2].second.floatValue();
            noiseS /= 3.f;
            noiseO /= 3.f;
            double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
            Log.d("PostPipeline", "noisempy:" + noisempy);
            noiseS *= noisempy;
            noiseO *= noisempy;
            noiseO = Math.max(noiseO, 1.0f/4096.0f);
            noiseS = Math.max(noiseS, Float.MIN_NORMAL);
        }
        Point rawSliced = parameters.rawSize;
        cropSize = new Point(parameters.rawSize);
        final boolean iris26540Aspect169 = mParameters.irisNightActive
                ? mParameters.irisNightAspect169 : PhotonCamera.getSettings().aspect169;
        if (iris26540Aspect169) {
            if (rawSliced.x > rawSliced.y) {
                rawSliced = new Point(rawSliced.x, rawSliced.x * 9 / 16);
            } else {
                rawSliced = new Point(rawSliced.y * 9 / 16, rawSliced.y);
            }
            cropSize =  new Point(rawSliced);
        }
        Point rotatedSize = getRotatedCoords(rawSliced);
        final boolean iris26540EnergySaving = mParameters.irisNightActive
                ? mParameters.irisNightEnergySaving : PhotonCamera.getSettings().energySaving;
        if (iris26540EnergySaving || mParameters.rawSize.x * mParameters.rawSize.y < ResolutionSolution.smallRes) {
            GLDrawParams.TileSize = 8;
        } else {
            GLDrawParams.TileSize = 256;
        }
        GLFormat format = new GLFormat(GLFormat.DataType.SIMPLE_8, 4);
        GLImage output = new GLImage(rotatedSize, format, false);
        GLCoreBlockProcessing glproc = new GLCoreBlockProcessing(rotatedSize, output, format, GLDrawParams.Allocate.Direct);
        glint = new GLInterface(glproc);
        stackFrame = inBuffer;
        glint.parameters = parameters;
        if (mParameters.motionV2Active) {
            iris26387LogMergedBayerInput(stackFrame);
        }

        // IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION
        // Night presentation is shutter-frozen. Legacy/live tunables remain available to other modes.
        if (!mParameters.irisNightActive) {
            com.particlesdevs.photoncamera.settings.TunableInjector.inject(this);
        } else {
            Log.i("PostPipeline", "IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION aspect169="
                    + mParameters.irisNightAspect169 + " energySaving="
                    + mParameters.irisNightEnergySaving + " watermark="
                    + mParameters.irisNightWatermarkEnabled);
        }
        
        BuildDefaultPipeline();
        GLImage resImg = runAll();
        Bitmap res = resImg.getBufferedImage();
        /* IRIS_26567_INTERNAL_DISPLAY_P3_BITMAP_TAG
         * Iris JPEG pixels have already been rendered in Display-P3 primaries. Tag them at the
         * bitmap boundary so publication/Jin adapters cannot apply the old sRGB->P3 transform twice.
         */
        if (mParameters.irisJpegColorValid && Build.VERSION.SDK_INT >= 26
                && res != null && !res.isRecycled()) {
            res.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            Log.i("PostPipeline", "IRIS_26567_JPEG_WORKING_GAMUT bitmap=DISPLAY_P3 dngAffected=false");
        }

        /*
         * IRIS_26432_TRUE_V2_ULTRAHDR_ATTACH
         * Gain map came from pre-tone extended-linear Motion V2 signal.
         */
        if (mParameters.irisNightActive && motionV2GainMapBitmap != null) {
            Log.i("PostPipeline", "IRIS_26550_NIGHT_HDR_AUTHORITY_DETACHED"
                    + " gainMap=" + motionV2GainMapBitmap.getWidth() + "x"
                    + motionV2GainMapBitmap.getHeight()
                    + " maxRatio=" + motionV2GainMapMaxRatio
                    + " attachedPreJin=false postJinRebaseRequired=true");
        }
        if (mParameters.motionV2Active && motionV2GainMapBitmap != null) {
            boolean attached = MotionV2UltraHdr.attachMotion(
                    res,
                    motionV2GainMapBitmap,
                    getRotation(),
                    motionV2GainMapMaxRatio,
                    motionV2GainMapFullHdrDisplayRatio);
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26432_TRUE_V2_ULTRAHDR",
                        "attached=" + attached
                                + " source=extendedLinearPreTone"
                                + " sdrBasePreserved=true"
                                + " bodyGainUnity=true"
                                + " maxRatio=" + motionV2GainMapMaxRatio
                                + " fullHdrDisplayRatio=" + motionV2GainMapFullHdrDisplayRatio
                                + " capacityMatchesActualGainPeak=true");
            } catch (Throwable ignored) {}
            motionV2GainMapBitmap = null;
        }

        Allocator.free(resImg.byteBuffer);
        GLTexture.closeAll();
        return res;
    }

    /* IRIS_26387_WHITE_STAGE_DIAGNOSTIC */
    private void iris26387LogMergedBayerInput(ByteBuffer source) {
        if (source == null) return;
        try {
            ByteBuffer b = source.duplicate().order(java.nio.ByteOrder.nativeOrder());
            int words = b.remaining() / 2;
            if (words <= 0) return;
            int step = Math.max(1, words / 8192);
            java.util.ArrayList<Float> values = new java.util.ArrayList<>();
            double sum = 0.0;
            int min = 65535;
            int max = 0;
            for (int i = 0; i < words; i += step) {
                int v = b.getShort(b.position() + i * 2) & 0xffff;
                min = Math.min(min, v);
                max = Math.max(max, v);
                sum += v;
                values.add((float)v);
            }
            java.util.Collections.sort(values);
            int n = values.size();
            float p01 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.01f))));
            float p10 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.10f))));
            float p50 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.50f))));
            float p90 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.90f))));
            float p99 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.99f))));
            String line = "IRIS_26387_STAGE_STATS stage=MERGE_OUTPUT_UINT16"
                    + " samples=" + n + " min=" + min + " mean=" + (sum/n)
                    + " max=" + max + " p01=" + p01 + " p10=" + p10
                    + " p50=" + p50 + " p90=" + p90 + " p99=" + p99
                    + " parameterWhiteLevel=" + mParameters.whiteLevel
                    + " black0=" + (mParameters.blackLevel != null && mParameters.blackLevel.length > 0
                            ? mParameters.blackLevel[0] : Float.NaN);
            Log.d("IRIS26387", line);
            try { com.particlesdevs.photoncamera.util.MotionTrace.processingState("WHITE_STAGE_26387", line); }
            catch (Throwable ignored) {}
        } catch (Throwable t) {
            Log.e("IRIS26387", "IRIS_26387_STAGE_STATS stage=MERGE_OUTPUT_UINT16 error=" + t.getClass().getSimpleName());
        }
    }

    private void BuildDefaultPipeline() {
        /* IRIS_26560_SABRE_ONLY_POST_GRAPH
         * Night and Motion enter the common finishing graph only from proven Sabre linear RGB.
         * Obsolete Spatial-RGB source restoration/reliability nodes no longer exist.
         * Common camera-RGB color/presentation/render nodes remain unchanged.
         */
        if(mParameters.irisNightActive){
            validateIrisReconstructionOwnership();
            add(new IrisNightRgbInput());
            add(new StageTelemetry("IRIS_NIGHT_RGB_INPUT"));
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26560_NIGHT_SABRE_POST_OWNERSHIP",
                    "owner=SABRE carrier=RESOLVE_SABRE_LINEAR_RGB"
                            + " spatialSourceRestore=false spatialHighlightReliability=false"
                            + " rcd=false demosaic=false commonIrisFinishingBegins=MotionV2ColorTransform");
            add(new MotionV2ColorTransform());
            add(new StageTelemetry("IRIS_NIGHT_PROFILE_COLOR"));
            add(new MotionV2ViewfinderExposureMatcher());
            add(new StageTelemetry("IRIS_26550_NIGHT_PRESENTATION_SOLVE"));
            /* IRIS_26563_UNIVERSAL_ADAPTIVE_COLOR_APPEARANCE
             * Device-specific profile color is already complete and the exposure solver has read
             * the untouched calibrated image. Restore only reliable weak colorfulness in common
             * extended linear-sRGB before display exposure/tone/highlight/gamut rendering.
             */
            add(new MotionV2AdaptiveColorAppearance());
            add(new StageTelemetry("IRIS_26563_NIGHT_ADAPTIVE_COLOR_APPEARANCE"));
            add(new MotionV2DisplayExposure());
            add(new StageTelemetry("IRIS_26550_NIGHT_PRESENTATION_EXPOSURE"));
            add(new MotionV2Render());
            add(new StageTelemetry("IRIS_NIGHT_RENDER"));
            add(new RotateWatermark(getRotation(), mParameters.irisNightWatermarkEnabled));
            return;
        }
        /* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */
        if(mParameters.motionV2Active&&irisMotionRcdActive){
            throw new IllegalStateException(
                    "26534 architecture guard: Motion post graph attempted forbidden Bayer/RCD detour");
        }

        boolean nightMode = PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT;

        /* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */
        if (mParameters.motionV2Active) {
            /*
             * IRIS_26414_MOTION_V2_FLOAT_CFA_POST_GRAPH
             * Temporal reconstruction is already in normalized FLOAT16 CFA.
             */
            add(new MotionV2CfaInput());
            /*
             * IRIS_26425_RESOLVED_CFA_ROUTING_AUTHORITY
             *
             * Parameters.cfaPattern is the Camera2-resolved sensor CFA after
             * optional user override. Settings.cfaPattern may still be -1
             * ("automatic"), so it must not decide the runtime image carrier.
             */
            boolean directBayer =
                    mParameters.cfaPattern >= 0 && mParameters.cfaPattern <= 3;
            /* IRIS_26501_REFERENCE_SAFE_RGB_ISOLATION
             * Standard Bayer Motion is already full-resolution camera-linear RGB.
             * Only non-standard CFA formats retain the historical packed-CFA fallback.
             */
            /* IRIS_26501_PROPER_PER_FRAME_RGB_POST_GRAPH
             * Standard Bayer arrives as native full-resolution camera-linear RGB.
             * No Bayer/RCD/demosaic stage may reinterpret that semantic carrier.
             */
            boolean directRgbCarrier = directBayer && motionV2DirectRgbCarrier;
            if (directRgbCarrier) {
                add(new StageTelemetry("V2_POST_PROPER_PER_FRAME_RGB"));
            } else if (directBayer) {
                throw new IllegalStateException(
                        "26501 standard Bayer Motion reached post graph without direct RGB carrier");
            } else {
                add(new StageTelemetry("V2_POST_FLOAT_CFA_INPUT_FALLBACK"));
                switch (mSettings.cfaPattern) {
                    case -2:
                        add(new DemosaicQUAD());
                        break;
                    case 4:
                        add(new MonoDemosaic());
                        break;
                    default:
                        add(new MotionV2CfaDemosaic());
                        break;
                }
                add(new StageTelemetry("V2_POST_DEMOSAIC_FALLBACK"));
            }
                    /*
                     * IRIS_26418_MOTION_V2_OWNED_IMAGE_FORMATION
                     * Linear camera RGB -> direct HAL linear sRGB ->
                     * residual luma/chroma denoise -> tone/output.
                     */
            /*
             * IRIS_26446_LOCAL_SUPPORT_CONSUMER_ORDER
             * Direct RGB alpha still carries true frame-equivalent support here.
             */
            if (false && directRgbCarrier) { /* IRIS_26462_WRONSKI_TEMPORAL_RECON_OWNS_PRIMARY_DENOISE */ add(new MotionV2LocalSupportDenoise()); add(new StageTelemetry("V2_POST_TRUE_LOCAL_SUPPORT_DENOISE")); }
            if (directBayer && !directRgbCarrier) {
                add(new StageTelemetry(
                        "V2_POST_REFERENCE_SAFE_DEMOSAIC_ISOLATION"));
            }
            /* IRIS_26560_SABRE_POST_DOMAIN_ORDER
             * Sabre enters this graph at identity source exposure. Profile color establishes the
             * DNG-aware working domain; automatic presentation EV is then solved from the
             * shutter-time viewfinder. User Iris controls remain later and additive.
             */
            validateIrisReconstructionOwnership();
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26560_MOTION_SABRE_POST_OWNERSHIP",
                    "owner=SABRE carrier=RESOLVE_SABRE_LINEAR_RGB"
                            + " spatialSourceRestore=false spatialHighlightReliability=false"
                            + " rcd=false demosaic=false commonIrisFinishingBegins=MotionV2ColorTransform");
            add(new MotionV2ColorTransform());
            add(new StageTelemetry("V2_POST_DNG_PROFILE_COLOR_TRANSFORM"));
            add(new MotionV2ViewfinderExposureMatcher());
            add(new StageTelemetry("V2_POST_VIEWFINDER_EXPOSURE_SOLVE"));
            /* IRIS_26563_UNIVERSAL_ADAPTIVE_COLOR_APPEARANCE
             * Shared Motion/SR appearance stage in common extended linear-sRGB. It runs exactly
             * once after device profile conversion/exposure solve and before presentation gain.
             */
            add(new MotionV2AdaptiveColorAppearance());
            add(new StageTelemetry("IRIS_26563_MOTION_ADAPTIVE_COLOR_APPEARANCE"));
            add(new MotionV2DisplayExposure());
            add(new StageTelemetry("V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE"));

            /* IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS
             * Manual Iris Exposure/Shadows/Contrast remain independent of the automatic
             * viewfinder match and operate afterward on the common extended-linear source.
             */
            IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current();
            motionV2ToneSettingsSnapshot = irisMotionSettings;
            if (irisMotionSettings.hasToneAdjustment()) {
                add(new IrisMotionToneControls(irisMotionSettings));
                add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));
            }

            /* IRIS_26560_SABRE_PRIMARY_RECONSTRUCTION_DENOISE
             * No legacy Photon residual spatial-denoise stage is reintroduced after Sabre.
             */
            add(new MotionV2Render());
            add(new StageTelemetry("V2_POST_RENDER"));
            add(new RotateWatermark(getRotation(), motionV2WatermarkEnabled));
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26410_MOTION_V2_POST_GRAPH",
                    "owner=" + motionReconstructionOwnerName(mParameters.motionV2ReconstructionOwner)
                            + " nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,OwnerSpecificPreColor,MotionV2ColorTransform,MotionV2ViewfinderExposureMatcher,MotionV2AdaptiveColorAppearance,MotionV2DisplayExposure,IrisManualOptional,MotionV2Render,RotateWatermark"
                            + " spatialHighlightNode=false"
                            + " directMultiframeRgb=" + directRgbCarrier
                            + " strictSabreAuthority26560=true"
                            + " displayExposureAfterSabre=true"
                            + " residualSpatialDenoise=false"
                            + " photonNoiseState=false"
                            + " exposureFusion=false esd=false ablc=false"
                            + " initial=false autoExposure=false"
                            + " captureSharpening=false correctingFlow=false sharpen2=false");
            return;
        }

        add(new Bayer2Float());
        add(new StageTelemetry("POST_BAYER2FLOAT"));
        add(new ExposureFusionBayer2());
        add(new StageTelemetry("POST_EXPOSURE_FUSION_BAYER2"));
        switch (PhotonCamera.getSettings().cfaPattern) {
            case -2: {
                add(new DemosaicQUAD());
                break;
            }
            case 4: {
                add(new MonoDemosaic());
                break;
            }
            default: {
                //if (nightMode)
                //    add(new HotPixelFilter());
                //if(PhotonCamera.getSettings().hdrxNR) {
                //add(new ESD3DBayerCS());
                //}

                if (PhotonCamera.getSettings().hdrxNR) {

                    //add(new BayerFilter());
                    /*if (nightMode) {
                        add(new BayerConcat(true));
                        add(new BayerFilter());
                        add(new BayerConcat(false));
                    }*/
                    //add(new BayerMoire());

                }

                if(mSettings.alignAlgorithm != 2) {
                    //add(new HotPixelFilter());
                    // demosaicingMethod is automatically injected from settings
                    //noinspection SwitchStatementWithTooFewBranches
                    switch (demosaicingMethod){
                        case 0:
                            add(new Demosaic());
                            break;
                        default:
                            add(new Demosaic3());
                            break;
                    }
                }
                add(new StageTelemetry("POST_DEMOSAIC"));
                if (PhotonCamera.getSettings().hdrxNR) {
                    add(new ESD3D2(true));
                }
                add(new StageTelemetry("POST_ESD3D2_OR_BYPASS"));
                //add(new ImpulsePixelFilter());
                break;
            }
        }
        add(new ABLC());
        add(new StageTelemetry("POST_ABLC"));
        /*
         * * * All filters after demosaicing * * *
         */

        //if (PhotonCamera.getSettings().hdrxNR) {
            //if (nightMode)
            //    add(new Wavelet());
            //add(new ESD3D(true));
            //add(new ESD3D(true));
        //}

        //add(new AWB());
        //add(new Equalization());

        add(new Initial());
        add(new StageTelemetry("POST_INITIAL"));

        add(new AutoExposure());
        add(new StageTelemetry("POST_AUTOEXPOSURE"));


        //add(new GlobalToneMapping());

        add(new CaptureSharpening());

        add(new CorrectingFlow());

        //add(new ChromaticFlow());

        add(new Sharpen2());
        //add(new Sharpen("sharpen33"));

        add(new RotateWatermark(getRotation()));
    }
}
