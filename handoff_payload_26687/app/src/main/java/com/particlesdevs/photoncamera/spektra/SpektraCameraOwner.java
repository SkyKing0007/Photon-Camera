package com.particlesdevs.photoncamera.spektra;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.MeteringRectangle;
import android.hardware.camera2.params.RggbChannelVector;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.hardware.camera2.params.OutputConfiguration;
import android.hardware.camera2.params.SessionConfiguration;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.LongSparseArray;
import android.util.Range;
import android.util.Rational;
import android.util.Size;
import android.view.Surface;
import android.view.SurfaceView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityCompat;

import com.particlesdevs.photoncamera.api.CameraEventsListener;
import com.particlesdevs.photoncamera.util.Log;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Independent Camera2 owner for CameraMode.SPEKTRA.
 *
 * No Motion/Night capture, ZSL, IsoExpoSelector, Parameters, Sabre/Wronski, UHDR or HEIC object
 * is referenced from this class. Spektra auto-discovers and persists only its own Camera2 RAW
 * lens profile; Photo/Motion/Night IQ profiles are never imported.
 */
final class SpektraCameraOwner {
    private static final String TAG = "SpektraCameraOwner";
    private static final int TARGET_PREVIEW_FPS = 30;
    private static final int PREVIEW_SHORT_EDGE_DEFAULT = 480;
    private static final long CAMERA_OPEN_TIMEOUT_MS = 4000L;
    private static final long RAW_GPU_WARMUP_TIMEOUT_MS = 10000L;
    private static final long PREVIEW_CONFIG_TIMEOUT_MS = 4000L;
    private static final long PREVIEW_FIRST_FRAME_TIMEOUT_MS = 6500L;
    private static final long STILL_CONFIG_TIMEOUT_MS = 4500L;
    private static final long STILL_CAPTURE_TIMEOUT_MS = 6500L;
    private static final int SPEKTRA_PROFILE_SCHEMA = 26687;

    public enum State {
        IDLE, OPENING, CONFIGURING, STREAMING,
        STILL_CONFIGURING, STILL_CAPTURING, STILL_CAPTURED, STILL_FAILED,
        PREVIEW_RECONFIGURING, FAILED, CLOSED
    }

    private enum CaptureJobState { IDLE, PROCESSING }

    private static final class Route {
        final String requestedId;
        final String openedId;
        final String characteristicsId;
        final String physicalOutputId;
        Route(String requestedId, String openedId, String characteristicsId, String physicalOutputId) {
            this.requestedId = requestedId;
            this.openedId = openedId;
            this.characteristicsId = characteristicsId;
            this.physicalOutputId = physicalOutputId;
        }
        @Override public String toString() {
            return "Route{requested=" + requestedId + ", opened=" + openedId
                    + ", chars=" + characteristicsId + ", physical=" + physicalOutputId + "}";
        }
    }

