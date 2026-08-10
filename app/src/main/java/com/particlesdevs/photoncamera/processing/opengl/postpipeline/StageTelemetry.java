package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.opengl.scripts.GLHistogram;
import com.particlesdevs.photoncamera.util.Log;

/*
 * IRIS_26400_MOTION_STAGE_BRIGHTNESS_TELEMETRY
 *
 * Diagnostic pass-through only.
 *
 * This node never writes pixels, never allocates an output image texture,
 * never changes WorkingTexture ownership, and never changes pipeline math.
 * It computes a sparse GPU histogram of the texture produced by the previous
 * node, reads only the 256-bin histogram buffers, logs compact statistics, and
 * passes the exact same GLTexture object to the next node.
 */
public class StageTelemetry extends Node {
    private static final int HIST_SIZE = 256;
    private static final int SAMPLE_RESIZE = 12;
    private final String stage;

    public StageTelemetry(String stage) {
        super("", "StageTelemetry_" + stage);
        this.stage = stage;
    }

    @Override
    public void Compile() {
    }

    private static float percentile(
            int[] histogram,
            long total,
            double fraction) {
        if (histogram == null || histogram.length == 0 || total <= 0L) {
            return Float.NaN;
        }
        long target = Math.max(1L, (long)Math.ceil(total * fraction));
        long cumulative = 0L;
        for (int i = 0; i < histogram.length; i++) {
            cumulative += histogram[i];
            if (cumulative >= target) {
                return i / (float)(histogram.length - 1);
            }
        }
        return 1.0f;
    }

    @Override
    public void Run() {
        GLTexture source = previousNode == null
                ? null
                : previousNode.WorkingTexture;

        /*
         * Pass through the identical texture object first. Even if telemetry
         * fails, image ownership remains unchanged.
         */
        WorkingTexture = source;

        if (PhotonCamera.getSettings().selectedMode != CameraMode.MOTION
                || source == null) {
            return;
        }

        GLHistogram histogram = null;
        try {
            histogram =
                    new GLHistogram(
                            basePipeline.glint.glProcessing,
                            HIST_SIZE);
            histogram.Rc = true;
            histogram.Gc = true;
            histogram.Bc = true;
            histogram.Ac = false;
            histogram.resize = SAMPLE_RESIZE;

            int[][] channels = histogram.Compute(source);
            int[] combined = new int[HIST_SIZE];

            long total = 0L;
            double weighted = 0.0;
            long floorCount = 0L;
            long darkCount = 0L;
            long nearClipCount = 0L;

            for (int i = 0; i < HIST_SIZE; i++) {
                int c =
                        channels[0][i]
                                + channels[1][i]
                                + channels[2][i];
                combined[i] = c;
                total += c;
                weighted += (double)c * i;

                if (i <= 2) {
                    floorCount += c;
                }
                if (i <= 10) {
                    darkCount += c;
                }
                if (i >= 250) {
                    nearClipCount += c;
                }
            }

            float mean =
                    total > 0L
                            ? (float)(weighted
                                    / (double)total
                                    / (HIST_SIZE - 1.0))
                            : Float.NaN;

            float p01 = percentile(combined, total, 0.01);
            float p10 = percentile(combined, total, 0.10);
            float p50 = percentile(combined, total, 0.50);
            float p90 = percentile(combined, total, 0.90);
            float p95 = percentile(combined, total, 0.95);
            float p99 = percentile(combined, total, 0.99);

            float floorFraction =
                    total > 0L ? floorCount / (float)total : Float.NaN;
            float darkFraction =
                    total > 0L ? darkCount / (float)total : Float.NaN;
            float nearClipFraction =
                    total > 0L ? nearClipCount / (float)total : Float.NaN;

            String message =
                    "IRIS_26400_STAGE_TELEMETRY"
                            + " stage=" + stage
                            + " mean=" + mean
                            + " p01=" + p01
                            + " p10=" + p10
                            + " p50=" + p50
                            + " p90=" + p90
                            + " p95=" + p95
                            + " p99=" + p99
                            + " floorLe1pct=" + floorFraction
                            + " darkLe4pct=" + darkFraction
                            + " nearClipGe98pct=" + nearClipFraction
                            + " sampleResize=" + SAMPLE_RESIZE
                            + " size=" + source.mSize.x + "x" + source.mSize.y
                            + " sameTexturePassThrough=true";

            Log.i("IRIS26400", message);
            try {
                com.particlesdevs.photoncamera.util.MotionTrace
                        .processingState(
                                "STAGE_TELEMETRY_26400",
                                message);
            } catch (Throwable ignored) {
                Log.d("IRIS26400",
                        "MotionTrace unavailable for stage=" + stage);
            }
        } catch (Throwable throwable) {
            Log.e(
                    "IRIS26400",
                    "IRIS_26400_STAGE_TELEMETRY"
                            + " stage=" + stage
                            + " error="
                            + throwable.getClass().getSimpleName()
                            + " sameTexturePassThrough=true");
        } finally {
            if (histogram != null) {
                histogram.close();
            }
            /*
             * Reassert identical pass-through after histogram program switching.
             */
            WorkingTexture = source;
            glProg.closed = true;
        }
    }
}