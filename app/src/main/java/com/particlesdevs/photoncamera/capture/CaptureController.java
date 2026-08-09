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
import com.particlesdevs.photoncamera.control.TouchFocus;
import com.particlesdevs.photoncamera.debugclient.DebugSender;
import com.particlesdevs.photoncamera.manual.ParamController;
import com.particlesdevs.photoncamera.processing.ImageSaver;
import com.particlesdevs.photoncamera.processing.parameters.ExposureIndex;
import com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
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
                if (mZslCapturing && !mMotionTopUpActive) {
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
                    int maxFrames = Math.min(PhotonCamera.getSettings().frameCount, 37);
                    while (mZslRingBuffer.size() > maxFrames) {
                        Image old = mZslRingBuffer.pollFirst();
                        if (old != null) old.close();
                    }
                }
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
    private final CameraDevice.StateCallback mStateCallback = new CameraDevice.StateCallback() {

        @Override
        public void onOpened(@NonNull CameraDevice cameraDevice) {
            // This method is called when the camera is opened.  We start camera preview here.
            mCameraOpenCloseLock.release();
            mCameraDevice = cameraDevice;
            mImageSaver = new ImageSaver(cameraEventsListener);
            createCameraPreviewSession(false);
        }

        @Override
        public void onDisconnected(@NonNull CameraDevice cameraDevice) {
            mCameraOpenCloseLock.release();
            cameraDevice.close();
            mCameraDevice = null;
        }

        @Override
        public void onError(@NonNull CameraDevice cameraDevice, int error) {
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
                String curID = PhotonCamera.getSettings().mCameraID;
                if(curID.contains("-")){
                    logicalID = curID.split("-")[0];
                    physicalID = curID.split("-")[1];
                } else {
                    logicalID = curID;
                    physicalID = curID;
                }
                
                Log.d(TAG, "ID:" + mCameraCharacteristicsMap.get(physicalID));
                // list available characteristics ids
                for (String id : mCameraCharacteristicsMap.keySet()) {
                    Log.d(TAG, "Available camera ID: " + id);
                }
                CameraCharacteristics chars = mCameraCharacteristicsMap.get(physicalID);
                if (chars == null) {
                    Log.e(TAG, "No characteristics for physicalID=" + physicalID
                            + " (mCameraID=" + PhotonCamera.getSettings().mCameraID + "). Falling back to first available.");
                    if (!mCameraCharacteristicsMap.isEmpty()) {
                        Map.Entry<String, CameraCharacteristics> first = mCameraCharacteristicsMap.entrySet().iterator().next();
                        physicalID = first.getKey();
                        logicalID = physicalID;
                        PhotonCamera.getSettings().mCameraID = physicalID;
                        chars = first.getValue();
                    } else {
                        showToast("No cameras available");
                        return;
                    }
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
            String curID = PhotonCamera.getSettings().mCameraID;
            if(curID.contains("-")) {
                logicalID = curID.split("-")[0];
                physicalID = curID.split("-")[1];
            } else {
                logicalID = curID;
                physicalID = logicalID;
            }
            
            UpdateCameraCharacteristics(physicalID);
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
                if (!isProcessing) {
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

    /* IRIS_26382_CAPTURE_STATE_HANDOFF */
    private volatile long mMotion26382LastOpportunityCeilingNs = 0L;
    private volatile float mMotion26382LastRawNeed = 0.0f;

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

        } catch (Throwable throwable) {
            Log.w(
                    TAG,
                    "IRIS_26380 sparse RAW signal sampling skipped: "
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

    public void rebuildPreviewBuilder() {
        if(burst) return;
        try {
//            mCaptureSession.stopRepeating();
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
            for (int capability : capabilities) {
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
                if (!isProcessing) {
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
        String curID = PhotonCamera.getSettings().mCameraID;
        if(curID.contains("-")) {
            logicalID = curID.split("-")[0];
            physicalID = curID.split("-")[1];
        } else {
            logicalID = curID;
            physicalID = logicalID;
        }
        
        try {
            if (!mCameraOpenCloseLock.tryAcquire(2500, TimeUnit.MILLISECONDS)) {
                throw new RuntimeException("Time out waiting to lock camera opening.");
            }
            this.mCameraManager.openCamera(logicalID, mStateCallback, mBackgroundHandler);
        } catch (CameraAccessException e) {
            Log.e(TAG, Log.getStackTraceString(e));
        } catch (InterruptedException e) {
            throw new RuntimeException("Interrupted while trying to restart camera.", e);
        }
        //stopBackgroundThread();
        //UpdateCameraCharacteristics(physicalID);
        startBackgroundThread();

        Size optimal = getPreviewOutputSize(getSafeDisplay(), mCameraCharacteristics, CameraFragment.mSelectedMode);

        setUpCameraOutputs(optimal.getWidth(), optimal.getHeight());
        configureTransform(optimal.getWidth(), optimal.getHeight());
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
                physicalID = PhotonCamera.getSettings().mCameraID;
                logicalID = PhotonCamera.getSettings().mCameraID;
                // Split x-y, x - logical, y - physical
                if(PhotonCamera.getSettings().mCameraID.contains("-")){
                    String[] ids = PhotonCamera.getSettings().mCameraID.split("-");
                    logicalID = ids[0];
                    physicalID = ids[1];
                    //isDualSession = true;
                }
                
                this.mCameraManager.openCamera(logicalID, mStateCallback, mBackgroundHandler);
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

        Size preview = getCameraOutputSize(map.getOutputSizes(mPreviewTargetFormat));

        int maxjpg = 3;
        if (mTargetFormat == mPreviewTargetFormat && isDualSession)
            maxjpg = PhotonCamera.getSettings().frameCount + 3;
        if (isZslMode())
            maxjpg = Math.min(PhotonCamera.getSettings().frameCount + 3, 40);
        Size target = getCameraOutputSize(allTargets.toArray(new Size[0]), preview);
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

        if(mImageReaderRaw != null)
            mImageReaderRaw.close();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && (PhotonCamera.getSettings().QuadBayer
                || !(Build.BRAND.equalsIgnoreCase("oppo")
                || Build.BRAND.equalsIgnoreCase("vivo")
                || Build.BRAND.equalsIgnoreCase("oneplus")
                || Build.BRAND.equalsIgnoreCase("realme")
                || Build.BRAND.equalsIgnoreCase("iqoo")
                || Build.BRAND.equalsIgnoreCase("nothing")
        ))
        ) {
            mImageReaderRaw = ImageReader.newInstance(target.getWidth(), target.getHeight(), mTargetFormat, maxjpg, 0x00100000);
        } else {
            mImageReaderRaw = ImageReader.newInstance(target.getWidth(), target.getHeight(), mTargetFormat, maxjpg);
        }
        mImageReaderRaw.setOnImageAvailableListener(mOnRawImageAvailableListener, mBackgroundHandler);
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
            ArrayList<OutputConfiguration> outputConfigurations = new ArrayList<>();
            for (Surface surfacei : surfaces) {
                var config = new OutputConfiguration(surfacei);
                if(!Objects.equals(physicalID, logicalID) && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P){
                    config.setPhysicalCameraId(physicalID);
                }
                outputConfigurations.add(config);
            }

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
                    showToast(activity.getString(R.string.session_on_configure_failed));
                    Log.d(TAG, "CameraCaptureSession onConfigureFailed()");
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

    @NotNull
    private List<Surface> configureSurfaces(boolean isBurstSession) {
        List<Surface> surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface());
        if (isDualSession) {
            if (isBurstSession) {
                surfaces = Arrays.asList(mImageReaderPreview.getSurface(), mImageReaderRaw.getSurface());
            }
            if (mTargetFormat == mPreviewTargetFormat) {
                surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface());
            }
        } else {
           if(Build.BRAND.equalsIgnoreCase("samsung")){
                surfaces = Arrays.asList(surface, mImageReaderRaw.getSurface());
            } else {
                surfaces = Arrays.asList(surface, mImageReaderPreview.getSurface(), mImageReaderRaw.getSurface());
            }
           if(PhotonCamera.getSettings().previewFormat == 0) {
                surfaces = Arrays.asList(surface, mImageReaderRaw.getSurface());
           }
        }
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
        if (isZslMode()) {
            mPreviewRequestBuilder.addTarget(mImageReaderRaw.getSurface());
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

    private TotalCaptureResult findNearestZslResult(long timestamp) {
        synchronized (mZslBufferLock) {
            TotalCaptureResult exact = mZslResultMap.get(timestamp);
            if (exact != null) return exact;
            long bestDelta = Long.MAX_VALUE;
            TotalCaptureResult best = null;
            for (Map.Entry<Long, TotalCaptureResult> entry : mZslResultMap.entrySet()) {
                long delta = Math.abs(entry.getKey() - timestamp);
                if (delta < bestDelta) {
                    bestDelta = delta;
                    best = entry.getValue();
                }
            }
            return bestDelta <= 40_000_000L ? best : null;
        }
    }

    private void triggerZslCapture() {
        if (mZslCapturing || CaptureController.isProcessing) {
            Log.w(TAG, "ZSL: capture already in progress, ignoring");
            return;
        }

        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;
        mMotionTopUpStartMs = android.os.SystemClock.elapsedRealtime();
        mMotionTopUpTargetFrames = Math.max(
                1,
                Math.min(PhotonCamera.getSettings().frameCount, 37));
        mMotionTopUpMinimumFrames = Math.min(
                mMotionTopUpTargetFrames,
                Math.max(6, Math.min(8, mMotionTopUpTargetFrames)));

        int buffered;
        synchronized (mZslBufferLock) {
            buffered = mZslRingBuffer.size();
        }

        mMotionDiagnosticShotId =
                com.particlesdevs.photoncamera.util.MotionTrace.beginShot(
                        physicalID,
                        mMotionTopUpTargetFrames,
                        buffered,
                        mMotionManualLadderActive,
                        mMotionUnifiedGeneration);

        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                "TOP_UP_BEGIN",
                "buffered=" + buffered
                        + " target=" + mMotionTopUpTargetFrames
                        + " minimum=" + mMotionTopUpMinimumFrames
                        + " timeoutMs=" + MOTION_TOP_UP_TIMEOUT_MS);

        pollMotionTopUp();
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

    private boolean motionExposurePairMatches(
            TotalCaptureResult first,
            TotalCaptureResult second) {
        if (first == null || second == null) return false;

        Long firstExposure =
                first.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer firstIso =
                first.get(CaptureResult.SENSOR_SENSITIVITY);
        Long secondExposure =
                second.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer secondIso =
                second.get(CaptureResult.SENSOR_SENSITIVITY);

        if (firstExposure == null || firstIso == null
                || secondExposure == null || secondIso == null
                || firstExposure <= 0L || secondExposure <= 0L
                || firstIso <= 0 || secondIso <= 0) {
            return false;
        }

        long exposureTolerance =
                iris26378MotionExposureToleranceNs(
                        firstExposure,
                        secondExposure);

        int isoReference =
                Math.max(firstIso, secondIso);
        int isoTolerance =
                Math.max(2, isoReference / 10);

        return Math.abs(firstExposure - secondExposure)
                        <= exposureTolerance
                && Math.abs(firstIso - secondIso)
                        <= isoTolerance;
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

        if (iris26379TargetReady
                || iris26383TimeoutMinimumReady) {
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
        int frameCount = mMotionTopUpTargetFrames > 0
                ? mMotionTopUpTargetFrames
                : Math.max(
                        1,
                        Math.min(PhotonCamera.getSettings().frameCount, 37));
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
            recoverMotionCaptureAfterEarlyExit(
                    "VALID_BUFFER_NOT_READY",
                    "Motion buffer preparing");
            return;
        }

        int take = Math.min(rawImages.size(), frameCount);
        int skip = rawImages.size() - take;
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

        TotalCaptureResult bestExposureGroup =
                findBestMotionExposureGroup(
                        rawImages,
                        skip);

        for (int i = skip; i < rawImages.size(); i++) {
            Image img = rawImages.get(i);
            TotalCaptureResult frameResult = findNearestZslResult(img.getTimestamp());
            boolean exposureAccepted =
                    motionExposurePairMatches(
                            frameResult,
                            bestExposureGroup);
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
            mExposures.put(frame.timestamp, ExposureIndex.time2sec(actualExposureNs) * actualIso);
            selected.add(frame);
        }
        int actualCount = selected.size();

        mImageSaver = new ImageSaver(cameraEventsListener);
        mImageSaver.setFrameCount(actualCount);
        mImageSaver.setImageFormat(CaptureController.RAW_FORMAT);
        mImageSaver.implementation = ImageSaverSelector.getImageSaver(CaptureController.RAW_FORMAT, mImageSaver.implementation);
        mImageSaver.implementation.frameCount = actualCount;

        SaverImplementation.IMAGE_BUFFER.clear();
        SaverImplementation.IMAGE_BUFFER.addAll(selected);

        // Publish the actual immutable Motion batch size before processing.
        // The existing JPEG ImageDescription/EXIF path reads this field.
        final int motionSelectedFrameCount = selected.size();
        com.particlesdevs.photoncamera.processing.parameters
                .FrameNumberSelector.frameCount =
                motionSelectedFrameCount;

        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                "JPEG_EXIF_FRAMECOUNT",
                "selectedFrameCount=" + motionSelectedFrameCount
                        + " publishedFrameCount="
                        + com.particlesdevs.photoncamera.processing.parameters
                                .FrameNumberSelector.frameCount);

        // Ownership has transferred to the immutable processing batch.
        // Re-open the passive ring immediately for the next scene. A second
        // shutter is still blocked by CaptureController.isProcessing.
        mZslCapturing = false;
        mMotionTopUpActive = false;

        mCaptureResult = mPreviewCaptureResult;
        mMeasuredFrameCnt = actualCount;

        cameraEventsListener.onFrameCountSet(actualCount);
        cameraEventsListener.onCaptureStillPictureStarted("ZSLCaptureStarted!");
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

        IsoExpoSelector.fullpairs.clear();
        for (int i = 0; i < actualCount; i++) {
            ImageFrame frame = selected.get(i);
            IsoExpoSelector.fullpairs.add(IsoExpoSelector.createEqualExposureZslPair(
                    this, selectedResults.get(frame.timestamp)));
        }

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
                selected, new ArrayList<>(BurstShakiness), mExposures, selectedResults,
                selectedResults.isEmpty() ? mPreviewCaptureResult
                        : selectedResults.get(selected.get(selected.size() - 1).timestamp),
                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount);
        processExecutor.execute(() -> {
            try {
                PhotonCamera.getGyro().CompleteSequence();
                mBackgroundHandler.post(this::unlockFocus);
                MotionMetrics.begin(
                        motionBatch.candidateCount,
                        motionBatch.retainedCount,
                        motionBatch.gyro
                );
                mImageSaver.runMotionRaw(mCameraCharacteristics, motionBatch);
            } catch (Exception e) {
                com.particlesdevs.photoncamera.util.MotionTrace.error(
                        mMotionDiagnosticShotId,
                        "CAPTURE_OR_PROCESSING",
                        e);
                Log.e(TAG, "ZSL runRaw full exception: "
                        + Log.getStackTraceString(e));
                String message = e.getClass().getSimpleName()
                        + ": " + String.valueOf(e.getLocalizedMessage());
                cameraEventsListener.onProcessingError(message);
            } finally {
                com.particlesdevs.photoncamera.util.MotionTrace.finish(
                        mMotionDiagnosticShotId,
                        "FINALLY",
                        "mZslCapturing=" + mZslCapturing
                                + " burst=" + burst
                                + " state=" + mState);
                // Do not clear mZslResultMap here: the passive ring may
                // already contain the next scene's frames and metadata.
                mZslCapturing = false;
                burst = false;
                mState = STATE_PREVIEW;
                SaverImplementation.IMAGE_BUFFER.clear();
                mBackgroundHandler.post(this::unlockFocus);
                try {
                    cameraEventsListener.onProcessingFinished(
                            "Motion processing ended");
                } catch (Exception cleanupError) {
                    Log.e(TAG, "Motion shutter cleanup callback failed: "
                            + Log.getStackTraceString(cleanupError));
                }
            }
        });
    }

    private void captureStillPicture() {
        try {
            if (null == mCameraDevice) {
                return;
            }
            if (isZslMode()) {
                triggerZslCapture();
                return;
            }
            // This is the CaptureRequest.Builder that we use to take a picture.
            final CaptureRequest.Builder captureBuilder;
            if(PhotonCamera.getSettings().selectedMode.equals(CameraMode.RAWVIDEO)) {
                captureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
                captureBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, getSelectedFpsRange());
            } else {
                captureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            }
            float focus = mFocus;
            double frametime = ExposureIndex.time2sec(IsoExpoSelector.GenerateExpoPair(-1, this).exposure);
            //this.mCaptureSession.stopRepeating();
            if(isDualSession) {
                if (mTargetFormat != mPreviewTargetFormat)
                    captureBuilder.addTarget(mImageReaderRaw.getSurface());
                else
                    captureBuilder.addTarget(mImageReaderPreview.getSurface());
            } else {
                captureBuilder.addTarget(mImageReaderRaw.getSurface());
                CameraMode selectedMode = PhotonCamera.getSettings().selectedMode;
                if(frametime > 0.06 && !isDualSession || selectedMode == CameraMode.RAWVIDEO || selectedMode == CameraMode.UNLIMITED || (!IsoExpoSelector.HDR)) {
                    captureBuilder.addTarget(surface);
                }
            }
            Camera2ApiAutoFix.applyEnergySaving();
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
            SaverImplementation.IMAGE_BUFFER.clear();

            int frameCount = FrameNumberSelector.getFrames();
            //if (frameCount == 1) frameCount++;
            cameraEventsListener.onFrameCountSet(frameCount);
            Log.d(TAG, "HDRFact1:" + paramController.isManualMode() + " HDRFact2:" + PhotonCamera.getSettings().alignAlgorithm);
            //IsoExpoSelector.HDR = (!manualParamModel.isManualMode()) && (PhotonCamera.getSettings().alignAlgorithm == 0);
            //IsoExpoSelector.HDR = (PhotonCamera.getSettings().alignAlgorithm == 1);
            Log.d(TAG, "HDR:" + IsoExpoSelector.HDR);
            Object mode = mPreviewRequestBuilder.get(CONTROL_AF_MODE);
            if(mode != null && (int) mode != CaptureRequest.CONTROL_AF_MODE_AUTO || PreferenceKeys.getAfMode() == CaptureRequest.CONTROL_AF_MODE_AUTO && !PhotonCamera.getSettings().selectedMode.equals(CameraMode.RAWVIDEO)) {
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

            IsoExpoSelector.useTripod = PhotonCamera.getGyro().getTripod();
            if (frameCount == -1) {
                for (int i = 0; i < 1; i++) {
                    if(!PhotonCamera.getSettings().selectedMode.equals(CameraMode.RAWVIDEO))
                        IsoExpoSelector.setExpo(captureBuilder, i, this);
                    else {
                        captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
                        captureBuilder.set(CaptureRequest.CONTROL_AE_MODE, mPreviewAEMode);
                    }
                    captures.add(captureBuilder.build());
                }
            } else {
                long[] times = new long[frameCount];
                for (int i = 0; i < frameCount; i++) {
                    IsoExpoSelector.setExpo(captureBuilder, i, this);
                    times[i] = IsoExpoSelector.lastSelectedExposure;
                    captures.add(captureBuilder.build());
                    mCaptureRequest = captureBuilder.build();
                }
                PhotonCamera.getGyro().PrepareGyroBurst(times, BurstShakiness);
            }

            //img
            Log.d(TAG, "FrameCount:" + frameCount);
            mImageSaver = new ImageSaver(cameraEventsListener);
            mImageSaver.setFrameCount(frameCount);
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
            Camera2ApiAutoFix.ApplyBurst();
            if (isDualSession)
                createCameraPreviewSession(true);
            else {
            mCaptureSession.stopRepeating();
            mCaptureSession.abortCaptures();
                switch (PhotonCamera.getSettings().selectedMode) {
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
            Log.e(TAG, Log.getStackTraceString(e));
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