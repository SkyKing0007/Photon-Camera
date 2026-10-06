package com.particlesdevs.photoncamera.control;

import android.graphics.Rect;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.os.Build;
import android.os.SystemClock;
import android.util.Range;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.ui.camera.CameraFragment;
import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData;
import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout;
import com.particlesdevs.photoncamera.util.Log;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Map;

/**
 * IRIS_26529_MANUAL_PHYSICAL_LENS_30X_OWNER
 *
 * Physical camera ownership changes only when the user explicitly presses a lens button.
 * Pinch zoom is local to that selected physical lens from 1x through 30x. Camera2 performs
 * only legal hardware crop and Iris supplies any residual digital zoom beyond the HAL limit.
 * The UI remains in global/equivalent zoom coordinates (optical anchor * local zoom), while
 * Motion/DNG keep the selected-lens-local zoom authority.
 *
 * This class never modifies Motion alignment, rejection, accumulation, exposure,
 * denoise, tone or sharpening.
 */
public final class IrisZoomController {
    private static final String TAG = "IrisZoomController";
    public static final float LOCAL_MAX_ZOOM = 30.0f;
    public static final float GLOBAL_MAX_ZOOM = 120.0f; // IRIS_26772_UNIVERSAL_GLOBAL_ZOOM_CEILING
    private static final long PREVIEW_APPLY_INTERVAL_MS = 24L;
    private static final Object STATE_LOCK = new Object();

    private static volatile boolean sInitialized = false;
    /* IRIS_26527_REQUESTED_VS_DISPLAYED_ZOOM
     * Requested zoom follows the fingers. Global/displayed zoom is the geometry actually safe
     * to show/capture on the route that has produced a proven result.
     */
    private static volatile float sRequestedGlobalZoom = 1.0f;
    private static volatile float sGlobalZoom = 1.0f;
    private static volatile float sOpticalAnchor = 1.0f;
    private static volatile float sHardwareLocalZoom = 1.0f;
    private static volatile float sResidualSoftwareZoom = 1.0f;
    private static volatile float sMinimumGlobalZoom = 1.0f;
    private static volatile float sMaximumGlobalZoom = LOCAL_MAX_ZOOM;
    /* IRIS_26526_TRANSACTIONAL_LENS_HANDOFF
     * sOwnerCameraId/sOpticalAnchor describe the camera that has produced a valid
     * result. Pending state is only a requested restart target until that result arrives.
     */
    private static volatile String sOwnerCameraId = null;
    private static volatile String sPendingOwnerCameraId = null;
    private static volatile float sPendingOpticalAnchor = 1.0f;
    private static volatile String[] sLensCameraIds = new String[0];
    private static volatile float[] sLensAnchors = new float[0];

    private final CameraFragment fragment;
    private final ArrayList<CameraLensData> backLenses = new ArrayList<>();
    private long lastPreviewApplyMs = 0L;

    public static final class ZoomSnapshot {
        public final float globalZoom;
        public final float opticalAnchor;
        public final float outputLocalZoom;
        public final float hardwareLocalZoom;
        public final float residualSoftwareZoom;
        public final float minimumGlobalZoom;
        public final float maximumGlobalZoom;
        public final String ownerCameraId;

        private ZoomSnapshot(float globalZoom, float opticalAnchor,
                             float hardwareLocalZoom, float residualSoftwareZoom,
                             float minimumGlobalZoom, float maximumGlobalZoom,
                             String ownerCameraId) {
            this.globalZoom = globalZoom;
            this.opticalAnchor = Math.max(0.01f, opticalAnchor);
            float requestedLocal = globalZoom / this.opticalAnchor;
            this.outputLocalZoom = Float.isFinite(requestedLocal)
                    ? clamp(requestedLocal, 1.0f, LOCAL_MAX_ZOOM) : 1.0f;
            this.hardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
            this.residualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
            this.minimumGlobalZoom = minimumGlobalZoom;
            this.maximumGlobalZoom = maximumGlobalZoom;
            this.ownerCameraId = ownerCameraId;
        }
    }

    public static final class CaptureZoomUpdate {
        public final float residualSoftwareZoom;
        public final boolean committedPending;
        public final String chainedPendingOwnerCameraId;
        public final boolean revealAllowed;
        public final boolean previewRefreshRequired;

