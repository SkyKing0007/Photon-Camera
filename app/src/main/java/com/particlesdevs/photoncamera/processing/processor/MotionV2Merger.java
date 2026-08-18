package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.ShortBuffer;
import java.util.List;

/**
 * IRIS_26409_MOTION_V2_FOUNDATION
 *
 * Independent Motion V2 RAW owner.
 *
 * Milestone 1 is intentionally reference-only:
 * - the metadata-owned physical RAW is the structural truth;
 * - no auxiliary frame is permitted to alter geometry yet;
 * - later V2 milestones will add aligned residual evidence and a support map;
 * - normalization math is owned here and does not use Iris floor-risk limits.
 */
public final class MotionV2Merger {
    private static final String TAG = "MotionV2Merger";

    public static final class Result {
        public final ByteBuffer raw;
        public final long referenceTimestamp;
        public final int inputFrames;
        public final float effectiveSupport;
        /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_BRIDGE
         * One exact float32 state per packed CFA observation: 0=NORMAL_MEASURED,
         * 1=CENSORED_UNKNOWN_CHROMA, 2=SHORT_VALIDATED.
         */
        public final ByteBuffer highlightProvenance;

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
        }
    }

    private MotionV2Merger() {}

    public static Result referenceFoundation(List<ImageFrame> frames, long referenceTimestamp) {
        if (frames == null || frames.isEmpty()) {
            throw new IllegalStateException("Motion V2 received no RAW frames");
        }

        ImageFrame reference = null;
        for (ImageFrame frame : frames) {
            if (frame != null && frame.timestamp == referenceTimestamp) {
                reference = frame;
                break;
            }
        }

        if (reference == null) {
            throw new IllegalStateException(
                    "Motion V2 owned reference is absent from batch: " + referenceTimestamp);
        }
        if (reference.buffer == null) {
            throw new IllegalStateException("Motion V2 owned reference buffer is null");
        }

        ByteBuffer output = reference.buffer;
        reference.buffer = null;

        for (ImageFrame frame : frames) {
            if (frame != null) frame.close();
        }

        Log.d(TAG, "IRIS_26409_V2_REFERENCE_FOUNDATION"
                + " referenceTimestamp=" + referenceTimestamp
                + " inputFrames=" + frames.size()
                + " effectiveSupport=1.0"
                + " auxiliaryContribution=0"
                + " structuralOwner=reference");

        return new Result(output, referenceTimestamp, frames.size(), 1.0f, null);
    }

    /**
     * Independent V2 display-normalization estimator.
     * IRIS_26490_EXPLICIT_DISPLAY_DOMAIN: the returned scalar must never be used as a RAW
     * white level, sensor clip threshold, Wronski exposure scale, or short-HDR exposure ratio.
     *
     * This samples the owned RAW but never mutates it. Near-black samples remain
     * valid image data; unlike the previous Iris estimator, floor occupancy is
     * not used to suppress gain. Broad p99 highlight headroom remains the limit.
     */
    public static float computeDisplayGain(
            ByteBuffer raw, int width, int height, Parameters parameters,
            double referenceExposureEnergy) {
        if (raw == null || width <= 0 || height <= 0
                || parameters == null || parameters.whiteLevel <= 0
                || parameters.blackLevel == null || parameters.blackLevel.length < 4) {
            return 1.0f;
        }

        final int bins = 2048;
        final int[] hist = new int[bins];
        long samples = 0L;

        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        view.clear();
        ShortBuffer shorts = view.asShortBuffer();

        int sx = Math.max(1, width / 256);
        int sy = Math.max(1, height / 192);
        float white = parameters.whiteLevel;

        for (int y = sy / 2; y < height; y += sy) {
            for (int x = sx / 2; x < width; x += sx) {
                int index = y * width + x;
                if (index < 0 || index >= shorts.limit()) continue;
                int rawValue = Short.toUnsignedInt(shorts.get(index));
                int cfa = ((y & 1) << 1) | (x & 1);
                float black = parameters.blackLevel[cfa];
                float span = Math.max(1.0f, white - black);
                float normalized = (rawValue - black) / span;

                // Histogram clipping is measurement-only; RAW data is untouched.
                float measured = Math.max(0.0f, Math.min(1.0f, normalized));
                int bin = Math.min(bins - 1,
                        Math.max(0, (int)(measured * (bins - 1))));
                hist[bin]++;
                samples++;
            }
        }

        if (samples < 64L) return 1.0f;

        float p50 = quantile(hist, samples, 0.50f);
        float p90 = quantile(hist, samples, 0.90f);
        float p95 = quantile(hist, samples, 0.95f);
        float p99 = quantile(hist, samples, 0.99f);
        float p995 = quantile(hist, samples, 0.995f);

        final float targetP50 = 0.050f;
        final float targetP90 = 0.18f;
        final float eps = 1.0e-6f;

        long bright80 = countAbove(hist, samples, 0.80f);
        long bright90 = countAbove(hist, samples, 0.90f);
        long bright97 = countAbove(hist, samples, 0.97f);
        float bright80Fraction = bright80 / (float)samples;
        float bright90Fraction = bright90 / (float)samples;
        float bright97Fraction = bright97 / (float)samples;

        float gain50 = targetP50 / Math.max(p50, eps);
        float gain90 = targetP90 / Math.max(p90, eps);
        float sceneGain = (float)Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));

        // IRIS_26411_V2_SCENE_BALANCED_NORMALIZATION
        // Highlights constrain gain in proportion to how much of the scene they
        // occupy. A tiny lamp/specular is not allowed to darken the whole frame.
        /* IRIS_26412_V2_PREDICTED_HDR_ALLOCATION
         * Evaluate highlights after the exposure we propose, not in the dark
         * pre-gain RAW domain. There is no 3.4x/2.45x aesthetic cap.
         */
        float candidateGain = Math.max(1.0f, sceneGain);
        float predictedShoulderFraction = fractionAbove(hist, samples, 0.82f / candidateGain);
        float predictedWhiteFraction = fractionAbove(hist, samples, 1.00f / candidateGain);
        float predictedHighFraction = fractionAbove(hist, samples, 1.50f / candidateGain);
        float trueRawClipFraction = fractionAbove(hist, samples, 0.995f);

        float occupancyPressure = clamp01(
                0.45f * smoothstep(0.06f, 0.32f, predictedShoulderFraction)
                        + 0.35f * smoothstep(0.02f, 0.18f, predictedWhiteFraction)
                        + 0.20f * smoothstep(0.005f, 0.08f, predictedHighFraction));
        float trueClipPressure = smoothstep(0.002f, 0.035f, trueRawClipFraction);

        float adaptiveReduction = 1.0f /
                (1.0f + 0.55f * occupancyPressure + 1.35f * trueClipPressure);

        /*
         * IRIS_26492_SINGLE_SCENE_BODY_EXPOSURE_AUTHORITY
         *
         * p50/p90 are the only semantic authority for Motion display exposure.
         * Camera2 exposure energy remains diagnostic metadata only: a bright lamp can
         * make HAL choose a short exposure, but that capture decision must not veto
         * the independently measured room/midtone brightness. Highlight occupancy and
         * true clipping are local-HDR telemetry only and cannot lower this gain.
         */
        float gain = Math.max(1.0f, Math.min(candidateGain, 16.0f));
        if (!Float.isFinite(gain)) gain = 1.0f;
        if (gain < 1.02f) gain = 1.0f;

        Log.d(TAG, "IRIS_26411_V2_SCENE_BALANCED_GAIN"
                + " samples=" + samples
                + " p50=" + p50 + " p90=" + p90
                + " p95=" + p95 + " p99=" + p99 + " p995=" + p995
                + " bright80Fraction=" + bright80Fraction
                + " bright90Fraction=" + bright90Fraction
                + " bright97Fraction=" + bright97Fraction
                + " occupancyPressure=" + occupancyPressure
                + " sceneGain=" + sceneGain
                + " predictedHdrAllocation=true"
                + " candidateGain=" + candidateGain
                + " predictedShoulderFraction=" + predictedShoulderFraction
                + " predictedWhiteFraction=" + predictedWhiteFraction
                + " predictedHighFraction=" + predictedHighFraction
                + " trueRawClipFraction=" + trueRawClipFraction
                + " adaptiveReductionDiagnosticOnly=" + adaptiveReduction
                + " referenceExposureEnergyDiagnosticOnly=" + referenceExposureEnergy
                + " exposureEnergyHasVeto=false"
                + " floorSuppression=false"
                + " midtonesOwnGlobalExposure=true"
                + " highlightsOwnLocalHdr=true"
                + " finalGain=" + gain);
        return gain;
    }

    private static float fractionAbove(int[] hist, long total, float threshold) {
        if (total <= 0L) return 0.0f;
        return countAbove(hist, total,
                Math.max(0.0f, Math.min(1.0f, threshold))) / (float)total;
    }

    private static long countAbove(int[] hist, long total, float threshold) {
        if (total <= 0L) return 0L;
        int start = Math.max(0, Math.min(hist.length - 1,
                (int)Math.floor(threshold * (hist.length - 1))));
        long count = 0L;
        for (int i = start; i < hist.length; i++) count += hist[i];
        return count;
    }

    private static float clamp01(float x) {
        return Math.max(0.0f, Math.min(1.0f, x));
    }

    private static float smoothstep(float a, float b, float x) {
        float t = clamp01((x - a) / Math.max(1.0e-6f, b - a));
        return t * t * (3.0f - 2.0f * t);
    }

    private static float mix(float a, float b, float t) {
        return a + (b - a) * clamp01(t);
    }

    private static float quantile(int[] hist, long total, float q) {
        long target = Math.max(1L, (long)Math.ceil(total * q));
        long sum = 0L;
        for (int i = 0; i < hist.length; i++) {
            sum += hist[i];
            if (sum >= target) return i / (float)(hist.length - 1);
        }
        return 1.0f;
    }
}