package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26420_MOTION_V2_OWNED_CONTINUOUS_ALIGNMENT
 *
 * Motion-V2-owned RAW/CFA registration. It deliberately does not use
 * PyramidAlignment, PyramidMerging, merge0/merge11, or Photon's tile atlas.
 *
 * Pipeline per auxiliary frame:
 *   packed CFA -> quarter-resolution green guide
 *   -> robust large-range global translation search
 *   -> local soft subpixel refinement on a dense guide lattice
 *   -> bilinearly sampled continuous full-image flow + confidence.
 *
 * The final flow is expressed in packed-CFA pixel coordinates. Confidence is
 * independent of flow; unreliable areas fall back to the physical reference.
 */
public final class MotionV2Alignment {
    private static final String TAG = "MotionV2Alignment";
    private static final int GUIDE_SCALE = 4;
    private static final int GLOBAL_RADIUS = 12;

    private MotionV2Alignment() {}

    public static final class Result implements AutoCloseable {
        public final GLTexture flowTexture;
        public final float globalDxPacked;
        public final float globalDyPacked;
        public final float meanConfidence;
        public final float lowConfidenceFraction;

        Result(
                GLTexture flowTexture,
                float globalDxPacked,
                float globalDyPacked,
                float meanConfidence,
                float lowConfidenceFraction) {
            this.flowTexture = flowTexture;
            this.globalDxPacked = globalDxPacked;
            this.globalDyPacked = globalDyPacked;
            this.meanConfidence = meanConfidence;
            this.lowConfidenceFraction = lowConfidenceFraction;
        }

        @Override
        public void close() {
            if (flowTexture != null) flowTexture.close();
        }
    }

