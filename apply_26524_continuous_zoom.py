#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, re
from pathlib import Path

SWIPE='app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java'
ZOOM='app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java'
TOUCH='app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java'
AUX='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java'
UI='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'
FRAGMENT='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
BATCH='app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
PARAMS='app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'
GLPREVIEW='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java'
RENDERER='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
PREVIEW_FS='app/src/main/assets/shaders/preview/main_fs.glsl'
MOTION_RENDER_JAVA='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
MOTION_RENDER_GLSL='app/src/main/assets/shaders/motionv2/render.glsl'
GAINMAP_GLSL='app/src/main/assets/shaders/motionv2/gainmap.glsl'

CHANGED={
    SWIPE,ZOOM,TOUCH,AUX,UI,FRAGMENT,CAPTURE,BATCH,SAVER,HDRX,PARAMS,
    GLPREVIEW,RENDERER,PREVIEW_FS,MOTION_RENDER_JAVA,MOTION_RENDER_GLSL,GAINMAP_GLSL
}

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def one(s:str, old:str, new:str, label:str)->str:
    n=s.count(old)
    if n!=1:
        raise AssertionError(f'{label}: anchor count={n}, expected=1')
    return s.replace(old,new,1)

ZOOM_SOURCE = r'''package com.particlesdevs.photoncamera.control;

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
 * IRIS_26524_CONTINUOUS_CROSSLENS_ZOOM_OWNER
 *
 * One global rear-camera zoom coordinate. Physical lenses are optical anchors;
 * Camera2 performs as much local crop as the active camera supports and Iris'
 * preview/final Motion renderer supplies only the residual beyond that limit.
 *
 * This class never modifies Motion alignment, rejection, accumulation, exposure,
 * denoise, tone or sharpening.
 */
public final class IrisZoomController {
    private static final String TAG = "IrisZoomController";
    public static final float TELE_MAX_GLOBAL_ZOOM = 50.0f;
    public static final float NO_TELE_MAX_GLOBAL_ZOOM = 20.0f;
    private static final float TELE_DETECTION_FACTOR = 1.50f;
    private static final long PREVIEW_APPLY_INTERVAL_MS = 24L;
    private static final Object STATE_LOCK = new Object();

    private static volatile boolean sInitialized = false;
    private static volatile float sGlobalZoom = 1.0f;
    private static volatile float sOpticalAnchor = 1.0f;
    private static volatile float sHardwareLocalZoom = 1.0f;
    private static volatile float sResidualSoftwareZoom = 1.0f;
    private static volatile float sMinimumGlobalZoom = 1.0f;
    private static volatile float sMaximumGlobalZoom = NO_TELE_MAX_GLOBAL_ZOOM;
    private static volatile String sOwnerCameraId = null;

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
            this.outputLocalZoom = Math.max(1.0f, globalZoom / this.opticalAnchor);
            this.hardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
            this.residualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
            this.minimumGlobalZoom = minimumGlobalZoom;
            this.maximumGlobalZoom = maximumGlobalZoom;
            this.ownerCameraId = ownerCameraId;
        }
    }

    public IrisZoomController(CameraFragment fragment) {
        this.fragment = fragment;
    }

    public void onLensInventoryReady() {
        refreshInventory();
        if (backLenses.isEmpty()) return;
        synchronized (STATE_LOCK) {
            CameraLensData selected = findLens(PreferenceKeys.getCameraID());
            if (selected == null || selected.getFacing() != CameraCharacteristics.LENS_FACING_BACK) {
                selected = findClosestToOne();
            }
            if (!sInitialized || findLens(sOwnerCameraId) == null) {
                sGlobalZoom = clamp(selected.getZoomFactor(),
                        sMinimumGlobalZoom, sMaximumGlobalZoom);
                CameraLensData owner = ownerFor(sGlobalZoom);
                sOwnerCameraId = owner.getCameraId();
                sOpticalAnchor = safeAnchor(owner);
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
                sInitialized = true;
            } else {
                CameraLensData owner = ownerFor(sGlobalZoom);
                sOwnerCameraId = owner.getCameraId();
                sOpticalAnchor = safeAnchor(owner);
            }
        }
        updateButtonUi();
    }

    public void onLensButtonSelected(String cameraId) {
        refreshInventory();
        CameraLensData lens = findLens(cameraId);
        if (lens == null || lens.getFacing() != CameraCharacteristics.LENS_FACING_BACK) {
            return;
        }
        synchronized (STATE_LOCK) {
            sGlobalZoom = clamp(safeAnchor(lens), sMinimumGlobalZoom, sMaximumGlobalZoom);
            sOpticalAnchor = safeAnchor(lens);
            sOwnerCameraId = lens.getCameraId();
            sHardwareLocalZoom = 1.0f;
            sResidualSoftwareZoom = 1.0f;
            sInitialized = true;
        }
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

        String oldOwner;
        String newOwner;
        synchronized (STATE_LOCK) {
            oldOwner = sOwnerCameraId;
            float requested = clamp(sGlobalZoom * scaleFactor,
                    sMinimumGlobalZoom, sMaximumGlobalZoom);
            CameraLensData owner = ownerFor(requested);
            sGlobalZoom = requested;
            sOwnerCameraId = owner.getCameraId();
            sOpticalAnchor = safeAnchor(owner);
            sInitialized = true;
            newOwner = sOwnerCameraId;
        }

        updateButtonUi();

        if (newOwner != null && !newOwner.equals(PreferenceKeys.getCameraID())) {
            PreferenceKeys.setCameraID(newOwner);
            if (fragment.auxButtonsViewModel != null) {
                fragment.auxButtonsViewModel.setActiveId(newOwner);
            }
            CaptureController controller = fragment.captureController;
            if (controller != null) {
                Log.i(TAG, "IRIS_26524_LENS_HANDOFF oldOwner=" + oldOwner
                        + " newOwner=" + newOwner
                        + " globalZoom=" + getGlobalZoom()
                        + " opticalAnchor=" + getOpticalAnchor());
                controller.restartCamera();
            }
            lastPreviewApplyMs = SystemClock.uptimeMillis();
            return;
        }

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
        final float z = getGlobalZoom();
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

        float minimum = safeAnchor(backLenses.get(0));
        boolean tele = false;
        for (CameraLensData lens : backLenses) {
            if (safeAnchor(lens) >= TELE_DETECTION_FACTOR) {
                tele = true;
                break;
            }
        }
        synchronized (STATE_LOCK) {
            sMinimumGlobalZoom = minimum;
            sMaximumGlobalZoom = tele ? TELE_MAX_GLOBAL_ZOOM : NO_TELE_MAX_GLOBAL_ZOOM;
            sGlobalZoom = clamp(sGlobalZoom, sMinimumGlobalZoom, sMaximumGlobalZoom);
        }
    }

    private CameraLensData ownerFor(float globalZoom) {
        CameraLensData owner = backLenses.get(0);
        for (CameraLensData lens : backLenses) {
            if (safeAnchor(lens) <= globalZoom + 0.0005f) owner = lens;
            else break;
        }
        return owner;
    }

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

    private static float clamp(float v, float lo, float hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    public static float applyToRequest(CaptureRequest.Builder builder,
                                       CameraCharacteristics characteristics,
                                       String activeCameraId) {
        if (builder == null || characteristics == null) return 1.0f;

        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        boolean rear = facing != null && facing == CameraCharacteristics.LENS_FACING_BACK;
        boolean motionZoom = isContinuousZoomEnabledForCurrentMode();
        float localZoom;
        synchronized (STATE_LOCK) {
            if (!motionZoom) {
                // Do not let a previous Motion digital zoom leak into PHOTO/NIGHT/VIDEO.
                sGlobalZoom = sOpticalAnchor;
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }
            boolean ownsActive = motionZoom && rear && sInitialized && sOwnerCameraId != null
                    && sOwnerCameraId.equals(activeCameraId);
            localZoom = ownsActive
                    ? Math.max(1.0f, sGlobalZoom / Math.max(0.01f, sOpticalAnchor))
                    : 1.0f;
        }

        float hardwareZoom = 1.0f;
        boolean usedZoomRatio = false;
        Rect activeArray = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Range<Float> range = characteristics.get(
                        CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE);
                if (range != null && range.getUpper() != null
                        && range.getUpper() >= 1.0f) {
                    hardwareZoom = clamp(localZoom, 1.0f, range.getUpper());
                    builder.set(CaptureRequest.CONTROL_ZOOM_RATIO, hardwareZoom);
                    if (activeArray != null) {
                        builder.set(CaptureRequest.SCALER_CROP_REGION,
                                new Rect(activeArray));
                    }
                    usedZoomRatio = true;
                }
            } catch (Throwable t) {
                Log.w(TAG, "CONTROL_ZOOM_RATIO skipped: "
                        + t.getClass().getSimpleName());
            }
        }

        if (!usedZoomRatio) {
            Float maxDigital = characteristics.get(
                    CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
            float maximum = maxDigital == null ? 1.0f : Math.max(1.0f, maxDigital);
            hardwareZoom = clamp(localZoom, 1.0f, maximum);
            if (activeArray != null) {
                int cropW = Math.max(2, Math.round(activeArray.width() / hardwareZoom));
                int cropH = Math.max(2, Math.round(activeArray.height() / hardwareZoom));
                cropW = Math.min(activeArray.width(), cropW);
                cropH = Math.min(activeArray.height(), cropH);
                if (cropW > 2) cropW &= ~1;
                if (cropH > 2) cropH &= ~1;
                int left = activeArray.left + (activeArray.width() - cropW) / 2;
                int top = activeArray.top + (activeArray.height() - cropH) / 2;
                builder.set(CaptureRequest.SCALER_CROP_REGION,
                        new Rect(left, top, left + cropW, top + cropH));
            }
        }

        float residual = Math.max(1.0f, localZoom / Math.max(1.0f, hardwareZoom));
        synchronized (STATE_LOCK) {
            boolean ownsActive = rear && sOwnerCameraId != null
                    && sOwnerCameraId.equals(activeCameraId);
            if (ownsActive) {
                sHardwareLocalZoom = hardwareZoom;
                sResidualSoftwareZoom = residual;
            } else if (!rear) {
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }
        }
        return residual;
    }

    /* IRIS_26524_ACTUAL_HAL_ZOOM_RECONCILIATION
     * Reconcile the request with the latest Camera2 result. Physical-camera
     * results may report zoom through SCALER_CROP_REGION even when
     * CONTROL_ZOOM_RATIO is 1.0.
     */
    public static float updateFromCaptureResult(CaptureResult result,
                                                CameraCharacteristics characteristics,
                                                String activeCameraId) {
        if (result == null || characteristics == null
                || !isContinuousZoomEnabledForCurrentMode()) {
            return 1.0f;
        }
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing == null || facing != CameraCharacteristics.LENS_FACING_BACK) {
            return 1.0f;
        }

        float desiredLocal;
        synchronized (STATE_LOCK) {
            if (!sInitialized || sOwnerCameraId == null
                    || !sOwnerCameraId.equals(activeCameraId)) {
                return 1.0f;
            }
            desiredLocal = Math.max(1.0f,
                    sGlobalZoom / Math.max(0.01f, sOpticalAnchor));
        }

        float actualHardware = 1.0f;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Float z = result.get(CaptureResult.CONTROL_ZOOM_RATIO);
                if (z != null && Float.isFinite(z) && z > 0.0f) {
                    actualHardware = Math.max(actualHardware, z);
                }
            } catch (Throwable ignored) {}
        }

        Rect active = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        Rect crop = null;
        try {
            crop = result.get(CaptureResult.SCALER_CROP_REGION);
        } catch (Throwable ignored) {}
        if (active != null && crop != null && crop.width() > 0 && crop.height() > 0) {
            float cropZoomX = active.width() / (float) crop.width();
            float cropZoomY = active.height() / (float) crop.height();
            float cropZoom = Math.max(1.0f, Math.min(cropZoomX, cropZoomY));
            actualHardware = Math.max(actualHardware, cropZoom);
        }

        actualHardware = Math.max(1.0f, Math.min(desiredLocal, actualHardware));
        float residual = Math.max(1.0f,
                desiredLocal / Math.max(1.0f, actualHardware));

        float oldHardware;
        float oldResidual;
        synchronized (STATE_LOCK) {
            oldHardware = sHardwareLocalZoom;
            oldResidual = sResidualSoftwareZoom;
            sHardwareLocalZoom = actualHardware;
            sResidualSoftwareZoom = residual;
        }
        if (Math.abs(oldHardware - actualHardware) > 0.01f
                || Math.abs(oldResidual - residual) > 0.01f) {
            Log.i(TAG, "IRIS_26524_ACTUAL_HAL_ZOOM"
                    + " activeCameraId=" + activeCameraId
                    + " globalZoom=" + getGlobalZoom()
                    + " opticalAnchor=" + getOpticalAnchor()
                    + " desiredLocalZoom=" + desiredLocal
                    + " actualHardwareZoom=" + actualHardware
                    + " residualSoftwareZoom=" + residual
                    + " crop=" + crop);
        }
        return residual;
    }

    public static ZoomSnapshot snapshot() {
        synchronized (STATE_LOCK) {
            return new ZoomSnapshot(sGlobalZoom, sOpticalAnchor,
                    sHardwareLocalZoom, sResidualSoftwareZoom,
                    sMinimumGlobalZoom, sMaximumGlobalZoom, sOwnerCameraId);
        }
    }

    public static boolean isInitialized() { return sInitialized; }
    public static float getGlobalZoom() { return sGlobalZoom; }
    public static float getOpticalAnchor() { return sOpticalAnchor; }
    public static float getResidualSoftwareZoom() { return sResidualSoftwareZoom; }
    public static float getMaximumGlobalZoom() { return sMaximumGlobalZoom; }
    public static String getOwnerCameraId() { return sOwnerCameraId; }
}
'''

