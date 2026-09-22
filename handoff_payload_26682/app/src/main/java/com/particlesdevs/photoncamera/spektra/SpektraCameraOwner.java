package com.particlesdevs.photoncamera.spektra;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
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
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.util.Log;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Independent Camera2 owner for CameraMode.SPEKTRA.
 *
 * No Motion/Night capture, ZSL, IsoExpoSelector, Parameters, per-lens IQ profile, Sabre/Wronski,
 * UHDR or HEIC object is referenced from this class. Device truth comes only from Camera2.
 */
public final class SpektraCameraOwner {
    private static final String TAG = "SpektraCameraOwner";
    private static final int TARGET_PREVIEW_FPS = 30;
    private static final int PREVIEW_SHORT_EDGE_DEFAULT = 480;
    private static final double PREVIEW_QUALITY_SCALAR = 0.25;

    public enum State {
        IDLE, OPENING, CONFIGURING, STREAMING,
        STILL_CONFIGURING, STILL_CAPTURING, PROCESSING,
        PREVIEW_RECONFIGURING, FAILED, CLOSED
    }

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
    private final ExecutorService processExecutor;
    private final CameraEventsListener events;
    private final AtomicLong generation = new AtomicLong(0L);
    private final Object stateLock = new Object();

    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private Executor cameraExecutor;
    private SurfaceView previewSurfaceView;
    private CameraDevice cameraDevice;
    private CameraCaptureSession session;
    private ImageReader previewReader;
    private ImageReader stillReader;
    private CaptureRequest.Builder repeatingBuilder;
    private CameraCharacteristics characteristics;
    private Route route;
    private SpektraExposureController exposureController;
    private SpektraPreviewRenderer previewRenderer;
    private State state = State.IDLE;
    private int rawFormat = ImageFormat.RAW_SENSOR;
    private Size previewSize;
    private Size stillSize;
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
    private final LongSparseArray<SpektraRawFrame> previewFrames = new LongSparseArray<>();
    private SpektraRawFrame pendingStillFrame;
    private TotalCaptureResult pendingStillResult;
    private long pendingStillTimestamp = 0L;
    private long pendingStillWallTimeMs = 0L;

    public SpektraCameraOwner(Activity activity, ExecutorService processExecutor, CameraEventsListener events) {
        this.activity = activity;
        this.processExecutor = processExecutor;
        this.events = events;
        this.cameraManager = (CameraManager) activity.getSystemService(Context.CAMERA_SERVICE);
    }

    public void bindPreviewSurface(@NonNull SurfaceView surfaceView) {
        previewSurfaceView = surfaceView;
        previewSurfaceView.setZOrderOnTop(false);
        previewSurfaceView.setVisibility(android.view.View.GONE);
    }

    public void setSelectedCameraId(@Nullable String cameraId) {
        selectedCameraId = cameraId == null ? "" : cameraId;
    }

    public State getState() { synchronized (stateLock) { return state; } }
    public boolean isActive() {
        State s = getState();
        return s != State.IDLE && s != State.CLOSED && s != State.FAILED;
    }

    public boolean isStreaming() { return getState() == State.STREAMING; }

    @SuppressLint("MissingPermission")
    public void resumeCamera() {
        final long g = generation.incrementAndGet();
        activeGeneration = g;
        ensureThread();
        cameraHandler.post(() -> openForPreview(g, false));
    }

    @SuppressLint("MissingPermission")
    public void restartCamera() {
        final long g = generation.incrementAndGet();
        activeGeneration = g;
        ensureThread();
        cameraHandler.post(() -> {
            closeCameraObjects(false);
            events.onCameraRestarted();
            openForPreview(g, true);
        });
    }

