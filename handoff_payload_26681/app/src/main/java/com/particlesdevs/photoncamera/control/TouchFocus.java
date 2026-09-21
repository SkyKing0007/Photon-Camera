package com.particlesdevs.photoncamera.control;

import android.graphics.Point;
import android.graphics.Rect;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.MeteringRectangle;
import com.particlesdevs.photoncamera.util.Log;
import android.util.Size;
import android.view.View;
import android.view.View.OnTouchListener;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.ui.camera.views.FocusCircleView;
import com.particlesdevs.photoncamera.ui.camera.views.viewfinder.GLPreview;

public class TouchFocus {
    private static final String TAG = "TouchFocus";
    private static final int AUTO_HIDE_DELAY_MS = 3000;
    private final CaptureController captureController;
    private final GLPreview textureView;
    private final View focusCircleView;
    private final Runnable hideFocusCircleRunnable = this::hideFocusCircleView;
    public boolean isTouchFocus = false;
    /* IRIS_26523_REAL_AF_LOCK_STATE */
    private volatile boolean focusLocked = false;
    private MeteringRectangle[] activeTouchRegion = null;
    /* IRIS_26679_SESSION_SAFE_TOUCH_FOCUS_RESET
     * Session teardown/reconfigure can overlap the delayed 3 s autofocus reset. Keep one pending
     * reset intent and replay it only after CaptureController proves a usable preview session. */
    private volatile boolean iris26679PendingAutoFocusReset = false;


    public TouchFocus(CaptureController captureController, View focusCircle, GLPreview textureView) {
        this.captureController = captureController;
        this.focusCircleView = focusCircle;
        this.textureView = textureView;
        // The focus ring is visual-only. It must not consume the second touch/hold
        // used to lock focus at the same point.
        focusCircleView.setOnTouchListener(null);
        focusCircleView.setClickable(false);
        resetFocusCircle();
    }

    public boolean isFocusLocked() {
        return focusLocked;
    }

    public void processTouchToFocus(float fx, float fy) {
        if (focusLocked) {
            unlockFocus();
            return;
        }
        focusCircleView.removeCallbacks(hideFocusCircleRunnable);
        focusCircleView.post(() -> showFocusCircle(fx, fy));
        applyFocus(fx, fy, false);
        focusCircleView.postDelayed(hideFocusCircleRunnable, AUTO_HIDE_DELAY_MS);
    }

    public void processLongPressToLock(float fx, float fy) {
        focusCircleView.removeCallbacks(hideFocusCircleRunnable);
        focusCircleView.post(() -> showFocusCircle(fx, fy));
        applyFocus(fx, fy, true);
    }

    public void unlockFocus() {
        focusCircleView.removeCallbacks(hideFocusCircleRunnable);
        resetAutoFocus();
        focusCircleView.post(hideFocusCircleRunnable);
    }

