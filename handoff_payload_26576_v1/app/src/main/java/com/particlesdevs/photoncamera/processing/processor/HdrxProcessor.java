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
    /* IRIS_26480_DEFERRED_DNG_OUTPUT_V2 */
    private static final java.util.concurrent.ExecutorService MOTION_26480_OUTPUT_EXECUTOR =
            java.util.concurrent.Executors.newSingleThreadExecutor(r -> {
                Thread out = new Thread(r, "MotionDeferredOutput"); out.setDaemon(true); return out;
            });
    private static final String TAG = "HdrxProcessor";
    private ArrayList<ImageFrame> mImageFramesToProcess;
    private HashMap<Long, Double> exposures;
    private java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair>
            mMotion26486ExposurePairs;
    private com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot
            mMotion26486ShortSlot;
    /* IRIS_26524_HDRX_ZOOM_GEOMETRY_HANDOFF */
    private float mMotion26524GlobalZoom = 1.0f;
    private float mMotion26524OpticalZoomAnchor = 1.0f;
    private float mMotion26524OutputLocalZoom = 1.0f;
    private float mMotion26524HardwareLocalZoom = 1.0f;
    private float mMotion26524ResidualSoftwareZoom = 1.0f;
    /* IRIS_26575_MOTION_SUPER_RES_HDRX_HANDOFF */
    private boolean mMotion26575SuperResEnabled = false;
    /* IRIS_26564_TRUE2X_EXCEPTION_CLEANUP_OWNER
     * Bridge handoff transfers disk-backed true-2x carriers to HdrxProcessor. These processor-level
     * references let Run() clean them on every exception path. Deferred DNG explicitly clears its
     * reference only after the background task has captured independent ownership.
     */
    private String mMotion26564True2xLinearRgbPathForCleanup;
    private String mMotion26564True2xRenderRgbPathForCleanup;
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
        this.mMotion26564True2xLinearRgbPathForCleanup = null;
        this.mMotion26564True2xRenderRgbPathForCleanup = null;
        Log.d(TAG, "HdrxProcessor called start()");
        Run();
    }

    /* IRIS_26486_HDRX_MOTIONBATCH_ENTRY */
    public void startMotion(Path dngFile, Path imageFile,
                      ParseExif.ExifData exifData,
                      ArrayList<GyroBurst> BurstShakiness,
                      ArrayList<ImageFrame> imageBuffer,
                      HashMap<Long, Double> exposures,
                      int imageFormat, int cameraRotation,
                      CameraCharacteristics characteristics,
                      CaptureResult captureResult, CaptureRequest captureRequest,
                      java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair> exposurePairs,
                      com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot shortSlot,
                      float globalZoom, float opticalZoomAnchor, float outputLocalZoom,
                      float hardwareLocalZoom, float residualSoftwareZoom,
                      boolean superResEnabled,
                      ProcessingCallback callback) {
        this.mMotion26486ExposurePairs = new java.util.ArrayList<>();
        if (exposurePairs != null) for (com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair source : exposurePairs) {
            com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair copy =
                    new com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair(source);
            copy.curlayer = com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair.exposureLayer.Normal;
            copy.layerMpy = 1.0f;
            this.mMotion26486ExposurePairs.add(copy);
        }
        this.mMotion26486ShortSlot = shortSlot;
        this.mMotion26524GlobalZoom = Math.max(0.05f, globalZoom);
        this.mMotion26524OpticalZoomAnchor = Math.max(0.05f, opticalZoomAnchor);
        this.mMotion26524OutputLocalZoom = Math.max(1.0f, outputLocalZoom);
        this.mMotion26524HardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
        this.mMotion26524ResidualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
        this.mMotion26575SuperResEnabled = superResEnabled;
        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,
                imageFormat, cameraRotation, characteristics, captureResult,
                captureRequest, callback);
    }

    public void Run() {
        Integer iris26480OriginalPriority=null;
        if(cameraMode==CameraMode.MOTION){try{int tid=android.os.Process.myTid();
            iris26480OriginalPriority=android.os.Process.getThreadPriority(tid);
            if(iris26480OriginalPriority<android.os.Process.THREAD_PRIORITY_BACKGROUND)
                android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);
            Log.d(TAG,"IRIS_26480_BACKGROUND_PROCESSING_PRIORITY active="+android.os.Process.getThreadPriority(tid));
        }catch(Throwable ignored){}}
        try {
            /* IRIS_26540_NIGHT_HDRX_ENTRY_FORBIDDEN
             * Night must enter IrisNightProcessor directly. This guard is intentionally before
             * Camera2ApiAutoFix.ApplyRes so no legacy metadata mutation can occur if routing regresses.
             */
            if (cameraMode == CameraMode.NIGHT) {
                throw new IllegalStateException("26540 Night must not enter HdrxProcessor.Run");
            }
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
            if (mMotion26486ShortSlot != null) {
                mMotion26486ShortSlot.sealAndClose();
                mMotion26486ShortSlot = null;
            }
            mMotion26486ExposurePairs = null;
            if (mMotion26564True2xLinearRgbPathForCleanup != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(mMotion26564True2xLinearRgbPathForCleanup)); } catch (Throwable ignored) {}
                mMotion26564True2xLinearRgbPathForCleanup = null;
            }
            if (mMotion26564True2xRenderRgbPathForCleanup != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(mMotion26564True2xRenderRgbPathForCleanup)); } catch (Throwable ignored) {}
                mMotion26564True2xRenderRgbPathForCleanup = null;
            }
            if(iris26480OriginalPriority!=null)try{android.os.Process.setThreadPriority(
                    android.os.Process.myTid(),iris26480OriginalPriority);}catch(Throwable ignored){}
        }
    }

    
    /* IRIS_26540_NIGHT_LEGACY_BODY_REMOVED
     * Night processing moved to IrisNightProcessor. Keeping a second compilable Night body here
     * would recreate two authorities and permit future accidental fallback.
     */
