package com.particlesdevs.photoncamera.spektra;

import android.app.Activity;
import android.hardware.camera2.CameraAccessException;
import android.net.Uri;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.LifecycleOwner;

import com.particlesdevs.photoncamera.api.CameraEventsListener;
import com.unspektrawesome.camera.CameraCatalog;
import com.unspektrawesome.camera.CameraDescriptor;
import com.unspektrawesome.camera.LensFacing;
import com.unspektrawesome.camera.LensRole;
import com.unspektrawesome.preview.RawVulkanPreviewController;
import com.unspektrawesome.preview.VulkanRawPreviewView;
import com.unspektrawesome.settings.CameraPreferences;
import com.unspektrawesome.settings.RawPreviewQuality;
import com.unspektrawesome.spektra.InMemorySpektraStatePersistence;
import com.unspektrawesome.spektra.SpektraStateRepository;

import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Thin Iris shell adapter around the Unspektrawesome RAW/Vulkan camera subsystem.
 *
 * While active, Iris does not own Camera2, RAW preview, exposure, still capture, RCD, or SPEKTRA.
 * The original Unspektrawesome controller owns that transaction; this facade only forwards Iris
 * mode/lens/control/shutter/lifecycle requests and restores Iris ownership on exit.
 */
public final class SpektraModeController {
    public interface Host {
        void onSpektraPreviewPreparing();
        void onSpektraPreviewReady();
        void onSpektraPreviewStopped();
        void onSpektraImageSaved(@NonNull Uri uri);
    }

