package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;

import com.particlesdevs.photoncamera.processing.opengl.scripts.PyramidMerging;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.api.Camera2ApiAutoFix;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImageFrameDeblur;
import com.particlesdevs.photoncamera.processing.ImageSaver;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline;
import com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;

public class HdrxProcessor extends ProcessorBase {
    private static final String TAG = "HdrxProcessor";
    private ArrayList<ImageFrame> mImageFramesToProcess;
    private HashMap<Long, Double> exposures;
    private int imageFormat;
    /* config */
    private int alignAlgorithm;
    private int saveRAW;
    private CameraMode cameraMode;
    private ArrayList<GyroBurst> BurstShakiness;


    public HdrxProcessor(ProcessingEventsListener processingEventsListener) {
        super(processingEventsListener);
    }

    public void configure(int alignAlgorithm, int saveRAW, CameraMode cameraMode) {
        this.alignAlgorithm = alignAlgorithm;
        this.saveRAW = saveRAW;
        this.cameraMode = cameraMode;
    }

    public void start(Path dngFile, Path imageFile,
                      ParseExif.ExifData exifData,
                      ArrayList<GyroBurst> BurstShakiness,
                      ArrayList<ImageFrame> imageBuffer,
                      HashMap<Long, Double> exposures,
                      int imageFormat,
                      int cameraRotation,
                      CameraCharacteristics characteristics,
                      CaptureResult captureResult,
                      CaptureRequest captureRequest,
                      ProcessingCallback callback) {
        this.imageFile = imageFile;
        this.dngFile = dngFile;
        this.exifData = exifData;
        this.BurstShakiness = new ArrayList<>(BurstShakiness);
        this.imageFormat = imageFormat;
        this.cameraRotation = cameraRotation;
        this.mImageFramesToProcess = imageBuffer;
        this.exposures = exposures;
        this.callback = callback;
        this.characteristics = characteristics;
        this.captureResult = captureResult;
        this.captureRequest = captureRequest;
        Log.d(TAG, "HdrxProcessor called start()");
        Run();
    }

    public void Run() {
        try {
            Camera2ApiAutoFix.ApplyRes(captureResult);
            if (imageFormat == CaptureController.RAW_FORMAT) {
                ApplyHdrX();
            } else {
                Log.d(TAG, "HdrX processing skipped due to unsupported image format: " + imageFormat);
                callback.onFinished();
                return;
            }
//            if (isYuv) {
//                ApplyStabilization();
//            }
        } catch (Exception e) {
            Log.e(TAG, ProcessingEventsListener.FAILED_MSG);
            Log.e(TAG, "Error in HdrX Processing:"+Log.getStackTraceString(e));
            if (cameraMode == CameraMode.MOTION) {
                Log.e(
                        TAG,
                        "MOTION_26286_HIGHLIGHT_SHADOW_CHROMA_HALO_COMPLETE"
                                + " success=false"
                                + " stage=HdrxProcessor.Run"
                                + " error=" + e.getClass().getSimpleName()
                );
                boolean flushed = Log.flushAndWait(5000L);
                android.util.Log.d(
                        TAG,
                        "MOTION_26280_LOG_FLUSH success=" + flushed
                );
            }
            callback.onFailed();
            processingEventsListener.onProcessingError("HdrX Processing Failed");
        }
    }

