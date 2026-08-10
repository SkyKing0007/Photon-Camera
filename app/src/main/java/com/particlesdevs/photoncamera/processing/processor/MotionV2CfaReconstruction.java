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

        GLTexture referenceRaw = null;
        GLTexture referenceCfa = null;
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
        final boolean directBayer =
                parameters.cfaPattern >= 0 && parameters.cfaPattern <= 3;

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

            if (directBayer) {
                directRgbA = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directRgbB = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directSupportA = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                directSupportB = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);

                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/direct_rgb_init", true);
                glProg.setVar("rawSize", raw);
                glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                glProg.setVar("sensorClipLevel", canonicalGain);
                glProg.setVar("sensorGains", directSensorGains);
                glProg.setTextureCompute("referenceCfa", referenceCfa, false);
                glProg.setTextureCompute("outRgb", directRgbA, true);
                glProg.setTextureCompute("outSupport", directSupportA, true);
                glProg.computeAuto(raw, 1);

                currentDirectRgb = directRgbA;
                nextDirectRgb = directRgbB;
                currentDirectSupport = directSupportA;
                nextDirectSupport = directSupportB;
            }

            for (int i = 1; i < frameCount; i++) {
                ImageFrame frame = images.get(i);
                if (frame == null || frame.buffer == null) continue;

                GLTexture rawInput = null;
                GLTexture alterCfa = null;
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

                    MotionV2Alignment.Result ownedAlignment = null;
                    try {
                        long alignmentStart = System.currentTimeMillis();
                        ownedAlignment = MotionV2Alignment.align(
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
                             * IRIS_26424_DIRECT_MULTIFRAME_CFA_RGB
                             * Reuse the exact owned continuous flow, but
                             * gather real CFA sites directly into RGB.
                             */
                            glProg.setLayout(tile, tile, 1);
                            glProg.useAssetProgram(
                                    "motionv2/direct_rgb_accumulate", true);
                            glProg.setVar("rawSize", raw);
                            glProg.setVar("rawHalf", rawHalf);
                            glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                            glProg.setVar("noiseS", noiseS);
                            glProg.setVar("noiseO", noiseO);
                            glProg.setVar("maximumSupport", (float) frameCount);
                            glProg.setVar("sensorClipLevel", canonicalGain);
                            glProg.setVar("sensorGains", directSensorGains);
                            glProg.setTexture(
                                    "flowTexture",
                                    ownedAlignment.flowTexture);
                            glProg.setTextureCompute(
                                    "currentRgb", currentDirectRgb, false);
                            glProg.setTextureCompute(
                                    "currentSupport", currentDirectSupport, false);
                            glProg.setTextureCompute(
                                    "alterCfa", alterCfa, false);
                            glProg.setTextureCompute(
                                    "outRgb", nextDirectRgb, true);
                            glProg.setTextureCompute(
                                    "outSupport", nextDirectSupport, true);
                            glProg.computeAuto(raw, 1);

                            GLTexture swapDirectRgb = currentDirectRgb;
                            currentDirectRgb = nextDirectRgb;
                            nextDirectRgb = swapDirectRgb;

                            GLTexture swapDirectSupport = currentDirectSupport;
                            currentDirectSupport = nextDirectSupport;
                            nextDirectSupport = swapDirectSupport;
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
                                + ownedAlignment.lowConfidenceFraction);
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
                    if (alterCfa != null) alterCfa.close();
                    if (rawInput != null) rawInput.close();
                }
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
            GLTexture imageOutput = directBayer ? currentDirectRgb : currentMerged;
            imageOutput.BufferLoad();
            output = imageOutput.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    true);
            output.order(ByteOrder.nativeOrder());
            output.position(0);

            Log.d(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE"
                    + " sourceInternal=rgba16f"
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
                    + " perFrameRgbCandidate=false"
                    + " anisotropicKernel=true"
                    + " clippedChromaFloor=false"
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
            if (directSupportB != null) directSupportB.close();
            if (directSupportA != null) directSupportA.close();
            if (directRgbB != null) directRgbB.close();
            if (directRgbA != null) directRgbA.close();
            if (supportB != null) supportB.close();
            if (supportA != null) supportA.close();
            if (mergedB != null) mergedB.close();
            if (mergedA != null) mergedA.close();
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
