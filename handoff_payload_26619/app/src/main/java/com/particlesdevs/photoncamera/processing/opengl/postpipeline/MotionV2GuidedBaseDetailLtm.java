package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/**
 * IRIS_26619_GUIDED_BASE_DETAIL_FINAL_COMPOSITION
 *
 * Motion-only edge-aware broad-guide decomposition.  Unlike 26618, this node does not multiply
 * or otherwise alter RGB.  It publishes one low-resolution guided log-guide base to the final
 * MotionV2Render owner and to true-2x publication.  The final renderer then maps only the broad
 * base and recombines the measured local log-detail residual with one common RGB scalar.
 */
public final class MotionV2GuidedBaseDetailLtm extends Node {
    private static final int MAP_LONG_EDGE = 256;
    private static final int MAP_MIN_EDGE = 48;
    private static final float ACTIVE_FINAL_GAIN = 1.05f;

    public MotionV2GuidedBaseDetailLtm() {
        super("", "MotionV2GuidedBaseDetailLtm");
    }

    @Override public void Compile() {}

    private static Point mapSize(Point source) {
        if (source == null || source.x <= 0 || source.y <= 0) {
            throw new IllegalArgumentException("Invalid 26619 LTM source size");
        }
        final float scale = (float) MAP_LONG_EDGE / (float) Math.max(source.x, source.y);
        final int w = Math.max(MAP_MIN_EDGE, Math.round(source.x * scale));
        final int h = Math.max(MAP_MIN_EDGE, Math.round(source.y * scale));
        return new Point(w, h);
    }

    private void clearState(PostPipeline pipeline) {
        basePipeline.mParameters.motionV2GuidedBaseDetailApplied = false;
        basePipeline.mParameters.motionV2GuidedBaseDetailWidth = 0;
        basePipeline.mParameters.motionV2GuidedBaseDetailHeight = 0;
        basePipeline.mParameters.motionV2GuidedBaseLogMap = null;
        if (pipeline.motionV2GuidedBaseLogTexture != null) {
            try { pipeline.motionV2GuidedBaseLogTexture.close(); } catch (Throwable ignored) {}
            pipeline.motionV2GuidedBaseLogTexture = null;
        }
    }

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("26619 guided LTM is Motion-only");
        }
        final PostPipeline pipeline = (PostPipeline) basePipeline;
        clearState(pipeline);
        final float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid 26619 LTM displayGain=" + displayGain);
        }
        final float requestedFinalGain = displayGain * MotionV2Render.OUTPUT_EXPOSURE_SCALE;
        if (requestedFinalGain <= ACTIVE_FINAL_GAIN) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.i(Name, "IRIS_26619_GUIDED_BASE_DETAIL_FINAL_COMPOSITION"
                    + " active=false requestedFinalGain=" + requestedFinalGain
                    + " reason=SMALL_OR_NO_GLOBAL_LIFT"
                    + " imageMutation=false finalToneOwner=MotionV2Render");
            return;
        }

        final Point sourceSize = previousNode.WorkingTexture.mSize;
        final Point low = mapSize(sourceSize);
        final GLFormat rgba16f = new GLFormat(GLFormat.DataType.FLOAT_16, 4);
        GLTexture coefficients = null;
        GLTexture baseLog = null;
        boolean transferred = false;
        try {
            coefficients = new GLTexture(low, rgba16f);
            baseLog = new GLTexture(low, rgba16f);

            glProg.useAssetProgram("motionv2/guided_base_detail_ltm_coeff_26619");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setVar("ltmGridSize", low);
            glProg.drawBlocks(coefficients);

            glProg.useAssetProgram("motionv2/guided_base_detail_ltm_base_26619");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setTexture("CoeffBuffer", coefficients);
            glProg.setVar("ltmGridSize", low);
            glProg.drawBlocks(baseLog);

            baseLog.BufferLoad();
            ByteBuffer bytes = baseLog.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(ByteOrder.nativeOrder());
            FloatBuffer floats = bytes.asFloatBuffer();
            final int count = low.x * low.y;
            final float[] sharedBaseLog = new float[count];
            float min = Float.POSITIVE_INFINITY;
            float max = Float.NEGATIVE_INFINITY;
            double sum = 0.0;
            for (int i = 0; i < count; ++i) {
                final float v = floats.get(i * 4);
                if (!Float.isFinite(v) || v < -16.0f || v > 8.0f) {
                    throw new IllegalStateException(
                            "Invalid 26619 guided base log at " + i + ": " + v);
                }
                sharedBaseLog[i] = v;
                min = Math.min(min, v);
                max = Math.max(max, v);
                sum += v;
            }

            basePipeline.mParameters.motionV2GuidedBaseLogMap = sharedBaseLog;
            basePipeline.mParameters.motionV2GuidedBaseDetailWidth = low.x;
            basePipeline.mParameters.motionV2GuidedBaseDetailHeight = low.y;
            basePipeline.mParameters.motionV2GuidedBaseDetailApplied = true;
            pipeline.motionV2GuidedBaseLogTexture = baseLog;
            transferred = true;

            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.i(Name, "IRIS_26619_GUIDED_BASE_DETAIL_FINAL_COMPOSITION"
                    + " active=true owner=GUIDED_LOG_TONE_GUIDE_BASE"
                    + " imageMutation=false preRenderRgbGain=false"
                    + " detailResidual=RECOMBINED_IN_FINAL_RENDER"
                    + " map=" + low.x + "x" + low.y
                    + " baseLogMin=" + min + " baseLogMean=" + (sum / count)
                    + " baseLogMax=" + max
                    + " displayGain=" + displayGain
                    + " requestedFinalGain=" + requestedFinalGain
                    + " finalToneOwner=MotionV2Render"
                    + " true2xSharedField=true"
                    + " sabreShortCfaDngUnchanged=true");
        } finally {
            if (coefficients != null) coefficients.close();
            if (baseLog != null && !transferred) baseLog.close();
        }
    }
}
