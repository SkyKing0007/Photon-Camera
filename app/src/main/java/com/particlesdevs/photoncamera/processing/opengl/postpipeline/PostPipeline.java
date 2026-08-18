package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
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
    /* IRIS_26501_FULL_RES_CAMERA_RGB_BRIDGE */
    public boolean motionV2DirectRgbCarrier = false;
    /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_BRIDGE */
    public ByteBuffer motionV2HighlightProvenance;
    public GLTexture motionV2HighlightProvenanceTexture;

    /* IRIS_26432_TRUE_V2_GAINMAP_HANDOFF */
    public Bitmap motionV2GainMapBitmap;
    public float motionV2GainMapMaxRatio = 1.0f;
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

    public int getRotation() {
        int rotation = mParameters.cameraRotation;
        String TAG = "ParseExif";
        Log.d(TAG, "Gravity rotation:" + PhotonCamera.getGravity().getRotation());
        Log.d(TAG, "Sensor rotation:" + PhotonCamera.getCaptureController().mSensorOrientation);
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
        Log.d("PostPipeline", "IRIS_26501_RGB_BRIDGE_CONTRACT directRgbCarrier="
                + motionV2DirectRgbCarrier
                + " carrierAuthority=explicitStandardBayerReconstruction"
                + " provenanceConsumedUpstream=" + motionV2DirectRgbCarrier);
        return Run(null, parameters);
    }

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
        mParameters = parameters;
        mSettings = PhotonCamera.getSettings();
        workSize = new Point(mParameters.rawSize.x, mParameters.rawSize.y);
        if (mParameters.motionV2Active) {
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
        if (PhotonCamera.getSettings().aspect169) {
            if (rawSliced.x > rawSliced.y) {
                rawSliced = new Point(rawSliced.x, rawSliced.x * 9 / 16);
            } else {
                rawSliced = new Point(rawSliced.y * 9 / 16, rawSliced.y);
            }
            cropSize =  new Point(rawSliced);
        }
        Point rotatedSize = getRotatedCoords(rawSliced);
        if (PhotonCamera.getSettings().energySaving || mParameters.rawSize.x * mParameters.rawSize.y < ResolutionSolution.smallRes) {
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
        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
            iris26387LogMergedBayerInput(stackFrame);
        }

        // Inject tunable values for PostPipeline (since it doesn't extend Node)
        com.particlesdevs.photoncamera.settings.TunableInjector.inject(this);
        
        BuildDefaultPipeline();
        GLImage resImg = runAll();
        Bitmap res = resImg.getBufferedImage();

        /*
         * IRIS_26432_TRUE_V2_ULTRAHDR_ATTACH
         * Gain map came from pre-tone extended-linear Motion V2 signal.
         */
        if (mParameters.motionV2Active && motionV2GainMapBitmap != null) {
            boolean attached = MotionV2UltraHdr.attach(
                    res,
                    motionV2GainMapBitmap,
                    getRotation(),
                    motionV2GainMapMaxRatio);
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26432_TRUE_V2_ULTRAHDR",
                        "attached=" + attached
                                + " source=extendedLinearPreTone"
                                + " sdrBasePreserved=true"
                                + " bodyGainUnity=true"
                                + " maxRatio=" + motionV2GainMapMaxRatio);
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
            /*
             * IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY
             * Wronski is complete before scene/display exposure is applied.
             */
            add(new MotionV2DisplayExposure());
            add(new StageTelemetry("V2_POST_DISPLAY_EXPOSURE_AFTER_WRONSKI"));
            add(new MotionV2ColorTransform());
            add(new StageTelemetry("V2_POST_CAMERA2_COLOR_TRANSFORM"));

            /*
             * IRIS_26477_WRONSKI_PRIMARY_DENOISE_ONLY
             * Pure comparison build: no residual spatial denoise after Wronski.
             */
            add(new MotionV2Render());
            add(new StageTelemetry("V2_POST_RENDER"));
            add(new RotateWatermark(getRotation()));
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26410_MOTION_V2_POST_GRAPH",
                    "nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2DisplayExposure,MotionV2ColorTransform,MotionV2Render,RotateWatermark"
                            + " directMultiframeRgb=" + directRgbCarrier
                            + " strictWronskiAuthority26477=true"
                            + " displayExposureAfterWronski=true"
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