        private CaptureZoomUpdate(float residualSoftwareZoom, boolean committedPending,
                                  String chainedPendingOwnerCameraId, boolean revealAllowed,
                                  boolean previewRefreshRequired) {
            this.residualSoftwareZoom = residualSoftwareZoom;
            this.committedPending = committedPending;
            this.chainedPendingOwnerCameraId = chainedPendingOwnerCameraId;
            this.revealAllowed = revealAllowed;
            this.previewRefreshRequired = previewRefreshRequired;
        }
    }

    public IrisZoomController(CameraFragment fragment) {
        this.fragment = fragment;
    }

    /** IRIS_26532_NEW_CAMERA_ACTIVITY_ONE_X
     * A genuinely new CameraActivity session (savedInstanceState == null) starts at 1x even if
     * Android kept the process alive after the previous activity was closed. Configuration/state
     * recreation with a non-null savedInstanceState keeps the live session instead.
     */
    public static void resetForNewCameraActivitySession() {
        synchronized (STATE_LOCK) {
            sInitialized = false;
            sRequestedGlobalZoom = 1.0f;
            sGlobalZoom = 1.0f;
            sOpticalAnchor = 1.0f;
            sHardwareLocalZoom = 1.0f;
            sResidualSoftwareZoom = 1.0f;
            sMinimumGlobalZoom = 1.0f;
            sMaximumGlobalZoom = LOCAL_MAX_ZOOM;
            sOwnerCameraId = null;
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = 1.0f;
        }
    }

    /** IRIS_26562_FOREGROUND_ONE_X_OWNER
     * A true application background/foreground boundary gets the same strict physical 1x reset as
     * a new CameraActivity. The subsequent inventory pass persists the rear lens closest to 1x
     * before CaptureController resolves its route.
     */
    public static void resetForForegroundSession() {
        resetForNewCameraActivitySession();
    }

    public void onLensInventoryReady() {
        refreshInventory();
        if (backLenses.isEmpty()) return;
        String freshProcessCameraId = null;
        synchronized (STATE_LOCK) {
            CameraLensData selected;
            if (!sInitialized) {
                /* IRIS_26532_FRESH_PROCESS_ONE_X
                 * Static zoom ownership dies with the app process. On the first inventory of a
                 * new process, ignore persisted camera/zoom state and start from the physical
                 * rear lens whose optical anchor is closest to 1x. Same-process recreation keeps
                 * the live owner below.
                 */
                selected = findClosestToOne();
                freshProcessCameraId = selected.getCameraId();
            } else {
                selected = findLens(PreferenceKeys.getCameraID());
                if (selected == null || selected.getFacing() != CameraCharacteristics.LENS_FACING_BACK) {
                    selected = findClosestToOne();
                }
            }
            CameraLensData owner = findLens(sOwnerCameraId);
            if (!sInitialized || owner == null) {
                sOpticalAnchor = safeAnchor(selected);
                sMinimumGlobalZoom = sOpticalAnchor;
                sMaximumGlobalZoom = safeGlobalMaximum(sOpticalAnchor);
                sGlobalZoom = sOpticalAnchor;
                sRequestedGlobalZoom = sGlobalZoom;
                sOwnerCameraId = selected.getCameraId();
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
                sInitialized = true;
            } else {
                sOpticalAnchor = safeAnchor(owner);
                sMinimumGlobalZoom = sOpticalAnchor;
                sMaximumGlobalZoom = safeGlobalMaximum(sOpticalAnchor);
                sGlobalZoom = clamp(sGlobalZoom, sMinimumGlobalZoom, sMaximumGlobalZoom);
                sRequestedGlobalZoom = clamp(sRequestedGlobalZoom,
                        sMinimumGlobalZoom, sMaximumGlobalZoom);
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
            }
        }
        if (freshProcessCameraId != null) {
            PreferenceKeys.setCameraID(freshProcessCameraId);
            CameraFragment.sActiveBackCamId = freshProcessCameraId;
            Log.i(TAG, "IRIS_26532_FRESH_PROCESS_ONE_X cameraId=" + freshProcessCameraId
                    + " globalZoom=" + getGlobalZoom() + " localZoom=1.0");
        }
        updateButtonUi();
    }

