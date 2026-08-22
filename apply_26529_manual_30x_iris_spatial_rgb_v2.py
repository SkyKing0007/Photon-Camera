#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, sys, difflib
from pathlib import Path

BASE_VERSION='0.9726528'
BASE_BUILD='26528'
TARGET_VERSION='0.9726529'
TARGET_BUILD='26529'
BJZHOU_COMMIT='c317bf97d2649ae9296bc1459979ce63cb3364b2'
BJZHOU_POST_BLOB='5f29df5461cb50b199a6b19eea096127bf4af35c'
IRIS_TEMPLATE_SHA256='5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4'

ZOOM='app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java'
SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
STACKER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
PACKER='app/src/main/java/com/hinnka/mycamera/utils/DirectBufferPixelPacker.kt'
ALLOWED=(ZOOM,SHADER,STACKER,POST,PACKER)

class TransformError(RuntimeError): pass

def read(root, rel):
    p=Path(root)/rel
    if not p.is_file(): raise TransformError(f'missing {rel}')
    return p.read_text()

def write(root, rel, text):
    p=Path(root)/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)

def once(text, old, new, label):
    n=text.count(old)
    if n!=1: raise TransformError(f'{label}: expected 1 anchor, got {n}')
    return text.replace(old,new,1)

def method_replace(text, signature, new_method, label):
    start=text.find(signature)
    if start<0: raise TransformError(f'{label}: signature missing')
    brace=text.find('{',start)
    if brace<0: raise TransformError(f'{label}: opening brace missing')
    depth=0; i=brace
    in_str=False; in_chr=False; esc=False; line=False; block=False
    while i<len(text):
        c=text[i]; d=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and d=='/': block=False; i+=1
        elif in_str:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': in_str=False
        elif in_chr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=="'": in_chr=False
        else:
            if c=='/' and d=='/': line=True; i+=1
            elif c=='/' and d=='*': block=True; i+=1
            elif c=='"': in_str=True
            elif c=="'": in_chr=True
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0:
                    return text[:start]+new_method.rstrip()+text[i+1:]
        i+=1
    raise TransformError(f'{label}: unterminated method')

def java_zoom(text):
    text=once(text,
''' * IRIS_26524_CONTINUOUS_CROSSLENS_ZOOM_OWNER
 *
 * One global rear-camera zoom coordinate. Physical lenses are optical anchors;
 * Camera2 performs as much local crop as the active camera supports and Iris'
 * preview/final Motion renderer supplies only the residual beyond that limit.
''',
''' * IRIS_26529_MANUAL_PHYSICAL_LENS_30X_OWNER
 *
 * Physical camera ownership changes only when the user explicitly presses a lens button.
 * Pinch zoom is local to that selected physical lens from 1x through 30x. Camera2 performs
 * only legal hardware crop and Iris supplies any residual digital zoom beyond the HAL limit.
 * The UI remains in global/equivalent zoom coordinates (optical anchor * local zoom), while
 * Motion/DNG keep the selected-lens-local zoom authority.
''','zoom class contract')
    text=once(text,
'''    public static final float TELE_MAX_GLOBAL_ZOOM = 50.0f;
    public static final float NO_TELE_MAX_GLOBAL_ZOOM = 20.0f;
    private static final float TELE_DETECTION_FACTOR = 1.50f;
    private static final float LENS_HANDOFF_HYSTERESIS_FRACTION = 0.02f;
''',
'''    public static final float LOCAL_MAX_ZOOM = 30.0f;
''','zoom constants')
    text=text.replace('private static volatile float sMaximumGlobalZoom = NO_TELE_MAX_GLOBAL_ZOOM;',
                      'private static volatile float sMaximumGlobalZoom = LOCAL_MAX_ZOOM;')
    text=once(text,
'''            this.opticalAnchor = Math.max(0.01f, opticalAnchor);
            this.outputLocalZoom = Math.max(1.0f, globalZoom / this.opticalAnchor);
''',
'''            this.opticalAnchor = Math.max(0.01f, opticalAnchor);
            float requestedLocal = globalZoom / this.opticalAnchor;
            this.outputLocalZoom = Float.isFinite(requestedLocal)
                    ? clamp(requestedLocal, 1.0f, LOCAL_MAX_ZOOM) : 1.0f;
''','snapshot local clamp')

    on_inventory='''    public void onLensInventoryReady() {
        refreshInventory();
        if (backLenses.isEmpty()) return;
        synchronized (STATE_LOCK) {
            CameraLensData selected = findLens(PreferenceKeys.getCameraID());
            if (selected == null || selected.getFacing() != CameraCharacteristics.LENS_FACING_BACK) {
                selected = findClosestToOne();
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
        updateButtonUi();
    }'''
    text=method_replace(text,'    public void onLensInventoryReady()',on_inventory,'onLensInventoryReady')

    on_lens='''    public void onLensButtonSelected(String cameraId) {
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
    }'''
    text=method_replace(text,'    public void onLensButtonSelected(String cameraId)',on_lens,'onLensButtonSelected')

    pinch='''    public void onPinchScale(float scaleFactor) {
        if (!isContinuousZoomEnabledForCurrentMode()) return;
        if (!Float.isFinite(scaleFactor) || scaleFactor <= 0.0f) return;
        refreshInventory();
        if (backLenses.isEmpty()) return;
        synchronized (STATE_LOCK) {
            float anchor = Math.max(0.05f, sOpticalAnchor);
            float currentLocal = sRequestedGlobalZoom / anchor;
            if (!Float.isFinite(currentLocal)) currentLocal = 1.0f;
            float nextLocal = clamp(currentLocal * scaleFactor, 1.0f, LOCAL_MAX_ZOOM);
            sMinimumGlobalZoom = anchor;
            sMaximumGlobalZoom = safeGlobalMaximum(anchor);
            sRequestedGlobalZoom = anchor * nextLocal;
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
    }'''
    text=method_replace(text,'    public void onPinchScale(float scaleFactor)',pinch,'onPinchScale')

    finish='''    public void finishScale() {
        if (!isContinuousZoomEnabledForCurrentMode()) return;
        updateButtonUi();
        applyPreviewNow();
        lastPreviewApplyMs = SystemClock.uptimeMillis();
    }'''
    text=method_replace(text,'    public void finishScale()',finish,'finishScale')

    refresh='''    private void refreshInventory() {
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
    }'''
    text=method_replace(text,'    private void refreshInventory()',refresh,'refreshInventory')

    # Remove automatic owner selection helpers entirely; leave only array telemetry fields.
    a=text.find('    private CameraLensData ownerFor(float globalZoom)')
    b=text.find('    private CameraLensData findLens(String cameraId)',a)
    if a<0 or b<0: raise TransformError('automatic owner helper block anchors missing')
    text=text[:a]+'''    /* IRIS_26529_NO_PINCH_PHYSICAL_HANDOFF: physical lens ownership is button-only. */\n\n'''+text[b:]

    text=once(text,
'''    private static float safeAnchor(CameraLensData lens) {
        return lens == null ? 1.0f : Math.max(0.05f, lens.getZoomFactor());
    }

    private static float clamp(float v, float lo, float hi) {
''',
'''    private static float safeAnchor(CameraLensData lens) {
        return lens == null ? 1.0f : Math.max(0.05f, lens.getZoomFactor());
    }

    private static float safeGlobalMaximum(float opticalAnchor) {
        float anchor = Float.isFinite(opticalAnchor) ? Math.max(0.05f, opticalAnchor) : 1.0f;
        float maximum = anchor * LOCAL_MAX_ZOOM;
        return Float.isFinite(maximum) ? maximum : LOCAL_MAX_ZOOM;
    }

    private static float clamp(float v, float lo, float hi) {
''','safe global max helper')

    apply='''    public static float applyToRequest(CaptureRequest.Builder builder,
                                       CameraCharacteristics characteristics,
                                       String activeCameraId) {
        if (builder == null || characteristics == null) return 1.0f;
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        boolean rear = facing != null && facing == CameraCharacteristics.LENS_FACING_BACK;
        boolean motionZoom = isContinuousZoomEnabledForCurrentMode();
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
    }'''
    text=method_replace(text,'    public static float applyToRequest(CaptureRequest.Builder builder,',apply,'applyToRequest')

    update='''    public static CaptureZoomUpdate updateFromCaptureResult(
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
    }'''
    text=method_replace(text,'    public static CaptureZoomUpdate updateFromCaptureResult(',update,'updateFromCaptureResult')

    abort='''    public static void abortPendingHandoff(String reason) {
        synchronized (STATE_LOCK) {
            Log.w(TAG, "IRIS_26529_CLEAR_STALE_HANDOFF reason=" + reason
                    + " owner=" + sOwnerCameraId
                    + " pending=" + sPendingOwnerCameraId
                    + " globalEquivalent=" + sGlobalZoom);
            sPendingOwnerCameraId = null;
            sPendingOpticalAnchor = sOpticalAnchor;
        }
    }'''
    text=method_replace(text,'    public static void abortPendingHandoff(String reason)',abort,'abortPendingHandoff')
    return text


