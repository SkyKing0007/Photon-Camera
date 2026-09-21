package com.particlesdevs.photoncamera.spektra;

import android.content.Context;
import android.content.res.AssetManager;
import android.graphics.Bitmap;

import java.io.File;

/** JNI boundary to the pinned public SPEKTRA Vulkan renderer. */
public final class SpektraFilmRenderer implements AutoCloseable {
    static { System.loadLibrary("spektra_iris"); }

    private final Context context;
    private boolean initialized;

    public SpektraFilmRenderer(Context context) {
        this.context = context.getApplicationContext();
    }

    private void ensureInitialized() {
        if (initialized) return;
        File root = context.getDir("spektra_runtime", Context.MODE_PRIVATE);
        AssetManager assets = context.getAssets();
        if (!nativeInitialize(assets, root.getAbsolutePath())) {
            throw new IllegalStateException("Spektra Vulkan initialization failed: " + nativeLastError());
        }
        initialized = true;
    }

    public Bitmap render(SpektraRawProcessor.LinearFrame frame, boolean preview, double timeSeconds) {
        if (frame == null || frame.rgba16f == null) throw new IllegalArgumentException("Spektra linear frame missing");
        ensureInitialized();
        frame.rgba16f.position(0);
        Bitmap bitmap = Bitmap.createBitmap(frame.width, frame.height, Bitmap.Config.ARGB_8888);
        if (!nativeRenderToBitmap(frame.rgba16f, frame.width, frame.height, bitmap, preview, timeSeconds)) {
            bitmap.recycle();
            throw new IllegalStateException("Spektra Vulkan render failed: " + nativeLastError());
        }
        return bitmap;
    }

    @Override public void close() {
        // Renderer is process-shared so preview/still can reuse static film resources. Camera-owner release
        // calls releaseProcessRenderer only when Spektra relinquishes ownership entirely.
    }

    public static void releaseProcessRenderer() { nativeRelease(); }

    private static native boolean nativeInitialize(AssetManager assets, String resourceRoot);
    private static native boolean nativeRenderToBitmap(java.nio.ByteBuffer rgba16f, int width, int height,
            Bitmap bitmap, boolean preview, double timeSeconds);
    private static native String nativeLastError();
    private static native void nativeRelease();
}
