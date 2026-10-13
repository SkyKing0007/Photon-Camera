package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.MotionV2Merger;
import com.particlesdevs.photoncamera.processing.processor.MotionV2SharedRgba16fCarrier;
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
 * camera-linear RGBA16F from the sole Sabre reconstruction owner; special CFA
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
        MotionV2SharedRgba16fCarrier shared = pipeline.motionV2SharedRgba16fCarrier;
        if ((source == null) == (shared == null)) {
            throw new IllegalStateException(
                    "26826 Motion V2 input requires exactly one carrier owner");
        }

        if (basePipeline.mParameters.motionV2Active
                && basePipeline.mParameters.motionV2ReconstructionOwner
                != com.particlesdevs.photoncamera.processing.render.Parameters.MOTION_V2_RECONSTRUCTION_SABRE) {
            throw new IllegalStateException("26560 Motion RGB input missing Sabre reconstruction owner");
        }
        Point raw = basePipeline.mParameters.rawSize;
        Point half = new Point(raw.x / 2, raw.y / 2);

        ByteBuffer view = source != null ? source.duplicate() : null;
        if (view != null) view.position(0);

        /* IRIS_26726_PROPER_PER_FRAME_RGB_FLOAT16_BRIDGE_OWNER
         * Standard Bayer crosses the context boundary as native full-resolution RGBA16F
         * camera-linear RGB. Special CFA formats retain the historical half-resolution float32 carrier.
         */
        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3
                        && raw.x > 0 && raw.y > 0
                        && (raw.x % 2) == 0 && (raw.y % 2) == 0;
        boolean directRgbCarrier = directBayer && pipeline.motionV2DirectRgbCarrier;
        long directHalfBytes = (long) raw.x * (long) raw.y * 4L * 2L;
        if (directRgbCarrier && pipeline.motionV2LinearRgbCarrierFormat
                != MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA16F) {
            throw new IllegalStateException("26726 Motion direct RGB carrier format invalid format="
                    + pipeline.motionV2LinearRgbCarrierFormat);
        }
        if (directRgbCarrier && source != null && source.capacity() != directHalfBytes) {
            throw new IllegalStateException("26726 Motion RGBA16F carrier byte contract invalid bytes="
                    + source.capacity() + " expected=" + directHalfBytes);
        }
        if (directRgbCarrier && shared != null
                && (shared.width != raw.x || shared.height != raw.y
                    || shared.expectedBytes() != directHalfBytes)) {
            throw new IllegalStateException("26826 shared RGBA16F carrier geometry mismatch");
        }
        if (!directRgbCarrier && pipeline.motionV2LinearRgbCarrierFormat
                != MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA32F) {
            throw new IllegalStateException("26726 special-CFA carrier format invalid format="
                    + pipeline.motionV2LinearRgbCarrierFormat);
        }
        if (!directRgbCarrier && source == null) {
            throw new IllegalStateException("26826 shared carrier is forbidden for special CFA fallback");
        }

        try {
            if (directRgbCarrier) {
                WorkingTexture = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                if (shared != null) {
                    boolean copied = shared.copyToCurrentGlTexture(WorkingTexture.mTextureID);
                    if (copied) {
                        Log.d(Name, "IRIS_26826_SHARED_RGBA16F_CONSUMER primary=true fallback=false");
                    } else {
                        ByteBuffer fallback = shared.copyTo26825FallbackBuffer();
                        if (fallback == null || fallback.capacity() != directHalfBytes) {
                            if (fallback != null) Allocator.free(fallback);
                            throw new IllegalStateException(
                                    "26826 shared consumer failed and 26825 fallback copy unavailable");
                        }
                        try {
                            fallback.position(0);
                            WorkingTexture.loadHalfFloatData(fallback);
                            Log.w(Name, "IRIS_26826_SHARED_RGBA16F_FALLBACK stage=consumer_import owner=26825_upload");
                        } finally {
                            Allocator.free(fallback);
                        }
                    }
                } else {
                    /* Exact 26825 fallback upload. */
                    WorkingTexture.loadHalfFloatData(view);
                }
            } else {
                WorkingTexture = new GLTexture(
                        half,
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        view,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
            }
        } finally {
            pipeline.motionV2FloatCfa = null;
            pipeline.motionV2SharedRgba16fCarrier = null;
            pipeline.motionV2LinearRgbCarrierFormat = MotionV2Merger.Result.LINEAR_RGB_CARRIER_NONE;
            if (source != null) Allocator.free(source);
            if (shared != null) shared.close();
            source = null;
            shared = null;
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
                + " transferFormat=" + (directRgbCarrier ? "rgba16f" : "float32_special_cfa")
                + " bytesPerChannel=" + (directRgbCarrier ? 2 : 4)
                + " cpuCarrierReleasedAfterUpload=true"
                + " rgbPingPong=" + raw.x + "x" + raw.y
                + " main1=true main2=true main3=true"
                + " texnumReset=0"
                + " Bayer2FloatBypassed=true"
                + " raw16RoundTrip=false"
                + " float16Transfer=" + directRgbCarrier
                + " halfFloatClientType=" + directRgbCarrier
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
