package com.particlesdevs.photoncamera.ui.camera;

import com.particlesdevs.photoncamera.capture.CaptureController;

import android.os.Bundle;
import android.widget.TextView;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.ImageButton;
import android.widget.ProgressBar;

import androidx.constraintlayout.widget.ConstraintLayout;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.databinding.LayoutBottombuttonsBinding;
import com.particlesdevs.photoncamera.databinding.LayoutMainTopbarBinding;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.TunableInjector;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.LiquidModePicker;
import com.particlesdevs.photoncamera.util.Utilities;


import static androidx.constraintlayout.widget.ConstraintSet.GONE;

/**
 * This Class is a dumb 'View' which contains view components visible in the main Camera User Interface
 * <p>
 * It gets instantiated in {@link CameraFragment#onViewCreated(View, Bundle)}
 */
public class CameraUIViewImpl implements CameraUIView {
    private static final String TAG = "CameraUIView";
    private static final String[] MODE_DISPLAY_LABELS = {
            "Unlimited",
            "RAW Video",
            "Motion",
            "Photo",
            "Night",
            "Video"
    };

    private static final CameraMode[] MODE_ACTION_ORDER = {
            CameraMode.UNLIMITED,
            CameraMode.RAWVIDEO,
            CameraMode.MOTION,
            CameraMode.PHOTO,
            CameraMode.NIGHT,
            CameraMode.VIDEO
    };

    @Tunable(
            title = "Enable Quad Resolution",
            description = "Show Quad Resolution toggle in camera controls. When off, Quad Res is forced disabled.",
            category = "UI",
            min = 0.0f,
            max = 1.0f,
            defaultValue = 0.0f,
            step = 1.0f
    )
    boolean enableQuadRes = false;

    private final CameraFragment cameraFragment;
    private final ProgressBar mCaptureProgressBar;
    private final ImageButton mShutterButton;
    private final ProgressBar mProcessingProgressBar;
    private final LiquidModePicker mModePicker;
    private final TextView mVideoRecordingInfo;
    private View formatSelectorPill;
    private View formatExpandedPanel;
    private View quadStatusContainer;
    private View quadStatusToggleButton;
    private TextView formatActiveLabel;
    private TextView quadStatusLabel;
    private boolean formatPanelOpen;
    private LayoutMainTopbarBinding topbar;
    private LayoutBottombuttonsBinding bottombuttons;
    private CameraUIEventsListener uiEventsListener;
    private CameraModeState currentState;

    private CameraMode displayedMode = null;
    CameraUIViewImpl(CameraFragment cameraFragment) {
        this.cameraFragment = cameraFragment;
        this.topbar = cameraFragment.cameraFragmentBinding.layoutTopbar;
        this.bottombuttons = cameraFragment.cameraFragmentBinding.layoutBottombar.bottomButtons;
        this.mCaptureProgressBar = cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar;
        this.mProcessingProgressBar = bottombuttons.processingProgressBar;
        this.mShutterButton = bottombuttons.shutterButton;
        this.mModePicker = cameraFragment.cameraFragmentBinding.layoutBottombar.modeSwitcher.modePickerView;
        this.mVideoRecordingInfo = cameraFragment.cameraFragmentBinding.getRoot().findViewById(R.id.video_recording_info);
        this.initListeners();
        this.initModeSwitcher();
        this.initLiquidUi();
        this.currentState = new PhotoMotionModeState(); //init mode
        initModeState(CameraMode.valueOf(PreferenceKeys.getCameraModeOrdinal()));
    }

    private void initModeState(CameraMode mode) {
        displayedMode = mode;
        switch (mode) {
            case VIDEO:
                currentState = new VideoModeState();
                break;
            case UNLIMITED:
            case RAWVIDEO:
                currentState = new UnlimitedModeState();
                break;
            case NIGHT:
                currentState = new NightModeState();
                break;
            default:
                currentState = new PhotoMotionModeState();
                break;
        }
        currentState.reConfigureModeViews(mode);
    }

    private void initListeners() {
        TunableInjector.inject(this);
        if (!enableQuadRes) {
            PreferenceKeys.setQuadBayer(false);
        }
        this.topbar.setTopBarClickListener(v -> this.uiEventsListener.onClick(v));
        this.bottombuttons.setBottomBarClickListener(v -> this.uiEventsListener.onClick(v));
        this.topbar.setQuadVisible(enableQuadRes);
    }

