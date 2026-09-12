package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.os.Build;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
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
    /* IRIS_26604_SINGLE_TONE_OWNER
     * displayGain is a brightness target, never a separate texture multiplier. Preserve 26603's
     * body brightness exactly through the proven 26582 final-domain tone start (0.50*0.80=0.40),
     * then use one C1 monotonic rational shoulder. The 26603 outdoor sample therefore keeps its
     * P50 (~144/255) while P95 is moved away from the near-white plateau so real cloud/curtain
     * structure remains visible. The same equation is mirrored by 1x GLSL, solver prediction,
     * adaptive-color safety prediction and true-2x CPU/GPU publication.
     */
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
    /* IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP
     * Motion UHDR keeps the completed SDR as the exact primary. Its HDR rendition is a scalar
     * luminance quotient in matched linear light, anchored at the existing 0.65 upper-tone entry.
     * There is no fixed body boost and no nominal-white discontinuity. */
    private static final float IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE = 0.65f;
    /* IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS
     * Preserve the tested 26505 SDR primary exactly. Ultra HDR is a reversible
     * rendition relationship: the gain map should recover the wanted HDR signal
     * from that SDR primary rather than inheriting the SDR headroom reduction.
     * 1.00 / 0.80 = 1.25 (+0.322 EV) nominal body recovery at full HDR where
     * tone mapping is otherwise identity. Highlight gain remains content-derived.
     */
    /* IRIS_26604_UHDR_MASTER_FROM_SCENE_SOURCE
     * The scene-referred master is never destructively display-multiplied. Gain derivation applies
     * the same brightness target and 0.80 presentation scale only when evaluating HDR display
     * luminance, while SDR uses the canonical compressed rendition. This intentionally permits a
     * broad non-unity gain map where SDR compression preserves highlight structure.
     */
    private static final float HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE;
    private static final int GAINMAP_DOWNSAMPLE = 1;

    /* IRIS_26621_NEW_SIMPLIFIED_PRESENTATION_OWNER
     * Motion keeps one global exposure request: motionV2DisplayGain * OUTPUT_EXPOSURE_SCALE.
     * The global tone map preserves the successful 26614 black/body slope and 0.95 source-white
     * anchor, but blends that cubic 50/50 with a rational shoulder so the complete source-body
     * derivative cannot collapse toward zero. A true fast Local-Laplacian then operates on the
     * globally mapped scalar log-luminance with alpha=1 (no detail amplification). */
    private static final int IRIS_26621_LAPLACIAN_LEVELS = 7;
    private static final int IRIS_26621_REFERENCE_COUNT = 12;
    private static final float IRIS_26621_REFERENCE_MIN_LOG = -6.0f;
    private static final float IRIS_26621_REFERENCE_MAX_LOG = 0.0f;
    private static final float IRIS_26621_DETAIL_SIGMA_EV = 0.35f;
    private static final float IRIS_26621_EDGE_SLOPE = 0.94f;
    public static final float IRIS_26621_SDR_WHITE_ANCHOR = 0.95f;
    public static final float IRIS_26623_UPPER_TONE_START = 0.65f;
    public static final float IRIS_26623_SPARSE_WHITE_ANCHOR = 0.925f;
    public static final float IRIS_26623_BROAD_WHITE_ANCHOR = 0.885f;
    public static final float IRIS_26623_SPARSE_WHITE_SLOPE = 0.270f;
    public static final float IRIS_26623_BROAD_WHITE_SLOPE = 0.200f;
    private static final float IRIS_26626_SOURCE_PRESERVATION_MAX = 0.30f;

    static float iris26621MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain) {
        float x = Math.max(sourceGuide, 0.0f);
        float requestedFinalGain = Math.max(brightnessTargetGain, 1.0e-6f)
                * OUTPUT_EXPOSURE_SCALE;
        float whiteAnchor = Math.min(IRIS_26621_SDR_WHITE_ANCHOR, requestedFinalGain);
        float bodyGain = requestedFinalGain;
        if (requestedFinalGain > whiteAnchor) {
            bodyGain = Math.min(requestedFinalGain, 4.0f * whiteAnchor - 1.0e-4f);
        }
        float safeWhite = Math.max(whiteAnchor, 1.0e-6f);
        float ratio = Math.max(bodyGain / safeWhite - 1.0f, 0.0f);
        if (x <= 1.0f) {
            float oneMinus = 1.0f - x;
            float cubic = whiteAnchor * x
                    + (bodyGain - whiteAnchor) * x * oneMinus * oneMinus;
            float rational = bodyGain * x / (1.0f + ratio * x);
            return 0.5f * (cubic + rational);
        }
        float rationalSlopeAtWhite = bodyGain
                / ((1.0f + ratio) * (1.0f + ratio));
        float bodySlopeAtWhite = 0.5f * (whiteAnchor + rationalSlopeAtWhite);
        float reserve = Math.max(1.0f - whiteAnchor, 0.0f);
        if (reserve <= 1.0e-6f) return whiteAnchor;
        float tailScale = reserve / Math.max(bodySlopeAtWhite, 1.0e-6f);
        float excess = x - 1.0f;
        return whiteAnchor + reserve * excess / (excess + tailScale);
    }

    static float iris26623HighlightPressure(float broadNearFraction, float hardFraction,
                                                float baseSceneWhite, float adaptiveSceneWhite) {
        float broad = iris26623Smoothstep(0.015f, 0.060f, iris26582Clamp(broadNearFraction, 0.0f, 1.0f));
        float hard = iris26623Smoothstep(0.010f, 0.050f, iris26582Clamp(hardFraction, 0.0f, 1.0f));
        float baseWhite = Math.max(baseSceneWhite, 1.0f);
        float adaptiveWhite = Math.max(adaptiveSceneWhite, baseWhite);
        float span = Math.max(adaptiveWhite / baseWhite - 1.0f, 0.0f);
        float spanPressure = iris26623Smoothstep(0.08f, 0.35f, span);
        return iris26582Clamp(Math.max(0.70f * broad + 0.30f * spanPressure, 0.75f * hard), 0.0f, 1.0f);
    }

    private static float iris26623Smoothstep(float edge0, float edge1, float x) {
        float t = iris26582Clamp((x - edge0) / Math.max(edge1 - edge0, 1.0e-6f), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }

    /* IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE_REFERENCE
     * Java reference for validation/telemetry. The viewfinder meter deliberately keeps the exact
     * 26621 body solver; final Motion presentation uses this adaptive upper-tone equation only
     * after displayGain and highlight-population statistics are frozen. */
    static float iris26623MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain,
                                                  float broadNearFraction, float hardFraction,
                                                  float baseSceneWhite, float adaptiveSceneWhite) {
        float x = Math.max(sourceGuide, 0.0f);
        float legacy = iris26621MapMotionSdrFinalGuide(x, brightnessTargetGain);
        float requested = Math.max(brightnessTargetGain, 1.0e-6f) * OUTPUT_EXPOSURE_SCALE;
        float adaptiveEnable = iris26623Smoothstep(1.05f, 1.25f, requested);
        if (adaptiveEnable <= 1.0e-7f || x <= IRIS_26623_UPPER_TONE_START) return legacy;

        float pressure = iris26623HighlightPressure(broadNearFraction, hardFraction,
                baseSceneWhite, adaptiveSceneWhite);
        float targetWhite = IRIS_26623_SPARSE_WHITE_ANCHOR
                + (IRIS_26623_BROAD_WHITE_ANCHOR - IRIS_26623_SPARSE_WHITE_ANCHOR) * pressure;
        float targetSlope = IRIS_26623_SPARSE_WHITE_SLOPE
                + (IRIS_26623_BROAD_WHITE_SLOPE - IRIS_26623_SPARSE_WHITE_SLOPE) * pressure;

        float oldWhiteAnchor = Math.min(IRIS_26621_SDR_WHITE_ANCHOR, requested);
        float bodyGain = requested;
        if (requested > oldWhiteAnchor) bodyGain = Math.min(requested, 4.0f * oldWhiteAnchor - 1.0e-4f);
        float safeWhite = Math.max(oldWhiteAnchor, 1.0e-6f);
        float ratio = Math.max(bodyGain / safeWhite - 1.0f, 0.0f);
        float startX = IRIS_26623_UPPER_TONE_START;
        float oneMinus = 1.0f - startX;
        float cubic = oldWhiteAnchor * startX
                + (bodyGain - oldWhiteAnchor) * startX * oneMinus * oneMinus;
        float rational = bodyGain * startX / (1.0f + ratio * startX);
        float startValue = 0.5f * (cubic + rational);
        float cubicDerivative = oldWhiteAnchor
                + (bodyGain - oldWhiteAnchor) * oneMinus * (1.0f - 3.0f * startX);
        float rationalDerivative = bodyGain / ((1.0f + ratio * startX) * (1.0f + ratio * startX));
        float startSlope = 0.5f * (cubicDerivative + rationalDerivative);
        float width = 1.0f - startX;
        float secant = (targetWhite - startValue) / width;
        if (secant <= 1.0e-6f) return legacy;
        float m0 = Math.max(startSlope, 0.0f);
        float m1 = Math.max(targetSlope, 0.0f);
        float a = m0 / secant;
        float b = m1 / secant;
        float norm2 = a * a + b * b;
        if (norm2 > 9.0f) {
            float limiter = 3.0f / (float)Math.sqrt(norm2);
            m0 *= limiter;
            m1 *= limiter;
        }

        float candidate;
        if (x <= 1.0f) {
            float t = iris26582Clamp((x - startX) / width, 0.0f, 1.0f);
            float t2 = t * t;
            float t3 = t2 * t;
            candidate = (2.0f * t3 - 3.0f * t2 + 1.0f) * startValue
                    + (t3 - 2.0f * t2 + t) * width * m0
                    + (-2.0f * t3 + 3.0f * t2) * targetWhite
                    + (t3 - t2) * width * m1;
        } else {
            float reserve = Math.max(1.0f - targetWhite, 0.0f);
            float tailScale = reserve / Math.max(m1, 1.0e-6f);
            float excess = x - 1.0f;
            candidate = targetWhite + reserve * excess / (excess + tailScale);
        }
        return legacy + (candidate - legacy) * adaptiveEnable;
    }

    static float iris26614MapHdrTargetLuma(float hdrBase) {
        return hdrBase;
    }

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

    private void iris26623SetAdaptiveUpperToneUniforms() {
        glProg.setVar("iris26623ToneBroadNearFraction",
                basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction);
        glProg.setVar("iris26623ToneHardFraction",
                basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction);
        glProg.setVar("iris26623ToneBaseSceneWhite",
                basePipeline.mParameters.motionV2ToneBaseSceneWhite);
        glProg.setVar("iris26623ToneAdaptiveSceneWhite",
                basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite);
    }

    /* IRIS_26626_BOUNDED_SOURCE_DOMAIN_LOCAL_LAPLACIAN_REFERENCE
     * 26625 remains the canonical baseline. A second transient Local-Laplacian pass uses the
     * original source-domain guide and source references, but maps every reference center through
     * the unchanged 26623 tone owner. The final per-pixel blend is capped by the exact pre-code
     * monotonicity/halo sweep; no scene semantic detector or alternate RGB owner is introduced. */
    private float iris26626SourcePreservationStrength() {
        final float requested = Math.max(basePipeline.mParameters.motionV2DisplayGain, 1.0e-6f)
                * OUTPUT_EXPOSURE_SCALE;
        final float adaptiveEnable = iris26623Smoothstep(1.05f, 1.25f, requested);
        final float pressure = iris26623HighlightPressure(
                basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction,
                basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction,
                basePipeline.mParameters.motionV2ToneBaseSceneWhite,
                basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite);
        return iris26582Clamp(
                IRIS_26626_SOURCE_PRESERVATION_MAX * adaptiveEnable * pressure,
                0.0f, IRIS_26626_SOURCE_PRESERVATION_MAX);
    }

    private float iris26626MappedReferenceLog(float sourceReferenceLog) {
        final float sourceGuide = (float)Math.pow(2.0, sourceReferenceLog);
        final float mappedGuide = iris26623MapMotionSdrFinalGuide(
                sourceGuide,
                basePipeline.mParameters.motionV2DisplayGain,
                basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction,
                basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction,
                basePipeline.mParameters.motionV2ToneBaseSceneWhite,
                basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite);
        return (float)(Math.log(Math.max(mappedGuide, 0.000244140625f)) / Math.log(2.0));
    }

    private void iris26621ClearLocalToneState() {
        basePipeline.mParameters.motionV2LocalToneLogMap = null;
        basePipeline.mParameters.motionV2LocalToneLogWidth = 0;
        basePipeline.mParameters.motionV2LocalToneLogHeight = 0;
        basePipeline.mParameters.motionV2LocalToneLogSourceWidth = 0;
        basePipeline.mParameters.motionV2LocalToneLogSourceHeight = 0;
    }

    private GLTexture iris26626ApplyBoundedSourceDomainPreservation(
            GLTexture source, GLTexture currentTone, GLFormat scalar, float preservationStrength) {
        if (preservationStrength <= 1.0e-7f) return currentTone;

        final GLTexture[] sourceGuide = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS];
        final GLTexture[] sourceBands = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS - 1];
        GLTexture coarsestLinear = null;
        GLTexture reconstruction = null;
        GLTexture delta = null;
        GLTexture blended = null;
        boolean keepBlended = false;
        try {
            sourceGuide[0] = new GLTexture(
                    new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
            glProg.setTexture("SourceLinear", source);
            glProg.setVar("iris26626Mode", 1);
            glProg.drawBlocks(sourceGuide[0]);

            for (int level = 1; level < IRIS_26621_LAPLACIAN_LEVELS; level++) {
                Point previous = sourceGuide[level - 1].mSize;
                Point nextSize = new Point(
                        Math.max(1, (previous.x + 1) / 2),
                        Math.max(1, (previous.y + 1) / 2));
                sourceGuide[level] = new GLTexture(
                        nextSize, scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                glProg.useAssetProgram("motionv2/local_laplacian_downsample_26621");
                glProg.setTexture("InputBuffer", sourceGuide[level - 1]);
                glProg.drawBlocks(sourceGuide[level]);
            }

            final float referenceStep =
                    (IRIS_26621_REFERENCE_MAX_LOG - IRIS_26621_REFERENCE_MIN_LOG)
                            / (IRIS_26621_REFERENCE_COUNT - 1.0f);
            for (int reference = 0; reference < IRIS_26621_REFERENCE_COUNT; reference++) {
                final float sourceReferenceLog =
                        IRIS_26621_REFERENCE_MIN_LOG + reference * referenceStep;
                final float mappedReferenceLog = iris26626MappedReferenceLog(sourceReferenceLog);
                final GLTexture[] remap = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS];
                try {
                    remap[0] = new GLTexture(
                            new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                    glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
                    glProg.setTexture("SourceLinear", source);
                    glProg.setVar("sourceReferenceLog", sourceReferenceLog);
                    glProg.setVar("mappedReferenceLog", mappedReferenceLog);
                    glProg.setVar("sigmaEv", IRIS_26621_DETAIL_SIGMA_EV);
                    glProg.setVar("edgeSlope", IRIS_26621_EDGE_SLOPE);
                    glProg.setVar("iris26626Mode", 2);
                    glProg.drawBlocks(remap[0]);

                    for (int level = 1; level < IRIS_26621_LAPLACIAN_LEVELS; level++) {
                        remap[level] = new GLTexture(
                                new Point(sourceGuide[level].mSize), scalar, null,
                                GL_LINEAR, GL_CLAMP_TO_EDGE);
                        glProg.useAssetProgram("motionv2/local_laplacian_downsample_26621");
                        glProg.setTexture("InputBuffer", remap[level - 1]);
                        glProg.drawBlocks(remap[level]);
                    }

                    for (int level = 0; level < IRIS_26621_LAPLACIAN_LEVELS - 1; level++) {
                        GLTexture next = new GLTexture(
                                new Point(sourceGuide[level].mSize), scalar, null,
                                GL_LINEAR, GL_CLAMP_TO_EDGE);
                        glProg.useAssetProgram("motionv2/local_laplacian_accumulate_26621");
                        glProg.setTexture("Accumulator",
                                sourceBands[level] != null ? sourceBands[level] : remap[level]);
                        glProg.setTexture("RemapFine", remap[level]);
                        glProg.setTexture("RemapCoarse", remap[level + 1]);
                        glProg.setTexture("GuideLevel", sourceGuide[level]);
                        glProg.setVar("referenceLog", sourceReferenceLog);
                        glProg.setVar("referenceStep", referenceStep);
                        glProg.setVar("referenceMin", IRIS_26621_REFERENCE_MIN_LOG);
                        glProg.setVar("referenceMax", IRIS_26621_REFERENCE_MAX_LOG);
                        glProg.setVar("firstReference", reference == 0 ? 1 : 0);
                        glProg.drawBlocks(next);
                        if (sourceBands[level] != null) {
                            try { sourceBands[level].close(); } catch (Throwable ignored) {}
                        }
                        sourceBands[level] = next;
                    }
                } finally {
                    for (GLTexture texture : remap) {
                        if (texture != null) {
                            try { texture.close(); } catch (Throwable ignored) {}
                        }
                    }
                }
            }

            coarsestLinear = new GLTexture(
                    new Point(sourceGuide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize),
                    scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
            glProg.setTexture("SourceGuideLog", sourceGuide[IRIS_26621_LAPLACIAN_LEVELS - 1]);
            glProg.setVar("iris26626Mode", 3);
            glProg.drawBlocks(coarsestLinear);

            reconstruction = new GLTexture(
                    new Point(coarsestLinear.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_global_log_26621");
            glProg.setTexture("InputBuffer", coarsestLinear);
            glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);
            glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);
            iris26623SetAdaptiveUpperToneUniforms();
            glProg.drawBlocks(reconstruction);
            try { coarsestLinear.close(); } catch (Throwable ignored) {}
            coarsestLinear = null;

            for (int level = IRIS_26621_LAPLACIAN_LEVELS - 2; level >= 1; level--) {
                GLTexture next = new GLTexture(
                        new Point(sourceGuide[level].mSize), scalar, null,
                        GL_LINEAR, GL_CLAMP_TO_EDGE);
                glProg.useAssetProgram("motionv2/local_laplacian_reconstruct_26621");
                glProg.setTexture("LocalBand", sourceBands[level]);
                glProg.setTexture("CoarseReconstruction", reconstruction);
                glProg.drawBlocks(next);
                try { reconstruction.close(); } catch (Throwable ignored) {}
                reconstruction = next;
            }

            delta = new GLTexture(
                    new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
            glProg.setTexture("LocalBand", sourceBands[0]);
            glProg.setTexture("CoarseReconstruction", reconstruction);
            glProg.setTexture("CurrentToneLog", currentTone);
            glProg.setVar("iris26626Mode", 4);
            glProg.drawBlocks(delta);
            try { reconstruction.close(); } catch (Throwable ignored) {}
            reconstruction = null;

            blended = new GLTexture(
                    new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
            glProg.setTexture("SourceLinear", source);
            glProg.setTexture("CurrentToneLog", currentTone);
            glProg.setTexture("DeltaLog", delta);
            glProg.setVar("iris26626PreservationStrength", preservationStrength);
            glProg.setVar("iris26626Mode", 5);
            glProg.drawBlocks(blended);

            Log.i(Name, "IRIS_26626_BOUNDED_SOURCE_DOMAIN_LOCAL_LAPLACIAN"
                    + " active=true"
                    + " preservationStrength=" + preservationStrength
                    + " preservationMax=" + IRIS_26626_SOURCE_PRESERVATION_MAX
                    + " lowerBodyGate=" + IRIS_26623_UPPER_TONE_START + "..0.72"
                    + " baseline=EXACT_26625_RECONSTRUCTION"
                    + " sourceReferences=" + IRIS_26621_REFERENCE_COUNT
                    + " sourceLevels=" + IRIS_26621_LAPLACIAN_LEVELS
                    + " true2xSharedFinalMap="
                    + basePipeline.mParameters.motionV2SuperResOutputEnabled);
            keepBlended = true;
            return blended;
        } finally {
            if (coarsestLinear != null) {
                try { coarsestLinear.close(); } catch (Throwable ignored) {}
            }
            if (reconstruction != null) {
                try { reconstruction.close(); } catch (Throwable ignored) {}
            }
            if (delta != null) {
                try { delta.close(); } catch (Throwable ignored) {}
            }
            for (GLTexture texture : sourceBands) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            for (GLTexture texture : sourceGuide) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            if (!keepBlended && blended != null) {
                try { blended.close(); } catch (Throwable ignored) {}
            }
        }
    }

    private GLTexture iris26621BuildLocalLaplacianTone(GLTexture source) {
        iris26621ClearLocalToneState();
        if (!basePipeline.mParameters.motionV2Active) return null;
        if (source == null || source.mSize == null || source.mSize.x <= 0 || source.mSize.y <= 0) {
            throw new IllegalStateException("IRIS_26621 invalid Local Laplacian source");
        }

        final GLFormat scalar = new GLFormat(GLFormat.DataType.FLOAT_16, 1);
        final GLTexture[] guide = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS];
        final GLTexture[] bands = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS - 1];
        GLTexture finalTone = null;
        boolean keepFinal = false;
        try {
            guide[0] = new GLTexture(new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/local_laplacian_global_log_26621");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);
            glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);
            iris26623SetAdaptiveUpperToneUniforms();
            glProg.drawBlocks(guide[0]);

            for (int level = 1; level < IRIS_26621_LAPLACIAN_LEVELS; level++) {
                Point previous = guide[level - 1].mSize;
                Point nextSize = new Point(
                        Math.max(1, (previous.x + 1) / 2),
                        Math.max(1, (previous.y + 1) / 2));
                guide[level] = new GLTexture(nextSize, scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                glProg.useAssetProgram("motionv2/local_laplacian_downsample_26621");
                glProg.setTexture("InputBuffer", guide[level - 1]);
                glProg.drawBlocks(guide[level]);
            }

            final float referenceStep = (IRIS_26621_REFERENCE_MAX_LOG - IRIS_26621_REFERENCE_MIN_LOG)
                    / (IRIS_26621_REFERENCE_COUNT - 1.0f);
            for (int reference = 0; reference < IRIS_26621_REFERENCE_COUNT; reference++) {
                final float referenceLog = IRIS_26621_REFERENCE_MIN_LOG + reference * referenceStep;
                final GLTexture[] remap = new GLTexture[IRIS_26621_LAPLACIAN_LEVELS];
                try {
                    remap[0] = new GLTexture(new Point(source.mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                    glProg.useAssetProgram("motionv2/local_laplacian_remap_26621");
                    glProg.setTexture("GlobalMappedLog", guide[0]);
                    glProg.setVar("referenceLog", referenceLog);
                    glProg.setVar("sigmaEv", IRIS_26621_DETAIL_SIGMA_EV);
                    glProg.setVar("edgeSlope", IRIS_26621_EDGE_SLOPE);
                    glProg.setVar("iris26626Mode", 0);
                    glProg.drawBlocks(remap[0]);

                    for (int level = 1; level < IRIS_26621_LAPLACIAN_LEVELS; level++) {
                        remap[level] = new GLTexture(new Point(guide[level].mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                        glProg.useAssetProgram("motionv2/local_laplacian_downsample_26621");
                        glProg.setTexture("InputBuffer", remap[level - 1]);
                        glProg.drawBlocks(remap[level]);
                    }

                    for (int level = 0; level < IRIS_26621_LAPLACIAN_LEVELS - 1; level++) {
                        GLTexture next = new GLTexture(new Point(guide[level].mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                        glProg.useAssetProgram("motionv2/local_laplacian_accumulate_26621");
                        glProg.setTexture("Accumulator", bands[level] != null ? bands[level] : remap[level]);
                        glProg.setTexture("RemapFine", remap[level]);
                        glProg.setTexture("RemapCoarse", remap[level + 1]);
                        glProg.setTexture("GuideLevel", guide[level]);
                        glProg.setVar("referenceLog", referenceLog);
                        glProg.setVar("referenceStep", referenceStep);
                        glProg.setVar("referenceMin", IRIS_26621_REFERENCE_MIN_LOG);
                        glProg.setVar("referenceMax", IRIS_26621_REFERENCE_MAX_LOG);
                        glProg.setVar("firstReference", reference == 0 ? 1 : 0);
                        glProg.drawBlocks(next);
                        if (bands[level] != null) {
                            try { bands[level].close(); } catch (Throwable ignored) {}
                        }
                        bands[level] = next;
                    }
                } finally {
                    for (GLTexture texture : remap) {
                        if (texture != null) {
                            try { texture.close(); } catch (Throwable ignored) {}
                        }
                    }
                }
            }

            GLTexture reconstruction = guide[IRIS_26621_LAPLACIAN_LEVELS - 1];
            boolean reconstructionOwned = false;
            for (int level = IRIS_26621_LAPLACIAN_LEVELS - 2; level >= 0; level--) {
                GLTexture next = new GLTexture(new Point(guide[level].mSize), scalar, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                glProg.useAssetProgram("motionv2/local_laplacian_reconstruct_26621");
                glProg.setTexture("LocalBand", bands[level]);
                glProg.setTexture("CoarseReconstruction", reconstruction);
                glProg.drawBlocks(next);
                if (reconstructionOwned) {
                    try { reconstruction.close(); } catch (Throwable ignored) {}
                }
                reconstruction = next;
                reconstructionOwned = true;
            }
            finalTone = reconstruction;

            /* IRIS_26622_LOCAL_LAPLACIAN_TELEMETRY_LIFETIME
             * Device regression from 26621: telemetry dereferenced guide[last].mSize after the
             * guide pyramid had been released and nulled, aborting every Motion capture after the
             * Local-Laplacian reconstruction had already completed. Snapshot diagnostic dimensions
             * before release; telemetry must never retain or dereference a freed GLTexture. */
            final int coarsestWidth = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.x;
            final int coarsestHeight = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.y;

            /* IRIS_26621_LOCAL_LAPLACIAN_PEAK_LIFETIME
             * The remap pyramid is already gone. Once reconstruction is complete, guide/band
             * pyramids are no longer needed; release them before the optional full-resolution
             * true-2x readback so the direct R16F map does not overlap those transient allocations. */
            for (int level = 0; level < bands.length; level++) {
                if (bands[level] != null) {
                    try { bands[level].close(); } catch (Throwable ignored) {}
                    bands[level] = null;
                }
            }
            for (int level = 0; level < guide.length; level++) {
                if (guide[level] != null && guide[level] != finalTone) {
                    try { guide[level].close(); } catch (Throwable ignored) {}
                    guide[level] = null;
                }
            }

            final float iris26626PreservationStrength = iris26626SourcePreservationStrength();
            if (iris26626PreservationStrength > 1.0e-7f) {
                GLTexture preservedTone = iris26626ApplyBoundedSourceDomainPreservation(
                        source, finalTone, scalar, iris26626PreservationStrength);
                if (preservedTone != finalTone) {
                    try { finalTone.close(); } catch (Throwable ignored) {}
                    finalTone = preservedTone;
                }
            }

            if (basePipeline.mParameters.motionV2SuperResOutputEnabled) {
                finalTone.BufferLoad();
                ByteBuffer map = finalTone.textureBuffer(scalar, true);
                map.position(0);
                basePipeline.mParameters.motionV2LocalToneLogMap = map;
                basePipeline.mParameters.motionV2LocalToneLogWidth = finalTone.mSize.x;
                basePipeline.mParameters.motionV2LocalToneLogHeight = finalTone.mSize.y;
                basePipeline.mParameters.motionV2LocalToneLogSourceWidth = source.mSize.x;
                basePipeline.mParameters.motionV2LocalToneLogSourceHeight = source.mSize.y;
            }

            Log.i(Name, "IRIS_26621_NEW_SIMPLIFIED_LOCAL_LAPLACIAN"
                    + " active=true"
                    + " levels=" + IRIS_26621_LAPLACIAN_LEVELS
                    + " references=" + IRIS_26621_REFERENCE_COUNT
                    + " source=" + source.mSize.x + "x" + source.mSize.y
                    + " target=" + finalTone.mSize.x + "x" + finalTone.mSize.y
                    + " coarsest=" + coarsestWidth
                        + "x" + coarsestHeight
                    + " referenceLogRange=" + IRIS_26621_REFERENCE_MIN_LOG
                        + ".." + IRIS_26621_REFERENCE_MAX_LOG
                    + " sigmaEv=" + IRIS_26621_DETAIL_SIGMA_EV
                    + " edgeSlope=" + IRIS_26621_EDGE_SLOPE
                    + " detailAlpha=1.0"
                    + " iris26626BoundedSourceDomain=true"
                    + " iris26626PreservationStrength=" + iris26626PreservationStrength
                    + " iris26626PreservationMax=" + IRIS_26626_SOURCE_PRESERVATION_MAX
                    + " iris26626LowerBodyGate=" + IRIS_26623_UPPER_TONE_START + "..0.72"
                    + " iris26626Baseline=EXACT_26625_RECONSTRUCTION"
                    + " globalExposureOwner=motionV2DisplayGain"
                    + " outputExposureScaleConsumedOnce=" + OUTPUT_EXPOSURE_SCALE
                    + " absoluteFullResolutionToneMap=true"
                    + " correctionMap=false"
                    + " rgbScalarOnly=true"
                    + " true2xSharedMap=" + basePipeline.mParameters.motionV2SuperResOutputEnabled);
            keepFinal = true;
            return finalTone;
        } finally {
            for (GLTexture texture : bands) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            for (GLTexture texture : guide) {
                if (texture != null && texture != finalTone) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            if (!keepFinal && finalTone != null) {
                try { finalTone.close(); } catch (Throwable ignored) {}
            }
        }
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
        GLTexture iris26621LocalTone = iris26621BuildLocalLaplacianTone(extendedLinearHdr);
        /* IRIS_26630_PER_LENS_SATURATION_ROUTE
         * Only the Motion graph owns the per-lens Iris Saturation snapshot. Night deliberately
         * receives neutral 1.0; SR uses the same frozen Motion snapshot through the native encoder. */
        PostPipeline pipeline = (PostPipeline) basePipeline;
        IrisMotionSettings.Snapshot iris26630Tone = pipeline.motionV2ToneSettingsSnapshot;
        float iris26630MotionSaturation = basePipeline.mParameters.motionV2Active
                && iris26630Tone != null ? iris26630Tone.saturation : 1.0f;
        iris26630MotionSaturation = Math.max(0.0f, Math.min(2.0f, iris26630MotionSaturation));
        try {
            glProg.useAssetProgram("motionv2/render");
            glProg.setTexture("InputBuffer", extendedLinearHdr);
            glProg.setVar("sceneWhite", sceneWhite);
            glProg.setVar("iris26592MotionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);
            glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);
            glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);
            iris26623SetAdaptiveUpperToneUniforms();
            glProg.setVar("irisOutputZoom", irisOutputZoom);
            glProg.setVar("iris26630MotionSaturation", iris26630MotionSaturation);
            glProg.setVar("iris26621LocalToneEnabled", iris26621LocalTone != null ? 1 : 0);
            if (iris26621LocalTone != null) {
                glProg.setTexture("iris26621LocalToneLog", iris26621LocalTone);
            }

            WorkingTexture = basePipeline.getMain();
            glProg.drawBlocks(WorkingTexture);
        } finally {
            if (iris26621LocalTone != null) {
                try { iris26621LocalTone.close(); } catch (Throwable ignored) {}
            }
        }

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
                glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);
                glProg.setVar("motionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);
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
                                    + " bodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"
                                    + " hdrGainSource=MATCHED_LINEAR_HDR_INTENT_OVER_FINAL_SDR_LUMINANCE"
                                    + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE
                                    + " fixedBodyGain=false nominalWhiteDiscontinuity=false"
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
                        + " sdrBaseDetailAuthority=true colorAuthority=SDR_BASE_ONLY"
                        + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE
                        + " motionHdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE
                        + " motionHdrGainIsScalarLuminanceOnly=true"
                        + " motionHdrGainEquation=LINEAR_HDR_INTENT_OVER_FINAL_LINEAR_SDR"
                        + " motionHdrFixedBodyGain=false motionHdrNominalWhiteGate=false"
                        + " IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP=true");
            } finally {
                if (gainTexture != null) {
                    try { gainTexture.close(); } catch (Throwable ignored) {}
                }
            }
        }

        glProg.closed = true;

        if (basePipeline.mParameters.motionV2Active) {
            final float iris26623Pressure = iris26623HighlightPressure(
                    basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction,
                    basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction,
                    basePipeline.mParameters.motionV2ToneBaseSceneWhite,
                    basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite);
            final float iris26623WhiteAnchor = IRIS_26623_SPARSE_WHITE_ANCHOR
                    + (IRIS_26623_BROAD_WHITE_ANCHOR - IRIS_26623_SPARSE_WHITE_ANCHOR) * iris26623Pressure;
            final float iris26623WhiteSlope = IRIS_26623_SPARSE_WHITE_SLOPE
                    + (IRIS_26623_BROAD_WHITE_SLOPE - IRIS_26623_SPARSE_WHITE_SLOPE) * iris26623Pressure;
            Log.i(Name, "IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE"
                    + " master=extendedLinearPreTone"
                    + " brightnessTargetGain=" + basePipeline.mParameters.motionV2DisplayGain
                    + " displayGainImageMultiplier=false"
                    + " lowerTonePreservedThrough=" + IRIS_26623_UPPER_TONE_START
                    + " highlightPressure=" + iris26623Pressure
                    + " adaptiveWhiteAnchor=" + iris26623WhiteAnchor
                    + " adaptiveWhiteSlope=" + iris26623WhiteSlope
                    + " broadNearFraction=" + basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction
                    + " hardFraction=" + basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction
                    + " baseSceneWhite=" + basePipeline.mParameters.motionV2ToneBaseSceneWhite
                    + " adaptiveSceneWhite=" + basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite
                    + " oldFixedWhiteAnchor=" + IRIS_26621_SDR_WHITE_ANCHOR
                    + " sceneRecognition=false"
                    + " c1UpperBody=true c1SourceWhite=true monotonic=true hardEndpointClamp=false"
                    + " localToneOwner=fastLocalLaplacian"
                    + " localToneGlobalExposureMultiplier=false"
                    + " localToneDetailAlpha=1.0"
                    + " sdrExposureScale=" + OUTPUT_EXPOSURE_SCALE
                    + " hdrTargetExposureScale=" + HDR_EXPOSURE_SCALE
                    + " oneMasterRendition=true"
                    + " uhdrBodyGainOwner=UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR"
                    + " uhdrGainOwner=CONTINUOUS_LINEAR_INTENT_QUOTIENT"
                    + " superResToneParity=true");
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
                + " hdrIntentMatchSourceGuide=" + IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE
                + " uhdrLuminanceOnly=true uhdrContinuousIntentQuotient=true"
                + " IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS=true"
                + " syntheticBitmapGainMap=false"
                + " irisOutputZoom=" + irisOutputZoom
                + " nativeOutputDimensionsPreserved=true"
                + " iris26621SdrWhiteAnchorLegacy=" + IRIS_26621_SDR_WHITE_ANCHOR
                + " iris26623AdaptiveUpperTone=true"
                + " iris26614DisplayDomainKneeAuthority=false"
                + " iris26614CanonicalAppearanceGainAuthority=false"
                + " IRIS_26623_ADAPTIVE_UPPER_TONE_SDR_UHDR_SR_PARITY=true"
                + " iris26630AdaptiveColorV5=true iris26630Saturation=" + iris26630MotionSaturation
                + " iris26630SaturationOwner=" + (basePipeline.mParameters.motionV2Active ? "MOTION_PER_LENS" : "NIGHT_NEUTRAL_1_0")
                + " localTone=" + basePipeline.mParameters.motionV2Active
                + " localToneOwner=IRIS_26621_FAST_LOCAL_LAPLACIAN"
                + " globalToneOwner=IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE"
                + " sharpening=false");
    }
}
