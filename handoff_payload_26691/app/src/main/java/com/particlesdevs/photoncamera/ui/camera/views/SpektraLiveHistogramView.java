package com.particlesdevs.photoncamera.ui.camera.views;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.Nullable;

import com.particlesdevs.photoncamera.spektra.SpektraModeController;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26691_SPEKTRA_NATIVE_HISTOGRAM_OWNER
 *
 * Spektra-only presentation of Unspektrawesome 1.1.2's native ViewfinderHistogram. The native
 * renderer returns its exact 128x128 ARGB histogram image. This view never samples the ordinary Iris preview and
 * never touches the existing histogram implementation used by Photo/Motion/Night/Super-Res.
 * Exactly one worker poll is scheduled at a time so histogram work cannot queue behind preview.
 */
public final class SpektraLiveHistogramView extends View {
    private static final String TAG = "SpektraHistogram";
    private static final int NATIVE_SIDE = 128;
    private static final int NATIVE_PIXELS = NATIVE_SIDE * NATIVE_SIDE;
    private static final long POLL_MS = 120L;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Bitmap bitmap = Bitmap.createBitmap(NATIVE_SIDE, NATIVE_SIDE, Bitmap.Config.ARGB_8888);
    private HandlerThread workerThread;
    private Handler workerHandler;
    private volatile SpektraModeController controller;
    private volatile boolean running;
    private volatile boolean hasFrame;
    private boolean failureLogged;

    public SpektraLiveHistogramView(Context context) {
        super(context);
        init();
    }

    public SpektraLiveHistogramView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public SpektraLiveHistogramView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setWillNotDraw(false);
    }

    public void bind(@Nullable SpektraModeController controller) {
        this.controller = controller;
        if (controller == null) {
            hasFrame = false;
            invalidate();
        }
    }

    public void setSpektraActive(boolean active) {
        setVisibility(active ? VISIBLE : GONE);
        if (active && isAttachedToWindow()) startPolling(); else stopPolling();
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        if (getVisibility() == VISIBLE) startPolling();
    }

    @Override
    protected void onDetachedFromWindow() {
        stopPolling();
        controller = null;
        super.onDetachedFromWindow();
    }

    private void startPolling() {
        if (running) return;
        running = true;
        if (workerThread == null || !workerThread.isAlive()) {
            workerThread = new HandlerThread("Iris26691SpektraHistogram");
            workerThread.start();
            workerHandler = new Handler(workerThread.getLooper());
        }
        schedulePoll(0L);
    }

    private void stopPolling() {
        running = false;
        if (workerHandler != null) workerHandler.removeCallbacksAndMessages(null);
        if (workerThread != null) {
            workerThread.quitSafely();
            workerThread = null;
            workerHandler = null;
        }
        hasFrame = false;
        mainHandler.post(this::invalidate);
    }

    private void schedulePoll(long delayMs) {
        Handler worker = workerHandler;
        if (!running || worker == null) return;
        worker.postDelayed(this::pollOnce, delayMs);
    }

    private void pollOnce() {
        if (!running) return;
        SpektraModeController active = controller;
        int[] pixels = active == null ? new int[0] : active.histogramPixels(1.0f);
        if (pixels.length == NATIVE_PIXELS) {
            mainHandler.post(() -> {
                if (!running) return;
                bitmap.setPixels(pixels, 0, NATIVE_SIDE, 0, 0, NATIVE_SIDE, NATIVE_SIDE);
                hasFrame = true;
                failureLogged = false;
                invalidate();
            });
        } else if (pixels.length != 0 && !failureLogged) {
            failureLogged = true;
            Log.w(TAG, "IRIS_26691_SPEKTRA_HISTOGRAM_BAD_SIZE length=" + pixels.length);
        }
        schedulePoll(POLL_MS);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (!hasFrame) return;
        canvas.drawBitmap(bitmap, null,
                new android.graphics.Rect(0, 0, getWidth(), getHeight()), paint);
    }
}
