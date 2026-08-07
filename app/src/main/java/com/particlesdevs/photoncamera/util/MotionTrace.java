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

    // IRIS_26360_SAFE_CPU_OBSERVABILITY
    private static volatile long currentShot = 0L;
    private static volatile int expectedFrames = 0;
    private static volatile int metadataRecords = 0;
    private static volatile int temporalRecords = 0;
    private static volatile int exposureFusionRecords = 0;
    private static volatile int autoExposureRecords = 0;
    private static volatile int adaptiveHdrRecords = 0;

    private MotionTrace() {}

    public static long currentShot() {
        return currentShot;
    }

    private static synchronized void countStage(String stage) {
        if (stage == null) return;
        if ("FRAME_META".equals(stage)) metadataRecords++;
        else if ("TEMPORAL_DETAIL".equals(stage)) temporalRecords++;
        else if ("EXPOSURE_FUSION".equals(stage)) exposureFusionRecords++;
        else if ("AUTO_EXPOSURE_PRE_REINHARD".equals(stage)) autoExposureRecords++;
        else if ("ADAPTIVE_HDR".equals(stage)) adaptiveHdrRecords++;
    }

    public static long beginShot(
            String cameraId,
            int requestedFrames,
            int bufferedFrames,
            boolean manualLadderActive,
            long generation) {

        long shot = SHOT_SEQUENCE.incrementAndGet();
        currentShot = shot;
        expectedFrames = Math.max(0, requestedFrames);
        metadataRecords = 0;
        temporalRecords = 0;
        exposureFusionRecords = 0;
        autoExposureRecords = 0;
        adaptiveHdrRecords = 0;

        String message = "MOTION_TRACE_BEGIN"
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

        countStage(stage);
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

        boolean complete =
                metadataRecords > 0
                        && temporalRecords > 0
                        && exposureFusionRecords > 0
                        && autoExposureRecords > 0
                        && adaptiveHdrRecords > 0;

        String message = (complete
                ? "MOTION_TRACE_COMPLETE"
                : "MOTION_TRACE_INCOMPLETE")
                + " shot=" + shot
                + " result=" + result
                + " expectedFrames=" + expectedFrames
                + " metadataRecords=" + metadataRecords
                + " temporalRecords=" + temporalRecords
                + " exposureFusionRecords=" + exposureFusionRecords
                + " autoExposureRecords=" + autoExposureRecords
                + " adaptiveHdrRecords=" + adaptiveHdrRecords
                + " details=" + sanitize(details)
                + " thread=" + Thread.currentThread().getName();

        writeInfo(message);
        currentShot = 0L;
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
        countStage(stage);
        String message = "PIPELINE_STATE"
                + " shot=" + currentShot
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
