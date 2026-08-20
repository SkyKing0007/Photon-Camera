#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

MATCHER_PATH = 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
FUSION_PATH = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
RELEASE_STACKER_PATH = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
RELEASE_SHADERS_PATH = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
NEW_STACKER_PATH = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
NEW_SHADERS_PATH = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'

CHANGED = {MATCHER_PATH, FUSION_PATH, NEW_STACKER_PATH, NEW_SHADERS_PATH}
NEW_FILES = {NEW_STACKER_PATH, NEW_SHADERS_PATH}

MATCHER_JAVA = r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Collections;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_FRAMEBUFFER;
import static android.opengl.GLES20.GL_FRAMEBUFFER_BINDING;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER
 *
 * Presentation exposure is solved only from like-for-like displayed-linear midtones. Preview and
 * candidate use the same eligibility interval and the same robust P35/P50/P65 statistics, fixing
 * the 26516 population mismatch that discarded preview shadows while retaining candidate shadows.
 * P10/P90 are diagnostic only. The frozen 26516 render model remains the forward model; this node
 * changes no RAW, MGC, Camera2 AE/shutter/ISO, color, or render behavior. Manual Iris Exposure
 * remains a later additive user control.
 */
public final class MotionV2ViewfinderExposureMatcher extends Node {
    private static final int METER_LONG_EDGE = 256;
    private static final float MIN_EV = -4.0f;
    private static final float MAX_EV = 4.0f;
    private static final int MAX_ITERATIONS = 4;
    private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;
    private static final float LOG2 = (float)Math.log(2.0);

    // IRIS_26517_MATCHED_DISPLAY_LINEAR_ELIGIBILITY
    private static final float METER_BLACK = 0.003f;
    private static final float METER_WHITE = 0.98f;


    // If the three midtone ratios do not describe one plausible scalar exposure, do not invent one.
    private static final float MAX_QUANTILE_SPREAD_EV = 0.60f;

    private static final class RgbSample {
        final float r, g, b;
        RgbSample(float r, float g, float b) { this.r = r; this.g = g; this.b = b; }
    }

    private static final class LumaStats {
        final float q10, q35, q50, q65, q90;
        LumaStats(float q10, float q35, float q50, float q65, float q90) {
            this.q10 = q10; this.q35 = q35; this.q50 = q50; this.q65 = q65; this.q90 = q90;
        }
    }

    public MotionV2ViewfinderExposureMatcher() {
        super("", "MotionV2ViewfinderExposureMatcher");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2ViewfinderExposureMatcher outside Motion V2");
        }
        WorkingTexture = previousNode.WorkingTexture;
        MotionViewfinderMetering.Snapshot snapshot = MotionViewfinderMetering.consumeLatest();
        Bitmap preview = snapshot == null ? null : snapshot.bitmap;
        float solvedEv = 0.0f;
        boolean valid = false;
        int previewCount = 0;
        int candidateCount = 0;
        LumaStats previewStats = null;
        LumaStats candidateStats0 = null;
        LumaStats candidateStatsSolved = null;
        float error0 = Float.NaN;
        float errorMinus = Float.NaN;
        float errorPlus = Float.NaN;
        float quantileSpreadEv = Float.NaN;

