package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.MotionV2Merger;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26726_NIGHT_RGBA16F_MOTION_PARITY_INPUT
 * Dedicated Night RGB input with the universal explicit RGBA16F cross-context contract.
 * MGC/Sabre still owns Night reconstruction and returns completed camera-linear RGB; only image
 * storage/transport is half-float while shader arithmetic remains highp float.
 */
public final class IrisNightRgbInput extends Node {
    public IrisNightRgbInput() { super("", "IrisNightRgbInput"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        PostPipeline pipeline = (PostPipeline) basePipeline;
        if (!basePipeline.mParameters.irisNightActive || basePipeline.mParameters.motionV2Active)
            throw new IllegalStateException("26548 dedicated Night RGB input used outside Night");
        ByteBuffer source = pipeline.irisNightLinearRgb;
        if (source == null)
            throw new IllegalStateException("26726 Night RGBA16F carrier is null");
        if (pipeline.irisNightLinearRgbCarrierFormat
                != MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA16F)
            throw new IllegalStateException("26726 Night RGBA16F carrier format mismatch format="
                    + pipeline.irisNightLinearRgbCarrierFormat);

        Point raw = basePipeline.mParameters.rawSize;
        long expected = (long) raw.x * (long) raw.y * 4L * 2L;
        if (raw.x <= 0 || raw.y <= 0 || source.capacity() != expected)
            throw new IllegalStateException("26726 Night RGBA16F carrier byte contract invalid bytes="
                    + source.capacity() + " expected=" + expected);

        ByteBuffer view = source.duplicate();
        view.position(0);
        /* IRIS_26727_NIGHT_EXPLICIT_HALF_FLOAT_UPLOAD
         * Keep the universal RGBA16F carrier and identify its client bytes correctly as GL_HALF_FLOAT. */
        WorkingTexture = new GLTexture(
                raw,
                new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                null,
                GL_NEAREST,
                GL_CLAMP_TO_EDGE);
        WorkingTexture.loadHalfFloatData(view);

        // glTexSubImage2D has consumed the client bytes before this call returns.
        // Release the ~96 MiB CPU transfer carrier before allocating the working ping-pong set.
        pipeline.irisNightLinearRgb = null;
        pipeline.irisNightLinearRgbCarrierFormat = MotionV2Merger.Result.LINEAR_RGB_CARRIER_NONE;
        Allocator.free(source);
        source = null;
        view = null;
        Log.critical(Name, "IRIS_26726_NIGHT_CPU_RGBA16F_RELEASED_AFTER_UPLOAD bytes=" + expected);

        GLFormat work = new GLFormat(GLFormat.DataType.FLOAT_16, GLDrawParams.WorkDim);
        basePipeline.main1 = new GLTexture(raw, work, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
        basePipeline.main2 = new GLTexture(raw, work, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
        basePipeline.main3 = new GLTexture(raw, work, null, GL_LINEAR, GL_CLAMP_TO_EDGE);
        basePipeline.texnum = 0;
        glProg.closed = true;

        Log.i(Name, "IRIS_26726_NIGHT_RGBA16F_MOTION_PARITY_INPUT"
                + " carrier=fullResCameraLinearRGBA16F"
                + " uploadSeparate=true halfFloatClientType=true main1=true main2=true main3=true texnum=0"
                + " cpuCarrierReleasedBeforePingPong=true"
                + " rcd=false demosaic=false photonNight=false"
                + " transportOnly=true reconstructionMathUnchanged=true"
                + " bytes=" + expected);
    }
}