    private void initModeSwitcher() {
        this.mModePicker.setValues(MODE_DISPLAY_LABELS);
        this.mModePicker.setSideItems(0);
        this.mModePicker.setOverScrollMode(View.OVER_SCROLL_NEVER);
        this.mModePicker.setOnItemSelectedListener(index -> {
            if (index >= 0 && index < MODE_ACTION_ORDER.length) {
                switchToMode(MODE_ACTION_ORDER[index]);
            }
        });
        this.mModePicker.collapseToIndex(
                indexOfMode(
                        CameraMode.valueOf(
                                PreferenceKeys.getCameraModeOrdinal()
                        )
                )
        );
    }

    private int indexOfMode(CameraMode mode) {
        for (int i = 0; i < MODE_ACTION_ORDER.length; i++) {
            if (MODE_ACTION_ORDER[i] == mode) return i;
        }
        return 0;
    }

    private void initLiquidUi() {
        View root = cameraFragment.cameraFragmentBinding.getRoot();
        formatSelectorPill = root.findViewById(R.id.format_selector_pill);
        formatExpandedPanel = root.findViewById(R.id.format_expanded_panel);
        quadStatusContainer = root.findViewById(R.id.quad_status_container);
        quadStatusToggleButton = root.findViewById(R.id.quad_status_toggle_button);
        formatActiveLabel = root.findViewById(R.id.format_active_label);
        quadStatusLabel = root.findViewById(R.id.quad_status_label);

        View formatJpg = root.findViewById(R.id.format_jpg_button);
        View formatRaw = root.findViewById(R.id.format_raw_button);
        View formatRawJpg = root.findViewById(R.id.format_raw_jpg_button);
        View manualControls = root.findViewById(R.id.approved_manual_handle);

        formatSelectorPill.setOnClickListener(v -> toggleFormatPanel());
        formatJpg.setOnClickListener(v -> selectFormat(0));
        formatRawJpg.setOnClickListener(v -> selectFormat(1));
        formatRaw.setOnClickListener(v -> selectFormat(2));
        quadStatusToggleButton.setOnClickListener(v -> {
            if (uiEventsListener != null) uiEventsListener.onClick(v);
        });
        if (manualControls != null) {
            manualControls.setOnClickListener(v -> {
                if (uiEventsListener != null) uiEventsListener.onClick(v);
            });
        }

        installPressAnimation(
                formatSelectorPill,
                formatJpg,
                formatRaw,
                formatRawJpg,
                quadStatusToggleButton,
                topbar.countdownTimerButton,
                topbar.flashButton,
                topbar.settingsButton,
                bottombuttons.galleryImageButton,
                bottombuttons.flipCameraButton,
                bottombuttons.shutterButton
        );
        View approvedManualHandle = root.findViewById(R.id.approved_manual_handle);
        TextView approvedManualChevron = root.findViewById(R.id.approved_manual_chevron);
        if (approvedManualHandle != null && approvedManualChevron != null) {
            approvedManualChevron.setText("\u2304");
            approvedManualHandle.setOnClickListener(v -> {
                boolean opening = !cameraFragment.getManualModeConsole().isPanelVisible();
                approvedManualChevron.animate()
                        .rotation(opening ? 180.0f : 0.0f)
                        .setDuration(220L)
                        .start();
                cameraFragment.toggleManualControls();
            });
        }

        refreshFormatStatus();
    }

