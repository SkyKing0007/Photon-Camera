package com.particlesdevs.photoncamera.processing;

import com.particlesdevs.photoncamera.control.GyroBurst;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

public final class MotionMetrics {
    private static volatile boolean active;
    private static volatile int candidateFrames = 1;
    private static volatile int retainedFrames = 1;
    private static volatile double accumulatedFrameConfidence = 1.0;
    private static volatile double cameraMotionConfidence = 1.0;
    private static final AtomicInteger measuredFrames = new AtomicInteger(1);

    /* IRIS_26383_REGIONAL_TEMPORAL_SUPPORT */
    private static volatile float[] localSupportGrid = null;
    private static volatile int localSupportWidth = 0;
    private static volatile int localSupportHeight = 0;

    private MotionMetrics() {}

    public static synchronized void begin(int candidates, int retained, List<GyroBurst> gyro) {
        active = true;
        candidateFrames = Math.max(1, candidates);
        retainedFrames = Math.max(1, retained);
        cameraMotionConfidence = estimateCameraMotionConfidence(gyro);
        accumulatedFrameConfidence = 1.0;
        measuredFrames.set(1);
        localSupportGrid = null;
        localSupportWidth = 0;
        localSupportHeight = 0;
    }

    private static double estimateCameraMotionConfidence(List<GyroBurst> gyro) {
        if (gyro == null || gyro.isEmpty()) return 1.0;
        double sum = 0.0;
        int count = 0;
        for (Object item : gyro) {
            Double magnitude = readMotionMagnitude(item);
            if (magnitude != null && Double.isFinite(magnitude)) {
                sum += Math.max(0.0, magnitude);
                count++;
            }
        }
        if (count == 0) return 1.0;
        double average = sum / count;
        return Math.max(0.05, Math.min(1.0, 1.0 / (1.0 + average / 120.0)));
    }

    private static Double readMotionMagnitude(Object item) {
        if (item == null) return null;
        String[] names = {
                "shakiness", "movement", "motion", "integrated",
                "mShakiness", "mMovement", "mMotion"
        };
        for (String name : names) {
            try {
                Field field = item.getClass().getField(name);
                Object value = field.get(item);
                if (value instanceof Number) return ((Number) value).doubleValue();
            } catch (Exception ignored) {}
            try {
                Field field = item.getClass().getDeclaredField(name);
                field.setAccessible(true);
                Object value = field.get(item);
                if (value instanceof Number) return ((Number) value).doubleValue();
            } catch (Exception ignored) {}
            try {
                Method method = item.getClass().getMethod(
                        "get" + Character.toUpperCase(name.charAt(0)) + name.substring(1)
                );
                Object value = method.invoke(item);
                if (value instanceof Number) return ((Number) value).doubleValue();
            } catch (Exception ignored) {}
        }
        return null;
    }

    public static synchronized void addFrameConfidence(double confidence) {
        if (!active) return;
        accumulatedFrameConfidence += Math.max(0.0, Math.min(1.0, confidence));
        measuredFrames.incrementAndGet();
    }

    public static synchronized float effectiveFrames() {
        if (!active) return retainedFrames;
        return (float)Math.max(1.0, Math.min(retainedFrames, accumulatedFrameConfidence));
    }

    public static synchronized float effectiveStackRatio() {
        return Math.max(1.0f / retainedFrames, Math.min(1.0f, effectiveFrames() / retainedFrames));
    }

    public static double cameraMotionConfidence() {
        return cameraMotionConfidence;
    }

    public static int candidateFrames() {
        return candidateFrames;
    }

    public static int retainedFrames() {
        return retainedFrames;
    }

    public static boolean isActive() {
        return active;
    }

    public static synchronized void setLocalSupportGrid(
            float[] grid, int width, int height) {
        if (!active || grid == null || width <= 0 || height <= 0
                || grid.length < width * height) {
            localSupportGrid = null;
            localSupportWidth = 0;
            localSupportHeight = 0;
            return;
        }
        localSupportGrid = grid.clone();
        localSupportWidth = width;
        localSupportHeight = height;
    }

    public static boolean hasLocalSupportGrid() {
        return active && localSupportGrid != null
                && localSupportWidth > 0 && localSupportHeight > 0;
    }

    public static synchronized float[] localSupportGridCopy() {
        return localSupportGrid == null ? null : localSupportGrid.clone();
    }

    public static int localSupportWidth() { return localSupportWidth; }
    public static int localSupportHeight() { return localSupportHeight; }

    /*
     * IRIS_26413_MOTION_V2_TRUTHFUL_LOCAL_SUPPORT
     *
     * V2 publishes measured temporal support from its own reconstruction.
     * The scalar is the spatial mean effective sample count. The coarse grid
     * preserves regional support for later confidence-aware denoise/tone use.
     */
    public static synchronized void publishV2Support(
            float effectiveSupport,
            float[] supportGrid,
            int supportWidth,
            int supportHeight) {
        accumulatedFrameConfidence = Math.max(
                1.0,
                Math.min(retainedFrames, effectiveSupport));
        measuredFrames.set(retainedFrames);

        if (supportGrid != null
                && supportWidth > 0
                && supportHeight > 0
                && supportGrid.length == supportWidth * supportHeight) {
            localSupportGrid = supportGrid.clone();
            localSupportWidth = supportWidth;
            localSupportHeight = supportHeight;
        } else {
            localSupportGrid = null;
            localSupportWidth = 0;
            localSupportHeight = 0;
        }
    }

    public static synchronized void end() {
        active = false;
        localSupportGrid = null;
        localSupportWidth = 0;
        localSupportHeight = 0;
    }
}