    /** Re-establish the repeating preview request after a capture without cancelling user AF lock. */
    public void resumeLockedFocusAfterCapture() {
        if (captureController.isSpektraModeActive()) return; // Spektra owner restores its lock after session rebuild.
        if (!focusLocked || CaptureController.burst
                || !captureController.iris26679PreviewSessionReadyForControl()) return;
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null || activeTouchRegion == null) return;
        builder.set(CaptureRequest.CONTROL_AF_REGIONS, activeTouchRegion);
        builder.set(CaptureRequest.CONTROL_AF_MODE, PreferenceKeys.getAfMode());
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        captureController.rebuildPreviewBuilder();
        isTouchFocus = true;
    }

    /** Replay exactly one delayed reset after a newly configured preview session is usable. */
    public void onPreviewSessionReady() {
        if (CaptureController.burst) return;
        if (iris26679PendingAutoFocusReset) {
            Log.d(TAG, "IRIS_26679_TOUCH_AF_PENDING_RESET_REPLAY");
            resetAutoFocus();
            return;
        }
        if (focusLocked && activeTouchRegion != null) {
            Log.d(TAG, "IRIS_26679_TOUCH_AF_LOCK_REPLAY");
            resumeLockedFocusAfterCapture();
        }
    }

    private void showFocusCircle(float fx, float fy) {
        focusCircleView.setX(textureView.getX() + fx - focusCircleView.getMeasuredWidth() / 2.0f);
        focusCircleView.setY(textureView.getY() + fy - focusCircleView.getMeasuredHeight() / 2.0f);
        focusCircleView.setAlpha(1f);
        focusCircleView.setVisibility(View.VISIBLE);
        focusCircleView.animate().scaleY(1.2f).scaleX(1.2f).setDuration(250)
                .withEndAction(() -> focusCircleView.animate().scaleY(1f).scaleX(1f).setDuration(250).start())
                .start();
    }

    /**
     * Sets state of focus circle view based on AF State
     */
    public void setState(@Nullable Integer afstate) {
        if (afstate != null) {
            ((FocusCircleView) focusCircleView).setAfState(afstate);
        }
    }

    /* IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING */
    private void applyFocus(float previewX, float previewY, boolean lockRequested) {
        if (captureController.isSpektraModeActive()) {
            int width = textureView.getWidth();
            int height = textureView.getHeight();
            if (width <= 0 || height <= 0) return;
            float nx = Math.max(0f, Math.min(1f, previewX / (float) width));
            float ny = Math.max(0f, Math.min(1f, previewY / (float) height));
            captureController.getSpektraCameraOwner().touchFocus(nx, ny, lockRequested);
            isTouchFocus = true;
            focusLocked = lockRequested;
            Log.d(TAG, "IRIS_26681_SPEKTRA_TOUCH_FOCUS normalized=" + nx + "," + ny
                    + " lock=" + lockRequested);
            return;
        }
        MeteringRectangle[] region = buildMeteringRegion(previewX, previewY);
        if (region == null) return;
        activeTouchRegion = region;
        triggerAutoFocus(region, lockRequested);
    }

    private MeteringRectangle[] buildMeteringRegion(float previewX, float previewY) {
        if (captureController.mImageReaderPreview == null || CaptureController.mCameraCharacteristics == null) {
            Log.w(TAG, "buildMeteringRegion(): camera not ready");
            return null;
        }
        int previewWidth = textureView.getWidth();
        int previewHeight = textureView.getHeight();
        if (previewWidth <= 0 || previewHeight <= 0) return null;

        CameraCharacteristics characteristics = CaptureController.mCameraCharacteristics;
        Rect coordinateArray = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        Integer distortion = builder != null
                ? builder.get(CaptureRequest.DISTORTION_CORRECTION_MODE) : null;
        if (distortion != null && distortion == CaptureRequest.DISTORTION_CORRECTION_MODE_OFF) {
            Rect pre = characteristics.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE);
            if (pre != null) coordinateArray = pre;
        }
        if (coordinateArray == null) {
            Size fallback = characteristics.get(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE);
            if (fallback == null) return null;
            coordinateArray = new Rect(0, 0, fallback.getWidth(), fallback.getHeight());
        }

        Rect crop = CaptureController.mPreviewCaptureResult != null
                ? CaptureController.mPreviewCaptureResult.get(CaptureResult.SCALER_CROP_REGION)
                : null;
        if (crop == null && builder != null) crop = builder.get(CaptureRequest.SCALER_CROP_REGION);
        crop = crop == null ? new Rect(coordinateArray) : new Rect(crop);
        if (!crop.intersect(coordinateArray)) crop.set(coordinateArray);

        // Camera2 applies an additional center crop when the output stream aspect ratio differs
        // from the active/crop region. Reproduce that visible field of view before mapping taps.
        int orientation = ((captureController.mSensorOrientation % 360) + 360) % 360;
        boolean quarterTurn = orientation == 90 || orientation == 270;
        float targetSensorAspect = quarterTurn
                ? (float) previewHeight / (float) previewWidth
                : (float) previewWidth / (float) previewHeight;
        float cropAspect = (float) crop.width() / (float) crop.height();
        if (cropAspect > targetSensorAspect) {
            int targetWidth = Math.max(1, Math.round(crop.height() * targetSensorAspect));
            int dx = (crop.width() - targetWidth) / 2;
            crop.left += dx;
            crop.right = crop.left + targetWidth;
        } else if (cropAspect < targetSensorAspect) {
            int targetHeight = Math.max(1, Math.round(crop.width() / targetSensorAspect));
            int dy = (crop.height() - targetHeight) / 2;
            crop.top += dy;
            crop.bottom = crop.top + targetHeight;
        }

        float nx = Math.max(0f, Math.min(1f, previewX / (float) previewWidth));
        float ny = Math.max(0f, Math.min(1f, previewY / (float) previewHeight));

        /* IRIS_26524_RESIDUAL_ZOOM_FOCUS_MAPPING
         * Camera2 already interprets AF/AE regions in its hardware-zoom field
         * of view. Only Iris' post-HAL preview crop needs to be folded back into
         * the normalized preview coordinate before the tested 26523 mapping.
         */
        float residualZoom = Math.max(1.0f,
                IrisZoomController.getResidualSoftwareZoom());
        if (residualZoom > 1.0001f) {
            nx = 0.5f + (nx - 0.5f) / residualZoom;
            ny = 0.5f + (ny - 0.5f) / residualZoom;
        }

        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) nx = 1f - nx;

        float su;
        float sv;
        switch (orientation) {
            case 270:
                su = 1f - ny;
                sv = nx;
                break;
            case 180:
                su = 1f - nx;
                sv = 1f - ny;
                break;
            case 0:
                su = nx;
                sv = ny;
                break;
            case 90:
            default:
                // Preserves the historical portrait mapping, now in the correct crop domain.
                su = ny;
                sv = 1f - nx;
                break;
        }

        int centerX = crop.left + Math.round(su * Math.max(0, crop.width() - 1));
        int centerY = crop.top + Math.round(sv * Math.max(0, crop.height() - 1));
        int regionWidth = Math.max(1, crop.width() / 8);
        int regionHeight = Math.max(1, crop.height() / 8);
        int left = Math.max(crop.left, Math.min(centerX - regionWidth / 2, crop.right - regionWidth));
        int top = Math.max(crop.top, Math.min(centerY - regionHeight / 2, crop.bottom - regionHeight));
        MeteringRectangle rect = new MeteringRectangle(
                left, top, regionWidth, regionHeight, MeteringRectangle.METERING_WEIGHT_MAX - 1);
        Log.v(TAG, "IRIS_26523_FOCUS_MAP preview=" + previewX + "," + previewY
                + " view=" + previewWidth + "x" + previewHeight
                + " crop=" + crop + " orientation=" + orientation
                + " residualSoftwareZoom=" + residualZoom
                + " rect=" + rect);
        return new MeteringRectangle[]{rect};
    }

    private void triggerAutoFocus(MeteringRectangle[] rectaf, boolean lockRequested) {
        if (CaptureController.burst) return;
        if (!captureController.iris26679PreviewSessionReadyForControl()) {
            Log.w(TAG, "IRIS_26679_TOUCH_AF_TRIGGER_SKIPPED sessionReady=false");
            return;
        }
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null) {
            Log.w(TAG, "triggerAutoFocus(): mPreviewRequestBuilder is null");
            return;
        }
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
        if (!captureController.rebuildPreviewBuilderOneShot()) {
            Log.d(TAG, "IRIS_26679_TOUCH_AF_TRIGGER_ABORT cancelAccepted=false");
            return;
        }
        builder.set(CaptureRequest.CONTROL_AF_REGIONS, rectaf);
        builder.set(CaptureRequest.CONTROL_AE_REGIONS, rectaf);
        builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO);
        int preferredAfMode = PreferenceKeys.getAfMode();
        builder.set(CaptureRequest.CONTROL_AF_MODE, preferredAfMode);
        builder.set(CaptureRequest.CONTROL_AE_MODE, Math.max(PreferenceKeys.getAeMode(), 1));

        boolean oneShotAfMode = preferredAfMode == CaptureRequest.CONTROL_AF_MODE_AUTO
                || preferredAfMode == CaptureRequest.CONTROL_AF_MODE_MACRO;
        if (lockRequested || oneShotAfMode) {
            builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_START);
            if (!captureController.rebuildPreviewBuilderOneShot()) {
                Log.d(TAG, "IRIS_26679_TOUCH_AF_TRIGGER_ABORT startAccepted=false");
                return;
            }
            builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        }
        if (!captureController.rebuildPreviewBuilder()) {
            Log.d(TAG, "IRIS_26679_TOUCH_AF_TRIGGER_ABORT repeatingAccepted=false");
            return;
        }
        isTouchFocus = true;
        focusLocked = lockRequested;
        Log.d(TAG, "IRIS_26523_TOUCH_AF lock=" + lockRequested
                + " afMode=" + preferredAfMode + " region=" + rectaf[0]);
    }
    private void resetAutoFocus() {
        focusLocked = false;
        activeTouchRegion = null;
        if (captureController.isSpektraModeActive()) {
            captureController.getSpektraCameraOwner().unlockFocus();
            iris26679PendingAutoFocusReset = false;
            isTouchFocus = false;
            Log.d(TAG, "IRIS_26681_SPEKTRA_TOUCH_AF_RESET");
            return;
        }
        if (CaptureController.burst) return;
        if (!captureController.iris26679PreviewSessionReadyForControl()) {
            iris26679PendingAutoFocusReset = true;
            isTouchFocus = false;
            Log.d(TAG, "IRIS_26679_TOUCH_AF_RESET_DEFERRED sessionReady=false");
            return;
        }
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null) {
            iris26679PendingAutoFocusReset = true;
            Log.w(TAG, "resetAutoFocus(): mPreviewRequestBuilder is null");
            isTouchFocus = false;
            return;
        }
        Log.d(TAG, "IRIS_26523_TOUCH_AF unlock");
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
        builder.set(CaptureRequest.CONTROL_AF_REGIONS, captureController.mPreviewMeteringAF);
        builder.set(CaptureRequest.CONTROL_AE_REGIONS, captureController.mPreviewMeteringAE);
        builder.set(CaptureRequest.CONTROL_AF_MODE, captureController.mPreviewAFMode);
        builder.set(CaptureRequest.CONTROL_AE_MODE, captureController.mPreviewAEMode);
        if (!captureController.rebuildPreviewBuilderOneShot()) {
            iris26679PendingAutoFocusReset = true;
            isTouchFocus = false;
            Log.d(TAG, "IRIS_26679_TOUCH_AF_RESET_DEFERRED oneShotAccepted=false");
            return;
        }
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        builder.set(CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER, CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER_IDLE);
        if (!captureController.rebuildPreviewBuilder()) {
            iris26679PendingAutoFocusReset = true;
            isTouchFocus = false;
            Log.d(TAG, "IRIS_26679_TOUCH_AF_RESET_DEFERRED repeatingAccepted=false");
            return;
        }
        iris26679PendingAutoFocusReset = false;
        isTouchFocus = false;
    }


    //Thread safe
    //call when focus circle needs to be hidden immediately
    public void resetFocusCircle() {
        focusCircleView.removeCallbacks(hideFocusCircleRunnable);
        focusCircleView.post(hideFocusCircleRunnable);
        resetAutoFocus();
    }

    //Must be run on UI Thread
    private void hideFocusCircleView() {
        if (focusCircleView.getVisibility() == View.VISIBLE) {
            focusCircleView.animate().alpha(0f).scaleY(1.8f).scaleX(1.8f).setDuration(100)
                    .withEndAction(() -> {
                        focusCircleView.setVisibility(View.GONE);
                        focusCircleView.setX((float) textureView.getWidth() / 2.f);
                        focusCircleView.setY((float) textureView.getHeight() / 2.f);
                        focusCircleView.setScaleY(1f);
                        focusCircleView.setScaleX(1f);
                        focusCircleView.setAlpha(1f);
                    })
                    .start();
        }
    }
}
