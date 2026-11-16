package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;

import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;
import android.view.PixelCopy;
import android.os.Build;
import android.graphics.Bitmap;
import android.content.Context;
import android.graphics.Matrix;
import android.graphics.Point;
import android.graphics.SurfaceTexture;
import android.opengl.GLSurfaceView;
import javax.microedition.khronos.egl.EGL10;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.egl.EGLContext;
import javax.microedition.khronos.egl.EGLDisplay;
import android.os.Handler;
import android.os.Looper;
import android.util.AttributeSet;
import android.view.SurfaceHolder;
import android.view.TextureView;


public class GLPreview extends GLSurfaceView {
    MainRenderer mRenderer;
    private int mRatioWidth;
    private int mRatioHeight;
    public Point cameraSize;
    private TextureView.SurfaceTextureListener surfaceTextureListener;
    private Handler handler;
    /* IRIS_26548_PREVIEW_SURFACE_HANDSHAKE
     * GLSurfaceView can create MainRenderer's camera SurfaceTexture before CaptureController
     * installs the TextureView-style listener. Keep the real surface generation as durable state
     * and replay it exactly once instead of dropping the event and leaving Camera2 unopened.
     */
    private final Object surfaceTextureStateLock = new Object();
    private SurfaceTexture currentSurfaceTexture;
    private int currentSurfaceWidth;
    private int currentSurfaceHeight;
    private long surfaceTextureGeneration = 0L;
    private long deliveredSurfaceTextureGeneration = -1L;
    private volatile boolean previewFrameReceived = false;
    /* IRIS_26945_FRONT_REAR_PREVIEW_SESSION_BARRIER
     * -1: waiting for the first NEW Camera2 preview result; >0: earliest
     * sensor timestamp allowed on the reused SurfaceTexture; 0: presented.
     * Only front<->rear camera restarts activate this, never rear lens hops.
     */
    private volatile long iris26945FrontRearMinTimestampNs = 0L;

    public void beginFrontRearPreviewHandoff() {
        iris26945FrontRearMinTimestampNs = -1L;
        previewFrameReceived = false;
        Log.i("GLPreview", "IRIS_26945_FRONT_REAR_PREVIEW_HOLD begin=true");
        requestRender();
    }

    public void confirmFrontRearPreviewResult(long timestampNs) {
        if (timestampNs <= 0L) return;
        synchronized (surfaceTextureStateLock) {
            if (iris26945FrontRearMinTimestampNs != -1L) return;
            iris26945FrontRearMinTimestampNs = timestampNs;
        }
        Log.i("GLPreview", "IRIS_26945_FRONT_REAR_PREVIEW_RESULT minNs=" + timestampNs);
        requestRender();
    }

    public boolean isFrontRearPreviewHandoffPending() {
        return iris26945FrontRearMinTimestampNs != 0L;
    }

    /** Called by the GL draw thread with the *newly latched* SurfaceTexture timestamp. */
    public boolean shouldPresentFrontRearPreviewFrame(long updatedTimestampNs) {
        long expected = iris26945FrontRearMinTimestampNs;
        if (expected == 0L) return true;
        if (expected < 0L || updatedTimestampNs < expected) return false;
        synchronized (surfaceTextureStateLock) {
            if (iris26945FrontRearMinTimestampNs != expected) return false;
            iris26945FrontRearMinTimestampNs = 0L;
        }
        Log.i("GLPreview", "IRIS_26945_FRONT_REAR_PREVIEW_RELEASE resultNs="
                + expected + " frameNs=" + updatedTimestampNs);
        fireOnPreviewFrameAvailable();
        return true;
    }

    public GLPreview(Context context) {
        super(context);
        init();
    }

