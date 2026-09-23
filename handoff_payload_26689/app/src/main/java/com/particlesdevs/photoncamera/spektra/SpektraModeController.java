package com.particlesdevs.photoncamera.spektra;

import android.app.Activity;
import android.hardware.camera2.CameraAccessException;

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
    }

    private final Activity activity;
    @SuppressWarnings("unused")
    private final CameraEventsListener events;
    private final Host host;
    private final CameraCatalog cameraCatalog;
    private final SpektraStateRepository spektraRepository;
    private final RawVulkanPreviewController controller;
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

    public SpektraModeController(@NonNull Activity activity, @NonNull CameraEventsListener events,
            @NonNull Host host) {
        this.activity = activity;
        this.events = events;
        this.host = host;
        this.cameraCatalog = new CameraCatalog(activity.getApplicationContext());
        this.spektraRepository = new SpektraStateRepository(
                InMemorySpektraStatePersistence.INSTANCE, 50);
        this.controller = new RawVulkanPreviewController(
                activity.getApplicationContext(), spektraRepository);
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
        previewView.bind(controller, owner);
    }

    public void resume(@Nullable String cameraId, int flashPreference) {
        requestedCameraId = cameraId;
        this.flashPreference = flashPreference;
        active = true;
        bridgeError = null;
        final int token = generation.incrementAndGet();
        activity.runOnUiThread(host::onSpektraPreviewPreparing);
        configureAsync(token, cameraId);
    }

    public void restart(@Nullable String cameraId, int flashPreference) {
        requestedCameraId = cameraId;
        this.flashPreference = flashPreference;
        active = true;
        bridgeError = null;
        final int token = generation.incrementAndGet();
        activity.runOnUiThread(host::onSpektraPreviewPreparing);
        controller.configure(null, preferences);
        configureAsync(token, cameraId);
    }

    private void configureAsync(int token, @Nullable String cameraId) {
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
                controller.setManualControls(manualIso, manualExposureNs, manualEvSteps);
                controller.setManualFocus(manualFocusDistance);
                controller.configure(selected, preferences);
            } catch (CameraAccessException | RuntimeException error) {
                if (token != generation.get()) return;
                bridgeError = error.getClass().getSimpleName() + ": "
                        + (error.getMessage() == null ? "camera configuration failed" : error.getMessage());
                selectedCamera = null;
                controller.configure(null, preferences);
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
        active = false;
        generation.incrementAndGet();
        selectedCamera = null;
        controller.configure(null, preferences);
        activity.runOnUiThread(host::onSpektraPreviewStopped);
    }

    public synchronized void shutdown() {
        if (shutdown) return;
        shutdown = true;
        active = false;
        generation.incrementAndGet();
        selectedCamera = null;
        if (previewView != null) previewView.unbind();
        previewView = null;
        lifecycleOwner = null;
        controller.close();
        bridgeExecutor.shutdownNow();
        activity.runOnUiThread(host::onSpektraPreviewStopped);
    }

    public boolean isActive() { return active && !shutdown; }
    public boolean isShutterReady() { return isActive() && controller.isCaptureReady(); }

    public String debugStatus() {
        String selected = selectedCamera == null ? "none" : selectedCamera.route.routeId;
        String error = bridgeError == null ? "none" : bridgeError;
        return "active=" + active + " shutdown=" + shutdown + " requested=" + requestedCameraId
                + " selected=" + selected + " flashPref=" + flashPreference
                + " error=" + error + " controller={" + controller.debugStatus() + "}";
    }

    public void takePicture() {
        if (!isActive()) return;
        controller.captureStill();
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
        controller.setManualControls(iso, exposureNs, evSteps);
    }

    public void setManualFocus(@Nullable Float focusDistance) {
        manualFocusDistance = focusDistance;
        controller.setManualFocus(focusDistance);
    }

    public void touchFocus(float normalizedX, float normalizedY, boolean lock) {
        controller.touchFocus(normalizedX, normalizedY, lock);
    }

    public void unlockFocus() { controller.unlockFocus(); }
}