def swipe_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_PINCH_ZOOM_GESTURE_OWNER' in s:
        raise AssertionError('26524 Swipe transform already present')
    if 'IRIS_26523_ACTUAL_PREVIEW_TOUCH_BOUNDS' not in s:
        raise AssertionError('26523 Swipe focus boundary missing')
    s=one(s,'import android.view.MotionEvent;\n',
          'import android.view.MotionEvent;\nimport android.view.ScaleGestureDetector;\n',
          'Swipe ScaleGestureDetector import')
    s=one(s,'    private GestureDetector gestureDetector;\n',
          '''    private GestureDetector gestureDetector;
    /* IRIS_26524_PINCH_ZOOM_GESTURE_OWNER */
    private ScaleGestureDetector iris26524ScaleDetector;
    private boolean iris26524PinchActive = false;
    private boolean iris26524SuppressNextUp = false;
''','Swipe zoom fields')
    old='''        View.OnTouchListener touchListener = (view, motionEvent) -> gestureDetector.onTouchEvent(motionEvent);
        View holder = cameraFragment.findViewById(R.id.textureHolder);
'''
    new='''        iris26524ScaleDetector = new ScaleGestureDetector(
                cameraFragment.getContext(),
                new ScaleGestureDetector.SimpleOnScaleGestureListener() {
                    @Override
                    public boolean onScaleBegin(ScaleGestureDetector detector) {
                        IrisZoomController zoom = cameraFragment.getIrisZoomController();
                        boolean enabled = zoom != null
                                && IrisZoomController.isContinuousZoomEnabledForCurrentMode();
                        iris26524PinchActive = enabled;
                        iris26524SuppressNextUp = enabled;
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
'''
    return one(s,old,new,'Swipe touch listener')