    public static Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {

        Point guideSize = new Point(
                Math.max(8, (rawHalf.x + GUIDE_SCALE - 1) / GUIDE_SCALE),
                Math.max(8, (rawHalf.y + GUIDE_SCALE - 1) / GUIDE_SCALE));
        Point scoreSize = new Point(
                GLOBAL_RADIUS * 2 + 1,
                GLOBAL_RADIUS * 2 + 1);

        GLTexture referenceGuide = null;
        GLTexture alterGuide = null;
        GLTexture scoreTexture = null;
        GLTexture flowTexture = null;

        try {
            /*
             * IRIS_26421_GLES_R32F_ALIGNMENT_GUIDE
             *
             * GLSL ES image variables support r32f but not r16f as an image
             * format qualifier. These guides are accessed with texelFetch,
             * so use NEAREST; the separate RGBA16F flow field remains LINEAR.
             */
            referenceGuide = new GLTexture(
                    guideSize,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
            alterGuide = new GLTexture(
                    guideSize,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8, 8, 1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", GUIDE_SCALE);
            glProg.setVar("signalScale", Math.max(signalScale, 1.0e-6f));
            glProg.setTexture("InputCfa", referenceCfa);
            glProg.setTextureCompute("OutputGuide", referenceGuide, true);
            glProg.computeAuto(guideSize, 1);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8, 8, 1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", GUIDE_SCALE);
            glProg.setVar("signalScale", Math.max(signalScale, 1.0e-6f));
            glProg.setTexture("InputCfa", alterCfa);
            glProg.setTextureCompute("OutputGuide", alterGuide, true);
            glProg.computeAuto(guideSize, 1);

            scoreTexture = new GLTexture(
                    scoreSize,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);

            glProg.setLayout(8, 8, 1);
            glProg.useAssetProgram("motionv2/alignment_global_score", true);
            glProg.setVar("searchRadius", GLOBAL_RADIUS);
            glProg.setTexture("ReferenceGuide", referenceGuide);
            glProg.setTexture("AlterGuide", alterGuide);
            glProg.setTextureCompute("OutputScore", scoreTexture, true);
            glProg.computeAuto(scoreSize, 1);

            scoreTexture.BufferLoad();
            ByteBuffer scoreBytes = scoreTexture.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    true);
            scoreBytes.order(ByteOrder.nativeOrder());
            FloatBuffer scores = scoreBytes.asFloatBuffer();

            float best = Float.POSITIVE_INFINITY;
            int bestX = GLOBAL_RADIUS;
            int bestY = GLOBAL_RADIUS;
            int scoreCount = Math.min(
                    scores.capacity(),
                    scoreSize.x * scoreSize.y);
            for (int i = 0; i < scoreCount; i++) {
                float s = scores.get(i);
                if (!Float.isFinite(s)) continue;
                if (s < best) {
                    best = s;
                    bestX = i % scoreSize.x;
                    bestY = i / scoreSize.x;
                }
            }
            if (!Float.isFinite(best)) {
                bestX = GLOBAL_RADIUS;
                bestY = GLOBAL_RADIUS;
                best = 1.0f;
            }

            int globalDxGuide = bestX - GLOBAL_RADIUS;
            int globalDyGuide = bestY - GLOBAL_RADIUS;

            flowTexture = new GLTexture(
                    guideSize,
                    new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                    null,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);

            glProg.setLayout(8, 8, 1);
            glProg.useAssetProgram("motionv2/alignment_local_flow", true);
            glProg.setVar("globalShiftGuide",
                    new Point(globalDxGuide, globalDyGuide));
            glProg.setVar("guideScale", (float) GUIDE_SCALE);
            glProg.setTexture("ReferenceGuide", referenceGuide);
            glProg.setTexture("AlterGuide", alterGuide);
            glProg.setTextureCompute("OutputFlow", flowTexture, true);
            glProg.computeAuto(guideSize, 1);

            /*
             * Small diagnostic readback. Request FLOAT32 explicitly so the
             * client-buffer byte contract matches GL_FLOAT, avoiding the
             * generic FLOAT16 transfer bug previously proven in V2.
             */
            flowTexture.BufferLoad();
            ByteBuffer flowBytes = flowTexture.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    true);
            flowBytes.order(ByteOrder.nativeOrder());
            FloatBuffer flow = flowBytes.asFloatBuffer();

            double confSum = 0.0;
            long confCount = 0L;
            long lowCount = 0L;
            int pixels = Math.min(
                    guideSize.x * guideSize.y,
                    flow.capacity() / 4);
            int step = Math.max(1, pixels / 8192);
            for (int i = 0; i < pixels; i += step) {
                float conf = flow.get(i * 4 + 2);
                if (!Float.isFinite(conf)) conf = 0.0f;
                conf = Math.max(0.0f, Math.min(1.0f, conf));
                confSum += conf;
                confCount++;
                if (conf < 0.25f) lowCount++;
            }
            float meanConfidence = confCount > 0
                    ? (float)(confSum / confCount) : 0.0f;
            float lowFraction = confCount > 0
                    ? lowCount / (float)confCount : 1.0f;

            float dxPacked = globalDxGuide * (float)GUIDE_SCALE;
            float dyPacked = globalDyGuide * (float)GUIDE_SCALE;

            Log.d(TAG,
                    "IRIS_26420_V2_OWNED_ALIGNMENT"
                            + " guide=" + guideSize.x + "x" + guideSize.y
                            + " guideScalePacked=" + GUIDE_SCALE
                            + " globalDxPacked=" + dxPacked
                            + " globalDyPacked=" + dyPacked
                            + " globalScore=" + best
                            + " meanConfidence=" + meanConfidence
                            + " lowConfidenceFraction=" + lowFraction
                            + " continuousFlow=true"
                            + " legacyPyramidAlignment=false"
                            + " tileAtlas=false");

            GLTexture keep = flowTexture;
            flowTexture = null;
            return new Result(
                    keep,
                    dxPacked,
                    dyPacked,
                    meanConfidence,
                    lowFraction);
        } finally {
            if (flowTexture != null) flowTexture.close();
            if (scoreTexture != null) scoreTexture.close();
            if (alterGuide != null) alterGuide.close();
            if (referenceGuide != null) referenceGuide.close();
        }
    }
}