    private void ApplyHdrX() {
        callback.onStarted();
        processingEventsListener.onProcessingStarted("HDRX");

        Log.d(TAG, "ApplyHdrX() called from" + Thread.currentThread().getName());

        long startTime = System.currentTimeMillis();
        Log.d(TAG, "ApplyHdrX() mImageFramesToProcess.size():" + mImageFramesToProcess.size());
        int width = mImageFramesToProcess.get(0).width;
        int height = mImageFramesToProcess.get(0).height;
        Log.d(TAG, "APPLY HDRX: buffer:" + mImageFramesToProcess.get(0).buffer.asShortBuffer().remaining());
        Log.d(TAG, "Api WhiteLevel:" + characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL));
        Log.d(TAG, "Api BlackLevel:" + characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN));
        Parameters processingParameters = new Parameters();
        processingParameters.motionCapture =
                cameraMode == CameraMode.MOTION;
        processingParameters.FillConstParameters(
                characteristics,
                new Point(width, height)
        );

        if (processingParameters.motionCapture) {
            Log.w(
                    TAG,
                    "MOTION_26232_DIAGNOSTIC_BEGIN"
                            + " configuredCameraMode=" + cameraMode
                            + " liveUiMode="
                            + PhotonCamera.getSettings().selectedMode
                            + " inputFrames="
                            + mImageFramesToProcess.size()
                            + " immutableMotionCapture=true"
            );
        }
        // sort by timestamp first
        mImageFramesToProcess.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
        double minExpo = exposures.get(mImageFramesToProcess.get(0).getTimestamp());
        for (int i = 1; i < mImageFramesToProcess.size(); i++) {
            minExpo = Math.min(minExpo, exposures.get(mImageFramesToProcess.get(i).getTimestamp()));
        }
        Log.d(TAG, "Wrapper.init");
        ArrayList<ImageFrame> images = new ArrayList<>();
        int ISO = 0;
        int normalFrames = 0;
        if(BurstShakiness.size() < mImageFramesToProcess.size()){
            Log.d(TAG,"Warning: Gyro data size:"+BurstShakiness.size()+" is less than image size:"+mImageFramesToProcess.size());
        }
        for (int i = 0; i < mImageFramesToProcess.size(); i++) {
            ImageFrame frame = mImageFramesToProcess.get(i);
            frame.frameGyro = BurstShakiness.get(i%BurstShakiness.size()); // cyclic for safety
            //frame.image = mImageFramesToProcess.get(i);
            //Log.d(TAG,"Timestamp:"+frame.image.getTimestamp());
            //frame.pair = IsoExpoSelector.pairs.get(i % IsoExpoSelector.patternSize);
            /*
             * Photo/Night normally create one exposure pair per request.
             * Equal-exposure Motion intentionally calculates exposure once,
             * so fullpairs contains one entry shared by the whole burst.
             */
            if (IsoExpoSelector.fullpairs.isEmpty()) {
                throw new IllegalStateException(
                        "No exposure pairs available for HDRX"
                );
            }

            int exposurePairIndex =
                    i % IsoExpoSelector.fullpairs.size();

            frame.pair = IsoExpoSelector.fullpairs.get(
                    exposurePairIndex
            );
            frame.number = i;

            Double frameExposure = exposures.get(
                    mImageFramesToProcess.get(i).getTimestamp()
            );

            if (frameExposure == null) {
                /*
                 * All Motion requests have identical ISO and shutter.
                 * A missing HAL timestamp entry may safely use minExpo.
                 */
                frameExposure = minExpo;

                Log.w(
                        TAG,
                        "Missing exposure metadata for frame "
                                + i
                                + "; using equal-burst exposure"
                );
            }

            frame.pair.layerMpy =
                    (float) (frameExposure / minExpo);
            if (frame.pair.layerMpy > 1.0) {
                frame.pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.High;
            } else {
                frame.pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.Normal;
                normalFrames++;
            }
            /*if(i == mImageFramesToProcess.size()-1){
                int ind = Math.max(0,mImageFramesToProcess.size()-2);
                frame.frameGyro = BurstShakiness.get(ind);
            }*/
            Log.d(TAG, "Mpy:" + frame.pair.layerMpy);
            images.add(frame);
            ISO += frame.pair.iso;
        }
        ISO /= mImageFramesToProcess.size();

        Log.d(
                TAG,
                "MOTION_DYNAMIC_METADATA_INPUT"
                        + " averagePairIso=" + ISO
                        + " captureResultIso="
                        + captureResult.get(
                                CaptureResult.SENSOR_SENSITIVITY
                        )
                        + " requestIso="
                        + captureRequest.get(
                                CaptureRequest.SENSOR_SENSITIVITY
                        )
                        + " captureResultExposureNs="
                        + captureResult.get(
                                CaptureResult.SENSOR_EXPOSURE_TIME
                        )
                        + " requestExposureNs="
                        + captureRequest.get(
                                CaptureRequest.SENSOR_EXPOSURE_TIME
                        )
                        + " captureResultNeutral="
                        + java.util.Arrays.toString(
                                captureResult.get(
                                        CaptureResult
                                                .SENSOR_NEUTRAL_COLOR_POINT
                                )
                        )
        );

        processingParameters.FillDynamicParameters(
                captureResult,
                captureRequest,
                ISO
        );

        processingParameters.cameraRotation =
                cameraRotation;

        Log.d(
                TAG,
                "MOTION_DYNAMIC_METADATA_SELECTED"
                        + " iso="
                        + processingParameters.iso
                        + " exposureSeconds="
                        + processingParameters.exposureTime
                        + " whitePoint="
                        + java.util.Arrays.toString(
                                processingParameters.whitePoint
                        )
                        + " cfaPattern="
                        + processingParameters.cfaPattern
                        + " whiteLevel="
                        + processingParameters.whiteLevel
                        + " blackLevel="
                        + java.util.Arrays.toString(
                                processingParameters.blackLevel
                        )
        );

        exifData.IMAGE_DESCRIPTION = processingParameters.toString();
        ImageFrameDeblur imageFrameDeblur = new ImageFrameDeblur(processingParameters);
        imageFrameDeblur.firstFrameGyro = images.get(0).frameGyro.clone();
        for (int i = 0; i < images.size(); i++)
            imageFrameDeblur.processDeblurPosition(images.get(i));
        if (mImageFramesToProcess.size() >= 3)
            images.sort((img1, img2) -> Float.compare(img1.frameGyro.shakiness, img2.frameGyro.shakiness));
        double unluckypickiness = 1.05;
        float unluckyavr = 0;
        for (ImageFrame image : images) {
            unluckyavr += image.frameGyro.shakiness;
            Log.d(TAG, "unlucky map:" + image.frameGyro.shakiness + "n:" + image.number);
        }
        unluckyavr /= images.size();
        // search for high exposure close frame by time
        int highind = -1;
        int timeDiff = Integer.MAX_VALUE;
        for (int i = 0; i < images.size(); i++) {
            if (images.get(i).pair.curlayer == IsoExpoSelector.ExpoPair.exposureLayer.High) {
                int diff = (int) Math.abs(images.get(i).timestamp - images.get(0).timestamp);
                if (diff < timeDiff) {
                    timeDiff = diff;
                    highind = i;
                }
            }
        }
        // swap to second
        if (highind != -1) {
            ImageFrame frame = images.get(0);
            images.set(0, images.get(highind));
            images.set(highind, frame);
        }

        if (images.size() > 10) {
            CameraMode selectedMode =
                    PhotonCamera.getSettings().selectedMode;

            if (selectedMode == CameraMode.MOTION) {
                /*
                 * Motion captures the complete per-lens configured burst.
                 *
                 * Do not automatically target 75 percent of the frames.
                 * Remove only frames whose whole-frame gyro shakiness is a
                 * severe outlier. Local alignment and robustness still
                 * determine how much each retained frame contributes.
                 */
                final int minimumFramesToKeep =
                        Math.max(8, (int) Math.ceil(images.size() * 0.75));

                final float severeOutlierThreshold =
                        unluckyavr * 1.80f;

                for (int i = images.size() - 1;
                     i >= 0 && images.size() > minimumFramesToKeep;
                     i--) {

                    ImageFrame candidate = images.get(i);

                    if (candidate.frameGyro.shakiness
                            <= severeOutlierThreshold) {
                        continue;
                    }

                    if (normalFrames == 1
                            && candidate.pair.curlayer
                            == IsoExpoSelector.ExpoPair.exposureLayer.Normal) {
                        continue;
                    }

                    if (candidate.pair.curlayer
                            == IsoExpoSelector.ExpoPair.exposureLayer.Normal) {
                        normalFrames--;
                    }

                    Log.d(
                            TAG,
                            "Motion severe-outlier removal: shakiness="
                                    + candidate.frameGyro.shakiness
                                    + " threshold="
                                    + severeOutlierThreshold
                                    + " frame="
                                    + candidate.number
                    );

                    candidate.close();
                    images.remove(i);
                }

                Log.d(
                        TAG,
                        "Motion frames retained: "
                                + images.size()
                                + " of configured burst"
                );
            } else {
                /*
                 * Preserve the developer's existing Photo and Night behavior.
                 */
                int size =
                        images.size() - FrameNumberSelector.throwCount;

                Log.d(TAG, "Throw Count target:" + size);
                Log.d(TAG, "Image Count:" + images.size());

                size = (int) (images.size() * 0.75);

                for (int i = images.size(); i > size; i--) {
                    ImageFrame cur = images.get(images.size() - 1);
                    float curunlucky = cur.frameGyro.shakiness;

                    if (curunlucky > unluckyavr * unluckypickiness) {
                        if (normalFrames == 1
                                && cur.pair.curlayer
                                == IsoExpoSelector.ExpoPair.exposureLayer.Normal) {
                            continue;
                        }

                        if (cur.pair.curlayer
                                == IsoExpoSelector.ExpoPair.exposureLayer.Normal) {
                            normalFrames--;
                        }

                        Log.d(
                                TAG,
                                "Removing unlucky:"
                                        + curunlucky
                                        + " number:"
                                        + cur.number
                        );

                        cur.close();
                        images.remove(images.size() - 1);
                    }
                }

                Log.d(TAG, "Size after removal:" + images.size());
            }
        }

        /*
         * Build 26229 — retained Motion stack exposure consistency audit.
         *
         * This does not reject or alter frames. It records the exact metadata
         * carried into alignment so low-light softness can be separated into
         * shutter blur, exposure inconsistency, or insufficient temporal
         * contribution without creating a separate diagnostic APK.
         */
        if (processingParameters.motionCapture) {

            int metadataFrames = 0;
            int missingExposureFrames = 0;
            int missingIsoFrames = 0;

            long minimumExposureNs = Long.MAX_VALUE;
            long maximumExposureNs = 0L;
            int minimumIso = Integer.MAX_VALUE;
            int maximumIso = 0;

            double minimumEnergy = Double.POSITIVE_INFINITY;
            double maximumEnergy = 0.0;
            double energyLog2Sum = 0.0;
            double energyLog2SquareSum = 0.0;

            for (ImageFrame frame : images) {
                long exposureNs = frame.diagnosticExposureNs;
                int frameIso = frame.diagnosticIso;

                if (exposureNs <= 0L) {
                    missingExposureFrames++;
                }
                if (frameIso <= 0) {
                    missingIsoFrames++;
                }

                if (exposureNs <= 0L || frameIso <= 0) {
                    continue;
                }

                metadataFrames++;
                minimumExposureNs =
                        Math.min(minimumExposureNs, exposureNs);
                maximumExposureNs =
                        Math.max(maximumExposureNs, exposureNs);
                minimumIso =
                        Math.min(minimumIso, frameIso);
                maximumIso =
                        Math.max(maximumIso, frameIso);

                double energy =
                        (double) exposureNs * (double) frameIso;

                minimumEnergy =
                        Math.min(minimumEnergy, energy);
                maximumEnergy =
                        Math.max(maximumEnergy, energy);

                double energyLog2 =
                        Math.log(energy) / Math.log(2.0);

                energyLog2Sum += energyLog2;
                energyLog2SquareSum += energyLog2 * energyLog2;
            }

            double exposureSpreadEv =
                    metadataFrames > 0
                                    && minimumExposureNs > 0L
                            ? Math.log(
                                    (double) maximumExposureNs
                                            / (double) minimumExposureNs
                            ) / Math.log(2.0)
                            : Double.NaN;

            double isoSpreadEv =
                    metadataFrames > 0
                                    && minimumIso > 0
                            ? Math.log(
                                    (double) maximumIso
                                            / (double) minimumIso
                            ) / Math.log(2.0)
                            : Double.NaN;

            double energySpreadEv =
                    metadataFrames > 0
                                    && minimumEnergy > 0.0
                            ? Math.log(
                                    maximumEnergy / minimumEnergy
                            ) / Math.log(2.0)
                            : Double.NaN;

            double energyMeanLog2 =
                    metadataFrames > 0
                            ? energyLog2Sum / metadataFrames
                            : Double.NaN;

            double energyVarianceLog2 =
                    metadataFrames > 0
                            ? Math.max(
                                    0.0,
                                    energyLog2SquareSum
                                            / metadataFrames
                                            - energyMeanLog2
                                                * energyMeanLog2
                            )
                            : Double.NaN;

            double energyStdDevEv =
                    metadataFrames > 0
                            ? Math.sqrt(energyVarianceLog2)
                            : Double.NaN;

            Log.d(
                    TAG,
                    "MOTION_26232_EXPOSURE_CONSISTENCY"
                            + " retainedFrames=" + images.size()
                            + " metadataFrames=" + metadataFrames
                            + " missingExposureFrames="
                            + missingExposureFrames
                            + " missingIsoFrames="
                            + missingIsoFrames
                            + " exposureMinNs="
                            + (
                                    minimumExposureNs
                                            == Long.MAX_VALUE
                                            ? 0L
                                            : minimumExposureNs
                            )
                            + " exposureMaxNs="
                            + maximumExposureNs
                            + " exposureSpreadEv="
                            + exposureSpreadEv
                            + " isoMin="
                            + (
                                    minimumIso
                                            == Integer.MAX_VALUE
                                            ? 0
                                            : minimumIso
                            )
                            + " isoMax=" + maximumIso
                            + " isoSpreadEv=" + isoSpreadEv
                            + " energySpreadEv=" + energySpreadEv
                            + " energyStdDevEv=" + energyStdDevEv
                            + " renderingChanged=false"
            );
        }

        float minMpy = 1000.f;
        for (int i = 0; i < images.size(); i++) {
            if (images.get(i).pair.layerMpy < minMpy) {
                minMpy = images.get(i).pair.layerMpy;
            }
        }
        /*
        if (images.get(0).pair.layerMpy != minMpy) {
            Log.d(TAG,"Replace 0 with minMpy");
            for (int i = 1; i < images.size(); i++) {
                if (images.get(i).pair.layerMpy == minMpy) {
                    ImageFrame frame = images.get(0);
                    images.set(0, images.get(i));
                    images.set(i, frame);
                    break;
                }
            }
        }*/
        int selected = 0;
        for (int i = 0; i < images.size(); i++) {
            if(images.get(i).pair.layerMpy == minMpy){
                selected = i;
                break;
            }
        }

        // move selected image to 0 index
        if(selected != 0){
            ImageFrame frame = images.get(0);
            images.set(0, images.get(selected));
            images.set(selected, frame);
        }
        selected = 0;



        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
        Log.d(TAG, "Wrapper.loadFrame");
        //float noiseLevel = (float) Math.sqrt((CaptureController.mCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY)) *
        //        IsoExpoSelector.getMPY() - 40.)*6400.f / (6.2f*IsoExpoSelector.getISOAnalog());

        ByteBuffer output = null;
        boolean motionContributionMeasured = false;
        float motionEffectiveFrameCount = 1.0f;
        float motionEffectiveStackRatio = 1.0f;
        float motionContributionMean = 1.0f;
        float motionContributionP10 = 1.0f;
        float motionContributionP25 = 1.0f;
        float motionContributionP50 = 1.0f;
        float motionContributionP75 = 1.0f;
        float motionContributionP90 = 1.0f;
        float motionContributionBelow4 = 0.0f;
        float motionContributionBelow8 = 0.0f;
        float motionContributionBelow12 = 0.0f;
        float motionContributionBelow16 = 0.0f;
        ArrayList<Float> motionPerFrameContributionDeltaMean =
                new ArrayList<>();

        Log.d(TAG, "Packing");
        //WrapperAl.packImages();
        Log.d(TAG, "Packed");
        if(images.size() > 1) {
            PyramidMerging pyramidMerging = new PyramidMerging(new Point(width, height), images);
            pyramidMerging.parameters = processingParameters;
            pyramidMerging.Run();

            motionContributionMeasured =
                    pyramidMerging
                            .hasMotionContributionMeasurement();

            motionEffectiveFrameCount =
                    pyramidMerging
                            .getMotionEffectiveFrameCount();

            motionEffectiveStackRatio =
                    pyramidMerging
                            .getMotionEffectiveStackRatio();

            motionContributionMean =
                    pyramidMerging
                            .getMotionContributionMean();

            motionContributionP10 =
                    pyramidMerging
                            .getMotionContributionP10();

            motionContributionP25 =
                    pyramidMerging
                            .getMotionContributionP25();

            motionContributionP50 =
                    pyramidMerging
                            .getMotionContributionP50();

            motionContributionP75 =
                    pyramidMerging
                            .getMotionContributionP75();

            motionContributionP90 =
                    pyramidMerging
                            .getMotionContributionP90();

            motionContributionBelow4 =
                    pyramidMerging
                            .getMotionContributionBelow4();

            motionContributionBelow8 =
                    pyramidMerging
                            .getMotionContributionBelow8();

            motionContributionBelow12 =
                    pyramidMerging
                            .getMotionContributionBelow12();

            motionContributionBelow16 =
                    pyramidMerging
                            .getMotionContributionBelow16();

            motionPerFrameContributionDeltaMean =
                    pyramidMerging
                            .getMotionPerFrameContributionDeltaMean();

            output = pyramidMerging.Output;
            pyramidMerging.close();
            for (int i = 0; i < images.size(); i++) {
                images.get(i).close();
            }
            IncreaseWLBL(processingParameters);
        } else {
            output = images.get(0).buffer;
            images.get(0).buffer = null;
        }
        Log.d(TAG, "HDRX Alignment elapsed:" + (System.currentTimeMillis() - startTime) + " ms");

        processingParameters.retainedFrameCount =
                Math.max(
                        1,
                        images.size()
                );

        processingParameters.localContributionMeasured =
                cameraMode == CameraMode.MOTION
                        && motionContributionMeasured;

        if (processingParameters.localContributionMeasured) {
            processingParameters.effectiveFrameCount =
                    Math.max(
                            1.0f,
                            Math.min(
                                    processingParameters.retainedFrameCount,
                                    motionEffectiveFrameCount
                            )
                    );

            processingParameters.effectiveStackRatio =
                    Math.max(
                            1.0f
                                    / processingParameters.retainedFrameCount,
                            Math.min(
                                    1.0f,
                                    motionEffectiveStackRatio
                            )
                    );

            processingParameters.localContributionMean =
                    motionContributionMean;

            processingParameters.localContributionP10 =
                    motionContributionP10;

            processingParameters.localContributionP25 =
                    motionContributionP25;

            processingParameters.localContributionP50 =
                    motionContributionP50;

            processingParameters.localContributionP75 =
                    motionContributionP75;

            processingParameters.localContributionP90 =
                    motionContributionP90;

            processingParameters.localContributionBelow4 =
                    motionContributionBelow4;

            processingParameters.localContributionBelow8 =
                    motionContributionBelow8;

            processingParameters.localContributionBelow12 =
                    motionContributionBelow12;

            processingParameters.localContributionBelow16 =
                    motionContributionBelow16;
        } else {
            processingParameters.effectiveFrameCount =
                    processingParameters.retainedFrameCount;

            processingParameters.effectiveStackRatio =
                    1.0f;
        }

        processingParameters.nativeResolutionSrEnabled =
                cameraMode == CameraMode.MOTION;

        processingParameters.motionAlternatesSelected =
                cameraMode == CameraMode.MOTION
                        ? Math.max(0, processingParameters.retainedFrameCount - 1)
                        : 0;

        processingParameters.motionAlternatesProcessed =
                processingParameters.motionAlternatesSelected;

        processingParameters.motionProcessingComplete =
                cameraMode == CameraMode.MOTION;

        processingParameters.subpixelSampleDiversity =
                cameraMode == CameraMode.MOTION
                        && processingParameters.retainedFrameCount > 1
                        ? Math.max(
                                0.0f,
                                Math.min(
                                        1.0f,
                                        (processingParameters.effectiveFrameCount - 1.0f)
                                                / (processingParameters.retainedFrameCount - 1.0f)
                                )
                        )
                        : 0.0f;

        if (cameraMode == CameraMode.MOTION) {
            double slowShutterContributionSum = 0.0;
            int slowShutterContributionCount = 0;
            double fastShutterContributionSum = 0.0;
            int fastShutterContributionCount = 0;

            double blurSum = 0.0;
            double contributionSum = 0.0;
            double blurContributionSum = 0.0;
            double blurSquareSum = 0.0;
            double contributionSquareSum = 0.0;
            int correlationCount = 0;

            for (int i = 1; i < images.size(); i++) {
                ImageFrame frame = images.get(i);
                int diagnosticIndex = i - 1;

                float contributionDelta =
                        diagnosticIndex
                                        < motionPerFrameContributionDeltaMean
                                                .size()
                                ? motionPerFrameContributionDeltaMean
                                        .get(diagnosticIndex)
                                : frame.diagnosticContributionDeltaMean;

                float gyroShakiness =
                        frame.frameGyro != null
                                ? frame.frameGyro.shakiness
                                : 0.0f;

                double shutterMs =
                        frame.diagnosticExposureNs > 0L
                                ? frame.diagnosticExposureNs
                                        / 1_000_000.0
                                : 0.0;

                double blurProduct =
                        shutterMs
                                * Math.max(
                                        gyroShakiness,
                                        frame.diagnosticOisMotion
                                );

                if (shutterMs >= 45.0) {
                    slowShutterContributionSum +=
                            contributionDelta;
                    slowShutterContributionCount++;
                } else {
                    fastShutterContributionSum +=
                            contributionDelta;
                    fastShutterContributionCount++;
                }

                blurSum += blurProduct;
                contributionSum += contributionDelta;
                blurContributionSum +=
                        blurProduct * contributionDelta;
                blurSquareSum +=
                        blurProduct * blurProduct;
                contributionSquareSum +=
                        contributionDelta * contributionDelta;
                correlationCount++;
            }

            double slowMean =
                    slowShutterContributionCount > 0
                            ? slowShutterContributionSum
                                    / slowShutterContributionCount
                            : Double.NaN;

            double fastMean =
                    fastShutterContributionCount > 0
                            ? fastShutterContributionSum
                                    / fastShutterContributionCount
                            : Double.NaN;

            double correlationNumerator =
                    correlationCount
                                    * blurContributionSum
                            - blurSum * contributionSum;

            double correlationDenominator =
                    Math.sqrt(
                            Math.max(
                                    0.0,
                                    (
                                            correlationCount
                                                    * blurSquareSum
                                            - blurSum * blurSum
                                    )
                                            * (
                                                    correlationCount
                                                            * contributionSquareSum
                                                    - contributionSum
                                                            * contributionSum
                                            )
                            )
                    );

            double blurContributionCorrelation =
                    correlationCount >= 2
                                    && correlationDenominator > 1e-12
                            ? correlationNumerator
                                    / correlationDenominator
                            : Double.NaN;

            processingParameters.temporalPerFrameDiagnosticCount =
                    motionPerFrameContributionDeltaMean.size();

            processingParameters
                    .temporalSlowShutterContributionMean =
                    (float) slowMean;

            processingParameters
                    .temporalFastShutterContributionMean =
                    (float) fastMean;

            processingParameters
                    .temporalBlurContributionCorrelation =
                    (float) blurContributionCorrelation;

            Log.d(
                    TAG,
                    "MOTION_26215_SLOW_SHUTTER_CORRELATION"
                            + " slowThresholdMs=45.0"
                            + " slowCount="
                            + slowShutterContributionCount
                            + " slowContributionMean="
                            + slowMean
                            + " fastCount="
                            + fastShutterContributionCount
                            + " fastContributionMean="
                            + fastMean
                            + " blurContributionCorrelation="
                            + blurContributionCorrelation
                            + " correlationDefinition="
                            + "pearsonShutterMotionVsContribution"
                            + " perFrameDiagnostics="
                            + motionPerFrameContributionDeltaMean
                                    .size()
            );
        }

        processingParameters.noiseModeler.computeStackingNoiseModel(
                processingParameters.effectiveFrameCount
        );

        Log.d(
                TAG,
                "MOTION_26172_LOCAL_STACK_MODEL"
                        + " retained="
                        + processingParameters.retainedFrameCount
                        + " measured="
                        + processingParameters.localContributionMeasured
                        + " effective="
                        + processingParameters.effectiveFrameCount
                        + " ratio="
                        + processingParameters.effectiveStackRatio
                        + " mean="
                        + processingParameters.localContributionMean
                        + " p10="
                        + processingParameters.localContributionP10
                        + " p25="
                        + processingParameters.localContributionP25
                        + " p50="
                        + processingParameters.localContributionP50
                        + " p75="
                        + processingParameters.localContributionP75
                        + " p90="
                        + processingParameters.localContributionP90
                        + " below4="
                        + processingParameters.localContributionBelow4
                        + " below8="
                        + processingParameters.localContributionBelow8
                        + " below12="
                        + processingParameters.localContributionBelow12
                        + " below16="
                        + processingParameters.localContributionBelow16
                        + " dngNoiseModelSelectedBeforeSave=true"
                        + " jpegNoiseModelUpdated=true"
                        + " adaptiveNoiseSettingUnchanged=true"
        );

        if ((saveRAW >= 1) && alignAlgorithm != 2) {
            boolean imageSaved = ImageSaver.Util.saveStackedRaw(dngFile, output,
                    processingParameters);
            processingEventsListener.notifyImageSavedStatus(imageSaved, dngFile);
            if (saveRAW == 2) {
                processingEventsListener.onProcessingFinished("HdrX RAW Processing Finished");
                callback.onFinished();
                Allocator.free(output);
                Allocator.getMemoryCount();
                return;
            }
        }

        Log.d(
                TAG,
                "MOTION_26172_COLOR_AND_STACK_HANDOFF"
                        + " retained="
                        + processingParameters.retainedFrameCount
                        + " effective="
                        + processingParameters.effectiveFrameCount
                        + " ratio="
                        + processingParameters.effectiveStackRatio
                        + " localContributionMeasured="
                        + processingParameters.localContributionMeasured
                        + " processingCore=26171"
                        + " colorNeutral=burstValidated"
                        + " matrixConvention=unchanged"
                        + " gainMapConvention=unchanged"
                        + " adaptiveNoiseSettingUnchanged=true"
        );

        PostPipeline pipeline = new PostPipeline();

        Bitmap img = pipeline.Run(output, processingParameters);

        if (processingParameters.motionCapture) {
            Log.w(
                    TAG,
                    "MOTION_26232_DIAGNOSTIC_END"
                            + " retainedFrames="
                            + processingParameters.retainedFrameCount
                            + " effectiveFrames="
                            + processingParameters.effectiveFrameCount
                            + " effectiveRatio="
                            + processingParameters.effectiveStackRatio
                            + " contributionMeasured="
                            + processingParameters.localContributionMeasured
                            + " contributionP25="
                            + processingParameters.localContributionP25
                            + " iso=" + processingParameters.iso
                            + " exposureSeconds="
                            + processingParameters.exposureTime
                            + " completedPipeline=true"
            );
        }

        Allocator.free(output);

        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));

        /*
         * Preserve Photo/Night UI timing. Motion completion is delayed until
         * after the JPEG is written and the ImageSaved callback is delivered.
         */
        if (cameraMode != CameraMode.MOTION) {
            try {
                processingEventsListener.onProcessingFinished(
                        "HdrX JPG Processing Finished"
                );
            }
            catch (Exception e){
                Log.d(
                        TAG,
                        "Error in processingEventsListener.onProcessingFinished:"
                                + Log.getStackTraceString(e)
                );
            }
        }

        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
        //Saves the final bitmap
        /* Refresh finalized processing metadata before saving. */
        exifData.IMAGE_DESCRIPTION = processingParameters.toString();

        Log.d(
                TAG,
                "Saving final metadata: retained="
                        + processingParameters.retainedFrameCount
                        + " effective="
                        + processingParameters.effectiveFrameCount
                        + " effectiveRatio="
                        + processingParameters.effectiveStackRatio
                        + " subpixelDiversity="
                        + processingParameters.subpixelSampleDiversity
        );

        boolean imageSaved = ImageSaver.Util.saveBitmapAsJPG(imageFile, img,
                ImageSaver.JPG_QUALITY, exifData);

        boolean saveCallbackDelivered = false;

        try {
            processingEventsListener.notifyImageSavedStatus(
                    imageSaved,
                    imageFile
            );
            saveCallbackDelivered = true;
        }
        catch (Exception e){
            Log.d(
                    TAG,
                    "Error in processingEventsListener.notifyImageSavedStatus:"
                            + Log.getStackTraceString(e)
            );
        }

        if (cameraMode == CameraMode.MOTION) {
            boolean fileExists =
                    imageFile != null
                            && imageFile.toFile().exists();

            long fileBytes =
                    fileExists
                            ? imageFile.toFile().length()
                            : 0L;

            Log.d(
                    TAG,
                    "MOTION_26166_IMAGE_SAVED_COMPLETE"
                            + " success=" + imageSaved
                            + " callbackDelivered="
                            + saveCallbackDelivered
                            + " exists=" + fileExists
                            + " bytes=" + fileBytes
                            + " path=" + imageFile
            );

            try {
                processingEventsListener.onProcessingFinished(
                        imageSaved
                                ? "HdrX JPG Saved"
                                : "HdrX JPG Save Failed"
                );
            }
            catch (Exception e){
                Log.d(
                        TAG,
                        "Error in Motion post-save onProcessingFinished:"
                                + Log.getStackTraceString(e)
                );
            }
        }

        pipeline.close();

        if (cameraMode == CameraMode.MOTION) {
            Log.d(
                    TAG,
                    "MOTION_26286_HIGHLIGHT_SHADOW_CHROMA_HALO_COMPLETE"
                            + " success=" + imageSaved
                            + " retained="
                            + processingParameters.retainedFrameCount
                            + " effective="
                            + processingParameters.effectiveFrameCount
                            + " ratio="
                            + processingParameters.effectiveStackRatio
                            + " localContributionMeasured="
                            + processingParameters.localContributionMeasured
                            + " localMean="
                            + processingParameters.localContributionMean
                            + " localP10="
                            + processingParameters.localContributionP10
                            + " localP25="
                            + processingParameters.localContributionP25
                            + " localP50="
                            + processingParameters.localContributionP50
                            + " localP75="
                            + processingParameters.localContributionP75
                            + " localP90="
                            + processingParameters.localContributionP90
            );
            boolean flushed = Log.flushAndWait(5000L);
            android.util.Log.d(
                    TAG,
                    "MOTION_26280_LOG_FLUSH success=" + flushed
            );
        }

        Allocator.getMemoryCount();
        callback.onFinished();
    }

}
