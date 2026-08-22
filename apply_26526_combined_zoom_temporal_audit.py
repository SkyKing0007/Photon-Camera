#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util, re
from pathlib import Path

ZOOM = "app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java"
CAPTURE = "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
ALLOWED = {ZOOM, CAPTURE}

PREDECESSOR_ZOOM_TRANSFORMER = "apply_26524_continuous_zoom.py"
PREDECESSOR_ZOOM_TRANSFORMER_SHA = "056dbbd4c72bed95054682c22c90de3041f88af4dfcc53dab3f6efb240d96bf3"
PREDECESSOR_DNG_TRANSFORMER = "apply_26525_dng_zoom_parity.py"
PREDECESSOR_DNG_TRANSFORMER_SHA = "25522634fbcba20638ccf9637475b5ac200ebe6a17d8242733e7de4e06577bbb"
EXPECTED_26525_DNG_ONLY = {
    "app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java",
    "app/src/main/cpp/dngCreator.cpp",
    "app/src/main/cpp/CMakeLists.txt",
}

def norm(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def one(s: str, old: str, new: str, label: str) -> str:
    n = s.count(old)
    if n != 1:
        raise AssertionError(f"{label} anchor count={n} expected=1")
    return s.replace(old, new, 1)

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.is_file():
        raise AssertionError("missing required runtime file: " + rel)
    return norm(p.read_text(encoding="utf-8"))

def load_26524_transformer(script_dir: Path):
    p = script_dir / PREDECESSOR_ZOOM_TRANSFORMER
    if not p.is_file():
        raise AssertionError("missing exact 26524 zoom transformer beside 26526 handoff")
    if sha(p) != PREDECESSOR_ZOOM_TRANSFORMER_SHA:
        raise AssertionError("exact 26524 zoom transformer SHA drift")
    spec = importlib.util.spec_from_file_location("iris26524_exact", p)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to import exact 26524 zoom transformer")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_26525_transformer(script_dir: Path):
    p = script_dir / PREDECESSOR_DNG_TRANSFORMER
    if not p.is_file():
        raise AssertionError("missing exact 26525 V1.1 DNG transformer beside 26526 handoff")
    if sha(p) != PREDECESSOR_DNG_TRANSFORMER_SHA:
        raise AssertionError("exact 26525 V1.1 DNG transformer SHA drift")
    spec = importlib.util.spec_from_file_location("iris26525_exact", p)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to import exact 26525 V1.1 DNG transformer")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def has_camera_device_field(src: str) -> bool:
    # Visibility was public in the predecessor source. Ownership only requires
    # the declared type/name, so never gate on public/protected/private spelling.
    return re.search(r"\bCameraDevice\s+mCameraDevice\s*;", src) is not None

def prove_predecessor_chain(script_dir: Path) -> None:
    prev24 = load_26524_transformer(script_dir)
    prev25 = load_26525_transformer(script_dir)

    allowed25 = set(getattr(prev25, "ALLOWED", set()))
    if allowed25 != EXPECTED_26525_DNG_ONLY:
        raise AssertionError(
            "exact 26525 V1.1 runtime allowlist drift: " + repr(sorted(allowed25))
        )
    if ZOOM in allowed25 or CAPTURE in allowed25:
        raise AssertionError("26525 V1.1 unexpectedly touches zoom/capture owners")

    prev24_source = norm((script_dir / PREDECESSOR_ZOOM_TRANSFORMER).read_text(encoding="utf-8"))
    if OLD_CAPTURE_HELPER not in prev24_source:
        raise AssertionError("26526 request-owner replacement is not exact 26524-generated block")
    if OLD_CAPTURE_RESULT not in prev24_source:
        raise AssertionError("26526 result-owner replacement is not exact 26524-generated block")

    if norm(prev24.ZOOM_SOURCE).count("IRIS_26524_CONTINUOUS_CROSSLENS_ZOOM_OWNER") != 1:
        raise AssertionError("exact 26524 generated zoom owner marker drift")

def zoom_expected(old: str) -> str:
    s = norm(old)

    s = one(
        s,
        """    private static final float TELE_DETECTION_FACTOR = 1.50f;
    private static final long PREVIEW_APPLY_INTERVAL_MS = 24L;
""",
        """    private static final float TELE_DETECTION_FACTOR = 1.50f;
    private static final float LENS_HANDOFF_HYSTERESIS_FRACTION = 0.02f;
    private static final long PREVIEW_APPLY_INTERVAL_MS = 24L;
""",
        "zoom hysteresis constant",
    )

    s = one(
        s,
        """    private static volatile float sMaximumGlobalZoom = NO_TELE_MAX_GLOBAL_ZOOM;
    private static volatile String sOwnerCameraId = null;
""",
        """    private static volatile float sMaximumGlobalZoom = NO_TELE_MAX_GLOBAL_ZOOM;
    /* IRIS_26526_TRANSACTIONAL_LENS_HANDOFF
     * sOwnerCameraId/sOpticalAnchor describe the camera that has produced a valid
     * result. Pending state is only a requested restart target until that result arrives.
     */
    private static volatile String sOwnerCameraId = null;
    private static volatile String sPendingOwnerCameraId = null;
    private static volatile float sPendingOpticalAnchor = 1.0f;
""",
        "zoom active/pending state",
    )

    old_inventory = """    public void onLensInventoryReady() {
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
"""
    new_inventory = """    public void onLensInventoryReady() {
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
                sOwnerCameraId = selected.getCameraId();
                sOpticalAnchor = safeAnchor(selected);
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
                sInitialized = true;
            } else {
                // IRIS_26526_KEEP_ACTIVE_OWNER_DURING_RESTART:
                // inventory refresh must not commit the pending camera merely because
                // PreferenceKeys already points at the restart target.
                sGlobalZoom = clamp(sGlobalZoom, sMinimumGlobalZoom, sMaximumGlobalZoom);
            }
        }
        updateButtonUi();
    }
"""
    s = one(s, old_inventory, new_inventory, "inventory must preserve active owner")

    s = one(
        s,
        """            sOwnerCameraId = lens.getCameraId();
            sHardwareLocalZoom = 1.0f;
            sResidualSoftwareZoom = 1.0f;
            sInitialized = true;
""",
        """            sOwnerCameraId = lens.getCameraId();
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = safeAnchor(lens);
            sHardwareLocalZoom = 1.0f;
            sResidualSoftwareZoom = 1.0f;
            sInitialized = true;
""",
        "lens button resets pending state",
    )

    old_pinch = """    public void onPinchScale(float scaleFactor) {
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
"""
    new_pinch = """    public void onPinchScale(float scaleFactor) {
        if (!isContinuousZoomEnabledForCurrentMode()) return;
        if (!Float.isFinite(scaleFactor) || scaleFactor <= 0.0f) return;
        refreshInventory();
        if (backLenses.isEmpty()) return;

        String activeOwner;
        String pendingOwner = null;
        float pendingAnchor = 1.0f;
        synchronized (STATE_LOCK) {
            sGlobalZoom = clamp(sGlobalZoom * scaleFactor,
                    sMinimumGlobalZoom, sMaximumGlobalZoom);
            sInitialized = true;
            activeOwner = sOwnerCameraId;

            // Only one physical-camera restart can be outstanding. The requested
            // global zoom may continue changing while the old camera remains active.
            if (sPendingOwnerCameraId == null) {
                CameraLensData nextOwner = ownerWithHysteresis(sGlobalZoom);
                if (nextOwner != null
                        && sOwnerCameraId != null
                        && !sOwnerCameraId.equals(nextOwner.getCameraId())) {
                    sPendingOwnerCameraId = nextOwner.getCameraId();
                    sPendingOpticalAnchor = safeAnchor(nextOwner);
                    pendingOwner = sPendingOwnerCameraId;
                    pendingAnchor = sPendingOpticalAnchor;
                }
            }
        }

        updateButtonUi();

        if (pendingOwner != null) {
            PreferenceKeys.setCameraID(pendingOwner);
            if (fragment.auxButtonsViewModel != null) {
                fragment.auxButtonsViewModel.setActiveId(pendingOwner);
            }
            CaptureController controller = fragment.captureController;
            if (controller != null) {
                Log.i(TAG, "IRIS_26526_HANDOFF_PENDING"
                        + " activeOwner=" + activeOwner
                        + " pendingOwner=" + pendingOwner
                        + " globalZoom=" + getGlobalZoom()
                        + " activeAnchor=" + getOpticalAnchor()
                        + " pendingAnchor=" + pendingAnchor);
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
"""
    s = one(s, old_pinch, new_pinch, "transactional pinch handoff")

    owner_for = """    private CameraLensData ownerFor(float globalZoom) {
        CameraLensData owner = backLenses.get(0);
        for (CameraLensData lens : backLenses) {
            if (safeAnchor(lens) <= globalZoom + 0.0005f) owner = lens;
            else break;
        }
        return owner;
    }
"""
    owner_hyst = owner_for + """
    /**
     * IRIS_26526_DIRECTIONAL_HANDOFF_HYSTERESIS
     * Physical cameras switch only after the global zoom clears a small band
     * around the relevant optical anchor. The anchors remain dynamically
     * discovered from CameraLensData. A fast gesture may directly request the
     * highest appropriate lens instead of forcing serial intermediate restarts.
     */
    private CameraLensData ownerWithHysteresis(float globalZoom) {
        CameraLensData active = findLens(sOwnerCameraId);
        if (active == null) return ownerFor(globalZoom);
        int activeIndex = backLenses.indexOf(active);
        if (activeIndex < 0) return ownerFor(globalZoom);

        float activeAnchor = safeAnchor(active);
        if (globalZoom >= activeAnchor) {
            CameraLensData target = active;
            for (int i = activeIndex + 1; i < backLenses.size(); ++i) {
                CameraLensData candidate = backLenses.get(i);
                float upperSwitch = safeAnchor(candidate)
                        * (1.0f + LENS_HANDOFF_HYSTERESIS_FRACTION);
                if (globalZoom >= upperSwitch) target = candidate;
                else break;
            }
            return target;
        }

        if (activeIndex > 0
                && globalZoom <= activeAnchor
                        * (1.0f - LENS_HANDOFF_HYSTERESIS_FRACTION)) {
            return ownerFor(globalZoom);
        }
        return active;
    }
"""
    s = one(s, owner_for, owner_hyst, "directional handoff hysteresis")

    old_apply = """    public static float applyToRequest(CaptureRequest.Builder builder,
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
"""
    new_apply = """    /**
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
        boolean motionZoom = isContinuousZoomEnabledForCurrentMode();
        float localZoom = 1.0f;
        boolean ownsRequest = false;
        synchronized (STATE_LOCK) {
            if (!motionZoom) {
                sGlobalZoom = sOpticalAnchor;
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
                sHardwareLocalZoom = 1.0f;
                sResidualSoftwareZoom = 1.0f;
            }

            float requestAnchor = sOpticalAnchor;
            String requestOwner = sOwnerCameraId;
            if (motionZoom && rear && sPendingOwnerCameraId != null
                    && sPendingOwnerCameraId.equals(activeCameraId)) {
                requestOwner = sPendingOwnerCameraId;
                requestAnchor = sPendingOpticalAnchor;
            }
            ownsRequest = motionZoom && rear && sInitialized
                    && requestOwner != null && requestOwner.equals(activeCameraId);
            if (ownsRequest) {
                localZoom = Math.max(1.0f,
                        sGlobalZoom / Math.max(0.01f, requestAnchor));
            }
        }

        float hardwareZoom = 1.0f;
        float supportedHardwareMax = 1.0f;
        boolean usedZoomRatio = false;
        Rect activeArray = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Range<Float> range = characteristics.get(
                        CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE);
                if (range != null && range.getUpper() != null
                        && range.getUpper() >= 1.0f) {
                    supportedHardwareMax = Math.max(1.0f, range.getUpper());
                    hardwareZoom = clamp(localZoom, 1.0f, supportedHardwareMax);
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
            supportedHardwareMax = maxDigital == null
                    ? 1.0f : Math.max(1.0f, maxDigital);
            hardwareZoom = clamp(localZoom, 1.0f, supportedHardwareMax);
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

        // Static capability residual only. Within the HAL range this is exactly 1x.
        float residual = ownsRequest
                ? Math.max(1.0f, localZoom / Math.max(1.0f, supportedHardwareMax))
                : 1.0f;
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
            Log.d(TAG, "IRIS_26526_ZOOM_REQUEST_AUTHORITY"
                    + " activeCameraId=" + activeCameraId
                    + " globalZoom=" + getGlobalZoom()
                    + " localZoom=" + localZoom
                    + " hardwareTarget=" + hardwareZoom
                    + " hardwareMax=" + supportedHardwareMax
                    + " residualSoftwareZoom=" + residual);
        }
        return residual;
    }
"""
    s = one(s, old_apply, new_apply, "single preview geometry authority")

    old_result = """    /* IRIS_26524_ACTUAL_HAL_ZOOM_RECONCILIATION
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
"""
    new_result = """    /* IRIS_26526_HAL_TELEMETRY_ONLY
     * CaptureResult may update actual-HAL telemetry and commit a pending physical
     * camera, but it must never drive the live software preview crop.
     */
    public static float updateFromCaptureResult(CaptureResult result,
                                                CameraCharacteristics characteristics,
                                                String activeCameraId) {
        if (result == null || characteristics == null
                || !isContinuousZoomEnabledForCurrentMode()
                || activeCameraId == null) {
            return getResidualSoftwareZoom();
        }
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing == null || facing != CameraCharacteristics.LENS_FACING_BACK) {
            return 1.0f;
        }

        boolean committedPending = false;
        synchronized (STATE_LOCK) {
            if (sPendingOwnerCameraId != null
                    && sPendingOwnerCameraId.equals(activeCameraId)) {
                String oldOwner = sOwnerCameraId;
                sOwnerCameraId = sPendingOwnerCameraId;
                sOpticalAnchor = Math.max(0.05f, sPendingOpticalAnchor);
                sPendingOwnerCameraId = null;
                sPendingOpticalAnchor = sOpticalAnchor;
                committedPending = true;
                Log.i(TAG, "IRIS_26526_HANDOFF_COMMIT"
                        + " oldOwner=" + oldOwner
                        + " activeOwner=" + sOwnerCameraId
                        + " globalZoom=" + sGlobalZoom
                        + " opticalAnchor=" + sOpticalAnchor);
            }
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
            actualHardware = Math.max(actualHardware,
                    Math.max(1.0f, Math.min(cropZoomX, cropZoomY)));
        }

        float residual;
        boolean resultOwnsCurrent;
        synchronized (STATE_LOCK) {
            resultOwnsCurrent = sOwnerCameraId != null
                    && sOwnerCameraId.equals(activeCameraId);
            if (resultOwnsCurrent) {
                // Actual HAL zoom is metadata only. It cannot modify residual.
                sHardwareLocalZoom = Math.max(1.0f, actualHardware);
            }
            residual = sResidualSoftwareZoom;
        }
        if (resultOwnsCurrent || committedPending) {
            Log.d(TAG, "IRIS_26526_HAL_TELEMETRY_ONLY"
                    + " activeCameraId=" + activeCameraId
                    + " globalZoom=" + getGlobalZoom()
                    + " opticalAnchor=" + getOpticalAnchor()
                    + " actualHardwareZoom=" + actualHardware
                    + " residualSoftwareZoom=" + residual
                    + " residualDrivenByCaptureResult=false"
                    + " crop=" + crop);
        }
        return residual;
    }
"""
    s = one(s, old_result, new_result, "CaptureResult telemetry only")
    return s

OLD_CAPTURE_HELPER = """    /* IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER
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

"""

NEW_CAPTURE_HELPER = """    /* IRIS_26526_CAMERA2_SINGLE_PREVIEW_AUTHORITY
     * Bind the request to the actual CameraCaptureSession device whenever possible,
     * not the mutable preference that merely requests a restart.
     */
    private void iris26524ApplyZoomToPreviewBuilder() {
        if (mPreviewRequestBuilder == null || mCameraCharacteristics == null) return;
        String iris26526ActiveCameraId = null;
        if (mCaptureSession != null && mCaptureSession.getDevice() != null) {
            iris26526ActiveCameraId = mCaptureSession.getDevice().getId();
        } else if (mCameraDevice != null) {
            iris26526ActiveCameraId = mCameraDevice.getId();
        }
        float residual = IrisZoomController.applyToRequest(
                mPreviewRequestBuilder,
                mCameraCharacteristics,
                iris26526ActiveCameraId);
        if (mTextureView != null) mTextureView.setSoftwareZoom(residual);
    }

    public void applyIrisZoomNow() {
        if (burst || mPreviewRequestBuilder == null || mCaptureSession == null) return;
        rebuildPreviewBuilder();
    }

"""

OLD_CAPTURE_RESULT = """            /* IRIS_26524_ACTUAL_HAL_ZOOM_RESULT_OWNER */
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
"""

NEW_CAPTURE_RESULT = """            /* IRIS_26526_SESSION_BOUND_HAL_TELEMETRY
             * The callback session is immutable for this result. Never infer result
             * ownership from PreferenceKeys or mutable mCameraDevice. CaptureResult
             * cannot drive the live software preview crop.
             */
            String iris26526ResultCameraId =
                    session.getDevice() == null ? null : session.getDevice().getId();
            IrisZoomController.updateFromCaptureResult(
                    result,
                    mCameraCharacteristics,
                    iris26526ResultCameraId);
"""

def capture_expected(old: str) -> str:
    s = norm(old)
    if not has_camera_device_field(s):
        raise AssertionError("CaptureController CameraDevice mCameraDevice declaration missing")
    if "IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER" not in s:
        raise AssertionError("successful-26525 candidate missing 26524 request owner")
    if "IRIS_26524_ACTUAL_HAL_ZOOM_RESULT_OWNER" not in s:
        raise AssertionError("successful-26525 candidate missing 26524 result owner")
    s = one(s, OLD_CAPTURE_HELPER, NEW_CAPTURE_HELPER, "CaptureController request authority")
    s = one(s, OLD_CAPTURE_RESULT, NEW_CAPTURE_RESULT, "CaptureController session-bound result")
    return s

def transformed(root: Path, script_dir: Path | None = None) -> dict[str, str]:
    if script_dir is None:
        script_dir = Path(__file__).resolve().parent
    prove_predecessor_chain(script_dir)
    prev = load_26524_transformer(script_dir)
    current_zoom = read(root, ZOOM)
    expected_old_zoom = norm(prev.ZOOM_SOURCE)
    if current_zoom != expected_old_zoom:
        raise AssertionError("successful-26525 IrisZoomController is not exact proven 26524 generated source")
    return {
        ZOOM: zoom_expected(current_zoom),
        CAPTURE: capture_expected(read(root, CAPTURE)),
    }

def tree_files(root: Path) -> dict[str, str]:
    out = {}
    main = root / "app/src/main"
    for p in main.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = hashlib.sha256(p.read_bytes()).hexdigest()
    v = root / "app/version.properties"
    if v.is_file():
        out["app/version.properties"] = hashlib.sha256(v.read_bytes()).hexdigest()
    return out

def write_patch(root: Path, outputs: dict[str, str], patch: Path):
    chunks = []
    for rel in sorted(outputs):
        old = read(root, rel).splitlines(True)
        new = outputs[rel].splitlines(True)
        chunks.extend(difflib.unified_diff(old, new, fromfile="a/" + rel, tofile="b/" + rel))
    patch.parent.mkdir(parents=True, exist_ok=True)
    patch.write_text("".join(chunks), encoding="utf-8")

def self_test(script_dir: Path):
    prove_predecessor_chain(script_dir)
    prev = load_26524_transformer(script_dir)
    z = zoom_expected(norm(prev.ZOOM_SOURCE))
    assert z.count("IRIS_26526_SINGLE_PREVIEW_GEOMETRY_AUTHORITY") == 1
    assert z.count("IRIS_26526_TRANSACTIONAL_LENS_HANDOFF") == 1
    assert z.count("IRIS_26526_HANDOFF_PENDING") == 1
    assert z.count("IRIS_26526_HANDOFF_COMMIT") == 1
    assert "desiredLocal / Math.max(1.0f, actualHardware)" not in z
    assert z.count("sResidualSoftwareZoom = residual;") == 1
    assert z.count("{") == z.count("}")
    synthetic = "public CameraDevice mCameraDevice;\n" + OLD_CAPTURE_HELPER + OLD_CAPTURE_RESULT
    c = capture_expected(synthetic)
    for declaration in (
        "public CameraDevice mCameraDevice;",
        "protected CameraDevice mCameraDevice;",
        "private CameraDevice mCameraDevice;",
    ):
        assert has_camera_device_field(declaration)
    assert not has_camera_device_field("CameraDevice otherDevice;")
    assert "session.getDevice().getId()" in c
    assert "iris26524PreviousResidual" not in c
    assert "mTextureView.setSoftwareZoom(iris26524ActualResidual)" not in c
    print("PASS: exact 26524 zoom blocks + exact 26525 DNG-only provenance chain")
    print("PASS: semantic CameraDevice field proof is visibility-independent")
    print("PASS: 26526 exact predecessor zoom transform self-test")
    print("PASS: CaptureResult-driven software zoom removal self-test")
    print("PASS: transactional pending/commit + hysteresis source structure self-test")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, nargs="?")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--patch-out", type=Path)
    ap.add_argument("--patch-sha-out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    script_dir = Path(__file__).resolve().parent

    if a.self_test:
        self_test(script_dir)
        return
    if a.root is None:
        raise SystemExit("root is required unless --self-test is used")

    outputs = transformed(a.root, script_dir)
    before = tree_files(a.root)
    simulated = dict(before)
    for rel, text in outputs.items():
        simulated[rel] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = {p for p in set(before) | set(simulated) if before.get(p) != simulated.get(p)}
    if changed != ALLOWED:
        raise AssertionError("in-memory changed-file scope mismatch: " + repr(sorted(changed)))

    if a.patch_out:
        write_patch(a.root, outputs, a.patch_out)
        if a.patch_sha_out:
            digest = hashlib.sha256(a.patch_out.read_bytes()).hexdigest()
            a.patch_sha_out.parent.mkdir(parents=True, exist_ok=True)
            a.patch_sha_out.write_text(f"{digest}  {a.patch_out.name}\n", encoding="utf-8")

    print("PASS: complete 26526 two-file zoom transform resolved in memory")
    print("PASS: temporal/DNG/image-producing owners are outside transform allowlist")
    if a.check_only:
        return

    for rel, text in outputs.items():
        (a.root / rel).write_text(text, encoding="utf-8")
    print("PASS: 26526 zoom runtime transform applied")

if __name__ == "__main__":
    main()
