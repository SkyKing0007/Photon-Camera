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
    private final float[] mTexRotateMatrix = new float[]{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};

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
        /* Check the active physical-lens B owner on every new preview frame. Never
         * substitute the historic 26679 RAW-row correction or alter HAL AE. */
        CaptureController iris26872Controller = PhotonCamera.getCaptureController();
        boolean iris26872Eligible = iris26872Controller != null
                && iris26872Controller.iris26872BPreviewStripeEligible();
        if (iris26872Eligible != mIris26872LastEligible) {
            mIris26872Stripe.reset();
            mIris26872LastEligible = iris26872Eligible;
        }
        if (iris26872Eligible && iris26553FrameTimestamp > 0L) {
            iris26872Probe(iris26553FrameTimestamp);
        }
        float[] iris26872Stripe = mIris26872Stripe.params();
        GLES20.glUniform4f(mIris26872StripeUniform, iris26872Stripe[0], iris26872Stripe[1],
                iris26872Stripe[2], iris26872Eligible ? iris26872Stripe[3] : 0f);
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
                mIris26663LastConfirmedProtectionEv = Math.max(0.0f, exactEv);
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

    private void iris26872Probe(long timestampNs) {
        if (mIris26872ProbeDisabled || mIris26872ProbeProgram == 0 || mIris26872ProbeFbo == 0)
            return;
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, mIris26872ProbeFbo);
        GLES20.glViewport(0, 0, Iris26872PreviewStripe.WIDTH, Iris26872PreviewStripe.HEIGHT);
        GLES20.glUseProgram(mIris26872ProbeProgram);
        GLES20.glVertexAttribPointer(mIris26872ProbePosition, 2, GLES20.GL_FLOAT, false, 0, pVertex);
        GLES20.glEnableVertexAttribArray(mIris26872ProbePosition);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, hTex[0]);
        GLES20.glUniform1i(mIris26872ProbeSampler, 0);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
        mIris26872ProbeReadback.rewind();
        GLES20.glReadPixels(0, 0, Iris26872PreviewStripe.WIDTH,
                Iris26872PreviewStripe.HEIGHT, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE,
                mIris26872ProbeReadback);
        int error = GLES20.glGetError();
        GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0);
        GLES20.glViewport(0, 0, mIris26872ViewportW, mIris26872ViewportH);
        GLES20.glUseProgram(mIris26553PreviewProgram);
        if (error != GLES20.GL_NO_ERROR) {
            mIris26872ProbeDisabled = true;
            mIris26872Stripe.reset();
            Log.w("MainRenderer", "IRIS_26872_PREVIEW_PROBE_DISABLED error=0x"
                    + Integer.toHexString(error));
        } else {
            if (mIris26872Stripe.consume(mIris26872ProbeReadback, timestampNs)
                    && !mIris26872LoggedFirstValid) {
                mIris26872LoggedFirstValid = true;
                Log.i("MainRenderer", "IRIS_26872_B_PREVIEW_STRIPE first_confident="
                        + "true preview_only=true hal_ae_unchanged=true");
            }
        }
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
        mView.fireOnPreviewFrameAvailable();
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
        android.opengl.Matrix.setRotateM(mTexRotateMatrix, 0, or, 0f, 0f, 1f);
    }

    public void setTransform(@NonNull android.graphics.Matrix matrix) {
        Log.d("MainRenderer", "setTransform: " + matrix + " " + Arrays.toString(mTexRotateMatrix));
        matrix.getValues(mTexRotateMatrix);
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