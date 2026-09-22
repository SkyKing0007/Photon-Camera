package com.particlesdevs.photoncamera.spektra;

import android.app.Activity;
import android.view.SurfaceView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.api.CameraEventsListener;

/**
 * The only Iris <-> Spektra control-plane boundary.
 *
 * Iris may host UI/surfaces and request enter/shutter/controls/exit. Camera2, RAW/result pairing,
 * discovery, processing executors, native GPU lifetime and Spektra capture-job state stay hidden
 * behind this facade.
 */
public final class SpektraModeController {
    public interface Host {
        void onSpektraPreviewPreparing();
        void onSpektraPreviewReady();
        void onSpektraPreviewStopped();
    }

    private final SpektraCameraOwner owner;

    public SpektraModeController(@NonNull Activity activity, @NonNull CameraEventsListener events,
            @NonNull Host host) {
        owner = new SpektraCameraOwner(activity, events, host);
    }

    public void bindPreviewSurface(@NonNull SurfaceView surfaceView) { owner.bindPreviewSurface(surfaceView); }

    public void resume(@Nullable String cameraId, int flashPreference) {
        owner.setSelectedCameraId(cameraId);
        owner.setFlashPreference(flashPreference);
        owner.resumeCamera();
    }

    public void restart(@Nullable String cameraId, int flashPreference) {
        owner.setSelectedCameraId(cameraId);
        owner.setFlashPreference(flashPreference);
        owner.restartCamera();
    }

    /** Mode handoff is fail-contained: Spektra relinquishes Camera2 even if a processor is wedged. */
    public void exitForModeHandoff() { owner.retireForHandoff(); }
    public void shutdown() { owner.shutdown(); }

    public boolean isActive() { return owner.isActive(); }
    public boolean isShutterReady() { return owner.isShutterReady(); }
    public String debugStatus() { return owner.describeStatus(); }
    public void takePicture() { owner.takePicture(); }
    public void setFlashPreference(int value) { owner.setFlashPreference(value); }
    public void setManualControls(@Nullable Integer iso, @Nullable Long exposureNs, int evSteps) {
        owner.setManualControls(iso, exposureNs, evSteps);
    }
    public void setManualFocus(@Nullable Float focusDistance) { owner.setManualFocus(focusDistance); }
    public void touchFocus(float normalizedX, float normalizedY, boolean lock) {
        owner.touchFocus(normalizedX, normalizedY, lock);
    }
    public void unlockFocus() { owner.unlockFocus(); }
}
