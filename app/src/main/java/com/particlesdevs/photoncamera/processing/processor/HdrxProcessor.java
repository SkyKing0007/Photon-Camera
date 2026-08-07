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

        if (images.size() > 10) {
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
        }
        selected = 0;



        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
        Log.d(TAG, "Wrapper.loadFrame");
        //float noiseLevel = (float) Math.sqrt((CaptureController.mCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY)) *
        //        IsoExpoSelector.getMPY() - 40.)*6400.f / (6.2f*IsoExpoSelector.getISOAnalog());

        ByteBuffer output = null;
        Log.d(TAG, "Packing");
        //WrapperAl.packImages();
        Log.d(TAG, "Packed");
        if(images.size() > 1) {
            PyramidMerging pyramidMerging = new PyramidMerging(
                    new Point(width, height), images, cameraMode == CameraMode.MOTION);
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

        processingParameters.noiseModeler.computeStackingNoiseModel(images.size());

        PostPipeline pipeline = new PostPipeline();

        Bitmap img = pipeline.Run(output, processingParameters);
        Allocator.free(output);

        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));
        try {
            processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));
        }
        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
        //Saves the final bitmap
        boolean imageSaved = ImageSaver.Util.saveBitmapAsJPG(imageFile, img,
                ImageSaver.JPG_QUALITY, exifData);

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

}
