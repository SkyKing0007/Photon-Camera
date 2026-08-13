package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.MotionMetrics;
import com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing;
import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLOneScript;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.render.NoiseModeler;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26413_MOTION_V2_REFERENCE_PRESERVING_CFA
 * IRIS_26429_SHARED_GUIDE_ROBUSTNESS_REFERENCE_STRUCTURE
 *
 * Native-resolution deterministic same-exposure burst reconstruction.
 *
 * Invariant:
 *   output = currentReferenceEstimate + trusted auxiliary evidence
 * and local confidence -> 0 leaves the reference estimate unchanged.
 *
 * MotionV2Alignment owns the fractional displacement field.
 * Legacy PyramidAlignment/PyramidMerging/merge0/merge11 are not used by V2.
 */
public final class MotionV2CfaReconstruction extends GLOneScript {
    private static final String TAG = "MotionV2CfaRecon";

    private final ArrayList<ImageFrame> images;
    private final long referenceTimestamp;
    private Parameters parameters;
    private GLProg glProg;

    private ByteBuffer output;
    private float effectiveSupport = 1.0f;
    private float supportP10 = 1.0f;
    private float supportP50 = 1.0f;
    private float supportP90 = 1.0f;

    /*
     * IRIS_26440_V2_DIAGNOSTIC_ONLY_LOCAL_OWNERSHIP
     * Diagnostics only. These values never feed reconstruction/image math.
     */
    private static final int IRIS26440_GRID_W = 12;
    private static final int IRIS26440_GRID_H = 8;

    private MotionV2CfaReconstruction(
            Point size,
            ArrayList<ImageFrame> orderedImages,
            long referenceTimestamp,
            Parameters parameters) {
        super(
                size,
                new GLCoreBlockProcessing(
                        size,
                        new GLFormat(GLFormat.DataType.UNSIGNED_16),
                        GLDrawParams.Allocate.Direct),
                "",
                "MotionV2CfaReconstruction",
                true);
        this.images = orderedImages;
        this.referenceTimestamp = referenceTimestamp;
        this.parameters = parameters;
        this.glProg = glOne.glProgram;
    }

    @Override
    public void Compile() {}

    public static MotionV2Merger.Result reconstruct(
            Point size,
            ArrayList<ImageFrame> inputImages,
            long referenceTimestamp,
            Parameters parameters) {
        if (inputImages == null || inputImages.isEmpty()) {
            throw new IllegalStateException("Motion V2 reconstruction received no RAW frames");
        }
        if (inputImages.size() == 1) {
            return MotionV2Merger.referenceFoundation(inputImages, referenceTimestamp);
        }

        ImageFrame reference = null;
        ArrayList<ImageFrame> ordered = new ArrayList<>(inputImages.size());
        for (ImageFrame frame : inputImages) {
            if (frame != null && frame.timestamp == referenceTimestamp) {
                reference = frame;
                break;
            }
        }
        if (reference == null || reference.buffer == null) {
            throw new IllegalStateException(
                    "Motion V2 owned reference missing from retained burst: "
                            + referenceTimestamp);
        }

        ordered.add(reference);
        for (ImageFrame frame : inputImages) {
            if (frame != null && frame != reference) ordered.add(frame);
        }

        /* IRIS_26436_REFERENCE_TIME_ORDERED_TEMPORAL_CONSENSUS */
        if (ordered.size() > 2) {
            ordered.subList(1, ordered.size()).sort(
                    (a, b) -> Long.compare(
                            Math.abs(a.timestamp - referenceTimestamp),
                            Math.abs(b.timestamp - referenceTimestamp)));
        }
        StringBuilder temporalOrder = new StringBuilder();
        for (int oi = 1; oi < ordered.size(); oi++) {
            if (oi > 1) temporalOrder.append(',');
            temporalOrder.append(Math.abs(
                    ordered.get(oi).timestamp - referenceTimestamp));
        }
        Log.d(TAG, "IRIS_26436_REFERENCE_TIME_ORDER"
                + " auxiliaryDeltaNs=" + temporalOrder
                + " allFramesRetained=true"
                + " nearestReferenceFirst=true");

        /*
         * IRIS_26414_REFERENCE_RAW_NORMALIZATION_BEFORE_FLOAT_RECON
         * Histogram/scene normalization remains owned by the physical reference
         * RAW, not by the reconstructed float carrier.
         */
        /*
         * IRIS_26423_KNOWN_HOT_PIXEL_SANITIZE
         *
         * Camera2 already gives us STATISTICS_HOT_PIXEL_MAP in Parameters.
         * Correct only explicitly mapped sites before RAW->CFA, alignment and
         * fusion. Two-pixel neighbours stay on the same Bayer/CFA component.
         */
        int mappedHotPixelsCorrected = 0;
        for (ImageFrame ownedFrame : ordered) {
            if (ownedFrame != null && ownedFrame.buffer != null) {
                mappedHotPixelsCorrected += correctKnownHotPixels(
                        ownedFrame.buffer,
                        size.x,
                        size.y,
                        parameters);
            }
        }
        Log.d(TAG, "IRIS_26423_KNOWN_HOT_PIXEL_SANITIZE"
                + " corrected=" + mappedHotPixelsCorrected
                + " frames=" + ordered.size()
                + " beforeAlignment=true"
                + " sameCfaNeighbors=true");

        parameters.motionCanonicalExposureGain =
                MotionV2Merger.computeReferenceGain(
                        reference.buffer,
                        size.x,
                        size.y,
                        parameters);

        MotionV2CfaReconstruction script = null;
        try {
            script = new MotionV2CfaReconstruction(
                    size, ordered, referenceTimestamp, parameters);
            script.Run();
            if (script.output == null) {
                throw new IllegalStateException("Motion V2 reconstruction returned null RAW");
            }
            return new MotionV2Merger.Result(
                    script.output,
                    referenceTimestamp,
                    ordered.size(),
                    script.effectiveSupport);
        } finally {
            if (script != null) {
                try { script.close(); } catch (Throwable ignored) {}
            }
            for (ImageFrame frame : inputImages) {
                if (frame != null) {
                    try { frame.close(); } catch (Throwable ignored) {}
                }
            }
        }
    }

