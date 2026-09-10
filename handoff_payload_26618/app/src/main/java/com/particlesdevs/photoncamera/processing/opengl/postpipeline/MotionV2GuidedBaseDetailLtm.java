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
 * IRIS_26618_GUIDED_BASE_DETAIL_LTM_OWNER
 *
 * Motion-only spatial exposure-allocation augmentation.  26614's viewfinder matcher still owns
 * the desired global brightness target and MotionV2Render remains the only final tone/output
 * curve.  This node only decomposes common extended-linear Display-P3 luminance into a guided
 * broad base plus untouched local detail, then emits a bounded common-RGB scalar that prevents a
 * large global brightness target from flattening already-bright broad illumination.
 *
 * The low-resolution scalar field is also copied into Parameters so the direct true-2x renderer
 * consumes the identical field.  It is read-only presentation state: Sabre, SHORT, CFA validity,
 * DNG, capture, denoise, alignment and temporal weights never consume it.
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
            throw new IllegalArgumentException("Invalid 26618 LTM source size");
        }
        final float scale = (float) MAP_LONG_EDGE / (float) Math.max(source.x, source.y);
        final int w = Math.max(MAP_MIN_EDGE, Math.round(source.x * scale));
        final int h = Math.max(MAP_MIN_EDGE, Math.round(source.y * scale));
        return new Point(w, h);
    }

    private void clearState() {
        basePipeline.mParameters.motionV2GuidedLtmApplied = false;
        basePipeline.mParameters.motionV2GuidedLtmWidth = 0;
        basePipeline.mParameters.motionV2GuidedLtmHeight = 0;
        basePipeline.mParameters.motionV2GuidedLtmGainMap = null;
    }

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("26618 guided LTM is Motion-only");
        }
        clearState();
        final float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid 26618 LTM displayGain=" + displayGain);
        }
        final float requestedFinalGain = displayGain * 0.80f;
        if (requestedFinalGain <= ACTIVE_FINAL_GAIN) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.i(Name, "IRIS_26618_GUIDED_BASE_DETAIL_LTM"
                    + " active=false requestedFinalGain=" + requestedFinalGain
                    + " reason=SMALL_OR_NO_GLOBAL_LIFT"
                    + " finalToneOwner=MotionV2Render true2xSharedField=false");
            return;
        }

        final Point sourceSize = previousNode.WorkingTexture.mSize;
        final Point low = mapSize(sourceSize);
        final GLFormat rgba16f = new GLFormat(GLFormat.DataType.FLOAT_16, 4);
        GLTexture coefficients = null;
        GLTexture gainMap = null;
        try {
            coefficients = new GLTexture(low, rgba16f);
            gainMap = new GLTexture(low, rgba16f);

            glProg.useAssetProgram("motionv2/guided_base_detail_ltm_coeff_26618");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setVar("ltmGridSize", low);
            glProg.drawBlocks(coefficients);

            glProg.useAssetProgram("motionv2/guided_base_detail_ltm_gain_26618");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setTexture("CoeffBuffer", coefficients);
            glProg.setVar("displayGain", displayGain);
            glProg.setVar("ltmGridSize", low);
            glProg.drawBlocks(gainMap);

            gainMap.BufferLoad();
            ByteBuffer bytes = gainMap.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(ByteOrder.nativeOrder());
            FloatBuffer floats = bytes.asFloatBuffer();
            final int count = low.x * low.y;
            final float[] sharedGain = new float[count];
            float min = Float.POSITIVE_INFINITY;
            float max = Float.NEGATIVE_INFINITY;
            double sum = 0.0;
            for (int i = 0; i < count; ++i) {
                final float g = floats.get(i * 4);
                if (!Float.isFinite(g) || g < 0.499f || g > 1.001f) {
                    throw new IllegalStateException(
                            "Invalid 26618 shared LTM gain at " + i + ": " + g);
                }
                sharedGain[i] = g;
                min = Math.min(min, g);
                max = Math.max(max, g);
                sum += g;
            }

            glProg.useAssetProgram("motionv2/guided_base_detail_ltm_apply_26618");
            glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
            glProg.setTexture("LtmGainBuffer", gainMap);
            WorkingTexture = basePipeline.getMain();
            glProg.drawBlocks(WorkingTexture);
            glProg.closed = true;

            basePipeline.mParameters.motionV2GuidedLtmGainMap = sharedGain;
            basePipeline.mParameters.motionV2GuidedLtmWidth = low.x;
            basePipeline.mParameters.motionV2GuidedLtmHeight = low.y;
            basePipeline.mParameters.motionV2GuidedLtmApplied = true;

            Log.i(Name, "IRIS_26618_GUIDED_BASE_DETAIL_LTM"
                    + " active=true owner=GUIDED_LOG_LUMINANCE_BASE"
                    + " detailResidual=UNCHANGED"
                    + " rgbGain=COMMON_SCALAR"
                    + " map=" + low.x + "x" + low.y
                    + " gainMin=" + min + " gainMean=" + (sum / count) + " gainMax=" + max
                    + " displayGain=" + displayGain
                    + " requestedFinalGain=" + requestedFinalGain
                    + " hdrAboveOnePreserved=true"
                    + " finalToneOwner=MotionV2Render"
                    + " true2xSharedField=true"
                    + " sabreShortCfaDngUnchanged=true");
        } finally {
            if (coefficients != null) coefficients.close();
            if (gainMap != null) gainMap.close();
        }
    }
}