        try {
            if (snapshot == null || !snapshot.isReady() || preview == null) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26517_VIEWFINDER_MATCH neutralFallback=true reason="
                        + (snapshot == null ? "no_request" :
                           snapshot.pixelCopyResult == MotionViewfinderMetering.RESULT_PENDING
                                   ? "pixelcopy_pending" : "pixelcopy_failed")
                        + " requestId=" + (snapshot == null ? -1L : snapshot.requestId)
                        + " camera2Write=false legacyRawGainAuthority=false");
                return;
            }

            ArrayList<Float> previewLuma = collectPreviewLuma(preview);
            ArrayList<RgbSample> candidate = collectCandidateSamples(
                    previousNode.WorkingTexture, preview.getWidth(), preview.getHeight());
            previewCount = previewLuma.size();
            candidateCount = candidate.size();
            if (previewCount < 64 || candidateCount < 64) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26517_VIEWFINDER_MATCH neutralFallback=true reason=insufficient_samples"
                        + " previewSamples=" + previewCount + " candidateSamples=" + candidateCount
                        + " requestId=" + snapshot.requestId);
                return;
            }

            previewStats = statsFromSorted(previewLuma);
            candidateStats0 = candidateStats(candidate, 1.0f);
            quantileSpreadEv = impliedExposureSpreadEv(previewStats, candidateStats0);
            if (!Float.isFinite(quantileSpreadEv) || quantileSpreadEv > MAX_QUANTILE_SPREAD_EV) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26517_VIEWFINDER_MATCH neutralFallback=true reason=distribution_mismatch"
                        + " quantileSpreadEv=" + quantileSpreadEv
                        + " maxSpreadEv=" + MAX_QUANTILE_SPREAD_EV
                        + " previewQ35=" + previewStats.q35 + " previewQ50=" + previewStats.q50
                        + " previewQ65=" + previewStats.q65
                        + " candidateQ35=" + candidateStats0.q35 + " candidateQ50=" + candidateStats0.q50
                        + " candidateQ65=" + candidateStats0.q65
                        + " requestId=" + snapshot.requestId);
                return;
            }

            error0 = exposureError(candidate, 0.0f, previewStats);
            errorMinus = exposureError(candidate, -0.5f, previewStats);
            errorPlus = exposureError(candidate, 0.5f, previewStats);
            solvedEv = solveBounded(candidate, previewStats, error0, errorMinus, errorPlus);
            float gain = (float)Math.pow(2.0, solvedEv);
            if (!Float.isFinite(gain) || gain <= 0.0f) {
                throw new IllegalStateException("non-finite solved viewfinder gain");
            }
            candidateStatsSolved = candidateStats(candidate, gain);
            basePipeline.mParameters.motionV2DisplayGain = gain;
            valid = true;

            Log.i(Name, "IRIS_26517_VIEWFINDER_MATCH"
                    + " requestId=" + snapshot.requestId
                    + " requestToCopyMs=" + Math.max(0L,
                            snapshot.completedUptimeMs - snapshot.requestedUptimeMs)
                    + " preview=" + preview.getWidth() + "x" + preview.getHeight()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " previewQ10=" + previewStats.q10
                    + " previewQ35=" + previewStats.q35
                    + " previewQ50=" + previewStats.q50
                    + " previewQ65=" + previewStats.q65
                    + " previewQ90=" + previewStats.q90
                    + " candidateQ10Gain1=" + candidateStats0.q10
                    + " candidateQ35Gain1=" + candidateStats0.q35
                    + " candidateQ50Gain1=" + candidateStats0.q50
                    + " candidateQ65Gain1=" + candidateStats0.q65
                    + " candidateQ90Gain1=" + candidateStats0.q90
                    + " candidateQ10Solved=" + candidateStatsSolved.q10
                    + " candidateQ35Solved=" + candidateStatsSolved.q35
                    + " candidateQ50Solved=" + candidateStatsSolved.q50
                    + " candidateQ65Solved=" + candidateStatsSolved.q65
                    + " candidateQ90Solved=" + candidateStatsSolved.q90
                    + " quantileSpreadEv=" + quantileSpreadEv
                    + " errorEv0=" + error0
                    + " errorEvMinus05=" + errorMinus
                    + " errorEvPlus05=" + errorPlus
                    + " solvedEv=" + solvedEv
                    + " displayGain=" + gain
                    + " sameEligibility=" + METER_BLACK + ".." + METER_WHITE
                    + " midtoneVotes=P35,P50,P65 shadowQ10DiagnosticOnly=true"
                    + " fixedCandidateSampleSet=true boundedSecant=true probeStepEv=0.5"
                    + " maxIterations=4 evBounds=-4..4"
                    + " legacyRawGainAuthority=false manualIrisExposureLater=true camera2Write=false");
        } catch (Throwable t) {
            basePipeline.mParameters.motionV2DisplayGain = 1.0f;
            Log.e(Name, "IRIS_26517_VIEWFINDER_MATCH neutralFallback=true reason="
                    + t.getClass().getSimpleName()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " spreadEv=" + quantileSpreadEv
                    + " e0=" + error0 + " em=" + errorMinus + " ep=" + errorPlus);
        } finally {
            if (preview != null && !preview.isRecycled()) {
                try { preview.recycle(); } catch (Throwable ignored) {}
            }
            glProg.closed = true;
            if (!valid) solvedEv = 0.0f;
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26517_VIEWFINDER_PRESENTATION_AUTHORITY",
                        "valid=" + valid
                                + " solvedEv=" + solvedEv
                                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain
                                + " previewCandidateEligibilitySymmetric=true"
                                + " deepShadowsDoNotVote=true renderModelFrozen26516=true"
                                + " legacyRawGainAuthority=false manualExposureAdditiveLater=true"
                                + " captureAeUntouched=true");
            } catch (Throwable ignored) {}
        }
    }

    private ArrayList<Float> collectPreviewLuma(Bitmap bitmap) {
        int w = bitmap.getWidth(), h = bitmap.getHeight();
        int[] pixels = new int[w * h];
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h);
        ArrayList<Float> luma = new ArrayList<>();
        for (int c : pixels) {
            float r = srgbDecode(((c >> 16) & 0xff) / 255.0f);
            float g = srgbDecode(((c >> 8) & 0xff) / 255.0f);
            float b = srgbDecode((c & 0xff) / 255.0f);
            float y = luma(r, g, b);
            if (eligibleDisplayedLuma(y)) luma.add(y);
        }
        Collections.sort(luma);
        return luma;
    }

    private ArrayList<RgbSample> collectCandidateSamples(GLTexture source, int previewW, int previewH) {
        int[] oldFramebuffer = new int[1];
        GLTexture probe = null;
        try {
            GLES30.glGetIntegerv(GL_FRAMEBUFFER_BINDING, oldFramebuffer, 0);
            int longEdge = Math.max(previewW, previewH);
            if (longEdge <= 0 || longEdge > METER_LONG_EDGE) {
                throw new IllegalStateException("invalid viewfinder meter dimensions "
                        + previewW + "x" + previewH);
            }
            Point size = new Point(previewW, previewH);
            probe = new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_32, 4), null,
                    GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useProgram(
                    "precision highp float;\n"
                    + "uniform sampler2D InputBuffer;\n"
                    + "uniform vec2 OutputSize;\n"
                    + "out vec4 Output;\n"
                    + "void main(){vec2 uv=(gl_FragCoord.xy-vec2(0.5))/OutputSize;"
                    + "Output=texture(InputBuffer,clamp(uv,vec2(0.0),vec2(1.0)));}\n");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("OutputSize", (float)previewW, (float)previewH);
            glProg.drawBlocks(probe);
            glProg.closed = true;
            probe.BufferLoad();
            ByteBuffer bytes = probe.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(ByteOrder.nativeOrder());
            FloatBuffer fb = bytes.asFloatBuffer();
            ArrayList<RgbSample> all = new ArrayList<>();
            while (fb.remaining() >= 4) {
                float r = fb.get(), g = fb.get(), b = fb.get();
                fb.get();
                if (!Float.isFinite(r) || !Float.isFinite(g) || !Float.isFinite(b)) continue;
                r = Math.max(0.0f, r); g = Math.max(0.0f, g); b = Math.max(0.0f, b);
                RgbSample sample = new RgbSample(r, g, b);
                float y = presentedLuma(sample, 1.0f);
                if (eligibleDisplayedLuma(y)) all.add(sample);
            }
            // Stable source ordering is sufficient; each stats pass sorts presented luminance.
            return all;
        } finally {
            if (probe != null) try { probe.close(); } catch (Throwable ignored) {}
            GLES30.glBindFramebuffer(GL_FRAMEBUFFER, oldFramebuffer[0]);
        }
    }

    private static boolean eligibleDisplayedLuma(float y) {
        return Float.isFinite(y) && y > METER_BLACK && y < METER_WHITE;
    }

    private static LumaStats candidateStats(ArrayList<RgbSample> samples, float gain) {
        ArrayList<Float> values = new ArrayList<>(samples.size());
        for (RgbSample sample : samples) values.add(presentedLuma(sample, gain));
        Collections.sort(values);
        return statsFromSorted(values);
    }

    private static LumaStats statsFromSorted(ArrayList<Float> sorted) {
        if (sorted.isEmpty()) throw new IllegalArgumentException("empty luminance population");
        return new LumaStats(
                percentileSorted(sorted, 0.10f),
                percentileSorted(sorted, 0.35f),
                percentileSorted(sorted, 0.50f),
                percentileSorted(sorted, 0.65f),
                percentileSorted(sorted, 0.90f));
    }

    private static float percentileSorted(ArrayList<Float> sorted, float q) {
        float pos = clamp(q, 0.0f, 1.0f) * (sorted.size() - 1);
        int lo = (int)Math.floor(pos);
        int hi = Math.min(sorted.size() - 1, lo + 1);
        float t = pos - lo;
        return mix(sorted.get(lo), sorted.get(hi), t);
    }

    private static float impliedExposureSpreadEv(LumaStats preview, LumaStats candidate) {
        float e35 = log2(Math.max(preview.q35, 1.0e-5f) / Math.max(candidate.q35, 1.0e-5f));
        float e50 = log2(Math.max(preview.q50, 1.0e-5f) / Math.max(candidate.q50, 1.0e-5f));
        float e65 = log2(Math.max(preview.q65, 1.0e-5f) / Math.max(candidate.q65, 1.0e-5f));
        float lo = Math.min(e35, Math.min(e50, e65));
        float hi = Math.max(e35, Math.max(e50, e65));
        return hi - lo;
    }

    private static float exposureError(ArrayList<RgbSample> samples, float ev, LumaStats target) {
        float gain = (float)Math.pow(2.0, ev);
        LumaStats candidate = candidateStats(samples, gain);
        float e35 = log2(Math.max(candidate.q35, 1.0e-5f)) - log2(Math.max(target.q35, 1.0e-5f));
        float e50 = log2(Math.max(candidate.q50, 1.0e-5f)) - log2(Math.max(target.q50, 1.0e-5f));
        float e65 = log2(Math.max(candidate.q65, 1.0e-5f)) - log2(Math.max(target.q65, 1.0e-5f));
        // Midtones own automatic exposure. q10/q90 are telemetry only.
        return 0.25f * e35 + 0.50f * e50 + 0.25f * e65;
    }

    private static float solveBounded(ArrayList<RgbSample> samples, LumaStats target,
                                      float e0, float eMinus, float ePlus) {
        float slope = ePlus - eMinus;
        float guess = Math.abs(slope) > 1.0e-4f
                ? clamp(-e0 / slope, MIN_EV, MAX_EV)
                : 0.0f;
        float bestEv = guess;
        float bestErr = Math.abs(exposureError(samples, guess, target));

        float lo = MIN_EV, hi = MAX_EV;
        float flo = exposureError(samples, lo, target);
        float fhi = exposureError(samples, hi, target);
        if (Math.signum(flo) == Math.signum(fhi)) {
            if (Math.abs(flo) < bestErr) { bestErr = Math.abs(flo); bestEv = lo; }
            if (Math.abs(fhi) < bestErr) bestEv = hi;
            return bestEv;
        }

        for (int i = 0; i < MAX_ITERATIONS; i++) {
            float denom = fhi - flo;
            float x = Math.abs(denom) > 1.0e-5f
                    ? lo - flo * (hi - lo) / denom
                    : 0.5f * (lo + hi);
            float guard = 0.12f * (hi - lo);
            x = clamp(x, lo + guard, hi - guard);
            float fx = exposureError(samples, x, target);
            if (Math.abs(fx) < bestErr) { bestErr = Math.abs(fx); bestEv = x; }
            if (Math.abs(fx) < 0.01f) break;
            if (Math.signum(fx) == Math.signum(flo)) { lo = x; flo = fx; }
            else { hi = x; fhi = fx; }
        }
        return clamp(bestEv, MIN_EV, MAX_EV);
    }

    private static float presentedLuma(RgbSample sample, float gain) {
        float effectiveGain = Math.max(gain, 1.0e-6f);
        float r = Math.max(0.0f, sample.r * effectiveGain);
        float g = Math.max(0.0f, sample.g * effectiveGain);
        float b = Math.max(0.0f, sample.b * effectiveGain);
        float y = luma(r, g, b);
        float peak = Math.max(r, Math.max(g, b));
        float guide = Math.max(y, peak);
        if (guide > 1.0e-7f) {
            float mappedGuide = mapHeadroom(guide, gain);
            float scale = mappedGuide / guide;
            float mr = r * scale, mg = g * scale, mb = b * scale;
            float whitePoint = Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, gain)));
            float pos = clamp((guide - 0.50f) / Math.max(whitePoint - 0.50f, 1.0e-6f), 0f, 1f);
            float neutralMix = smoothstep(0.82f, 1.0f, pos);
            r = mix(mr, mappedGuide, neutralMix);
            g = mix(mg, mappedGuide, neutralMix);
            b = mix(mb, mappedGuide, neutralMix);
        }
        r *= OUTPUT_EXPOSURE_SCALE;
        g *= OUTPUT_EXPOSURE_SCALE;
        b *= OUTPUT_EXPOSURE_SCALE;
        float outPeak = Math.max(r, Math.max(g, b));
        if (outPeak > 1.0f) {
            float overflow = clamp((outPeak - 1.0f) / 0.25f, 0f, 1f);
            float t = smoothstep(0.0f, 1.0f, overflow);
            r = mix(r / outPeak, 1.0f, t);
            g = mix(g / outPeak, 1.0f, t);
            b = mix(b / outPeak, 1.0f, t);
        }
        return clamp(luma(r, g, b), 0.0f, 1.0f);
    }

    private static float mapHeadroom(float guide, float gain) {
        final float start = 0.50f;
        if (guide <= start) return guide;
        float whitePoint = Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, gain)));
        float x = clamp((guide - start) / Math.max(whitePoint - start, 1.0e-6f), 0f, 1f);
        final float logShape = 6.0f;
        float shaped = (float)(Math.log(1.0 + logShape * x) / Math.log(1.0 + logShape));
        float preScaleDisplayWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        return start + (preScaleDisplayWhite - start) * shaped;
    }

    private static float srgbDecode(float x) {
        x = clamp(x, 0.0f, 1.0f);
        return x <= 0.04045f
                ? x / 12.92f
                : (float)Math.pow((x + 0.055f) / 1.055f, 2.4);
    }

    private static float luma(float r, float g, float b) {
        return 0.2126f * r + 0.7152f * g + 0.0722f * b;
    }

    private static float log2(float x) { return (float)(Math.log(x) / LOG2); }
    private static float clamp(float x, float lo, float hi) { return Math.max(lo, Math.min(hi, x)); }
    private static float mix(float a, float b, float t) { return a + (b - a) * t; }
    private static float smoothstep(float e0, float e1, float x) {
        float t = clamp((x - e0) / Math.max(e1 - e0, 1.0e-8f), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }
}
'''

FUSION_OLD = r'''        return GlesMgcRawSpatialStacker(
            width = width,
            height = height,
            cfaPattern = cfaPattern,
            blackLevel = blackLevel,
            whiteLevel = whiteLevel,
            whiteBalanceGains = whiteBalanceGains,
            noiseProfileSelection = noiseProfileSelection,
            lensShading = lensShading,
            lensShadingWidth = lensShadingWidth,
            lensShadingHeight = lensShadingHeight,
            outputMode = outputMode,
            mergeMethod = mergeMethod,
            outputScale = outputScale,
            useCurrentGlContext = useCurrentGlContext,
            exportGpuLinearRgbSource = exportGpuLinearRgbSource,
            gpuLinearRgbStorage = gpuLinearRgbStorage,
        ).processFrames(scheduledFrames)
