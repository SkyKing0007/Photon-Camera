#!/usr/bin/env python3
from __future__ import annotations
import argparse,difflib,hashlib,re
from pathlib import Path

DNG_CREATOR='app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java'
IMAGE_SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'
IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
TOUCH_FOCUS='app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java'
SWIPE='app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java'
CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
PREFS='app/src/main/res/xml/preferences.xml'
CHANGED={DNG_CREATOR,IMAGE_SAVER,IRIS_STACK,IRIS_SHADER,TOUCH_FOCUS,SWIPE,CAPTURE,PREFS}

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def one(s:str,old:str,new:str,label:str)->str:
    n=s.count(old)
    if n!=1:
        raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)

def regex_one(s:str,pattern:str,repl:str,label:str)->str:
    out,n=re.subn(pattern,repl,s,count=1,flags=re.S)
    if n!=1:
        raise AssertionError(f'{label} regex count={n} expected=1')
    return out

def dng_creator_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26523_DNG_SINGLE_METADATA_OWNERSHIP' in s:
        raise AssertionError('26523 DngCreator transform already present')
    sig='''    public void setParameters(Parameters parameters) {\n'''
    repl='''    public void setParameters(Parameters parameters) {
        setParameters(parameters, true, true);
    }

    /* IRIS_26523_DNG_SINGLE_METADATA_OWNERSHIP
     * Ordinary RAW calls keep the historical setParameters(parameters) behavior. The overload is
     * used only by the synthetic normalized16 stacked-DNG writer so its ImageDescription and
     * NoiseProfile are emitted once rather than appended after one-frame values.
     */
    public void setParameters(Parameters parameters, boolean includeDescription, boolean includeNoiseProfile) {
'''
    s=one(s,sig,repl,'DngCreator overload')
    s=one(s,'        setDescription(parameters.toString());\n',
          '        if (includeDescription) setDescription(parameters.toString());\n',
          'DngCreator description gate')
    s=one(s,
          '        if (parameters.noiseModeler != null && parameters.noiseModeler.baseModel != null) {\n',
          '        if (includeNoiseProfile && parameters.noiseModeler != null && parameters.noiseModeler.baseModel != null) {\n',
          'DngCreator noise gate')
    return s

def image_saver_expected(text:str)->str:
    s=norm(text)
    marker='IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER'
    a=s.find(marker)
    if a<0: raise AssertionError('26522 normalized16 writer missing')
    b=s.find('        public static boolean saveSingleRaw(',a)
    if b<0: raise AssertionError('saveSingleRaw boundary missing')
    block=s[a:b]
    old='                dngCreator.setParameters(parameters);\n'
    if block.count(old)!=1: raise AssertionError(f'stacked writer setParameters count={block.count(old)} expected=1')
    block=block.replace(old,'                dngCreator.setParameters(parameters, false, false);\n',1)
    block=one(block,
              '                                + " NoiseEquivalentSupport=" + noiseEquivalentSupport\n',
              '                                + " FrameEquivalentNoiseSupport=" + noiseEquivalentSupport\n',
              'stacked DNG support description label')
    block=one(block,
              '                                + " NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicEffectiveSupport");\n',
              '                                + " NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicReferenceFrameEquivalentSupport"\n'
              '                                + " IRIS_26523_SINGLE_METADATA=true");\n',
              'stacked DNG noise-profile basis')
    return s[:a]+block+s[b:]

