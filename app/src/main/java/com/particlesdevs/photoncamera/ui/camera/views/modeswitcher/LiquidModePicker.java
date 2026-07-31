package com.particlesdevs.photoncamera.ui.camera.views.modeswitcher;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.MotionEvent;
import android.view.ViewGroup;
import android.view.animation.AccelerateDecelerateInterpolator;

import com.particlesdevs.photoncamera.ui.camera.views.modeswitcher.wefika.horizontalpicker.HorizontalPicker;

public class LiquidModePicker extends HorizontalPicker {
    private static final int SELECTED_YELLOW = 0xFFFFCC00;
    private static final int UNSELECTED_WHITE = 0xFFFFFFFF;
    private static final int COLLAPSED_WIDTH_DP = 154;
    private static final int EXPANDED_WIDTH_DP = 338;

    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF pill = new RectF();
    private final RectF selection = new RectF();

    private boolean expanded = false;
    private int selectedIndex = 0;
    private float downX;

    public LiquidModePicker(Context context) {
        this(context, null);
    }

    public LiquidModePicker(Context context, AttributeSet attrs) {
        super(context, attrs);
        setSideItems(0);
        setOverScrollMode(OVER_SCROLL_NEVER);
        setWillNotDraw(false);

        fillPaint.setStyle(Paint.Style.FILL);
        fillPaint.setColor(0xB0141414);

        strokePaint.setStyle(Paint.Style.STROKE);
        strokePaint.setStrokeWidth(dp(1.0f));
        strokePaint.setColor(0x55FFFFFF);

        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(
                android.graphics.Typeface.create(
                        android.graphics.Typeface.DEFAULT,
                        android.graphics.Typeface.BOLD
                )
        );
        textPaint.setTextSize(sp(10.5f));
    }

    public void collapseToIndex(int index) {
        CharSequence[] labels = getValues();
        if (labels == null || labels.length == 0) return;

        selectedIndex =
                Math.max(
                        0,
                        Math.min(
                                labels.length - 1,
                                index
                        )
                );

        setSelectedItem(selectedIndex);
        setExpanded(false);
        invalidate();
    }

    private void setExpanded(boolean value) {
        if (expanded == value) return;
        expanded = value;

        int start = getLayoutParams().width;
        int end =
                (int) dp(
                        expanded
                                ? EXPANDED_WIDTH_DP
                                : COLLAPSED_WIDTH_DP
                );

        ValueAnimator animator = ValueAnimator.ofInt(start, end);
        animator.setDuration(240L);
        animator.setInterpolator(new AccelerateDecelerateInterpolator());
        animator.addUpdateListener(animation -> {
            ViewGroup.LayoutParams params = getLayoutParams();
            params.width = (Integer) animation.getAnimatedValue();
            setLayoutParams(params);
            invalidate();
        });
        animator.start();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        CharSequence[] labels = getValues();
        int width = getWidth();
        int height = getHeight();

        if (labels == null || labels.length == 0 || width <= 0 || height <= 0) {
            return;
        }

        float pad = dp(2.5f);
        float radius = height / 2.0f;
        pill.set(pad, pad, width - pad, height - pad);

        canvas.drawRoundRect(pill, radius, radius, fillPaint);
        canvas.drawRoundRect(pill, radius, radius, strokePaint);

        float baseline =
                height / 2.0f
                        - (textPaint.ascent() + textPaint.descent()) / 2.0f;

        if (!expanded) {
            float half = width / 2.0f;
            selection.set(pad, pad, half - pad, height - pad);

            Paint selectedFill = new Paint(fillPaint);
            selectedFill.setColor(0x22FFFFFF);

            canvas.drawRoundRect(selection, radius, radius, selectedFill);
            canvas.drawRoundRect(selection, radius, radius, strokePaint);

            drawLabel(
                    canvas,
                    labels[selectedIndex].toString(),
                    half * 0.5f,
                    baseline,
                    SELECTED_YELLOW
            );

            int videoIndex = labels.length > 1 ? 1 : selectedIndex;

            drawLabel(
                    canvas,
                    labels[videoIndex].toString(),
                    half * 1.5f,
                    baseline,
                    selectedIndex == videoIndex
                            ? SELECTED_YELLOW
                            : UNSELECTED_WHITE
            );
            return;
        }

        float itemWidth = width / (float) labels.length;
        selection.set(
                selectedIndex * itemWidth + pad,
                pad,
                (selectedIndex + 1) * itemWidth - pad,
                height - pad
        );

        Paint selectedFill = new Paint(fillPaint);
        selectedFill.setColor(0x22FFFFFF);

        canvas.drawRoundRect(selection, radius, radius, selectedFill);
        canvas.drawRoundRect(selection, radius, radius, strokePaint);

        for (int i = 0; i < labels.length; i++) {
            drawLabel(
                    canvas,
                    labels[i].toString(),
                    itemWidth * (i + 0.5f),
                    baseline,
                    i == selectedIndex
                            ? SELECTED_YELLOW
                            : UNSELECTED_WHITE
            );
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        CharSequence[] labels = getValues();
        if (labels == null || labels.length == 0) return false;

        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            downX = event.getX();
            return true;
        }

        if (event.getAction() == MotionEvent.ACTION_UP) {
            if (Math.abs(event.getX() - downX) > dp(18.0f)) {
                return true;
            }

            if (!expanded) {
                if (event.getX() < getWidth() / 2.0f) {
                    setExpanded(true);
                } else {
                    collapseToIndex(Math.min(1, labels.length - 1));
                }
                return true;
            }

            int index =
                    Math.max(
                            0,
                            Math.min(
                                    labels.length - 1,
                                    (int) (
                                            event.getX()
                                                    / (
                                                            getWidth()
                                                                    / (float) labels.length
                                                    )
                                    )
                            )
                    );

            collapseToIndex(index);
            return true;
        }

        return true;
    }

    private void drawLabel(
            Canvas canvas,
            String label,
            float x,
            float baseline,
            int color
    ) {
        textPaint.setColor(color);
        canvas.drawText(label, x, baseline, textPaint);
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