'''

FUSION_NEW = r'''        // IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER
        // Motion requests SPATIAL_RGB. Route only that mode to the released pre-Sabre 1.27.1
        // Spatial implementation (c4ff5a3). Keep current 09c Spatial Bayer and Sabre owners intact.
        if (mergeMethod == MgcMergeMethod.SPATIAL_RGB) {
            PLog.i(TAG, "IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER commit=c4ff5a3 " +
                "postSabreSpatial=false currentSabreUntouched=true")
            return GlesMgc1271ReleasedSpatialStacker(
                width = width,
                height = height,
                cfaPattern = cfaPattern,
                blackLevel = blackLevel,
                whiteLevel = whiteLevel,
                whiteBalanceGains = whiteBalanceGains,
                noiseProfileSelection = noiseProfileSelection,
                lensShading = lensShading,
                lensShadingWidth = lensShadingWidth,
                lensShadingHeight = lensShadingHeight,
                outputMode = outputMode,
                outputScale = outputScale,
                useCurrentGlContext = useCurrentGlContext,
                exportGpuLinearRgbSource = exportGpuLinearRgbSource,
                gpuLinearRgbStorage = gpuLinearRgbStorage,
            ).processFrames(scheduledFrames)
        }
        return GlesMgcRawSpatialStacker(
            width = width,
            height = height,
            cfaPattern = cfaPattern,
            blackLevel = blackLevel,
            whiteLevel = whiteLevel,
            whiteBalanceGains = whiteBalanceGains,
            noiseProfileSelection = noiseProfileSelection,
            lensShading = lensShading,
            lensShadingWidth = lensShadingWidth,
            lensShadingHeight = lensShadingHeight,
            outputMode = outputMode,
            mergeMethod = mergeMethod,
            outputScale = outputScale,
            useCurrentGlContext = useCurrentGlContext,
            exportGpuLinearRgbSource = exportGpuLinearRgbSource,
            gpuLinearRgbStorage = gpuLinearRgbStorage,
        ).processFrames(scheduledFrames)
