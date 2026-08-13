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
import com.particlesdevs.photoncamera.processing.MotionMetrics;
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
            Log.e(TAG, "Error in HdrX Processing:"
                    + Log.getStackTraceString(e));
            com.particlesdevs.photoncamera.util.MotionTrace.error(
                    -1L,
                    "HDRX_PROCESSOR",
                    e);
            callback.onFailed();
            processingEventsListener.onProcessingError(
                    e.getClass().getSimpleName()
                            + ": " + String.valueOf(e.getMessage()));
        }
        finally {
            // IRIS_26338_MOTION_METRICS_FINALLY
            MotionMetrics.end();
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
        processingParameters.FillConstParameters(characteristics, new Point(width, height));
        // sort by timestamp first
        mImageFramesToProcess.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
        double minExpo = exposures.get(mImageFramesToProcess.get(0).getTimestamp());
        for (int i = 1; i < mImageFramesToProcess.size(); i++) {
            minExpo = Math.min(minExpo, exposures.get(mImageFramesToProcess.get(i).getTimestamp()));
        }

        /*
         * IRIS_26363_MOTION_REFERENCE_OWNERSHIP
         *
         * Motion already carries a timestamp-matched CaptureResult. Keep the
         * merged Bayer reference anchored to that same physical RAW instead
         * of silently replacing it with the darkest/minimum-energy frame.
         */
        final boolean iris26363MotionReferenceOwnership =
                cameraMode == CameraMode.MOTION;
        long iris26363ReferenceTimestamp = Long.MIN_VALUE;
        double iris26363ReferenceEnergy = minExpo;

        if (iris26363MotionReferenceOwnership) {
            Long iris26363ResultTimestamp =
                    captureResult == null
                            ? null
                            : captureResult.get(CaptureResult.SENSOR_TIMESTAMP);
            long iris26363TargetTimestamp =
                    iris26363ResultTimestamp != null
                            ? iris26363ResultTimestamp
                            : mImageFramesToProcess.get(
                                    mImageFramesToProcess.size() - 1).getTimestamp();

            long iris26363BestDelta = Long.MAX_VALUE;
            for (ImageFrame iris26363Frame : mImageFramesToProcess) {
                Double iris26363EnergyObj =
                        exposures.get(iris26363Frame.getTimestamp());
                if (iris26363EnergyObj == null
                        || iris26363EnergyObj <= 0.0) {
                    continue;
                }

                long iris26363Delta = Math.abs(
                        iris26363Frame.getTimestamp()
                                - iris26363TargetTimestamp);
                if (iris26363Delta < iris26363BestDelta) {
                    iris26363BestDelta = iris26363Delta;
                    iris26363ReferenceTimestamp =
                            iris26363Frame.getTimestamp();
                    iris26363ReferenceEnergy =
                            iris26363EnergyObj;
                }
            }

            if (iris26363ReferenceTimestamp == Long.MIN_VALUE) {
                ImageFrame iris26363Fallback =
                        mImageFramesToProcess.get(
                                mImageFramesToProcess.size() - 1);
                iris26363ReferenceTimestamp =
                        iris26363Fallback.getTimestamp();
                Double iris26363FallbackEnergy =
                        exposures.get(iris26363ReferenceTimestamp);
                if (iris26363FallbackEnergy != null
                        && iris26363FallbackEnergy > 0.0) {
                    iris26363ReferenceEnergy =
                            iris26363FallbackEnergy;
                }
            }

            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "MOTION_REFERENCE_OWNERSHIP",
                    "metadataTimestamp=" + iris26363ResultTimestamp
                            + " chosenRawTimestamp="
                            + iris26363ReferenceTimestamp
                            + " matchDeltaNs="
                            + iris26363BestDelta
                            + " referenceEnergy="
                            + iris26363ReferenceEnergy
                            + " minBurstEnergy=" + minExpo
                            + " policy=metadataMatchedReference"
                            + " captureAeBehavior=unchanged");
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
            frame.pair = IsoExpoSelector.fullpairs.get(i);
            frame.number = i;
            double iris26363FrameEnergy =
                    exposures.get(mImageFramesToProcess.get(i).getTimestamp());
            if (iris26363MotionReferenceOwnership) {
                // Actual exposure-energy ratio relative to the owned reference.
                // PyramidMerging uses 1/layerMpy to radiometrically normalize
                // the alternate to this reference. It is not an HDR bracket.
                frame.pair.layerMpy = (float) (
                        iris26363FrameEnergy
                                / Math.max(iris26363ReferenceEnergy, 1e-12));
                frame.pair.curlayer =
                        IsoExpoSelector.ExpoPair.exposureLayer.Normal;
                normalFrames++;
            } else {
                frame.pair.layerMpy = (float) (
                        iris26363FrameEnergy / minExpo);
                if (frame.pair.layerMpy > 1.0) {
                    frame.pair.curlayer =
                            IsoExpoSelector.ExpoPair.exposureLayer.High;
                } else {
                    frame.pair.curlayer =
                            IsoExpoSelector.ExpoPair.exposureLayer.Normal;
                    normalFrames++;
                }
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

        processingParameters.FillDynamicParameters(captureResult, captureRequest,ISO);
        processingParameters.cameraRotation = cameraRotation;

        exifData.IMAGE_DESCRIPTION = processingParameters.toString()
                + "\n" + com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector
                .lastMotionExposureDiagnostics;
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

        /*
         * IRIS_26431_MOTION_V2_ALL_FRAME_HANDOFF
         * Motion V2 owns local rejection. Do not globally throw away Motion RAWs.
         */
        if (cameraMode == CameraMode.MOTION) {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "FRAME_RETENTION",
                    "inputFrames=" + mImageFramesToProcess.size()
                            + " retainedFrames=" + images.size()
                            + " targetFraction=1.0"
                            + " globalGyroDiscard=false"
                            + " localConfidenceAuthority=MotionV2"
                            + " referenceFallback=true"
                            + " averageShakiness=" + unluckyavr
                            + " pickinessDiagnosticOnly=" + unluckypickiness);
        } else if (images.size() > 10) {
            int size = (int) (images.size() - FrameNumberSelector.throwCount);
            Log.d(TAG, "Throw Count:" + size);
            Log.d(TAG, "Image Count:" + images.size());
            //if (size == images.size())
                size = (int) (images.size() * 0.75);
            for (int i = images.size(); i > size; i--) {
                ImageFrame cur = images.get(images.size() - 1);
                float curunlucky = cur.frameGyro.shakiness;
                if (curunlucky > unluckyavr * unluckypickiness) {
                    if (iris26363MotionReferenceOwnership
                            && cur.timestamp
                                    == iris26363ReferenceTimestamp) {
                        // Preserve the RAW that owns downstream dynamic metadata.
                        continue;
                    }
                    if(normalFrames == 1 && cur.pair.curlayer == IsoExpoSelector.ExpoPair.exposureLayer.Normal) {
                        continue;
                    }
                    if(cur.pair.curlayer == IsoExpoSelector.ExpoPair.exposureLayer.Normal){
                        normalFrames--;
                    }
                    Log.d(TAG, "Removing unlucky:" + curunlucky + " number:" + images.get(images.size() - 1).number);
                    images.get(images.size() - 1).close();
                    images.remove(images.size() - 1);
                }
            }
            Log.d(TAG, "Size after removal:" + images.size());
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "FRAME_RETENTION",
                    "inputFrames=" + mImageFramesToProcess.size()
                            + " retainedFrames=" + images.size()
                            + " targetFraction=0.75"
                            + " averageShakiness=" + unluckyavr
                            + " pickiness=" + unluckypickiness);
        }

        float minMpy = 1000.f;
        int selected = 0;

        if (iris26363MotionReferenceOwnership) {
            boolean iris26363ReferenceFound = false;
            for (int i = 0; i < images.size(); i++) {
                if (images.get(i).timestamp
                        == iris26363ReferenceTimestamp) {
                    selected = i;
                    iris26363ReferenceFound = true;
                    break;
                }
            }

            if (!iris26363ReferenceFound) {
                long iris26363BestDelta = Long.MAX_VALUE;
                for (int i = 0; i < images.size(); i++) {
                    long iris26363Delta = Math.abs(
                            images.get(i).timestamp
                                    - iris26363ReferenceTimestamp);
                    if (iris26363Delta < iris26363BestDelta) {
                        iris26363BestDelta = iris26363Delta;
                        selected = i;
                    }
                }
            }
        } else {
            for (int i = 0; i < images.size(); i++) {
                if (images.get(i).pair.layerMpy < minMpy) {
                    minMpy = images.get(i).pair.layerMpy;
                }
            }
            for (int i = 0; i < images.size(); i++) {
                if(images.get(i).pair.layerMpy == minMpy){
                    selected = i;
                    break;
                }
            }
        }

        // move selected image to 0 index
        if(selected != 0){
            ImageFrame frame = images.get(0);
            images.set(0, images.get(selected));
            images.set(selected, frame);
        }

        if (iris26363MotionReferenceOwnership) {
            images.get(0).pair.layerMpy = 1.0f;
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "MOTION_REFERENCE_AFTER_RETENTION",
                    "rawTimestamp=" + images.get(0).timestamp
                            + " layerMpy=" + images.get(0).pair.layerMpy
                            + " retainedFrames=" + images.size()
                            + " policy=ownedReferencePreserved");

            /*
             * IRIS_26450_MOTION_V2_REFERENCE_DNG
             * Save the true timestamp-owned Bayer reference while its original
             * RAW buffer is still alive. This is single-frame sensor RAW:
             * no multiframe NR, no demosaic, no V2 RGB processing.
             */
            ByteBuffer iris26450ReferenceDng =
                    images.get(0).buffer == null
                            ? null
                            : images.get(0).buffer.duplicate();
            if (iris26450ReferenceDng == null) {
                throw new IllegalStateException(
                        "Motion V2 reference DNG buffer is null");
            }
            iris26450ReferenceDng.position(0);
            boolean iris26450DngSaved =
                    ImageSaver.Util.saveStackedRaw(
                            dngFile,
                            iris26450ReferenceDng,
                            processingParameters);
            processingEventsListener.notifyImageSavedStatus(
                    iris26450DngSaved,
                    dngFile);
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26450_MOTION_V2_REFERENCE_DNG",
                    "saved=" + iris26450DngSaved
                            + " rawTimestamp=" + images.get(0).timestamp
                            + " source=timestampOwnedReferenceBayer"
                            + " multiframeNr=false"
                            + " bakedRgb=false");
        }
        selected = 0;



        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
        Log.d(TAG, "Wrapper.loadFrame");
        //float noiseLevel = (float) Math.sqrt((CaptureController.mCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY)) *
        //        IsoExpoSelector.getMPY() - 40.)*6400.f / (6.2f*IsoExpoSelector.getISOAnalog());

        ByteBuffer output = null;

        /*
         * IRIS_26379_PRODUCTION_DIAGNOSTIC_CLEANUP
         *
         * Remove the 26370-26378 full-resolution CPU diagnostic/hot-pixel
         * passes from normal Motion processing. The utility source remains
         * available for explicit audit builds, but a normal shutter does not
         * scan or mutate RAW buffers here.
         */
        if (cameraMode == CameraMode.MOTION) {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "PRODUCTION_CLEANUP_26379",
                    "cpuRawDiagnostics=false"
                            + " transientRawReplacement=false"
                            + " persistentCpuRepair=false"
                            + " hfCpuScan=false");
        }

        Log.d(TAG, "Packing");
        //WrapperAl.packImages();
        Log.d(TAG, "Packed");
        /*
         * IRIS_26409_MOTION_V2_INDEPENDENT_RAW_OWNER
         *
         * Motion no longer enters PyramidMerging in V2 milestone 1.
         * The metadata-owned reference RAW is the structural owner.
         * Auxiliary contribution is deliberately zero until the new
         * confidence/residual fusion math is introduced in V2 itself.
         */
        if (cameraMode == CameraMode.MOTION) {
            processingParameters.motionV2Active = true;
            MotionV2Merger.Result iris26409V2 =
                    MotionV2CfaReconstruction.reconstruct(
                            new Point(width, height),
                            images,
                            iris26363ReferenceTimestamp,
                            processingParameters);
            output = iris26409V2.raw;
            processingParameters.motionV2EffectiveSupport =
                    iris26409V2.effectiveSupport;
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26409_MOTION_V2_FOUNDATION",
                    "referenceTimestamp=" + iris26409V2.referenceTimestamp
                            + " inputFrames=" + iris26409V2.inputFrames
                            + " effectiveSupport="
                            + iris26409V2.effectiveSupport
                            + " currentPyramidMergeBypassed=true"
                            + " reconstruction=IRIS_26413_REFERENCE_PRESERVING_CFA"
                            + " auxiliaryContribution=confidenceWeighted");
        } else if(images.size() > 1) {
            PyramidMerging pyramidMerging = new PyramidMerging(
                    new Point(width, height), images, false);
            pyramidMerging.parameters = processingParameters;
            pyramidMerging.Run();
            pyramidMerging.close();
            output = pyramidMerging.Output;

            for (int i = 0; i < images.size(); i++) {
                images.get(i).close();
            }
            IncreaseWLBL(processingParameters);
        } else {
            output = images.get(0).buffer;
            images.get(0).buffer = null;
        }
        Log.d(TAG, "HDRX Alignment elapsed:" + (System.currentTimeMillis() - startTime) + " ms");
        /*
         * IRIS_26414_MOTION_V2_FLOAT_CFA_DNG_GUARD
         * Motion V2 output is now a FLOAT16 CFA carrier at this point.
         * Do not serialize it through the legacy RAW16 DNG writer.
         */
        if ((saveRAW >= 1)
                && alignAlgorithm != 2
                && cameraMode != CameraMode.MOTION) {
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

        /*
         * IRIS_26409_MOTION_V2_NORMALIZATION_OWNER
         * V2 owns its normalization math. The old Iris floor-risk canonical
         * estimator is not used by Motion V2.
         */
        if (cameraMode == CameraMode.MOTION) {
            /*
             * IRIS_26414_REFERENCE_RAW_NORMALIZATION_BEFORE_FLOAT_RECON
             * MotionV2CfaReconstruction computed this from the physical
             * reference RAW before the burst buffers were closed.
             */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26414_MOTION_V2_NORMALIZATION",
                    "gain=" + processingParameters.motionCanonicalExposureGain
                            + " source=ownedReferenceRawPreReconstruction"
                            + " floatCarrierNotReparsed=true"
                            + " floorSuppression=false");
        } else {
            processingParameters.motionCanonicalExposureGain = 1.0f;
        }

        /*
         * IRIS_26409_MOTION_V2_TRUTHFUL_SUPPORT
         * Milestone 1 contains one effective structural sample, regardless of
         * how many RAWs arrived in the batch.
         */
        /*
         * IRIS_26414_MOTION_V2_SUPPORT_DRIVEN_NOISE_MODEL
         * Use the actually measured temporal contribution instead of the old
         * reference-only support=1 assumption.
         */
        processingParameters.noiseModeler.computeStackingNoiseModel(
                cameraMode == CameraMode.MOTION
                        ? Math.max(
                                1,
                                Math.round(
                                        processingParameters.motionV2EffectiveSupport))
                        : images.size());

        PostPipeline pipeline = new PostPipeline();

        Bitmap img;
        if (cameraMode == CameraMode.MOTION) {
            /*
             * IRIS_26414_MOTION_V2_FLOAT_CFA_HANDOFF
             * No reconstructed-CFA -> RAW16 -> Bayer2Float round trip.
             */
            img = pipeline.RunMotionV2FloatCfa(
                    output,
                    processingParameters);
            output = null;
        } else {
            img = pipeline.Run(output, processingParameters);
            Allocator.free(output);
            output = null;
        }

        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));
        try {
            processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));
        }
        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
        //Saves the final bitmap
        final boolean imageSaved;
        if (cameraMode == CameraMode.MOTION) {
            /*
             * IRIS_26432_MOTION_V2_TRUE_LINEAR_GAINMAP
             * Generic bitmap-derived Ultra HDR is bypassed for Motion.
             */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26431_MOTION_V2_JPEG_OWNERSHIP",
                    "syntheticBitmapGainMap=false"
                            + " sdrBase=true"
                            + " trueV2LinearGainMap=true"
                            + " bodyGainUnity=true");
            imageSaved = ImageSaver.Util.saveBitmapAsJPGMotionV2(
                    imageFile, img, ImageSaver.JPG_QUALITY, exifData);
        } else {
            imageSaved = ImageSaver.Util.saveBitmapAsJPG(
                    imageFile, img, ImageSaver.JPG_QUALITY, exifData);
        }

        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));
        }

        pipeline.close();


        Allocator.getMemoryCount();
        callback.onFinished();
    }


    /*
     * IRIS_26394 canonical exposure estimator.
     * x = clamp((raw-black)/(white-black), 0, 1)
     * p50 target = 0.055 linear
     * p90 target = 0.20 linear
     * p99.5 after gain <= 0.90
     * gain <= 8x (+3 EV)
     */
    private float computeMotionCanonicalExposureGain(
            ByteBuffer raw,
            int width,
            int height,
            Parameters parameters) {
        if (raw == null || width <= 0 || height <= 0
                || parameters == null || parameters.whiteLevel <= 0) {
            return 1.0f;
        }

        final float targetP50 = 0.055f;
        final float targetP90 = 0.20f;
        final float safeP995 = 0.90f;
        final float maxGain = 8.0f;
        final float epsilon = 1.0e-6f;
        final int bins = 4096;

        int[] hist = new int[bins];
        long samples = 0L;
        long floorSamples = 0L;

        java.nio.ByteBuffer view = raw.duplicate();
        view.clear();
        view.order(java.nio.ByteOrder.nativeOrder());
        java.nio.ShortBuffer shorts = view.asShortBuffer();

        int availablePixels = shorts.capacity();
        long requestedPixels = (long) width * (long) height;
        int pixelCount = (int) Math.min(
                (long) availablePixels,
                Math.min(requestedPixels, (long) Integer.MAX_VALUE));
        if (pixelCount <= 0) return 1.0f;

        double targetBaseSamples = 120000.0;
        int step = Math.max(
                2,
                (int) Math.floor(
                        Math.sqrt(
                                Math.max(
                                        1.0,
                                        ((double) pixelCount) / targetBaseSamples))));

        float white = (float) parameters.whiteLevel;

        for (int y = 0; y < height; y += step) {
            for (int x = 0; x < width; x += step) {
                for (int dy = 0; dy < 2; dy++) {
                    int yy = y + dy;
                    if (yy >= height) continue;
                    for (int dx = 0; dx < 2; dx++) {
                        int xx = x + dx;
                        if (xx >= width) continue;
                        int index = yy * width + xx;
                        if (index < 0 || index >= pixelCount) continue;

                        int rawValue = java.lang.Short.toUnsignedInt(shorts.get(index));
                        int blackIndex = ((yy & 1) << 1) | (xx & 1);
                        float black = parameters.blackLevel[blackIndex];
                        float span = Math.max(1.0f, white - black);
                        float normalized = (rawValue - black) / span;
                        normalized = Math.max(0.0f, Math.min(1.0f, normalized));
                        if (normalized <= 0.005f) {
                            floorSamples++;
                        }

                        int bin = Math.min(
                                bins - 1,
                                Math.max(0, (int) (normalized * (bins - 1))));
                        hist[bin]++;
                        samples++;
                    }
                }
            }
        }

        if (samples < 64L) return 1.0f;

        float p50 = histogramQuantile(hist, samples, 0.50f);
        float p90 = histogramQuantile(hist, samples, 0.90f);
        float p99 = histogramQuantile(hist, samples, 0.99f);
        float p995 = histogramQuantile(hist, samples, 0.995f);
        float floorFraction = floorSamples / (float) samples;

        /*
         * IRIS_26402_SCENE_AWARE_CANONICAL_NORMALIZATION
         *
         * A tiny extreme highlight/specular tail must not veto normalization
         * of the other ~99% of the merged RAW. Use p99 as the broad-highlight
         * headroom authority and retain p99.5 only as diagnostic evidence.
         *
         * This is intentionally compatible with equal-exposure HDR+ logic:
         * broad highlights/cloud fields remain protected because they occupy
         * enough area to raise p99, while isolated bulbs/speculars are allowed
         * to roll into the later highlight/tone pipeline instead of forcing
         * the entire frame dark.
         *
         * Shadow amplification trust is separately limited by:
         * - actual near-floor occupancy,
         * - effective temporal stack support,
         * - and ISO/noise risk.
         */
        final float safeP99 = 0.88f;
        final float canonicalMaxGain26402 = 4.0f;

        float floorRisk = Math.max(
                0.0f,
                Math.min(
                        1.0f,
                        (floorFraction - 0.10f) / 0.45f));

        float effectiveStackRatio =
                MotionMetrics.isActive()
                        ? MotionMetrics.effectiveStackRatio()
                        : 1.0f;
        effectiveStackRatio =
                Math.max(0.10f, Math.min(1.0f, effectiveStackRatio));

        float iso =
                Math.max(1.0f, parameters.iso);
        float isoRisk =
                Math.max(
                        0.0f,
                        Math.min(
                                1.0f,
                                (iso - 800.0f) / 2400.0f));

        float recoverability =
                effectiveStackRatio
                        * (1.0f - 0.60f * isoRisk);

        float signalGainLimit =
                2.0f
                        + 4.0f
                        * recoverability
                        * (1.0f - 0.55f * floorRisk);
        signalGainLimit =
                Math.max(1.5f, Math.min(6.0f, signalGainLimit));

        float gain50 = targetP50 / Math.max(p50, epsilon);
        float gain90 = targetP90 / Math.max(p90, epsilon);
        float sceneGain = (float) Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));

        float broadHighlightHeadroomGain =
                safeP99 / Math.max(p99, epsilon);

        float gain = Math.min(
                sceneGain,
                Math.min(
                        broadHighlightHeadroomGain,
                        signalGainLimit));
        gain =
                Math.max(
                        1.0f,
                        Math.min(
                                Math.min(maxGain, canonicalMaxGain26402),
                                gain));
        if (gain < 1.02f) gain = 1.0f;

        Log.d(TAG,
                "IRIS_26394_CANONICAL_RAW_STATS"
                        + " build=26402"
                        + " samples=" + samples
                        + " p50=" + p50
                        + " p90=" + p90
                        + " p99=" + p99
                        + " p995=" + p995
                        + " floorFraction=" + floorFraction
                        + " effectiveStackRatio=" + effectiveStackRatio
                        + " iso=" + iso
                        + " isoRisk=" + isoRisk
                        + " recoverability=" + recoverability
                        + " signalGainLimit=" + signalGainLimit
                        + " gain50=" + gain50
                        + " gain90=" + gain90
                        + " sceneGain=" + sceneGain
                        + " broadHighlightHeadroomGain="
                        + broadHighlightHeadroomGain
                        + " finalGain=" + gain);
        return gain;
    }

    private float histogramQuantile(int[] hist, long total, float quantile) {
        if (hist == null || hist.length == 0 || total <= 0L) return 0.0f;
        long target = Math.max(
                1L,
                (long) Math.ceil(
                        Math.max(0.0, Math.min(1.0, quantile)) * (double) total));
        long cumulative = 0L;
        for (int i = 0; i < hist.length; i++) {
            cumulative += hist[i];
            if (cumulative >= target) {
                return ((float) i) / ((float) (hist.length - 1));
            }
        }
        return 1.0f;
    }

}