    public void onLensButtonSelected(String cameraId) {
        refreshInventory();
        CameraLensData lens = findLens(cameraId);
        if (lens == null || lens.getFacing() != CameraCharacteristics.LENS_FACING_BACK) return;
        synchronized (STATE_LOCK) {
            sOpticalAnchor = safeAnchor(lens);
            sMinimumGlobalZoom = sOpticalAnchor;
            sMaximumGlobalZoom = safeGlobalMaximum(sOpticalAnchor);
            sGlobalZoom = sOpticalAnchor;
            sRequestedGlobalZoom = sOpticalAnchor;
            sOwnerCameraId = lens.getCameraId();
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = sOpticalAnchor;
            sHardwareLocalZoom = 1.0f;
            sResidualSoftwareZoom = 1.0f;
            sInitialized = true;
        }
        Log.i(TAG, "IRIS_26529_MANUAL_LENS_SELECTED cameraId=" + cameraId
                + " opticalAnchor=" + getOpticalAnchor()
                + " globalDisplayed=" + getGlobalZoom()
                + " localZoom=1.0");
        updateButtonUi();
    }

    public static boolean isContinuousZoomEnabledForCurrentMode() {
        return PhotonCamera.getSettings().selectedMode == CameraMode.MOTION;
    }

    public void onPinchScale(float scaleFactor) {
        if (!isContinuousZoomEnabledForCurrentMode()) return;
        if (!Float.isFinite(scaleFactor) || scaleFactor <= 0.0f) return;
        refreshInventory();
        if (backLenses.isEmpty()) return;
        synchronized (STATE_LOCK) {
            float anchor = Math.max(0.05f, sOpticalAnchor);
            float currentLocal = sRequestedGlobalZoom / anchor;
            if (!Float.isFinite(currentLocal)) currentLocal = 1.0f;
            sMinimumGlobalZoom = anchor;
            sMaximumGlobalZoom = safeGlobalMaximum(anchor);
            float localCeiling = Math.min(LOCAL_MAX_ZOOM, sMaximumGlobalZoom / anchor);
            float nextLocal = clamp(currentLocal * scaleFactor, 1.0f, localCeiling);
            sRequestedGlobalZoom = clamp(anchor * nextLocal, anchor, sMaximumGlobalZoom);
            sGlobalZoom = sRequestedGlobalZoom;
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = anchor;
            sInitialized = true;
        }
        updateButtonUi();
        long now = SystemClock.uptimeMillis();
        if (now - lastPreviewApplyMs >= PREVIEW_APPLY_INTERVAL_MS) {
            applyPreviewNow();
            lastPreviewApplyMs = now;
        }
    }

    public void finishScale() {
        if (!isContinuousZoomEnabledForCurrentMode()) return;
        updateButtonUi();
        applyPreviewNow();
        lastPreviewApplyMs = SystemClock.uptimeMillis();
    }

    private void applyPreviewNow() {
        CaptureController controller = fragment.captureController;
        if (controller != null) controller.applyIrisZoomNow();
    }

    private void updateButtonUi() {
        if (fragment.activity == null) return;
        final float z = getRequestedGlobalZoom();
        final String owner = getOwnerCameraId();
        fragment.activity.runOnUiThread(() -> {
            AuxButtonsLayout layout = fragment.findViewById(R.id.aux_buttons_container);
            if (layout != null) layout.setLiveZoomState(z, owner);
        });
    }

    private void refreshInventory() {
        Map<String, CameraLensData> map = fragment.mCameraLensDataMap;
        if (map == null || map.isEmpty()) return;
        backLenses.clear();
        for (CameraLensData lens : map.values()) {
            if (lens != null
                    && lens.getFacing() == CameraCharacteristics.LENS_FACING_BACK
                    && Float.isFinite(lens.getZoomFactor())
                    && lens.getZoomFactor() > 0.05f) {
                backLenses.add(lens);
            }
        }
        backLenses.sort(Comparator.comparingDouble(CameraLensData::getZoomFactor));
        if (backLenses.isEmpty()) return;
        synchronized (STATE_LOCK) {
            sLensCameraIds = new String[backLenses.size()];
            sLensAnchors = new float[backLenses.size()];
            for (int i = 0; i < backLenses.size(); ++i) {
                sLensCameraIds[i] = backLenses.get(i).getCameraId();
                sLensAnchors[i] = safeAnchor(backLenses.get(i));
            }
            CameraLensData owner = findLens(sOwnerCameraId);
            if (owner != null) {
                float anchor = safeAnchor(owner);
                sMinimumGlobalZoom = anchor;
                sMaximumGlobalZoom = safeGlobalMaximum(anchor);
                sGlobalZoom = clamp(sGlobalZoom, sMinimumGlobalZoom, sMaximumGlobalZoom);
                sRequestedGlobalZoom = clamp(sRequestedGlobalZoom,
                        sMinimumGlobalZoom, sMaximumGlobalZoom);
            }
        }
    }