def fragment_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_ZOOM_CONTROLLER_LIFECYCLE' in s:
        raise AssertionError('26524 CameraFragment transform already present')
    if 'public <T extends View> T findViewById(@IdRes int id)' not in s:
        raise AssertionError('CameraFragment findViewById helper missing')
    s=one(s,'import com.particlesdevs.photoncamera.control.Swipe;\n',
          'import com.particlesdevs.photoncamera.control.Swipe;\nimport com.particlesdevs.photoncamera.control.IrisZoomController;\n',
          'CameraFragment zoom import')
    s=one(s,'    public Swipe mSwipe;\n',
          '''    public Swipe mSwipe;
    /* IRIS_26524_ZOOM_CONTROLLER_LIFECYCLE */
    private IrisZoomController irisZoomController;
''','CameraFragment zoom field')
    anchor='''    public CaptureController getCaptureController() {
        return captureController;
    }
'''
    repl=anchor+'''
    public IrisZoomController getIrisZoomController() {
        return irisZoomController;
    }
'''
    s=one(s,anchor,repl,'CameraFragment zoom getter')
    s=one(s,'        this.mCameraLensDataMap = manager2.getCameraLensDataMap();\n',
          '''        this.mCameraLensDataMap = manager2.getCameraLensDataMap();
        if (irisZoomController == null) {
            irisZoomController = new IrisZoomController(this);
        }
        irisZoomController.onLensInventoryReady();
''','CameraFragment lens inventory hook')
    return s

