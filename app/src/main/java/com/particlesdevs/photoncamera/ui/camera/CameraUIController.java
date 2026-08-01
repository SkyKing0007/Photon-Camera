package com.particlesdevs.photoncamera.ui.camera;

import android.annotation.SuppressLint;
import android.content.Context;
import android.os.CountDownTimer;

import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.util.Log;
import android.view.View;

import androidx.lifecycle.Observer;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.control.CountdownTimer;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingType;
import com.particlesdevs.photoncamera.ui.camera.model.TopBarSettingsData;
import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout;
import com.particlesdevs.photoncamera.ui.camera.views.FlashButton;
import com.particlesdevs.photoncamera.ui.camera.views.TimerButton;

/**
 * Implementation of {@link CameraUIEventsListener}
 * <p>
 * Responsible for converting user inputs into actions
 */
final class CameraUIController implements CameraUIEventsListener,
        Observer<TopBarSettingsData<?, ?>>, AuxButtonsLayout.AuxButtonListener {
    private static final String TAG = "CameraUIController";
    private final CameraFragment cameraFragment;
    private CountDownTimer countdownTimer;
    private View shutterButton;

    public CameraUIController(CameraFragment cameraFragment) {
        this.cameraFragment = cameraFragment;
    }

    private void restoreVideoIdleScaleAfterStop(View view) {
        /*
         * The liquid-button touch animation finishes at scale 1.0.
         * The approved Video/RAW Video idle button uses scale 0.84.
         * Run after that animation so stopped state exactly matches
         * the initial default state.
         */
        view.postDelayed(() -> {
            view.animate().cancel();
            view.setScaleX(0.84f);
            view.setScaleY(0.84f);
            view.setPressed(false);
            view.setActivated(true);
            view.jumpDrawablesToCurrentState();
            view.invalidate();
        }, 240L);
    }

    @SuppressLint("NonConstantResourceId")
    @Override
    public void onClick(View view) {
        switch (view.getId()) {
            case R.id.shutter_button:
                shutterButton = view;
                switch (PhotonCamera.getSettings().selectedMode) {
                    case PHOTO:
                    case MOTION:
                    case NIGHT:
                        if (view.isHovered()) resetTimer();
                        else startTimer();
                        break;
                    case UNLIMITED:
                    case RAWVIDEO:
                        if (!cameraFragment.captureController.unlimitedStarted) {
                            cameraFragment.captureController.onUnlimited = false;
                            cameraFragment.captureController.unlimitedStarted = false;
                            cameraFragment.captureController.callUnlimitedStart();
                            view.setActivated(false);
                        } else {
                            cameraFragment.captureController.callUnlimitedEnd();
                            view.setActivated(true);
                            if (PhotonCamera.getSettings().selectedMode
                                    == CameraMode.RAWVIDEO) {
                                restoreVideoIdleScaleAfterStop(view);
                            }
                        }
                        break;
                    case VIDEO:
                        if (!cameraFragment.captureController.mIsRecordingVideo) {
                            cameraFragment.captureController.VideoStart();
                            view.setActivated(false);
                        } else {
                            cameraFragment.captureController.VideoEnd();
                            view.setActivated(true);
                            restoreVideoIdleScaleAfterStop(view);
                        }
                        break;
                }
                break;
            case R.id.settings_button: {
                boolean controlsVisible = cameraFragment.cameraFragmentBinding
                        .getUimodel().isSettingsBarVisibility();
                cameraFragment.cameraFragmentBinding
                        .getUimodel().setSettingsBarVisibility(!controlsVisible);
                break;
            }

            case R.id.manual_controls_button:
                cameraFragment.cameraFragmentBinding
                        .getUimodel().setSettingsBarVisibility(false);
                cameraFragment.toggleManualControls();
                break;

            case R.id.quad_status_toggle_button:
                PreferenceKeys.setQuadBayer(!PreferenceKeys.isQuadBayerOn());
                cameraFragment.showSnackBar(
                        cameraFragment.getString(R.string.quad_bayer_toggle_text)
                                + ':' + onOff(PreferenceKeys.isQuadBayerOn()));
                this.restartCamera();
                cameraFragment.updateSettingsBar();
                break;

            case R.id.hdrx_toggle_button:
                PreferenceKeys.setHdrX(!PreferenceKeys.isHdrXOn());
                if (PreferenceKeys.isHdrXOn())
                    CaptureController.setTargetFormat(CaptureController.RAW_FORMAT);
                else
                    CaptureController.setTargetFormat(CaptureController.YUV_FORMAT);
                cameraFragment.showSnackBar(cameraFragment.getString(R.string.hdrx) + ':' + onOff(PreferenceKeys.isHdrXOn()));
                this.restartCamera();
                break;

            case R.id.gallery_image_button:
                cameraFragment.launchGallery();
                break;

            case R.id.eis_toggle_button:
                PreferenceKeys.setEisPhoto(!PreferenceKeys.isEisPhotoOn());
                cameraFragment.showSnackBar(cameraFragment.getString(R.string.eis_toggle_text) + ':' + onOff(PreferenceKeys.isEisPhotoOn()));
                cameraFragment.updateSettingsBar();
                break;

            case R.id.fps_toggle_button:
                PreferenceKeys.setFpsMode((PreferenceKeys.getFpsMode() + 1) % 4);
                cameraFragment.captureController.applyFpsRange();
                cameraFragment.updateSettingsBar();
                break;

            case R.id.quad_res_toggle_button:
                PreferenceKeys.setQuadBayer(!PreferenceKeys.isQuadBayerOn());
                cameraFragment.showSnackBar(cameraFragment.getString(R.string.quad_bayer_toggle_text) + ':' + onOff(PreferenceKeys.isQuadBayerOn()));
                this.restartCamera();
                cameraFragment.updateSettingsBar();
                break;

            case R.id.flip_camera_button:
                view.animate().rotationBy(180).setDuration(450).start();
                //cameraFragment.textureView.animate().rotationBy(360).setDuration(450).start();
                //PreferenceKeys.setCameraID(cycler(PreferenceKeys.getCameraID()));
                setID(cameraFragment.cycler(PreferenceKeys.getCameraID()));
                this.restartCamera();
                break;
            case R.id.grid_toggle_button:
                PreferenceKeys.setGridValue((PreferenceKeys.getGridValue() + 1) % view.getResources().getStringArray(R.array.vf_grid_entryvalues).length);
                view.setSelected(PreferenceKeys.getGridValue() != 0);
                cameraFragment.invalidateSurfaceView();
                cameraFragment.updateSettingsBar();
                break;

            case R.id.flash_button:
                PreferenceKeys.setAeMode((PreferenceKeys.getAeMode() + 1) % 2); //cycles in 0 (torch), 1 (off)
                ((FlashButton) view).setFlashValueState(PreferenceKeys.getAeMode());
                cameraFragment.captureController.setPreviewAEModeRebuild(PreferenceKeys.getAeMode());
                cameraFragment.updateSettingsBar();
                break;

            case R.id.countdown_timer_button:
                PreferenceKeys.setCountdownTimerIndex((PreferenceKeys.getCountdownTimerIndex() + 1) % view.getResources().getIntArray(R.array.countdowntimer_entryvalues).length);
                ((TimerButton) view).setTimerIconState(PreferenceKeys.getCountdownTimerIndex());
                cameraFragment.updateSettingsBar();
                break;
        }
    }

    private int getTimerValue(Context context) {
        int[] timerValues = context.getResources().getIntArray(R.array.countdowntimer_entryvalues);
        return timerValues[PreferenceKeys.getCountdownTimerIndex()];
    }

    private void startTimer() {
        if (this.shutterButton != null) {
            this.shutterButton.setHovered(true);
            this.countdownTimer = new CountdownTimer(
                    cameraFragment.findViewById(R.id.frameTimer),
                    getTimerValue(this.shutterButton.getContext()) * 1000L, 1000,
                    this::onTimerFinished).start();
        }
    }

    private void resetTimer() {
        if (this.countdownTimer != null) this.countdownTimer.cancel();
        if (this.shutterButton != null) this.shutterButton.setHovered(false);
    }

    @Override
    public void onAuxButtonClicked(String id) {
        Log.d(TAG, "onAuxButtonClicked() called with: id = [" + id + "]");
        setID(id);
        this.restartCamera();

    }

    private void setID(String input) {
        PreferenceKeys.setCameraID(String.valueOf(input));
    }

    @Override
    public void onCameraModeChanged(CameraMode cameraMode) {
        CameraMode previousMode = PhotonCamera.getSettings().selectedMode;
        if ((previousMode == CameraMode.RAWVIDEO
                || previousMode == CameraMode.UNLIMITED)
                && previousMode != cameraMode
                && cameraFragment.captureController.onUnlimited) {
            Log.d(TAG, "Stopping active continuous capture before mode change: "
                    + previousMode + " -> " + cameraMode);
            /*
             * restartCamera() below owns the replacement session. Building a
             * temporary preview session here races its onConfigured callback
             * against the restart and leaves RAW Video unable to start again.
             */
            cameraFragment.captureController.callUnlimitedEnd(false);
        }

        /*
         * RAW Video is a streaming writer, not an HDR processor. It never owns
         * the normal processing callback lifecycle, so any process-wide
         * isProcessing=true value that survives RAW Video exit is stale.
         * Clear it before Motion refreshes its still-mode processing ring.
         */
        if (previousMode == CameraMode.RAWVIDEO && previousMode != cameraMode) {
            CaptureController.isProcessing = false;
            Log.d(TAG, "Cleared stale processing state after RAW Video exit");
        }

        if (cameraMode == CameraMode.RAWVIDEO
                && previousMode != CameraMode.RAWVIDEO) {
            cameraFragment.captureController.onUnlimited = false;
            cameraFragment.captureController.unlimitedStarted = false;
            Log.d(TAG, "Reset RAW Video start state on mode entry");
        }

        PreferenceKeys.setCameraModeOrdinal(cameraMode.ordinal());
        Log.d(TAG, "onCameraModeChanged() called with: cameraMode = [" + cameraMode + "]");
        switch (cameraMode) {
            case PHOTO:
            case MOTION:
            case NIGHT:
            case UNLIMITED:
            case RAWVIDEO:
            default:
                break;
            case VIDEO:
                PreferenceKeys.setCameraModeOrdinal(CameraMode.VIDEO.ordinal());
                break;
        }
        this.restartCamera();
    }

    @Override
    public void onPause() {
        this.resetTimer();
    }

    private void restartCamera() {
        this.resetTimer();
        cameraFragment.captureController.restartCamera();
    }

    private String onOff(boolean value) {
        return value ? "On" : "Off";
    }

    private void onTimerFinished() {
        this.shutterButton.setHovered(false);
        this.shutterButton.setActivated(false);
        this.shutterButton.setClickable(false);
        cameraFragment.captureController.takePicture();
    }

    @Override
    public void onChanged(TopBarSettingsData<?, ?> topBarSettingsData) {
        if (topBarSettingsData != null && topBarSettingsData.getType() != null && topBarSettingsData.getValue() != null) {
            if (topBarSettingsData.getType() instanceof SettingType) {
                SettingType type = (SettingType) topBarSettingsData.getType();
                Object value = topBarSettingsData.getValue();
                switch (type) {
                    case FLASH:
                        PreferenceKeys.setAeMode((Integer) value); //cycles in 0,1,2,3
                        cameraFragment.captureController.setPreviewAEModeRebuild(PreferenceKeys.getAeMode());
                        cameraFragment.cameraFragmentBinding.layoutTopbar.flashButton.setFlashValueState((Integer) value);
                        break;
                    case HDRX:
                        PreferenceKeys.setHdrX(value.equals(1));
                        if (value.equals(1))
                            CaptureController.setTargetFormat(CaptureController.RAW_FORMAT);
                        else
                            CaptureController.setTargetFormat(CaptureController.YUV_FORMAT);
                        this.restartCamera();
                        break;
                    case QUAD:
                        PreferenceKeys.setQuadBayer(value.equals(1));
                        this.restartCamera();
                        break;
                    case GRID:
                        PreferenceKeys.setGridValue((Integer) value);
                        cameraFragment.invalidateSurfaceView();
                        break;
                    case FPS_60:
                        PreferenceKeys.setFpsMode((Integer) value);
                        cameraFragment.captureController.applyFpsRange();
                        break;
                    case TIMER:
                        PreferenceKeys.setCountdownTimerIndex((Integer) value);
                        cameraFragment.cameraFragmentBinding.layoutTopbar.countdownTimerButton.setTimerIconState((Integer) value);
                        break;
                    case EIS:
                        PreferenceKeys.setEisPhoto(value.equals(1));
                        break;
                    case RAW:
                        PreferenceKeys.setSaveRaw((Integer) value);
                        break;
                    case BATTERY_SAVER:
                        PreferenceKeys.setBatterySaver(value.equals(1));
                        break;
                    case BRACKETING:
                        PreferenceKeys.setBracketingMode((Integer) value);
                        // Update HDR class to use the new bracketing mode
                        IsoExpoSelector.HDR = (Integer) value > 0;
                        break;
                    case HISTOGRAM:
                        PreferenceKeys.setShowHistogram(value.equals(1));
                        cameraFragment.invalidateSurfaceView();
                        break;
                    case AE_METERING:
                        PreferenceKeys.setAeMetering((Integer) value);
                        cameraFragment.captureController.applyAeMetering();
                        break;

                }
                cameraFragment.cameraFragmentBinding.layoutTopbar.invalidateAll();
            }
        }

    }
}
