package com.particlesdevs.photoncamera.ui.camera.views.modeswitcher;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.animation.AccelerateDecelerateInterpolator;

public class LiquidModePicker extends View {
    public interface OnItemSelectedListener {
        void onItemSelected(int index);
    }

    private static final int SELECTED_YELLOW = 0xFFFFCC00;
    private static final int UNSELECTED_WHITE = 0xFFFFFFFF;
    private static final int PANEL_FILL = 0xD90C0C0C;
    private static final int STROKE = 0xCCFFFFFF;
    private static final int SELECTION_FILL = 0x18FFFFFF;

    private static final float COLLAPSED_WIDTH_DP = 112f;
    private static final float EXPANDED_WIDTH_DP = 356f;
    private static final long HOLD_DELAY_MS = 230L;

    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint selectionFillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF pillRect = new RectF();
    private final RectF selectionRect = new RectF();
    private final Handler holdHandler = new Handler(Looper.getMainLooper());

    private String[] labels = new String[0];
    private int selectedIndex = 0;
    private int highlightedIndex = 0;
    private float displayedHighlightIndex = 0f;

    private boolean expanded = false;
    private boolean holdActivated = false;
    private boolean pointerDown = false;

    private float animatedPillWidthPx;
    private float downX;
    private float downY;
    private final int touchSlop;

    private ValueAnimator widthAnimator;
    private ValueAnimator highlightAnimator;
    private OnItemSelectedListener onItemSelectedListener;

    private final Runnable holdRunnable = () -> {
        if (!pointerDown || labels.length == 0) return;
        holdActivated = true;
        highlightedIndex = selectedIndex;
        displayedHighlightIndex = selectedIndex;
        animateExpanded(true);
        performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
    };

    public LiquidModePicker(Context context) {
        this(context, null);
    }

    public LiquidModePicker(Context context, AttributeSet attrs) {
        super(context, attrs);
        setClickable(true);
        setFocusable(true);
        touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        animatedPillWidthPx = dp(COLLAPSED_WIDTH_DP);

        fillPaint.setStyle(Paint.Style.FILL);
        fillPaint.setColor(PANEL_FILL);

        strokePaint.setStyle(Paint.Style.STROKE);
        strokePaint.setStrokeWidth(dp(1.25f));
        strokePaint.setColor(STROKE);

        selectionFillPaint.setStyle(Paint.Style.FILL);
        selectionFillPaint.setColor(SELECTION_FILL);

        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
        textPaint.setTextSize(sp(10.7f));
    }

    public void setValues(String[] values) {
        labels = values != null ? values : new String[0];
        selectedIndex = clampIndex(selectedIndex);
        highlightedIndex = selectedIndex;
        displayedHighlightIndex = selectedIndex;
        invalidate();
    }

    public void setSideItems(int ignored) {
        // Compatibility with the previous picker API.
    }

    public void setSelectedItem(int index) {
        if (labels.length == 0) return;
        selectedIndex = clampIndex(index);
        highlightedIndex = selectedIndex;
        displayedHighlightIndex = selectedIndex;
        expanded = false;
        animatedPillWidthPx = dp(COLLAPSED_WIDTH_DP);
        invalidate();
    }

    public void collapseToIndex(int index) {
        setSelectedItem(index);
    }

    public void setOnItemSelectedListener(OnItemSelectedListener listener) {
        onItemSelectedListener = listener;
    }

    private int clampIndex(int index) {
        if (labels.length == 0) return 0;
        return Math.max(0, Math.min(labels.length - 1, index));
    }

    private float collapsedWidthPx() {
        return dp(COLLAPSED_WIDTH_DP);
    }

    private float expandedWidthPx() {
        return Math.min(getWidth(), dp(EXPANDED_WIDTH_DP));
    }

    private float pillLeft() {
        return (getWidth() - animatedPillWidthPx) / 2f;
    }

    private float pillRight() {
        return pillLeft() + animatedPillWidthPx;
    }

    private boolean isInsideCurrentPill(float x, float y) {
        return x >= pillLeft()
                && x <= pillRight()
                && y >= 0f
                && y <= getHeight();
    }

