package com.particlesdevs.photoncamera.control;

import android.graphics.RectF;
import com.particlesdevs.photoncamera.util.Log;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;

import androidx.constraintlayout.widget.ConstraintLayout;

import com.particlesdevs.photoncamera.circularbarlib.api.ManualModeConsole;
import com.particlesdevs.photoncamera.circularbarlib.control.ManualParamModel;
import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.ui.camera.CameraFragment;
import com.particlesdevs.photoncamera.ui.camera.viewmodel.CameraFragmentViewModel;

public class Swipe {
    private static final String TAG = "Swipe";
    private final CameraFragment cameraFragment;
    private final CaptureController captureController;
    private GestureDetector gestureDetector;
    /* IRIS_26524_PINCH_ZOOM_GESTURE_OWNER */
    private ScaleGestureDetector iris26524ScaleDetector;
    private boolean iris26524PinchActive = false;
    private boolean iris26524SuppressNextUp = false;
    private ManualModeConsole manualModeConsole;
    private CameraFragmentViewModel cameraFragmentViewModel;
    private ImageView ocManual;

    public Swipe(CameraFragment cameraFragment) {
        this.cameraFragment = cameraFragment;
        this.captureController = cameraFragment.getCaptureController();
    }

    public void init() {
        Log.d(TAG, "SwipeDetection - ON");
        manualModeConsole = cameraFragment.getManualModeConsole();
        cameraFragmentViewModel = cameraFragment.getCameraFragmentViewModel();
        ocManual = cameraFragment.findViewById(R.id.open_close_manual);
        manualModeConsole.setPanelVisibility(false);
        ocManual.animate().rotation(0).setDuration(250).start();
        ocManual.setOnClickListener((v) -> {
            if (!manualModeConsole.isPanelVisible()) {
                SwipeUp();
                Log.d(TAG, "Arrow Clicked:SwipeUp");
            } else {
                SwipeDown();
                Log.d(TAG, "Arrow Clicked:SwipeDown");
            }
        });
        gestureDetector = new GestureDetector(cameraFragment.getContext(), new GestureDetector.SimpleOnGestureListener() {
            private static final int SWIPE_THRESHOLD = 100;
            private static final int SWIPE_VELOCITY_THRESHOLD = 100;

            @Override
            public boolean onDown(MotionEvent e) {
                return true;
            }

            @Override
            public boolean onSingleTapUp(MotionEvent e) {
                cameraFragmentViewModel.setSettingsBarVisible(false);
                startTouchToFocus(e);
                return false;
            }

            @Override
            public void onLongPress(MotionEvent e) {
                startTouchFocusLock(e);
            }

            @Override
            public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
                float diffY = e2.getY() - e1.getY();
                float diffX = e2.getX() - e1.getX();
                if (Math.abs(diffX) > Math.abs(diffY)) {
                    if (Math.abs(diffX) > SWIPE_THRESHOLD && Math.abs(velocityX) > SWIPE_VELOCITY_THRESHOLD) {
                        if (diffX > 0) {
                            Log.d(TAG, "Right");
                            SwipeRight();
                        } else {
                            Log.d(TAG, "Left");
                            SwipeLeft();
                        }
                        return true;
                    }
                } else if (Math.abs(diffY) > SWIPE_THRESHOLD && Math.abs(velocityY) > SWIPE_VELOCITY_THRESHOLD) {
                    if (diffY > 0) {
                        Log.d(TAG, "Bottom");//it swipes from top to bottom
                        SwipeDown();
                    } else {
                        Log.d(TAG, "Top");//it swipes from bottom to top
                        SwipeUp();
                    }
                    return true;
                }
                return false;
            }
        });
        iris26524ScaleDetector = new ScaleGestureDetector(
                cameraFragment.getContext(),
                new ScaleGestureDetector.SimpleOnScaleGestureListener() {
                    @Override
                    public boolean onScaleBegin(ScaleGestureDetector detector) {
                        IrisZoomController zoom = cameraFragment.getIrisZoomController();
                        boolean enabled = zoom != null
                                && IrisZoomController.isContinuousZoomEnabledForCurrentMode();
                        iris26524PinchActive = enabled;
                        iris26524SuppressNextUp = enabled;
                        if (enabled && gestureDetector != null) {
                            long now = android.os.SystemClock.uptimeMillis();
                            MotionEvent cancel = MotionEvent.obtain(
                                    now, now, MotionEvent.ACTION_CANCEL,
                                    detector.getFocusX(), detector.getFocusY(), 0);
                            try {
                                gestureDetector.onTouchEvent(cancel);
                                Log.d(TAG, "IRIS_26527_PINCH_OWNS_GESTURE_STREAM cancelPriorTap=true");
                            } finally {
                                cancel.recycle();
                            }
                        }
                        return enabled;
                    }

                    @Override
                    public boolean onScale(ScaleGestureDetector detector) {
                        IrisZoomController zoom = cameraFragment.getIrisZoomController();
                        if (zoom == null
                                || !IrisZoomController.isContinuousZoomEnabledForCurrentMode()) {
                            return false;
                        }
                        zoom.onPinchScale(detector.getScaleFactor());
                        return true;
                    }

                    @Override
                    public void onScaleEnd(ScaleGestureDetector detector) {
                        IrisZoomController zoom = cameraFragment.getIrisZoomController();
                        if (zoom != null) zoom.finishScale();
                        iris26524PinchActive = false;
                    }
                });