def iris_shader_expected(text:str)->str:
    s=norm(text)
    # Track the sum of squared *individual Spatial sample weights* for each frame. This is the
    # missing variance term in 26522: squaring the already-summed per-frame kernel weight is not
    # equivalent when one frame contributes several same-CFA observations.
    s=one(s,
          '            float intensity = 0.0;\n            float accumulatedWeight = 0.0;\n',
          '''            float intensity = 0.0;
            float accumulatedWeight = 0.0;
            float accumulatedWeightSquared = 0.0;
''',
          '26523 per-sample kernel variance accumulator')
    s=one(s,'                        accumulatedWeight += weight;\n',
          '                        accumulatedWeight += weight;\n                        accumulatedWeightSquared += weight * weight;\n',
          '26523 primary kernel squared weight')
    s=one(s,'                            accumulatedWeight += otherWeight;\n',
          '                            accumulatedWeight += otherWeight;\n                            accumulatedWeightSquared += otherWeight * otherWeight;\n',
          '26523 diagonal-green kernel squared weight')
    old='''            /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_ACCUMULATOR
             * z accumulates each frame's squared contribution weight / 256. The existing r/g
             * signal and sum-weight channels remain unchanged, so RGB/JPEG math is untouched.
             */
            float contributionWeight = accumulatedWeight * frameWeight;
            oBayerAndWeight = vec4(
                intensity * frameWeight,
                contributionWeight,
                contributionWeight * contributionWeight / 256.0,
                0.0
            );
'''
    new='''            /* IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS
             * Preserve the tested 26522 Bayer signal and normalization channels exactly:
             *   r = weighted signal, g = sum of Spatial sample weights * temporal robustness.
             *
             * b accumulates the variance weight sum over INDIVIDUAL same-CFA observations:
             *   sum(frameWeight^2 * sum(kernelWeight_i^2)).
             * a stores the reference frame's own normalized Spatial-kernel variance once.
             * Together these yield frame-equivalent noise support relative to the reference
             * frame's own reconstruction kernel, without confusing kernel geometry with temporal
             * rejection as 26522 did.
             */
            float contributionWeight = accumulatedWeight * frameWeight;
            float contributionVarianceWeight =
                accumulatedWeightSquared * frameWeight * frameWeight;
            float referenceNormalizedKernelVariance = uUseFrameWeight == 0
                ? accumulatedWeightSquared /
                    max(accumulatedWeight * accumulatedWeight, 1.0e-12)
                : 0.0;
            oBayerAndWeight = vec4(
                intensity * frameWeight,
                contributionWeight,
                contributionVarianceWeight,
                referenceNormalizedKernelVariance
            );
'''
    s=one(s,old,new,'26523 frame-equivalent support moments')
    s=one(s,'    /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_Q8 */\n',
          '    /* IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8 */\n',
          '26523 support shader marker')
    old_formula='''            float sumW = max(accumulated.g, 0.0);
            float sumW2 = max(accumulated.b * 256.0, 0.0);
            float effective = 1.0;
            if (sumW > 1.0e-8 && sumW2 > 1.0e-12) {
                effective = sumW * sumW / sumW2;
            }
'''
    new_formula='''            float sumW = max(accumulated.g, 0.0);
            float sumIndividualW2 = max(accumulated.b, 0.0);
            float referenceNormalizedVariance = max(accumulated.a, 0.0);
            float effective = 1.0;
            if (sumW > 1.0e-8 && sumIndividualW2 > 1.0e-12 &&
                referenceNormalizedVariance > 1.0e-12) {
                effective = referenceNormalizedVariance * sumW * sumW / sumIndividualW2;
            }
'''
    s=one(s,old_formula,new_formula,'26523 frame-equivalent support formula')
    return s

def iris_stack_expected(text:str)->str:
    s=norm(text)
    s=one(s,'    /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_STATS */\n',
          '''    /* IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_STATS
     * Per-pixel support is now expressed in reference-frame-equivalent units. The denominator
     * uses squared INDIVIDUAL Spatial sample weights, while the numerator uses the exact tested
     * Bayer normalization weight. This keeps Spatial kernel geometry and temporal rejection in
     * the variance calculation without the 26522 sum-then-square bias.
     */
''','26523 support stats marker')
    s=s.replace('"IRIS_26522_DNG_EFFECTIVE_SUPPORT grid=${supportWidth}x$supportHeight " +',
                '"IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT grid=${supportWidth}x$supportHeight " +')
    s=s.replace('"supportMin=${normalStackedDngSupport.minimum} " +',
                '"frameEquivalentSupportMin=${normalStackedDngSupport.minimum} " +')
    s=s.replace('"supportP01=${normalStackedDngSupport.p01} " +',
                '"frameEquivalentSupportP01=${normalStackedDngSupport.p01} " +')
    s=s.replace('"supportP10=${normalStackedDngSupport.p10} " +',
                '"frameEquivalentSupportP10=${normalStackedDngSupport.p10} " +')
    s=s.replace('"supportMedian=${normalStackedDngSupport.median} " +',
                '"frameEquivalentSupportMedian=${normalStackedDngSupport.median} " +')
    s=s.replace('"supportMean=${normalStackedDngSupport.mean} " +',
                '"frameEquivalentSupportMean=${normalStackedDngSupport.mean} " +')
    s=s.replace('"supportMax=${normalStackedDngSupport.maximum} " +',
                '"frameEquivalentSupportMax=${normalStackedDngSupport.maximum} " +')
    s=s.replace('"noiseEquivalentSupport=${normalStackedDngSupport.noiseEquivalent} " +',
                '"frameEquivalentNoiseSupport=${normalStackedDngSupport.noiseEquivalent} " +')
    old_comment='''    /* Camera2 SENSOR_NOISE_PROFILE is defined in normalized [0,1] signal units.
     * The normal Motion population is equal-exposure; divide the reference profile by the
     * measured harmonic effective support so the synthetic DNG describes the fused variance
     * rather than inheriting a stale one-frame/slider-count model.
     */
'''
    new_comment='''    /* Camera2 SENSOR_NOISE_PROFILE is defined in normalized [0,1] signal units.
     * The NORMAL Motion population is equal-exposure. Divide the reference profile by the
     * harmonic reference-frame-equivalent support measured from the exact Bayer merge weights.
     * The support calculation includes individual Spatial kernel weights and temporal robustness,
     * and is clamped to the admitted NORMAL frame count so the global DNG profile never claims
     * more frame-equivalent reduction than the burst actually contains.
     */
'''
    s=one(s,old_comment,new_comment,'26523 noise profile comment')
    return s