    @Override
    public void Run() {

        final Point raw = parameters.rawSize;
        final Point rawHalf = new Point(raw.x / 2, raw.y / 2);
        final int frameCount = images.size();
        final int tile = 8;

        /*
         * IRIS_26420_MOTION_V2_CANONICAL_GAIN_APPLIED_ONCE
         * computeReferenceGain() owns scene normalization. Apply it at the
         * first linear sensor conversion, equally to reference and auxiliaries.
         */
        final float canonicalGain =
                Math.max(1.0f, parameters.motionCanonicalExposureGain);

        /*
         * IRIS_26418_MOTION_V2_RAW_CODE_DOMAIN
         *
         * Parameters.blackLevel and whiteLevel are copied from Camera2 RAW
         * metadata in sensor code values. raw_to_cfa reads UNSIGNED_16 sensor
         * code values. Therefore V2 uses black level in the same code domain:
         * no inherited 0.5 scale is permitted.
         */
        final float[] blackLevel = new float[] {
                parameters.blackLevel[0],
                parameters.blackLevel[1],
                parameters.blackLevel[2],
                parameters.blackLevel[3]
        };

        float noiseS = 1.0e-6f;
        float noiseO = 1.0e-6f;
        NoiseModeler modeler = parameters.noiseModeler;
        if (modeler != null && modeler.baseModel != null
                && modeler.baseModel.length >= 3) {
            noiseS = (
                    modeler.baseModel[0].first.floatValue()
                            + modeler.baseModel[1].first.floatValue()
                            + modeler.baseModel[2].first.floatValue()) / 3.0f;
            noiseO = (
                    modeler.baseModel[0].second.floatValue()
                            + modeler.baseModel[1].second.floatValue()
                            + modeler.baseModel[2].second.floatValue()) / 3.0f;
        }
        noiseS = Math.max(noiseS, 1.0e-7f);
        noiseO = Math.max(noiseO, 1.0e-8f);

        /*
         * IRIS_26420_V2_CANONICAL_NOISE_DOMAIN
         * y=g*x => Var(y)=g*S*y + g^2*O in the canonical signal domain.
         */
        noiseS *= canonicalGain;
        noiseO *= canonicalGain * canonicalGain;

        /*
         * IRIS_26462_WRONSKI_PUBLIC_SNR_TUNING
         * Public implementation clamps SNR to [6,30] and linearly tunes:
         * kDetail .33->.25, kDenoise 5->3, Dth .81->.71, Dtr 1.24->1.0.
         */
        final float mfsrSnr = Math.max(
                6.0f,
                Math.min(
                        30.0f,
                        0.18f / (float)Math.sqrt(
                                Math.max(
                                        noiseS * 0.18f + noiseO,
                                        1.0e-8f))));
        final float mfsrT = (mfsrSnr - 6.0f) / 24.0f;
        final float mfsrKDetail = 0.33f + mfsrT * (0.25f - 0.33f);
        final float mfsrKDenoise = 5.0f + mfsrT * (3.0f - 5.0f);
        final float mfsrDth = 0.81f + mfsrT * (0.71f - 0.81f);
        final float mfsrDtr = 1.24f + mfsrT * (1.00f - 1.24f);
        final float mfsrKStretch = 4.0f;
        final float mfsrKShrink = 2.0f;
        final int mfsrTileSize =
                mfsrSnr <= 14.0f ? 64 : (mfsrSnr <= 22.0f ? 32 : 16);

        GLTexture referenceRaw = null;
        GLTexture referenceCfa = null;
        /* IRIS_26463_WRONSKI_WB_DOMAIN_REFERENCE */
        GLTexture wronskiReferenceCfa = null;
        GLTexture wronskiReferenceCov = null;
        GLTexture mergedA = null;
        GLTexture mergedB = null;
        GLTexture supportA = null;
        GLTexture supportB = null;
        GLTexture result = null;

        /* IRIS_26424_DIRECT_MULTIFRAME_RGB_TEXTURES */
        GLTexture directRgbA = null;
        GLTexture directRgbB = null;
        GLTexture directSupportA = null;
        GLTexture directSupportB = null;

        /*
         * IRIS_26446_TRUE_FRAME_SUPPORT_TEXTURES
         * Separate from normalized-convolution kernel support.
         * Units: reference=1.0 + sum of accepted auxiliary observation
         * confidences, bounded to retained frame count.
         */
        GLTexture directFrameSupportA = null;
        GLTexture directFrameSupportB = null;
        /*
         * IRIS_26462_HAL_STANDARD_BAYER_WRONSKI_GUARD
         * Published direct-RGB reconstruction is enabled only for standard
         * Bayer and exact even physical RAW dimensions.
         */
        final boolean directBayer =
                parameters.cfaPattern >= 0
                        && parameters.cfaPattern <= 3
                        && raw.x > 0
                        && raw.y > 0
                        && (raw.x % 2) == 0
                        && (raw.y % 2) == 0
                        && rawHalf.x * 2 == raw.x
                        && rawHalf.y * 2 == raw.y;

        /*
         * IRIS_26426_DIRECT_RGB_SENSOR_GAIN_AUTHORITY
         * Keep timestamp-owned HAL gains in method scope because both the
         * reference initializer and every auxiliary accumulator use them.
         */
        final float[] directGains = parameters.motionV2ColorGains;
        final float directGreenGain =
                directGains != null && directGains.length == 4
                        ? 0.5f * (directGains[1] + directGains[2])
                        : 1.0f;
        final float[] directSensorGains =
                directGains != null && directGains.length == 4
                        ? new float[]{
                                directGains[0],
                                directGreenGain,
                                directGains[3]}
                        : new float[]{1.0f, 1.0f, 1.0f};
        final float wronskiGlobalWbR = directSensorGains[0]
                / Math.max(directSensorGains[1], 1.0e-6f);
        final float wronskiGlobalWbG = 1.0f;
        final float wronskiGlobalWbB = directSensorGains[2]
                / Math.max(directSensorGains[1], 1.0e-6f);

        /*
         * IRIS_26447_TRUE_SENSOR_NEUTRAL_HIGHLIGHT_OWNER
         *
         * SENSOR_NEUTRAL_COLOR_POINT is a captured sensor-RGB chromatic
         * direction, not a saturation level and not another white-balance
         * transform. Normalize it to G=1 and expose it only to the reference
         * initializer's missing-channel highlight fallback.
         *
         * Normal measured CFA color remains authoritative. Camera2
         * COLOR_CORRECTION_GAINS + TRANSFORM remain the actual downstream
         * white-balance/color transform and are not replaced or multiplied
         * twice.
         */
        final float[] directWhitePoint = parameters.whitePoint;
        final boolean directWhitePointValid =
                directWhitePoint != null
                        && directWhitePoint.length == 3
                        && Float.isFinite(directWhitePoint[0])
                        && Float.isFinite(directWhitePoint[1])
                        && Float.isFinite(directWhitePoint[2])
                        && directWhitePoint[0] > 1.0e-6f
                        && directWhitePoint[1] > 1.0e-6f
                        && directWhitePoint[2] > 1.0e-6f;
        final float[] directSensorNeutralPoint =
                directWhitePointValid
                        ? new float[]{
                                directWhitePoint[0] / directWhitePoint[1],
                                1.0f,
                                directWhitePoint[2] / directWhitePoint[1]}
                        : new float[]{
                                directGreenGain
                                        / Math.max(directSensorGains[0], 1.0e-6f),
                                1.0f,
                                directGreenGain
                                        / Math.max(directSensorGains[2], 1.0e-6f)};

        try {
            /*
             * IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT
             * Motion V2 now owns the geometric producer and consumer.
             */
            Log.d(TAG, "IRIS_26420_V2_ALIGNMENT_ARCH"
                    + " v2Owned=true"
                    + " legacyPyramidAlignment=false"
                    + " legacyTileAtlas=false"
                    + " continuousFlow=true");

            referenceRaw = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                    images.get(0).buffer,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            referenceCfa = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);

            glProg.setLayout(tile, tile, 1);
            glProg.useAssetProgram("motionv2/raw_to_cfa", true);
            glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
            glProg.setVar("blackLevel", blackLevel);
            glProg.setVar(
                    "exposure",
                    canonicalGain * (
                            images.get(0).pair != null
                                    ? 1.0f / Math.max(
                                            images.get(0).pair.layerMpy, 1.0e-6f)
                                    : 1.0f));
            glProg.setTexture("inTexture", referenceRaw);
            glProg.setTextureCompute("outTexture", referenceCfa, true);
            glProg.computeAuto(rawHalf, 1);

            if (directBayer) {
                /*
                 * IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN
                 * Public implementation normalizes RAW then applies camera WB
                 * before alignment/kernel/merge. Camera2 gains are normalized
                 * to green so Wronski sees the same signal convention.
                 */
                final float wronskiWbR = directSensorGains[0]
                        / Math.max(directSensorGains[1], 1.0e-6f);
                final float wronskiWbG = 1.0f;
                final float wronskiWbB = directSensorGains[2]
                        / Math.max(directSensorGains[1], 1.0e-6f);

                wronskiReferenceCfa = new GLTexture(
                        rawHalf,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_wb_cfa", true);
                glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                glProg.setVar("wbR", wronskiWbR);
                glProg.setVar("wbG", wronskiWbG);
                glProg.setVar("wbB", wronskiWbB);
                glProg.setTextureCompute("inputCfa", referenceCfa, false);
                glProg.setTextureCompute("outputCfa", wronskiReferenceCfa, true);
                glProg.computeAuto(rawHalf, 1);

                wronskiReferenceCov = new GLTexture(
                        rawHalf,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_kernel_covariance", true);
                glProg.setVar("rawHalf", rawHalf);
                glProg.setVar("noiseS", noiseS);
                glProg.setVar("noiseO", noiseO);
                glProg.setVar("kDetail", mfsrKDetail);
                glProg.setVar("kDenoise", mfsrKDenoise);
                glProg.setVar("Dth", mfsrDth);
                glProg.setVar("Dtr", mfsrDtr);
                glProg.setVar("kStretch", mfsrKStretch);
                glProg.setVar("kShrink", mfsrKShrink);
                glProg.setTextureCompute("inputCfa", wronskiReferenceCfa, false);
                glProg.setTextureCompute("outputCov", wronskiReferenceCov, true);
                glProg.computeAuto(rawHalf, 1);
            }

            mergedA = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            mergedB = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            supportA = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            supportB = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);

            glProg.setLayout(tile, tile, 1);
            glProg.useAssetProgram("motionv2/cfa_reconstruct_init", true);
            glProg.setTextureCompute("referenceTexture", referenceCfa, false);
            glProg.setTextureCompute("outTexture", mergedA, true);
            glProg.setTextureCompute("outSupport", supportA, true);
            glProg.computeAuto(rawHalf, 1);

            GLTexture currentMerged = mergedA;
            GLTexture nextMerged = mergedB;
            GLTexture currentSupport = supportA;
            GLTexture nextSupport = supportB;

            GLTexture currentDirectRgb = null;
            GLTexture nextDirectRgb = null;
            GLTexture currentDirectSupport = null;
            GLTexture nextDirectSupport = null;
            GLTexture currentDirectFrameSupport = null;
            GLTexture nextDirectFrameSupport = null;

            if (directBayer) {
                directRgbA = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directRgbB = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directSupportA = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directSupportB = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directFrameSupportA = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directFrameSupportB = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);

                /* IRIS_26463_WRONSKI_ACCUMULATORS_FLOAT32_DIVIDE_ONCE */
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/direct_rgb_init", true);
                glProg.setVar("rawSize", raw);
                glProg.setVar("rawHalf", rawHalf);
                glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                /* IRIS_26465_REFERENCE_CLIP_PROVENANCE */
                glProg.setVar("clipR", canonicalGain * wronskiGlobalWbR);
                glProg.setVar("clipG", canonicalGain * wronskiGlobalWbG);
                glProg.setVar("clipB", canonicalGain * wronskiGlobalWbB);
                glProg.setTextureCompute(
                        "referenceCfa", wronskiReferenceCfa, false);
                glProg.setTextureCompute(
                        "referenceCov", wronskiReferenceCov, false);
                glProg.setTextureCompute("outNumerator", directRgbA, true);
                glProg.setTextureCompute("outDenominator", directSupportA, true);
                glProg.setTextureCompute(
                        "outFrameSupport", directFrameSupportA, true);
                glProg.computeAuto(raw, 1);

                currentDirectRgb = directRgbA;
                nextDirectRgb = directRgbB;
                currentDirectSupport = directSupportA;
                nextDirectSupport = directSupportB;
                currentDirectFrameSupport = directFrameSupportA;
                nextDirectFrameSupport = directFrameSupportB;
            }

            /*
             * IRIS_26440_REFERENCE_FIRST_TELEMETRY_INIT
             *
             * Read the reference initializer support before any auxiliary frame
             * can modify it. This is diagnostic-only and reuses the proven
             * FLOAT32 V2 readback contract.
             */
            float[] iris26440PreviousDirectSupport = null;
            Iris26440ReferenceSummary iris26440ReferenceSummary = null;
            Iris26440TemporalSummary iris26440TemporalSummary =
                    new Iris26440TemporalSummary(
                            IRIS26440_GRID_W,
                            IRIS26440_GRID_H);
            if (false && /* IRIS_26442_DISABLE_REFERENCE_SUPPORT_GPU_READBACK */ (directBayer && currentDirectSupport != null)) {
                currentDirectSupport.BufferLoad();
                ByteBuffer iris26440ReferenceSupportBytes =
                        currentDirectSupport.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                iris26440PreviousDirectSupport =
                        iris26440CopyFloatBuffer(
                                iris26440ReferenceSupportBytes);
                iris26440ReferenceSummary =
                        iris26440SummarizeReferenceSupport(
                                iris26440PreviousDirectSupport,
                                raw.x,
                                raw.y,
                                IRIS26440_GRID_W,
                                IRIS26440_GRID_H);
                Log.d(TAG, "IRIS_26440_REFERENCE_SUPPORT"
                        + " meanRGB="
                        + iris26440ReferenceSummary.meanR + ","
                        + iris26440ReferenceSummary.meanG + ","
                        + iris26440ReferenceSummary.meanB
                        + " fallbackFractionRGB="
                        + iris26440ReferenceSummary.fallbackR + ","
                        + iris26440ReferenceSummary.fallbackG + ","
                        + iris26440ReferenceSummary.fallbackB
                        + " fallbackRBGrid12x8="
                        + iris26440FormatGrid(
                                iris26440ReferenceSummary.fallbackRbGrid)
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_REFERENCE_SUPPORT",
                            "meanR=" + iris26440ReferenceSummary.meanR
                                    + " meanG=" + iris26440ReferenceSummary.meanG
                                    + " meanB=" + iris26440ReferenceSummary.meanB
                                    + " fallbackR=" + iris26440ReferenceSummary.fallbackR
                                    + " fallbackG=" + iris26440ReferenceSummary.fallbackG
                                    + " fallbackB=" + iris26440ReferenceSummary.fallbackB
                                    + " fallbackRBGrid12x8="
                                    + iris26440FormatGrid(
                                            iris26440ReferenceSummary.fallbackRbGrid));
                } catch (Throwable ignored) {}
            }