    public GLPreview(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        handler = new Handler(Looper.getMainLooper());
        mRenderer = new MainRenderer(this);

        setEGLContextClientVersion(2);
        /* IRIS_26936_PREVIEW_GPU_QOS: Adreno shares graphics and Vulkan
         * compute hardware. Prefer the well-defined EGL_IMG_context_priority
         * HIGH level when the driver advertises it, with an exact legacy ES2
         * fallback if unavailable/rejected. No EGL ownership is transferred
         * and no LKR native/solver binaries are modified. Context priority
         * is a DRIVER HINT, never a guaranteed preemption contract. */
        setEGLContextFactory(new GLSurfaceView.EGLContextFactory() {
            private final int EGL_CONTEXT_CLIENT_VERSION = 0x3098;
            private final int EGL_CONTEXT_PRIORITY_LEVEL_IMG = 0x3100;
            private final int EGL_CONTEXT_PRIORITY_HIGH_IMG = 0x3101;
            @Override public EGLContext createContext(EGL10 egl, EGLDisplay display,
                                                       EGLConfig config) {
                int[] ordinary = {EGL_CONTEXT_CLIENT_VERSION, 2, EGL10.EGL_NONE};
                String extensions = egl.eglQueryString(display, EGL10.EGL_EXTENSIONS);
                boolean prioritySupported = extensions != null
                        && java.util.Arrays.asList(extensions.split(" "))
                            .contains("EGL_IMG_context_priority");
                if (prioritySupported) {
                    int[] preferred = {EGL_CONTEXT_CLIENT_VERSION, 2,
                            EGL_CONTEXT_PRIORITY_LEVEL_IMG, EGL_CONTEXT_PRIORITY_HIGH_IMG,
                            EGL10.EGL_NONE};
                    EGLContext preferredContext = egl.eglCreateContext(
                            display, config, EGL10.EGL_NO_CONTEXT, preferred);
                    if (preferredContext != null
                            && preferredContext != EGL10.EGL_NO_CONTEXT) {
                        Log.i("GLPreview", "IRIS_26936_EGL_PREVIEW_PRIORITY=HIGH_IMG "
                                + "driverHintOnly=true");
                        return preferredContext;
                    }
                    Log.w("GLPreview", "IRIS_26936_EGL_PRIORITY_REJECTED err="
                            + Integer.toHexString(egl.eglGetError()) + " legacyFallback=true");
                }
                EGLContext context = egl.eglCreateContext(
                        display, config, EGL10.EGL_NO_CONTEXT, ordinary);
                Log.i("GLPreview", "IRIS_26936_EGL_PREVIEW_PRIORITY="
                        + (prioritySupported ? "FALLBACK_NORMAL" : "UNSUPPORTED_NORMAL")
                        + " legacyContext=" + (context != null));
                return context;
            }
            @Override public void destroyContext(EGL10 egl, EGLDisplay display,
                                                  EGLContext context) {
                if (!egl.eglDestroyContext(display, context)) {
                    Log.w("GLPreview", "IRIS_26936_EGL_CONTEXT_DESTROY_FAILED err="
                            + Integer.toHexString(egl.eglGetError()));
                }
            }
        });
        setRenderer(mRenderer);
        // Keep redrawing the latest preview texture while the unified
        // sensor request uses a slow Motion exposure.
        setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
    }

    public void fireOnSurfaceTextureAvailable(SurfaceTexture surfaceTexture, int w, int h) {
        if (surfaceTexture == null) return;
        handler.post(() -> {
            TextureView.SurfaceTextureListener listenerToNotify = null;
            long generation;
            synchronized (surfaceTextureStateLock) {
                if (currentSurfaceTexture != surfaceTexture) {
                    currentSurfaceTexture = surfaceTexture;
                    currentSurfaceWidth = w;
                    currentSurfaceHeight = h;
                    surfaceTextureGeneration++;
                    deliveredSurfaceTextureGeneration = -1L;
                    previewFrameReceived = false;
                } else {
                    currentSurfaceWidth = w;
                    currentSurfaceHeight = h;
                }
                available = true;
                generation = surfaceTextureGeneration;
                if (surfaceTextureListener != null
                        && deliveredSurfaceTextureGeneration != generation) {
                    deliveredSurfaceTextureGeneration = generation;
                    listenerToNotify = surfaceTextureListener;
                }
            }
            Log.i("GLPreview", "IRIS_26548_PREVIEW_SURFACE_CREATED generation=" + generation
                    + " listenerPresent=" + (listenerToNotify != null));
            if (listenerToNotify != null) {
                listenerToNotify.onSurfaceTextureAvailable(surfaceTexture, w, h);
                Log.i("GLPreview", "IRIS_26548_PREVIEW_SURFACE_DELIVERED generation=" + generation
                        + " replay=false");
            }
        });
    }