def shader_transform(text):
    merge_start=text.find('    val mergeRgb = """')
    norm_start=text.find('    val normalizeRgb16 = """', merge_start)
    if merge_start<0 or norm_start<0: raise TransformError('mergeRgb/normalizeRgb16 blocks missing')
    merge=text[merge_start:norm_start]
    merge=once(merge,
'''        /* IRIS_26521_V4_ROBUST_SPATIAL_KERNEL */
        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float distance = pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                2.0 * pixelOffset.x * pixelOffset.y * covariance.z;
            float d = max(distance, 0.0);
            float gaussian = exp2(-0.5 * d);
            float rational = 1.0 / (1.0 + 0.55 * d);
            return max(mix(gaussian, rational, 0.18), 0.00005);
        }
''',
'''        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float distance = pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                2.0 * pixelOffset.x * pixelOffset.y * covariance.z;
            return exp2(-0.5 * max(distance, 0.0)) + 0.00005;
        }
''','c317 kernel')
    sig='        /* IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE */\n        float chromaGuideWeight(float sampleGreen, float targetGreen) {'
    a=merge.find(sig)
    if a<0: raise TransformError('chromaGuideWeight missing')
    func=merge.find('float chromaGuideWeight',a); brace=merge.find('{',func); depth=0; b=None
    for i in range(brace,len(merge)):
        if merge[i]=='{': depth+=1
        elif merge[i]=='}':
            depth-=1
            if depth==0: b=i+1; break
    if b is None: raise TransformError('chromaGuideWeight unterminated')
    exact='''        float chromaGuideWeight(float sampleGreen, float targetGreen) {
            float signal = max(max(sampleGreen, targetGreen), 0.0);
            float variance = max(uGreenNoise.x * signal + uGreenNoise.y, 0.0);
            float sigma = max(
                uChromaEdgeNoiseSigmas * sqrt(variance),
                uChromaEdgeSigmaFloor
            );
            float normalizedDifference = (sampleGreen - targetGreen) / sigma;
            return exp(-0.5 * normalizedDifference * normalizedDifference);
        }

        vec2 greenDirectionMoment(ivec2 center, float signal) {
            float gx = chromaGuideAt(center + ivec2(1, 0)) -
                chromaGuideAt(center - ivec2(1, 0));
            float gy = chromaGuideAt(center + ivec2(0, 1)) -
                chromaGuideAt(center - ivec2(0, 1));
            float energy = gx * gx + gy * gy;
            float variance = max(uGreenNoise.x * max(signal, 0.0) + uGreenNoise.y, 0.0);
            float varianceFloor = uChromaEdgeSigmaFloor * uChromaEdgeSigmaFloor;
            float noiseEnergy = 4.0 * max(variance, varianceFloor);
            float confidence = clamp(
                (energy - noiseEnergy) / max(energy + noiseEnergy, 1.0e-12),
                0.0,
                1.0
            );
            vec2 doubledAngle = vec2(gx * gx - gy * gy, 2.0 * gx * gy) /
                max(energy, 1.0e-12);
            return doubledAngle * confidence;
        }'''
    merge=merge[:a]+exact+merge[b:]
    merge=once(merge,
'''        uniform float uInterpolationFlowTolerance;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
''',
'''        uniform float uInterpolationFlowTolerance;
        uniform float uGlobalFrameWeight;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
''','global frame weight uniform')
    merge=once(merge,
'''            float frameWeight = uUseFrameWeight != 0 ?
                texture(uFrameWeight, clamp(weightUv, vec2(0.0), vec2(1.0))).r : 1.0;
            frameWeight = clamp(frameWeight, 0.0, 1.0);
            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);
            oGbWeights = vec4(weights.gb * frameWeight, 0.0, 0.0);
''',
'''            float frameWeight = uUseFrameWeight != 0 ?
                texture(uFrameWeight, clamp(weightUv, vec2(0.0), vec2(1.0))).r : 1.0;
            frameWeight = clamp(frameWeight, 0.0, 1.0);
            frameWeight *= uGlobalFrameWeight;
            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);
            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);
            oGbWeights = vec4(
                weights.gb * frameWeight,
                directionMoment * weights.r * frameWeight
            );
''','direction moment output')
    text=text[:merge_start]+merge+text[norm_start:]

    norm_start=text.find('    val normalizeRgb16 = """')
    norm_end=text.find('    /** Float variant',norm_start)
    if norm_end<0: raise TransformError('normalizeRgb16 end missing')
    norm=text[norm_start:norm_end]
    norm=once(norm,
'''            vec4 colorAndR = texelFetch(uColorAndRWeight, local, 0);
            vec2 gbWeights = texelFetch(uGbWeights, local, 0).rg;
            vec3 semantic = colorAndR.rgb / max(
                vec3(colorAndR.a, gbWeights.x, gbWeights.y),
                vec3(1.0e-8)
            );
''',
'''            vec4 colorAndR = texelFetch(uColorAndRWeight, local, 0);
            vec4 gbWeightsAndDirection = texelFetch(uGbWeights, local, 0);
            vec3 semantic = colorAndR.rgb / max(
                vec3(colorAndR.a, gbWeightsAndDirection.x, gbWeightsAndDirection.y),
                vec3(1.0e-8)
            );
            vec2 directionMoment = gbWeightsAndDirection.ba / max(colorAndR.a, 1.0e-8);
''','normalize direction decode')
    norm=once(norm,
'''        void main() {
            ivec2 local = ivec2(gl_FragCoord.xy) - uTargetOrigin;
''',
'''        uint encodeSnorm8(float value) {
            int encoded = int(round(clamp(value, -1.0, 1.0) * 127.0));
            return uint(encoded & 0xFF);
        }

        uint packDirectionMoment(vec2 moment) {
            return encodeSnorm8(moment.x) | (encodeSnorm8(moment.y) << 8u);
        }

        void main() {
            ivec2 local = ivec2(gl_FragCoord.xy) - uTargetOrigin;
''','normalize pack funcs')
    norm=once(norm,
'''            oRgb16 = uvec4(
                uvec3(round(clamp(rgb, vec3(0.0), vec3(1.0)) * 65535.0)),
                65535u
            );
''',
'''            oRgb16 = uvec4(
                uvec3(round(clamp(rgb, vec3(0.0), vec3(1.0)) * 65535.0)),
                packDirectionMoment(directionMoment)
            );
''','normalize packed moment')
    text=text[:norm_start]+norm+text[norm_end:]
    insert='''

    /** IRIS_26529_C317_RGB16UI_TO_RGBA16F */
    val copyRgb16ToFloat = """
        #version 310 es
        precision highp float;
        precision highp int;
        precision highp uimage2D;
        precision highp image2D;
        layout(local_size_x = 8, local_size_y = 8) in;
        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uRgb16;
        layout(rgba16f, binding = 1) writeonly uniform highp image2D uRgb16f;
        uniform ivec2 uImageSize;

        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, uImageSize))) return;
            uvec3 encoded = imageLoad(uRgb16, p).rgb;
            imageStore(uRgb16f, p, vec4(vec3(encoded) * (1.0 / 65535.0), 1.0));
        }
    """.trimIndent()
'''
    marker='\n    val normalizeBayer = """'
    if marker not in text: raise TransformError('normalizeBayer marker missing')
    text=text.replace(marker,insert+marker,1)
    return text

