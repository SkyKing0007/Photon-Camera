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
        GLES20.glUniformMatrix4fv(uTexRotateMatrix, 1, false, mTexRotateMatrix, 0);
        GLES20.glUniform1i(enablePeak, PhotonCamera.getSettings().focusPeak);
        GLES20.glUniform1i(mirror, mMirrorPreview ? 1 : 0);
        GLES20.glUniform1f(irisSoftwareZoom, mSoftwareZoom);
        /* IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION
         * 26661 brightened the preview from the newly requested protection EV before Camera2 had
         * actually delivered a frame at that exposure, producing the measured startup flash and
         * oscillation. Bind compensation to the exact SurfaceTexture sensor timestamp instead.
         */
        float iris26662ProtectionEv = 0.0f;
        CaptureController iris26662Controller = PhotonCamera.getCaptureController();
        if (iris26662Controller != null && iris26553FrameTimestamp > 0L) {
            iris26662ProtectionEv =
                    iris26662Controller.getMotion26662ReferencePreviewProtectionEv(
                            iris26553FrameTimestamp);
        }
        float iris26662PreviewGain = (float) Math.pow(2.0, iris26662ProtectionEv);
        GLES20.glUniform1f(iris26662ReferencePreviewGain, iris26662PreviewGain);

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
        GLES20.glVertexAttribPointer(vPosition, 2, GLES20.GL_FLOAT, false, 4 * 2, pVertex);
        GLES20.glVertexAttribPointer(vTexCoord, 2, GLES20.GL_FLOAT, false, 4 * 2, pTexCoord);
        GLES20.glEnableVertexAttribArray(vPosition);
        GLES20.glEnableVertexAttribArray(vTexCoord);
        GLES20.glUniform2f(GLES20.glGetUniformLocation(hProgram, "resolution"), mView.getWidth(), mView.getHeight());
        mGLInit = true;
        mView.fireOnSurfaceTextureAvailable(mSTexture, 0, 0);
    }

    public void onSurfaceChanged(GL10 unused, int width, int height) {
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