    public void fireOnSurfaceTextureDestroyed(SurfaceTexture surfaceTexture) {
        handler.post(() -> {
            TextureView.SurfaceTextureListener listenerToNotify;
            long generation;
            synchronized (surfaceTextureStateLock) {
                if (surfaceTexture != null && currentSurfaceTexture != null
                        && currentSurfaceTexture != surfaceTexture) {
                    return;
                }
                listenerToNotify = surfaceTextureListener;
                currentSurfaceTexture = null;
                currentSurfaceWidth = 0;
                currentSurfaceHeight = 0;
                available = false;
                surfaceTextureGeneration++;
                generation = surfaceTextureGeneration;
                deliveredSurfaceTextureGeneration = -1L;
                previewFrameReceived = false;
            }
            Log.i("GLPreview", "IRIS_26548_PREVIEW_SURFACE_DESTROYED generation=" + generation);
            if (listenerToNotify != null && surfaceTexture != null)
                listenerToNotify.onSurfaceTextureDestroyed(surfaceTexture);
        });
    }

    public void surfaceCreated(SurfaceHolder holder) {
        super.surfaceCreated(holder);
    }

    public void surfaceDestroyed(SurfaceHolder holder) {
        super.surfaceDestroyed(holder);
    }

    public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) {
        super.surfaceChanged(holder, format, w, h);
        handler.post(() -> {
            if (surfaceTextureListener != null)
                surfaceTextureListener.onSurfaceTextureSizeChanged(getSurfaceTexture(), w, h);
        });
    }

    @Override
    public void onResume() {
        super.onResume();

        //mRenderer.onResume();
    }

    @Override
    public void onPause() {
        available = false;
        fireOnSurfaceTextureDestroyed(getSurfaceTexture());
        //mRenderer.onPause();
        super.onPause();
    }

    /**
     * Sets the aspect ratio for this view. The size of the view will be measured based on the ratio
     * calculated from the parameters. Note that the actual sizes of parameters don't matter, that
     * is, calling setAspectRatio(2, 3) and setAspectRatio(4, 6) make the same result.
     *
     * @param width  Relative horizontal size
     * @param height Relative vertical size
     */
    public void setAspectRatio(int width, int height) {
        if (width < 0 || height < 0) {
            throw new IllegalArgumentException("Size cannot be negative.");
        }

        mRatioWidth = width;
        mRatioHeight = height;
        this.post(this::requestLayout);

    }


    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        super.onLayout(changed, left, top, right, bottom);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
        int width = MeasureSpec.getSize(widthMeasureSpec);
        int height = MeasureSpec.getSize(heightMeasureSpec);

        if (mRatioWidth == 0 || mRatioHeight == 0)
            setMeasuredDimension(width, height);
        else {
            if (width > height * mRatioWidth / mRatioHeight)
                setMeasuredDimension(width, width * mRatioHeight / mRatioWidth);
            else
                setMeasuredDimension(height * mRatioWidth / mRatioHeight, height);
            setMeasuredDimension(mRatioWidth, mRatioHeight);
        }
    }

    public SurfaceTexture getSurfaceTexture() {
        return mRenderer.getmSTexture();
    }

    public void setTransform(Matrix matrix) {

    }

    public void setOrientation(int or) {
        mRenderer.setOrientation(or);
    }

    public void setMirror(boolean mirror) {
        mRenderer.setMirror(mirror);
        requestRender();
    }

    /* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
    public void setSoftwareZoom(float zoom) {
        mRenderer.setSoftwareZoom(Math.max(1.0f, zoom));
        requestRender();
    }

    /** IRIS_26516_SHUTTER_VIEWFINDER_PIXELCOPY
     * Request a small copy of the already-rendered preview surface. The copy is asynchronous: the
     * still capture proceeds immediately, while Motion postprocessing consumes the result later.
     */
    public void requestMotionViewfinderMetering() {
        final long requestId = MotionViewfinderMetering.beginRequest();
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N
                || getHolder() == null || getHolder().getSurface() == null
                || !getHolder().getSurface().isValid()
                || getWidth() <= 0 || getHeight() <= 0) {
            MotionViewfinderMetering.fail(requestId, PixelCopy.ERROR_SOURCE_INVALID);
            Log.w("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY unavailable requestId=" + requestId);
            return;
        }
        int srcW = getWidth(), srcH = getHeight();
        int longEdge = 256;
        int dstW, dstH;
        if (srcW >= srcH) {
            dstW = longEdge;
            dstH = Math.max(1, Math.round(longEdge * srcH / (float)srcW));
        } else {
            dstH = longEdge;
            dstW = Math.max(1, Math.round(longEdge * srcW / (float)srcH));
        }
        final Bitmap bitmap = Bitmap.createBitmap(dstW, dstH, Bitmap.Config.ARGB_8888);
        try {
            PixelCopy.request(this, bitmap, result -> {
                MotionViewfinderMetering.complete(requestId, result, bitmap);
                Log.d("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY requestId=" + requestId
                        + " result=" + result + " size=" + dstW + "x" + dstH
                        + " asynchronous=true captureBlocked=false");
            }, handler);
        } catch (Throwable t) {
            MotionViewfinderMetering.fail(requestId, PixelCopy.ERROR_UNKNOWN);
            if (!bitmap.isRecycled()) bitmap.recycle();
            Log.w("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY exception="
                    + t.getClass().getSimpleName() + " requestId=" + requestId);
        }
    }

    volatile boolean available = false;

    public boolean isAvailable() {
        return available && currentSurfaceTexture != null;
    }

    public void setSurfaceTextureListener(TextureView.SurfaceTextureListener l) {
        SurfaceTexture replaySurface;
        int replayWidth;
        int replayHeight;
        long replayGeneration;
        synchronized (surfaceTextureStateLock) {
            this.surfaceTextureListener = l;
            available = currentSurfaceTexture != null;
            replaySurface = currentSurfaceTexture;
            replayWidth = currentSurfaceWidth;
            replayHeight = currentSurfaceHeight;
            replayGeneration = surfaceTextureGeneration;
        }
        if (l == null || replaySurface == null) return;
        handler.post(() -> {
            synchronized (surfaceTextureStateLock) {
                if (surfaceTextureListener != l
                        || currentSurfaceTexture != replaySurface
                        || surfaceTextureGeneration != replayGeneration
                        || deliveredSurfaceTextureGeneration == replayGeneration) {
                    return;
                }
                deliveredSurfaceTextureGeneration = replayGeneration;
            }
            Log.i("GLPreview", "IRIS_26548_PREVIEW_SURFACE_REPLAY generation="
                    + replayGeneration);
            l.onSurfaceTextureAvailable(replaySurface, replayWidth, replayHeight);
            Log.i("GLPreview", "IRIS_26548_PREVIEW_SURFACE_DELIVERED generation="
                    + replayGeneration + " replay=true");
        });
    }

    public boolean hasReceivedPreviewFrame() {
        return previewFrameReceived;
    }

    public void fireOnPreviewFrameAvailable() {
        if (previewFrameReceived) return;
        previewFrameReceived = true;
        Log.i("GLPreview", "IRIS_26548_FIRST_PREVIEW_FRAME");
    }

    public void scale(int in_width, int in_height, int out_width, int out_height, int or) {
        mRenderer.scale(in_width, in_height, out_width, out_height, or);
    }
}