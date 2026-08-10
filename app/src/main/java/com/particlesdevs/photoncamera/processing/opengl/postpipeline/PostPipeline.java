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
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;
import java.util.ArrayList;

public class PostPipeline extends GLBasePipeline {
    public ByteBuffer stackFrame;

    /* IRIS_26414_MOTION_V2_FLOAT_CFA_HANDOFF */
    public ByteBuffer motionV2FloatCfa;
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
            Parameters parameters) {
        if (reconstructedCfa == null) {
            throw new IllegalArgumentException(
                    "Motion V2 reconstructed CFA buffer is null");
        }
        motionV2FloatCfa = reconstructedCfa;
        return Run(null, parameters);
    }

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
        mParameters = parameters;
        mSettings = PhotonCamera.getSettings();
        workSize = new Point(mParameters.rawSize.x, mParameters.rawSize.y);
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

        /* IRIS_26394_MOTION_CANONICAL_NOISE_DOMAIN
         * y=g*x, Var(x)=S*x+O -> S'=g*S, O'=g^2*O.
         */
        float iris26394CanonicalGain =
                Math.max(1.0f, mParameters.motionCanonicalExposureGain);
        if (iris26394CanonicalGain > 1.0f) {
            noiseS *= iris26394CanonicalGain;
            noiseO *= iris26394CanonicalGain * iris26394CanonicalGain;
        }
        Log.d("PostPipeline",
                "IRIS_26394_CANONICAL_NOISE gain=" + iris26394CanonicalGain
                        + " noiseS=" + noiseS + " noiseO=" + noiseO);
        Log.d("PostPipeline", "NoiseS:" + noiseS + "\n" + "NoiseO:" + noiseO);
        /*if (!PhotonCamera.getSettings().hdrxNR) {
            noiseO = 0.f;
            noiseS = 0.f;
        }*/
        noiseO = Math.max(noiseO, 1.0f/4096.0f);
        noiseS = Math.max(noiseS, Float.MIN_NORMAL);
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
            if (directBayer) {
                /*
                 * IRIS_26424_DIRECT_MULTIFRAME_RGB_POST_GRAPH
                 * Standard Bayer image formation already produced full-
                 * resolution linear camera RGB. No separate demosaic runs.
                 */
                add(new StageTelemetry("V2_POST_DIRECT_MULTIFRAME_RGB"));
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
            add(new MotionV2ColorTransform());
            add(new MotionV2Denoise());

            add(new StageTelemetry("V2_POST_LUMA_CHROMA_RECONSTRUCTION"));
            add(new MotionV2Render());
            add(new StageTelemetry("V2_POST_RENDER"));
            add(new RotateWatermark(getRotation()));
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26410_MOTION_V2_POST_GRAPH",
                    "nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"
                            + " directMultiframeRgb=" + directBayer
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
