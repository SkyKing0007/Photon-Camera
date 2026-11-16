package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;

import android.graphics.RectF;
import android.graphics.SurfaceTexture;
import android.opengl.GLES11Ext;
import android.opengl.GLES20;
import android.opengl.GLES30;
import android.opengl.GLSurfaceView;
import com.particlesdevs.photoncamera.util.Log;

import androidx.annotation.NonNull;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.capture.Iris26911Continuity;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Arrays;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class MainRenderer implements GLSurfaceView.Renderer, SurfaceTexture.OnFrameAvailableListener {

    private int[] hTex;
    private final FloatBuffer pVertex;
    private final FloatBuffer pTexCoord;
    /* IRIS_26945_PREVIEW_ATOMIC_ORIENTATION: UI thread publishes a whole matrix;
     * GL never reads a half-written 180-degree camera-switch transform. */
    private volatile float[] mTexRotateMatrix = new float[]{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};

    private SurfaceTexture mSTexture;

    private boolean mGLInit = false;
    private boolean mUpdateST = false;
    /* IRIS_26553_MOTOROLA_A_PREVIEW_DIAGNOSTICS */
    private boolean mIris26553FirstFrameAvailableLogged = false;
    private boolean mIris26553FirstFrameDrawLogged = false;
    private int mIris26553PreviewProgram = 0;
    private volatile boolean mMirrorPreview;
    /* IRIS_26524_PREVIEW_RESIDUAL_ZOOM */
    private volatile float mSoftwareZoom = 1.0f;
    /* IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION_STATE
     * Keep only the last exact Camera2-result protection value. No second presentation slew is
     * permitted; metadata misses hold the last exact value. */
    private float mIris26663LastConfirmedProtectionEv = 0.0f;
    /* IRIS_26911_WYSIWYG_SENSOR_TRANSITION: capture-only preview sampling state;
     * no pipeline exposure/ISP ownership is changed. */
    private final Iris26911Continuity.Preview mIris26911Preview = new Iris26911Continuity.Preview();
    private long mIris26911LastGeneration = -1L;
    private boolean mIris26911PreviewCalibratedLogged = false;
    /* IRIS_26678_PREVIEW_FLICKER_PRESENTATION_STATE
     * Phase-specific row evidence never holds indefinitely: each displayed frame receives exact or
     * at-most-one-frame-old timestamp-owned evidence, otherwise correction is neutral. */
    private final float[] mIris26678PreviewFlicker = new float[4];

    /* IRIS_26872_PREVIEW_FLICKER_GL_OWNER: 12x96 frame-local probe, no retained GPU
     * full-resolution preview image and no per-pixel RAW corrections. */
    private final Iris26872PreviewStripe mIris26872Stripe = new Iris26872PreviewStripe();
    private final ByteBuffer mIris26872ProbeReadback = ByteBuffer.allocateDirect(
            4 * Iris26872PreviewStripe.WIDTH * Iris26872PreviewStripe.HEIGHT);
    private int mIris26872ProbeProgram = 0;
    private int mIris26872ProbeFbo = 0;
    private int mIris26872ProbeTex = 0;
    private int mIris26872StripeUniform = -1;
    private int mIris26872ViewportW = 1;
    private int mIris26872ViewportH = 1;
    private boolean mIris26872ProbeDisabled = false;
    private boolean mIris26872LastEligible = false;
    private boolean mIris26872LoggedFirstValid = false;
    private int mIris26872ProbePosition = -1;
    private int mIris26872ProbeSampler = -1;
    /* IRIS_26935_LKR_READBACK_BUDGET: only measured B/ON contention
     * permits a bounded skip. Never guess a sample/exposure timestamp. */
    private int mIris26935ProbeSkipBudget;
    private int mIris26935SlowReadbackEvents;
    private long mIris26935LastProbeWaitNs;
    private boolean mIris26935LastBusy;
    private long mIris26935LastFrameNs;
    private long mIris26935LastMeasuredTimestamp;
    private int mIris26935FrameCount;
    /* IRIS_26936_B_ON_NONBLOCKING_PROBE
     * Two GLES3 PBOs + fences live exclusively on this GLSurfaceView GL
     * thread. Never map a buffer until its GPU fence is signaled; never
     * apply a previous sensor timestamp's stripe phase to the displayed
     * preview frame. Under measured flicker / low-light, keep the original
     * synchronous EXACT-frame probe and compensation, unchanged. */
    private static final int IRIS_26936_PROBE_BYTES =
            4 * Iris26872PreviewStripe.WIDTH * Iris26872PreviewStripe.HEIGHT;
    private final int[] mIris26936Pbo = new int[2];
    private final long[] mIris26936Fence = new long[2];
    private final long[] mIris26936PendingTimestamp = new long[2];
    private int mIris26936WriteCursor;
    private boolean mIris26936AsyncReady;
    private boolean mIris26936AsyncUnsupported;
    private boolean mIris26936AsyncThisFrame;
    private int mIris26936Submitted;
    private int mIris26936Completed;
    private int mIris26936Backpressure;
    private long mIris26936LastCompletedTimestamp;
    private long mIris26936WorstSubmitNs;

    private final GLPreview mView;

    MainRenderer(GLPreview view) {
        mView = view;
        pVertex = ByteBuffer.allocateDirect(8 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
        float[] vtmp = {1.0f, -1.0f, -1.0f, -1.0f, 1.0f, 1.0f, -1.0f, 1.0f};
        pVertex.put(vtmp);
        pVertex.position(0);
        pTexCoord = ByteBuffer.allocateDirect(8 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
        float[] ttmp = {1.0f, 1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f};
        pTexCoord.put(ttmp);
        pTexCoord.position(0);
        setOrientation(180);
    }


    public void onDrawFrame(GL10 unused) {
        if (!mGLInit) return;
        //GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        long iris26553FrameTimestamp = -1L;
        synchronized (this) {
            if (mUpdateST) {
                mSTexture.updateTexImage();
                iris26553FrameTimestamp = mSTexture.getTimestamp();
                mUpdateST = false;
            }
        }
        /* IRIS_26945_FRONT_REAR_PREVIEW_SESSION_BARRIER
         * Hide recycled front frames under a rear transform (and vice versa).
         * New session RESULT plus a new SurfaceTexture frame are both required;
         * no stale camera frame is ever rendered under the destination angle.
         */
        if (!mView.shouldPresentFrontRearPreviewFrame(iris26553FrameTimestamp)) {
            GLES20.glClearColor(0f, 0f, 0f, 1f);
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
            return;
        }
        /* Check the active physical-lens B owner on every new preview frame. Never
         * substitute the historic 26679 RAW-row correction or alter HAL AE. */
        CaptureController iris26872Controller = PhotonCamera.getCaptureController();
        boolean iris26872Eligible = iris26872Controller != null
                && iris26872Controller.iris26872BPreviewStripeEligible();
        if (iris26872Eligible != mIris26872LastEligible) {
            iris26936DisposeAsyncProbe();
            mIris26872Stripe.reset();
            mIris26911Preview.reset();
            mIris26872LastEligible = iris26872Eligible;
        }
        if (iris26872Eligible) {
            long generation = iris26872Controller.iris26911PreviewGeneration();
            if (mIris26911LastGeneration != generation) {
                mIris26911Preview.reset();
                mIris26911PreviewCalibratedLogged = false;
                mIris26911LastGeneration = generation;
                mIris26663LastConfirmedProtectionEv = 0.0f;
            }
        }
        final boolean iris26935Busy = iris26872Eligible
                && com.particlesdevs.photoncamera.capture.Iris26935BOnSession.isActive();
        if (iris26935Busy != mIris26935LastBusy) {
            mIris26935LastBusy = iris26935Busy;
            mIris26935ProbeSkipBudget = 0;
            mIris26935LastProbeWaitNs = 0L;
            mIris26935LastFrameNs = 0L;
            iris26936DisposeAsyncProbe();
            Log.i("MainRenderer", "IRIS_26935_PREVIEW_B_ON_LKR busy=" + iris26935Busy);
        }
        if (iris26872Eligible && iris26553FrameTimestamp > 0L) {
            /* IRIS_26936_B_ON_NONBLOCKING_PROBE: use bounded async GPU
             * readback ONLY during B/ON LKR while the scene is not low-light
             * and no stripe compensation is active. If a late async sample
             * detects flicker, return to exact-frame synchronous sampling
             * immediately; never present stale phase coefficients. */
            final boolean iris26936LowLight = iris26872Controller.iris26911DarkPreviewEvidence();
            final boolean iris26936StripeActive = mIris26872Stripe.params()[3] > 0.0f;
            mIris26936AsyncThisFrame = false;
            final boolean iris26936AllowAsync = iris26935Busy && !iris26936LowLight
                    && !iris26936StripeActive && !mIris26872ProbeDisabled;
            if (iris26936AllowAsync) {
                mIris26936AsyncThisFrame = iris26936ProbeAsync(iris26553FrameTimestamp);
            }
            if (!mIris26936AsyncThisFrame) {
                if (mIris26936AsyncReady) iris26936DisposeAsyncProbe();
                long iris26935Start = System.nanoTime();
                iris26872Probe(iris26553FrameTimestamp);
                mIris26935LastMeasuredTimestamp = iris26553FrameTimestamp;
                mIris26935LastProbeWaitNs = System.nanoTime() - iris26935Start;
                if (iris26935Busy && mIris26935LastProbeWaitNs > 12_000_000L) {
                    mIris26935SlowReadbackEvents++;
                    if (mIris26935SlowReadbackEvents == 1
                            || mIris26935SlowReadbackEvents % 120 == 0) {
                        Log.i("MainRenderer", "IRIS_26936_SYNC_PROTECTED_PROBE_WAIT_NS="
                                + mIris26935LastProbeWaitNs + " lowLight=" + iris26936LowLight
                                + " stripeActive=" + iris26936StripeActive);
                    }
                }
            } else {
                mIris26935LastProbeWaitNs = 0L;
            }
            mIris26935FrameCount++;
            if (iris26935Busy && mIris26935FrameCount % 120 == 0) {
                long frameDelta = mIris26935LastFrameNs > 0L
                        ? System.nanoTime() - mIris26935LastFrameNs : 0L;
                Log.i("MainRenderer", "IRIS_26935_PREVIEW_FRAME_TRACE timestamp="
                        + iris26553FrameTimestamp + " probeWallWaitNs="
                        + mIris26935LastProbeWaitNs + " renderDeltaNs=" + frameDelta);
            }
            mIris26935LastFrameNs = System.nanoTime();
            mIris26911Preview.resolve(iris26553FrameTimestamp,
                    iris26872Controller::iris26911PreviewStage,
                    iris26872Controller.iris26911DarkPreviewEvidence(),
                    iris26872Controller.iris26911RawSceneMean());
            if (mIris26911Preview.liftEv() > 0.25f && !mIris26911PreviewCalibratedLogged) {
                mIris26911PreviewCalibratedLogged = true;
                Log.i("MainRenderer", "IRIS_26911_B_PREVIEW_MEASURED_GAIN"
                        + " ev=" + mIris26911Preview.liftEv()
                        + " actualRawScene=" + iris26872Controller.iris26911RawSceneMean()
                        + " sceneAllowsLowLight=" + iris26872Controller.iris26911DarkPreviewEvidence()
                        + " exactTimestampOwnership=true noSensorAEChange=true");
            }
        }
        float[] iris26872Stripe = mIris26872Stripe.params();
        /* A missed GPU probe cannot apply prior-frame stripe phase to the
         * new frame: neutral strength, not stale anti-stripe/exposure evidence. */
        final boolean iris26935UnmeasuredFrame = iris26935Busy
                && iris26553FrameTimestamp > 0L
                && iris26553FrameTimestamp != mIris26935LastMeasuredTimestamp;
        /* Async probes are deliberately delayed: their measured flicker
         * coefficients NEVER apply to another displayed sensor timestamp. */
        GLES20.glUniform4f(mIris26872StripeUniform, iris26872Stripe[0], iris26872Stripe[1],
                iris26872Stripe[2], iris26872Eligible && !iris26935UnmeasuredFrame
                        ? iris26872Stripe[3] : 0f);
        GLES20.glUniformMatrix4fv(uTexRotateMatrix, 1, false, mTexRotateMatrix, 0);
        GLES20.glUniform1i(enablePeak, PhotonCamera.getSettings().focusPeak);
        GLES20.glUniform1i(mirror, mMirrorPreview ? 1 : 0);
        GLES20.glUniform1f(irisSoftwareZoom, mSoftwareZoom);
        /* IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION
         * Preserve 26662 timestamp matching and 26663 hold-on-miss, with no additional display
         * slew. Compensation changes only when an exact Camera2 result for the displayed frame
         * proves the protection EV. */
        CaptureController iris26663Controller = PhotonCamera.getCaptureController();
        if (iris26663Controller != null && iris26553FrameTimestamp > 0L) {
            float exactEv = iris26663Controller.getMotion26663ReferencePreviewProtectionEv(
                    iris26553FrameTimestamp);
            if (Float.isFinite(exactEv)) {
                float targetEv = Math.max(0.0f, exactEv);
                if (iris26872Eligible && iris26663Controller.iris26910PreserveBManualExposure()) {
                    /* Preserve the *observed* bright HAL appearance across
                     * the 26909 AE-ON -> AE-OFF transition. Only a measured
                     * low-light preview ISP brightness drop may add EV. */
                    targetEv = Math.max(targetEv, mIris26911Preview.liftEv());
                }
                if (iris26663Controller.iris26910PreserveBManualExposure()) {
                    /* IRIS_26910_DARK_B_PREVIEW_ONLY_SLEW
                     * Smooth only new B manual low-light presentation lift;
                     * A/HAL Auto and all preexisting preview behavior remain
                     * bit-identical. No artificial RAW frames or AE writes. */
                    float difference = targetEv - mIris26663LastConfirmedProtectionEv;
                    mIris26663LastConfirmedProtectionEv += Math.max(-0.22f,
                            Math.min(0.22f, difference));
                } else {
                    mIris26663LastConfirmedProtectionEv = targetEv;
                }
            }
        }
        float iris26667PreviewGain = (float) Math.pow(2.0,
                Math.max(0.0f, mIris26663LastConfirmedProtectionEv));
        GLES20.glUniform1f(iris26662ReferencePreviewGain, iris26667PreviewGain);
        mIris26678PreviewFlicker[0] = 0.0f;
        mIris26678PreviewFlicker[1] = 0.0f;
        mIris26678PreviewFlicker[2] = 0.0f;
        mIris26678PreviewFlicker[3] = 0.0f;
        if (iris26663Controller != null && iris26553FrameTimestamp > 0L) {
            iris26663Controller.getMotion26678PreviewFlicker(
                    iris26553FrameTimestamp, mIris26678PreviewFlicker);
        }
        GLES20.glUniform4f(iris26678FlickerParams,
                mIris26678PreviewFlicker[0], mIris26678PreviewFlicker[1],
                mIris26678PreviewFlicker[2], mIris26678PreviewFlicker[3]);

        GLES20.glVertexAttribPointer(vPosition, 2, GLES20.GL_FLOAT, false, 4 * 2, pVertex);
        GLES20.glVertexAttribPointer(vTexCoord, 2, GLES20.GL_FLOAT, false, 4 * 2, pTexCoord);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
        if (!mIris26553FirstFrameDrawLogged && iris26553FrameTimestamp >= 0L) {
            mIris26553FirstFrameDrawLogged = true;
            int glError = GLES20.glGetError();
            Log.i("MainRenderer", "IRIS_26553_PREVIEW_DIAG_FIRST_DRAW timestamp="
                    + iris26553FrameTimestamp + " program=" + mIris26553PreviewProgram
                    + " glError=0x" + Integer.toHexString(glError)
                    + " view=" + mView.getWidth() + "x" + mView.getHeight()
                    + " alpha=" + mView.getAlpha() + " visibility=" + mView.getVisibility());
        }
        //GLES20.glFlush();
    }

    private int uTexRotateMatrix;
    private int vPosition;
    private int vTexCoord;
    private int enablePeak;
    private int mirror;
    private int irisSoftwareZoom;
    private int iris26662ReferencePreviewGain;
    private int iris26678FlickerParams;

    private void iris26872ProbeDraw() {
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, mIris26872ProbeFbo);
        GLES20.glViewport(0, 0, Iris26872PreviewStripe.WIDTH, Iris26872PreviewStripe.HEIGHT);
        GLES20.glUseProgram(mIris26872ProbeProgram);
        GLES20.glVertexAttribPointer(mIris26872ProbePosition, 2, GLES20.GL_FLOAT, false, 0, pVertex);
        GLES20.glEnableVertexAttribArray(mIris26872ProbePosition);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, hTex[0]);
        GLES20.glUniform1i(mIris26872ProbeSampler, 0);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
    }

    private void iris26872ProbeRestore() {
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0);
        GLES20.glViewport(0, 0, mIris26872ViewportW, mIris26872ViewportH);
        GLES20.glUseProgram(mIris26553PreviewProgram);
    }

    private void iris26872Probe(long timestampNs) {
        if (mIris26872ProbeDisabled || mIris26872ProbeProgram == 0 || mIris26872ProbeFbo == 0)
            return;
        iris26872ProbeDraw();
        mIris26872ProbeReadback.rewind();
        GLES20.glReadPixels(0, 0, Iris26872PreviewStripe.WIDTH,
                Iris26872PreviewStripe.HEIGHT, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE,
                mIris26872ProbeReadback);
        int error = GLES20.glGetError();
        iris26872ProbeRestore();
        if (error != GLES20.GL_NO_ERROR) {
            mIris26872ProbeDisabled = true;
            mIris26872Stripe.reset();
            Log.w("MainRenderer", "IRIS_26872_PREVIEW_PROBE_DISABLED error=0x"
                    + Integer.toHexString(error));
        } else {
            mIris26911Preview.sample(mIris26872ProbeReadback, timestampNs);
            if (mIris26872Stripe.consume(mIris26872ProbeReadback, timestampNs)
                    && !mIris26872LoggedFirstValid) {
                mIris26872LoggedFirstValid = true;
                Log.i("MainRenderer", "IRIS_26872_B_PREVIEW_STRIPE first_confident="
                        + "true preview_only=true hal_ae_unchanged=true");
            }
        }
    }

    /* A completed PBO read is consumed on the original GL thread under its
     * original sensor timestamp. EGL context recreation clears these handles;
     * no GL call is issued from the Camera2/processExecutor/main threads. */
    private void iris26936DisposeAsyncProbe() {
        for (int i = 0; i < 2; i++) {
            if (mIris26936Fence[i] != 0L) {
                GLES30.glDeleteSync(mIris26936Fence[i]);
                mIris26936Fence[i] = 0L;
            }
            mIris26936PendingTimestamp[i] = 0L;
        }
        if (mIris26936AsyncReady) {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
            GLES30.glDeleteBuffers(2, mIris26936Pbo, 0);
        }
        Arrays.fill(mIris26936Pbo, 0);
        mIris26936AsyncReady = false;
        mIris26936WriteCursor = 0;
        mIris26936AsyncThisFrame = false;
        mIris26936LastCompletedTimestamp = 0L;
    }

    private boolean iris26936InitAsyncProbe() {
        if (mIris26936AsyncUnsupported || mIris26872ProbeDisabled) return false;
        if (mIris26936AsyncReady) return true;
        String version = GLES20.glGetString(GLES20.GL_VERSION);
        // This feature requires an ACTUAL GLES 3.x EGL context, not just a
        // GLES3-capable phone. On unknown contexts use proven sync behavior.
        if (version == null || !version.startsWith("OpenGL ES 3.")) {
            mIris26936AsyncUnsupported = true;
            Log.w("MainRenderer", "IRIS_26936_ASYNC_UNSUPPORTED eglVersion=" + version);
            return false;
        }
        GLES30.glGenBuffers(2, mIris26936Pbo, 0);
        boolean valid = mIris26936Pbo[0] != 0 && mIris26936Pbo[1] != 0;
        if (valid) {
            for (int pbo : mIris26936Pbo) {
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, pbo);
                GLES30.glBufferData(GLES30.GL_PIXEL_PACK_BUFFER,
                        IRIS_26936_PROBE_BYTES, null, GLES30.GL_STREAM_READ);
            }
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
            valid = GLES20.glGetError() == GLES20.GL_NO_ERROR;
        }
        if (!valid) {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
            GLES30.glDeleteBuffers(2, mIris26936Pbo, 0);
            Arrays.fill(mIris26936Pbo, 0);
            mIris26936AsyncUnsupported = true;
            Log.w("MainRenderer", "IRIS_26936_ASYNC_UNSUPPORTED PBO allocation failed");
            return false;
        }
        mIris26936AsyncReady = true;
        Log.i("MainRenderer", "IRIS_26936_ASYNC_PBO_READY originalFrameTimestamps=true "
                + "stripeActiveAndLowLightRemainSynchronous=true twoBuffers=2");
        return true;
    }

    private boolean iris26936DrainCompletedProbe(long currentTimestamp) {
        for (int checks = 0; checks < 2; checks++) {
            int oldest = -1;
            for (int i = 0; i < 2; i++) {
                if (mIris26936Fence[i] != 0L
                        && (oldest == -1 || mIris26936PendingTimestamp[i]
                            < mIris26936PendingTimestamp[oldest])) oldest = i;
            }
            if (oldest == -1) return true;
            int ready = GLES30.glClientWaitSync(mIris26936Fence[oldest], 0, 0L);
            if (ready == GLES30.GL_TIMEOUT_EXPIRED) return true;
            if (ready != GLES30.GL_ALREADY_SIGNALED
                    && ready != GLES30.GL_CONDITION_SATISFIED) {
                Log.w("MainRenderer", "IRIS_26936_PBO_SYNC_FAILED code=" + ready);
                mIris26936AsyncUnsupported = true;
                return false;
            }
            final long ownedTimestamp = mIris26936PendingTimestamp[oldest];
            boolean valid = currentTimestamp > 0L && ownedTimestamp > 0L
                    && currentTimestamp >= ownedTimestamp
                    && currentTimestamp - ownedTimestamp <= 250_000_000L;
            if (valid) {
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, mIris26936Pbo[oldest]);
                java.nio.Buffer mapped = GLES30.glMapBufferRange(
                        GLES30.GL_PIXEL_PACK_BUFFER, 0, IRIS_26936_PROBE_BYTES,
                        GLES30.GL_MAP_READ_BIT);
                if (!(mapped instanceof ByteBuffer)) {
                    GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
                    mIris26936AsyncUnsupported = true;
                    return false;
                }
                ByteBuffer buffer = (ByteBuffer) mapped;
                buffer.position(0);
                buffer.limit(IRIS_26936_PROBE_BYTES);
                mIris26872ProbeReadback.clear();
                mIris26872ProbeReadback.put(buffer);
                mIris26872ProbeReadback.rewind();
                boolean unmapped = GLES30.glUnmapBuffer(GLES30.GL_PIXEL_PACK_BUFFER);
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
                if (!unmapped || GLES20.glGetError() != GLES20.GL_NO_ERROR) {
                    mIris26936AsyncUnsupported = true;
                    return false;
                }
                mIris26911Preview.sample(mIris26872ProbeReadback, ownedTimestamp);
                mIris26872Stripe.consume(mIris26872ProbeReadback, ownedTimestamp);
                mIris26936LastCompletedTimestamp = ownedTimestamp;
                mIris26936Completed++;
            } else {
                // A late result cannot supply a guessed current-frame stripe
                // phase or low-light exposure; expire it without consumption.
                mIris26872Stripe.reset();
            }
            GLES30.glDeleteSync(mIris26936Fence[oldest]);
            mIris26936Fence[oldest] = 0L;
            mIris26936PendingTimestamp[oldest] = 0L;
        }
        return true;
    }

    private boolean iris26936ProbeAsync(long timestampNs) {
        if (!iris26936InitAsyncProbe()) return false;
        if (!iris26936DrainCompletedProbe(timestampNs)) {
            iris26936DisposeAsyncProbe();
            return false; // fail closed to original synchronous sampling
        }
        if (mIris26872Stripe.params()[3] > 0.0f) {
            iris26936DisposeAsyncProbe();
            return false; // flicker detected from a timestamp-owned async sample
        }
        int slot = -1;
        for (int i = 0; i < 2; i++) {
            int candidate = (mIris26936WriteCursor + i) % 2;
            if (mIris26936Fence[candidate] == 0L) {slot = candidate;break;}
        }
        if (slot == -1) {
            ++mIris26936Backpressure;
            // Skip an unmeasured frame instead of blocking preview on Vulkan.
            return true;
        }
        long begin = System.nanoTime();
        iris26872ProbeDraw();
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, mIris26936Pbo[slot]);
        GLES30.glReadPixels(0, 0, Iris26872PreviewStripe.WIDTH,
                Iris26872PreviewStripe.HEIGHT, GLES20.GL_RGBA,
                GLES20.GL_UNSIGNED_BYTE, 0);
        long fence = GLES30.glFenceSync(GLES30.GL_SYNC_GPU_COMMANDS_COMPLETE, 0);
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0);
        iris26872ProbeRestore();
        int error = GLES20.glGetError();
        if (error != GLES20.GL_NO_ERROR || fence == 0L) {
            if (fence != 0L) GLES30.glDeleteSync(fence);
            mIris26936AsyncUnsupported = true;
            iris26936DisposeAsyncProbe();
            Log.w("MainRenderer", "IRIS_26936_ASYNC_PBO_FAILED err=0x"
                    + Integer.toHexString(error));
            return false;
        }
        mIris26936Fence[slot] = fence;
        mIris26936PendingTimestamp[slot] = timestampNs;
        mIris26936WriteCursor = (slot + 1) % 2;
        mIris26936Submitted++;
        GLES20.glFlush(); // nonblocking GPU submission, NOT glFinish
        long submitNs = System.nanoTime() - begin;
        mIris26936WorstSubmitNs = Math.max(mIris26936WorstSubmitNs,submitNs);
        if (mIris26936Submitted == 1 || mIris26936Submitted % 120 == 0) {
            Log.i("MainRenderer", "IRIS_26936_ASYNC_PROBE submitted=" + mIris26936Submitted
                    + " consumed=" + mIris26936Completed
                    + " backpressure=" + mIris26936Backpressure
                    + " submitWallNs=" + submitNs
                    + " worstSubmitNs=" + mIris26936WorstSubmitNs
                    + " lastOwnedTs=" + mIris26936LastCompletedTimestamp);
        }
        return true;
    }

    private void iris26872CreateProbe() {
        String vs = "in vec2 vPosition; void main(){gl_Position=vec4(vPosition,0.0,1.0);}";
        String fs = "#extension GL_OES_EGL_image_external_essl3 : require\n"
                + "precision highp float;\n"
                + "uniform samplerExternalOES sTexture;\n"
                + "out vec4 probeOut;\n"
                + "void main(){vec2 uv=gl_FragCoord.xy/vec2(12.0,96.0);"
                + "probeOut=vec4(texture(sTexture,uv).rgb,1.0);}";
        mIris26872ProbeProgram = loadShader(vs, fs);
        int[] linked = new int[1];
        GLES20.glGetProgramiv(mIris26872ProbeProgram, GLES20.GL_LINK_STATUS, linked, 0);
        if (linked[0] == 0) {
            mIris26872ProbeDisabled = true;
            GLES20.glUseProgram(mIris26553PreviewProgram);
            Log.w("MainRenderer", "IRIS_26872_PREVIEW_PROBE_DISABLED link_failed");
            return;
        }
        mIris26872ProbePosition = GLES20.glGetAttribLocation(mIris26872ProbeProgram, "vPosition");
        mIris26872ProbeSampler = GLES20.glGetUniformLocation(mIris26872ProbeProgram, "sTexture");
        if (mIris26872ProbePosition < 0 || mIris26872ProbeSampler < 0) {
            mIris26872ProbeDisabled = true;
            GLES20.glUseProgram(mIris26553PreviewProgram);
            return;
        }
        int[] tex = new int[1];
        int[] fbo = new int[1];
        GLES20.glGenTextures(1, tex, 0);
        mIris26872ProbeTex = tex[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, mIris26872ProbeTex);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_NEAREST);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_NEAREST);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA,
                Iris26872PreviewStripe.WIDTH, Iris26872PreviewStripe.HEIGHT, 0,
                GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, null);
        GLES20.glGenFramebuffers(1, fbo, 0);
        mIris26872ProbeFbo = fbo[0];
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, mIris26872ProbeFbo);
        GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER, GLES20.GL_COLOR_ATTACHMENT0,
                GLES20.GL_TEXTURE_2D, mIris26872ProbeTex, 0);
        int status = GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER);
        mIris26872ProbeDisabled = status != GLES20.GL_FRAMEBUFFER_COMPLETE
                || mIris26872ProbeProgram == 0;
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, 0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, hTex[0]);
        GLES20.glUseProgram(mIris26553PreviewProgram);
        if (mIris26872ProbeDisabled)
            Log.w("MainRenderer", "IRIS_26872_PREVIEW_PROBE_DISABLED framebuffer=0x"
                    + Integer.toHexString(status));
    }
    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        Arrays.fill(mIris26936Pbo, 0);
        Arrays.fill(mIris26936Fence, 0L);
        Arrays.fill(mIris26936PendingTimestamp, 0L);
        mIris26936AsyncReady = false;
        mIris26936AsyncUnsupported = false;
        mIris26936AsyncThisFrame = false;
        mIris26936WriteCursor = 0;
        mIris26935LastBusy = false;
        initTex();
        mSTexture = new SurfaceTexture(hTex[0]);
        mSTexture.setOnFrameAvailableListener(this);

        String vss_default = PhotonCamera.getAssetLoader().getString("shaders/preview/main_vs.glsl");
        String fss_default = PhotonCamera.getAssetLoader().getString("shaders/preview/main_fs.glsl");
        int hProgram = loadShader(vss_default, fss_default);
        mIris26553PreviewProgram = hProgram;
        Log.i("MainRenderer", "IRIS_26553_PREVIEW_DIAG_GL_CREATED vendor="
                + GLES20.glGetString(GLES20.GL_VENDOR) + " renderer="
                + GLES20.glGetString(GLES20.GL_RENDERER) + " version="
                + GLES20.glGetString(GLES20.GL_VERSION) + " glsl="
                + GLES20.glGetString(GLES20.GL_SHADING_LANGUAGE_VERSION)
                + " program=" + hProgram + " texture=" + hTex[0]
                + " view=" + mView.getWidth() + "x" + mView.getHeight());
        GLES20.glUseProgram(hProgram);
        uTexRotateMatrix = GLES20.glGetUniformLocation(hProgram, "uTexRotateMatrix");
        GLES20.glUniformMatrix4fv(uTexRotateMatrix, 1, false, mTexRotateMatrix, 0);
        vPosition = GLES20.glGetAttribLocation(hProgram, "vPosition");
        vTexCoord = GLES20.glGetAttribLocation(hProgram, "vTexCoord");
        enablePeak = GLES20.glGetUniformLocation(hProgram, "enablePeak");
        mirror = GLES20.glGetUniformLocation(hProgram, "mirror");
        irisSoftwareZoom = GLES20.glGetUniformLocation(hProgram, "irisSoftwareZoom");
        iris26662ReferencePreviewGain = GLES20.glGetUniformLocation(hProgram, "iris26662ReferencePreviewGain");
        iris26678FlickerParams = GLES20.glGetUniformLocation(hProgram, "iris26678FlickerParams");
        mIris26872StripeUniform = GLES20.glGetUniformLocation(hProgram, "iris26872PreviewStripe");
        iris26872CreateProbe();
        GLES20.glVertexAttribPointer(vPosition, 2, GLES20.GL_FLOAT, false, 4 * 2, pVertex);
        GLES20.glVertexAttribPointer(vTexCoord, 2, GLES20.GL_FLOAT, false, 4 * 2, pTexCoord);
        GLES20.glEnableVertexAttribArray(vPosition);
        GLES20.glEnableVertexAttribArray(vTexCoord);
        GLES20.glUniform2f(GLES20.glGetUniformLocation(hProgram, "resolution"), mView.getWidth(), mView.getHeight());
        mGLInit = true;
        mView.fireOnSurfaceTextureAvailable(mSTexture, 0, 0);
    }

    public void onSurfaceChanged(GL10 unused, int width, int height) {
        mIris26872ViewportW = Math.max(1, width);
        mIris26872ViewportH = Math.max(1, height);
        GLES30.glViewport(0, 0, width, height);
        Log.i("MainRenderer", "IRIS_26553_PREVIEW_DIAG_SURFACE_CHANGED viewport="
                + width + "x" + height + " glError=0x" + Integer.toHexString(GLES20.glGetError()));
    }



    public SurfaceTexture getmSTexture() {
        return mSTexture;
    }

    private void initTex() {
        hTex = new int[1];
        GLES20.glGenTextures(1, hTex, 0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, hTex[0]);
        GLES20.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
    }

    public synchronized void onFrameAvailable(SurfaceTexture st) {
        mUpdateST = true;
        if (!mIris26553FirstFrameAvailableLogged) {
            mIris26553FirstFrameAvailableLogged = true;
            Log.i("MainRenderer", "IRIS_26553_PREVIEW_DIAG_FIRST_FRAME_AVAILABLE surface="
                    + System.identityHashCode(st) + " view=" + mView.getWidth() + "x"
                    + mView.getHeight() + " alpha=" + mView.getAlpha()
                    + " visibility=" + mView.getVisibility());
        }
        if (!mView.isFrontRearPreviewHandoffPending()) {
            mView.fireOnPreviewFrameAvailable();
        }
        mView.requestRender();
    }

    private static String GetSupportedVersion() {
        return "#version 300 es";
    }

    private static int loadShader(String vss, String fss) {
        String SupportedVersion = GetSupportedVersion();
        vss = SupportedVersion + "\n #line 1\n" + vss;
        fss = SupportedVersion + "\n #line 1\n" + fss;
        int vshader = GLES20.glCreateShader(GLES20.GL_VERTEX_SHADER);
        GLES20.glShaderSource(vshader, vss);
        GLES20.glCompileShader(vshader);
        int[] compiled = new int[1];
        GLES20.glGetShaderiv(vshader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            Log.e("Shader", "Could not compile vshader");
            Log.v("Shader", "Could not compile vshader:" + GLES20.glGetShaderInfoLog(vshader));
            GLES20.glDeleteShader(vshader);
            vshader = 0;
        }

        int fshader = GLES20.glCreateShader(GLES20.GL_FRAGMENT_SHADER);
        GLES20.glShaderSource(fshader, fss);
        GLES20.glCompileShader(fshader);
        GLES20.glGetShaderiv(fshader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            Log.e("Shader", "Could not compile fshader");
            Log.v("Shader", "Could not compile fshader:" + GLES20.glGetShaderInfoLog(fshader));
            GLES20.glDeleteShader(fshader);
            fshader = 0;
        }

        int program = GLES20.glCreateProgram();
        GLES20.glAttachShader(program, vshader);
        GLES20.glAttachShader(program, fshader);
        GLES20.glLinkProgram(program);
        int[] linked = new int[1];
        GLES20.glGetProgramiv(program, GLES20.GL_LINK_STATUS, linked, 0);
        Log.i("MainRenderer", "IRIS_26553_PREVIEW_DIAG_PROGRAM_LINK status=" + linked[0]
                + " log=" + GLES20.glGetProgramInfoLog(program));

        return program;
    }

    public void setMirror(boolean mirrorPreview) {
        mMirrorPreview = mirrorPreview;
    }

    public void setSoftwareZoom(float zoom) {
        mSoftwareZoom = Math.max(1.0f, zoom);
    }

    public void setOrientation(int or) {
        float[] next = new float[16];
        android.opengl.Matrix.setRotateM(next, 0, or, 0f, 0f, 1f);
        mTexRotateMatrix = next;
    }

    public void setTransform(@NonNull android.graphics.Matrix matrix) {
        Log.d("MainRenderer", "setTransform: " + matrix + " " + Arrays.toString(mTexRotateMatrix));
        float[] next = new float[16];
        float[] nine = new float[9];
        matrix.getValues(nine);
        // Android Matrix is 3x3; GL uniform is 4x4. Keep a complete
        // immutable column-major 4x4 rather than overwriting a 16-element GL array.
        next[0] = nine[0]; next[1] = nine[3];
        next[4] = nine[1]; next[5] = nine[4];
        next[10] = 1.0f; next[12] = nine[2]; next[13] = nine[5]; next[15] = 1.0f;
        mTexRotateMatrix = next;
    }

    RectF mLastImageRect = new RectF();
    RectF inputRect = new RectF();

    public void scale(int in_width, int in_height, int out_width, int out_height, int rotation) {
        int difw = out_width - in_width;
        int difh = out_height - in_height;

        inputRect.left = (int) (difw / 2);
        inputRect.top = (int) (difh / 2);
        inputRect.right = in_width;
        inputRect.bottom = in_height;
        if (mLastImageRect != inputRect) {
            GLES20.glViewport((int) inputRect.left, (int) inputRect.top, (int) inputRect.width(), (int) inputRect.height());

            mLastImageRect.set(inputRect);
        }

    }
}