        View.OnTouchListener touchListener = (view, motionEvent) -> {
            iris26524ScaleDetector.onTouchEvent(motionEvent);
            int action = motionEvent.getActionMasked();
            if (motionEvent.getPointerCount() > 1
                    || iris26524ScaleDetector.isInProgress()
                    || iris26524PinchActive) {
                return true;
            }
            if ((action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL)
                    && iris26524SuppressNextUp) {
                iris26524SuppressNextUp = false;
                return true;
            }
            return gestureDetector.onTouchEvent(motionEvent);
        };
        View holder = cameraFragment.findViewById(R.id.textureHolder);
        Log.d(TAG, "input:" + holder);
        if (holder != null) holder.setOnTouchListener(touchListener);
    }

    /* IRIS_26523_ACTUAL_PREVIEW_TOUCH_BOUNDS */
    private float[] getPreviewTouchPoint(MotionEvent event) {
        if (event == null || cameraFragment.textureView == null) return null;
        View preview = captureController.isSpektraModeActive()
                ? cameraFragment.spektraSurfaceView : cameraFragment.textureView;
        if (preview == null) return null;
        int width = preview.getWidth();
        int height = preview.getHeight();
        if (width <= 0 || height <= 0 || !preview.isShown()) return null;
        int[] location = new int[2];
        preview.getLocationOnScreen(location);
        float x = event.getRawX() - location[0];
        float y = event.getRawY() - location[1];
        if (x < 0f || y < 0f || x >= width || y >= height) return null;

        /* IRIS_26699_VIDEO_BOTTOM_TOUCH_FOCUS_EXCLUSION
         * Video previews intentionally extend under the translucent bottom controls. That visual
         * preview area is not a focus target: shutter/gallery/switcher keep their own touch owners,
         * while tap/long-press focus remains available everywhere above the actual bottom bar. */
        CameraMode mode = captureController.getAuthoritativeCameraMode();
        if (mode == CameraMode.VIDEO || mode == CameraMode.RAWVIDEO) {
            View bottomControls = cameraFragment.findViewById(R.id.layout_bottombar);
            if (bottomControls != null && bottomControls.isShown()) {
                int[] bottomLocation = new int[2];
                bottomControls.getLocationOnScreen(bottomLocation);
                float rawY = event.getRawY();
                if (rawY >= bottomLocation[1]
                        && rawY < bottomLocation[1] + bottomControls.getHeight()) {
                    Log.d(TAG, "IRIS_26699_VIDEO_BOTTOM_FOCUS_REJECT mode=" + mode
                            + " rawY=" + rawY + " bottomTop=" + bottomLocation[1]);
                    return null;
                }
            }
        }
        return new float[]{x, y};
    }

    private boolean focusGesturesAllowed() {
        return manualModeConsole.getManualParamModel().getCurrentFocusValue()
                == ManualParamModel.FOCUS_AUTO;
    }

    private void startTouchToFocus(MotionEvent event) {
        float[] point = getPreviewTouchPoint(event);
        if (point == null || !focusGesturesAllowed()) return;
        TouchFocus touchFocus = cameraFragment.getTouchFocus();
        if (touchFocus == null) return;
        if (touchFocus.isFocusLocked()) {
            // A normal tap while locked returns to the camera's normal autofocus behavior.
            touchFocus.unlockFocus();
        } else {
            touchFocus.processTouchToFocus(point[0], point[1]);
        }
    }

    private void startTouchFocusLock(MotionEvent event) {
        float[] point = getPreviewTouchPoint(event);
        if (point == null || !focusGesturesAllowed()) return;
        TouchFocus touchFocus = cameraFragment.getTouchFocus();
        if (touchFocus != null) {
            touchFocus.processLongPressToLock(point[0], point[1]);
        }
    }

    public void SwipeUp() {
        if (cameraFragmentViewModel.isSettingsBarVisible()) {
            cameraFragmentViewModel.setSettingsBarVisible(false);
        } else {
            ocManual.animate().rotation(180).setDuration(250).start();
            manualModeConsole.setPanelVisibility(true);
//        cameraFragment.getCaptureController().rebuildPreview();
            cameraFragment.getTouchFocus().resetFocusCircle();
        }

    }

    public void SwipeDown() {
        if (manualModeConsole.isPanelVisible()) {
            ocManual.animate().rotation(0).setDuration(250).start();
            cameraFragment.getTouchFocus().resetFocusCircle();
            captureController.reset3Aparams();
            manualModeConsole.setPanelVisibility(false);
            manualModeConsole.retractAllKnobs();
        } else {
            cameraFragmentViewModel.setSettingsBarVisible(true);
        }
    }

    public void SwipeRight() {

    }

    public void SwipeLeft() {

    }

}
