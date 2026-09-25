package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26414_MOTION_V2_FLOAT_CFA_INPUT
 *
 * First V2 post node. Standard Bayer Motion now arrives as full-resolution
 * camera-linear RGBA32F from the sole Sabre reconstruction owner; special CFA
 * formats retain the historical packed float fallback. Bayer2Float must not run again.
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

        if (basePipeline.mParameters.motionV2Active
                && basePipeline.mParameters.motionV2ReconstructionOwner
                != com.particlesdevs.photoncamera.processing.render.Parameters.MOTION_V2_RECONSTRUCTION_SABRE) {
            throw new IllegalStateException("26560 Motion RGB input missing Sabre reconstruction owner");
        }
        Point raw = basePipeline.mParameters.rawSize;
        Point half = new Point(raw.x / 2, raw.y / 2);

        ByteBuffer view = source.duplicate();
        view.position(0);

        /* IRIS_26501_PROPER_PER_FRAME_RGB_FLOAT32_BRIDGE_OWNER
         * Standard Bayer crosses the context boundary as native full-resolution RGBA32F
         * camera-linear RGB. Special CFA formats retain the historical half-resolution carrier.
         */
        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3
                        && raw.x > 0 && raw.y > 0
                        && (raw.x % 2) == 0 && (raw.y % 2) == 0;
        boolean directRgbCarrier = directBayer && pipeline.motionV2DirectRgbCarrier;
        long directFloatBytes = (long) raw.x * (long) raw.y * 4L * 4L;
        if (directRgbCarrier && source.capacity() != directFloatBytes) {
            throw new IllegalStateException("26700 Motion RGBA32F recovery carrier byte contract invalid bytes="
                    + source.capacity() + " expected=" + directFloatBytes);
        }

        try {
            WorkingTexture = new GLTexture(
                    directRgbCarrier ? raw : half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
        } finally {
            /* IRIS_26700_MOTION_RGBA32F_RELEASE_OWNER
             * Retain the 26699 ownership fix while restoring the successful-26698 carrier format:
             * GLTexture upload has consumed client memory before returning, so release the native
             * RGBA32F carrier immediately instead of leaking ~192 MiB per 4096x3072 capture. */
            pipeline.motionV2FloatCfa = null;
            Allocator.free(source);
            source = null;
            view = null;
        }

        if (directBayer && !directRgbCarrier) {
            throw new IllegalStateException(
                    "26501 standard Bayer input is not the full-resolution RGB carrier");
        }
        if (!directRgbCarrier && pipeline.motionV2HighlightProvenance != null) {
            ByteBuffer provenanceView = pipeline.motionV2HighlightProvenance.duplicate();
            provenanceView.position(0);
            pipeline.motionV2HighlightProvenanceTexture = new GLTexture(
                    half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    provenanceView,
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

        Log.d(Name, "IRIS_26700_V2_RGB_INPUT"
                + " carrier=" + (directRgbCarrier ? "properPerFrameCameraRgbFullRes" : "packedCfaHalfRes")
                + " transferFormat=rgba32f"
                + " bytesPerChannel=4"
                + " cpuCarrierReleasedAfterUpload=true"
                + " rgbPingPong=" + raw.x + "x" + raw.y
                + " main1=true main2=true main3=true"
                + " texnumReset=0"
                + " Bayer2FloatBypassed=true"
                + " raw16RoundTrip=false"
                + " float16Transfer=false"
                + " reconstructionOwner=" + basePipeline.mParameters.motionV2ReconstructionOwner
                + " directMultiframeRgb=" + directRgbCarrier
                + " fusedBayerCanonical=false"
                + " highlightProvenanceConsumedUpstream=" + directRgbCarrier);
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26415_MOTION_V2_GL_LIFECYCLE_OWNER",
                    "carrier=" + (directRgbCarrier ? "properPerFrameCameraRgbFullRes" : "packedCfaHalfRes")
                            + " rgbPingPong=" + raw.x + "x" + raw.y
                            + " main1=true main2=true main3=true"
                            + " texnumReset=0"
                            + " Bayer2FloatBypassed=true");
        } catch (Throwable ignored) {}
    }
}