    private void animateExpanded(boolean value) {
        expanded = value;
        float start = animatedPillWidthPx;
        float end = value ? expandedWidthPx() : collapsedWidthPx();

        if (widthAnimator != null) widthAnimator.cancel();
        widthAnimator = ValueAnimator.ofFloat(start, end);
        widthAnimator.setDuration(value ? 220L : 190L);
        widthAnimator.setInterpolator(new AccelerateDecelerateInterpolator());
        widthAnimator.addUpdateListener(animation -> {
            animatedPillWidthPx = (Float) animation.getAnimatedValue();
            invalidate();
        });
        widthAnimator.addListener(new AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(Animator animation) {
                animatedPillWidthPx = end;
                invalidate();
            }
        });
        widthAnimator.start();
    }

    private int indexForFinger(float x) {
        if (labels.length == 0) return selectedIndex;

        float left = (getWidth() - expandedWidthPx()) / 2f;
        float localX = Math.max(0f, Math.min(expandedWidthPx() - 0.001f, x - left));
        float itemWidth = expandedWidthPx() / labels.length;
        return clampIndex((int) (localX / itemWidth));
    }

    private void animateHighlightTo(int targetIndex) {
        int target = clampIndex(targetIndex);
        if (target == highlightedIndex && highlightAnimator != null
                && highlightAnimator.isRunning()) {
            return;
        }

        highlightedIndex = target;
        if (highlightAnimator != null) highlightAnimator.cancel();

        highlightAnimator = ValueAnimator.ofFloat(displayedHighlightIndex, target);
        highlightAnimator.setDuration(95L);
        highlightAnimator.setInterpolator(new AccelerateDecelerateInterpolator());
        highlightAnimator.addUpdateListener(animation -> {
            displayedHighlightIndex = (Float) animation.getAnimatedValue();
            invalidate();
        });
        highlightAnimator.addListener(new AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(Animator animation) {
                displayedHighlightIndex = highlightedIndex;
                invalidate();
            }
        });
        highlightAnimator.start();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (labels.length == 0 || getWidth() <= 0 || getHeight() <= 0) return;

        float pad = dp(1.8f);
        float left = pillLeft();
        float right = pillRight();
        float radius = getHeight() / 2f;

        pillRect.set(left + pad, pad, right - pad, getHeight() - pad);
        canvas.drawRoundRect(pillRect, radius, radius, fillPaint);
        canvas.drawRoundRect(pillRect, radius, radius, strokePaint);

        float baseline =
                getHeight() / 2f - (textPaint.ascent() + textPaint.descent()) / 2f;

        if (expanded || animatedPillWidthPx > collapsedWidthPx() + dp(8f)) {
            drawExpanded(canvas, baseline, radius, pad, left);
        } else {
            drawCollapsed(canvas, baseline, radius, pad, left, right);
        }
    }

    private void drawCollapsed(
            Canvas canvas,
            float baseline,
            float radius,
            float pad,
            float left,
            float right
    ) {
        selectionRect.set(
                left + pad,
                pad,
                right - pad,
                getHeight() - pad
        );
        canvas.drawRoundRect(selectionRect, radius, radius, selectionFillPaint);

        textPaint.setColor(SELECTED_YELLOW);
        textPaint.setFakeBoldText(true);
        canvas.drawText(
                labels[selectedIndex],
                getWidth() / 2f,
                baseline,
                textPaint
        );
    }

    private void drawExpanded(
            Canvas canvas,
            float baseline,
            float radius,
            float pad,
            float left
    ) {
        float itemWidth = animatedPillWidthPx / labels.length;

        selectionRect.set(
                left + displayedHighlightIndex * itemWidth + pad,
                pad,
                left + (displayedHighlightIndex + 1f) * itemWidth - pad,
                getHeight() - pad
        );
        canvas.drawRoundRect(selectionRect, radius, radius, selectionFillPaint);

        for (int i = 0; i < labels.length; i++) {
            boolean selected = i == highlightedIndex;
            textPaint.setColor(selected ? SELECTED_YELLOW : UNSELECTED_WHITE);
            textPaint.setFakeBoldText(selected);
            canvas.drawText(
                    labels[i],
                    left + itemWidth * (i + 0.5f),
                    baseline,
                    textPaint
            );
        }
    }

    private void finishGesture(boolean cancelled) {
        holdHandler.removeCallbacks(holdRunnable);

        if (holdActivated && expanded && !cancelled) {
            selectedIndex = highlightedIndex;
            displayedHighlightIndex = highlightedIndex;

            if (onItemSelectedListener != null) {
                onItemSelectedListener.onItemSelected(selectedIndex);
            }

            postDelayed(() -> animateExpanded(false), 70L);
        } else if (expanded) {
            animateExpanded(false);
        }

        pointerDown = false;
        holdActivated = false;
        setPressed(false);
        invalidate();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (labels.length == 0 || !isEnabled()) return false;

        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                if (!isInsideCurrentPill(event.getX(), event.getY())) {
                    return false;
                }
                getParent().requestDisallowInterceptTouchEvent(true);
                pointerDown = true;
                holdActivated = false;
                downX = event.getX();
                downY = event.getY();
                setPressed(true);
                holdHandler.removeCallbacks(holdRunnable);
                holdHandler.postDelayed(holdRunnable, HOLD_DELAY_MS);
                return true;

            case MotionEvent.ACTION_MOVE:
                if (!pointerDown) return false;

                if (!holdActivated) {
                    float dx = Math.abs(event.getX() - downX);
                    float dy = Math.abs(event.getY() - downY);
                    if (dx > touchSlop * 1.5f || dy > touchSlop * 1.5f) {
                        holdHandler.removeCallbacks(holdRunnable);
                    }
                    return true;
                }

                animateHighlightTo(indexForFinger(event.getX()));
                return true;

            case MotionEvent.ACTION_UP:
                finishGesture(false);
                performClick();
                getParent().requestDisallowInterceptTouchEvent(false);
                return true;

            case MotionEvent.ACTION_CANCEL:
                finishGesture(true);
                getParent().requestDisallowInterceptTouchEvent(false);
                return true;

            default:
                return true;
        }
    }

    @Override
    public boolean performClick() {
        super.performClick();
        return true;
    }

    @Override
    protected void onDetachedFromWindow() {
        holdHandler.removeCallbacks(holdRunnable);
        if (widthAnimator != null) widthAnimator.cancel();
        if (highlightAnimator != null) highlightAnimator.cancel();
        super.onDetachedFromWindow();
    }

    private float dp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP,
                value,
                getResources().getDisplayMetrics()
        );
    }

    private float sp(float value) {
        return TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_SP,
                value,
                getResources().getDisplayMetrics()
        );
    }
}