def aux_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_LIVE_ZOOM_INSIDE_OPTICAL_BUTTON' in s:
        raise AssertionError('26524 AuxButtons transform already present')
    s=one(s,'import com.particlesdevs.photoncamera.R;\n',
          'import com.particlesdevs.photoncamera.R;\nimport com.particlesdevs.photoncamera.control.IrisZoomController;\n',
          'AuxButtons zoom import')
    s=one(s,'        setListenerAndSelected(activeId);\n        updateVisibility();\n',
          '''        setListenerAndSelected(activeId);
        /* IRIS_26524_LIVE_ZOOM_INSIDE_OPTICAL_BUTTON */
        if (IrisZoomController.isInitialized()
                && IrisZoomController.isContinuousZoomEnabledForCurrentMode()) {
            setLiveZoomState(IrisZoomController.getGlobalZoom(),
                    IrisZoomController.getOwnerCameraId());
        }
        updateVisibility();
''','AuxButtons refresh live label')
    anchor='''    private void updateVisibility() {
        setVisibility(hiddenBySettings || getChildCount() <= 1 ? View.INVISIBLE : View.VISIBLE);
    }
'''
    repl='''    private static String getLiveZoomName(float zoom) {
        String text = String.format(Locale.US, "%.1fx", zoom);
        return text.replace(".0x", "x");
    }

    private float zoomFactorForCameraId(String cameraId) {
        if (auxButtonsModel == null || cameraId == null) return 1.0f;
        List<CameraLensData> front = auxButtonsModel.getFrontCameras();
        List<CameraLensData> back = auxButtonsModel.getBackCameras();
        if (back != null) for (CameraLensData lens : back)
            if (cameraId.equals(lens.getCameraId())) return lens.getZoomFactor();
        if (front != null) for (CameraLensData lens : front)
            if (cameraId.equals(lens.getCameraId())) return lens.getZoomFactor();
        return 1.0f;
    }

    public void setLiveZoomState(float globalZoom, String ownerCameraId) {
        if (auxButtonsModel == null || ownerCameraId == null
                || !auxButtonsMap.containsValue(ownerCameraId)) return;
        for (int i = 0; i < getChildCount(); i++) {
            View child = getChildAt(i);
            if (!(child instanceof Button)) continue;
            String cameraId = auxButtonsMap.get(child.getId());
            Button button = (Button) child;
            if (ownerCameraId != null && ownerCameraId.equals(cameraId)) {
                button.setText(getLiveZoomName(globalZoom));
                button.setSelected(true);
            } else {
                button.setText(getAuxButtonName(zoomFactorForCameraId(cameraId)));
                button.setSelected(false);
            }
        }
    }

'''+anchor
    return one(s,anchor,repl,'AuxButtons live label API')

def ui_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_EXPLICIT_LENS_BUTTON_RESETS_GLOBAL_ZOOM' in s:
        raise AssertionError('26524 CameraUIController transform already present')
    s=one(s,'import com.particlesdevs.photoncamera.control.CountdownTimer;\n',
          'import com.particlesdevs.photoncamera.control.CountdownTimer;\nimport com.particlesdevs.photoncamera.control.IrisZoomController;\n',
          'CameraUIController zoom import')
    old='''    public void onAuxButtonClicked(String id) {
        Log.d(TAG, "onAuxButtonClicked() called with: id = [" + id + "]");
        setID(id);
        this.restartCamera();

    }
'''
    new='''    public void onAuxButtonClicked(String id) {
        Log.d(TAG, "onAuxButtonClicked() called with: id = [" + id + "]");
        /* IRIS_26524_EXPLICIT_LENS_BUTTON_RESETS_GLOBAL_ZOOM */
        IrisZoomController zoom = cameraFragment.getIrisZoomController();
        if (zoom != null) zoom.onLensButtonSelected(id);
        setID(id);
        this.restartCamera();

    }
'''
    return one(s,old,new,'CameraUIController aux click')

