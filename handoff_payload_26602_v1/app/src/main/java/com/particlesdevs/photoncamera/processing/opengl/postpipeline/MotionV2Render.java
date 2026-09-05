package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.os.Build;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26435_EXACT_26430_BASE_LOW_FREQUENCY_TRUE_GAINMAP
 *
 * IRIS_26498_FULL_RESOLUTION_UHDR_PRIMARY_DETAIL_AUTHORITY
 * The complete 26430 SDR color/highlight/tone path remains unchanged. Ultra HDR
 * now carries a one-to-one gain sample for every primary pixel, eliminating the
 * quarter-resolution interpolation that measurably softened the UHDR rendition.
 */
public final class MotionV2Render extends Node {
    static final float OUTPUT_EXPOSURE_SCALE = 0.80f;
    /* IRIS_26602_UHDR_MASTER_SDR_PARITY
     * UHDR's pre-tone extended-linear rendition is the Motion master. Keep that exact grade
     * through guide=1.0 in SDR; only true HDR headroom above it enters the shoulder.
     */
    static final float IRIS_26602_MOTION_MASTER_SDR_TONE_START = 1.00f;
    static final float IRIS_26582_TONE_START = 0.50f;
    static final float IRIS_26582_HIGHLIGHT_TARGET = 0.97f;
    static final float IRIS_26582_CLIP_FRACTION_START = 0.002f;
    static final float IRIS_26582_CLIP_FRACTION_FULL = 0.025f;
    static final float IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE = 12.0f;
    /* IRIS_26583_PROJECTED_BROAD_AND_COMPACT_HIGHLIGHT_TAIL
     * Both broad window/cloud regions and compact sunset/specular-like highlight structures are
     * detected after the requested display gain and exact baseline 26582 tone curve. Detection is
     * max-channel aware, but rendering remains the exact same uniform-RGB scalar curve.
     */
    static final float IRIS_26583_BROAD_HIGHLIGHT_TARGET = 0.955f;
    static final float IRIS_26583_PROJECTED_BROAD_NEAR_CEILING = 0.930f;
    static final float IRIS_26583_BROAD_FRACTION_START = 0.012f;
    static final float IRIS_26583_BROAD_FRACTION_FULL = 0.060f;
    static final float IRIS_26583_BROAD_HARD_FRACTION_START = 0.0025f;
    static final float IRIS_26583_BROAD_HARD_FRACTION_FULL = 0.020f;
    static final float IRIS_26583_COMPACT_HIGHLIGHT_TARGET = 0.965f;
    static final float IRIS_26583_PROJECTED_NEAR_CEILING = 0.965f;
    static final float IRIS_26583_PROJECTED_HARD_CEILING = 0.985f;
    static final float IRIS_26583_COMPACT_FRACTION_START = 0.004f;
    static final float IRIS_26583_COMPACT_FRACTION_FULL = 0.015f;
    private static final float IRIS_26582_LOG_SHAPE = 6.0f;
    /* IRIS_26591_PHOTON_LIKE_UPPER_TAIL_SEPARATION
     * Keep the exact 26590 viewfinder/body meter curve above as a frozen control-loop model.
     * Final SDR rendering uses a less-concave monotonic shoulder so reconstructed NORMAL and
     * aligned SHORT highlight differences remain separated instead of crowding below white.
     * Tone start and the proven 0.80 output exposure remain unchanged.
     */
    static final float IRIS_26591_HIGHLIGHT_TARGET = 0.980f;
    static final float IRIS_26591_BROAD_HIGHLIGHT_TARGET = 0.975f;
    static final float IRIS_26591_COMPACT_HIGHLIGHT_TARGET = 0.985f;
    static final float IRIS_26591_CONTINUOUS_HIGHLIGHT_TARGET = 0.980f;
    static final float IRIS_26591_STRUCTURED_HIGHLIGHT_TARGET = 0.985f;
    private static final float IRIS_26591_LOG_SHAPE = 3.0f;
    /* IRIS_26592_UNBOUNDED_MONOTONIC_HIGHLIGHT_TAIL
     * sceneWhite is a scale, never a finite clipping endpoint. The nested log+tanh tail is strictly
     * increasing for every finite positive guide and asymptotically approaches display white.
     * Tanh scale 1.2020679 is chosen so the new curve exactly meets the 26591 log-shape-3 curve at
     * half of sceneWhite headroom (u=0.5), preserving the proven upper-midtone anchor while retiring
     * the x<=1 clamp that collapsed all brighter recovered values together.
     */
    private static final float IRIS_26592_TAIL_LOG_SHAPE = 3.0f;
    private static final float IRIS_26592_TANH_SCALE = 1.2020679f;
    private static final float IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f;
    /* IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS
     * Preserve the tested 26505 SDR primary exactly. Ultra HDR is a reversible
     * rendition relationship: the gain map should recover the wanted HDR signal
     * from that SDR primary rather than inheriting the SDR headroom reduction.
     * 1.00 / 0.80 = 1.25 (+0.322 EV) nominal body recovery at full HDR where
     * tone mapping is otherwise identity. Highlight gain remains content-derived.
     */
    /* IRIS_26596_UHDR_BODY_UNITY
     * Use the same presentation scalar for SDR and HDR source before gain derivation. Ordinary
     * body pixels therefore encode unity gain; only preserved pre-tone highlight headroom gains.
     */
    private static final float HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE;
    private static final int GAINMAP_DOWNSAMPLE = 1;