    /* IRIS_26529_NO_PINCH_PHYSICAL_HANDOFF: physical lens ownership is button-only. */

    private CameraLensData findLens(String cameraId) {
        if (cameraId == null) return null;
        for (CameraLensData lens : backLenses) {
            if (cameraId.equals(lens.getCameraId())) return lens;
        }
        return null;
    }

    private CameraLensData findClosestToOne() {
        CameraLensData best = backLenses.get(0);
        float bestDistance = Math.abs(safeAnchor(best) - 1.0f);
        for (CameraLensData lens : backLenses) {
            float distance = Math.abs(safeAnchor(lens) - 1.0f);
            if (distance < bestDistance) {
                best = lens;
                bestDistance = distance;
            }
        }
        return best;
    }

    private static float safeAnchor(CameraLensData lens) {
        return lens == null ? 1.0f : Math.max(0.05f, lens.getZoomFactor());
    }

    private static float safeGlobalMaximum(float opticalAnchor) {
        float anchor = Float.isFinite(opticalAnchor) ? Math.max(0.05f, opticalAnchor) : 1.0f;
        float maximum = anchor * LOCAL_MAX_ZOOM;
        if (!Float.isFinite(maximum)) maximum = LOCAL_MAX_ZOOM;
        return Math.min(maximum, GLOBAL_MAX_ZOOM);
    }

