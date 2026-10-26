package com.particlesdevs.photoncamera.spektra;

import android.content.Context;

import com.particlesdevs.photoncamera.util.Log;
import com.unspektrawesome.vulkan.VulkanRenderer;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Non-blocking warmup for restored working 26692 UnspektrAwesome 1.1.2 native. */
public final class SpektraPipelineWarmup {
    private static final String TAG = "SpektraPipelineWarmup";
    private static final AtomicBoolean STARTED = new AtomicBoolean(false);
    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(2, task -> {
        Thread thread = new Thread(task, "UnspektrawesomeShaderWarmup");
        thread.setDaemon(true);
        return thread;
    });

    private SpektraPipelineWarmup() {}

    public static void start(Context context) {
        // The matching verified 26692 Vulkan binary is arm64-v8a.
        if (!android.os.Process.is64Bit()) return;
        if (!STARTED.compareAndSet(false, true)) return;
        Context app = context.getApplicationContext();
        // IRIS_26696_STANDALONE_ASYNC_WARMUP_OWNER
        // Preview and export preparation are independent, strictly opportunistic. Neither camera
        // entry, shutter, mode switching nor teardown ever waits for these tasks.
        EXECUTOR.execute(() -> runTrack(app, true, "preview"));
        EXECUTOR.execute(() -> runTrack(app, false, "export"));
    }

    private static void runTrack(Context context, boolean preview, String name) {
        long started = android.os.SystemClock.elapsedRealtime();
        int completed = 0;
        try (VulkanRenderer renderer = new VulkanRenderer(context)) {
            // 1.1.2 accepts a single step argument. Its API does not
            // expose the 1.2.5 step/part hierarchy; never invoke that ABI.
            // Warmup is opportunistic and cannot gate the camera or shutter.
            if (!renderer.warmUp(preview, 0)) {
                Log.w(TAG, "IRIS_26881_SPEKTRA_112_WARMUP track=" + name
                        + " completed=false step=0 diagnostic=" + renderer.diagnostics());
                return;
            }
            completed = 1;
            Log.i(TAG, "IRIS_26696_SPEKTRA_WARMUP track=" + name + " completed=true steps="
                    + completed + " elapsedMs="
                    + (android.os.SystemClock.elapsedRealtime() - started));
        } catch (Throwable error) {
            // Warmup is opportunistic exactly as a startup preparation path should be: failure can
            // never suppress the real camera or become a second runtime owner.
            Log.e(TAG, "IRIS_26696_SPEKTRA_WARMUP_FAILED track=" + name
                    + " steps=" + completed, error);
        }
    }
}