    public MotionV2Render() { super("", "MotionV2Render"); }
    @Override public void Compile() {}

    /* IRIS_26582_SHARED_GLOBAL_TONE_MODEL
     * Single Java authority used by both the viewfinder solver and render setup. The GLSL render
     * uses the same start/log shape/output scale; only sceneWhite is scene-adaptive.
     */
    static float iris26582BaseSceneWhite(float displayGain) {
        return Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, displayGain)));
    }

    /* IRIS_26598_MOTION_PUBLICATION_SCENE_WHITE_AUTHORITY
     * 26597 made Motion publication itself preserve an unbounded monotonic highlight tail. The
     * older adaptiveSceneWhite expansion was designed for the pre-26597 endpoint-compression
     * renderer and therefore double-reserved highlight range when reused by Motion. Motion now
     * publishes against the body/physical baseSceneWhite. Night intentionally retains its proven
     * adaptive scene-white owner because it still uses the successful 26591 publication curve.
     * Keep this as the single Java selector consumed by normal Motion render, tone-aware highlight
     * chroma prediction, and true-2x publication so those paths cannot silently diverge again.
     */
    public static float iris26598PublicationSceneWhite(Parameters parameters) {
        if (parameters == null) {
            throw new IllegalArgumentException("parameters == null");
        }
        float computedBase = iris26582BaseSceneWhite(parameters.motionV2DisplayGain);
        float baseWhite = parameters.motionV2ToneBaseSceneWhite;
        if (!Float.isFinite(baseWhite) || baseWhite < 1.0f) baseWhite = computedBase;
        baseWhite = Math.max(1.0f, Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, baseWhite));
        if (parameters.motionV2Active) return baseWhite;

        float adaptiveWhite = parameters.motionV2ToneAdaptiveSceneWhite;
        if (!Float.isFinite(adaptiveWhite) || adaptiveWhite < baseWhite) adaptiveWhite = baseWhite;
        return Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, adaptiveWhite);
    }

    static float iris26582MapHeadroom(float guide, float sceneWhite) {
        if (guide <= IRIS_26582_TONE_START) return guide;
        float whitePoint = Math.max(sceneWhite, IRIS_26582_TONE_START + 0.05f);
        float x = iris26582Clamp((guide - IRIS_26582_TONE_START)
                / Math.max(whitePoint - IRIS_26582_TONE_START, 1.0e-6f), 0.0f, 1.0f);
        float shaped = (float)(Math.log(1.0 + IRIS_26582_LOG_SHAPE * x)
                / Math.log(1.0 + IRIS_26582_LOG_SHAPE));
        float preScaleDisplayWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        return IRIS_26582_TONE_START
                + (preScaleDisplayWhite - IRIS_26582_TONE_START) * shaped;
    }

    static float iris26591MapHeadroom(float guide, float sceneWhite) {
        if (guide <= IRIS_26582_TONE_START) return guide;
        float whitePoint = Math.max(sceneWhite, IRIS_26582_TONE_START + 0.05f);
        float x = iris26582Clamp((guide - IRIS_26582_TONE_START)
                / Math.max(whitePoint - IRIS_26582_TONE_START, 1.0e-6f), 0.0f, 1.0f);
        float shaped = (float)(Math.log(1.0 + IRIS_26591_LOG_SHAPE * x)
                / Math.log(1.0 + IRIS_26591_LOG_SHAPE));
        float preScaleDisplayWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        return IRIS_26582_TONE_START
                + (preScaleDisplayWhite - IRIS_26582_TONE_START) * shaped;
    }

    static float iris26592MapHeadroom(float guide, float sceneWhite) {
        if (guide <= IRIS_26582_TONE_START) return guide;
        float whitePoint = Math.max(sceneWhite, IRIS_26582_TONE_START + 0.05f);
        float u = Math.max((guide - IRIS_26582_TONE_START)
                / Math.max(whitePoint - IRIS_26582_TONE_START, 1.0e-6f), 0.0f);
        float logCoordinate = (float)(Math.log(1.0 + IRIS_26592_TAIL_LOG_SHAPE * u)
                / Math.log(1.0 + IRIS_26592_TAIL_LOG_SHAPE));
        float shaped = (float)Math.tanh(IRIS_26592_TANH_SCALE * logCoordinate);
        float preScaleDisplayWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        return IRIS_26582_TONE_START
                + (preScaleDisplayWhite - IRIS_26582_TONE_START) * shaped;
    }

    static float iris26582AdaptiveStrength(float clippedFraction) {
        float t = iris26582Clamp((clippedFraction - IRIS_26582_CLIP_FRACTION_START)
                / Math.max(IRIS_26582_CLIP_FRACTION_FULL
                        - IRIS_26582_CLIP_FRACTION_START, 1.0e-6f), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }

    static float iris26583RequiredSceneWhite(float displayGain, float sourceGuide,
                                              float outputTarget) {
        float baseWhite = iris26582BaseSceneWhite(displayGain);
        if (!Float.isFinite(sourceGuide) || sourceGuide <= 0.0f) return baseWhite;
        float postGuide = sourceGuide * Math.max(displayGain, 1.0e-6f);
        if (postGuide <= IRIS_26582_TONE_START) return baseWhite;
        float targetPreScale = iris26582Clamp(outputTarget, 0.80f, 0.995f) / OUTPUT_EXPOSURE_SCALE;
        float preScaleWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        float targetShape = iris26582Clamp((targetPreScale - IRIS_26582_TONE_START)
                / Math.max(preScaleWhite - IRIS_26582_TONE_START, 1.0e-6f), 0.0f, 1.0f);
        float targetX = (float)((Math.exp(targetShape * Math.log(1.0 + IRIS_26582_LOG_SHAPE)) - 1.0)
                / IRIS_26582_LOG_SHAPE);
        float requiredWhite = IRIS_26582_TONE_START
                + (postGuide - IRIS_26582_TONE_START) / Math.max(targetX, 1.0e-4f);
        return Math.max(baseWhite, Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, requiredWhite));
    }

    static float iris26591RequiredSceneWhite(float displayGain, float sourceGuide,
                                              float outputTarget) {
        float baseWhite = iris26582BaseSceneWhite(displayGain);
        if (!Float.isFinite(sourceGuide) || sourceGuide <= 0.0f) return baseWhite;
        float postGuide = sourceGuide * Math.max(displayGain, 1.0e-6f);
        if (postGuide <= IRIS_26582_TONE_START) return baseWhite;
        float targetPreScale = iris26582Clamp(outputTarget, 0.80f, 0.995f) / OUTPUT_EXPOSURE_SCALE;
        float preScaleWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        float targetShape = iris26582Clamp((targetPreScale - IRIS_26582_TONE_START)
                / Math.max(preScaleWhite - IRIS_26582_TONE_START, 1.0e-6f), 0.0f, 1.0f);
        float targetX = (float)((Math.exp(targetShape * Math.log(1.0 + IRIS_26591_LOG_SHAPE)) - 1.0)
                / IRIS_26591_LOG_SHAPE);
        float requiredWhite = IRIS_26582_TONE_START
                + (postGuide - IRIS_26582_TONE_START) / Math.max(targetX, 1.0e-4f);
        return Math.max(baseWhite, Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, requiredWhite));
    }

    static float iris26591AdaptiveSceneWhite(float displayGain, float p99Guide,
                                              float clippedFraction) {
        float baseWhite = iris26582BaseSceneWhite(displayGain);
        if (!Float.isFinite(p99Guide) || p99Guide <= 0.0f) return baseWhite;
        float postP99 = p99Guide * Math.max(displayGain, 1.0e-6f);
        if (postP99 <= baseWhite) return baseWhite;
        float requiredWhite = iris26591RequiredSceneWhite(
                displayGain, p99Guide, IRIS_26591_HIGHLIGHT_TARGET);
        float strength = iris26582AdaptiveStrength(clippedFraction);
        return baseWhite + (requiredWhite - baseWhite) * strength;
    }

    static float iris26582AdaptiveSceneWhite(float displayGain, float p99Guide,
                                              float clippedFraction) {
        float baseWhite = iris26582BaseSceneWhite(displayGain);
        if (!Float.isFinite(p99Guide) || p99Guide <= 0.0f) return baseWhite;
        float postP99 = p99Guide * Math.max(displayGain, 1.0e-6f);
        if (postP99 <= baseWhite) return baseWhite;

        /* Exact 26582 broad-tail behavior retained. */
        float requiredWhite = iris26583RequiredSceneWhite(
                displayGain, p99Guide, IRIS_26582_HIGHLIGHT_TARGET);
        float strength = iris26582AdaptiveStrength(clippedFraction);
        return baseWhite + (requiredWhite - baseWhite) * strength;
    }

    private static float iris26582Clamp(float x, float lo, float hi) {
        return Math.max(lo, Math.min(hi, x));
    }

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2Render used outside Motion V2");
        }

        final GLTexture extendedLinearHdr = previousNode.WorkingTexture;

        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float mgcSourceExposureGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(mgcSourceExposureGain) || mgcSourceExposureGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid MGC source-domain exposure gain at render: " + mgcSourceExposureGain);
        }
        /* IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT
         * sceneWhite follows only the real Photon display exposure. Accepted-Short BaselineExposure
         * is source-domain restoration and must not stretch the SDR highlight shoulder.
         */
        float baseSceneWhite = basePipeline.mParameters.motionV2ToneBaseSceneWhite;
        if (!Float.isFinite(baseSceneWhite) || baseSceneWhite < 1.0f) {
            baseSceneWhite = iris26582BaseSceneWhite(postDisplaySensorWhite);
        }
        float sceneWhite = iris26598PublicationSceneWhite(basePipeline.mParameters);
        /* IRIS_26530_V1_3_FOV_AUTHORITY
         * motionV2OutputZoom is the final FOV authority. SR reconstruction scale must not divide
         * the JPEG/UHDR crop request; doing so produced the measured ~2x-wide 123x frame.
         */
        float reconstructionZoom = Math.max(1.0f,
                basePipeline.mParameters.motionV2ReconstructionZoom);
        /* IRIS_26532_20X_SR_GEOMETRY_IDENTITY
         * MGC owns the crop through 20x total. Render owns only any residual request beyond the
         * reconstruction crop, so reconstruction * residual == selected-lens local zoom exactly.
         */
        float irisOutputZoom = Math.max(1.0f,
                basePipeline.mParameters.motionV2RenderResidualZoom);
        Log.i("MotionV2Render", "IRIS_26532_FINAL_FOV_IDENTITY requestedLocal="
                + basePipeline.mParameters.motionV2OutputZoom
                + " reconstructionOwner=" + basePipeline.mParameters.motionV2ReconstructionOwner
                + " reconstructionZoom=" + reconstructionZoom
                + " renderResidual=" + irisOutputZoom
                + " product=" + (reconstructionZoom * irisOutputZoom));
                glProg.useAssetProgram("motionv2/render");
        glProg.setTexture("InputBuffer", extendedLinearHdr);
        glProg.setVar("sceneWhite", sceneWhite);
        glProg.setVar("iris26592MotionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);
        glProg.setVar("iris26602MotionMasterToneStart", IRIS_26602_MOTION_MASTER_SDR_TONE_START);
                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);
        glProg.setVar("irisOutputZoom", irisOutputZoom);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);

        PostPipeline pipeline = (PostPipeline) basePipeline;
        pipeline.motionV2GainMapBitmap = null;
        pipeline.motionV2GainMapMaxRatio = 1.0f;
        pipeline.motionV2GainMapFullHdrDisplayRatio = 1.0f;

        /* IRIS_26550_NIGHT_POST_JIN_ULTRAHDR_AUTHORITY
         * Motion keeps its exact full-resolution gain-map geometry. Night now retains only a 1/4
         * resolution pre-Jin HDR/SDR relationship from this GL owner. IrisNightUltraHdr later
         * rebases that relationship against the final post-Jin SDR before attaching JPEG_R.
         */
        final boolean iris26550Night = basePipeline.mParameters.irisNightActive;
        if ((basePipeline.mParameters.motionV2Active || iris26550Night)
                && Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            /* IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY */
            Point renderedSdrSize = new Point(WorkingTexture.mSize);
            final int gainDownsample = iris26550Night ? 4 : GAINMAP_DOWNSAMPLE;
            Point gainSize = new Point(
                    Math.max(1, (renderedSdrSize.x + gainDownsample - 1) / gainDownsample),
                    Math.max(1, (renderedSdrSize.y + gainDownsample - 1) / gainDownsample));

            /* Preserve the pre-26515 UHDR capacity exactly. The Short source-domain
             * headroom still participates in max gain even though it no longer changes sceneWhite.
             */
            float maxGainRatio = iris26550Night
                    ? Math.max(2.0f, Math.min(2.5f, HDR_EXPOSURE_SCALE * postDisplaySensorWhite
                            * mgcSourceExposureGain))
                    : IRIS_26592_MOTION_UHDR_MAX_RATIO;

            GLTexture gainTexture = null;
            try {
                gainTexture = new GLTexture(
                        gainSize,
                        new GLFormat(GLFormat.DataType.SIMPLE_8, 1),
                        null,
                        GL_LINEAR,
                        GL_CLAMP_TO_EDGE);

                glProg.useAssetProgram("motionv2/gainmap");
                glProg.setTexture("HdrBuffer", extendedLinearHdr);
                glProg.setTexture("SdrBuffer", WorkingTexture);
                glProg.setVar("gainMapSize", gainSize);
                glProg.setVar("hdrExposureScale", HDR_EXPOSURE_SCALE);
                glProg.setVar("maxGainRatio", maxGainRatio);
                glProg.setVar("irisOutputZoom", irisOutputZoom);
                glProg.drawBlocks(gainTexture);

                gainTexture.BufferLoad();
                GLFormat readFormat =
                        new GLFormat(GLFormat.DataType.SIMPLE_8, 1);
                ByteBuffer rgba =
                        gainTexture.textureBuffer(readFormat, true);
                rgba.position(0);

                int pixels = gainSize.x * gainSize.y;
                ByteBuffer alpha = ByteBuffer.allocateDirect(pixels);
                int nonUnity = 0;
                int peakCode = 0;
                for (int i = 0; i < pixels; i++) {
                    int code = rgba.get(i) & 0xff;
                    if (code > 0) nonUnity++;
                    peakCode = Math.max(peakCode, code);
                    alpha.put((byte)code);
                }
                alpha.position(0);

                /*
                 * Per-pixel gain-map provenance, not just a global percentage.
                 * 12x8 nearest samples are written as hexadecimal gain codes.
                 * Also report horizontal/vertical roughness so a smooth floor
                 * or ceiling-light region cannot hide behind one global mean.
                 */
                /* IRIS_26513_GAINMAP_DIAGNOSTIC_DECIMATION
                 * Keep the actual full-resolution gain map byte-for-byte unchanged.
                 * Only the diagnostic roughness measurement is reduced from a second
                 * 12.6 MP full-image walk to 12x8 sampled local pixel neighborhoods.
                 */
                StringBuilder grid = new StringBuilder();
                final int gridW = 12;
                final int gridH = 8;
                long roughSum = 0L;
                long roughCount = 0L;
                for (int gy = 0; gy < gridH; gy++) {
                    if (gy > 0) grid.append('/');
                    int sy = Math.min(gainSize.y - 1,
                            (int)(((gy + 0.5f) * gainSize.y) / gridH));
                    for (int gx = 0; gx < gridW; gx++) {
                        int sx = Math.min(gainSize.x - 1,
                                (int)(((gx + 0.5f) * gainSize.x) / gridW));
                        int idx = sy * gainSize.x + sx;
                        int code = rgba.get(idx) & 0xff;
                        if (code < 16) grid.append('0');
                        grid.append(Integer.toHexString(code));
                        if (sx + 1 < gainSize.x) {
                            int right = rgba.get(idx + 1) & 0xff;
                            roughSum += Math.abs(code - right);
                            roughCount++;
                        }
                        if (sy + 1 < gainSize.y) {
                            int down = rgba.get(idx + gainSize.x) & 0xff;
                            roughSum += Math.abs(code - down);
                            roughCount++;
                        }
                    }
                }
                float meanNeighborDelta = roughCount > 0
                        ? roughSum / (float)roughCount
                        : 0.0f;

                Bitmap gainMap = Bitmap.createBitmap(
                        gainSize.x,
                        gainSize.y,
                        Bitmap.Config.ALPHA_8);
                gainMap.copyPixelsFromBuffer(alpha);

                float actualPeakContentRatio = (float)Math.pow(
                        Math.max(maxGainRatio, 1.001f), peakCode / 255.0f);
                float fullHdrDisplayRatio = Math.max(1.02f, actualPeakContentRatio);
                pipeline.motionV2GainMapBitmap = gainMap;
                pipeline.motionV2GainMapMaxRatio = maxGainRatio;
                pipeline.motionV2GainMapFullHdrDisplayRatio = fullHdrDisplayRatio;
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26596_UHDR_GAINMAP_CONTENT",
                            "ratioEncodingMax=" + maxGainRatio
                                    + " peakCode=" + peakCode
                                    + " actualPeakContentRatio=" + actualPeakContentRatio
                                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio
                                    + " bodyGainUnity=true"
                                    + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE
                                    + " hdrExposureScale=" + HDR_EXPOSURE_SCALE);
                } catch (Throwable ignored) {}

                Log.d(Name, "IRIS_26470_UHDR_GAINMAP_GEOMETRY"
                        + " renderedSdr=" + renderedSdrSize.x + "x" + renderedSdrSize.y
                        + " gainMap=" + gainSize.x + "x" + gainSize.y
                        + " downsample=" + gainDownsample
                        + " authority=actualRenderedSdrTexture"
                        + " pipeline=" + (iris26550Night ? "NIGHT_PRE_JIN_DETACHED" : "MOTION"));
                Log.d(Name, "IRIS_26436_V2_GAINMAP"
                        + " size=" + gainSize.x + "x" + gainSize.y
                        + " maxRatio=" + maxGainRatio
                        + " nonUnityFraction="
                        + (pixels > 0 ? nonUnity / (float)pixels : 0.0f)
                        + " peakCode=" + peakCode
                        + " meanNeighborDeltaCode=" + meanNeighborDelta
                        + " roughnessSampling=12x8_local_neighbors"
                        + " fullImageRoughnessScan=false"
                        + " provenance=actualGainMapBeforeJpegAttach"
                        + " grid12x8=" + grid
                        + " source=extendedLinearPreTone"
                        + " fullResolutionGainMap=" + (!iris26550Night)
                        + " downsample=" + gainDownsample
                        + " widthFraction=" + (1.0f / gainDownsample)
                        + " heightFraction=" + (1.0f / gainDownsample)
                        + " nightPostJinRebaseRequired=" + iris26550Night
                        + " quotientOffset=0.015625"
                        + " standardLogGainEncoding=true"
                        + " gainMapResamplingRequired=false"
                        + " reconstructionDetailAuthorityOwner="
                        + basePipeline.mParameters.motionV2ReconstructionOwner
                        + " pointDecimation=false"
                        + " postAliasSpikeRepair=false"
                        + " midtoneGainUnity=true"
                        + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE
                        + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE
                        + " nominalBodyRecoveryRatio="
                            + (HDR_EXPOSURE_SCALE / OUTPUT_EXPOSURE_SCALE)
                        + " IRIS_26506_HDR_BODY_RECOVERY_GAINMAP=true");
            } finally {
                if (gainTexture != null) {
                    try { gainTexture.close(); } catch (Throwable ignored) {}
                }
            }
        }

        glProg.closed = true;

        if (basePipeline.mParameters.motionV2Active) {
            Log.i(Name, "IRIS_26602_SDR_UHDR_MASTER_PARITY"
                    + " master=extendedLinearPreTone"
                    + " motionToneStart=" + IRIS_26602_MOTION_MASTER_SDR_TONE_START
                    + " bodyGuideMax=1.0"
                    + " bodyOutputMax=" + OUTPUT_EXPOSURE_SCALE
                    + " bodyGainUnity=true"
                    + " sameColor=true sameBlack=true sameMidtones=true sameContrast=true"
                    + " differenceOnlyAboveBody=HDR_HEADROOM"
                    + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE
                    + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE
                    + " oneMasterRendition=true");
        }

        Log.d(Name, "IRIS_26436_V2_RENDER"
                + " canonicalSignalAlreadyApplied=true"
                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " mgcSourceExposureGain=" + mgcSourceExposureGain
                + " sceneWhite=" + sceneWhite
                + " baseSceneWhite=" + baseSceneWhite
                + " adaptiveSceneWhite=" + basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite
                + " publicationSceneWhiteSource="
                    + (basePipeline.mParameters.motionV2Active ? "BASE_26598_MOTION" : "ADAPTIVE_26591_NIGHT")
                + " IRIS_26598_SEMANTIC_AUTHORITY=true"
                + " toneP95Guide=" + basePipeline.mParameters.motionV2ToneP95Guide
                + " toneP99Guide=" + basePipeline.mParameters.motionV2ToneP99Guide
                + " toneP995Guide=" + basePipeline.mParameters.motionV2ToneP995Guide
                + " toneP998Guide=" + basePipeline.mParameters.motionV2ToneP998Guide
                + " legacyPredictedClipFraction=" + basePipeline.mParameters.motionV2TonePredictedClipFraction
                + " projectedBroadNearCeilingFraction=" + basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction
                + " projectedNearCeilingFraction=" + basePipeline.mParameters.motionV2ToneProjectedNearCeilingFraction
                + " projectedHardCeilingFraction=" + basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction
                + " projectedBroadTailStrength=" + basePipeline.mParameters.motionV2ToneProjectedBroadTailStrength
                + " compactTailStrength=" + basePipeline.mParameters.motionV2ToneCompactTailStrength
                + " adaptiveStrength=" + basePipeline.mParameters.motionV2ToneAdaptiveStrength
                + " legacyHighlightTarget=" + IRIS_26582_HIGHLIGHT_TARGET
                + " broadHighlightTarget=" + IRIS_26583_BROAD_HIGHLIGHT_TARGET
                + " compactHighlightTarget=" + IRIS_26583_COMPACT_HIGHLIGHT_TARGET
                + " iris26591FinalLogShape=" + IRIS_26591_LOG_SHAPE
                + " iris26592MotionUnboundedTail=" + basePipeline.mParameters.motionV2Active
                + " iris26592TanhScale=" + IRIS_26592_TANH_SCALE
                + " iris26591FinalTargets=" + IRIS_26591_HIGHLIGHT_TARGET + ","
                    + IRIS_26591_BROAD_HIGHLIGHT_TARGET + ","
                    + IRIS_26591_COMPACT_HIGHLIGHT_TARGET + ","
                    + IRIS_26591_CONTINUOUS_HIGHLIGHT_TARGET + ","
                    + IRIS_26591_STRUCTURED_HIGHLIGHT_TARGET
                + " IRIS_26583_PROJECTED_BROAD_AND_COMPACT_HIGHLIGHT_TAIL=true"
                + " IRIS_26582_SCENE_ADAPTIVE_GLOBAL_TONE=true"
                + " IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT=true"
                                + " toneCurve26430ExactBase=true"
                + " outputExposureScale=" + OUTPUT_EXPOSURE_SCALE
                + " outputExposureEv=-0.321928"
                + " hdrTargetUsesSameScale=true"
                + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE
                + " nominalHdrBodyRecoveryRatio="
                    + (HDR_EXPOSURE_SCALE / OUTPUT_EXPOSURE_SCALE)
                + " IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS=true"
                + " syntheticBitmapGainMap=false"
                + " irisOutputZoom=" + irisOutputZoom
                + " nativeOutputDimensionsPreserved=true"
                + " localTone=false"
                + " sharpening=false");
    }
}
