package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.util.AttributeSet;
import android.view.PixelCopy;
import android.view.View;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.ui.camera.views.viewfinder.GLPreview;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26668_LIVE_VIEWFINDER_RGB_HISTOGRAM
 *
 * A read-only, latest-frame RGB histogram of the already-rendered preview surface. Exactly one
 * asynchronous PixelCopy may be outstanding; older work is never queued, so histogram work cannot
 * accumulate behind the viewfinder. The 96x54 copy and 64-bin reduction run off the UI thread.
 * This view has no route to Camera2 AE/AWB/AF, capture planning, Motion processing or DNG.
 */
public final class IrisLiveHistogramView extends View {
    private static final String TAG = "IrisLiveHistogram";
    private static final int COPY_W = 96;
    private static final int COPY_H = 54;
    private static final int BINS = 64;
    private static final long RETRY_MS = 32L;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private HandlerThread workerThread;
    private Handler workerHandler;
    private Bitmap copyBitmap;
    /* Reused full-copy scratch: the always-on histogram must not allocate a ~20 KB int[]
     * for every preview update. The tiny published RGB bin arrays remain immutable per frame so
     * UI drawing can never race the worker while the next reduction is being filled. */
    private final int[] pixelScratch = new int[COPY_W * COPY_H];
    private GLPreview preview;
    private boolean inFlight;
    private boolean running;

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

    public IrisLiveHistogramView(Context context) {
        super(context);
        init();
    }

    public IrisLiveHistogramView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public IrisLiveHistogramView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setWillNotDraw(false);
        copyBitmap = Bitmap.createBitmap(COPY_W, COPY_H, Bitmap.Config.ARGB_8888);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeWidth(dp(1.1f));
        linePaint.setStrokeJoin(Paint.Join.ROUND);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
        fillPaint.setStyle(Paint.Style.FILL);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(dp(1.4f));
        borderPaint.setColor(Color.argb(0xCC, 255, 255, 255));
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        startWorker();
        running = true;
        mainHandler.post(this::ensurePreviewAndRequest);
    }

    @Override
    protected void onDetachedFromWindow() {
        running = false;
        inFlight = false;
        mainHandler.removeCallbacksAndMessages(null);
        preview = null;
        if (workerThread != null) {
            workerThread.quitSafely();
            workerThread = null;
            workerHandler = null;
        }
        super.onDetachedFromWindow();
    }

    @Override
    protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        if (visibility == VISIBLE && isAttachedToWindow()) {
            running = true;
            startWorker();
            mainHandler.post(this::ensurePreviewAndRequest);
        } else if (visibility != VISIBLE) {
            running = false;
            inFlight = false;
            mainHandler.removeCallbacksAndMessages(null);
            clearHistogram();
        }
    }

    private void startWorker() {
        if (workerThread != null && workerThread.isAlive()) return;
        workerThread = new HandlerThread("Iris26668Histogram");
        workerThread.start();
        workerHandler = new Handler(workerThread.getLooper());
    }

    private void ensurePreviewAndRequest() {
        if (!running || !isAttachedToWindow() || getVisibility() != VISIBLE) return;
        if (preview == null) {
            View root = getRootView();
            View candidate = root == null ? null : root.findViewById(R.id.texture);
            if (candidate instanceof GLPreview) preview = (GLPreview) candidate;
        }
        if (preview == null || !preview.isShown() || !preview.isAvailable()
                || Build.VERSION.SDK_INT < Build.VERSION_CODES.N || workerHandler == null) {
            mainHandler.postDelayed(this::ensurePreviewAndRequest, RETRY_MS);
            return;
        }
        if (inFlight) return;
        inFlight = true;
        try {
            PixelCopy.request(preview, copyBitmap, result -> {
                if (!running) {
                    inFlight = false;
                    return;
                }
                if (result == PixelCopy.SUCCESS) {
                    reduceLatestBitmap();
                } else {
                    clearHistogram();
                }
                inFlight = false;
                mainHandler.post(this::ensurePreviewAndRequest);
            }, workerHandler);
        } catch (Throwable t) {
            inFlight = false;
            clearHistogram();
            Log.w(TAG, "IRIS_26668_LIVE_HISTOGRAM_COPY exception="
                    + t.getClass().getSimpleName());
            mainHandler.postDelayed(this::ensurePreviewAndRequest, RETRY_MS);
        }
    }

    private void reduceLatestBitmap() {
        copyBitmap.getPixels(pixelScratch, 0, COPY_W, 0, 0, COPY_W, COPY_H);
        float[] r = new float[BINS];
        float[] g = new float[BINS];
        float[] b = new float[BINS];
        for (int c : pixelScratch) {
            r[Math.min(BINS - 1, Color.red(c) * BINS / 256)] += 1.0f;
            g[Math.min(BINS - 1, Color.green(c) * BINS / 256)] += 1.0f;
            b[Math.min(BINS - 1, Color.blue(c) * BINS / 256)] += 1.0f;
        }
        smooth3(r); smooth3(g); smooth3(b);
        float max = 1.0f;
        for (int i = 2; i < BINS; i++) {
            max = Math.max(max, Math.max(r[i], Math.max(g[i], b[i])));
        }
        // A black preview spike must not flatten the useful body of the graph.
        float darkCap = max * 1.25f;
        r[0] = Math.min(r[0], darkCap); r[1] = Math.min(r[1], darkCap);
        g[0] = Math.min(g[0], darkCap); g[1] = Math.min(g[1], darkCap);
        b[0] = Math.min(b[0], darkCap); b[1] = Math.min(b[1], darkCap);
        normalize(r, max); normalize(g, max); normalize(b, max);
        red = r; green = g; blue = b;
        postInvalidateOnAnimation();
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
        red = new float[BINS];
        green = new float[BINS];
        blue = new float[BINS];
        postInvalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        final float left = getPaddingLeft() + dp(5.0f);
        final float right = getWidth() - getPaddingRight() - dp(5.0f);
        final float top = getPaddingTop() + dp(4.0f);
        final float bottom = getHeight() - getPaddingBottom() - dp(4.0f);
        if (right <= left || bottom <= top) return;

        /* IRIS_26671_HISTOGRAM_INNER_PILL_CLIP
         * The histogram may begin at full-scale when a bright source dominates the preview, but
         * RGB fill/line pixels must never paint into the rounded pill border. Clip the graph to an
         * inset rounded pill for the entire channel pass, then draw the border above it. The view
         * remains read-only and does not change PixelCopy cadence or Camera2 ownership.
         */
        final float innerInset = dp(2.2f);
        innerClipRect.set(innerInset, innerInset,
                getWidth() - innerInset, getHeight() - innerInset);
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
        borderRect.set(halfStroke, halfStroke,
                getWidth() - halfStroke, getHeight() - halfStroke);
        final float borderRadius = Math.max(0.0f, borderRect.height() * 0.5f);
        canvas.drawRoundRect(borderRect, borderRadius, borderRadius, borderPaint);
    }

    private void drawChannel(Canvas canvas, float[] values, int color,
                             float left, float top, float right, float bottom) {
        path.reset();
        path.moveTo(left, bottom);
        for (int i = 0; i < BINS; i++) {
            float x = left + (right - left) * i / (BINS - 1.0f);
            float y = bottom - (bottom - top) * values[i];
            path.lineTo(x, y);
        }
        path.lineTo(right, bottom);
        path.close();
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