    private void installPressAnimation(View... views) {
        for (View view : views) {
            if (view == null) continue;
            view.setOnTouchListener((target, event) -> {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        target.animate().scaleX(0.91f).scaleY(0.91f).alpha(0.84f)
                                .setDuration(90).start();
                        break;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        target.animate().scaleX(1f).scaleY(1f).alpha(1f)
                                .setDuration(210).start();
                        break;
                    default:
                        break;
                }
                return false;
            });
        }
    }

    private void toggleFormatPanel() {
        if (formatExpandedPanel == null) return;
        formatPanelOpen = !formatPanelOpen;
        if (formatPanelOpen) {
            refreshFormatStatus();
            formatExpandedPanel.setVisibility(View.VISIBLE);
            formatExpandedPanel.setAlpha(0f);
            formatExpandedPanel.setTranslationY(-12f);
            formatExpandedPanel.setScaleX(0.94f);
            formatExpandedPanel.setScaleY(0.94f);
            formatExpandedPanel.animate()
                    .alpha(1f)
                    .translationY(0f)
                    .scaleX(1f)
                    .scaleY(1f)
                    .setDuration(260)
                    .start();
        } else {
            formatExpandedPanel.animate()
                    .alpha(0f)
                    .translationY(-12f)
                    .scaleX(0.94f)
                    .scaleY(0.94f)
                    .setDuration(190)
                    .withEndAction(() -> formatExpandedPanel.setVisibility(View.GONE))
                    .start();
        }
    }

    private void collapseFormatPanel() {
        if (!formatPanelOpen) return;
        toggleFormatPanel();
    }

    private void selectFormat(int value) {
        PreferenceKeys.setSaveRaw(value);
        refreshFormatStatus();
        collapseFormatPanel();
        cameraFragment.updateSettingsBar();
    }

    private void refreshFormatStatus() {
        if (formatActiveLabel == null) return;
        int saveRaw = PreferenceKeys.isSaveRaw();
        switch (saveRaw) {
            case 2:
                formatActiveLabel.setText("RAW");
                break;
            case 1:
                formatActiveLabel.setText("JPG+RAW");
                break;
            case 0:
            default:
                formatActiveLabel.setText("JPG");
                break;
        }

        boolean quadEnabled = enableQuadRes && PreferenceKeys.isQuadBayerOn();
        if (quadStatusContainer != null) {
            quadStatusContainer.setVisibility(quadEnabled ? View.VISIBLE : View.GONE);
        }
        if (quadStatusLabel != null) {
            quadStatusLabel.setText("48/64MP");
        }
        if (quadStatusToggleButton != null) {
            quadStatusToggleButton.setVisibility(enableQuadRes ? View.VISIBLE : View.GONE);
            if (quadStatusToggleButton instanceof TextView) {
                ((TextView) quadStatusToggleButton).setText(
                        PreferenceKeys.isQuadBayerOn()
                                ? "QUAD 48/64MP  ON"
                                : "QUAD 48/64MP  OFF");
            }
        }
    }

    @Override
    public void activateShutterButton(boolean status) {
        this.mShutterButton.post(() -> {
            boolean videoStyle = isVideoStyleMode();

            applyVideoShutterStack(videoStyle);
            this.mShutterButton.setActivated(status);
            this.mShutterButton.setClickable(status);

            /*
             * In Video and RAW Video, keep the progress overlay hidden
             * after every recording-state transition so default,
             * recording, and finished layouts remain identical.
             */
            if (videoStyle) {
                this.mProcessingProgressBar.setVisibility(View.GONE);
            }
        });
    }


    private boolean isVideoStyleMode() {
        CameraMode mode =
                CameraMode.valueOf(PreferenceKeys.getCameraModeOrdinal());
        return mode == CameraMode.VIDEO || mode == CameraMode.RAWVIDEO;
    }

    private void applyVideoShutterStack(boolean videoStyle) {
        if (mShutterButton == null || mProcessingProgressBar == null) {
            return;
        }

        if (videoStyle) {
            /*
             * Keep one persistent outer ring on the container.
             * The ImageButton draws only the red circle or stop square.
             * The processing ring is hidden because it was the source of
             * the duplicate circular outlines in Video and RAW Video.
             */
            mProcessingProgressBar.setVisibility(View.GONE);
            mProcessingProgressBar.setProgress(0);
            mProcessingProgressBar.setIndeterminate(false);

            mShutterButton.setScaleX(0.84f);
            mShutterButton.setScaleY(0.84f);
            mShutterButton.setBackgroundResource(
                    R.drawable.video_record_button
            );
        } else {
            if (CaptureController.isProcessing) {
                mProcessingProgressBar.setVisibility(View.VISIBLE);
            } else {
                mProcessingProgressBar.animate().cancel();
                mProcessingProgressBar.setIndeterminate(false);
                mProcessingProgressBar.setProgress(0);
                mProcessingProgressBar.clearAnimation();
                mProcessingProgressBar.setVisibility(View.INVISIBLE);
            }

            mShutterButton.setScaleX(0.83f);
            mShutterButton.setScaleY(0.83f);
        }
    }
    private void restoreVideoShutterIdleState() {
        if (!isVideoStyleMode() || mShutterButton == null) {
            return;
        }

        mShutterButton.post(() -> {
            applyVideoShutterStack(true);
            mShutterButton.setActivated(true);
            mShutterButton.setPressed(false);
            mShutterButton.jumpDrawablesToCurrentState();
            mShutterButton.invalidate();

            if (mProcessingProgressBar != null) {
                mProcessingProgressBar.setVisibility(View.GONE);
                mProcessingProgressBar.setProgress(0);
                mProcessingProgressBar.setIndeterminate(false);
            }
        });
    }
    private void applyBottomGeometry(boolean videoStyle) {
        float density =
                cameraFragment.getResources()
                        .getDisplayMetrics()
                        .density;

        if (bottombuttons != null
                && bottombuttons.shutterButtonContainer != null) {
            android.view.ViewGroup.LayoutParams rawParams =
                    bottombuttons.shutterButtonContainer.getLayoutParams();

            if (rawParams instanceof androidx.constraintlayout.widget.ConstraintLayout.LayoutParams) {
                androidx.constraintlayout.widget.ConstraintLayout.LayoutParams params =
                        (androidx.constraintlayout.widget.ConstraintLayout.LayoutParams) rawParams;

                if (videoStyle) {
                    params.width = Math.round(88.0f * density);
                    params.height = Math.round(88.0f * density);
                    params.topMargin = Math.round(74.0f * density);
                } else {
                    params.width = Math.round(92.0f * density);
                    params.height = Math.round(92.0f * density);
                    params.topMargin = Math.round(56.0f * density);
                }

                bottombuttons.shutterButtonContainer.setTranslationY(0.0f);
                bottombuttons.shutterButtonContainer.setLayoutParams(params);
            }
        }

        View manualToggle =
                cameraFragment.cameraFragmentBinding.getRoot()
                        .findViewById(R.id.manual_toggle_stack);
        if (manualToggle != null) {
            manualToggle.animate()
                    .translationY(videoStyle ? -30.0f * density : 0.0f)
                    .setDuration(180L)
                    .start();
        }

        View lensSelector =
                cameraFragment.cameraFragmentBinding.getRoot()
                        .findViewById(R.id.aux_buttons_container);
        if (lensSelector != null) {
            lensSelector.animate()
                    .translationY(videoStyle ? -48.0f * density : 0.0f)
                    .setDuration(180L)
                    .start();
        }
    }
    private void switchToMode(CameraMode cameraMode) {
        Log.d(TAG, "Current Mode:" + cameraMode.name());
        CameraMode previousMode = displayedMode;
        displayedMode = cameraMode;

        switch (cameraMode) {
            case VIDEO:
                currentState = new VideoModeState();
                break;
            case UNLIMITED:
            case RAWVIDEO:
                currentState = new UnlimitedModeState();
                break;
            case PHOTO:
            case MOTION:
                currentState = new PhotoMotionModeState();
                break;
            case NIGHT:
                currentState = new NightModeState();
                break;
        }


        /*
         * Clear RAW Video-only overlays before the destination still mode is
         * drawn. Without this pre-reset, Motion briefly makes the old
         * processing ring visible and the delayed safety cleanup removes it
         * about 360 ms later.
         */
        if (previousMode == CameraMode.RAWVIDEO
                && cameraMode != CameraMode.RAWVIDEO) {
            mCaptureProgressBar.animate().cancel();
            mCaptureProgressBar.setProgress(0);
            mCaptureProgressBar.setAlpha(0.0f);
            mCaptureProgressBar.clearAnimation();
            mCaptureProgressBar.invalidate();

            if (mProcessingProgressBar != null) {
                mProcessingProgressBar.animate().cancel();
                mProcessingProgressBar.setIndeterminate(false);
                mProcessingProgressBar.setProgress(0);
                mProcessingProgressBar.clearAnimation();
                mProcessingProgressBar.setVisibility(View.INVISIBLE);
                mProcessingProgressBar.invalidate();
            }

            if (mVideoRecordingInfo != null) {
                mVideoRecordingInfo.setText("");
                mVideoRecordingInfo.setVisibility(View.GONE);
                mVideoRecordingInfo.setAlpha(0.0f);
            }

            cameraFragment.clearTimerFrameCountForModeTransition();
        }

        currentState.reConfigureModeViews(cameraMode);

        if (cameraMode == CameraMode.RAWVIDEO
                && mVideoRecordingInfo != null) {
            mVideoRecordingInfo.setText("");
            mVideoRecordingInfo.setAlpha(1.0f);
            mVideoRecordingInfo.setVisibility(View.GONE);
        }

        if (!CaptureController.isProcessing) {
            resetCaptureProgressBar();
            if (mProcessingProgressBar != null) {
                mProcessingProgressBar.animate().cancel();
                mProcessingProgressBar.setIndeterminate(false);
                mProcessingProgressBar.setProgress(0);
                mProcessingProgressBar.clearAnimation();
                mProcessingProgressBar.setClickable(false);
                mProcessingProgressBar.setFocusable(false);
                mProcessingProgressBar.setVisibility(View.GONE);
            }
        }

        if (mShutterButton != null) {
            mShutterButton.setClickable(true);
            mShutterButton.setEnabled(true);
            mShutterButton.bringToFront();
        }

        if (uiEventsListener != null) uiEventsListener.onCameraModeChanged(cameraMode);

        /*
         * One next-loop safety pass catches a callback already queued by RAW
         * Video without leaving the spinner visible for the old 360 ms delay.
         */
        if (previousMode == CameraMode.RAWVIDEO
                && cameraMode != CameraMode.RAWVIDEO) {
            mCaptureProgressBar.post(() -> {
                mCaptureProgressBar.animate().cancel();
                mCaptureProgressBar.setProgress(0);
                mCaptureProgressBar.setAlpha(0.0f);
                mCaptureProgressBar.clearAnimation();

                if (mProcessingProgressBar != null) {
                    mProcessingProgressBar.animate().cancel();
                    mProcessingProgressBar.setIndeterminate(false);
                    mProcessingProgressBar.setProgress(0);
                    mProcessingProgressBar.clearAnimation();
                    mProcessingProgressBar.setVisibility(View.INVISIBLE);
                }

                if (mVideoRecordingInfo != null) {
                    mVideoRecordingInfo.setText("");
                    mVideoRecordingInfo.setVisibility(View.GONE);
                    mVideoRecordingInfo.setAlpha(0.0f);
                }

                cameraFragment.clearTimerFrameCountForModeTransition();
            });
        }
    }

    private void toggleConstraints(CameraMode mode) {
        if (cameraFragment.displayAspectRatio <= 16f / 9f) {
            ConstraintLayout.LayoutParams camera_containerLP =
                    (ConstraintLayout.LayoutParams) cameraFragment.cameraFragmentBinding
                            .textureHolder
                            .findViewById(R.id.camera_container)
                            .getLayoutParams();
            switch (mode) {
                case RAWVIDEO:
                case VIDEO:
                    camera_containerLP.topToTop = R.id.textureHolder;
                    camera_containerLP.topToBottom = -1;
                    break;
                case UNLIMITED:
                case PHOTO:
                case MOTION:
                case NIGHT:
                    camera_containerLP.topToTop = -1;
                    camera_containerLP.topToBottom = R.id.layout_topbar;
            }

        }
    }

    @Override
    public void refresh(boolean processing) {
        TunableInjector.inject(this);
        if (!enableQuadRes) {
            PreferenceKeys.setQuadBayer(false);
        }
        this.topbar.setQuadVisible(enableQuadRes);
        refreshFormatStatus();
        cameraFragment.cameraFragmentBinding.invalidateAll();
        currentState.reConfigureModeViews(CameraMode.valueOf(PreferenceKeys.getCameraModeOrdinal()));
        this.resetCaptureProgressBar();
        if (!processing) {
            this.activateShutterButton(true);
            this.setProcessingProgressBarIndeterminate(false);
            this.lockUIForBurst(false);
        }
    }

    @Override
    public void setProcessingProgressBarIndeterminate(boolean indeterminate) {
        this.mProcessingProgressBar.post(() -> {
            boolean show =
                    indeterminate
                            && CaptureController.isProcessing
                            && displayedMode != CameraMode.RAWVIDEO;
            this.mProcessingProgressBar.animate().cancel();
            this.mProcessingProgressBar.setIndeterminate(show);
            this.mProcessingProgressBar.setClickable(false);
            this.mProcessingProgressBar.setFocusable(false);
            this.mProcessingProgressBar.setVisibility(
                    show ? View.VISIBLE : View.GONE
            );
            if (!show) {
                this.mProcessingProgressBar.setProgress(0);
                this.mProcessingProgressBar.clearAnimation();
            }
        });
    }

    @Override
    public void incrementCaptureProgressBar(int step) {
        this.mCaptureProgressBar.post(() -> this.mCaptureProgressBar.incrementProgressBy(step));
    }

    @Override
    public void resetCaptureProgressBar() {
        this.mCaptureProgressBar.post(() -> {
            this.mCaptureProgressBar.animate().cancel();
            this.mCaptureProgressBar.setProgress(0);
            this.mCaptureProgressBar.setAlpha(0.0f);
            this.mCaptureProgressBar.setVisibility(View.INVISIBLE);
            this.mCaptureProgressBar.clearAnimation();

            if (cameraFragment.cameraFragmentBinding != null
                    && cameraFragment.cameraFragmentBinding.layoutViewfinder != null
                    && cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer != null) {
                cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer
                        .setVisibility(View.INVISIBLE);
            }
        });
    }

    @Override
    public void setCaptureProgressBarOpacity(float alpha) {
        this.mCaptureProgressBar.post(() -> {
            boolean visible = alpha > 0.0f;
            this.mCaptureProgressBar.setAlpha(alpha);
            this.mCaptureProgressBar.setVisibility(
                    visible ? View.VISIBLE : View.INVISIBLE
            );

            if (cameraFragment.cameraFragmentBinding != null
                    && cameraFragment.cameraFragmentBinding.layoutViewfinder != null
                    && cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer != null) {
                cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer
                        .setVisibility(visible ? View.VISIBLE : View.INVISIBLE);
            }
        });
    }

    @Override
    public void setCaptureProgressMax(int max) {
        this.mCaptureProgressBar.post(() -> this.mCaptureProgressBar.setMax(max));
    }

    @Override
    public void showFlashButton(boolean flashAvailable) {
        this.topbar.setFlashVisible(flashAvailable);
        cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.flash_entry_layout, flashAvailable ? View.VISIBLE : GONE);
    }

    @Override
    public void lockUIForBurst(boolean locked) {

        // Lock/unlock bottom bar buttons (except shutter button)
        if (this.bottombuttons != null) {
                this.bottombuttons.galleryImageButton.post(() -> this.bottombuttons.galleryImageButton.setEnabled(!locked));
            // Note: shutter button remains enabled for burst control
        }

        // Lock/unlock mode picker
        if (this.mModePicker != null) {
            this.mModePicker.post(() -> this.mModePicker.setEnabled(!locked));
        }

        // Lock/unlock aux buttons container - disable touch events
        if (cameraFragment.cameraFragmentBinding != null) {
            cameraFragment.cameraFragmentBinding.auxButtonsContainer.post(() -> {
                cameraFragment.cameraFragmentBinding.auxButtonsContainer.setEnabled(!locked);
                // Also set alpha to visually indicate disabled state
                cameraFragment.cameraFragmentBinding.auxButtonsContainer.setAlpha(locked ? 0.5f : 1.0f);
                cameraFragment.auxButtonsViewModel.setEnabled(!locked);
            });
        }

        // Lock/unlock settings bar - disable touch events and reduce alpha
        if (cameraFragment.cameraFragmentBinding != null) {
            cameraFragment.cameraFragmentBinding.settingsBar.post(() -> {
                cameraFragment.cameraFragmentBinding.settingsBar.setEnabled(!locked);
                cameraFragment.cameraFragmentBinding.settingsBar.setAlpha(locked ? 0.5f : 1.0f);
            });
        }

        // Lock/unlock manual mode console - disable swipe gestures
        if (cameraFragment.cameraFragmentBinding != null) {
            cameraFragment.cameraFragmentBinding.manualMode.post(() -> {
                cameraFragment.cameraFragmentBinding.manualMode.setEnabled(!locked);
                cameraFragment.cameraFragmentBinding.manualMode.setAlpha(locked ? 0.5f : 1.0f);
            });
        }

        // Lock/unlock touch focus by disabling the swipe controls
        if (cameraFragment.textureView != null) {
            // Disable touch events on the texture view to prevent focus/swipe during burst
            cameraFragment.textureView.post(() -> cameraFragment.textureView.setEnabled(!locked));
        }
    }

    @Override
    public void setCameraUIEventsListener(CameraUIEventsListener cameraUIEventsListener) {
        this.uiEventsListener = cameraUIEventsListener;
    }

    @Override
    @android.annotation.SuppressLint("DefaultLocale")
    public void updateVideoRecordingInfo(long elapsedMs, long estimatedBytes, long availableBytes) {
        if (mVideoRecordingInfo == null) return;
        long totalSeconds = elapsedMs / 1000;
        long minutes = totalSeconds / 60;
        long seconds = totalSeconds % 60;
        double estimatedGB = estimatedBytes / 1_073_741_824.0;
        double availableGB = availableBytes / 1_073_741_824.0;
        String text = String.format("%02d:%02d  %.2f/%.1f GB", minutes, seconds, estimatedGB, availableGB);
        mVideoRecordingInfo.post(() -> {
            boolean rawVideoActive =
                    displayedMode == CameraMode.RAWVIDEO
                            && cameraFragment.captureController != null
                            && (cameraFragment.captureController.onUnlimited
                                || cameraFragment.captureController.unlimitedStarted);
            if (rawVideoActive) {
                mVideoRecordingInfo.setText(text);
                mVideoRecordingInfo.setAlpha(1.0f);
                mVideoRecordingInfo.setVisibility(View.VISIBLE);
            } else {
                mVideoRecordingInfo.setText("");
                mVideoRecordingInfo.setAlpha(0.0f);
                mVideoRecordingInfo.setVisibility(View.GONE);
            }
        });
    }

    @Override
    public void setVideoRecordingInfoVisible(boolean visible) {
        if (mVideoRecordingInfo != null) {
            mVideoRecordingInfo.post(() -> {
                boolean allowVisible =
                        visible
                                && displayedMode == CameraMode.RAWVIDEO
                                && cameraFragment.captureController != null
                                && (cameraFragment.captureController.onUnlimited
                                    || cameraFragment.captureController.unlimitedStarted);
                mVideoRecordingInfo.setVisibility(
                        allowVisible ? View.VISIBLE : View.GONE
                );
                if (!allowVisible) {
                    mVideoRecordingInfo.setText("");
                    mVideoRecordingInfo.setAlpha(0.0f);
                } else {
                    mVideoRecordingInfo.setAlpha(1.0f);
                }
            });
        }


    }

    @Override
    public void destroy() {
        topbar = null;
        bottombuttons = null;
    }

    public class VideoModeState implements CameraModeState {
        @Override
        public void reConfigureModeViews(CameraMode mode) {
            resetCaptureProgressBar();
            topbar.setEisVisible(true);
            // cameraUIView.cameraFragmentBinding.textureHolder.setBackgroundResource(R.drawable.gradient_vector_video);
            topbar.setFpsVisible(true);
            topbar.setTimerVisible(false);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.fps_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.timer_entry_layout, View.GONE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.quad_entry_layout, enableQuadRes ? View.VISIBLE : View.GONE);
            applyVideoShutterStack(true);
            mShutterButton.setActivated(true);
            mShutterButton.setPressed(false);
            applyBottomGeometry(true);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer.setVisibility(View.VISIBLE);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar.setVisibility(View.VISIBLE);
            setVideoRecordingInfoVisible(false);
            // Set the dummy view's aspect ratio to 16:9
            if(cameraFragment.displayAspectRatio <= 16f / 9f)
                cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
            else {
                float avg = ((4f/3f) + (16f / 9f)) / 2f;
                cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio(String.valueOf(1.0f/avg));
                //cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("0.580");
            }
            cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackgroundResource(R.color.panel_transparency);
            cameraFragment.cameraFragmentBinding.getRoot().setBackgroundResource(R.drawable.gradient_vector_video);

            toggleConstraints(mode);
        }
    }

    //
    public class UnlimitedModeState implements CameraModeState {
        @Override
        public void reConfigureModeViews(CameraMode mode) {
            resetCaptureProgressBar();
            topbar.setFpsVisible(true);
            topbar.setTimerVisible(false);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.fps_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.timer_entry_layout, View.GONE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.quad_entry_layout, enableQuadRes ? View.VISIBLE : View.GONE);
            if (mode == CameraMode.RAWVIDEO) {
                applyVideoShutterStack(true);
                mShutterButton.setActivated(true);
                mShutterButton.setPressed(false);
                applyBottomGeometry(true);
            } else {
                /*
                 * Pro maps to CameraMode.UNLIMITED but visually remains a
                 * still-photo mode, so it keeps the shared white shutter.
                 */
                applyVideoShutterStack(false);
                mShutterButton.setBackgroundResource(R.drawable.roundbutton);
                applyBottomGeometry(false);
            }

            if (mode == CameraMode.RAWVIDEO) {
                cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer.setVisibility(View.GONE);
                cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar.setVisibility(View.GONE);
            } else {
                cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer.setVisibility(View.VISIBLE);
                cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar.setVisibility(View.VISIBLE);
                setVideoRecordingInfoVisible(false);
            }
            if(PhotonCamera.getSettings().aspect169 || mode == CameraMode.RAWVIDEO) {
                // Set the dummy view's aspect ratio to 16:9
                if(cameraFragment.displayAspectRatio <= 16f / 9f)
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                else {
                    float avg = ((4f/3f) + (16f / 9f)) / 2f;
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio(String.valueOf(1.0f/avg));
                    //cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("0.580");
                }
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackgroundResource(R.color.panel_transparency);
                cameraFragment.cameraFragmentBinding.getRoot().setBackgroundResource(R.drawable.gradient_vector_video);
            } else {
                cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackground(null);
                cameraFragment.cameraFragmentBinding.getRoot().setBackground(Utilities.resolveDrawable(cameraFragment.requireActivity(), R.attr.cameraFragmentBackground));
            }
            toggleConstraints(mode);
        }
    }

    //
    public class PhotoMotionModeState implements CameraModeState {
        @Override
        public void reConfigureModeViews(CameraMode mode) {
            resetCaptureProgressBar();
            topbar.setEisVisible(true);
            topbar.setFpsVisible(true);
            topbar.setTimerVisible(true);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer.setVisibility(View.VISIBLE);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar.setVisibility(View.VISIBLE);
            setVideoRecordingInfoVisible(false);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.eis_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.fps_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.timer_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.hdrx_entry_layout, View.GONE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.quad_entry_layout, enableQuadRes ? View.VISIBLE : View.GONE);
            applyVideoShutterStack(false);
            mShutterButton.setBackgroundResource(R.drawable.roundbutton);
            applyBottomGeometry(false);
            //cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackground(null);
            //cameraFragment.cameraFragmentBinding.getRoot().setBackground(Utilities.resolveDrawable(cameraFragment.requireActivity(), R.attr.cameraFragmentBackground));

            if(PhotonCamera.getSettings().aspect169) {
                // Set the dummy view's aspect ratio to 16:9
                if(cameraFragment.displayAspectRatio <= 16f / 9f)
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                else {
                    float avg = ((4f/3f) + (16f / 9f)) / 2f;
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio(String.valueOf(1.0f/avg));
                    //cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("0.580");
                }
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackgroundResource(R.color.panel_transparency);
                cameraFragment.cameraFragmentBinding.getRoot().setBackgroundResource(R.drawable.gradient_vector_video);
            } else {
                cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackground(null);
                cameraFragment.cameraFragmentBinding.getRoot().setBackground(Utilities.resolveDrawable(cameraFragment.requireActivity(), R.attr.cameraFragmentBackground));
            }

            toggleConstraints(mode);
        }
    }

    public class NightModeState implements CameraModeState {
        @Override
        public void reConfigureModeViews(CameraMode mode) {
            resetCaptureProgressBar();
            topbar.setEisVisible(false);
            topbar.setFpsVisible(true);
            topbar.setTimerVisible(true);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.frameTimer.setVisibility(View.VISIBLE);
            cameraFragment.cameraFragmentBinding.layoutViewfinder.captureProgressBar.setVisibility(View.VISIBLE);
            setVideoRecordingInfoVisible(false);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.eis_entry_layout, View.GONE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.fps_entry_layout, View.GONE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.timer_entry_layout, View.VISIBLE);
            cameraFragment.cameraFragmentBinding.settingsBar.setChildVisibility(R.id.quad_entry_layout, enableQuadRes ? View.VISIBLE : View.GONE);
            applyVideoShutterStack(false);
            mShutterButton.setBackgroundResource(R.drawable.roundbutton);
            applyBottomGeometry(false);
            if(PhotonCamera.getSettings().aspect169) {
                // Set the dummy view's aspect ratio to 16:9
                if(cameraFragment.displayAspectRatio <= 16f / 9f)
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                else {
                    float avg = ((4f/3f) + (16f / 9f)) / 2f;
                    cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio(String.valueOf(1.0f/avg));
                    //cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("0.580");
                }
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackgroundResource(R.color.panel_transparency);
                cameraFragment.cameraFragmentBinding.getRoot().setBackgroundResource(R.drawable.gradient_vector_video);
            } else {
                cameraFragment.cameraFragmentBinding.getUimodel().setDummyAspectRatio("3:4");
                cameraFragment.cameraFragmentBinding.layoutBottombar.layoutBottombar.setBackground(null);
                cameraFragment.cameraFragmentBinding.getRoot().setBackground(Utilities.resolveDrawable(cameraFragment.requireActivity(), R.attr.cameraFragmentBackground));
            }

            toggleConstraints(mode);
        }
    }

}

