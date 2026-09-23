package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.os.Handler;
import android.os.Looper;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.spektra.SpektraModeController;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26693_SPEKTRA_PRESENTATION_ONLY_HISTOGRAM
 *
 * Unspektrawesome owns native histogram acquisition and lifecycle. This Iris View is deliberately
 * presentation-only: it receives completed native viewfinder samples, reduces them to Photo-style
 * 64-bin RGB curves, and draws the same pill/geometry as IrisLiveHistogramView. It owns no worker,
 * polling cadence, renderer generation, camera session, lens switch or capture lifecycle.
 */
public final class SpektraLiveHistogramView extends View {
    private static final String TAG = "SpektraHistogram";
    private static final int NATIVE_SIDE = 128;
    private static final int NATIVE_PIXELS = NATIVE_SIDE * NATIVE_SIDE;
    private static final int BINS = 64;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private volatile SpektraModeController controller;
    private volatile boolean spektraActive;
    private boolean failureLogged;

    private volatile float[] red = new float[BINS];
    private volatile float[] green = new float[BINS];
    private volatile float[] blue = new float[BINS];

    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final Path innerClipPath = new Path();
    private final RectF innerClipRect = new RectF();
    private final RectF borderRect = new RectF();
    private final com.unspektrawesome.preview.RawVulkanPreviewController.HistogramListener
            histogramListener = this::acceptHistogramPixels;

    public SpektraLiveHistogramView(Context context) { super(context); init(); }
    public SpektraLiveHistogramView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs); init();
    }
    public SpektraLiveHistogramView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr); init();
    }

    private void init() {
        setWillNotDraw(false);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeWidth(dp(1.1f));
        linePaint.setStrokeJoin(Paint.Join.ROUND);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
        fillPaint.setStyle(Paint.Style.FILL);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(dp(1.4f));
        borderPaint.setColor(Color.argb(0xCC, 255, 255, 255));
    }

    public void bind(@Nullable SpektraModeController nextController) {
        SpektraModeController previous = controller;
        if (previous == nextController) return;
        if (previous != null) previous.setHistogramListener(null);
        controller = nextController;
        syncPresentationSubscription();
    }

    public void setSpektraActive(boolean active) {
        spektraActive = active;
        setVisibility(active ? VISIBLE : GONE);
        syncPresentationSubscription();
        if (!active) clearHistogram();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        syncPresentationSubscription();
    }

    @Override protected void onDetachedFromWindow() {
        SpektraModeController current = controller;
        if (current != null) current.setHistogramListener(null);
        clearHistogram();
        super.onDetachedFromWindow();
    }

    private void syncPresentationSubscription() {
        SpektraModeController current = controller;
        if (current == null) return;
        current.setHistogramListener(
                spektraActive && isAttachedToWindow() ? histogramListener : null);
    }

    private void acceptHistogramPixels(int[] pixels) {
        if (!spektraActive || pixels == null || pixels.length == 0) {
            if (spektraActive) clearHistogram();
            return;
        }
        if (pixels.length != NATIVE_PIXELS) {
            if (!failureLogged) {
                failureLogged = true;
                Log.w(TAG, "IRIS_26693_SPEKTRA_HISTOGRAM_BAD_SOURCE_SIZE length=" + pixels.length);
            }
            return;
        }
        float[] r = new float[BINS];
        float[] g = new float[BINS];
        float[] b = new float[BINS];
        for (int color : pixels) {
            r[Math.min(BINS - 1, Color.red(color) * BINS / 256)] += 1.0f;
            g[Math.min(BINS - 1, Color.green(color) * BINS / 256)] += 1.0f;
            b[Math.min(BINS - 1, Color.blue(color) * BINS / 256)] += 1.0f;
        }
        smooth3(r); smooth3(g); smooth3(b);
        float max = 1.0f;
        for (int i = 2; i < BINS; i++) {
            max = Math.max(max, Math.max(r[i], Math.max(g[i], b[i])));
        }
        float darkCap = max * 1.25f;
        r[0] = Math.min(r[0], darkCap); r[1] = Math.min(r[1], darkCap);
        g[0] = Math.min(g[0], darkCap); g[1] = Math.min(g[1], darkCap);
        b[0] = Math.min(b[0], darkCap); b[1] = Math.min(b[1], darkCap);
        normalize(r, max); normalize(g, max); normalize(b, max);
        mainHandler.post(() -> {
            if (!spektraActive) return;
            red = r; green = g; blue = b;
            failureLogged = false;
            postInvalidateOnAnimation();
        });
    }

    private static void smooth3(float[] x) {
        float previous = x[0];
        for (int i = 1; i < x.length - 1; i++) {
            float current = x[i];
            float next = x[i + 1];
            x[i] = 0.25f * previous + 0.50f * current + 0.25f * next;
            previous = current;
        }
    }

    private static void normalize(float[] x, float max) {
        float inv = 1.0f / Math.max(max, 1.0f);
        for (int i = 0; i < x.length; i++) x[i] = Math.min(1.0f, x[i] * inv);
    }

    private void clearHistogram() {
        red = new float[BINS]; green = new float[BINS]; blue = new float[BINS];
        mainHandler.post(this::invalidate);
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        final float left = getPaddingLeft() + dp(5.0f);
        final float right = getWidth() - getPaddingRight() - dp(5.0f);
        final float top = getPaddingTop() + dp(4.0f);
        final float bottom = getHeight() - getPaddingBottom() - dp(4.0f);
        if (right <= left || bottom <= top) return;

        final float innerInset = dp(2.2f);
        innerClipRect.set(innerInset, innerInset, getWidth() - innerInset, getHeight() - innerInset);
        final float innerRadius = Math.max(0.0f, innerClipRect.height() * 0.5f);
        innerClipPath.reset();
        innerClipPath.addRoundRect(innerClipRect, innerRadius, innerRadius, Path.Direction.CW);
        final int save = canvas.save();
        canvas.clipPath(innerClipPath);
        drawChannel(canvas, red, Color.rgb(255, 70, 70), left, top, right, bottom);
        drawChannel(canvas, green, Color.rgb(68, 235, 96), left, top, right, bottom);
        drawChannel(canvas, blue, Color.rgb(70, 115, 255), left, top, right, bottom);
        canvas.restoreToCount(save);

        final float halfStroke = borderPaint.getStrokeWidth() * 0.5f;
        borderRect.set(halfStroke, halfStroke, getWidth() - halfStroke, getHeight() - halfStroke);
        final float borderRadius = Math.max(0.0f, borderRect.height() * 0.5f);
        canvas.drawRoundRect(borderRect, borderRadius, borderRadius, borderPaint);
    }

    private void drawChannel(Canvas canvas, float[] values, int color,
                             float left, float top, float right, float bottom) {
        path.reset(); path.moveTo(left, bottom);
        for (int i = 0; i < BINS; i++) {
            float x = left + (right - left) * i / (BINS - 1.0f);
            float y = bottom - (bottom - top) * values[i];
            path.lineTo(x, y);
        }
        path.lineTo(right, bottom); path.close();
        fillPaint.setColor((color & 0x00ffffff) | 0x30000000);
        canvas.drawPath(path, fillPaint);
        path.reset();
        for (int i = 0; i < BINS; i++) {
            float x = left + (right - left) * i / (BINS - 1.0f);
            float y = bottom - (bottom - top) * values[i];
            if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        linePaint.setColor((color & 0x00ffffff) | 0xd8000000);
        canvas.drawPath(path, linePaint);
    }

    private float dp(float value) {
        return value * getResources().getDisplayMetrics().density;
    }
}
