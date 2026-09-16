package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.opengl.scripts.GLHistogram;
import com.particlesdevs.photoncamera.util.BufferUtils;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.MotionTrace;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26650_PHOTON_HIGHLIGHT_COMPRESSION_ANALYSIS_OWNER
 *
 * Motion-only analysis owner for the user-visible Settings -> Photo Settings -> Highlight
 * Compression switch.  The camera RGB carrier remains Iris-owned and is never replaced by the
 * Photon tone pipeline.  Instead this node reconstructs Photon's complete common
 * AutoExposureCurve analysis on the exact pre-color Sabre camera-linear RGB domain, builds both
 * the Highlight Compression OFF and ON curves, and publishes those two curves to
 * MotionV2ColorTransform.  That downstream owner applies only ON/OFF, so OFF is byte-for-pixel
 * equivalent to the successful 26648 presentation path while ON reproduces the Photon toggle's
 * exact differential without replacing Iris color, exposure, SHORT fusion, VGN, or UHDR owners.
 *
 * Domain bridge proof: Photon Bayer2Float's AutoExposureCurve input is cameraRGB/whitePoint and
 * GLHistogram multiplies each channel by whitePoint (1/extent).  The products cancel exactly,
 * therefore histogramming Iris' pre-WB cameraRGB with exposure=1 produces the same bin ownership;
 * mapped bin values are still expanded by extent=1/whitePoint exactly as Photon does.
 */
public final class MotionV2PhotonHighlightCompression extends Node {
    private static final int HIST_SIZE = 256;
    private static final int CURVE_SIZE = 1024;

    private static final float TARGET = 128.0f;
    private static final float NOISE_MAX = 0.05f;
    private static final float GAIN_MAX = 9.0f;
    private static final float WHITE_APPLY = 0.8f;
    private static final float FILL_COEFFICIENT = 0.99f;
    private static final float APPLY_GAMMA_MIX = 0.05f;
    private static final float KNEE_MAX = 0.90f;
    private static final float KNEE_MIN = 0.55f;
    private static final float KNEE_REF = 0.10f;
    private static final float CLIP_TOLERANCE = 0.03f;

    private final boolean enabled;

    public MotionV2PhotonHighlightCompression(boolean enabled) {
        super("", "MotionV2PhotonHighlightCompression");
        this.enabled = enabled;
    }

