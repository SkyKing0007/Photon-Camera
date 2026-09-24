package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.opengl.scripts.GLHistogram;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Collections;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_NEAREST;

/*
 * IRIS_26498_STAGE_CHROMA_ORIGIN_TELEMETRY
 *
 * Diagnostic pass-through only. The exact input GLTexture object continues to the next node.
 * In addition to historical brightness histograms, a sparse 32x24 readback measures spatial
 * log(R/G) and log(B/G) variation in low-gradient cells. Absolute white balance is irrelevant:
 * standard deviation of log color ratios tells us where broad false chroma first appears.
 */
public class StageTelemetry extends Node {
    private static final int HIST_SIZE = 256;
    private static final int SAMPLE_RESIZE = 12;
    private static final int PROBE_W = 32;
    private static final int PROBE_H = 24;
    private final String stage;

    public StageTelemetry(String stage) {
        super("", "StageTelemetry_" + stage);
        this.stage = stage;
    }

    @Override public void Compile() {}

    private static float percentile(int[] histogram, long total, double fraction) {
        if (histogram == null || histogram.length == 0 || total <= 0L) return Float.NaN;
        long target = Math.max(1L, (long)Math.ceil(total * fraction));
        long cumulative = 0L;
        for (int i = 0; i < histogram.length; i++) {
            cumulative += histogram[i];
            if (cumulative >= target) return i / (float)(histogram.length - 1);
        }
        return 1.0f;
    }

    private static double std(ArrayList<Double> v) {
        if (v.size() < 2) return Double.NaN;
        double m = 0.0;
        for (double x : v) m += x;
        m /= v.size();
        double s = 0.0;
        for (double x : v) { double d = x - m; s += d * d; }
        return Math.sqrt(s / Math.max(1, v.size() - 1));
    }

    private float[] semantic(float a, float b, float c, float d, boolean cfa) {
        if (!cfa) return new float[]{a, b, c, Float.NaN};
        int pattern = (int) basePipeline.mParameters.cfaPattern;
        switch (pattern) {
            case 0: return new float[]{a, 0.5f * (b + c), d, b - c};
            case 1: return new float[]{b, 0.5f * (a + d), c, a - d};
            case 2: return new float[]{c, 0.5f * (a + d), b, a - d};
            default:return new float[]{d, 0.5f * (b + c), a, b - c};
        }
    }

    private String chromaOriginStats(GLTexture source) {
        GLTexture probe = null;
        try {
            Point ps = new Point(PROBE_W, PROBE_H);
            probe = new GLTexture(ps, new GLFormat(GLFormat.DataType.FLOAT_32, 4), null,
                    GL_NEAREST, GL_CLAMP_TO_EDGE);
            glProg.useProgram(
                    "precision highp float;\n"
                    + "uniform sampler2D InputBuffer;\n"
                    + "uniform vec2 OutputSize;\n"
                    + "out vec4 Output;\n"
                    + "void main(){vec2 uv=gl_FragCoord.xy/OutputSize;Output=texture(InputBuffer,uv);}\n");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("OutputSize", (float)PROBE_W, (float)PROBE_H);
            glProg.drawBlocks(probe);
            glProg.closed = true;
            probe.BufferLoad();
            ByteBuffer bytes = probe.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(ByteOrder.nativeOrder());
            FloatBuffer fb = bytes.asFloatBuffer();
            float[][][] rgb = new float[PROBE_H][PROBE_W][4];
            boolean cfa = stage.contains("FUSED_BAYER_CANONICAL");
            for (int y = 0; y < PROBE_H; ++y) {
                for (int x = 0; x < PROBE_W; ++x) {
                    float a = fb.get(), b = fb.get(), c = fb.get(), d = fb.get();
                    rgb[y][x] = semantic(a,b,c,d,cfa);
                }
            }

            ArrayList<Double> rg = new ArrayList<>();
            ArrayList<Double> bg = new ArrayList<>();
            ArrayList<Double> gsplit = new ArrayList<>();
            final double eps = 0.01;
            for (int y = 0; y + 1 < PROBE_H; ++y) {
                for (int x = 0; x + 1 < PROBE_W; ++x) {
                    float[] p = rgb[y][x];
                    float[] rx = rgb[y][x+1];
                    float[] dy = rgb[y+1][x];
                    double l = (p[0] + 2.0*p[1] + p[2]) * 0.25;
                    double lr = (rx[0] + 2.0*rx[1] + rx[2]) * 0.25;
                    double ld = (dy[0] + 2.0*dy[1] + dy[2]) * 0.25;
                    if (!Double.isFinite(l) || l < 0.03 || l > 0.90) continue;
                    double relX = Math.abs(l-lr)/Math.max(Math.max(l,lr),0.05);
                    double relY = Math.abs(l-ld)/Math.max(Math.max(l,ld),0.05);
                    if (relX > 0.06 || relY > 0.06) continue;
                    if (p[0] <= -eps || p[1] <= -eps || p[2] <= -eps) continue;
                    rg.add(Math.log((p[0]+eps)/(p[1]+eps)));
                    bg.add(Math.log((p[2]+eps)/(p[1]+eps)));
                    if (cfa && Float.isFinite(p[3])) {
                        gsplit.add((double)p[3] / Math.max(Math.abs(p[1]), 0.03));
                    }
                }
            }
            return " flatCells=" + rg.size()
                    + " flatLogRGStd=" + std(rg)
                    + " flatLogBGStd=" + std(bg)
                    + " flatGreenPhaseSplitStd=" + std(gsplit)
                    + " probe=" + PROBE_W + "x" + PROBE_H
                    + " domain=" + (cfa ? "packedCfaSemanticRatios" : "rgbRatios");
        } catch (Throwable t) {
            return " chromaProbeError=" + t.getClass().getSimpleName();
        } finally {
            if (probe != null) try { probe.close(); } catch (Throwable ignored) {}
        }
    }

    @Override
    public void Run() {
        GLTexture source = previousNode == null ? null : previousNode.WorkingTexture;
        WorkingTexture = source;
        // IRIS_26698_PRODUCTION_TELEMETRY_IMAGE_WORK_DISABLED
        // Preserve the exact pass-through node and a conservative GPU completion boundary.
        if (!basePipeline.mParameters.motionV2Active || source == null) return;
        android.opengl.GLES20.glFinish();
        String message = "IRIS_26698_STAGE_TELEMETRY_IMAGE_WORK_DISABLED"
                + " stage=" + stage
                + " histogramReadback=false chromaProbeReadback=false"
                + " explicitCompletionBoundary=true sameTexturePassThrough=true";
        Log.i("IRIS26698", message);
        try { com.particlesdevs.photoncamera.util.MotionTrace.processingState("STAGE_TELEMETRY_26698", message); }
        catch (Throwable ignored) {}
        WorkingTexture = source;
        glProg.closed = true;
    }
}