def prefs_expected(text:str)->str:
    s=norm(text)
    old='''            <Preference ns0:layout="@layout/preference_about" ns0:title="@string/app_name" ns0:summary="@string/photon_camera_summary" ns0:key="@string/pref_photoncamera" ns0:enabled="false" ns0:icon="@drawable/ic_splash" />
'''
    new='''            <!-- IRIS_26523_ABOUT_MINIMAL_IRIS -->
            <Preference ns0:layout="@layout/preference_about" ns0:title="@string/app_name" ns0:key="@string/pref_photoncamera" ns0:enabled="false" ns0:icon="@mipmap/ic_launcher" />
'''
    s=one(s,old,new,'About Iris icon/summary')
    for line,label in [
        ('            <Preference ns0:layout="@layout/preference_about" ns0:key="@string/pref_contributors_key" ns0:icon="@drawable/ic_github" ns0:title="@string/contributors_title" ns0:summary="eszdman, assasinfil, killerink, mirai, Urnyx05, vibhorSrv, snajdovski" />\n','contributors'),
        ('            <Preference ns0:layout="@layout/preference_about" ns0:title="@string/telegram" ns0:icon="@drawable/ic_telegram" ns0:key="@string/pref_telegram_channel_key" />\n','telegram'),
        ('            <Preference ns0:layout="@layout/preference_about" ns0:title="@string/supported_devices" ns0:enabled="false" ns0:persistent="false" ns0:key="@string/all_devices_names" />\n','supported devices'),
    ]:
        s=one(s,line,'',f'About remove {label}')
    return s

def swipe_expected(text:str)->str:
    s=norm(text)
    long_anchor='''            @Override
            public boolean onSingleTapUp(MotionEvent e) {
                cameraFragmentViewModel.setSettingsBarVisible(false);
                startTouchToFocus(e);
                return false;
            }
'''
    long_repl=long_anchor+'''\n            @Override
            public void onLongPress(MotionEvent e) {
                startTouchFocusLock(e);
            }
'''
    s=one(s,long_anchor,long_repl,'Swipe long-press callback')
    pattern=r'''    private void startTouchToFocus\(MotionEvent event\) \{.*?\n    \}\n\n    public void SwipeUp\(\) \{'''
    repl='''    /* IRIS_26523_ACTUAL_PREVIEW_TOUCH_BOUNDS */
    private float[] getPreviewTouchPoint(MotionEvent event) {
        if (event == null || cameraFragment.textureView == null) return null;
        View preview = cameraFragment.textureView;
        int width = preview.getWidth();
        int height = preview.getHeight();
        if (width <= 0 || height <= 0 || !preview.isShown()) return null;
        int[] location = new int[2];
        preview.getLocationOnScreen(location);
        float x = event.getRawX() - location[0];
        float y = event.getRawY() - location[1];
        if (x < 0f || y < 0f || x >= width || y >= height) return null;
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

    public void SwipeUp() {'''
    s=regex_one(s,pattern,repl,'Swipe actual preview focus bounds')
    if 'import com.particlesdevs.photoncamera.control.TouchFocus;' not in s:
        # Swipe is in the same package, so no import is necessary.
        pass
    return s

