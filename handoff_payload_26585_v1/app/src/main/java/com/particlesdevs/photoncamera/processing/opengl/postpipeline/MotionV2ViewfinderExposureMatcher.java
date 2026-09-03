package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingsManager;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_FRAMEBUFFER;
import static android.opengl.GLES20.GL_FRAMEBUFFER_BINDING;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE
 *
 * Exact 26516 viewfinder metering/solver relationship, with only its solved EV response
 * scaled by a user-controlled per-lens percentage. At the 65% default, the known 26516
 * reference solve of +1.764 EV becomes about +1.147 EV. This is not a fixed EV clamp.
 *
 * Post-capture presentation exposure only. A small shutter-time bitmap of the displayed preview
 * supplies the target midtone distribution. A fixed sample set from the profile-colored RAW
 * candidate is then probed at +/-0.5 EV and solved with a bounded monotonic secant iteration.
 * The result writes only Parameters.motionV2DisplayGain; shutter/ISO/AE are untouched.
 *
 * Manual Iris Exposure remains a later, independent user control.
 */
public final class MotionV2ViewfinderExposureMatcher extends Node {
    private static final int METER_LONG_EDGE = 256;
    private static final float MIN_EV = -4.0f;
    private static final float MAX_EV = 4.0f;
    private static final int MAX_ITERATIONS = 4;
    private static final float OUTPUT_EXPOSURE_SCALE = MotionV2Render.OUTPUT_EXPOSURE_SCALE;
    private static final float LOG2 = (float)Math.log(2.0);

    private static final String MATCH_STRENGTH_KEY = "pref_motion_viewfinder_match_strength";
    private static final float DEFAULT_MATCH_STRENGTH_PERCENT = 65.0f;
    /* IRIS_26558_NIGHT_PRESENTATION_POLICY
     * Keep Motion's proven current match-strength solve as the comparison authority, then give Night a bounded
     * scene-adaptive visibility advantage: about +0.40 EV (~32%) in very dark scenes and +0.30 EV
     * (~23%) in bright scenes. This prevents the old bright-scene ramp to 100% of rawSolvedEv from
     * washing midtones while retaining a meaningful Night advantage in a dark closet. The existing
     * P99 extended-linear headroom cap remains the highlight-safety authority.
     */
    private static final float NIGHT_DARK_ADVANTAGE_EV = 0.40f;
    private static final float NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f;
    private static final float NIGHT_FULL_MATCH_LUMA = 0.22f;
    private static final float NIGHT_DARK_LUMA = 0.06f;
    private static final float NIGHT_HEADROOM_GUIDE_LIMIT = 5.0f;
    private float iris26550CandidateP99Guide = Float.NaN;
    private float iris26582CandidateP95Guide = Float.NaN;
    private float iris26583CandidateP995Guide = Float.NaN;
    private float iris26583CandidateP998Guide = Float.NaN;
    private final ArrayList<Float> iris26582CandidateGuides = new ArrayList<>();
    /* IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER
     * Keep the complete fixed-resolution candidate guide field, not only sorted percentiles.
     * This lets tone adaptation distinguish a coherent small lamp/cloud from one isolated sparkle
     * without local tone mapping or another full-resolution readback.
     */
    private float[] iris26584CandidateGuideGrid = null;
    private int iris26584CandidateGridWidth = 0;
    private int iris26584CandidateGridHeight = 0;
    private float[] iris26584ProjectedGridScratch = null;

    private static final class RgbSample {
        final float r, g, b;
        RgbSample(float r, float g, float b) { this.r = r; this.g = g; this.b = b; }
    }

    public MotionV2ViewfinderExposureMatcher() {
        super("", "MotionV2ViewfinderExposureMatcher");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        final boolean iris26550Night = basePipeline.mParameters.irisNightActive;
        if (!(basePipeline.mParameters.motionV2Active || iris26550Night)) {
            throw new IllegalStateException("MotionV2ViewfinderExposureMatcher outside Iris Motion/Night");
        }
        WorkingTexture = previousNode.WorkingTexture;
        iris26582CandidateGuides.clear();
        iris26582CandidateP95Guide = Float.NaN;
        iris26550CandidateP99Guide = Float.NaN;
        iris26583CandidateP995Guide = Float.NaN;
        iris26583CandidateP998Guide = Float.NaN;
        iris26584CandidateGuideGrid = null;
        iris26584CandidateGridWidth = 0;
        iris26584CandidateGridHeight = 0;
        basePipeline.mParameters.motionV2ToneP95Guide = Float.NaN;
        basePipeline.mParameters.motionV2ToneP99Guide = Float.NaN;
        basePipeline.mParameters.motionV2ToneP995Guide = Float.NaN;
        basePipeline.mParameters.motionV2ToneP998Guide = Float.NaN;
        basePipeline.mParameters.motionV2TonePredictedClipFraction = 0.0f;
        basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction = 0.0f;
        basePipeline.mParameters.motionV2ToneProjectedNearCeilingFraction = 0.0f;
        basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction = 0.0f;
        basePipeline.mParameters.motionV2ToneProjectedBroadTailStrength = 0.0f;
        basePipeline.mParameters.motionV2ToneCompactTailStrength = 0.0f;
        basePipeline.mParameters.motionV2ToneBaseSceneWhite = 1.0f;
        basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite = 1.0f;
        basePipeline.mParameters.motionV2ToneAdaptiveStrength = 0.0f;
        MotionViewfinderMetering.Snapshot snapshot = MotionViewfinderMetering.consumeLatest();
        Bitmap preview = snapshot == null ? null : snapshot.bitmap;
        float solvedEv = 0.0f;
        boolean valid = false;
        int previewCount = 0;
        int candidateCount = 0;
        float targetLog = Float.NaN;
        float error0 = Float.NaN;
        float errorMinus = Float.NaN;
        float errorPlus = Float.NaN;
        float rawSolvedEv = Float.NaN;
        float matchStrengthPercent = DEFAULT_MATCH_STRENGTH_PERCENT;

        try {
            if (snapshot == null || !snapshot.isReady() || preview == null) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26519_VIEWFINDER_MATCH neutralFallback=true reason="
                        + (snapshot == null ? "no_request" :
                           snapshot.pixelCopyResult == MotionViewfinderMetering.RESULT_PENDING
                                   ? "pixelcopy_pending" : "pixelcopy_failed")
                        + " requestId=" + (snapshot == null ? -1L : snapshot.requestId)
                        + " camera2Write=false legacyRawGainAuthority=false");
                return;
            }

