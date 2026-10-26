package com.particlesdevs.photoncamera.spektra;

import android.content.Context;

import com.particlesdevs.photoncamera.util.Log;
import com.unspektrawesome.vulkan.VulkanRenderer;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Background-only Original UnspektrAwesome 1.2.5 native preview/export warmup. */
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
        // No 32-bit 1.2.5 renderer exists in the ORIGINAL release APK.
        if (!android.os.Process.is64Bit()) return;
        if (!STARTED.compareAndSet(false, true)) return;
        Context app = context.getApplicationContext();
        // IRIS_26696_STANDALONE_ASYNC_WARMUP_OWNER
        // Original 1.2.5 prepares preview and export tracks independently at startup. Neither camera
        // entry, shutter, mode switching nor teardown ever waits for these tasks.
        EXECUTOR.execute(() -> runTrack(app, true, "preview"));
        EXECUTOR.execute(() -> runTrack(app, false, "export"));
    }

    private static void runTrack(Context context, boolean preview, String name) {
        long started = android.os.SystemClock.elapsedRealtime();
        int completed = 0;
        try (VulkanRenderer renderer = new VulkanRenderer(context)) {
            final int steps = renderer.warmUpStepCount(preview);
            for (int step = 0; step < steps; step++) {
                final int parts = renderer.warmUpPartCount(preview, step);
                for (int part = 0; part < parts; part++) {
                    if (!renderer.warmUp(preview, step, part)) {
                        Log.w(TAG, "IRIS_26880_SPEKTRA_125_WARMUP track=" + name
                                + " completed=false step=" + step + " part=" + part
                                + " diagnostic=" + renderer.diagnostics());
                        return;
                    }
                    completed++;
                }
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