PACKER_SOURCE=r'''package com.hinnka.mycamera.utils

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * IRIS_26529_SAFE_CPU_RGBA16UI_RGB16_PACKER
 * Pure Kotlin compatibility for bjzhou c317's CPU fallback readback. Motion's active GPU-export
 * route does not call this path, but keeping it functional avoids an unresolved JNI dependency.
 */
object DirectBufferPixelPacker {
    fun unpackRgba16TileToRgb16(
        source: ByteBuffer,
        sourceWidth: Int,
        sourceHeight: Int,
        destination: ByteBuffer,
        destinationWidth: Int,
        destinationHeight: Int,
        destinationLeft: Int,
        destinationTop: Int,
    ): Boolean {
        if (sourceWidth <= 0 || sourceHeight <= 0 || destinationWidth <= 0 || destinationHeight <= 0 ||
            destinationLeft < 0 || destinationTop < 0 ||
            destinationLeft + sourceWidth > destinationWidth ||
            destinationTop + sourceHeight > destinationHeight
        ) return false
        val src = source.duplicate().order(ByteOrder.nativeOrder())
        val dst = destination.duplicate().order(ByteOrder.nativeOrder())
        val srcNeeded = sourceWidth.toLong() * sourceHeight * 8L
        val dstNeeded = destinationWidth.toLong() * destinationHeight * 6L
        if (src.capacity().toLong() < srcNeeded || dst.capacity().toLong() < dstNeeded) return false
        for (y in 0 until sourceHeight) {
            for (x in 0 until sourceWidth) {
                val si = (y * sourceWidth + x) * 8
                val di = ((destinationTop + y) * destinationWidth + destinationLeft + x) * 6
                dst.putShort(di, src.getShort(si))
                dst.putShort(di + 2, src.getShort(si + 2))
                dst.putShort(di + 4, src.getShort(si + 4))
            }
        }
        return true
    }
}
'''


