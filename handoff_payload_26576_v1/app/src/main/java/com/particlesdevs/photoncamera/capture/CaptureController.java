package com.particlesdevs.photoncamera.capture;
/*
 * Copyright 2020 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.graphics.Point;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CameraMetadata;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.hardware.camera2.params.MeteringRectangle;
import android.hardware.camera2.params.OutputConfiguration;
import android.hardware.camera2.params.SessionConfiguration;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.CamcorderProfile;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.SystemClock;

import com.particlesdevs.photoncamera.util.Allocator;
import com.particlesdevs.photoncamera.util.Log;
import android.util.Range;
import android.util.Rational;
import android.util.Size;
import android.util.SparseIntArray;
import android.view.Display;
import android.view.Surface;
import android.view.TextureView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.api.Camera2ApiAutoFix;
import com.particlesdevs.photoncamera.api.CameraEventsListener;
import com.particlesdevs.photoncamera.api.CameraManager2;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.api.CameraReflectionApi;
import com.particlesdevs.photoncamera.api.Settings;
import com.particlesdevs.photoncamera.api.VendorTagUtils;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.control.IrisZoomController;
import com.particlesdevs.photoncamera.control.TouchFocus;
import com.particlesdevs.photoncamera.debugclient.DebugSender;
import com.particlesdevs.photoncamera.manual.ParamController;
import com.particlesdevs.photoncamera.processing.ImageSaver;
import com.particlesdevs.photoncamera.processing.IrisNightBatch;
import com.particlesdevs.photoncamera.processing.processor.IrisNightProcessor;
import com.particlesdevs.photoncamera.processing.processor.IrisNightNeuralEnhancer;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.parameters.ExposureIndex;
import com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.processing.parameters.IrisNightExposureSelector;
import com.particlesdevs.photoncamera.processing.parameters.IrisNightFrameSelector;
import com.particlesdevs.photoncamera.processing.parameters.ResolutionSolution;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.ui.camera.CameraFragment;
import com.particlesdevs.photoncamera.ui.camera.viewmodel.TimerFrameCountViewModel;
import com.particlesdevs.photoncamera.ui.camera.views.viewfinder.AutoFitPreviewView;
import com.particlesdevs.photoncamera.ui.camera.views.viewfinder.GLPreview;
import com.particlesdevs.photoncamera.util.log.Logger;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.TestOnly;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import android.media.Image;
import java.util.ArrayDeque;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.MotionMetrics;
import com.particlesdevs.photoncamera.processing.ImageSaverSelector;
import com.particlesdevs.photoncamera.processing.SaverImplementation;

import static android.hardware.camera2.CameraMetadata.CONTROL_AE_MODE_ON;
import static android.hardware.camera2.CameraMetadata.CONTROL_AF_MODE_CONTINUOUS_VIDEO;
import static android.hardware.camera2.CameraMetadata.CONTROL_VIDEO_STABILIZATION_MODE_ON;
import static android.hardware.camera2.CameraMetadata.FLASH_MODE_TORCH;
import static android.hardware.camera2.CaptureRequest.COLOR_CORRECTION_MODE;
import static android.hardware.camera2.CaptureRequest.CONTROL_AE_MODE;
import static android.hardware.camera2.CaptureRequest.CONTROL_AE_REGIONS;
import static android.hardware.camera2.CaptureRequest.CONTROL_AF_MODE;
import static android.hardware.camera2.CaptureRequest.CONTROL_AF_REGIONS;
import static android.hardware.camera2.CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE;
import static android.hardware.camera2.CaptureRequest.FLASH_MODE;

/**
 * Class responsible for image capture and sending images for subsequent processing
 * <p>
 * All relevant events are notified to cameraEventsListener
 * <p>
 * Constructor {@link CaptureController#CaptureController(Activity, ExecutorService, CameraEventsListener)}
 */
public class CaptureController implements MediaRecorder.OnInfoListener {
    public static final int RAW_FORMAT = ImageFormat.RAW_SENSOR;
    public static final int YUV_FORMAT = ImageFormat.YUV_420_888;
    private static final String TAG = CaptureController.class.getSimpleName();
    public List<Future<?>> taskResults = new ArrayList<>();
    private final ExecutorService processExecutor;
    /**
     * Camera state: Showing camera preview.
     */
    private static final int STATE_PREVIEW = 0;
    /**
     * Camera state: Waiting for the focus to be locked.
     */
    private static final int STATE_WAITING_LOCK = 1;
    /**
     * Camera state: Waiting for the exposure to be precapture state.
     */
    private static final int STATE_WAITING_PRECAPTURE = 2;
    /**
     * Camera state: Waiting for the exposure state to be something other than precapture.
     */
    private static final int STATE_WAITING_NON_PRECAPTURE = 3;
    /**
     * Camera state: Picture was taken.
     */
    private static final int STATE_PICTURE_TAKEN = 4;
    private static final int STATE_CLOSED = 5;
    /**
     * Max preview width that is guaranteed by Camera2 API
     */
    private static final int MAX_PREVIEW_WIDTH = 1920;
    /**
     * Max preview height that is guaranteed by Camera2 API
     */
    private static final int MAX_PREVIEW_HEIGHT = 1080;
    /**
     * Timeout for the pre-capture sequence.
     */
    private static final long PRECAPTURE_TIMEOUT_MS = 100;
    private static final int SENSOR_ORIENTATION_DEFAULT_DEGREES = 90;
    private static final int SENSOR_ORIENTATION_INVERSE_DEGREES = 270;
    /**
     * Conversion from screen rotation to JPEG orientation.
     */
    private static final SparseIntArray ORIENTATIONS = new SparseIntArray();
    private static final SparseIntArray DEFAULT_ORIENTATIONS = new SparseIntArray();
    private static final SparseIntArray INVERSE_ORIENTATIONS = new SparseIntArray();

    private boolean useMaximumResolutionKey = false;

    static {
        ORIENTATIONS.append(Surface.ROTATION_0, 90);
        ORIENTATIONS.append(Surface.ROTATION_90, 0);
        ORIENTATIONS.append(Surface.ROTATION_180, 270);
        ORIENTATIONS.append(Surface.ROTATION_270, 180);
    }

    static {
        DEFAULT_ORIENTATIONS.append(Surface.ROTATION_0, 90);
        DEFAULT_ORIENTATIONS.append(Surface.ROTATION_90, 0);
        DEFAULT_ORIENTATIONS.append(Surface.ROTATION_180, 270);
        DEFAULT_ORIENTATIONS.append(Surface.ROTATION_270, 180);
    }

    static {
        INVERSE_ORIENTATIONS.append(Surface.ROTATION_0, 270);
        INVERSE_ORIENTATIONS.append(Surface.ROTATION_90, 180);
        INVERSE_ORIENTATIONS.append(Surface.ROTATION_180, 90);
        INVERSE_ORIENTATIONS.append(Surface.ROTATION_270, 0);
    }

    private Map<String, CameraCharacteristics> mCameraCharacteristicsMap = new HashMap<>();
    public static CameraCharacteristics mCameraCharacteristics;
    public static CaptureResult mCaptureResult;
    public static CaptureRequest mCaptureRequest;

    public static CaptureResult mPreviewCaptureResult;
    public static CaptureRequest mPreviewCaptureRequest;
    public static int mPreviewTargetFormat = ImageFormat.JPEG;
    public boolean isDualSession = false;
    private static int mTargetFormat = RAW_FORMAT;
    private final ParamController paramController;
    public TouchFocus mTouchFocus;

    public final boolean mFlashEnabled = false;
    private CameraEventsListener cameraEventsListener;
    /**
     * A {@link Semaphore} to prevent the app from exiting before closing the camera.
     */
    private final Semaphore mCameraOpenCloseLock = new Semaphore(1);
    private CameraManager mCameraManager;
    private CameraManager2 mCameraManager2;
    private Activity activity;
    public long mPreviewExposureTime;
    /**
     * ID of the current {@link CameraDevice}.
     */
    public int mPreviewIso;
    public Rational[] mPreviewTemp;
    public ColorSpaceTransform mColorSpaceTransform;
    /**
     * A reference to the opened {@link CameraDevice}.
     */
    public CameraDevice mCameraDevice;
    /*A {@link Handler} for running tasks in the background.*/
    public Handler mBackgroundHandler;
    /*An {@link ImageReader} that handles still image capture.*/
    public ImageReader mImageReaderPreview;
    public ImageReader mImageReaderRaw;
    /*{@link CaptureRequest.Builder} for the camera preview*/
    public CaptureRequest.Builder mPreviewRequestBuilder;
    public CaptureRequest mPreviewInputRequest;
    /**
     * The current state of camera state for taking pictures.
     */
    public int mState = STATE_PREVIEW;
    /**
     * Orientation of the camera sensor
     */
    public int mSensorOrientation;
    public int cameraRotation;
    public boolean onUnlimited = false;
    public boolean unlimitedStarted = false;
    public boolean mFlashed = false;
    public ArrayList<GyroBurst> BurstShakiness;
    /**
     * This a callback object for the {@link ImageReader}. "onImageAvailable" will be called when a
     * still image is ready to be saved.
     */
    public ImageSaver mImageSaver;
    public HashMap<Long, Double> mExposures = new HashMap<>();

    private final ArrayDeque<Image> mZslRingBuffer = new ArrayDeque<>();
    private final Object mZslBufferLock = new Object();
    private volatile boolean mZslCapturing = false;
    private final HashMap<Long, TotalCaptureResult> mZslResultMap = new HashMap<>();
    private static final int MAX_ZSL_RESULT_METADATA = 48;

    private long mMotionUnifiedExposureNs = 0L;
    private int mMotionUnifiedIso = 0;
    private long mMotionUnifiedGeneration = 0L;
    private int mMotionUnifiedSettledFrames = 0;
        // IRIS_26344_ACTUAL_EXPOSURE_GENERATION
    private long mMotionActualCandidateExposureNs = 0L;
    private int mMotionActualCandidateIso = 0;
    private int mMotionActualCandidateFrames = 0;
    private static final int MOTION_ACTUAL_GENERATION_CONFIRM_FRAMES = 6;
    private int mMotionAeProbeFrames = 0;
private long mMotionUnifiedLastUpdateMs = 0L;
    private static final long MOTION_UNIFIED_UPDATE_MIN_MS = 450L;

    // Keep preview AE active long enough to measure the scene, then enter
    // one confirmed shutter zone. Zone 0 remains automatic.
    private int mMotionAeWarmupFrames = 0;
    private boolean mMotionManualLadderActive = false;
    private boolean mMotionAeProbeActive = false;
    // IRIS_26341_MOTION_THREE_STATE_PREVIEW
    private int mMotionManualFrames = 0;
    private int mMotionCandidateZone = 0;
    private int mMotionCandidateFrames = 0;
    private int mMotionActiveZone = 0;
    // IRIS_26345_FAST_BOUNDED_METERING
    private static final int MOTION_AE_WARMUP_FRAMES = 6;
    private static final int MOTION_ZONE_CONFIRM_FRAMES = 4;
    private static final int MOTION_MANUAL_RESAMPLE_FRAMES = 45;
    private static final int MOTION_AE_PROBE_MAX_FRAMES = 24;
    private static final long MOTION_ZONE_30_ENERGY = 12_000_000_000L;
    private static final long MOTION_ZONE_20_ENERGY = 22_000_000_000L;
    private static final long MOTION_ZONE_15_ENERGY = 36_000_000_000L;

    private static final int MOTION_ZONE_30_MIN_AE_ISO = 1000;
    private static final int MOTION_ZONE_20_MIN_AE_ISO = 1600;
    private static final int MOTION_ZONE_15_MIN_AE_ISO = 2400;

    private long mMotionLastLoggedRequestedExposureNs = Long.MIN_VALUE;
    private long mMotionLastLoggedActualExposureNs = Long.MIN_VALUE;
    private int mMotionLastLoggedRequestedIso = Integer.MIN_VALUE;
    private int mMotionLastLoggedActualIso = Integer.MIN_VALUE;
    private String mMotionLastLadderDecision = "";

    /* IRIS_26412_MOTION_V2_EXPOSURE_AUTHORITY */
    private boolean mMotionV2AeBaseReady = false;
    private int mMotionV2AeBaseSteps = 0;
    private int mMotionV2AeAppliedSteps = Integer.MIN_VALUE;
    private long mMotionV2AeLastUpdateMs = 0L;

    private long mMotionDiagnosticShotId = 0L;

    // Responsive hybrid ZSL: wait briefly for the passive rolling ring to
    // reach the requested count, then process whatever current-generation
    // frames are available above the safe minimum.
    private boolean mMotionTopUpActive = false;
    private long mMotionTopUpStartMs = 0L;
    private int mMotionTopUpTargetFrames = 0;
    private int mMotionTopUpMinimumFrames = 0;
    private static final long MOTION_TOP_UP_TIMEOUT_MS = 1400L;
    private static final long MOTION_TOP_UP_POLL_MS = 25L;
    /* IRIS_26556_MOTION_GLOBAL_SLIDER_EFFECTIVE_CAP
     * The shared preference remains 1..50 for Night, but Motion stays a pure pre-shutter ZSL
     * capture and consumes at most 30 normal RAWs. This is an acquisition-policy cap only;
     * Sabre/VGN/Jin reconstruction math is not changed by the frame-count policy.
     */
    private static final int MOTION_26556_MAX_NORMAL_FRAMES = 30;

    private static int iris26556RequestedMotionFrames() {
        return Math.max(1, Math.min(PhotonCamera.getSettings().frameCount,
                MOTION_26556_MAX_NORMAL_FRAMES));
    }
    /* IRIS_26520_V4_FROZEN_METADATA_GRACE
     * RAW can arrive before its exact SENSOR_TIMESTAMP TotalCaptureResult. Freeze the already
     * present shutter-time RAW population and allow metadata only to catch up. New normal RAWs
     * remain inadmissible for the entire grace window.
     */
    private static final long MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L;
    private static final long MOTION_VERY_DARK_ENERGY_THRESHOLD = 30_000_000_000L;

    private final ImageReader.OnImageAvailableListener mOnYuvImageAvailableListener
            = new ImageReader.OnImageAvailableListener() {
        @Override
        public void onImageAvailable(ImageReader reader) {
            //mImageSaver.mImage = reader.acquireNextImage();
            //mImageSaver.initProcess(reader);
//            Message msg = new Message();
//            msg.obj = reader;
//            mImageSaver.processingHandler.sendMessage(msg);
            //processExecutor.execute(() -> mImageSaver.initProcess(reader));
            mImageSaver.initProcess(reader);
        }
    };
    private final ImageReader.OnImageAvailableListener mOnRawImageAvailableListener
            = new ImageReader.OnImageAvailableListener() {

        @Override
        public void onImageAvailable(ImageReader reader) {
            //dequeueAndSaveImage(mRawResultQueue, mRawImageReader);
            //mImageSaver.mImage = reader.acquireNextImage();
//            Message msg = new Message();
//            msg.obj = reader;
//            mImageSaver.processingHandler.sendMessage(msg);
            if (isZslMode()) {
                Image img = reader.acquireNextImage();
                if (img == null) return;
                /* IRIS_26489_SHORT_RAW_CALLBACK_BEFORE_RING_DRAIN
                 * Stage a copied candidate before the historical capture-state early-close can
                 * discard the one short RAW whose TotalCaptureResult has not arrived yet.
                 */

                /* IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP
                 * The intentional Long-A request is physically outside the normal ZSL
                 * exposure group. CaptureStarted/Image timestamp equality owns the role.
                 * Copy/stage before the historical capture-state close just like Short-A.
                 */
                Motion26505LongTicket iris26505LongTicket = mMotion26505CaptureLongTicket;
                final long iris26505RawTimestamp = img.getTimestamp();
                final long iris26505ExpectedLongTimestamp = iris26505LongTicket == null
                        ? 0L : iris26505LongTicket.expectedTimestampNs();
                final boolean iris26505ExactLongRawOwned = iris26505LongTicket != null
                        && iris26505ExpectedLongTimestamp > 0L
                        && iris26505RawTimestamp == iris26505ExpectedLongTimestamp;
                boolean iris26505LongCandidateCopied =
                        stageMotion26505LongRawCandidate(iris26505LongTicket, img);
                if (iris26505ExactLongRawOwned) {
                    Log.i(TAG, "IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP"
                            + " rawTimestamp=" + iris26505RawTimestamp
                            + " expectedTimestamp=" + iris26505ExpectedLongTimestamp
                            + " stagedOrDelivered=" + iris26505LongCandidateCopied
                            + " slotSealed=" + iris26505LongTicket.slot.isSealed()
                            + " normalRingAdmission=false");
                    img.close();
                    return;
                }
                Motion26486ShortTicket iris26489ShortTicket = mMotion26486CaptureShortTicket;
                final long iris26490RawTimestamp = img.getTimestamp();
                final long iris26490ExpectedShortTimestamp = iris26489ShortTicket == null
                        ? 0L : iris26489ShortTicket.expectedTimestampNs();
                final boolean iris26490ExactShortRawOwned = iris26489ShortTicket != null
                        && iris26490ExpectedShortTimestamp > 0L
                        && iris26490RawTimestamp == iris26490ExpectedShortTimestamp;
                boolean iris26489ShortCandidateCopied =
                        stageMotion26489ShortRawCandidate(iris26489ShortTicket, img);
                /* IRIS_26490_EXACT_SHORT_RAW_NEVER_ENTERS_NORMAL_RING
                 * Camera2 guarantees onCaptureStarted/result/Image timestamps identify the same
                 * physical capture. Once this Image is the exact HIGHLIGHT_SHORT observation,
                 * the short ticket owns it exclusively even if reconstruction already sealed the
                 * optional slot. Never let a bracketed short exposure contaminate the normal ZSL ring.
                 */
                if (iris26490ExactShortRawOwned) {
                    Log.i(TAG, "IRIS_26490_SHORT_RAW_EXACT_CALLBACK_OWNERSHIP"
                            + " rawTimestamp=" + iris26490RawTimestamp
                            + " expectedTimestamp=" + iris26490ExpectedShortTimestamp
                            + " stagedOrDelivered=" + iris26489ShortCandidateCopied
                            + " slotSealed=" + iris26489ShortTicket.slot.isSealed()
                            + " normalRingAdmission=false");
                    img.close();
                    return;
                }
                if (mZslCapturing && !mMotionTopUpActive) {
                    if (iris26489ShortCandidateCopied) {
                        Log.d(TAG, "IRIS_26489_SHORT_RAW_SURVIVED_EARLY_CLOSE timestamp="
                                + img.getTimestamp());
                    }
                    img.close();
                    return;
                }
                // Keep buffering during AE probe. Eligibility is decided from
                // actual exposure/ISO groups at shutter time.
                // Metadata can arrive after the Image callback.
                // Measure only a sparse RAW sample; the frame is not changed.
                sampleMotion26380RawCaptureQuality(img);

                // Buffer first; validate timestamp/exposure when shutter is pressed.
                synchronized (mZslBufferLock) {
                    mZslRingBuffer.addLast(img);
                    if (!mIris26548FirstZslRaw) {
                        mIris26548FirstZslRaw = true;
                        Log.i(TAG, "IRIS_26548_FIRST_ZSL_RAW generation="
                                + mIris26548CameraHealthGeneration + " timestamp=" + img.getTimestamp());
                    }
                    /* IRIS_26480_SHORT_RING_HEADROOM_V1
                     * ImageReader already owns frameCount+3 buffers in Motion.
                     * Keep up to two extra acquired Images only while the short
                     * highlight observation is pending, so normal ZSL frames
                     * are not evicted by the short probe.
                     */
                    int maxFrames = Math.min(
                            iris26556RequestedMotionFrames()
                                    + ((mMotion26480ShortRequested
                                            || mMotion26486ShortAcquisitions.get() > 0) ? 2 : 0),
                            MOTION_26556_MAX_NORMAL_FRAMES + 2);
                    while (mZslRingBuffer.size() > maxFrames) {
                        Image old = mZslRingBuffer.pollFirst();
                        if (old != null) old.close();
                    }
                }
                return;
            }
            if (mIrisNight26540CaptureActive) {
                // IRIS_26554_NIGHT_HAL_QUEUE_DRAIN_OWNER
                // A callback is only a notification that one OR MORE RAWs may be queued. Drain
                // every currently available Camera2 Image synchronously so HALs that coalesce
                // notifications cannot strand tail frames. Exactly one copied SHORT reference is
                // retained in memory; every later RAW is spooled and its Camera2 Image closed.
                drainIrisNight26554AvailableRawImages(reader, "image-callback");
                return;
            }
            if (onUnlimited && !unlimitedStarted) {
                return;
            }

            //This code creates single frame bugs
            //taskResults.removeIf(Future::isDone); //remove already completed results
            //Future<?> result = processExecutor.submit(() -> mImageSaver.initProcess(reader));
            //taskResults.add(result);
            if(PhotonCamera.getSettings().frameCount != 1) {
                //taskResults.removeIf(Future::isDone); //remove already completed results
                //Future<?> result = processExecutor.submit(() -> mImageSaver.initProcess(reader));
                //taskResults.add(result);
                //processExecutor.execute(() -> mImageSaver.initProcess(reader));
                mImageSaver.initProcess(reader);
                //mBackgroundHandler.post(() -> mImageSaver.initProcess(reader));
                //AsyncTask.execute(() -> mImageSaver.initProcess(reader));
            }
            else {
                mBackgroundHandler.post(() -> mImageSaver.initProcess(reader));
                //mImageSaver.initProcess(reader);
                //processExecutor.execute(() -> mImageSaver.initProcess(reader));
            }
        }

    };
    private Range<Integer> FpsRangeAuto;
    private int[] mCameraAfModes;
    private int mPreviewWidth;
    private int mPreviewHeight;
    private ArrayList<CaptureRequest> captures;
    private CameraCaptureSession.CaptureCallback CaptureCallback;
    private File vid = null;
    public int mMeasuredFrameCnt;
    public static boolean isProcessing;
    /**
     * An {@link AutoFitPreviewView} for camera preview.
     */
    private GLPreview mTextureView;
    /**
     * A {@link CameraCaptureSession } for camera preview.
     */
    private CameraCaptureSession mCaptureSession;
    /**
     * MediaRecorder
     */
    private MediaRecorder mMediaRecorder;
    /**
     * Whether the app is recording video now
     */
    public boolean mIsRecordingVideo;
    private Size target;
    private float mFocus;
    public int mPreviewAFMode;
    public int mPreviewAEMode;
    public MeteringRectangle[] mPreviewMeteringAF;
    public MeteringRectangle[] mPreviewMeteringAE;
    /**
     * The {@link Size} of camera preview.
     */
    public Size mPreviewSize;
    public Size mBufferSize;
    /*An additional thread for running tasks that shouldn't block the UI.*/
    private HandlerThread mBackgroundThread;
    /**
     * Timer to use with pre-capture sequence to ensure a timely capture if 3A convergence is
     * taking too long.
     */
    private long mCaptureTimer;
    /**
     * Whether the current camera device supports Flash or not.
     */
    private boolean mFlashSupported;
    /**
     * Creates a new {@link CameraCaptureSession} for camera preview.
     */
    public static boolean burst = false;
    /**
     * A {@link CameraCaptureSession.CaptureCallback} that handles events related to JPEG capture.
     */
    public ProcessCallbacks debugCallback = new ProcessCallbacks();
    private final CameraCaptureSession.CaptureCallback mCaptureCallback = new CameraCaptureSession.CaptureCallback() {

        private void process(CaptureResult result) {
            debugCallback.process();
            switch (mState) {
                case STATE_PREVIEW:
                    previewProcess();
                    break;
                case STATE_WAITING_LOCK:
                    waitingLockProcess(result);
                    break;
                case STATE_WAITING_PRECAPTURE:
                    waitingPrecaptureProcess(result);
                    break;
                case STATE_WAITING_NON_PRECAPTURE:
                    waitingNonPrecaptureProcess(result);
                    break;
            }
        }

        private void previewProcess() {
            // We have nothing to do when the camera preview is working normally.
            //Log.v(TAG, "PREVIEW");
        }

        private void waitingLockProcess(CaptureResult result) {
            //Log.v(TAG, "WAITING_LOCK");
            Integer afState = result.get(CaptureResult.CONTROL_AF_STATE);
            // If we haven't finished the pre-capture sequence but have hit our maximum
            // wait timeout, too bad! Begin capture anyway.
            if (hitTimeoutLocked()) {
                Log.w(TAG, "Timed out waiting for pre-capture sequence to complete.");
                mState = STATE_PICTURE_TAKEN;
                captureStillPicture();
                // IRIS_26553_NIGHT_AF_TIMEOUT_SINGLE_DISPATCH
                // One Camera2 callback must never continue into a second captureStillPicture().
                return;
            }
            if (afState == null) {
                mState = STATE_PICTURE_TAKEN;
                captureStillPicture();
            } else if (CaptureResult.CONTROL_AF_STATE_FOCUSED_LOCKED == afState ||
                    CaptureResult.CONTROL_AF_STATE_NOT_FOCUSED_LOCKED == afState) {
                // CONTROL_AE_STATE can be null on some devices
                Integer aeState = result.get(CaptureResult.CONTROL_AE_STATE);
                if (aeState == null ||
                        aeState == CaptureResult.CONTROL_AE_STATE_CONVERGED) {
                    mState = STATE_PICTURE_TAKEN;
                    captureStillPicture();
                } else {
                    runPreCaptureSequence();
                }
            }
        }

        private void waitingPrecaptureProcess(CaptureResult result) {
            Log.v(TAG, "WAITING_PRECAPTURE");
            // CONTROL_AE_STATE can be null on some devices
            Integer aeState = result.get(CaptureResult.CONTROL_AE_STATE);
            if (aeState == null ||
                    aeState == CaptureResult.CONTROL_AE_STATE_PRECAPTURE ||
                    aeState == CaptureRequest.CONTROL_AE_STATE_FLASH_REQUIRED) {
                mState = STATE_WAITING_NON_PRECAPTURE;
            }
            if (paramController.isManualMode())
                mState = STATE_WAITING_NON_PRECAPTURE;
        }

        private void waitingNonPrecaptureProcess(CaptureResult result) {
            // CONTROL_AE_STATE can be null on some devices
            Integer aeState = result.get(CaptureResult.CONTROL_AE_STATE);
            if (aeState == null || aeState != CaptureResult.CONTROL_AE_STATE_PRECAPTURE) {
                mState = STATE_PICTURE_TAKEN;
                captureStillPicture();
            }
        }

        @Override
        public void onCaptureProgressed(@NonNull CameraCaptureSession session,
                                        @NonNull CaptureRequest request,
                                        @NonNull CaptureResult partialResult) {

            process(partialResult);
        }

        private boolean shouldLogMotionExposure(
                Long requestedExposure,
                Long actualExposure,
                Integer requestedIso,
                Integer actualIso) {

            long reqExp = requestedExposure == null
                    ? Long.MIN_VALUE : requestedExposure;
            long actExp = actualExposure == null
                    ? Long.MIN_VALUE : actualExposure;
            int reqIso = requestedIso == null
                    ? Integer.MIN_VALUE : requestedIso;
            int actIso = actualIso == null
                    ? Integer.MIN_VALUE : actualIso;

            boolean first = mMotionLastLoggedActualExposureNs
                    == Long.MIN_VALUE;

            boolean requestChanged =
                    reqExp != mMotionLastLoggedRequestedExposureNs
                    || reqIso != mMotionLastLoggedRequestedIso;

            boolean actualExposureChanged = first;
            if (!first
                    && actExp > 0
                    && mMotionLastLoggedActualExposureNs > 0) {
                long high = Math.max(
                        actExp,
                        mMotionLastLoggedActualExposureNs);
                long low = Math.min(
                        actExp,
                        mMotionLastLoggedActualExposureNs);
                actualExposureChanged = high >= low + low / 4;
            }

            boolean actualIsoChanged = first;
            if (!first
                    && actIso > 0
                    && mMotionLastLoggedActualIso > 0) {
                int high = Math.max(
                        actIso,
                        mMotionLastLoggedActualIso);
                int low = Math.min(
                        actIso,
                        mMotionLastLoggedActualIso);
                actualIsoChanged = high >= low + low / 4;
            }

            if (!(first
                    || requestChanged
                    || actualExposureChanged
                    || actualIsoChanged)) {
                return false;
            }

            mMotionLastLoggedRequestedExposureNs = reqExp;
            mMotionLastLoggedActualExposureNs = actExp;
            mMotionLastLoggedRequestedIso = reqIso;
            mMotionLastLoggedActualIso = actIso;
            return true;
        }

        @Override
        public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                       @NonNull CaptureRequest request,
                                       @NonNull TotalCaptureResult result) {
            Object exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Object iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
            Object focus = result.get(CaptureResult.LENS_FOCUS_DISTANCE);
            Rational[] mTemp = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
            if (exposure != null) mPreviewExposureTime = (long) exposure;
            if (iso != null) mPreviewIso = (int) iso;
            if (focus != null) mFocus = (float) focus;
            if (isZslMode()) {
                updateMotionUnifiedExposure(request, result);
                /*
                 * IRIS_26413_MOTION_V2_HAL_AE_STABLE_PREVIEW
                 *
                 * 26412 proved that a second continuously-running RAW-derived
                 * AE-compensation loop can fight the HAL AE controller and
                 * produce visible preview oscillation. Keep system/HAL AE as
                 * the live preview authority. V2 still uses actual RAW/result
                 * metadata for capture processing and JPEG normalization.
                 */
                /* updateMotionV2ExposureAuthority(result); intentionally dormant */
                /* IRIS_26386_STABLE_HAL_AE_AUTHORITY */
                // Asynchronous RAW evidence is diagnostic only; HAL AE owns live preview.
                // updateMotion26368AdaptiveAeBias(result);
            }
            if (mTemp != null) mPreviewTemp = mTemp;
            if (mPreviewTemp == null) {
                mPreviewTemp = new Rational[3];
                for (int i = 0; i < mPreviewTemp.length; i++)
                    mPreviewTemp[i] = new Rational(101, 100);
            }
            mColorSpaceTransform = result.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
            Integer state = result.get(CaptureResult.FLASH_STATE);
            mFlashed = state != null && state == CaptureResult.FLASH_STATE_PARTIAL || state == CaptureResult.FLASH_STATE_FIRED;
            mPreviewCaptureResult = result;
            mPreviewCaptureRequest = request;
            if (!mIris26548FirstCaptureResult) {
                mIris26548FirstCaptureResult = true;
                Long iris26548Timestamp = result.get(CaptureResult.SENSOR_TIMESTAMP);
                Log.i(TAG, "IRIS_26548_FIRST_CAPTURE_RESULT generation="
                        + mIris26548CameraHealthGeneration + " timestamp=" + iris26548Timestamp);
                // IRIS_26555_JIN_PREWARM_AFTER_CAMERA_FLOW
                // Do not compete with Surface/session creation on fragile Camera2 HALs. Mode
                // changes restart the camera, so the first real Night result is the safe trigger.
                if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT) {
                    IrisNightNeuralEnhancer.prewarmAsync();
                }
            }
            /* IRIS_26526_SESSION_BOUND_HAL_TELEMETRY
             * The callback session is immutable for this result. Never infer result
             * ownership from PreferenceKeys or mutable mCameraDevice. CaptureResult
             * cannot drive the live software preview crop.
             */
            IrisCameraRoute iris26527ResultRoute = mIrisSessionRoutes.get(session);
            String iris26527ResultOwner = iris26527ResultRoute == null
                    ? (session.getDevice() == null ? null : session.getDevice().getId())
                    : iris26527ResultRoute.provenOwnerId;
            CameraCharacteristics iris26527ResultCharacteristics = mCameraCharacteristics;
            if (iris26527ResultRoute != null) {
                CameraCharacteristics routeCharacteristics =
                        mCameraCharacteristicsMap.get(iris26527ResultRoute.characteristicsId);
                if (routeCharacteristics != null) iris26527ResultCharacteristics = routeCharacteristics;
            }
            IrisZoomController.CaptureZoomUpdate iris26527ZoomUpdate =
                    IrisZoomController.updateFromCaptureResult(
                            result, iris26527ResultCharacteristics, iris26527ResultOwner);
            if (iris26527ZoomUpdate.committedPending) {
                if (iris26527ZoomUpdate.chainedPendingOwnerCameraId != null) {
                    PreferenceKeys.setCameraID(iris26527ZoomUpdate.chainedPendingOwnerCameraId);
                    restartCameraForIrisHandoff(iris26527ZoomUpdate.chainedPendingOwnerCameraId);
                } else {
                    if (iris26527ZoomUpdate.previewRefreshRequired && mBackgroundHandler != null) {
                        mBackgroundHandler.post(CaptureController.this::applyIrisZoomNow);
                    }
                    if (iris26527ZoomUpdate.revealAllowed) {
                        iris26527RevealZoomCurtain(iris26527ResultOwner);
                    }
                }
            }
            Long sensorTimestamp = result.get(CaptureResult.SENSOR_TIMESTAMP);
            if (sensorTimestamp != null && PhotonCamera.getSettings().selectedMode == CameraMode.MOTION) {
                synchronized (mZslBufferLock) {
                    mZslResultMap.put(sensorTimestamp, result);
                    while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
                        Long oldest = Collections.min(mZslResultMap.keySet());
                        mZslResultMap.remove(oldest);
                    }
                }
                Long requestedExposure =
                        request.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
                Long actualMotionExposure =
                        result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                Integer requestedMotionIso =
                        request.get(CaptureRequest.SENSOR_SENSITIVITY);
                Integer actualMotionIso =
                        result.get(CaptureResult.SENSOR_SENSITIVITY);

                if (shouldLogMotionExposure(
                        requestedExposure,
                        actualMotionExposure,
                        requestedMotionIso,
                        actualMotionIso)) {
                    Log.d(TAG, "MotionExposureChange camera=" + physicalID
                            + " timestamp=" + sensorTimestamp
                            + " requested=" + requestedExposure
                            + " actual=" + actualMotionExposure
                            + " requestedIso=" + requestedMotionIso
                            + " actualIso=" + actualMotionIso
                            + " generation=" + mMotionUnifiedGeneration
                            + " activeZone=" + mMotionActiveZone);
                }

                String diagnosticBase =
                        com.particlesdevs.photoncamera.processing.parameters
                                .IsoExpoSelector.lastMotionExposureDiagnostics;
                int previousUnified =
                        diagnosticBase.indexOf(";UnifiedGeneration=");
                if (previousUnified >= 0) {
                    diagnosticBase = diagnosticBase.substring(0, previousUnified);
                }
                com.particlesdevs.photoncamera.processing.parameters
                        .IsoExpoSelector.lastMotionExposureDiagnostics =
                        diagnosticBase
                        + ";UnifiedGeneration=" + mMotionUnifiedGeneration
                        + ";UnifiedSettledFrames=" + mMotionUnifiedSettledFrames
                        + ";UnifiedRequestedExposureNs="
                            + request.get(CaptureRequest.SENSOR_EXPOSURE_TIME)
                        + ";UnifiedRequestedIso="
                            + request.get(CaptureRequest.SENSOR_SENSITIVITY)
                        + ";UnifiedActualExposureNs="
                            + result.get(CaptureResult.SENSOR_EXPOSURE_TIME)
                        + ";UnifiedActualIso="
                            + result.get(CaptureResult.SENSOR_SENSITIVITY)
                        + ";PhysicalCameraId=" + physicalID
                        + ";ManualLadderActive=" + mMotionManualLadderActive
                        + ";AeWarmupFrames=" + mMotionAeWarmupFrames
                        + ";MotionCandidateZone=" + mMotionCandidateZone
                        + ";MotionCandidateFrames=" + mMotionCandidateFrames
                        + ";MotionActiveZone=" + mMotionActiveZone
                        + ";ManualFrames=" + mMotionManualFrames;
            }
            process(result);
            cameraEventsListener.onPreviewCaptureCompleted(result);
            if(PreferenceKeys.getAfMode() == CaptureRequest.CONTROL_AF_MODE_AUTO && !burst && !mTouchFocus.isTouchFocus) {
                mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_START);
                rebuildPreviewBuilderOneShot();
            }
        }

    };
    /**
     * {@link CameraDevice.StateCallback} is called when {@link CameraDevice} changes its state.
     */
    /* IRIS_26527_SESSION_BOUND_ROUTE_OWNER */
    private static final class IrisCameraRoute {
        final String requestedOwnerId;
        final String openedDeviceId;
        final String physicalOutputId;
        final String characteristicsId;
        final String provenOwnerId;
        final String mode;

        IrisCameraRoute(String requestedOwnerId, String openedDeviceId, String physicalOutputId,
                        String characteristicsId, String provenOwnerId, String mode) {
            this.requestedOwnerId = requestedOwnerId;
            this.openedDeviceId = openedDeviceId;
            this.physicalOutputId = physicalOutputId;
            this.characteristicsId = characteristicsId;
            this.provenOwnerId = provenOwnerId;
            this.mode = mode;
        }

        @Override public String toString() {
            return "requested=" + requestedOwnerId + ",opened=" + openedDeviceId
                    + ",physicalOutput=" + physicalOutputId + ",characteristics="
                    + characteristicsId + ",provenOwner=" + provenOwnerId + ",mode=" + mode;
        }
    }

    private volatile IrisCameraRoute mIrisOpeningRoute = null;
    private volatile IrisCameraRoute mIrisActiveRoute = null;
    /* IRIS_26548_CAMERA_SESSION_HEALTH_CONTRACT
     * A configured Camera2 object is not sufficient evidence of a usable camera. Track actual
     * session/result/preview/RAW flow so startup stalls become recoverable instead of a permanent
     * black viewfinder followed by an empty frozen Motion batch.
     */
    private volatile long mIris26548CameraHealthGeneration = 0L;
    private volatile boolean mIris26548SessionConfigured = false;
    private volatile boolean mIris26548RepeatingSubmitted = false;
    private volatile boolean mIris26548FirstCaptureResult = false;
    private volatile boolean mIris26548FirstZslRaw = false;
    private volatile int mIris26548ConsecutiveHealthRecoveries = 0;
    /* IRIS_26555_UNIVERSAL_PREVIEW_AND_RAW_CAPABILITY_STATE
     * No manufacturer/model gates. Healthy sessions retain the exact 26554 topology. A session
     * that reports configured + repeating but produces no CaptureResult/SurfaceTexture frame is
     * first rebuilt PREVIEW-ONLY. Once real preview flow is proven, the desired full topology is
     * retried exactly once. If that retry kills flow again, return to preview-only and stop there:
     * never loop the failing topology and never sacrifice a working viewfinder for RAW readiness.
     * Cameras without a usable RAW output keep preview alive but cannot enter Iris RAW Motion/Night.
     */
    private static final int IRIS_26555_RECOVERY_NONE = 0;
    private static final int IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP = 1;
    private static final int IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY = 2;
    private static final int IRIS_26555_RECOVERY_PREVIEW_ONLY_FALLBACK = 3;
    private volatile int mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_NONE;
    private volatile boolean mIris26555RawStreamAvailable = true;
    private static final long IRIS_26548_POST_OPEN_HEALTH_TIMEOUT_MS = 3500L;
    private final Map<CameraCaptureSession, IrisCameraRoute> mIrisSessionRoutes =
            Collections.synchronizedMap(new java.util.IdentityHashMap<>());
    private volatile boolean mIrisZoomCurtainClosed = false;
    private volatile long mIrisZoomCurtainGeneration = 0L;
    private static final long IRIS_26527_CURTAIN_FAILSAFE_MS = 1600L;

    private final CameraDevice.StateCallback mStateCallback = new CameraDevice.StateCallback() {

        @Override
        public void onOpened(@NonNull CameraDevice cameraDevice) {
            // This method is called when the camera is opened.  We start camera preview here.
            mCameraOpenCloseLock.release();
            mCameraDevice = cameraDevice;
            Log.i(TAG, "IRIS_26548_CAMERA_ON_OPENED generation=" + mIris26548CameraHealthGeneration
                    + " camera=" + cameraDevice.getId());
            iris26548SchedulePostOpenHealthCheck(cameraDevice);
            IrisCameraRoute route = mIrisOpeningRoute;
            if (route != null && !route.openedDeviceId.equals(cameraDevice.getId())) {
                Log.e(TAG, "IRIS_26527_CAMERA_ROUTE_MISMATCH expected="
                        + route.openedDeviceId + " actual=" + cameraDevice.getId());
            }
            mImageSaver = new ImageSaver(cameraEventsListener);
            createCameraPreviewSession(false);
        }

        @Override
        public void onDisconnected(@NonNull CameraDevice cameraDevice) {
            Log.e(TAG, "IRIS_26548_CAMERA_ON_DISCONNECTED generation="
                    + mIris26548CameraHealthGeneration + " camera=" + cameraDevice.getId());
            mCameraOpenCloseLock.release();
            cameraDevice.close();
            mCameraDevice = null;
        }

        @Override
        public void onError(@NonNull CameraDevice cameraDevice, int error) {
            Log.e(TAG, "IRIS_26548_CAMERA_ON_ERROR generation="
                    + mIris26548CameraHealthGeneration + " camera=" + cameraDevice.getId()
                    + " error=" + error);
            mCameraOpenCloseLock.release();
            cameraDevice.close();
            mCameraDevice = null;
            showToast("onError() : cameraDevice = [" + cameraDevice + "], error = [" + error + "]");
            Log.d(TAG, "onError() : cameraDevice = [" + cameraDevice + "], error = [" + error + "]");
        }
    };
    /**
     * {@link TextureView.SurfaceTextureListener} handles several lifecycle events on a
     * {@link TextureView}.
     */
    public final TextureView.SurfaceTextureListener mSurfaceTextureListener
            = new TextureView.SurfaceTextureListener() {

        @Override
        public void onSurfaceTextureAvailable(@NonNull SurfaceTexture texture, int width, int height) {
            try {
                mIris26548ConsecutiveHealthRecoveries = 0;
                mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_NONE;
                iris26548BeginCameraHealthGeneration("surface_available");
                Log.i(TAG, "IRIS_26548_PREVIEW_SURFACE_AVAILABLE width=" + width + " height=" + height);
                Log.i(TAG, "IRIS_26553_PREVIEW_DIAG_SURFACE_AVAILABLE manufacturer="
                        + Build.MANUFACTURER + " model=" + Build.MODEL
                        + " view=" + mTextureView.getWidth() + "x" + mTextureView.getHeight()
                        + " alpha=" + mTextureView.getAlpha() + " visibility=" + mTextureView.getVisibility()
                        + " surfaceTexture=" + System.identityHashCode(texture));
                /* IRIS_26527_SINGLE_ROUTE_AUTHORITY_SURFACE */
                IrisCameraRoute route = iris26527ResolveRoute(PhotonCamera.getSettings().mCameraID);
                mIrisOpeningRoute = route;
                iris26527ApplyRouteToLegacyFields(route);
                CameraCharacteristics chars = mCameraCharacteristics;
                if (chars == null) {
                    Log.e(TAG, "No characteristics for resolved route " + route);
                    showToast("No camera characteristics for selected lens");
                    return;
                }
                Size optimal = getPreviewOutputSize(getSafeDisplay(), chars,
                        PhotonCamera.getSettings().selectedMode);
                openCamera(optimal.getWidth(), optimal.getHeight());
            } catch (Exception e){
                Log.e(TAG,Log.getStackTraceString(e));
                showToast("Error onSurfaceTextureAvailable:"+e.getLocalizedMessage());
            }
        }

        @Override
        public void onSurfaceTextureSizeChanged(@NonNull SurfaceTexture texture, int width, int height) {
            Log.d(TAG, " CHANGED SIZE:" + width + ' ' + height);
            configureTransform(width, height);
        }

        @Override

        public boolean onSurfaceTextureDestroyed(@NonNull SurfaceTexture texture) {
            return true;
        }

        @Override
        public void onSurfaceTextureUpdated(@NonNull SurfaceTexture texture) {
        }

    };
    public CaptureController(Activity activity, ExecutorService processExecutor, CameraEventsListener cameraEventsListener) {
        if(PhotonCamera.getSettings().previewFormat != 0) {
            mPreviewTargetFormat = PhotonCamera.getSettings().previewFormat;
        } else {
            mPreviewTargetFormat = ImageFormat.JPEG;
        }
        this.activity = activity;
        this.cameraEventsListener = cameraEventsListener;
        this.mTextureView = activity.findViewById(R.id.texture);
        this.mCameraManager = (CameraManager) activity.getSystemService(Context.CAMERA_SERVICE);
        this.mCameraManager2 = new CameraManager2(mCameraManager, PhotonCamera.getInstance(activity).getSettingsManager());
        PreferenceKeys.addIds(mCameraManager2.getCameraIdList());

        this.processExecutor = processExecutor;
        this.paramController = new ParamController(this);

        this.fillInCameraCharacteristics();
    }

    /**
     * Fills in {@link CaptureController#mCameraCharacteristicsMap} that is used in
     * {@link CaptureController#UpdateCameraCharacteristics}.
     */
    private void fillInCameraCharacteristics() {
        try {
            String[] cameraIds = mCameraManager2.getCameraIdList();
            for (String cameraId : cameraIds) {
                String physicalID = cameraId;
                if(cameraId.contains("-")){
                    physicalID = cameraId.split("-")[1];
                }
                mCameraCharacteristicsMap.put(physicalID, mCameraManager.getCameraCharacteristics(physicalID));
            }
        } catch (CameraAccessException cameraAccessException) {
            // Should not be possible to get here but anyway
            cameraAccessException.printStackTrace();
            showToast("Failed to fetch camera characteristics: " + cameraAccessException.getLocalizedMessage());
        }

    }

    public ParamController getParamController() {
        return paramController;
    }

    public static int getTargetFormat() {
        return mTargetFormat;
    }

    public static void setTargetFormat(int targetFormat) {
        mTargetFormat = targetFormat;
    }

    /**
     * Given {@code choices} of {@code Size}s supported by a camera, choose the smallest one that
     * is at least as large as the respective texture view size, and that is at most as large as the
     * respective max size, and whose aspect ratio matches with the specified value. If such size
     * doesn't exist, choose the largest one that is at most as large as the respective max size,
     * and whose aspect ratio matches with the specified value.
     *
     * @param choices           The list of sizes that the camera supports for the intended output
     *                          class
     * @param textureViewWidth  The width of the texture view relative to sensor coordinate
     * @param textureViewHeight The height of the texture view relative to sensor coordinate
     * @param maxWidth          The maximum width that can be chosen
     * @param maxHeight         The maximum height that can be chosen
     * @param aspectRatio       The aspect ratio
     * @return The optimal {@code Size}, or an arbitrary one if none were big enough
     */
    private static Size chooseOptimalSize(Size[] choices, int textureViewWidth,
                                          int textureViewHeight, int maxWidth, int maxHeight, Size aspectRatio) {

        // Collect the supported resolutions that are at least as big as the preview Surface
        List<Size> bigEnough = new ArrayList<>();
        // Collect the supported resolutions that are smaller than the preview Surface
        List<Size> notBigEnough = new ArrayList<>();
        int targetWidth = aspectRatio.getWidth();
        int targetHeight = aspectRatio.getHeight();
        for (Size option : choices) {
            int width = option.getWidth();
            int height = option.getHeight();
            boolean isAspectRatioMatching = (height * targetWidth == width * targetHeight);

            if (width <= maxWidth && height <= maxHeight && isAspectRatioMatching) {
                if (width >= textureViewWidth && height >= textureViewHeight) {
                    bigEnough.add(option);
                } else {
                    notBigEnough.add(option);
                }
            }
        }

        // Pick the smallest of those big enough.
        // If there is no one big enough, pick the largest of those not big enough.
        if (!bigEnough.isEmpty()) {
            return Collections.min(bigEnough, new CompareSizesByArea());
        } else if (!notBigEnough.isEmpty()) {
            return Collections.max(notBigEnough, new CompareSizesByArea());
        } else {
            Log.e(TAG, "Couldn't find any suitable preview size");
            return choices[0];
        }
    }

    private Size getCameraOutputSize(Size[] sizes) {
        if (sizes != null) {
            if (sizes.length > 0) {
                Arrays.sort(sizes, new CompareSizesByArea());

                int largestSizeIdx = sizes.length - 1;
                int largestSizeArea = sizes[largestSizeIdx].getWidth() * sizes[largestSizeIdx].getHeight();

                if (largestSizeArea <= ResolutionSolution.highRes) {
                    target = sizes[largestSizeIdx];
                    return target;
                } else if (sizes.length > 1) {
                    target = sizes[largestSizeIdx - 1];
                    return target;
                }
            }
        }
        return null;
    }

    /**
     * For test method {@link CaptureController#getCameraOutputSize(Size[])}
     */
    @TestOnly
    private static Size getCameraOutputSizeTest(Size[] sizes) {
        if (sizes != null) {
            if (sizes.length > 0) {
                Arrays.sort(sizes, new CompareSizesByArea());

                int largestSizeIdx = sizes.length - 1;
                int largestSizeArea = sizes[largestSizeIdx].getWidth() * sizes[largestSizeIdx].getHeight();

                if (largestSizeArea <= ResolutionSolution.highRes) {
                    return sizes[largestSizeIdx];
                } else if (sizes.length > 1) {
                    return sizes[largestSizeIdx - 1];
                }
            }
        }
        return null;
    }

    private Size getCameraOutputSize(Size[] sizes, Size previewSize) {
        if (sizes == null || sizes.length == 0) return previewSize;

        Arrays.sort(sizes, new CompareSizesByArea());
        int largestSizeIdx = sizes.length - 1;
        int largestSizeArea = sizes[largestSizeIdx].getWidth() * sizes[largestSizeIdx].getHeight();

        if (PhotonCamera.getSettings().QuadBayer) {
            target = sizes[largestSizeIdx];
            Rect preCorrectionActiveArraySize = mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE);
            Rect activeArraySize = mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
            if (preCorrectionActiveArraySize != null && activeArraySize != null) {
                double k = (double) (target.getHeight()) / activeArraySize.bottom;
                mul(preCorrectionActiveArraySize, k);
                mul(activeArraySize, k);
                CameraReflectionApi.set(mCameraCharacteristics, CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE, activeArraySize);
                CameraReflectionApi.set(mCameraCharacteristics, CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE, preCorrectionActiveArraySize);
            }
            return target;
        }

        int[] preferred = PhotonCamera.getSpecificSensor().selectedSensorSpecifics.preferredResolution;
        if (preferred != null && preferred.length >= 2) {
            for (Size size : sizes) {
                if (size.getWidth() == preferred[0] && size.getHeight() == preferred[1]) {
                    target = size;
                    return target;
                }
            }
        }

        if (largestSizeArea <= ResolutionSolution.highRes) {
            target = sizes[largestSizeIdx];
            return target;
        } else if (sizes.length > 1) {
            target = sizes[largestSizeIdx - 1];
            return target;
        }
        return previewSize;
    }

    /**
     * For test method {@link CaptureController#getCameraOutputSize(Size[], Size)}
     */
    @TestOnly
    private static Size getCameraOutputSizeTest(Size[] sizes, Size previewSize) {
        if (sizes == null || sizes.length == 0) return previewSize;

        Size temp = null;

        Arrays.sort(sizes, new CompareSizesByArea());
        int largestSizeIdx = sizes.length - 1;
        int largestSizeArea = sizes[largestSizeIdx].getWidth() * sizes[largestSizeIdx].getHeight();

        if (largestSizeArea <= ResolutionSolution.highRes || PhotonCamera.getSettings().QuadBayer) {
            temp = sizes[largestSizeIdx];
            if (PhotonCamera.getSettings().QuadBayer) {
                Rect preCorrectionActiveArraySize = mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE);
                Rect activeArraySize = mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);

                if (preCorrectionActiveArraySize != null && activeArraySize != null) {
                    double k = (double) (temp.getHeight()) / activeArraySize.bottom;
                    mulForTest(preCorrectionActiveArraySize, k);
                    mulForTest(activeArraySize, k);
                    CameraReflectionApi.set(mCameraCharacteristics, CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE, activeArraySize);
                    CameraReflectionApi.set(mCameraCharacteristics, CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE, preCorrectionActiveArraySize);
                }
            }
            return temp;
        } else if (sizes.length > 1) {
            temp = sizes[largestSizeIdx - 1];
            return temp;
        }
        return previewSize;
    }

    /**
     * Sets up member variables related to camera.
     *
     * @param width  The width of available size for camera preview
     * @param height The height of available size for camera preview
     */
    private void setUpCameraOutputs(int width, int height) {
        try {
            mPreviewWidth = width;
            mPreviewHeight = height;
            /* IRIS_26527_SINGLE_ROUTE_AUTHORITY_SETUP */
            IrisCameraRoute route = iris26527ResolveRoute(PhotonCamera.getSettings().mCameraID);
            mIrisOpeningRoute = route;
            iris26527ApplyRouteToLegacyFields(route);
            //Thread thr = new Thread(mImageSaver);
            //thr.start();
        } catch (Exception e) {
            // Currently an NPE is thrown when the Camera2API is used but not supported on the
            // device this code runs.
            Log.e(TAG, Log.getStackTraceString(e));
            showToast(activity.getString(R.string.camera_error));
            //cameraEventsListener.onError(R.string.camera_error);
        }
    }

    /**
     * Closes the current {@link CameraDevice}.
     */
    public void closeCamera() {
        try {
            mCameraOpenCloseLock.acquire();
            if (null != mCaptureSession) {
                mCaptureSession.close();
                mCaptureSession = null;
            }
            if (null != mCameraDevice) {
                mCameraDevice.close();
                mCameraDevice = null;
            }
            if (null != mImageReaderPreview) {
                if (!isProcessing) {
                    mImageReaderPreview.close();
                    mImageReaderPreview = null;
                }
                if (!isProcessing && mImageReaderRaw != null) {
                    mImageReaderRaw.close();
                    mImageReaderRaw = null;
                }
            }
            if (null != mMediaRecorder) {
                mMediaRecorder.release();
                mMediaRecorder = null;
            }
            if (surface != null) {
                surface.release();
                surface = null;
            }
            mState = STATE_CLOSED;
        } catch (InterruptedException e) {
            throw new RuntimeException("Interrupted while trying to lock camera closing.", e);
        } finally {
            mCameraOpenCloseLock.release();
        }
    }

    /**
     * Starts a background thread and its {@link Handler}.
     */
    public void startBackgroundThread() {
        if (mBackgroundThread == null) {
            mBackgroundThread = new HandlerThread("CameraBackground");
            mBackgroundThread.start();
            mBackgroundHandler = new Handler(mBackgroundThread.getLooper());
            Log.d(TAG, "startBackgroundThread() called from \"" + Thread.currentThread().getName() + "\" Thread");
        }
        //mBackgroundHandler.post(mImageSaver);
    }

    /**
     * Stops the background thread and its {@link Handler}.
     */
    public void stopBackgroundThread() {
        if (mBackgroundThread == null)
            return;
        mBackgroundThread.quitSafely();
        try {
            mBackgroundThread.join();
            mBackgroundThread = null;
            mBackgroundHandler = null;
            Log.d(TAG, "stopBackgroundThread() called from \"" + Thread.currentThread().getName() + "\" Thread");
        } catch (InterruptedException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

//    public void rebuildPreview() {
//        try {
////            mCaptureSession.stopRepeating();
//            mCaptureSession.setRepeatingRequest(mPreviewRequest, mCaptureCallback, mBackgroundHandler);
//        } catch (CameraAccessException e) {
//            Log.e(TAG, Log.getStackTraceString(e));
//        }
//    }

    private Range<Integer> getSelectedFpsRange() {
        switch (PhotonCamera.getSettings().fpsMode) {
            case 1: return new Range<>(24, 24);
            case 2: return new Range<>(30, 30);
            case 3: return new Range<>(60, 60);
            default: return FpsRangeAuto;
        }
    }

    private Range<Integer> chooseMotionUnifiedFpsRange(long exposureNs) {
        final int targetFps = exposureNs > 34_000_000L ? 15 : 30;
        Range<Integer>[] ranges = mCameraCharacteristics == null ? null
                : mCameraCharacteristics.get(
                        CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
        if (ranges == null || ranges.length == 0) {
            return new Range<>(targetFps, targetFps);
        }

        Range<Integer> containing = null;
        int containingScore = Integer.MAX_VALUE;
        for (Range<Integer> range : ranges) {
            int lower = range.getLower();
            int upper = range.getUpper();
            if (lower == targetFps && upper == targetFps) {
                return range;
            }
            if (lower <= targetFps && upper >= targetFps) {
                int score = (upper - lower) * 100
                        + Math.abs(upper - targetFps)
                        + Math.abs(lower - targetFps);
                if (score < containingScore) {
                    containing = range;
                    containingScore = score;
                }
            }
        }
        return containing == null
                ? new Range<>(targetFps, targetFps)
                : containing;
    }
    private void clearMotionUnifiedBuffer() {
        synchronized (mZslBufferLock) {
            while (!mZslRingBuffer.isEmpty()) {
                Image image = mZslRingBuffer.pollFirst();
                if (image != null) image.close();
            }
            mZslResultMap.clear();
        }
    }

    private boolean motionExposureMatches(TotalCaptureResult result) {
        if (result == null || mMotionUnifiedExposureNs <= 0L
                || mMotionUnifiedIso <= 0) return false;
        Long exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
        if (exposure == null || iso == null) return false;
        /*
         * IRIS_26379_UNIFIED_EXPOSURE_EQUIVALENCE
         * One definition of "same actual exposure" for short Motion RAWs.
         */
        long exposureTolerance =
                iris26378MotionExposureToleranceNs(
                        mMotionUnifiedExposureNs,
                        exposure);
        int isoTolerance = Math.max(2, mMotionUnifiedIso / 10);
        return Math.abs(exposure - mMotionUnifiedExposureNs)
                        <= exposureTolerance
                && Math.abs(iso - mMotionUnifiedIso) <= isoTolerance;
    }

    /*
     * IRIS_26368_MOTION_ADAPTIVE_AE_BIAS
     *
     * System/HAL AE remains fully enabled. This helper never sets
     * SENSOR_EXPOSURE_TIME or SENSOR_SENSITIVITY.
     *
     * 26367 controls:
     * - good bright HDR control: ~2.72 ms / ISO 50 -> no intervention
     * - problematic direct-bright scenes: ~0.11-0.50 ms / ISO 50
     * - genuine low light: ~30-40 ms / ISO ~3200 -> no intervention
     */
    /*
     * IRIS_26377_BLACK_FLOOR_CAPTURE_BIAS
     *
     * Evidence-informed extension of 26368. System AE stays ON.
     * The goal is to acquire photons instead of digitally lifting RAW-floor
     * emptiness. This remains bounded and applies only through the existing
     * short-shutter + low-ISO confidence gates.
     */
    private static final float MOTION_26368_AE_MAX_EXTRA_EV = 0.80f;
    private static final long MOTION_26368_AE_FULL_NS = 600000L;
    private static final long MOTION_26368_AE_ZERO_NS = 2000000L;
    private static final int MOTION_26368_AE_FULL_ISO = 70;
    private static final int MOTION_26368_AE_ZERO_ISO = 220;
    /*
     * IRIS_26378_ACTUAL_READY_PREBUFFER
     *
     * Keep the 26377 +0.80 EV ceiling unchanged. Reduce only the response
     * latency so the continuously running RAW ring reaches the already
     * requested exposure state sooner after framing changes.
     */
    private static final int MOTION_26368_AE_CONFIRM_FRAMES = 6;
    private static final long MOTION_26368_AE_MIN_UPDATE_MS = 400L;

    private boolean mMotion26368AeBaseReady = false;
    private int mMotion26368AeBaseSteps = 0;
    private int mMotion26368AeAppliedExtraSteps = 0;
    private int mMotion26368AeCandidateExtraSteps = 0;
    private int mMotion26368AeCandidateFrames = 0;
    private long mMotion26368AeLastUpdateMs = 0L;

    /*
     * IRIS_26380_RAW_CAPTURE_QUALITY
     * Sparse evidence from the same live RAW stream Motion captures.
     */
    private volatile long mMotion26380RawSignalTimestampNs = 0L;
    private volatile float mMotion26380RawFloorFraction = Float.NaN;
    private volatile float mMotion26380RawShadowFraction = Float.NaN;
    private volatile float mMotion26380RawHighlightFraction = Float.NaN;
    private volatile float mMotion26380RawMeanSignal = Float.NaN;
    private volatile int mMotion26380RawSampleCount = 0;

    /* IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER
     * A global clipped-pixel percentage misses tiny but visually dominant LEDs,
     * chandelier rims, flowers and window glints. Keep the per-frame sampler cheap,
     * but dither its coarse lattice over a 3x3 sequence and remember recent coherent
     * clipping. A single hot pixel cannot trigger the short RAW: either at least two
     * sampled physical phases clip in the frame or one sampled 2x2 CFA quad contains
     * two clipped phases. False-positive short capture is safe because the auxiliary
     * never enters the normal Motion accumulator.
     */
    private volatile int mMotion26496RawHighlightSampleCount = 0;
    private volatile int mMotion26496RawCoherentHighlightCells = 0;
    private volatile int mMotion26496RawPeakQuadHighlightPhases = 0;
    private volatile int mMotion26496RawDitherIndex = 0;
    private volatile long mMotion26496RecentHighlightEvidenceTimestampNs = 0L;
    private final java.util.concurrent.atomic.AtomicInteger mMotion26496SparseDitherCounter =
            new java.util.concurrent.atomic.AtomicInteger(0);
    private static final int MOTION_26496_MIN_HIGHLIGHT_SAMPLES = 2;
    private static final long MOTION_26496_HIGHLIGHT_EVIDENCE_HOLD_NS = 400_000_000L;

    /* IRIS_26382_CAPTURE_STATE_HANDOFF */
    private volatile long mMotion26382LastOpportunityCeilingNs = 0L;
    private volatile float mMotion26382LastRawNeed = 0.0f;

    /*
     * IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST
     *
     * Photon-specific acquisition adaptation, not claimed as unpublished
     * Google production code. The published HDR+ principle is an equal-
     * exposure RAW burst exposed low enough to retain highlights.
     *
     * Use the existing 0.2% sparse-RAW highlight onset and request one stop
     * less AE exposure only AFTER shutter press. Old prebuffer frames are
     * cleared so reconstruction receives one actual exposure group.
     */
    private static final float MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER = 0.002f;
    private static final float MOTION_26478_HIGHLIGHT_PROTECTION_EV = 1.0f;
    private boolean mMotion26478HighlightSafeBiasApplied = false;
    private int mMotion26478HighlightSafeBaseSteps = 0;
    private int mMotion26478HighlightSafeTargetSteps = 0;


    /* IRIS_26480_BJZHOU_STYLE_SEPARATE_SHORT_HIGHLIGHT_V1
     * Architecture borrowed from bjzhou/PhotonCamera: one short frame is a
     * separate highlight-recovery observation, never a normal fusion frame.
     * Exposure role is determined from ACTUAL Camera2 exposure*ISO metadata.
     */
    /* IRIS_26495_PHYSICAL_SHORT_HEADROOM_2P5EV
     * One isolated auxiliary RAW is now 2.5 EV below the normal reference when
     * hardware permits. This changes only the evidence acquisition depth; normal
     * ZSL exposure, ISO, Wronski accumulation, display exposure, and tone remain
     * untouched. 2^2.5 = sqrt(32) = 5.656854249492381.
     */
    private static final float MOTION_26480_SHORT_PROTECTION_EV = 2.5f;
    private static final double MOTION_26480_SHORT_EXPOSURE_DIVISOR =
            5.656854249492381;
    private static final long MOTION_26480_SHORT_WAIT_MS = 300L;
    private static final double MOTION_26480_SHORT_TARGET_RATIO =
            1.0 / MOTION_26480_SHORT_EXPOSURE_DIVISOR;
    private static final double MOTION_26480_SHORT_TOLERANCE_EV = 0.35;
    private static final double MOTION_26480_SHORT_RATIO_MIN =
            MOTION_26480_SHORT_TARGET_RATIO / Math.pow(2.0, MOTION_26480_SHORT_TOLERANCE_EV);
    private static final double MOTION_26480_SHORT_RATIO_MAX =
            MOTION_26480_SHORT_TARGET_RATIO * Math.pow(2.0, MOTION_26480_SHORT_TOLERANCE_EV);
    private static final String MOTION_26480_SHORT_TAG = "IRIS_26480_HIGHLIGHT_SHORT";
    private volatile boolean mMotion26480ShortRequestCompleted = false;
    private boolean mMotion26480ShortRequested = false;
    private long mMotion26480ShortBaselineExposureNs = 0L;
    private int mMotion26480ShortBaselineIso = 0;
    private double mMotion26480ShortBaselineEnergy = 0.0;
    private volatile long mMotion26480ShortResultTimestampNs = 0L;
    private volatile long mMotion26480ShortActualExposureNs = 0L;
    private volatile int mMotion26480ShortActualIso = 0;
    private volatile double mMotion26480ShortActualEnergy = 0.0;

    private static float motion26368Clamp01(float value) {
        return Math.max(0.0f, Math.min(1.0f, value));
    }

    /*
     * IRIS_26380_SPARSE_RAW_SIGNAL_SAMPLER
     *
     * About 48 x 36 coarse cells, sampling a 2x2 CFA quad per cell.
     * This does not mutate or copy the RAW frame.
     */
    private void sampleMotion26380RawCaptureQuality(@NonNull Image image) {
        if (!isZslMode() || mCameraCharacteristics == null) {
            return;
        }

        try {
            Integer whiteLevel =
                    mCameraCharacteristics.get(
                            CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
            android.hardware.camera2.params.BlackLevelPattern blackPattern =
                    mCameraCharacteristics.get(
                            CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);

            if (whiteLevel == null
                    || whiteLevel <= 0
                    || blackPattern == null
                    || image.getPlanes() == null
                    || image.getPlanes().length == 0) {
                return;
            }

            Image.Plane plane = image.getPlanes()[0];
            java.nio.ByteBuffer buffer =
                    plane.getBuffer().duplicate()
                            .order(java.nio.ByteOrder.nativeOrder());

            int rowStride = plane.getRowStride();
            int pixelStride = plane.getPixelStride();
            int width = image.getWidth();
            int height = image.getHeight();

            if (rowStride <= 0
                    || pixelStride < 2
                    || width < 8
                    || height < 8) {
                return;
            }

            int stepX = Math.max(4, width / 48);
            int stepY = Math.max(4, height / 36);

            long count = 0L;
            long floorCount = 0L;
            long shadowCount = 0L;
            long highlightCount = 0L;
            double signalSum = 0.0;

            for (int y = 2; y < height - 2; y += stepY) {
                for (int x = 2; x < width - 2; x += stepX) {
                    for (int dy = 0; dy < 2; dy++) {
                        for (int dx = 0; dx < 2; dx++) {
                            int sx = x + dx;
                            int sy = y + dy;
                            int index = sy * rowStride + sx * pixelStride;

                            if (index < 0 || index + 1 >= buffer.limit()) {
                                continue;
                            }

                            int raw = buffer.getShort(index) & 0xffff;
                            int black =
                                    blackPattern.getOffsetForIndex(
                                            sx & 1,
                                            sy & 1);
                            int span = Math.max(1, whiteLevel - black);

                            float signal =
                                    motion26368Clamp01(
                                            (raw - black) / (float) span);

                            signalSum += signal;
                            count++;

                            if (signal <= 0.010f) floorCount++;
                            if (signal <= 0.040f) shadowCount++;
                            if (signal >= 0.980f) highlightCount++;
                        }
                    }
                }
            }

            if (count < 64L) {
                return;
            }

            mMotion26380RawSignalTimestampNs = image.getTimestamp();
            mMotion26380RawFloorFraction = floorCount / (float) count;
            mMotion26380RawShadowFraction = shadowCount / (float) count;
            mMotion26380RawHighlightFraction = highlightCount / (float) count;
            mMotion26380RawMeanSignal = (float) (signalSum / count);
            mMotion26380RawSampleCount =
                    (int) Math.min(Integer.MAX_VALUE, count);

            /* Keep all 26380 AE/readiness statistics above byte-for-byte equivalent
             * to 26494. The 26496 small-highlight detector is a separate read-only
             * pass so it cannot perturb normal exposure authority. */
            sampleMotion26496SpatialHighlightEvidence(
                    image, buffer, rowStride, pixelStride, width, height,
                    whiteLevel, blackPattern);

        } catch (Throwable throwable) {
            Log.w(
                    TAG,
                    "IRIS_26380 sparse RAW signal sampling skipped: "
                            + throwable.getClass().getSimpleName());
        }
    }


    private void sampleMotion26496SpatialHighlightEvidence(
            @NonNull Image image,
            @NonNull java.nio.ByteBuffer buffer,
            int rowStride,
            int pixelStride,
            int width,
            int height,
            int whiteLevel,
            @NonNull android.hardware.camera2.params.BlackLevelPattern blackPattern) {
        try {
            int stepX = Math.max(4, width / 48);
            int stepY = Math.max(4, height / 36);
            int ditherIndex = Math.floorMod(
                    mMotion26496SparseDitherCounter.getAndIncrement(), 9);
            int ditherX = (ditherIndex % 3) * Math.max(1, stepX / 3);
            int ditherY = (ditherIndex / 3) * Math.max(1, stepY / 3);
            int highlightSamples = 0;
            int coherentCells = 0;
            int peakQuadPhases = 0;

            for (int y = 2 + ditherY; y < height - 2; y += stepY) {
                for (int x = 2 + ditherX; x < width - 2; x += stepX) {
                    int quadPhases = 0;
                    for (int dy = 0; dy < 2; ++dy) {
                        for (int dx = 0; dx < 2; ++dx) {
                            int sx = x + dx;
                            int sy = y + dy;
                            int index = sy * rowStride + sx * pixelStride;
                            if (index < 0 || index + 1 >= buffer.limit()) continue;
                            int raw = buffer.getShort(index) & 0xffff;
                            int black = blackPattern.getOffsetForIndex(sx & 1, sy & 1);
                            int span = Math.max(1, whiteLevel - black);
                            float signal = motion26368Clamp01((raw - black) / (float) span);
                            if (signal >= 0.980f) {
                                highlightSamples++;
                                quadPhases++;
                            }
                        }
                    }
                    peakQuadPhases = Math.max(peakQuadPhases, quadPhases);
                    if (quadPhases >= 2) coherentCells++;
                }
            }

            mMotion26496RawHighlightSampleCount = highlightSamples;
            mMotion26496RawCoherentHighlightCells = coherentCells;
            mMotion26496RawPeakQuadHighlightPhases = peakQuadPhases;
            mMotion26496RawDitherIndex = ditherIndex;
            if (highlightSamples >= MOTION_26496_MIN_HIGHLIGHT_SAMPLES
                    || coherentCells > 0) {
                mMotion26496RecentHighlightEvidenceTimestampNs = image.getTimestamp();
            }
        } catch (Throwable throwable) {
            Log.w(TAG, "IRIS_26496 spatial highlight sampler skipped: "
                    + throwable.getClass().getSimpleName());
        }
    }

    /*
     * IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY
     * Public Camera2 only. Advisory to system AE; no direct shutter/ISO set.
     */
    private long iris26381MotionOpportunityCeilingNs(
            @NonNull TotalCaptureResult result) {
        final long absoluteDarkCeilingNs = 1_000_000_000L / 15L;
        final long fastFloorNs = 1_000_000_000L / 120L;
        double equivalent35mm = Double.NaN;

        try {
            Float focal = result.get(CaptureResult.LENS_FOCAL_LENGTH);
            android.util.SizeF sensor =
                    mCameraCharacteristics == null
                            ? null
                            : mCameraCharacteristics.get(
                                    CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
            if (focal != null && focal > 0.0f
                    && sensor != null
                    && sensor.getWidth() > 0.0f
                    && sensor.getHeight() > 0.0f) {
                double sensorDiagonal =
                        Math.hypot(sensor.getWidth(), sensor.getHeight());
                if (sensorDiagonal > 0.0) {
                    equivalent35mm =
                            focal * Math.hypot(36.0, 24.0) / sensorDiagonal;
                }
            }
        } catch (Throwable ignored) {}

        long focalCeilingNs = absoluteDarkCeilingNs;
        if (Double.isFinite(equivalent35mm)
                && equivalent35mm >= 8.0
                && equivalent35mm <= 500.0) {
            double denominator =
                    Math.max(15.0, Math.min(80.0, equivalent35mm / 3.0));
            focalCeilingNs = (long)(1_000_000_000.0 / denominator);
            focalCeilingNs =
                    Math.min(
                            absoluteDarkCeilingNs,
                            Math.max(fastFloorNs, focalCeilingNs));
        }

        double cameraConfidence = 1.0;
        try {
            cameraConfidence =
                    com.particlesdevs.photoncamera.processing.MotionMetrics
                            .cameraMotionConfidence();
        } catch (Throwable ignored) {}
        cameraConfidence = Math.max(0.0, Math.min(1.0, cameraConfidence));

        long motionAwareCeilingNs =
                fastFloorNs
                        + (long)((focalCeilingNs - fastFloorNs)
                                * cameraConfidence);

        return Math.max(
                fastFloorNs,
                Math.min(absoluteDarkCeilingNs, motionAwareCeilingNs));
    }

    /*
     * IRIS_26412_MOTION_V2_EXPOSURE_AUTHORITY
     *
     * Keep HAL AE ON. V2 supplies only a slowly-changing compensation target
     * derived from actual RAW starvation, highlight safety, and the existing
     * focal/motion-aware shutter opportunity. No AE-off/manual shutter toggling.
     */
    private void updateMotionV2ExposureAuthority(
            @NonNull TotalCaptureResult result) {
        if (!isZslMode() || mZslCapturing || burst || isProcessing
                || mPreviewRequestBuilder == null || mCaptureSession == null
                || mCameraCharacteristics == null) return;

        Integer aeMode=result.get(CaptureResult.CONTROL_AE_MODE);
        Long actualExposure=result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer actualIso=result.get(CaptureResult.SENSOR_SENSITIVITY);
        Long ts=result.get(CaptureResult.SENSOR_TIMESTAMP);
        if(aeMode==null || aeMode==CaptureResult.CONTROL_AE_MODE_OFF
                || actualExposure==null || actualIso==null || ts==null
                || actualExposure<=0L || actualIso<=0) return;

        android.util.Range<Integer> range=mCameraCharacteristics.get(
                CameraCharacteristics.CONTROL_AE_COMPENSATION_RANGE);
        android.util.Rational step=mCameraCharacteristics.get(
                CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP);
        if(range==null || step==null || step.floatValue()<=0.0f) return;

        Integer current=mPreviewRequestBuilder.get(
                CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION);
        if(!mMotionV2AeBaseReady){
            mMotionV2AeBaseSteps=current!=null?current:0;
            mMotionV2AeBaseSteps=Math.max(range.getLower(),Math.min(range.getUpper(),mMotionV2AeBaseSteps));
            mMotionV2AeBaseReady=true;
        }

        long age=Math.abs(ts-mMotion26380RawSignalTimestampNs);
        boolean fresh=age<=180_000_000L && mMotion26380RawSampleCount>=64
                && !Float.isNaN(mMotion26380RawFloorFraction)
                && !Float.isNaN(mMotion26380RawShadowFraction)
                && !Float.isNaN(mMotion26380RawHighlightFraction)
                && !Float.isNaN(mMotion26380RawMeanSignal);
        if(!fresh) return;

        float floorNeed=motion26368Clamp01((mMotion26380RawFloorFraction-0.10f)/(0.58f-0.10f));
        float shadowNeed=motion26368Clamp01((mMotion26380RawShadowFraction-0.24f)/(0.78f-0.24f));
        float meanNeed=1.0f-motion26368Clamp01((mMotion26380RawMeanSignal-0.035f)/(0.18f-0.035f));
        float rawNeed=Math.max(floorNeed,0.72f*shadowNeed)*(0.40f+0.60f*meanNeed);

        float highlightSafety=1.0f-0.75f*motion26368Clamp01(
                (mMotion26380RawHighlightFraction-0.008f)/(0.10f-0.008f));
        long shutterCeiling=iris26381MotionOpportunityCeilingNs(result);
        float shutterOpportunity=motion26368Clamp01(
                (shutterCeiling-actualExposure)/(float)Math.max(1L,shutterCeiling));
        float requestedExtraEv=1.65f*rawNeed*highlightSafety*(0.45f+0.55f*shutterOpportunity);
        requestedExtraEv=Math.max(0.0f,requestedExtraEv);

        int extraSteps=Math.round(requestedExtraEv/step.floatValue());
        int target=Math.max(range.getLower(),Math.min(range.getUpper(),mMotionV2AeBaseSteps+extraSteps));
        long now=android.os.SystemClock.elapsedRealtime();
        if(mMotionV2AeAppliedSteps!=Integer.MIN_VALUE
                && Math.abs(target-mMotionV2AeAppliedSteps)<1) return;
        if(now-mMotionV2AeLastUpdateMs<500L) return;

        try{
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION,target);
            mMotionV2AeAppliedSteps=target;
            mMotionV2AeLastUpdateMs=now;
            rebuildPreviewBuilder();
            Log.i(TAG,"IRIS_26412_V2_EXPOSURE_PLAN"
                    +" actualExposureNs="+actualExposure+" actualIso="+actualIso
                    +" rawFloor="+mMotion26380RawFloorFraction
                    +" rawShadow="+mMotion26380RawShadowFraction
                    +" rawHighlight="+mMotion26380RawHighlightFraction
                    +" rawMean="+mMotion26380RawMeanSignal
                    +" shutterCeilingNs="+shutterCeiling
                    +" rawNeed="+rawNeed+" requestedExtraEv="+requestedExtraEv
                    +" compensationSteps="+target+" halAeRemainsOn=true");
        }catch(IllegalArgumentException|IllegalStateException e){
            Log.w(TAG,"IRIS_26412 V2 exposure authority skipped: "+e.getClass().getSimpleName());
        }
    }
    private void updateMotion26368AdaptiveAeBias(
            @NonNull TotalCaptureResult result) {
        if (PhotonCamera.getSettings().selectedMode != CameraMode.MOTION
                || mPreviewRequestBuilder == null
                || mCaptureSession == null
                || mCameraCharacteristics == null) {
            return;
        }

        Integer aeMode = result.get(CaptureResult.CONTROL_AE_MODE);
        Long actualExposure =
                result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer actualIso =
                result.get(CaptureResult.SENSOR_SENSITIVITY);

        if (aeMode == null
                || aeMode == CaptureResult.CONTROL_AE_MODE_OFF
                || actualExposure == null
                || actualIso == null
                || actualExposure <= 0L
                || actualIso <= 0) {
            return;
        }

        android.util.Range<Integer> aeRange =
                mCameraCharacteristics.get(
                        android.hardware.camera2.CameraCharacteristics
                                .CONTROL_AE_COMPENSATION_RANGE);
        android.util.Rational aeStep =
                mCameraCharacteristics.get(
                        android.hardware.camera2.CameraCharacteristics
                                .CONTROL_AE_COMPENSATION_STEP);

        if (aeRange == null
                || aeStep == null
                || aeRange.getUpper() <= 0
                || aeStep.floatValue() <= 0.0f) {
            return;
        }

        Integer currentSteps =
                mPreviewRequestBuilder.get(
                        CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION);

        if (!mMotion26368AeBaseReady) {
            mMotion26368AeBaseSteps =
                    currentSteps != null ? currentSteps : 0;
            mMotion26368AeBaseSteps =
                    Math.max(
                            aeRange.getLower(),
                            Math.min(
                                    aeRange.getUpper(),
                                    mMotion26368AeBaseSteps));
            mMotion26368AeBaseReady = true;
        }

        float shutterConfidence =
                motion26368Clamp01(
                        (float) (MOTION_26368_AE_ZERO_NS
                                - actualExposure)
                                / (float) (MOTION_26368_AE_ZERO_NS
                                - MOTION_26368_AE_FULL_NS));

        float isoConfidence =
                motion26368Clamp01(
                        (float) (MOTION_26368_AE_ZERO_ISO
                                - actualIso)
                                / (float) (MOTION_26368_AE_ZERO_ISO
                                - MOTION_26368_AE_FULL_ISO));

        float brightSceneConfidence =
                shutterConfidence * isoConfidence;

        /*
         * IRIS_26380_SCENE_RELATIVE_EXPOSURE_NEED
         *
         * RAW signal is primary when fresh. ISO is only a soft modifier.
         */
        Long iris26380ResultTimestamp =
                result.get(CaptureResult.SENSOR_TIMESTAMP);

        long iris26380RawAgeNs =
                iris26380ResultTimestamp == null
                        || mMotion26380RawSignalTimestampNs <= 0L
                        ? Long.MAX_VALUE
                        : Math.abs(
                                iris26380ResultTimestamp
                                        - mMotion26380RawSignalTimestampNs);

        boolean iris26380RawFresh =
                iris26380RawAgeNs <= 150_000_000L
                        && !Float.isNaN(mMotion26380RawFloorFraction)
                        && !Float.isNaN(mMotion26380RawShadowFraction)
                        && !Float.isNaN(mMotion26380RawHighlightFraction)
                        && !Float.isNaN(mMotion26380RawMeanSignal)
                        && mMotion26380RawSampleCount >= 64;

        float iris26380FloorPressure =
                iris26380RawFresh
                        ? motion26368Clamp01(
                                (mMotion26380RawFloorFraction - 0.18f)
                                        / (0.55f - 0.18f))
                        : 0.0f;

        float iris26380ShadowPressure =
                iris26380RawFresh
                        ? motion26368Clamp01(
                                (mMotion26380RawShadowFraction - 0.35f)
                                        / (0.78f - 0.35f))
                        : 0.0f;

        float iris26380HighlightPressure =
                iris26380RawFresh
                        ? motion26368Clamp01(
                                (mMotion26380RawHighlightFraction - 0.002f)
                                        / (0.035f - 0.002f))
                        : 0.0f;

        float iris26380HighlightSafety =
                1.0f - iris26380HighlightPressure;

        float iris26380MeanDarkness =
                iris26380RawFresh
                        ? 1.0f
                                - motion26368Clamp01(
                                        (mMotion26380RawMeanSignal - 0.050f)
                                                / (0.220f - 0.050f))
                        : 0.0f;

        float iris26380RawNeed =
                iris26380RawFresh
                        ? Math.max(
                                iris26380FloorPressure,
                                0.70f * iris26380ShadowPressure)
                                * iris26380HighlightSafety
                                * (0.45f + 0.55f * iris26380MeanDarkness)
                        : 0.0f;

        /*
         * IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY
         * Replace 26380's fixed ~33 ms ceiling with a focal/camera-motion
         * aware ceiling that can approach the established 1/15 s dark limit.
         */
        long iris26381OpportunityCeilingNs =
                iris26381MotionOpportunityCeilingNs(result);
        mMotion26382LastOpportunityCeilingNs = iris26381OpportunityCeilingNs;

        float iris26380ShutterOpportunity =
                iris26381OpportunityCeilingNs <= 2_000_000L
                        ? 0.0f
                        : motion26368Clamp01(
                                (iris26381OpportunityCeilingNs
                                        - actualExposure)
                                        / (float)Math.max(
                                                1L,
                                                iris26381OpportunityCeilingNs
                                                        - 2_000_000L));

        /*
         * ISO is deliberately only a soft modifier.
         */
        float iris26380IsoModifier =
                0.72f + 0.28f * isoConfidence;

        /*
         * IRIS_26382_RAW_QUALITY_DRIVES_PRESSURE
         *
         * 26381 correctly found the legal shutter ceiling, but multiplied
         * severe RAW starvation by the remaining-distance fraction. That
         * made pressure collapse near the ceiling even when RAW quality had
         * not improved. Keep a bounded pressure floor while more legal
         * integration time exists; let RAW quality/highlights terminate it.
         */
        float iris26382OpportunityEligibility =
                iris26380ShutterOpportunity > 0.015f ? 1.0f : 0.0f;
        float iris26382SevereNeed =
                motion26368Clamp01((iris26380RawNeed - 0.45f) / 0.45f);
        float iris26382PressureShape =
                Math.max(
                        iris26380ShutterOpportunity,
                        iris26382OpportunityEligibility
                                * (0.55f + 0.25f * iris26382SevereNeed));

        float iris26380RawRequestedExtraEv =
                MOTION_26368_AE_MAX_EXTRA_EV
                        * iris26380RawNeed
                        * iris26382PressureShape
                        * iris26380IsoModifier;
        mMotion26382LastRawNeed = iris26380RawNeed;

        float iris26380MetadataFallbackEv =
                MOTION_26368_AE_MAX_EXTRA_EV
                        * brightSceneConfidence;

        float requestedExtraEv =
                iris26380RawFresh
                        ? iris26380RawRequestedExtraEv
                        : iris26380MetadataFallbackEv;

        int requestedExtraSteps =
                Math.max(
                        0,
                        Math.round(
                                requestedExtraEv
                                        / aeStep.floatValue()));

        int maximumExtraSteps =
                Math.max(
                        0,
                        aeRange.getUpper()
                                - mMotion26368AeBaseSteps);

        requestedExtraSteps =
                Math.min(
                        requestedExtraSteps,
                        maximumExtraSteps);

        if (requestedExtraSteps
                != mMotion26368AeCandidateExtraSteps) {
            mMotion26368AeCandidateExtraSteps =
                    requestedExtraSteps;
            mMotion26368AeCandidateFrames = 1;
        } else {
            mMotion26368AeCandidateFrames++;
        }

        if (mMotion26368AeCandidateFrames
                < MOTION_26368_AE_CONFIRM_FRAMES) {
            return;
        }

        if (requestedExtraSteps
                == mMotion26368AeAppliedExtraSteps) {
            return;
        }

        long nowMs = android.os.SystemClock.elapsedRealtime();
        if (nowMs - mMotion26368AeLastUpdateMs
                < MOTION_26368_AE_MIN_UPDATE_MS) {
            return;
        }

        int finalSteps =
                Math.max(
                        aeRange.getLower(),
                        Math.min(
                                aeRange.getUpper(),
                                mMotion26368AeBaseSteps
                                        + requestedExtraSteps));

        try {
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION,
                    finalSteps);

            mMotion26368AeAppliedExtraSteps =
                    requestedExtraSteps;
            mMotion26368AeLastUpdateMs = nowMs;

            rebuildPreviewBuilder();

            Log.i(
                    TAG,
                    "IRIS_26368_MOTION_ADAPTIVE_AE_BIAS"
                            + " exposureNs=" + actualExposure
                            + " iso=" + actualIso
                            + " shutterConfidence="
                            + shutterConfidence
                            + " isoConfidence="
                            + isoConfidence
                            + " brightSceneConfidence="
                            + brightSceneConfidence
                            + " iris26377BlackFloorCaptureBias=true"
                            + " iris26380RawFresh=" + iris26380RawFresh
                            + " iris26380RawAgeNs=" + iris26380RawAgeNs
                            + " iris26380FloorFraction="
                            + mMotion26380RawFloorFraction
                            + " iris26380ShadowFraction="
                            + mMotion26380RawShadowFraction
                            + " iris26380HighlightFraction="
                            + mMotion26380RawHighlightFraction
                            + " iris26380MeanSignal="
                            + mMotion26380RawMeanSignal
                            + " iris26380RawSamples="
                            + mMotion26380RawSampleCount
                            + " iris26380RawNeed=" + iris26380RawNeed
                            + " iris26380ShutterOpportunity="
                            + iris26380ShutterOpportunity
                            + " iris26381OpportunityCeilingNs="
                            + iris26381OpportunityCeilingNs
                            + " iris26380IsoModifier="
                            + iris26380IsoModifier
                            + " iris26380RawRequestedExtraEv="
                            + iris26380RawRequestedExtraEv
                            + " iris26382PressureShape="
                            + iris26382PressureShape
                            + " iris26382SevereNeed="
                            + iris26382SevereNeed
                            + " iris26380MetadataFallbackEv="
                            + iris26380MetadataFallbackEv
                            + " baseSteps="
                            + mMotion26368AeBaseSteps
                            + " extraSteps="
                            + requestedExtraSteps
                            + " finalSteps="
                            + finalSteps
                            + " stepEv="
                            + aeStep.floatValue()
                            + " appliedExtraEv="
                            + (requestedExtraSteps
                                    * aeStep.floatValue())
                            + " aeMode=" + aeMode);
        } catch (IllegalArgumentException
                | IllegalStateException exception) {
            Log.e(
                    TAG,
                    "IRIS_26368 AE compensation update failed: "
                            + Log.getStackTraceString(exception));
        }
    }

    private void restoreMotionPreviewAe() {
        /*
         * IRIS_26346_CONTINUOUS_AE_GROUPS
         *
         * Motion preview now remains under one continuous AE request. The old
         * implementation switched the repeating request from manual exposure
         * back to AE, rebuilt it, then switched back to manual. That request
         * oscillation was the source of the visible preview flash.
         *
         * Keep this private helper as a state reset for compatibility, but do
         * not mutate or resubmit the preview request here.
         */
        mMotionAeProbeActive = false;
        mMotionManualLadderActive = false;
        mMotionManualFrames = 0;
        mMotionAeWarmupFrames = 0;
        mMotionAeProbeFrames = 0;
        mMotionCandidateZone = 0;
        mMotionCandidateFrames = 0;
        mMotionActualCandidateExposureNs = 0L;
        mMotionActualCandidateIso = 0;
        mMotionActualCandidateFrames = 0;
        mMotionLastLadderDecision = "";
    }
    private int chooseMotionBrightnessZone(
            long exposureEnergy,
            int aeIso) {

        if (exposureEnergy >= MOTION_ZONE_15_ENERGY
                && aeIso >= MOTION_ZONE_15_MIN_AE_ISO) {
            return 3;
        }

        if (exposureEnergy >= MOTION_ZONE_30_ENERGY
                && aeIso >= MOTION_ZONE_30_MIN_AE_ISO) {
            return 2;
        }

        return 1;
    }
    private int chooseMotionGyroLimitZone(int gyroShakiness) {
        // Zone 3 (1/15) requires a very steady camera. Zone 2 (1/30) tolerates
        // moderate movement. Zone 1 (1/60) remains available for shaky scenes.
        if (gyroShakiness <= 35) return 3;
        if (gyroShakiness <= 180) return 2;
        return 1;
    }

    private void logMotionLadderDecision(
            int brightnessZone,
            int motionLimitZone,
            int desiredZone,
            long exposureEnergy,
            long actualExposure,
            int actualIso,
            int gyroShakiness,
            String reason) {

        String signature = brightnessZone
                + ":" + motionLimitZone
                + ":" + desiredZone
                + ":" + reason;

        if (signature.equals(mMotionLastLadderDecision)) {
            return;
        }

        mMotionLastLadderDecision = signature;

        Log.i(TAG, "MOTION_LADDER_DECISION"
                + " reason=" + reason
                + " brightnessZone=" + brightnessZone
                + " motionLimitZone=" + motionLimitZone
                + " desiredZone=" + desiredZone
                + " aeEnergy=" + exposureEnergy
                + " aeExposureNs=" + actualExposure
                + " aeIso=" + actualIso
                + " gyroShakiness=" + gyroShakiness
                + " candidateZone=" + mMotionCandidateZone
                + " candidateFrames=" + mMotionCandidateFrames);
    }

    private long exposureForMotionZone(
            int zone,
            Integer antibandingMode) {

        boolean fiftyHz = antibandingMode != null
                && antibandingMode
                == CaptureResult.CONTROL_AE_ANTIBANDING_MODE_50HZ;

        if (fiftyHz) {
            if (zone >= 3) return 1_000_000_000L / 20L;
            if (zone == 2) return 1_000_000_000L / 30L;
            return 1_000_000_000L / 60L;
        }

        if (zone >= 3) return 1_000_000_000L / 15L;
        if (zone == 2) return 1_000_000_000L / 30L;
        return 1_000_000_000L / 60L;
    }
    private void updateMotionUnifiedExposure(
            @NonNull CaptureRequest completedRequest,
            @NonNull TotalCaptureResult result) {

        if (!isZslMode()
                || mZslCapturing
                || burst
                || isProcessing) {
            return;
        }

        Long actualExposure =
                result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer actualIso =
                result.get(CaptureResult.SENSOR_SENSITIVITY);
        if (actualExposure == null || actualIso == null
                || actualExposure <= 0L || actualIso <= 0) {
            return;
        }

        /*
         * Continuous AE observer only. This callback records actual exposure
         * groups and never changes or resubmits the preview request.
         */
        mMotionAeProbeActive = false;
        mMotionManualLadderActive = false;
        mMotionManualFrames = 0;

        boolean sameCandidate = false;
        if (mMotionActualCandidateExposureNs > 0L
                && mMotionActualCandidateIso > 0) {
            long exposureTolerance = Math.max(
                    750_000L,
                    mMotionActualCandidateExposureNs / 12L);
            int isoTolerance = Math.max(
                    2,
                    mMotionActualCandidateIso / 10);

            sameCandidate =
                    Math.abs(actualExposure
                            - mMotionActualCandidateExposureNs)
                            <= exposureTolerance
                    && Math.abs(actualIso
                            - mMotionActualCandidateIso)
                            <= isoTolerance;
        }

        if (sameCandidate) {
            mMotionActualCandidateFrames++;
        } else {
            mMotionActualCandidateExposureNs = actualExposure;
            mMotionActualCandidateIso = actualIso;
            mMotionActualCandidateFrames = 1;
        }

        if (mMotionActualCandidateFrames
                >= MOTION_ACTUAL_GENERATION_CONFIRM_FRAMES) {
            boolean groupChanged =
                    mMotionUnifiedExposureNs <= 0L
                            || mMotionUnifiedIso <= 0
                            || Math.abs(actualExposure
                                    - mMotionUnifiedExposureNs)
                                    > Math.max(
                                            750_000L,
                                            actualExposure / 12L)
                            || Math.abs(actualIso
                                    - mMotionUnifiedIso)
                                    > Math.max(2, actualIso / 10);

            mMotionUnifiedExposureNs = actualExposure;
            mMotionUnifiedIso = actualIso;
            mMotionUnifiedSettledFrames =
                    mMotionActualCandidateFrames;

            if (groupChanged) {
                Log.i(TAG, "MOTION_CONTINUOUS_AE_GROUP"
                        + " exposureNs=" + actualExposure
                        + " iso=" + actualIso
                        + " stableFrames="
                        + mMotionActualCandidateFrames
                        + " ringCleared=false"
                        + " previewRebuilt=false");
            }
        }
    }

    /* IRIS_26526_CAMERA2_SINGLE_PREVIEW_AUTHORITY
     * Bind the request to the actual CameraCaptureSession device whenever possible,
     * not the mutable preference that merely requests a restart.
     */
    private void iris26524ApplyZoomToPreviewBuilder() {
        if (mPreviewRequestBuilder == null || mCameraCharacteristics == null) return;
        IrisCameraRoute irisRoute = mCaptureSession == null
                ? mIrisOpeningRoute : mIrisSessionRoutes.get(mCaptureSession);
        String iris26527ActiveOwner = irisRoute != null
                ? irisRoute.provenOwnerId
                : (mCameraDevice == null ? null : mCameraDevice.getId());
        float residual = IrisZoomController.applyToRequest(
                mPreviewRequestBuilder, mCameraCharacteristics, iris26527ActiveOwner);
        if (mTextureView != null) mTextureView.setSoftwareZoom(residual);
    }

    public void applyIrisZoomNow() {
        if (burst || mPreviewRequestBuilder == null || mCaptureSession == null) return;
        rebuildPreviewBuilder();
    }

    public void rebuildPreviewBuilder() {
        if(burst) return;
        try {
//            mCaptureSession.stopRepeating();
            iris26524ApplyZoomToPreviewBuilder();
            mCaptureSession.setRepeatingRequest(mPreviewInputRequest = mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
        } catch (IllegalStateException | IllegalArgumentException | NullPointerException e) {
            Logger.warnShort(TAG, "Cannot rebuildPreviewBuilder()!", e);
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    public void rebuildPreviewBuilderOneShot() {
        if(burst) return;
        try {
            Log.d(TAG, "rebuildPreviewBuilderOneShot: " + mCaptureSession + " " + mPreviewRequestBuilder + " " + mCaptureCallback + " " + mBackgroundHandler);
            iris26524ApplyZoomToPreviewBuilder();
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
        } catch (IllegalStateException | IllegalArgumentException | NullPointerException e) {
            Logger.warnShort(TAG, "Cannot rebuildPreviewBuilderOneShot()!", e);
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    /**
     * Configures the necessary {@link Matrix} transformation to `mTextureView`.
     * This method should be called after the camera preview size is determined in
     * setUpCameraOutputs and also the size of `mTextureView` is fixed.
     *
     * @param viewWidth  The width of `mTextureView`
     * @param viewHeight The height of `mTextureView`
     */
    private void configureTransform(int viewWidth, int viewHeight) {
        if (null == mTextureView || null == mPreviewSize) {
            return;
        }
        int rotation = PhotonCamera.getGravity().getRotation();//activity.getWindowManager().getDefaultDisplay().getRotation();
        Matrix matrix = new Matrix();
        RectF viewRect = new RectF(0, 0, viewWidth, viewHeight);
        RectF bufferRect = new RectF(0, 0, mPreviewSize.getHeight(), mPreviewSize.getWidth());
        float centerX = viewRect.centerX();
        float centerY = viewRect.centerY();
        /*
        if (Surface.ROTATION_90 == rotation || Surface.ROTATION_270 == rotation) {
            bufferRect.offset(centerX - bufferRect.centerX(), centerY - bufferRect.centerY());
            matrix.setRectToRect(viewRect, bufferRect, Matrix.ScaleToFit.FILL);
            float scale = Math.max(
                    (float) viewHeight / mPreviewSize.getHeight(),
                    (float) viewWidth / mPreviewSize.getWidth());
            matrix.postScale(scale, scale, centerX, centerY);
            matrix.postRotate(90 * (rotation - 2), centerX, centerY);
        } else if (Surface.ROTATION_180 == rotation) {
            matrix.postRotate(180, centerX, centerY);
        }*/
        //mTextureView.setTransform(matrix);
        mTextureView.setOrientation(mSensorOrientation+90);
        updatePreviewMirror();
    }

    private void updatePreviewMirror() {
        if (mTextureView == null || mCameraCharacteristics == null) {
            return;
        }
        Integer facing = mCameraCharacteristics.get(CameraCharacteristics.LENS_FACING);
        boolean mirror = facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT;
        mTextureView.setMirror(mirror);
    }

    private ArrayList<Size> getAllTargets(){
        CameraCharacteristics characteristics =  this.mCameraCharacteristicsMap.get(physicalID);
        StreamConfigurationMap map = characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        ArrayList<Size> allTargets = new ArrayList<>();

        Size[] targetSizes = map.getOutputSizes(mTargetFormat);
        if(targetSizes != null)
            allTargets.addAll(Arrays.asList(targetSizes));
        if(PhotonCamera.getSettings().QuadBayer) {
            useMaximumResolutionKey = false;
            int[] capabilities = characteristics.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if (capabilities != null) for (int capability : capabilities) {
                if (capability == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_ULTRA_HIGH_RESOLUTION_SENSOR) {
                    Size arraySize = null;
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        arraySize = characteristics.get(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE_MAXIMUM_RESOLUTION);
                    }
                    if(arraySize != null) {
                        useMaximumResolutionKey = true;
                        allTargets.add(arraySize);
                    }
                }
            }
            if(!useMaximumResolutionKey) {
                Size[] highResSizes = map.getHighResolutionOutputSizes(mTargetFormat);
                // Extend targetSizes with high resolution sizes
                if (highResSizes != null && highResSizes.length > 0) {
                    allTargets.addAll(Arrays.asList(highResSizes));
                }
                var keys = CameraReflectionApi.getCameraCharacteristicsKeys(characteristics, null, true);
                for (Object keyObj : keys) {
                    try {
                        if (keyObj instanceof CameraCharacteristics.Key<?>) {
                            CameraCharacteristics.Key<?> key = (CameraCharacteristics.Key<?>) keyObj;
                            if (key.getName().contains("StreamConfigurations")) {
                                Object res = characteristics.get(key);
                                int[] vals = (int[]) res;
                                for (int i = 0; i < vals.length; i += 4) {
                                    int format = vals[i];
                                    int width = vals[i + 1];
                                    int height = vals[i + 2];
                                    if (format == mTargetFormat) {
                                        allTargets.add(new Size(width, height));
                                        Log.d(TAG, "Added custom resolution(" + key.getName() + "):" + width + " " + height);
                                    }
                                }
                            }
                        }
                    } catch (Exception ignored) {
                    }
                }
            }
        }
        return allTargets;
    }
    private IrisCameraRoute iris26527ResolveRoute(String selectedId) {
        String requested = selectedId == null ? "" : selectedId;
        String logical = requested;
        String physical = requested;
        if (requested.contains("-")) {
            String[] ids = requested.split("-", 2);
            logical = ids[0];
            physical = ids[1];
        }
        boolean directListed = false;
        try {
            directListed = Arrays.asList(mCameraManager.getCameraIdList()).contains(physical);
        } catch (Throwable ignored) {}
        if (!requested.equals(physical) && directListed) {
            return new IrisCameraRoute(requested, physical, null, physical, requested,
                    "direct-physical");
        }
        if (!requested.equals(physical) && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            try {
                CameraCharacteristics logicalChars = mCameraManager.getCameraCharacteristics(logical);
                if (logicalChars.getPhysicalCameraIds().contains(physical)) {
                    return new IrisCameraRoute(requested, logical, physical, physical, requested,
                            "logical+physical-output");
                }
            } catch (Throwable ignored) {}
            /* IRIS_26527_ADAPTIVE_LOGICAL_PHYSICAL_SEARCH
             * Some vendors expose the requested physical lens under a logical camera other than
             * the settings hint. Search Camera2's real public IDs before degrading to logical-only.
             */
            try {
                for (String candidateLogical : mCameraManager.getCameraIdList()) {
                    CameraCharacteristics candidateChars =
                            mCameraManager.getCameraCharacteristics(candidateLogical);
                    if (candidateChars.getPhysicalCameraIds().contains(physical)) {
                        return new IrisCameraRoute(requested, candidateLogical, physical,
                                physical, requested, "adaptive-logical+physical-output");
                    }
                }
            } catch (Throwable error) {
                Log.w(TAG, "IRIS_26527_ADAPTIVE_ROUTE_SEARCH_FAILED requested=" + requested
                        + " error=" + error.getClass().getSimpleName());
            }
        }
        String opened = requested.equals(physical) ? physical : logical;
        return new IrisCameraRoute(requested, opened, null, opened, opened, "logical-only");
    }

    private void iris26527ApplyRouteToLegacyFields(IrisCameraRoute route) {
        if (route == null) return;
        logicalID = route.openedDeviceId;
        physicalID = route.characteristicsId;
        UpdateCameraCharacteristics(route.characteristicsId);
    }

    public void restartCameraForIrisHandoff(String requestedOwnerId) {
        PreferenceKeys.setCameraID(requestedOwnerId);
        final long generation = ++mIrisZoomCurtainGeneration;
        /* IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART
         * restartCamera() historically runs from CameraUIController / ScaleGestureDetector on
         * the main thread and directly touches UI-owned preview state. 26527 moved it onto
         * processExecutor behind the curtain, violating that contract and crashing at each
         * optical boundary. Always marshal the actual restart back to the Activity main thread.
         */
        Runnable restart = () -> activity.runOnUiThread(() -> {
            if (generation != mIrisZoomCurtainGeneration) return;
            Log.i(TAG, "IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART generation="
                    + generation + " thread=" + Thread.currentThread().getName());
            restartCamera();
        });
        if (mTextureView == null) {
            restart.run();
            return;
        }
        activity.runOnUiThread(() -> {
            if (mIrisZoomCurtainClosed) {
                restart.run();
            } else {
                mIrisZoomCurtainClosed = true;
                mTextureView.animate().cancel();
                mTextureView.animate().alpha(0.0f).setDuration(90L)
                        .withEndAction(restart).start();
            }
            mTextureView.postDelayed(() -> {
                if (generation != mIrisZoomCurtainGeneration || !mIrisZoomCurtainClosed) return;
                Log.e(TAG, "IRIS_26527_ZOOM_CURTAIN_FAILSAFE generation=" + generation);
                IrisZoomController.abortPendingHandoff("curtain-timeout");
                mIrisZoomCurtainClosed = false;
                mTextureView.animate().cancel();
                mTextureView.setAlpha(1.0f);
                ++mIrisZoomCurtainGeneration;
            }, IRIS_26527_CURTAIN_FAILSAFE_MS);
        });
    }

    private void iris26527RevealZoomCurtain(String provenOwnerId) {
        if (!mIrisZoomCurtainClosed || mTextureView == null) return;
        final long generation = ++mIrisZoomCurtainGeneration;
        activity.runOnUiThread(() -> {
            if (generation != mIrisZoomCurtainGeneration) return;
            mIrisZoomCurtainClosed = false;
            mTextureView.animate().cancel();
            mTextureView.animate().alpha(1.0f).setDuration(90L).start();
            Log.i(TAG, "IRIS_26527_ZOOM_CURTAIN_REVEAL provenOwner=" + provenOwnerId);
        });
    }

    private void iris26548BeginCameraHealthGeneration(String reason) {
        mIris26548CameraHealthGeneration++;
        mIris26548SessionConfigured = false;
        mIris26548RepeatingSubmitted = false;
        mIris26548FirstCaptureResult = false;
        mIris26548FirstZslRaw = false;
        Log.i(TAG, "IRIS_26548_CAMERA_START_REQUESTED generation="
                + mIris26548CameraHealthGeneration + " reason=" + reason);
    }

    private boolean iris26548MotionZslHasFrames() {
        synchronized (mZslBufferLock) {
            return !mZslRingBuffer.isEmpty();
        }
    }

    private boolean iris26555PreviewFlowHealthy() {
        return mIris26548SessionConfigured && mIris26548RepeatingSubmitted
                && mIris26548FirstCaptureResult && mTextureView != null
                && mTextureView.hasReceivedPreviewFrame();
    }

    private boolean iris26555MotionZslReady() {
        return PhotonCamera.getSettings().selectedMode != CameraMode.MOTION
                || !mIris26555RawStreamAvailable
                || (mIris26548FirstZslRaw && iris26548MotionZslHasFrames());
    }

    private boolean iris26555PreviewOnlyRecoveryActive() {
        return mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP
                || mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_PREVIEW_ONLY_FALLBACK;
    }

    private boolean iris26548CameraFlowHealthy() {
        if (!iris26555PreviewFlowHealthy()) return false;
        // Preview-only recovery intentionally has no RAW target. Its health proof is real
        // CaptureResult + real SurfaceTexture flow; RAW is evaluated only after full promotion.
        return iris26555PreviewOnlyRecoveryActive() || iris26555MotionZslReady();
    }

    private boolean iris26555CaptureOrProcessingOwnsCamera() {
        boolean nightOwned;
        synchronized (mIrisNight26540Lock) {
            nightOwned = mIrisNight26553ShutterDispatchPending || mIrisNight26540CaptureActive;
        }
        return CaptureController.isProcessing || mZslCapturing || burst
                || mState != STATE_PREVIEW || nightOwned;
    }

    private void iris26548SchedulePostOpenHealthCheck(@NonNull CameraDevice cameraDevice) {
        if (mBackgroundHandler == null) return;
        final long generation = mIris26548CameraHealthGeneration;
        mBackgroundHandler.postDelayed(() -> {
            if (generation != mIris26548CameraHealthGeneration
                    || mCameraDevice != cameraDevice) return;
            final boolean previewHealthy = iris26555PreviewFlowHealthy();
            final boolean motionZslReady = iris26555MotionZslReady();
            final boolean healthy = iris26548CameraFlowHealthy();
            Log.i(TAG, "IRIS_26548_CAMERA_HEALTH_CHECK generation=" + generation
                    + " healthy=" + healthy
                    + " sessionConfigured=" + mIris26548SessionConfigured
                    + " repeatingSubmitted=" + mIris26548RepeatingSubmitted
                    + " firstCaptureResult=" + mIris26548FirstCaptureResult
                    + " firstPreviewFrame=" + (mTextureView != null && mTextureView.hasReceivedPreviewFrame())
                    + " firstZslRaw=" + mIris26548FirstZslRaw
                    + " zslBuffered=" + iris26548MotionZslHasFrames()
                    + " recoveryCount=" + mIris26548ConsecutiveHealthRecoveries);
            Log.i(TAG, "IRIS_26553_PREVIEW_DIAG_HEALTH generation=" + generation
                    + " view=" + (mTextureView == null ? "null"
                    : (mTextureView.getWidth() + "x" + mTextureView.getHeight()
                    + ",alpha=" + mTextureView.getAlpha()
                    + ",visibility=" + mTextureView.getVisibility()))
                    + " outputSurfaceValid=" + (surface != null && surface.isValid())
                    + " device=" + (mCameraDevice == null ? "null" : mCameraDevice.getId())
                    + " activeRoute=" + mIrisActiveRoute);

            if (healthy) {
                if (mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP) {
                    iris26555PromoteProvenPreviewToFullTopology(cameraDevice, generation);
                    return;
                }
                if (mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY) {
                    Log.i(TAG, "IRIS_26555_PREVIEW_RECOVERY_FULL_TOPOLOGY_PROVEN generation="
                            + generation + " rawReady=" + motionZslReady);
                    mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_NONE;
                }
                mIris26548ConsecutiveHealthRecoveries = 0;
                return;
            }

            // A live preview with a not-yet-populated Motion RAW ring is not a black-preview
            // failure. Keep the working session and let the shutter readiness guard wait for RAW.
            if (previewHealthy && !motionZslReady) {
                Log.w(TAG, "IRIS_26555_MOTION_ZSL_NOT_READY generation=" + generation
                        + " previewPreserved=true sessionRecovery=false");
                return;
            }

            if (iris26555CaptureOrProcessingOwnsCamera()) {
                Log.w(TAG, "IRIS_26555_CAMERA_RECOVERY_SUPPRESSED captureOrProcessingOwner=true"
                        + " generation=" + generation);
                return;
            }

            if (mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY) {
                // The preview-only bootstrap proved the device/Surface path. If adding the normal
                // outputs kills flow again, preserve preview rather than repeating that topology.
                iris26555ReturnToPreviewOnlyFallback(cameraDevice, generation);
                return;
            }
            if (mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_PREVIEW_ONLY_FALLBACK) {
                Log.e(TAG, "IRIS_26555_PREVIEW_RECOVERY_TERMINAL generation=" + generation
                        + " previewOnlyFallbackSilent=true repeatedRecovery=false");
                return;
            }
            if (mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP) {
                Log.e(TAG, "IRIS_26555_PREVIEW_RECOVERY_TERMINAL generation=" + generation
                        + " previewOnlyBootstrapSilent=true repeatedRecovery=false");
                return;
            }

            if (mIris26548ConsecutiveHealthRecoveries >= 1) {
                Log.e(TAG, "IRIS_26548_CAMERA_SESSION_STALLED recoverySuppressed=true generation="
                        + generation + " recoveryStage=" + mIris26555PreviewRecoveryStage);
                return;
            }

            final boolean previewFrameMissing = mTextureView == null
                    || !mTextureView.hasReceivedPreviewFrame();
            final boolean configuredButSilent = mIris26548SessionConfigured
                    && mIris26548RepeatingSubmitted
                    && (!mIris26548FirstCaptureResult || previewFrameMissing);
            mIris26548ConsecutiveHealthRecoveries++;
            if (configuredButSilent) {
                Log.e(TAG, "IRIS_26555_PREVIEW_SILENT_SESSION_RECOVERY generation=" + generation
                        + " recovery=preview_only_bootstrap"
                        + " missingResult=" + !mIris26548FirstCaptureResult
                        + " missingPreview=" + previewFrameMissing
                        + " manufacturerGate=false");
                iris26555RecoverConfiguredButSilentSession(cameraDevice, generation);
            } else {
                Log.e(TAG, "IRIS_26548_CAMERA_SESSION_STALLED recovery=single_restart generation="
                        + generation + " configured=" + mIris26548SessionConfigured
                        + " repeating=" + mIris26548RepeatingSubmitted);
                activity.runOnUiThread(() -> {
                    if (generation != mIris26548CameraHealthGeneration
                            || mCameraDevice != cameraDevice) return;
                    mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_NONE;
                    restartCamera();
                });
            }
        }, IRIS_26548_POST_OPEN_HEALTH_TIMEOUT_MS);
    }

    private void iris26555CloseSessionForRecovery() {
        CameraCaptureSession oldSession = mCaptureSession;
        mCaptureSession = null;
        if (oldSession == null) return;
        try { oldSession.stopRepeating(); } catch (Throwable ignored) {}
        try { oldSession.abortCaptures(); } catch (Throwable ignored) {}
        oldSession.close();
    }

    private void iris26555RecoverConfiguredButSilentSession(
            @NonNull CameraDevice cameraDevice, long failedGeneration) {
        if (mBackgroundHandler == null) return;
        mBackgroundHandler.post(() -> {
            if (failedGeneration != mIris26548CameraHealthGeneration
                    || mCameraDevice != cameraDevice) return;
            if (iris26555CaptureOrProcessingOwnsCamera()) {
                Log.w(TAG, "IRIS_26555_CAMERA_RECOVERY_SUPPRESSED captureOrProcessingOwner=true"
                        + " generation=" + failedGeneration + " phase=dispatch");
                return;
            }
            if (surface == null || !surface.isValid()) {
                Log.w(TAG, "IRIS_26555_CAMERA_RECOVERY_SUPPRESSED invalidPreviewSurface=true"
                        + " generation=" + failedGeneration);
                return;
            }
            try {
                iris26555CloseSessionForRecovery();
                mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP;
                iris26548BeginCameraHealthGeneration("configured_but_silent_preview_only_bootstrap");
                Log.i(TAG, "IRIS_26555_PREVIEW_RECOVERY_TOPOLOGY generation="
                        + mIris26548CameraHealthGeneration
                        + " stage=preview_only_bootstrap outputs=preview deviceReopened=false");
                createCameraPreviewSession(false);
                iris26548SchedulePostOpenHealthCheck(cameraDevice);
            } catch (Throwable recoveryFailure) {
                Log.e(TAG, "IRIS_26555_PREVIEW_SILENT_SESSION_RECOVERY_FAILED", recoveryFailure);
            }
        });
    }

    private void iris26555PromoteProvenPreviewToFullTopology(
            @NonNull CameraDevice cameraDevice, long provenGeneration) {
        if (mBackgroundHandler == null) return;
        mBackgroundHandler.post(() -> {
            if (provenGeneration != mIris26548CameraHealthGeneration
                    || mCameraDevice != cameraDevice
                    || mIris26555PreviewRecoveryStage != IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP) return;
            if (iris26555CaptureOrProcessingOwnsCamera()) return;
            try {
                iris26555CloseSessionForRecovery();
                mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY;
                iris26548BeginCameraHealthGeneration("preview_only_proven_full_topology_retry");
                Log.i(TAG, "IRIS_26555_PREVIEW_RECOVERY_TOPOLOGY generation="
                        + mIris26548CameraHealthGeneration
                        + " stage=full_topology_retry previewPreviouslyProven=true");
                createCameraPreviewSession(false);
                iris26548SchedulePostOpenHealthCheck(cameraDevice);
            } catch (Throwable promotionFailure) {
                Log.e(TAG, "IRIS_26555_PREVIEW_RECOVERY_PROMOTION_FAILED", promotionFailure);
            }
        });
    }

    private void iris26555ReturnToPreviewOnlyFallback(
            @NonNull CameraDevice cameraDevice, long failedGeneration) {
        if (mBackgroundHandler == null) return;
        mBackgroundHandler.post(() -> {
            if (failedGeneration != mIris26548CameraHealthGeneration
                    || mCameraDevice != cameraDevice
                    || mIris26555PreviewRecoveryStage != IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY) return;
            if (iris26555CaptureOrProcessingOwnsCamera()) return;
            try {
                iris26555CloseSessionForRecovery();
                mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_PREVIEW_ONLY_FALLBACK;
                iris26548BeginCameraHealthGeneration("full_topology_retry_failed_preview_only_fallback");
                Log.e(TAG, "IRIS_26555_PREVIEW_RECOVERY_TOPOLOGY generation="
                        + mIris26548CameraHealthGeneration
                        + " stage=preview_only_fallback fullTopologySuppressed=true");
                createCameraPreviewSession(false);
                iris26548SchedulePostOpenHealthCheck(cameraDevice);
            } catch (Throwable fallbackFailure) {
                Log.e(TAG, "IRIS_26555_PREVIEW_RECOVERY_FALLBACK_FAILED", fallbackFailure);
            }
        });
    }

    @SuppressLint("MissingPermission")
    public void restartCamera() {
        Log.d(TAG, "restartCamera() called from \"" + Thread.currentThread().getName() + "\" Thread");
        CameraFragment.mSelectedMode = PhotonCamera.getSettings().selectedMode;
        try {
            mCameraOpenCloseLock.acquire();
            if (mIsRecordingVideo) {
                this.VideoEnd();
            }

            if (mCaptureSession != null) {
                mCaptureSession.close();
                mCaptureSession = null;
            }
            if (null != mCameraDevice) {
                mCameraDevice.close();
                mCameraDevice = null;
            }
            if (null != mImageReaderPreview) {
                if (!isProcessing) {
                    mImageReaderPreview.close();
                    mImageReaderPreview = null;
                }
                if (!isProcessing && mImageReaderRaw != null) {
                    mImageReaderRaw.close();
                    mImageReaderRaw = null;
                }
            }
            if (null != mMediaRecorder) {
                mMediaRecorder.release();
                mMediaRecorder = null;
            }
            if (null != mPreviewRequestBuilder) {
                mPreviewRequestBuilder = null;
            }
            if (surface != null) {
                surface.release();
                surface = null;
            }
            stopBackgroundThread();
            cameraEventsListener.onCameraRestarted();
        } catch (Exception e) {
            Log.e(TAG, Log.getStackTraceString(e));
            throw new RuntimeException("Interrupted while trying to lock camera restarting.", e);
        } finally {
            try {
                mCameraOpenCloseLock.release();
            } catch (Exception ignored) {
                showToast("Failed to release camera");
            }
        }
        IrisCameraRoute irisRoute = iris26527ResolveRoute(PhotonCamera.getSettings().mCameraID);
        mIrisOpeningRoute = irisRoute;
        iris26527ApplyRouteToLegacyFields(irisRoute);
        Log.i(TAG, "IRIS_26527_CAMERA_ROUTE_OPEN " + irisRoute);
        mIris26555PreviewRecoveryStage = IRIS_26555_RECOVERY_NONE;
        iris26548BeginCameraHealthGeneration("restart_camera");

        // IRIS_26527_ROUTE_RESTART_ORDER: prepare the complete route/output state before the
        // asynchronous onOpened callback can create a capture session.
        startBackgroundThread();
        Size optimal = getPreviewOutputSize(
                getSafeDisplay(), mCameraCharacteristics, CameraFragment.mSelectedMode);
        setUpCameraOutputs(optimal.getWidth(), optimal.getHeight());
        configureTransform(optimal.getWidth(), optimal.getHeight());
        irisRoute = mIrisOpeningRoute;
        try {
            if (!mCameraOpenCloseLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                throw new RuntimeException("Time out waiting to lock camera opening.");
            }
            Log.i(TAG, "IRIS_26548_CAMERA_OPEN_REQUESTED generation="
                    + mIris26548CameraHealthGeneration + " camera=" + irisRoute.openedDeviceId
                    + " restart=true");
            this.mCameraManager.openCamera(irisRoute.openedDeviceId, mStateCallback, mBackgroundHandler);
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        } catch (InterruptedException e) {
            throw new RuntimeException("Interrupted while trying to restart camera.", e);
        }
    }
    private Size getAspect(CameraMode targetMode){
        Size aspectRatio;
        if (targetMode == CameraMode.VIDEO || targetMode == CameraMode.RAWVIDEO || PhotonCamera.getSettings().aspect169) {
            aspectRatio = new Size(9, 16);
        } else {
            aspectRatio = new Size(3, 4);
        }
        return aspectRatio;
    }

    private Display getSafeDisplay() {
        if (mTextureView != null) {
            Display d = mTextureView.getDisplay();
            if (d != null) return d;
        }
        //noinspection deprecation
        return activity.getWindowManager().getDefaultDisplay();
    }

    //Size for preview drawing
    private Size getTextureOutputSize(
            Display display,
            CameraMode targetMode
    ) {
        Size aspectRatio = getAspect(targetMode);
        Point displayPoint = new Point();
        display.getRealSize(displayPoint);
        int shortSide = Math.min(displayPoint.x, displayPoint.y);
        int longSide = shortSide * aspectRatio.getHeight() / aspectRatio.getWidth();

        return new Size(longSide, shortSide);
    }

    //Size for preview buffer
    private Size getPreviewOutputSize(
            Display display,
            CameraCharacteristics characteristics,
            CameraMode targetMode
    ) {
        Size aspectRatio = getAspect(targetMode);
        Point displayPoint = new Point();
        display.getRealSize(displayPoint);
        int shortSide = Math.min(displayPoint.x, displayPoint.y);
        int longSide = shortSide / aspectRatio.getWidth() * aspectRatio.getHeight();


        // If image format is provided, use it to determine supported sizes; else use target class
        StreamConfigurationMap config = characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);

        Size[] allSizes = config.getOutputSizes(SurfaceTexture.class);

        Size retsize = null;
        for (Size size : allSizes) {
            int sizeShort = Math.min(size.getHeight(), size.getWidth());
            int sizeLong = Math.max(size.getHeight(), size.getWidth());
            if (sizeLong % aspectRatio.getHeight() == 0 &&
                    sizeShort == aspectRatio.getWidth() * sizeLong / aspectRatio.getHeight() &&
                    sizeShort * sizeLong <= ResolutionSolution.previewRes) {
                retsize = new Size(sizeShort, sizeLong);
                break;
            }
            /*if (sizeShort <= shortSide && sizeLong <= longSide) {
                retsize = new Size(sizeShort, sizeLong);
                break;
            }*/
        }
        if (retsize == null) {
            retsize = new Size(800, 600);
        }
        return retsize;
    }

    /**
     * Lock the focus as the first step for a still image capture.
     */
    private void lockFocus() {
        if(burst) return;
        if (mPreviewRequestBuilder == null || mCaptureSession == null) {
            Log.w(TAG, "lockFocus(): camera not ready (builder=" + mPreviewRequestBuilder + " session=" + mCaptureSession + ")");
            return;
        }
        startTimerLocked();
        // This is how to tell the camera to lock focus.
        mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                CameraMetadata.CONTROL_AF_TRIGGER_START);
        // Tell #mCaptureCallback to wait for the lock.
        mState = STATE_WAITING_LOCK;
        try {
            mCaptureSession.setRepeatingRequest(mPreviewRequestBuilder.build(), mCaptureCallback,
                    mBackgroundHandler);
        } catch (CameraAccessException e) {
            Log.e(TAG, "Failed to start camera preview because it couldn't access camera", e);
        } catch (IllegalStateException e) {
            Log.e(TAG, "Failed to start camera preview.", e);
        }
    }

    /**
     * Run the precapture sequence for capturing a still image. This method should be called when
     * we get a response in {@link #mCaptureCallback} from {@link #lockFocus()}.
     */
    private void runPreCaptureSequence() {
        if(burst) return;
        try {
            // This is how to tell the camera to trigger.
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER,
                    CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER_START);
            // Tell #mCaptureCallback to wait for the precapture sequence to be set.
            mState = STATE_WAITING_PRECAPTURE;
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback,
                    mBackgroundHandler);
        } catch (CameraAccessException | IllegalStateException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    private String physicalID = "";
    private String logicalID = "";

    /**
     * Opens the camera specified by {@link Settings#mCameraID}.
     */
    public void openCamera(int width, int height) {
        //Open camera in non ui thread
        processExecutor.execute(()->{
            CameraFragment.mSelectedMode = PhotonCamera.getSettings().selectedMode;
            if (ContextCompat.checkSelfPermission(activity, Manifest.permission.CAMERA)
                    != PackageManager.PERMISSION_GRANTED) {
                //requestCameraPermission();
                return;
            }
            processExecutor.execute(()-> {
                mMediaRecorder = new MediaRecorder();
            });
            cameraEventsListener.onOpenCamera(this.mCameraManager);
            setUpCameraOutputs(width, height);
            configureTransform(width, height);
            try {
                if (!mCameraOpenCloseLock.tryAcquire(1000, TimeUnit.MILLISECONDS)) {
                    throw new RuntimeException("Time out waiting to lock camera opening.");
                }
                IrisCameraRoute irisRoute =
                        iris26527ResolveRoute(PhotonCamera.getSettings().mCameraID);
                mIrisOpeningRoute = irisRoute;
                iris26527ApplyRouteToLegacyFields(irisRoute);
                Log.i(TAG, "IRIS_26527_CAMERA_ROUTE_OPEN " + irisRoute);
                Log.i(TAG, "IRIS_26548_CAMERA_OPEN_REQUESTED generation="
                        + mIris26548CameraHealthGeneration + " camera=" + irisRoute.openedDeviceId);
                this.mCameraManager.openCamera(
                        irisRoute.openedDeviceId, mStateCallback, mBackgroundHandler);
            } catch (CameraAccessException e) {
                Log.e(TAG, Log.getStackTraceString(e));
            } catch (InterruptedException e) {
                throw new RuntimeException("Interrupted while trying to lock camera opening.", e);
            }
    });
    }
    public void UpdateCameraCharacteristics(String cameraId) {
        PhotonCamera.getSpecificSensor().selectSpecifics(
                Integer.parseInt(cameraId));
        CameraCharacteristics characteristics = this.mCameraCharacteristicsMap.get(cameraId);
        mCameraCharacteristics = characteristics;
        //Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);

        StreamConfigurationMap map = null;
        if (mCameraCharacteristics != null) {
            map = mCameraCharacteristics.get(
                    CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        }
        if (map == null) {
            return;
        }
        ArrayList<Size> allTargets = getAllTargets();
        Size[] iris26555RawSizes = null;
        Size[] iris26555HighRawSizes = null;
        try { iris26555RawSizes = map.getOutputSizes(ImageFormat.RAW_SENSOR); }
        catch (Throwable ignored) {}
        try { iris26555HighRawSizes = map.getHighResolutionOutputSizes(ImageFormat.RAW_SENSOR); }
        catch (Throwable ignored) {}
        mIris26555RawStreamAvailable = (iris26555RawSizes != null && iris26555RawSizes.length > 0)
                || (iris26555HighRawSizes != null && iris26555HighRawSizes.length > 0)
                || (mTargetFormat == RAW_FORMAT && !allTargets.isEmpty());
        Log.i(TAG, "IRIS_26555_RAW_CAPABILITY available=" + mIris26555RawStreamAvailable
                + " standard=" + (iris26555RawSizes == null ? 0 : iris26555RawSizes.length)
                + " highRes=" + (iris26555HighRawSizes == null ? 0 : iris26555HighRawSizes.length)
                + " targetFormat=" + mTargetFormat + " manufacturerGate=false");

        Size preview = getCameraOutputSize(map.getOutputSizes(mPreviewTargetFormat));

        int maxjpg = 3;
        if (mTargetFormat == mPreviewTargetFormat && isDualSession)
            maxjpg = PhotonCamera.getSettings().frameCount + 3;
        if (isZslMode())
            maxjpg = Math.min(iris26556RequestedMotionFrames() + 3,
                    MOTION_26556_MAX_NORMAL_FRAMES + 3);
        Size target = allTargets.isEmpty()
                ? preview
                : getCameraOutputSize(allTargets.toArray(new Size[0]), preview);
        Size aspect = getAspect(PhotonCamera.getSettings().selectedMode);
        if(preview.getWidth() > preview.getHeight())
            preview = new Size(preview.getWidth(),preview.getWidth()*aspect.getWidth()/aspect.getHeight());
        else {
            preview = new Size(preview.getHeight()*aspect.getWidth()/aspect.getHeight(),preview.getHeight());
        }
        if(mImageReaderPreview != null)
            mImageReaderPreview.close();

        mImageReaderPreview = ImageReader.newInstance(preview.getWidth(), preview.getHeight(), mPreviewTargetFormat, maxjpg);
        mImageReaderPreview.setOnImageAvailableListener(mOnYuvImageAvailableListener, mBackgroundHandler);
            mBufferSize = getPreviewOutputSize(getSafeDisplay(),characteristics,PhotonCamera.getSettings().selectedMode);

        if (mImageReaderRaw != null) {
            mImageReaderRaw.close();
            mImageReaderRaw = null;
        }
        final boolean iris26555TargetOutputAvailable = !allTargets.isEmpty();
        if (iris26555TargetOutputAvailable) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && (PhotonCamera.getSettings().QuadBayer
                    || !(Build.BRAND.equalsIgnoreCase("oppo")
                    || Build.BRAND.equalsIgnoreCase("vivo")
                    || Build.BRAND.equalsIgnoreCase("oneplus")
                    || Build.BRAND.equalsIgnoreCase("realme")
                    || Build.BRAND.equalsIgnoreCase("iqoo")
                    || Build.BRAND.equalsIgnoreCase("nothing")
            ))) {
                mImageReaderRaw = ImageReader.newInstance(
                        target.getWidth(), target.getHeight(), mTargetFormat, maxjpg, 0x00100000);
            } else {
                mImageReaderRaw = ImageReader.newInstance(
                        target.getWidth(), target.getHeight(), mTargetFormat, maxjpg);
            }
            mImageReaderRaw.setOnImageAvailableListener(mOnRawImageAvailableListener, mBackgroundHandler);
        } else {
            Log.w(TAG, "IRIS_26555_TARGET_STREAM_UNAVAILABLE previewContinues=true targetFormat="
                    + mTargetFormat + " rawAvailable=" + mIris26555RawStreamAvailable);
        }
        // Find out if we need to swap dimension to get the preview size relative to sensor
        // coordinate.
        int displayRotation = PhotonCamera.getGravity().getRotation();
        mSensorOrientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Range<Integer>[] ranges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
        if (ranges == null) {
            ranges = new Range[1];
            ranges[0] = new Range<>(14, 30);
        }
        int minLower = Integer.MAX_VALUE;
        for (Range<Integer> range : ranges) {
            if (range.getLower() < minLower) {
                minLower = range.getLower();
            }
        }
        if (minLower == Integer.MAX_VALUE) minLower = 14;
        FpsRangeAuto = new Range<>(minLower, 30);

        /*boolean swappedDimensions = false;
        switch (displayRotation) {
            case 0:
            case 180:
                if (mSensorOrientation == 90 || mSensorOrientation == 270) {
                    swappedDimensions = true;
                }
                break;
            case 90:
            case 270:
                if (mSensorOrientation == 0 || mSensorOrientation == 180) {
                    swappedDimensions = true;
                }
                break;
            default:
                Log.e(TAG, "Display rotation is invalid: " + displayRotation);
        }*/

        mCameraAfModes = characteristics.get(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES);

        /*Point displaySize = new Point();
        activity.getWindowManager().getDefaultDisplay().getSize(displaySize);
        int rotatedPreviewWidth = mPreviewWidth;
        int rotatedPreviewHeight = mPreviewHeight;

        mPreviewWidth = Math.max(rotatedPreviewHeight, rotatedPreviewWidth);
        mPreviewHeight = Math.min(rotatedPreviewHeight, rotatedPreviewWidth);*/




        /*mPreviewSize = chooseOptimalSize(map.getOutputSizes(SurfaceTexture.class),
                rotatedPreviewWidth, rotatedPreviewHeight, maxPreviewWidth*2,
                maxPreviewHeight*2, target);*/
        //mPreviewSize = new Size(mPreviewWidth, mPreviewHeight);


        // Danger, W.R.! Attempting to use too large a preview size could  exceed the camera
        //        // bus' bandwidth limitation, resulting in gorgeous previews but the storage of
        //        // garbage capture data.



        // We fit the aspect ratio of TextureView to the size of preview we picked.
        /*
        int orientation = activity.getResources().getConfiguration().orientation;

        if (orientation == Configuration.ORIENTATION_LANDSCAPE) {
            mTextureView.setAspectRatio(
                    mPreviewSize.getWidth(), mPreviewSize.getHeight());
            mTextureView.cameraSize = new Point(mPreviewSize.getWidth(), mPreviewSize.getHeight());
        } else {
            mTextureView.setAspectRatio(
                    mPreviewSize.getHeight(), mPreviewSize.getWidth());
            mTextureView.cameraSize = new Point(mPreviewSize.getHeight(), mPreviewSize.getWidth());
        }*/


        // Check if the flash is supported.
        Boolean available = characteristics.get(CameraCharacteristics.FLASH_INFO_AVAILABLE);
        mFlashSupported = available != null && available;
        Camera2ApiAutoFix.Init();
        if (mMediaRecorder == null) {
            mMediaRecorder = new MediaRecorder();
//            setUpMediaRecorder();
        }
        activity.runOnUiThread(() -> {
            //Preview drawing size changing
            mPreviewSize = getTextureOutputSize(getSafeDisplay(), PhotonCamera.getSettings().selectedMode);
            mTextureView.setAspectRatio(
                    mPreviewSize.getHeight(), mPreviewSize.getWidth());
            updatePreviewMirror();
            cameraEventsListener.onCharacteristicsUpdated(characteristics);
            if (PhotonCamera.getSettings().DebugData)
                showToast("preview:" + new Point(mPreviewWidth, mPreviewHeight));
        });
        //activity.runOnUiThread(() -> cameraEventsListener.onCharacteristicsUpdated(characteristics));
    }
    Surface surface;
    public void createCameraPreviewSession(boolean isBurstSession) {
        try {
            Log.i(TAG, "IRIS_26548_PREVIEW_SESSION_CREATE_BEGIN generation="
                    + mIris26548CameraHealthGeneration + " burstSession=" + isBurstSession);
            SurfaceTexture texture = mTextureView.getSurfaceTexture();
            if (texture == null) {
                Log.w(TAG, "createCameraPreviewSession(): SurfaceTexture not ready, waiting for surface");
                mTextureView.setSurfaceTextureListener(mSurfaceTextureListener);
                return;
            }
            // We configure the size of default buffer to be the size of camera preview we want.
            Log.d(TAG, "createCameraPreviewSession() mTextureView:" + mTextureView);
            Log.d(TAG, "createCameraPreviewSession() Texture:" + texture);
            Log.d(TAG, "bufferSize:" + mBufferSize);
            Log.d(TAG, "previewSize:" + mPreviewSize);
            Log.d(TAG, "ID:" + PhotonCamera.getSettings().mCameraID + " deviceID:" + mCameraDevice.getId() + " logicalID:" + logicalID + " physicalID:" + physicalID);

            //Camera output
            texture.setDefaultBufferSize(mBufferSize.getHeight(), mBufferSize.getWidth());

            // This is the output Surface we need to start preview.
            if(surface == null)
                surface = new Surface(texture);
            // We set up a CaptureRequest.Builder with the output Surface.
            setCaptureRequestBuilder();

            // Here, we create a CameraCaptureSession for camera preview.
            List<Surface> surfaces = configureSurfaces(isBurstSession);
            Log.d(TAG, "createCameraPreviewSession() surfaces:" + Arrays.toString(surfaces.toArray()));
            final IrisCameraRoute irisSessionRoute = mIrisOpeningRoute != null
                    ? mIrisOpeningRoute
                    : iris26527ResolveRoute(PhotonCamera.getSettings().mCameraID);
            ArrayList<OutputConfiguration> outputConfigurations = new ArrayList<>();
            for (Surface surfacei : surfaces) {
                var config = new OutputConfiguration(surfacei);
                if (irisSessionRoute.physicalOutputId != null
                        && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    config.setPhysicalCameraId(irisSessionRoute.physicalOutputId);
                }
                outputConfigurations.add(config);
            }
            Log.i(TAG, "IRIS_26527_SESSION_ROUTE_CONFIG " + irisSessionRoute);

            CameraCaptureSession.StateCallback stateCallback =
                    new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
                    Log.d(TAG, "CameraCaptureSession onConfigured():" + cameraCaptureSession);
                    // The camera is already closed
                    if (null == mCameraDevice) {
                        return;
                    }
                    // When the session is ready, we start displaying the preview.
                    mCaptureSession = cameraCaptureSession;
                    /* IRIS_26534_SESSION_STATE_RECOVERY_OWNER
                     * A freshly configured live preview session is authoritative proof that the
                     * controller is no longer CLOSED. This prevents a failed Night transition from
                     * leaving Motion capture functional while the shutter/UI state remains stale.
                     */
                    mState = STATE_PREVIEW;
                    mIris26548SessionConfigured = true;
                    Log.i(TAG, "IRIS_26534_SESSION_STATE_RECOVERY state=STATE_PREVIEW sessionConfigured=true");
                    Log.i(TAG, "IRIS_26548_PREVIEW_SESSION_ON_CONFIGURED generation="
                            + mIris26548CameraHealthGeneration);
                    Log.i(TAG, "IRIS_26553_PREVIEW_DIAG_SESSION_CONFIGURED generation="
                            + mIris26548CameraHealthGeneration + " device="
                            + (mCameraDevice == null ? "null" : mCameraDevice.getId())
                            + " route=" + irisSessionRoute + " outputs=" + outputConfigurations.size()
                            + " previewSize=" + mPreviewSize + " bufferSize=" + mBufferSize
                            + " previewSurfaceValid=" + (surface != null && surface.isValid()));
                    mIrisSessionRoutes.put(cameraCaptureSession, irisSessionRoute);
                    mIrisActiveRoute = irisSessionRoute;
                    Log.i(TAG, "IRIS_26527_SESSION_ROUTE_ACTIVE " + irisSessionRoute);
                    try {
                        // Auto focus should be continuous for camera preview.
                        //mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
                        // Flash is automatically enabled when necessary.
                        resetPreviewAEMode();
                        Camera2ApiAutoFix.applyPrev(mPreviewRequestBuilder);
                        VendorTagUtils.builderSessionApply(mPreviewRequestBuilder, false, useMaximumResolutionKey, physicalID);
                        //if(isZslMode()){
                            try {
                                mPreviewRequestBuilder.set(CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE, CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE_ON);
                            } catch (Exception e) {
                                Log.d(TAG, "Failed to set LENS_SHADING_MAP_MODE_ON for ZSL mode:" + Log.getStackTraceString(e));
                            }
                        //}
                        // Finally, we start displaying the camera preview.
                        mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                                getSelectedFpsRange());
                        iris26524ApplyZoomToPreviewBuilder();
                        mPreviewInputRequest = mPreviewRequestBuilder.build();
                        if (isBurstSession && isDualSession) {
                            switch (CameraFragment.mSelectedMode) {
                                case NIGHT:
                                case PHOTO:
                                case MOTION:
                                    mCaptureSession.captureBurst(captures, CaptureCallback, mBackgroundHandler);
                                    break;
                                case UNLIMITED:
                                case RAWVIDEO:
                                    mCaptureSession.setRepeatingBurst(captures, CaptureCallback, mBackgroundHandler);
                                    break;
                            }
                        } else {
                            //if(mSelectedMode != CameraMode.VIDEO)
                            mCaptureSession.setRepeatingRequest(mPreviewInputRequest,
                                    mCaptureCallback, mBackgroundHandler);
                            mIris26548RepeatingSubmitted = true;
                            Log.i(TAG, "IRIS_26548_REPEATING_REQUEST_SUBMITTED generation="
                                    + mIris26548CameraHealthGeneration);
                            Log.i(TAG, "IRIS_26553_PREVIEW_DIAG_REPEATING generation="
                                    + mIris26548CameraHealthGeneration + " requestTag="
                                    + mPreviewInputRequest.getTag() + " afMode="
                                    + mPreviewInputRequest.get(CaptureRequest.CONTROL_AF_MODE) + " aeMode="
                                    + mPreviewInputRequest.get(CaptureRequest.CONTROL_AE_MODE) + " fps="
                                    + mPreviewInputRequest.get(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE));
                            unlockFocus();
                        }
                    } catch (Exception e) {
                        Log.e(TAG, Log.getStackTraceString(e));
                    }
                    if (mIsRecordingVideo)
                        activity.runOnUiThread(() -> {
                            // Start recording
                            mMediaRecorder.start();
                        });
                }

                @Override
                public void onConfigureFailed(
                        @NonNull CameraCaptureSession cameraCaptureSession) {
                    mIrisSessionRoutes.remove(cameraCaptureSession);
                    if (mIrisActiveRoute == irisSessionRoute) mIrisActiveRoute = null;
                    showToast(activity.getString(R.string.session_on_configure_failed));
                    Log.d(TAG, "CameraCaptureSession onConfigureFailed()");
                }

                @Override
                public void onClosed(@NonNull CameraCaptureSession cameraCaptureSession) {
                    mIrisSessionRoutes.remove(cameraCaptureSession);
                    if (mCaptureSession == cameraCaptureSession) mCaptureSession = null;
                    if (mIrisActiveRoute == irisSessionRoute) mIrisActiveRoute = null;
                    super.onClosed(cameraCaptureSession);
                }
            };
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                SessionConfiguration configuration = new SessionConfiguration(
                        SessionConfiguration.SESSION_REGULAR,
                        outputConfigurations,
                        processExecutor,
                        stateCallback
                );
                mCameraDevice.createCaptureSession(configuration);
            } else {
                mCameraDevice.createCaptureSession(surfaces, stateCallback, mBackgroundHandler);
            }
        } catch (Exception e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    private Surface iris26555StillCaptureSurfaceOrNull() {
        if (isDualSession && mTargetFormat == mPreviewTargetFormat) {
            return mImageReaderPreview == null ? null : mImageReaderPreview.getSurface();
        }
        return mImageReaderRaw == null ? null : mImageReaderRaw.getSurface();
    }

    @NotNull
    private List<Surface> configureSurfaces(boolean isBurstSession) {
        List<Surface> surfaces;
        if (iris26555PreviewOnlyRecoveryActive() && !mIsRecordingVideo) {
            // The observed failure class already configured and accepted repeating with the normal
            // preview+RAW topology but delivered zero results/preview/RAW. The recovery must be
            // materially different: bootstrap Camera2 with the TextureView Surface only.
            surfaces = Collections.singletonList(surface);
        } else if (isDualSession) {
            surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface());
            if (isBurstSession && mImageReaderRaw != null) {
                surfaces = Arrays.asList(mImageReaderPreview.getSurface(), mImageReaderRaw.getSurface());
            }
            if (mTargetFormat == mPreviewTargetFormat) {
                surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface());
            }
        } else if (mImageReaderRaw == null) {
            // Capability-safe preview-only topology. No fake RAW/YUV substitution.
            surfaces = PhotonCamera.getSettings().previewFormat == 0
                    ? Collections.singletonList(surface)
                    : Arrays.asList(surface, mImageReaderPreview.getSurface());
        } else {
            if (Build.BRAND.equalsIgnoreCase("samsung")) {
                surfaces = Arrays.asList(surface, mImageReaderRaw.getSurface());
            } else {
                surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface(), mImageReaderRaw.getSurface());
            }
            if (PhotonCamera.getSettings().previewFormat == 0) {
                surfaces = Arrays.asList(surface, mImageReaderRaw.getSurface());
            }
        }
        Log.i(TAG, "IRIS_26555_SESSION_TOPOLOGY generation=" + mIris26548CameraHealthGeneration
                + " recoveryStage=" + mIris26555PreviewRecoveryStage
                + " rawAvailable=" + mIris26555RawStreamAvailable
                + " outputs=" + surfaces.size());
        if (mIsRecordingVideo) {
            setUpMediaRecorder();
            surfaces = Arrays.asList(surface, mMediaRecorder.getSurface());
            mPreviewRequestBuilder.addTarget(mMediaRecorder.getSurface());
        }
        return surfaces;
    }

    private void setCaptureRequestBuilder() throws CameraAccessException {
        mPreviewRequestBuilder = null;
        if (mIsRecordingVideo) {
            mPreviewRequestBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
        } else {
            mPreviewRequestBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
        }

        mPreviewRequestBuilder.addTarget(surface);
        synchronized (mZslBufferLock) {
            while (!mZslRingBuffer.isEmpty()) {
                Image img = mZslRingBuffer.pollFirst();
                if (img != null) img.close();
            }
        }
        // Drain any frames still queued in the RAW ImageReader to prevent them leaking
        // into the next non-ZSL capture's IMAGE_BUFFER
        if (mImageReaderRaw != null) {
            Image stale;
            try {
                while ((stale = mImageReaderRaw.acquireNextImage()) != null) stale.close();
            } catch (Exception ignored) {}
        }
        if (isZslMode() && mImageReaderRaw != null && mIris26555RawStreamAvailable
                && !iris26555PreviewOnlyRecoveryActive()) {
            mPreviewRequestBuilder.addTarget(mImageReaderRaw.getSurface());
        } else if (isZslMode() && iris26555PreviewOnlyRecoveryActive()) {
            Log.i(TAG, "IRIS_26555_ZSL_RAW_TARGET_SKIPPED recoveryStage="
                    + mIris26555PreviewRecoveryStage + " previewOnly=true");
        } else if (isZslMode() && !mIris26555RawStreamAvailable) {
            Log.w(TAG, "IRIS_26555_ZSL_RAW_TARGET_SKIPPED rawAvailable=false previewContinues=true");
        }
        mPreviewMeteringAF = mPreviewRequestBuilder.get(CONTROL_AF_REGIONS);
        mPreviewAFMode = PreferenceKeys.getAfMode();
        if (mIsRecordingVideo) {
            mPreviewRequestBuilder.set(CONTROL_AF_MODE, CONTROL_AF_MODE_CONTINUOUS_VIDEO);
            mPreviewAFMode = CONTROL_AF_MODE_CONTINUOUS_VIDEO;
            if (PreferenceKeys.isEisPhotoOn()) {
                mPreviewRequestBuilder.set(CONTROL_VIDEO_STABILIZATION_MODE, CONTROL_VIDEO_STABILIZATION_MODE_ON);
            }
        }
        mPreviewMeteringAE = mPreviewRequestBuilder.get(CONTROL_AE_REGIONS);
        mPreviewAEMode = mPreviewRequestBuilder.get(CONTROL_AE_MODE);
    }

    private void showToast(String msg) {
        if (activity != null) {
            new Handler(Looper.getMainLooper()).post(() -> Toast.makeText(activity, msg, Toast.LENGTH_SHORT).show());
        }
    }

    /**
     * Initiate a still image capture.
     */
    public void takePicture() {
        final CameraMode iris26555Mode = PhotonCamera.getSettings().selectedMode;
        if (!mIris26555RawStreamAvailable
                && (iris26555Mode == CameraMode.MOTION || iris26555Mode == CameraMode.NIGHT)) {
            Log.w(TAG, "IRIS_26555_RAW_MODE_UNAVAILABLE mode=" + iris26555Mode
                    + " previewAlive=true fakeYuvFallback=false");
            showToast("RAW capture is not supported by this camera");
            return;
        }
        if (iris26555Mode == CameraMode.MOTION && mIris26555RawStreamAvailable
                && (iris26555PreviewOnlyRecoveryActive() || !iris26555MotionZslReady())) {
            Log.w(TAG, "IRIS_26555_MOTION_CAPTURE_NOT_READY recoveryStage="
                    + mIris26555PreviewRecoveryStage + " firstZslRaw=" + mIris26548FirstZslRaw
                    + " zslBuffered=" + iris26548MotionZslHasFrames());
            showToast("Motion RAW buffer is still preparing");
            return;
        }
        /* IRIS_26547_NIGHT_REENTRY_GUARD
         * UI state is not a sufficient serialization primitive. Reject a second Night shutter at
         * the controller boundary while the prior Night capture/reconstruction still owns RAW/GL.
         */
        if (PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT && isProcessing) {
            Log.w(TAG, "IRIS_26547_NIGHT_REENTRY_REJECTED processing=true");
            return;
        }
        if (mPreviewRequestBuilder == null || mCaptureSession == null) {
            Log.w(TAG, "takePicture(): camera not ready, ignoring shutter press");
            return;
        }
        if (isZslMode()) {
            captureStillPicture();
            return;
        }
        if (mCameraAfModes.length > 1) lockFocus();
        else {
            try {
                mState = STATE_WAITING_NON_PRECAPTURE;
                mCaptureSession.setRepeatingRequest(mPreviewRequestBuilder.build(), mCaptureCallback,
                        mBackgroundHandler);
            } catch (CameraAccessException e) {
                Log.e(TAG, "Failed to start camera preview because it couldn't access camera", e);
            } catch (IllegalStateException e) {
                Log.e(TAG, "Failed to start camera preview.", e);
            }
        }
    }

    /**
     * Unlock the focus. This method should be called when still image capture sequence is
     * finished.
     */
    public void unlockFocus() {
        try {
            /* IRIS_26523_PRESERVE_USER_AF_LOCK_ACROSS_CAPTURE */
            if (mTouchFocus != null && mTouchFocus.isFocusLocked()) {
                mState = STATE_PREVIEW;
                mTouchFocus.resumeLockedFocusAfterCapture();
                Log.d(TAG, "26523 unlockFocus preserved user long-press AF lock");
                return;
            }
            /* IRIS_26484_UNLOCK_FOCUS_NULL_BUILDER_GUARD */
            if (mPreviewRequestBuilder == null || mCaptureSession == null) {
                Log.w(TAG, "26484 unlockFocus skipped: builder/session unavailable");
                mState = STATE_PREVIEW;
                return;
            }
            // Reset the auto-focus trigger
            //mCaptureSession.stopRepeating();
            //mCaptureSession.abortCaptures();
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                    CameraMetadata.CONTROL_AF_TRIGGER_CANCEL);
            rebuildPreviewBuilderOneShot();
            //mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
            //        CameraMetadata.CONTROL_AF_TRIGGER_START);
            //rebuildPreviewBuilderOneShot();
            reset3Aparams();
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                    CameraMetadata.CONTROL_AF_TRIGGER_START);
            rebuildPreviewBuilderOneShot();
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                    CameraMetadata.CONTROL_AF_TRIGGER_CANCEL);
            rebuildPreviewBuilderOneShot();
            paramController.setupPreview();
            /*mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                    CameraMetadata.CONTROL_AF_TRIGGER_CANCEL);
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback,
                    mBackgroundHandler);
            mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,
                    CameraMetadata.CONTROL_AF_TRIGGER_START);
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback,
                    mBackgroundHandler);*/
            // After this, the camera will go back to the normal state of preview.
            mState = STATE_PREVIEW;
            rebuildPreviewBuilder();
            //mCaptureSession.setRepeatingRequest(mPreviewRequest, mCaptureCallback,
            //        mBackgroundHandler);
        }catch(Exception e){
            Log.d(TAG, "unlockFocus:"+e);
        }
    }
    public CaptureRequest.Builder getDebugCaptureRequestBuilder(){
        final CaptureRequest.Builder captureBuilder;
        try {
            captureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            if (mTargetFormat != mPreviewTargetFormat)
                captureBuilder.addTarget(mImageReaderRaw.getSurface());
            else
                captureBuilder.addTarget(mImageReaderPreview.getSurface());
            return captureBuilder;
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
        return null;
    }
    private void debugCapture(CaptureRequest.Builder builder){
        try {
            if (null == mCameraDevice) {
                return;
            }
            Camera2ApiAutoFix.applyEnergySaving();
            captures = new ArrayList<>();

            int frameCount = 1;
            cameraEventsListener.onFrameCountSet(frameCount);

            captures.add(builder.build());


            Log.d(TAG, "FrameCount:" + frameCount);

            Log.d(TAG, "CaptureStarted!");

            final long[] baseFrameNumber = {0};
            final int[] maxFrameCount = {frameCount};

            cameraEventsListener.onCaptureStillPictureStarted("CaptureStarted!");
            mMeasuredFrameCnt = 0;
            mImageSaver.implementation = new DebugSender(cameraEventsListener);

            cameraEventsListener.onBurstPrepared(null);
            this.CaptureCallback = new CameraCaptureSession.CaptureCallback() {

                @Override
                public void onCaptureStarted(@NonNull CameraCaptureSession session,
                                             @NonNull CaptureRequest request,
                                             long timestamp,
                                             long frameNumber) {

                    if (baseFrameNumber[0] == 0) {
                        baseFrameNumber[0] = frameNumber - 1L;
                        Log.v("BurstCounter", "CaptureStarted with FirstFrameNumber:" + frameNumber);
                    } else {
                        Log.v("BurstCounter", "CaptureStarted:" + frameNumber);
                    }
                    cameraEventsListener.onFrameCaptureStarted(null);
                }

                @Override
                public void onCaptureProgressed(@NonNull CameraCaptureSession session, @NonNull CaptureRequest request,
                                                @NonNull CaptureResult partialResult) {
                    //mCaptureResult = partialResult;
                }

                @Override
                public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                               @NonNull CaptureRequest request,
                                               @NonNull TotalCaptureResult result) {

                    int frameCount = (int) (result.getFrameNumber() - baseFrameNumber[0]);
                    Log.v("BurstCounter", "CaptureCompleted! FrameCount:" + frameCount);
                    long frametime = 100;
                    Object time = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    if(time != null) frametime = (long)time;
                    cameraEventsListener.onFrameCaptureCompleted(
                            new TimerFrameCountViewModel.FrameCntTime(frameCount, maxFrameCount[0], frametime));
                    mCaptureResult = result;
                }

                @Override
                public void onCaptureSequenceCompleted(@NonNull CameraCaptureSession session,
                                                       int sequenceId,
                                                       long lastFrameNumber) {

                    int finalFrameCount = (int) (lastFrameNumber - baseFrameNumber[0]);
                    Log.v("BurstCounter", "CaptureSequenceCompleted! FrameCount:" + finalFrameCount);
                    Log.v("BurstCounter", "CaptureSequenceCompleted! LastFrameNumber:" + lastFrameNumber);
                    Log.d(TAG, "SequenceCompleted");
                    mBackgroundHandler.postDelayed(() -> {
                        while(mImageSaver.implementation.IMAGE_BUFFER.size() > PhotonCamera.getSettings().frameCount/2) {
                            try {
                                Thread.sleep(1);
                            } catch (InterruptedException ignored) {}
                        }
                        cameraEventsListener.onCaptureSequenceCompleted(null);
                    }, 100);
                    mMeasuredFrameCnt = finalFrameCount;
                    burst = false;
                    //Surface texture related
                    activity.runOnUiThread(() -> UpdateCameraCharacteristics(physicalID));
                    if (!isDualSession)
                        unlockFocus();
                    else
                        createCameraPreviewSession(false);
                    taskResults.removeIf(Future::isDone); //remove already completed results
                    Future<?> result = processExecutor.submit(() -> mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, mCaptureRequest, new ArrayList<>(BurstShakiness), cameraRotation, mExposures));
                    taskResults.add(result);
                }
            };
            burst = true;
            Camera2ApiAutoFix.ApplyBurst();
            if (isDualSession)
                createCameraPreviewSession(true);
            else {
                mCaptureSession.captureBurst(captures, CaptureCallback, mBackgroundHandler);
            }

        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    public void runDebug(CaptureRequest.Builder builder){
        activity.runOnUiThread(() -> debugCapture(builder));
    }

    private boolean isZslMode() {
        return PhotonCamera.getSettings().selectedMode == CameraMode.MOTION
                && !isDualSession;
    }

    /* IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP
     * RAW Image SENSOR_TIMESTAMP is frame identity. Never borrow Camera2
     * metadata from an adjacent ~33 ms frame: that makes exposure/noise/role
     * metadata belong to the wrong physical observation.
     */
    private TotalCaptureResult findNearestZslResult(long timestamp) {
        synchronized (mZslBufferLock) {
            TotalCaptureResult exact = mZslResultMap.get(timestamp);
            if (exact == null) {
                Log.w(TAG, "IRIS_26481_EXACT_TIMESTAMP_MISS"
                        + " rawTimestamp=" + timestamp
                        + " neighborFallback=false");
            }
            return exact;
        }
    }

    /*
     * IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST
     * Shutter-time only; the continuous preview RAW-AE loop stays dormant.
     */

    private ImageFrame copyMotion26505LongFrame(
            Image img, TotalCaptureResult result) {
        if (img == null) return null;
        int rowStride = img.getPlanes()[0].getRowStride();
        int pixelStride = img.getPlanes()[0].getPixelStride();
        int width = (img.getFormat() == ImageFormat.RAW10)
                ? img.getWidth()
                : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
        int height = img.getHeight();
        int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
        int offset = 0;
        if (PhotonCamera.getSettings().aspect169 && width > height) {
            height = width * 9 / 16;
            int offsetH = (img.getHeight() - height) / 2;
            offsetH -= offsetH % 2;
            offset = rowStride * offsetH;
            bufCapacity = rowStride * height;
        }
        Allocator.binning = PhotonCamera.getSettings().binning;
        ImageFrame frame = new ImageFrame(
                img.getPlanes()[0].getBuffer(), img.getFormat(),
                width, rowStride, offset, bufCapacity);
        frame.timestamp = img.getTimestamp();
        frame.width = PhotonCamera.getSettings().binning ? width / 2 : width;
        frame.height = PhotonCamera.getSettings().binning ? height / 2 : height;
        frame.setMotionV2PlaneLayout(
                img.getFormat(), img.getWidth(), height, rowStride, pixelStride,
                PhotonCamera.getSettings().binning);
        populateMotion26480FrameMetadata(frame, result, false);
        frame.motionV2ShortHighlightFrame = false;
        frame.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        return frame;
    }

    private boolean tryDeliverMotion26505StagedLongRaw(
            Motion26505LongTicket ticket, TotalCaptureResult exactResult) {
        if (ticket == null || ticket.slot == null || ticket.slot.isSealed()
                || ticket.slot.hasFrame() || ticket.resultTimestampNs <= 0L) {
            if (ticket != null && ticket.slot != null && ticket.slot.isSealed()) {
                ticket.closeStaged();
            }
            return false;
        }
        ImageFrame staged = ticket.takeStaged(ticket.resultTimestampNs);
        if (staged == null) {
            Log.d(TAG, "IRIS_26505_LONG_STAGED_EXACT_MISS"
                    + " resultTimestamp=" + ticket.resultTimestampNs
                    + " staged=" + ticket.stagedCount()
                    + " nearestFallback=false");
            return false;
        }
        populateMotion26480FrameMetadata(staged, exactResult, false);
        staged.motionV2ShortHighlightFrame = false;
        staged.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        staged.motionV2ActualExposureNs = ticket.actualExposureNs;
        staged.motionV2ActualIso = ticket.actualIso;
        staged.motionV2ExposureEnergy = ticket.actualEnergy;
        boolean accepted = ticket.slot.offer(staged);
        ticket.closeStaged();
        if (accepted) {
            clearMotion26505LongTicket(ticket, "staged_exact_delivery");
        }
        Log.i(TAG, "IRIS_26505_LONG_STAGED_DELIVERY"
                + " accepted=" + accepted
                + " timestamp=" + ticket.resultTimestampNs
                + " exactTimestampEquality=true exactMetadata=true"
                + " normalAccumulatorAdmission=false");
        return accepted;
    }

    private boolean stageMotion26505LongRawCandidate(
            Motion26505LongTicket ticket, Image img) {
        if (ticket == null || img == null || !ticket.requested
                || ticket.slot == null || ticket.slot.isSealed()
                || ticket.slot.hasFrame()) return false;
        long ts = img.getTimestamp();
        long identityTimestamp = ticket.expectedTimestampNs();
        /* IRIS_26505_LONG_STAGE_REQUIRES_CAPTURE_STARTED_IDENTITY
         * Do not even copy an unrelated normal/Short RAW while the Long request is
         * waiting for onCaptureStarted. A Long candidate exists only after Camera2
         * has published its exact sensor timestamp and this Image equals it.
         */
        if (identityTimestamp <= 0L || ts != identityTimestamp) return false;
        if (ticket.completed && ticket.resultTimestampNs <= 0L) return false;

        TotalCaptureResult exact;
        synchronized (mZslBufferLock) { exact = mZslResultMap.get(ts); }
        ImageFrame copy;
        try {
            copy = copyMotion26505LongFrame(img, exact);
        } catch (Throwable t) {
            Log.w(TAG, "IRIS_26505_LONG_STAGE_COPY_SKIPPED timestamp=" + ts
                    + " reason=" + t.getClass().getSimpleName());
            return false;
        }
        if (copy == null) return false;

        if (ticket.resultTimestampNs > 0L
                && copy.timestamp == ticket.resultTimestampNs
                && exact != null) {
            populateMotion26480FrameMetadata(copy, exact, false);
            copy.motionV2ShortHighlightFrame = false;
            copy.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
            copy.motionV2ActualExposureNs = ticket.actualExposureNs;
            copy.motionV2ActualIso = ticket.actualIso;
            copy.motionV2ExposureEnergy = ticket.actualEnergy;
            boolean accepted = ticket.slot.offer(copy);
            ticket.closeStaged();
            if (accepted) clearMotion26505LongTicket(ticket, "raw_callback_direct_delivery");
            Log.i(TAG, "IRIS_26505_LONG_RAW_CALLBACK_DIRECT_DELIVERY"
                    + " accepted=" + accepted
                    + " timestamp=" + ts
                    + " exactTimestampEquality=true exactResultAlreadyKnown=true"
                    + " normalAccumulatorAdmission=false");
            return true;
        }

        ticket.stage(copy);
        Log.d(TAG, "IRIS_26505_LONG_RAW_STAGED timestamp=" + ts
                + " staged=" + ticket.stagedCount()
                + " expectedTimestamp=" + ticket.expectedTimestampNs()
                + " awaitingExactResultTimestamp=" + (ticket.resultTimestampNs <= 0L)
                + " imageReaderObjectRetained=false");
        return true;
    }

    /* IRIS_26505_PHYSICAL_LONG_BRACKET
     * Bjzhou-consistency principle, adapted without replacing Wronski: request one
     * separate longer RAW around +2.5 EV in exposure energy. Prefer shutter up to
     * ~10 ms (or the already-longer base shutter), then ISO. Actual CaptureResult
     * metadata, not requested metadata, decides admission. The request never gates
     * the shutter and the frame can only enter ShadowAuxSlot.
     */
    private boolean applyMotion26505ExplicitLongCaptureIfUseful(
            @NonNull Motion26505LongTicket ticket) {
        if (ticket == null || ticket.slot == null || !isZslMode()
                || mCaptureSession == null || mCameraDevice == null
                || mImageReaderRaw == null || mCameraCharacteristics == null
                || mPreviewCaptureResult == null || mMotion26380RawSampleCount < 64) {
            return false;
        }
        Long baseExpObj = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIsoObj = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        Long previewTs = mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        if (baseExpObj == null || baseExpObj <= 0L || baseIsoObj == null || baseIsoObj <= 0
                || previewTs == null) return false;
        long rawAgeNs = mMotion26380RawSignalTimestampNs <= 0L
                ? Long.MAX_VALUE : Math.abs(previewTs - mMotion26380RawSignalTimestampNs);
        if (rawAgeNs > 180_000_000L) return false;

        boolean manual = false;
        int[] caps = mCameraCharacteristics.get(
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        if (caps != null) for (int c : caps) {
            if (c == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR) {
                manual = true; break;
            }
        }
        if (!manual) return false;

        final long baseExp = baseExpObj;
        final int baseIso = baseIsoObj;
        ticket.baselineEnergy = ExposureIndex.time2sec(baseExp) * baseIso;
        if (!(ticket.baselineEnergy > 0.0)) return false;

        android.util.Range<Long> er = mCameraCharacteristics.get(
                CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        android.util.Range<Integer> sr = mCameraCharacteristics.get(
                CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        if (er == null || sr == null) return false;

        double targetEnergy = ticket.baselineEnergy * MOTION_26505_LONG_TARGET_MULTIPLIER;
        long maxLongExp = Math.min(er.getUpper(),
                Math.max(MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS, baseExp));
        maxLongExp = Math.max(er.getLower(), maxLongExp);
        long reqExp = Math.round(baseExp * MOTION_26505_LONG_TARGET_MULTIPLIER);
        reqExp = Math.max(er.getLower(), Math.min(maxLongExp, reqExp));

        int isoUpper = Math.min(sr.getUpper(),
                Math.max(baseIso, MOTION_26505_LONG_FALLBACK_MAX_ISO));
        int reqIso = (int)Math.round(targetEnergy
                / Math.max(ExposureIndex.time2sec(reqExp), 1.0e-12));
        reqIso = Math.max(sr.getLower(), Math.min(isoUpper, reqIso));
        long recomputedExp = Math.round(
                targetEnergy / Math.max(reqIso, 1) * 1_000_000_000.0);
        reqExp = Math.max(er.getLower(), Math.min(maxLongExp, recomputedExp));

        final double requestedEnergy = ExposureIndex.time2sec(reqExp) * reqIso;
        final double requestedRatio = requestedEnergy / ticket.baselineEnergy;
        if (!(requestedEnergy > ticket.baselineEnergy * MOTION_26505_LONG_MIN_ACTUAL_RATIO)) {
            Log.w(TAG, "IRIS_26505_LONG_REQUEST_NO_PHYSICAL_GAIN"
                    + " baselineEnergy=" + ticket.baselineEnergy
                    + " targetEnergy=" + targetEnergy
                    + " requestedEnergy=" + requestedEnergy
                    + " requestedRatio=" + requestedRatio
                    + " requestedExposureNs=" + reqExp
                    + " requestedIso=" + reqIso);
            return false;
        }

        final double tol = Math.pow(2.0, MOTION_26505_LONG_REQUEST_TOLERANCE_EV);
        final double requestedRatioMin = requestedRatio / tol;
        final double requestedRatioMax = requestedRatio * tol;
        final long requestedExp = reqExp;
        final int requestedIso = reqIso;

        try {
            CaptureRequest.Builder b = mCameraDevice.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26505_LONG_TAG);
            if (mPreviewAFMode >= 0) b.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
            if (Float.isFinite(mFocus) && mFocus >= 0.0f) {
                try { b.set(CaptureRequest.LENS_FOCUS_DISTANCE, mFocus); }
                catch (IllegalArgumentException ignored) {}
            }
            b.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME, requestedExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY, requestedIso);
            try { VendorTagUtils.builderSessionApply(
                    b, true, useMaximumResolutionKey, physicalID); }
            catch (Throwable e) {
                Log.w(TAG, "IRIS_26505 long vendor tags skipped "
                        + e.getClass().getSimpleName());
            }

            ticket.requested = true;
            mMotion26505LongRequested = true;
            mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureStarted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, long timestamp, long frameNumber) {
                    ticket.captureStartedTimestampNs = timestamp;
                    ticket.captureStartedFrameNumber = frameNumber;
                    Log.i(TAG, "IRIS_26505_LONG_CAPTURE_STARTED_IDENTITY"
                            + " sensorTimestamp=" + timestamp
                            + " frameNumber=" + frameNumber
                            + " exactImageTimestampContract=true");
                }
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    Long ts = result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Long exp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
                    if (ts != null) {
                        synchronized (mZslBufferLock) {
                            mZslResultMap.put(ts, result);
                            while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
                                Long oldest = Collections.min(mZslResultMap.keySet());
                                mZslResultMap.remove(oldest);
                            }
                        }
                    }
                    ticket.completed = true;
                    if (ts == null || exp == null || exp <= 0L || iso == null || iso <= 0) {
                        ticket.closeStaged();
                        clearMotion26505LongTicket(ticket, "missing_actual_metadata");
                        return;
                    }
                    double energy = ExposureIndex.time2sec(exp) * iso;
                    double ratio = energy / ticket.baselineEnergy;
                    boolean accepted = energy > ticket.baselineEnergy * MOTION_26505_LONG_MIN_ACTUAL_RATIO
                            && ratio >= requestedRatioMin && ratio <= requestedRatioMax;
                    if (accepted) {
                        ticket.resultTimestampNs = ts;
                        ticket.actualExposureNs = exp;
                        ticket.actualIso = iso;
                        ticket.actualEnergy = energy;
                        double actualDeltaEv = Math.log(ratio) / Math.log(2.0);
                        Log.i(TAG, "IRIS_26505_LONG_ACTUAL_ACCEPTED"
                                + " sensorTimestamp=" + ts
                                + " requestedExposureNs=" + requestedExp
                                + " requestedIso=" + requestedIso
                                + " requestedRatio=" + requestedRatio
                                + " actualExposureNs=" + exp
                                + " actualIso=" + iso
                                + " actualRatio=" + ratio
                                + " actualDeltaEv=" + actualDeltaEv
                                + " targetDeltaEv=" + MOTION_26505_LONG_TARGET_EV
                                + " allowedAroundClampedRequest="
                                + requestedRatioMin + ".." + requestedRatioMax
                                + " normalAccumulatorAdmission=false shutterGate=false");
                        tryDeliverMotion26505StagedLongRaw(ticket, result);
                    } else {
                        ticket.closeStaged();
                        clearMotion26505LongTicket(ticket, "actual_exposure_rejected");
                        Log.w(TAG, "IRIS_26505_LONG_ACTUAL_REJECTED"
                                + " ratio=" + ratio
                                + " requestedRatio=" + requestedRatio
                                + " allowed=" + requestedRatioMin + ".." + requestedRatioMax);
                    }
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,
                        @NonNull android.hardware.camera2.CaptureFailure failure) {
                    ticket.completed = true;
                    ticket.closeStaged();
                    clearMotion26505LongTicket(ticket, "capture_failed");
                    Log.w(TAG, "IRIS_26505_LONG_CAPTURE_FAILED reason=" + failure.getReason());
                }
            }, mBackgroundHandler);
            Log.i(TAG, "IRIS_26505_PHYSICAL_LONG_BRACKET"
                    + " submitted=true rawOnlyTarget=true"
                    + " baseExposureNs=" + baseExp
                    + " baseIso=" + baseIso
                    + " targetEv=" + MOTION_26505_LONG_TARGET_EV
                    + " requestedExposureNs=" + requestedExp
                    + " requestedIso=" + requestedIso
                    + " requestedRatio=" + requestedRatio
                    + " preferredMaxShutterNs=" + MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS
                    + " normalRingCleared=false previewRebuilt=false shutterGate=false");
            if (mBackgroundHandler != null) {
                mBackgroundHandler.postDelayed(() -> {
                    if (ticket.completed || ticket.slot.isSealed() || ticket.slot.hasFrame()) {
                        ticket.closeStaged();
                    }
                }, 1200L);
                mBackgroundHandler.postDelayed(() -> {
                    ticket.closeStaged();
                    clearMotion26505LongTicket(ticket, "terminal_cleanup");
                }, 2500L);
            }
            return true;
        } catch (CameraAccessException | IllegalArgumentException | IllegalStateException e) {
            ticket.completed = true;
            ticket.closeStaged();
            mMotion26505LongRequested = false;
            clearMotion26505LongTicket(ticket, "capture_submit_exception");
            Log.w(TAG, "IRIS_26505_LONG_CAPTURE skipped " + e.getClass().getSimpleName());
            return false;
        }
    }

    /* IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET
     * A short RAW is an optional asynchronous observation. It never gates the
     * normal shutter and its callback state belongs to one Motion generation.
     */
    private boolean applyMotion26486ExplicitShortCaptureIfNeeded(
            @NonNull Motion26486ShortTicket ticket) {
        if (ticket == null || !isZslMode() || mCaptureSession == null
                || mCameraDevice == null || mImageReaderRaw == null
                || mCameraCharacteristics == null || mPreviewCaptureResult == null
                || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) return false;

        Long previewTimestamp = mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        Long baseExp = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIso = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        long rawAgeNs = previewTimestamp == null || mMotion26380RawSignalTimestampNs <= 0L
                ? Long.MAX_VALUE : Math.abs(previewTimestamp - mMotion26380RawSignalTimestampNs);
        long highlightEvidenceAgeNs = previewTimestamp == null
                || mMotion26496RecentHighlightEvidenceTimestampNs <= 0L
                ? Long.MAX_VALUE
                : Math.abs(previewTimestamp - mMotion26496RecentHighlightEvidenceTimestampNs);
        boolean legacyFractionTrigger =
                mMotion26380RawHighlightFraction >= MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER;
        boolean currentSpatialTrigger =
                mMotion26496RawHighlightSampleCount >= MOTION_26496_MIN_HIGHLIGHT_SAMPLES
                        || mMotion26496RawCoherentHighlightCells > 0;
        boolean recentSpatialTrigger =
                highlightEvidenceAgeNs <= MOTION_26496_HIGHLIGHT_EVIDENCE_HOLD_NS;
        boolean highlightTrigger = legacyFractionTrigger
                || currentSpatialTrigger
                || recentSpatialTrigger;
        Log.i(TAG, "IRIS_26496_SHORT_TRIGGER_DECISION"
                + " rawAgeMs=" + (rawAgeNs == Long.MAX_VALUE ? -1L : rawAgeNs / 1_000_000L)
                + " evidenceAgeMs=" + (highlightEvidenceAgeNs == Long.MAX_VALUE
                        ? -1L : highlightEvidenceAgeNs / 1_000_000L)
                + " fraction=" + mMotion26380RawHighlightFraction
                + " highlightSamples=" + mMotion26496RawHighlightSampleCount
                + " coherentCells=" + mMotion26496RawCoherentHighlightCells
                + " peakQuadPhases=" + mMotion26496RawPeakQuadHighlightPhases
                + " ditherIndex=" + mMotion26496RawDitherIndex
                + " legacyFractionTrigger=" + legacyFractionTrigger
                + " currentSpatialTrigger=" + currentSpatialTrigger
                + " recentSpatialTrigger=" + recentSpatialTrigger
                + " requestShort=" + (rawAgeNs <= 180_000_000L && highlightTrigger));
        if (rawAgeNs > 180_000_000L
                || !highlightTrigger
                || baseExp == null || baseExp <= 0L || baseIso == null || baseIso <= 0) return false;

        ticket.baselineEnergy = ExposureIndex.time2sec(baseExp) * baseIso;
        try {
            CaptureRequest.Builder b = mCameraDevice.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26480_SHORT_TAG);
            if (mPreviewAFMode >= 0) b.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
            if (Float.isFinite(mFocus) && mFocus >= 0.0f) {
                try { b.set(CaptureRequest.LENS_FOCUS_DISTANCE, mFocus); }
                catch (IllegalArgumentException ignored) {}
            }

            boolean manual = false;
            int[] caps = mCameraCharacteristics.get(
                    CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if (caps != null) for (int c : caps) {
                if (c == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR) {
                    manual = true; break;
                }
            }
            if (!manual) return false;

            long reqExp = Math.max(1L,
                    Math.round(baseExp / MOTION_26480_SHORT_EXPOSURE_DIVISOR));
            int reqIso = baseIso;
            android.util.Range<Long> er = mCameraCharacteristics.get(
                    CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            android.util.Range<Integer> sr = mCameraCharacteristics.get(
                    CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            if (er != null) reqExp = Math.max(er.getLower(), Math.min(er.getUpper(), reqExp));
            if (sr != null) reqIso = Math.max(sr.getLower(), Math.min(sr.getUpper(), reqIso));

            /* IRIS_26495_CLAMP_AWARE_SHORT_RADIOMETRY
             * Camera2 may clamp the requested 2.5 EV shutter to the physical
             * exposure-time range. The request tag/ticket already owns the role;
             * validate actual metadata around the exposure we could really request,
             * not around an unreachable nominal ratio. Physical short clipping is
             * still tested later per CFA phase before SHORT_VALIDATED is granted.
             */
            final double requestedEnergy = ExposureIndex.time2sec(reqExp) * reqIso;
            if (!(requestedEnergy > 0.0) || !(requestedEnergy < ticket.baselineEnergy)) {
                Log.w(TAG, "IRIS_26495_SHORT_REQUEST_NO_PHYSICAL_HEADROOM"
                        + " baselineEnergy=" + ticket.baselineEnergy
                        + " requestedEnergy=" + requestedEnergy
                        + " requestedExposureNs=" + reqExp
                        + " requestedIso=" + reqIso);
                return false;
            }
            final double requestedRatio = requestedEnergy / ticket.baselineEnergy;
            final double toleranceFactor = Math.pow(2.0, MOTION_26480_SHORT_TOLERANCE_EV);
            final double requestedRatioMin = requestedRatio / toleranceFactor;
            final double requestedRatioMax = Math.min(0.999999, requestedRatio * toleranceFactor);
            final double requestedHeadroomEv = Math.log(ticket.baselineEnergy / requestedEnergy)
                    / Math.log(2.0);

            b.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME, reqExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY, reqIso);
            try { VendorTagUtils.builderSessionApply(b, true, useMaximumResolutionKey, physicalID); }
            catch (Throwable e) { Log.w(TAG, "26486 short vendor tags skipped "
                    + e.getClass().getSimpleName()); }

            ticket.requested = true;
            mMotion26486ShortAcquisitions.incrementAndGet();
            final long requestedExp = reqExp;
            final int requestedIso = reqIso;
            mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureStarted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, long timestamp, long frameNumber) {
                    ticket.captureStartedTimestampNs = timestamp;
                    ticket.captureStartedFrameNumber = frameNumber;
                    Log.i(TAG, "IRIS_26490_SHORT_CAPTURE_STARTED_IDENTITY"
                            + " sensorTimestamp=" + timestamp
                            + " frameNumber=" + frameNumber
                            + " exactImageTimestampContract=true");
                }
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    Long ts = result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Long exp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
                    if (ts != null) {
                        synchronized (mZslBufferLock) {
                            mZslResultMap.put(ts, result);
                            while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
                                Long oldest = Collections.min(mZslResultMap.keySet());
                                mZslResultMap.remove(oldest);
                            }
                        }
                    }
                    ticket.completed = true;
                    if (ts == null || exp == null || exp <= 0L || iso == null || iso <= 0
                            || !(ticket.baselineEnergy > 0.0)) {
                        ticket.closeStaged();
                        clearMotion26490CaptureShortTicket(ticket, "missing_actual_metadata");
                        return;
                    }
                    if (ticket.captureStartedTimestampNs > 0L
                            && ticket.captureStartedTimestampNs != ts) {
                        Log.e(TAG, "IRIS_26490_SHORT_TIMESTAMP_CONTRACT_MISMATCH"
                                + " startedTimestamp=" + ticket.captureStartedTimestampNs
                                + " resultTimestamp=" + ts
                                + " frameNumber=" + result.getFrameNumber()
                                + " resultTimestampAuthoritativeForExactImageMatch=true");
                    }
                    double energy = ExposureIndex.time2sec(exp) * iso;
                    double ratio = energy / ticket.baselineEnergy;
                    double actualHeadroomEv = Math.log(ticket.baselineEnergy / energy)
                            / Math.log(2.0);
                    boolean accepted = ratio >= requestedRatioMin
                            && ratio <= requestedRatioMax
                            && energy < ticket.baselineEnergy;
                    if (accepted) {
                        ticket.resultTimestampNs = ts;
                        ticket.actualExposureNs = exp;
                        ticket.actualIso = iso;
                        ticket.actualEnergy = energy;
                        Log.i(TAG, "IRIS_26486_SHORT_ACTUAL_ACCEPTED_NONBLOCKING"
                                + " sensorTimestamp=" + ts
                                + " captureStartedTimestamp=" + ticket.captureStartedTimestampNs
                                + " timestampExact=" + (ticket.captureStartedTimestampNs <= 0L
                                        || ticket.captureStartedTimestampNs == ts)
                                + " requestedExposureNs=" + requestedExp
                                + " requestedIso=" + requestedIso
                                + " requestedRatio=" + requestedRatio
                                + " requestedHeadroomEv=" + requestedHeadroomEv
                                + " nominalTargetRatio=" + MOTION_26480_SHORT_TARGET_RATIO
                                + " nominalProtectionEv=" + MOTION_26480_SHORT_PROTECTION_EV
                                + " actualExposureNs=" + exp + " actualIso=" + iso
                                + " ratio=" + ratio
                                + " actualHeadroomEv=" + actualHeadroomEv
                                + " allowedAroundClampedRequest=" + requestedRatioMin + ".." + requestedRatioMax
                                + " shutterGate=false");
                        boolean iris26489StagedDelivered =
                                tryDeliverMotion26489StagedShortRaw(ticket, result);
                        if (!iris26489StagedDelivered) scheduleMotion26486ShortDelivery(ticket);
                    } else {
                        ticket.closeStaged();
                        clearMotion26490CaptureShortTicket(ticket, "actual_exposure_rejected");
                        Log.w(TAG, "IRIS_26486_SHORT_ACTUAL_REJECTED ratio=" + ratio
                                + " actualHeadroomEv=" + actualHeadroomEv
                                + " requestedRatio=" + requestedRatio
                                + " requestedHeadroomEv=" + requestedHeadroomEv
                                + " allowedAroundClampedRequest=" + requestedRatioMin + ".." + requestedRatioMax);
                    }
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,
                        @NonNull android.hardware.camera2.CaptureFailure failure) {
                    ticket.completed = true;
                    ticket.closeStaged();
                    clearMotion26490CaptureShortTicket(ticket, "capture_failed");
                    Log.w(TAG, "IRIS_26486_SHORT_CAPTURE_FAILED reason=" + failure.getReason());
                }
            }, mBackgroundHandler);
            Log.i(TAG, "IRIS_26486_SHORT_CAPTURE_SUBMITTED_NONBLOCKING"
                    + " rawOnlyTarget=true shutterGate=false normalRingCleared=false");
            if (mBackgroundHandler != null) {
                mBackgroundHandler.postDelayed(() -> releaseMotion26486ShortHeadroom(ticket), 600L);
                mBackgroundHandler.postDelayed(() -> {
                    if (ticket.completed || ticket.slot.isSealed() || ticket.slot.hasFrame()) {
                        ticket.closeStaged();
                    }
                }, 1000L);
                mBackgroundHandler.postDelayed(() -> {
                    ticket.closeStaged();
                    clearMotion26490CaptureShortTicket(ticket, "two_second_terminal_cleanup");
                }, 2000L);
            }
            return true;
        } catch (CameraAccessException | IllegalArgumentException | IllegalStateException e) {
            ticket.completed = true;
            ticket.closeStaged();
            clearMotion26490CaptureShortTicket(ticket, "capture_submit_exception");
            Log.w(TAG, "IRIS_26486_SHORT_CAPTURE skipped " + e.getClass().getSimpleName());
            releaseMotion26486ShortHeadroom(ticket);
            return false;
        }
    }

    private void releaseMotion26486ShortHeadroom(Motion26486ShortTicket ticket) {
        if (ticket != null && ticket.headroomReleased.compareAndSet(false, true)) {
            int left = mMotion26486ShortAcquisitions.decrementAndGet();
            if (left < 0) mMotion26486ShortAcquisitions.set(0);
        }
    }

    private ImageFrame copyMotion26486ShortFrame(Image img, TotalCaptureResult result) {
        if (img == null) return null;
        int rowStride = img.getPlanes()[0].getRowStride();
        int pixelStride = img.getPlanes()[0].getPixelStride();
        int width = (img.getFormat() == ImageFormat.RAW10)
                ? img.getWidth() : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
        int height = img.getHeight();
        int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
        int offset = 0;
        if (PhotonCamera.getSettings().aspect169 && width > height) {
            height = width * 9 / 16;
            int offsetH = (img.getHeight() - height) / 2;
            offsetH -= offsetH % 2;
            offset = rowStride * offsetH;
            bufCapacity = rowStride * height;
        }
        Allocator.binning = PhotonCamera.getSettings().binning;
        ImageFrame frame = new ImageFrame(img.getPlanes()[0].getBuffer(), img.getFormat(),
                width, rowStride, offset, bufCapacity);
        frame.timestamp = img.getTimestamp();
        frame.width = PhotonCamera.getSettings().binning ? width / 2 : width;
        frame.height = PhotonCamera.getSettings().binning ? height / 2 : height;
        frame.setMotionV2PlaneLayout(
                img.getFormat(), img.getWidth(), height, rowStride, pixelStride,
                PhotonCamera.getSettings().binning);
        long exp = 0L; int iso = 0;
        if (result != null) {
            Long e = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer s = result.get(CaptureResult.SENSOR_SENSITIVITY);
            if (e != null) exp = e;
            if (s != null) iso = s;
        }
        frame.motionV2ActualExposureNs = exp;
        frame.motionV2ActualIso = iso;
        frame.motionV2ExposureEnergy = exp > 0L && iso > 0
                ? ExposureIndex.time2sec(exp) * iso : 0.0;
        populateMotion26480FrameMetadata(frame, result, true);
        return frame;
    }

    /* IRIS_26489_SHORT_RAW_PRE_RESULT_STAGING_DELIVERY
     * Resolve a copied RAW candidate once the exact Camera2 sensor timestamp becomes known.
     * Metadata is attached only after the timestamp match; neighboring-frame borrowing remains forbidden.
     */
    private boolean tryDeliverMotion26489StagedShortRaw(
            Motion26486ShortTicket ticket, TotalCaptureResult exactResult) {
        if (ticket == null || ticket.slot.isSealed() || ticket.slot.hasFrame()
                || ticket.resultTimestampNs <= 0L) {
            if (ticket != null && ticket.slot.isSealed()) ticket.closeStaged();
            return false;
        }
        ImageFrame staged = ticket.takeStaged(ticket.resultTimestampNs);
        if (staged == null) {
            Log.d(TAG, "IRIS_26490_SHORT_STAGED_EXACT_MISS"
                    + " resultTimestamp=" + ticket.resultTimestampNs
                    + " staged=" + ticket.stagedCount()
                    + " nearestFallback=false");
            return false;
        }
        populateMotion26480FrameMetadata(staged, exactResult, true);
        staged.motionV2ActualExposureNs = ticket.actualExposureNs;
        staged.motionV2ActualIso = ticket.actualIso;
        staged.motionV2ExposureEnergy = ticket.actualEnergy;
        boolean accepted = ticket.slot.offer(staged);
        ticket.closeStaged();
        if (accepted) {
            removeMotion26490ExactShortFromNormalRing(ticket.resultTimestampNs);
            clearMotion26490CaptureShortTicket(ticket, "staged_exact_delivery");
        }
        Log.i(TAG, "IRIS_26489_SHORT_STAGED_DELIVERY accepted=" + accepted
                + " timestamp=" + ticket.resultTimestampNs
                + " exactTimestampEquality=true"
                + " exactMetadata=true rawBeforeResultRaceRecovered=true");
        return accepted;
    }

    private boolean stageMotion26489ShortRawCandidate(
            Motion26486ShortTicket ticket, Image img) {
        if (ticket == null || img == null || !ticket.requested
                || ticket.slot.isSealed() || ticket.slot.hasFrame()) return false;
        long ts = img.getTimestamp();
        long identityTimestamp = ticket.expectedTimestampNs();
        if (identityTimestamp > 0L && ts != identityTimestamp) return false;
        if (ticket.completed && ticket.resultTimestampNs <= 0L) return false;

        TotalCaptureResult exact = null;
        synchronized (mZslBufferLock) { exact = mZslResultMap.get(ts); }
        ImageFrame copy;
        try {
            copy = copyMotion26486ShortFrame(img, exact);
        } catch (Throwable t) {
            Log.w(TAG, "IRIS_26489_SHORT_STAGE_COPY_SKIPPED timestamp=" + ts
                    + " reason=" + t.getClass().getSimpleName());
            return false;
        }
        if (copy == null) return false;

        if (ticket.resultTimestampNs > 0L
                && copy.timestamp == ticket.resultTimestampNs
                && exact != null) {
            populateMotion26480FrameMetadata(copy, exact, true);
            copy.motionV2ActualExposureNs = ticket.actualExposureNs;
            copy.motionV2ActualIso = ticket.actualIso;
            copy.motionV2ExposureEnergy = ticket.actualEnergy;
            boolean accepted = ticket.slot.offer(copy);
            ticket.closeStaged();
            if (accepted) {
                removeMotion26490ExactShortFromNormalRing(ts);
                clearMotion26490CaptureShortTicket(ticket, "raw_callback_direct_delivery");
            }
            Log.i(TAG, "IRIS_26489_SHORT_RAW_CALLBACK_DIRECT_DELIVERY accepted=" + accepted
                    + " timestamp=" + ts
                    + " resultTimestamp=" + ticket.resultTimestampNs
                    + " exactTimestampEquality=true exactResultAlreadyKnown=true");
            return true;
        }

        ticket.stage(copy);
        long expectedAfterStage = ticket.expectedTimestampNs();
        Log.d(TAG, "IRIS_26489_SHORT_RAW_STAGED timestamp=" + ts
                + " staged=" + ticket.stagedCount()
                + " expectedTimestamp=" + expectedAfterStage
                + " deltaNs=" + (expectedAfterStage > 0L ? ts - expectedAfterStage : Long.MIN_VALUE)
                + " identityKnown=" + (expectedAfterStage > 0L)
                + " awaitingExactResultTimestamp=" + (ticket.resultTimestampNs <= 0L)
                + " imageReaderObjectRetained=false");
        return true;
    }

    private void tryDeliverMotion26486ShortRaw(Motion26486ShortTicket ticket) {
        if (ticket == null || ticket.slot.isSealed() || ticket.slot.hasFrame()
                || ticket.resultTimestampNs <= 0L) return;
        Image found = null;
        TotalCaptureResult result = null;
        synchronized (mZslBufferLock) {
            java.util.Iterator<Image> it = mZslRingBuffer.iterator();
            while (it.hasNext()) {
                Image im = it.next();
                if (im != null && im.getTimestamp() == ticket.resultTimestampNs) {
                    found = im; it.remove();
                    result = mZslResultMap.get(im.getTimestamp());
                    break;
                }
            }
        }
        if (found == null) return;
        try {
            ImageFrame frame = copyMotion26486ShortFrame(found, result);
            boolean accepted = ticket.slot.offer(frame);
            if (accepted) {
                clearMotion26490CaptureShortTicket(ticket, "ring_exact_delivery");
            }
            Log.i(TAG, "IRIS_26486_SHORT_ASYNC_DELIVERY"
                    + " accepted=" + accepted
                    + " timestamp=" + (frame == null ? -1L : frame.timestamp)
                    + " resultTimestamp=" + ticket.resultTimestampNs
                    + " exactTimestampEquality=true"
                    + " processingMayAlreadyBeRunning=true");
        } finally {
            found.close();
        }
    }

    private void scheduleMotion26486ShortDelivery(Motion26486ShortTicket ticket) {
        if (ticket == null || mBackgroundHandler == null) return;
        final long[] delays = new long[]{0L, 20L, 60L, 140L, 260L, 420L};
        for (long delay : delays) {
            mBackgroundHandler.postDelayed(() -> tryDeliverMotion26486ShortRaw(ticket), delay);
        }
    }

    private boolean applyMotion26480ExplicitShortCaptureIfNeeded() {
        if (!isZslMode() || mCaptureSession == null || mCameraDevice == null
                || mImageReaderRaw == null || mCameraCharacteristics == null
                || mPreviewCaptureResult == null || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) return false;

        Long previewTimestamp=mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        Long baseExp=mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIso=mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        long rawAgeNs=previewTimestamp==null||mMotion26380RawSignalTimestampNs<=0L
                ?Long.MAX_VALUE:Math.abs(previewTimestamp-mMotion26380RawSignalTimestampNs);
        if(rawAgeNs>180_000_000L
                ||mMotion26380RawHighlightFraction<MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER
                ||baseExp==null||baseExp<=0L||baseIso==null||baseIso<=0) return false;

        mMotion26480ShortBaselineExposureNs=baseExp;
        mMotion26480ShortBaselineIso=baseIso;
        mMotion26480ShortBaselineEnergy=ExposureIndex.time2sec(baseExp)*baseIso;
        mMotion26480ShortResultTimestampNs=0L;
        mMotion26480ShortActualExposureNs=0L;
        mMotion26480ShortActualIso=0;
        mMotion26480ShortActualEnergy=0.0;
        mMotion26480ShortRequestCompleted=false;

        try {
            CaptureRequest.Builder b=mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26480_SHORT_TAG);
            if(mPreviewAFMode>=0) b.set(CaptureRequest.CONTROL_AF_MODE,mPreviewAFMode);
            if(Float.isFinite(mFocus)&&mFocus>=0.0f){
                try{b.set(CaptureRequest.LENS_FOCUS_DISTANCE,mFocus);}catch(IllegalArgumentException ignored){}
            }

            boolean manual=false;
            int[] caps=mCameraCharacteristics.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if(caps!=null) for(int c:caps){
                if(c==CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR){manual=true;break;}
            }
            long reqExp=Math.max(1L,Math.round(baseExp/MOTION_26480_SHORT_EXPOSURE_DIVISOR));
            int reqIso=baseIso;
            String mode;
            if(!manual){
                Log.w(TAG,"IRIS_26480_SHORT_CAPTURE skipped reason=MANUAL_SENSOR_UNAVAILABLE previewAeUntouched=true");
                mMotion26480ShortRequestCompleted=true;
                return false;
            }
            android.util.Range<Long> er=mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            android.util.Range<Integer> sr=mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            if(er!=null) reqExp=Math.max(er.getLower(),Math.min(er.getUpper(),reqExp));
            if(sr!=null) reqIso=Math.max(sr.getLower(),Math.min(sr.getUpper(),reqIso));
            b.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME,reqExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY,reqIso);
            mode="MANUAL_SENSOR_RAW_ONLY";
            try{VendorTagUtils.builderSessionApply(b,true,useMaximumResolutionKey,physicalID);}
            catch(Throwable e){Log.w(TAG,"IRIS_26480_SHORT_CAPTURE vendor tags skipped "+e.getClass().getSimpleName());}

            mMotion26480ShortRequested=true;
            final long requestedExp=reqExp;
            final int requestedIso=reqIso;
            final String requestedMode=mode;
            mCaptureSession.capture(b.build(),new CameraCaptureSession.CaptureCallback(){
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,@NonNull TotalCaptureResult result){
                    Long ts=result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Long exp=result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer iso=result.get(CaptureResult.SENSOR_SENSITIVITY);
                    if(ts!=null){
                        synchronized(mZslBufferLock){
                            mZslResultMap.put(ts,result);
                            while(mZslResultMap.size()>MAX_ZSL_RESULT_METADATA){
                                Long oldest=Collections.min(mZslResultMap.keySet());mZslResultMap.remove(oldest);
                            }
                        }
                    }
                    mMotion26480ShortRequestCompleted=true;
                    if(ts==null||exp==null||exp<=0L||iso==null||iso<=0||mMotion26480ShortBaselineEnergy<=0.0){
                        Log.w(TAG,"IRIS_26480_SHORT_ACTUAL_REJECTED reason=missingActualMetadata");return;
                    }
                    double e=ExposureIndex.time2sec(exp)*iso;
                    double ratio=e/mMotion26480ShortBaselineEnergy;
                    boolean accepted=ratio>=MOTION_26480_SHORT_RATIO_MIN&&ratio<=MOTION_26480_SHORT_RATIO_MAX
                            &&e<mMotion26480ShortBaselineEnergy;
                    if(accepted){
                        mMotion26480ShortResultTimestampNs=ts;
                        mMotion26480ShortActualExposureNs=exp;
                        mMotion26480ShortActualIso=iso;
                        mMotion26480ShortActualEnergy=e;
                        Log.i(TAG,"IRIS_26480_SHORT_ACTUAL_ACCEPTED role=HIGHLIGHT_SHORT"
                                +" requestMode="+requestedMode+" requestedExposureNs="+requestedExp
                                +" requestedIso="+requestedIso+" actualExposureNs="+exp+" actualIso="+iso
                                +" ratio="+ratio+" targetRatio="+MOTION_26480_SHORT_TARGET_RATIO
                                +" toleranceEv="+MOTION_26480_SHORT_TOLERANCE_EV
                                +" previewRepeatingRequestMutated=false");
                    }else Log.w(TAG,"IRIS_26480_SHORT_ACTUAL_REJECTED ratio="+ratio
                            +" allowed="+MOTION_26480_SHORT_RATIO_MIN+".."+MOTION_26480_SHORT_RATIO_MAX);
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,@NonNull android.hardware.camera2.CaptureFailure failure){
                    mMotion26480ShortRequestCompleted=true;
                    Log.w(TAG,"IRIS_26480_SHORT_CAPTURE_FAILED reason="+failure.getReason());
                }
            },mBackgroundHandler);
            Log.i(TAG,"IRIS_26480_SHORT_CAPTURE_SUBMITTED role=HIGHLIGHT_SHORT"
                    +" requestMode="+mode+" rawOnlyTarget=true previewRepeatingRequestMutated=false"
                    +" previewRebuilt=false normalRingCleared=false");
            return true;
        }catch(CameraAccessException|IllegalArgumentException|IllegalStateException e){
            mMotion26480ShortRequested=false;mMotion26480ShortRequestCompleted=true;
            Log.w(TAG,"IRIS_26480_SHORT_CAPTURE skipped "+e.getClass().getSimpleName());return false;
        }
    }

    /* IRIS_26540_NIGHT_CAPTURE_OWNER
     * Night RAW copies and exact Camera2 results are accumulated independently of ImageSaver and
     * sealed together into one immutable IrisNightBatch. No static IMAGE_BUFFER and no busy wait.
     */
    private final Object mIrisNight26540Lock = new Object();
    private final ArrayList<ImageFrame> mIrisNight26540Frames = new ArrayList<>();
    /* IRIS_26544_NIGHT_IMMEDIATE_IMAGE_RELEASE_OWNER
     * Original Photon copies/consumes a Camera2 RAW while the Image is valid and closes that
     * Image before returning from ImageReader.OnImageAvailableListener. 26543 diverged from that
     * proven ownership by handing live Camera2 Images to asynchronous disk workers. Night died
     * inside that exact ingestion window on the tested 26543 V1.4 APK. 26544 restores the proven
     * ownership discipline while retaining Iris Night's one-reference + disk-backed RAW memory:
     * reference is copied synchronously; every other RAW is synchronously spooled and the Camera2
     * Image is closed in this callback before the next callback is serviced. No live Image escapes.
     */
    private static final long IRIS_NIGHT_26544_SPOOL_RESERVE_BYTES = 128L * 1024L * 1024L;
    private volatile boolean mIrisNight26544ReferenceCopied = false;
    private volatile long mIrisNight26544CaptureGeneration = 0L;
    private volatile boolean mIrisNight26544SpoolCapacityChecked = false;
    private volatile String mIrisNight26544SpoolFailure = null;
    private final java.util.concurrent.ConcurrentHashMap<Long, TotalCaptureResult>
            mIrisNight26540Results = new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.ConcurrentHashMap<Long, CaptureRequest>
            mIrisNight26540Requests = new java.util.concurrent.ConcurrentHashMap<>();
    private volatile boolean mIrisNight26540CaptureActive = false;
    /* IRIS_26553_NIGHT_SINGLE_FLIGHT_OWNER
     * Covers the small interval between an AF callback entering captureStillPicture() and
     * prepareIrisNight26540CaptureState() publishing mIrisNight26540CaptureActive.
     */
    private boolean mIrisNight26553ShutterDispatchPending = false;
    private boolean mIrisNight26540SequenceComplete = false;
    private boolean mIrisNight26540Dispatched = false;
    private int mIrisNight26540ExpectedFrames = 0;
    // IRIS_26552_NIGHT_FROZEN_FRAME_PLAN_OWNER
    private IrisNightFrameSelector.Plan mIrisNight26552FramePlan = null;
    private int mIrisNight26540SaveRaw = 0;
    private boolean mIrisNight26540SuperRes = false;
    private boolean mIrisNight26540Aspect169 = false;
    private boolean mIrisNight26540EnergySaving = false;
    private boolean mIrisNight26540Watermark = false;
    private boolean mIrisNight26540Binning = false;
    private String mIrisNight26540CameraId = "0";
    private IrisMotionSettings.Snapshot mIrisNight26540IrisSettings = null;
    private CameraCharacteristics mIrisNight26540Characteristics = null;
    private int mIrisNight26540Rotation = 0;
    private static final String IRIS_26541_NIGHT_SHORT_TAG = "IRIS_26541_NIGHT_SHORT";
    private static final String IRIS_26541_NIGHT_LONG_TAG = "IRIS_26541_NIGHT_LONG";

    private void drainIrisNight26540ReaderBeforeCapture() {
        if (mImageReaderRaw == null) return;
        while (true) {
            Image stale = null;
            try { stale = mImageReaderRaw.acquireNextImage(); }
            catch (Throwable ignored) { break; }
            if (stale == null) break;
            try { stale.close(); } catch (Throwable ignored) {}
        }
    }

    private boolean reserveIrisNight26553ShutterDispatch() {
        synchronized (mIrisNight26540Lock) {
            if (mIrisNight26553ShutterDispatchPending || mIrisNight26540CaptureActive
                    || CaptureController.isProcessing) {
                Log.w(TAG, "IRIS_26553_NIGHT_SINGLE_FLIGHT_REJECT pending="
                        + mIrisNight26553ShutterDispatchPending + " active="
                        + mIrisNight26540CaptureActive + " processing=" + CaptureController.isProcessing);
                return false;
            }
            mIrisNight26553ShutterDispatchPending = true;
        }
        Log.i(TAG, "IRIS_26553_NIGHT_SINGLE_FLIGHT_RESERVED");
        return true;
    }

    private void releaseIrisNight26553ShutterDispatch(String reason) {
        boolean released;
        synchronized (mIrisNight26540Lock) {
            released = mIrisNight26553ShutterDispatchPending;
            mIrisNight26553ShutterDispatchPending = false;
        }
        if (released) Log.i(TAG, "IRIS_26553_NIGHT_SINGLE_FLIGHT_RELEASE reason=" + reason);
    }

    /* IRIS_26547_NIGHT_CAPTURE_ABORT_OWNER
     * Pre-dispatch Night failure must release every app-owned RAW representation and clear the
     * controller gate. Once dispatched, IrisNightProcessor owns the immutable batch instead.
     */
    private boolean abortIrisNight26547CaptureState(String reason) {
        boolean aborted = false;
        synchronized (mIrisNight26540Lock) {
            if (mIrisNight26540CaptureActive && !mIrisNight26540Dispatched) {
                for (ImageFrame frame : mIrisNight26540Frames) {
                    if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
                }
                mIrisNight26540Frames.clear();
                mIrisNight26540Results.clear();
                mIrisNight26540Requests.clear();
                mIrisNight26540CaptureActive = false;
                mIrisNight26540SequenceComplete = false;
                mIrisNight26540ExpectedFrames = 0;
                mIrisNight26552FramePlan = null;
                mIrisNight26544ReferenceCopied = false;
                mIrisNight26544SpoolFailure = null;
                CaptureController.isProcessing = false;
                aborted = true;
            }
        }
        if (aborted) {
            cleanupIrisNight26544SpoolCache();
            Log.critical(TAG, "IRIS_26547_NIGHT_CAPTURE_ABORT_CLEAN reason=" + reason
                    + " processing=false");
        }
        return aborted;
    }

    private void prepareIrisNight26540CaptureState(IrisNightFrameSelector.Plan framePlan, int saveRaw,
            boolean superRes, boolean aspect169, boolean energySaving, boolean watermark,
            boolean binning, String cameraId, IrisMotionSettings.Snapshot irisSettings,
            CameraCharacteristics characteristics, int rotation) {
        if (framePlan == null) throw new IllegalArgumentException("26552 Night frozen frame plan is null");
        final int expectedFrames = framePlan.totalFrames;
        if (expectedFrames < IrisNightFrameSelector.MIN_NIGHT_FRAMES
                || expectedFrames > IrisNightFrameSelector.MAX_NIGHT_FRAMES)
            throw new IllegalArgumentException("26552 Night invalid frozen frame count=" + expectedFrames);
        drainIrisNight26540ReaderBeforeCapture();
        cleanupIrisNight26544SpoolCache();
        mIrisNight26544ReferenceCopied = false;
        mIrisNight26544CaptureGeneration++;
        mIrisNight26544SpoolCapacityChecked = false;
        mIrisNight26544SpoolFailure = null;
        synchronized (mIrisNight26540Lock) {
            for (ImageFrame old : mIrisNight26540Frames) {
                if (old != null) try { old.close(); } catch (Throwable ignored) {}
            }
            mIrisNight26540Frames.clear();
            mIrisNight26540Results.clear();
            mIrisNight26540Requests.clear();
            mIrisNight26540ExpectedFrames = expectedFrames;
            mIrisNight26552FramePlan = framePlan;
            mIrisNight26540SequenceComplete = false;
            mIrisNight26540Dispatched = false;
            mIrisNight26540SaveRaw = saveRaw;
            mIrisNight26540SuperRes = superRes;
            mIrisNight26540Aspect169 = aspect169;
            mIrisNight26540EnergySaving = energySaving;
            mIrisNight26540Watermark = watermark;
            mIrisNight26540Binning = binning;
            mIrisNight26540CameraId = cameraId == null ? "0" : cameraId;
            mIrisNight26540IrisSettings = irisSettings;
            mIrisNight26540Characteristics = characteristics;
            mIrisNight26540Rotation = rotation;
            if (mIrisNight26540IrisSettings == null || mIrisNight26540IrisSettings.customNoiseModelEnabled
                    || mIrisNight26540Characteristics == null) {
                throw new IllegalStateException("26540 Night requires frozen exact-Camera2 Iris settings");
            }
            mIrisNight26540CaptureActive = true;
            CaptureController.isProcessing = true;
        }
        Log.processState(TAG, "NIGHT_CAPTURE_ARMED_" + expectedFrames + "_FRAMES");
        Log.critical(TAG, "IRIS_26544_NIGHT_CAPTURE_ARMED frames=" + expectedFrames
                + " saveRaw=" + mIrisNight26540SaveRaw + " cameraId=" + mIrisNight26540CameraId);
        Log.i(TAG, "IRIS_26552_NIGHT_CAPTURE_STATE_FROZEN frames=" + expectedFrames
                + " shortRequested=" + framePlan.shortFrames
                + " longRequested=" + framePlan.longFrames
                + " saveRaw=" + mIrisNight26540SaveRaw
                + " superRes=" + mIrisNight26540SuperRes
                + " aspect169=" + mIrisNight26540Aspect169
                + " energySaving=" + mIrisNight26540EnergySaving
                + " binning=" + mIrisNight26540Binning
                + " cameraId=" + mIrisNight26540CameraId);
    }

    /* IRIS_26554_NIGHT_HAL_QUEUE_DRAIN_OWNER
     * ImageReader callbacks are availability notifications, not a one-callback/one-image contract.
     * Drain all currently queued RAWs without retaining live Camera2 Images asynchronously.
     */
    private int drainIrisNight26554AvailableRawImages(@NonNull ImageReader reader, String reason) {
        int drained = 0;
        final long generation = mIrisNight26544CaptureGeneration;
        while (mIrisNight26540CaptureActive && generation == mIrisNight26544CaptureGeneration) {
            Image nightImage = null;
            ImageFrame copied = null;
            long timestamp = 0L;
            try {
                nightImage = reader.acquireNextImage();
                if (nightImage == null) break;
                drained++;
                timestamp = nightImage.getTimestamp();
                if (!mIrisNight26544ReferenceCopied) {
                    Log.i(TAG, "IRIS_26554_NIGHT_RAW_DRAIN role=REFERENCE reason=" + reason
                            + " timestamp=" + timestamp + " drained=" + drained);
                    copied = copyIrisNight26540Raw(nightImage);
                    synchronized (mIrisNight26540Lock) {
                        if (!mIrisNight26540CaptureActive
                                || generation != mIrisNight26544CaptureGeneration) {
                            copied.close();
                            copied = null;
                        } else if (!mIrisNight26544ReferenceCopied) {
                            mIrisNight26540Frames.add(copied);
                            mIrisNight26544ReferenceCopied = true;
                            Log.i(TAG, "IRIS_26544_NIGHT_REFERENCE_COPIED timestamp="
                                    + timestamp + " bytes="
                                    + (copied.buffer == null ? 0 : copied.buffer.capacity())
                                    + " persistentNativeReferenceFrames=1");
                            copied = null; // Controller frame list owns the copied RAW.
                        } else {
                            copied.close();
                            copied = null;
                        }
                    }
                } else {
                    Log.i(TAG, "IRIS_26554_NIGHT_RAW_DRAIN role=AUX reason=" + reason
                            + " timestamp=" + timestamp + " drained=" + drained);
                    final Image ownedImage = nightImage;
                    nightImage = null;
                    spoolIrisNight26544RawSynchronously(ownedImage, generation);
                }
            } catch (Throwable nightRawFailure) {
                if (copied != null) try { copied.close(); } catch (Throwable ignored) {}
                mIrisNight26544SpoolFailure = "drain:"
                        + nightRawFailure.getClass().getSimpleName() + ":"
                        + String.valueOf(nightRawFailure.getMessage());
                Log.e(TAG, "IRIS_26554_NIGHT_RAW_DRAIN_FAILED reason=" + reason, nightRawFailure);
                Log.critical(TAG, "IRIS_26554_NIGHT_RAW_DRAIN_FAILED reason=" + reason
                        + " type=" + nightRawFailure.getClass().getName()
                        + " message=" + String.valueOf(nightRawFailure.getMessage()));
                break;
            } finally {
                if (nightImage != null) {
                    try { nightImage.close(); } catch (Throwable ignored) {}
                    Log.critical(TAG, "IRIS_26544_NIGHT_CAMERA2_IMAGE_CLOSED role="
                            + (mIrisNight26544ReferenceCopied ? "REFERENCE_OR_AUX" : "REFERENCE")
                            + " timestamp=" + timestamp);
                }
            }
        }
        if (drained > 0) {
            Log.i(TAG, "IRIS_26554_NIGHT_RAW_DRAIN_COMPLETE reason=" + reason
                    + " drained=" + drained + " generation=" + generation);
        }
        tryDispatchIrisNight26540();
        return drained;
    }

    private long irisNight26554SequenceDrainGraceMs() {
        long maxExposureNs = 0L;
        synchronized (mIrisNight26540Lock) {
            for (CaptureRequest request : mIrisNight26540Requests.values()) {
                if (request == null) continue;
                Long ns = request.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
                if (ns != null) maxExposureNs = Math.max(maxExposureNs, ns);
            }
        }
        long exposureMs = Math.max(0L, maxExposureNs / 1_000_000L);
        return Math.max(750L, Math.min(5000L, 750L + exposureMs));
    }

    private ImageFrame copyIrisNight26540Raw(@NonNull Image image) {
        if (image.getFormat() != ImageFormat.RAW_SENSOR) {
            throw new IllegalArgumentException("26540 Night requires RAW_SENSOR image");
        }
        Image.Plane plane = image.getPlanes()[0];
        int rowStride = plane.getRowStride();
        int pixelStride = plane.getPixelStride();
        int storageWidth = rowStride / Math.max(1, pixelStride);
        int height = image.getHeight();
        int capacity = plane.getBuffer().capacity();
        ImageFrame frame = new ImageFrame(plane.getBuffer(), image.getFormat(), storageWidth,
                rowStride, 0, capacity, mIrisNight26540Binning);
        frame.timestamp = image.getTimestamp();
        frame.setMotionV2PlaneLayout(image.getFormat(), image.getWidth(), image.getHeight(),
                rowStride, pixelStride, mIrisNight26540Binning);
        frame.width = mIrisNight26540Binning ? storageWidth / 2 : storageWidth;
        frame.height = mIrisNight26540Binning ? height / 2 : height;
        return frame;
    }

    /* IRIS_26543_NIGHT_RAW_SPOOL_OWNER */
    private File irisNight26543SpoolDirectory() {
        File dir = new File(PhotonCamera.getApplicationContextStatic().getCacheDir(), "iris-night-raw-spool");
        if (!dir.exists() && !dir.mkdirs())
            throw new IllegalStateException("Cannot create Iris Night RAW spool directory");
        return dir;
    }

    private void cleanupIrisNight26544SpoolCache() {
        try {
            File dir = new File(PhotonCamera.getApplicationContextStatic().getCacheDir(), "iris-night-raw-spool");
            File[] stale = dir.listFiles((d, name) -> name.endsWith(".raw")
                    && (name.startsWith("iris26543_") || name.startsWith("iris26544_")));
            if (stale != null) for (File f : stale) { try { f.delete(); } catch (Throwable ignored) {} }
        } catch (Throwable cleanupFailure) {
            Log.w(TAG, "IRIS_26544_NIGHT_SPOOL_STALE_CLEANUP_FAILED " + cleanupFailure);
        }
    }

    /* IRIS_26544_NIGHT_SYNC_RAW_SPOOL_OWNER
     * The Camera2 Image never leaves OnImageAvailable ownership. The raw plane is written while
     * the Image is valid; the Image is closed in this method's finally block before callback return.
     * This restores original Photon's proven immediate-release discipline without retaining 14
     * additional full RAW copies in memory.
     */
    private void spoolIrisNight26544RawSynchronously(@NonNull Image image, long generation) {
        ImageFrame frame = null;
        File file = null;
        long bytes = 0L;
        long timestamp = 0L;
        long startNs = System.nanoTime();
        try {
            timestamp = image.getTimestamp();
            Log.i(TAG, "IRIS_26544_NIGHT_RAW_ACQUIRED role=AUX timestamp=" + timestamp);
            if (image.getFormat() != ImageFormat.RAW_SENSOR)
                throw new IllegalArgumentException("26544 Night spool requires RAW_SENSOR");
            if (mIrisNight26540Binning)
                throw new IllegalStateException("26544 Night disk spool requires native non-binned RAW layout");
            Image.Plane plane = image.getPlanes()[0];
            int rowStride = plane.getRowStride();
            int pixelStride = plane.getPixelStride();
            int storageWidth = rowStride / Math.max(1, pixelStride);
            int capacity = plane.getBuffer().capacity();
            bytes = capacity;
            File dir = irisNight26543SpoolDirectory();
            if (!mIrisNight26544SpoolCapacityChecked) {
                synchronized (mIrisNight26540Lock) {
                    if (!mIrisNight26544SpoolCapacityChecked) {
                        long required = Math.max(0L, (long)mIrisNight26540ExpectedFrames - 1L) * capacity
                                + IRIS_NIGHT_26544_SPOOL_RESERVE_BYTES;
                        if (dir.getUsableSpace() < required)
                            throw new IllegalStateException("Insufficient cache space for Night RAW spool: required="
                                    + required + " usable=" + dir.getUsableSpace());
                        mIrisNight26544SpoolCapacityChecked = true;
                        Log.critical(TAG, "IRIS_26544_NIGHT_SPOOL_CAPACITY expectedFrames="
                                + mIrisNight26540ExpectedFrames + " rawBytes=" + capacity
                                + " requiredWithReserve=" + required + " usable=" + dir.getUsableSpace());
                    }
                }
            }
            file = new File(dir, "iris26544_" + generation + "_" + timestamp + ".raw");
            java.nio.ByteBuffer source = plane.getBuffer().duplicate();
            source.position(0);
            source.limit(capacity);
            Log.i(TAG, "IRIS_26544_NIGHT_RAW_SYNC_WRITE_BEGIN timestamp=" + timestamp
                    + " bytes=" + capacity);
            try (FileOutputStream fos = new FileOutputStream(file);
                 java.nio.channels.FileChannel channel = fos.getChannel()) {
                while (source.hasRemaining()) channel.write(source);
            }
            if (file.length() != capacity)
                throw new IllegalStateException("Night RAW spool length=" + file.length() + " expected=" + capacity);
            frame = new ImageFrame();
            frame.timestamp = timestamp;
            frame.setMotionV2PlaneLayout(image.getFormat(), image.getWidth(), image.getHeight(),
                    rowStride, pixelStride, false);
            frame.width = storageWidth;
            frame.height = image.getHeight();
            frame.setIrisNightRawSpool(file, capacity);
            file = null; // frame.close() owns deletion from here.
            synchronized (mIrisNight26540Lock) {
                if (!mIrisNight26540CaptureActive || generation != mIrisNight26544CaptureGeneration) {
                    frame.close();
                    frame = null;
                } else {
                    mIrisNight26540Frames.add(frame);
                    Log.i(TAG, "IRIS_26544_NIGHT_RAW_SYNC_WRITE_END timestamp=" + frame.timestamp
                            + " bytes=" + frame.irisNightRawSpoolBytes
                            + " persistentNativeCopies=1 tookMs="
                            + ((System.nanoTime() - startNs) / 1_000_000L));
                    frame = null;
                }
            }
        } catch (Throwable spoolFailure) {
            if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            if (file != null) try { file.delete(); } catch (Throwable ignored) {}
            mIrisNight26544SpoolFailure = "write:" + spoolFailure.getClass().getSimpleName()
                    + ":" + String.valueOf(spoolFailure.getMessage());
            Log.e(TAG, "IRIS_26544_NIGHT_RAW_SYNC_SPOOL_FAILED bytes=" + bytes, spoolFailure);
            Log.critical(TAG, "IRIS_26544_NIGHT_RAW_SYNC_SPOOL_FAILED timestamp=" + timestamp
                    + " type=" + spoolFailure.getClass().getName() + " message="
                    + String.valueOf(spoolFailure.getMessage()));
        } finally {
            try { image.close(); } catch (Throwable ignored) {}
            Log.critical(TAG, "IRIS_26544_NIGHT_CAMERA2_IMAGE_CLOSED role=AUX timestamp=" + timestamp);
            tryDispatchIrisNight26540();
        }
    }

    /* IRIS_26540_NIGHT_EXACT_FRAME_METADATA_OWNER */
    private static void populateIrisNight26540FrameMetadata(@NonNull ImageFrame frame,
            @NonNull TotalCaptureResult result, @NonNull CaptureRequest request,
            @NonNull CameraCharacteristics characteristics) {
        Long exp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
        Long ts = result.get(CaptureResult.SENSOR_TIMESTAMP);
        Long skew = result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW);
        Float focus = result.get(CaptureResult.LENS_FOCUS_DISTANCE);
        Integer lens = result.get(CaptureResult.LENS_STATE);
        if (exp == null || exp <= 0L || iso == null || iso <= 0 || ts == null || ts <= 0L) {
            throw new IllegalStateException("26540 Night result missing exposure/ISO/timestamp");
        }
        Object iris26541RoleTag = request.getTag();
        if (IRIS_26541_NIGHT_SHORT_TAG.equals(iris26541RoleTag)) {
            frame.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        } else if (IRIS_26541_NIGHT_LONG_TAG.equals(iris26541RoleTag)) {
            frame.motionV2FrameRole = ImageFrame.MotionV2FrameRole.SHADOW_LONG;
        } else {
            throw new IllegalStateException("26541 Night exact request is missing SHORT/LONG role tag: "
                    + iris26541RoleTag);
        }
        frame.motionV2ShortHighlightFrame = false;
        frame.motionV2ActualExposureNs = exp;
        frame.motionV2ActualIso = iso;
        frame.motionV2ExposureEnergy = ExposureIndex.time2sec(exp) * iso;
        frame.motionV2ResultSensorTimestampNs = ts;
        frame.motionV2FrameNumber = result.getFrameNumber();
        if (skew != null) frame.motionV2RollingShutterSkewNs = skew;
        if (focus != null) frame.motionV2FocusDistanceDiopters = focus;
        if (lens != null) frame.motionV2LensState = lens;

        float[] dynamicBlack = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamicBlack != null && dynamicBlack.length >= 4) {
            boolean sane = true;
            for (int i = 0; i < 4; i++) sane &= Float.isFinite(dynamicBlack[i]) && dynamicBlack[i] >= 0f;
            if (sane) {
                System.arraycopy(dynamicBlack, 0, frame.motionV2BlackLevel, 0, 4);
                frame.motionV2BlackLevelValid = true;
            }
        }
        if (!frame.motionV2BlackLevelValid) {
            android.hardware.camera2.params.BlackLevelPattern fixed =
                    characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
            if (fixed != null) {
                int[] values = new int[4]; fixed.copyTo(values, 0);
                for (int i = 0; i < 4; i++) frame.motionV2BlackLevel[i] = values[i];
                frame.motionV2BlackLevelValid = true;
            }
        }
        Integer white = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (white == null || white <= 0) {
            white = characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        }
        if (white != null && white > 0) {
            frame.motionV2WhiteLevel = white;
            frame.motionV2WhiteLevelValid = true;
        }

        android.util.Pair<Double, Double>[] profile = result.get(CaptureResult.SENSOR_NOISE_PROFILE);
        boolean valid = profile != null && profile.length >= 4;
        boolean allReadZero = valid;
        if (valid) for (int i = 0; i < 4; i++) {
            android.util.Pair<Double, Double> q = profile[i];
            if (q == null || q.first == null || q.second == null
                    || !Double.isFinite(q.first) || !Double.isFinite(q.second)
                    || q.first <= 0.0 || q.second < 0.0) { valid = false; break; }
            frame.motionV2NoiseProfile[i * 2] = q.first.floatValue();
            frame.motionV2NoiseProfile[i * 2 + 1] = q.second.floatValue();
            allReadZero &= q.second == 0.0;
        }
        frame.motionV2NoiseProfileValid = valid;
        if (valid && allReadZero) {
            Log.i(TAG, "IRIS_26548_CAMERA2_ZERO_READ_NOISE_ACCEPTED timestamp=" + ts
                    + " source=night_exact_metadata");
        }
        frame.motionV2NoiseProfileSource = valid ? "CAMERA2_PER_FRAME" : "UNAVAILABLE";
        if (valid) {
            float[] n = frame.motionV2NoiseProfile;
            frame.motionV2NoiseS = (n[0] + 0.5f * (n[2] + n[4]) + n[6]) / 3.0f;
            frame.motionV2NoiseO = (n[1] + 0.5f * (n[3] + n[5]) + n[7]) / 3.0f;
        }
        if (!frame.motionV2BlackLevelValid || !frame.motionV2WhiteLevelValid || !valid) {
            throw new IllegalStateException("26540 Night exact sensor metadata incomplete timestamp=" + ts);
        }
    }

    private void finishIrisNight26544AfterSequenceGrace() {
        if (mImageReaderRaw != null && mIrisNight26540CaptureActive) {
            drainIrisNight26554AvailableRawImages(mImageReaderRaw, "sequence-grace");
        }
        boolean fail = false;
        int matchedCount = 0;
        int requestedCount = 0;
        synchronized (mIrisNight26540Lock) {
            if (!mIrisNight26540CaptureActive || mIrisNight26540Dispatched
                    || !mIrisNight26540SequenceComplete) return;
            requestedCount = mIrisNight26540ExpectedFrames;
            java.util.HashSet<Long> seen = new java.util.HashSet<>();
            for (ImageFrame frame : mIrisNight26540Frames) {
                if (frame == null || !seen.add(frame.timestamp)) continue;
                if (mIrisNight26540Results.containsKey(frame.timestamp)
                        && mIrisNight26540Requests.containsKey(frame.timestamp)) matchedCount++;
            }
            if (matchedCount >= 2) {
                // IRIS_26554_NIGHT_ACTUAL_DELIVERED_ROLE_RECOVERY
                // The slider is the immutable requested maximum. If the HAL truly delivers fewer
                // exact RAW/result/request pairs after the bounded drain, process that exact
                // delivered set. IrisNightBatch keeps requested roles as provenance and validates
                // actual SHORT/LONG roles independently; no missing role is fabricated.
                mIrisNight26540ExpectedFrames = matchedCount;
            } else {
                fail = true;
                mIrisNight26540CaptureActive = false;
                for (ImageFrame frame : mIrisNight26540Frames) {
                    if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
                }
                mIrisNight26540Frames.clear();
                mIrisNight26540Results.clear();
                mIrisNight26540Requests.clear();
                CaptureController.isProcessing = false;
            }
        }
        if (fail) {
            Log.e(TAG, "IRIS_26540_NIGHT_BOUNDED_DRAIN_FAILED matched=" + matchedCount);
            cameraEventsListener.onProcessingError("Iris Night: fewer than two exact RAW/result pairs");
            return;
        }
        Log.w(TAG, "IRIS_26554_NIGHT_ACTUAL_DELIVERED_SET matched=" + matchedCount
                + " requested=" + requestedCount
                + " degraded=" + (matchedCount != requestedCount)
                + " singleFrameFallback=false fabricatedFrames=false");
        tryDispatchIrisNight26540();
    }

    private void tryDispatchIrisNight26540() {
        IrisNightBatch sealedBatch = null;
        try {
            if (mIrisNight26544SpoolFailure != null) {
                throw new IllegalStateException("26544 Night RAW spool failure: "
                        + mIrisNight26544SpoolFailure);
            }
            synchronized (mIrisNight26540Lock) {
                if (!mIrisNight26540CaptureActive || !mIrisNight26540SequenceComplete
                        || mIrisNight26540Dispatched || mIrisNight26540ExpectedFrames < 2) return;
                ArrayList<ImageFrame> matched = new ArrayList<>();
                java.util.HashSet<Long> seen = new java.util.HashSet<>();
                for (ImageFrame frame : mIrisNight26540Frames) {
                    if (frame == null || !seen.add(frame.timestamp)) continue;
                    TotalCaptureResult result = mIrisNight26540Results.get(frame.timestamp);
                    CaptureRequest request = mIrisNight26540Requests.get(frame.timestamp);
                    if (result != null && request != null) matched.add(frame);
                }
                if (matched.size() < mIrisNight26540ExpectedFrames) return;
                matched.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
                if (matched.size() > mIrisNight26540ExpectedFrames) {
                    for (int i = mIrisNight26540ExpectedFrames; i < matched.size(); i++) {
                        try { matched.get(i).close(); } catch (Throwable ignored) {}
                    }
                    matched = new ArrayList<>(matched.subList(0, mIrisNight26540ExpectedFrames));
                }
                for (ImageFrame frame : matched) {
                    TotalCaptureResult exact = mIrisNight26540Results.get(frame.timestamp);
                    CaptureRequest exactRequest = mIrisNight26540Requests.get(frame.timestamp);
                    populateIrisNight26540FrameMetadata(frame, exact, exactRequest,
                            mIrisNight26540Characteristics);
                    frame.irisNightExactCaptureResult = exact;
                    frame.irisNightExactCaptureRequest = exactRequest;
                }
                ImageFrame sortedReference = matched.get(0);
                if (sortedReference.buffer == null
                        || sortedReference.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL) {
                    throw new IllegalStateException(
                            "26543 Night sorted first SHORT/reference is not the sole in-memory RAW");
                }
                Log.i(TAG, "IRIS_26543_NIGHT_REFERENCE_ORDER_PROOF timestamp="
                        + sortedReference.timestamp + " role=SHORT inMemory=true sortedBySensorTimestamp=true");
                ArrayList<ImageFrame> unmatched = new ArrayList<>(mIrisNight26540Frames);
                unmatched.removeAll(matched);
                for (ImageFrame frame : unmatched) {
                    if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
                }
                int inMemoryRawFrames = 0;
                int diskBackedRawFrames = 0;
                for (ImageFrame frame : matched) {
                    if (frame.buffer != null) inMemoryRawFrames++;
                    if (frame.irisNightRawDiskBacked) diskBackedRawFrames++;
                    if (!frame.hasMotionV2RawBacking())
                        throw new IllegalStateException("26543 Night matched frame lost RAW backing");
                }
                if (inMemoryRawFrames != 1 || diskBackedRawFrames != matched.size() - 1) {
                    throw new IllegalStateException("26544 Night bounded-memory proof failed memory="
                            + inMemoryRawFrames + " disk=" + diskBackedRawFrames
                            + " frames=" + matched.size());
                }
                Log.critical(TAG, "IRIS_26544_NIGHT_BOUNDED_MEMORY_PROOF frames=" + matched.size()
                        + " inMemoryRawFrames=" + inMemoryRawFrames
                        + " diskBackedRawFrames=" + diskBackedRawFrames
                        + " persistentNativeCopies=1 asyncLiveCamera2Images=0");
                final IrisNightFrameSelector.Plan frozenFramePlan = mIrisNight26552FramePlan;
                if (frozenFramePlan == null)
                    throw new IllegalStateException("26552 Night frozen frame plan missing at batch seal");
                sealedBatch = new IrisNightBatch(matched, new ArrayList<>(BurstShakiness),
                        java.util.Collections.emptyMap(), mIrisNight26540Results, mIrisNight26540Requests,
                        mIrisNight26540Characteristics, RAW_FORMAT, mIrisNight26540Rotation,
                        mIrisNight26540ExpectedFrames, frozenFramePlan.shortFrames, frozenFramePlan.longFrames,
                        mIrisNight26540SaveRaw, mIrisNight26540SuperRes,
                        mIrisNight26540Aspect169, mIrisNight26540EnergySaving,
                        mIrisNight26540Watermark, mIrisNight26540Binning,
                        mIrisNight26540CameraId, mIrisNight26540IrisSettings);
                mIrisNight26540Dispatched = true;
                mIrisNight26540CaptureActive = false;
                mIrisNight26540Frames.clear();
                mIrisNight26540Results.clear();
                mIrisNight26540Requests.clear();
                mIrisNight26552FramePlan = null;
            }
        } catch (Throwable sealFailure) {
            synchronized (mIrisNight26540Lock) {
                for (ImageFrame frame : mIrisNight26540Frames) {
                    if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
                }
                mIrisNight26540Frames.clear();
                mIrisNight26540Results.clear();
                mIrisNight26540Requests.clear();
                mIrisNight26540CaptureActive = false;
                mIrisNight26540Dispatched = false;
                mIrisNight26552FramePlan = null;
            }
            CaptureController.isProcessing = false;
            Log.e(TAG, "IRIS_26540_NIGHT_BATCH_SEAL_FAILED", sealFailure);
            cameraEventsListener.onProcessingError("Iris Night batch: "
                    + sealFailure.getClass().getSimpleName() + ": "
                    + String.valueOf(sealFailure.getMessage()));
            return;
        }
        final IrisNightBatch batch = sealedBatch;
        if (batch == null) return;
        Log.processState(TAG, "NIGHT_BATCH_SEALED");
        Log.critical(TAG, "IRIS_26544_NIGHT_BATCH_SEALED frames=" + batch.frames.size());
        Log.i(TAG, "IRIS_26554_NIGHT_BATCH_SEALED frames=" + batch.frames.size()
                + " shortActual=" + batch.shortFrameCount + " longActual=" + batch.longFrameCount
                + " shortRequested=" + batch.requestedShortFrames + " longRequested=" + batch.requestedLongFrames
                + " degradedBracket=" + batch.degradedBracket
                + " fabricatedFrames=false"
                + " exactResults=" + batch.results.size()
                + " zsl=false motionRing=false preShutterRaw=false"
                + " staticImageBuffer=false defaultSaver=false hdrxRun=false");
        try {
            Log.processState(TAG, "NIGHT_PROCESS_DISPATCH");
            Log.critical(TAG, "IRIS_26544_NIGHT_PROCESS_DISPATCH frames=" + batch.frames.size());
            processExecutor.execute(() -> {
                Log.processState(TAG, "NIGHT_PROCESSOR_THREAD_ENTER");
                Log.critical(TAG, "IRIS_26544_NIGHT_PROCESSOR_ENTER frames=" + batch.frames.size());
                IrisNightProcessor.process(batch, cameraEventsListener);
            });
        } catch (Throwable dispatchFailure) {
            for (ImageFrame frame : batch.frames) {
                if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            }
            CaptureController.isProcessing = false;
            Log.e(TAG, "IRIS_26540_NIGHT_PROCESS_DISPATCH_FAILED", dispatchFailure);
            cameraEventsListener.onProcessingError("Iris Night dispatch: "
                    + dispatchFailure.getClass().getSimpleName());
        }
    }

    private void resetMotion26480ShortCaptureState(){
        mMotion26480ShortRequested=false;mMotion26480ShortRequestCompleted=false;
        mMotion26480ShortResultTimestampNs=0L;mMotion26480ShortActualExposureNs=0L;
        mMotion26480ShortActualIso=0;mMotion26480ShortActualEnergy=0.0;
    }

    private void populateMotion26480FrameMetadata(@NonNull ImageFrame frame,
            TotalCaptureResult result,boolean shortRole){
        frame.motionV2FrameRole=shortRole?ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT:ImageFrame.MotionV2FrameRole.NORMAL;
        frame.motionV2ShortHighlightFrame=shortRole;
        if(result==null){frame.motionV2NoiseProfileSource="UNAVAILABLE";return;}
        Long exp=result.get(CaptureResult.SENSOR_EXPOSURE_TIME);Integer iso=result.get(CaptureResult.SENSOR_SENSITIVITY);
        Long ts=result.get(CaptureResult.SENSOR_TIMESTAMP);Long skew=result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW);
        Float focus=result.get(CaptureResult.LENS_FOCUS_DISTANCE);Integer lens=result.get(CaptureResult.LENS_STATE);
        if(exp!=null&&exp>0L)frame.motionV2ActualExposureNs=exp;if(iso!=null&&iso>0)frame.motionV2ActualIso=iso;
        if(frame.motionV2ActualExposureNs>0L&&frame.motionV2ActualIso>0)
            frame.motionV2ExposureEnergy=ExposureIndex.time2sec(frame.motionV2ActualExposureNs)*frame.motionV2ActualIso;
        if(ts!=null)frame.motionV2ResultSensorTimestampNs=ts;frame.motionV2FrameNumber=result.getFrameNumber();
        if(skew!=null)frame.motionV2RollingShutterSkewNs=skew;if(focus!=null)frame.motionV2FocusDistanceDiopters=focus;
        if(lens!=null)frame.motionV2LensState=lens;

        /* IRIS_26490_TIMESTAMP_OWNED_FRAME_RADIOMETRY
         * Use per-result dynamic levels when exposed by the HAL; otherwise fall back to the
         * physical-camera fixed 2x2 black pattern / white level. Values stay in row-column CFA
         * order, matching raw_to_cfa phase indexing.
         */
        float[] dynamicBlack = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamicBlack != null && dynamicBlack.length >= 4) {
            boolean saneBlack = true;
            for (int i = 0; i < 4; i++) {
                saneBlack &= Float.isFinite(dynamicBlack[i]) && dynamicBlack[i] >= 0.0f;
            }
            if (saneBlack) {
                System.arraycopy(dynamicBlack, 0, frame.motionV2BlackLevel, 0, 4);
                frame.motionV2BlackLevelValid = true;
            }
        }
        if (!frame.motionV2BlackLevelValid && mCameraCharacteristics != null) {
            android.hardware.camera2.params.BlackLevelPattern fixedBlack =
                    mCameraCharacteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
            if (fixedBlack != null) {
                int[] fixed = new int[4];
                fixedBlack.copyTo(fixed, 0);
                for (int i = 0; i < 4; i++) frame.motionV2BlackLevel[i] = fixed[i];
                frame.motionV2BlackLevelValid = true;
            }
        }
        Integer dynamicWhite = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (dynamicWhite != null && dynamicWhite > 0) {
            frame.motionV2WhiteLevel = dynamicWhite;
            frame.motionV2WhiteLevelValid = true;
        } else if (mCameraCharacteristics != null) {
            Integer fixedWhite = mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
            if (fixedWhite != null && fixedWhite > 0) {
                frame.motionV2WhiteLevel = fixedWhite;
                frame.motionV2WhiteLevelValid = true;
            }
        }
        android.util.Pair<Double,Double>[] np=result.get(CaptureResult.SENSOR_NOISE_PROFILE);
        boolean valid=np!=null&&np.length>=4,allReadZero=valid;
        if(valid)for(int i=0;i<4;i++){
            android.util.Pair<Double,Double> q=np[i];
            if(q==null||q.first==null||q.second==null||!Double.isFinite(q.first)||!Double.isFinite(q.second)
                    ||q.first<=0.0||q.second<0.0){valid=false;break;}
            frame.motionV2NoiseProfile[i*2]=q.first.floatValue();frame.motionV2NoiseProfile[i*2+1]=q.second.floatValue();
            allReadZero&=q.second==0.0;
        }
        frame.motionV2NoiseProfileValid=valid;
        if(valid&&allReadZero)Log.i(TAG,"IRIS_26548_CAMERA2_ZERO_READ_NOISE_ACCEPTED timestamp="
                +frame.timestamp+" source=motion_timestamp_metadata");
        frame.motionV2NoiseProfileSource=valid?"CAMERA2_PER_FRAME":"UNAVAILABLE";
        if(valid){float[] p=frame.motionV2NoiseProfile;
            frame.motionV2NoiseS=(p[0]+0.5f*(p[2]+p[4])+p[6])/3.0f;
            frame.motionV2NoiseO=(p[1]+0.5f*(p[3]+p[5])+p[7])/3.0f;}
    }

    /* IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL
     * True only when the rolling RAW ring already contained the requested
     * maximum at the instant of shutter press. Such a shot must not spend
     * 1.4 s trying to manufacture another normal frame group after press.
     */
    private boolean mMotion26485PrebufferFullAtPress = false;
    /* IRIS_26575_MOTION_SUPER_RES_SHUTTER_OWNER
     * One active Motion shot owns one immutable SR decision. The public preference may change
     * after shutter, but it must never change reconstruction/publication for this batch.
     */
    private boolean mMotion26575SuperResAtShutter = false;

    /* IRIS_26486_NO_WAIT_MAXIMUM_FRAME_POLICY */
    private static final double MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05;
    private static final double MOTION_26486_MAX_GROUP_SPAN_EV =
            2.0 * MOTION_26486_EXPOSURE_HALF_WINDOW_EV;
    /* IRIS_26487_SINGLE_ACTIVE_MOTION_PROCESSING_NO_BACKLOG
     * Keep the RAW ring filling while one immutable batch processes, but do not queue or run
     * another Motion reconstruction concurrently. The next shutter becomes eligible only after
     * the current batch completes, at which point the ring has already refilled pre-shutter RAWs.
     */
    private static final int MOTION_26486_MAX_INFLIGHT_BATCHES = 1;
    private final java.util.concurrent.atomic.AtomicInteger mMotion26486InFlightBatches =
            new java.util.concurrent.atomic.AtomicInteger(0);
    private final java.util.concurrent.atomic.AtomicInteger mMotion26486ShortAcquisitions =
            new java.util.concurrent.atomic.AtomicInteger(0);

    /* One capture-generation ticket. Callback state is ticket-local, so a second
     * queued Motion shot cannot overwrite the first shot's highlight metadata. */
    private static final class Motion26486ShortTicket {
        final com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot slot =
                new com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot();
        final java.util.concurrent.atomic.AtomicBoolean headroomReleased =
                new java.util.concurrent.atomic.AtomicBoolean(false);
        /* IRIS_26489_SHORT_RAW_PRE_RESULT_STAGING_OWNER
         * Camera2 may deliver RAW before TotalCaptureResult. Keep only four copied candidates,
         * newest-first relevant to the one outstanding short request. No ImageReader Image object
         * is retained, so the rolling ZSL reader cannot be starved by this race repair.
         */
        private final ArrayDeque<ImageFrame> stagedRaw = new ArrayDeque<>();
        private static final int MAX_STAGED_RAW = 4;
        synchronized void stage(ImageFrame frame) {
            if (frame == null) return;
            if (slot.isSealed() || slot.hasFrame()) {
                frame.close();
                return;
            }
            for (ImageFrame existing : stagedRaw) {
                if (existing != null && existing.timestamp == frame.timestamp) {
                    frame.close();
                    return;
                }
            }
            /* IRIS_26490_NEWEST_FOUR_PRE_RESULT_RAW_COPIES
             * This queue is only a race fallback until Camera2 identity is known. Preserve the
             * newest four observations rather than freezing the oldest four and accidentally
             * dropping the later short capture. Selection is still exact timestamp equality.
             */
            while (stagedRaw.size() >= MAX_STAGED_RAW) {
                ImageFrame oldest = stagedRaw.pollFirst();
                if (oldest != null) oldest.close();
            }
            stagedRaw.addLast(frame);
        }
        synchronized ImageFrame takeStaged(long timestampNs) {
            ImageFrame match = null;
            java.util.Iterator<ImageFrame> it = stagedRaw.iterator();
            while (it.hasNext()) {
                ImageFrame frame = it.next();
                if (frame != null && frame.timestamp == timestampNs) {
                    match = frame;
                    it.remove();
                    break;
                }
            }
            return match;
        }
        synchronized void closeStaged() {
            ImageFrame frame;
            while ((frame = stagedRaw.pollFirst()) != null) frame.close();
        }
        synchronized int stagedCount() { return stagedRaw.size(); }
        volatile boolean requested = false;
        volatile boolean completed = false;
        volatile long captureStartedTimestampNs = 0L;
        volatile long captureStartedFrameNumber = -1L;
        volatile long resultTimestampNs = 0L;
        long expectedTimestampNs() {
            long resultTs = resultTimestampNs;
            return resultTs > 0L ? resultTs : captureStartedTimestampNs;
        }
        volatile long actualExposureNs = 0L;
        volatile int actualIso = 0;
        volatile double actualEnergy = 0.0;
        double baselineEnergy = 0.0;
    }
    private volatile Motion26486ShortTicket mMotion26486CaptureShortTicket = null;

    /* IRIS_26505_PHYSICAL_LONG_BRACKET_OWNER
     * One intentional +EV RAW observation shares the already-existing isolated
     * ShadowAuxSlot owned by this Motion generation. It never enters the equal-
     * exposure Wronski frame list. Camera2 onCaptureStarted/result/Image timestamps
     * are the only identity authority; there is no nearest-frame borrowing.
     */
    private static final double MOTION_26505_LONG_TARGET_EV = 2.5;
    private static final double MOTION_26505_LONG_TARGET_MULTIPLIER =
            5.656854249492381;
    private static final long MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS =
            10_000_000L;
    private static final int MOTION_26505_LONG_FALLBACK_MAX_ISO = 800;
    private static final double MOTION_26505_LONG_MIN_ACTUAL_RATIO = 1.15;
    private static final double MOTION_26505_LONG_REQUEST_TOLERANCE_EV = 0.40;
    private static final String MOTION_26505_LONG_TAG = "IRIS_26505_SHADOW_LONG";

    private static final class Motion26505LongTicket {
        final com.particlesdevs.photoncamera.processing.MotionBatch.ShadowAuxSlot slot;
        private final java.util.ArrayDeque<ImageFrame> stagedRaw =
                new java.util.ArrayDeque<>();
        private static final int MAX_STAGED_RAW = 4;
        volatile boolean requested = false;
        volatile boolean completed = false;
        volatile long captureStartedTimestampNs = 0L;
        volatile long captureStartedFrameNumber = -1L;
        volatile long resultTimestampNs = 0L;
        volatile long actualExposureNs = 0L;
        volatile int actualIso = 0;
        volatile double actualEnergy = 0.0;
        double baselineEnergy = 0.0;

        Motion26505LongTicket(
                com.particlesdevs.photoncamera.processing.MotionBatch.ShadowAuxSlot slot) {
            this.slot = slot;
        }
        long expectedTimestampNs() {
            return resultTimestampNs > 0L
                    ? resultTimestampNs : captureStartedTimestampNs;
        }
        synchronized void stage(ImageFrame frame) {
            if (frame == null) return;
            if (slot == null || slot.isSealed() || slot.hasFrame()) {
                try { frame.close(); } catch (Throwable ignored) {}
                return;
            }
            while (stagedRaw.size() >= MAX_STAGED_RAW) {
                ImageFrame old = stagedRaw.pollFirst();
                if (old != null) try { old.close(); } catch (Throwable ignored) {}
            }
            stagedRaw.addLast(frame);
        }
        synchronized ImageFrame takeStaged(long timestampNs) {
            java.util.Iterator<ImageFrame> it = stagedRaw.iterator();
            while (it.hasNext()) {
                ImageFrame frame = it.next();
                if (frame != null && frame.timestamp == timestampNs) {
                    it.remove();
                    return frame;
                }
            }
            return null;
        }
        synchronized int stagedCount() { return stagedRaw.size(); }
        synchronized void closeStaged() {
            while (!stagedRaw.isEmpty()) {
                ImageFrame frame = stagedRaw.pollFirst();
                if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            }
        }
    }
    private volatile Motion26505LongTicket mMotion26505CaptureLongTicket = null;
    private volatile boolean mMotion26505LongRequested = false;

    private void clearMotion26505LongTicket(
            Motion26505LongTicket ticket, String reason) {
        if (ticket == null) return;
        boolean cleared = false;
        synchronized (mZslBufferLock) {
            if (mMotion26505CaptureLongTicket == ticket) {
                mMotion26505CaptureLongTicket = null;
                cleared = true;
            }
        }
        Log.d(TAG, "IRIS_26505_LONG_TICKET_CLEAR"
                + " reason=" + reason
                + " cleared=" + cleared
                + " slotHasFrame=" + (ticket.slot != null && ticket.slot.hasFrame())
                + " slotSealed=" + (ticket.slot != null && ticket.slot.isSealed()));
    }

    /* IRIS_26490_GENERATION_OWNED_SHORT_TICKET_LIFETIME
     * Keep the one outstanding short ticket reachable until exact RAW delivery or terminal
     * cleanup. Identity-checked clearing prevents an older callback from clearing a newer shot.
     */
    private void clearMotion26490CaptureShortTicket(
            Motion26486ShortTicket ticket, String reason) {
        if (ticket == null) return;
        boolean cleared = false;
        synchronized (mZslBufferLock) {
            if (mMotion26486CaptureShortTicket == ticket) {
                mMotion26486CaptureShortTicket = null;
                cleared = true;
            }
        }
        Log.d(TAG, "IRIS_26490_SHORT_TICKET_RELEASE"
                + " cleared=" + cleared
                + " reason=" + reason
                + " startedTimestamp=" + ticket.captureStartedTimestampNs
                + " resultTimestamp=" + ticket.resultTimestampNs
                + " slotHasFrame=" + ticket.slot.hasFrame()
                + " slotSealed=" + ticket.slot.isSealed());
    }

    private void removeMotion26490ExactShortFromNormalRing(long timestampNs) {
        if (timestampNs <= 0L) return;
        synchronized (mZslBufferLock) {
            java.util.Iterator<Image> it = mZslRingBuffer.iterator();
            while (it.hasNext()) {
                Image candidate = it.next();
                if (candidate != null && candidate.getTimestamp() == timestampNs) {
                    it.remove();
                    try { candidate.close(); } catch (Throwable ignored) {}
                }
            }
        }
    }

    /* IRIS_26520_V4_FROZEN_METADATA_GRACE
     * This is metadata-only grace, never a post-shutter RAW top-up.
     */
    private void pollMotion26520FrozenMetadataGrace(
            long shotId,
            Motion26486ShortTicket shortTicket,
            boolean shortRequested,
            long graceStartMs) {
        if (!mZslCapturing || mMotionDiagnosticShotId != shotId) return;
        if (mMotionTopUpActive) {
            throw new IllegalStateException("26520 frozen metadata grace cannot run with normal top-up active");
        }
        int exactValid = countValidMotionFrames();
        long elapsed = android.os.SystemClock.elapsedRealtime() - graceStartMs;
        if (exactValid >= mMotionTopUpMinimumFrames) {
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    shotId, "IRIS_26520_V4_FROZEN_METADATA_GRACE_READY",
                    "valid=" + exactValid + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " exactTimestampMetadata=true normalRingFrozen=true"
                            + " postShutterNormalAdmission=false shortNonBlocking=" + shortRequested);
            finalizeMotionZslCapture();
            return;
        }
        if (elapsed >= MOTION_26520_FROZEN_METADATA_GRACE_MS) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(shortTicket, "frozen_metadata_grace_timeout");
            }
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    shotId, "BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT",
                    "valid=" + exactValid + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " neighborFallback=false postShutterNormalAdmission=false");
            recoverMotionCaptureAfterEarlyExit("BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT", "Motion metadata preparing");
            return;
        }
        if (mBackgroundHandler == null) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(shortTicket, "frozen_metadata_no_handler");
            }
            recoverMotionCaptureAfterEarlyExit("FROZEN_METADATA_NO_HANDLER", "Motion metadata unavailable");
            return;
        }
        mBackgroundHandler.postDelayed(
                () -> pollMotion26520FrozenMetadataGrace(shotId, shortTicket, shortRequested, graceStartMs),
                MOTION_TOP_UP_POLL_MS);
    }

    private void triggerZslCapture() {
        /* IRIS_26486_BATCH_QUEUE_CAPTURE_OWNERSHIP
         * Immutable copied RAW batches do not block the Camera2 rolling ring.
         * IRIS_26487_SINGLE_ACTIVE_MOTION_PROCESSING_NO_BACKLOG narrows the old
         * bounded queue to exactly one active Motion reconstruction and zero queued
         * processing jobs, while the next pre-shutter RAW set refills in the ring.
         */
        if (mZslCapturing
                || mMotion26486InFlightBatches.get() >= MOTION_26486_MAX_INFLIGHT_BATCHES) {
            Log.w(TAG, "ZSL: Motion processing active; ring keeps refilling but shutter waits for current job");
            return;
        }

        /* IRIS_26548_MOTION_INPUT_READINESS_GATE
         * Never transition a Motion shot into the frozen generation when Camera2/session/result
         * ownership is not live or the shutter-time RAW ring cannot satisfy the existing minimum.
         * This does not change the healthy Xiaomi path and deliberately does not use
         * countValidMotionFrames(): exact timestamp metadata keeps its existing 180 ms frozen
         * metadata grace once RAW frames are physically present.
         */
        final int iris26548RequestedMaximum = iris26556RequestedMotionFrames();
        Log.i(TAG, "IRIS_26556_MOTION_FRAME_POLICY persisted="
                + PhotonCamera.getSettings().frameCount
                + " effective=" + iris26548RequestedMaximum
                + " cap=" + MOTION_26556_MAX_NORMAL_FRAMES
                + " postShutterNormalAdmission=false");
        final int iris26548MinimumRawFrames = Math.min(iris26548RequestedMaximum, 2);
        final int iris26548BufferedRawFrames;
        synchronized (mZslBufferLock) {
            iris26548BufferedRawFrames = mZslRingBuffer.size();
        }
        final boolean iris26548SessionReady = mCameraDevice != null
                && mCaptureSession != null && mPreviewCaptureResult != null;
        if (!iris26548SessionReady || iris26548BufferedRawFrames < iris26548MinimumRawFrames) {
            Log.w(TAG, "IRIS_26548_MOTION_NOT_READY_SESSION_OR_ZSL sessionReady="
                    + iris26548SessionReady + " bufferedRawFrames=" + iris26548BufferedRawFrames
                    + " minimumRawFrames=" + iris26548MinimumRawFrames
                    + " cameraDevice=" + (mCameraDevice != null)
                    + " captureSession=" + (mCaptureSession != null)
                    + " previewResult=" + (mPreviewCaptureResult != null));
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26548_MOTION_NOT_READY_SESSION_OR_ZSL",
                    "bufferedRawFrames=" + iris26548BufferedRawFrames
                            + " minimumRawFrames=" + iris26548MinimumRawFrames
                            + " sessionReady=" + iris26548SessionReady
                            + " ringFrozen=false auxRequested=false");
            return;
        }

        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;
        mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn();
        Log.i(TAG, "IRIS_26575_SUPER_RES_SHUTTER_SNAPSHOT enabled="
                + mMotion26575SuperResAtShutter
                + " preferenceReadback=" + PreferenceKeys.isIrisSuperResOn()
                + " immutableBatchPending=true");

        /* IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK
         * UI acknowledgement is not gated by the 1.4 s RAW top-up readiness loop. The actual
         * processing batch still waits for normal capture readiness; this only removes the frozen
         * shutter/animation perception.
         */
        try { cameraEventsListener.onCaptureStillPictureStarted("ZSLCaptureStarted!"); }
        catch (Exception uiError) { Log.e(TAG,"26484 immediate shutter ack failed",uiError); }

        mMotion26505LongRequested = false;
        Motion26505LongTicket iris26505PreviousLongTicket = mMotion26505CaptureLongTicket;
        if (iris26505PreviousLongTicket != null) {
            iris26505PreviousLongTicket.closeStaged();
            clearMotion26505LongTicket(iris26505PreviousLongTicket, "new_generation");
        }
        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();
        mMotion26486CaptureShortTicket = iris26486ShortTicket;
        final boolean iris26480ShortHighlightRequested =
                applyMotion26486ExplicitShortCaptureIfNeeded(iris26486ShortTicket);
        final Motion26505LongTicket iris26505LongTicket = new Motion26505LongTicket(
                iris26486ShortTicket.slot.shadowAuxSlot);
        mMotion26505CaptureLongTicket = iris26505LongTicket;
        final boolean iris26505LongRequested =
                applyMotion26505ExplicitLongCaptureIfUseful(iris26505LongTicket);
        if (!iris26505LongRequested) {
            clearMotion26505LongTicket(iris26505LongTicket, "not_requested");
        }

        mMotionTopUpStartMs = android.os.SystemClock.elapsedRealtime();
        mMotionTopUpTargetFrames = iris26548RequestedMaximum;
        /* IRIS_26486_NO_SINGLE_FRAME_FALLBACK */
        mMotionTopUpMinimumFrames = iris26548MinimumRawFrames;

        int buffered;
        synchronized (mZslBufferLock) {
            buffered = mZslRingBuffer.size();
        }
        mMotion26485PrebufferFullAtPress =
                buffered >= mMotionTopUpTargetFrames;

        mMotionDiagnosticShotId =
                com.particlesdevs.photoncamera.util.MotionTrace.beginShot(
                        physicalID,
                        mMotionTopUpTargetFrames,
                        buffered,
                        mMotionManualLadderActive,
                        mMotionUnifiedGeneration);

        /* IRIS_26576_SR_SHOT_SCOPED_SHUTTER_PROOF
         * Mirror the already-proven 26575 immutable shutter decision into the persistent trace
         * after beginShot() assigns the diagnostic shot id. No capture state is changed here.
         */
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                "IRIS_26576_SR_SHUTTER_STATE",
                "frozen=" + mMotion26575SuperResAtShutter
                        + " preferenceReadbackDiagnosticOnly=" + PreferenceKeys.isIrisSuperResOn()
                        + " immutableBatch=true");

        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                "TOP_UP_BEGIN",
                "buffered=" + buffered
                        + " target=" + mMotionTopUpTargetFrames
                        + " minimum=" + mMotionTopUpMinimumFrames
                        + " timeoutMs=" + MOTION_TOP_UP_TIMEOUT_MS
                        + " iris26480ShortHighlightRequested="
                        + iris26480ShortHighlightRequested
                        + " iris26505LongRequested="
                        + iris26505LongRequested
                        + " iris26480RawHighlightFraction="
                        + mMotion26380RawHighlightFraction
                        + " iris26480ShortAeTargetSteps="
                        + mMotion26478HighlightSafeTargetSteps
                        + " iris26485PrebufferFullAtPress="
                        + mMotion26485PrebufferFullAtPress);

        /* IRIS_26520_V4_EXPLICIT_ONE_NORMAL_FRAME
         * Slider value 1 is an explicit one-normal capture. Values >=2 retain a two-normal
         * admission floor, while the slider remains a maximum and the shutter-time ring stays
         * frozen. Metadata may catch up; replacement normal RAWs may not.
         */
        int iris26486ReadyNow = countValidMotionFrames();
        mMotionTopUpActive = false;
        if (iris26486ReadyNow < mMotionTopUpMinimumFrames) {
            long iris26520GraceStartMs = android.os.SystemClock.elapsedRealtime();
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    mMotionDiagnosticShotId, "IRIS_26520_V4_FROZEN_METADATA_GRACE_BEGIN",
                    "validAtPress=" + iris26486ReadyNow + " minimum=" + mMotionTopUpMinimumFrames
                            + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " normalRingFrozen=true postShutterNormalAdmission=false"
                            + " exactTimestampMetadataRequired=true neighborFallback=false");
            if (mBackgroundHandler != null) {
                final long iris26520ShotId = mMotionDiagnosticShotId;
                mBackgroundHandler.postDelayed(
                        () -> pollMotion26520FrozenMetadataGrace(
                                iris26520ShotId, iris26486ShortTicket,
                                iris26480ShortHighlightRequested, iris26520GraceStartMs),
                        MOTION_TOP_UP_POLL_MS);
            } else {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "frozen_metadata_no_handler");
                recoverMotionCaptureAfterEarlyExit("FROZEN_METADATA_NO_HANDLER", "Motion metadata unavailable");
            }
            return;
        }
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "IRIS_26520_V4_SHUTTER_FROZEN_BATCH_READY",
                "validAtPress=" + iris26486ReadyNow + " minimum=" + mMotionTopUpMinimumFrames
                        + " requestedMaximum=" + mMotionTopUpTargetFrames
                        + " shortNonBlocking=" + iris26480ShortHighlightRequested
                        + " normalRingFrozen=true postShutterNormalAdmission=false normalWaitMs=0");
        finalizeMotionZslCapture();
    }    // IRIS_26343_GENERATION_SAFE_ZSL
    /*
     * IRIS_26378_SHORT_EXPOSURE_GROUP_PRECISION
     *
     * The previous 750 us minimum tolerance merged ~0.286 ms and ~0.60 ms
     * into one "equal exposure" group. That allowed the stale dark first-shot
     * RAWs to satisfy the top-up even after system AE had moved brighter.
     *
     * Below 2 ms use a 100 us / 12.5% floor. Above 2 ms retain the historical
     * 750 us tolerance, preserving indoor/night grouping behavior.
     */
    private long iris26378MotionExposureToleranceNs(
            long firstExposure,
            long secondExposure) {
        long exposureReference =
                Math.max(firstExposure, secondExposure);

        if (exposureReference <= 2_000_000L) {
            return Math.max(
                    100_000L,
                    exposureReference / 8L);
        }

        return Math.max(
                750_000L,
                exposureReference / 12L);
    }

    /* IRIS_26486_EXPOSURE_ENERGY_EV_GROUPING */
    private double motion26486ExposureEnergy(TotalCaptureResult result) {
        if (result == null) return Double.NaN;
        Long exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
        if (exposure == null || iso == null || exposure <= 0L || iso <= 0)
            return Double.NaN;
        return ((double) exposure) * ((double) iso);
    }

    private double motion26486ExposureDeltaEv(TotalCaptureResult first,
            TotalCaptureResult second) {
        double a = motion26486ExposureEnergy(first);
        double b = motion26486ExposureEnergy(second);
        if (!(a > 0.0) || !(b > 0.0)) return Double.POSITIVE_INFINITY;
        return Math.abs(Math.log(a / b) / Math.log(2.0));
    }

    private boolean motionExposurePairMatches(
            TotalCaptureResult first, TotalCaptureResult second) {
        return motion26486ExposureDeltaEv(first, second)
                <= MOTION_26486_EXPOSURE_HALF_WINDOW_EV;
    }

    /*
     * IRIS_26378_SHADOW_DATA_READINESS
     *
     * Actual returned sensor metadata, never requested metadata:
     *   2 = >=0.50 ms at ISO <=100 (ready)
     *   1 = 0.40-0.50 ms at ISO <=100 (transitional)
     *   0 = <0.40 ms at ISO <=100 (stale/dark)
     *  -1 = not the bright/base-ISO class
     */
    private int iris26378ShadowReadiness(
            TotalCaptureResult result) {
        if (result == null) return -1;

        Long exposure =
                result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer iso =
                result.get(CaptureResult.SENSOR_SENSITIVITY);

        if (exposure == null
                || iso == null
                || exposure <= 0L
                || iso <= 0
                || iso > 100) {
            return -1;
        }

        if (exposure >= 500_000L) return 2;
        if (exposure >= 400_000L) return 1;
        return 0;
    }

    private boolean iris26378PreferShadowReadyGroup() {
        /* IRIS_26386_HAL_AE_GROUP_SELECTION */
        return false;
    }

    private TotalCaptureResult findBestMotionExposureGroup(
            List<Image> images,
            int startIndex) {
        if (images == null || images.isEmpty()) return null;

        TotalCaptureResult bestResult = null;
        int bestCount = 0;
        int bestReadiness = Integer.MIN_VALUE;

        boolean preferReady =
                iris26378PreferShadowReadyGroup();

        /*
         * IRIS_26378_ACTUAL_READY_GROUP_SELECTION
         *
         * Search newest to oldest as before.
         *
         * If the existing bright-scene AE bias is active, actual sensor
         * readiness outranks raw group count:
         * ready >=0.50ms > transitional > stale <0.40ms.
         *
         * Outside that bright/base-ISO class, behavior remains count-first.
         */
        for (int candidateIndex = images.size() - 1;
                candidateIndex >= Math.max(0, startIndex);
                candidateIndex--) {
            Image candidateImage = images.get(candidateIndex);
            if (candidateImage == null) continue;

            TotalCaptureResult candidateResult =
                    findNearestZslResult(
                            candidateImage.getTimestamp());
            if (candidateResult == null) continue;

            int matching = 0;
            for (int frameIndex = Math.max(0, startIndex);
                    frameIndex < images.size();
                    frameIndex++) {
                Image frameImage = images.get(frameIndex);
                if (frameImage == null) continue;

                TotalCaptureResult frameResult =
                        findNearestZslResult(
                                frameImage.getTimestamp());

                if (motionExposurePairMatches(
                        frameResult,
                        candidateResult)) {
                    matching++;
                }
            }

            int readiness =
                    iris26378ShadowReadiness(
                            candidateResult);

            boolean candidateInBrightClass =
                    readiness >= 0;

            boolean bestInBrightClass =
                    bestReadiness >= 0;

            boolean replace;

            if (preferReady
                    && candidateInBrightClass) {
                if (!bestInBrightClass) {
                    replace = true;
                } else if (readiness > bestReadiness) {
                    replace = true;
                } else if (readiness == bestReadiness) {
                    replace = matching > bestCount;
                } else {
                    replace = false;
                }
            } else if (preferReady
                    && bestInBrightClass) {
                replace = false;
            } else {
                replace = matching > bestCount;
            }

            if (replace) {
                bestCount = matching;
                bestReadiness = readiness;
                bestResult = candidateResult;
            }
        }

        return bestResult;
    }

    private int countValidMotionFrames() {
        int valid = 0;
        synchronized (mZslBufferLock) {
            List<Image> bufferedImages =
                    new ArrayList<>(mZslRingBuffer);
            TotalCaptureResult bestGroup =
                    findBestMotionExposureGroup(
                            bufferedImages,
                            0);

            for (Image image : bufferedImages) {
                if (image == null) continue;
                TotalCaptureResult frameResult =
                        findNearestZslResult(
                                image.getTimestamp());

                if (motionExposurePairMatches(
                        frameResult,
                        bestGroup)) {
                    valid++;
                }
            }
        }
        return valid;
    }


    private void pollMotionTopUp() {
        if (!mMotionTopUpActive) {
            return;
        }

        int buffered;
        synchronized (mZslBufferLock) {
            buffered = mZslRingBuffer.size();
        }

        int validBuffered = countValidMotionFrames();

        long elapsed = android.os.SystemClock.elapsedRealtime()
                - mMotionTopUpStartMs;

        boolean targetReady = validBuffered >= mMotionTopUpTargetFrames;
        boolean timedOut = elapsed >= MOTION_TOP_UP_TIMEOUT_MS;

        boolean iris26480ShortRawReady = false;
        if (mMotion26480ShortResultTimestampNs > 0L) {
            synchronized (mZslBufferLock) {
                for (Image im : mZslRingBuffer) {
                    if (im != null && im.getTimestamp() == mMotion26480ShortResultTimestampNs) {
                        iris26480ShortRawReady=true; break;
                    }
                }
            }
        }
        boolean iris26480ShortDoneWithoutAcceptedFrame=mMotion26480ShortRequested
                &&mMotion26480ShortRequestCompleted&&mMotion26480ShortResultTimestampNs==0L;
        boolean iris26480ShortExpired=mMotion26480ShortRequested&&!iris26480ShortRawReady
                &&elapsed>=MOTION_26480_SHORT_WAIT_MS;
        boolean iris26480ShortGateReady=!mMotion26480ShortRequested||iris26480ShortRawReady
                ||iris26480ShortDoneWithoutAcceptedFrame||iris26480ShortExpired;

        /*
         * IRIS_26378_PREBUFFER_READINESS_TRACE
         *
         * countValidMotionFrames() now follows the same actual-ready group
         * selector used during final drain.
         */
        TotalCaptureResult iris26378BestResult = null;
        int iris26378Readiness = -1;
        long iris26378BestExposureNs = -1L;
        int iris26378BestIso = -1;

        synchronized (mZslBufferLock) {
            java.util.List<Image> iris26378Images =
                    new java.util.ArrayList<>(mZslRingBuffer);
            iris26378BestResult =
                    findBestMotionExposureGroup(
                            iris26378Images,
                            0);
        }

        if (iris26378BestResult != null) {
            iris26378Readiness =
                    iris26378ShadowReadiness(
                            iris26378BestResult);
            Long iris26378Exp =
                    iris26378BestResult.get(
                            CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer iris26378Iso =
                    iris26378BestResult.get(
                            CaptureResult.SENSOR_SENSITIVITY);

            if (iris26378Exp != null) {
                iris26378BestExposureNs =
                        iris26378Exp;
            }
            if (iris26378Iso != null) {
                iris26378BestIso =
                        iris26378Iso;
            }
        }

        /*
         * IRIS_26379_AUTHORITATIVE_SHADOW_READINESS
         *
         * 26378 only logged readiness. It did not participate in completion,
         * so readiness=0 could still finalize immediately from frame count.
         */
        boolean iris26379ShadowPolicyActive =
                iris26378PreferShadowReadyGroup()
                        && iris26378Readiness >= 0;

        boolean iris26379TargetExposureReady =
                !iris26379ShadowPolicyActive
                        || iris26378Readiness >= 2;

        boolean iris26379TimeoutExposureAcceptable =
                !iris26379ShadowPolicyActive
                        || iris26378Readiness >= 1;

        /*
         * IRIS_26382_RAW_ADEQUACY_READINESS
         * A full frame count is not sufficient when the live RAW is still
         * severely floor-starved, highlights are safe, and the current
         * exposure remains materially below the same dynamic Motion ceiling.
         */
        boolean iris26382RawEvidenceFreshEnough =
                !Float.isNaN(mMotion26380RawFloorFraction)
                        && !Float.isNaN(mMotion26380RawShadowFraction)
                        && !Float.isNaN(mMotion26380RawHighlightFraction)
                        && mMotion26380RawSampleCount >= 64;
        boolean iris26382SeverelyStarved =
                iris26382RawEvidenceFreshEnough
                        && (mMotion26380RawFloorFraction >= 0.38f
                                || mMotion26380RawShadowFraction >= 0.88f)
                        && mMotion26380RawHighlightFraction < 0.010f;
        boolean iris26382MoreIntegrationAvailable =
                mMotion26382LastOpportunityCeilingNs > 0L
                        && mMotionUnifiedExposureNs > 0L
                        && mMotionUnifiedExposureNs
                                < (long)(0.92
                                        * mMotion26382LastOpportunityCeilingNs);
        /* IRIS_26386_RAW_EVIDENCE_ADVISORY_ONLY */
        boolean iris26382RawAdequacyReady = true;

        boolean iris26379TargetReady =
                targetReady
                        && iris26379TargetExposureReady
                        && iris26382RawAdequacyReady;

        boolean iris26379TimeoutReady =
                timedOut
                        && validBuffered >= mMotionTopUpMinimumFrames
                        && iris26379TimeoutExposureAcceptable;

        /*
         * IRIS_26383_TIMEOUT_FINALIZES_MINIMUM
         * The 1.4 s deadline is the safety valve. If minimum valid actual-
         * exposure frames exist, finalize the best available group rather
         * than aborting only because the older readiness rank is still zero.
         * Normal pre-timeout completion still obeys 26382 RAW adequacy.
         */
        boolean iris26383TimeoutMinimumReady =
                timedOut
                        && validBuffered >= mMotionTopUpMinimumFrames;

        /* IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS
         * Full rolling ZSL buffer at press is authoritative. The valid
         * equal-exposure group may be smaller than the requested maximum
         * after exact metadata filtering; that is not a reason to wait
         * 1.4 s after the shutter. Keep the existing safe minimum,
         * exposure-readiness, RAW-adequacy, and short-highlight gates.
         */
        boolean iris26485FullPrebufferReady =
                mMotion26485PrebufferFullAtPress
                        && validBuffered >= mMotionTopUpMinimumFrames
                        && iris26379TargetExposureReady
                        && iris26382RawAdequacyReady;

        if ((iris26379TargetReady
                || iris26485FullPrebufferReady
                || iris26383TimeoutMinimumReady)
                && iris26480ShortGateReady) {
            mMotionTopUpActive = false;
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    mMotionDiagnosticShotId,
                    "TOP_UP_END",
                    "buffered=" + buffered + " valid=" + validBuffered
                            + " targetReady=" + targetReady
                            + " timedOut=" + timedOut
                            + " elapsedMs=" + elapsed
                            + " iris26378Readiness="
                            + iris26378Readiness
                            + " iris26378BestExposureNs="
                            + iris26378BestExposureNs
                            + " iris26378BestIso="
                            + iris26378BestIso
                            + " iris26378AppliedExtraSteps="
                            + mMotion26368AeAppliedExtraSteps
                            + " iris26379ShadowPolicyActive="
                            + iris26379ShadowPolicyActive
                            + " iris26379TargetExposureReady="
                            + iris26379TargetExposureReady
                            + " iris26379TimeoutExposureAcceptable="
                            + iris26379TimeoutExposureAcceptable
                            + " iris26379TargetReady="
                            + iris26379TargetReady
                            + " iris26382RawAdequacyReady="
                            + iris26382RawAdequacyReady
                            + " iris26382SeverelyStarved="
                            + iris26382SeverelyStarved
                            + " iris26382MoreIntegrationAvailable="
                            + iris26382MoreIntegrationAvailable
                            + " iris26382LastOpportunityCeilingNs="
                            + mMotion26382LastOpportunityCeilingNs
                            + " iris26379TimeoutReady="
                            + iris26379TimeoutReady
                            + " iris26383TimeoutMinimumReady="
                            + iris26383TimeoutMinimumReady
                            + " iris26485PrebufferFullAtPress="
                            + mMotion26485PrebufferFullAtPress
                            + " iris26485FullPrebufferReady="
                            + iris26485FullPrebufferReady
                            + " iris26380RawFloorFraction="
                            + mMotion26380RawFloorFraction
                            + " iris26380RawShadowFraction="
                            + mMotion26380RawShadowFraction
                            + " iris26380RawHighlightFraction="
                            + mMotion26380RawHighlightFraction
                            + " iris26380RawMeanSignal="
                            + mMotion26380RawMeanSignal
                            + " iris26380RawSamples="
                            + mMotion26380RawSampleCount);
            finalizeMotionZslCapture();
            return;
        }

        if (timedOut) {
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    mMotionDiagnosticShotId,
                    "BUFFER_NOT_READY",
                    "buffered=" + buffered + " valid=" + validBuffered
                            + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed
                            + " aeProbe=" + mMotionAeProbeActive
                            + " probeFrames=" + mMotionAeProbeFrames
                            + " iris26379ExposureReadiness="
                            + iris26378Readiness
                            + " iris26379ExposureGateRejected="
                            + (iris26379ShadowPolicyActive
                                    && !iris26379TimeoutExposureAcceptable));
            recoverMotionCaptureAfterEarlyExit(
                    "BUFFER_NOT_READY",
                    "Motion buffer preparing");
            return;
        }

        mBackgroundHandler.postDelayed(
                this::pollMotionTopUp,
                MOTION_TOP_UP_POLL_MS);
    }    // IRIS_26342_MOTION_CAPTURE_RECOVERY
    private void recoverMotionCaptureAfterEarlyExit(
            @NonNull String traceResult,
            @NonNull String userMessage) {
        mMotionTopUpActive = false;
        mZslCapturing = false;
        burst = false;

        /*
         * IRIS_26383_ABORT_UI_RESET
         * This helper is pre-processing recovery. Clear the global busy latch
         * so BUFFER_NOT_READY/EMPTY_BUFFER cannot leave the shutter stuck.
         */
        isProcessing = false;
        mState = STATE_PREVIEW;

        if (mBackgroundHandler != null) {
            mBackgroundHandler.post(this::unlockFocus);
        }

        Runnable restoreUi = () -> {
            try {
                cameraEventsListener.onCaptureSequenceCompleted(null);
            } catch (Exception sequenceError) {
                Log.e(TAG, "Motion early-exit sequence cleanup failed: "
                        + Log.getStackTraceString(sequenceError));
            }

            try {
                cameraEventsListener.onProcessingFinished(userMessage);
            } catch (Exception processingError) {
                Log.e(TAG, "Motion early-exit shutter cleanup failed: "
                        + Log.getStackTraceString(processingError));
            }
        };

        if (activity != null) {
            activity.runOnUiThread(restoreUi);
        } else {
            new Handler(Looper.getMainLooper()).post(restoreUi);
        }

        Log.w(TAG, "IRIS_26383_ABORT_UI_RESET"
                + " isProcessing=" + isProcessing
                + " result=" + traceResult);
        Log.w(TAG, "MOTION_CAPTURE_RECOVERED"
                + " result=" + traceResult
                + " generation=" + mMotionUnifiedGeneration
                + " settled=" + mMotionUnifiedSettledFrames
                + " aeProbe=" + mMotionAeProbeActive);
    }


    private void finalizeMotionZslCapture() {
        final Motion26486ShortTicket iris26486ShortTicket = mMotion26486CaptureShortTicket;
        /* IRIS_26490_SHORT_TICKET_SURVIVES_NORMAL_BATCH_FREEZE
         * Do not detach the ingress owner here. The normal 15-frame batch is immutable, while the
         * one separately exposed short RAW may still arrive asynchronously on the same ImageReader.
         */
        /*
         * Top-up is stopped before this method; restoring live preview AE
         * cannot alter the already-buffered equal-exposure RAW group.
         */

        int frameCount = mMotionTopUpTargetFrames > 0
                ? mMotionTopUpTargetFrames
                : Math.max(
                        1,
                        iris26556RequestedMotionFrames());
        int candidateCount = frameCount;
        cameraRotation = PhotonCamera.getGravity().getCameraRotation(mSensorOrientation);
        BurstShakiness = new ArrayList<>();
        mExposures = new HashMap<>();

        // Drain raw Image objects from the ring buffer (no copy yet)
        List<Image> rawImages;
        int validAtDrain;
        synchronized (mZslBufferLock) {
            validAtDrain = countValidMotionFrames();
            if (validAtDrain >= mMotionTopUpMinimumFrames) {
                rawImages = new ArrayList<>(mZslRingBuffer);
                mZslRingBuffer.clear();
            } else {
                rawImages = null;
            }
        }

        if (rawImages == null) {
            Log.w(TAG, "MOTION_DRAIN_DEFERRED"
                    + " valid=" + validAtDrain
                    + " minimum=" + mMotionTopUpMinimumFrames
                    + " generation=" + mMotionUnifiedGeneration);
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    mMotionDiagnosticShotId,
                    "VALID_BUFFER_NOT_READY",
                    "valid=" + validAtDrain
                            + " minimum=" + mMotionTopUpMinimumFrames
                            + " generation=" + mMotionUnifiedGeneration);
            if (iris26486ShortTicket != null) {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "valid_buffer_not_ready");
            }
            recoverMotionCaptureAfterEarlyExit(
                    "VALID_BUFFER_NOT_READY",
                    "Motion buffer preparing");
            return;
        }

        /* IRIS_26480_SHORT_DRAIN_HEADROOM_V1 */
        int iris26480DrainTarget = frameCount
                + (mMotion26480ShortResultTimestampNs > 0L ? 1 : 0);
        int take = Math.min(rawImages.size(), iris26480DrainTarget);
        int skip = rawImages.size() - take;

        /* IRIS_26498_V13_COMPLETE_FROZEN_RING_EXPOSURE_AUTHORITY
         * Determine the unchanged normal exposure group from the same drain window as 26494,
         * but inspect all shutter-frozen RAWs before closing the prefix. Exactly one physically
         * brighter pre-shutter RAW may be cloned into the isolated shadow lane.
         */
        TotalCaptureResult bestExposureGroup =
                findBestMotionExposureGroup(rawImages, skip);
        ImageFrame irisV13ShadowAuxFrame = null;
        long irisV13ShadowAuxTimestamp = -1L;
        TotalCaptureResult irisV13ShadowAuxResult = null;
        int irisV13ShadowAuxIndex = -1;
        final long irisV13ShadowSelectStartNs = System.nanoTime();
        /* rawImages is the immediately frozen rolling-ZSL ring from the shutter path;
         * only tagged Short-A is non-normal and excluded separately. */
        final long irisV13PreShutterCeilingNs = Long.MAX_VALUE;
        final double irisV13NormalEnergy = motion26486ExposureEnergy(bestExposureGroup);
        Long irisV13NormalExpObj = bestExposureGroup == null ? null
                : bestExposureGroup.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer irisV13NormalIsoObj = bestExposureGroup == null ? null
                : bestExposureGroup.get(CaptureResult.SENSOR_SENSITIVITY);
        final long irisV13NormalExpNs = irisV13NormalExpObj == null ? 0L : irisV13NormalExpObj;
        final int irisV13NormalIso = irisV13NormalIsoObj == null ? 0 : irisV13NormalIsoObj;
        final long irisV13ShortTicketTimestamp = iris26486ShortTicket == null
                ? 0L : iris26486ShortTicket.expectedTimestampNs();
        double irisV13BestShadowExposureRatio = 0.0;
        int irisV13RingExact = 0, irisV13RingNormalEligible = 0;
        int irisV13DrainNormalEligible = 0, irisV13RingBrighter = 0;
        StringBuilder irisV13RingExposureTrace = new StringBuilder();
        for (int i = 0; i < rawImages.size(); ++i) {
            Image im = rawImages.get(i);
            if (im == null) continue;
            long rawTs = im.getTimestamp();
            TotalCaptureResult rr = findNearestZslResult(rawTs);
            Long rrTs = rr == null ? null : rr.get(CaptureResult.SENSOR_TIMESTAMP);
            Long e = rr == null ? null : rr.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer iso = rr == null ? null : rr.get(CaptureResult.SENSOR_SENSITIVITY);
            boolean exact = rrTs != null && rrTs == rawTs;
            if (exact) irisV13RingExact++;
            boolean normalEligible = motionExposurePairMatches(rr, bestExposureGroup);
            if (normalEligible) {
                irisV13RingNormalEligible++;
                if (i >= skip) irisV13DrainNormalEligible++;
            }
            double energy = motion26486ExposureEnergy(rr);
            double energyRatio = irisV13NormalEnergy > 0.0 && energy > 0.0
                    ? energy / irisV13NormalEnergy : Double.NaN;
            double deltaEv = energyRatio > 0.0
                    ? Math.log(energyRatio) / Math.log(2.0) : Double.NaN;
            boolean taggedShort = (rr != null && rr.getRequest() != null
                    && MOTION_26480_SHORT_TAG.equals(rr.getRequest().getTag()))
                    || (irisV13ShortTicketTimestamp > 0L && rawTs == irisV13ShortTicketTimestamp)
                    || (mMotion26480ShortResultTimestampNs > 0L
                            && rawTs == mMotion26480ShortResultTimestampNs);
            boolean preShutter = rawTs <= irisV13PreShutterCeilingNs;
            double exposureRatio = irisV13NormalExpNs > 0L && e != null && e > 0L
                    ? e / (double) irisV13NormalExpNs : Double.NaN;
            boolean brighter = !mMotion26505LongRequested
                    && !normalEligible && !taggedShort && exact && preShutter
                    && energyRatio >= 1.50 && energyRatio <= 4.0
                    && exposureRatio >= 1.15 && exposureRatio <= 2.50
                    && iso != null && iso > 0
                    && (irisV13NormalIso <= 0 || iso <= 2 * irisV13NormalIso);
            if (brighter) {
                irisV13RingBrighter++;
                if (irisV13ShadowAuxTimestamp < 0L || rawTs > irisV13ShadowAuxTimestamp) {
                    irisV13BestShadowExposureRatio = energyRatio;
                    irisV13ShadowAuxTimestamp = rawTs;
                    irisV13ShadowAuxResult = rr;
                    irisV13ShadowAuxIndex = i;
                }
            }
            if (irisV13RingExposureTrace.length() > 0) irisV13RingExposureTrace.append(';');
            irisV13RingExposureTrace.append(i).append(':').append(rawTs).append('/')
                    .append(e).append('/').append(iso).append("/dEv=").append(deltaEv)
                    .append("/normalEligible=").append(normalEligible)
                    .append("/inNormalDrainWindow=").append(i >= skip)
                    .append("/pre=").append(preShutter)
                    .append("/short=").append(taggedShort)
                    .append("/shadowEligible=").append(brighter);
        }

        if (irisV13ShadowAuxIndex >= 0 && irisV13ShadowAuxResult != null) {
            Image img = rawImages.get(irisV13ShadowAuxIndex);
            try {
                int rowStride = img.getPlanes()[0].getRowStride();
                int pixelStride = img.getPlanes()[0].getPixelStride();
                int width = (img.getFormat() == ImageFormat.RAW10)
                        ? img.getWidth()
                        : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
                int height = img.getHeight();
                int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
                int offset = 0;
                if (PhotonCamera.getSettings().aspect169 && width > height) {
                    height = width * 9 / 16;
                    int offsetH = (img.getHeight() - height) / 2;
                    offsetH -= offsetH % 2;
                    offset = rowStride * offsetH;
                    bufCapacity = rowStride * height;
                }
                Allocator.binning = PhotonCamera.getSettings().binning;
                ImageFrame shadow = new ImageFrame(
                        img.getPlanes()[0].getBuffer(), img.getFormat(),
                        width, rowStride, offset, bufCapacity);
                shadow.timestamp = img.getTimestamp();
                shadow.width = width;
                shadow.height = height;
                if (PhotonCamera.getSettings().binning) {
                    shadow.width /= 2;
                    shadow.height /= 2;
                }
                shadow.setMotionV2PlaneLayout(
                        img.getFormat(), img.getWidth(), height, rowStride, pixelStride,
                        PhotonCamera.getSettings().binning);
                populateMotion26480FrameMetadata(shadow, irisV13ShadowAuxResult, false);
                if (shadow.motionV2ExposureEnergy > 0.0) {
                    irisV13ShadowAuxFrame = shadow;
                } else {
                    shadow.close();
                    irisV13ShadowAuxTimestamp = -1L;
                    irisV13ShadowAuxResult = null;
                    irisV13ShadowAuxIndex = -1;
                }
            } catch (Throwable shadowCopyError) {
                if (irisV13ShadowAuxFrame != null) {
                    try { irisV13ShadowAuxFrame.close(); } catch (Throwable ignored) {}
                    irisV13ShadowAuxFrame = null;
                }
                irisV13ShadowAuxTimestamp = -1L;
                irisV13ShadowAuxResult = null;
                irisV13ShadowAuxIndex = -1;
                Log.w(TAG, "IRIS_26498_V13_SHADOW_AUX_COPY_REJECTED", shadowCopyError);
            }
        }
        final long irisV13ShadowSelectCpuMs =
                (System.nanoTime() - irisV13ShadowSelectStartNs) / 1_000_000L;
        Log.i(TAG, "IRIS_26498_V13_RING_EXPOSURE_DISTRIBUTION"
                + " frozenRingFrames=" + rawImages.size()
                + " normalDrainWindowFrames=" + (rawImages.size() - skip)
                + " exactMetadata=" + irisV13RingExact
                + " ringNormalEligible=" + irisV13RingNormalEligible
                + " drainNormalEligible=" + irisV13DrainNormalEligible
                + " shadowAuxCandidateFrames=" + irisV13RingBrighter
                + " normalExposureNs=" + irisV13NormalExpNs
                + " normalIso=" + irisV13NormalIso
                + " preShutterCeilingNs=" + irisV13PreShutterCeilingNs
                + " shadowAuxTimestamp=" + irisV13ShadowAuxTimestamp
                + " shadowAuxIndex=" + irisV13ShadowAuxIndex
                + " shadowAuxSelected=" + (irisV13ShadowAuxFrame != null)
                + " shadowAuxSelectMs=" + irisV13ShadowSelectCpuMs
                + " frames=[" + irisV13RingExposureTrace + "]");

        /* Preserve 26494 normal drain semantics byte-for-byte after the read-only full-ring scan.
         * The selected shadow RAW has already been copied into independently owned memory. */
        for (int i = 0; i < skip; i++) {
            rawImages.get(i).close();
        }

        // Populate exposures map from preview capture result ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â all ZSL frames share preview exposure
        double previewExpTime = 1.0;
        double previewISO = 100.0;
        long exposureTimeNs = 0;
        if (mPreviewCaptureResult != null) {
            Long expTimeNs = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer isoVal = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
            if (expTimeNs != null) {
                exposureTimeNs = expTimeNs;
                previewExpTime = expTimeNs / 1_000_000_000.0;
            }
            if (isoVal != null) previewISO = isoVal.doubleValue();
        }
        final double exposureVal = previewExpTime * previewISO;

        // Copy selected Images to ImageFrames only now (on shutter press)
        List<ImageFrame> selected = new ArrayList<>();
        HashMap<Long, TotalCaptureResult> selectedResults = new HashMap<>();
        ImageFrame iris26480ShortFrame = null;
        TotalCaptureResult iris26480ShortResult = null;

        for (int i = skip; i < rawImages.size(); i++) {
            Image img = rawImages.get(i);
            TotalCaptureResult frameResult = findNearestZslResult(img.getTimestamp());
            if (irisV13ShadowAuxFrame != null
                    && img.getTimestamp() == irisV13ShadowAuxTimestamp) {
                img.close();
                Log.i(TAG, "IRIS_26498_V13_SHADOW_AUX_ORIGINAL_IMAGE_CONSUMED"
                        + " timestamp=" + irisV13ShadowAuxTimestamp
                        + " copiedBeforePrefixClose=true normalAccumulatorAdmission=false");
                continue;
            }
            boolean iris26486TaggedShort = frameResult != null
                    && frameResult.getRequest() != null
                    && MOTION_26480_SHORT_TAG.equals(frameResult.getRequest().getTag());
            long iris26490TicketIdentityTimestamp = iris26486ShortTicket == null
                    ? 0L : iris26486ShortTicket.expectedTimestampNs();
            boolean iris26480IsShort = iris26486TaggedShort
                    || (iris26490TicketIdentityTimestamp > 0L
                            && img.getTimestamp() == iris26490TicketIdentityTimestamp)
                    || (mMotion26480ShortResultTimestampNs > 0L
                            && img.getTimestamp() == mMotion26480ShortResultTimestampNs);
            if (iris26480IsShort && frameResult == null && iris26486ShortTicket != null) {
                boolean stagedExact = stageMotion26489ShortRawCandidate(iris26486ShortTicket, img);
                Log.i(TAG, "IRIS_26490_SHORT_DRAIN_EXACT_PRE_RESULT_STAGED"
                        + " timestamp=" + img.getTimestamp()
                        + " expectedTimestamp=" + iris26490TicketIdentityTimestamp
                        + " staged=" + stagedExact
                        + " normalExposureGroupAdmission=false");
                img.close();
                continue;
            }
            if (iris26480IsShort && iris26480ShortFrame == null) {
                int rowStride = img.getPlanes()[0].getRowStride();
                int pixelStride = img.getPlanes()[0].getPixelStride();
                int width = (img.getFormat() == ImageFormat.RAW10)
                        ? img.getWidth()
                        : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
                int height = img.getHeight();
                int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
                int offset = 0;
                if (PhotonCamera.getSettings().aspect169 && width > height) {
                    height = width * 9 / 16;
                    int offsetH = (img.getHeight() - height) / 2;
                    offsetH -= offsetH % 2;
                    offset = rowStride * offsetH;
                    bufCapacity = rowStride * height;
                }
                Allocator.binning = PhotonCamera.getSettings().binning;
                ImageFrame shortFrame = new ImageFrame(
                        img.getPlanes()[0].getBuffer(), img.getFormat(),
                        width, rowStride, offset, bufCapacity);
                shortFrame.timestamp = img.getTimestamp();
                shortFrame.width = width;
                shortFrame.height = height;
                if (PhotonCamera.getSettings().binning) {
                    shortFrame.width /= 2;
                    shortFrame.height /= 2;
                }
                shortFrame.setMotionV2PlaneLayout(
                        img.getFormat(), img.getWidth(), height, rowStride, pixelStride,
                        PhotonCamera.getSettings().binning);
                long shortExpNs = mMotion26480ShortActualExposureNs;
                int shortIso = mMotion26480ShortActualIso;
                if (frameResult != null) {
                    Long e = frameResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer s = frameResult.get(CaptureResult.SENSOR_SENSITIVITY);
                    if (e != null) shortExpNs = e;
                    if (s != null) shortIso = s;
                }
                shortFrame.motionV2ActualExposureNs = shortExpNs;
                shortFrame.motionV2ActualIso = shortIso;
                shortFrame.motionV2ExposureEnergy = ExposureIndex.time2sec(shortExpNs) * shortIso;
                populateMotion26480FrameMetadata(shortFrame, frameResult, true);
                if (shortFrame.motionV2ExposureEnergy <= 0.0)
                    shortFrame.motionV2ExposureEnergy = ExposureIndex.time2sec(shortExpNs) * shortIso;
                if (frameResult != null) selectedResults.put(shortFrame.timestamp, frameResult);
                mExposures.put(shortFrame.timestamp, shortFrame.motionV2ExposureEnergy);
                iris26480ShortFrame = shortFrame;
                iris26480ShortResult = frameResult;
                img.close();
                Log.i(TAG, "IRIS_26480_SHORT_FRAME_TRANSPORTED"
                        + " timestamp=" + shortFrame.timestamp
                        + " exposureNs=" + shortFrame.motionV2ActualExposureNs
                        + " iso=" + shortFrame.motionV2ActualIso
                        + " energy=" + shortFrame.motionV2ExposureEnergy
                        + " noiseS=" + shortFrame.motionV2NoiseS
                        + " noiseO=" + shortFrame.motionV2NoiseO
                        + " excludedFromNormalExposureGroup=true");
                continue;
            }

            boolean exposureAccepted =
                    motionExposurePairMatches(frameResult, bestExposureGroup);
            if (!exposureAccepted) {
                img.close();
                continue;
            }
            int rowStride = img.getPlanes()[0].getRowStride();
            int pixelStride = img.getPlanes()[0].getPixelStride();
            int width = (img.getFormat() == ImageFormat.RAW10)
                    ? img.getWidth()
                    : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
            int height = img.getHeight();
            int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
            int offset = 0;
            if (PhotonCamera.getSettings().aspect169 && width > height) {
                height = width * 9 / 16;
                int offsetH = (img.getHeight() - height) / 2;
                offsetH -= offsetH % 2;
                offset = rowStride * offsetH;
                bufCapacity = rowStride * height;
            }
            Allocator.binning = PhotonCamera.getSettings().binning;
            ImageFrame frame = new ImageFrame(img.getPlanes()[0].getBuffer(), img.getFormat(),
                    width, rowStride, offset, bufCapacity);
            frame.timestamp = img.getTimestamp();

            frame.width = width;
            frame.height = height;
            if(PhotonCamera.getSettings().binning) {
                frame.width/= 2;
                frame.height/= 2;
            }
            frame.setMotionV2PlaneLayout(
                    img.getFormat(), img.getWidth(), height, rowStride, pixelStride,
                    PhotonCamera.getSettings().binning);
            img.close();
            long actualExposureNs = exposureTimeNs;
            int actualIso = (int)previewISO;
            if (frameResult != null) {
                Long e = frameResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                Integer s = frameResult.get(CaptureResult.SENSOR_SENSITIVITY);
                if (e != null) actualExposureNs = e;
                if (s != null) actualIso = s;
                selectedResults.put(frame.timestamp, frameResult);
            }
            frame.motionV2ActualExposureNs = actualExposureNs;
            frame.motionV2ActualIso = actualIso;
            frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            populateMotion26480FrameMetadata(frame, frameResult, false);
            if (frame.motionV2ExposureEnergy <= 0.0)
                frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            mExposures.put(frame.timestamp, frame.motionV2ExposureEnergy);
            selected.add(frame);
        }
        int actualCount = selected.size();
        /* IRIS_26486_WHOLE_GROUP_EXPOSURE_SPAN_PROOF */
        if (actualCount < mMotionTopUpMinimumFrames) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (irisV13ShadowAuxFrame != null) irisV13ShadowAuxFrame.close();
            if (iris26486ShortTicket != null) {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "insufficient_equal_energy_group");
            }
            recoverMotionCaptureAfterEarlyExit("INSUFFICIENT_EQUAL_ENERGY_GROUP",
                    "Motion buffer preparing");
            return;
        }
        double iris26486MinEnergy = Double.POSITIVE_INFINITY;
        double iris26486MaxEnergy = 0.0;
        for (ImageFrame f : selected) {
            if (f != null && f.motionV2ExposureEnergy > 0.0) {
                iris26486MinEnergy = Math.min(iris26486MinEnergy, f.motionV2ExposureEnergy);
                iris26486MaxEnergy = Math.max(iris26486MaxEnergy, f.motionV2ExposureEnergy);
            }
        }
        double iris26486SpanEv = iris26486MinEnergy > 0.0 && iris26486MaxEnergy >= iris26486MinEnergy
                ? Math.log(iris26486MaxEnergy / iris26486MinEnergy) / Math.log(2.0)
                : Double.POSITIVE_INFINITY;
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "IRIS_26486_EXPOSURE_GROUP_SPAN",
                "frames=" + actualCount + " minEnergy=" + iris26486MinEnergy
                        + " maxEnergy=" + iris26486MaxEnergy
                        + " spanEv=" + iris26486SpanEv
                        + " maxAllowedEv=" + MOTION_26486_MAX_GROUP_SPAN_EV);
        if (!(iris26486SpanEv <= MOTION_26486_MAX_GROUP_SPAN_EV + 1.0e-4)) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (irisV13ShadowAuxFrame != null) irisV13ShadowAuxFrame.close();
            if (iris26486ShortTicket != null) {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "exposure_group_span_rejected");
            }
            recoverMotionCaptureAfterEarlyExit("EXPOSURE_GROUP_SPAN_REJECTED",
                    "Motion exposure changed");
            return;
        }
        if (iris26480ShortFrame != null) {
            double minNormalEnergy=Double.POSITIVE_INFINITY;
            for(ImageFrame n:selected) if(n!=null&&n.motionV2ExposureEnergy>0.0)
                minNormalEnergy=Math.min(minNormalEnergy,n.motionV2ExposureEnergy);
            if(!(iris26480ShortFrame.motionV2ExposureEnergy>0.0&&Double.isFinite(minNormalEnergy)
                    &&iris26480ShortFrame.motionV2ExposureEnergy<minNormalEnergy)){
                Log.w(TAG,"IRIS_26480_SHORT_ROLE_REJECTED_AT_DRAIN reason=notStrictlyLowerThanEveryNormal"
                        +" shortEnergy="+iris26480ShortFrame.motionV2ExposureEnergy+" minNormalEnergy="+minNormalEnergy);
                mExposures.remove(iris26480ShortFrame.timestamp);selectedResults.remove(iris26480ShortFrame.timestamp);
                iris26480ShortFrame.close();iris26480ShortFrame=null;iris26480ShortResult=null;
            }
        }
        final com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot
                iris26486ShortSlot = iris26486ShortTicket != null
                        ? iris26486ShortTicket.slot
                        : new com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot();
        if (irisV13ShadowAuxFrame != null) {
            long shadowTs = irisV13ShadowAuxFrame.timestamp;
            boolean shadowAccepted = iris26486ShortSlot.shadowAuxSlot.offer(irisV13ShadowAuxFrame);
            Log.i(TAG, "IRIS_26498_V13_SHADOW_AUX_BATCH_DELIVERY"
                    + " accepted=" + shadowAccepted
                    + " timestamp=" + shadowTs
                    + " normalAccumulatorAdmission=false separateAuxSlot=true");
            irisV13ShadowAuxFrame = null;
        }
        if (iris26480ShortFrame != null) {
            long iris26486ShortTs = iris26480ShortFrame.timestamp;
            boolean iris26490ShortAcceptedAtDrain = iris26486ShortSlot.offer(iris26480ShortFrame);
            if (iris26490ShortAcceptedAtDrain && iris26486ShortTicket != null) {
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "drain_exact_delivery");
            }
            Log.i(TAG, "IRIS_26490_SHORT_DRAIN_DELIVERY"
                    + " accepted=" + iris26490ShortAcceptedAtDrain
                    + " timestamp=" + iris26486ShortTs
                    + " exactMetadata=" + (iris26480ShortResult != null));
            mExposures.remove(iris26486ShortTs);
            selectedResults.remove(iris26486ShortTs);
            iris26480ShortFrame = null;
        }
        /* IRIS_26486_SHORT_NEVER_IN_NORMAL_FRAME_LIST */
        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);

        /* IRIS_26486_MOTIONBATCH_SOLE_PROCESSING_OWNER */
        final ImageSaver iris26486ImageSaver = new ImageSaver(cameraEventsListener);
        iris26486ImageSaver.setFrameCount(iris26480ProcessingFrames.size());
        iris26486ImageSaver.setImageFormat(CaptureController.RAW_FORMAT);
        iris26486ImageSaver.implementation = ImageSaverSelector.getImageSaver(
                CaptureController.RAW_FORMAT, iris26486ImageSaver.implementation);
        iris26486ImageSaver.implementation.frameCount = iris26480ProcessingFrames.size();
        mImageSaver = iris26486ImageSaver; // UI/debug compatibility only; lambda uses local owner.

        final int motionSelectedFrameCount = selected.size();
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "JPEG_EXIF_FRAMECOUNT",
                "selectedFrameCount=" + motionSelectedFrameCount
                        + " publication=serializedMotionBatchOwner");

        /* IRIS_26486_CAPTURE_RELEASE_DEFERRED_UNTIL_BATCH_FROZEN */
        mMotionTopUpActive = false;

        mCaptureResult = mPreviewCaptureResult;
        mMeasuredFrameCnt = actualCount;

        cameraEventsListener.onFrameCountSet(actualCount);
        /* IRIS_26484_SHUTTER_ACK_ALREADY_SENT_AT_PRESS */
        cameraEventsListener.onBurstPrepared(null);
        final double frametime = exposureTimeNs > 0 ? ExposureIndex.time2sec(exposureTimeNs) : previewExpTime;
        for (int i = 0; i < actualCount; i++) {
            cameraEventsListener.onFrameCaptureStarted(null);
            cameraEventsListener.onFrameCaptureCompleted(
                    new TimerFrameCountViewModel.FrameCntTime(i, actualCount, frametime));
        }
        cameraEventsListener.onCaptureSequenceCompleted(null);

        long[] frameTimestamps = new long[actualCount];
        for (int i = 0; i < actualCount; i++) {
            frameTimestamps[i] = selected.get(i).timestamp;
        }
        PhotonCamera.getGyro().buildZslBurstShakiness(frameTimestamps, exposureTimeNs, BurstShakiness);
        PhotonCamera.getGyro().CompleteSequence();

        /* IRIS_26486_EXPOSURE_PAIR_PUBLICATION_DEFERRED
         * MotionBatch reconstructs per-shot ExpoPair objects from copied actual metadata.
         * The legacy static fullpairs list is populated only on the serialized process lane.
         */

        /*
         * IRIS_26360_PER_FRAME_ACTUAL_METADATA
         * Logging only. This does not alter frame selection, exposure,
         * image buffers, merge weights, or processing.
         */
        if (actualCount > 0) {
            double[] iris26360Energies = new double[actualCount];
            Double iris26360RefObj =
                    mExposures.get(selected.get(actualCount - 1).timestamp);
            double iris26360ReferenceEnergy =
                    iris26360RefObj == null ? 0.0 : iris26360RefObj;
            double iris26360Sum = 0.0;

            for (int iris26360Index = 0;
                 iris26360Index < actualCount;
                 iris26360Index++) {
                ImageFrame iris26360Frame = selected.get(iris26360Index);
                TotalCaptureResult iris26360Result =
                        selectedResults.get(iris26360Frame.timestamp);

                Long iris26360ResultTs = iris26360Result == null
                        ? null
                        : iris26360Result.get(CaptureResult.SENSOR_TIMESTAMP);
                Long iris26360ExposureNs = iris26360Result == null
                        ? null
                        : iris26360Result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                Integer iris26360Iso = iris26360Result == null
                        ? null
                        : iris26360Result.get(CaptureResult.SENSOR_SENSITIVITY);

                Double iris26360EnergyObj =
                        mExposures.get(iris26360Frame.timestamp);
                double iris26360Energy =
                        iris26360EnergyObj == null
                                ? 0.0
                                : iris26360EnergyObj;

                iris26360Energies[iris26360Index] = iris26360Energy;
                iris26360Sum += iris26360Energy;

                long iris26360MatchDeltaNs =
                        iris26360ResultTs == null
                                ? Long.MIN_VALUE
                                : Math.abs(
                                        iris26360ResultTs
                                                - iris26360Frame.timestamp);
                double iris26360Ratio =
                        iris26360ReferenceEnergy > 0.0
                                ? iris26360Energy
                                        / iris26360ReferenceEnergy
                                : Double.NaN;

                com.particlesdevs.photoncamera.util.MotionTrace.state(
                        mMotionDiagnosticShotId,
                        "FRAME_META",
                        "index=" + iris26360Index
                                + " rawTimestamp="
                                + iris26360Frame.timestamp
                                + " resultTimestamp="
                                + iris26360ResultTs
                                + " matchDeltaNs="
                                + iris26360MatchDeltaNs
                                + " exposureNs="
                                + iris26360ExposureNs
                                + " iso=" + iris26360Iso
                                + " exposureEnergy="
                                + iris26360Energy
                                + " energyRatioToReference="
                                + iris26360Ratio);
            }

            double[] iris26360Sorted =
                    java.util.Arrays.copyOf(
                            iris26360Energies,
                            iris26360Energies.length);
            java.util.Arrays.sort(iris26360Sorted);

            double iris26360Mean = iris26360Sum / actualCount;
            double iris26360Variance = 0.0;
            for (double iris26360Energy : iris26360Energies) {
                double iris26360Delta =
                        iris26360Energy - iris26360Mean;
                iris26360Variance +=
                        iris26360Delta * iris26360Delta;
            }
            iris26360Variance /= actualCount;
            double iris26360Std = Math.sqrt(iris26360Variance);
            double iris26360Cv =
                    iris26360Mean > 0.0
                            ? iris26360Std / iris26360Mean
                            : Double.NaN;
            double iris26360Median =
                    (actualCount & 1) == 1
                            ? iris26360Sorted[actualCount / 2]
                            : 0.5 * (
                                    iris26360Sorted[actualCount / 2 - 1]
                                            + iris26360Sorted[actualCount / 2]);

            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    mMotionDiagnosticShotId,
                    "FRAME_META_SUMMARY",
                    "count=" + actualCount
                            + " minEnergy=" + iris26360Sorted[0]
                            + " medianEnergy=" + iris26360Median
                            + " maxEnergy="
                            + iris26360Sorted[actualCount - 1]
                            + " meanEnergy=" + iris26360Mean
                            + " stdEnergy=" + iris26360Std
                            + " coefficientOfVariation=" + iris26360Cv
                            + " referenceEnergy="
                            + iris26360ReferenceEnergy);
        }

        final int capturedCount = actualCount;

        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                /*
         * IRIS_26378_FINAL_ACTUAL_READY_SELECTION
         * Final selected frames use the same precise exposure grouping and
         * readiness-prioritized selector as top-up counting.
         */
        "BUFFER_SELECTED",
                "capturedCount=" + capturedCount
                        + " requestedSetting="
                        + PhotonCamera.getSettings().frameCount
                        + " candidateCount=" + candidateCount
                        + " topUpTarget=" + mMotionTopUpTargetFrames
                        + " topUpMinimum=" + mMotionTopUpMinimumFrames
                        + " generation=" + mMotionUnifiedGeneration);

        if (capturedCount == 0) {
            Log.w(TAG, "ZSL ring buffer had no valid current-generation frames");
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    mMotionDiagnosticShotId,
                    "EMPTY_BUFFER",
                    "generation=" + mMotionUnifiedGeneration + " validAtDrain=" + validAtDrain + " settled="
                            + mMotionUnifiedSettledFrames);
            SaverImplementation.IMAGE_BUFFER.clear();
            recoverMotionCaptureAfterEarlyExit(
                    "EMPTY_BUFFER",
                    "ZSL buffer not ready");
            return;
        }

        final MotionBatch motionBatch = new MotionBatch(
                iris26480ProcessingFrames, new ArrayList<>(BurstShakiness), mExposures, selectedResults,
                selectedResults.isEmpty() ? mPreviewCaptureResult
                        : selectedResults.get(selected.get(selected.size() - 1).timestamp),
                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount,
                iris26486ShortSlot, mMotion26575SuperResAtShutter);
        Log.i(TAG, "IRIS_26480_SHORT_BATCH_BOUNDARY"
                + " normalWronskiFrames=" + motionBatch.retainedCount
                + " processingFrames=" + motionBatch.processingFrameCount
                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()
                + " shadowAuxPresent=" + iris26486ShortSlot.shadowAuxSlot.hasFrame()
                + " superResFrozen=" + motionBatch.superResEnabled
                + " shortNeverNormalFusion=true shadowNeverNormalFusion=true");
        /* IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY
         * Snapshot the persistent generation owners before historical Short-A request
         * fields are cleared. These are valid in finalizeMotionZslCapture(); the old
         * shutter-method locals are intentionally not referenced here.
         */
        final boolean iris26507ShortExpected =
                iris26486ShortTicket != null && iris26486ShortTicket.requested;
        final boolean iris26507LongExpected = mMotion26505LongRequested;
        mMotion26480ShortRequested = false;
        mMotion26480ShortRequestCompleted = false;
        mMotion26480ShortResultTimestampNs = 0L;
        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);
        long iris26507FreezeStartNs=System.nanoTime();
        iris26486ShortSlot.freezeExpectedAuxiliaries(
                iris26507ShortExpected, iris26507LongExpected, 80L);
        long iris26507FreezeMs=(System.nanoTime()-iris26507FreezeStartNs)/1_000_000L;
        Log.i(TAG,"IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY"
                +" shortExpected="+iris26507ShortExpected
                +" shortPresent="+iris26486ShortSlot.hasFrame()
                +" longExpected="+iris26507LongExpected
                +" longPresent="+iris26486ShortSlot.shadowAuxSlot.hasFrame()
                +" freezeWaitMs="+iris26507FreezeMs
                +" timeoutMs=80 lateOffersRejectedBySealedSlot=true shutterWait=false");
        final long iris26486ShotId = mMotionDiagnosticShotId;
        final CameraCharacteristics iris26486Characteristics = mCameraCharacteristics;
        int iris26486Queued = mMotion26486InFlightBatches.incrementAndGet();
        Log.i(TAG, "IRIS_26486_BATCH_ENQUEUED inFlight=" + iris26486Queued
                + " max=" + MOTION_26486_MAX_INFLIGHT_BATCHES
                + " serializedGpuExecutor=true"
                + " ringRefillsDuringProcessing=true"
                + " shutterEligibleWhenInFlightZero=true");
        /* IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH */
        mZslCapturing = false;
        burst = false;
        mState = STATE_PREVIEW;
        processExecutor.execute(() -> {
            try {
                mBackgroundHandler.post(this::unlockFocus);
                MotionMetrics.begin(
                        motionBatch.candidateCount,
                        motionBatch.retainedCount,
                        motionBatch.gyro
                );
                iris26486ImageSaver.runMotionRaw(iris26486Characteristics, motionBatch);
            } catch (Exception e) {
                com.particlesdevs.photoncamera.util.MotionTrace.error(
                        iris26486ShotId,
                        "CAPTURE_OR_PROCESSING",
                        e);
                Log.e(TAG, "ZSL runRaw full exception: "
                        + Log.getStackTraceString(e));
                String message = e.getClass().getSimpleName()
                        + ": " + String.valueOf(e.getLocalizedMessage());
                cameraEventsListener.onProcessingError(message);
            } finally {
                com.particlesdevs.photoncamera.util.MotionTrace.finish(
                        iris26486ShotId,
                        "FINALLY",
                        "mZslCapturing=" + mZslCapturing
                                + " burst=" + burst
                                + " state=" + mState);
                // Do not mutate mZslCapturing/burst/mState here: a newer Motion
                // acquisition may already own those fields.
                int iris26486Remaining = mMotion26486InFlightBatches.decrementAndGet();
                if (iris26486Remaining < 0) {
                    mMotion26486InFlightBatches.set(0);
                    iris26486Remaining = 0;
                }
                Log.i(TAG, "IRIS_26486_BATCH_FINISHED inFlight=" + iris26486Remaining);
                if (iris26486ShortTicket != null && iris26486ShortTicket.slot.isSealed()) {
                    iris26486ShortTicket.closeStaged();
                    clearMotion26490CaptureShortTicket(iris26486ShortTicket, "batch_finished_slot_sealed");
                }
                /* No SaverImplementation.IMAGE_BUFFER ownership in Motion. */
                mBackgroundHandler.post(this::unlockFocus);
                if (iris26486Remaining == 0) {
                    try {
                        cameraEventsListener.onProcessingFinished(
                                "Motion processing ended");
                    } catch (Exception cleanupError) {
                        Log.e(TAG, "Motion shutter cleanup callback failed: "
                                + Log.getStackTraceString(cleanupError));
                    }
                }
            }
        });
    }

    private void captureStillPicture() {
        final CameraMode iris26555Mode = PhotonCamera.getSettings().selectedMode;
        if (!mIris26555RawStreamAvailable
                && (iris26555Mode == CameraMode.MOTION || iris26555Mode == CameraMode.NIGHT)) {
            Log.w(TAG, "IRIS_26555_RAW_MODE_UNAVAILABLE_INTERNAL mode=" + iris26555Mode
                    + " captureRejected=true");
            showToast("RAW capture is not supported by this camera");
            return;
        }
        if (iris26555Mode == CameraMode.MOTION && mIris26555RawStreamAvailable
                && (iris26555PreviewOnlyRecoveryActive() || !iris26555MotionZslReady())) {
            Log.w(TAG, "IRIS_26555_MOTION_CAPTURE_NOT_READY_INTERNAL recoveryStage="
                    + mIris26555PreviewRecoveryStage + " captureRejected=true");
            showToast("Motion RAW buffer is still preparing");
            return;
        }
        if (iris26555StillCaptureSurfaceOrNull() == null) {
            Log.w(TAG, "IRIS_26555_STILL_TARGET_UNAVAILABLE mode=" + iris26555Mode
                    + " captureRejected=true previewAlive=true");
            showToast("Still capture is not supported by this camera");
            return;
        }
        boolean iris26547NightRequested = false;
        boolean iris26553NightDispatchReserved = false;
        try {
            iris26547NightRequested = PhotonCamera.getSettings().selectedMode == CameraMode.NIGHT;
            if (iris26547NightRequested) {
                if (!reserveIrisNight26553ShutterDispatch()) return;
                iris26553NightDispatchReserved = true;
            }
            if (null == mCameraDevice) {
                return;
            }
            if (isZslMode()) {
                triggerZslCapture();
                return;
            }
            /* IRIS_26540_NIGHT_SHUTTER_SETTINGS_SNAPSHOT */
            final Settings iris26540ShutterSettings = PhotonCamera.getSettings();
            final CameraMode iris26533CaptureMode = iris26540ShutterSettings.selectedMode;
            final float iris26540ExposureCompensation = (float) iris26540ShutterSettings.exposureCompensation;
            final int iris26540RequestedFrames = iris26540ShutterSettings.frameCount;
            final int iris26540SaveRaw = iris26540ShutterSettings.rawSaver;
            final int iris26540AlignAlgorithm = iris26540ShutterSettings.alignAlgorithm;
            final boolean iris26540Aspect169 = iris26540ShutterSettings.aspect169;
            final boolean iris26540EnergySaving = iris26540ShutterSettings.energySaving;
            final boolean iris26540Binning = iris26540ShutterSettings.binning;
            final String iris26540CameraId = iris26540ShutterSettings.mCameraID;
            final boolean iris26540SuperRes = iris26533CaptureMode == CameraMode.NIGHT
                    && PreferenceKeys.isIrisSuperResOn();
            final boolean iris26540Watermark = iris26533CaptureMode == CameraMode.NIGHT
                    && PreferenceKeys.isShowWatermarkOn();
            final IrisMotionSettings.Snapshot iris26540IrisSettings =
                    iris26533CaptureMode == CameraMode.NIGHT
                            ? IrisMotionSettings.exactCamera2NightSnapshot() : null;
            final IrisNightFrameSelector.Plan iris26552NightFramePlan =
                    iris26533CaptureMode == CameraMode.NIGHT
                            ? IrisNightFrameSelector.freezePlan(iris26540RequestedFrames) : null;
            final IrisNightExposureSelector.Plan iris26540NightPlan =
                    iris26533CaptureMode == CameraMode.NIGHT
                            ? IrisNightExposureSelector.freezePlan(
                                    this, mCameraCharacteristics,
                                    iris26540ExposureCompensation,
                                    PhotonCamera.getGyro() != null && PhotonCamera.getGyro().getTripod(),
                                    PhotonCamera.getGyro() == null ? 0 : PhotonCamera.getGyro().getFilteredShakiness(),
                                    mPreviewCaptureResult, iris26552NightFramePlan.longFrames > 0)
                            : null;
            if (iris26533CaptureMode == CameraMode.NIGHT) {
                if (isZslMode()) throw new IllegalStateException("26541 Night must never enter Motion ZSL");
                Log.i(TAG, "IRIS_26552_NIGHT_FRESH_CAPTURE_CONTRACT"
                        + " zsl=false motionRing=false preShutterRaw=false shutterTriggeredFreshRaw=true"
                        + " requestedPreference=" + iris26540RequestedFrames
                        + " totalRequested=" + iris26552NightFramePlan.totalFrames
                        + " shortRequested=" + iris26552NightFramePlan.shortFrames
                        + " longRequested=" + iris26552NightFramePlan.longFrames);
            }
            // This is the CaptureRequest.Builder that we use to take a picture.
            final CaptureRequest.Builder captureBuilder;
            if(iris26533CaptureMode == CameraMode.RAWVIDEO) {
                captureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
                captureBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, getSelectedFpsRange());
            } else {
                captureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            }
            float focus = mFocus;
            double frametime = iris26540NightPlan != null
                    ? ExposureIndex.time2sec(iris26540NightPlan.exposureNs)
                    : ExposureIndex.time2sec(IsoExpoSelector.GenerateExpoPair(-1, this).exposure);
            //this.mCaptureSession.stopRepeating();
            if(isDualSession) {
                if (mTargetFormat != mPreviewTargetFormat)
                    captureBuilder.addTarget(mImageReaderRaw.getSurface());
                else
                    captureBuilder.addTarget(mImageReaderPreview.getSurface());
            } else {
                captureBuilder.addTarget(mImageReaderRaw.getSurface());
                /* IRIS_26546_NIGHT_PREVIEW_SURFACE_ISOLATION
                 * Night RAW still requests must never drive the repeating preview surface.
                 * The final 3 long (+2 EV) frames previously made the viewfinder brighten
                 * and stall near 12/15 even though RAW capture itself was healthy.
                 */
                final boolean iris26546AddPreviewTarget = iris26533CaptureMode != CameraMode.NIGHT
                        && (frametime > 0.06 || iris26533CaptureMode == CameraMode.RAWVIDEO
                        || iris26533CaptureMode == CameraMode.UNLIMITED || !IsoExpoSelector.HDR);
                if (iris26546AddPreviewTarget) captureBuilder.addTarget(surface);
                else if (iris26533CaptureMode == CameraMode.NIGHT)
                    Log.i(TAG, "IRIS_26546_NIGHT_PREVIEW_SURFACE_ISOLATED stillTarget=false repeatingPreviewIndependent=true");
            }
            if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.applyEnergySaving();
            else Log.i(TAG, "IRIS_26540_NIGHT_BYPASS photonApplyEnergySaving=true");
            cameraRotation = PhotonCamera.getGravity().getCameraRotation(mSensorOrientation);

            //captureBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
            //setCaptureAEMode(captureBuilder);
            if (mFlashed) captureBuilder.set(FLASH_MODE, FLASH_MODE_TORCH);
            Log.d(TAG, "Focus:" + focus);
            captureBuilder.set(CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER, CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER_CANCEL);
            int[] stabilizationModes = mCameraCharacteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION);
            if (stabilizationModes != null && stabilizationModes.length > 1) {
                Log.d(TAG, "LENS_OPTICAL_STABILIZATION_MODE");
//                captureBuilder.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE, CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_OFF);//Fix ois bugs for preview and burst
                captureBuilder.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE, CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_ON);//Fix ois bugs for preview and burst
            }
            for (int i = 0; i < 3; i++) {
                Log.d(TAG, "Temperature:" + mPreviewTemp[i]);
            }
            Log.d(TAG, "CaptureBuilderStarted!");
            //setAutoFlash(captureBuilder);
            //int rotation = Interface.getGravity().getCameraRotation();//activity.getWindowManager().getDefaultDisplay().getRotation();
            captureBuilder.set(CaptureRequest.JPEG_ORIENTATION, PhotonCamera.getGravity().getCameraRotation(mSensorOrientation));
            VendorTagUtils.builderSessionApply(captureBuilder, true, useMaximumResolutionKey, physicalID);
            try {
                captureBuilder.set(CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE, CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE_ON);
            } catch (Exception e) {
                Log.d(TAG, "Failed to set LENS_SHADING_MAP_MODE_ON:" + Log.getStackTraceString(e));
            }

            captures = new ArrayList<>();
            BurstShakiness = new ArrayList<>();
            mExposures = new HashMap<>();
            if (iris26533CaptureMode != CameraMode.NIGHT) SaverImplementation.IMAGE_BUFFER.clear();

            int frameCount = iris26533CaptureMode == CameraMode.NIGHT
                    ? iris26552NightFramePlan.totalFrames
                    : FrameNumberSelector.getFrames();
            if (iris26533CaptureMode == CameraMode.NIGHT) {
                prepareIrisNight26540CaptureState(iris26552NightFramePlan, iris26540SaveRaw,
                        iris26540SuperRes, iris26540Aspect169, iris26540EnergySaving,
                        iris26540Watermark, iris26540Binning, iris26540CameraId,
                        iris26540IrisSettings, mCameraCharacteristics, cameraRotation);
                releaseIrisNight26553ShutterDispatch("capture_state_active");
                iris26553NightDispatchReserved = false;
            }
            //if (frameCount == 1) frameCount++;
            cameraEventsListener.onFrameCountSet(frameCount);
            Log.d(TAG, "HDRFact1:" + paramController.isManualMode() + " HDRFact2:" + iris26540AlignAlgorithm);
            //IsoExpoSelector.HDR = (!manualParamModel.isManualMode()) && (PhotonCamera.getSettings().alignAlgorithm == 0);
            //IsoExpoSelector.HDR = (PhotonCamera.getSettings().alignAlgorithm == 1);
            if (iris26533CaptureMode != CameraMode.NIGHT) {
                Log.d(TAG, "HDR:" + IsoExpoSelector.HDR);
            } else {
                Log.i(TAG, "IRIS_26540_NIGHT_NO_PHOTON_HDR_STATE_READ=true");
            }
            Object mode = mPreviewRequestBuilder.get(CONTROL_AF_MODE);
            if(mode != null && (int) mode != CaptureRequest.CONTROL_AF_MODE_AUTO
                    || PreferenceKeys.getAfMode() == CaptureRequest.CONTROL_AF_MODE_AUTO
                    && iris26533CaptureMode != CameraMode.RAWVIDEO) {
                captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_AUTO);
                captureBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
            }
            //captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_EDOF);
            //if ((!(focus == 0.0 && Build.BRAND.equalsIgnoreCase("samsung")))) {
                MeteringRectangle rectaf = new MeteringRectangle(0, 0, 0, 0, 0);
                //captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CONTROL_AF_MODE_OFF);
                //captureBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CONTROL_AF_TRIGGER_CANCEL);
                //captureBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, focus);
                /*if(!mTouchFocus.isTouchFocus)
                    captureBuilder.set(CaptureRequest.CONTROL_AF_REGIONS, new MeteringRectangle[]{rectaf});
                else {
                    captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_AUTO);
                    captureBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
                    //captureBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, mFocus);
                }
                if (paramController.FOCUS != -1){
                    captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
                    captureBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, paramController.FOCUS);
                }*/
            //}
            /*
            if(!isDualSession){
                captureBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CONTROL_AF_TRIGGER_IDLE);
                captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
                captureBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, focus);
            }*/



            /*mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
            if (focus != 0.0)
                mPreviewRequestBuilder.set(CaptureRequest.LENS_FOCUS_DISTANCE, focus);
            rebuildPreviewBuilder();*/

            if (iris26533CaptureMode != CameraMode.NIGHT)
                IsoExpoSelector.useTripod = PhotonCamera.getGyro().getTripod();
            if (frameCount == -1) {
                for (int i = 0; i < 1; i++) {
                    if(iris26533CaptureMode != CameraMode.RAWVIDEO) {
                        if (iris26533CaptureMode == CameraMode.NIGHT) {
                            IrisNightExposureSelector.applyPlan(captureBuilder, iris26540NightPlan);
                        } else {
                            IsoExpoSelector.setExpo(captureBuilder, i, this);
                        }
                    } else {
                        captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
                        captureBuilder.set(CaptureRequest.CONTROL_AE_MODE, mPreviewAEMode);
                    }
                    captures.add(captureBuilder.build());
                }
            } else {
                long[] times = new long[frameCount];
                for (int i = 0; i < frameCount; i++) {
                    if (iris26533CaptureMode == CameraMode.NIGHT) {
                        if (frameCount != iris26552NightFramePlan.totalFrames)
                            throw new IllegalStateException("26552 Night request count drift=" + frameCount
                                    + " frozen=" + iris26552NightFramePlan.totalFrames);
                        if (iris26552NightFramePlan.isShortFrame(i)) {
                            IrisNightExposureSelector.applyShortPlan(captureBuilder, iris26540NightPlan);
                            captureBuilder.setTag(IRIS_26541_NIGHT_SHORT_TAG);
                            times[i] = iris26540NightPlan.shortExposureNs;
                        } else {
                            IrisNightExposureSelector.applyLongPlan(captureBuilder, iris26540NightPlan);
                            captureBuilder.setTag(IRIS_26541_NIGHT_LONG_TAG);
                            times[i] = iris26540NightPlan.longExposureNs;
                        }
                    } else {
                        IsoExpoSelector.setExpo(captureBuilder, i, this);
                        times[i] = IsoExpoSelector.lastSelectedExposure;
                    }
                    CaptureRequest built = captureBuilder.build();
                    captures.add(built);
                    mCaptureRequest = built;
                }
                if (iris26533CaptureMode == CameraMode.NIGHT) {
                    Log.i(TAG, "IRIS_26552_NIGHT_DYNAMIC_REQUESTS"
                            + " short=" + iris26552NightFramePlan.shortFrames
                            + " long=" + iris26552NightFramePlan.longFrames
                            + " total=" + captures.size()
                            + " shortNs=" + iris26540NightPlan.shortExposureNs
                            + " longNs=" + iris26540NightPlan.longExposureNs
                            + " shortIso=" + iris26540NightPlan.shortIso
                            + " longIso=" + iris26540NightPlan.longIso
                            + " longToShortEnergy=" + iris26540NightPlan.longToShortEnergyRatio
                            + " zsl=false");
                    // Built requests retain immutable tags; clear the mutable builder afterwards.
                    captureBuilder.setTag(null);
                }
                PhotonCamera.getGyro().PrepareGyroBurst(times, BurstShakiness);
            }

            //img
            Log.d(TAG, "FrameCount:" + frameCount);
            if (iris26533CaptureMode != CameraMode.NIGHT) {
                mImageSaver = new ImageSaver(cameraEventsListener);
                mImageSaver.setFrameCount(frameCount);
            } else {
                mImageSaver = null;
            }
//            final int[] burstcount = {0, 0, frameCount};
            /*if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                mImageReaderRaw.discardFreeBuffers();
            }*/
            Log.d(TAG, "CaptureStarted!");

            final long[] baseFrameNumber = {0};
            final int[] maxFrameCount = {frameCount};

            cameraEventsListener.onCaptureStillPictureStarted("CaptureStarted!");
            mMeasuredFrameCnt = 0;

            cameraEventsListener.onBurstPrepared(null);
            this.CaptureCallback = new CameraCaptureSession.CaptureCallback() {

                @Override
                public void onCaptureStarted(@NonNull CameraCaptureSession session,
                                             @NonNull CaptureRequest request,
                                             long timestamp,
                                             long frameNumber) {

                    if (baseFrameNumber[0] == 0) {
                        baseFrameNumber[0] = frameNumber;
                        if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CaptureGyroBurst();
                        Log.v("BurstCounter", "CaptureStarted with FirstFrameNumber:" + frameNumber);
                    } else {
                        Log.v("BurstCounter", "CaptureStarted:" + frameNumber);
                    }
                    cameraEventsListener.onFrameCaptureStarted(null);
                    //if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CaptureGyroBurst();
                }

                @Override
                public void onCaptureProgressed(@NonNull CameraCaptureSession session, @NonNull CaptureRequest request,
                                                @NonNull CaptureResult partialResult) {
                    int frameCount = (int) (partialResult.getFrameNumber() - baseFrameNumber[0]);
                    Log.v("BurstCounter", "CaptureProgressed! FrameCount:" + frameCount);
                    if (mCaptureResult == null) {
                        mCaptureResult = partialResult;
                    }
                }

                @Override
                public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                               @NonNull CaptureRequest request,
                                               @NonNull TotalCaptureResult result) {

                    int frameCount = (int) (result.getFrameNumber() - baseFrameNumber[0]);
                    Log.v("BurstCounter", "CaptureCompleted! FrameCount:" + frameCount);
                    Object time = result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Log.d(TAG, "Timestamp:" + time);
                    if (iris26533CaptureMode == CameraMode.NIGHT) {
                        Long irisNightTs = result.get(CaptureResult.SENSOR_TIMESTAMP);
                        Log.i(TAG, "IRIS_26544_NIGHT_CAPTURE_RESULT frameNumber="
                                + result.getFrameNumber() + " timestamp=" + String.valueOf(irisNightTs));
                        if (irisNightTs == null) {
                            Log.e(TAG, "IRIS_26540_NIGHT_RESULT_MISSING_TIMESTAMP frame="
                                    + result.getFrameNumber());
                        } else {
                            TotalCaptureResult previousResult = mIrisNight26540Results.putIfAbsent(irisNightTs, result);
                            CaptureRequest previousRequest = mIrisNight26540Requests.putIfAbsent(irisNightTs, request);
                            if (previousResult != null || previousRequest != null)
                                Log.e(TAG, "IRIS_26540_NIGHT_DUPLICATE_RESULT timestamp=" + irisNightTs);
                        }
                        tryDispatchIrisNight26540();
                    }
                    if (time != null) {
                        // get exposure multiply ISO and exposure time
                        Object isoKey = result.get(CaptureResult.SENSOR_SENSITIVITY);
                        int iso = 100;
                        if (isoKey != null) {
                            iso = (int) isoKey;
                        }
                        Object timeKey = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                        double exposureTime = ExposureIndex.time2sec((long) timeKey);
                        mExposures.put((long) time, exposureTime * iso);
                    }
                    cameraEventsListener.onFrameCaptureCompleted(
                            new TimerFrameCountViewModel.FrameCntTime(frameCount, maxFrameCount[0], frametime));

                    if (onUnlimited && !unlimitedStarted) {
                        mImageSaver.processStart(mCameraCharacteristics, result, request, cameraRotation);
                        unlimitedStarted = true;
                    }
                    //if(frameCount == 0)
                        mCaptureResult = result;
                    if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CaptureGyroBurst();
                }

                @Override
                public void onCaptureSequenceAborted(@NonNull CameraCaptureSession session,
                                                     int sequenceId) {
                    if (iris26533CaptureMode == CameraMode.NIGHT) {
                        burst = false;
                        try { PhotonCamera.getGyro().CompleteSequence(); } catch (Throwable ignored) {}
                        final boolean cleaned = abortIrisNight26547CaptureState(
                                "camera-sequence-aborted:" + sequenceId);
                        if (mBackgroundHandler != null) {
                            mBackgroundHandler.post(() -> {
                                if (!isDualSession) unlockFocus();
                                else createCameraPreviewSession(false);
                            });
                        }
                        Log.e(TAG, "IRIS_26547_NIGHT_SEQUENCE_ABORTED id=" + sequenceId
                                + " cleanup=" + cleaned);
                        cameraEventsListener.onProcessingError("Iris Night capture sequence aborted");
                        return;
                    }
                }

                @Override
                public void onCaptureSequenceCompleted(@NonNull CameraCaptureSession session,
                                                       int sequenceId,
                                                       long lastFrameNumber) {

                    int finalFrameCount = (int) (lastFrameNumber - baseFrameNumber[0]) + 1;
                    Log.v("BurstCounter", "CaptureSequenceCompleted! FrameCount:" + finalFrameCount);
                    Log.d("DefaultSaver", "CaptureSequenceCompleted! FrameCount:" + finalFrameCount);
                    Log.v("BurstCounter", "CaptureSequenceCompleted! LastFrameNumber:" + lastFrameNumber);
                    Log.d(TAG, "SequenceCompleted");
                    mMeasuredFrameCnt = finalFrameCount;
                    cameraEventsListener.onCaptureSequenceCompleted(null);
                    burst = false;
                    //unlockFocus();
                    //Surface texture related
                    //activity.runOnUiThread(() -> UpdateCameraCharacteristics(PhotonCamera.getSettings().mCameraID));
                    if (iris26533CaptureMode == CameraMode.NIGHT) {
                        try { PhotonCamera.getGyro().CompleteSequence(); } catch (Throwable ignored) {}
                        synchronized (mIrisNight26540Lock) {
                            // IRIS_26552_NIGHT_REQUEST_BUDGET_IMMUTABLE_AT_SEQUENCE_END
                            // Keep the shutter-frozen expected budget. The bounded-drain grace may
                            // observe a HAL drop, but IrisNightBatch still exact-validates roles.
                            mIrisNight26540SequenceComplete = true;
                        }
                        Log.processState(TAG, "NIGHT_SEQUENCE_COMPLETE_" + finalFrameCount);
                        Log.critical(TAG, "IRIS_26544_NIGHT_SEQUENCE_COMPLETE frames=" + finalFrameCount);
                        mBackgroundHandler.post(() -> {
                            if (!isDualSession) unlockFocus();
                            else createCameraPreviewSession(false);
                        });
                        Log.i(TAG, "IRIS_26540_NIGHT_SEQUENCE_COMPLETE frames=" + finalFrameCount
                                + " legacySaverWait=false");
                        tryDispatchIrisNight26540();
                        if (mBackgroundHandler != null) {
                            final long iris26554DrainGraceMs = irisNight26554SequenceDrainGraceMs();
                            Log.i(TAG, "IRIS_26554_NIGHT_SEQUENCE_DRAIN_GRACE ms="
                                    + iris26554DrainGraceMs + " exposureAware=true maxMs=5000");
                            mBackgroundHandler.postDelayed(
                                    CaptureController.this::finishIrisNight26544AfterSequenceGrace,
                                    iris26554DrainGraceMs);
                        }
                        return;
                    }
                    if (PhotonCamera.getSettings().selectedMode != CameraMode.UNLIMITED && PhotonCamera.getSettings().selectedMode != CameraMode.RAWVIDEO) {
                        //processExecutor.submit(() -> mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, new ArrayList<>(BurstShakiness), cameraRotation));
                        /*taskResults.removeIf(Future::isDone); //remove already completed results
                        Future<?> result =processExecutor.submit(() -> {
                            while (PhotonCamera.getGyro().capturingNumber < finalFrameCount){
                                try {
                                    Thread.sleep(1);
                                } catch (InterruptedException ignored) {
                                }
                            }
                            if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CompleteGyroBurst();
                            mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, new ArrayList<>(BurstShakiness), cameraRotation);
                        });
                        //Future<?> result = processExecutor.submit(() -> mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, new ArrayList<>(BurstShakiness), cameraRotation));
                        taskResults.add(result);*/
                        processExecutor.execute(() -> {
                            int cnt = 0;
                            //int captureNumber = PhotonCamera.getGyro().capturingNumber;
                            while (PhotonCamera.getGyro().capturingNumber < finalFrameCount || mImageSaver.bufferSize() < finalFrameCount){
                                if(cnt > 1000) {
                                    Log.d(TAG, "GyroBurstTimeout");
                                    break;
                                }
                                try {
                                    Thread.sleep(1);
                                } catch (InterruptedException ignored) {
                                }
                                //if(captureNumber - PhotonCamera.getGyro().capturingNumber != 0)
                                //    cnt = 0;
                                //else
                                    cnt++;
                            }
                            PhotonCamera.getGyro().CompleteSequence();
                            mBackgroundHandler.post(() -> {
                                if (!isDualSession)
                                    unlockFocus();
                                else
                                    createCameraPreviewSession(false);
                            });
                            try{
                            if(mImageSaver.bufferSize() == 0){
                                return;
                            }
                            mImageSaver.updateFrameCount(mImageSaver.bufferSize());
                            if (mImageSaver.bufferSize() != 0)
                                mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, mCaptureRequest, new ArrayList<>(BurstShakiness), cameraRotation, mExposures);
                            } catch (Exception e){
                                Log.e(TAG, "runRaw:"+Log.getStackTraceString(e));
                                cameraEventsListener.onProcessingError(e.getLocalizedMessage());
                            }
                        });
                        /*mBackgroundHandler.post(() -> {
                                    while (PhotonCamera.getGyro().capturingNumber < finalFrameCount){
                                        try {
                                            Thread.sleep(1);
                                        } catch (InterruptedException ignored) {
                                        }
                                    }
                                    if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CompleteGyroBurst();
                                    mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, new ArrayList<>(BurstShakiness), cameraRotation);
                                });*/
                        //mBackgroundHandler.post(() -> {mImageSaver.runRaw(mCameraCharacteristics, mCaptureResult, new ArrayList<>(BurstShakiness), cameraRotation);});
                    }
                }
            };
            //mCaptureSession.setRepeatingBurst(captures, CaptureCallback, null);
            burst = true;
            if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.ApplyBurst();
            else Log.i(TAG, "IRIS_26540_NIGHT_BYPASS photonApplyBurst=true");
            if (isDualSession)
                createCameraPreviewSession(true);
            else {
            mCaptureSession.stopRepeating();
            mCaptureSession.abortCaptures();
                switch (iris26533CaptureMode) {
                    case UNLIMITED:
                        mCaptureSession.setRepeatingBurst(captures, CaptureCallback, mBackgroundHandler);
                        break;
                    case RAWVIDEO:
                        mCaptureSession.setRepeatingRequest(captures.get(0), CaptureCallback, mBackgroundHandler);
                        break;
                    case NIGHT:
                    case PHOTO:
                    case MOTION:
                        mCaptureSession.captureBurst(captures, CaptureCallback, mBackgroundHandler);
                        break;
                }
            }
        } catch (CameraAccessException e) {
            abortIrisNight26547CaptureState("CameraAccessException");
            Log.e(TAG, Log.getStackTraceString(e));
        } catch (RuntimeException e) {
            if (iris26547NightRequested) {
                final boolean cleaned = abortIrisNight26547CaptureState(
                        "RuntimeException:" + e.getClass().getSimpleName());
                if (!cleaned) {
                    CaptureController.isProcessing = false;
                    cleanupIrisNight26544SpoolCache();
                }
                if (mBackgroundHandler != null) {
                    mBackgroundHandler.post(() -> {
                        if (!isDualSession) unlockFocus();
                        else createCameraPreviewSession(false);
                    });
                }
                Log.e(TAG, "IRIS_26547_NIGHT_CAPTURE_RUNTIME_FAILURE cleanup=" + cleaned, e);
                cameraEventsListener.onProcessingError("Iris Night capture: "
                        + e.getClass().getSimpleName());
                return;
            }
            throw e;
        } finally {
            if (iris26553NightDispatchReserved)
                releaseIrisNight26553ShutterDispatch("captureStillPicture_exit_before_active");
        }
    }

    public void abortCaptures() {
        try {
            mCaptureSession.abortCaptures();
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
    }

    public void reset3Aparams() {
        setAEMode(mPreviewRequestBuilder, PreferenceKeys.getAeMode());
        setAFMode(mPreviewRequestBuilder, PreferenceKeys.getAfMode());
        rebuildPreviewBuilder();
    }

    public void setPreviewAEModeRebuild(int aeMode) {
        setAEMode(mPreviewRequestBuilder, aeMode);
        rebuildPreviewBuilder();
    }

    public void applyFpsRange() {
        if (mPreviewRequestBuilder == null) return;
        PhotonCamera.getSettings().fpsMode = PreferenceKeys.getFpsMode();
        mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, getSelectedFpsRange());
        rebuildPreviewBuilder();
    }

    public void resetPreviewAEMode() {
        setAEMode(mPreviewRequestBuilder, PreferenceKeys.getAeMode());
    }

    /**
     * @param requestBuilder CaptureRequest.Builder
     * @param aeMode         possible values = 0, 1, 2, 3
     */
    private void setAEMode(CaptureRequest.Builder requestBuilder, int aeMode) {
        if (requestBuilder != null) {
            if (mFlashSupported) {
                requestBuilder.set(CONTROL_AE_MODE, Math.max(aeMode, 1));//here AE_MODE will never be OFF(0)

                //if PreferenceKeys.getAeMode() returns zero, we set the FLASH_MODE_TORCH instead of setting AE_MODE to OFF(0)
                requestBuilder.set(CaptureRequest.FLASH_MODE,
                        aeMode == 0 ? CaptureRequest.FLASH_MODE_TORCH : CaptureRequest.FLASH_MODE_OFF);
            } else {
                requestBuilder.set(CONTROL_AE_MODE, CONTROL_AE_MODE_ON);
                requestBuilder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF);
            }
        }
    }

    private void setAFMode(CaptureRequest.Builder builder, int afMode) {
        if (builder != null) {
            builder.set(CaptureRequest.CONTROL_AF_REGIONS, builder.get(CONTROL_AF_REGIONS));
            builder.set(CaptureRequest.CONTROL_AE_REGIONS, builder.get(CONTROL_AE_REGIONS));
            builder.set(CaptureRequest.CONTROL_AF_MODE, afMode);
        }
    }

    /**
     * Start the timer for the pre-capture sequence.
     * <p/>
     * Call this only with { #mCameraStateLock} held.
     */
    private void startTimerLocked() {
        mCaptureTimer = SystemClock.elapsedRealtime();
    }

    /**
     * Check if the timer for the pre-capture sequence has been hit.
     * <p/>
     * Call this only with { #mCameraStateLock} held.
     *
     * @return true if the timeout occurred.
     */
    private boolean hitTimeoutLocked() {
        return (SystemClock.elapsedRealtime() - mCaptureTimer) > PRECAPTURE_TIMEOUT_MS;
    }

    public void callUnlimitedEnd() {
        onUnlimited = false;
        //mImageSaver.unlimitedEnd();
        mBackgroundHandler.post(() -> mImageSaver.processEnd());
        abortCaptures();
        createCameraPreviewSession(false);
        unlimitedStarted = false;
    }

    public void callUnlimitedStart() {
        onUnlimited = true;
        takePicture();
    }

    public void VideoEnd() {
        mIsRecordingVideo = false;
        stopRecordingVideo();
    }

    public void VideoStart() {
        mIsRecordingVideo = true;
        createCameraPreviewSession(false);
    }

    private CamcorderProfile resolveVideoProfile(int cameraId, String resolution) {
        int[] qualities;
        switch (resolution) {
            case "3840x2160": qualities = new int[]{CamcorderProfile.QUALITY_2160P, CamcorderProfile.QUALITY_1080P, CamcorderProfile.QUALITY_720P}; break;
            case "1280x720":  qualities = new int[]{CamcorderProfile.QUALITY_720P,  CamcorderProfile.QUALITY_1080P, CamcorderProfile.QUALITY_2160P}; break;
            default:          qualities = new int[]{CamcorderProfile.QUALITY_1080P, CamcorderProfile.QUALITY_720P,  CamcorderProfile.QUALITY_2160P}; break;
        }
        for (int q : qualities) {
            if (CamcorderProfile.hasProfile(cameraId, q)) {
                return CamcorderProfile.get(cameraId, q);
            }
        }
        return CamcorderProfile.get(cameraId, CamcorderProfile.QUALITY_HIGH);
    }

    private void setUpMediaRecorder() {
        mMediaRecorder.reset();
        mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
        mMediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
        mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
        String cameraIdStr = PhotonCamera.getSettings().mCameraID;
        if (cameraIdStr.contains("-")) cameraIdStr = cameraIdStr.split("-")[0];
        int cameraIdInt;
        try { cameraIdInt = Integer.parseInt(cameraIdStr); } catch (NumberFormatException e) { cameraIdInt = 0; }
        CamcorderProfile profile = resolveVideoProfile(cameraIdInt, PreferenceKeys.getVideoResolution());
        mMediaRecorder.setVideoFrameRate(profile.videoFrameRate);
        mMediaRecorder.setVideoSize(profile.videoFrameWidth, profile.videoFrameHeight);
        mMediaRecorder.setVideoEncodingBitRate(profile.videoBitRate);
        mMediaRecorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264);
        mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
        mMediaRecorder.setAudioEncodingBitRate(profile.audioBitRate);
        mMediaRecorder.setAudioSamplingRate(profile.audioSampleRate);
        mMediaRecorder.setOnInfoListener(this);
        mMediaRecorder.setOrientationHint(PhotonCamera.getGravity().getCameraRotation(mSensorOrientation));
        Date currentDate = new Date();
        DateFormat dateFormat = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US);
        String dateText = dateFormat.format(currentDate);
        File dir = new File(Environment.getExternalStorageDirectory() + "//DCIM//Camera//");
        vid = new File(dir.getAbsolutePath(), "VID_" + dateText + ".mp4");
        try {
            vid.createNewFile();
        } catch (IOException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        }
        mMediaRecorder.setOutputFile(vid.getAbsolutePath());
        try {
            mMediaRecorder.prepare();
            Log.d(TAG, "video record start");

        } catch (Exception e) {
            Log.d(TAG, "video record failed");
        }
    }

    private void stopRecordingVideo() {
        mIsRecordingVideo = false;

        try {
            mMediaRecorder.stop();
        } catch (Exception stopFailure) {
            Log.d(TAG, "Failed to stop recording " + Log.getStackTraceString(stopFailure));
            Toast.makeText(activity.getApplicationContext(), "Failed to stop recording", Toast.LENGTH_SHORT).show();
            if (vid.delete()) {
                Toast.makeText(activity.getApplicationContext(), "Video file has been removed", Toast.LENGTH_SHORT).show();
            }
        }
        mMediaRecorder.reset();
        cameraEventsListener.onRequestTriggerMediaScanner(Uri.fromFile(vid));
        createCameraPreviewSession(false);
    }

    @Override
    public void onInfo(MediaRecorder mr, int what, int extra) {
        if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED) {
            Log.v(TAG, "Maximum Duration Reached, Call stopRecordingVideo()");
            stopRecordingVideo();
        }
    }

    private void mul(Rect in, double k) {
        in.bottom *= k;
        in.left *= k;
        in.right *= k;
        in.top *= k;
    }

    @TestOnly
    private static void mulForTest(Rect in, double k) {
        in.bottom *= k;
        in.left *= k;
        in.right *= k;
        in.top *= k;
    }

    @Override
    protected void finalize() throws Throwable {
        activity = null;
        cameraEventsListener = null;
        mCameraManager = null;
        mTextureView = null;
        super.finalize();
    }
    public void resumeCamera() {
        if(PhotonCamera.getSettings().previewFormat != 0) {
            mPreviewTargetFormat = PhotonCamera.getSettings().previewFormat;
        } else {
            mPreviewTargetFormat = ImageFormat.JPEG;
        }
        processExecutor.execute(() -> {
            if (mTextureView == null)
                mTextureView = new GLPreview(activity);
            if (mTextureView.isAvailable()) {
                mIris26548ConsecutiveHealthRecoveries = 0;
                iris26548BeginCameraHealthGeneration("resume_surface_already_available");
                Log.d(TAG,"ID:"+mCameraCharacteristicsMap.get(physicalID));
                Size optimal = getPreviewOutputSize(getSafeDisplay(),
                        mCameraCharacteristicsMap.get(physicalID),
                        PhotonCamera.getSettings().selectedMode);
                openCamera(optimal.getWidth(), optimal.getHeight());
            } else {
                mTextureView.setSurfaceTextureListener(mSurfaceTextureListener);
            }
        });
    }

    /**
     * Compares two {@code Size}s based on their areas.
     */
    static class CompareSizesByArea implements Comparator<Size> {

        @Override
        public int compare(Size lhs, Size rhs) {
            // We cast here to ensure the multiplications won't overflow
            return Long.signum((long) lhs.getWidth() * lhs.getHeight() -
                    (long) rhs.getWidth() * rhs.getHeight());
        }

    }

    public static class CameraProperties {
        private final Float minFocal = mCameraCharacteristics.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE);
        private final Float maxFocal = mCameraCharacteristics.get(CameraCharacteristics.LENS_INFO_HYPERFOCAL_DISTANCE);
        public Range<Float> focusRange = (!(minFocal == null || maxFocal == null || minFocal == 0.0f)) ? new Range<>(Math.min(minFocal, maxFocal), Math.max(minFocal, maxFocal)) : null;
        public Range<Integer> isoRange = new Range<>(IsoExpoSelector.getISOLOWExt(), IsoExpoSelector.getISOHIGHExt());
        public Range<Long> expRange = new Range<>(IsoExpoSelector.getEXPLOW(), IsoExpoSelector.getEXPHIGH());
        private final float evStep = mCameraCharacteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP).floatValue();
        public Range<Float> evRange = new Range<>((mCameraCharacteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_RANGE).getLower() * evStep),
                (mCameraCharacteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_RANGE).getUpper() * evStep));

        public CameraProperties() {
            logIt();
        }

        private void logIt() {
            String lens = PhotonCamera.getSettings().mCameraID;
            Log.d(TAG, "focusRange(" + lens + ") : " + (focusRange == null ? "Fixed [" + maxFocal + "]" : focusRange.toString()));
            Log.d(TAG, "isoRange(" + lens + ") : " + isoRange.toString());
            Log.d(TAG, "expRange(" + lens + ") : " + expRange.toString());
            Log.d(TAG, "evCompRange(" + lens + ") : " + evRange.toString());
        }

    }
}