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
 * IRIS_26656_PHOTON_NEW_EXPOSURE_AUTHORITY
 *
 * Motion-only faithful bridge of the uploaded Photon APK's AutoExposureCurve used by the
 * selected "New (simplified)" tone pipeline. Capture policy is deliberately outside this node:
 * shutter/ISO/frame count/prebuffer/Sabre are already frozen before this point.
 *
 * Photon Bayer2Float feeds AutoExposureCurve with cameraRGB/whitePoint while GLHistogram scales
 * each channel by whitePoint. Iris Sabre reaches this node as the equivalent pre-WB cameraRGB,
 * therefore histogram exposure=1 is the exact algebraic bridge. The Photon equations, defaults,
 * adaptive-white re-analysis, Reinhard normalization, clipped-fraction knee and 1024-sample curve
 * are otherwise preserved. The only noise plumbing substitution is required by Iris ownership:
 * Photon's gain-noise clamp consumes the frozen Camera2/Wronski S/O values rather than reviving
 * Photon NoiseModeler.
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

    public MotionV2PhotonHighlightCompression() { super("", "MotionV2PhotonNewExposure"); }
    @Override public void Compile() {}
    @Override public void AfterRun() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("26656 Photon New exposure is Motion-only");
        }
        if (previousNode == null || previousNode.WorkingTexture == null) {
            throw new IllegalStateException("26656 missing pre-color Sabre RGB input");
        }
        final PostPipeline pipeline = (PostPipeline) basePipeline;

        final float[] wp = basePipeline.mParameters.whitePoint;
        requireWhitePoint(wp);
        final float noiseS = basePipeline.mParameters.motionV2WronskiNoiseS;
        final float noiseO = basePipeline.mParameters.motionV2WronskiNoiseO;
        if (!Float.isFinite(noiseS) || !Float.isFinite(noiseO) || noiseS <= 0.0f || noiseO < 0.0f) {
            throw new IllegalStateException("26656 invalid Wronski noise S=" + noiseS + " O=" + noiseO);
        }

        final float[] extent = new float[3];
        for (int c = 0; c < 3; c++) extent[c] = 1.0f / wp[c];
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
            throw new IllegalStateException("26656 empty Photon New RGB histogram");
        }

        final float[][] mapped = new float[3][HIST_SIZE];
        remapHistogram(mapped, extent, 1.0f);
        float avg = estimateAvg(hist, mapped, normR, normG, normB);
        GainClamp gain = clampGain(TARGET / Math.max(avg, 1.0e-4f), noiseS, noiseO);
        float mpy = gain.value;
        float sceneWhite = searchWhite(hist, mapped, normR, normG, normB, mpy);

        float adaptiveWhitePoint = 1.0f;
        if (sceneWhite > 1.0f) {
            adaptiveWhitePoint = srgbDecodeExtended(sceneWhite);
            remapHistogram(mapped, extent, adaptiveWhitePoint);
            avg = estimateAvg(hist, mapped, normR, normG, normB);
            gain = clampGain(TARGET / Math.max(avg, 1.0e-4f), noiseS, noiseO);
            mpy = gain.value;
            sceneWhite = searchWhite(hist, mapped, normR, normG, normB, mpy);
        }

        float normL = 0.0f;
        float normRr = 0.0f;
        for (int i = 0; i < HIST_SIZE; i++) {
            float val = (i / (HIST_SIZE - 1.0f)) * mpy;
            normL += Math.min(val, 1.0f);
            normRr += (val * (1.0f + val / (mpy * mpy))) / (1.0f + val);
        }
        mpy *= normL / Math.max(normRr, 1.0e-8f);
        final float whiteMax = sceneWhite * mpy;
        final float whiteEff = mix(mpy, whiteMax, WHITE_APPLY);

        long clipped = 0L;
        final long total = (long)normR + normG + normB;
        for (int i = 0; i < HIST_SIZE; i++) {
            for (int c = 0; c < 3; c++) {
                float x = mapped[c][i] / (HIST_SIZE - 1.0f);
                float g = mix(x, (float)Math.sqrt(Math.max(x, 0.0f)), APPLY_GAMMA_MIX);
                float v = g * mpy;
                float r = v * (1.0f + v / (whiteEff * whiteEff)) / (1.0f + v);
                if (r > 1.0f + CLIP_TOLERANCE) clipped += (long)hist[c][i];
            }
        }
        final float clippedFraction = total > 0 ? clipped / (float)total : 0.0f;
        final float kneeLo = Math.min(KNEE_MIN, KNEE_MAX);
        final float knee = mix(KNEE_MAX, kneeLo,
                Math.min(clippedFraction / Math.max(KNEE_REF, 1.0e-4f), 1.0f));

        final float[] curve = new float[CURVE_SIZE];
        for (int i = 0; i < CURVE_SIZE; i++) {
            float x = i / (CURVE_SIZE - 1.0f);
            float g = mix(x, (float)Math.sqrt(x), APPLY_GAMMA_MIX);
            float r = g * mpy;
            r = r * (1.0f + r / (whiteEff * whiteEff)) / (1.0f + r);
            float o = mix(r, r * r, APPLY_GAMMA_MIX);
            if (knee < 1.0f) o = softShoulder(o, knee);
            curve[i] = clamp01(o);
        }

        GLTexture exposureCurve = new GLTexture(
                new Point(CURVE_SIZE, 1),
                new GLFormat(GLFormat.DataType.FLOAT_16, 1),
                BufferUtils.getFrom(curve), GL_LINEAR, GL_CLAMP_TO_EDGE);
        pipeline.motionV2PhotonAdaptiveWhitePoint = adaptiveWhitePoint;
        pipeline.motionV2PhotonHighlightCompressionEnabled = true;
        pipeline.motionV2PhotonHighlightKnee = knee;
        pipeline.motionV2PhotonHighlightClippedFraction = clippedFraction;

        /* Uploaded Photon ModernInitial applies adaptive-white + AutoExposureCurve before its
         * color matrices.  Iris owns those color matrices, so reproduce only the common scalar
         * here on the equivalent pre-color Sabre cameraRGB carrier.  Photon evaluates the scalar
         * on cameraRGB/whitePoint; after its later NEUTRALPOINT multiply this is exactly cameraRGB
         * times that scalar.  The output below is therefore the exact scalar bridge while Iris
         * color/chroma remains byte-unchanged in the following node. */
        GLTexture preColor = basePipeline.getMain();
        try {
            glProg.useAssetProgram("motionv2/photon_new_precolor");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setTexture("ExposureCurve", exposureCurve);
            glProg.setVar("neutralPoint", wp);
            glProg.setVar("adaptiveWhitePoint", Math.max(1.0f, adaptiveWhitePoint));
            glProg.drawBlocks(preColor);
            glProg.close();
        } finally {
            try { exposureCurve.close(); } catch (Throwable ignored) {}
        }

        final String line = "IRIS_26656_PHOTON_NEW_EXPOSURE"
                + " owner=uploadedPhotonAutoExposureCurve"
                + " tonePipeline=NEW"
                + " capturePolicyAffected=false"
                + " histogramDomain=preColorSabreCameraRgb"
                + " histogramResize=GLHistogramDefault"
                + " adaptiveWhitePoint=" + adaptiveWhitePoint
                + " avgFinal=" + avg
                + " mpyFinal=" + mpy
                + " sceneWhiteFinal=" + sceneWhite
                + " whiteEff=" + whiteEff
                + " clippedFraction=" + clippedFraction
                + " knee=" + knee
                + " curveEnd=" + curve[CURVE_SIZE - 1]
                + " noiseSource=motionV2WronskiCamera2"
                + " noiseS=" + noiseS + " noiseO=" + noiseO
                + " gainNoiseLimit=" + gain.noiseLimit
                + " gainNoiseClamped=" + gain.noiseClamped
                + " gainMaxClamped=" + gain.maxClamped
                + " curveApplication=preColorPhotonDomainCommonScalar"
                + " irisColorAffected=false"
                + " wronskiAffected=false";
        Log.i(Name, line);
        try { MotionTrace.processingState("IRIS_26656_PHOTON_NEW_EXPOSURE", line); }
        catch (Throwable ignored) {}

        WorkingTexture = preColor;
    }

    private static int sum(int[] a) { int s = 0; for (int v : a) s += v; return s; }

    private static void requireWhitePoint(float[] wp) {
        if (wp == null || wp.length < 3) throw new IllegalStateException("26656 invalid white point");
        for (int c = 0; c < 3; c++) {
            if (!Float.isFinite(wp[c]) || wp[c] <= 0.0f || wp[c] > 1.0f) {
                throw new IllegalStateException("26656 invalid white point component " + c + ": " + wp[c]);
            }
        }
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
    private static void remapHistogram(float[][] mapped, float[] extent, float adaptiveWhite) {
        for (int c = 0; c < 3; c++) {
            for (int i = 0; i < HIST_SIZE; i++) {
                mapped[c][i] = srgbEncodeExtended(
                        (i + 0.5f) / (HIST_SIZE - 1.0f) * extent[c] / adaptiveWhite)
                        * (HIST_SIZE - 1.0f);
            }
        }
    }
    private static float estimateAvg(int[][] result, float[][] mapped,
                                     int normR, int normG, int normB) {
        final float cap = HIST_SIZE - 1.0f;
        float sum = 0.0f;
        int cnt = 0;
        for (int i = 0; i < HIST_SIZE - 1; i++) {
            if (cnt > (normR + normG + normB) * FILL_COEFFICIENT) break;
            sum += result[0][i] * Math.min(mapped[0][i], cap)
                    + result[1][i] * Math.min(mapped[1][i], cap)
                    + result[2][i] * Math.min(mapped[2][i], cap);
            cnt += result[0][i] + result[1][i] + result[2][i];
        }
        return cnt > 0 ? sum / cnt : TARGET;
    }
    private static float searchWhite(int[][] result, float[][] mapped,
                                     int normR, int normG, int normB, float mpy) {
        float white = Float.MAX_VALUE;
        for (int c = 0; c < 3; c++) {
            int histNorm = c == 0 ? normR : (c == 1 ? normG : normB);
            float sum = 0.0f;
            int cnt = 0;
            for (int i = HIST_SIZE - 1;
                 i > Math.max(HIST_SIZE * 2.0 / 3.0, HIST_SIZE / (mpy + 0.001)); i--) {
                sum += result[c][i] * mapped[c][i];
                cnt += result[c][i];
                if (cnt > histNorm * 0.005f) break;
            }
            if (cnt == 0) { sum = HIST_SIZE - 1; cnt = 1; }
            white = Math.min(white, (sum / cnt) / HIST_SIZE);
        }
        return white;
    }
    private static GainClamp clampGain(float mpy, float noiseS, float noiseO) {
        float noiseLimit = (float)(NOISE_MAX / Math.sqrt(noiseS * 0.5f + noiseO));
        noiseLimit = Math.max(noiseLimit, 1.0f);
        boolean noiseClamped = false;
        boolean maxClamped = false;
        if (mpy > noiseLimit) { mpy = noiseLimit; noiseClamped = true; }
        if (mpy > GAIN_MAX) { mpy = GAIN_MAX; maxClamped = true; }
        return new GainClamp(mpy, noiseLimit, noiseClamped, maxClamped);
    }
    private static float softShoulder(float x, float knee) {
        if (x <= knee) return x;
        float t = x - knee;
        float s = 1.0f - knee;
        float g = t / s;
        return knee + s * g * g;
    }
    private static float clamp01(float x) { return Math.max(0.0f, Math.min(1.0f, x)); }
    private static float mix(float a, float b, float t) { return a + (b - a) * t; }
    private static final class GainClamp {
        final float value, noiseLimit; final boolean noiseClamped, maxClamped;
        GainClamp(float value, float noiseLimit, boolean noiseClamped, boolean maxClamped) {
            this.value = value; this.noiseLimit = noiseLimit;
            this.noiseClamped = noiseClamped; this.maxClamped = maxClamped;
        }
    }
}