    private final Activity activity;
    private final CameraManager cameraManager;
    /** Saved-photo processing belongs only to Spektra and never shares Iris processing state. */
    private final ExecutorService savedProcessExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "SpektraSavedProcess");
        t.setDaemon(true);
        return t;
    });
    /** Native teardown is isolated from Camera2/UI teardown and is always non-blocking. */
    private final ExecutorService nativeLifecycleExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "SpektraNativeLifecycle");
        t.setDaemon(true);
        return t;
    });
    /** VF-S RAW reconstruction must never run on the Camera2 callback thread. */
    private final ExecutorService previewDecodeExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "SpektraVfsRawDecode");
        t.setDaemon(true);
        return t;
    });
    private final AtomicBoolean previewDecodeBusy = new AtomicBoolean(false);
    /** True only after a real Spektra frame from the current generation reached the SurfaceView. */
    private final AtomicBoolean previewPresented = new AtomicBoolean(false);
    private final CameraEventsListener events;
    private final SpektraModeController.Host host;
    private final AtomicReference<CaptureJobState> captureJobState =
            new AtomicReference<>(CaptureJobState.IDLE);
    private final AtomicReference<SpektraShot> pendingSavedShot = new AtomicReference<>(null);
    private final AtomicLong generation = new AtomicLong(0L);
    private final Object stateLock = new Object();
    private final SharedPreferences lensProfiles;
    private final ScheduledExecutorService watchdogExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "SpektraWatchdog");
        t.setDaemon(true);
        return t;
    });

    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private Executor cameraExecutor;
    private SurfaceView previewSurfaceView;
    private CameraDevice cameraDevice;
    private CameraCaptureSession session;
    private ImageReader previewReader;
    private CaptureRequest.Builder repeatingBuilder;
    private CameraCharacteristics characteristics;
    private Route route;
    private SpektraExposureController exposureController;
    private SpektraPreviewRenderer previewRenderer;
    private State state = State.IDLE;
    private int rawFormat = ImageFormat.RAW_SENSOR;
    /** Full-resolution Camera2 RAW stream; shared by VF-S and still capture. */
    private Size previewSize;
    private Size stillSize;
    /** LOW VF-S processing lattice (default 480 short edge, normally 640x480). */
    private Size previewProcessSize;
    private long activeGeneration = 0L;
    private int requestedIso = 0;
    private long requestedExposureNs = 0L;
    private int flashPreference = CaptureRequest.CONTROL_AE_MODE_ON;
    private MeteringRectangle[] touchAfRegion;
    private MeteringRectangle[] touchMeterRegion;
    private float touchMeterX = 0.5f;
    private float touchMeterY = 0.5f;
    private boolean touchMeterActive = false;
    private RggbChannelVector latestColorGains;
    private ColorSpaceTransform latestColorTransform;
    private boolean focusLocked = false;
    private volatile String selectedCameraId = "";
    private volatile Integer manualIso = null;
    private volatile Long manualExposureNs = null;
    private volatile int manualEvSteps = 0;
    private volatile Float manualFocusDistance = null;

    private final LongSparseArray<TotalCaptureResult> previewResults = new LongSparseArray<>();
    /** Exact-timestamp RAW Images awaiting their repeating TotalCaptureResult. Bounded and closed on trim. */
    private final LongSparseArray<Image> previewImages = new LongSparseArray<>();
    private final LongSparseArray<Image> pendingStillImages = new LongSparseArray<>();
    private SpektraRawFrame pendingStillFrame;
    private boolean stillDecodeInFlight = false;
    private TotalCaptureResult pendingStillResult;
    private long pendingStillTimestamp = 0L;
    private long pendingStillWallTimeMs = 0L;
    private int pendingStillFrozenIso = 0;
    private final AtomicLong watchdogToken = new AtomicLong(0L);
    private volatile ScheduledFuture<?> watchdogFuture;
    private volatile boolean awaitingPostStillPreview = false;
    private boolean automaticLensDiscoverySeeded = false;
    private final ArrayList<Route> automaticDiscoveryQueue = new ArrayList<>();
    private boolean automaticDiscoveryActive = false;
    private Route automaticDiscoveryRoute = null;
    private String automaticDiscoveryReturnCameraId = "";
    private boolean currentProfileNeedsVerification = false;
    private boolean verificationCaptureInFlight = false;
    private boolean verificationCaptureSucceeded = false;
    private int activeBayerOffset = -1;
    private boolean loggedPreviewRawContract = false;
    private boolean loggedStillRawContract = false;
    private boolean loggedPreviewWaitWb = false;
    /** Camera transport evidence is separate from processor health; never poison discovery on GPU failure. */
    private volatile boolean currentStreamRawSeen = false;
    private volatile boolean currentStreamResultSeen = false;

    SpektraCameraOwner(Activity activity, CameraEventsListener events, SpektraModeController.Host host) {
        this.activity = activity;
        this.events = events;
        this.host = host;
        this.cameraManager = (CameraManager) activity.getSystemService(Context.CAMERA_SERVICE);
        this.lensProfiles = activity.getSharedPreferences("spektra_auto_lens_discovery", Context.MODE_PRIVATE);
    }

    public void bindPreviewSurface(@NonNull SurfaceView surfaceView) {
        previewSurfaceView = surfaceView;
        previewSurfaceView.setZOrderOnTop(false);
    }

    public void setSelectedCameraId(@Nullable String cameraId) {
        selectedCameraId = cameraId == null ? "" : cameraId;
    }

    public State getState() { synchronized (stateLock) { return state; } }
    public boolean isActive() {
        State s = getState();
        return s != State.IDLE && s != State.CLOSED && s != State.FAILED;
    }

    public boolean isStreaming() {
        return getState() == State.STREAMING && !currentProfileNeedsVerification
                && !verificationCaptureInFlight;
    }

    public boolean isShutterReady() {
        return isStreaming() && previewPresented.get()
                && captureJobState.get() == CaptureJobState.IDLE;
    }

    public String describeStatus() {
        return getState() + "/presented=" + previewPresented.get()
                + "/job=" + captureJobState.get()
                + "/verify=" + currentProfileNeedsVerification
                + "/verifyCapture=" + verificationCaptureInFlight;
    }

    @SuppressLint("MissingPermission")
    public void resumeCamera() { startCamera(false); }

    @SuppressLint("MissingPermission")
    public void restartCamera() { startCamera(true); }

    private void startCamera(boolean restart) {
        final long g = generation.incrementAndGet();
        activeGeneration = g;
        previewPresented.set(false);
        ensureThread();
        Handler h = cameraHandler;
        if (h == null) {
            failProcessor(g, "CAMERA_THREAD_UNAVAILABLE", null);
            return;
        }
        h.post(() -> {
            if (!isCurrent(g)) return;
            if (restart) {
                closeCameraObjects(false);
                activity.runOnUiThread(events::onCameraRestarted);
            }
            host.onSpektraPreviewPreparing();
            setState(State.OPENING);
            armFatalWatchdog(g, State.OPENING, RAW_GPU_WARMUP_TIMEOUT_MS, "RAW_GPU_WARMUP_TIMEOUT");
            try {
                previewDecodeExecutor.execute(() -> {
                    Throwable warmupFailure = null;
                    try {
                        Log.i(TAG, "IRIS_26687_SPEKTRA_RAW_OWNER_WARMUP_BEGIN generation=" + g);
                        SpektraRawProcessor.warmUpNativeOwner();
                        Log.i(TAG, "IRIS_26687_SPEKTRA_RAW_OWNER_WARMUP_PASS generation=" + g);
                    } catch (Throwable t) {
                        warmupFailure = t;
                    }
                    final Throwable failure = warmupFailure;
                    Handler camera = cameraHandler;
                    if (camera != null) camera.post(() -> {
                        if (!isCurrent(g)) return;
                        if (failure != null) {
                            failProcessor(g, "RAW_GPU_WARMUP_FAILED", failure);
                            return;
                        }
                        openForPreview(g, restart);
                    });
                });
            } catch (RuntimeException rejected) {
                failProcessor(g, "RAW_GPU_WARMUP_QUEUE_REJECTED", rejected);
            }
        });
    }

    public void closeCamera() {
        automaticDiscoveryActive = false;
        automaticDiscoveryRoute = null;
        automaticDiscoveryQueue.clear();
        final long retired = generation.incrementAndGet();
        activeGeneration = retired;
        Handler h = cameraHandler;
        if (h != null) h.post(() -> closeCameraObjects(true));
        else closeCameraObjects(true);
    }

    /**
     * IRIS_26681_SPEKTRA_SYNCHRONOUS_HANDOFF
     * Retire the Spektra CameraDevice/session before Iris opens another owner for the same lens.
     * This is intentionally blocking only at mode/lifecycle handoff boundaries, never in capture.
     */
    public boolean retireForHandoff() {
        startPendingSavedProcess("mode_handoff");
        automaticDiscoveryActive = false;
        automaticDiscoveryRoute = null;
        automaticDiscoveryQueue.clear();
        final long retired = generation.incrementAndGet();
        activeGeneration = retired;
        final Handler h = cameraHandler;
        if (h == null || Thread.currentThread() == (cameraThread == null ? null : cameraThread)) {
            closeCameraObjects(true);
            return true;
        }
        final CountDownLatch done = new CountDownLatch(1);
        h.post(() -> {
            try { closeCameraObjects(true); } finally { done.countDown(); }
        });
        try {
            final boolean completed = done.await(2500L, TimeUnit.MILLISECONDS);
            if (completed) return true;
            Log.e(TAG, "IRIS_26687_SPEKTRA_HANDOFF_TIMEOUT generation=" + retired
                    + " action=force_transport_close");
            forceCloseCameraTransportForHandoff();
            host.onSpektraPreviewStopped();
            setState(State.CLOSED);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            Log.e(TAG, "IRIS_26687_SPEKTRA_HANDOFF_INTERRUPTED action=force_transport_close", e);
            forceCloseCameraTransportForHandoff();
            host.onSpektraPreviewStopped();
            setState(State.CLOSED);
            return true;
        }
    }

    public void shutdown() {
        retireForHandoff();
        watchdogExecutor.shutdownNow();
        previewDecodeExecutor.shutdownNow();
        startPendingSavedProcess("shutdown");
        savedProcessExecutor.shutdown();
        try {
            nativeLifecycleExecutor.execute(() -> {
                try {
                    if (!savedProcessExecutor.awaitTermination(30L, TimeUnit.SECONDS)) {
                        Log.w(TAG, "IRIS_26687_SPEKTRA_NATIVE_RELEASE_DEFERRED savedJobStillActive=true");
                        return;
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                SpektraRawProcessor.releaseNativeOwner();
                SpektraFilmRenderer.releaseProcessRenderer();
            });
        } catch (RuntimeException ignored) {}
        nativeLifecycleExecutor.shutdown();
        HandlerThread t = cameraThread;
        if (t != null) {
            t.quitSafely();
            cameraThread = null;
            cameraHandler = null;
            cameraExecutor = null;
        }
    }

    public void setFlashPreference(int aeModePreference) {
        // Iris stores flash UI as AE-mode integers. Spektra interprets it locally and never enables
        // Android sensor AE. Values are consumed only by Spektra's capture/torch policy.
        flashPreference = aeModePreference;
        Handler h = cameraHandler;
        if (h != null) h.post(() -> {
            if (state != State.STREAMING || repeatingBuilder == null || session == null) return;
            applyFlashToPreviewRequest(repeatingBuilder);
            submitRepeating();
        });
    }

    public void setManualExposureMode(SpektraExposureController.Mode mode,
            @Nullable Integer iso, @Nullable Long exposureNs, double ev) {
        SpektraExposureController controller = exposureController;
        if (controller == null) return;
        controller.setMode(mode, iso, exposureNs);
        controller.setExposureCompensationEv(ev);
        requestedIso = controller.getCurrentIso();
        requestedExposureNs = controller.getCurrentExposureNs();
        Handler h = cameraHandler;
        if (h != null) h.post(this::applyCurrentExposureToRepeating);
    }

    public void setManualControls(@Nullable Integer iso, @Nullable Long exposureNs, int evSteps) {
        manualIso = iso;
        manualExposureNs = exposureNs;
        manualEvSteps = evSteps;
        Handler h = cameraHandler;
        if (h != null) h.post(this::applyStoredManualControls);
        else applyStoredManualControls();
    }

    public void setManualFocus(@Nullable Float focusDistance) {
        manualFocusDistance = focusDistance;
        Handler h = cameraHandler;
        if (h != null) h.post(() -> {
            if (repeatingBuilder == null || state != State.STREAMING) return;
            configureDefaultAf(repeatingBuilder);
            submitRepeating();
        });
    }

    private void applyStoredManualControls() {
        SpektraExposureController controller = exposureController;
        if (controller == null) return;
        final SpektraExposureController.Mode mode;
        if (manualIso == null && manualExposureNs == null) mode = SpektraExposureController.Mode.AUTO;
        else if (manualIso != null && manualExposureNs == null) mode = SpektraExposureController.Mode.ISO_PRIORITY;
        else if (manualIso == null) mode = SpektraExposureController.Mode.SHUTTER_PRIORITY;
        else mode = SpektraExposureController.Mode.MANUAL;
        double ev = 0.0;
        if (characteristics != null) {
            Rational step = characteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP);
            if (step != null && step.getDenominator() != 0) ev = manualEvSteps * step.doubleValue();
        }
        controller.setMode(mode, manualIso, manualExposureNs);
        controller.setExposureCompensationEv(ev);
        requestedIso = controller.getCurrentIso();
        requestedExposureNs = controller.getCurrentExposureNs();
        applyCurrentExposureToRepeating();
        Log.i(TAG, "IRIS_26681_SPEKTRA_MANUAL mode=" + mode + " iso=" + manualIso
                + " exposureNs=" + manualExposureNs + " evSteps=" + manualEvSteps + " ev=" + ev);
    }

    public void touchFocus(float normalizedX, float normalizedY, boolean lock) {
        Handler h = cameraHandler;
        if (h == null) return;
        h.post(() -> applyTouchFocus(normalizedX, normalizedY, lock));
    }

    public void unlockFocus() {
        Handler h = cameraHandler;
        if (h == null) return;
        h.post(() -> {
            focusLocked = false;
            touchAfRegion = null;
            touchMeterRegion = null;
            touchMeterActive = false;
            if (repeatingBuilder != null) {
                repeatingBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
                submitOneShotThenRepeating();
                repeatingBuilder.set(CaptureRequest.CONTROL_AF_REGIONS, null);
                configureDefaultAf(repeatingBuilder);
                repeatingBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
                submitRepeating();
            }
        });
    }

    public void takePicture() {
        Handler h = cameraHandler;
        if (h == null) {
            rejectShutter("SPEKTRA_CAMERA_NOT_READY");
            return;
        }
        h.post(() -> {
            if (!isShutterReady()) {
                rejectShutter("SPEKTRA_NOT_SHUTTER_READY");
                return;
            }
            if (cameraDevice == null || session == null || characteristics == null) {
                rejectShutter("SPEKTRA_TRANSPORT_NOT_READY");
                return;
            }
            if (!lensProfiles.getBoolean(lensProfileKey() + ".captureVerified", false)) {
                rejectShutter("SPEKTRA_PROFILE_NOT_VERIFIED");
                return;
            }
            setState(State.STILL_CONFIGURING);
            events.onFrameCountSet(1);
            events.onCaptureStillPictureStarted("SPEKTRA");
            configureStillSession(activeGeneration);
        });
    }

    private void rejectShutter(String reason) {
        Log.w(TAG, "IRIS_26681_SPEKTRA_SHUTTER_REJECT reason=" + reason + " state=" + getState());
        activity.runOnUiThread(() -> events.onCaptureStillPictureRejected(reason));
    }

    private void ensureThread() {
        if (cameraThread != null) return;
        cameraThread = new HandlerThread("SpektraCamera");
        cameraThread.start();
        cameraHandler = new Handler(cameraThread.getLooper());
        cameraExecutor = command -> {
            Handler h = cameraHandler;
            if (h != null) h.post(command);
        };
    }

    @SuppressLint("MissingPermission")
    private void openForPreview(long g, boolean restart) {
        if (!isCurrent(g)) return;
        try {
            if (ActivityCompat.checkSelfPermission(activity, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                fail(g, "CAMERA_PERMISSION_MISSING", null);
                return;
            }
            seedAutomaticLensProfiles();
            setState(State.OPENING);
            String requested = selectedCameraId;
            route = automaticDiscoveryActive && automaticDiscoveryRoute != null
                    ? automaticDiscoveryRoute : resolveRoute(requested);
            characteristics = cameraManager.getCameraCharacteristics(route.characteristicsId);
            requireRawCapability(characteristics);
            requireManualSensorCapability(cameraManager.getCameraCharacteristics(route.openedId));
            discoverRawStreams(characteristics);
            exposureController = new SpektraExposureController(characteristics);
            exposureController.reset(System.nanoTime());
            applyStoredManualControls();
            requestedIso = exposureController.getCurrentIso();
            requestedExposureNs = exposureController.getCurrentExposureNs();
            if (previewRenderer == null) {
                previewRenderer = new SpektraPreviewRenderer(activity, previewSurfaceView,
                        this::onFirstPreviewFramePresented, this::onPreviewRenderFailure);
            }
            previewRenderer.configure(characteristics, previewSize, previewProcessSize, rawFormat);
            activity.runOnUiThread(() -> {
                if (!isCurrent(g)) return;
                events.onCharacteristicsUpdated(characteristics);
                events.onOpenCamera(cameraManager);
            });
            Log.i(TAG, "IRIS_26684_SPEKTRA_OPEN " + route + " rawFormat=" + rawFormat
                    + " rawStream=" + previewSize + " vfS=" + previewProcessSize
                    + " still=" + stillSize + " fps=" + TARGET_PREVIEW_FPS + " generation=" + g);
            armFatalWatchdog(g, State.OPENING, CAMERA_OPEN_TIMEOUT_MS, "CAMERA_OPEN_TIMEOUT");
            cameraManager.openCamera(route.openedId, new CameraDevice.StateCallback() {
                @Override public void onOpened(@NonNull CameraDevice camera) {
                    if (!isCurrent(g)) { camera.close(); return; }
                    cameraDevice = camera;
                    configurePreviewSession(g);
                }
                @Override public void onDisconnected(@NonNull CameraDevice camera) {
                    camera.close();
                    if (isCurrent(g)) fail(g, "CAMERA_DISCONNECTED", null);
                }
                @Override public void onError(@NonNull CameraDevice camera, int error) {
                    camera.close();
                    if (isCurrent(g)) fail(g, "CAMERA_ERROR_" + error, null);
                }
            }, cameraHandler);
        } catch (Throwable t) {
            if (automaticDiscoveryActive && automaticDiscoveryRoute != null) {
                skipAutomaticDiscoveryRoute(g, "OPEN_FAILED", t);
            } else {
                fail(g, "OPEN_FAILED", t);
            }
        }
    }

    private static boolean hasCapability(CameraCharacteristics c, int wanted) {
        int[] caps = c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        if (caps != null) for (int cap : caps) if (cap == wanted) return true;
        return false;
    }

    private static boolean hasRawCapability(CameraCharacteristics c) {
        return hasCapability(c, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW);
    }

    private static boolean hasManualSensorCapability(CameraCharacteristics c) {
        return hasCapability(c, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR);
    }

    private static void requireRawCapability(CameraCharacteristics c) {
        if (!hasRawCapability(c)) {
            throw new IllegalStateException("Spektra requires Camera2 RAW capability for the selected lens");
        }
    }

    private static void requireManualSensorCapability(CameraCharacteristics c) {
        if (!hasManualSensorCapability(c)) {
            throw new IllegalStateException("Spektra requires MANUAL_SENSOR on the opened camera for Unspektra AE");
        }
    }

    private Route resolveRoute(String requestedValue) throws CameraAccessException {
        final String requested = requestedValue == null ? "" : requestedValue.trim();
        if (requested.isEmpty()) throw new IllegalArgumentException("Spektra camera ID is empty");

        final List<Route> discovered = enumerateSpektraRoutes();
        // Exact Spektra route IDs (for example 0-2) always win. This preserves the logical-camera
        // owner plus physical OutputConfiguration even when Android also exposes physical 2 as a
        // separately openable public ID.
        for (Route candidate : discovered) {
            if (requested.equals(candidate.requestedId) || requested.equals(routeProfileId(candidate))) {
                return candidate;
            }
        }

        // Iris may hand Spektra a plain physical lens ID. Map it back to the verified logical/physical
        // Spektra route instead of opening that physical ID directly. Standalone Unspektrawesome's
        // Xiaomi profiles are 0/2, 0/3, 0/4, 0/5 rather than direct 2/3/4/5 owners.
        for (Route candidate : discovered) {
            if (candidate.physicalOutputId != null && requested.equals(candidate.physicalOutputId)) {
                return candidate;
            }
        }

        // Standalone/direct lenses (for example the front camera) keep their public Camera2 ID.
        for (Route candidate : discovered) {
            if (candidate.physicalOutputId == null
                    && (requested.equals(candidate.openedId) || requested.equals(candidate.characteristicsId))) {
                return candidate;
            }
        }

        throw new IllegalArgumentException("Unable to resolve verified Spektra Camera2 route for " + requested
                + " discoveredRoutes=" + discovered);
    }

    private void seedAutomaticLensProfiles() {
        if (automaticLensDiscoverySeeded) return;
        automaticLensDiscoverySeeded = true;
        int discovered = 0;
        try {
            final List<Route> routes = enumerateSpektraRoutes();
            final StringBuilder topology = new StringBuilder("schema=").append(SPEKTRA_PROFILE_SCHEMA);
            for (Route r : routes) {
                CameraCharacteristics cc = cameraManager.getCameraCharacteristics(r.characteristicsId);
                StreamConfigurationMap map = cc.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                topology.append('|').append(routeProfileId(r));
                if (map != null) {
                    for (int format : new int[]{ImageFormat.RAW10, ImageFormat.RAW_SENSOR}) {
                        Size[] sizes = map.getOutputSizes(format);
                        if (sizes == null) continue;
                        java.util.Arrays.sort(sizes, (a, b) -> Long.compare(area(b), area(a)));
                        for (Size size : sizes) {
                            if (size != null) topology.append(':').append(format).append('@')
                                    .append(size.getWidth()).append('x').append(size.getHeight());
                        }
                    }
                }
            }
            final String fingerprint = topology.toString();
            final String prior = lensProfiles.getString("topologyFingerprint", "");
            final int priorSchema = lensProfiles.getInt("profileSchema", 0);
            if (priorSchema != SPEKTRA_PROFILE_SCHEMA || !fingerprint.equals(prior)) {
                lensProfiles.edit().clear()
                        .putInt("profileSchema", SPEKTRA_PROFILE_SCHEMA)
                        .putString("topologyFingerprint", fingerprint).apply();
                Log.i(TAG, "IRIS_26687_SPEKTRA_DISCOVERY_INVALIDATE priorSchema=" + priorSchema
                        + " topologyChanged=" + !fingerprint.equals(prior));
            }
            SharedPreferences.Editor e = lensProfiles.edit();
            for (Route r : routes) {
                String key = lensProfileKeyForRoute(r);
                e.putString(key + ".requested", r.requestedId)
                        .putString(key + ".opened", r.openedId)
                        .putString(key + ".characteristics", r.characteristicsId)
                        .putString(key + ".physical", r.physicalOutputId == null ? "" : r.physicalOutputId)
                        .putBoolean(key + ".candidate", true);
                discovered++;
            }
            e.apply();
            automaticDiscoveryQueue.clear();
            for (Route r : routes) {
                String key = lensProfileKeyForRoute(r);
                if (!lensProfiles.getBoolean(key + ".captureVerified", false)
                        && !lensProfiles.getBoolean(key + ".unsupported", false)) {
                    automaticDiscoveryQueue.add(r);
                }
            }
            if (!automaticDiscoveryQueue.isEmpty()) {
                automaticDiscoveryReturnCameraId = selectedCameraId;
                automaticDiscoveryActive = true;
                automaticDiscoveryRoute = automaticDiscoveryQueue.remove(0);
            }
            Log.i(TAG, "IRIS_26685_SPEKTRA_AUTO_LENS_DISCOVERY candidates=" + discovered
                    + " pendingFunctional=" + (automaticDiscoveryQueue.size() + (automaticDiscoveryRoute == null ? 0 : 1))
                    + " functionalVerification=preview+still+resume manualScanRequired=false");
        } catch (Throwable t) {
            Log.w(TAG, "IRIS_26685_SPEKTRA_AUTO_LENS_DISCOVERY_PARTIAL reason="
                    + t.getClass().getSimpleName());
        }
    }

    private List<Route> enumerateSpektraRoutes() throws CameraAccessException {
        java.util.LinkedHashMap<String, Route> out = new java.util.LinkedHashMap<>();
        java.util.HashSet<String> claimedPhysicalIds = new java.util.HashSet<>();
        java.util.HashSet<String> logicalOwnersWithPhysicalRaw = new java.util.HashSet<>();
        final String[] publicIds = cameraManager.getCameraIdList();

        // First establish logical->physical ownership. A physical lens owns RAW/calibration; the
        // opened logical camera owns the MANUAL_SENSOR request authority used by Unspektra AE.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            for (String publicId : publicIds) {
                CameraCharacteristics logical = cameraManager.getCameraCharacteristics(publicId);
                if (!hasManualSensorCapability(logical)) continue;
                java.util.List<String> physicalIds = new java.util.ArrayList<>(logical.getPhysicalCameraIds());
                java.util.Collections.sort(physicalIds);
                for (String physicalId : physicalIds) {
                    try {
                        CameraCharacteristics physical = cameraManager.getCameraCharacteristics(physicalId);
                        if (!hasRawCapability(physical)) continue;
                        Route r = new Route(publicId + "-" + physicalId, publicId, physicalId, physicalId);
                        out.put(routeProfileId(r), r);
                        claimedPhysicalIds.add(physicalId);
                        logicalOwnersWithPhysicalRaw.add(publicId);
                    } catch (Throwable ignored) {}
                }
            }
        }

        // Then add true direct RAW cameras that were not already claimed as a child of a logical
        // owner. This prevents duplicate 0/2 + 2/direct profiles on devices that publicly list both.
        for (String publicId : publicIds) {
            if (claimedPhysicalIds.contains(publicId) || logicalOwnersWithPhysicalRaw.contains(publicId)) continue;
            CameraCharacteristics direct = cameraManager.getCameraCharacteristics(publicId);
            if (!hasRawCapability(direct) || !hasManualSensorCapability(direct)) continue;
            Route r = new Route(publicId, publicId, publicId, null);
            out.put(routeProfileId(r), r);
        }
        return new ArrayList<>(out.values());
    }

    private static String routeProfileId(Route r) {
        return r.openedId + "/" + (r.physicalOutputId == null ? "direct" : r.physicalOutputId);
    }

    private void discoverRawStreams(CameraCharacteristics c) {
        StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        if (map == null) throw new IllegalStateException("Camera has no stream configuration map");

        final String key = lensProfileKey();
        final int persistedFormat = lensProfiles.getInt(key + ".format", 0);
        final int persistedWidth = lensProfiles.getInt(key + ".width", 0);
        final int persistedHeight = lensProfiles.getInt(key + ".height", 0);
        Size selectedSize = findAdvertisedRawSize(map, persistedFormat, persistedWidth, persistedHeight);
        int selectedFormat = selectedSize == null ? 0 : persistedFormat;
        if (selectedSize != null && lensProfiles.getBoolean(streamFailureKey(key, selectedFormat, selectedSize), false)) {
            selectedSize = null;
            selectedFormat = 0;
        }
        boolean persisted = selectedSize != null;

        if (selectedSize == null) {
            final int[] formatOrder = new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR};
            outer:
            for (int format : formatOrder) {
                Size[] advertised = map.getOutputSizes(format);
                if (advertised == null || advertised.length == 0) continue;
                List<Size> viable = new ArrayList<>();
                for (Size candidate : advertised) {
                    if (candidate != null && candidate.getWidth() > 0 && candidate.getHeight() > 0
                            && (candidate.getWidth() & 1) == 0 && (candidate.getHeight() & 1) == 0) {
                        viable.add(candidate);
                    }
                }
                viable.sort((a, b) -> Long.compare(area(b), area(a)));
                for (Size candidate : viable) {
                    if (lensProfiles.getBoolean(streamFailureKey(key, format, candidate), false)) continue;
                    selectedSize = candidate;
                    selectedFormat = format;
                    break outer;
                }
            }
        }
        if (selectedSize == null) {
            throw new IllegalStateException("Auto Lens Discovery exhausted RAW10/RAW_SENSOR streams for " + key);
        }

        rawFormat = selectedFormat;
        stillSize = selectedSize;
        previewSize = selectedSize;
        previewProcessSize = derivePreviewProcessSize(selectedSize, PREVIEW_SHORT_EDGE_DEFAULT);
        currentProfileNeedsVerification = !lensProfiles.getBoolean(key + ".captureVerified", false);
        activeBayerOffset = lensProfiles.getInt(key + ".bayerOffset", -1);

        lensProfiles.edit()
                .putInt(key + ".format", rawFormat)
                .putInt(key + ".width", selectedSize.getWidth())
                .putInt(key + ".height", selectedSize.getHeight())
                .putInt(key + ".previewShortEdge", PREVIEW_SHORT_EDGE_DEFAULT)
                .apply();
        Log.i(TAG, "IRIS_26685_SPEKTRA_AUTO_LENS_PROFILE route=" + route
                + " persisted=" + persisted + " format=" + rawFormat
                + " rawStream=" + previewSize + " vfS=" + previewProcessSize
                + " fps=" + TARGET_PREVIEW_FPS + " quality=LOW captureVerified="
                + !currentProfileNeedsVerification + " bayerOffset=" + activeBayerOffset);
    }

    private static String streamFailureKey(String key, int format, Size size) {
        return key + ".failed." + format + "." + size.getWidth() + "x" + size.getHeight();
    }

    private Size findAdvertisedRawSize(StreamConfigurationMap map, int format, int width, int height) {
        if ((format != ImageFormat.RAW10 && format != ImageFormat.RAW_SENSOR) || width <= 0 || height <= 0) {
            return null;
        }
        Size[] advertised = map.getOutputSizes(format);
        if (advertised == null) return null;
        for (Size s : advertised) {
            if (s != null && s.getWidth() == width && s.getHeight() == height
                    && (width & 1) == 0 && (height & 1) == 0) return s;
        }
        return null;
    }

    private String lensProfileKey() {
        return route == null ? "lens.unknown" : lensProfileKeyForRoute(route);
    }

    private static String lensProfileKeyForRoute(Route r) {
        String safe = routeProfileId(r).replaceAll("[^A-Za-z0-9_.-]", "_");
        return "lens." + safe;
    }

    private static Size derivePreviewProcessSize(Size source, int shortEdge) {
        final int sw = source.getWidth();
        final int sh = source.getHeight();
        int w;
        int h;
        if (sw >= sh) {
            h = Math.min(sh, shortEdge);
            w = Math.max(2, (int)Math.round((double)sw * h / sh));
        } else {
            w = Math.min(sw, shortEdge);
            h = Math.max(2, (int)Math.round((double)sh * w / sw));
        }
        w &= ~1;
        h &= ~1;
        if (w <= 0 || h <= 0) throw new IllegalStateException("Invalid VF-S preview dimensions");
        return new Size(w, h);
    }

    private static long area(Size s) { return (long)s.getWidth() * s.getHeight(); }

    private void configurePreviewSession(long g) {
        configurePreviewSession(g, false);
    }

    private void configurePreviewSession(long g, boolean restoringAfterStill) {
        if (!isCurrent(g) || cameraDevice == null) return;
        setState(restoringAfterStill ? State.PREVIEW_RECONFIGURING : State.CONFIGURING);
        previewPresented.set(false);
        if (previewRenderer != null) previewRenderer.beginPreviewSession();
        currentStreamRawSeen = false;
        currentStreamResultSeen = false;
        closeSessionAndReaders();
        previewReader = ImageReader.newInstance(previewSize.getWidth(), previewSize.getHeight(), rawFormat, 4);
        previewReader.setOnImageAvailableListener(reader -> onRawAvailable(reader, g), cameraHandler);
        Surface rawSurface = previewReader.getSurface();
        try {
            repeatingBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            repeatingBuilder.addTarget(rawSurface);
            configureManualSensor(repeatingBuilder, requestedIso, requestedExposureNs);
            configureDefaultAf(repeatingBuilder);
            applyFlashToPreviewRequest(repeatingBuilder);
            repeatingBuilder.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO);
            repeatingBuilder.set(CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE,
                    CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE_ON);
            armFatalWatchdog(g, restoringAfterStill ? State.PREVIEW_RECONFIGURING : State.CONFIGURING,
                    PREVIEW_CONFIG_TIMEOUT_MS,
                    restoringAfterStill ? "PREVIEW_RESTORE_CONFIG_TIMEOUT" : "PREVIEW_SESSION_CONFIG_TIMEOUT");
            createSession(Collections.singletonList(rawSurface), g, new CameraCaptureSession.StateCallback() {
                @Override public void onConfigured(@NonNull CameraCaptureSession s) {
                    if (!isCurrent(g) || cameraDevice == null) { s.close(); return; }
                    session = s;
                    submitRepeating();
                    setState(State.STREAMING);
                    armFatalWatchdog(g, State.STREAMING, PREVIEW_FIRST_FRAME_TIMEOUT_MS,
                            restoringAfterStill ? "PREVIEW_RESTORE_FIRST_FRAME_TIMEOUT"
                                    : "PREVIEW_FIRST_FRAME_TIMEOUT");
                    if (focusLocked && touchMeterActive && manualFocusDistance == null) {
                        applyTouchFocus(touchMeterX, touchMeterY, true);
                    }
                    Log.i(TAG, "IRIS_26684_SPEKTRA_STREAMING generation=" + g
                            + " rawStream=" + previewSize + " vfS=" + previewProcessSize
                            + " format=" + rawFormat + " sessionReuseReady=true");
                }
                @Override public void onConfigureFailed(@NonNull CameraCaptureSession s) {
                    if (isCurrent(g)) fail(g, "PREVIEW_SESSION_CONFIGURE_FAILED", null);
                }
            });
        } catch (Throwable t) {
            fail(g, "PREVIEW_SESSION_CREATE_FAILED", t);
        }
    }

    private void createSession(List<Surface> surfaces, long g, CameraCaptureSession.StateCallback callback)
            throws CameraAccessException {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && route != null && route.physicalOutputId != null) {
            List<OutputConfiguration> outputs = new ArrayList<>();
            for (Surface surface : surfaces) {
                OutputConfiguration oc = new OutputConfiguration(surface);
                oc.setPhysicalCameraId(route.physicalOutputId);
                outputs.add(oc);
            }
            cameraDevice.createCaptureSession(new SessionConfiguration(
                    SessionConfiguration.SESSION_REGULAR, outputs, cameraExecutor, callback));
        } else {
            cameraDevice.createCaptureSession(surfaces, callback, cameraHandler);
        }
    }

    private void onRawAvailable(ImageReader reader, long g) {
        if (!isCurrent(g)) {
            Image stale = reader.acquireLatestImage();
            if (stale != null) stale.close();
            return;
        }
        final State current = getState();
        if (current == State.STILL_CONFIGURING || current == State.STILL_CAPTURING) {
            onStillRawFromSharedReader(reader, g);
            return;
        }
        if (current != State.STREAMING) {
            Image stale = reader.acquireLatestImage();
            if (stale != null) stale.close();
            return;
        }
        final Image image = reader.acquireLatestImage();
        if (image == null) return;
        try {
            validateRawImageContract(image, "preview", !loggedPreviewRawContract);
            loggedPreviewRawContract = true;
            currentStreamRawSeen = true;
        } catch (Throwable t) {
            image.close();
            Log.e(TAG, "IRIS_26685_SPEKTRA_PREVIEW_RAW_CONTRACT_FAILED", t);
            return;
        }
        final long timestamp = image.getTimestamp();
        TotalCaptureResult result = previewResults.get(timestamp);
        if (result != null) {
            previewResults.remove(timestamp);
            schedulePreviewDecode(image, result, g);
        } else {
            putPendingPreviewImage(timestamp, image);
        }
    }

    private void putPendingPreviewImage(long timestamp, Image image) {
        Image replaced = previewImages.get(timestamp);
        if (replaced != null && replaced != image) {
            try { replaced.close(); } catch (Throwable ignored) {}
        }
        previewImages.put(timestamp, image);
        while (previewImages.size() > 3) {
            Image oldest = previewImages.valueAt(0);
            previewImages.removeAt(0);
            if (oldest != null) try { oldest.close(); } catch (Throwable ignored) {}
        }
    }

    private void schedulePreviewDecode(Image image, TotalCaptureResult result, long g) {
        if (image == null || result == null) {
            if (image != null) image.close();
            return;
        }
        if (!isCurrent(g) || state != State.STREAMING || previewRenderer == null
                || !previewRenderer.canAcceptFrame() || !previewDecodeBusy.compareAndSet(false, true)) {
            image.close();
            return;
        }
        final SpektraFrameMetadata baseMetadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), requestedIso, image.getWidth(), image.getHeight());
        final int previewBayerOffset = activeBayerOffset >= 0
                ? activeBayerOffset : baseMetadata.geometryBayerOffsetHint;
        try {
            previewDecodeExecutor.execute(() -> {
                SpektraRawFrame decoded = null;
                Throwable failure = null;
                try {
                    // copyPreviewFrom detaches packed RAW and closes the Camera2 Image before
                    // native Vulkan processing. First-run discovery may be meter-only until Bayer origin is proven.
                    SpektraFrameMetadata nativeMetadata = null;
                    float[] nativeMatrix = null;
                    if (previewBayerOffset >= 0 && previewBayerOffset <= 3 && baseMetadata.neutral3 != null) {
                        nativeMetadata = SpektraFrameMetadata.from(result, characteristics,
                                result.getFrameNumber(), requestedIso, image.getWidth(), image.getHeight(),
                                previewBayerOffset);
                        SpektraColorSolver.Solution color = SpektraColorSolver.solveQuiet(result,
                                nativeMetadata.neutral3,
                                characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1),
                                characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2),
                                characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1),
                                characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2),
                                characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1),
                                characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2),
                                valueOrZero(characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)),
                                valueOrZero(characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)));
                        nativeMatrix = color == null ? null : color.sensorToLinearSrgb;
                    }
                    decoded = SpektraRawFrame.copyPreviewFrom(image, PREVIEW_SHORT_EDGE_DEFAULT,
                            nativeMetadata, nativeMatrix);
                } catch (Throwable t) {
                    failure = t;
                } finally {
                    try { image.close(); } catch (Throwable ignored) {}
                }
                final SpektraRawFrame frame = decoded;
                final Throwable error = failure;
                Handler h = cameraHandler;
                if (h == null) {
                    previewDecodeBusy.set(false);
                    return;
                }
                h.post(() -> {
                    previewDecodeBusy.set(false);
                    if (!isCurrent(g) || state != State.STREAMING) return;
                    if (error != null) {
                        failProcessor(g, "RAW_PREVIEW_PROCESS_FAILED", error);
                        return;
                    }
                    if (frame == null) {
                        failProcessor(g, "RAW_PREVIEW_PROCESS_RETURNED_NULL", null);
                        return;
                    }
                    if (frame.width != previewProcessSize.getWidth() || frame.height != previewProcessSize.getHeight()) {
                        Log.e(TAG, "IRIS_26685_SPEKTRA_VFS_SIZE_MISMATCH got=" + frame.width + "x" + frame.height
                                + " expected=" + previewProcessSize);
                        return;
                    }
                    consumePreviewPair(frame, result, g);
                });
            });
        } catch (RuntimeException rejected) {
            previewDecodeBusy.set(false);
            image.close();
            if (isCurrent(g)) Log.e(TAG, "IRIS_26685_SPEKTRA_PREVIEW_DECODE_QUEUE_REJECTED", rejected);
        }
    }

    private final CameraCaptureSession.CaptureCallback repeatingCallback = new CameraCaptureSession.CaptureCallback() {
        @Override public void onCaptureCompleted(@NonNull CameraCaptureSession s,
                @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
            if (s != session || state != State.STREAMING) return;
            Long ts = result.get(TotalCaptureResult.SENSOR_TIMESTAMP);
            if (ts == null) return;
            currentStreamResultSeen = true;
            Image image = previewImages.get(ts);
            if (image != null) {
                previewImages.remove(ts);
                schedulePreviewDecode(image, result, activeGeneration);
            } else {
                previewResults.put(ts, result);
                trimSparse(previewResults, 8);
            }
        }
    };

    private void consumePreviewPair(SpektraRawFrame frame, TotalCaptureResult result, long g) {
        if (!isCurrent(g) || state != State.STREAMING || characteristics == null) return;
        SpektraFrameMetadata baseMetadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), requestedIso, frame.sourceWidth(), frame.sourceHeight());
        // Native owner intentionally dropped this verified preview because saved work or another
        // VF-S dispatch already owned the persistent compute queue. Do not run AE on a fake meter.
        if (activeBayerOffset >= 0 && frame.previewLinearRgba16f == null) return;
        if (activeBayerOffset < 0) {
            int geometryHint = baseMetadata.geometryBayerOffsetHint;
            activeBayerOffset = frame.estimateBayerOffset(baseMetadata.cfaArrangement,
                    baseMetadata.blackLevel4, baseMetadata.whiteLevel, geometryHint);
            if (activeBayerOffset < 0) {
                Log.e(TAG, "IRIS_26685_SPEKTRA_BAYER_ORIGIN_AMBIGUOUS route=" + route
                        + " geometryHint=" + geometryHint + " sensorCfa=" + baseMetadata.cfaArrangement
                        + " action=reject_stream");
                failProcessor(g, "BAYER_ORIGIN_AMBIGUOUS", null);
                return;
            }
            lensProfiles.edit().putInt(lensProfileKey() + ".bayerOffset", activeBayerOffset).apply();
            Log.i(TAG, "IRIS_26685_SPEKTRA_BAYER_OFFSET_VERIFIED route=" + route
                    + " geometryHint=" + geometryHint + " selected=" + activeBayerOffset
                    + " sensorCfa=" + baseMetadata.cfaArrangement);
        }
        SpektraFrameMetadata metadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), requestedIso, frame.sourceWidth(), frame.sourceHeight(), activeBayerOffset);
        if (metadata.neutral3 == null) {
            if (!loggedPreviewWaitWb) {
                loggedPreviewWaitWb = true;
                Log.w(TAG, "IRIS_26685_SPEKTRA_PREVIEW_WAIT_WB firstTimestamp=" + frame.timestampNs);
            }
            return;
        }
        loggedPreviewWaitWb = false;
        RggbChannelVector gains = result.get(TotalCaptureResult.COLOR_CORRECTION_GAINS);
        ColorSpaceTransform transform = result.get(TotalCaptureResult.COLOR_CORRECTION_TRANSFORM);
        if (gains != null) latestColorGains = gains;
        if (transform != null) latestColorTransform = transform;
        double meter = frame.centerWeightedMeter(metadata.blackLevel4, metadata.whiteLevel,
                touchMeterX, touchMeterY, touchMeterActive);
        SpektraExposureController.Solution solution = exposureController.update(System.nanoTime(), meter);
        if (solution.iso != requestedIso || solution.exposureNs != requestedExposureNs) {
            requestedIso = solution.iso;
            requestedExposureNs = solution.exposureNs;
            applyCurrentExposureToRepeating();
        }
        // The first discovery frame may exist only as a reduced RAW meter while Bayer origin is
        // being verified. Never fall back to demosaicing that reduced Bayer carrier for display;
        // wait for the next full RAW frame to produce source-lattice camera RGB with the verified origin.
        if (frame.previewLinearRgba16f == null) return;
        previewRenderer.render(frame);
    }

    private int geometryBayerOffsetHint(int rawWidth, int rawHeight) {
        if (characteristics == null) return -1;
        try {
            return SpektraFrameMetadata.geometryBayerOffsetHint(characteristics, null, rawWidth, rawHeight);
        } catch (IllegalArgumentException unresolved) {
            Log.e(TAG, "IRIS_26686_SPEKTRA_RAW_GEOMETRY_UNRESOLVED raw=" + rawWidth + "x" + rawHeight, unresolved);
            return -1;
        }
    }

    private void applyCurrentExposureToRepeating() {
        if (state != State.STREAMING || repeatingBuilder == null || session == null) return;
        configureManualSensor(repeatingBuilder, requestedIso, requestedExposureNs);
        submitRepeating();
    }

    private void configureManualSensor(CaptureRequest.Builder b, int iso, long exposureNs) {
        b.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO);
        b.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
        b.set(CaptureRequest.SENSOR_SENSITIVITY, iso);
        b.set(CaptureRequest.SENSOR_EXPOSURE_TIME, exposureNs);
        long frameDuration = Math.max(exposureNs, 1_000_000_000L / TARGET_PREVIEW_FPS);
        Long maxDuration = characteristics == null ? null
                : characteristics.get(CameraCharacteristics.SENSOR_INFO_MAX_FRAME_DURATION);
        if (maxDuration != null) frameDuration = Math.min(frameDuration, maxDuration);
        b.set(CaptureRequest.SENSOR_FRAME_DURATION, frameDuration);
        setPhysical(b, CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
        setPhysical(b, CaptureRequest.SENSOR_SENSITIVITY, iso);
        setPhysical(b, CaptureRequest.SENSOR_EXPOSURE_TIME, exposureNs);
        setPhysical(b, CaptureRequest.SENSOR_FRAME_DURATION, frameDuration);
    }

    private <T> void setPhysical(CaptureRequest.Builder b, CaptureRequest.Key<T> key, T value) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && route != null && route.physicalOutputId != null) {
            try { b.setPhysicalCameraKey(key, value, route.physicalOutputId); } catch (Throwable ignored) {}
        }
    }

    private void configureDefaultAf(CaptureRequest.Builder b) {
        final Float manual = manualFocusDistance;
        if (manual != null) {
            b.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
            b.set(CaptureRequest.LENS_FOCUS_DISTANCE, manual);
            b.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            setPhysical(b, CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
            setPhysical(b, CaptureRequest.LENS_FOCUS_DISTANCE, manual);
            return;
        }
        int[] modes = characteristics == null ? null
                : characteristics.get(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES);
        int selected = CaptureRequest.CONTROL_AF_MODE_OFF;
        if (contains(modes, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)) {
            selected = CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE;
        } else if (contains(modes, CaptureRequest.CONTROL_AF_MODE_AUTO)) {
            selected = CaptureRequest.CONTROL_AF_MODE_AUTO;
        }
        b.set(CaptureRequest.CONTROL_AF_MODE, selected);
        b.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
    }

    private static boolean contains(int[] a, int v) {
        if (a == null) return false; for (int x : a) if (x == v) return true; return false;
    }

    private void submitRepeating() {
        CameraCaptureSession s = session;
        CaptureRequest.Builder b = repeatingBuilder;
        Handler h = cameraHandler;
        if (s == null || b == null || h == null) return;
        try { s.setRepeatingRequest(b.build(), repeatingCallback, h); }
        catch (Throwable t) { Log.e(TAG, "IRIS_26681_SPEKTRA_REPEATING_FAILED", t); }
    }

    private void submitOneShotThenRepeating() {
        if (session == null || repeatingBuilder == null || cameraHandler == null) return;
        try { session.capture(repeatingBuilder.build(), repeatingCallback, cameraHandler); }
        catch (Throwable t) { Log.e(TAG, "IRIS_26681_SPEKTRA_AF_ONESHOT_FAILED", t); }
    }

    private void applyTouchFocus(float nx, float ny, boolean lock) {
        if (state != State.STREAMING || repeatingBuilder == null || characteristics == null) return;
        Rect active = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        if (active == null) return;
        nx = Math.max(0f, Math.min(1f, nx));
        ny = Math.max(0f, Math.min(1f, ny));
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) nx = 1f - nx;
        final float sx;
        final float sy;
        switch (outputRotationDegrees()) {
            case 270: sx = 1f - ny; sy = nx; break;
            case 180: sx = 1f - nx; sy = 1f - ny; break;
            case 0: sx = nx; sy = ny; break;
            case 90:
            default: sx = ny; sy = 1f - nx; break;
        }
        int cx = active.left + Math.round(sx * Math.max(1, active.width() - 1));
        int cy = active.top + Math.round(sy * Math.max(1, active.height() - 1));
        int rw = Math.max(1, active.width() / 8);
        int rh = Math.max(1, active.height() / 8);
        int left = Math.max(active.left, Math.min(cx - rw / 2, active.right - rw));
        int top = Math.max(active.top, Math.min(cy - rh / 2, active.bottom - rh));
        MeteringRectangle[] region = new MeteringRectangle[] { new MeteringRectangle(
                left, top, rw, rh, MeteringRectangle.METERING_WEIGHT_MAX - 1) };
        touchAfRegion = region;
        touchMeterRegion = region; // consumed by Spektra metering policy, never Android AE.
        touchMeterX = nx;
        touchMeterY = ny;
        touchMeterActive = true;
        focusLocked = lock;
        if (manualFocusDistance != null) {
            Log.i(TAG, "IRIS_26681_SPEKTRA_TOUCH_METER_ONLY manualFocus=true region=" + region[0]);
            submitRepeating();
            return;
        }
        repeatingBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
        submitOneShotThenRepeating();
        repeatingBuilder.set(CaptureRequest.CONTROL_AF_REGIONS, region);
        repeatingBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_AUTO);
        repeatingBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_START);
        submitOneShotThenRepeating();
        repeatingBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        if (!lock) submitRepeating();
        Log.i(TAG, "IRIS_26681_SPEKTRA_TOUCH_FOCUS region=" + region[0] + " lock=" + lock
                + " androidAeRegionWritten=false");
    }

    private void configureStillSession(long g) {
        if (!isCurrent(g) || cameraDevice == null || session == null || previewReader == null) {
            terminalStillFailure(g, "STILL_ACTIVE_RAW_SESSION_MISSING", null);
            return;
        }
        if (!previewSize.equals(stillSize)) {
            terminalStillFailure(g, "STILL_PROFILE_NOT_REUSABLE preview=" + previewSize + " still=" + stillSize, null);
            return;
        }
        armStillWatchdog(g, State.STILL_CONFIGURING, STILL_CONFIG_TIMEOUT_MS,
                "STILL_ACTIVE_SESSION_REUSE_TIMEOUT");
        try {
            session.stopRepeating();
            Log.i(TAG, "IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true raw=" + stillSize
                    + " format=" + rawFormat + " generation=" + g);
            submitStill(g, previewReader.getSurface());
        } catch (Throwable t) {
            terminalStillFailure(g, "STILL_ACTIVE_SESSION_REUSE_FAILED", t);
        }
    }

    private void submitStill(long g, Surface target) {
        if (!isCurrent(g) || cameraDevice == null || session == null || target == null) return;
        try {
            setState(State.STILL_CAPTURING);
            armStillWatchdog(g, State.STILL_CAPTURING, STILL_CAPTURE_TIMEOUT_MS,
                    "STILL_CAPTURE_TIMEOUT");
            closePendingStillImages();
            pendingStillFrame = null;
            stillDecodeInFlight = false;
            pendingStillResult = null;
            pendingStillTimestamp = 0L;
            pendingStillWallTimeMs = System.currentTimeMillis();
            pendingStillFrozenIso = requestedIso;
            final int frozenIso = requestedIso;
            final long frozenExposure = requestedExposureNs;
            CaptureRequest.Builder b = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(target);
            configureManualSensor(b, frozenIso, frozenExposure);
            configureDefaultAf(b); // No new AF trigger; current lens state continues.
            applyFrozenWhiteBalance(b);
            b.set(CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE,
                    CaptureRequest.STATISTICS_LENS_SHADING_MAP_MODE_ON);
            if (touchAfRegion != null) b.set(CaptureRequest.CONTROL_AF_REGIONS, touchAfRegion);
            applyFlashToStillRequest(b);
            b.setTag("IRIS_26684_SPEKTRA_" + g);
            session.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureStarted(@NonNull CameraCaptureSession activeSession,
                        @NonNull CaptureRequest request, long timestamp, long frameNumber) {
                    if (isCurrent(g)) {
                        pendingStillWallTimeMs = System.currentTimeMillis();
                        if (!verificationCaptureInFlight) events.onFrameCaptureStarted("SPEKTRA");
                    }
                }
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession activeSession,
                        @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    if (!isCurrent(g) || activeSession != session) return;
                    Long ts = result.get(TotalCaptureResult.SENSOR_TIMESTAMP);
                    if (ts == null) { terminalStillFailure(g, "STILL_RESULT_NO_TIMESTAMP", null); return; }
                    pendingStillTimestamp = ts;
                    pendingStillResult = result;
                    discardPendingStillImagesExcept(ts);
                    tryCompleteStill(g);
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession activeSession,
                        @NonNull CaptureRequest request, @NonNull android.hardware.camera2.CaptureFailure failure) {
                    if (isCurrent(g)) terminalStillFailure(g, "STILL_CAPTURE_FAILED_" + failure.getReason(), null);
                }
            }, cameraHandler);
        } catch (Throwable t) {
            terminalStillFailure(g, "STILL_SUBMIT_FAILED", t);
        }
    }

    private void applyFrozenWhiteBalance(CaptureRequest.Builder b) {
        if (latestColorGains != null && latestColorTransform != null) {
            b.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_OFF);
            b.set(CaptureRequest.COLOR_CORRECTION_MODE, CaptureRequest.COLOR_CORRECTION_MODE_TRANSFORM_MATRIX);
            b.set(CaptureRequest.COLOR_CORRECTION_GAINS, latestColorGains);
            b.set(CaptureRequest.COLOR_CORRECTION_TRANSFORM, latestColorTransform);
            setPhysical(b, CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_OFF);
            setPhysical(b, CaptureRequest.COLOR_CORRECTION_MODE, CaptureRequest.COLOR_CORRECTION_MODE_TRANSFORM_MATRIX);
            setPhysical(b, CaptureRequest.COLOR_CORRECTION_GAINS, latestColorGains);
            setPhysical(b, CaptureRequest.COLOR_CORRECTION_TRANSFORM, latestColorTransform);
            Log.i(TAG, "IRIS_26681_SPEKTRA_WB_FREEZE source=matchedPreview gains=true transform=true");
        } else {
            b.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO);
            b.set(CaptureRequest.CONTROL_AWB_LOCK, true);
            setPhysical(b, CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO);
            setPhysical(b, CaptureRequest.CONTROL_AWB_LOCK, true);
            Log.i(TAG, "IRIS_26681_SPEKTRA_WB_FREEZE source=halAwbLockFallback");
        }
    }

    private int outputRotationDegrees() {
        Integer sensor = characteristics == null ? null : characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Integer facing = characteristics == null ? null : characteristics.get(CameraCharacteristics.LENS_FACING);
        int display = 0;
        int rotation = activity.getWindowManager().getDefaultDisplay().getRotation();
        if (rotation == Surface.ROTATION_90) display = 90;
        else if (rotation == Surface.ROTATION_180) display = 180;
        else if (rotation == Surface.ROTATION_270) display = 270;
        int so = sensor == null ? 0 : sensor;
        if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
            return (so + display) % 360;
        }
        return (so - display + 360) % 360;
    }

    private void applyFlashToPreviewRequest(CaptureRequest.Builder b) {
        // Photon/Iris uses AE_MODE_OFF (0) as its top-bar torch state. Spektra keeps sensor AE OFF
        // regardless; only FLASH_MODE changes. AUTO remains non-invasive until its audited preflash
        // transaction is implemented rather than inventing an Android-AE substitute.
        if (flashPreference == CaptureRequest.CONTROL_AE_MODE_OFF) {
            b.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_TORCH);
        } else {
            b.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF);
        }
    }

    private void applyFlashToStillRequest(CaptureRequest.Builder b) {
        // Sensor AE remains OFF. Torch/off/always are deterministic Spektra-owned behaviors.
        if (flashPreference == CaptureRequest.CONTROL_AE_MODE_OFF) {
            b.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_TORCH);
        } else if (flashPreference == CaptureRequest.CONTROL_AE_MODE_ON_ALWAYS_FLASH) {
            b.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_SINGLE);
        } else {
            b.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF);
            if (flashPreference == CaptureRequest.CONTROL_AE_MODE_ON_AUTO_FLASH) {
                Log.w(TAG, "IRIS_26681_SPEKTRA_AUTO_FLASH_HELD_OFF reason=preflash_contract_not_proven");
            }
        }
    }

    private void onStillRawFromSharedReader(ImageReader reader, long g) {
        Image image = reader.acquireNextImage();
        if (image == null) return;
        boolean retained = false;
        try {
            validateRawImageContract(image, "still-shared-session", !loggedStillRawContract);
            loggedStillRawContract = true;
            if (!isCurrent(g)) return;
            final long ts = image.getTimestamp();
            if (pendingStillTimestamp != 0L && ts != pendingStillTimestamp) {
                Log.d(TAG, "IRIS_26684_SPEKTRA_STILL_DROP_STALE_RAW timestamp=" + ts
                        + " expected=" + pendingStillTimestamp);
                return;
            }
            Image old = pendingStillImages.get(ts);
            if (old != null && old != image) old.close();
            pendingStillImages.put(ts, image);
            retained = true;
            trimPendingStillImages(3);
            tryCompleteStill(g);
        } catch (Throwable t) {
            terminalStillFailure(g, "STILL_RAW_PAIR_FAILED", t);
        } finally {
            if (!retained) image.close();
        }
    }

    private void tryCompleteStill(long g) {
        if (!isCurrent(g) || pendingStillResult == null || pendingStillTimestamp == 0L) return;
        if (pendingStillFrame == null) {
            if (stillDecodeInFlight) return;
            final Image exact = pendingStillImages.get(pendingStillTimestamp);
            if (exact == null) return;
            pendingStillImages.remove(pendingStillTimestamp);
            closePendingStillImages();
            stillDecodeInFlight = true;
            savedProcessExecutor.execute(() -> {
                SpektraRawFrame decoded = null;
                Throwable failure = null;
                try {
                    decoded = SpektraRawFrame.copyStillFrom(exact);
                } catch (Throwable t) {
                    failure = t;
                } finally {
                    try { exact.close(); } catch (Throwable ignored) {}
                }
                final SpektraRawFrame ready = decoded;
                final Throwable error = failure;
                Handler h = cameraHandler;
                if (h != null) h.post(() -> {
                    stillDecodeInFlight = false;
                    if (!isCurrent(g)) return;
                    if (error != null || ready == null) {
                        terminalStillFailure(g, "STILL_NATIVE_RAW_DECODE_FAILED", error);
                        return;
                    }
                    pendingStillFrame = ready;
                    tryCompleteStill(g);
                });
            });
            return;
        }
        Long resultTs = pendingStillResult.get(TotalCaptureResult.SENSOR_TIMESTAMP);
        if (resultTs == null || pendingStillFrame.timestampNs != resultTs) {
            terminalStillFailure(g, "RAW_RESULT_TIMESTAMP_MISMATCH raw=" + pendingStillFrame.timestampNs
                    + " result=" + resultTs, null);
            return;
        }
        final SpektraRawFrame raw = pendingStillFrame;
        final TotalCaptureResult result = pendingStillResult;
        closePendingStillImages();
        pendingStillFrame = null;
        pendingStillResult = null;
        int stillBayerOffset = activeBayerOffset >= 0 ? activeBayerOffset
                : SpektraFrameMetadata.geometryBayerOffsetHint(characteristics, result, raw.sourceWidth(), raw.sourceHeight());
        if (stillBayerOffset < 0) {
            terminalStillFailure(g, "BAYER_ORIGIN_UNRESOLVED_AT_STILL", null);
            return;
        }
        SpektraFrameMetadata metadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), pendingStillFrozenIso, raw.sourceWidth(), raw.sourceHeight(), stillBayerOffset);
        if (metadata.neutral3 == null) {
            terminalStillFailure(g, "MISSING_RAW_WHITE_BALANCE", null);
            return;
        }
        SpektraColorSolver.Solution color = SpektraColorSolver.solve(result, metadata.neutral3,
                characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1),
                characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2),
                characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1),
                characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2),
                characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1),
                characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2),
                valueOrZero(characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)),
                valueOrZero(characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)));
        if (color == null) {
            terminalStillFailure(g, "CAMERA_COLOR_SOLUTION_FAILED", null);
            return;
        }
        if (verificationCaptureInFlight) {
            verificationCaptureSucceeded = true;
            Log.i(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_STILL_VERIFIED route=" + route
                    + " timestamp=" + raw.timestampNs + " frame=" + result.getFrameNumber()
                    + " awaitingPreviewResume=true");
            resumePreviewAfterStillReuse(g, true);
            return;
        }
        setState(State.STILL_CAPTURED);
        Log.i(TAG, "IRIS_26684_SPEKTRA_STILL_CAPTURED timestamp=" + raw.timestampNs
                + " frame=" + result.getFrameNumber() + " sessionReused=true");
        if (!captureJobState.compareAndSet(CaptureJobState.IDLE, CaptureJobState.PROCESSING)) {
            terminalStillFailure(g, "CAPTURE_JOB_STATE_BUSY", null);
            return;
        }
        activity.runOnUiThread(() -> {
            events.onFrameCaptureCompleted("SPEKTRA");
            events.onCaptureSequenceCompleted("SPEKTRA");
            events.onProcessingStarted("Spektra");
        });
        final int outputRotation = outputRotationDegrees();
        final String lensModel = metadata.focalLengthMm > 0f
                ? (route == null ? "" : route.characteristicsId) + " " + metadata.focalLengthMm + "mm"
                : (route == null ? "" : route.characteristicsId);
        final long captureWallTimeMs = pendingStillWallTimeMs > 0L
                ? pendingStillWallTimeMs : System.currentTimeMillis();
        final SpektraShot shot = new SpektraShot(raw, metadata, captureWallTimeMs,
                color.sensorToLinearSrgb, outputRotation,
                route == null ? "" : route.characteristicsId, lensModel);

        // Freeze one immutable recipe, restore one actual preview frame first, then run the heavy
        // saved path. This prevents saved GPU priority from starving the proof-of-life frame.
        if (!pendingSavedShot.compareAndSet(null, shot)) {
            captureJobState.set(CaptureJobState.IDLE);
            terminalStillFailure(g, "PENDING_SAVED_SHOT_ALREADY_OWNED", null);
            return;
        }
        resumePreviewAfterStillReuse(g, true);
    }

    private void trimPendingStillImages(int max) {
        while (pendingStillImages.size() > max) {
            Image image = pendingStillImages.valueAt(0);
            pendingStillImages.removeAt(0);
            try { if (image != null) image.close(); } catch (Throwable ignored) {}
        }
    }

    private void discardPendingStillImagesExcept(long timestamp) {
        for (int i = pendingStillImages.size() - 1; i >= 0; --i) {
            if (pendingStillImages.keyAt(i) == timestamp) continue;
            Image image = pendingStillImages.valueAt(i);
            pendingStillImages.removeAt(i);
            try { if (image != null) image.close(); } catch (Throwable ignored) {}
        }
    }

    private void closePendingPreviewImages() {
        for (int i = 0; i < previewImages.size(); ++i) {
            Image image = previewImages.valueAt(i);
            if (image != null) try { image.close(); } catch (Throwable ignored) {}
        }
        previewImages.clear();
        previewResults.clear();
    }

    private void closePendingStillImages() {
        for (int i = pendingStillImages.size() - 1; i >= 0; --i) {
            Image image = pendingStillImages.valueAt(i);
            try { if (image != null) image.close(); } catch (Throwable ignored) {}
        }
        pendingStillImages.clear();
    }

    private static int valueOrZero(Integer value) { return value == null ? 0 : value; }
    private static int valueOrZero(Byte value) { return value == null ? 0 : Byte.toUnsignedInt(value); }

    private void startPendingSavedProcess(String trigger) {
        final SpektraShot shot = pendingSavedShot.getAndSet(null);
        if (shot == null) return;
        Log.i(TAG, "IRIS_26687_SPEKTRA_SAVED_JOB_START trigger=" + trigger
                + " timestamp=" + shot.raw.timestampNs);
        try {
            savedProcessExecutor.execute(() -> processShot(activeGeneration, shot));
        } catch (RuntimeException rejected) {
            captureJobState.set(CaptureJobState.IDLE);
            Log.e(TAG, "IRIS_26687_SPEKTRA_SAVED_PROCESS_QUEUE_REJECTED trigger=" + trigger, rejected);
            activity.runOnUiThread(() -> events.onProcessingError("Spektra processing queue unavailable"));
        }
    }

    private void processShot(long g, SpektraShot shot) {
        File recovery = null;
        try {
            recovery = SpektraShotStore.writeAtomic(activity, shot);
            SpektraShot frozenShot = SpektraShotStore.read(recovery);
            SpektraProcessor.Result result = new SpektraProcessor(activity).process(frozenShot, recovery);
            if (!result.saved) throw new IllegalStateException(result.error == null ? "Spektra processing failed" : result.error);
            if (!recovery.delete()) Log.w(TAG, "IRIS_26681_SPEKTRA_RECOVERY_DELETE_DEFERRED file=" + recovery);
            events.notifyImageSavedStatus(true, result.path);
            events.onProcessingFinished("Spektra");
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26681_SPEKTRA_PROCESS_FAILED recovery=" + recovery, t);
            events.onProcessingError(t.getMessage() == null ? "Spektra processing failed" : t.getMessage());
        } finally {
            captureJobState.set(CaptureJobState.IDLE);
        }
    }

    private void resumePreviewAfterStillReuse(long g, boolean successfulCapture) {
        if (!isCurrent(g) || cameraDevice == null) return;
        closePendingStillImages();
        pendingStillFrame = null;
        stillDecodeInFlight = false;
        pendingStillResult = null;
        pendingStillTimestamp = 0L;
        if (session == null || previewReader == null || repeatingBuilder == null) {
            Log.w(TAG, "IRIS_26684_SPEKTRA_SESSION_REUSE_LOST rebuilding=true");
            configurePreviewSession(g, true);
            return;
        }
        if (previewRenderer != null) previewRenderer.beginPreviewSession();
        awaitingPostStillPreview = successfulCapture;
        previewPresented.set(false);
        setState(State.STREAMING);
        submitRepeating();
        armFatalWatchdog(g, State.STREAMING, PREVIEW_FIRST_FRAME_TIMEOUT_MS,
                "PREVIEW_RESUME_FIRST_FRAME_TIMEOUT");
        Log.i(TAG, "IRIS_26684_SPEKTRA_PREVIEW_RESUMED sessionReused=true generation=" + g);
    }

    private void terminalStillFailure(long g, String reason, Throwable t) {
        if (verificationCaptureInFlight || currentProfileNeedsVerification) {
            if (isDiscoveryStreamFailure(reason)) {
                retryDiscoveryStream(g, reason, t);
            } else {
                failProcessor(g, reason, t);
            }
            return;
        }
        if (t != null) Log.e(TAG, "IRIS_26687_SPEKTRA_STILL_FAILURE reason=" + reason, t);
        else Log.e(TAG, "IRIS_26687_SPEKTRA_STILL_FAILURE reason=" + reason);
        setState(State.STILL_FAILED);
        activity.runOnUiThread(() -> {
            events.onCaptureStillPictureRejected(reason);
            events.onProcessingError(reason);
        });
        resumePreviewAfterStillReuse(g, false);
    }

    private boolean isDiscoveryStreamFailure(String reason) {
        if (reason == null) return false;
        if (reason.startsWith("PREVIEW_SESSION_CONFIGURE_FAILED")
                || reason.startsWith("PREVIEW_SESSION_CREATE_FAILED")) return true;
        if (reason.contains("FIRST_FRAME_TIMEOUT")) return !currentStreamRawSeen;
        return reason.startsWith("STILL_CAPTURE_FAILED_")
                || reason.equals("STILL_CAPTURE_TIMEOUT")
                || reason.equals("STILL_SUBMIT_FAILED")
                || reason.equals("STILL_ACTIVE_SESSION_REUSE_FAILED");
    }

    private void failProcessor(long g, String reason, Throwable t) {
        if (!isCurrent(g)) return;
        previewPresented.set(false);
        startPendingSavedProcess("processor_failure");
        automaticDiscoveryActive = false;
        automaticDiscoveryRoute = null;
        automaticDiscoveryQueue.clear();
        if (t != null) Log.e(TAG, "IRIS_26687_SPEKTRA_PROCESSOR_FATAL reason=" + reason
                + " rawSeen=" + currentStreamRawSeen + " resultSeen=" + currentStreamResultSeen, t);
        else Log.e(TAG, "IRIS_26687_SPEKTRA_PROCESSOR_FATAL reason=" + reason
                + " rawSeen=" + currentStreamRawSeen + " resultSeen=" + currentStreamResultSeen);
        closeCameraObjects(true);
        setState(State.FAILED);
        activity.runOnUiThread(() -> events.onError(reason));
    }

    private void fail(long g, String reason, Throwable t) {
        if (!isCurrent(g)) return;
        previewPresented.set(false);
        startPendingSavedProcess("fatal_failure");
        if (currentProfileNeedsVerification && route != null && previewSize != null) {
            if (isDiscoveryStreamFailure(reason)) retryDiscoveryStream(g, reason, t);
            else failProcessor(g, reason, t);
            return;
        }
        if (t != null) Log.e(TAG, "IRIS_26687_SPEKTRA_FATAL reason=" + reason, t);
        else Log.e(TAG, "IRIS_26687_SPEKTRA_FATAL reason=" + reason);
        closeCameraObjects(true);
        setState(State.FAILED);
        activity.runOnUiThread(() -> events.onError(reason));
    }

    private void onPreviewRenderFailure(Throwable t) {
        final long g = activeGeneration;
        Handler h = cameraHandler;
        if (h != null) h.post(() -> failProcessor(g, "FILM_PREVIEW_RENDER_FAILED", t));
    }

    private void onFirstPreviewFramePresented() {
        final long g = activeGeneration;
        Handler h = cameraHandler;
        if (h == null) return;
        h.post(() -> {
            if (!isCurrent(g) || state != State.STREAMING) return;
            cancelWatchdog();
            final String key = lensProfileKey();
            SharedPreferences.Editor profileEdit = lensProfiles.edit().putBoolean(key + ".previewVerified", true);
            if (awaitingPostStillPreview && !verificationCaptureInFlight && pendingSavedShot.get() != null) {
                awaitingPostStillPreview = false;
                profileEdit.apply();
                previewPresented.set(true);
                host.onSpektraPreviewReady();
                startPendingSavedProcess("preview_restored");
                return;
            }
            if (awaitingPostStillPreview && verificationCaptureInFlight && verificationCaptureSucceeded) {
                profileEdit.putBoolean(key + ".captureVerified", true).remove(key + ".unsupported").apply();
                awaitingPostStillPreview = false;
                verificationCaptureInFlight = false;
                verificationCaptureSucceeded = false;
                currentProfileNeedsVerification = false;
                Log.i(TAG, "IRIS_26685_SPEKTRA_PROFILE_VERIFIED route=" + route
                        + " format=" + rawFormat + " raw=" + previewSize + " vfS=" + previewProcessSize
                        + " bayerOffset=" + activeBayerOffset + " preview=true still=true resumed=true");
                if (automaticDiscoveryActive) {
                    advanceAutomaticDiscovery(g);
                } else {
                    previewPresented.set(true);
                    host.onSpektraPreviewReady();
                }
                return;
            }
            profileEdit.apply();
            final boolean captureVerified = lensProfiles.getBoolean(key + ".captureVerified", false);
            Log.i(TAG, "IRIS_26685_SPEKTRA_FIRST_FRAME_PRESENTED generation=" + g
                    + " route=" + route + " rawStream=" + previewSize + " vfS=" + previewProcessSize
                    + " format=" + rawFormat + " previewVerified=true captureVerified=" + captureVerified
                    + " autoDiscovery=" + automaticDiscoveryActive);
            if (captureVerified) {
                currentProfileNeedsVerification = false;
                if (automaticDiscoveryActive) advanceAutomaticDiscovery(g);
                else {
                    previewPresented.set(true);
                    host.onSpektraPreviewReady();
                }
                return;
            }
            if (currentProfileNeedsVerification && !verificationCaptureInFlight) {
                verificationCaptureInFlight = true;
                verificationCaptureSucceeded = false;
                Log.i(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_STILL_BEGIN route=" + route
                        + " sessionReuse=true userShutter=false");
                setState(State.STILL_CONFIGURING);
                configureStillSession(g);
            }
        });
    }

    private void advanceAutomaticDiscovery(long g) {
        if (!isCurrent(g) || !automaticDiscoveryActive) return;
        if (!automaticDiscoveryQueue.isEmpty()) {
            automaticDiscoveryRoute = automaticDiscoveryQueue.remove(0);
            Log.i(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_NEXT route=" + automaticDiscoveryRoute
                    + " remaining=" + automaticDiscoveryQueue.size());
            closeCameraObjects(false);
            if (isCurrent(g)) openForPreview(g, true);
            return;
        }
        automaticDiscoveryRoute = null;
        automaticDiscoveryActive = false;
        Log.i(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_COMPLETE returnCamera=" + automaticDiscoveryReturnCameraId);
        closeCameraObjects(false);
        if (isCurrent(g)) openForPreview(g, true);
    }

    private void skipAutomaticDiscoveryRoute(long g, String reason, Throwable t) {
        if (!isCurrent(g) || automaticDiscoveryRoute == null) return;
        final String key = lensProfileKeyForRoute(automaticDiscoveryRoute);
        lensProfiles.edit().putBoolean(key + ".unsupported", true)
                .remove(key + ".previewVerified").remove(key + ".captureVerified")
                .remove(key + ".bayerOffset").apply();
        if (t != null) Log.w(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_LENS_SKIP route=" + automaticDiscoveryRoute
                + " reason=" + reason, t);
        else Log.w(TAG, "IRIS_26685_SPEKTRA_DISCOVERY_LENS_SKIP route=" + automaticDiscoveryRoute
                + " reason=" + reason);
        advanceAutomaticDiscovery(g);
    }

    private void retryDiscoveryStream(long g, String reason, Throwable t) {
        if (!isCurrent(g) || route == null || previewSize == null) return;
        if (!isDiscoveryStreamFailure(reason)) {
            failProcessor(g, "DISCOVERY_REJECT_DOMAIN_VIOLATION_" + reason, t);
            return;
        }
        final String key = lensProfileKey();
        final String failed = streamFailureKey(key, rawFormat, previewSize);
        if (t != null) Log.w(TAG, "IRIS_26687_SPEKTRA_DISCOVERY_STREAM_REJECT reason=" + reason
                + " route=" + route + " format=" + rawFormat + " raw=" + previewSize, t);
        else Log.w(TAG, "IRIS_26687_SPEKTRA_DISCOVERY_STREAM_REJECT reason=" + reason
                + " route=" + route + " format=" + rawFormat + " raw=" + previewSize);
        lensProfiles.edit().putBoolean(failed, true)
                .remove(key + ".format").remove(key + ".width").remove(key + ".height")
                .remove(key + ".previewVerified").remove(key + ".captureVerified")
                .remove(key + ".bayerOffset").apply();
        verificationCaptureInFlight = false;
        verificationCaptureSucceeded = false;
        currentProfileNeedsVerification = false;
        activeBayerOffset = -1;
        closeCameraObjects(false);
        if (isCurrent(g)) openForPreview(g, true);
    }

    private void validateRawImageContract(@NonNull Image image, String phase, boolean logContract) {
        if (image.getPlanes() == null || image.getPlanes().length == 0) {
            throw new IllegalStateException("Spektra " + phase + " RAW has no plane");
        }
        final Image.Plane plane = image.getPlanes()[0];
        final int width = image.getWidth();
        final int height = image.getHeight();
        final int format = image.getFormat();
        final int rowStride = plane.getRowStride();
        final int pixelStride = plane.getPixelStride();
        final int bufferBytes = plane.getBuffer() == null ? 0 : plane.getBuffer().remaining();
        final int minRowBytes;
        if (format == ImageFormat.RAW10) {
            minRowBytes = ((width + 3) / 4) * 5;
        } else if (format == ImageFormat.RAW12) {
            minRowBytes = ((width + 1) / 2) * 3;
        } else if (format == ImageFormat.RAW_SENSOR) {
            minRowBytes = width * Math.max(2, pixelStride);
        } else {
            throw new IllegalStateException("Unsupported Spektra RAW format " + format);
        }
        final long minimumBuffer = height <= 0 ? 0L
                : (long) Math.max(0, height - 1) * rowStride + minRowBytes;
        final boolean packedWidthInvalid = (format == ImageFormat.RAW10 || format == ImageFormat.RAW12)
                && (width & 3) != 0;
        if (width <= 0 || height <= 0 || (width & 1) != 0 || (height & 1) != 0
                || packedWidthInvalid || rowStride < minRowBytes || bufferBytes < minimumBuffer) {
            throw new IllegalStateException("Invalid Spektra " + phase + " RAW geometry format="
                    + format + " size=" + width + "x" + height + " rowStride=" + rowStride
                    + " pixelStride=" + pixelStride + " bufferBytes=" + bufferBytes
                    + " minRowBytes=" + minRowBytes + " minimumBuffer=" + minimumBuffer);
        }
        if (logContract) {
            Log.i(TAG, "IRIS_26684_SPEKTRA_RAW_PLANE phase=" + phase
                    + " format=" + format + " size=" + width + "x" + height
                    + " rowStride=" + rowStride + " pixelStride=" + pixelStride
                    + " bufferBytes=" + bufferBytes + " minRowBytes=" + minRowBytes
                    + " route=" + route);
        }
    }

    private void armFatalWatchdog(long g, State expectedState, long timeoutMs, String reason) {
        cancelWatchdog();
        final long token = watchdogToken.incrementAndGet();
        watchdogFuture = watchdogExecutor.schedule(() -> {
            if (token != watchdogToken.get() || !isCurrent(g) || getState() != expectedState) return;
            Log.e(TAG, "IRIS_26684_SPEKTRA_WATCHDOG_FATAL reason=" + reason
                    + " state=" + getState() + " generation=" + g + " independentThread=true");
            Handler h = cameraHandler;
            if (h != null) h.post(() -> {
                if (token == watchdogToken.get() && isCurrent(g) && getState() == expectedState) {
                    fail(g, reason, null);
                }
            });
        }, timeoutMs, TimeUnit.MILLISECONDS);
    }

    private void armStillWatchdog(long g, State expectedState, long timeoutMs, String reason) {
        cancelWatchdog();
        final long token = watchdogToken.incrementAndGet();
        watchdogFuture = watchdogExecutor.schedule(() -> {
            if (token != watchdogToken.get() || !isCurrent(g) || getState() != expectedState) return;
            Log.e(TAG, "IRIS_26684_SPEKTRA_WATCHDOG_STILL reason=" + reason
                    + " state=" + getState() + " generation=" + g + " independentThread=true");
            Handler h = cameraHandler;
            if (h != null) h.post(() -> {
                if (token == watchdogToken.get() && isCurrent(g) && getState() == expectedState) {
                    terminalStillFailure(g, reason, null);
                }
            });
        }, timeoutMs, TimeUnit.MILLISECONDS);
    }

    private void cancelWatchdog() {
        watchdogToken.incrementAndGet();
        ScheduledFuture<?> future = watchdogFuture;
        watchdogFuture = null;
        if (future != null) future.cancel(false);
    }

    /** Camera transport retirement never waits on RAW/film GPU workers. */
    private void forceCloseCameraTransportForHandoff() {
        CameraCaptureSession localSession;
        CameraDevice localDevice;
        ImageReader localReader;
        SpektraPreviewRenderer localRenderer;
        synchronized (stateLock) {
            localSession = session;
            session = null;
            localDevice = cameraDevice;
            cameraDevice = null;
            localReader = previewReader;
            previewReader = null;
            localRenderer = previewRenderer;
            previewRenderer = null;
            repeatingBuilder = null;
            state = State.CLOSED;
        }
        try { if (localSession != null) localSession.close(); } catch (Throwable ignored) {}
        try { if (localDevice != null) localDevice.close(); } catch (Throwable ignored) {}
        try { if (localReader != null) localReader.close(); } catch (Throwable ignored) {}
        // A force handoff is terminal for the retired generation. Close any Camera2-owned pending
        // images/results immediately; the decode worker has already detached an accepted RAW before
        // entering native processing, so this cannot invalidate a GPU submission.
        previewResults.clear();
        closePendingPreviewImages();
        closePendingStillImages();
        pendingStillFrame = null;
        pendingStillResult = null;
        pendingStillTimestamp = 0L;
        pendingStillWallTimeMs = 0L;
        stillDecodeInFlight = false;
        if (localRenderer != null) localRenderer.release();
        previewPresented.set(false);
        cancelWatchdog();
        Log.i(TAG, "IRIS_26687_SPEKTRA_TRANSPORT_FORCE_CLOSED generation=" + activeGeneration);
    }

    private void closeCameraObjects(boolean hideSurface) {
        try { if (session != null) session.close(); } catch (Throwable ignored) {}
        session = null;
        repeatingBuilder = null;
        try { if (cameraDevice != null) cameraDevice.close(); } catch (Throwable ignored) {}
        cameraDevice = null;
        closeSessionAndReaders();
        previewResults.clear();
        closePendingPreviewImages();
        closePendingStillImages();
        pendingStillFrame = null;
        stillDecodeInFlight = false;
        pendingStillResult = null;
        pendingStillTimestamp = 0L;
        pendingStillWallTimeMs = 0L;
        pendingStillFrozenIso = 0;
        awaitingPostStillPreview = false;
        verificationCaptureInFlight = false;
        verificationCaptureSucceeded = false;
        currentProfileNeedsVerification = false;
        activeBayerOffset = -1;
        // Do not clear previewDecodeBusy here: an accepted Image may still be owned by the
        // decode executor after Camera2 retirement. That task clears the gate when it releases
        // the Image, preventing a new generation from queueing behind stale RAW work.
        loggedPreviewRawContract = false;
        loggedStillRawContract = false;
        loggedPreviewWaitWb = false;
        currentStreamRawSeen = false;
        currentStreamResultSeen = false;
        previewPresented.set(false);
        cancelWatchdog();
        characteristics = null;
        route = null;
        exposureController = null;
        if (previewRenderer != null) {
            previewRenderer.release();
            previewRenderer = null;
        }
        if (hideSurface) host.onSpektraPreviewStopped();
        setState(hideSurface ? State.CLOSED : State.IDLE);
    }

    private void closeSessionAndReaders() {
        try { if (session != null) session.close(); } catch (Throwable ignored) {}
        session = null;
        try { if (previewReader != null) previewReader.close(); } catch (Throwable ignored) {}
        previewReader = null;
    }

    private boolean isCurrent(long g) { return g == activeGeneration && g == generation.get(); }
    private void setState(State s) {
        cancelWatchdog();
        synchronized (stateLock) { state = s; }
        Log.d(TAG, "IRIS_26687_SPEKTRA_STATE state=" + s + " generation=" + activeGeneration);
    }

    private static <T> void trimSparse(LongSparseArray<T> a, int max) {
        while (a.size() > max) a.removeAt(0);
    }
}
