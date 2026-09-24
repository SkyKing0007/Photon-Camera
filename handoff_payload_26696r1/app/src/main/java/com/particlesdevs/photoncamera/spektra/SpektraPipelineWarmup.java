package com.particlesdevs.photoncamera.spektra;

import android.content.Context;

import com.particlesdevs.photoncamera.util.Log;
import com.unspektrawesome.vulkan.VulkanRenderer;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Background-only Unspektrawesome 1.1.2 preview/export pipeline warmup. */
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
        if (!STARTED.compareAndSet(false, true)) return;
        Context app = context.getApplicationContext();
        // IRIS_26696_STANDALONE_ASYNC_WARMUP_OWNER
        // Exact 1.1.2 prepares preview and export tracks independently at startup. Neither camera
        // entry, shutter, mode switching nor teardown ever waits for these tasks.
        EXECUTOR.execute(() -> runTrack(app, true, "preview"));
        EXECUTOR.execute(() -> runTrack(app, false, "export"));
    }

    private static void runTrack(Context context, boolean preview, String name) {
        long started = android.os.SystemClock.elapsedRealtime();
        int completed = 0;
        try (VulkanRenderer renderer = new VulkanRenderer(context)) {
            for (int step = 0; step <= 9; step++) {
                if (!renderer.warmUp(preview, step)) {
                    Log.w(TAG, "IRIS_26696_SPEKTRA_WARMUP track=" + name
                            + " completed=false step=" + step + " diagnostic=" + renderer.diagnostics());
                    return;
                }
                completed++;
            }
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
