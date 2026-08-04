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
import android.hardware.camera2.CaptureFailure;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.hardware.camera2.params.MeteringRectangle;
import android.hardware.camera2.params.OutputConfiguration;
import android.hardware.camera2.params.OisSample;
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
import java.nio.ByteOrder;
import java.nio.ShortBuffer;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import com.particlesdevs.photoncamera.processing.ImageFrame;
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
    /*
     * Characteristics for the currently selected physical camera.
     *
     * Keep access centralized through getActiveCameraCharacteristics() so
     * camera-specific code does not retain stale references during lens
     * switching.
     */
    private static volatile CameraCharacteristics mCameraCharacteristics;

    public static CameraCharacteristics getActiveCameraCharacteristics() {
        return mCameraCharacteristics;
    }
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
    private volatile boolean continuousCaptureFinalizing = false;
    public boolean mFlashed = false;
    public ArrayList<GyroBurst> BurstShakiness;
    /**
     * This a callback object for the {@link ImageReader}. "onImageAvailable" will be called when a
     * still image is ready to be saved.
     */
    public ImageSaver mImageSaver;
    public HashMap<Long, Double> mExposures = new HashMap<>();

    /*
     * Motion rolling buffer.
     *
     * Frames are copied into ImageFrame immediately, then the camera-owned
     * Image is closed. This allows the camera HAL and preview to continue
     * producing buffers while HDRX processes an immutable snapshot.
     */
    private final ArrayDeque<ImageFrame> mZslRingBuffer = new ArrayDeque<>();
    private final Object mZslBufferLock = new Object();
    private final HashMap<Long, Double> mZslExposureEnergy = new HashMap<>();
    private final HashMap<Long, Long> mZslExposureTimeNs = new HashMap<>();
    private final HashMap<Long, Integer> mZslSensitivity = new HashMap<>();

    private final HashMap<Long, Float> mZslRawSharpness =
            new HashMap<>();
    private final HashMap<Long, Float> mZslOisMotion =
            new HashMap<>();
    private final HashMap<Long, Integer> mZslOisMode =
            new HashMap<>();
    private final HashMap<Long, Integer> mZslEisMode =
            new HashMap<>();

    private volatile boolean mZslCapturing = false;
    private volatile long mMotionShutterTimestampNs = 0L;
    private volatile long mMotionCaptureStartMs = 0L;

    private volatile boolean mMotionRollingExposureConfigured = false;
    private volatile int mMotionPreviewMetadataFrames = 0;
    private volatile long mMotionRequestedExposureNs = 0L;
    private volatile int mMotionRequestedIso = 0;

    /*
     * Capture-time Motion target shared by rolling compatibility and the
     * dedicated controlled burst. It is recalculated for every shutter press.
     */
    private volatile long mMotionTargetExposureNs = 0L;
    private volatile int mMotionTargetIso = 0;

    /*
     * Build 26216:
     * Use a median of the five most recent actual preview exposure-energy
     * samples so one unstable Xiaomi AE result cannot darken the full burst.
     */
    private final double[] mMotionPreviewEnergyHistory =
            new double[5];
    private int mMotionPreviewEnergyHistoryCount = 0;
    private int mMotionPreviewEnergyHistoryIndex = 0;

    /*
     * Motion processing must use the white balance measured by the visible
     * continuously auto-balanced preview. The controlled manual RAW burst
     * still owns exposure, ISO, noise profile, timestamps, and EXIF.
     */
    private static volatile float[] mMotionProcessingNeutral = null;

    public static float[] getMotionProcessingNeutral() {
        if (PhotonCamera.getSettings().selectedMode != CameraMode.MOTION) {
            return null;
        }

        float[] neutral = mMotionProcessingNeutral;
        return neutral != null ? neutral.clone() : null;
    }

    private volatile boolean mLoggedStabilizationVendorTags = false;

    private static final int MOTION_SELECTION_RESERVE = 8;
    private static final int MOTION_MAX_RING_FRAMES = 37;
    private static final int MOTION_MIN_PROCESS_FRAMES = 2;
    private static final String MOTION_LOG_TAG = "MotionPipeline";

    /*
     * Dedicated Motion still-burst ownership.
     *
     * Photo and Night continue using ImageSaver's normal shared collection
     * path. Motion copies each arriving RAW into this private list, closes the
     * Image immediately, and hands one immutable batch to HDRX exactly once.
     */
    private final Object mMotionBurstLock = new Object();
    private final ArrayList<ImageFrame> mMotionBurstFrames =
            new ArrayList<>();
    private final AtomicBoolean mMotionBurstFinalized =
            new AtomicBoolean(false);

    private volatile boolean mMotionBurstActive = false;
    private volatile int mMotionBurstExpectedFrames = 0;
    private volatile long mMotionBurstFirstTimestampNs = 0L;

    private final HashMap<Long, ImageFrame> mMotionBurstPendingFrames =
            new HashMap<>();

    private final HashMap<Long, Long> mMotionBurstExposureTimeNs =
            new HashMap<>();
    private final HashMap<Long, Integer> mMotionBurstSensitivity =
            new HashMap<>();

    /*
     * Build 26215 integrated temporal-stack diagnostics.
     * OIS motion and delivery counters remain capture-local and do not alter
     * frame selection or processing.
     */
    private final HashMap<Long, Float> mMotionBurstOisMotion =
            new HashMap<>();
    private volatile int mMotionDiagnosticSubmittedFrames = 0;
    private volatile int mMotionDiagnosticCompletedResults = 0;
    private volatile int mMotionDiagnosticMatchedRawFrames = 0;
    private volatile int mMotionDiagnosticCaptureFailures = 0;

    /*
     * Build 26166:
     *
     * Keep the four-channel dynamic black level belonging to every
     * controlled RAW timestamp. Processing uses a validated burst median,
     * never an arbitrary last-frame value.
     */
    private final HashMap<Long, float[]> mMotionBurstDynamicBlackLevel =
            new HashMap<>();

    private static volatile float[] mMotionValidatedBlackLevel = null;
    private static volatile String mMotionValidatedBlackLevelSource =
            "unavailable";

    public static float[] getMotionValidatedBlackLevel() {
        float[] selected = mMotionValidatedBlackLevel;
        return selected != null ? selected.clone() : null;
    }

    public static String getMotionValidatedBlackLevelSource() {
        return mMotionValidatedBlackLevelSource;
    }

    /*
     * Controlled Motion pre-buffer. The visible preview remains under Xiaomi
     * AE; these one-shot RAW requests use Photon's 1/15-priority target.
     */
    private static final int MOTION_PREBUFFER_MAX_FRAMES = 8;
    private static final long MOTION_PREBUFFER_MAX_AGE_NS =
            1_000_000_000L;
    private static final long MOTION_PREBUFFER_INTERVAL_MS = 90L;

    private final ArrayDeque<ImageFrame> mMotionPrebufferFrames =
            new ArrayDeque<>();
    private final HashMap<Long, ImageFrame> mMotionPrebufferPendingFrames =
            new HashMap<>();
    private final HashMap<Long, Long> mMotionPrebufferExposureTimeNs =
            new HashMap<>();
    private final HashMap<Long, Integer> mMotionPrebufferSensitivity =
            new HashMap<>();

    private final ArrayList<ImageFrame> mMotionPreselectedFrames =
            new ArrayList<>();
    private final HashMap<Long, Long> mMotionPreselectedExposureTimeNs =
            new HashMap<>();
    private final HashMap<Long, Integer> mMotionPreselectedSensitivity =
            new HashMap<>();

    private volatile boolean mMotionPrebufferEnabled = false;
    private volatile boolean mMotionPrebufferRequestInFlight = false;
    private volatile long mMotionPrebufferAcceptUntilNs = 0L;
    private volatile long mMotionPrebufferTargetExposureNs = 0L;
    private volatile int mMotionPrebufferTargetIso = 0;
    private volatile int mMotionPrebufferFailureCount = 0;
    private volatile int mMotionPostShutterFrameOverride = 0;
    private volatile int mMotionCombinedRequestedFrames = 0;

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
            /*
             * Controlled Motion must be routed before the normal rolling-ZSL
             * branch. Motion is itself a ZSL mode, so checking isZslMode()
             * first previously swallowed every controlled RAW frame.
             */
            if (mMotionBurstActive) {
                Image image = null;
                ImageFrame frame = null;

                try {
                    image = reader.acquireNextImage();
                    if (image == null) {
                        return;
                    }

                    frame = mImageSaver.implementation.getFrame(image);
                    frame.timestamp = image.getTimestamp();
                } catch (Exception e) {
                    Log.e(
                            MOTION_LOG_TAG,
                            "CONTROLLED_RAW_COPY_FAILED "
                                    + Log.getStackTraceString(e)
                    );
                } finally {
                    if (image != null) {
                        image.close();
                    }
                }

                if (frame == null) {
                    return;
                }

                synchronized (mMotionBurstLock) {
                    if (!mMotionBurstActive) {
                        frame.close();
                        return;
                    }

                    ImageFrame replaced =
                            mMotionBurstPendingFrames.put(
                                    frame.timestamp,
                                    frame
                            );

                    if (replaced != null) {
                        replaced.close();
                    }

                    tryMatchControlledMotionFrameLocked(
                            frame.timestamp
                    );

                    int maximumPending =
                            Math.max(
                                    16,
                                    mMotionBurstExpectedFrames * 4
                            );

                    while (mMotionBurstPendingFrames.size()
                            > maximumPending) {

                        Long oldestTimestamp = null;

                        for (Long timestamp
                                : mMotionBurstPendingFrames.keySet()) {
                            if (oldestTimestamp == null
                                    || timestamp < oldestTimestamp) {
                                oldestTimestamp = timestamp;
                            }
                        }

                        if (oldestTimestamp == null) {
                            break;
                        }

                        ImageFrame stale =
                                mMotionBurstPendingFrames.remove(
                                        oldestTimestamp
                                );

                        if (stale != null) {
                            stale.close();
                        }
                    }
                }

                return;
            }

            if (mMotionPrebufferEnabled
                    && (
                        mMotionPrebufferRequestInFlight
                                || android.os.SystemClock
                                        .elapsedRealtimeNanos()
                                        <= mMotionPrebufferAcceptUntilNs
                                || !mMotionPrebufferExposureTimeNs.isEmpty()
                    )
                    && PhotonCamera.getSettings().selectedMode
                            == CameraMode.MOTION
                    && !mZslCapturing
                    && !CaptureController.isProcessing) {

                Image image = null;
                ImageFrame frame = null;

                try {
                    image = reader.acquireNextImage();

                    if (image == null) {
                        return;
                    }

                    frame =
                            mImageSaver.implementation
                                    .getFrame(image);

                    frame.timestamp = image.getTimestamp();
                } catch (Exception e) {
                    Log.e(
                            MOTION_LOG_TAG,
                            "PREBUFFER_RAW_COPY_FAILED "
                                    + Log.getStackTraceString(e)
                    );
                } finally {
                    if (image != null) {
                        image.close();
                    }
                }

                if (frame == null) {
                    return;
                }

                synchronized (mMotionBurstLock) {
                    ImageFrame replaced =
                            mMotionPrebufferPendingFrames.put(
                                    frame.timestamp,
                                    frame
                            );

                    if (replaced != null) {
                        replaced.close();
                    }

                    tryMatchMotionPrebufferFrameLocked(
                            frame.timestamp
                    );

                    while (mMotionPrebufferPendingFrames.size()
                            > 24) {

                        Long oldestTimestamp = null;

                        for (Long timestamp
                                : mMotionPrebufferPendingFrames
                                        .keySet()) {

                            if (oldestTimestamp == null
                                    || timestamp
                                            < oldestTimestamp) {
                                oldestTimestamp = timestamp;
                            }
                        }

                        if (oldestTimestamp == null) {
                            break;
                        }

                        ImageFrame stale =
                                mMotionPrebufferPendingFrames
                                        .remove(
                                                oldestTimestamp
                                        );

                        if (stale != null) {
                            stale.close();
                        }
                    }
                }

                return;
            }

            if (isZslMode()) {
                Image image = null;
                ImageFrame frame = null;

                try {
                    image = reader.acquireNextImage();
                    if (image == null) {
                        return;
                    }

                    frame = mImageSaver.implementation.getFrame(image);
                    frame.timestamp = image.getTimestamp();

                    mZslRawSharpness.put(
                            frame.timestamp,
                            calculateRawSharpness(frame)
                    );
                } catch (Exception e) {
                    Log.e(
                            MOTION_LOG_TAG,
                            "RING_COPY_FAILED "
                                    + Log.getStackTraceString(e)
                    );
                } finally {
                    if (image != null) {
                        image.close();
                    }
                }

                if (frame == null) {
                    return;
                }

                synchronized (mZslBufferLock) {
                    if (mZslCapturing) {
                        frame.close();
                        return;
                    }

                    mZslRingBuffer.addLast(frame);

                    int configured =
                            Math.max(
                                    MOTION_MIN_PROCESS_FRAMES,
                                    PhotonCamera.getSettings().frameCount
                            );

                    /*
                     * The passive Motion pre-buffer is always capped at eight
                     * frames. For slider totals below eight, never retain more
                     * frames than the requested final stack.
                     */
                    int ringCapacity =
                            Math.min(
                                    MOTION_PREBUFFER_MAX_FRAMES,
                                    configured
                            );

                    while (mZslRingBuffer.size() > ringCapacity) {
                        ImageFrame old = mZslRingBuffer.pollFirst();

                        if (old != null) {
                            mZslExposureEnergy.remove(old.timestamp);
                            mZslExposureTimeNs.remove(old.timestamp);
                            mZslSensitivity.remove(old.timestamp);
                            mZslRawSharpness.remove(old.timestamp);
                            mZslOisMotion.remove(old.timestamp);
                            mZslOisMode.remove(old.timestamp);
                            mZslEisMode.remove(old.timestamp);
                            old.close();
                        }
                    }
                }

                return;
            }
            /*
             * Motion post-shutter bursts have independent image ownership.
             * Do not send these frames through ImageSaver.frameCounter or the
             * Photo/Night collection state.
             */
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

        @Override
        public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                       @NonNull CaptureRequest request,
                                       @NonNull TotalCaptureResult result) {
            /*
             * CaptureRequest.getTargets() is not available on this project's
             * Android API surface. The repeating preview callback receives the
             * exact request object stored in mPreviewInputRequest, while the
             * RAW-only prebuffer uses a separate request object.
             */
            boolean visiblePreviewResult =
                    request == mPreviewInputRequest;

            /*
             * Photo and Night retain their original behavior. In Motion,
             * RAW-only prebuffer/manual results must not overwrite the latest
             * visible-preview AE/AWB metadata.
             */
            if (!isZslMode() || visiblePreviewResult) {
                Object exposure =
                        result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                Object iso =
                        result.get(CaptureResult.SENSOR_SENSITIVITY);
                Object focus =
                        result.get(CaptureResult.LENS_FOCUS_DISTANCE);
                Rational[] mTemp =
                        result.get(
                                CaptureResult.SENSOR_NEUTRAL_COLOR_POINT
                        );

                if (exposure != null) {
                    mPreviewExposureTime = (long) exposure;
                }
                if (iso != null) {
                    mPreviewIso = (int) iso;
                }
                if (focus != null) {
                    mFocus = (float) focus;
                }
                if (mTemp != null && mTemp.length >= 3) {
                    mPreviewTemp = mTemp;
                }
                if (mPreviewTemp == null) {
                    mPreviewTemp = new Rational[3];
                    for (int i = 0; i < mPreviewTemp.length; i++) {
                        mPreviewTemp[i] = new Rational(101, 100);
                    }
                }

                mColorSpaceTransform =
                        result.get(
                                CaptureResult.COLOR_CORRECTION_TRANSFORM
                        );

                Integer state =
                        result.get(CaptureResult.FLASH_STATE);

                mFlashed =
                        state != null
                                && (
                                    state
                                            == CaptureResult
                                                    .FLASH_STATE_PARTIAL
                                    || state
                                            == CaptureResult
                                                    .FLASH_STATE_FIRED
                                );

                mPreviewCaptureResult = result;
                mPreviewCaptureRequest = request;
            }

            if (isZslMode()) {
                Long sensorTimestamp =
                        result.get(CaptureResult.SENSOR_TIMESTAMP);

                Long actualExposureNs =
                        result.get(
                                CaptureResult.SENSOR_EXPOSURE_TIME
                        );

                Integer actualIso =
                        result.get(
                                CaptureResult.SENSOR_SENSITIVITY
                        );

                if (sensorTimestamp != null
                        && actualExposureNs != null
                        && actualIso != null) {

                    synchronized (mZslBufferLock) {
                        mZslExposureTimeNs.put(
                                sensorTimestamp,
                                actualExposureNs
                        );

                        mZslSensitivity.put(
                                sensorTimestamp,
                                actualIso
                        );

                        mZslExposureEnergy.put(
                                sensorTimestamp,
                                ExposureIndex.time2sec(
                                        actualExposureNs
                                ) * actualIso
                        );

                        double actualPreviewEnergy =
                                ExposureIndex.time2sec(
                                        actualExposureNs
                                ) * actualIso;

                        synchronized (mZslBufferLock) {
                            mMotionPreviewEnergyHistory[
                                    mMotionPreviewEnergyHistoryIndex
                            ] = actualPreviewEnergy;

                            mMotionPreviewEnergyHistoryIndex =
                                    (
                                            mMotionPreviewEnergyHistoryIndex
                                                    + 1
                                    )
                                            % mMotionPreviewEnergyHistory.length;

                            if (mMotionPreviewEnergyHistoryCount
                                    < mMotionPreviewEnergyHistory.length) {
                                mMotionPreviewEnergyHistoryCount++;
                            }
                        }

                        Integer actualOisMode =
                                result.get(
                                        CaptureResult
                                                .LENS_OPTICAL_STABILIZATION_MODE
                                );

                        Integer actualEisMode =
                                result.get(
                                        CaptureResult
                                                .CONTROL_VIDEO_STABILIZATION_MODE
                                );

                        if (actualOisMode != null) {
                            mZslOisMode.put(
                                    sensorTimestamp,
                                    actualOisMode
                            );
                        }

                        if (actualEisMode != null) {
                            mZslEisMode.put(
                                    sensorTimestamp,
                                    actualEisMode
                            );
                        }

                        if (Build.VERSION.SDK_INT
                                >= Build.VERSION_CODES.P) {

                            OisSample[] oisSamples =
                                    result.get(
                                            CaptureResult
                                                    .STATISTICS_OIS_SAMPLES
                                    );

                            mZslOisMotion.put(
                                    sensorTimestamp,
                                    calculateOisMotion(oisSamples)
                            );
                        }
                    }
                }

                logStabilizationVendorTags(result);

                /*
                 * Allow AE to settle briefly, then convert the already-active
                 * preview + RAW repeating request to one controlled Motion
                 * exposure. This is not a standalone capture pump: preview
                 * and RAW remain outputs of the same repeating request.
                 */
                if (!mMotionRollingExposureConfigured) {
                    mMotionPreviewMetadataFrames++;

                    if (mMotionPreviewMetadataFrames == 5) {
                        Log.d(
                                MOTION_LOG_TAG,
                                "ROLLING_AE_WARMUP_COMPLETE"
                                        + " previewExposureNs="
                                        + actualExposureNs
                                        + " previewIso="
                                        + actualIso
                        );

                        if (mBackgroundHandler != null) {
                            mBackgroundHandler.post(
                                    CaptureController.this
                                            ::configureMotionRollingExposure
                            );
                        }
                    }
                }
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
            onUnlimited = false;
            unlimitedStarted = false;
            continuousCaptureFinalizing = false;
            mState = STATE_PREVIEW;
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
        stopMotionPrebufferPump();

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
        stopMotionPrebufferPump();

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
        if (cameraId == null || cameraId.isEmpty()) {
            Log.e(TAG, "Cannot update camera characteristics: empty camera ID");
            return;
        }

        CameraCharacteristics characteristics =
                this.mCameraCharacteristicsMap.get(cameraId);

        if (characteristics == null) {
            Log.e(TAG, "No camera characteristics found for physical ID: " + cameraId);
            return;
        }

        try {
            PhotonCamera.getSpecificSensor().selectSpecifics(
                    Integer.parseInt(cameraId)
            );
        } catch (NumberFormatException exception) {
            Log.w(TAG, "Non-numeric physical camera ID: " + cameraId);
        }

        mCameraCharacteristics = characteristics;

        StreamConfigurationMap map = characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP
        );

        if (map == null) {
            Log.e(TAG, "No stream configuration map for physical ID: " + cameraId);
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
                        if (mCaptureSession != cameraCaptureSession
                                || mCameraDevice == null) {
                            Log.d(TAG, "Ignoring stale preview-session callback: "
                                    + cameraCaptureSession);
                            cameraCaptureSession.close();
                            return;
                        }
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
                            cameraCaptureSession.setRepeatingRequest(
                                    mPreviewInputRequest,
                                    mCaptureCallback,
                                    mBackgroundHandler
                            );
                            unlockFocus();

                            if (PhotonCamera.getSettings().selectedMode
                                    == CameraMode.MOTION) {
                                startMotionPrebufferPump();
                            } else {
                                stopMotionPrebufferPump();
                            }
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
                ImageFrame frame = mZslRingBuffer.pollFirst();
                if (frame != null) {
                    frame.close();
                }
            }

            mZslExposureEnergy.clear();
            mZslExposureTimeNs.clear();
            mZslSensitivity.clear();
            mZslRawSharpness.clear();
            mZslOisMotion.clear();
            mZslOisMode.clear();
            mZslEisMode.clear();

            mMotionRollingExposureConfigured = false;
            mMotionPreviewMetadataFrames = 0;
            mMotionRequestedExposureNs = 0L;
            mMotionRequestedIso = 0;
            mMotionTargetExposureNs = 0L;
            mMotionTargetIso = 0;
            java.util.Arrays.fill(
                    mMotionPreviewEnergyHistory,
                    0.0
            );
            mMotionPreviewEnergyHistoryCount = 0;
            mMotionPreviewEnergyHistoryIndex = 0;
            mLoggedStabilizationVendorTags = false;
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
            mPreviewRequestBuilder.addTarget(
                    mImageReaderRaw.getSurface()
            );

            /*
             * The viewfinder and rolling RAW stream share this repeating
             * request. Leave exposure under continuous AE so scene changes
             * are followed normally before and after shutter press.
             */
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_MODE,
                    CaptureRequest.CONTROL_MODE_AUTO
            );

            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_MODE,
                    CaptureRequest.CONTROL_AE_MODE_ON
            );

            configureMotionStabilizationRequest(
                    mPreviewRequestBuilder
            );
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
        if (mPreviewRequestBuilder == null
                || mCaptureSession == null
                || mBackgroundHandler == null) {
            Log.d(TAG, "unlockFocus(): ignored while camera session is rebuilding");
            return;
        }

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
        return PhotonCamera.getSettings().selectedMode
                == CameraMode.MOTION;
    }

    private float calculateRawSharpness(ImageFrame frame) {
        if (frame == null
                || frame.buffer == null
                || frame.width < 8
                || frame.height < 8) {
            return 0.0f;
        }

        try {
            ShortBuffer raw =
                    frame.buffer
                            .duplicate()
                            .order(ByteOrder.nativeOrder())
                            .asShortBuffer();

            int width = frame.width;
            int height = frame.height;

            int stepX = Math.max(8, width / 96);
            int stepY = Math.max(8, height / 72);

            double gradientSum = 0.0;
            int samples = 0;

            /*
             * Sample primarily green CFA positions. This avoids a full RAW
             * conversion and keeps the ImageReader callback lightweight.
             */
            for (int y = stepY; y < height - stepY; y += stepY) {
                int greenY = (y & ~1) + 1;

                for (int x = stepX; x < width - stepX; x += stepX) {
                    int greenX = x & ~1;

                    int centerIndex = greenY * width + greenX;
                    int rightIndex = centerIndex + 2;
                    int downIndex = centerIndex + width * 2;

                    if (downIndex >= raw.limit()
                            || rightIndex >= raw.limit()) {
                        continue;
                    }

                    int center = raw.get(centerIndex) & 0xffff;
                    int right = raw.get(rightIndex) & 0xffff;
                    int down = raw.get(downIndex) & 0xffff;

                    gradientSum += Math.abs(right - center);
                    gradientSum += Math.abs(down - center);
                    samples += 2;
                }
            }

            return samples > 0
                    ? (float) (gradientSum / samples)
                    : 0.0f;
        } catch (Exception e) {
            Log.w(
                    MOTION_LOG_TAG,
                    "RAW_SHARPNESS_FAILED "
                            + Log.getStackTraceString(e)
            );
            return 0.0f;
        }
    }

    private float calculateOisMotion(OisSample[] samples) {
        if (samples == null || samples.length < 2) {
            return 0.0f;
        }

        float path = 0.0f;

        for (int i = 1; i < samples.length; i++) {
            float dx =
                    samples[i].getXshift()
                            - samples[i - 1].getXshift();

            float dy =
                    samples[i].getYshift()
                            - samples[i - 1].getYshift();

            path += Math.hypot(dx, dy);
        }

        return path;
    }

    private float medianFloat(ArrayList<Float> values) {
        if (values.isEmpty()) {
            return 0.0f;
        }

        ArrayList<Float> sorted = new ArrayList<>(values);
        Collections.sort(sorted);

        int middle = sorted.size() / 2;

        if ((sorted.size() & 1) == 0) {
            return (
                    sorted.get(middle - 1)
                            + sorted.get(middle)
            ) * 0.5f;
        }

        return sorted.get(middle);
    }

    private void configureMotionStabilizationRequest(
            CaptureRequest.Builder builder
    ) {
        if (builder == null || mCameraCharacteristics == null) {
            return;
        }

        try {
            int[] oisModes =
                    mCameraCharacteristics.get(
                            CameraCharacteristics
                                    .LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION
                    );

            if (oisModes != null) {
                for (int mode : oisModes) {
                    if (mode
                            == CaptureRequest
                                    .LENS_OPTICAL_STABILIZATION_MODE_ON) {

                        builder.set(
                                CaptureRequest
                                        .LENS_OPTICAL_STABILIZATION_MODE,
                                CaptureRequest
                                        .LENS_OPTICAL_STABILIZATION_MODE_ON
                        );
                        break;
                    }
                }
            }
        } catch (Exception e) {
            Log.w(
                    MOTION_LOG_TAG,
                    "OIS_ENABLE_FAILED "
                            + Log.getStackTraceString(e)
            );
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            try {
                int[] oisDataModes =
                        mCameraCharacteristics.get(
                                CameraCharacteristics
                                        .STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES
                        );

                if (oisDataModes != null) {
                    for (int mode : oisDataModes) {
                        if (mode
                                == CaptureRequest
                                        .STATISTICS_OIS_DATA_MODE_ON) {

                            builder.set(
                                    CaptureRequest
                                            .STATISTICS_OIS_DATA_MODE,
                                    CaptureRequest
                                            .STATISTICS_OIS_DATA_MODE_ON
                            );
                            break;
                        }
                    }
                }
            } catch (Exception e) {
                Log.w(
                        MOTION_LOG_TAG,
                        "OIS_DATA_ENABLE_FAILED "
                                + Log.getStackTraceString(e)
                );
            }
        }
    }

    private void configureMotionRollingExposure() {
        if (!isZslMode()
                || mMotionRollingExposureConfigured
                || mPreviewRequestBuilder == null
                || mCaptureSession == null) {
            return;
        }

        try {
            /*
             * Keep Xiaomi AE continuously active on the shared preview+RAW
             * repeating request. The rolling ring therefore follows the scene
             * in real time and remains capable of true 30 fps.
             *
             * Photon selects its controlled shutter ladder only when the user
             * presses the shutter. Compatible recent AE frames are retained;
             * any mismatched frames are replaced by controlled post frames.
             */
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_MODE,
                    CaptureRequest.CONTROL_MODE_AUTO
            );

            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_MODE,
                    CaptureRequest.CONTROL_AE_MODE_ON
            );

            mPreviewRequestBuilder.set(
                    CaptureRequest.SENSOR_EXPOSURE_TIME,
                    null
            );

            mPreviewRequestBuilder.set(
                    CaptureRequest.SENSOR_SENSITIVITY,
                    null
            );

            configureMotionStabilizationRequest(
                    mPreviewRequestBuilder
            );

            mPreviewInputRequest =
                    mPreviewRequestBuilder.build();

            mCaptureSession.setRepeatingRequest(
                    mPreviewInputRequest,
                    mCaptureCallback,
                    mBackgroundHandler
            );

            mMotionRequestedExposureNs =
                    Math.max(1L, mPreviewExposureTime);
            mMotionRequestedIso =
                    Math.max(1, mPreviewIso);
            mMotionRollingExposureConfigured = true;

            Log.d(
                    MOTION_LOG_TAG,
                    "MOTION_CONTINUOUS_AE_ACTIVE"
                            + " camera=" + physicalID
                            + " latestAeExposureNs="
                            + mMotionRequestedExposureNs
                            + " latestAeIso="
                            + mMotionRequestedIso
                            + " previewAndRawShareAe=true"
                            + " manualRollingLock=false"
            );
        } catch (Exception e) {
            mMotionRollingExposureConfigured = false;

            Log.e(
                    MOTION_LOG_TAG,
                    "MOTION_CONTINUOUS_AE_FAILED "
                            + Log.getStackTraceString(e)
            );
        }
    }

    private void logStabilizationVendorTags(
            TotalCaptureResult result
    ) {
        if (mLoggedStabilizationVendorTags || result == null) {
            return;
        }

        mLoggedStabilizationVendorTags = true;

        try {
            for (CaptureResult.Key<?> key : result.getKeys()) {
                String name =
                        key.getName().toLowerCase(Locale.US);

                if (name.contains("ois")
                        || name.contains("eis")
                        || name.contains("stabil")
                        || name.contains("gyro")
                        || name.contains("motion")
                        || name.contains("shake")
                        || name.contains("lens.shift")) {

                    Object value = result.get(key);

                    String formattedValue;

                    if (value == null) {
                        formattedValue = "null";
                    } else if (value.getClass().isArray()) {
                        int arrayLength =
                                java.lang.reflect.Array.getLength(value);

                        StringBuilder arrayText =
                                new StringBuilder("[");

                        int displayedValues =
                                Math.min(arrayLength, 32);

                        for (int i = 0;
                                i < displayedValues;
                                i++) {

                            if (i > 0) {
                                arrayText.append(", ");
                            }

                            arrayText.append(
                                    String.valueOf(
                                            java.lang.reflect.Array.get(
                                                    value,
                                                    i
                                            )
                                    )
                            );
                        }

                        if (arrayLength > displayedValues) {
                            arrayText.append(
                                    ", ... total="
                                            + arrayLength
                            );
                        }

                        arrayText.append("]");
                        formattedValue = arrayText.toString();
                    } else {
                        formattedValue = String.valueOf(value);
                    }

                    Log.d(
                            MOTION_LOG_TAG,
                            "STABILIZATION_VENDOR_TAG"
                                    + " name="
                                    + key.getName()
                                    + " value="
                                    + formattedValue
                    );
                }
            }
        } catch (Exception e) {
            Log.w(
                    MOTION_LOG_TAG,
                    "VENDOR_TAG_ENUMERATION_FAILED "
                            + Log.getStackTraceString(e)
            );
        }
    }


    private double motionEvDifference(
            double first,
            double second
    ) {
        if (first <= 0.0 || second <= 0.0) {
            return Double.POSITIVE_INFINITY;
        }

        return Math.abs(
                Math.log(first / second)
                        / Math.log(2.0)
        );
    }

    private double getStableMotionPreviewEnergy(
            double latestPreviewEnergy
    ) {
        double[] validHistory;

        synchronized (mZslBufferLock) {
            if (mMotionPreviewEnergyHistoryCount <= 0) {
                return latestPreviewEnergy;
            }

            validHistory =
                    new double[mMotionPreviewEnergyHistoryCount];

            for (int i = 0;
                 i < mMotionPreviewEnergyHistoryCount;
                 i++) {
                validHistory[i] =
                        mMotionPreviewEnergyHistory[i];
            }
        }

        java.util.Arrays.sort(validHistory);

        int middle = validHistory.length / 2;
        double median =
                (validHistory.length & 1) == 0
                        ? (
                                validHistory[middle - 1]
                                        + validHistory[middle]
                        ) * 0.5
                        : validHistory[middle];

        if (median <= 0.0) {
            return latestPreviewEnergy;
        }

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26216_STABLE_PREVIEW_ENERGY"
                        + " latest=" + latestPreviewEnergy
                        + " median=" + median
                        + " samples=" + validHistory.length
                        + " latestVsMedianEv="
                        + (
                            latestPreviewEnergy > 0.0
                                    ? Math.log(
                                            latestPreviewEnergy / median
                                    ) / Math.log(2.0)
                                    : Double.NaN
                        )
        );

        return median;
    }

    private long[] calculateMotionPrebufferTarget() {
        Long previewExposureNs = null;
        Integer previewIso = null;

        if (mPreviewCaptureResult != null) {
            previewExposureNs =
                    mPreviewCaptureResult.get(
                            CaptureResult.SENSOR_EXPOSURE_TIME
                    );

            previewIso =
                    mPreviewCaptureResult.get(
                            CaptureResult.SENSOR_SENSITIVITY
                    );
        }

        IsoExpoSelector.ExpoPair selectorPair =
                IsoExpoSelector.GenerateExpoPair(-1, this);

        Range<Long> exposureRange =
                mCameraCharacteristics != null
                        ? mCameraCharacteristics.get(
                                CameraCharacteristics
                                        .SENSOR_INFO_EXPOSURE_TIME_RANGE
                        )
                        : null;

        Range<Integer> sensitivityRange =
                mCameraCharacteristics != null
                        ? mCameraCharacteristics.get(
                                CameraCharacteristics
                                        .SENSOR_INFO_SENSITIVITY_RANGE
                        )
                        : null;

        long minimumExposureNs =
                exposureRange != null
                        ? exposureRange.getLower()
                        : 1_000_000L;

        long maximumExposureNs =
                exposureRange != null
                        ? Math.min(
                                exposureRange.getUpper(),
                                66_666_667L
                        )
                        : 66_666_667L;

        int minimumIso =
                sensitivityRange != null
                        ? sensitivityRange.getLower()
                        : 50;

        int maximumIso =
                sensitivityRange != null
                        ? sensitivityRange.getUpper()
                        : 12_800;

        double previewEnergy =
                previewExposureNs != null
                        && previewExposureNs > 0L
                        && previewIso != null
                        && previewIso > 0
                        ? ExposureIndex.time2sec(
                                previewExposureNs
                        ) * previewIso
                        : 0.0;

        long exposureNs;
        int iso;

        if (previewEnergy > 0.0) {
            long exposureAtMinimumIsoNs =
                    Math.round(
                            previewEnergy
                                    / Math.max(
                                            1,
                                            minimumIso
                                    )
                                    * 1_000_000_000.0
                    );

            exposureNs =
                    Math.max(
                            minimumExposureNs,
                            Math.min(
                                    maximumExposureNs,
                                    exposureAtMinimumIsoNs
                            )
                    );

            iso =
                    (int) Math.round(
                            previewEnergy
                                    / ExposureIndex.time2sec(
                                            exposureNs
                                    )
                    );

            iso =
                    Math.max(
                            minimumIso,
                            Math.min(maximumIso, iso)
                    );
        } else {
            exposureNs =
                    selectorPair != null
                            ? selectorPair.exposure
                            : maximumExposureNs;

            iso =
                    selectorPair != null
                            ? selectorPair.iso
                            : minimumIso;

            exposureNs =
                    Math.max(
                            minimumExposureNs,
                            Math.min(
                                    maximumExposureNs,
                                    exposureNs
                            )
                    );

            iso =
                    Math.max(
                            minimumIso,
                            Math.min(maximumIso, iso)
                    );
        }

        return new long[]{exposureNs, iso};
    }

    private void closeMotionPrebufferLocked() {
        for (ImageFrame frame : mMotionPrebufferFrames) {
            if (frame != null) {
                frame.close();
            }
        }

        for (ImageFrame frame
                : mMotionPrebufferPendingFrames.values()) {
            if (frame != null) {
                frame.close();
            }
        }

        mMotionPrebufferFrames.clear();
        mMotionPrebufferPendingFrames.clear();
        mMotionPrebufferExposureTimeNs.clear();
        mMotionPrebufferSensitivity.clear();
    }

    private void pruneMotionPrebufferLocked(
            long nowNs
    ) {
        while (!mMotionPrebufferFrames.isEmpty()) {
            ImageFrame oldest =
                    mMotionPrebufferFrames.peekFirst();

            if (oldest == null
                    || nowNs - oldest.timestamp
                            <= MOTION_PREBUFFER_MAX_AGE_NS) {
                break;
            }

            mMotionPrebufferFrames.pollFirst();

            if (oldest != null) {
                mMotionPrebufferExposureTimeNs.remove(
                        oldest.timestamp
                );

                mMotionPrebufferSensitivity.remove(
                        oldest.timestamp
                );

                oldest.close();
            }
        }
    }

    private void tryMatchMotionPrebufferFrameLocked(
            long timestamp
    ) {
        ImageFrame frame =
                mMotionPrebufferPendingFrames.get(
                        timestamp
                );

        Long exposureNs =
                mMotionPrebufferExposureTimeNs.get(
                        timestamp
                );

        Integer iso =
                mMotionPrebufferSensitivity.get(
                        timestamp
                );

        if (frame == null
                || exposureNs == null
                || exposureNs <= 0L
                || iso == null
                || iso <= 0) {
            return;
        }

        mMotionPrebufferPendingFrames.remove(
                timestamp
        );

        pruneMotionPrebufferLocked(
                android.os.SystemClock
                        .elapsedRealtimeNanos()
        );

        mMotionPrebufferFrames.addLast(frame);

        while (mMotionPrebufferFrames.size()
                > MOTION_PREBUFFER_MAX_FRAMES) {

            ImageFrame oldest =
                    mMotionPrebufferFrames.pollFirst();

            if (oldest != null) {
                mMotionPrebufferExposureTimeNs.remove(
                        oldest.timestamp
                );

                mMotionPrebufferSensitivity.remove(
                        oldest.timestamp
                );

                oldest.close();
            }
        }

        Log.d(
                MOTION_LOG_TAG,
                "PREBUFFER_RAW_MATCHED"
                        + " timestamp="
                        + timestamp
                        + " exposureNs="
                        + exposureNs
                        + " iso="
                        + iso
                        + " buffered="
                        + mMotionPrebufferFrames.size()
                        + "/"
                        + MOTION_PREBUFFER_MAX_FRAMES
        );
    }

    private final CameraCaptureSession.CaptureCallback
            mMotionPrebufferCaptureCallback =
            new CameraCaptureSession.CaptureCallback() {

        @Override
        public void onCaptureCompleted(
                @NonNull CameraCaptureSession session,
                @NonNull CaptureRequest request,
                @NonNull TotalCaptureResult result
        ) {
            Long timestamp =
                    result.get(
                            CaptureResult.SENSOR_TIMESTAMP
                    );

            Long exposureNs =
                    result.get(
                            CaptureResult.SENSOR_EXPOSURE_TIME
                    );

            Integer iso =
                    result.get(
                            CaptureResult.SENSOR_SENSITIVITY
                    );

            synchronized (mMotionBurstLock) {
                if (timestamp != null
                        && exposureNs != null
                        && exposureNs > 0L
                        && iso != null
                        && iso > 0) {

                    mMotionPrebufferExposureTimeNs.put(
                            timestamp,
                            exposureNs
                    );

                    mMotionPrebufferSensitivity.put(
                            timestamp,
                            iso
                    );

                    tryMatchMotionPrebufferFrameLocked(
                            timestamp
                    );
                }

                mMotionPrebufferRequestInFlight = false;
                mMotionPrebufferAcceptUntilNs =
                        android.os.SystemClock
                                .elapsedRealtimeNanos()
                                + 500_000_000L;

                mMotionPrebufferFailureCount = 0;
            }

            scheduleMotionPrebufferPump(
                    MOTION_PREBUFFER_INTERVAL_MS
            );
        }

        @Override
        public void onCaptureFailed(
                @NonNull CameraCaptureSession session,
                @NonNull CaptureRequest request,
                @NonNull CaptureFailure failure
        ) {
            synchronized (mMotionBurstLock) {
                mMotionPrebufferRequestInFlight = false;
                mMotionPrebufferFailureCount++;

                if (mMotionPrebufferFailureCount >= 3) {
                    mMotionPrebufferEnabled = false;
                    closeMotionPrebufferLocked();

                    Log.e(
                            MOTION_LOG_TAG,
                            "PREBUFFER_DISABLED"
                                    + " reason=repeated_capture_failure"
                    );
                }
            }

            scheduleMotionPrebufferPump(
                    500L
            );
        }
    };

    private final Runnable mMotionPrebufferRunnable =
            new Runnable() {
        @Override
        public void run() {
            submitNextMotionPrebufferFrame();
        }
    };

    private void scheduleMotionPrebufferPump(
            long delayMs
    ) {
        if (mBackgroundHandler == null) {
            return;
        }

        mBackgroundHandler.removeCallbacks(
                mMotionPrebufferRunnable
        );

        mBackgroundHandler.postDelayed(
                mMotionPrebufferRunnable,
                delayMs
        );
    }

    private void startMotionPrebufferPump() {
        /*
         * Disabled in build 0.9726144.
         *
         * The 0.9726143 implementation submitted controlled full-resolution
         * RAW captures while preview was active. Those long-exposure requests
         * interrupted the repeating preview, caused visible exposure flicker,
         * and could restart while the previous HDRX shot still owned RAW
         * frames.
         *
         * Keep all pre-buffer state empty so normal preview and the dedicated
         * shutter-triggered Motion RAW burst remain isolated.
         */
        if (mBackgroundHandler != null) {
            mBackgroundHandler.removeCallbacks(mMotionPrebufferRunnable);
        }

        synchronized (mMotionBurstLock) {
            mMotionPrebufferEnabled = false;
            mMotionPrebufferRequestInFlight = false;
            mMotionPrebufferAcceptUntilNs = 0L;
            mMotionPrebufferTargetExposureNs = 0L;
            mMotionPrebufferTargetIso = 0;
            mMotionPrebufferFailureCount = 0;
            closeMotionPrebufferLocked();
        }

        Log.d(
                TAG,
                "MOTION_PREBUFFER_DISABLED build=0.9726144"
        );
    }

    private void stopMotionPrebufferPump() {
        if (mBackgroundHandler != null) {
            mBackgroundHandler.removeCallbacks(
                    mMotionPrebufferRunnable
            );
        }

        synchronized (mMotionBurstLock) {
            mMotionPrebufferEnabled = false;
            mMotionPrebufferRequestInFlight = false;
            mMotionPrebufferAcceptUntilNs = 0L;
            closeMotionPrebufferLocked();
        }
    }

    private void submitNextMotionPrebufferFrame() {
        if (!mMotionPrebufferEnabled
                || mBackgroundHandler == null
                || mCameraDevice == null
                || mCaptureSession == null
                || mImageReaderRaw == null
                || PhotonCamera.getSettings().selectedMode
                        != CameraMode.MOTION
                || mZslCapturing
                || CaptureController.isProcessing
                || mMotionBurstActive
                || mMotionPrebufferRequestInFlight) {

            scheduleMotionPrebufferPump(250L);
            return;
        }

        final long[] target =
                calculateMotionPrebufferTarget();

        final long targetExposureNs = target[0];
        final int targetIso = (int) target[1];

        synchronized (mMotionBurstLock) {
            pruneMotionPrebufferLocked(
                    android.os.SystemClock
                            .elapsedRealtimeNanos()
            );

            if (mMotionPrebufferTargetExposureNs > 0L
                    && mMotionPrebufferTargetIso > 0) {

                double shutterDifferenceEv =
                        motionEvDifference(
                                targetExposureNs,
                                mMotionPrebufferTargetExposureNs
                        );

                double isoDifferenceEv =
                        motionEvDifference(
                                targetIso,
                                mMotionPrebufferTargetIso
                        );

                if (shutterDifferenceEv > 0.50
                        || isoDifferenceEv > 0.75) {

                    closeMotionPrebufferLocked();

                    Log.d(
                            MOTION_LOG_TAG,
                            "PREBUFFER_FLUSHED"
                                    + " reason=target_changed"
                                    + " shutterDifferenceEv="
                                    + shutterDifferenceEv
                                    + " isoDifferenceEv="
                                    + isoDifferenceEv
                    );
                }
            }

            mMotionPrebufferTargetExposureNs =
                    targetExposureNs;

            mMotionPrebufferTargetIso = targetIso;

            if (mMotionPrebufferFrames.size()
                    >= MOTION_PREBUFFER_MAX_FRAMES) {

                scheduleMotionPrebufferPump(120L);
                return;
            }

            mMotionPrebufferRequestInFlight = true;
            mMotionPrebufferAcceptUntilNs =
                    android.os.SystemClock
                            .elapsedRealtimeNanos()
                            + 750_000_000L;
        }

        try {
            CaptureRequest.Builder builder =
                    mCameraDevice.createCaptureRequest(
                            CameraDevice.TEMPLATE_STILL_CAPTURE
                    );

            builder.addTarget(
                    mImageReaderRaw.getSurface()
            );

            builder.set(
                    CaptureRequest.CONTROL_AE_MODE,
                    CaptureRequest.CONTROL_AE_MODE_OFF
            );

            builder.set(
                    CaptureRequest.SENSOR_EXPOSURE_TIME,
                    targetExposureNs
            );

            builder.set(
                    CaptureRequest.SENSOR_SENSITIVITY,
                    targetIso
            );

            builder.set(
                    CaptureRequest.JPEG_ORIENTATION,
                    PhotonCamera.getGravity()
                            .getCameraRotation(
                                    mSensorOrientation
                            )
            );

            configureMotionStabilizationRequest(
                    builder
            );

            VendorTagUtils.builderSessionApply(
                    builder,
                    true,
                    useMaximumResolutionKey,
                    physicalID
            );

            Log.d(
                    MOTION_LOG_TAG,
                    "PREBUFFER_REQUEST"
                            + " camera="
                            + physicalID
                            + " exposureNs="
                            + targetExposureNs
                            + " iso="
                            + targetIso
            );

            mCaptureSession.capture(
                    builder.build(),
                    mMotionPrebufferCaptureCallback,
                    mBackgroundHandler
            );
        } catch (Exception e) {
            synchronized (mMotionBurstLock) {
                mMotionPrebufferRequestInFlight = false;
                mMotionPrebufferFailureCount++;

                if (mMotionPrebufferFailureCount >= 3) {
                    mMotionPrebufferEnabled = false;
                    closeMotionPrebufferLocked();
                }
            }

            Log.e(
                    MOTION_LOG_TAG,
                    "PREBUFFER_REQUEST_FAILED "
                            + Log.getStackTraceString(e)
            );

            scheduleMotionPrebufferPump(500L);
        }
    }

    private float[] getMotionStaticBlackLevel() {
        int[] staticValues = new int[]{64, 64, 64, 64};

        CameraCharacteristics characteristics =
                getActiveCameraCharacteristics();

        if (characteristics != null) {
            android.hardware.camera2.params.BlackLevelPattern pattern =
                    characteristics.get(
                            CameraCharacteristics
                                    .SENSOR_BLACK_LEVEL_PATTERN
                    );

            if (pattern != null) {
                pattern.copyTo(staticValues, 0);
            }
        }

        return new float[]{
                staticValues[0],
                staticValues[1],
                staticValues[2],
                staticValues[3]
        };
    }

    private int getMotionStaticWhiteLevel() {
        CameraCharacteristics characteristics =
                getActiveCameraCharacteristics();

        if (characteristics != null) {
            Integer whiteLevel =
                    characteristics.get(
                            CameraCharacteristics
                                    .SENSOR_INFO_WHITE_LEVEL
                    );

            if (whiteLevel != null && whiteLevel > 0) {
                return whiteLevel;
            }
        }

        return 1023;
    }

    private boolean isValidMotionDynamicBlackLevel(
            float[] candidate,
            int whiteLevel
    ) {
        if (candidate == null || candidate.length < 4) {
            return false;
        }

        float maximumAllowed =
                Math.max(
                        256.0f,
                        Math.max(1, whiteLevel) * 0.25f
                );

        float minimum = Float.POSITIVE_INFINITY;
        float maximum = Float.NEGATIVE_INFINITY;

        for (int i = 0; i < 4; i++) {
            float value = candidate[i];

            if (!Float.isFinite(value)
                    || value < 0.0f
                    || value >= maximumAllowed) {
                return false;
            }

            minimum = Math.min(minimum, value);
            maximum = Math.max(maximum, value);
        }

        float maximumChannelSpread =
                Math.max(
                        64.0f,
                        Math.max(1, whiteLevel) * 0.08f
                );

        return maximum - minimum <= maximumChannelSpread;
    }

    private float medianMotionValue(
            ArrayList<Float> values
    ) {
        Collections.sort(values);

        int size = values.size();
        int middle = size / 2;

        if ((size & 1) == 1) {
            return values.get(middle);
        }

        return (
                values.get(middle - 1)
                        + values.get(middle)
        ) * 0.5f;
    }

    private void selectMotionValidatedBlackLevelLocked(
            ArrayList<ImageFrame> completedFrames
    ) {
        float[] staticBlackLevel = getMotionStaticBlackLevel();
        int whiteLevel = getMotionStaticWhiteLevel();

        ArrayList<float[]> samples = new ArrayList<>();

        for (ImageFrame frame : completedFrames) {
            if (frame == null) {
                continue;
            }

            float[] sample =
                    mMotionBurstDynamicBlackLevel.get(
                            frame.timestamp
                    );

            if (isValidMotionDynamicBlackLevel(
                    sample,
                    whiteLevel
            )) {
                samples.add(sample.clone());
            }
        }

        int requiredSamples =
                Math.max(
                        3,
                        (int) Math.ceil(
                                completedFrames.size() * 0.75
                        )
                );

        float[] selected = staticBlackLevel.clone();
        String source = "staticFallback";
        String reason = "insufficientSamples";

        float maximumObservedRange =
                Float.POSITIVE_INFINITY;

        if (samples.size() >= requiredSamples) {
            float[] median = new float[4];
            maximumObservedRange = 0.0f;

            for (int channel = 0; channel < 4; channel++) {
                ArrayList<Float> channelValues =
                        new ArrayList<>();

                float channelMinimum =
                        Float.POSITIVE_INFINITY;
                float channelMaximum =
                        Float.NEGATIVE_INFINITY;

                for (float[] sample : samples) {
                    float value = sample[channel];

                    channelValues.add(value);
                    channelMinimum =
                            Math.min(channelMinimum, value);
                    channelMaximum =
                            Math.max(channelMaximum, value);
                }

                median[channel] =
                        medianMotionValue(channelValues);

                maximumObservedRange =
                        Math.max(
                                maximumObservedRange,
                                channelMaximum - channelMinimum
                        );
            }

            float medianMinimum =
                    Math.min(
                            Math.min(median[0], median[1]),
                            Math.min(median[2], median[3])
                    );

            float medianMaximum =
                    Math.max(
                            Math.max(median[0], median[1]),
                            Math.max(median[2], median[3])
                    );

            float stabilityLimit =
                    Math.max(
                            8.0f,
                            whiteLevel * 0.02f
                    );

            float channelSpreadLimit =
                    Math.max(
                            64.0f,
                            whiteLevel * 0.08f
                    );

            boolean stable =
                    maximumObservedRange <= stabilityLimit;

            boolean plausible =
                    isValidMotionDynamicBlackLevel(
                            median,
                            whiteLevel
                    )
                            && medianMaximum - medianMinimum
                                    <= channelSpreadLimit;

            if (stable && plausible) {
                selected = median;
                source = "dynamicMedian";
                reason = "validated";
            } else if (!stable) {
                reason = "burstVariation";
            } else {
                reason = "implausibleMedian";
            }
        }

        mMotionValidatedBlackLevel = selected.clone();
        mMotionValidatedBlackLevelSource = source;

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26166_BLACK_LEVEL_SELECTED"
                        + " source=" + source
                        + " reason=" + reason
                        + " samples="
                        + samples.size()
                        + "/"
                        + completedFrames.size()
                        + " required="
                        + requiredSamples
                        + " selected="
                        + Arrays.toString(selected)
                        + " static="
                        + Arrays.toString(staticBlackLevel)
                        + " maxObservedRange="
                        + maximumObservedRange
                        + " whiteLevel="
                        + whiteLevel
                        + " cfaOrder=R_G1_G2_B"
        );
    }

    private void tryMatchControlledMotionFrameLocked(
            long timestamp
    ) {
        if (!mMotionBurstActive
                || mMotionBurstFrames.size()
                        >= mMotionBurstExpectedFrames) {
            return;
        }

        ImageFrame frame =
                mMotionBurstPendingFrames.get(timestamp);

        Long exposureNs =
                mMotionBurstExposureTimeNs.get(timestamp);

        Integer iso =
                mMotionBurstSensitivity.get(timestamp);

        if (frame == null
                || exposureNs == null
                || exposureNs <= 0L
                || iso == null
                || iso <= 0) {
            return;
        }

        mMotionBurstPendingFrames.remove(timestamp);
        mMotionBurstFrames.add(frame);
        mMotionDiagnosticMatchedRawFrames++;

        Log.d(
                MOTION_LOG_TAG,
                "CONTROLLED_RAW_MATCHED"
                        + " timestamp="
                        + timestamp
                        + " exposureNs="
                        + exposureNs
                        + " iso="
                        + iso
                        + " matched="
                        + mMotionBurstFrames.size()
                        + "/"
                        + mMotionBurstExpectedFrames
        );
    }

    private void closePendingMotionFramesLocked() {
        for (ImageFrame frame
                : mMotionBurstPendingFrames.values()) {
            if (frame != null) {
                frame.close();
            }
        }

        mMotionBurstPendingFrames.clear();
    }

    private void recoverDedicatedMotionCapture(
            String reason
    ) {
        synchronized (mMotionBurstLock) {
            mMotionBurstActive = false;

            for (ImageFrame frame : mMotionBurstFrames) {
                if (frame != null) {
                    frame.close();
                }
            }

            for (ImageFrame frame : mMotionPreselectedFrames) {
                if (frame != null) {
                    frame.close();
                }
            }

            mMotionBurstFrames.clear();
            mMotionPreselectedFrames.clear();
            closePendingMotionFramesLocked();
            mMotionBurstExposureTimeNs.clear();
            mMotionBurstSensitivity.clear();
            mMotionBurstDynamicBlackLevel.clear();
            mMotionValidatedBlackLevel = null;
            mMotionValidatedBlackLevelSource =
                    "recoveryCleared";
            mMotionPreselectedExposureTimeNs.clear();
            mMotionPreselectedSensitivity.clear();
            mMotionBurstExpectedFrames = 0;
            mMotionBurstFirstTimestampNs = 0L;
            mMotionPostShutterFrameOverride = 0;
            mMotionCombinedRequestedFrames = 0;
        }

        mImageSaver.implementation.bufferLock = false;
        mZslCapturing = false;

        Log.e(
                MOTION_LOG_TAG,
                "CONTROLLED_BURST_RECOVERED reason="
                        + reason
        );

        mBackgroundHandler.post(() -> {
            try {
                if (!isDualSession) {
                    unlockFocus();
                } else {
                    createCameraPreviewSession(false);
                }
            } catch (Exception e) {
                Log.e(
                        MOTION_LOG_TAG,
                        "CONTROLLED_RECOVERY_PREVIEW_FAILED "
                                + Log.getStackTraceString(e)
                );
            }
        });
    }

    private void triggerZslCapture() {
        if (mZslCapturing || CaptureController.isProcessing) {
            Log.w(
                    MOTION_LOG_TAG,
                    "MOTION_REJECTED reason=capture_or_processing_busy"
            );
            return;
        }

        mZslCapturing = true;
        burst = false;
        mMotionCaptureStartMs =
                android.os.SystemClock.elapsedRealtime();
        mMotionShutterTimestampNs =
                android.os.SystemClock.elapsedRealtimeNanos();

        final int requestedFrames =
                Math.max(
                        MOTION_MIN_PROCESS_FRAMES,
                        FrameNumberSelector.getFrames()
                );

        cameraRotation =
                PhotonCamera.getGravity().getCameraRotation(
                        mSensorOrientation
                );

        BurstShakiness = new ArrayList<>();
        mExposures = new HashMap<>();

        final ArrayList<ImageFrame> candidates =
                new ArrayList<>();

        /*
         * Freeze the controlled pre-buffer at shutter press. Only recent,
         * timestamp-matched controlled frames are admitted; the visible
         * preview remains under normal AE.
         */
        synchronized (mMotionBurstLock) {
            pruneMotionPrebufferLocked(
                    mMotionShutterTimestampNs
            );

            while (!mMotionPrebufferFrames.isEmpty()) {
                ImageFrame frame =
                        mMotionPrebufferFrames.pollFirst();

                if (frame == null) {
                    continue;
                }

                Long exposureNs =
                        mMotionPrebufferExposureTimeNs.remove(
                                frame.timestamp
                        );

                Integer iso =
                        mMotionPrebufferSensitivity.remove(
                                frame.timestamp
                        );

                if (exposureNs != null
                        && exposureNs > 0L
                        && iso != null
                        && iso > 0) {

                    mZslExposureTimeNs.put(
                            frame.timestamp,
                            exposureNs
                    );

                    mZslSensitivity.put(
                            frame.timestamp,
                            iso
                    );

                    mZslExposureEnergy.put(
                            frame.timestamp,
                            ExposureIndex.time2sec(
                                    exposureNs
                            ) * iso
                    );

                    candidates.add(frame);
                } else {
                    frame.close();
                }
            }

            closeMotionPrebufferLocked();
            mMotionPrebufferRequestInFlight = false;
            mMotionPrebufferAcceptUntilNs = 0L;
        }

        synchronized (mZslBufferLock) {
            while (!mZslRingBuffer.isEmpty()) {
                ImageFrame frame = mZslRingBuffer.pollFirst();

                if (frame != null) {
                    candidates.add(frame);
                }
            }
        }

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_START"
                        + " camera="
                        + physicalID
                        + " requested="
                        + requestedFrames
                        + " candidates="
                        + candidates.size()
                        + " shutterNs="
                        + mMotionShutterTimestampNs
        );

        Rational[] previewNeutralRational = null;

        if (mPreviewCaptureResult != null) {
            previewNeutralRational =
                    mPreviewCaptureResult.get(
                            CaptureResult.SENSOR_NEUTRAL_COLOR_POINT
                    );
        }

        if (previewNeutralRational != null
                && previewNeutralRational.length >= 3) {

            mMotionProcessingNeutral = new float[]{
                    previewNeutralRational[0].floatValue(),
                    previewNeutralRational[1].floatValue(),
                    previewNeutralRational[2].floatValue()
            };

            Integer previewAwbState =
                    mPreviewCaptureResult.get(
                            CaptureResult.CONTROL_AWB_STATE
                    );

            Log.d(
                    MOTION_LOG_TAG,
                    "MOTION_PREVIEW_NEUTRAL_SNAPSHOT"
                            + " camera=" + physicalID
                            + " neutral="
                            + java.util.Arrays.toString(
                                    mMotionProcessingNeutral
                            )
                            + " awbState=" + previewAwbState
            );
        } else {
            mMotionProcessingNeutral = null;

            Log.w(
                    MOTION_LOG_TAG,
                    "MOTION_PREVIEW_NEUTRAL_SNAPSHOT"
                            + " camera=" + physicalID
                            + " neutralUnavailable=true"
                            + " fallback=controlledResult"
            );
        }

        Long latestPreviewExposureNs = null;
        Integer latestPreviewIso = null;

        if (mPreviewCaptureResult != null) {
            latestPreviewExposureNs =
                    mPreviewCaptureResult.get(
                            CaptureResult.SENSOR_EXPOSURE_TIME
                    );

            latestPreviewIso =
                    mPreviewCaptureResult.get(
                            CaptureResult.SENSOR_SENSITIVITY
                    );
        }

        IsoExpoSelector.ExpoPair selectorMotionPair =
                IsoExpoSelector.GenerateExpoPair(-1, this);

        Range<Long> exposureRange =
                mCameraCharacteristics.get(
                        CameraCharacteristics
                                .SENSOR_INFO_EXPOSURE_TIME_RANGE
                );

        Range<Integer> sensitivityRange =
                mCameraCharacteristics.get(
                        CameraCharacteristics
                                .SENSOR_INFO_SENSITIVITY_RANGE
                );

        final long motionMaximumExposureNs =
                66_666_667L; // approximately 1/15 second

        long minimumExposureNs =
                exposureRange != null
                        ? exposureRange.getLower()
                        : 1_000_000L;

        long maximumExposureNs =
                exposureRange != null
                        ? Math.min(
                                exposureRange.getUpper(),
                                motionMaximumExposureNs
                        )
                        : motionMaximumExposureNs;

        int minimumIso =
                sensitivityRange != null
                        ? sensitivityRange.getLower()
                        : 50;

        int maximumIso =
                sensitivityRange != null
                        ? sensitivityRange.getUpper()
                        : 12_800;

        double latestPreviewEnergy =
                latestPreviewExposureNs != null
                        && latestPreviewExposureNs > 0L
                        && latestPreviewIso != null
                        && latestPreviewIso > 0
                        ? ExposureIndex.time2sec(
                                latestPreviewExposureNs
                        ) * latestPreviewIso
                        : 0.0;

        double previewEnergy =
                getStableMotionPreviewEnergy(
                        latestPreviewEnergy
                );

        long desiredMotionExposureNs;
        int desiredMotionIso;

        if (previewEnergy > 0.0) {
            final long oneOver120Ns = 8_333_333L;
            final long oneOver60Ns = 16_666_667L;
            final long oneOver30Ns = 33_333_333L;
            final long oneOver20Ns = 50_000_000L;
            final long oneOver15Ns = 66_666_667L;

            /* Build 26212: fastest shutter whose required ISO remains reasonable. */
            int isoAt120 = (int) Math.round(previewEnergy / ExposureIndex.time2sec(oneOver120Ns));
            int isoAt60 = (int) Math.round(previewEnergy / ExposureIndex.time2sec(oneOver60Ns));
            int isoAt30 = (int) Math.round(previewEnergy / ExposureIndex.time2sec(oneOver30Ns));
            int isoAt20 = (int) Math.round(previewEnergy / ExposureIndex.time2sec(oneOver20Ns));

            double adaptiveBrightHeadroomEv = 0.0;

            if (isoAt120 < minimumIso) {
                /*
                 * Build 26213 bright-scene correction:
                 *
                 * 1/120 is not a fastest-shutter limit. If preserving preview
                 * exposure energy at 1/120 would require ISO below the sensor
                 * minimum, hold minimum ISO and shorten shutter continuously.
                 */
                final double brightnessBeyondMinimumIso =
                        Math.max(
                                1.0,
                                minimumIso
                                        / Math.max(
                                                1.0,
                                                isoAt120
                                        )
                        );

                /*
                 * Build 26218:
                 * Xiaomi preview AE is consistently highlight-biased in the
                 * tested outdoor HDR scenes. Do not subtract headroom here.
                 * Add a restrained +0.25 EV only in the continuous
                 * minimum-ISO bright branch so foregrounds receive cleaner
                 * source data without changing normal indoor exposure.
                 */
                adaptiveBrightHeadroomEv = -0.25;

                final double brightSceneHeadroomMultiplier =
                        Math.pow(
                                2.0,
                                -adaptiveBrightHeadroomEv
                        );

                final double brightSceneCaptureEnergy =
                        previewEnergy
                                * brightSceneHeadroomMultiplier;

                Log.d(
                        MOTION_LOG_TAG,
                        "MOTION_26217_ADAPTIVE_HEADROOM"
                                + " isoAt120=" + isoAt120
                                + " minimumIso=" + minimumIso
                                + " brightnessRatio="
                                + brightnessBeyondMinimumIso
                                + " captureCompensationEv="
                                + adaptiveBrightHeadroomEv
                                + " previewEnergy="
                                + previewEnergy
                                + " captureEnergy="
                                + brightSceneCaptureEnergy
                );

                desiredMotionExposureNs =
                        Math.round(
                                brightSceneCaptureEnergy
                                        / Math.max(1, minimumIso)
                                        * 1_000_000_000.0
                        );
            } else if (isoAt120 <= Math.min(maximumIso, 600)) {
                desiredMotionExposureNs = oneOver120Ns;
            } else if (isoAt60 <= Math.min(maximumIso, 2400)) {
                desiredMotionExposureNs = oneOver60Ns;
            } else if (isoAt30 <= Math.min(maximumIso, 5000)) {
                desiredMotionExposureNs = oneOver30Ns;
            } else if (isoAt20 <= Math.min(maximumIso, 6400)) {
                desiredMotionExposureNs = oneOver20Ns;
            } else {
                desiredMotionExposureNs = oneOver15Ns;
            }

            desiredMotionExposureNs = Math.max(minimumExposureNs,Math.min(maximumExposureNs,desiredMotionExposureNs));
            desiredMotionIso = (int) Math.round(previewEnergy / ExposureIndex.time2sec(desiredMotionExposureNs));
            desiredMotionIso = Math.max(minimumIso,Math.min(maximumIso,desiredMotionIso));

            Log.d(MOTION_LOG_TAG,"MOTION_ADAPTIVE_LADDER_26212"
                    + " camera=" + physicalID
                    + " previewExposureNs=" + latestPreviewExposureNs
                    + " previewIso=" + latestPreviewIso
                    + " previewEnergy=" + previewEnergy
                    + " minimumIso=" + minimumIso
                            + " brightContinuous="
                            + (isoAt120 < minimumIso)
                            + " brightHeadroomEv="
                            + adaptiveBrightHeadroomEv
                            + " isoAt120=" + isoAt120
                            + " isoAt60=" + isoAt60
                    + " isoAt30=" + isoAt30
                    + " isoAt20=" + isoAt20
                    + " selectedExposureNs=" + desiredMotionExposureNs
                    + " selectedIso=" + desiredMotionIso);
        } else {
            desiredMotionExposureNs = selectorMotionPair != null ? selectorMotionPair.exposure : maximumExposureNs;
            desiredMotionExposureNs = Math.max(minimumExposureNs,Math.min(maximumExposureNs,desiredMotionExposureNs));
            desiredMotionIso = selectorMotionPair != null ? selectorMotionPair.iso : minimumIso;
            desiredMotionIso = Math.max(minimumIso,Math.min(maximumIso,desiredMotionIso));
        }

        /*
         * Photon owns the full shutter x ISO pair for the controlled Motion
         * stack. Xiaomi AE remains only the live scene meter for the preview.
         * Photon's selector is primary, with a one-stop floor against severe
         * RAW underexposure and an upper limit at fresh AE-equivalent energy.
         */
        final long aeLadderExposureNs =
                desiredMotionExposureNs;
        final int aeLadderIso =
                desiredMotionIso;
        final double aeLadderEnergy =
                ExposureIndex.time2sec(
                        Math.max(1L, aeLadderExposureNs)
                ) * Math.max(1, aeLadderIso);

        boolean photonSelectorValid =
                selectorMotionPair != null
                        && selectorMotionPair.exposure > 0L
                        && selectorMotionPair.iso > 0;

        long photonExposureNs =
                photonSelectorValid
                        ? selectorMotionPair.exposure
                        : aeLadderExposureNs;

        photonExposureNs = Math.max(
                minimumExposureNs,
                Math.min(maximumExposureNs, photonExposureNs)
        );

        int photonIso =
                photonSelectorValid
                        ? selectorMotionPair.iso
                        : aeLadderIso;

        photonIso = Math.max(
                minimumIso,
                Math.min(maximumIso, photonIso)
        );

        double photonEnergy =
                ExposureIndex.time2sec(
                        Math.max(1L, photonExposureNs)
                ) * Math.max(1, photonIso);

        final double oneStopSafetyFloorEnergy =
                previewEnergy > 0.0
                        ? previewEnergy * 0.5
                        : aeLadderEnergy * 0.5;

        final double maximumAllowedEnergy =
                previewEnergy > 0.0
                        ? previewEnergy
                        : aeLadderEnergy;

        double selectedEnergy = photonEnergy;

        if (selectedEnergy < oneStopSafetyFloorEnergy) {
            selectedEnergy = oneStopSafetyFloorEnergy;
        }

        if (maximumAllowedEnergy > 0.0
                && selectedEnergy > maximumAllowedEnergy) {
            selectedEnergy = maximumAllowedEnergy;
        }

        int safetyAdjustedIso =
                (int) Math.round(
                        selectedEnergy
                                / ExposureIndex.time2sec(
                                        Math.max(1L, desiredMotionExposureNs)
                                )
                );

        safetyAdjustedIso = Math.max(minimumIso,Math.min(maximumIso,safetyAdjustedIso));

        /* Keep the adaptive ladder shutter; use Photon only as an energy safety check. */
        desiredMotionIso = safetyAdjustedIso;

        /*
         * Build 26223:
         * Re-project extreme-low-light exposure onto a practical ISO derived
         * from fresh preview metadata, preserving selected exposure energy.
         */
        final long preProjectionExposureNs = desiredMotionExposureNs;
        final int preProjectionIso = desiredMotionIso;

        final boolean practicalIsoProjectionEligible =
                previewEnergy > 0.0
                        && latestPreviewIso != null
                        && latestPreviewIso >= 2000
                        && desiredMotionIso
                                > Math.round(latestPreviewIso * 1.08)
                        && desiredMotionExposureNs < maximumExposureNs;

        int practicalIsoCeiling =
                latestPreviewIso != null
                        ? (int) Math.round(latestPreviewIso * 1.05)
                        : maximumIso;

        practicalIsoCeiling =
                Math.max(
                        minimumIso,
                        Math.min(maximumIso, practicalIsoCeiling)
                );

        boolean practicalIsoProjectionApplied = false;

        if (practicalIsoProjectionEligible) {
            long projectedExposureNs =
                    Math.round(
                            selectedEnergy
                                    / Math.max(1, practicalIsoCeiling)
                                    * 1_000_000_000.0
                    );

            projectedExposureNs =
                    Math.max(
                            desiredMotionExposureNs,
                            Math.min(maximumExposureNs, projectedExposureNs)
                    );

            int projectedIso =
                    (int) Math.round(
                            selectedEnergy
                                    / ExposureIndex.time2sec(
                                            Math.max(1L, projectedExposureNs)
                                    )
                    );

            projectedIso =
                    Math.max(
                            minimumIso,
                            Math.min(practicalIsoCeiling, projectedIso)
                    );

            double projectedEnergy =
                    ExposureIndex.time2sec(projectedExposureNs)
                            * projectedIso;

            if (projectedExposureNs > desiredMotionExposureNs
                    && projectedEnergy > 0.0) {
                desiredMotionExposureNs = projectedExposureNs;
                desiredMotionIso = projectedIso;
                practicalIsoProjectionApplied = true;
            }
        }

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26223_PRACTICAL_ISO_PROJECTION"
                        + " camera=" + physicalID
                        + " advertisedMaximumIso=" + maximumIso
                        + " previewExposureNs=" + latestPreviewExposureNs
                        + " previewIso=" + latestPreviewIso
                        + " previewEnergy=" + previewEnergy
                        + " selectedEnergy=" + selectedEnergy
                        + " practicalIsoCeiling=" + practicalIsoCeiling
                        + " eligible=" + practicalIsoProjectionEligible
                        + " applied=" + practicalIsoProjectionApplied
                        + " preExposureNs=" + preProjectionExposureNs
                        + " preIso=" + preProjectionIso
                        + " finalExposureNs=" + desiredMotionExposureNs
                        + " finalIso=" + desiredMotionIso
                        + " finalEnergy="
                        + (
                            ExposureIndex.time2sec(desiredMotionExposureNs)
                                    * desiredMotionIso
                        )
        );

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_PHOTON_ENERGY_POLICY"
                        + " camera=" + physicalID
                        + " previewExposureNs="
                        + latestPreviewExposureNs
                        + " previewIso="
                        + latestPreviewIso
                        + " previewEnergy="
                        + previewEnergy
                        + " aeLadderExposureNs="
                        + aeLadderExposureNs
                        + " aeLadderIso="
                        + aeLadderIso
                        + " selectorValid="
                        + photonSelectorValid
                        + " selectorExposureNs="
                        + (
                            selectorMotionPair != null
                                    ? selectorMotionPair.exposure
                                    : null
                        )
                        + " selectorIso="
                        + (
                            selectorMotionPair != null
                                    ? selectorMotionPair.iso
                                    : null
                        )
                        + " selectorEnergy="
                        + photonEnergy
                        + " safetyFloorEnergy="
                        + oneStopSafetyFloorEnergy
                        + " maximumEnergy="
                        + maximumAllowedEnergy
                        + " finalExposureNs="
                        + desiredMotionExposureNs
                        + " finalIso="
                        + desiredMotionIso
                        + " finalEnergy="
                        + (
                            ExposureIndex.time2sec(
                                    desiredMotionExposureNs
                            ) * desiredMotionIso
                        )
        );

        /*
         * Keep the established target-reporting structure. The authoritative
         * pair now comes from Photon's selector with the one-stop safety floor.
         * Continuous preview AE remains untouched.
         */
        final long legacyDesiredMotionExposureNs =
                desiredMotionExposureNs;
        final int legacyDesiredMotionIso =
                desiredMotionIso;

        final boolean rollingTargetAvailable = false;

        mMotionTargetExposureNs = desiredMotionExposureNs;
        mMotionTargetIso = desiredMotionIso;

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_CAPTURE_TARGET_REUSED"
                        + " camera=" + physicalID
                        + " rollingTargetAvailable="
                        + rollingTargetAvailable
                        + " rollingExposureNs="
                        + mMotionRequestedExposureNs
                        + " rollingIso="
                        + mMotionRequestedIso
                        + " legacyExposureNs="
                        + legacyDesiredMotionExposureNs
                        + " legacyIso="
                        + legacyDesiredMotionIso
                        + " finalExposureNs="
                        + desiredMotionExposureNs
                        + " finalIso="
                        + desiredMotionIso
        );

        final double desiredMotionEnergy =
                ExposureIndex.time2sec(
                        desiredMotionExposureNs
                ) * desiredMotionIso;

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_TARGET_EXPOSURE"
                        + " camera=" + physicalID
                        + " desiredExposureNs="
                        + desiredMotionExposureNs
                        + " desiredIso="
                        + desiredMotionIso
                        + " previewExposureNs="
                        + latestPreviewExposureNs
                        + " previewIso="
                        + latestPreviewIso
                        + " selectorExposureNs="
                        + (
                            selectorMotionPair != null
                                    ? selectorMotionPair.exposure
                                    : null
                        )
                        + " selectorIso="
                        + (
                            selectorMotionPair != null
                                    ? selectorMotionPair.iso
                                    : null
                        )
                        + " exposureRange="
                        + exposureRange
                        + " sensitivityRange="
                        + sensitivityRange
        );

        final double maximumExposureDifferenceEv = 0.75;
        final double maximumShutterDifferenceEv = 0.50;
        final double maximumIsoDifferenceEv = 0.75;
        final long maximumCandidateAgeNs =
                2_000_000_000L;

        final ArrayList<ImageFrame> compatibleCandidates =
                new ArrayList<>();

        int rejectedMissingMetadata = 0;
        int rejectedExposureMismatch = 0;
        int rejectedShutterMismatch = 0;
        int rejectedIsoMismatch = 0;
        int rejectedTooOld = 0;

        for (ImageFrame frame : candidates) {
            Long actualExposureNs =
                    mZslExposureTimeNs.get(frame.timestamp);

            Integer actualIso =
                    mZslSensitivity.get(frame.timestamp);

            long ageNs =
                    Math.abs(
                            mMotionShutterTimestampNs
                                    - frame.timestamp
                    );

            boolean metadataValid =
                    actualExposureNs != null
                            && actualExposureNs > 0L
                            && actualIso != null
                            && actualIso > 0;

            double actualEnergy =
                    metadataValid
                            ? ExposureIndex.time2sec(
                                    actualExposureNs
                            ) * actualIso
                            : 0.0;

            double exposureDifferenceEv =
                    metadataValid
                            && desiredMotionEnergy > 0.0
                            && actualEnergy > 0.0
                            ? Math.abs(
                                    Math.log(
                                            actualEnergy
                                                    / desiredMotionEnergy
                                    ) / Math.log(2.0)
                            )
                            : Double.POSITIVE_INFINITY;

            double shutterDifferenceEv =
                    metadataValid
                            && desiredMotionExposureNs > 0L
                            ? Math.abs(
                                    Math.log(
                                            (double) actualExposureNs
                                                    / desiredMotionExposureNs
                                    ) / Math.log(2.0)
                            )
                            : Double.POSITIVE_INFINITY;

            double isoDifferenceEv =
                    metadataValid
                            && desiredMotionIso > 0
                            ? Math.abs(
                                    Math.log(
                                            (double) actualIso
                                                    / desiredMotionIso
                                    ) / Math.log(2.0)
                            )
                            : Double.POSITIVE_INFINITY;

            boolean ageValid =
                    ageNs <= maximumCandidateAgeNs;

            boolean exposureCompatible =
                    exposureDifferenceEv
                            <= maximumExposureDifferenceEv;

            boolean shutterCompatible =
                    shutterDifferenceEv
                            <= maximumShutterDifferenceEv;

            boolean isoCompatible =
                    isoDifferenceEv
                            <= maximumIsoDifferenceEv;

            if (metadataValid
                    && ageValid
                    && exposureCompatible
                    && shutterCompatible
                    && isoCompatible) {

                compatibleCandidates.add(frame);
            } else {
                if (!metadataValid) {
                    rejectedMissingMetadata++;
                } else if (!ageValid) {
                    rejectedTooOld++;
                } else if (!shutterCompatible) {
                    rejectedShutterMismatch++;
                } else if (!isoCompatible) {
                    rejectedIsoMismatch++;
                } else {
                    rejectedExposureMismatch++;
                }

                Log.d(
                        MOTION_LOG_TAG,
                        "FRAME_PREFILTER"
                                + " timestamp="
                                + frame.timestamp
                                + " ageNs="
                                + ageNs
                                + " exposureNs="
                                + actualExposureNs
                                + " iso="
                                + actualIso
                                + " exposureDifferenceEv="
                                + exposureDifferenceEv
                                + " shutterDifferenceEv="
                                + shutterDifferenceEv
                                + " isoDifferenceEv="
                                + isoDifferenceEv
                                + " targetExposureNs="
                                + desiredMotionExposureNs
                                + " targetIso="
                                + desiredMotionIso
                                + " decision="
                                + (
                                    !metadataValid
                                            ? "REJECTED_INVALID_METADATA"
                                            : !ageValid
                                                    ? "REJECTED_TOO_OLD"
                                                    : !shutterCompatible
                                                            ? "REJECTED_SHUTTER_MISMATCH"
                                                            : !isoCompatible
                                                                    ? "REJECTED_ISO_MISMATCH"
                                                                    : "REJECTED_EXPOSURE_MISMATCH"
                                )
                );

                mZslExposureEnergy.remove(frame.timestamp);
                mZslExposureTimeNs.remove(frame.timestamp);
                mZslSensitivity.remove(frame.timestamp);
                mZslRawSharpness.remove(frame.timestamp);
                mZslOisMotion.remove(frame.timestamp);
                mZslOisMode.remove(frame.timestamp);
                mZslEisMode.remove(frame.timestamp);

                frame.close();
            }
        }

        candidates.clear();
        candidates.addAll(compatibleCandidates);

        Log.d(
                MOTION_LOG_TAG,
                "BUFFER_COMPATIBILITY"
                        + " targetExposureNs="
                        + desiredMotionExposureNs
                        + " targetIso="
                        + desiredMotionIso
                        + " previewExposureNs="
                        + latestPreviewExposureNs
                        + " previewIso="
                        + latestPreviewIso
                        + " compatible="
                        + candidates.size()
                        + " rejectedMissingMetadata="
                        + rejectedMissingMetadata
                        + " rejectedExposureMismatch="
                        + rejectedExposureMismatch
                        + " rejectedShutterMismatch="
                        + rejectedShutterMismatch
                        + " rejectedIsoMismatch="
                        + rejectedIsoMismatch
                        + " rejectedTooOld="
                        + rejectedTooOld
        );

        /*
         * Controlled hybrid capture:
         * keep at most eight recent pre-shutter frames, but always reserve at
         * least one post-shutter frame so the final stack represents the
         * moment the user pressed the shutter. Any missing frames are captured
         * by the proven controlled post-shutter path.
         */
        candidates.sort(
                (left, right) ->
                        Long.compare(
                                right.timestamp,
                                left.timestamp
                        )
        );

        final int maximumPreFrames =
                Math.min(
                        MOTION_PREBUFFER_MAX_FRAMES,
                        requestedFrames
                );

        /*
         * Build 26165 color-stability checkpoint:
         *
         * The rolling RAW candidates are produced by the live
         * TEMPLATE_PREVIEW request with preview + RAW targets, while the
         * controlled post-shutter RAWs use TEMPLATE_STILL_CAPTURE with a RAW
         * target. Mixing those two HAL paths has produced intermittent
         * green/cyan output even when exposure and AWB metadata appear close.
         *
         * Keep collecting and validating the rolling ring, but do not feed
         * its frames into HDRX until every RAW carries its own complete
         * CaptureResult/CaptureRequest and both paths are proven compatible.
         * The requested stack is therefore filled with homogeneous
         * post-shutter still-capture RAWs.
         */
        final int preFramesToUse = 0;

        synchronized (mMotionBurstLock) {
            for (ImageFrame old : mMotionPreselectedFrames) {
                if (old != null) {
                    old.close();
                }
            }

            mMotionPreselectedFrames.clear();
            mMotionPreselectedExposureTimeNs.clear();
            mMotionPreselectedSensitivity.clear();

            for (int i = 0; i < candidates.size(); i++) {
                ImageFrame frame = candidates.get(i);

                Long exposureNs =
                        mZslExposureTimeNs.remove(
                                frame.timestamp
                        );

                Integer iso =
                        mZslSensitivity.remove(
                                frame.timestamp
                        );

                mZslExposureEnergy.remove(
                        frame.timestamp
                );

                if (i < preFramesToUse
                        && exposureNs != null
                        && exposureNs > 0L
                        && iso != null
                        && iso > 0) {

                    mMotionPreselectedFrames.add(frame);

                    mMotionPreselectedExposureTimeNs.put(
                            frame.timestamp,
                            exposureNs
                    );

                    mMotionPreselectedSensitivity.put(
                            frame.timestamp,
                            iso
                    );
                } else {
                    frame.close();
                }
            }

            mMotionCombinedRequestedFrames =
                    requestedFrames;

            mMotionPostShutterFrameOverride =
                    Math.max(
                            1,
                            requestedFrames
                                    - mMotionPreselectedFrames.size()
                    );
        }

        Log.d(
                MOTION_LOG_TAG,
                "PREBUFFER_TOP_UP"
                        + " requested="
                        + requestedFrames
                        + " pre="
                        + preFramesToUse
                        + " post="
                        + mMotionPostShutterFrameOverride
                        + " maxPre="
                        + maximumPreFrames
                        + " colorStabilityPostOnly=true"
                        + " rollingCandidatesStillCollected="
                        + candidates.size()
        );

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_26165_HOMOGENEOUS_RAW_STACK"
                        + " preframesContributing=0"
                        + " postframesRequested="
                        + mMotionPostShutterFrameOverride
                        + " previewTemplateRawExcluded=true"
                        + " stillTemplateRawOnly=true"
                        + " shutterPolicyUnchanged=true"
        );

        Log.d(
                MOTION_LOG_TAG,
                "MOTION_POST_TARGET_FROM_FRESH_AE"
                        + " camera=" + physicalID
                        + " exposureNs="
                        + mMotionTargetExposureNs
                        + " iso="
                        + mMotionTargetIso
                        + " preselectedFrames="
                        + mMotionPreselectedFrames.size()
                        + " requestedTotal="
                        + mMotionCombinedRequestedFrames
        );

        mZslCapturing = false;
        captureDedicatedMotionFallback();
        return;

    }


    /*
     * Known-good 0.9726135 post-shutter implementation retained only for the
     * short period after camera/lens startup when the rolling ring is empty.
     */
    private void captureDedicatedMotionFallback() {
        final boolean previousCaptureState = mZslCapturing;

        try {
            mZslCapturing = false;

            Log.d(
                    MOTION_LOG_TAG,
                    "POST_SHUTTER_FALLBACK_START"
            );

            captureStillPicturePostShutter();
        } finally {
            if (previousCaptureState) {
                mZslCapturing = false;
            }
        }
    }

    private void finalizeDedicatedMotionBurst(
            int cameraSequenceFrameCount
    ) {
        processExecutor.execute(() -> {
            final long startMs =
                    android.os.SystemClock.elapsedRealtime();

            final long maximumWaitMs = Math.max(
                    5_000L,
                    Math.min(
                            15_000L,
                            mMotionBurstExpectedFrames * 500L
                    )
            );

            int lastSize = -1;
            long unchangedSinceMs = startMs;

            while (true) {
                int currentSize;

                synchronized (mMotionBurstLock) {
                    currentSize = mMotionBurstFrames.size();
                }

                long nowMs =
                        android.os.SystemClock.elapsedRealtime();

                if (currentSize != lastSize) {
                    lastSize = currentSize;
                    unchangedSinceMs = nowMs;
                }

                boolean complete =
                        currentSize >= mMotionBurstExpectedFrames;

                boolean settled =
                        currentSize >= 2
                                && nowMs - unchangedSinceMs >= 750L
                                && nowMs - startMs >= 1_250L;

                boolean timedOut =
                        nowMs - startMs >= maximumWaitMs;

                if (complete || settled || timedOut) {
                    Log.d(
                            TAG,
                            "Dedicated Motion delivery finished:"
                                    + " requested="
                                    + mMotionBurstExpectedFrames
                                    + " cameraSequence="
                                    + cameraSequenceFrameCount
                                    + " raw="
                                    + currentSize
                                    + " complete="
                                    + complete
                                    + " settled="
                                    + settled
                                    + " timedOut="
                                    + timedOut
                    );
                    break;
                }

                try {
                    Thread.sleep(10L);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }

            if (!mMotionBurstFinalized.compareAndSet(false, true)) {
                Log.w(
                        TAG,
                        "Ignoring duplicate Motion finalization"
                );
                return;
            }

            final ArrayList<ImageFrame> completedFrames;

            synchronized (mMotionBurstLock) {
                mMotionBurstActive = false;

                completedFrames =
                        new ArrayList<>(
                                mMotionPreselectedFrames
                        );

                completedFrames.addAll(
                        mMotionBurstFrames
                );

                selectMotionValidatedBlackLevelLocked(
                        completedFrames
                );

                mMotionPreselectedFrames.clear();
                mMotionBurstFrames.clear();
                closePendingMotionFramesLocked();
            }

            if (completedFrames.size() < 2) {
                Log.e(
                        TAG,
                        "Dedicated Motion HDRX cancelled: only "
                                + completedFrames.size()
                                + " matched RAW frame(s)"
                );

                for (ImageFrame frame : completedFrames) {
                    if (frame != null) {
                        frame.close();
                    }
                }

                PhotonCamera.getGyro().CompleteSequence();

                recoverDedicatedMotionCapture(
                        "not_enough_matched_raw"
                );

                cameraEventsListener.onProcessingError(
                        "Not enough matched Motion RAW frames were delivered"
                );
                return;
            }

            ArrayList<GyroBurst> completedGyro =
                    new ArrayList<>(BurstShakiness);

            if (completedGyro.size() > completedFrames.size()) {
                completedGyro = new ArrayList<>(
                        completedGyro.subList(
                                0,
                                completedFrames.size()
                        )
                );
            }

            PhotonCamera.getGyro().CompleteSequence();

            /*
             * The common HDRX processor still reads IMAGE_BUFFER, but only
             * this finalized immutable Motion batch is placed there. Photo
             * and Night never share collection state with Motion.
             */
            synchronized (SaverImplementation.IMAGE_BUFFER) {
                SaverImplementation.IMAGE_BUFFER.clear();
                SaverImplementation.IMAGE_BUFFER.addAll(
                        completedFrames
                );
            }

            /*
             * DefaultSaver.runRaw() waits until bufferLock becomes false.
             * Normal Photo/Night collection releases this flag through
             * RAW16Saver.addImage(). Dedicated Motion bypasses addImage(), so
             * signal explicitly that its finalized buffer is ready.
             */
            IsoExpoSelector.fullpairs.clear();
            synchronized (mMotionBurstLock) {
                for (int i = 0; i < completedFrames.size(); i++) {
                    ImageFrame completedFrame = completedFrames.get(i);
                    IsoExpoSelector.ExpoPair actualPair =
                            IsoExpoSelector.GenerateExpoPair(i, this);

                    Long actualExposureNs =
                            mMotionBurstExposureTimeNs.get(
                                    completedFrame.timestamp
                            );

                    Integer actualIso =
                            mMotionBurstSensitivity.get(
                                    completedFrame.timestamp
                            );

                    if (actualExposureNs == null) {
                        actualExposureNs =
                                mMotionPreselectedExposureTimeNs.get(
                                        completedFrame.timestamp
                                );
                    }

                    if (actualIso == null) {
                        actualIso =
                                mMotionPreselectedSensitivity.get(
                                        completedFrame.timestamp
                                );
                    }

                    if (actualExposureNs != null && actualExposureNs > 0L) {
                        actualPair.exposure = actualExposureNs;
                    }
                    if (actualIso != null && actualIso > 0) {
                        actualPair.iso = actualIso;
                    }

                    actualPair.layerMpy = 1.0f;
                    completedFrame.pair = actualPair;
                    completedFrame.diagnosticExposureNs =
                            actualPair.exposure;
                    completedFrame.diagnosticIso =
                            actualPair.iso;
                    Float actualOisMotion =
                            mMotionBurstOisMotion.get(
                                    completedFrame.timestamp
                            );
                    completedFrame.diagnosticOisMotion =
                            actualOisMotion != null
                                    ? actualOisMotion
                                    : 0.0f;
                    IsoExpoSelector.fullpairs.add(actualPair);

                    Log.d(MOTION_LOG_TAG,
                            "CONTROLLED_ACTUAL_EXPO_PAIR index=" + i
                                    + " timestamp=" + completedFrame.timestamp
                                    + " exposureNs=" + actualPair.exposure
                                    + " iso=" + actualPair.iso);
                }
                mMotionBurstExposureTimeNs.clear();
                mMotionBurstSensitivity.clear();
                mMotionBurstOisMotion.clear();
                mMotionPreselectedExposureTimeNs.clear();
                mMotionPreselectedSensitivity.clear();
            }

            /*
             * HDRX looks up exposure energy by each RAW timestamp. The
             * post-shutter callback populated mExposures only for controlled
             * burst frames, so add every finalized pre-shutter frame here
             * from its actual matched shutter and ISO metadata.
             */
            for (ImageFrame completedFrame : completedFrames) {
                if (completedFrame == null
                        || completedFrame.pair == null
                        || completedFrame.pair.exposure <= 0L
                        || completedFrame.pair.iso <= 0) {
                    continue;
                }

                mExposures.put(
                        completedFrame.timestamp,
                        ExposureIndex.time2sec(
                                completedFrame.pair.exposure
                        ) * completedFrame.pair.iso
                );
            }

            Log.d(
                    MOTION_LOG_TAG,
                    "COMBINED_EXPOSURE_MAP_READY"
                            + " frames=" + completedFrames.size()
                            + " entries=" + mExposures.size()
            );

            Log.d(
                    MOTION_LOG_TAG,
                    "MOTION_26215_DELIVERY_SUMMARY"
                            + " submitted="
                            + mMotionDiagnosticSubmittedFrames
                            + " completedResults="
                            + mMotionDiagnosticCompletedResults
                            + " matchedRaw="
                            + mMotionDiagnosticMatchedRawFrames
                            + " finalFrames="
                            + completedFrames.size()
                            + " pendingRaw="
                            + mMotionBurstPendingFrames.size()
                            + " captureFailures="
                            + mMotionDiagnosticCaptureFailures
                            + " cameraSequence="
                            + cameraSequenceFrameCount
            );

            /*
             * Gyro history currently exists only for the post-shutter burst.
             * Do not allow a shorter list to become index-shifted against the
             * combined RAW stack. Pad missing pre-shutter positions with
             * neutral entries copied from the nearest available sample.
             */
            if (!completedFrames.isEmpty()
                    && completedGyro.size() < completedFrames.size()) {

                GyroBurst fallbackGyro =
                        !completedGyro.isEmpty()
                                ? completedGyro.get(0)
                                : null;

                while (fallbackGyro != null
                        && completedGyro.size()
                                < completedFrames.size()) {
                    completedGyro.add(0, fallbackGyro);
                }

                Log.d(
                        MOTION_LOG_TAG,
                        "COMBINED_GYRO_PADDED"
                                + " frames=" + completedFrames.size()
                                + " gyro=" + completedGyro.size()
                                + " fallbackAvailable="
                                + (fallbackGyro != null)
                );
            }

            mImageSaver.implementation.bufferLock = false;

            Log.d(
                    TAG,
                    "Dedicated Motion buffer handed to saver: frames="
                            + completedFrames.size()
                            + " bufferLock="
                            + mImageSaver.implementation.bufferLock
            );

            /*
             * Normal Photo/Night collection calls ImageSaver.initProcess(),
             * which records the ImageReader format. Dedicated Motion copies
             * RAW frames directly and therefore must set it explicitly.
             */
            mImageSaver.setImageFormat(
                    android.graphics.ImageFormat.RAW_SENSOR
            );

            mImageSaver.updateFrameCount(completedFrames.size());
            mMeasuredFrameCnt = completedFrames.size();

            Log.d(
                    TAG,
                    "Dedicated Motion HDRX format="
                            + android.graphics.ImageFormat.RAW_SENSOR
            );

            try {
                Log.d(
                        TAG,
                        "Starting dedicated Motion HDRX with "
                                + completedFrames.size()
                                + " RAW frames and "
                                + completedGyro.size()
                                + " gyro frames"
                );

                mImageSaver.runRaw(
                        mCameraCharacteristics,
                        mCaptureResult,
                        mCaptureRequest,
                        completedGyro,
                        cameraRotation,
                        new HashMap<>(mExposures)
                );
            } catch (Exception e) {
                Log.e(
                        TAG,
                        "Dedicated Motion runRaw: "
                                + Log.getStackTraceString(e)
                );

                cameraEventsListener.onProcessingError(
                        e.getLocalizedMessage()
                );
            } finally {
                mImageSaver.implementation.bufferLock = false;
                mZslCapturing = false;
                mMotionPostShutterFrameOverride = 0;
                mMotionCombinedRequestedFrames = 0;

                synchronized (mMotionBurstLock) {
                    mMotionBurstDynamicBlackLevel.clear();
                }

                mMotionValidatedBlackLevel = null;
                mMotionValidatedBlackLevelSource =
                        "processingComplete";

                /*
                 * The preview builder is restored to Xiaomi AE by the normal
                 * preview recovery path. Reset the passive-ring state so five
                 * fresh AE metadata frames are observed, then reconfigure one
                 * controlled repeating preview+RAW request for the next shot.
                 */
                /*
                 * Preserve the rolling target so preview can resume without
                 * an AE-on brightness flash. Clear only the one-shot
                 * post-shutter target.
                 */
                mMotionPreviewMetadataFrames = 0;
                mMotionTargetExposureNs = 0L;
                mMotionTargetIso = 0;

                synchronized (mZslBufferLock) {
                    while (!mZslRingBuffer.isEmpty()) {
                        ImageFrame stale =
                                mZslRingBuffer.pollFirst();

                        if (stale != null) {
                            stale.close();
                        }
                    }

                    mZslExposureEnergy.clear();
                    mZslExposureTimeNs.clear();
                    mZslSensitivity.clear();
                    mZslRawSharpness.clear();
                    mZslOisMotion.clear();
                    mZslOisMode.clear();
                    mZslEisMode.clear();
                }

                startMotionPrebufferPump();

                mMotionRollingExposureConfigured = true;
                mMotionTargetExposureNs = 0L;
                mMotionTargetIso = 0;

                mBackgroundHandler.post(() -> {
                    try {
                        if (mPreviewRequestBuilder != null
                                && mCaptureSession != null) {

                            mPreviewRequestBuilder.set(
                                    CaptureRequest.CONTROL_MODE,
                                    CaptureRequest.CONTROL_MODE_AUTO
                            );

                            mPreviewRequestBuilder.set(
                                    CaptureRequest.CONTROL_AE_MODE,
                                    CaptureRequest.CONTROL_AE_MODE_ON
                            );

                            mPreviewRequestBuilder.set(
                                    CaptureRequest.SENSOR_EXPOSURE_TIME,
                                    null
                            );

                            mPreviewRequestBuilder.set(
                                    CaptureRequest.SENSOR_SENSITIVITY,
                                    null
                            );

                            configureMotionStabilizationRequest(
                                    mPreviewRequestBuilder
                            );

                            mPreviewInputRequest =
                                    mPreviewRequestBuilder.build();

                            mCaptureSession.setRepeatingRequest(
                                    mPreviewInputRequest,
                                    mCaptureCallback,
                                    mBackgroundHandler
                            );

                            Log.d(
                                    MOTION_LOG_TAG,
                                    "MOTION_CONTINUOUS_AE_RESTORED"
                                            + " camera=" + physicalID
                                            + " noManualExposureRestore=true"
                                            + " previewSurfaceExcludedFromBurst=true"
                            );
                        }

                        startMotionPrebufferPump();
                    } catch (Exception e) {
                        Log.e(
                                MOTION_LOG_TAG,
                                "CONTROLLED_FINISH_PREVIEW_FAILED "
                                        + Log.getStackTraceString(e)
                        );
                    }
                });

                Log.d(
                        MOTION_LOG_TAG,
                        "CONTROLLED_HDRX_FINISHED"
                                + " rawSurfaceStayedAttached=true"
                                + " captureStateReleased=true"
                                + " passiveRingReset=true"
                );
            }
        });
    }

    private void captureStillPicture() {
        if (isZslMode()) {
            triggerZslCapture();
            return;
        }

        captureStillPicturePostShutter();
    }

    private void captureStillPicturePostShutter() {
        try {
            if (null == mCameraDevice) {
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
                if (
                        selectedMode != CameraMode.MOTION
                                && (
                                    frametime > 0.06
                                            && !isDualSession
                                        || selectedMode
                                                == CameraMode.RAWVIDEO
                                        || selectedMode
                                                == CameraMode.UNLIMITED
                                        || (!IsoExpoSelector.HDR)
                                )
                ) {
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
            int frameCount =
                    FrameNumberSelector.getFrames();

            if (PhotonCamera.getSettings().selectedMode
                    == CameraMode.MOTION
                    && mMotionPostShutterFrameOverride > 0) {

                frameCount =
                        mMotionPostShutterFrameOverride;

                Log.d(
                        MOTION_LOG_TAG,
                        "POST_SHUTTER_TOP_UP_COUNT"
                                + " postFrames="
                                + frameCount
                                + " combinedRequested="
                                + mMotionCombinedRequestedFrames
                );
            }

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

                boolean motionMode =
                        PhotonCamera.getSettings().selectedMode
                                == CameraMode.MOTION;

                if (motionMode) {
                    /*
                     * Select the Motion exposure exactly once. Every request in the
                     * burst must use the same ISO and shutter, matching the classic
                     * equal-exposure HDR+ strategy.
                     */
                    IsoExpoSelector.setExpo(
                            captureBuilder,
                            0,
                            this
                    );

                    Long selectedExposure = captureBuilder.get(
                            CaptureRequest.SENSOR_EXPOSURE_TIME
                    );

                    Integer selectedIso = captureBuilder.get(
                            CaptureRequest.SENSOR_SENSITIVITY
                    );

                    long motionExposure =
                            mMotionTargetExposureNs > 0L
                                    ? mMotionTargetExposureNs
                                    : (
                                        selectedExposure != null
                                                ? selectedExposure
                                                : IsoExpoSelector
                                                        .lastSelectedExposure
                                    );

                    int motionIso =
                            mMotionTargetIso > 0
                                    ? mMotionTargetIso
                                    : (
                                        selectedIso != null
                                                ? selectedIso
                                                : mPreviewIso
                                    );

                    /*
                     * Use the exact shutter-time Motion target. In low light
                     * this prioritizes approximately 1/15 second and reduces
                     * ISO for both ID2 and ID5. Camera capability ranges are
                     * still enforced below.
                     */
                    Range<Long> exposureRange =
                            mCameraCharacteristics.get(
                                    CameraCharacteristics
                                            .SENSOR_INFO_EXPOSURE_TIME_RANGE
                            );

                    motionExposure = Math.max(
                            exposureRange != null
                                    ? exposureRange.getLower()
                                    : 1L,
                            motionExposure
                    );

                    if (exposureRange != null) {
                        motionExposure = Math.max(
                                exposureRange.getLower(),
                                Math.min(
                                        exposureRange.getUpper(),
                                        motionExposure
                                )
                        );
                    }

                    Range<Integer> sensitivityRange =
                            mCameraCharacteristics.get(
                                    CameraCharacteristics
                                            .SENSOR_INFO_SENSITIVITY_RANGE
                            );

                    if (sensitivityRange != null) {
                        motionIso = Math.max(
                                sensitivityRange.getLower(),
                                Math.min(
                                        sensitivityRange.getUpper(),
                                        motionIso
                                )
                        );
                    }

                    captureBuilder.set(
                            CaptureRequest.CONTROL_AE_MODE,
                            CaptureRequest.CONTROL_AE_MODE_OFF
                    );

                    captureBuilder.set(
                            CaptureRequest.SENSOR_EXPOSURE_TIME,
                            motionExposure
                    );

                    captureBuilder.set(
                            CaptureRequest.SENSOR_SENSITIVITY,
                            motionIso
                    );

                    IsoExpoSelector.lastSelectedExposure =
                            motionExposure;

                    Log.d(
                            MOTION_LOG_TAG,
                            "CONTROLLED_REQUEST_TARGET"
                                    + " camera=" + physicalID
                                    + " frames=" + frameCount
                                    + " requestedExposureNs="
                                    + motionExposure
                                    + " requestedIso="
                                    + motionIso
                                    + " exposureRange=" + exposureRange
                                    + " minimumExposureAppliedNs="
                                    + (
                                        exposureRange != null
                                                ? exposureRange.getLower()
                                                : 1L
                                    )
                                    + " sensitivityRange="
                                    + sensitivityRange
                    );

                    /*
                     * Build 26293:
                     * Keep every configured normal Motion frame and append one
                     * additional short RAW. The short frame remains auxiliary
                     * and never enters motionmerge11.
                     * MOTION_26293_EXTRA_SHORT_FRAME_NO_TEMPORAL_PENALTY
                     */
                    final int motionNormalFrameCount = frameCount;
                    final boolean motionHighlightBracketEnabled =
                            motionNormalFrameCount >= 6
                                    && motionExposure <= 33_333_333L
                                    && motionIso <= 3200;
                    /* MOTION_26295_DEEPER_AUXILIARY_DIAGNOSTIC */
                    final double motionHighlightFrameEv = 2.30;
                    final long motionHighlightExposure =
                            motionHighlightBracketEnabled
                                    ? Math.max(
                                            exposureRange != null
                                                    ? exposureRange.getLower()
                                                    : 1L,
                                            Math.round(
                                                    motionExposure
                                                            / Math.pow(
                                                                    2.0,
                                                                    motionHighlightFrameEv
                                                            )
                                            )
                                      )
                                    : motionExposure;

                    if (motionHighlightBracketEnabled) {
                        times = java.util.Arrays.copyOf(
                                times,
                                motionNormalFrameCount + 1
                        );
                        frameCount = motionNormalFrameCount + 1;
                    }

                    for (int i = 0; i < motionNormalFrameCount; i++) {
                        captureBuilder.set(
                                CaptureRequest.SENSOR_EXPOSURE_TIME,
                                motionExposure
                        );
                        captureBuilder.set(
                                CaptureRequest.SENSOR_SENSITIVITY,
                                motionIso
                        );
                        CaptureRequest frameRequest = captureBuilder.build();
                        captures.add(frameRequest);
                        times[i] = motionExposure;
                        mCaptureRequest = frameRequest;
                    }

                    if (motionHighlightBracketEnabled) {
                        captureBuilder.set(
                                CaptureRequest.SENSOR_EXPOSURE_TIME,
                                motionHighlightExposure
                        );
                        captureBuilder.set(
                                CaptureRequest.SENSOR_SENSITIVITY,
                                motionIso
                        );
                        CaptureRequest highlightRequest =
                                captureBuilder.build();
                        captures.add(highlightRequest);
                        times[motionNormalFrameCount] =
                                motionHighlightExposure;
                        /*
                         * Build 26294:
                         * Do not replace the authoritative normal-stack request
                         * with the appended short auxiliary request.
                         * MOTION_26294_NORMAL_METADATA_REQUEST_OWNERSHIP
                         */
                        Log.d(
                                MOTION_LOG_TAG,
                                "MOTION_26293_AUXILIARY_REQUEST"
                                        + " normalFrameCount="
                                        + motionNormalFrameCount
                                        + " totalFrames=" + frameCount
                                        + " normalExposureNs="
                                        + motionExposure
                                        + " shortExposureNs="
                                        + motionHighlightExposure
                                        + " iso=" + motionIso
                                        + " bracketEv="
                                        + motionHighlightFrameEv
                        );
                    }

                    captureBuilder.set(
                            CaptureRequest.SENSOR_EXPOSURE_TIME,
                            motionExposure
                    );
                } else {
                    /*
                     * Preserve the existing Photo and Night exposure sequence.
                     */
                    for (int i = 0; i < frameCount; i++) {
                        IsoExpoSelector.setExpo(
                                captureBuilder,
                                i,
                                this
                        );

                        times[i] =
                                IsoExpoSelector.lastSelectedExposure;

                        CaptureRequest frameRequest =
                                captureBuilder.build();

                        captures.add(frameRequest);
                        mCaptureRequest = frameRequest;
                    }
                }

                PhotonCamera.getGyro().PrepareGyroBurst(
                        times,
                        BurstShakiness
                );
            }

            //img
            Log.d(TAG, "FrameCount:" + frameCount);
            mImageSaver = new ImageSaver(cameraEventsListener);
            mImageSaver.setFrameCount(frameCount);

            if (PhotonCamera.getSettings().selectedMode
                    == CameraMode.MOTION) {

                synchronized (mMotionBurstLock) {
                    mMotionBurstFrames.clear();
                    mMotionBurstExpectedFrames = Math.max(1, frameCount);
                    mMotionBurstFirstTimestampNs = 0L;
                    closePendingMotionFramesLocked();
                    mMotionBurstExposureTimeNs.clear();
                    mMotionBurstSensitivity.clear();
                    mMotionBurstOisMotion.clear();
                    mMotionBurstDynamicBlackLevel.clear();
                    mMotionDiagnosticSubmittedFrames = Math.max(1, frameCount);
                    mMotionDiagnosticCompletedResults = 0;
                    mMotionDiagnosticMatchedRawFrames = 0;
                    mMotionDiagnosticCaptureFailures = 0;
                    mMotionValidatedBlackLevel = null;
                    mMotionValidatedBlackLevelSource =
                            "collecting";
                    mMotionBurstFinalized.set(false);
                    mMotionBurstActive = false;
                }

                Log.d(
                        TAG,
                        "Dedicated Motion burst started: expected="
                                + mMotionBurstExpectedFrames
                );
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
                        if (PhotonCamera.getSettings().selectedMode
                                == CameraMode.MOTION) {
                            mMotionBurstFirstTimestampNs = timestamp;
                            Log.d(MOTION_LOG_TAG,
                                    "CONTROLLED_BURST_FIRST_TIMESTAMP timestamp="
                                            + timestamp);
                        }
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
                        if (timeKey != null) {
                            long actualExposureNs = (long) timeKey;
                            double exposureTime = ExposureIndex.time2sec(actualExposureNs);
                            mExposures.put((long) time, exposureTime * iso);

                            if (PhotonCamera.getSettings().selectedMode
                                    == CameraMode.MOTION) {
                                synchronized (mMotionBurstLock) {
                                    mMotionBurstExposureTimeNs.put(
                                            (long) time, actualExposureNs);
                                    mMotionBurstSensitivity.put(
                                            (long) time, iso);

                                    float controlledOisMotion = 0.0f;
                                    if (Build.VERSION.SDK_INT
                                            >= Build.VERSION_CODES.P) {
                                        OisSample[] controlledOisSamples =
                                                result.get(
                                                        CaptureResult
                                                                .STATISTICS_OIS_SAMPLES
                                                );
                                        controlledOisMotion =
                                                calculateOisMotion(
                                                        controlledOisSamples
                                                );
                                    }
                                    mMotionBurstOisMotion.put(
                                            (long) time,
                                            controlledOisMotion
                                    );
                                    mMotionDiagnosticCompletedResults++;

                                    float[] dynamicBlackLevel =
                                            result.get(
                                                    CaptureResult
                                                            .SENSOR_DYNAMIC_BLACK_LEVEL
                                            );

                                    Integer dynamicWhiteLevel =
                                            result.get(
                                                    CaptureResult
                                                            .SENSOR_DYNAMIC_WHITE_LEVEL
                                            );

                                    int validationWhiteLevel =
                                            dynamicWhiteLevel != null
                                                    && dynamicWhiteLevel > 0
                                                    ? dynamicWhiteLevel
                                                    : getMotionStaticWhiteLevel();

                                    boolean dynamicBlackLevelValid =
                                            isValidMotionDynamicBlackLevel(
                                                    dynamicBlackLevel,
                                                    validationWhiteLevel
                                            );

                                    if (dynamicBlackLevelValid) {
                                        mMotionBurstDynamicBlackLevel.put(
                                                (long) time,
                                                dynamicBlackLevel.clone()
                                        );
                                    } else {
                                        mMotionBurstDynamicBlackLevel.remove(
                                                (long) time
                                        );
                                    }

                                    Log.d(
                                            MOTION_LOG_TAG,
                                            "CONTROLLED_BLACK_LEVEL"
                                                    + " timestamp=" + time
                                                    + " dynamic="
                                                    + Arrays.toString(
                                                            dynamicBlackLevel
                                                    )
                                                    + " valid="
                                                    + dynamicBlackLevelValid
                                                    + " static="
                                                    + Arrays.toString(
                                                            getMotionStaticBlackLevel()
                                                    )
                                                    + " whiteLevel="
                                                    + validationWhiteLevel
                                                    + " cfaOrder=R_G1_G2_B"
                                    );

                                    tryMatchControlledMotionFrameLocked(
                                            (long) time
                                    );
                                }
                                Long requestedExposureNs = request.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
                                Integer requestedIso = request.get(CaptureRequest.SENSOR_SENSITIVITY);
                                double requestedEnergy = requestedExposureNs != null && requestedExposureNs > 0L
                                                && requestedIso != null && requestedIso > 0
                                        ? ExposureIndex.time2sec(requestedExposureNs) * requestedIso
                                        : 0.0;
                                double actualEnergy = ExposureIndex.time2sec(actualExposureNs) * iso;
                                double resultDifferenceEv = requestedEnergy > 0.0 && actualEnergy > 0.0
                                        ? Math.log(actualEnergy / requestedEnergy) / Math.log(2.0)
                                        : Double.NaN;

                                Float controlledOisMotion =
                                        mMotionBurstOisMotion.get(
                                                (long) time
                                        );
                                Log.d(MOTION_LOG_TAG,"CONTROLLED_RESULT"
                                        + " frameIndex=" + frameCount
                                        + " timestamp=" + time
                                        + " requestedExposureNs=" + requestedExposureNs
                                        + " requestedIso=" + requestedIso
                                        + " actualExposureNs=" + actualExposureNs
                                        + " actualIso=" + iso
                                        + " oisMotion="
                                        + (
                                            controlledOisMotion != null
                                                    ? controlledOisMotion
                                                    : 0.0f
                                        )
                                        + " resultDifferenceEv=" + resultDifferenceEv);
                            }
                        }
                    }
                    cameraEventsListener.onFrameCaptureCompleted(
                            new TimerFrameCountViewModel.FrameCntTime(frameCount, maxFrameCount[0], frametime));

                    if (onUnlimited && !unlimitedStarted) {
                        mImageSaver.processStart(mCameraCharacteristics, result, request, cameraRotation);
                        unlimitedStarted = true;
                    }
                    /*
                     * Build 26294:
                     * Keep the capture result whose exposure matches the normal
                     * processing request. The appended short result remains
                     * timestamp-matched in the per-frame maps but cannot become
                     * global HDRX metadata.
                     * MOTION_26294_NORMAL_METADATA_RESULT_OWNERSHIP
                     */
                    boolean acceptProcessingMetadata = true;

                    if (PhotonCamera.getSettings().selectedMode
                            == CameraMode.MOTION
                            && mCaptureRequest != null) {

                        Long processingExposureNs =
                                mCaptureRequest.get(
                                        CaptureRequest.SENSOR_EXPOSURE_TIME
                                );

                        Long completedExposureNs =
                                result.get(
                                        CaptureResult.SENSOR_EXPOSURE_TIME
                                );

                        if (processingExposureNs != null
                                && completedExposureNs != null
                                && !processingExposureNs.equals(
                                        completedExposureNs
                                )) {
                            acceptProcessingMetadata = false;

                            Log.d(
                                    MOTION_LOG_TAG,
                                    "MOTION_26294_AUXILIARY_METADATA_ISOLATED"
                                            + " processingExposureNs="
                                            + processingExposureNs
                                            + " completedExposureNs="
                                            + completedExposureNs
                                            + " timestamp="
                                            + result.get(
                                                    CaptureResult
                                                            .SENSOR_TIMESTAMP
                                              )
                            );
                        }
                    }

                    if (acceptProcessingMetadata) {
                        mCaptureResult = result;
                    }

                    if (maxFrameCount[0] != -1) PhotonCamera.getGyro().CaptureGyroBurst();
                }

                @Override
                public void onCaptureFailed(
                        @NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,
                        @NonNull CaptureFailure failure
                ) {
                    if (PhotonCamera.getSettings().selectedMode
                            == CameraMode.MOTION) {
                        mMotionDiagnosticCaptureFailures++;
                        Log.w(
                                MOTION_LOG_TAG,
                                "CONTROLLED_CAPTURE_FAILED"
                                        + " frameNumber="
                                        + failure.getFrameNumber()
                                        + " reason="
                                        + failure.getReason()
                                        + " wasImageCaptured="
                                        + failure.wasImageCaptured()
                        );
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
                    if (PhotonCamera.getSettings().selectedMode
                            == CameraMode.MOTION) {
                        Log.d(
                                MOTION_LOG_TAG,
                                "CONTROLLED_SEQUENCE_COMPLETED"
                                        + " frames="
                                        + finalFrameCount
                                        + " rawSurfaceStayedAttached=true"
                                        + " previewContinues=true"
                        );
                        finalizeDedicatedMotionBurst(finalFrameCount);
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
            Camera2ApiAutoFix.ApplyBurst();
            if (isDualSession) {
                createCameraPreviewSession(true);
            } else if (PhotonCamera.getSettings().selectedMode
                    == CameraMode.MOTION) {
                try {
                    synchronized (mMotionBurstLock) {
                        mMotionBurstFirstTimestampNs = 0L;
                        mMotionBurstActive = true;
                    }

                    Log.d(
                            MOTION_LOG_TAG,
                            "CONTROLLED_BURST_SUBMITTED"
                                    + " frames="
                                    + captures.size()
                                    + " rawSurfaceStayedAttached=true"
                                    + " previewContinues=true"
                    );

                    mCaptureSession.captureBurst(
                            captures,
                            CaptureCallback,
                            mBackgroundHandler
                    );
                } catch (Exception e) {
                    recoverDedicatedMotionCapture(
                            "submit_failed"
                    );
                    throw e;
                }
            } else {
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

    public void applyAeMetering() {
        if (mPreviewRequestBuilder == null) return;
        VendorTagUtils.builderSessionApply(
                mPreviewRequestBuilder,
                false,
                useMaximumResolutionKey,
                physicalID
        );
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

    public void callUnlimitedEnd(boolean rebuildPreviewAfterStop) {
        onUnlimited = false;
        unlimitedStarted = false;
        mState = STATE_PREVIEW;

        /*
         * Stop camera delivery first, then finish the RAW Video archive before
         * restartCamera() destroys the current CameraBackground HandlerThread.
         * This keeps processor state, camera state, and UI state in one ordered
         * transition instead of allowing old callbacks to cross into Motion.
         */
        abortCaptures();

        if (!continuousCaptureFinalizing) {
            continuousCaptureFinalizing = true;
            try {
                if (mImageSaver != null) {
                    mImageSaver.processEnd();
                }
            } catch (Exception e) {
                Log.e(TAG, "CONTINUOUS_CAPTURE_FINALIZE_FAILED "
                        + Log.getStackTraceString(e));
            } finally {
                continuousCaptureFinalizing = false;
                Log.d(TAG, "CONTINUOUS_CAPTURE_FINALIZE_COMPLETE_SYNC");
            }
        }

        if (rebuildPreviewAfterStop
                && mCameraDevice != null
                && mBackgroundHandler != null) {
            createCameraPreviewSession(false);
        }
    }

    public void callUnlimitedEnd() {
        callUnlimitedEnd(true);
    }

    public void callUnlimitedStart() {
        callUnlimitedStartWithRetry(0);
    }

    private void callUnlimitedStartWithRetry(int attempt) {
        if (continuousCaptureFinalizing) {
            if (attempt < 20) {
                new Handler(Looper.getMainLooper()).postDelayed(
                        () -> callUnlimitedStartWithRetry(attempt + 1),
                        100L
                );
            } else {
                onUnlimited = false;
                unlimitedStarted = false;
                Log.w(TAG, "RAW Video start timed out waiting for finalization");
            }
            return;
        }

        if (mPreviewRequestBuilder == null
                || mCaptureSession == null
                || mCameraDevice == null
                || mBackgroundHandler == null) {
            onUnlimited = false;
            unlimitedStarted = false;

            if (attempt < 20) {
                Log.d(TAG, "RAW Video start waiting for camera attempt=" + attempt);
                new Handler(Looper.getMainLooper()).postDelayed(
                        () -> callUnlimitedStartWithRetry(attempt + 1),
                        100L
                );
            } else {
                Log.w(TAG, "RAW Video start timed out waiting for camera");
            }
            return;
        }

        onUnlimited = true;
        unlimitedStarted = false;

        /*
         * RAW Video is a continuous stream, not a single still capture.
         * After returning from Motion, the generic takePicture()/lockFocus()
         * state machine can remain waiting on an AF transition that never
         * arrives. Reset the capture state and enter the proven RAW builder
         * directly so every recording start follows the same deterministic
         * path.
         */
        mState = STATE_PREVIEW;
        Log.d(TAG, "RAW Video direct capture start attempt=" + attempt);
        captureStillPicture();
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