            ArrayList<Float> previewLuma = collectPreviewMidtones(preview);
            ArrayList<RgbSample> candidate = collectCandidateSamples(
                    previousNode.WorkingTexture, preview.getWidth(), preview.getHeight());
            previewCount = previewLuma.size();
            candidateCount = candidate.size();
            if (previewCount < 32 || candidateCount < 32) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26519_VIEWFINDER_MATCH neutralFallback=true reason=insufficient_samples"
                        + " previewSamples=" + previewCount + " candidateSamples=" + candidateCount
                        + " requestId=" + snapshot.requestId);
                return;
            }

            targetLog = medianLogLuma(previewLuma);
            error0 = exposureError(candidate, 0.0f, targetLog);
            errorMinus = exposureError(candidate, -0.5f, targetLog);
            errorPlus = exposureError(candidate, 0.5f, targetLog);
            rawSolvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);
            if (iris26550Night) {
                float targetLinearLuma = (float)Math.pow(2.0, targetLog);
                float daylightness = smoothstep(NIGHT_DARK_LUMA, NIGHT_FULL_MATCH_LUMA, targetLinearLuma);
                matchStrengthPercent = readMatchStrengthPercent();
                float motionStrength = matchStrengthPercent / 100.0f;
                float motionEquivalentEv = clamp(rawSolvedEv * motionStrength, MIN_EV, MAX_EV);
                float nightAdvantageEv = mix(
                        NIGHT_DARK_ADVANTAGE_EV, NIGHT_BRIGHT_ADVANTAGE_EV, daylightness);
                float desiredEv = clamp(motionEquivalentEv + nightAdvantageEv, MIN_EV, MAX_EV);
                float headroomCapEv = MAX_EV;
                if (Float.isFinite(iris26550CandidateP99Guide) && iris26550CandidateP99Guide > 0.0f) {
                    headroomCapEv = clamp(log2(NIGHT_HEADROOM_GUIDE_LIMIT
                            / Math.max(0.05f, iris26550CandidateP99Guide)), 0.0f, MAX_EV);
                }
                solvedEv = desiredEv > 0.0f ? Math.min(desiredEv, headroomCapEv) : desiredEv;
                Log.i(Name, "IRIS_26558_NIGHT_PRESENTATION_SOLVE"
                        + " targetLinearLuma=" + targetLinearLuma
                        + " rawSolvedEv=" + rawSolvedEv
                        + " motionEquivalentEv=" + motionEquivalentEv
                        + " nightAdvantageEv=" + nightAdvantageEv
                        + " targetBrightnessRatio=" + Math.pow(2.0, nightAdvantageEv)
                        + " candidateP99Guide=" + iris26550CandidateP99Guide
                        + " headroomCapEv=" + headroomCapEv
                        + " solvedEv=" + solvedEv
                        + " realizedAdvantageEv=" + (solvedEv - motionEquivalentEv)
                        + " realizedBrightnessRatio=" + Math.pow(2.0, solvedEv - motionEquivalentEv)
                        + " captureExposureWrite=false shortReferenceUnchanged=true"
                        + " motionPresentationUnchanged=true preserveNightFeel=true viewfinderTarget=true");
            } else {
                /* Exact Motion behavior retained from 26549. */
                matchStrengthPercent = readMatchStrengthPercent();
                float matchStrength = matchStrengthPercent / 100.0f;
                solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);
            }
            float gain = (float)Math.pow(2.0, solvedEv);
            if (!Float.isFinite(gain) || gain <= 0.0f) {
                throw new IllegalStateException("non-finite solved viewfinder gain");
            }
            basePipeline.mParameters.motionV2DisplayGain = gain;
            ToneDecision iris26583Tone = iris26583ToneDecision(gain);
            basePipeline.mParameters.motionV2ToneP95Guide = iris26582CandidateP95Guide;
            basePipeline.mParameters.motionV2ToneP99Guide = iris26550CandidateP99Guide;
            basePipeline.mParameters.motionV2ToneP995Guide = iris26583CandidateP995Guide;
            basePipeline.mParameters.motionV2ToneP998Guide = iris26583CandidateP998Guide;
            basePipeline.mParameters.motionV2TonePredictedClipFraction = iris26583Tone.clippedFraction;
            basePipeline.mParameters.motionV2ToneProjectedBroadNearCeilingFraction = iris26583Tone.projectedBroadNearFraction;
            basePipeline.mParameters.motionV2ToneProjectedNearCeilingFraction = iris26583Tone.projectedNearFraction;
            basePipeline.mParameters.motionV2ToneProjectedHardCeilingFraction = iris26583Tone.projectedHardFraction;
            basePipeline.mParameters.motionV2ToneProjectedBroadTailStrength = iris26583Tone.projectedBroadTailStrength;
            basePipeline.mParameters.motionV2ToneCompactTailStrength = iris26583Tone.compactTailStrength;
            basePipeline.mParameters.motionV2ToneBaseSceneWhite = iris26583Tone.baseSceneWhite;
            basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite = iris26583Tone.adaptiveSceneWhite;
            basePipeline.mParameters.motionV2ToneAdaptiveStrength = iris26583Tone.adaptiveStrength;
            valid = true;

            Log.i(Name, "IRIS_26583_PROJECTED_HIGHLIGHT_TAIL_DECISION"
                    + " p95Guide=" + iris26582CandidateP95Guide
                    + " p99Guide=" + iris26550CandidateP99Guide
                    + " p995Guide=" + iris26583CandidateP995Guide
                    + " p998Guide=" + iris26583CandidateP998Guide
                    + " displayGain=" + gain
                    + " legacyBroadClipFraction=" + iris26583Tone.clippedFraction
                    + " projectedBroadNearCeilingFraction=" + iris26583Tone.projectedBroadNearFraction
                    + " projectedNearCeilingFraction=" + iris26583Tone.projectedNearFraction
                    + " projectedHardCeilingFraction=" + iris26583Tone.projectedHardFraction
                    + " projectedBroadTailStrength=" + iris26583Tone.projectedBroadTailStrength
                    + " compactTailStrength=" + iris26583Tone.compactTailStrength
                    + " baseSceneWhite=" + iris26583Tone.baseSceneWhite
                    + " adaptiveSceneWhite=" + iris26583Tone.adaptiveSceneWhite
                    + " adaptiveStrength=" + iris26583Tone.adaptiveStrength
                    + " legacyHighlightTarget=" + MotionV2Render.IRIS_26582_HIGHLIGHT_TARGET
                    + " broadHighlightTarget=" + MotionV2Render.IRIS_26583_BROAD_HIGHLIGHT_TARGET
                    + " compactHighlightTarget=" + MotionV2Render.IRIS_26583_COMPACT_HIGHLIGHT_TARGET
                    + " projectedBaselineTone=true maxChannelDetection=true"
                    + " localTone=false uniformRgbScalar=true chromaOwnerUnchanged=true");
            Log.i(Name, "IRIS_26584_ALL_SCENE_HIGHLIGHT_DECISION"
                    + " continuousTailPressure=" + iris26583Tone.continuousTailPressure
                    + " continuousTailStrength=" + iris26583Tone.continuousTailStrength
                    + " structuredPixels=" + iris26583Tone.structuredPixels
                    + " structuredCells=" + iris26583Tone.structuredCells
                    + " structuredGuide=" + iris26583Tone.structuredGuide
                    + " structuredGuidePercentile=0.98"
                    + " structuredHighlightTarget=0.945"
                    + " structuredStrength=" + iris26583Tone.structuredStrength
                    + " floor26583SceneWhite=" + iris26583Tone.floor26583SceneWhite
                    + " adaptiveSceneWhite=" + iris26583Tone.adaptiveSceneWhite
                    + " spatialPopulationIndependent=true continuousTail=true"
                    + " toneStartUnchanged=true uniformRgbScalar=true localToneMap=false");

            Log.i(Name, "IRIS_26519_VIEWFINDER_MATCH"
                    + " requestId=" + snapshot.requestId
                    + " requestToCopyMs=" + Math.max(0L,
                            snapshot.completedUptimeMs - snapshot.requestedUptimeMs)
                    + " preview=" + preview.getWidth() + "x" + preview.getHeight()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " targetLogLuma=" + targetLog
                    + " errorEv0=" + error0
                    + " errorEvMinus05=" + errorMinus
                    + " errorEvPlus05=" + errorPlus
                    + " rawSolvedEv=" + rawSolvedEv
                    + " matchStrengthPercent=" + matchStrengthPercent
                    + " solvedEv=" + solvedEv
                    + " cameraId=" + cameraIdForLog()
                    + " displayGain=" + gain
                    + " irisNight=" + iris26550Night
                    + " candidateP99Guide=" + iris26550CandidateP99Guide
                    + " fixedCandidateSampleSet=true"
                    + " boundedSecant=true probeStepEv=0.5 maxIterations=4 evBounds=-4..4"
                    + " meterLongEdge=" + METER_LONG_EDGE
                    + " displayLinearLuma=true candidateMidtoneBand=P25-P50"
                    + " legacyRawGainAuthority=false"
                    + " manualIrisExposureLater=true"
                    + " camera2Write=false");
        } catch (Throwable t) {
            basePipeline.mParameters.motionV2DisplayGain = 1.0f;
            Log.e(Name, "IRIS_26519_VIEWFINDER_MATCH neutralFallback=true reason="
                    + t.getClass().getSimpleName()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " targetLog=" + targetLog
                    + " e0=" + error0 + " em=" + errorMinus + " ep=" + errorPlus);
        } finally {
            if (preview != null && !preview.isRecycled()) {
                try { preview.recycle(); } catch (Throwable ignored) {}
            }
            glProg.closed = true;
            if (!valid) solvedEv = 0.0f;
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26519_VIEWFINDER_PRESENTATION_AUTHORITY",
                        "valid=" + valid
                                + " rawSolvedEv=" + rawSolvedEv
                                + " matchStrengthPercent=" + matchStrengthPercent
                                + " solvedEv=" + solvedEv
                                + " cameraId=" + cameraIdForLog()
                                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain
                                + " legacyRawGainAuthority=false"
                                + " manualExposureAdditiveLater=true"
                                + " captureAeUntouched=true");
            } catch (Throwable ignored) {}
        }
    }

    private static float readMatchStrengthPercent() {
        try {
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            if (sm == null) return DEFAULT_MATCH_STRENGTH_PERCENT;
            String raw = sm.getString(
                    PreferenceKeys.SCOPE_GLOBAL,
                    MATCH_STRENGTH_KEY,
                    Integer.toString(Math.round(DEFAULT_MATCH_STRENGTH_PERCENT)));
            float value = Float.parseFloat(raw);
            if (!Float.isFinite(value)) return DEFAULT_MATCH_STRENGTH_PERCENT;
            return Math.max(0.0f, Math.min(100.0f, value));
        } catch (Throwable ignored) {
            return DEFAULT_MATCH_STRENGTH_PERCENT;
        }
    }

    private static String cameraIdForLog() {
        try {
            String id = PreferenceKeys.getCameraID();
            return id == null ? "unknown" : id;
        } catch (Throwable ignored) {
            return "unknown";
        }
    }

    private ArrayList<Float> collectPreviewMidtones(Bitmap bitmap) {
        int w = bitmap.getWidth(), h = bitmap.getHeight();
        int[] pixels = new int[w * h];
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h);
        ArrayList<Float> luma = new ArrayList<>();
        for (int c : pixels) {
            float r = srgbDecode(((c >> 16) & 0xff) / 255.0f);
            float g = srgbDecode(((c >> 8) & 0xff) / 255.0f);
            float b = srgbDecode((c & 0xff) / 255.0f);
            float y = 0.2126f * r + 0.7152f * g + 0.0722f * b;
            if (Float.isFinite(y) && y > 0.025f && y < 0.975f) luma.add(y);
        }
        Collections.sort(luma);
        return trimMiddle(luma, 0.25f, 0.50f);
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
            iris26584CandidateGuideGrid = new float[previewW * previewH];
            java.util.Arrays.fill(iris26584CandidateGuideGrid, Float.NaN);
            iris26584CandidateGridWidth = previewW;
            iris26584CandidateGridHeight = previewH;
            int pixelIndex = 0;
            while (fb.remaining() >= 4) {
                float r = fb.get(), g = fb.get(), b = fb.get();
                fb.get();
                if (Float.isFinite(r) && Float.isFinite(g) && Float.isFinite(b)) {
                    r = Math.max(0.0f, r); g = Math.max(0.0f, g); b = Math.max(0.0f, b);
                    float y = luma(r, g, b);
                    if (y > 1.0e-4f && y < 8.0f) {
                        all.add(new RgbSample(r, g, b));
                        if (pixelIndex < iris26584CandidateGuideGrid.length) {
                            iris26584CandidateGuideGrid[pixelIndex] = Math.max(r, Math.max(g, b));
                        }
                    }
                }
                pixelIndex++;
            }
            if (!all.isEmpty()) {
                iris26582CandidateGuides.clear();
                for (RgbSample s : all) {
                    iris26582CandidateGuides.add(Math.max(s.r, Math.max(s.g, s.b)));
                }
                Collections.sort(iris26582CandidateGuides);
                int p95 = Math.max(0, Math.min(iris26582CandidateGuides.size() - 1,
                        Math.round((iris26582CandidateGuides.size() - 1) * 0.95f)));
                int p99 = Math.max(0, Math.min(iris26582CandidateGuides.size() - 1,
                        Math.round((iris26582CandidateGuides.size() - 1) * 0.99f)));
                int p995 = Math.max(0, Math.min(iris26582CandidateGuides.size() - 1,
                        Math.round((iris26582CandidateGuides.size() - 1) * 0.995f)));
                int p998 = Math.max(0, Math.min(iris26582CandidateGuides.size() - 1,
                        Math.round((iris26582CandidateGuides.size() - 1) * 0.998f)));
                iris26582CandidateP95Guide = iris26582CandidateGuides.get(p95);
                iris26550CandidateP99Guide = iris26582CandidateGuides.get(p99);
                iris26583CandidateP995Guide = iris26582CandidateGuides.get(p995);
                iris26583CandidateP998Guide = iris26582CandidateGuides.get(p998);
            }
            ToneDecision iris26583MeterTone = iris26583ToneDecision(1.0f);
            all.sort(Comparator.comparingDouble(s ->
                    presentedLuma(s, 1.0f, iris26583MeterTone.adaptiveSceneWhite)));
            int from = Math.max(0, Math.round((all.size() - 1) * 0.25f));
            int to = Math.min(all.size(), Math.max(from + 1,
                    Math.round((all.size() - 1) * 0.50f) + 1));
            return new ArrayList<>(all.subList(from, to));
        } finally {
            if (probe != null) try { probe.close(); } catch (Throwable ignored) {}
            GLES30.glBindFramebuffer(GL_FRAMEBUFFER, oldFramebuffer[0]);
        }
    }

    private static ArrayList<Float> trimMiddle(ArrayList<Float> sorted, float lo, float hi) {
        if (sorted.isEmpty()) return sorted;
        int from = Math.max(0, Math.round((sorted.size() - 1) * lo));
        int to = Math.min(sorted.size(), Math.max(from + 1,
                Math.round((sorted.size() - 1) * hi) + 1));
        return new ArrayList<>(sorted.subList(from, to));
    }

    private static float medianLogLuma(ArrayList<Float> values) {
        ArrayList<Float> logs = new ArrayList<>(values.size());
        for (float value : values) {
            logs.add(log2(Math.max(value, 1.0e-5f)));
        }
        Collections.sort(logs);
        return medianSorted(logs);
    }

    private float exposureError(ArrayList<RgbSample> samples, float ev, float targetLog) {
        float gain = (float)Math.pow(2.0, ev);
        ToneDecision tone = iris26583ToneDecision(gain);
        ArrayList<Float> logs = new ArrayList<>(samples.size());
        for (RgbSample sample : samples) {
            logs.add(log2(Math.max(presentedLuma(sample, gain, tone.adaptiveSceneWhite), 1.0e-5f)));
        }
        Collections.sort(logs);
        return medianSorted(logs) - targetLog;
    }

    private float solveBounded(ArrayList<RgbSample> samples, float targetLog,
                                      float e0, float eMinus, float ePlus) {
        float slope = ePlus - eMinus;
        float guess = Math.abs(slope) > 1.0e-4f
                ? clamp(-e0 / slope, MIN_EV, MAX_EV)
                : 0.0f;
        float bestEv = guess;
        float bestErr = Math.abs(exposureError(samples, guess, targetLog));

        float lo = MIN_EV, hi = MAX_EV;
        float flo = exposureError(samples, lo, targetLog);
        float fhi = exposureError(samples, hi, targetLog);
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
            float fx = exposureError(samples, x, targetLog);
            if (Math.abs(fx) < bestErr) { bestErr = Math.abs(fx); bestEv = x; }
            if (Math.abs(fx) < 0.01f) break;
            if (Math.signum(fx) == Math.signum(flo)) { lo = x; flo = fx; }
            else { hi = x; fhi = fx; }
        }
        return clamp(bestEv, MIN_EV, MAX_EV);
    }

    private static final class ToneDecision {
        final float baseSceneWhite;
        final float adaptiveSceneWhite;
        final float clippedFraction;
        final float projectedBroadNearFraction;
        final float projectedNearFraction;
        final float projectedHardFraction;
        final float projectedBroadTailStrength;
        final float compactTailStrength;
        final float adaptiveStrength;
        final float continuousTailPressure;
        final float continuousTailStrength;
        final int structuredPixels;
        final int structuredCells;
        final float structuredGuide;
        final float structuredStrength;
        final float floor26583SceneWhite;
        ToneDecision(float baseSceneWhite, float adaptiveSceneWhite,
                     float clippedFraction, float projectedBroadNearFraction,
                     float projectedNearFraction, float projectedHardFraction,
                     float projectedBroadTailStrength, float compactTailStrength,
                     float adaptiveStrength, float continuousTailPressure,
                     float continuousTailStrength, int structuredPixels, int structuredCells,
                     float structuredGuide, float structuredStrength, float floor26583SceneWhite) {
            this.baseSceneWhite = baseSceneWhite;
            this.adaptiveSceneWhite = adaptiveSceneWhite;
            this.clippedFraction = clippedFraction;
            this.projectedBroadNearFraction = projectedBroadNearFraction;
            this.projectedNearFraction = projectedNearFraction;
            this.projectedHardFraction = projectedHardFraction;
            this.projectedBroadTailStrength = projectedBroadTailStrength;
            this.compactTailStrength = compactTailStrength;
            this.adaptiveStrength = adaptiveStrength;
            this.continuousTailPressure = continuousTailPressure;
            this.continuousTailStrength = continuousTailStrength;
            this.structuredPixels = structuredPixels;
            this.structuredCells = structuredCells;
            this.structuredGuide = structuredGuide;
            this.structuredStrength = structuredStrength;
            this.floor26583SceneWhite = floor26583SceneWhite;
        }
    }

    private static float iris26583ProjectedOutputPeak(float sourceGuide, float gain, float sceneWhite) {
        float postGuide = Math.max(0.0f, sourceGuide) * Math.max(gain, 1.0e-6f);
        return clamp(MotionV2Render.iris26582MapHeadroom(postGuide, sceneWhite)
                * OUTPUT_EXPOSURE_SCALE, 0.0f, 1.0f);
    }

    private ToneDecision iris26583ToneDecision(float gain) {
        float baseWhite = MotionV2Render.iris26582BaseSceneWhite(gain);

        /* Preserve the exact successful 26582 broad owner as a floor, never as the sole vote. */
        float legacyBroadClippedFraction = 0.0f;
        if (!iris26582CandidateGuides.isEmpty()) {
            float sourceThreshold = baseWhite / Math.max(gain, 1.0e-6f);
            int lo = 0, hi = iris26582CandidateGuides.size();
            while (lo < hi) {
                int mid = (lo + hi) >>> 1;
                if (iris26582CandidateGuides.get(mid) < sourceThreshold) lo = mid + 1;
                else hi = mid;
            }
            legacyBroadClippedFraction = (iris26582CandidateGuides.size() - lo)
                    / (float)iris26582CandidateGuides.size();
        }
        float legacyBroadWhite = MotionV2Render.iris26582AdaptiveSceneWhite(
                gain, iris26550CandidateP99Guide, legacyBroadClippedFraction);
        float legacyBroadStrength = MotionV2Render.iris26582AdaptiveStrength(legacyBroadClippedFraction);
        if (legacyBroadWhite <= baseWhite + 1.0e-6f) legacyBroadStrength = 0.0f;

        /* IRIS_26583_PROJECTED_BROAD_AND_COMPACT_TAIL_OWNER
         * Evaluate all max-channel samples through the requested viewfinder gain and exact baseline
         * tone curve. The broad vote starts before hard clipping so office windows/cloud fields get
         * headroom before their upper tones crowd together. The compact vote remains population-
         * gated so a tiny lamp/specular cannot pull the global curve.
         */
        float projectedBroadNearFraction = 0.0f;
        float projectedNearFraction = 0.0f;
        float projectedHardFraction = 0.0f;
        if (!iris26582CandidateGuides.isEmpty()) {
            int broadNear = 0, near = 0, hard = 0;
            for (float guide : iris26582CandidateGuides) {
                float projected = iris26583ProjectedOutputPeak(guide, gain, baseWhite);
                if (projected >= MotionV2Render.IRIS_26583_PROJECTED_BROAD_NEAR_CEILING) broadNear++;
                if (projected >= MotionV2Render.IRIS_26583_PROJECTED_NEAR_CEILING) near++;
                if (projected >= MotionV2Render.IRIS_26583_PROJECTED_HARD_CEILING) hard++;
            }
            float n = (float)iris26582CandidateGuides.size();
            projectedBroadNearFraction = broadNear / n;
            projectedNearFraction = near / n;
            projectedHardFraction = hard / n;
        }

        float p99Projected = iris26583ProjectedOutputPeak(iris26550CandidateP99Guide, gain, baseWhite);
        float broadPopulation = smoothstep(MotionV2Render.IRIS_26583_BROAD_FRACTION_START,
                MotionV2Render.IRIS_26583_BROAD_FRACTION_FULL, projectedBroadNearFraction);
        float broadPressure = smoothstep(MotionV2Render.IRIS_26583_PROJECTED_BROAD_NEAR_CEILING,
                0.985f, p99Projected);
        float hardPopulation = smoothstep(MotionV2Render.IRIS_26583_BROAD_HARD_FRACTION_START,
                MotionV2Render.IRIS_26583_BROAD_HARD_FRACTION_FULL, projectedHardFraction);
        float projectedBroadStrength = Math.max(broadPopulation * broadPressure, 0.70f * hardPopulation);

        float p995BroadAssist = smoothstep(0.020f, 0.080f, projectedBroadNearFraction);
        float projectedBroadGuide = iris26550CandidateP99Guide;
        if (Float.isFinite(iris26583CandidateP995Guide) && Float.isFinite(projectedBroadGuide)) {
            projectedBroadGuide = mix(projectedBroadGuide,
                    Math.max(projectedBroadGuide, iris26583CandidateP995Guide),
                    0.45f * p995BroadAssist);
        }
        float projectedBroadRequiredWhite = MotionV2Render.iris26583RequiredSceneWhite(
                gain, projectedBroadGuide, MotionV2Render.IRIS_26583_BROAD_HIGHLIGHT_TARGET);
        float projectedBroadWhite = baseWhite
                + (projectedBroadRequiredWhite - baseWhite) * projectedBroadStrength;

        float broadWhite = Math.max(legacyBroadWhite, projectedBroadWhite);
        float broadStrength = Math.max(legacyBroadStrength, projectedBroadStrength);

        float p995Projected = iris26583ProjectedOutputPeak(iris26583CandidateP995Guide, gain, baseWhite);
        float compactSupport = smoothstep(MotionV2Render.IRIS_26583_COMPACT_FRACTION_START,
                MotionV2Render.IRIS_26583_COMPACT_FRACTION_FULL, projectedNearFraction);
        float compactPressure = smoothstep(0.965f, 0.995f, p995Projected);
        float compactStrength = compactSupport * compactPressure;
        float broadDominance = smoothstep(0.25f, 0.70f, broadStrength);
        compactStrength *= (1.0f - broadDominance);

        /* P99.8 may set the compact requested white only after P99.5 proves population support. */
        float p998Assist = smoothstep(0.006f, 0.020f, projectedNearFraction);
        float compactGuide = iris26583CandidateP995Guide;
        if (Float.isFinite(iris26583CandidateP998Guide) && Float.isFinite(compactGuide)) {
            compactGuide = mix(compactGuide, Math.max(compactGuide, iris26583CandidateP998Guide),
                    0.35f * p998Assist);
        }
        float compactRequiredWhite = MotionV2Render.iris26583RequiredSceneWhite(
                gain, compactGuide, MotionV2Render.IRIS_26583_COMPACT_HIGHLIGHT_TARGET);
        float compactWhite = baseWhite
                + (compactRequiredWhite - baseWhite) * compactStrength;

        float floor26583White = Math.max(broadWhite, compactWhite);
        float floor26583Strength = Math.max(broadStrength, compactStrength);

        /* IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER
         * 26583 remains the strict minimum. Above that floor, integrate the complete projected
         * high-tail continuously instead of requiring a percentile AND a population threshold.
         * Then add a population-independent spatial vote for a small but coherent 2-D highlight.
         * Both votes only increase sceneWhite; mapHeadroom still starts at linear 0.50 and applies
         * one uniform RGB scalar, so body/midtone and chroma ownership remain unchanged.
         */
        double pressureSum = 0.0;
        int pressureCount = 0;
        if (iris26584CandidateGuideGrid != null) {
            if (iris26584ProjectedGridScratch == null
                    || iris26584ProjectedGridScratch.length != iris26584CandidateGuideGrid.length) {
                iris26584ProjectedGridScratch = new float[iris26584CandidateGuideGrid.length];
            }
            java.util.Arrays.fill(iris26584ProjectedGridScratch, Float.NaN);
            for (int i = 0; i < iris26584CandidateGuideGrid.length; i++) {
                float guide = iris26584CandidateGuideGrid[i];
                if (!Float.isFinite(guide)) continue;
                float projected = iris26583ProjectedOutputPeak(guide, gain, baseWhite);
                iris26584ProjectedGridScratch[i] = projected;
                float q = smoothstep(0.885f, 0.995f, projected);
                pressureSum += q * q;
                pressureCount++;
            }
        } else {
            for (float guide : iris26582CandidateGuides) {
                float projected = iris26583ProjectedOutputPeak(guide, gain, baseWhite);
                float q = smoothstep(0.885f, 0.995f, projected);
                pressureSum += q * q;
                pressureCount++;
            }
        }
        float continuousTailPressure = pressureCount > 0
                ? (float)(pressureSum / pressureCount) : 0.0f;
        float continuousTailStrength = smoothstep(0.0015f, 0.024f, continuousTailPressure);
        float continuousGuide = iris26550CandidateP99Guide;
        float tailAssist995 = smoothstep(0.0015f, 0.010f, continuousTailPressure);
        float tailAssist998 = smoothstep(0.0030f, 0.020f, continuousTailPressure);
        if (Float.isFinite(iris26583CandidateP995Guide) && Float.isFinite(continuousGuide)) {
            continuousGuide = mix(continuousGuide,
                    Math.max(continuousGuide, iris26583CandidateP995Guide), 0.70f * tailAssist995);
        }
        if (Float.isFinite(iris26583CandidateP998Guide) && Float.isFinite(continuousGuide)) {
            continuousGuide = mix(continuousGuide,
                    Math.max(continuousGuide, iris26583CandidateP998Guide), 0.45f * tailAssist998);
        }
        float continuousRequiredWhite = MotionV2Render.iris26583RequiredSceneWhite(
                gain, continuousGuide, 0.958f);
        float continuousWhite = baseWhite
                + (continuousRequiredWhite - baseWhite) * continuousTailStrength;

        int structuredPixels = 0;
        int structuredCells = 0;
        float structuredGuide = Float.NaN;
        float structuredStrength = 0.0f;
        if (iris26584CandidateGuideGrid != null
                && iris26584CandidateGridWidth > 2 && iris26584CandidateGridHeight > 2
                && iris26584CandidateGuideGrid.length
                == iris26584CandidateGridWidth * iris26584CandidateGridHeight) {
            final int gw = iris26584CandidateGridWidth;
            final int gh = iris26584CandidateGridHeight;
            final int cellSize = 8;
            final int cellsX = (gw + cellSize - 1) / cellSize;
            final int cellsY = (gh + cellSize - 1) / cellSize;
            final int[] cellCounts = new int[cellsX * cellsY];
            /* IRIS_26585_STRUCTURED_HIGHLIGHT_SHAPE_TAIL
             * 26584 proved the coherent region exists, but P90/0.965 still allowed the
             * brightest shape-bearing part of neutral pots/practical lights to crowd at white.
             * Resolve the supported structured tail more finely and protect P98 instead.
             */
            final int[] hist = new int[256];
            int histTotal = 0;
            float histMaxGuide = 0.0f;
            for (int y = 1; y < gh - 1; y++) {
                for (int x = 1; x < gw - 1; x++) {
                    int idx = y * gw + x;
                    float guide = iris26584CandidateGuideGrid[idx];
                    if (!Float.isFinite(guide)) continue;
                    float projected = iris26584ProjectedGridScratch != null
                            ? iris26584ProjectedGridScratch[idx]
                            : iris26583ProjectedOutputPeak(guide, gain, baseWhite);
                    if (!Float.isFinite(projected) || projected < 0.945f) continue;
                    int neighborCount = 0;
                    float np = iris26584ProjectedGridScratch != null ? iris26584ProjectedGridScratch[idx - 1] : Float.NaN;
                    if (Float.isFinite(np) && np >= 0.925f) neighborCount++;
                    np = iris26584ProjectedGridScratch != null ? iris26584ProjectedGridScratch[idx + 1] : Float.NaN;
                    if (Float.isFinite(np) && np >= 0.925f) neighborCount++;
                    np = iris26584ProjectedGridScratch != null ? iris26584ProjectedGridScratch[idx - gw] : Float.NaN;
                    if (Float.isFinite(np) && np >= 0.925f) neighborCount++;
                    np = iris26584ProjectedGridScratch != null ? iris26584ProjectedGridScratch[idx + gw] : Float.NaN;
                    if (Float.isFinite(np) && np >= 0.925f) neighborCount++;
                    if (neighborCount < 1) continue;
                    structuredPixels++;
                    cellCounts[(y / cellSize) * cellsX + (x / cellSize)]++;
                    histMaxGuide = Math.max(histMaxGuide, guide);
                    int bin = Math.max(0, Math.min(hist.length - 1,
                            (int)Math.floor(Math.min(guide, 7.999f) * (hist.length / 8.0f))));
                    hist[bin]++;
                    histTotal++;
                }
            }
            for (int count : cellCounts) if (count >= 2) structuredCells++;
            if (histTotal > 0) {
                int target = Math.max(1, (int)Math.ceil(histTotal * 0.98));
                int accum = 0, chosen = 0;
                for (int b = 0; b < hist.length; b++) {
                    accum += hist[b];
                    if (accum >= target) { chosen = b; break; }
                }
                structuredGuide = Math.min(histMaxGuide, (chosen + 1.0f) * (8.0f / hist.length));
                float pixelStrength = smoothstep(2.0f, 18.0f, structuredPixels);
                float cellStrength = smoothstep(1.0f, 5.0f, structuredCells);
                structuredStrength = Math.max(pixelStrength, cellStrength);
            }
        }
        float structuredWhite = baseWhite;
        if (structuredStrength > 0.0f && Float.isFinite(structuredGuide)) {
            float structuredRequiredWhite = MotionV2Render.iris26583RequiredSceneWhite(
                    gain, structuredGuide, 0.945f);
            structuredWhite = baseWhite
                    + (structuredRequiredWhite - baseWhite) * structuredStrength;
        }

        float adaptiveWhite = Math.max(floor26583White,
                Math.max(continuousWhite, structuredWhite));
        float combinedStrength = Math.max(floor26583Strength,
                Math.max(continuousTailStrength, structuredStrength));
        if (adaptiveWhite <= baseWhite + 1.0e-6f) combinedStrength = 0.0f;
        return new ToneDecision(baseWhite, adaptiveWhite, legacyBroadClippedFraction,
                projectedBroadNearFraction, projectedNearFraction, projectedHardFraction,
                projectedBroadStrength, compactStrength, combinedStrength,
                continuousTailPressure, continuousTailStrength, structuredPixels, structuredCells,
                structuredGuide, structuredStrength, floor26583White);
    }

    /* IRIS_26582_SOLVER_RENDER_TONE_PARITY
     * Exact scalar tone/gamut model used by motionv2/render.glsl. The removed 26581
     * neutral-to-white and overflow-to-white solver approximations were stale and were not
     * present in the final renderer.
     */
    private static float presentedLuma(RgbSample sample, float gain, float sceneWhite) {
        float r = Math.max(0.0f, sample.r * gain);
        float g = Math.max(0.0f, sample.g * gain);
        float b = Math.max(0.0f, sample.b * gain);
        float y = luma(r, g, b);
        float peak = Math.max(r, Math.max(g, b));
        float guide = Math.max(y, peak);
        if (guide > 1.0e-7f) {
            float mappedGuide = MotionV2Render.iris26582MapHeadroom(guide, sceneWhite);
            float scale = mappedGuide / guide;
            r *= scale;
            g *= scale;
            b *= scale;
        }
        r *= OUTPUT_EXPOSURE_SCALE;
        g *= OUTPUT_EXPOSURE_SCALE;
        b *= OUTPUT_EXPOSURE_SCALE;
        float outPeak = Math.max(r, Math.max(g, b));
        if (outPeak > 1.0f) {
            r /= outPeak;
            g /= outPeak;
            b /= outPeak;
        }
        return clamp(luma(r, g, b), 0.0f, 1.0f);
    }

    private static float srgbDecode(float x) {
        x = clamp(x, 0.0f, 1.0f);
        return x <= 0.04045f
                ? x / 12.92f
                : (float)Math.pow((x + 0.055f) / 1.055f, 2.4);
    }

    private static float luma(float r, float g, float b) {
        // Candidate samples are already linear Display-P3. Preview sampling above remains
        // explicitly decoded sRGB/Rec.709 so the meter compares each source in its own primaries.
        return 0.22897456f * r + 0.69173852f * g + 0.07928691f * b;
    }

    private static float medianSorted(ArrayList<Float> sorted) {
        int n = sorted.size();
        if (n == 0) return Float.NaN;
        if ((n & 1) != 0) return sorted.get(n / 2);
        return 0.5f * (sorted.get(n / 2 - 1) + sorted.get(n / 2));
    }

    private static float log2(float x) { return (float)(Math.log(x) / LOG2); }
    private static float clamp(float x, float lo, float hi) { return Math.max(lo, Math.min(hi, x)); }
    private static float mix(float a, float b, float t) { return a + (b - a) * t; }
    private static float smoothstep(float a, float b, float x) {
        float t = clamp((x - a) / Math.max(b - a, 1.0e-6f), 0f, 1f);
        return t * t * (3.0f - 2.0f * t);
    }
}