    @Override public void Compile() {}
    @Override public void AfterRun() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("26650 Highlight Compression owner is Motion-only");
        }
        if (previousNode == null || previousNode.WorkingTexture == null) {
            throw new IllegalStateException("26650 missing pre-color Sabre RGB input");
        }

        final PostPipeline pipeline = (PostPipeline) basePipeline;
        clearPublishedCurves(pipeline);

        final float[] wp = basePipeline.mParameters.whitePoint;
        requireWhitePoint(wp);
        final float noiseS = basePipeline.mParameters.motionV2WronskiNoiseS;
        final float noiseO = basePipeline.mParameters.motionV2WronskiNoiseO;
        if (!Float.isFinite(noiseS) || !Float.isFinite(noiseO) || noiseS <= 0.0f || noiseO < 0.0f) {
            throw new IllegalStateException("26650 invalid Motion noise authority S=" + noiseS + " O=" + noiseO);
        }

        final float[] extent = new float[3];
        for (int c = 0; c < 3; ++c) extent[c] = 1.0f / wp[c];
        final float gCeiling = (float)Math.pow(
                (Math.cbrt(extent[0]) + Math.cbrt(extent[2])) * 0.5, 3.0);
        if (gCeiling > extent[1]) extent[1] = gCeiling;

        final int[][] hist;
        GLHistogram histogram = new GLHistogram(glProg, HIST_SIZE);
        try {
            histogram.Rc = true;
            histogram.Gc = true;
            histogram.Bc = true;
            histogram.Ac = false;
            histogram.resize = 3;
            // Exact domain bridge described in the class comment: Photon WB * histogram exposure
            // cancels to the un-WB cameraRGB carrier that Iris has here.
            histogram.exposure[0] = 1.0f;
            histogram.exposure[1] = 1.0f;
            histogram.exposure[2] = 1.0f;
            hist = histogram.Compute(previousNode.WorkingTexture);
        } finally {
            histogram.close();
        }

        final int normR = sum(hist[0]);
        final int normG = sum(hist[1]);
        final int normB = sum(hist[2]);
        if (normR <= 0 || normG <= 0 || normB <= 0) {
            throw new IllegalStateException("26650 empty RGB histogram");
        }

        final float[][] mapped = new float[3][HIST_SIZE];
        remapHistogram(mapped, extent, 1.0f);

        float avgPass1 = estimateAvg(hist, mapped, normR, normG, normB);
        GainClamp gain1 = clampGain(TARGET / Math.max(avgPass1, 1.0e-4f), noiseS, noiseO);
        float mpyPass1 = gain1.value;
        float sceneWhitePass1 = searchWhite(hist, mapped, normR, normG, normB, mpyPass1);

        float adaptiveWhitePoint = 1.0f;
        float avgFinal = avgPass1;
        float mpyPreNorm = mpyPass1;
        float sceneWhiteFinal = sceneWhitePass1;
        GainClamp gain2 = gain1;
        if (sceneWhitePass1 > 1.0f) {
            adaptiveWhitePoint = srgbDecodeExtended(sceneWhitePass1);
            remapHistogram(mapped, extent, adaptiveWhitePoint);
            avgFinal = estimateAvg(hist, mapped, normR, normG, normB);
            gain2 = clampGain(TARGET / Math.max(avgFinal, 1.0e-4f), noiseS, noiseO);
            mpyPreNorm = gain2.value;
            sceneWhiteFinal = searchWhite(hist, mapped, normR, normG, normB, mpyPreNorm);
        }

        float normL = 0.0f;
        float normRr = 0.0f;
        for (int i = 0; i < HIST_SIZE; ++i) {
            float val = (i / (HIST_SIZE - 1.0f)) * mpyPreNorm;
            normL += Math.min(val, 1.0f);
            normRr += (val * (1.0f + val / (mpyPreNorm * mpyPreNorm))) / (1.0f + val);
        }
        float mpy = mpyPreNorm * normL / Math.max(normRr, 1.0e-8f);
        float whiteMax = sceneWhiteFinal * mpy;
        float whiteEff = mix(mpy, whiteMax, WHITE_APPLY);

        long clipped = 0L;
        long total = (long)normR + normG + normB;
        for (int i = 0; i < HIST_SIZE; ++i) {
            for (int c = 0; c < 3; ++c) {
                float x = mapped[c][i] / (HIST_SIZE - 1.0f);
                float g = mix(x, (float)Math.sqrt(Math.max(x, 0.0f)), APPLY_GAMMA_MIX);
                float v = g * mpy;
                float r = v * (1.0f + v / (whiteEff * whiteEff)) / (1.0f + v);
                if (r > 1.0f + CLIP_TOLERANCE) clipped += (long)hist[c][i];
            }
        }
        float clippedFraction = total > 0L ? clipped / (float)total : 0.0f;
        float kneeLo = Math.min(KNEE_MIN, KNEE_MAX);
        float knee = mix(KNEE_MAX, kneeLo,
                Math.min(clippedFraction / Math.max(KNEE_REF, 1.0e-4f), 1.0f));

        float[] curveOff = new float[CURVE_SIZE];
        float[] curveOn = new float[CURVE_SIZE];
        float maxDelta = 0.0f;
        int activeSamples = 0;
        for (int i = 0; i < CURVE_SIZE; ++i) {
            float x = i / (CURVE_SIZE - 1.0f);
            float g = mix(x, (float)Math.sqrt(x), APPLY_GAMMA_MIX);
            float r = g * mpy;
            r = r * (1.0f + r / (whiteEff * whiteEff)) / (1.0f + r);
            float off = mix(r, r * r, APPLY_GAMMA_MIX);
            float on = softShoulder(off, knee);
            off = clamp01(off);
            on = clamp01(on);
            curveOff[i] = off;
            curveOn[i] = on;
            float d = off - on;
            if (d > 1.0e-7f) ++activeSamples;
            maxDelta = Math.max(maxDelta, d);
        }

        pipeline.motionV2PhotonHighlightCompressionEnabled = enabled;
        pipeline.motionV2PhotonAdaptiveWhitePoint = adaptiveWhitePoint;
        pipeline.motionV2PhotonHighlightKnee = enabled ? knee : 1.0f;
        pipeline.motionV2PhotonHighlightClippedFraction = clippedFraction;

        if (enabled) {
            pipeline.motionV2PhotonCurveOff = new GLTexture(
                    new Point(CURVE_SIZE, 1), new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    BufferUtils.getFrom(curveOff), GL_LINEAR, GL_CLAMP_TO_EDGE);
            pipeline.motionV2PhotonCurveOn = new GLTexture(
                    new Point(CURVE_SIZE, 1), new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    BufferUtils.getFrom(curveOn), GL_LINEAR, GL_CLAMP_TO_EDGE);
        }

        final String line = "IRIS_26650_PHOTON_HIGHLIGHT_COMPRESSION"
                + " enabled=" + enabled
                + " owner=preColorSabreCameraRgb"
                + " toggleApplication=exactOnOverOffCurveRatio"
                + " photonCommonAnalysis=true"
                + " histSize=" + HIST_SIZE
                + " histogramResize=3"
                + " domainBridge=unbalancedCameraRgbEquivalent"
                + " extent=" + extent[0] + "," + extent[1] + "," + extent[2]
                + " avgPass1=" + avgPass1
                + " mpyPass1=" + mpyPass1
                + " sceneWhitePass1=" + sceneWhitePass1
                + " adaptiveWhitePoint=" + adaptiveWhitePoint
                + " avgFinal=" + avgFinal
                + " mpyPreNorm=" + mpyPreNorm
                + " reinhardNormL=" + normL
                + " reinhardNormR=" + normRr
                + " mpyFinal=" + mpy
                + " sceneWhiteFinal=" + sceneWhiteFinal
                + " whiteMax=" + whiteMax
                + " whiteEff=" + whiteEff
                + " clippedFraction=" + clippedFraction
                + " appliedKnee=" + (enabled ? knee : 1.0f)
                + " potentialKnee=" + knee
                + " clipTolerance=" + CLIP_TOLERANCE
                + " kneeMax=" + KNEE_MAX
                + " kneeMin=" + KNEE_MIN
                + " kneeRef=" + KNEE_REF
                + " applyGammaMix=" + APPLY_GAMMA_MIX
                + " whiteApply=" + WHITE_APPLY
                + " fillCoefficient=" + FILL_COEFFICIENT
                + " noiseSource=motionV2WronskiCamera2"
                + " noiseS=" + noiseS
                + " noiseO=" + noiseO
                + " gainNoiseMaxPass1=" + gain1.noiseLimit
                + " gainNoiseClampedPass1=" + gain1.noiseClamped
                + " gainMaxClampedPass1=" + gain1.maxClamped
                + " gainNoiseMaxFinal=" + gain2.noiseLimit
                + " gainNoiseClampedFinal=" + gain2.noiseClamped
                + " gainMaxClampedFinal=" + gain2.maxClamped
                + " curveOffEnd=" + curveOff[CURVE_SIZE - 1]
                + " curveOnEnd=" + curveOn[CURVE_SIZE - 1]
                + " curveActiveSamples=" + activeSamples
                + " curveMaxDelta=" + maxDelta
                + " shortFusionUnchanged=true"
                + " irisColorUnchanged=true"
                + " heicUhHdrUnchanged=true";
        Log.i(Name, line);
        try { MotionTrace.processingState("IRIS_26650_PHOTON_HIGHLIGHT_COMPRESSION", line); }
        catch (Throwable ignored) {}

        WorkingTexture = previousNode.WorkingTexture;
        glProg.closed = true;
    }

    private static void clearPublishedCurves(PostPipeline p) {
        if (p.motionV2PhotonCurveOff != null) try { p.motionV2PhotonCurveOff.close(); } catch (Throwable ignored) {}
        if (p.motionV2PhotonCurveOn != null) try { p.motionV2PhotonCurveOn.close(); } catch (Throwable ignored) {}
        p.motionV2PhotonCurveOff = null;
        p.motionV2PhotonCurveOn = null;
        p.motionV2PhotonHighlightCompressionEnabled = false;
        p.motionV2PhotonAdaptiveWhitePoint = 1.0f;
        p.motionV2PhotonHighlightKnee = 1.0f;
        p.motionV2PhotonHighlightClippedFraction = 0.0f;
    }

    private static void requireWhitePoint(float[] wp) {
        if (wp == null || wp.length < 3) throw new IllegalStateException("26650 missing camera neutral");
        for (int i = 0; i < 3; ++i) {
            if (!Float.isFinite(wp[i]) || wp[i] <= 0.0f || wp[i] > 1.0f) {
                throw new IllegalStateException("26650 invalid camera neutral[" + i + "]=" + wp[i]);
            }
        }
    }

    private static int sum(int[] h) {
        long s = 0L;
        for (int v : h) s += v;
        if (s > Integer.MAX_VALUE) throw new IllegalStateException("26650 histogram count overflow");
        return (int)s;
    }

    private static void remapHistogram(float[][] mapped, float[] extent, float adaptiveWhitePoint) {
        float awp = Math.max(adaptiveWhitePoint, 1.0e-8f);
        for (int c = 0; c < 3; ++c) {
            for (int i = 0; i < HIST_SIZE; ++i) {
                float linear = (i + 0.5f) / (HIST_SIZE - 1.0f) * extent[c] / awp;
                mapped[c][i] = srgbEncodeExtended(linear) * (HIST_SIZE - 1.0f);
            }
        }
    }

    private static float estimateAvg(int[][] result, float[][] mapped,
                                     int histNormR, int histNormG, int histNormB) {
        float cap = HIST_SIZE - 1.0f;
        float sum = 0.0f;
        int cnt = 0;
        int total = histNormR + histNormG + histNormB;
        for (int i = 0; i < HIST_SIZE - 1; ++i) {
            if (cnt > total * FILL_COEFFICIENT) break;
            sum += result[0][i] * Math.min(mapped[0][i], cap)
                    + result[1][i] * Math.min(mapped[1][i], cap)
                    + result[2][i] * Math.min(mapped[2][i], cap);
            cnt += result[0][i] + result[1][i] + result[2][i];
        }
        return cnt > 0 ? sum / cnt : TARGET;
    }

    private static float searchWhite(int[][] result, float[][] mapped,
                                     int histNormR, int histNormG, int histNormB, float mpy) {
        float white = Float.MAX_VALUE;
        for (int c = 0; c < 3; ++c) {
            int histNorm = c == 0 ? histNormR : (c == 1 ? histNormG : histNormB);
            float sum = 0.0f;
            int cnt = 0;
            double lower = Math.max(HIST_SIZE * 2.0 / 3.0, HIST_SIZE / (mpy + 0.001));
            for (int i = HIST_SIZE - 1; i > lower; --i) {
                sum += result[c][i] * mapped[c][i];
                cnt += result[c][i];
                if (cnt > histNorm * 0.005f) break;
            }
            if (cnt == 0) {
                sum = HIST_SIZE - 1.0f;
                cnt = 1;
            }
            white = Math.min(white, (sum / cnt) / HIST_SIZE);
        }
        return white;
    }

    private static GainClamp clampGain(float requested, float noiseS, float noiseO) {
        float mpy = requested;
        float gainNoiseMax = (float)(NOISE_MAX / Math.sqrt(noiseS * 0.5 + noiseO));
        gainNoiseMax = Math.max(gainNoiseMax, 1.0f);
        boolean noiseClamped = false;
        boolean maxClamped = false;
        if (mpy > gainNoiseMax) { mpy = gainNoiseMax; noiseClamped = true; }
        if (mpy > GAIN_MAX) { mpy = GAIN_MAX; maxClamped = true; }
        return new GainClamp(mpy, gainNoiseMax, noiseClamped, maxClamped);
    }

    private static float srgbEncodeExtended(float v) {
        if (v <= 0.0f) return 0.0f;
        return v <= 0.0031308f ? v * 12.92f
                : 1.055f * (float)Math.pow(v, 1.0f / 2.4f) - 0.055f;
    }

    private static float srgbDecodeExtended(float v) {
        return v <= 0.0031308f ? v / 12.92f
                : (float)Math.pow((v + 0.055f) / 1.055f, 2.4f);
    }

    private static float softShoulder(float x, float knee) {
        if (x <= knee) return x;
        float t = x - knee;
        float s = 1.0f - knee;
        float g = t / s;
        return knee + s * g * g;
    }

    private static float clamp01(float v) { return Math.min(Math.max(v, 0.0f), 1.0f); }
    private static float mix(float a, float b, float t) { return a + (b - a) * t; }

    private static final class GainClamp {
        final float value;
        final float noiseLimit;
        final boolean noiseClamped;
        final boolean maxClamped;
        GainClamp(float value, float noiseLimit, boolean noiseClamped, boolean maxClamped) {
            this.value = value;
            this.noiseLimit = noiseLimit;
            this.noiseClamped = noiseClamped;
            this.maxClamped = maxClamped;
        }
    }
}
