package com.particlesdevs.photoncamera.util;


import java.util.concurrent.atomic.AtomicLong;

/**
 * Compact multi-shot Motion timeline.
 *
 * Each event is written both through Photon's normal persistent logger and
 * to an independent rotating file so verbose processing output cannot evict
 * later Motion shots.
 */
public final class MotionTrace {
    private static final String TAG = "MotionTrace";
    private static final AtomicLong SHOT_SEQUENCE =
            new AtomicLong(0L);

    private MotionTrace() {}

    public static long beginShot(
            String cameraId,
            int requestedFrames,
            int bufferedFrames,
            boolean manualLadderActive,
            long generation) {

        long shot = SHOT_SEQUENCE.incrementAndGet();

        String message = "SHOT_BEGIN"
                + " shot=" + shot
                + " camera=" + cameraId
                + " requestedFrames=" + requestedFrames
                + " bufferedFrames=" + bufferedFrames
                + " manualLadder=" + manualLadderActive
                + " generation=" + generation
                + " thread=" + Thread.currentThread().getName();

        writeInfo(message);
        return shot;
    }

    public static void state(
            long shot,
            String stage,
            String details) {

        String message = "SHOT_STATE"
                + " shot=" + shot
                + " stage=" + stage
                + " details=" + sanitize(details)
                + " thread=" + Thread.currentThread().getName();

        writeInfo(message);
    }

    public static void finish(
            long shot,
            String result,
            String details) {

        String message = "SHOT_END"
                + " shot=" + shot
                + " result=" + result
                + " details=" + sanitize(details)
                + " thread=" + Thread.currentThread().getName();

        writeInfo(message);
    }

    public static void error(
            long shot,
            String stage,
            Exception throwable) {

        Exception safe = throwable == null
                ? new RuntimeException("null throwable")
                : throwable;

        String message = "SHOT_ERROR"
                + " shot=" + shot
                + " stage=" + stage
                + " exception=" + sanitize(
                        safe.getClass().getName()
                                + ": "
                                + String.valueOf(
                                        safe.getMessage()))
                + " thread=" + Thread.currentThread().getName();

        Log.e(TAG, message
                + "\n"
                + Log.getStackTraceString(safe));
        Log.flushNow();

        Log.writeMotionTrace(
                "E",
                message
                        + " stack="
                        + sanitize(
                                Log.getStackTraceString(safe)));
        Log.flushMotionNow();
    }

    public static void processingState(String stage, String details) {
        String message = "PIPELINE_STATE"
                + " stage=" + sanitize(stage)
                + " details=" + sanitize(details)
                + " thread=" + Thread.currentThread().getName();
        writeInfo(message);
    }

    private static void writeInfo(String message) {
        Log.d(TAG, message);
        Log.writeMotionTrace("I", message);
        Log.flushNow();
        Log.flushMotionNow();
    }

    private static String sanitize(String value) {
        if (value == null) {
            return "null";
        }

        return value.replace('\n', ' ')
                .replace('\r', ' ')
                .replace('\t', ' ');
    }
}