    public void closeCamera() {
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
            if (!completed) Log.e(TAG, "IRIS_26681_SPEKTRA_HANDOFF_TIMEOUT generation=" + retired);
            return completed;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            Log.e(TAG, "IRIS_26681_SPEKTRA_HANDOFF_INTERRUPTED", e);
            return false;
        }
    }

    public void shutdown() {
        retireForHandoff();
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
            if (state != State.STREAMING || cameraDevice == null || session == null || characteristics == null) {
                rejectShutter("SPEKTRA_SESSION_NOT_STREAMING");
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
            setState(State.OPENING);
            String requested = selectedCameraId;
            route = resolveRoute(requested);
            characteristics = cameraManager.getCameraCharacteristics(route.characteristicsId);
            requireRawManualCapability(characteristics);
            discoverRawStreams(characteristics);
            exposureController = new SpektraExposureController(characteristics);
            exposureController.reset(System.nanoTime());
            applyStoredManualControls();
            requestedIso = exposureController.getCurrentIso();
            requestedExposureNs = exposureController.getCurrentExposureNs();
            if (previewRenderer == null) previewRenderer = new SpektraPreviewRenderer(activity, previewSurfaceView);
            previewRenderer.configure(characteristics, previewSize, rawFormat);
            events.onCharacteristicsUpdated(characteristics);
            events.onOpenCamera(cameraManager);
            setPreviewVisibility(true);
            Log.i(TAG, "IRIS_26681_SPEKTRA_OPEN " + route + " rawFormat=" + rawFormat
                    + " preview=" + previewSize + " still=" + stillSize + " generation=" + g);
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
            fail(g, "OPEN_FAILED", t);
        }
    }

    private void requireRawManualCapability(CameraCharacteristics c) {
        int[] caps = c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        boolean raw = false, manual = false;
        if (caps != null) {
            for (int cap : caps) {
                raw |= cap == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW;
                manual |= cap == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR;
            }
        }
        if (!raw) throw new IllegalStateException("Spektra requires Camera2 RAW capability");
        if (!manual) throw new IllegalStateException("Spektra requires Camera2 MANUAL_SENSOR for Unspektra AE");
    }

    private Route resolveRoute(String requestedValue) throws CameraAccessException {
        final String requested = requestedValue == null ? "" : requestedValue.trim();
        if (requested.isEmpty()) throw new IllegalArgumentException("Spektra camera ID is empty");

        String logicalHint = requested;
        String physicalHint = requested;
        final boolean explicitLogicalPhysical = requested.contains("-");
        if (explicitLogicalPhysical) {
            String[] split = requested.split("-", 2);
            logicalHint = split[0];
            physicalHint = split[1];
        }

        final List<String> listed = Arrays.asList(cameraManager.getCameraIdList());

        // A directly openable public ID is authoritative whether it represents a logical camera
        // or a directly listed physical camera. Do not translate it to an unrelated fallback ID.
        if (listed.contains(physicalHint)) {
            return new Route(requested, physicalHint, physicalHint, null);
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            // Preserve an explicit logical-physical route when the selected physical lens is a
            // child of the hinted logical camera.
            if (explicitLogicalPhysical && listed.contains(logicalHint)) {
                CameraCharacteristics logicalChars = cameraManager.getCameraCharacteristics(logicalHint);
                if (logicalChars.getPhysicalCameraIds().contains(physicalHint)) {
                    return new Route(requested, logicalHint, physicalHint, physicalHint);
                }
            }

            // A plain physical ID may not itself appear in getCameraIdList(). Search every public
            // logical camera for that physical child and route the OutputConfiguration explicitly.
            for (String candidateLogical : listed) {
                CameraCharacteristics logicalChars = cameraManager.getCameraCharacteristics(candidateLogical);
                if (logicalChars.getPhysicalCameraIds().contains(physicalHint)) {
                    return new Route(requested, candidateLogical, physicalHint, physicalHint);
                }
            }
        }

        // A plain logical ID that was not found above is not a valid public Camera2 ID. Failing
        // closed is safer than silently opening camera 0 with the wrong CFA/calibration/LSC data.
        throw new IllegalArgumentException("Unable to resolve Spektra Camera2 route for " + requested
                + " publicIds=" + listed);
    }

    private void discoverRawStreams(CameraCharacteristics c) {
        StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        if (map == null) throw new IllegalStateException("Camera has no stream configuration map");
        int[] formats = new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR, ImageFormat.RAW12};
        Size[] selected = null;
        int selectedFormat = 0;
        for (int format : formats) {
            Size[] sizes = map.getOutputSizes(format);
            if (sizes != null && sizes.length > 0) { selected = sizes; selectedFormat = format; break; }
        }
        if (selected == null) throw new IllegalStateException("No RAW10/RAW_SENSOR/RAW12 output");
        List<Size> sizes = new ArrayList<>(Arrays.asList(selected));
        sizes.sort(Comparator.comparingLong(SpektraCameraOwner::area));
        stillSize = sizes.get(sizes.size() - 1);
        int targetShort = Math.max(PREVIEW_SHORT_EDGE_DEFAULT,
                (int)Math.round(Math.min(stillSize.getWidth(), stillSize.getHeight()) * PREVIEW_QUALITY_SCALAR));
        Size best = null;
        for (Size s : sizes) {
            int sh = Math.min(s.getWidth(), s.getHeight());
            if (sh >= targetShort) { best = s; break; }
        }
        previewSize = best != null ? best : sizes.get(0);
        rawFormat = selectedFormat;
    }

    private static long area(Size s) { return (long)s.getWidth() * s.getHeight(); }

    private void configurePreviewSession(long g) {
        if (!isCurrent(g) || cameraDevice == null) return;
        setState(State.CONFIGURING);
        closeSessionAndReaders();
        previewReader = ImageReader.newInstance(previewSize.getWidth(), previewSize.getHeight(), rawFormat, 4);
        previewReader.setOnImageAvailableListener(reader -> onPreviewRaw(reader, g), cameraHandler);
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
            createSession(Collections.singletonList(rawSurface), g, new CameraCaptureSession.StateCallback() {
                @Override public void onConfigured(@NonNull CameraCaptureSession s) {
                    if (!isCurrent(g) || cameraDevice == null) { s.close(); return; }
                    session = s;
                    submitRepeating();
                    setState(State.STREAMING);
                    if (focusLocked && touchMeterActive && manualFocusDistance == null) {
                        applyTouchFocus(touchMeterX, touchMeterY, true);
                    }
                    Log.i(TAG, "IRIS_26681_SPEKTRA_STREAMING generation=" + g
                            + " raw=" + previewSize + " format=" + rawFormat);
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

    private void onPreviewRaw(ImageReader reader, long g) {
        if (!isCurrent(g) || state != State.STREAMING) {
            Image stale = reader.acquireLatestImage(); if (stale != null) stale.close(); return;
        }
        Image image = reader.acquireLatestImage();
        if (image == null) return;
        try {
            SpektraRawFrame frame = SpektraRawFrame.copyFrom(image);
            TotalCaptureResult result = previewResults.get(frame.timestampNs);
            if (result != null) {
                previewResults.remove(frame.timestampNs);
                consumePreviewPair(frame, result, g);
            } else {
                previewFrames.put(frame.timestampNs, frame);
                trimSparse(previewFrames, 8);
            }
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26681_SPEKTRA_PREVIEW_RAW_FAILED", t);
        } finally {
            image.close();
        }
    }

    private final CameraCaptureSession.CaptureCallback repeatingCallback = new CameraCaptureSession.CaptureCallback() {
        @Override public void onCaptureCompleted(@NonNull CameraCaptureSession s,
                @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
            if (s != session || state != State.STREAMING) return;
            Long ts = result.get(TotalCaptureResult.SENSOR_TIMESTAMP);
            if (ts == null) return;
            SpektraRawFrame frame = previewFrames.get(ts);
            if (frame != null) {
                previewFrames.remove(ts);
                consumePreviewPair(frame, result, activeGeneration);
            } else {
                previewResults.put(ts, result);
                trimSparse(previewResults, 8);
            }
        }
    };

    private void consumePreviewPair(SpektraRawFrame frame, TotalCaptureResult result, long g) {
        if (!isCurrent(g) || state != State.STREAMING || characteristics == null) return;
        SpektraFrameMetadata metadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), requestedIso);
        if (metadata.neutral3 == null) {
            Log.w(TAG, "IRIS_26681_SPEKTRA_PREVIEW_WAIT_WB timestamp=" + frame.timestampNs);
            return;
        }
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
        previewRenderer.render(frame, metadata, result);
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
        if (!isCurrent(g) || cameraDevice == null) return;
        try {
            if (session != null) { try { session.stopRepeating(); } catch (Throwable ignored) {} session.close(); session = null; }
            if (previewReader != null) { previewReader.close(); previewReader = null; }
            stillReader = ImageReader.newInstance(stillSize.getWidth(), stillSize.getHeight(), rawFormat, 2);
            stillReader.setOnImageAvailableListener(reader -> onStillRaw(reader, g), cameraHandler);
            Surface rawSurface = stillReader.getSurface();
            createSession(Collections.singletonList(rawSurface), g, new CameraCaptureSession.StateCallback() {
                @Override public void onConfigured(@NonNull CameraCaptureSession s) {
                    if (!isCurrent(g) || cameraDevice == null) { s.close(); return; }
                    session = s;
                    submitStill(g, rawSurface);
                }
                @Override public void onConfigureFailed(@NonNull CameraCaptureSession s) {
                    if (isCurrent(g)) terminalStillFailure(g, "STILL_SESSION_CONFIGURE_FAILED", null);
                }
            });
        } catch (Throwable t) {
            terminalStillFailure(g, "STILL_SESSION_CREATE_FAILED", t);
        }
    }

    private void submitStill(long g, Surface target) {
        if (!isCurrent(g) || cameraDevice == null || session == null) return;
        try {
            setState(State.STILL_CAPTURING);
            pendingStillFrame = null;
            pendingStillResult = null;
            pendingStillTimestamp = 0L;
            pendingStillWallTimeMs = System.currentTimeMillis();
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
            b.setTag("IRIS_26681_SPEKTRA_" + g);
            session.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureStarted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, long timestamp, long frameNumber) {
                    if (isCurrent(g)) {
                        pendingStillWallTimeMs = System.currentTimeMillis();
                        events.onFrameCaptureStarted("SPEKTRA");
                    }
                }
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession s,
                        @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    if (!isCurrent(g)) return;
                    Long ts = result.get(TotalCaptureResult.SENSOR_TIMESTAMP);
                    if (ts == null) { terminalStillFailure(g, "STILL_RESULT_NO_TIMESTAMP", null); return; }
                    pendingStillTimestamp = ts;
                    pendingStillResult = result;
                    tryCompleteStill(g, frozenIso);
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession s,
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

    private void onStillRaw(ImageReader reader, long g) {
        Image image = reader.acquireNextImage();
        if (image == null) return;
        try {
            SpektraRawFrame frame = SpektraRawFrame.copyFrom(image);
            if (!isCurrent(g)) return;
            pendingStillFrame = frame;
            if (pendingStillTimestamp == 0L) pendingStillTimestamp = frame.timestampNs;
            tryCompleteStill(g, requestedIso);
        } catch (Throwable t) {
            terminalStillFailure(g, "STILL_RAW_COPY_FAILED", t);
        } finally {
            image.close();
        }
    }

    private void tryCompleteStill(long g, int frozenRequestedIso) {
        if (!isCurrent(g) || pendingStillFrame == null || pendingStillResult == null) return;
        Long resultTs = pendingStillResult.get(TotalCaptureResult.SENSOR_TIMESTAMP);
        if (resultTs == null || pendingStillFrame.timestampNs != resultTs) {
            terminalStillFailure(g, "RAW_RESULT_TIMESTAMP_MISMATCH raw=" + pendingStillFrame.timestampNs
                    + " result=" + resultTs, null);
            return;
        }
        final SpektraRawFrame raw = pendingStillFrame;
        final TotalCaptureResult result = pendingStillResult;
        pendingStillFrame = null;
        pendingStillResult = null;
        SpektraFrameMetadata metadata = SpektraFrameMetadata.from(result, characteristics,
                result.getFrameNumber(), frozenRequestedIso);
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
        setState(State.PROCESSING);
        CaptureController.isProcessing = true;
        events.onFrameCaptureCompleted("SPEKTRA");
        events.onCaptureSequenceCompleted("SPEKTRA");
        events.onProcessingStarted("Spektra");
        final int outputRotation = outputRotationDegrees();
        final String lensModel = metadata.focalLengthMm > 0f
                ? (route == null ? "" : route.characteristicsId) + " " + metadata.focalLengthMm + "mm"
                : (route == null ? "" : route.characteristicsId);
        final long captureWallTimeMs = pendingStillWallTimeMs > 0L
                ? pendingStillWallTimeMs : System.currentTimeMillis();
        final SpektraShot shot = new SpektraShot(raw, metadata, captureWallTimeMs,
                color.sensorToLinearSrgb, outputRotation,
                route == null ? "" : route.characteristicsId, lensModel);
        processExecutor.execute(() -> processShot(g, shot));
    }

    private static int valueOrZero(Integer value) { return value == null ? 0 : value; }
    private static int valueOrZero(Byte value) { return value == null ? 0 : Byte.toUnsignedInt(value); }

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
            CaptureController.isProcessing = false;
            Handler h = cameraHandler;
            if (h != null) h.post(() -> restorePreviewAfterStill(g));
        }
    }

    private void restorePreviewAfterStill(long g) {
        if (!isCurrent(g) || cameraDevice == null) return;
        setState(State.PREVIEW_RECONFIGURING);
        if (session != null) { session.close(); session = null; }
        if (stillReader != null) { stillReader.close(); stillReader = null; }
        configurePreviewSession(g);
    }

    private void terminalStillFailure(long g, String reason, Throwable t) {
        if (t != null) Log.e(TAG, "IRIS_26681_SPEKTRA_STILL_FAILURE reason=" + reason, t);
        else Log.e(TAG, "IRIS_26681_SPEKTRA_STILL_FAILURE reason=" + reason);
        CaptureController.isProcessing = false;
        activity.runOnUiThread(() -> {
            events.onCaptureStillPictureRejected(reason);
            events.onProcessingError(reason);
        });
        restorePreviewAfterStill(g);
    }

    private void fail(long g, String reason, Throwable t) {
        if (!isCurrent(g)) return;
        if (t != null) Log.e(TAG, "IRIS_26681_SPEKTRA_FATAL reason=" + reason, t);
        else Log.e(TAG, "IRIS_26681_SPEKTRA_FATAL reason=" + reason);
        closeCameraObjects(false);
        setState(State.FAILED);
        activity.runOnUiThread(() -> events.onError(reason));
    }

    private void closeCameraObjects(boolean hideSurface) {
        try { if (session != null) session.close(); } catch (Throwable ignored) {}
        session = null;
        repeatingBuilder = null;
        try { if (cameraDevice != null) cameraDevice.close(); } catch (Throwable ignored) {}
        cameraDevice = null;
        closeSessionAndReaders();
        previewResults.clear();
        previewFrames.clear();
        pendingStillFrame = null;
        pendingStillResult = null;
        pendingStillTimestamp = 0L;
        pendingStillWallTimeMs = 0L;
        characteristics = null;
        route = null;
        exposureController = null;
        if (previewRenderer != null) {
            previewRenderer.release();
            previewRenderer = null;
        }
        if (hideSurface) {
            SpektraFilmRenderer.releaseProcessRenderer();
            setPreviewVisibility(false);
        }
        setState(hideSurface ? State.CLOSED : State.IDLE);
    }

    private void closeSessionAndReaders() {
        try { if (session != null) session.close(); } catch (Throwable ignored) {}
        session = null;
        try { if (previewReader != null) previewReader.close(); } catch (Throwable ignored) {}
        previewReader = null;
        try { if (stillReader != null) stillReader.close(); } catch (Throwable ignored) {}
        stillReader = null;
    }

    private void setPreviewVisibility(boolean visible) {
        SurfaceView sv = previewSurfaceView;
        if (sv == null) return;
        activity.runOnUiThread(() -> sv.setVisibility(visible ? android.view.View.VISIBLE : android.view.View.GONE));
    }

    private boolean isCurrent(long g) { return g == activeGeneration && g == generation.get(); }
    private void setState(State s) { synchronized (stateLock) { state = s; } }

    private static <T> void trimSparse(LongSparseArray<T> a, int max) {
        while (a.size() > max) a.removeAt(0);
    }
}