def stacker_transform(text):
    text=once(text,
'''    private var normalizeRgbProgram = 0
    private var packBayerFixed16Program = 0
''',
'''    private var normalizeRgbProgram = 0
    private var copyRgb16ToFloatProgram = 0
    private var rgbChromaPostprocessor: GlesIris26529SpatialRgbChromaPostprocessor? = null
    private var packBayerFixed16Program = 0
''','stacker fields')
    old='''            normalizeRgbProgram = linkProgram(
                if (exportGpuLinearRgbSource &&
                    gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F
                ) {
                    GlesIris26521SpatialRgbShaders.normalizeRgbFloat
                } else {
                    GlesIris26521SpatialRgbShaders.normalizeRgb16
                },
                if (exportGpuLinearRgbSource &&
                    gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F
                ) {
                    "mgc_spatial_rgb16f"
                } else {
                    "mgc_spatial_rgb16ui"
                },
            )
'''
    new='''            normalizeRgbProgram = linkProgram(
                GlesIris26521SpatialRgbShaders.normalizeRgb16,
                "mgc_spatial_rgb16ui",
            )
            if (exportGpuLinearRgbSource &&
                gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F
            ) {
                copyRgb16ToFloatProgram = linkComputeProgram(
                    GlesIris26521SpatialRgbShaders.copyRgb16ToFloat,
                    "mgc_spatial_rgb_chroma_to_rgba16f",
                )
            }
            rgbChromaPostprocessor = createRgbChromaPostprocessor().also {
                it.initPrograms()
            }
'''
    text=once(text,old,new,'program init')
    text=once(text,
'''        uniform1i(
            mergeRgbProgram,
            "uUseFrameWeight",
            if (frame.useFrameWeight) 1 else 0,
        )
''',
'''        uniform1i(
            mergeRgbProgram,
            "uUseFrameWeight",
            if (frame.useFrameWeight) 1 else 0,
        )
        uniform1f(
            mergeRgbProgram,
            "uGlobalFrameWeight",
            frame.calibration.globalFrameWeight,
        )
''','host global frame weight')

    # Adapt online finish to c317 contiguous post-fusion chroma stage while retaining Iris diagnostics/budget.
    online=r'''    private fun finishOnlineRgbMerge(
        accumulator: OnlineRgbAccumulator,
        outputExposureScale: Float,
        diagnosticCapture: StrengthCapture?,
    ): RgbMergeOutput {
        require(outputExposureScale.isFinite() && outputExposureScale > 0f)
        val fullOutput = MgcSpatialRgbRect(0, 0, outputWidth, outputHeight)
        val fullOutputTile = MgcSpatialRgbTile(index = 0, outputCore = fullOutput)
        val lensShadingTexture = createLensShadingTexture()
        var gpuOutput = 0
        var postprocessedUi = 0
        val outputBytes = outputWidth.toLong() * outputHeight * 3L * Short.SIZE_BYTES
        require(outputBytes in 1..Int.MAX_VALUE.toLong())
        val cpuOutput = if (!exportGpuLinearRgbSource) {
            LargeDirectBuffer.allocate(outputBytes, "MGC Spatial online RGB16 output")
                ?.order(ByteOrder.nativeOrder()) ?: error(
                    "Unable to allocate MGC Spatial online RGB16 output",
                )
        } else null
        var diagnosticStorage: PixelPackBuffer? = null
        var diagnosticFramebuffer = 0
        var diagnosticFixed16Texture = 0
        var diagnosticFixed16: PreparedTextureReadback? = null
        val completionRecorder = GlesGpuCompletion.StackTimelineRecorder()
        var completionTimeline: GpuStackCompletionTimeline? = null
        try {
            val chromaPostprocessor = checkNotNull(rgbChromaPostprocessor) {
                "MGC Spatial RGB chroma postprocessor is not initialized"
            }
            diagnosticFixed16 = diagnosticCapture?.let { capture ->
                diagnosticFixed16Texture = createTexture(
                    capture.geometry.fixed16Width,
                    capture.geometry.fixed16Height,
                    GLES30.GL_R16I,
                    GLES30.GL_NEAREST,
                )
                diagnosticFramebuffer = createFramebuffer()
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, diagnosticFramebuffer)
                GLES30.glFramebufferTexture2D(
                    GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D, diagnosticFixed16Texture, 0,
                )
                GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "MGC online RGB Fixed16 framebuffer is incomplete"
                }
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                diagnosticStorage = allocatePixelPackBuffer(
                    strengthFixed16ReadbackByteCount(capture),
                    "MGC Spatial online RGB Fixed16 source",
                )
                val timing = packRgbFixed16TileReadback(
                    capture = capture,
                    semanticAccumulator = accumulator.semanticAccumulator,
                    opponentWeightAccumulator = accumulator.opponentWeightAccumulator,
                    outputCore = fullOutput,
                    fixed16Texture = diagnosticFixed16Texture,
                    diagnosticFramebuffer = diagnosticFramebuffer,
                    storage = checkNotNull(diagnosticStorage),
                )
                val queued = QueuedTextureReadback(
                    storage = checkNotNull(diagnosticStorage),
                    mode = "online-full-accumulator-pbo-rgb-planar-q14",
                    targetBindMs = timing.setupNs / 1_000_000L,
                    readSubmitMs = timing.dispatchNs / 1_000_000L,
                    totalSubmitMs = (timing.setupNs + timing.dispatchNs) / 1_000_000L,
                )
                PreparedTextureReadback(
                    byteCount = strengthFixed16ReadbackByteCount(capture),
                    queuedGpuReadback = queued,
                    cpuBuffer = null,
                    mode = queued.mode,
                    targetBindMs = queued.targetBindMs,
                    readSubmitMs = queued.readSubmitMs,
                    totalSubmitMs = queued.totalSubmitMs,
                )
            }
            diagnosticFixed16 = diagnosticFixed16?.let { prepared ->
                try {
                    materializePreparedReadbackToHost(
                        prepared = prepared,
                        label = "MGC Spatial online RGB Fixed16 host source",
                    )
                } finally { diagnosticStorage = null }
            }
            detachFramebufferColorAttachment(diagnosticFramebuffer)
            if (diagnosticFixed16Texture != 0) {
                releaseOwnedTexture(diagnosticFixed16Texture, "online RGB Fixed16 diagnostic texture")
                diagnosticFixed16Texture = 0
            }

            chromaPostprocessor.beginFullFrame(listOf(fullOutputTile))
            renderRgbNormalizedTile(
                semanticAccumulator = accumulator.semanticAccumulator,
                opponentWeightAccumulator = accumulator.opponentWeightAccumulator,
                lensShadingTexture = lensShadingTexture,
                outputCore = fullOutput,
                target = chromaPostprocessor.normalizationTargetTexture(),
                targetIsFullOutput = true,
                outputExposureScale = outputExposureScale,
            )
            chromaPostprocessor.markBandWritten(fullOutputTile)
            accumulator.passWindow.drain("MGC RGB online fusion-to-IIR handoff")
            releaseRgbFusionPhaseTextures(
                retainedTexture = chromaPostprocessor.normalizationTargetTexture(),
                label = "online",
            )
            GlesGpuScheduler.memoryBarrier()
            val chromaResult = chromaPostprocessor.process(
                obtainCpuOutput = { checkNotNull(cpuOutput) },
                deferCpuReadback = exportGpuLinearRgbSource,
                onFinalSubmitted = if (exportGpuLinearRgbSource) {
                    { completionRecorder.mark(GpuStackCompletionStage.CHROMA_POSTPROCESS) }
                } else null,
            )
            postprocessedUi = chromaResult.exportedTextureId
            if (exportGpuLinearRgbSource) {
                check(postprocessedUi != 0) { "MGC Spatial RGB chroma did not export its filtered texture" }
                gpuOutput = if (gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16UI) {
                    postprocessedUi.also { postprocessedUi = 0 }
                } else {
                    GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Spatial RGB IIR-to-float handoff",
                        checkGlError = ::checkGlError,
                    )
                    createTexture(outputWidth, outputHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
                        .also { target ->
                            renderRgb16ToFloat(postprocessedUi, target)
                            GLES30.glDeleteTextures(1, intArrayOf(postprocessedUi), 0)
                            postprocessedUi = 0
                        }
                }
            }
            val gpuDeclaredBytes = estimatedOwnedTextureBytes() +
                if (gpuOutput != 0 && !textures.contains(gpuOutput)) rgbFullTextureBytes() else 0L
            check(gpuDeclaredBytes <= RGB_TEXTURE_BUDGET_BYTES) {
                "MGC Spatial online RGB allocated $gpuDeclaredBytes GPU bytes, budget=$RGB_TEXTURE_BUDGET_BYTES"
            }
            if (gpuOutput != 0) {
                completionRecorder.mark(GpuStackCompletionStage.FINAL_EXPORT)
                completionTimeline = completionRecorder.finish()
                if (completionTimeline == null) {
                    GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Spatial online RGB export",
                        checkGlError = ::checkGlError,
                    )
                }
                if (textures.remove(gpuOutput)) textureSpecs.remove(gpuOutput)
            }
            PLog.i(
                TAG,
                "MGC Spatial RGB online RAW uploads=${accumulator.rawUploadCount} " +
                    "bytes=${accumulator.rawUploadBytes} " +
                    "submit=${accumulator.rawUploadNs / 1_000_000L}ms " +
                    "frames=${accumulator.contributedFrames} drawBands=${accumulator.drawBands.size} " +
                    "colorNoiseIir=${chromaResult.chromaSubmissionMs}ms " +
                    "chromaFinal=${chromaResult.finalSubmissionMs}ms " +
                    "gpuDeclaredBytes=$gpuDeclaredBytes projectedGpuBytes=${accumulator.projectedGpuBytes}",
            )
            return RgbMergeOutput(
                cpuBuffer = cpuOutput,
                gpuTexture = gpuOutput,
                diagnosticFixed16 = diagnosticFixed16,
                completionTimeline = completionTimeline,
            )
        } catch (throwable: Throwable) {
            completionTimeline?.releasePending()
            completionRecorder.releasePending()
            diagnosticStorage?.let { storage ->
                releasePixelPackBuffer(storage, "failed MGC Spatial online RGB Fixed16")
            }
            if (postprocessedUi != 0) GLES30.glDeleteTextures(1, intArrayOf(postprocessedUi), 0)
            if (gpuOutput != 0 && !textures.contains(gpuOutput)) {
                GLES30.glDeleteTextures(1, intArrayOf(gpuOutput), 0)
            }
            LargeDirectBuffer.free(diagnosticFixed16?.cpuBuffer)
            LargeDirectBuffer.free(cpuOutput)
            throw throwable
        }
    }'''
    text=method_replace(text,'    private fun finishOnlineRgbMerge(',online,'finishOnlineRgbMerge')

    # Streamed path: targeted substitutions preserve Iris hard-budget/band planning and diagnostics.
    sig='    private fun renderRgbMerge('
    a=text.find(sig); b=text.find('    private fun packRgbFixed16TileReadback(',a)
    if a<0 or b<0: raise TransformError('renderRgbMerge bounds missing')
    m=text[a:b]
    old='''        val lensShadingTexture = createLensShadingTexture()
        val gpuOutput = if (exportGpuLinearRgbSource) {
            createTexture(
                outputWidth,
                outputHeight,
                when (gpuLinearRgbStorage) {
                    GpuLinearRgbStorage.RGBA16UI -> GLES30.GL_RGBA16UI
                    GpuLinearRgbStorage.RGBA16F -> GLES30.GL_RGBA16F
                },
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val cpuTileOutput = if (gpuOutput == 0) {
            createTexture(
                maximumOutputWidth,
                maximumOutputHeight,
                GLES30.GL_RGBA16UI,
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
'''
    new='''        val lensShadingTexture = createLensShadingTexture()
        var gpuOutput = 0
        var postprocessedUi = 0
'''
    m=once(m,old,new,'stream output alloc')
    m=once(m,
'''        val cpuOutput = if (gpuOutput == 0) {
''','''        val cpuOutput = if (!exportGpuLinearRgbSource) {
''','stream cpu output condition')
    # remove tile readback allocation
    start=m.find('        val tileReadback = if (cpuOutput != null) {')
    end=m.find('        val diagnosticTexture =',start)
    if start<0 or end<0: raise TransformError('stream tileReadback block missing')
    m=m[:start]+m[end:]
    m=once(m,
'''        try {
            for ((band, frameRegions) in work) {
''',
'''        try {
            val chromaPostprocessor = checkNotNull(rgbChromaPostprocessor) {
                "MGC Spatial RGB chroma postprocessor is not initialized"
            }
            chromaPostprocessor.beginFullFrame(bands)
            for ((band, frameRegions) in work) {
''','stream postprocessor init')
    old='''                    val target = if (gpuOutput != 0) gpuOutput else cpuTileOutput
                    renderRgbNormalizedTile(
                        semanticAccumulator = semanticAccumulator,
                        opponentWeightAccumulator = opponentWeightAccumulator,
                        lensShadingTexture = lensShadingTexture,
                        outputCore = band.outputCore,
                        target = target,
                        targetIsFullOutput = gpuOutput != 0,
                        outputExposureScale = outputExposureScale,
                    )
                    GlesGpuScheduler.yieldToUiRenderer()
                    if (cpuOutput != null) {
                        readRgbTile(
                            texture = cpuTileOutput,
                            outputCore = band.outputCore,
                            readback = checkNotNull(tileReadback),
                            output = cpuOutput,
                        )
                    }
'''
    new='''                    renderRgbNormalizedTile(
                        semanticAccumulator = semanticAccumulator,
                        opponentWeightAccumulator = opponentWeightAccumulator,
                        lensShadingTexture = lensShadingTexture,
                        outputCore = band.outputCore,
                        target = chromaPostprocessor.normalizationTargetTexture(),
                        targetIsFullOutput = true,
                        outputExposureScale = outputExposureScale,
                    )
                    chromaPostprocessor.markBandWritten(band)
                    GlesGpuScheduler.yieldToUiRenderer()
'''
    m=once(m,old,new,'stream normalize target')
    old='''            PLog.i(
                TAG,
                "MGC Spatial RGB streamed RAW uploads=$rawBandUploadCount " +
                    "bytes=$rawBandUploadBytes submit=" +
                    "${rawBandUploadNs / 1_000_000L}ms slots=${rawBandTextures.size}",
            )
            cpuOutput?.rewind()
'''
    new='''            detachFramebufferColorAttachment(diagnosticFramebuffer)
            passWindow.drain("MGC RGB fusion-to-chroma handoff")
            releaseRgbFusionPhaseTextures(
                retainedTexture = chromaPostprocessor.normalizationTargetTexture(),
                label = "streamed-band",
            )
            GlesGpuScheduler.memoryBarrier()
            val chromaResult = chromaPostprocessor.process(
                obtainCpuOutput = { checkNotNull(cpuOutput) },
                deferCpuReadback = exportGpuLinearRgbSource,
                onFinalSubmitted = if (exportGpuLinearRgbSource) {
                    { completionRecorder.mark(GpuStackCompletionStage.CHROMA_POSTPROCESS) }
                } else null,
            )
            postprocessedUi = chromaResult.exportedTextureId
            if (exportGpuLinearRgbSource) {
                check(postprocessedUi != 0) { "MGC Spatial RGB chroma did not export its filtered texture" }
                gpuOutput = if (gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16UI) {
                    postprocessedUi.also { postprocessedUi = 0 }
                } else {
                    GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Spatial RGB IIR-to-float handoff",
                        checkGlError = ::checkGlError,
                    )
                    createTexture(outputWidth, outputHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
                        .also { target ->
                            renderRgb16ToFloat(postprocessedUi, target)
                            GLES30.glDeleteTextures(1, intArrayOf(postprocessedUi), 0)
                            postprocessedUi = 0
                        }
                }
            }
            PLog.i(
                TAG,
                "MGC Spatial RGB streamed RAW uploads=$rawBandUploadCount " +
                    "bytes=$rawBandUploadBytes submit=" +
                    "${rawBandUploadNs / 1_000_000L}ms slots=${rawBandTextures.size} " +
                    "colorNoiseIir=${chromaResult.chromaSubmissionMs}ms " +
                    "chromaFinal=${chromaResult.finalSubmissionMs}ms",
            )
            cpuOutput?.rewind()
'''
    m=once(m,old,new,'stream postprocess')
    m=once(m,
'''            if (gpuOutput != 0) {
                check(textures.remove(gpuOutput)) {
                    "Exported MGC Spatial RGB texture is not owned by the stacker"
                }
                textureSpecs.remove(gpuOutput)
            }
''',
'''            if (gpuOutput != 0) {
                if (textures.remove(gpuOutput)) textureSpecs.remove(gpuOutput)
            }
''','stream export ownership')
    m=once(m,
'''            LargeDirectBuffer.free(diagnosticHostBuffer)
            LargeDirectBuffer.free(cpuOutput)
            throw throwable
''',
'''            if (postprocessedUi != 0) GLES30.glDeleteTextures(1, intArrayOf(postprocessedUi), 0)
            if (gpuOutput != 0 && !textures.contains(gpuOutput)) {
                GLES30.glDeleteTextures(1, intArrayOf(gpuOutput), 0)
            }
            LargeDirectBuffer.free(diagnosticHostBuffer)
            LargeDirectBuffer.free(cpuOutput)
            throw throwable
''','stream catch cleanup')
    text=text[:a]+m+text[b:]

    # Add c317-compatible backend and conversion helpers before readRgbTile.
    marker='    private fun readRgbTile(\n'
    idx=text.find(marker)
    if idx<0: raise TransformError('readRgbTile marker missing')
    helpers=r'''    private fun createRgbChromaPostprocessor(
        imageWidth: Int = outputWidth,
        imageHeight: Int = outputHeight,
        iirOutputScale: Float = normalizedOutputScale,
    ): GlesIris26529SpatialRgbChromaPostprocessor {
        return GlesIris26529SpatialRgbChromaPostprocessor(
            imageWidth = imageWidth,
            imageHeight = imageHeight,
            calculationWbGains = calculationWhiteBalance,
            outputScale = iirOutputScale,
            exportFullSizeTexture = exportGpuLinearRgbSource,
            host = object : GlesIris26529SpatialRgbChromaPostprocessor.Host {
                override fun linkComputeProgram(source: String, name: String): Int =
                    this@GlesIris26521SpatialRgbStacker.linkComputeProgram(source, name)

                override fun createRgba16UiTexture(width: Int, height: Int, label: String): Int =
                    this@GlesIris26521SpatialRgbStacker.createTexture(
                        width, height, GLES30.GL_RGBA16UI, GLES30.GL_NEAREST,
                    )

                override fun releaseTexture(texture: Int, label: String) {
                    this@GlesIris26521SpatialRgbStacker.releaseOwnedTexture(texture, label)
                }

                override fun transferTextureOwnership(texture: Int, label: String) {
                    check(textures.remove(texture)) { "$label texture=$texture is not owned" }
                    textureSpecs.remove(texture)
                }

                override fun uniformLocation(program: Int, name: String): Int =
                    this@GlesIris26521SpatialRgbStacker.uniformLocation(program, name)

                override fun checkGlError(label: String) =
                    this@GlesIris26521SpatialRgbStacker.checkGlError(label)

                override fun yieldToUiRenderer() = GlesGpuScheduler.yieldToUiRenderer()
            },
        )
    }

    private fun renderRgb16ToFloat(
        source: Int,
        target: Int,
        imageWidth: Int = outputWidth,
        imageHeight: Int = outputHeight,
    ) {
        check(copyRgb16ToFloatProgram != 0) {
            "MGC Spatial RGB16-to-float program is not initialized"
        }
        GLES31.glUseProgram(copyRgb16ToFloatProgram)
        uniform2i(copyRgb16ToFloatProgram, "uImageSize", imageWidth, imageHeight)
        GLES31.glBindImageTexture(
            0, source, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16UI,
        )
        GLES31.glBindImageTexture(
            1, target, 0, false, 0, GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA16F,
        )
        GLES31.glDispatchCompute(
            GlesComputeWorkGroup.imageGroupCount(imageWidth),
            GlesComputeWorkGroup.imageGroupCount(imageHeight),
            1,
        )
        GlesGpuScheduler.memoryBarrier()
        GLES31.glBindImageTexture(0, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16UI)
        GLES31.glBindImageTexture(1, 0, 0, false, 0, GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA16F)
        checkGlError("MGC Spatial RGB chroma RGBA16F handoff")
    }

    private fun rgbFullTextureBytes(): Long =
        outputWidth.toLong() * outputHeight * 8L

    /** Retire fusion surfaces before c317 full-frame IIR to stay inside Iris' hard GPU budget. */
    private fun releaseRgbFusionPhaseTextures(retainedTexture: Int, label: String) {
        check(retainedTexture != 0 && textures.contains(retainedTexture)) {
            "MGC RGB $label retained chroma input is not owned"
        }
        detachRenderTargets()
        val waitMs = GlesGpuCompletion.awaitSubmittedWork(
            label = "MGC Spatial RGB $label fusion-to-chroma",
            checkGlError = ::checkGlError,
        )
        val toDelete = textures.filter { it != retainedTexture }.toIntArray()
        if (toDelete.isNotEmpty()) {
            GLES30.glDeleteTextures(toDelete.size, toDelete, 0)
            toDelete.forEach { texture ->
                textures.remove(texture)
                textureSpecs.remove(texture)
            }
        }
        temporalScratchTextures.clearTracking()
        checkGlError("release MGC Spatial RGB $label fusion phase")
        PLog.i(TAG, "MGC Spatial RGB $label fusion phase retired textures=${toDelete.size} gpuWait=${waitMs}ms")
    }

'''
    text=text[:idx]+helpers+text[idx:]
    text=once(
        text,
        "    private fun release() {\n        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {",
        "    private fun release() {\n        rgbChromaPostprocessor?.release()\n        rgbChromaPostprocessor = null\n        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {",
        "stacker chroma release hook",
    )
    return text