            /*
             * Also inspect the immutable reference CFA before merging. This is
             * read-only telemetry for clipped/thin-structure diagnosis.
             */
            if (false && /* IRIS_26442_DISABLE_REFERENCE_CFA_CLIP_GPU_READBACK */ (directBayer && referenceCfa != null)) {
                referenceCfa.BufferLoad();
                ByteBuffer iris26440ReferenceCfaBytes =
                        referenceCfa.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                Iris26440ClipSummary iris26440ClipSummary =
                        iris26440SummarizeReferenceClip(
                                iris26440ReferenceCfaBytes,
                                rawHalf.x,
                                rawHalf.y,
                                canonicalGain,
                                IRIS26440_GRID_W,
                                IRIS26440_GRID_H);
                Log.d(TAG, "IRIS_26440_REFERENCE_CFA_CLIP"
                        + " nearClipComponentFraction="
                        + iris26440ClipSummary.c0 + ","
                        + iris26440ClipSummary.c1 + ","
                        + iris26440ClipSummary.c2 + ","
                        + iris26440ClipSummary.c3
                        + " anyNearClipGrid12x8="
                        + iris26440FormatGrid(
                                iris26440ClipSummary.anyClipGrid)
                        + " thresholdRelative=0.93"
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_REFERENCE_CFA_CLIP",
                            "componentFractions="
                                    + iris26440ClipSummary.c0 + ","
                                    + iris26440ClipSummary.c1 + ","
                                    + iris26440ClipSummary.c2 + ","
                                    + iris26440ClipSummary.c3
                                    + " anyNearClipGrid12x8="
                                    + iris26440FormatGrid(
                                            iris26440ClipSummary.anyClipGrid));
                } catch (Throwable ignored) {}
            }

            for (int i = 1; i < frameCount; i++) {
                ImageFrame frame = images.get(i);
                if (frame == null || frame.buffer == null) continue;

                /*
                 * IRIS_26439_V2_TEMPORAL_OWNERSHIP_PRODUCER
                 *
                 * V2 previously retained frame timestamps in Java but never
                 * delivered temporal distance to the local CFA accumulator.
                 * Keep every RAW available; make age explicit so local
                 * evidence can become stricter as it moves farther from the
                 * immutable reference instant.
                 */
                final float temporalDistanceMs =
                        referenceTimestamp > 0L && frame.timestamp > 0L
                                ? Math.min(
                                        1000.0f,
                                        Math.abs(
                                                frame.timestamp
                                                        - referenceTimestamp)
                                                / 1_000_000.0f)
                                : 1000.0f;

                /*
                 * IRIS_26441_CRASH_SAFE_TEMPORAL_AGE
                 *
                 * Diagnostic-only CPU telemetry. No GPU readback and no image
                 * math dependency. This preserves temporal-distance visibility
                 * after disabling the crashing per-frame support texture readback.
                 */
                final String iris26441AgeBin =
                        temporalDistanceMs < 50.0f
                                ? "LT50"
                                : temporalDistanceMs < 120.0f
                                        ? "50_120"
                                        : temporalDistanceMs < 200.0f
                                                ? "120_200"
                                                : "GT200";
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26441_TEMPORAL_FRAME_AGE",
                            "frameIndex=" + i
                                    + " temporalDistanceMs=" + temporalDistanceMs
                                    + " ageBin=" + iris26441AgeBin
                                    + " gpuReadback=false"
                                    + " imageMathUnchanged=true");
                } catch (Throwable ignored) {}

                GLTexture rawInput = null;
                GLTexture alterCfa = null;
                GLTexture wronskiAlterCfa = null;
                GLTexture wronskiAlterCov = null;
                try {
                    rawInput = new GLTexture(
                            raw,
                            new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                            frame.buffer,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    alterCfa = new GLTexture(
                            rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);

                    float exposure = canonicalGain * (
                            frame.pair != null
                                    ? 1.0f / Math.max(
                                            frame.pair.layerMpy, 1.0e-6f)
                                    : 1.0f);

                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/raw_to_cfa", true);
                    glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
                    glProg.setVar("blackLevel", blackLevel);
                    glProg.setVar("exposure", exposure);
                    glProg.setTexture("inTexture", rawInput);
                    glProg.setTextureCompute("outTexture", alterCfa, true);
                    glProg.computeAuto(rawHalf, 1);

                    if (directBayer) {
                        final float wronskiWbR = directSensorGains[0]
                                / Math.max(directSensorGains[1], 1.0e-6f);
                        final float wronskiWbB = directSensorGains[2]
                                / Math.max(directSensorGains[1], 1.0e-6f);
                        wronskiAlterCfa = new GLTexture(
                                rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile, tile, 1);
                        glProg.useAssetProgram("motionv2/mfsr_wb_cfa", true);
                        glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                        glProg.setVar("wbR", wronskiWbR);
                        glProg.setVar("wbG", 1.0f);
                        glProg.setVar("wbB", wronskiWbB);
                        glProg.setTextureCompute("inputCfa", alterCfa, false);
                        glProg.setTextureCompute("outputCfa", wronskiAlterCfa, true);
                        glProg.computeAuto(rawHalf, 1);

                        wronskiAlterCov = new GLTexture(
                                rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile, tile, 1);
                        glProg.useAssetProgram("motionv2/mfsr_kernel_covariance", true);
                        glProg.setVar("rawHalf", rawHalf);
                        glProg.setVar("noiseS", noiseS);
                        glProg.setVar("noiseO", noiseO);
                        glProg.setVar("kDetail", mfsrKDetail);
                        glProg.setVar("kDenoise", mfsrKDenoise);
                        glProg.setVar("Dth", mfsrDth);
                        glProg.setVar("Dtr", mfsrDtr);
                        glProg.setVar("kStretch", mfsrKStretch);
                        glProg.setVar("kShrink", mfsrKShrink);
                        glProg.setTextureCompute("inputCfa", wronskiAlterCfa, false);
                        glProg.setTextureCompute("outputCov", wronskiAlterCov, true);
                        glProg.computeAuto(rawHalf, 1);
                    }

                    MotionV2Alignment.Result ownedAlignment = null;
                    try {
                        long alignmentStart = System.currentTimeMillis();
                        ownedAlignment =
                                directBayer
                                        ? MotionV2WronskiAlignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                mfsrSnr,
                                                glProg,
                                                wronskiReferenceCfa,
                                                wronskiAlterCfa)
                                        : MotionV2Alignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                glProg,
                                                referenceCfa,
                                                alterCfa);

                        glProg.setLayout(tile, tile, 1);
                        glProg.useAssetProgram(
                                "motionv2/cfa_reconstruct_accumulate", true);
                        glProg.setVar("rawHalf", rawHalf);
                        /*
                         * IRIS_26452_PHASE_AWARE_CFA_BINDINGS
                         * Flow is packed-CFA displacement; the shader converts it
                         * exactly once into physical RAW-pixel displacement.
                         */
                        glProg.setVar("rawSize", raw);
                        glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                        glProg.setVar("temporalDistanceMs", temporalDistanceMs);
                        glProg.setVar("noiseS", noiseS);
                        glProg.setVar("noiseO", noiseO);
                        glProg.setVar("maximumSupport", (float) frameCount);
                        glProg.setVar("sensorClipLevel", canonicalGain);
                        glProg.setTexture(
                                "flowTexture",
                                ownedAlignment.flowTexture);
                        glProg.setTextureCompute(
                                "referenceTexture", referenceCfa, false);
                        glProg.setTextureCompute(
                                "currentTexture", currentMerged, false);
                        glProg.setTextureCompute(
                                "alterTexture", alterCfa, false);
                        glProg.setTextureCompute(
                                "currentSupport", currentSupport, false);
                        glProg.setTextureCompute(
                                "outTexture", nextMerged, true);
                        glProg.setTextureCompute(
                                "outSupport", nextSupport, true);
                        glProg.computeAuto(rawHalf, 1);

                        if (directBayer) {
                            /*
                             * IRIS_26462_FULL_PUBLISHED_WRONSKI_MFSR
                             * Robustness -> 5x5 min -> independent RGB merge.
                             */
                            GLTexture mfsrRobustRaw = new GLTexture(
                                    raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
                            GLTexture mfsrRobustMin = new GLTexture(
                                    raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
                            try {
                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness", true);
                                glProg.setVar("rawSize", raw);
                                glProg.setVar("rawHalf", rawHalf);
                                glProg.setVar(
                                        "cfaPattern",
                                        (int) parameters.cfaPattern);
                                glProg.setVar("noiseS", noiseS);
                                glProg.setVar("noiseO", noiseO);
                                glProg.setVar(
                                        "tileSizeRaw",
                                        Math.max(1, mfsrTileSize));
                                glProg.setVar(
                                        "wbR",
                                        directSensorGains[0]
                                                / Math.max(directSensorGains[1], 1.0e-6f));
                                glProg.setVar("wbG", 1.0f);
                                glProg.setVar(
                                        "wbB",
                                        directSensorGains[2]
                                                / Math.max(directSensorGains[1], 1.0e-6f));
                                glProg.setTexture(
                                        "flowTexture",
                                        ownedAlignment.flowTexture);
                                glProg.setTextureCompute(
                                        "referenceCfa", wronskiReferenceCfa, false);
                                glProg.setTextureCompute(
                                        "alterCfa", wronskiAlterCfa, false);
                                glProg.setTextureCompute(
                                        "outRobustness",
                                        mfsrRobustRaw,
                                        true);
                                glProg.computeAuto(raw, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness_erode", true);
                                glProg.setTexture(
                                        "InputRobustness",
                                        mfsrRobustRaw);
                                glProg.setTextureCompute(
                                        "OutputRobustness",
                                        mfsrRobustMin,
                                        true);
                                glProg.computeAuto(raw, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/direct_rgb_accumulate", true);
                                glProg.setVar("rawSize", raw);
                                glProg.setVar("rawHalf", rawHalf);
                                glProg.setVar(
                                        "cfaPattern",
                                        (int) parameters.cfaPattern);
                                glProg.setVar(
                                        "maximumSupport",
                                        (float) frameCount);
                                /* IRIS_26465_AUX_CLIP_PROVENANCE */
                                glProg.setVar("clipR", exposure * wronskiGlobalWbR);
                                glProg.setVar("clipG", exposure);
                                glProg.setVar("clipB", exposure * wronskiGlobalWbB);
                                glProg.setTexture(
                                        "flowTexture",
                                        ownedAlignment.flowTexture);
                                glProg.setTexture(
                                        "robustnessTexture",
                                        mfsrRobustMin);
                                glProg.setTexture(
                                        "previousNumerator",
                                        currentDirectRgb);
                                glProg.setTexture(
                                        "previousDenominator",
                                        currentDirectSupport);
                                glProg.setTexture(
                                        "previousFrameSupport",
                                        currentDirectFrameSupport);
                                glProg.setTextureCompute(
                                        "alterCfa",
                                        wronskiAlterCfa,
                                        false);
                                glProg.setTextureCompute(
                                        "alterCov",
                                        wronskiAlterCov,
                                        false);
                                glProg.setTextureCompute(
                                        "outNumerator",
                                        nextDirectRgb,
                                        true);
                                glProg.setTextureCompute(
                                        "outDenominator",
                                        nextDirectSupport,
                                        true);
                                glProg.setTextureCompute(
                                        "outFrameSupport",
                                        nextDirectFrameSupport,
                                        true);
                                glProg.computeAuto(raw, 1);
                            } finally {
                                mfsrRobustMin.close();
                                mfsrRobustRaw.close();
                            }

                            /*
                             * IRIS_26440_PER_FRAME_TEMPORAL_SUPPORT_DELTA
                             *
                             * The output support after THIS auxiliary is
                             * subtracted from the previous support snapshot.
                             * Therefore the telemetry retains frame/source
                             * identity without altering shader/image math.
                             */
                            if (false && /* IRIS_26441_DISABLE_PER_FRAME_SUPPORT_READBACK */ (iris26440PreviousDirectSupport != null)) {
                                nextDirectSupport.BufferLoad();
                                ByteBuffer iris26440NextSupportBytes =
                                        nextDirectSupport.textureBuffer(
                                                new GLFormat(
                                                        GLFormat.DataType.FLOAT_32,
                                                        4),
                                                true);
                                float[] iris26440NextSupport =
                                        iris26440CopyFloatBuffer(
                                                iris26440NextSupportBytes);
                                Iris26440FrameDelta iris26440Delta =
                                        iris26440SummarizeFrameDelta(
                                                iris26440PreviousDirectSupport,
                                                iris26440NextSupport,
                                                raw.x,
                                                raw.y,
                                                temporalDistanceMs,
                                                IRIS26440_GRID_W,
                                                IRIS26440_GRID_H);
                                iris26440TemporalSummary.add(
                                        temporalDistanceMs,
                                        iris26440Delta);
                                Log.d(TAG, "IRIS_26440_FRAME_SUPPORT_DELTA"
                                        + " frame=" + i
                                        + " ageMs=" + temporalDistanceMs
                                        + " ageBin="
                                        + iris26440AgeBinName(
                                                temporalDistanceMs)
                                        + " meanDeltaRGB="
                                        + iris26440Delta.meanR + ","
                                        + iris26440Delta.meanG + ","
                                        + iris26440Delta.meanB
                                        + " positivePixelFraction="
                                        + iris26440Delta.positiveFraction
                                        + " grid12x8="
                                        + iris26440FormatGrid(
                                                iris26440Delta.grid)
                                        + " imageMathUnchanged=true");
                                try {
                                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                            "IRIS_26440_FRAME_SUPPORT_DELTA",
                                            "frame=" + i
                                                    + " ageMs=" + temporalDistanceMs
                                                    + " ageBin="
                                                    + iris26440AgeBinName(
                                                            temporalDistanceMs)
                                                    + " meanR="
                                                    + iris26440Delta.meanR
                                                    + " meanG="
                                                    + iris26440Delta.meanG
                                                    + " meanB="
                                                    + iris26440Delta.meanB
                                                    + " positiveFraction="
                                                    + iris26440Delta.positiveFraction
                                                    + " grid12x8="
                                                    + iris26440FormatGrid(
                                                            iris26440Delta.grid));
                                } catch (Throwable ignored) {}
                                iris26440PreviousDirectSupport =
                                        iris26440NextSupport;
                            }

                            /*
                             * IRIS_26464_GLES31_WRONSKI_PING_PONG_FLOAT32
                             * Same public Wronski running num/den recurrence;
                             * separate previous/next textures only satisfy the
                             * GLSL ES rgba32f image access contract.
                             */
                            GLTexture swapDirectRgb = currentDirectRgb;
                            currentDirectRgb = nextDirectRgb;
                            nextDirectRgb = swapDirectRgb;

                            GLTexture swapDirectSupport = currentDirectSupport;
                            currentDirectSupport = nextDirectSupport;
                            nextDirectSupport = swapDirectSupport;

                            GLTexture swapDirectFrameSupport =
                                    currentDirectFrameSupport;
                            currentDirectFrameSupport =
                                    nextDirectFrameSupport;
                            nextDirectFrameSupport = swapDirectFrameSupport;
                        }

                        Log.d(TAG, "IRIS_26420_V2_ALIGNMENT_FRAME"
                                + " frame=" + i
                                + " elapsedMs="
                                + (System.currentTimeMillis()-alignmentStart)
                                + " globalDxPacked="
                                + ownedAlignment.globalDxPacked
                                + " globalDyPacked="
                                + ownedAlignment.globalDyPacked
                                + " meanConfidence="
                                + ownedAlignment.meanConfidence
                                + " lowConfidenceFraction="
                                + ownedAlignment.lowConfidenceFraction
                                + " temporalDistanceMs="
                                + temporalDistanceMs);
                    } finally {
                        if (ownedAlignment != null) ownedAlignment.close();
                    }

                    GLTexture swapMerged = currentMerged;
                    currentMerged = nextMerged;
                    nextMerged = swapMerged;

                    GLTexture swapSupport = currentSupport;
                    currentSupport = nextSupport;
                    nextSupport = swapSupport;
                } finally {
                    if (wronskiAlterCov != null) wronskiAlterCov.close();
                    if (wronskiAlterCfa != null) wronskiAlterCfa.close();
                    if (alterCfa != null) alterCfa.close();
                    if (rawInput != null) rawInput.close();
                }
            }

            /*
             * IRIS_26440_TEMPORAL_BIN_SUMMARY
             *
             * Reference-first decision telemetry:
             *   <50 ms, 50-120 ms, 120-200 ms, >200 ms.
             * These are measured support additions, not requested frames.
             */
            if (false && /* IRIS_26442_DISABLE_DIRECT_RGB_SUPPORT_GPU_READBACK */ (directBayer)) {
                Log.d(TAG, "IRIS_26440_TEMPORAL_BIN_SUMMARY"
                        + " lt50MeanRGB="
                        + iris26440TemporalSummary.meanRgb(0)
                        + " ms50to120MeanRGB="
                        + iris26440TemporalSummary.meanRgb(1)
                        + " ms120to200MeanRGB="
                        + iris26440TemporalSummary.meanRgb(2)
                        + " gt200MeanRGB="
                        + iris26440TemporalSummary.meanRgb(3)
                        + " lt50Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(0))
                        + " ms50to120Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(1))
                        + " ms120to200Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(2))
                        + " gt200Grid12x8="
                        + iris26440FormatGrid(
                                iris26440TemporalSummary.grid(3))
                        + " referenceFirstTarget=true"
                        + " staticOnlyTemporalEnrichmentTarget=true"
                        + " naturalReferenceMotionBlurPreserved=true"
                        + " imageMathUnchanged=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26440_TEMPORAL_BIN_SUMMARY",
                            "lt50=" + iris26440TemporalSummary.meanRgb(0)
                                    + " 50to120="
                                    + iris26440TemporalSummary.meanRgb(1)
                                    + " 120to200="
                                    + iris26440TemporalSummary.meanRgb(2)
                                    + " gt200="
                                    + iris26440TemporalSummary.meanRgb(3)
                                    + " gt200Grid12x8="
                                    + iris26440FormatGrid(
                                            iris26440TemporalSummary.grid(3))
                                    + " referenceFirstTarget=true");
                } catch (Throwable ignored) {}
            }

            /*
             * IRIS_26416_MOTION_V2_PROVEN_FLOAT32_BRIDGE
             *
             * 26415 audit proved Photon's generic FLOAT_16 ByteBuffer transfer
             * contract is internally inconsistent: two bytes/channel are
             * allocated while GL_FLOAT requests four-byte transfer elements.
             *
             * Until Motion V2 owns a single shared GL context end-to-end, use
             * an explicit FLOAT32 transfer. FLOAT_32 is four bytes/channel and
             * GL_FLOAT is also four bytes/component, so the byte count and GL
             * transfer type agree exactly. This bridge is a stabilization
             * boundary, not an image-processing stage.
             */
            /*
             * IRIS_26424_DIRECT_MULTIFRAME_RGB_OUTPUT
             * Preserve the proven 26416 FLOAT32 cross-context bridge.
             */
            /*
             * IRIS_26446_LOCAL_FRAME_SUPPORT_CARRIER
             *
             * GPU-only finalization. RGB stays byte-for-byte mathematically
             * identical to currentDirectRgb; alpha becomes true local
             * frame-equivalent support. No diagnostic support readback is added.
             */
            GLTexture imageOutput;
            if (directBayer) {
                /*
                 * Wronski direct-RGB final owner for standard Bayer.
                 * No explicit MotionV2CfaDemosaic for standard Bayer.
                 */
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_finalize", true);
                glProg.setVar(
                        "wbR",
                        directSensorGains[0]
                                / Math.max(directSensorGains[1], 1.0e-6f));
                glProg.setVar("wbG", 1.0f);
                glProg.setVar(
                        "wbB",
                        directSensorGains[2]
                                / Math.max(directSensorGains[1], 1.0e-6f));
                glProg.setTextureCompute(
                        "currentNumerator", currentDirectRgb, false);
                glProg.setTextureCompute(
                        "currentDenominator", currentDirectSupport, false);
                glProg.setTextureCompute(
                        "currentFrameSupport",
                        currentDirectFrameSupport,
                        false);
                glProg.setTextureCompute("outRgb", nextDirectRgb, true);
                glProg.computeAuto(raw, 1);
                imageOutput = nextDirectRgb;
                Log.d(TAG,
                        "IRIS_26465_WRONSKI_PLUS_PROVEN_CFA_SATURATION_VALIDITY"
                        + " publishedMethod=true"
                        + " perFrameCovariance=true"
                        + " alignedCovarianceInterpolation=true"
                        + " halfPixelGather=true"
                        + " float32NumDen=true"
                        + " gles31PingPong=true"
                        + " divideOnce=true"
                        + " wronskiWbDomain=true"
                        + " directPhysicalCfa=true"
                        + " separateDemosaic=false"
                        + " sharpening=false"
                        + " saturationValidity=true"
                        + " fullyClippedNeutralRecovery=true"
                        + " partialColorPreserved=true");
            } else {
                imageOutput = currentMerged;
            }
            imageOutput.BufferLoad();
            output = imageOutput.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    true);
            output.order(ByteOrder.nativeOrder());
            output.position(0);

            Log.d(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE"
                    + " sourceInternal=rgba32f"
                    + " transfer=rgba32f"
                    + " bytesPerChannel=4"
                    + " glType=GL_FLOAT"
                    + " size=" + (directBayer
                            ? raw.x + "x" + raw.y
                            : rawHalf.x + "x" + rawHalf.y)
                    + " raw16Repack=false"
                    + " float16Transfer=false"
                    + " legacyMerge00=false"
                    + " directMultiframeRgb=" + directBayer
                    + " normalizedConvolution=true"
                    + " float32BurstAccumulators=" + directBayer
                    + " divideOnceAfterBurst=" + directBayer
                    + " perFrameCovariance=" + directBayer
                    + " publicHalfPixelMergeGeometry=" + directBayer
                    + " perFrameRgbCandidate=false"
                    + " anisotropicKernel=true"
                    + " clippedChromaFloor=false"
                    + " sharedGuideRobustness=" + directBayer
                    + " rgbPredictionRobustness=false"
                    + " referenceCfaStructure=" + directBayer
                    + " orderIndependentWeights=" + directBayer
                    + " crossEdgeSigmaMin=0.72"
                    + " separateDemosaic=" + (!directBayer)
                    + " hdrHeadroomPreserved=true");

            /*
             * IRIS_26426_DIRECT_RGB_CHANNEL_SUPPORT_TELEMETRY
             *
             * Diagnostic-only readback of the NEW direct RGB support carrier.
             * It does not feed image math. This tells us whether R/G/B are
             * actually receiving burst support in the difficult highlight/edge
             * pixels rather than relying on the legacy packed-CFA support map.
             */
            if (directBayer && currentDirectSupport != null) {
                currentDirectSupport.BufferLoad();
                ByteBuffer directSupportBytes =
                        currentDirectSupport.textureBuffer(
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                true);
                DirectRgbSupportSummary directSummary =
                        summarizeDirectRgbSupport(
                                directSupportBytes,
                                raw.x,
                                raw.y);
                Log.d(TAG, "IRIS_26426_DIRECT_RGB_SUPPORT"
                        + " meanRGB=" + directSummary.meanR + ","
                                + directSummary.meanG + ","
                                + directSummary.meanB
                        + " lowSupportRGB=" + directSummary.lowR + ","
                                + directSummary.lowG + ","
                                + directSummary.lowB
                        + " imbalanceP95=" + directSummary.imbalanceP95
                        + " sampledPixels=" + directSummary.samples
                        + " perChannel=true"
                        + " imageMathUnchangedByTelemetry=true");
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26426_DIRECT_RGB_SUPPORT",
                            "meanR=" + directSummary.meanR
                                    + " meanG=" + directSummary.meanG
                                    + " meanB=" + directSummary.meanB
                                    + " lowR=" + directSummary.lowR
                                    + " lowG=" + directSummary.lowG
                                    + " lowB=" + directSummary.lowB
                                    + " imbalanceP95=" + directSummary.imbalanceP95
                                    + " samples=" + directSummary.samples);
                } catch (Throwable ignored) {}
            }

            /*
             * Deliberate readback only for truthful support accounting.
             * The image reconstruction itself remains GPU-side.
             */
            currentSupport.BufferLoad();
            ByteBuffer supportBytes = currentSupport.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    true);
            SupportSummary summary = summarizeSupport(
                    supportBytes,
                    rawHalf.x,
                    rawHalf.y,
                    frameCount);

            effectiveSupport = summary.mean;
            supportP10 = summary.p10;
            supportP50 = summary.p50;
            supportP90 = summary.p90;

            MotionMetrics.publishV2Support(
                    effectiveSupport,
                    summary.coarseGrid,
                    summary.gridWidth,
                    summary.gridHeight);

            /*
             * IRIS_26436_PERMANENT_SPATIAL_SUPPORT_TELEMETRY
             * Logging only; never participates in reconstruction.
             */
            StringBuilder supportGrid12x8 = new StringBuilder();
            float supportRoughness = 0.0f;
            int supportRoughCount = 0;
            for (int y = 0; y < summary.gridHeight; y++) {
                for (int x = 0; x < summary.gridWidth; x++) {
                    int idx = y * summary.gridWidth + x;
                    float c = summary.coarseGrid[idx];
                    if (x + 1 < summary.gridWidth) {
                        supportRoughness += Math.abs(
                                c - summary.coarseGrid[idx + 1]);
                        supportRoughCount++;
                    }
                    if (y + 1 < summary.gridHeight) {
                        supportRoughness += Math.abs(
                                c - summary.coarseGrid[
                                        idx + summary.gridWidth]);
                        supportRoughCount++;
                    }
                }
            }
            supportRoughness = supportRoughCount > 0
                    ? supportRoughness / supportRoughCount
                    : 0.0f;
            for (int gy = 0; gy < 8; gy++) {
                if (gy > 0) supportGrid12x8.append('/');
                int sy = Math.min(
                        summary.gridHeight - 1,
                        (int)(((gy + 0.5f) * summary.gridHeight) / 8.0f));
                for (int gx = 0; gx < 12; gx++) {
                    int sx = Math.min(
                            summary.gridWidth - 1,
                            (int)(((gx + 0.5f) * summary.gridWidth) / 12.0f));
                    float value = summary.coarseGrid[
                            sy * summary.gridWidth + sx];
                    int code = Math.max(0, Math.min(
                            255,
                            Math.round(
                                    value / Math.max(1, frameCount)
                                            * 255.0f)));
                    if (code < 16) supportGrid12x8.append('0');
                    supportGrid12x8.append(Integer.toHexString(code));
                }
            }
            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");

            Log.d(TAG, "IRIS_26413_V2_CFA_RECONSTRUCTION"
                    + " referenceTimestamp=" + referenceTimestamp
                    + " retainedFrames=" + frameCount
                    + " effectiveSupport=" + effectiveSupport
                    + " supportP10=" + supportP10
                    + " supportP50=" + supportP50
                    + " supportP90=" + supportP90
                    + " allRetainedFramesConsidered=true"
                    + " referenceGeometryAuthoritative=true"
                    + " confidenceZeroReturnsReference=true"
                    + " sharedCfaFlow=true"
                    + " subpixelSampling=truePerObservationNormalizedConvolution"
                    + " directMultiframeRgb=" + directBayer
                    + " legacyPyramidMerge=false"
                    + " legacyPyramidAlignment=false"
                    + " v2OwnedContinuousAlignment=true"
                    + " sharpening=false");

            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26413_MOTION_V2_CFA_RECONSTRUCTION",
                        "referenceTimestamp=" + referenceTimestamp
                                + " retained=" + frameCount
                                + " effectiveSupport=" + effectiveSupport
                                + " p10=" + supportP10
                                + " p50=" + supportP50
                                + " p90=" + supportP90
                                + " localSupportGrid="
                                + summary.gridWidth + "x" + summary.gridHeight
                                + " referenceOwned=true"
                                + " fractionalAlignment=true"
                                + " alignmentOwner=MotionV2"
                                + " legacyPyramidAlignment=false"
                                + " sharedFlow=true"
                                + " confidenceZeroReferenceFallback=true");
            } catch (Throwable ignored) {}
        } finally {
            /* IRIS_26413 pack-fix: no temporary uint16 result texture is allocated. */
            if (directFrameSupportB != null) directFrameSupportB.close();
            if (directFrameSupportA != null) directFrameSupportA.close();
            if (directSupportB != null) directSupportB.close();
            if (directSupportA != null) directSupportA.close();
            if (directRgbB != null) directRgbB.close();
            if (directRgbA != null) directRgbA.close();
            if (supportB != null) supportB.close();
            if (supportA != null) supportA.close();
            if (mergedB != null) mergedB.close();
            if (mergedA != null) mergedA.close();
            if (wronskiReferenceCov != null) wronskiReferenceCov.close();
            if (wronskiReferenceCfa != null) wronskiReferenceCfa.close();
            if (referenceCfa != null) referenceCfa.close();
            if (referenceRaw != null) referenceRaw.close();
        }
    }

    /*
     * Only Camera2-declared defective sites are altered here. Coordinates from
     * STATISTICS_HOT_PIXEL_MAP are normally in sensor active-array space; map
     * through sensorPix when available and retain a direct-coordinate fallback
     * for HALs that already report RAW-buffer-relative points.
     */
    private static int correctKnownHotPixels(
            ByteBuffer buffer,
            int width,
            int height,
            Parameters parameters) {
        if (buffer == null || width <= 4 || height <= 4
                || parameters == null
                || parameters.hotPixels == null
                || parameters.hotPixels.length == 0) {
            return 0;
        }

        ByteBuffer view = buffer.duplicate().order(ByteOrder.nativeOrder());
        int sampleCapacity = view.capacity() / 2;
        int corrected = 0;

        for (Point hot : parameters.hotPixels) {
            if (hot == null) continue;

            int x = hot.x;
            int y = hot.y;

            if (parameters.sensorPix != null) {
                int translatedX = hot.x - parameters.sensorPix.left;
                int translatedY = hot.y - parameters.sensorPix.top;
                if (translatedX >= 0 && translatedX < width
                        && translatedY >= 0 && translatedY < height) {
                    x = translatedX;
                    y = translatedY;
                }
            }

            if (x < 0 || x >= width || y < 0 || y >= height) continue;

            int[] values = new int[4];
            int n = 0;
            int[][] offsets = new int[][]{
                    {-2, 0}, {2, 0}, {0, -2}, {0, 2}
            };

            for (int[] d : offsets) {
                int nx = x + d[0];
                int ny = y + d[1];
                if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
                int index = ny * width + nx;
                if (index < 0 || index >= sampleCapacity) continue;
                values[n++] = Short.toUnsignedInt(view.getShort(index * 2));
            }

            if (n < 2) continue;

            for (int i = 1; i < n; i++) {
                int v = values[i];
                int j = i - 1;
                while (j >= 0 && values[j] > v) {
                    values[j + 1] = values[j];
                    j--;
                }
                values[j + 1] = v;
            }

            int replacement = (n & 1) != 0
                    ? values[n / 2]
                    : (values[n / 2 - 1] + values[n / 2]) / 2;

            int target = y * width + x;
            if (target < 0 || target >= sampleCapacity) continue;
            view.putShort(target * 2, (short)(replacement & 0xffff));
            corrected++;
        }
        return corrected;
    }
    /*
     * IRIS_26440_DIAGNOSTIC_HELPERS
     * No method below feeds reconstruction/image math.
     */
    private static float[] iris26440CopyFloatBuffer(ByteBuffer bytes) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();
        float[] out = new float[values.capacity()];
        for (int i = 0; i < out.length; i++) {
            float v = values.get(i);
            out[i] = Float.isFinite(v) ? v : 0.0f;
        }
        return out;
    }

    private static int iris26440AgeBin(float ageMs) {
        if (ageMs < 50.0f) return 0;
        if (ageMs < 120.0f) return 1;
        if (ageMs < 200.0f) return 2;
        return 3;
    }

    private static String iris26440AgeBinName(float ageMs) {
        int bin = iris26440AgeBin(ageMs);
        if (bin == 0) return "lt50";
        if (bin == 1) return "50to120";
        if (bin == 2) return "120to200";
        return "gt200";
    }

    private static String iris26440FormatGrid(float[] grid) {
        if (grid == null) return "null";
        StringBuilder sb = new StringBuilder(grid.length * 7);
        for (int i = 0; i < grid.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(String.format(java.util.Locale.US, "%.3f", grid[i]));
        }
        return sb.toString();
    }

    private static final class Iris26440ReferenceSummary {
        final float meanR;
        final float meanG;
        final float meanB;
        final float fallbackR;
        final float fallbackG;
        final float fallbackB;
        final float[] fallbackRbGrid;

        Iris26440ReferenceSummary(
                float meanR,
                float meanG,
                float meanB,
                float fallbackR,
                float fallbackG,
                float fallbackB,
                float[] fallbackRbGrid) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.fallbackR = fallbackR;
            this.fallbackG = fallbackG;
            this.fallbackB = fallbackB;
            this.fallbackRbGrid = fallbackRbGrid;
        }
    }

    private static Iris26440ReferenceSummary iris26440SummarizeReferenceSupport(
            float[] support,
            int width,
            int height,
            int gridW,
            int gridH) {
        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        long fallbackR = 0L;
        long fallbackG = 0L;
        long fallbackB = 0L;
        long count = 0L;
        double[] gridFallback = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];

        int pixels = Math.min(width * height, support.length / 4);
        for (int p = 0; p < pixels; p++) {
            float r = Math.max(0.0f, support[4 * p]);
            float g = Math.max(0.0f, support[4 * p + 1]);
            float b = Math.max(0.0f, support[4 * p + 2]);
            boolean fr = r <= 0.00015f;
            boolean fg = g <= 0.00015f;
            boolean fb = b <= 0.00015f;
            sumR += r;
            sumG += g;
            sumB += b;
            if (fr) fallbackR++;
            if (fg) fallbackG++;
            if (fb) fallbackB++;
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            if (fr || fb) gridFallback[gi] += 1.0;
            gridCount[gi]++;
            count++;
        }

        float[] grid = new float[gridFallback.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridFallback[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1L, count);
        return new Iris26440ReferenceSummary(
                (float) (sumR / denom),
                (float) (sumG / denom),
                (float) (sumB / denom),
                fallbackR / (float) denom,
                fallbackG / (float) denom,
                fallbackB / (float) denom,
                grid);
    }

    private static final class Iris26440ClipSummary {
        final float c0;
        final float c1;
        final float c2;
        final float c3;
        final float[] anyClipGrid;

        Iris26440ClipSummary(
                float c0,
                float c1,
                float c2,
                float c3,
                float[] anyClipGrid) {
            this.c0 = c0;
            this.c1 = c1;
            this.c2 = c2;
            this.c3 = c3;
            this.anyClipGrid = anyClipGrid;
        }
    }

    private static Iris26440ClipSummary iris26440SummarizeReferenceClip(
            ByteBuffer bytes,
            int width,
            int height,
            float clip,
            int gridW,
            int gridH) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer v = bytes.asFloatBuffer();
        int pixels = Math.min(width * height, v.capacity() / 4);
        long[] clipped = new long[4];
        double[] gridClip = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];
        float threshold = 0.93f * Math.max(clip, 1.0e-6f);

        for (int p = 0; p < pixels; p++) {
            boolean any = false;
            for (int c = 0; c < 4; c++) {
                float value = v.get(4 * p + c);
                if (Float.isFinite(value) && value >= threshold) {
                    clipped[c]++;
                    any = true;
                }
            }
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            if (any) gridClip[gi] += 1.0;
            gridCount[gi]++;
        }

        float[] grid = new float[gridClip.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridClip[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1, pixels);
        return new Iris26440ClipSummary(
                clipped[0] / denom,
                clipped[1] / denom,
                clipped[2] / denom,
                clipped[3] / denom,
                grid);
    }

    private static final class Iris26440FrameDelta {
        final float meanR;
        final float meanG;
        final float meanB;
        final float positiveFraction;
        final float[] grid;

        Iris26440FrameDelta(
                float meanR,
                float meanG,
                float meanB,
                float positiveFraction,
                float[] grid) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.positiveFraction = positiveFraction;
            this.grid = grid;
        }
    }

    private static Iris26440FrameDelta iris26440SummarizeFrameDelta(
            float[] before,
            float[] after,
            int width,
            int height,
            float ageMs,
            int gridW,
            int gridH) {
        int floats = Math.min(before.length, after.length);
        int pixels = Math.min(width * height, floats / 4);
        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        long positive = 0L;
        double[] gridSum = new double[gridW * gridH];
        int[] gridCount = new int[gridW * gridH];

        for (int p = 0; p < pixels; p++) {
            float dr = Math.max(0.0f, after[4 * p] - before[4 * p]);
            float dg = Math.max(0.0f, after[4 * p + 1] - before[4 * p + 1]);
            float db = Math.max(0.0f, after[4 * p + 2] - before[4 * p + 2]);
            float d = (dr + dg + db) / 3.0f;
            sumR += dr;
            sumG += dg;
            sumB += db;
            if (d > 1.0e-5f) positive++;
            int x = p % width;
            int y = p / width;
            int gx = Math.min(gridW - 1, x * gridW / Math.max(1, width));
            int gy = Math.min(gridH - 1, y * gridH / Math.max(1, height));
            int gi = gy * gridW + gx;
            gridSum[gi] += d;
            gridCount[gi]++;
        }

        float[] grid = new float[gridSum.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = gridCount[i] > 0
                    ? (float) (gridSum[i] / gridCount[i])
                    : 0.0f;
        }
        float denom = Math.max(1, pixels);
        return new Iris26440FrameDelta(
                (float) (sumR / denom),
                (float) (sumG / denom),
                (float) (sumB / denom),
                positive / denom,
                grid);
    }

    private static final class Iris26440TemporalSummary {
        private final double[][] gridSum;
        private final int[] frameCount;
        private final double[][] rgbSum;
        private final int gridSize;

        Iris26440TemporalSummary(int gridW, int gridH) {
            gridSize = gridW * gridH;
            gridSum = new double[4][gridSize];
            frameCount = new int[4];
            rgbSum = new double[4][3];
        }

        void add(float ageMs, Iris26440FrameDelta delta) {
            int bin = iris26440AgeBin(ageMs);
            frameCount[bin]++;
            rgbSum[bin][0] += delta.meanR;
            rgbSum[bin][1] += delta.meanG;
            rgbSum[bin][2] += delta.meanB;
            for (int i = 0; i < gridSize && i < delta.grid.length; i++) {
                gridSum[bin][i] += delta.grid[i];
            }
        }

        String meanRgb(int bin) {
            int n = Math.max(1, frameCount[bin]);
            return String.format(
                    java.util.Locale.US,
                    "%.5f,%.5f,%.5f",
                    rgbSum[bin][0] / n,
                    rgbSum[bin][1] / n,
                    rgbSum[bin][2] / n);
        }

        float[] grid(int bin) {
            float[] out = new float[gridSize];
            int n = Math.max(1, frameCount[bin]);
            for (int i = 0; i < gridSize; i++) {
                out[i] = (float) (gridSum[bin][i] / n);
            }
            return out;
        }
    }

    private static final class SupportSummary {
        final float mean;
        final float p10;
        final float p50;
        final float p90;
        final float[] coarseGrid;
        final int gridWidth;
        final int gridHeight;

        SupportSummary(
                float mean,
                float p10,
                float p50,
                float p90,
                float[] coarseGrid,
                int gridWidth,
                int gridHeight) {
            this.mean = mean;
            this.p10 = p10;
            this.p50 = p50;
            this.p90 = p90;
            this.coarseGrid = coarseGrid;
            this.gridWidth = gridWidth;
            this.gridHeight = gridHeight;
        }
    }

    private static final class DirectRgbSupportSummary {
        final float meanR;
        final float meanG;
        final float meanB;
        final float lowR;
        final float lowG;
        final float lowB;
        final float imbalanceP95;
        final int samples;

        DirectRgbSupportSummary(
                float meanR,
                float meanG,
                float meanB,
                float lowR,
                float lowG,
                float lowB,
                float imbalanceP95,
                int samples) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.lowR = lowR;
            this.lowG = lowG;
            this.lowB = lowB;
            this.imbalanceP95 = imbalanceP95;
            this.samples = samples;
        }
    }

    /*
     * IRIS_26426_DIRECT_RGB_CHANNEL_SUPPORT_TELEMETRY
     * Sample every eighth pixel to keep diagnostics inexpensive.
     */
    private static DirectRgbSupportSummary summarizeDirectRgbSupport(
            ByteBuffer bytes,
            int width,
            int height) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();

        final int stride = 8;
        final int maxSamples =
                Math.max(1, ((width + stride - 1) / stride)
                        * ((height + stride - 1) / stride));
        float[] imbalance = new float[maxSamples];

        double sumR = 0.0;
        double sumG = 0.0;
        double sumB = 0.0;
        int lowR = 0;
        int lowG = 0;
        int lowB = 0;
        int n = 0;

        for (int y = 0; y < height; y += stride) {
            for (int x = 0; x < width; x += stride) {
                int base = (y * width + x) * 4;
                if (base + 2 >= values.limit()) continue;

                float r = Math.max(0.0f, values.get(base));
                float g = Math.max(0.0f, values.get(base + 1));
                float b = Math.max(0.0f, values.get(base + 2));

                sumR += r;
                sumG += g;
                sumB += b;

                if (r < 1.25f) lowR++;
                if (g < 1.25f) lowG++;
                if (b < 1.25f) lowB++;

                float max = Math.max(r, Math.max(g, b));
                float min = Math.min(r, Math.min(g, b));
                imbalance[n] =
                        max > 1.0e-6f ? (max - min) / max : 0.0f;
                n++;
            }
        }

        if (n <= 0) {
            return new DirectRgbSupportSummary(
                    0,0,0,1,1,1,0,0);
        }

        java.util.Arrays.sort(imbalance, 0, n);
        int p95Index = Math.min(n - 1, Math.max(0, (int)Math.floor(0.95 * (n - 1))));
        return new DirectRgbSupportSummary(
                (float)(sumR / n),
                (float)(sumG / n),
                (float)(sumB / n),
                lowR / (float)n,
                lowG / (float)n,
                lowB / (float)n,
                imbalance[p95Index],
                n);
    }

    private static SupportSummary summarizeSupport(
            ByteBuffer bytes,
            int width,
            int height,
            int frameCount) {
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer values = bytes.asFloatBuffer();

        final int gridWidth = 48;
        final int gridHeight = 36;
        float[] sums = new float[gridWidth * gridHeight];
        int[] counts = new int[gridWidth * gridHeight];
        int[] histogram = new int[256];

        double sum = 0.0;
        long count = 0L;
        int total = Math.min(values.capacity(), width * height);

        for (int index = 0; index < total; index++) {
            float value = values.get(index);
            if (!Float.isFinite(value)) value = 1.0f;
            value = Math.max(1.0f, Math.min(frameCount, value));

            int x = index % width;
            int y = index / width;
            int gx = Math.min(gridWidth - 1, x * gridWidth / Math.max(1, width));
            int gy = Math.min(gridHeight - 1, y * gridHeight / Math.max(1, height));
            int gi = gy * gridWidth + gx;
            sums[gi] += value;
            counts[gi]++;

            int bin;
            if (frameCount <= 1) {
                bin = 0;
            } else {
                bin = Math.max(
                        0,
                        Math.min(
                                255,
                                Math.round(
                                        255.0f * (value - 1.0f)
                                                / (frameCount - 1.0f))));
            }
            histogram[bin]++;
            sum += value;
            count++;
        }

        float[] grid = new float[sums.length];
        for (int i = 0; i < grid.length; i++) {
            grid[i] = counts[i] > 0 ? sums[i] / counts[i] : 1.0f;
        }

        float mean = count > 0 ? (float) (sum / count) : 1.0f;
        return new SupportSummary(
                mean,
                supportQuantile(histogram, count, frameCount, 0.10f),
                supportQuantile(histogram, count, frameCount, 0.50f),
                supportQuantile(histogram, count, frameCount, 0.90f),
                grid,
                gridWidth,
                gridHeight);
    }

    private static float supportQuantile(
            int[] histogram,
            long total,
            int frameCount,
            float q) {
        if (total <= 0L || frameCount <= 1) return 1.0f;
        long target = Math.max(1L, (long) Math.ceil(total * q));
        long cumulative = 0L;
        for (int i = 0; i < histogram.length; i++) {
            cumulative += histogram[i];
            if (cumulative >= target) {
                return 1.0f
                        + (frameCount - 1.0f)
                        * ((float) i / (histogram.length - 1.0f));
            }
        }
        return frameCount;
    }
}
