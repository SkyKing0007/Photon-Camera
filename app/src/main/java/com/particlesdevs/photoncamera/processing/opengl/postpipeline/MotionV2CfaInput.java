package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26414_MOTION_V2_FLOAT_CFA_INPUT
 *
 * First V2 post node. The temporal reconstructor already produced normalized
 * FLOAT16 RGBA CFA planes, so Bayer2Float must not run again.
 *
 * IRIS_26415_MOTION_V2_GL_LIFECYCLE_OWNER
 *
 * Bayer2Float historically did two jobs:
 *  1. RAW16 -> float conversion, and
 *  2. allocation of PostPipeline main1/main2/main3.
 *
 * 26414 correctly removed job (1), but accidentally removed job (2) too.
 * This node now owns only the missing GL lifecycle initialization while
 * preserving the packed floating CFA values unchanged.
 */
public final class MotionV2CfaInput extends Node {
    public MotionV2CfaInput() {
        super("", "MotionV2CfaInput");
    }

    @Override
    public void Compile() {}

    @Override
    public void Run() {
        PostPipeline pipeline = (PostPipeline) basePipeline;
        ByteBuffer source = pipeline.motionV2FloatCfa;
        if (source == null) {
            throw new IllegalStateException(
                    "Motion V2 FLOAT32 CFA bridge buffer is null");
        }

        Point raw = basePipeline.mParameters.rawSize;
        Point half = new Point(raw.x / 2, raw.y / 2);

        ByteBuffer view = source.duplicate();
        view.position(0);

        /*
         * IRIS_26424_DIRECT_MULTIFRAME_RGB_INPUT
         *
         * Standard Bayer (0..3) arrives from the owned burst reconstructor as
         * full-resolution linear camera RGB. The proven 26416 FLOAT32 bridge
         * remains unchanged. Special CFA formats retain the prior packed-CFA
         * fallback carrier.
         */
        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3;
        if (directBayer) {
            WorkingTexture = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);
        } else {
            WorkingTexture = new GLTexture(
                    half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
        }

        /*
         * Recreate the PostPipeline ping-pong textures that Bayer2Float used
         * to initialize. They are full raw resolution because demosaic output
         * and every later V2 RGB stage are native-resolution RGB(A).
         */
        GLFormat workFormat =
                new GLFormat(
                        GLFormat.DataType.FLOAT_16,
                        GLDrawParams.WorkDim);

        basePipeline.main1 = new GLTexture(
                raw,
                workFormat,
                null,
                GL_LINEAR,
                GL_CLAMP_TO_EDGE);
        basePipeline.main2 = new GLTexture(
                raw,
                workFormat,
                null,
                GL_LINEAR,
                GL_CLAMP_TO_EDGE);
        basePipeline.main3 = new GLTexture(
                raw,
                workFormat,
                null,
                GL_LINEAR,
                GL_CLAMP_TO_EDGE);
        basePipeline.texnum = 0;

        Log.d(Name, "IRIS_26416_V2_FLOAT32_INPUT"
                + " carrier=" + (directBayer ? "directRgbFullRes" : "packedCfaHalfRes")
                + " transferFormat=rgba32f"
                + " bytesPerChannel=4"
                + " rgbPingPong=" + raw.x + "x" + raw.y
                + " main1=true main2=true main3=true"
                + " texnumReset=0"
                + " Bayer2FloatBypassed=true"
                + " raw16RoundTrip=false"
                + " float16Transfer=false"
                + " directMultiframeRgb=" + directBayer);
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26415_MOTION_V2_GL_LIFECYCLE_OWNER",
                    "carrier=" + (directBayer ? "directRgbFullRes" : "packedCfaHalfRes")
                            + " rgbPingPong=" + raw.x + "x" + raw.y
                            + " main1=true main2=true main3=true"
                            + " texnumReset=0"
                            + " Bayer2FloatBypassed=true");
        } catch (Throwable ignored) {}
    }
}