def touch_focus_expected(text:str)->str:
    s=norm(text)
    if 'IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING' in s:
        raise AssertionError('26523 TouchFocus already applied')
    s=one(s,'import android.graphics.Point;\n','import android.graphics.Point;\nimport android.graphics.Rect;\n', 'TouchFocus Rect import')
    old_listener='''    private final OnTouchListener focusListener = (v, event) -> {
        v.performClick();
        resetFocusCircle();
        setInitialAFAE();
        return true;
    };
'''
    new_listener='''    /* IRIS_26523_REAL_AF_LOCK_STATE */
    private volatile boolean focusLocked = false;
    private MeteringRectangle[] activeTouchRegion = null;
'''
    s=one(s,old_listener,new_listener,'TouchFocus overlay listener removal')
    s=one(s,'        focusCircleView.setOnTouchListener(focusListener);\n',
          '''        // The focus ring is visual-only. It must not consume the second touch/hold
        // used to lock focus at the same point.
        focusCircleView.setOnTouchListener(null);
        focusCircleView.setClickable(false);
''','TouchFocus overlay pass-through')
    old_process='''    public void processTouchToFocus(float fx, float fy) {
        focusCircleView.removeCallbacks(hideFocusCircleRunnable);
        focusCircleView.post(() -> showFocusCircle(fx, fy));
        setFocus((int) fy, (int) fx);
        focusCircleView.postDelayed(hideFocusCircleRunnable, AUTO_HIDE_DELAY_MS);
    }
'''
    new_process='''    public boolean isFocusLocked() {
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
        if (!focusLocked || CaptureController.burst) return;
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null || activeTouchRegion == null) return;
        builder.set(CaptureRequest.CONTROL_AF_REGIONS, activeTouchRegion);
        builder.set(CaptureRequest.CONTROL_AF_MODE, PreferenceKeys.getAfMode());
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        captureController.rebuildPreviewBuilder();
        isTouchFocus = true;
    }
'''
    s=one(s,old_process,new_process,'TouchFocus public focus API')
    s=one(s,
          '        focusCircleView.setX(fx - focusCircleView.getMeasuredWidth() / 2.0f);\n        focusCircleView.setY(fy - focusCircleView.getMeasuredHeight() / 2.0f);\n        focusCircleView.setVisibility(View.VISIBLE);\n',
          '''        focusCircleView.setX(textureView.getX() + fx - focusCircleView.getMeasuredWidth() / 2.0f);
        focusCircleView.setY(textureView.getY() + fy - focusCircleView.getMeasuredHeight() / 2.0f);
        focusCircleView.setAlpha(1f);
        focusCircleView.setVisibility(View.VISIBLE);
''','TouchFocus ring preview-local placement')
    setfocus_pattern=r'''    private void setFocus\(int x, int y\) \{.*?\n    \}\n\n    private void triggerAutoFocus\(MeteringRectangle\[] rectaf\) \{'''
    setfocus_repl='''    /* IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING */
    private void applyFocus(float previewX, float previewY, boolean lockRequested) {
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
                ? CaptureController.mPreviewCaptureResult.get(CaptureRequest.SCALER_CROP_REGION)
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
                + " rect=" + rect);
        return new MeteringRectangle[]{rect};
    }

    private void triggerAutoFocus(MeteringRectangle[] rectaf, boolean lockRequested) {'''
    s=regex_one(s,setfocus_pattern,setfocus_repl,'TouchFocus active crop mapping')
    trigger_pattern=r'''    private void triggerAutoFocus\(MeteringRectangle\[] rectaf, boolean lockRequested\) \{.*?\n    \}\n    private void resetAutoFocus\(\) \{'''
    trigger_repl='''    private void triggerAutoFocus(MeteringRectangle[] rectaf, boolean lockRequested) {
        if (CaptureController.burst) return;
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null) {
            Log.w(TAG, "triggerAutoFocus(): mPreviewRequestBuilder is null");
            return;
        }
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
        captureController.rebuildPreviewBuilderOneShot();
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
            captureController.rebuildPreviewBuilderOneShot();
            builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        }
        captureController.rebuildPreviewBuilder();
        isTouchFocus = true;
        focusLocked = lockRequested;
        Log.d(TAG, "IRIS_26523_TOUCH_AF lock=" + lockRequested
                + " afMode=" + preferredAfMode + " region=" + rectaf[0]);
    }
    private void resetAutoFocus() {'''
    s=regex_one(s,trigger_pattern,trigger_repl,'TouchFocus Camera2 trigger lifecycle')
    reset_pattern=r'''    private void resetAutoFocus\(\) \{.*?\n    \}\n\n\n    //Thread safe'''
    reset_repl='''    private void resetAutoFocus() {
        focusLocked = false;
        activeTouchRegion = null;
        if (CaptureController.burst) return;
        CaptureRequest.Builder builder = captureController.mPreviewRequestBuilder;
        if (builder == null) {
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
        captureController.rebuildPreviewBuilderOneShot();
        builder.set(CaptureRequest.CONTROL_AF_TRIGGER, CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
        builder.set(CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER, CaptureRequest.CONTROL_AE_PRECAPTURE_TRIGGER_IDLE);
        captureController.rebuildPreviewBuilder();
        isTouchFocus = false;
    }


    //Thread safe'''
    s=regex_one(s,reset_pattern,reset_repl,'TouchFocus reset lifecycle')
    # The old private helper is no longer used and is harmless; remove it to make ownership explicit.
    s=s.replace('''    private void setInitialAFAE() {
        captureController.reset3Aparams();
    }

''','')
    return s