private void ApplyHdrX() {
        if (cameraMode == CameraMode.NIGHT) {
            throw new IllegalStateException("26540 architecture guard: Night legacy Hdrx path forbidden");
        }

        callback.onStarted();
        processingEventsListener.onProcessingStarted("HDRX");

        Log.d(TAG, "ApplyHdrX() called from" + Thread.currentThread().getName());

        long startTime = System.currentTimeMillis();
        Log.d(TAG, "ApplyHdrX() mImageFramesToProcess.size():" + mImageFramesToProcess.size());

        /* IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI_V2 */
        ImageFrame iris26480ShortHighlightFrame = null;
        ByteBuffer iris26480DeferredDng = null;
        /* IRIS_26522_NORMALIZED16_DNG_METADATA */
        double[] iris26522DeferredDngNoiseProfile = null;
        int iris26522DeferredDngFrameCount = 0;
        float iris26522DngSupportMin = 1.0f;
        float iris26522DngSupportP01 = 1.0f;
        float iris26522DngSupportP10 = 1.0f;
        float iris26522DngSupportMedian = 1.0f;
        float iris26522DngSupportMean = 1.0f;
        float iris26522DngSupportMax = 1.0f;
        float iris26522DngNoiseEquivalentSupport = 1.0f;
        if (cameraMode == CameraMode.MOTION) {
            for (int i = mImageFramesToProcess.size() - 1; i >= 0; i--) {
                ImageFrame candidate = mImageFramesToProcess.get(i);
                if (candidate != null && candidate.motionV2FrameRole == ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT) {
                    if (iris26480ShortHighlightFrame == null) {
                        iris26480ShortHighlightFrame = candidate;
                    } else {
                        candidate.close();
                    }
                    mImageFramesToProcess.remove(i);
                }
            }
            if (mImageFramesToProcess.isEmpty()) {
                if (iris26480ShortHighlightFrame != null) iris26480ShortHighlightFrame.close();
                throw new IllegalStateException("26480 short frame cannot replace normal Wronski group");
            }
            Log.d(TAG, "IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI"
                    + " normalFrames=" + mImageFramesToProcess.size()
                    + " shortPresent=" + (iris26480ShortHighlightFrame != null)
                    + " shortInWronskiList=false short excluded from Wronski=true");
        }
        int width = mImageFramesToProcess.get(0).width;
        int height = mImageFramesToProcess.get(0).height;
        /* IRIS_26512_MGC1271_LOGICAL_RAW_GEOMETRY
         * Motion MGC must use Camera2 logical image geometry, never rowStride/pixelStride padding.
         */
        if (cameraMode == CameraMode.MOTION
                && mImageFramesToProcess.get(0).motionV2PlaneLayoutValid) {
            width = mImageFramesToProcess.get(0).motionV2PlaneLogicalWidth;
            height = mImageFramesToProcess.get(0).motionV2PlaneLogicalHeight;
        }
        Log.d(TAG, "APPLY HDRX: buffer:" + mImageFramesToProcess.get(0).buffer.asShortBuffer().remaining());
        Log.d(TAG, "Api WhiteLevel:" + characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL));
        Log.d(TAG, "Api BlackLevel:" + characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN));
        Parameters processingParameters = new Parameters();
        processingParameters.FillConstParameters(characteristics, new Point(width, height));
        if (cameraMode == CameraMode.MOTION) {
            /* IRIS_26575_SUPER_RES_IMMUTABLE_PROCESSING_OWNER
             * The old 26532 code reread a mutable global preference here, after shutter. Motion now
             * consumes only the SR decision frozen into its immutable MotionBatch at shutter.
             */
            processingParameters.motionV2SuperResOutputEnabled = mMotion26575SuperResEnabled;
            processingParameters.motionV2SuperResOutputScale =
                    mMotion26575SuperResEnabled ? 2.0f : 1.0f;
            Log.i(TAG, "IRIS_26575_SUPER_RES_PROCESSING_SNAPSHOT frozen="
                    + mMotion26575SuperResEnabled
                    + " livePreferenceDiagnosticOnly="
                    + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                    + " outputScale=" + processingParameters.motionV2SuperResOutputScale);
            /* IRIS_26576_SR_PROCESSING_PERSISTENT_PROOF */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_PROCESSING_STATE",
                    "frozen=" + mMotion26575SuperResEnabled
                            + " livePreferenceDiagnosticOnly="
                            + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                            + " outputScale=" + processingParameters.motionV2SuperResOutputScale);
            processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom;
            processingParameters.motionV2OpticalZoomAnchor = mMotion26524OpticalZoomAnchor;
            processingParameters.motionV2OutputZoom = mMotion26524OutputLocalZoom;
            processingParameters.motionV2HardwareZoom = mMotion26524HardwareLocalZoom;
            processingParameters.motionV2ResidualSoftwareZoom = mMotion26524ResidualSoftwareZoom;
            Log.i(TAG, "IRIS_26524_MOTION_ZOOM_FROZEN"
                    + " globalZoom=" + mMotion26524GlobalZoom
                    + " opticalAnchor=" + mMotion26524OpticalZoomAnchor
                    + " outputLocalZoom=" + mMotion26524OutputLocalZoom
                    + " hardwareLocalZoom=" + mMotion26524HardwareLocalZoom
                    + " residualSoftwareZoom=" + mMotion26524ResidualSoftwareZoom);
        }
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
            if (cameraMode == CameraMode.MOTION) {
                if (mMotion26486ExposurePairs == null
                        || i >= mMotion26486ExposurePairs.size()) {
                    throw new IllegalStateException(
                            "26486 MotionBatch exposure-pair ownership mismatch");
                }
                frame.pair = new IsoExpoSelector.ExpoPair(
                        mMotion26486ExposurePairs.get(i));
                frame.pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.Normal;
                frame.pair.layerMpy = 1.0f;
            } else {
                frame.pair = IsoExpoSelector.fullpairs.get(i);
            }
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
        if (cameraMode == CameraMode.MOTION) {
            configureStrictWronskiSensorAuthority(processingParameters);
        }
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

            /* IRIS_26520_V4_REFERENCE_ONLY_DNG_REMOVED */
            iris26480DeferredDng = null;
        }
        selected = 0;

        /* IRIS_26480_PER_FRAME_NOISE_SOURCE_TRACKING_V2 */
        if(cameraMode==CameraMode.MOTION&&!images.isEmpty()){
            ImageFrame baseNoise=images.get(0);boolean baseValid=baseNoise.motionV2NoiseProfileValid;
            for(ImageFrame f:images){if(f==null)continue;
                if(!f.motionV2NoiseProfileValid&&baseValid){System.arraycopy(baseNoise.motionV2NoiseProfile,0,
                        f.motionV2NoiseProfile,0,f.motionV2NoiseProfile.length);f.motionV2NoiseProfileValid=true;
                    f.motionV2NoiseProfileSource="CAMERA2_BASE_FRAME";f.motionV2NoiseS=baseNoise.motionV2NoiseS;f.motionV2NoiseO=baseNoise.motionV2NoiseO;}
                else if(!f.motionV2NoiseProfileValid)f.motionV2NoiseProfileSource="WRONSKI_EXISTING_FALLBACK";
                com.particlesdevs.photoncamera.util.MotionTrace.processingState("IRIS_26480_FRAME_NOISE_SOURCE",
                        "timestamp="+f.timestamp+" source="+f.motionV2NoiseProfileSource+" valid="+f.motionV2NoiseProfileValid
                        +" normalizedSensorVariance=true rawCodeRangeRescale=false");
            }
        }

        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
        Log.d(TAG, "Wrapper.loadFrame");
        //float noiseLevel = (float) Math.sqrt((CaptureController.mCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY)) *
        //        IsoExpoSelector.getMPY() - 40.)*6400.f / (6.2f*IsoExpoSelector.getISOAnalog());

        ByteBuffer output = null;
        ByteBuffer motionV2HighlightProvenance = null;
        /* IRIS_26564_TRUE_2X_SINGLE_CARRIER */
        String iris26564True2xLinearRgbPath = null;
        String iris26564True2xRenderRgbPath = null;
        int iris26564True2xWidth = 0;
        int iris26564True2xHeight = 0;
        String iris26564True2xBackend = null;
        float iris26564True2xPhaseMean = 1.0f;
        float iris26564True2xPhaseP10 = 1.0f;
        long iris26564True2xReconstructionMs = 0L;
        boolean iris26545SabreSelected = false;

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
            if (iris26480ShortHighlightFrame != null) {
                if (mMotion26486ShortSlot != null)
                    mMotion26486ShortSlot.offer(iris26480ShortHighlightFrame);
                else iris26480ShortHighlightFrame.close();
                iris26480ShortHighlightFrame = null;
            }
            final int iris26520ExpectedNormalFrames = images.size();
            MotionV2Merger.Result iris26409V2 =
                    PhotonMotionMgc1271Bridge.reconstruct(
                            new Point(width, height),
                            images,
                            iris26363ReferenceTimestamp,
                            processingParameters,
                            mMotion26486ShortSlot,
                            saveRAW >= 1);
            output = iris26409V2.raw;
            motionV2HighlightProvenance = iris26409V2.highlightProvenance;
            processingParameters.motionV2EffectiveSupport =
                    iris26409V2.effectiveSupport;
            iris26564True2xLinearRgbPath = iris26409V2.true2xLinearRgbPath;
            iris26564True2xRenderRgbPath = iris26409V2.true2xRenderRgbPath;
            mMotion26564True2xLinearRgbPathForCleanup = iris26564True2xLinearRgbPath;
            mMotion26564True2xRenderRgbPathForCleanup = iris26564True2xRenderRgbPath;
            iris26564True2xWidth = iris26409V2.true2xWidth;
            iris26564True2xHeight = iris26409V2.true2xHeight;
            iris26564True2xBackend = iris26409V2.true2xBackend;
            iris26564True2xPhaseMean = iris26409V2.true2xPhaseSupportMean;
            iris26564True2xPhaseP10 = iris26409V2.true2xPhaseSupportP10;
            iris26564True2xReconstructionMs = iris26409V2.true2xReconstructionMs;
            /* IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG */
            iris26480DeferredDng = iris26409V2.stackedDngRaw16;
            iris26522DeferredDngNoiseProfile = iris26409V2.dngNoiseProfile;
            iris26522DeferredDngFrameCount = iris26409V2.dngStackFrames;
            iris26522DngSupportMin = iris26409V2.dngSupportMin;
            iris26522DngSupportP01 = iris26409V2.dngSupportP01;
            iris26522DngSupportP10 = iris26409V2.dngSupportP10;
            iris26522DngSupportMedian = iris26409V2.dngSupportMedian;
            iris26522DngSupportMean = iris26409V2.dngSupportMean;
            iris26522DngSupportMax = iris26409V2.dngSupportMax;
            iris26522DngNoiseEquivalentSupport = iris26409V2.dngNoiseEquivalentSupport;
            iris26545SabreSelected = iris26409V2.sabreSelected;
            if (!iris26545SabreSelected) {
                throw new IllegalStateException("26560 Sabre-only Motion returned a non-Sabre reconstruction result");
            }
            if (processingParameters.motionV2ReconstructionOwner
                    != Parameters.MOTION_V2_RECONSTRUCTION_SABRE) {
                throw new IllegalStateException("26560 Sabre-only reconstruction owner mismatch parameters="
                        + processingParameters.motionV2ReconstructionOwner);
            }
            if (saveRAW >= 1 && iris26480DeferredDng == null) {
                throw new IllegalStateException("26545 Motion DNG requested but reconstruction sidecar is missing");
            }
            if (saveRAW >= 1 && iris26409V2.dngStackFrames != iris26520ExpectedNormalFrames) {
                throw new IllegalStateException("26545 JPEG-normal/DNG-normal population mismatch reconstruction="
                        + "SABRE"
                        + " admittedNormal=" + iris26520ExpectedNormalFrames
                        + " dng=" + iris26409V2.dngStackFrames);
            }
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG",
                    "requestedFrames=" + PhotonCamera.getSettings().frameCount
                            + " admittedNormalFrames=" + iris26520ExpectedNormalFrames
                            + " dngStackFrames=" + iris26409V2.dngStackFrames
                            + " bridgeTotalScheduledFrames=" + iris26409V2.inputFrames
                            + " effectiveSupport=" + iris26409V2.effectiveSupport
                            + " dngSupportMin=" + iris26409V2.dngSupportMin
                            + " dngSupportP01=" + iris26409V2.dngSupportP01
                            + " dngSupportP10=" + iris26409V2.dngSupportP10
                            + " dngSupportMedian=" + iris26409V2.dngSupportMedian
                            + " dngSupportMean=" + iris26409V2.dngSupportMean
                            + " dngSupportMax=" + iris26409V2.dngSupportMax
                            + " dngNoiseEquivalentSupport=" + iris26409V2.dngNoiseEquivalentSupport
                            + " dngDomain=normalized16 blackLevel=0 whiteLevel=65535"
                            + " sameAdmittedNormalPopulation=true"
                            + " shortLongBentoExcludedFromDng=true"
                            + " reconstruction=" + "SABRE"
                            + " secondAlignmentPass=false");
            if (saveRAW == 2) {
                final boolean iris26564SrDng = processingParameters.motionV2SuperResOutputEnabled
                        && iris26564True2xLinearRgbPath != null
                        && iris26564True2xWidth > 0 && iris26564True2xHeight > 0;
                boolean iris26520RawSaved;
                if (iris26564SrDng) {
                    iris26520RawSaved = com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter.write(
                            dngFile, java.nio.file.Paths.get(iris26564True2xLinearRgbPath),
                            iris26564True2xWidth, iris26564True2xHeight,
                            processingParameters, iris26522DeferredDngFrameCount, iris26522DngSupportMin, iris26522DngSupportP01,
                            iris26522DngSupportP10, iris26522DngSupportMedian, iris26522DngSupportMean,
                            iris26522DngSupportMax, iris26522DngNoiseEquivalentSupport);
                    if (iris26480DeferredDng != null) {
                        try { Allocator.free(iris26480DeferredDng); } catch (Throwable ignored) {}
                        iris26480DeferredDng = null;
                    }
                } else {
                    if (processingParameters.motionV2SuperResOutputEnabled) {
                        Log.critical(TAG, "IRIS_26564_MOTION_TRUE2X_DNG_MISSING rawOnly=true");
                    }
                    ByteBuffer iris26520RawOnly = iris26480DeferredDng;
                    iris26480DeferredDng = null;
                    iris26520RawOnly.position(0);
                    iris26520RawSaved = ImageSaver.Util.saveNormalized16StackedRaw(
                            dngFile, iris26520RawOnly, processingParameters,
                            iris26522DeferredDngNoiseProfile, iris26522DeferredDngFrameCount,
                            iris26522DngSupportMin, iris26522DngSupportP01, iris26522DngSupportP10,
                            iris26522DngSupportMedian, iris26522DngSupportMean, iris26522DngSupportMax,
                            iris26522DngNoiseEquivalentSupport);
                    try { Allocator.free(iris26520RawOnly); } catch (Throwable ignored) {}
                }
                processingEventsListener.notifyImageSavedStatus(iris26520RawSaved, dngFile);
                if (output != null) { try { Allocator.free(output); } catch (Throwable ignored) {} output = null; }
                if (motionV2HighlightProvenance != null) {
                    try { Allocator.free(motionV2HighlightProvenance); } catch (Throwable ignored) {}
                    motionV2HighlightProvenance = null;
                }
                if (iris26564True2xLinearRgbPath != null) {
                    try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xLinearRgbPath)); } catch (Throwable ignored) {}
                    iris26564True2xLinearRgbPath = null;
                    mMotion26564True2xLinearRgbPathForCleanup = null;
                }
                if (iris26564True2xRenderRgbPath != null) {
                    try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xRenderRgbPath)); } catch (Throwable ignored) {}
                    iris26564True2xRenderRgbPath = null;
                    mMotion26564True2xRenderRgbPathForCleanup = null;
                }
                processingEventsListener.onProcessingFinished("Motion stacked RAW Processing Finished");
                callback.onFinished();
                return;
            }
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26409_MOTION_V2_FOUNDATION",
                    "referenceTimestamp=" + iris26409V2.referenceTimestamp
                            + " inputFrames=" + iris26409V2.inputFrames
                            + " effectiveSupport="
                            + iris26409V2.effectiveSupport
                            + " currentPyramidMergeBypassed=true"
                            + " reconstruction=" + "SABRE"
                            + " reconstructionOwner=" + processingParameters.motionV2ReconstructionOwner
                            + " auxiliaryContribution=ownedSelectedReconstruction");
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
             * The Sabre bridge owns normalized sensor-domain input before postprocessing.
             */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26490_MOTION_V2_DOMAIN_OWNERSHIP",
                    "sensorDomainScale=" + processingParameters.motionCanonicalExposureGain
                            + " displayGain=" + processingParameters.motionV2DisplayGain
                            + " sensorDomainOwner=SabreNormalizedRaw"
                            + " displayGainOwner=MotionV2DisplayExposure"
                            + " displayGainBeforeSabreResolve=false"
                            + " floatCarrierNotReparsed=true");
        } else {
            processingParameters.motionCanonicalExposureGain = 1.0f;
            processingParameters.motionV2DisplayGain = 1.0f;
            processingParameters.motionV2ShortHighlightRecoveryExecuted = false;
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
        if (cameraMode != CameraMode.MOTION) {
            processingParameters.noiseModeler.computeStackingNoiseModel(images.size());
        } else {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26477_PHOTON_STACK_NOISE_BYPASS",
                    "noiseModeler.computeStackingNoiseModel=false"
                            + " sabreNoiseMetadataOwner=Camera2_BJZHOU_MGC"
                            + " effectiveSupport="
                            + processingParameters.motionV2EffectiveSupport);
        }

        PostPipeline pipeline = new PostPipeline();

        Bitmap img;
        if (cameraMode == CameraMode.MOTION) {
            /* IRIS_26545_MOTION_LINEAR_RGB_PRODUCTION_AUTHORITY
             * PhotonMotionMgc1271Bridge.raw is the sole Sabre reconstruction's full-resolution
             * linear RGB carrier. DNG evidence is always separate and never aliases RGB.
             * Standard Bayer therefore re-enters the proven direct-RGB post graph and is never
             * reinterpreted as CFA or demosaiced again.
             */
            if (output == null)
                throw new IllegalStateException("26560 Motion Sabre RGB carrier missing");
            if (processingParameters.cfaPattern >= 0 && processingParameters.cfaPattern <= 3) {
                long expectedRgbBytes = (long) width * (long) height * 4L * 4L;
                if (output.capacity() < expectedRgbBytes)
                    throw new IllegalStateException("26534 Motion RGB carrier too small bytes="
                            + output.capacity() + " expectedAtLeast=" + expectedRgbBytes);
                if (iris26480DeferredDng != null && output == iris26480DeferredDng)
                    throw new IllegalStateException("26534 Motion production carrier aliases DNG sidecar");
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26545_MOTION_LINEAR_RGB_PRODUCTION_AUTHORITY",
                        "jpegCarrier=MGC_SABRE_RESOLVE_RGBA32F"
                                + " dngCarrier=normalized16_sidecar_separate"
                                + " rcdBypassed=true demosaicBypassed=true"
                                + " postEntry=RunMotionV2FloatCfa");
            }
            img=pipeline.RunMotionV2FloatCfa(output,motionV2HighlightProvenance,processingParameters);
            output=null;
        } else {
            img = pipeline.Run(output, processingParameters);
            Allocator.free(output);
            output = null;
        }

        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));
        /* Keep non-Motion completion timing equivalent to 26512.
         * Only Motion waits for its actual JPEG_R save/publication boundary.
         */
        if (cameraMode != CameraMode.MOTION) {
            try {
                processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");
            }
            catch (Exception e){
                Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));
            }
        }
        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");
        // Saves the final bitmap before Motion announces JPG completion.
        final long iris26513JpegSaveStartNs =
                cameraMode == CameraMode.MOTION ? System.nanoTime() : 0L;
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
                    imageFile, img, ImageSaver.JPG_QUALITY, exifData,
                    iris26564True2xRenderRgbPath, iris26564True2xWidth, iris26564True2xHeight,
                    processingParameters, pipeline.cropSize, pipeline.motionV2ToneSettingsSnapshot,
                    pipeline.motionV2WatermarkEnabled);
            // IRIS_26564_TRUE2X_RENDER_CARRIER_OWNERSHIP
            // JPEG consumes the render derivative synchronously. LinearRaw remains separate for DNG.
            if (iris26564True2xRenderRgbPath != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xRenderRgbPath)); } catch (Throwable ignored) {}
                iris26564True2xRenderRgbPath = null;
                mMotion26564True2xRenderRgbPathForCleanup = null;
            }
        } else {
            imageSaved = ImageSaver.Util.saveBitmapAsJPG(
                    imageFile, img, ImageSaver.JPG_QUALITY, exifData);
        }

        if (cameraMode == CameraMode.MOTION) {
            int iris26575JpegWidth = -1;
            int iris26575JpegHeight = -1;
            try {
                android.graphics.BitmapFactory.Options iris26575Bounds =
                        new android.graphics.BitmapFactory.Options();
                iris26575Bounds.inJustDecodeBounds = true;
                android.graphics.BitmapFactory.decodeFile(imageFile.toString(), iris26575Bounds);
                iris26575JpegWidth = iris26575Bounds.outWidth;
                iris26575JpegHeight = iris26575Bounds.outHeight;
            } catch (Throwable ignored) {}
            Log.i(TAG, "IRIS_26575_FINAL_JPEG_DIMENSION_PROOF imageSaved=" + imageSaved
                    + " frozenSuperRes=" + mMotion26575SuperResEnabled
                    + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                    + " true2xWidth=" + iris26564True2xWidth
                    + " true2xHeight=" + iris26564True2xHeight
                    + " jpegWidth=" + iris26575JpegWidth
                    + " jpegHeight=" + iris26575JpegHeight
                    + " path=" + imageFile);
            /* IRIS_26576_SR_FINAL_DIMENSION_PERSISTENT_PROOF */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_FINAL_DIMENSIONS",
                    "imageSaved=" + imageSaved
                            + " frozenSuperRes=" + mMotion26575SuperResEnabled
                            + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                            + " true2xWidth=" + iris26564True2xWidth
                            + " true2xHeight=" + iris26564True2xHeight
                            + " jpegWidth=" + iris26575JpegWidth
                            + " jpegHeight=" + iris26575JpegHeight);
        }
        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));
        }
        if (cameraMode == CameraMode.MOTION) {
            /* IRIS_26513_JPEG_COMPLETION_AFTER_SAVE
             * Motion UI completion follows the actual JPEG_R write and image-saved
             * notification. Deferred DNG remains background-only.
             */
            final long iris26513JpegSaveMs =
                    (System.nanoTime() - iris26513JpegSaveStartNs) / 1_000_000L;
            Log.d(TAG,"IRIS_26513_JPEG_COMPLETION_AFTER_SAVE"
                    + " imageSaved=" + imageSaved
                    + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs
                    + " nonMotionCompletionUnchanged=true"
                    + " deferredDngExcluded=true");
            /* IRIS_26576_SR_CAPTURE_SUMMARY
             * One compact end-of-JPEG line. Reconstruction and final dimensions are existing
             * authorities; native publication backend/timing is emitted separately by the encoder.
             */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_CAPTURE_SUMMARY",
                    "requested=" + mMotion26575SuperResEnabled
                            + " reconstructionBackend=" + iris26564True2xBackend
                            + " reconstructionMs=" + iris26564True2xReconstructionMs
                            + " phaseMean=" + iris26564True2xPhaseMean
                            + " phaseP10=" + iris26564True2xPhaseP10
                            + " true2xWidth=" + iris26564True2xWidth
                            + " true2xHeight=" + iris26564True2xHeight
                            + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs
                            + " imageSaved=" + imageSaved);
            try {
                processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");
            }
            catch (Exception e){
                Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));
            }
        }
        if(cameraMode==CameraMode.MOTION&&iris26480DeferredDng!=null){
            final ByteBuffer dngBytes=iris26480DeferredDng;final Path dngPath=dngFile;final Parameters dngParams=processingParameters;
            final double[] dngNoise=iris26522DeferredDngNoiseProfile;
            final int dngFrameCount=iris26522DeferredDngFrameCount;
            final float dngSupportMin=iris26522DngSupportMin,dngSupportP01=iris26522DngSupportP01,
                    dngSupportP10=iris26522DngSupportP10,dngSupportMedian=iris26522DngSupportMedian,
                    dngSupportMean=iris26522DngSupportMean,dngSupportMax=iris26522DngSupportMax,
                    dngNoiseEquivalent=iris26522DngNoiseEquivalentSupport;
            final String srLinearRawPath=iris26564True2xLinearRgbPath;
            final int srLinearRawWidth=iris26564True2xWidth;
            final int srLinearRawHeight=iris26564True2xHeight;
            final boolean srLinearDng=dngParams.motionV2SuperResOutputEnabled
                    &&srLinearRawPath!=null&&srLinearRawWidth>0&&srLinearRawHeight>0;
            MOTION_26480_OUTPUT_EXECUTOR.execute(()->{Integer old=null;try{int tid=android.os.Process.myTid();
                old=android.os.Process.getThreadPriority(tid);android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);
                final boolean saved;
                if(srLinearDng){
                    saved=com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter.write(
                            dngPath,java.nio.file.Paths.get(srLinearRawPath),srLinearRawWidth,srLinearRawHeight,
                            dngParams,dngFrameCount,dngSupportMin,dngSupportP01,dngSupportP10,
                            dngSupportMedian,dngSupportMean,dngSupportMax,dngNoiseEquivalent);
                }else{
                    if(dngParams.motionV2SuperResOutputEnabled)Log.critical(TAG,"IRIS_26564_MOTION_TRUE2X_DNG_MISSING deferred=true");
                    dngBytes.position(0);saved=ImageSaver.Util.saveNormalized16StackedRaw(
                            dngPath,dngBytes,dngParams,dngNoise,dngFrameCount,
                            dngSupportMin,dngSupportP01,dngSupportP10,dngSupportMedian,
                            dngSupportMean,dngSupportMax,dngNoiseEquivalent);
                }
                processingEventsListener.notifyImageSavedStatus(saved,dngPath);Log.d(TAG,"IRIS_26545_DEFERRED_DNG_FINISHED saved="+saved+" normalizedStacked=true srLinearRaw="+srLinearDng);
            }catch(Exception e){Log.e(TAG,"IRIS_26480_DEFERRED_DNG_FAILED "+Log.getStackTraceString(e));}
            finally{try{Allocator.free(dngBytes);}catch(Throwable ignored){}
                if(srLinearRawPath!=null)try{java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(srLinearRawPath));}catch(Throwable ignored){}
                if(old!=null)try{android.os.Process.setThreadPriority(android.os.Process.myTid(),old);}catch(Throwable ignored){}}});
            iris26480DeferredDng=null;
            iris26564True2xLinearRgbPath=null;
            mMotion26564True2xLinearRgbPathForCleanup=null;
        } else if (cameraMode==CameraMode.MOTION && iris26564True2xLinearRgbPath!=null) {
            // No DNG was requested: no consumer owns the pristine LinearRaw carrier.
            try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xLinearRgbPath)); } catch (Throwable ignored) {}
            iris26564True2xLinearRgbPath=null;
            mMotion26564True2xLinearRgbPathForCleanup=null;
        }


        pipeline.close();


        Allocator.getMemoryCount();
        callback.onFinished();
    }


    /*
     * IRIS_26560_STRICT_SABRE_SENSOR_AUTHORITY_COMPAT
     * Legacy-named fields preserve the proven Camera2 sensor-metadata boundary now consumed by Sabre.
     */
    private void configureStrictWronskiSensorAuthority(Parameters p) {
        if (p == null || characteristics == null || captureResult == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires Camera2 characteristics + timestamp result");
        }

        Integer cfa = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (cfa == null || cfa < 0 || cfa > 3) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires standard Camera2 Bayer CFA; cfa=" + cfa);
        }

        android.hardware.camera2.params.BlackLevelPattern staticBlack =
                characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        if (staticBlack == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_BLACK_LEVEL_PATTERN");
        }
        int[] staticBl = new int[4];
        staticBlack.copyTo(staticBl, 0);
        float[] strictBl = new float[] {
                staticBl[0], staticBl[1], staticBl[2], staticBl[3]
        };
        float[] dynamicBl =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamicBl != null && dynamicBl.length >= 4) {
            boolean finite = true;
            for (int i = 0; i < 4; i++) {
                finite &= Float.isFinite(dynamicBl[i]) && dynamicBl[i] >= 0.0f;
            }
            if (finite) {
                System.arraycopy(dynamicBl, 0, strictBl, 0, 4);
            }
        }

        Integer strictWhite =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (strictWhite == null || strictWhite <= 0) {
            strictWhite = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        }
        if (strictWhite == null || strictWhite <= 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing sensor white level");
        }

        android.util.Pair<Double, Double>[] profile =
                captureResult.get(CaptureResult.SENSOR_NOISE_PROFILE);
        if (profile == null || profile.length == 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_NOISE_PROFILE; Photon fallback forbidden");
        }

        double strictS;
        double strictO;
        if (profile.length >= 4) {
            strictS = (
                    profile[0].first
                            + 0.5 * (profile[1].first + profile[2].first)
                            + profile[3].first) / 3.0;
            strictO = (
                    profile[0].second
                            + 0.5 * (profile[1].second + profile[2].second)
                            + profile[3].second) / 3.0;
        } else if (profile.length >= 3) {
            strictS = (
                    profile[0].first + profile[1].first + profile[2].first) / 3.0;
            strictO = (
                    profile[0].second + profile[1].second + profile[2].second) / 3.0;
        } else {
            strictS = profile[0].first;
            strictO = profile[0].second;
        }

        if (!Double.isFinite(strictS) || !Double.isFinite(strictO)
                || strictS <= 0.0 || strictO < 0.0) {
            throw new IllegalStateException(
                    "26477 invalid Camera2 noise profile S=" + strictS + " O=" + strictO);
        }

        // Overwrite reconstruction-critical fields after TunableInjector.
        p.blackLevel = strictBl;
        p.whiteLevel = strictWhite;
        p.cfaPattern = (byte)(int)cfa;
        p.motionV2WronskiNoiseS = (float)strictS;
        p.motionV2WronskiNoiseO = (float)strictO;
        p.motionV2StrictWronskiSensorValid = true;

        String authority =
                "IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY"
                        + " cfaSource=CameraCharacteristics"
                        + " blackSource=Camera2"
                        + " whiteSource=Camera2"
                        + " noiseSource=CaptureResult.SENSOR_NOISE_PROFILE"
                        + " photonAdaptiveNoise=false"
                        + " photonNoiseModeler=false"
                        + " dynamicNoiseStore=false"
                        + " blackLevelOverride=false"
                        + " whiteLevelOverride=false"
                        + " cfaOverride=false"
                        + " noiseS=" + p.motionV2WronskiNoiseS
                        + " noiseO=" + p.motionV2WronskiNoiseO
                        + " whiteLevel=" + p.whiteLevel
                        + " cfa=" + p.cfaPattern;
        Log.d(TAG, authority);
        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                "MOTION_WRONSKI_SENSOR_AUTHORITY", authority);
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
