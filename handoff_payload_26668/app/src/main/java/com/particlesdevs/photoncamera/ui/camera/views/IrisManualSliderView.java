package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.circularbarlib.api.ManualModeConsole;
import com.particlesdevs.photoncamera.circularbarlib.console.ManualModeConsoleImpl;
import com.particlesdevs.photoncamera.circularbarlib.control.ManualParamModel;
import com.particlesdevs.photoncamera.circularbarlib.control.models.EvModel;
import com.particlesdevs.photoncamera.circularbarlib.control.models.FocusModel;
import com.particlesdevs.photoncamera.circularbarlib.control.models.IsoModel;
import com.particlesdevs.photoncamera.circularbarlib.control.models.ManualModel;
import com.particlesdevs.photoncamera.circularbarlib.control.models.ShutterModel;
import com.particlesdevs.photoncamera.circularbarlib.model.KnobModel;
import com.particlesdevs.photoncamera.circularbarlib.ui.views.knobview.KnobItemInfo;
import com.particlesdevs.photoncamera.util.Log;

import java.util.List;
import java.util.Observable;
import java.util.Observer;

/**
 * IRIS_26668_EXACT_VALUE_MANUAL_SLIDER
 *
 * Presentation replacement for the circular KnobView. It consumes the exact existing ManualModel
 * item list: AUTO remains item zero and is a separate button; every other KnobItemInfo is rendered
 * as exactly one slider tick. There is no interpolated/manual value invented by this view.
 *
 * Once a slider drag begins this view owns the pointer until ACTION_UP/CANCEL. Horizontal movement
 * continues to select valid ticks even when the pointer leaves the translucent rectangle or this
 * view's visual bounds; vertical movement never cancels the gesture. Parent interception is blocked
 * for that pointer so shutter/lens/touch-focus controls cannot receive the same drag.
 */
@SuppressWarnings("deprecation")
public final class IrisManualSliderView extends View implements Observer {
    private static final String TAG = "IrisManualSlider";
    private static final int YELLOW = Color.rgb(255, 214, 10);
    private static final int WHITE = Color.WHITE;

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF autoRect = new RectF();
    private final GradientDrawable panel = new GradientDrawable(
            GradientDrawable.Orientation.TOP_BOTTOM,
            new int[]{0xD9181818, 0xC0101010});

    private ManualModeConsoleImpl console;
    private KnobModel knobModel;
    private int activePointerId = MotionEvent.INVALID_POINTER_ID;
    private boolean dragging;
    private boolean autoPressed;
    private int lastSelectedIndex = -1;

    public IrisManualSliderView(Context context) {
        super(context);
        init();
    }

