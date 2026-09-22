package com.particlesdevs.photoncamera.spektra;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.RectF;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.TotalCaptureResult;
import android.util.Size;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import com.particlesdevs.photoncamera.util.Log;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Low-quality single-RAW preview owner. Camera callbacks only enqueue; rendering never blocks Camera2. */
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
    private final AtomicBoolean firstFramePresented = new AtomicBoolean(false);
    private CameraCharacteristics characteristics;
    private int sensorOrientation;
    private boolean frontFacing;
    private volatile boolean released;

    public SpektraPreviewRenderer(Activity activity, SurfaceView surfaceView,
            Runnable firstFramePresentedCallback) {
        this.activity = activity;
        this.surfaceView = surfaceView;
        this.firstFramePresentedCallback = firstFramePresentedCallback;
    }

    public void configure(CameraCharacteristics characteristics, Size previewSize, int rawFormat) {
        this.characteristics = characteristics;
        Integer so = characteristics == null ? null : characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Integer facing = characteristics == null ? null : characteristics.get(CameraCharacteristics.LENS_FACING);
        sensorOrientation = so == null ? 0 : so;
        frontFacing = facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT;
        released = false;
        firstFramePresented.set(false);
        Log.d(TAG, "IRIS_26681_SPEKTRA_PREVIEW_CONFIG raw=" + previewSize + " format=" + rawFormat
                + " targetFps=30 quality=LOW scalar=0.25");
    }

    public void beginPreviewSession() {
        firstFramePresented.set(false);
    }

    public void render(SpektraRawFrame frame, SpektraFrameMetadata metadata, TotalCaptureResult result) {
        if (released || frame == null || metadata == null || result == null || !busy.compareAndSet(false, true)) return;
        final CameraCharacteristics cc = characteristics;
        try {
            executor.execute(() -> {
                synchronized (renderLifecycleLock) {
                    Bitmap bitmap = null;
                try {
                    if (released) return;
                    SpektraColorSolver.Solution color = SpektraColorSolver.solve(result, metadata.neutral3,
                        cc.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1), cc.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2),
                        cc.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1), cc.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2),
                        cc.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1), cc.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2),
                        valueOrZero(cc.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)),
                        valueOrZero(cc.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)));
                if (color == null) return;
                SpektraShot shot = new SpektraShot(frame, metadata, System.currentTimeMillis(),
                        color.sensorToLinearSrgb,
                        0, "preview", "preview");
                SpektraRawProcessor.LinearFrame linear = new SpektraRawProcessor().process(shot, false);
                try (SpektraFilmRenderer film = new SpektraFilmRenderer(activity)) {
                    bitmap = film.render(linear, true, System.nanoTime() * 1.0e-9);
                }
                if (!released && draw(bitmap)
                        && firstFramePresented.compareAndSet(false, true)
                        && firstFramePresentedCallback != null) {
                    firstFramePresentedCallback.run();
                }
                } catch (Throwable t) {
                    if (!released) Log.e(TAG, "IRIS_26681_SPEKTRA_PREVIEW_RENDER_FAILED", t);
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
        released = true;
        executor.shutdownNow();
        // IRIS_26682_SPEKTRA_PREVIEW_DRAIN_ON_HANDOFF
        // busy permits at most one render. Waiting on this lock therefore proves that the active
        // RAW/RCD/SPEKTRA render has left before Photo/Night/Motion may retake camera/GPU ownership.
        synchronized (renderLifecycleLock) {
            busy.set(false);
        }
        Log.i(TAG, "IRIS_26682_SPEKTRA_PREVIEW_DRAINED");
    }

    private static int valueOrZero(Integer value) { return value == null ? 0 : value; }
    private static int valueOrZero(Byte value) { return value == null ? 0 : Byte.toUnsignedInt(value); }
}
