package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * C-only GPU upload of pinned donor MGC 64-QMC sqrt-domain shot/read RAW noise model.
 * Four true Camera2 Bayer-channel coefficients per frame; two time-axis LUT rows.
 * The alternate frame never shares the reference row unless its genuine noise matches.
 */
internal object Iris26972CDonorSabreGpuNoiseLut {
    private const val COMPONENT = "26972 C Sabre donor 64-QMC noise LUT"
    private val gl = Iris26972CDonorSabreGpuMerge
    internal class Result private constructor(val texture: Int,private val owner: EGLContext) : AutoCloseable {
        private var closed = false
        internal fun checkOwner() {
            check(!closed && owner != EGL14.EGL_NO_CONTEXT && EGL14.eglGetCurrentContext()==owner) {
                "$COMPONENT wrong EGL context/ownership"
            }
        }
        override fun close() {
            checkOwner()
            GLES30.glDeleteTextures(1,intArrayOf(texture),0)
            closed = true
        }
        internal companion object {
            fun own(texture: Int) = Result(texture,EGL14.eglGetCurrentContext())
        }
    }

    internal fun create(
        referenceShot: FloatArray,
        referenceRead: FloatArray,
        currentShot: FloatArray,
        currentRead: FloatArray,
    ): Result {
        // Do CPU validation before touching caller GL state.
        val samples=Iris26972CDonorSabreNoiseEstimatesLut.create(
            referenceShot,referenceRead,currentShot,currentRead)
        gl.requireCurrentContext()
        check(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= 10) {
            "$COMPONENT GL texture limit below donor 10x2 LUT"
        }
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val oldUnpackBuffer=gl.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val ids=IntArray(1)
        var success=false
        try {
            GLES30.glGenTextures(1,ids,0)
            check(ids[0]>0) { "$COMPONENT texture allocation failed" }
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
            val data=ByteBuffer.allocateDirect(samples.size*Float.SIZE_BYTES)
                .order(ByteOrder.nativeOrder()).asFloatBuffer().apply { put(samples);rewind() }
            // Make sure the provided FloatBuffer is NOT interpreted as a stale PBO offset.
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                Iris26972CDonorSabreNoiseEstimatesLut.WIDTH,
                Iris26972CDonorSabreNoiseEstimatesLut.ROWS,0,
                GLES30.GL_RGBA,GLES30.GL_FLOAT,data)
            gl.checkGl("donor Sabre 64-QMC 10x2 float LUT upload")
            success=true
            return Result.own(ids[0])
        } finally {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,oldUnpackBuffer)
            state.restore()
            if(!success && ids[0]>0) GLES30.glDeleteTextures(1,ids,0)
        }
    }
}