    private final Activity activity;
    private final CameraEventsListener events;
    private final Host host;
    private final CameraCatalog cameraCatalog;
    private final SpektraStateRepository spektraRepository;
    @Nullable
    private volatile RawVulkanPreviewController controller;
    private final CameraPreferences preferences;
    private final ExecutorService bridgeExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread thread = new Thread(r, "IrisSpektraBridge");
        thread.setDaemon(true);
        return thread;
    });
    private final AtomicInteger generation = new AtomicInteger();

    private volatile boolean active;
    private volatile boolean shutdown;
    private volatile String requestedCameraId;
    private volatile int flashPreference;
    private volatile Integer manualIso;
    private volatile Long manualExposureNs;
    private volatile int manualEvSteps;
    private volatile Float manualFocusDistance;
    private volatile CameraDescriptor selectedCamera;
    private volatile String bridgeError;
    private VulkanRawPreviewView previewView;
    private LifecycleOwner lifecycleOwner;
    @Nullable
    private volatile RawVulkanPreviewController.HistogramListener histogramListener;
    private final Object captureUiLock = new Object();
    private long captureUiRevision = Long.MIN_VALUE;
    private int captureUiGeneration = -1;
    private boolean captureUiProcessing;

    public SpektraModeController(@NonNull Activity activity, @NonNull CameraEventsListener events,
            @NonNull Host host) {
        this.activity = activity;
        this.events = events;
        this.host = host;
        this.cameraCatalog = new CameraCatalog(activity.getApplicationContext());
        this.spektraRepository = new SpektraStateRepository(
                InMemorySpektraStatePersistence.INSTANCE, 50);
        // IRIS_26690_SPEKTRA_LAZY_NATIVE_OWNER
        // Do not construct RawVulkanPreviewController/VulkanRenderer during ordinary Iris startup.
        // The exact Unspektrawesome native owner is created only when SPEKTRA becomes active.
        this.controller = null;
        // Exact 1.1.2 factory viewfinder default: LOW / 0.25 at 30 fps.
        this.preferences = new CameraPreferences(
                RawPreviewQuality.LOW,
                Collections.emptySet(),
                false,
                null,
                Collections.emptyList(),
                false,
                Collections.emptyMap());
    }

    public synchronized void bindPreviewSurface(@NonNull VulkanRawPreviewView surfaceView,
            @NonNull LifecycleOwner owner) {
        if (shutdown) return;
        if (previewView == surfaceView && lifecycleOwner == owner) return;
        if (previewView != null) previewView.unbind();
        previewView = surfaceView;
        lifecycleOwner = owner;
        // Binding the dormant Spektra SurfaceView must not load the native renderer.
        if (controller != null) previewView.bind(controller, owner);
    }

    @NonNull
    private synchronized RawVulkanPreviewController ensureControllerForActivation() {
        if (shutdown) throw new IllegalStateException("Spektra controller is shut down");
        if (controller != null) return controller;
        RawVulkanPreviewController created = new RawVulkanPreviewController(
                activity.getApplicationContext(), spektraRepository);
        created.setHistogramListener(histogramListener);
        created.setCaptureListener(new RawVulkanPreviewController.CaptureListener() {
            @Override public void onCaptureAccepted(long revisionId) {
                bridgeCaptureAccepted(created, revisionId);
            }
            @Override public void onProcessingStarted(long revisionId) {
                bridgeProcessingStarted(created, revisionId);
            }
            @Override public void onCaptureSucceeded(long revisionId, @NonNull Uri uri) {
                bridgeCaptureSucceeded(created, revisionId, uri);
            }
            @Override public void onCaptureFailed(@Nullable Long revisionId, @NonNull String message) {
                bridgeCaptureFailed(created, revisionId, message);
            }
        });
        controller = created;
        if (previewView != null && lifecycleOwner != null) {
            previewView.bind(created, lifecycleOwner);
        }
        return created;
    }

    // IRIS_26694_SPEKTRA_IRIS_CAPTURE_PRESENTATION_BRIDGE
    // Camera/RAW/RCD/save ownership remains inside RawVulkanPreviewController. These callbacks only
    // adapt the current generation to Iris's proven capture progress, processing ring and gallery.
    // A dedicated presentation lock avoids lock inversion with the RAW controller's camera lock.
    private boolean captureUiIsCurrentLocked(@NonNull RawVulkanPreviewController source, long revisionId) {
        return !shutdown && active && controller == source
                && captureUiGeneration == generation.get() && captureUiRevision == revisionId;
    }

    private void bridgeCaptureAccepted(@NonNull RawVulkanPreviewController source, long revisionId) {
        final int token;
        synchronized (captureUiLock) {
            if (shutdown || !active || controller != source) return;
            captureUiRevision = revisionId;
            captureUiGeneration = generation.get();
            captureUiProcessing = false;
            token = captureUiGeneration;
        }
        activity.runOnUiThread(() -> {
            synchronized (captureUiLock) {
                if (shutdown || !active || controller != source || generation.get() != token
                        || captureUiRevision != revisionId) return;
            }
            events.onFrameCountSet(1);
            events.onCaptureStillPictureStarted("Spektra");
        });
    }

    private void bridgeProcessingStarted(@NonNull RawVulkanPreviewController source, long revisionId) {
        final int token;
        synchronized (captureUiLock) {
            if (!captureUiIsCurrentLocked(source, revisionId) || captureUiProcessing) return;
            captureUiProcessing = true;
            token = captureUiGeneration;
        }
        activity.runOnUiThread(() -> {
            synchronized (captureUiLock) {
                if (shutdown || !active || controller != source || generation.get() != token
                        || captureUiRevision != revisionId || !captureUiProcessing) return;
            }
            events.onFrameCaptureCompleted(null);
            events.onCaptureSequenceCompleted("Spektra RAW acquired");
            events.onProcessingStarted("Spektra");
        });
    }

    private void bridgeCaptureSucceeded(@NonNull RawVulkanPreviewController source, long revisionId,
            @NonNull Uri uri) {
        final int token;
        synchronized (captureUiLock) {
            if (!captureUiIsCurrentLocked(source, revisionId)) return;
            token = captureUiGeneration;
        }
        activity.runOnUiThread(() -> {
            synchronized (captureUiLock) {
                if (shutdown || !active || controller != source || generation.get() != token
                        || captureUiRevision != revisionId) return;
                clearCaptureUiOwnershipLocked();
            }
            host.onSpektraImageSaved(uri);
            events.onProcessingFinished("Spektra");
        });
    }

    private void bridgeCaptureFailed(@NonNull RawVulkanPreviewController source, @Nullable Long revisionId,
            @NonNull String message) {
        if (revisionId == null) return;
        final int token;
        final boolean wasProcessing;
        synchronized (captureUiLock) {
            if (!captureUiIsCurrentLocked(source, revisionId)) return;
            token = captureUiGeneration;
            wasProcessing = captureUiProcessing;
        }
        activity.runOnUiThread(() -> {
            synchronized (captureUiLock) {
                if (shutdown || !active || controller != source || generation.get() != token
                        || captureUiRevision != revisionId) return;
                clearCaptureUiOwnershipLocked();
            }
            if (!wasProcessing) {
                events.onCaptureSequenceCompleted("Spektra capture failed");
            }
            events.onProcessingError(message);
        });
    }

    private void clearCaptureUiOwnershipLocked() {
        captureUiRevision = Long.MIN_VALUE;
        captureUiGeneration = -1;
        captureUiProcessing = false;
    }

    private void releaseCaptureUiBeforeHandoff() {
        final boolean hadCapture;
        final boolean wasProcessing;
        synchronized (captureUiLock) {
            hadCapture = captureUiRevision != Long.MIN_VALUE;
            wasProcessing = captureUiProcessing;
            clearCaptureUiOwnershipLocked();
        }
        if (!hadCapture) return;
        activity.runOnUiThread(() -> {
            if (!wasProcessing) {
                events.onCaptureSequenceCompleted("Spektra mode handoff");
            }
            events.onProcessingFinished("Spektra mode handoff");
        });
    }

    private void failActivation(int token, @NonNull Throwable error) {
        if (token != generation.get()) return;
        active = false;
        selectedCamera = null;
        bridgeError = error.getClass().getSimpleName() + ": "
                + (error.getMessage() == null ? "Spektra initialization failed" : error.getMessage());
        activity.runOnUiThread(host::onSpektraPreviewStopped);
    }

    public void resume(@Nullable String cameraId, int flashPreference) {
        requestedCameraId = cameraId;
        this.flashPreference = flashPreference;
        active = true;
        bridgeError = null;
        final int token = generation.incrementAndGet();
        activity.runOnUiThread(host::onSpektraPreviewPreparing);
        final RawVulkanPreviewController activeController;
        try {
            activeController = ensureControllerForActivation();
        } catch (RuntimeException | LinkageError error) {
            failActivation(token, error);
            return;
        }
        configureAsync(token, cameraId, activeController);
    }

    public void restart(@Nullable String cameraId, int flashPreference) {
        requestedCameraId = cameraId;
        this.flashPreference = flashPreference;
        active = true;
        bridgeError = null;
        final int token = generation.incrementAndGet();
        activity.runOnUiThread(host::onSpektraPreviewPreparing);
        final RawVulkanPreviewController activeController;
        try {
            activeController = ensureControllerForActivation();
            activeController.configure(null, preferences);
        } catch (RuntimeException | LinkageError error) {
            failActivation(token, error);
            return;
        }
        configureAsync(token, cameraId, activeController);
    }

    private void configureAsync(int token, @Nullable String cameraId,
            @NonNull RawVulkanPreviewController activeController) {
        bridgeExecutor.execute(() -> {
            if (shutdown || !active || token != generation.get()) return;
            try {
                List<CameraDescriptor> cameras = cameraCatalog.discover();
                CameraDescriptor selected = selectCamera(cameras, cameraId);
                if (selected == null) {
                    throw new IllegalStateException("No usable Unspektrawesome RAW camera route");
                }
                if (shutdown || !active || token != generation.get()) return;
                selectedCamera = selected;
                activeController.setManualControls(manualIso, manualExposureNs, manualEvSteps);
                activeController.setManualFocus(manualFocusDistance);
                activeController.configure(selected, preferences);
            } catch (CameraAccessException | RuntimeException error) {
                if (token != generation.get()) return;
                bridgeError = error.getClass().getSimpleName() + ": "
                        + (error.getMessage() == null ? "camera configuration failed" : error.getMessage());
                selectedCamera = null;
                activeController.configure(null, preferences);
            }
        });
    }

    @Nullable
    private static CameraDescriptor selectCamera(@NonNull List<CameraDescriptor> cameras,
            @Nullable String requestedId) {
        if (requestedId != null && !requestedId.trim().isEmpty()) {
            for (CameraDescriptor camera : cameras) {
                if (!camera.isUsable()) continue;
                if (requestedId.equals(camera.route.routeId)
                        || requestedId.equals(camera.route.physicalCameraId)
                        || requestedId.equals(camera.route.characteristicsCameraId)) {
                    return camera;
                }
            }
            for (CameraDescriptor camera : cameras) {
                if (camera.isUsable() && requestedId.equals(camera.route.openCameraId)) return camera;
            }
        }
        for (CameraDescriptor camera : cameras) {
            if (camera.isUsable() && camera.facing == LensFacing.BACK
                    && camera.lensRole == LensRole.MAIN) return camera;
        }
        for (CameraDescriptor camera : cameras) {
            if (camera.isUsable() && camera.facing == LensFacing.BACK) return camera;
        }
        for (CameraDescriptor camera : cameras) {
            if (camera.isUsable()) return camera;
        }
        return null;
    }

    /** Fail-contained mode handoff: stop Unspektrawesome Camera2 before Iris may reopen Camera2. */
    public void exitForModeHandoff() {
        releaseCaptureUiBeforeHandoff();
        active = false;
        generation.incrementAndGet();
        selectedCamera = null;
        RawVulkanPreviewController current = controller;
        if (current != null) current.configure(null, preferences);
        activity.runOnUiThread(host::onSpektraPreviewStopped);
    }

    public synchronized void shutdown() {
        if (shutdown) return;
        shutdown = true;
        releaseCaptureUiBeforeHandoff();
        active = false;
        generation.incrementAndGet();
        selectedCamera = null;
        if (previewView != null) previewView.unbind();
        previewView = null;
        lifecycleOwner = null;
        histogramListener = null;
        if (controller != null) {
            controller.setHistogramListener(null);
            controller.setCaptureListener(null);
            controller.close();
            controller = null;
        }
        bridgeExecutor.shutdownNow();
        activity.runOnUiThread(host::onSpektraPreviewStopped);
    }

    public boolean isActive() { return active && !shutdown; }

    public boolean isShutterReady() {
        RawVulkanPreviewController current = controller;
        return isActive() && current != null && current.isCaptureReady();
    }

    public String debugStatus() {
        String selected = selectedCamera == null ? "none" : selectedCamera.route.routeId;
        String error = bridgeError == null ? "none" : bridgeError;
        RawVulkanPreviewController current = controller;
        String controllerStatus = current == null ? "not_initialized" : current.debugStatus();
        return "active=" + active + " shutdown=" + shutdown + " requested=" + requestedCameraId
                + " selected=" + selected + " flashPref=" + flashPreference
                + " error=" + error + " controller={" + controllerStatus + "}";
    }

    public boolean takePicture() {
        RawVulkanPreviewController current = controller;
        return isActive() && current != null && current.captureStill();
    }

    /**
     * IRIS_26693_SPEKTRA_HISTOGRAM_PRESENTATION_BRIDGE
     * Iris registers only a presentation sink. The Unspektrawesome preview controller owns when
     * native histogram acquisition runs and automatically follows preview/session lifecycle.
     */
    public synchronized void setHistogramListener(
            @Nullable RawVulkanPreviewController.HistogramListener listener) {
        histogramListener = listener;
        RawVulkanPreviewController current = controller;
        if (current != null) current.setHistogramListener(listener);
    }

    public void setFlashPreference(int value) {
        // Standalone Unspektrawesome 1.1.2 owns manual sensor exposure; keep Iris flash preference
        // only as shell state so it cannot alter the Spektra Camera2 request behind the controller.
        flashPreference = value;
    }

    public void setManualControls(@Nullable Integer iso, @Nullable Long exposureNs, int evSteps) {
        manualIso = iso;
        manualExposureNs = exposureNs;
        manualEvSteps = evSteps;
        RawVulkanPreviewController current = controller;
        if (current != null) current.setManualControls(iso, exposureNs, evSteps);
    }

    public void setManualFocus(@Nullable Float focusDistance) {
        manualFocusDistance = focusDistance;
        RawVulkanPreviewController current = controller;
        if (current != null) current.setManualFocus(focusDistance);
    }

    public void touchFocus(float normalizedX, float normalizedY, boolean lock) {
        RawVulkanPreviewController current = controller;
        if (current != null) current.touchFocus(normalizedX, normalizedY, lock);
    }

    public void unlockFocus() {
        RawVulkanPreviewController current = controller;
        if (current != null) current.unlockFocus();
    }
}