def capture_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER' in s:
        raise AssertionError('26524 CaptureController transform already present')
    s=one(s,'import com.particlesdevs.photoncamera.control.GyroBurst;\n',
          'import com.particlesdevs.photoncamera.control.GyroBurst;\nimport com.particlesdevs.photoncamera.control.IrisZoomController;\n',
          'CaptureController zoom import')
    anchor='''    public void rebuildPreviewBuilder() {
        if(burst) return;
        try {
'''
    repl='''    /* IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER
     * Re-apply zoom immediately before every preview request submission so
     * AF/AE rebuilds and session restarts cannot silently return to 1x.
     */
    private void iris26524ApplyZoomToPreviewBuilder() {
        if (mPreviewRequestBuilder == null || mCameraCharacteristics == null) return;
        float residual = IrisZoomController.applyToRequest(
                mPreviewRequestBuilder,
                mCameraCharacteristics,
                PhotonCamera.getSettings().mCameraID);
        if (mTextureView != null) mTextureView.setSoftwareZoom(residual);
    }

    public void applyIrisZoomNow() {
        if (burst || mPreviewRequestBuilder == null || mCaptureSession == null) return;
        rebuildPreviewBuilder();
    }

'''+anchor
    s=one(s,anchor,repl,'CaptureController zoom helper')
    s=one(s,'''        try {
//            mCaptureSession.stopRepeating();
            mCaptureSession.setRepeatingRequest(mPreviewInputRequest = mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
''',
          '''        try {
//            mCaptureSession.stopRepeating();
            iris26524ApplyZoomToPreviewBuilder();
            mCaptureSession.setRepeatingRequest(mPreviewInputRequest = mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
''','CaptureController repeating zoom')
    s=one(s,'''        try {
            Log.d(TAG, "rebuildPreviewBuilderOneShot: " + mCaptureSession + " " + mPreviewRequestBuilder + " " + mCaptureCallback + " " + mBackgroundHandler);
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
''',
          '''        try {
            Log.d(TAG, "rebuildPreviewBuilderOneShot: " + mCaptureSession + " " + mPreviewRequestBuilder + " " + mCaptureCallback + " " + mBackgroundHandler);
            iris26524ApplyZoomToPreviewBuilder();
            mCaptureSession.capture(mPreviewRequestBuilder.build(), mCaptureCallback, mBackgroundHandler);
''','CaptureController one-shot zoom')
    s=one(s,'''                        mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                                getSelectedFpsRange());
                        mPreviewInputRequest = mPreviewRequestBuilder.build();
''',
          '''                        mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                                getSelectedFpsRange());
                        iris26524ApplyZoomToPreviewBuilder();
                        mPreviewInputRequest = mPreviewRequestBuilder.build();
''','CaptureController session initial zoom')
    s=one(s,'''            mPreviewCaptureResult = result;
            mPreviewCaptureRequest = request;
            Long sensorTimestamp = result.get(CaptureResult.SENSOR_TIMESTAMP);
''',
          '''            mPreviewCaptureResult = result;
            mPreviewCaptureRequest = request;
            /* IRIS_26524_ACTUAL_HAL_ZOOM_RESULT_OWNER */
            float iris26524PreviousResidual =
                    IrisZoomController.getResidualSoftwareZoom();
            float iris26524ActualResidual =
                    IrisZoomController.updateFromCaptureResult(
                            result,
                            mCameraCharacteristics,
                            PhotonCamera.getSettings().mCameraID);
            if (mTextureView != null
                    && Math.abs(iris26524ActualResidual
                            - iris26524PreviousResidual) > 0.0005f) {
                mTextureView.setSoftwareZoom(iris26524ActualResidual);
            }
            Long sensorTimestamp = result.get(CaptureResult.SENSOR_TIMESTAMP);
''','CaptureController actual HAL zoom result reconciliation')
    return s

def touch_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_RESIDUAL_ZOOM_FOCUS_MAPPING' in s:
        raise AssertionError('26524 TouchFocus transform already present')
    if 'IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING' not in s:
        raise AssertionError('26523 active crop focus mapping missing')
    old='''        float nx = Math.max(0f, Math.min(1f, previewX / (float) previewWidth));
        float ny = Math.max(0f, Math.min(1f, previewY / (float) previewHeight));
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
'''
    new='''        float nx = Math.max(0f, Math.min(1f, previewX / (float) previewWidth));
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
'''
    s=one(s,old,new,'TouchFocus residual crop')
    s=one(s,'''                + " crop=" + crop + " orientation=" + orientation
                + " rect=" + rect);
''',
          '''                + " crop=" + crop + " orientation=" + orientation
                + " residualSoftwareZoom=" + residualZoom
                + " rect=" + rect);
''','TouchFocus residual log')
    return s

def batch_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_SHUTTER_FROZEN_ZOOM_GEOMETRY' in s:
        raise AssertionError('26524 MotionBatch transform already present')
    s=one(s,'import com.particlesdevs.photoncamera.control.GyroBurst;\n',
          'import com.particlesdevs.photoncamera.control.GyroBurst;\nimport com.particlesdevs.photoncamera.control.IrisZoomController;\n',
          'MotionBatch zoom import')
    s=one(s,'    public final List<IsoExpoSelector.ExpoPair> exposurePairs;\n',
          '''    public final List<IsoExpoSelector.ExpoPair> exposurePairs;
    /* IRIS_26524_SHUTTER_FROZEN_ZOOM_GEOMETRY */
    public final float iris26524GlobalZoom;
    public final float iris26524OpticalZoomAnchor;
    public final float iris26524OutputLocalZoom;
    public final float iris26524HardwareLocalZoom;
    public final float iris26524ResidualSoftwareZoom;
    public final String iris26524OwnerCameraId;
''','MotionBatch zoom fields')
    anchor='''        this.shortHighlightSlot = shortHighlightSlot == null
                ? new ShortHighlightSlot() : shortHighlightSlot;
'''
    repl=anchor+'''        IrisZoomController.ZoomSnapshot iris26524Zoom = IrisZoomController.snapshot();
        this.iris26524GlobalZoom = iris26524Zoom.globalZoom;
        this.iris26524OpticalZoomAnchor = iris26524Zoom.opticalAnchor;
        this.iris26524OutputLocalZoom = iris26524Zoom.outputLocalZoom;
        this.iris26524HardwareLocalZoom = iris26524Zoom.hardwareLocalZoom;
        this.iris26524ResidualSoftwareZoom = iris26524Zoom.residualSoftwareZoom;
        this.iris26524OwnerCameraId = iris26524Zoom.ownerCameraId;
'''
    return one(s,anchor,repl,'MotionBatch shutter zoom snapshot')

