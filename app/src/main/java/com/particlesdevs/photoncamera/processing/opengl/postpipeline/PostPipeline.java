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

    /*
     * Build 26179:
     * Strength of the Motion indoor bright-window HDR scene gate.
     * Zero preserves the complete existing pipeline, including Night mode.
     */
    /*
     * Build 26252:
     * Shadow recovery and highlight compression are separate decisions.
     * The older shared strength allowed a zero highlight gate to disable
     * clearly needed shadow recovery.
     */
    float motionShadowSceneStrength = 0.0f;
    float motionHighlightSceneStrength = 0.0f;

    /*
     * Compatibility mirror for older diagnostics and unchanged nodes.
     * It follows shadow strength because that was the failed path proven by
     * the 26251 EXIF record.
     */
    float indoorHdrSceneStrength = 0.0f;

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

    @Tunable(
            title = "Motion residual variance boost",
            description = "Maximum extra downstream noise variance at ISO 3200. 0 disables the extra boost; 0.80 gives a 1.80x model.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 2.0f,
            defaultValue = 0.55f,
            step = 0.05f
    )
    float motionResidualVarianceBoost = 0.25f;

    @Tunable(
            title = "Motion measured residual variance boost",
            description = "Optional extra downstream variance after the measured local effective-stack model is active. The default is zero to avoid counting the same correction twice.",
            category = "Motion Noise Tuning",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.0f,
            step = 0.05f
    )
    float motionMeasuredResidualVarianceBoost = 0.0f;

    public Bitmap Run(ByteBuffer inBuffer, Parameters parameters) {
        mParameters = parameters;
        mSettings = PhotonCamera.getSettings();

        /* Build 26251: reset the JPEG EXIF tone diagnostic for this run. */
        MotionToneExifDiagnostics.reset(
                mSettings.selectedMode == CameraMode.MOTION,
                Math.max(1.0f, mParameters.iso),
                mParameters.effectiveFrameCount,
                mParameters.effectiveStackRatio,
                mParameters.localContributionMeasured,
                0.0f,
                0.0f
        );

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

        /* Refresh modeled noise after normal Photon multipliers are applied. */
        MotionToneExifDiagnostics.reset(
                mSettings.selectedMode == CameraMode.MOTION,
                Math.max(1.0f, mParameters.iso),
                mParameters.effectiveFrameCount,
                mParameters.effectiveStackRatio,
                mParameters.localContributionMeasured,
                noiseS,
                noiseO
        );

        float motionResidualNoiseMpy = 1.0f;
        /*if (!PhotonCamera.getSettings().hdrxNR) {
            noiseO = 0.f;
            noiseS = 0.f;
        }*/
        noiseO = Math.max(noiseO, 1.0f/4096.0f);
        noiseS = Math.max(noiseS, Float.MIN_NORMAL);

        /*
         * Build 26168:
         * Apply residual Motion variance after the normal Photon floors.
         * This keeps every captured/merged frame and leaves the effective
         * frame diagnostic unchanged.
         */
        if (mSettings.selectedMode == CameraMode.MOTION) {
            float motionIso =
                    Math.max(
                            1.0f,
                            mParameters.iso
                    );

            float highIsoBlend =
                    com.particlesdevs.photoncamera.util.Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            float configuredResidualBoost =
                    mParameters.localContributionMeasured
                            ? motionMeasuredResidualVarianceBoost
                            : motionResidualVarianceBoost;

            motionResidualNoiseMpy =
                    1.0f
                            + configuredResidualBoost
                            * highIsoBlend;

            noiseS *= motionResidualNoiseMpy;
            noiseO *= motionResidualNoiseMpy;

            Log.d(
                    "PostPipeline",
                    "MOTION_26172_LOCAL_NOISE_HANDOFF"
                            + " iso=" + motionIso
                            + " retainedFrames="
                            + mParameters.retainedFrameCount
                            + " effectiveMeasured="
                            + mParameters.effectiveFrameCount
                            + " effectiveRatio="
                            + mParameters.effectiveStackRatio
                            + " localContributionMeasured="
                            + mParameters.localContributionMeasured
                            + " varianceMultiplier="
                            + motionResidualNoiseMpy
                            + " configuredFallbackBoost="
                            + motionResidualVarianceBoost
                            + " configuredMeasuredBoost="
                            + motionMeasuredResidualVarianceBoost
                            + " appliedConfiguredBoost="
                            + configuredResidualBoost
                            + " appliedAfterNoiseFloor=true"
                            + " dngAndJpegModelShareEffectiveCount=true"
                            + " adaptiveNoiseSettingUnchanged=true"
            );
        }

        Log.d(
                "PostPipeline",
                "NoiseS:" + noiseS
                        + "\nNoiseO:" + noiseO
                        + "\nMotionResidualNoiseMpy:"
                        + motionResidualNoiseMpy
        );

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

        // Inject tunable values for PostPipeline (since it doesn't extend Node)
        com.particlesdevs.photoncamera.settings.TunableInjector.inject(this);
        
        BuildDefaultPipeline();
        GLImage resImg = runAll();
        Bitmap res = resImg.getBufferedImage();
        Allocator.free(resImg.byteBuffer);
        GLTexture.closeAll();
        return res;
    }

    private void BuildDefaultPipeline() {
        boolean nightMode = PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT;
        add(new Bayer2Float());
        add(new ExposureFusionBayer2());


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
                if (PhotonCamera.getSettings().hdrxNR) {
                    add(new ESD3D2(true));
                }


                //add(new ImpulsePixelFilter());
                break;
            }
        }
        add(new ABLC());
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

        if (mSettings.selectedMode == CameraMode.MOTION
                && mSettings.hdrxNR) {
            /*
         * Build 26216:
         * Bypass dedicated post-tone luma cleanup because it can consolidate
         * residual temporal noise into blotches. Keep the separate coarse
         * chroma cleanup stage.
         */
        // add(new MotionLumaDenoise());
        add(new MotionChromaDenoise());
        }

        add(new AutoExposure());

        /*
         * Build 26232:
         * Restore a small amount of GCam-like narrow mid-frequency contrast
         * only where temporal stack confidence and local edge support agree.
         * This is luma-only and is not a global sharpening increase.
         */
        if (mParameters.motionCapture
                && mSettings.hdrxNR) {
            /*
             * Build 26246 A/B:
             * Temporarily bypass MotionMicroContrast so surviving edge
             * enhancement cannot hide whether ESD preserved real texture.
             * Merge, alignment and sharpening nodes remain unchanged.
             */
            // add(new MotionMicroContrast());
        }

        //add(new GlobalToneMapping());

        add(new CaptureSharpening());

        add(new CorrectingFlow());

        //add(new ChromaticFlow());

        add(new Sharpen2());
        //add(new Sharpen("sharpen33"));

        add(new RotateWatermark(getRotation()));
    }
}