    private static float clamp(float v, float lo, float hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    /**
     * IRIS_26526_SINGLE_PREVIEW_GEOMETRY_AUTHORITY
     * Camera2 owns all live preview geometry inside its advertised zoom range.
     * Software residual is derived only from a static capability clamp; it never
     * chases asynchronous CaptureResult metadata.
     */
    public static float applyToRequest(CaptureRequest.Builder builder,
                                       CameraCharacteristics characteristics,
                                       String activeCameraId) {
        if (builder == null || characteristics == null) return 1.0f;
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        boolean rear = facing != null && facing == CameraCharacteristics.LENS_FACING_BACK;
        final CameraMode activeMode = PhotonCamera.getSettings().selectedMode;
        boolean motionZoom = isContinuousZoomEnabledForCurrentMode();
        final boolean universalNaturalOneXMode = activeMode == CameraMode.MOTION
                || activeMode == CameraMode.NIGHT;
        float localZoom = 1.0f;
        boolean ownsRequest;
        synchronized (STATE_LOCK) {
            if (!motionZoom) {
                sGlobalZoom = sOpticalAnchor;
                sRequestedGlobalZoom = sOpticalAnchor;
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }
            ownsRequest = motionZoom && rear && sInitialized
                    && sOwnerCameraId != null && sOwnerCameraId.equals(activeCameraId);
            if (ownsRequest) {
                float requested = sGlobalZoom / Math.max(0.01f, sOpticalAnchor);
                localZoom = Float.isFinite(requested)
                        ? clamp(requested, 1.0f, LOCAL_MAX_ZOOM) : 1.0f;
            }
        }

        float hardwareZoom = 1.0f;
        float supportedHardwareMax = 1.0f;
        boolean hardwareApplied = false;
        final boolean naturalOneX = universalNaturalOneXMode
                && (!ownsRequest || localZoom <= 1.0001f);
        if (naturalOneX) {
            // IRIS_26556_26507_NATURAL_ONE_X: do not issue a redundant 1x zoom command or
            // full-array crop. A freshly selected camera/lens starts at its own uncropped native
            // field of view. This also clears stale keys if the same builder previously carried
            // Motion zoom state before switching to Night or back to local 1x.
            try { builder.set(CaptureRequest.CONTROL_ZOOM_RATIO, null); }
            catch (Throwable ignored) {}
            try { builder.set(CaptureRequest.SCALER_CROP_REGION, null); }
            catch (Throwable ignored) {}
            synchronized (STATE_LOCK) {
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }
            Log.i(TAG, "IRIS_26556_NATURAL_ONE_X mode=" + activeMode
                    + " activeCameraId=" + activeCameraId
                    + " opticalAnchor=" + getOpticalAnchor()
                    + " zoomRatioKey=false cropRegionKey=false");
            return 1.0f;
        }
        Rect activeArray = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        boolean validActiveArray = activeArray != null
                && activeArray.width() >= 2 && activeArray.height() >= 2;

        if (ownsRequest && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Range<Float> range = characteristics.get(
                        CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE);
                Float lower = range == null ? null : range.getLower();
                Float upper = range == null ? null : range.getUpper();
                if (lower != null && upper != null
                        && Float.isFinite(lower) && Float.isFinite(upper)
                        && lower > 0.0f && lower <= 1.0f && upper >= 1.0f) {
                    supportedHardwareMax = Math.max(1.0f, upper);
                    float target = clamp(localZoom, 1.0f, supportedHardwareMax);
                    builder.set(CaptureRequest.CONTROL_ZOOM_RATIO, target);
                    if (validActiveArray) {
                        builder.set(CaptureRequest.SCALER_CROP_REGION, new Rect(activeArray));
                    }
                    hardwareZoom = target;
                    hardwareApplied = true;
                }
            } catch (Throwable t) {
                hardwareZoom = 1.0f;
                hardwareApplied = false;
                Log.w(TAG, "IRIS_26529_CONTROL_ZOOM_RATIO_FALLBACK "
                        + t.getClass().getSimpleName());
            }
        }

        if (ownsRequest && !hardwareApplied) {
            try {
                Float maxDigital = characteristics.get(
                        CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
                supportedHardwareMax = maxDigital != null && Float.isFinite(maxDigital)
                        && maxDigital >= 1.0f ? maxDigital : 1.0f;
                float target = clamp(localZoom, 1.0f, supportedHardwareMax);
                if (validActiveArray && target > 1.0f) {
                    int cropW = Math.max(2, Math.round(activeArray.width() / target));
                    int cropH = Math.max(2, Math.round(activeArray.height() / target));
                    cropW = Math.min(activeArray.width(), cropW);
                    cropH = Math.min(activeArray.height(), cropH);
                    if (cropW > 2) cropW &= ~1;
                    if (cropH > 2) cropH &= ~1;
                    int left = activeArray.left + (activeArray.width() - cropW) / 2;
                    int top = activeArray.top + (activeArray.height() - cropH) / 2;
                    Rect crop = new Rect(left, top, left + cropW, top + cropH);
                    if (crop.width() >= 2 && crop.height() >= 2
                            && activeArray.contains(crop)) {
                        builder.set(CaptureRequest.SCALER_CROP_REGION, crop);
                        hardwareZoom = target;
                        hardwareApplied = true;
                    }
                } else {
                    if (validActiveArray) {
                        builder.set(CaptureRequest.SCALER_CROP_REGION, new Rect(activeArray));
                    }
                    hardwareZoom = 1.0f;
                    hardwareApplied = true;
                }
            } catch (Throwable t) {
                hardwareZoom = 1.0f;
                hardwareApplied = false;
                Log.w(TAG, "IRIS_26529_SCALER_CROP_FALLBACK "
                        + t.getClass().getSimpleName());
            }
        }

        if (!ownsRequest) hardwareZoom = 1.0f;
        if (!Float.isFinite(hardwareZoom) || hardwareZoom < 1.0f) hardwareZoom = 1.0f;
        float residual = ownsRequest
                ? clamp(localZoom / hardwareZoom, 1.0f, LOCAL_MAX_ZOOM) : 1.0f;
        synchronized (STATE_LOCK) {
            if (ownsRequest) {
                sHardwareLocalZoom = hardwareZoom;
                sResidualSoftwareZoom = residual;
            } else if (!rear) {
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }
        }
        if (ownsRequest) {
            Log.d(TAG, "IRIS_26529_SAFE_30X_REQUEST"
                    + " activeCameraId=" + activeCameraId
                    + " opticalAnchor=" + getOpticalAnchor()
                    + " globalEquivalent=" + getGlobalZoom()
                    + " localZoom=" + localZoom
                    + " hardwareApplied=" + hardwareApplied
                    + " hardwareZoom=" + hardwareZoom
                    + " hardwareMax=" + supportedHardwareMax
                    + " residualSoftwareZoom=" + residual);
        }
        return residual;
    }

    /* IRIS_26526_HAL_TELEMETRY_ONLY
     * CaptureResult may update actual-HAL telemetry and commit a pending physical
     * camera, but it must never drive the live software preview crop.
     */
    public static CaptureZoomUpdate updateFromCaptureResult(
            CaptureResult result, CameraCharacteristics characteristics, String activeCameraId) {
        if (result == null || characteristics == null
                || !isContinuousZoomEnabledForCurrentMode() || activeCameraId == null) {
            return new CaptureZoomUpdate(getResidualSoftwareZoom(), false, null, false, false);
        }
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing == null || facing != CameraCharacteristics.LENS_FACING_BACK) {
            return new CaptureZoomUpdate(1.0f, false, null, false, false);
        }
        float actualHardware = 1.0f;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Float zoom = result.get(CaptureResult.CONTROL_ZOOM_RATIO);
                if (zoom != null && Float.isFinite(zoom) && zoom > 0.0f) {
                    actualHardware = Math.max(actualHardware, zoom);
                }
            } catch (Throwable ignored) {}
        }
        Rect active = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        Rect crop = null;
        try { crop = result.get(CaptureResult.SCALER_CROP_REGION); } catch (Throwable ignored) {}
        if (active != null && crop != null && active.width() > 0 && active.height() > 0
                && crop.width() > 0 && crop.height() > 0) {
            float cropZoomX = active.width() / (float) crop.width();
            float cropZoomY = active.height() / (float) crop.height();
            float cropZoom = Math.max(1.0f, Math.min(cropZoomX, cropZoomY));
            if (Float.isFinite(cropZoom)) actualHardware = Math.max(actualHardware, cropZoom);
        }
        float residual;
        boolean ownsCurrent;
        synchronized (STATE_LOCK) {
            ownsCurrent = sOwnerCameraId != null && sOwnerCameraId.equals(activeCameraId);
            if (ownsCurrent && Float.isFinite(actualHardware)) {
                sHardwareLocalZoom = Math.max(1.0f, actualHardware);
            }
            residual = sResidualSoftwareZoom;
        }
        if (ownsCurrent) {
            Log.d(TAG, "IRIS_26529_HAL_TELEMETRY_ONLY"
                    + " routeOwner=" + activeCameraId
                    + " globalEquivalent=" + getGlobalZoom()
                    + " opticalAnchor=" + getOpticalAnchor()
                    + " actualHardwareZoom=" + actualHardware
                    + " residualSoftwareZoom=" + residual
                    + " physicalOwnerChangedByResult=false"
                    + " crop=" + crop);
        }
        return new CaptureZoomUpdate(residual, false, null, false, false);
    }

    public static void abortPendingHandoff(String reason) {
        synchronized (STATE_LOCK) {
            Log.w(TAG, "IRIS_26529_CLEAR_STALE_HANDOFF reason=" + reason
                    + " owner=" + sOwnerCameraId
                    + " pending=" + sPendingOwnerCameraId
                    + " globalEquivalent=" + sGlobalZoom);
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = sOpticalAnchor;
        }
    }

    public static ZoomSnapshot snapshot() {
        synchronized (STATE_LOCK) {
            return new ZoomSnapshot(sGlobalZoom, sOpticalAnchor,
                    sHardwareLocalZoom, sResidualSoftwareZoom,
                    sMinimumGlobalZoom, sMaximumGlobalZoom, sOwnerCameraId);
        }
    }

    public static boolean isInitialized() { return sInitialized; }
    public static float getRequestedGlobalZoom() { return sRequestedGlobalZoom; }
    public static float getGlobalZoom() { return sGlobalZoom; }
    public static float getOpticalAnchor() { return sOpticalAnchor; }
    public static float getResidualSoftwareZoom() { return sResidualSoftwareZoom; }
    public static float getMaximumGlobalZoom() { return sMaximumGlobalZoom; }
    public static String getOwnerCameraId() { return sOwnerCameraId; }
}