'''

def released_owner_texts(released_root: Path) -> dict[str,str]:
    stack=(released_root/RELEASE_STACKER_PATH).read_text().replace('\r\n','\n')
    shaders=(released_root/RELEASE_SHADERS_PATH).read_text().replace('\r\n','\n')
    if stack.count('internal class GlesMgcRawSpatialStacker(') != 1:
        raise AssertionError('released stacker class anchor drift')
    if shaders.count('internal object GlesMgcRawSpatialShaders') != 1:
        raise AssertionError('released shader object anchor drift')
    if 'private val guideWidth = max(1, width / 4)' not in stack:
        raise AssertionError('released quarter-guide contract missing')
    if 'MgcRawProcessorPipeline' in stack or 'private val mergeMethod:' in stack:
        raise AssertionError('released stacker unexpectedly contains post-Sabre processor contract')
    stack=stack.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker')
    stack=stack.replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
    shaders=shaders.replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
    return {NEW_STACKER_PATH:stack, NEW_SHADERS_PATH:shaders}

def expected_text(rel: str, base: str, released: dict[str,str]) -> str:
    s=base.replace('\r\n','\n')
    if rel == MATCHER_PATH:
        for needle in (
            'IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER',
            'private static final float MIN_EV = -4.0f;',
            'private static final float MAX_EV = 4.0f;',
            'y > 0.025f && y < 0.975f',
            'y > 1.0e-4f && y < 8.0f',
        ):
            if needle not in s: raise AssertionError('26516 matcher anchor missing: '+needle)
        return MATCHER_JAVA
    if rel == FUSION_PATH:
        if s.count(FUSION_OLD) != 1:
            raise AssertionError(f'current Fusion Spatial constructor anchor count={s.count(FUSION_OLD)}')
        if 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in s:
            raise AssertionError('26517 released Spatial route already present in base')
        return s.replace(FUSION_OLD,FUSION_NEW,1)
    if rel in NEW_FILES:
        if s: raise AssertionError(rel+' unexpectedly exists in tested-26516 base')
        return released[rel]
    raise AssertionError('unexpected changed path: '+rel)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--released-root',required=True,type=Path)
    ap.add_argument('--patch-out',required=True,type=Path)
    ap.add_argument('--patch-sha-out',required=True,type=Path)
    ns=ap.parse_args(); root=ns.root.resolve(); released=released_owner_texts(ns.released_root.resolve())
    before={}; after={}
    for rel in sorted(CHANGED):
        p=root/rel
        if not p.is_file() and rel not in NEW_FILES: raise AssertionError('missing tested-26516 path: '+rel)
        old=p.read_text() if p.is_file() else ''
        new=expected_text(rel,old,released)
        if old==new: raise AssertionError('26517 transform made no change: '+rel)
        before[rel]=old; after[rel]=new
    parts=[]
    for rel in sorted(CHANGED):
        parts += difflib.unified_diff(before[rel].splitlines(keepends=True),after[rel].splitlines(keepends=True),
            fromfile='tested26516/'+rel,tofile='candidate26517/'+rel)
    patch=''.join(parts)
    if not patch.strip(): raise AssertionError('26517 rollback/audit patch is empty')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True)
    ns.patch_out.write_text(patch)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    # Critical ordering: rollback/audit patch exists before any candidate runtime write.
    for rel in sorted(CHANGED):
        p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(after[rel])
    print('PASS: 26517 rollback/audit patch created before runtime writes')
    print('PASS: released c4ff Spatial owners + Fusion route + symmetric viewfinder matcher applied')
if __name__=='__main__': main()
