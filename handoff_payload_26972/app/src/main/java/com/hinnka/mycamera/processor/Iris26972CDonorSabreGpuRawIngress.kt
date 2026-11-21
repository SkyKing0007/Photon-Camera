package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Experiment C-only RAW_SENSOR uint16 GPU upload and pinned bjzhou 1.29.0 Sabre
 * `extractBayer` stage.  The input is Camera2 RAW_SENSOR data, NOT a YUV image,
 * and output is donor 2x2 RGBA16F Bayer quads, NOT demosaiced RGB.
 *
 * The caller supplies a shutter-frozen, non-recycled DirectByteBuffer containing
 * RAW16 pixels.  Ownership of the buffer stays with the caller throughout this
 * synchronous upload.  This component owns no alignment or finished photo.
 */
internal object Iris26972CDonorSabreGpuRawIngress {
    private const val COMPONENT = "26972 C donor RAW16 GPU ingress"
    private val gl = Iris26972CDonorSabreGpuMerge

    internal data class Plane(
        val data: ByteBuffer,
        val sourceWidth: Int,
        val sourceHeight: Int,
        val rowStrideBytes: Int,
        val pixelStrideBytes: Int,
        val cropLeft: Int,
        val cropTop: Int,
        val cropWidth: Int,
        val cropHeight: Int,
    ) {
        val extractedWidth: Int get() = cropWidth / 2
        val extractedHeight: Int get() = cropHeight / 2
    }

    internal class Result private constructor(
        val extractedBayerTexture: Int,
        /** Retained R16UI RAW_SENSOR texture; donor unblocker consumes these original samples. */
        val raw16Texture: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        private val context: EGLContext,
    ) : AutoCloseable {
        private var released = false
        internal fun requireOwner() {
            check(!released && context != EGL14.EGL_NO_CONTEXT &&
                context == EGL14.eglGetCurrentContext()) { "$COMPONENT wrong EGL owner or released" }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(2, intArrayOf(extractedBayerTexture, raw16Texture), 0)
            released = true
        }
        internal companion object {
            fun owned(bayer: Int, raw16: Int, width: Int, height: Int): Result =
                Result(bayer, raw16, width, height, EGL14.eglGetCurrentContext())
        }
    }

    /** Fail before GL allocation on invalid sensor-plane/crop metadata. */
    internal fun validate(plane: Plane) {
        require(plane.data.isDirect) {
            "$COMPONENT requires a live direct RAW16 byte buffer"
        }
        require(plane.sourceWidth in 16..16384 && plane.sourceHeight in 16..16384 &&
            plane.cropWidth in 16..16384 && plane.cropHeight in 16..16384 &&
            (plane.cropWidth and 1) == 0 && (plane.cropHeight and 1) == 0 &&
            (plane.cropLeft and 1) == 0 && (plane.cropTop and 1) == 0 &&
            plane.cropLeft >= 0 && plane.cropTop >= 0 &&
            plane.cropLeft.toLong()+plane.cropWidth <= plane.sourceWidth &&
            plane.cropTop.toLong()+plane.cropHeight <= plane.sourceHeight) {
            "$COMPONENT requires a valid even-origin Bayer crop"
        }
        require(plane.pixelStrideBytes == 2 && plane.rowStrideBytes >= plane.sourceWidth * 2 &&
            (plane.rowStrideBytes and 1) == 0) {
            "$COMPONENT requires RAW16 pixel stride 2 and even row stride"
        }
        val start = plane.data.position().toLong() +
            plane.cropTop.toLong()*plane.rowStrideBytes + plane.cropLeft.toLong()*2
        val end = start + (plane.cropHeight-1L)*plane.rowStrideBytes +
            plane.cropWidth.toLong()*2
        require(start >= 0 && end >= start && end <= plane.data.limit().toLong()) {
            "$COMPONENT RAW16 crop exceeds the actual ByteBuffer limit"
        }
    }

    /**
     * Synchronous upload + exact upstream extract shader. No synthetic RAW,
     * generic demosaic, CPU reconstruction, or A/B fallback is permitted.
     */
    internal fun extract(plane: Plane): Result {
        validate(plane)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= plane.cropWidth &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= plane.cropHeight &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 1) {
            "$COMPONENT RAW upload exceeds GLES capabilities"
        }
        gl.checkGl("before donor RAW ingress")
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val savedUnpack = gl.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val savedRowLength = gl.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        val savedPixelUnpackBuffer = gl.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val textures = IntArray(2)
        var framebuffer = 0
        var vao = 0
        var program = 0
        var done = false
        try {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, plane.rowStrideBytes/2)
            GLES30.glGenTextures(2, textures, 0)
            check(textures.all { it>0 } && textures[0]!=textures[1]) {
                "$COMPONENT texture allocation failed"
            }
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,textures[0])
            configureTexture(GLES30.GL_NEAREST)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_R16UI,
                plane.cropWidth,plane.cropHeight,0,GLES30.GL_RED_INTEGER,
                GLES30.GL_UNSIGNED_SHORT,null)
            val upload = plane.data.duplicate().order(ByteOrder.nativeOrder())
            val offset = plane.data.position().toLong() +
                plane.cropTop.toLong()*plane.rowStrideBytes + plane.cropLeft.toLong()*2
            upload.position(offset.toInt())
            GLES30.glTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,0,
                plane.cropWidth,plane.cropHeight,GLES30.GL_RED_INTEGER,
                GLES30.GL_UNSIGNED_SHORT,upload)
            gl.checkGl("donor RAW16 crop upload")
            // Unbind PBO and reset unpack layout before initializing the floating texture.
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,textures[1])
            configureTexture(GLES30.GL_NEAREST)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                plane.extractedWidth,plane.extractedHeight,0,
                GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,null)
            gl.checkGl("donor extracted Bayer texture")
            program = gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreMergeShaders.extractBayer)
            val fbos=IntArray(1)
            GLES30.glGenFramebuffers(1,fbos,0)
            framebuffer=fbos[0]
            val vaos=IntArray(1)
            GLES30.glGenVertexArrays(1,vaos,0)
            vao=vaos[0]
            check(framebuffer>0 && vao>0) { "$COMPONENT FBO/VAO creation failed" }
            GLES30.glBindVertexArray(vao)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,textures[1],0)
            GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                GLES30.GL_FRAMEBUFFER_COMPLETE) { "$COMPONENT RAW extraction FBO incomplete" }
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glUseProgram(program)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,textures[0])
            GLES30.glUniform1i(loc(program,"uRaw"),0)
            GLES30.glUniform2i(loc(program,"uRawSize"),plane.cropWidth,plane.cropHeight)
            GLES30.glViewport(0,0,plane.extractedWidth,plane.extractedHeight)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gl.checkGl("donor 2x2 RAW16 Bayer extraction")
            done=true
            return Result.owned(textures[1],textures[0],plane.cropWidth,plane.cropHeight)
        } finally {
            if(program>0) GLES30.glDeleteProgram(program)
            if(framebuffer>0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if(vao>0) GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            // RAW16 remains owned by Result until the per-frame unblocker has finished.
            if (!done) {
                val allocated = textures.filter { it > 0 }.toIntArray()
                if (allocated.isNotEmpty()) GLES30.glDeleteTextures(allocated.size,allocated,0)
            }
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,savedPixelUnpackBuffer)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,savedRowLength)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,savedUnpack)
            state.restore()
        }
    }
    private fun loc(p:Int,n:String):Int=GLES30.glGetUniformLocation(p,n).also {
        check(it>=0) { "$COMPONENT missing donor uniform $n" }
    }
    private fun configureTexture(filter:Int) {
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
    }
}
