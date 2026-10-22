package com.hinnka.mycamera.processor;

import android.content.Context;
import android.content.res.AssetManager;
import android.opengl.GLES30;
import java.nio.ByteBuffer;

/**
 * IRIS_26864_NATIVE_B_RAW_BURST_TO_REAL_RAWR_VULKAN_AMAZE.
 *
 * Additive B-only entry. The established 26863 packed-GL-to-AMaZE JNI owner
 * remains unchanged. Called synchronously on the thread with the current
 * EGL context. Caller retains every SafeImage/raw ByteBuffer until return.
 * On any GPU, clipping, or file-publication error the caller must discard
 * this B image rather than run an A/Camera2/legacy reconstruction fallback.
 */
public final class GlesIris26864NativeRawr {
    private GlesIris26864NativeRawr() { }
    static { System.loadLibrary("iris26856amaze"); }

    public static int createOwnedClipGlTexture(int width, int height) {
        if (width < 32 || height < 32 || width > 16384 || height > 16384)
            throw new IllegalArgumentException("26864 invalid GL sensor-clip dimensions");
        int[] handle = new int[1];
        int[] previous = new int[1];
        GLES30.glGetIntegerv(GLES30.GL_TEXTURE_BINDING_2D, previous, 0);
        GLES30.glGenTextures(1, handle, 0);
        if (handle[0] == 0)
            throw new IllegalStateException("26864 sensor clip GL allocation failed");
        try {
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, handle[0]);
            // The inherited Iris 26836/26837 final clip consumer reads R16F,
            // not RGBA16F. Vulkan's temporary AHB is RGBA16F; its red
            // original-sensor bit is blitted to this exact GL_R16F carrier.
            GLES30.glTexStorage2D(GLES30.GL_TEXTURE_2D, 1, GLES30.GL_R16F, width, height);
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST);
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST);
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE);
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE);
            if (GLES30.glGetError() != GLES30.GL_NO_ERROR)
                throw new IllegalStateException("26864 sensor-clip GL texture format unsupported");
            return handle[0];
        } catch (RuntimeException failure) {
            GLES30.glDeleteTextures(1, handle, 0);
            throw failure;
        } finally {
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, previous[0]);
        }
    }

    public static void run(Context app, GlesIris26864FrozenRawrIngress frozen,
            float[] wb, float[] physicalLensShading,
            int lscWidth, int lscHeight,
            int physicalBayer, int cropX, int cropY,
            int fullSensorWidth, int fullSensorHeight,
            int referenceNormalIndex, boolean wronskiTrue2x,
            int outputRgbTexture, int outputClipTexture,
            long physicalCameraIdentity) {
        if (app == null || frozen == null || wb == null || wb.length != 3
                || physicalBayer < 0 || physicalBayer > 3
                || referenceNormalIndex < 0 || referenceNormalIndex >= frozen.getBuffers().length
                || fullSensorWidth < frozen.getWidth() || fullSensorHeight < frozen.getHeight()
                || cropX < 0 || cropY < 0 ||
                   cropX > fullSensorWidth - frozen.getWidth() ||
                   cropY > fullSensorHeight - frozen.getHeight()
                || ((lscWidth == 0) != (lscHeight == 0))
                || (lscWidth != 0 && (lscWidth < 2 || lscHeight < 2))
                || (long)lscWidth * lscHeight * 4L !=
                    (physicalLensShading == null ? 0L : physicalLensShading.length)
                || outputRgbTexture <= 0 || outputClipTexture <= 0 ||
                   outputRgbTexture == outputClipTexture || physicalCameraIdentity == 0L) {
            throw new IllegalArgumentException("26864 B native RAW/clip/LSC/AMaZE contract failed");
        }
        frozen.assertUsable();
        // The caller may not close, free, or reuse a NORMAL SafeImage until
        // the GPU upload, RAWR stages, AMaZE and GL clip export all complete.
        nativeExecuteGpu(app.getAssets(), frozen.getBuffers(), frozen.getStridesBytes(),
                frozen.getExposures(), frozen.getTimestampsNs(),
                frozen.getBlackByFrameByPhase(), frozen.getSensorWhiteByFrame(),
                wb, physicalLensShading, lscWidth, lscHeight,
                frozen.getWidth(), frozen.getHeight(), physicalBayer,
                cropX, cropY, fullSensorWidth, fullSensorHeight,
                referenceNormalIndex, wronskiTrue2x,
                outputRgbTexture, outputClipTexture, physicalCameraIdentity);
    }

    private static native void nativeExecuteGpu(AssetManager assets,
            ByteBuffer[] normalRaw16, int[] strides, float[] exposures,
            long[] timestamps, float[] phaseBlacks, float[] sensorWhites,
            float[] wb, float[] physicalLsc, int lscW, int lscH,
            int width, int height, int physicalBayer, int cropX, int cropY,
            int fullWidth, int fullHeight, int referenceIndex,
            boolean true2x, int rgbTexture, int clipTexture,
            long physicalLensIdentity);
}