    public IrisManualSliderView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public IrisManualSliderView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setWillNotDraw(false);
        setClickable(true);
        panel.setCornerRadius(dp(18.0f));
        panel.setStroke(Math.max(1, Math.round(dp(1.0f))), 0x55FFFFFF);
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        ManualModeConsole generic = ManualModeConsoleImpl.getInstance();
        if (generic instanceof ManualModeConsoleImpl) {
            console = (ManualModeConsoleImpl) generic;
            knobModel = console.getKnobModel();
            knobModel.addObserver(this);
        }
        invalidate();
    }

    @Override
    protected void onDetachedFromWindow() {
        if (knobModel != null) knobModel.deleteObserver(this);
        knobModel = null;
        console = null;
        releaseGesture();
        super.onDetachedFromWindow();
    }

    @Override
    public void update(Observable observable, Object arg) {
        post(() -> {
            lastSelectedIndex = -1;
            invalidate();
        });
    }

    private ManualModel<?> activeModel() {
        return knobModel == null || !knobModel.isKnobVisible()
                ? null : knobModel.getManualModel();
    }

    private static String modeName(ManualModel<?> model) {
        if (model instanceof FocusModel) return "Focus";
        if (model instanceof ShutterModel) return "Shutter Speed";
        if (model instanceof IsoModel) return "ISO";
        if (model instanceof EvModel) return "Exposure";
        return "Manual";
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        ManualModel<?> model = activeModel();
        if (model == null) return;
        List<KnobItemInfo> all = model.getKnobInfoList();
        if (all == null || all.size() <= 1) return;
        reconcileTrueAutoModelState(model, all);

        float panelLeft = dp(30.0f);
        float panelRight = getWidth() - dp(30.0f);
        float panelTop = 0.0f;
        float panelBottom = getHeight();
        panel.setBounds(Math.round(panelLeft), Math.round(panelTop),
                Math.round(panelRight), Math.round(panelBottom));
        panel.draw(canvas);

        KnobItemInfo current = model.getCurrentInfo();
        KnobItemInfo auto = all.get(0);
        boolean manual = current != null && current != auto && current.tick != 0;
        int selected = findManualIndex(all, current);

        paint.setTypeface(android.graphics.Typeface.create("sans", android.graphics.Typeface.NORMAL));
        paint.setTextSize(dp(9.2f));
        paint.setColor(WHITE);
        paint.setTextAlign(Paint.Align.LEFT);
        canvas.drawText(modeName(model), panelLeft + dp(10.0f), dp(17.5f), paint);

        float autoRadius = dp(12.0f);
        float autoCx = panelRight - dp(16.0f);
        float tickY = dp(44.0f);
        float autoCy = tickY;
        autoRect.set(autoCx - autoRadius, autoCy - autoRadius,
                autoCx + autoRadius, autoCy + autoRadius);

        // The AUTO button exists only while a manual tick owns the parameter.
        if (manual) {
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(0xEE303030);
            canvas.drawCircle(autoCx, autoCy, autoRadius, paint);
            if (autoPressed) {
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(dp(1.0f));
                paint.setColor(YELLOW);
                canvas.drawCircle(autoCx, autoCy, autoRadius, paint);
                paint.setStyle(Paint.Style.FILL);
            }
            paint.setTextAlign(Paint.Align.CENTER);
            paint.setTypeface(android.graphics.Typeface.create("sans", android.graphics.Typeface.BOLD));
            paint.setTextSize(dp(6.8f));
            paint.setColor(autoPressed ? YELLOW : WHITE);
            Paint.FontMetrics fm = paint.getFontMetrics();
            float baseline = autoCy - (fm.ascent + fm.descent) * 0.5f;
            canvas.drawText("AUTO", autoCx, baseline, paint);
        }

        if (manual && current != null) {
            paint.setTextAlign(Paint.Align.RIGHT);
            paint.setTypeface(android.graphics.Typeface.create("sans", android.graphics.Typeface.BOLD));
            paint.setTextSize(dp(10.0f));
            paint.setColor(YELLOW);
            float valueRight = autoRect.left - dp(7.0f);
            canvas.drawText(current.text, valueRight, dp(17.5f), paint);
        }

        final int manualCount = all.size() - 1;
        final float sliderLeft = panelLeft + dp(14.0f);
        final float sliderRight = autoRect.left - dp(10.0f);
        final float span = Math.max(1.0f, sliderRight - sliderLeft);
        for (int i = 0; i < manualCount; i++) {
            float x = manualCount == 1
                    ? sliderLeft : sliderLeft + span * i / (manualCount - 1.0f);
            boolean isSelected = manual && i == selected;
            boolean major = (i % 4) == 0;
            float half = dp(isSelected ? 8.5f : (major ? 6.2f : 4.2f));
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setStrokeWidth(dp(isSelected ? 3.0f : (major ? 1.0f : 0.65f)));
            paint.setColor(isSelected ? YELLOW : (major ? 0xD8FFFFFF : 0x90FFFFFF));
            canvas.drawLine(x, tickY - half, x, tickY + half, paint);
        }
        paint.setStyle(Paint.Style.FILL);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        ManualModel<?> model = activeModel();
        if (model == null) return false;
        List<KnobItemInfo> all = model.getKnobInfoList();
        if (all == null || all.size() <= 1) return false;

        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN: {
                activePointerId = event.getPointerId(0);
                KnobItemInfo current = model.getCurrentInfo();
                boolean manual = current != null && current != all.get(0) && current.tick != 0;
                if (manual && autoRect.contains(event.getX(), event.getY())) {
                    autoPressed = true;
                    dragging = false;
                    getParent().requestDisallowInterceptTouchEvent(true);
                    invalidate();
                    return true;
                }
                // A manual drag starts anywhere inside the visible slider panel.
                if (event.getY() >= 0.0f && event.getY() <= getHeight()) {
                    dragging = true;
                    autoPressed = false;
                    getParent().requestDisallowInterceptTouchEvent(true);
                    selectFromX(model, all, event.getX());
                    return true;
                }
                releaseGesture();
                return false;
            }
            case MotionEvent.ACTION_MOVE: {
                int index = event.findPointerIndex(activePointerId);
                if (index < 0) return true;
                if (dragging) {
                    // X may now be far outside this view; clamp only to the first/last real tick.
                    selectFromX(model, all, event.getX(index));
                    return true;
                }
                if (autoPressed) {
                    invalidate();
                    return true;
                }
                return false;
            }
            case MotionEvent.ACTION_UP: {
                int index = event.findPointerIndex(activePointerId);
                if (autoPressed) {
                    boolean commitAuto = index >= 0 && autoRect.contains(
                            event.getX(index), event.getY(index));
                    if (commitAuto) {
                        commitTrueAuto(model);
                        Log.i(TAG, "IRIS_26668_MANUAL_SLIDER_AUTO mode=" + modeName(model)
                                + " trueModelAuto=true aeSensorPairCoupled="
                                + (model instanceof ShutterModel || model instanceof IsoModel)
                                + " autoButtonHiddenAfterCommit=true");
                    }
                } else if (dragging && index >= 0) {
                    selectFromX(model, all, event.getX(index));
                }
                releaseGesture();
                invalidate();
                return true;
            }
            case MotionEvent.ACTION_CANCEL:
                releaseGesture();
                invalidate();
                return true;
            default:
                return dragging || autoPressed;
        }
    }

    /** Camera2 AE cannot make shutter and ISO independently automatic while the paired sensor
     * parameter remains manual. AUTO on either sensor parameter therefore returns the complete
     * shutter+ISO pair to the existing system-AE owner; Focus and EV retain their independent
     * existing AUTO semantics. */
    private void commitTrueAuto(ManualModel<?> model) {
        model.resetModel();
        if (console == null) return;
        ManualParamModel params = console.getManualParamModel();
        if (model instanceof ShutterModel) {
            if (params.getCurrentISOValue() != ManualParamModel.ISO_AUTO) {
                params.setCurrentISOValue(ManualParamModel.ISO_AUTO);
            }
        } else if (model instanceof IsoModel) {
            if (params.getCurrentExposureValue() != ManualParamModel.EXPOSURE_AUTO) {
                params.setCurrentExposureValue(ManualParamModel.EXPOSURE_AUTO);
            }
        }
    }

    /* If the paired shutter/ISO model was not selected when the other AUTO button restored system
     * AE, its private currentInfo can still point at the old manual tick. Reconcile it lazily from
     * the public ManualParamModel source of truth before drawing that slider. */
    private void reconcileTrueAutoModelState(ManualModel<?> model, List<KnobItemInfo> all) {
        if (console == null || all.isEmpty() || model.getCurrentInfo() == all.get(0)) return;
        ManualParamModel params = console.getManualParamModel();
        boolean shouldBeAuto = (model instanceof ShutterModel
                && params.getCurrentExposureValue() == ManualParamModel.EXPOSURE_AUTO)
                || (model instanceof IsoModel
                && params.getCurrentISOValue() == ManualParamModel.ISO_AUTO);
        if (shouldBeAuto) model.resetModel();
    }

    private void selectFromX(ManualModel<?> model, List<KnobItemInfo> all, float x) {
        int count = all.size() - 1; // item zero is AUTO and never consumes a slider tick
        if (count <= 0) return;
        float panelLeft = dp(30.0f);
        float panelRight = getWidth() - dp(30.0f);
        float autoLeft = panelRight - dp(28.0f); // exact reserved AUTO region, visible or hidden
        float left = panelLeft + dp(14.0f);
        float right = autoLeft - dp(10.0f);
        float t = (x - left) / Math.max(1.0f, right - left);
        int manualIndex = Math.round(Math.max(0.0f, Math.min(1.0f, t)) * (count - 1));
        if (manualIndex == lastSelectedIndex && model.getCurrentInfo() == all.get(manualIndex + 1)) {
            return;
        }
        KnobItemInfo next = all.get(manualIndex + 1);
        KnobItemInfo previous = model.getCurrentInfo();
        model.onSelectedKnobItemChanged(null, previous, next);
        lastSelectedIndex = manualIndex;
        Log.d(TAG, "IRIS_26668_MANUAL_SLIDER_VALUE mode=" + modeName(model)
                + " tick=" + manualIndex + "/" + count
                + " exactText=" + next.text + " exactValue=" + next.value
                + " selectedYellow=true fullScreenDragOwner=true");
        invalidate();
    }

    private static int findManualIndex(List<KnobItemInfo> all, KnobItemInfo current) {
        if (current == null) return -1;
        for (int i = 1; i < all.size(); i++) {
            if (all.get(i) == current) return i - 1;
        }
        return -1;
    }

    private void releaseGesture() {
        activePointerId = MotionEvent.INVALID_POINTER_ID;
        dragging = false;
        autoPressed = false;
        lastSelectedIndex = -1;
        if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(false);
    }

    private float dp(float value) {
        return value * getResources().getDisplayMetrics().density;
    }
}
