package com.particlesdevs.photoncamera.spektra;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.hardware.camera2.CameraCharacteristics;
import android.util.Size;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import com.particlesdevs.photoncamera.util.Log;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/** VF-S presenter. RAW development is already complete before this queue receives a frame. */
public final class SpektraPreviewRenderer {
    private static final String TAG = "SpektraPreviewRenderer";
    private final Activity activity;
    private final SurfaceView surfaceView;
    private final ExecutorService executor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "SpektraPreviewRender"); t.setDaemon(true); return t;
    });
    private final AtomicBoolean busy = new AtomicBoolean(false);
    private final Object renderLifecycleLock = new Object();
    private final Runnable firstFramePresentedCallback;
    private final Consumer<Throwable> failureCallback;
    private final AtomicBoolean firstFramePresented = new AtomicBoolean(false);
    private int sensorOrientation;
    private boolean frontFacing;
    private volatile boolean released;

    public SpektraPreviewRenderer(Activity activity, SurfaceView surfaceView,
            Runnable firstFramePresentedCallback, Consumer<Throwable> failureCallback) {
        this.activity = activity;
        this.surfaceView = surfaceView;
        this.firstFramePresentedCallback = firstFramePresentedCallback;
        this.failureCallback = failureCallback;
    }

    public void configure(CameraCharacteristics characteristics, Size rawStreamSize, Size processSize, int rawFormat) {
        Integer so = characteristics == null ? null : characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Integer facing = characteristics == null ? null : characteristics.get(CameraCharacteristics.LENS_FACING);
        sensorOrientation = so == null ? 0 : so;
        frontFacing = facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT;
        released = false;
        firstFramePresented.set(false);
        Log.d(TAG, "IRIS_26687_SPEKTRA_PREVIEW_CONFIG rawStream=" + rawStreamSize
                + " process=" + processSize + " format=" + rawFormat
                + " targetFps=30 quality=LOW previewShortEdge=480 vfS=true rawOwner=CPU");
    }

    public void beginPreviewSession() { firstFramePresented.set(false); }

    /** Drop presentation work instead of queueing when the previous frame is still being drawn. */
    public boolean canAcceptFrame() { return !released && !busy.get(); }

    public void render(SpektraRawFrame frame) {
        if (released || frame == null || frame.previewLinearRgba16f == null || !busy.compareAndSet(false, true)) return;
        try {
            executor.execute(() -> {
                synchronized (renderLifecycleLock) {
                    Bitmap bitmap = null;
                    try {
                        if (released) return;
                        SpektraRawProcessor.LinearFrame linear = SpektraRawProcessor.previewLinearFrame(frame);
                        try (SpektraFilmRenderer film = new SpektraFilmRenderer(activity)) {
                            bitmap = film.render(linear, true, System.nanoTime() * 1.0e-9);
                        }
                        if (!released && draw(bitmap)
                                && firstFramePresented.compareAndSet(false, true)
                                && firstFramePresentedCallback != null) {
                            activity.runOnUiThread(firstFramePresentedCallback);
                        }
                    } catch (Throwable t) {
                        if (!released) {
                            Log.e(TAG, "IRIS_26687_SPEKTRA_PREVIEW_RENDER_FAILED", t);
                            if (failureCallback != null) failureCallback.accept(t);
                        }
                    } finally {
                        if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
                        busy.set(false);
                    }
                }
            });
        } catch (RuntimeException rejectedAfterRetire) {
            busy.set(false);
            if (!released) throw rejectedAfterRetire;
        }
    }

    private boolean draw(Bitmap bitmap) {
        SurfaceHolder holder = surfaceView.getHolder();
        Surface s = holder.getSurface();
        if (s == null || !s.isValid()) return false;
        Canvas canvas = null;
        boolean presented = false;
        try {
            canvas = holder.lockCanvas();
            if (canvas == null) return false;
            canvas.drawColor(android.graphics.Color.BLACK);
            int rotation = outputRotation();
            float bw = (rotation == 90 || rotation == 270) ? bitmap.getHeight() : bitmap.getWidth();
            float bh = (rotation == 90 || rotation == 270) ? bitmap.getWidth() : bitmap.getHeight();
            float scale = Math.max(canvas.getWidth() / bw, canvas.getHeight() / bh);
            Matrix m = new Matrix();
            m.postTranslate(-bitmap.getWidth() / 2f, -bitmap.getHeight() / 2f);
            m.postRotate(rotation);
            m.postScale(frontFacing ? -scale : scale, scale);
            m.postTranslate(canvas.getWidth() / 2f, canvas.getHeight() / 2f);
            canvas.drawBitmap(bitmap, m, null);
            presented = true;
        } finally {
            if (canvas != null) holder.unlockCanvasAndPost(canvas);
        }
        return presented;
    }

    private int outputRotation() {
        int display = 0;
        int r = activity.getWindowManager().getDefaultDisplay().getRotation();
        if (r == Surface.ROTATION_90) display = 90;
        else if (r == Surface.ROTATION_180) display = 180;
        else if (r == Surface.ROTATION_270) display = 270;
        return frontFacing
                ? (sensorOrientation + display) % 360
                : (sensorOrientation - display + 360) % 360;
    }

    public void release() {
        // Never join a potentially wedged film/Vulkan render from camera teardown. The render task
        // observes released when it returns; Camera2 ownership is free immediately.
        released = true;
        executor.shutdownNow();
        busy.set(false);
        long[] stats = SpektraRawProcessor.nativeStats();
        Log.i(TAG, "IRIS_26687_SPEKTRA_PREVIEW_DRAINED"
                + " vfProcessed=" + stats[0] + " vfDropped=" + stats[1]
                + " avgVfMicros=" + stats[2] + " lastStillMicros=" + stats[3]
                + " rawOwners=" + stats[4] + " persistentRawAllocations=" + stats[5]);
    }
}