def saver_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_MOTION_ZOOM_HANDOFF' in s:
        raise AssertionError('26524 DefaultSaver transform already present')
    old='''                batch.exposurePairs,
                batch.shortHighlightSlot,
                processingCallback);
'''
    new='''                batch.exposurePairs,
                batch.shortHighlightSlot,
                /* IRIS_26524_MOTION_ZOOM_HANDOFF */
                batch.iris26524GlobalZoom,
                batch.iris26524OpticalZoomAnchor,
                batch.iris26524OutputLocalZoom,
                batch.iris26524HardwareLocalZoom,
                batch.iris26524ResidualSoftwareZoom,
                processingCallback);
'''
    return one(s,old,new,'DefaultSaver zoom handoff')

def hdrx_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_HDRX_ZOOM_GEOMETRY_HANDOFF' in s:
        raise AssertionError('26524 HdrxProcessor transform already present')
    s=one(s,'''    private com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot
            mMotion26486ShortSlot;
''',
          '''    private com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot
            mMotion26486ShortSlot;
    /* IRIS_26524_HDRX_ZOOM_GEOMETRY_HANDOFF */
    private float mMotion26524GlobalZoom = 1.0f;
    private float mMotion26524OpticalZoomAnchor = 1.0f;
    private float mMotion26524OutputLocalZoom = 1.0f;
    private float mMotion26524HardwareLocalZoom = 1.0f;
    private float mMotion26524ResidualSoftwareZoom = 1.0f;
''','HdrxProcessor zoom fields')
    old='''                      java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair> exposurePairs,
                      com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot shortSlot,
                      ProcessingCallback callback) {
'''
    new='''                      java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair> exposurePairs,
                      com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot shortSlot,
                      float globalZoom, float opticalZoomAnchor, float outputLocalZoom,
                      float hardwareLocalZoom, float residualSoftwareZoom,
                      ProcessingCallback callback) {
'''
    s=one(s,old,new,'HdrxProcessor startMotion signature')
    s=one(s,'''        this.mMotion26486ShortSlot = shortSlot;
        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,
''',
          '''        this.mMotion26486ShortSlot = shortSlot;
        this.mMotion26524GlobalZoom = Math.max(0.05f, globalZoom);
        this.mMotion26524OpticalZoomAnchor = Math.max(0.05f, opticalZoomAnchor);
        this.mMotion26524OutputLocalZoom = Math.max(1.0f, outputLocalZoom);
        this.mMotion26524HardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
        this.mMotion26524ResidualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,
''','HdrxProcessor zoom assignment')
    s=one(s,'''        Parameters processingParameters = new Parameters();
        processingParameters.FillConstParameters(characteristics, new Point(width, height));
''',
          '''        Parameters processingParameters = new Parameters();
        processingParameters.FillConstParameters(characteristics, new Point(width, height));
        if (cameraMode == CameraMode.MOTION) {
            processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom;
            processingParameters.motionV2OpticalZoomAnchor = mMotion26524OpticalZoomAnchor;
            processingParameters.motionV2OutputZoom = mMotion26524OutputLocalZoom;
            processingParameters.motionV2HardwareZoom = mMotion26524HardwareLocalZoom;
            processingParameters.motionV2ResidualSoftwareZoom = mMotion26524ResidualSoftwareZoom;
            Log.i(TAG, "IRIS_26524_MOTION_ZOOM_FROZEN"
                    + " globalZoom=" + mMotion26524GlobalZoom
                    + " opticalAnchor=" + mMotion26524OpticalZoomAnchor
                    + " outputLocalZoom=" + mMotion26524OutputLocalZoom
                    + " hardwareLocalZoom=" + mMotion26524HardwareLocalZoom
                    + " residualSoftwareZoom=" + mMotion26524ResidualSoftwareZoom);
        }
''','HdrxProcessor parameters zoom')
    return s

def params_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_MOTION_OUTPUT_ZOOM_STATE' in s:
        raise AssertionError('26524 Parameters transform already present')
    old='''    public boolean motionV2Active = false;
    public float motionV2EffectiveSupport = 1.0f;
'''
    new='''    public boolean motionV2Active = false;
    public float motionV2EffectiveSupport = 1.0f;
    /* IRIS_26524_MOTION_OUTPUT_ZOOM_STATE
     * Geometry only. Non-tunable and ignored by alignment/rejection/merge.
     */
    public float motionV2GlobalZoom = 1.0f;
    public float motionV2OpticalZoomAnchor = 1.0f;
    public float motionV2OutputZoom = 1.0f;
    public float motionV2HardwareZoom = 1.0f;
    public float motionV2ResidualSoftwareZoom = 1.0f;
'''
    return one(s,old,new,'Parameters Motion zoom state')

def glpreview_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_PREVIEW_RESIDUAL_ZOOM' in s:
        raise AssertionError('26524 GLPreview transform already present')
    anchor='''    public void setMirror(boolean mirror) {
        mRenderer.setMirror(mirror);
        requestRender();
    }
'''
    repl=anchor+'''
    /* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
    public void setSoftwareZoom(float zoom) {
        mRenderer.setSoftwareZoom(Math.max(1.0f, zoom));
        requestRender();
    }
'''
    return one(s,anchor,repl,'GLPreview residual zoom API')

