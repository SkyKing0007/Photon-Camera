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
        /* IRIS_26726_EXPLICIT_LINEAR_RGB_CARRIER_CONTRACT
         * Cross-context image transport format is explicit so an RGBA16F producer can never
         * be reinterpreted by an RGBA32F consumer (the exact 26699 black-image failure class).
         */
        public static final int LINEAR_RGB_CARRIER_NONE = 0;
        public static final int LINEAR_RGB_CARRIER_RGBA16F = 1;
        public static final int LINEAR_RGB_CARRIER_RGBA32F = 2;

        public final ByteBuffer raw;
        public final long referenceTimestamp;
        public final int inputFrames;
        public final float effectiveSupport;
        /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_BRIDGE
         * One exact float32 state per packed CFA observation: 0=NORMAL_MEASURED,
         * 1=CENSORED_UNKNOWN_CHROMA, 2=SHORT_VALIDATED.
         */
        public final ByteBuffer highlightProvenance;
        /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
        public final ByteBuffer stackedDngRaw16;
        public final int dngStackFrames;
        /* IRIS_26522_NORMALIZED16_DNG_METADATA */
        public final double[] dngNoiseProfile;
        public final float dngSupportMin;
        public final float dngSupportP01;
        public final float dngSupportP10;
        public final float dngSupportMedian;
        public final float dngSupportMean;
        public final float dngSupportMax;
        public final float dngNoiseEquivalentSupport;
        /* IRIS_26532_STREAMED_2X_OUTPUTS
         * JPEG uses a compact unsigned-Q8 log-luma detail stream (~1 byte/output pixel).
         * A full RGB16 LinearRaw stream is created only when DNG is requested. Neither path
         * materializes a 50 MP RGB Bitmap/FLOAT32/whole-image direct buffer.
         */
        public final String superResDetailPath;
        public final int superResDetailWidth;
        public final int superResDetailHeight;
        public final String superResLinearRawPath;
        public final int superResLinearRawWidth;
        public final int superResLinearRawHeight;
        /* IRIS_26564_TRUE_2X_CFA_RECONSTRUCTION */
        public final String true2xLinearRgbPath;
        public final String true2xRenderRgbPath;
        public final int true2xWidth;
        public final int true2xHeight;
        public final String true2xBackend;
        public final float true2xPhaseSupportMean;
        public final float true2xPhaseSupportP10;
        public final long true2xReconstructionMs;
        /* IRIS_26545_RECONSTRUCTION_RESULT_CONTRACT */
        public boolean sabreSelected = false;
        public int linearRgbCarrierFormat = LINEAR_RGB_CARRIER_NONE;

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport,
                    highlightProvenance, null, 0);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport, highlightProvenance,
                    stackedDngRaw16, dngStackFrames, null,
                    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
                    null, 0, 0, null, 0, 0);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames,
                double[] dngNoiseProfile,
                float dngSupportMin, float dngSupportP01, float dngSupportP10,
                float dngSupportMedian, float dngSupportMean, float dngSupportMax,
                float dngNoiseEquivalentSupport) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport, highlightProvenance,
                    stackedDngRaw16, dngStackFrames, dngNoiseProfile,
                    dngSupportMin, dngSupportP01, dngSupportP10, dngSupportMedian,
                    dngSupportMean, dngSupportMax, dngNoiseEquivalentSupport,
                    null, 0, 0, null, 0, 0);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames,
                double[] dngNoiseProfile,
                float dngSupportMin, float dngSupportP01, float dngSupportP10,
                float dngSupportMedian, float dngSupportMean, float dngSupportMax,
                float dngNoiseEquivalentSupport, String superResDetailPath,
                int superResDetailWidth, int superResDetailHeight,
                String superResLinearRawPath, int superResLinearRawWidth,
                int superResLinearRawHeight) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport, highlightProvenance,
                    stackedDngRaw16, dngStackFrames, dngNoiseProfile,
                    dngSupportMin, dngSupportP01, dngSupportP10, dngSupportMedian,
                    dngSupportMean, dngSupportMax, dngNoiseEquivalentSupport,
                    superResDetailPath, superResDetailWidth, superResDetailHeight,
                    superResLinearRawPath, superResLinearRawWidth, superResLinearRawHeight,
                    null, null, 0, 0, null, 1.0f, 1.0f, 0L);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames,
                double[] dngNoiseProfile,
                float dngSupportMin, float dngSupportP01, float dngSupportP10,
                float dngSupportMedian, float dngSupportMean, float dngSupportMax,
                float dngNoiseEquivalentSupport, String superResDetailPath,
                int superResDetailWidth, int superResDetailHeight,
                String superResLinearRawPath, int superResLinearRawWidth,
                int superResLinearRawHeight, String true2xLinearRgbPath,
                String true2xRenderRgbPath, int true2xWidth, int true2xHeight, String true2xBackend,
                float true2xPhaseSupportMean, float true2xPhaseSupportP10,
                long true2xReconstructionMs) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
            this.stackedDngRaw16 = stackedDngRaw16;
            this.dngStackFrames = Math.max(0, dngStackFrames);
            this.dngNoiseProfile = dngNoiseProfile == null ? null : dngNoiseProfile.clone();
            this.dngSupportMin = dngSupportMin;
            this.dngSupportP01 = dngSupportP01;
            this.dngSupportP10 = dngSupportP10;
            this.dngSupportMedian = dngSupportMedian;
            this.dngSupportMean = dngSupportMean;
            this.dngSupportMax = dngSupportMax;
            this.dngNoiseEquivalentSupport = dngNoiseEquivalentSupport;
            this.superResDetailPath = superResDetailPath;
            this.superResDetailWidth = Math.max(0, superResDetailWidth);
            this.superResDetailHeight = Math.max(0, superResDetailHeight);
            this.superResLinearRawPath = superResLinearRawPath;
            this.superResLinearRawWidth = Math.max(0, superResLinearRawWidth);
            this.superResLinearRawHeight = Math.max(0, superResLinearRawHeight);
            this.true2xLinearRgbPath = true2xLinearRgbPath;
            this.true2xRenderRgbPath = true2xRenderRgbPath;
            this.true2xWidth = Math.max(0, true2xWidth);
            this.true2xHeight = Math.max(0, true2xHeight);
            this.true2xBackend = true2xBackend;
            this.true2xPhaseSupportMean = true2xPhaseSupportMean;
            this.true2xPhaseSupportP10 = true2xPhaseSupportP10;
            this.true2xReconstructionMs = Math.max(0L, true2xReconstructionMs);
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
    /* IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN
     * The one post-Wronski display multiplier remains the sole large-scale
     * brightness authority. The selected reference CaptureResult supplies the
     * frozen HAL/capture scene key. Sparse RAW percentiles are residual evidence
     * only and are bounded to +/-0.25 EV around that capture-state anchor.
     *
     * This deliberately prevents two near-identical compositions from producing
     * multi-EV brightness swings merely because a window occupies more pixels.
     * Nothing here feeds Camera2 or live AE.
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
        final int[] histogram = new int[bins];
        long total = 0L;
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
                int phase = ((y & 1) << 1) | (x & 1);
                float black = parameters.blackLevel[phase];
                float span = Math.max(1.0f, white - black);
                float measured = Math.max(
                        0.0f,
                        Math.min(1.0f, (rawValue - black) / span));
                int bin = Math.min(
                        bins - 1,
                        Math.max(0, (int)(measured * (bins - 1))));
                histogram[bin]++;
                total++;
            }
        }
        if (total < 64L) return 1.0f;

        float p50 = quantile(histogram, total, 0.50f);
        float p90 = quantile(histogram, total, 0.90f);
        float p99 = quantile(histogram, total, 0.99f);

        double exposureSeconds = parameters.exposureTime;
        float iso = Math.max(1.0f, (float) parameters.iso);
        float aperture = parameters.aperture;
        boolean frozenCaptureValid = Double.isFinite(exposureSeconds)
                && exposureSeconds > 0.0 && exposureSeconds < 30.0
                && Float.isFinite(iso) && iso > 0.0f
                && Float.isFinite(aperture) && aperture > 0.1f;
        float ev100 = 4.0f;
        if (frozenCaptureValid) {
            double ev =
                    Math.log((aperture * aperture) / exposureSeconds) / Math.log(2.0)
                    - Math.log(iso / 100.0) / Math.log(2.0);
            if (Double.isFinite(ev)) {
                ev100 = (float) ev;
            } else {
                frozenCaptureValid = false;
            }
        }

        float anchorScene = frozenCaptureValid
                ? smoothstep(2.0f, 5.0f, ev100)
                : 0.65f;
        float captureAnchorGain = mix(1.0f, 2.15f, anchorScene);

        float darknessSceneKey = frozenCaptureValid
                ? smoothstep(1.5f, 5.5f, ev100)
                : 0.65f;
        float targetP50 = mix(0.0020f, 0.050f, darknessSceneKey);
        float targetP90 = mix(0.0120f, 0.180f, darknessSceneKey);
        float gain50 = targetP50 / Math.max(p50, 1.0e-5f);
        float gain90 = targetP90 / Math.max(p90, 1.0e-5f);
        float histogramGain = (float)Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));
        histogramGain = Math.max(1.0f, Math.min(16.0f, histogramGain));

        float rawResidualRatio =
                histogramGain / Math.max(captureAnchorGain, 1.0e-6f);
        float residualEv = (float)(
                Math.log(Math.max(rawResidualRatio, 1.0e-6f)) / Math.log(2.0));
        residualEv = Math.max(-0.25f, Math.min(0.25f, residualEv));

        float predictedNearClip = fractionAbove(
                histogram,
                total,
                Math.min(
                        1.0f,
                        0.985f / Math.max(captureAnchorGain, 1.0f)));
        float occupancyPressure = smoothstep(0.015f, 0.18f, predictedNearClip);
        if (residualEv > 0.0f) {
            residualEv *= 1.0f - 0.70f * occupancyPressure;
        }

        float residualGain = (float)Math.pow(2.0, residualEv);
        float gain = captureAnchorGain * residualGain;
        gain = Math.max(1.0f, Math.min(4.0f, gain));
        if (!Float.isFinite(gain)) gain = 1.0f;
        if (gain < 1.02f) gain = 1.0f;

        Log.d(TAG, "IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN"
                + " rawP50=" + p50
                + " rawP90=" + p90
                + " rawP99=" + p99
                + " aperture=" + aperture
                + " exposureSeconds=" + exposureSeconds
                + " iso=" + iso
                + " frozenCaptureValid=" + frozenCaptureValid
                + " ev100=" + ev100
                + " captureAnchorGain=" + captureAnchorGain
                + " histogramGain=" + histogramGain
                + " residualEvBound=0.25"
                + " residualEv=" + residualEv
                + " predictedNearClip=" + predictedNearClip
                + " occupancyPressure=" + occupancyPressure
                + " displayGain=" + gain
                + " referenceExposureEnergyDiagnosticOnly="
                    + referenceExposureEnergy
                + " globalExposureOwner=true"
                + " liveAeFeedback=false"
                + " previewKeyImplemented=false");
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