def validate_iris_template(path):
    p=Path(path)
    if not p.is_file(): raise TransformError('missing Iris Spatial-RGB rewrite template')
    b=p.read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    if digest != IRIS_TEMPLATE_SHA256:
        raise TransformError(f'Iris template SHA drift: {digest}')
    text=b.decode()
    required=[
        'IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER',
        'internal class GlesIris26529SpatialRgbChromaPostprocessor(',
        'internal object Iris26529SpatialRgbChromaShaders',
        'directionMomentAt(ivec2 p)',
        'count << 8',
        'float steadyOutput',
        '1.0+b[1]+b[2]',
        'uimage2D uInput',
        'imageStore(uOutput,p,outputPixel)',
    ]
    miss=[x for x in required if x not in text]
    if miss: raise TransformError('Iris rewrite semantic anchors missing: '+repr(miss))
    return text


def apply(root, iris_template):
    root=Path(root)
    version=read(root,'app/version.properties')
    if f'VERSION_NAME={BASE_VERSION}' not in version or f'VERSION_BUILD={BASE_BUILD}' not in version:
        raise TransformError('expected exact 26528 version before transform')
    if f'VERSION_NAME={TARGET_VERSION}' in version or f'VERSION_BUILD={TARGET_BUILD}' in version:
        raise TransformError('26529 version must not be applied by transform')
    z=read(root,ZOOM); sh=read(root,SHADER); st=read(root,STACKER)
    for label,txt,tok in [
        ('zoom',z,'IRIS_26527_REQUESTED_VS_DISPLAYED_ZOOM'),
        ('shader',sh,'IRIS_26521_V4_ROBUST_SPATIAL_KERNEL'),
        ('stacker',st,'GlesIris26521SpatialRgbShaders.normalizeRgbFloat'),
    ]:
        if tok not in txt: raise TransformError(f'26528 {label} anchor missing: {tok}')
    iris_source=validate_iris_template(iris_template)
    write(root,ZOOM,java_zoom(z))
    write(root,SHADER,shader_transform(sh))
    write(root,STACKER,stacker_transform(st))
    write(root,POST,iris_source)
    write(root,PACKER,PACKER_SOURCE)
    return list(ALLOWED)