def renderer_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_PREVIEW_RESIDUAL_ZOOM' in s:
        raise AssertionError('26524 MainRenderer transform already present')
    s=one(s,'    private volatile boolean mMirrorPreview;\n',
          '''    private volatile boolean mMirrorPreview;
    /* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
    private volatile float mSoftwareZoom = 1.0f;
''','MainRenderer zoom field')
    s=one(s,'        GLES20.glUniform1i(mirror, mMirrorPreview ? 1 : 0);\n',
          '''        GLES20.glUniform1i(mirror, mMirrorPreview ? 1 : 0);
        GLES20.glUniform1f(irisSoftwareZoom, mSoftwareZoom);
''','MainRenderer zoom uniform draw')
    s=one(s,'    private int mirror;\n',
          '''    private int mirror;
    private int irisSoftwareZoom;
''','MainRenderer zoom uniform field')
    s=one(s,'        mirror = GLES20.glGetUniformLocation(hProgram, "mirror");\n',
          '''        mirror = GLES20.glGetUniformLocation(hProgram, "mirror");
        irisSoftwareZoom = GLES20.glGetUniformLocation(hProgram, "irisSoftwareZoom");
''','MainRenderer zoom uniform location')
    anchor='''    public void setMirror(boolean mirrorPreview) {
        mMirrorPreview = mirrorPreview;
    }
'''
    repl=anchor+'''
    public void setSoftwareZoom(float zoom) {
        mSoftwareZoom = Math.max(1.0f, zoom);
    }
'''
    return one(s,anchor,repl,'MainRenderer zoom setter')

def preview_fs_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_PREVIEW_RESIDUAL_ZOOM' in s:
        raise AssertionError('26524 preview shader already present')
    s=one(s,'uniform bool mirror;\n',
          '''uniform bool mirror;
uniform float irisSoftwareZoom;
/* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
''','Preview shader zoom uniform')
    s=one(s,'''    vec2 uv = texCoord.xy;
    if(mirror)
''',
          '''    vec2 uv = texCoord.xy;
    float zoom = max(irisSoftwareZoom, 1.0);
    uv = vec2(0.5) + (uv - vec2(0.5)) / zoom;
    if(mirror)
''','Preview shader crop')
    s=one(s,'            avg += texture(sTexture, uv + vec2(i*2, j*2) / size);\n',
          '            avg += texture(sTexture, uv + vec2(i*2, j*2) / (size * zoom));\n',
          'Preview shader peaking zoom')
    return s

def motion_render_java_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER' in s:
        raise AssertionError('26524 MotionV2Render transform already present')
    s=one(s,'''        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));
                glProg.useAssetProgram("motionv2/render");
''',
          '''        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));
        /* IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER */
        float irisOutputZoom = Math.max(1.0f,
                basePipeline.mParameters.motionV2OutputZoom);
                glProg.useAssetProgram("motionv2/render");
''','MotionV2Render output zoom')
    s=one(s,'                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);\n',
          '''                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);
        glProg.setVar("irisOutputZoom", irisOutputZoom);
''','MotionV2Render shader zoom var')
    s=one(s,'                glProg.setVar("maxGainRatio", maxGainRatio);\n',
          '''                glProg.setVar("maxGainRatio", maxGainRatio);
                glProg.setVar("irisOutputZoom", irisOutputZoom);
''','MotionV2 gainmap zoom var')
    s=one(s,'''                + " syntheticBitmapGainMap=false"
                + " localTone=false"
''',
          '''                + " syntheticBitmapGainMap=false"
                + " irisOutputZoom=" + irisOutputZoom
                + " nativeOutputDimensionsPreserved=true"
                + " localTone=false"
''','MotionV2Render zoom log')
    return s

def motion_render_glsl_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER' in s:
        raise AssertionError('26524 Motion render shader already present')
    s=one(s,'uniform float outputExposureScale;\n',
          '''uniform float outputExposureScale;
uniform float irisOutputZoom;
/* IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER */
''','Motion render zoom uniform')
    marker='''vec3 srgbEncode(vec3 x) {
    return vec3(
            srgbEncode(x.r),
            srgbEncode(x.g),
            srgbEncode(x.b));
}
'''
    helper=marker+'''
vec3 iris26524BilinearInput(vec2 sourcePixel) {
    ivec2 sz = textureSize(InputBuffer,0);
    vec2 hi = max(vec2(sz) - vec2(1.0), vec2(0.0));
    vec2 p = clamp(sourcePixel, vec2(0.0), hi);
    ivec2 p0 = ivec2(floor(p));
    ivec2 p1 = min(p0 + ivec2(1), sz - ivec2(1));
    vec2 f = fract(p);
    vec3 a = mix(texelFetch(InputBuffer, ivec2(p0.x,p0.y),0).rgb,
                 texelFetch(InputBuffer, ivec2(p1.x,p0.y),0).rgb, f.x);
    vec3 b = mix(texelFetch(InputBuffer, ivec2(p0.x,p1.y),0).rgb,
                 texelFetch(InputBuffer, ivec2(p1.x,p1.y),0).rgb, f.x);
    return mix(a,b,f.y);
}
'''
    s=one(s,marker,helper,'Motion render bilinear helper')
    old='''    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sourceXY=xy;
    /* IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL
     * The successful 26490 four-edge RCD mirror stays untouched. Only the known
     * final x==0 output defect is replaced with the already-renderable x==1 source.
     */
    ivec2 sourceSize=textureSize(InputBuffer,0);
    if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;
    vec3 linearSrgb=max(
            texelFetch(InputBuffer,sourceXY,0).rgb,
            vec3(0.0));

    /*
     * Apply the same pre-tone local-contrast intent that the HDR target uses.
     * The existing headroom mapper and 0.80 exposure remain unchanged.
     */
    linearSrgb=applyReferenceSafeMicrocontrast(sourceXY,linearSrgb);
'''
    new='''    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sourceSize=textureSize(InputBuffer,0);
    ivec2 sourceXY=xy;
    vec3 linearSrgb;
    float zoom=max(irisOutputZoom,1.0);
    if(zoom<=1.00001) {
        /* IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL
         * Exact tested 26523 1x path remains unchanged.
         */
        if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;
        linearSrgb=max(texelFetch(InputBuffer,sourceXY,0).rgb,vec3(0.0));
    } else {
        vec2 center=(vec2(sourceSize)-vec2(1.0))*0.5;
        vec2 sourcePixel=center+(vec2(xy)-center)/zoom;
        linearSrgb=max(iris26524BilinearInput(sourcePixel),vec3(0.0));
        sourceXY=ivec2(clamp(floor(sourcePixel+vec2(0.5)),
                            vec2(0.0),vec2(sourceSize-ivec2(1))));
    }

    /*
     * Apply the same pre-tone local-contrast intent that the HDR target uses.
     * The existing headroom mapper and 0.80 exposure remain unchanged.
     */
    linearSrgb=applyReferenceSafeMicrocontrast(sourceXY,linearSrgb);
'''
    return one(s,old,new,'Motion render geometry')