def capture_expected(text:str)->str:
    s=norm(text)
    marker='''            /* IRIS_26484_UNLOCK_FOCUS_NULL_BUILDER_GUARD */
            if (mPreviewRequestBuilder == null || mCaptureSession == null) {
'''
    insertion='''            /* IRIS_26523_PRESERVE_USER_AF_LOCK_ACROSS_CAPTURE */
            if (mTouchFocus != null && mTouchFocus.isFocusLocked()) {
                mState = STATE_PREVIEW;
                mTouchFocus.resumeLockedFocusAfterCapture();
                Log.d(TAG, "26523 unlockFocus preserved user long-press AF lock");
                return;
            }
'''
    return one(s,marker,insertion+marker,'CaptureController preserve focus lock')

def expected_for(path:str,text:str)->str:
    return {
        DNG_CREATOR:dng_creator_expected,
        IMAGE_SAVER:image_saver_expected,
        IRIS_STACK:iris_stack_expected,
        IRIS_SHADER:iris_shader_expected,
        TOUCH_FOCUS:touch_focus_expected,
        SWIPE:swipe_expected,
        CAPTURE:capture_expected,
        PREFS:prefs_expected,
    }[path](text)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--check-only',action='store_true')
    ap.add_argument('--patch-out',type=Path)
    ap.add_argument('--patch-sha-out',type=Path)
    a=ap.parse_args()
    root=a.root
    before={}
    after={}
    for rel in sorted(CHANGED):
        p=root/rel
        if not p.is_file(): raise SystemExit('missing '+rel)
        before[rel]=norm(p.read_text(encoding='utf-8'))
        after[rel]=expected_for(rel,before[rel])
        if before[rel]==after[rel]: raise SystemExit('no transform for '+rel)
    patch_parts=[]
    for rel in sorted(CHANGED):
        patch_parts.extend(difflib.unified_diff(
            before[rel].splitlines(True),after[rel].splitlines(True),
            fromfile='a/'+rel,tofile='b/'+rel,n=3))
    patch=''.join(patch_parts)
    if not patch: raise SystemExit('empty 26523 patch')
    if a.patch_out:
        a.patch_out.parent.mkdir(parents=True,exist_ok=True)
        a.patch_out.write_text(patch,encoding='utf-8',newline='\n')
        if a.patch_sha_out:
            digest=hashlib.sha256(a.patch_out.read_bytes()).hexdigest()
            a.patch_sha_out.write_text(f'{digest}  {a.patch_out.name}\n',encoding='utf-8')
    if not a.check_only:
        for rel in sorted(CHANGED):
            (root/rel).write_text(after[rel],encoding='utf-8',newline='\n')
    print('PASS: 26523 complete transform resolved for exactly',len(CHANGED),'runtime files')
    for rel in sorted(CHANGED): print('CHANGED',rel)

if __name__=='__main__': main()