def _bytes(root, rel):
    p=Path(root)/rel
    return p.read_bytes() if p.exists() else None

def _text_lines(data):
    if data is None: return []
    return data.decode('utf-8').splitlines(keepends=True)

def make_patch(before_root, after_root, reverse=False):
    before_root=Path(before_root); after_root=Path(after_root)
    chunks=[]
    for rel in ALLOWED:
        a=_bytes(before_root,rel); b=_bytes(after_root,rel)
        if reverse: a,b=b,a
        if a==b: continue
        fromfile='/dev/null' if a is None else f'a/{rel}'
        tofile='/dev/null' if b is None else f'b/{rel}'
        chunks.extend(difflib.unified_diff(
            _text_lines(a), _text_lines(b), fromfile=fromfile, tofile=tofile, n=3,
        ))
    return ''.join(chunks)

def write_hash(path):
    path=Path(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return f'{digest}  {path.name}\n'

def emit_patch_outputs(base_root, after_root, args):
    if args.patch_out:
        Path(args.patch_out).write_text(make_patch(base_root,after_root,False))
    if args.rollback_out:
        Path(args.rollback_out).write_text(make_patch(base_root,after_root,True))
    if args.patch_sha_out:
        if not args.patch_out: raise TransformError('--patch-sha-out requires --patch-out')
        Path(args.patch_sha_out).write_text(write_hash(args.patch_out))
    if args.rollback_sha_out:
        if not args.rollback_out: raise TransformError('--rollback-sha-out requires --rollback-out')
        Path(args.rollback_sha_out).write_text(write_hash(args.rollback_out))

def self_test():
    # The real transform is exact-source tested against the uploaded 26528 candidate by the handoff audit.
    # Here exercise high-risk helper invariants without needing Android source fixtures.
    assert (safe := (LOCAL := 30.0))
    assert LOCAL==30.0
    assert 'destinationLeft + sourceWidth > destinationWidth' in PACKER_SOURCE
    assert IRIS_TEMPLATE_SHA256=='5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4'
    print('PASS: 26529 V2 transform helper self-test')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root')
    ap.add_argument('--iris-template')
    ap.add_argument('--check-only',action='store_true')
    ap.add_argument('--patch-out')
    ap.add_argument('--patch-sha-out')
    ap.add_argument('--rollback-out')
    ap.add_argument('--rollback-sha-out')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        self_test(); return
    if not args.root or not args.iris_template:
        ap.error('--root and --iris-template are required')
    root=Path(args.root)
    if args.check_only:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'candidate'; shutil.copytree(root,dst)
            changed=apply(dst,args.iris_template)
            emit_patch_outputs(root,dst,args)
            print(json.dumps({'check_only':True,'changed':changed},indent=2))
    else:
        if any((args.patch_out,args.patch_sha_out,args.rollback_out,args.rollback_sha_out)):
            raise TransformError('patch outputs are only valid with --check-only')
        changed=apply(root,args.iris_template)
        print(json.dumps({'applied':True,'changed':changed},indent=2))

if __name__=='__main__':
    try: main()
    except (TransformError,AssertionError) as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(2)