def gainmap_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY' in s:
        raise AssertionError('26524 gainmap shader already present')
    s=one(s,'uniform float maxGainRatio;\n',
          '''uniform float maxGainRatio;
uniform float irisOutputZoom;
/* IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY */
''','Gainmap zoom uniform')
    old='''void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,gainMapSize))){Output=0.0;return;}
    float hdr=max(luminance(max(texelFetch(HdrBuffer,p,0).rgb,vec3(0.0))*hdrExposureScale),0.0);
    float sdr=max(luminance(srgbDecode(texelFetch(SdrBuffer,p,0).rgb)),0.0);
'''
    new='''vec3 iris26524BilinearHdr(vec2 sourcePixel){
    ivec2 sz=textureSize(HdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(texelFetch(HdrBuffer,ivec2(p0.x,p0.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p0.y),0).rgb,f.x);
    vec3 b=mix(texelFetch(HdrBuffer,ivec2(p0.x,p1.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p1.y),0).rgb,f.x);
    return mix(a,b,f.y);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,gainMapSize))){Output=0.0;return;}
    float zoom=max(irisOutputZoom,1.0);
    vec3 hdrRgb;
    if(zoom<=1.00001){
        hdrRgb=texelFetch(HdrBuffer,p,0).rgb;
    }else{
        ivec2 hdrSize=textureSize(HdrBuffer,0);
        vec2 center=(vec2(hdrSize)-vec2(1.0))*0.5;
        vec2 sourcePixel=center+(vec2(p)-center)/zoom;
        hdrRgb=iris26524BilinearHdr(sourcePixel);
    }
    float hdr=max(luminance(max(hdrRgb,vec3(0.0))*hdrExposureScale),0.0);
    float sdr=max(luminance(srgbDecode(texelFetch(SdrBuffer,p,0).rgb)),0.0);
'''
    return one(s,old,new,'Gainmap geometry parity')

TRANSFORMS={
    SWIPE:swipe_expected,
    TOUCH:touch_expected,
    AUX:aux_expected,
    UI:ui_expected,
    FRAGMENT:fragment_expected,
    CAPTURE:capture_expected,
    BATCH:batch_expected,
    SAVER:saver_expected,
    HDRX:hdrx_expected,
    PARAMS:params_expected,
    GLPREVIEW:glpreview_expected,
    RENDERER:renderer_expected,
    PREVIEW_FS:preview_fs_expected,
    MOTION_RENDER_JAVA:motion_render_java_expected,
    MOTION_RENDER_GLSL:motion_render_glsl_expected,
    GAINMAP_GLSL:gainmap_expected,
}

def transformed(root:Path):
    out={}
    for rel,fn in TRANSFORMS.items():
        p=root/rel
        if not p.is_file():
            raise AssertionError('missing required source '+rel)
        out[rel]=fn(p.read_text())
    zp=root/ZOOM
    if zp.exists():
        raise AssertionError('IrisZoomController already exists before 26524')
    out[ZOOM]=ZOOM_SOURCE
    return out

def emit_patch(root:Path, outputs:dict[str,str])->str:
    chunks=[]
    for rel in sorted(outputs):
        p=root/rel
        old=norm(p.read_text()) if p.exists() else ''
        new=norm(outputs[rel])
        chunks.extend(difflib.unified_diff(
            old.splitlines(True),new.splitlines(True),
            fromfile=('a/'+rel if p.exists() else '/dev/null'),
            tofile='b/'+rel))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--check-only',action='store_true')
    ap.add_argument('--patch-out',type=Path)
    ap.add_argument('--patch-sha-out',type=Path)
    a=ap.parse_args()

    outputs=transformed(a.root)
    patch=emit_patch(a.root,outputs)
    if not patch:
        raise SystemExit('empty 26524 patch unexpectedly')

    if a.patch_out:
        a.patch_out.parent.mkdir(parents=True,exist_ok=True)
        a.patch_out.write_text(patch)
        digest=hashlib.sha256(a.patch_out.read_bytes()).hexdigest()
        if a.patch_sha_out:
            a.patch_sha_out.write_text(f'{digest}  {a.patch_out.name}\n')
    if a.check_only:
        print('PASS: 26524 complete transform resolved in memory')
        print('changed_files='+str(len(outputs)))
        for rel in sorted(outputs): print(rel)
        return

    for rel,new in outputs.items():
        p=a.root/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(new)
    print('PASS: 26524 continuous zoom transform applied')
    print('changed_files='+str(len(outputs)))

if __name__=='__main__':
    main()
