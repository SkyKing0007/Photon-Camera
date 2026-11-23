package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer

/**
 * C-only fail-closed bounded tile extraction from genuine SDR / HDR color targets.
 * Reads exactly RGBA Float32 into caller-owned direct buffers. Never reads
 * a full 50MP image or turns donor U16 SDR into an invented HDR reference.
 * Requires GL_RGBA/GL_FLOAT readPixels support on the live device, not guessed.
 * The input/output scanline convention is the donor GL source RAW grid (row zero
 * corresponds to first sensor RAW row), *not* the phone screen rotation.
 */
internal class Iris26972CGlReadback(
    private val color: Iris26972CColorDeveloper.Result,
) : AutoCloseable {
    private val gl = Iris26972CDonorSabreGpuMerge
    private val owner: EGLContext = EGL14.eglGetCurrentContext()
    private val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
    private val savedPackBuffer=gl.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
    private val savedPackAlign=gl.glInt(GLES30.GL_PACK_ALIGNMENT)
    private val savedPackRowLength=gl.glInt(GLES30.GL_PACK_ROW_LENGTH)
    private var fbo=0
    private var closed=false
    init {
        color.requireOwner()
        gl.requireCurrentContext()
        check(owner!=EGL14.EGL_NO_CONTEXT) {"26972 C readback requires EGL context"}
        val ids=IntArray(1)
        GLES30.glGenFramebuffers(1,ids,0)
        fbo=ids[0]
        check(fbo>0) {"26972 C readback FBO allocation failed"}
        gl.checkGl("C readback FBO creation")
    }
    private fun requireOwner() {
        color.requireOwner()
        check(!closed && owner==EGL14.eglGetCurrentContext()) {
            "26972 C expired readback or wrong GL owner"
        }
    }
    /**
     * Full float32 native pixel values are obtained without gamma conversion or
     * postprocess. A driver that disallows this format fails the request.
     */
    internal fun finalizedColorSource(): Iris26972CColorDeveloper.Result {
        requireOwner()
        return color
    }
    fun readSdr(x:Int,y:Int,w:Int,h:Int,dst:ByteBuffer) =
        read(color.encodedSrgbTexture,x,y,w,h,dst)
    fun readHdrRatio(x:Int,y:Int,w:Int,h:Int,dst:ByteBuffer) =
        read(color.donorHdrRatioTexture,x,y,w,h,dst)

    private fun read(texture:Int,x:Int,y:Int,w:Int,h:Int,dst:ByteBuffer) {
        requireOwner()
        require(x>=0 && y>=0 && w in 1..1024 && h in 1..1024 &&
            x<=color.width-w && y<=color.height-h && dst.isDirect &&
            !dst.isReadOnly && dst.capacity().toLong()>=w.toLong()*h*16) {
            "26972 C invalid bounded SDR/HDR source tile"
        }
        val bytes=w*h*16
        val saved=dst.position()
        val savedLimit=dst.limit()
        try {
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,fbo)
            GLES30.glFramebufferTexture2D(GLES30.GL_READ_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,texture,0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_READ_FRAMEBUFFER)==
                GLES30.GL_FRAMEBUFFER_COMPLETE) {"26972 C FLOAT16 color tile FBO unavailable"}
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
            dst.clear()
            dst.limit(bytes)
            GLES30.glReadPixels(x,y,w,h,GLES30.GL_RGBA,GLES30.GL_FLOAT,dst)
            gl.checkGl("C exact Float32 color tile readback")
            dst.position(0)
        } catch (error:Throwable) {
            dst.clear() // unreadable bytes must not be consumed as a photograph
            throw error
        } finally {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,savedPackBuffer)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,savedPackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,savedPackRowLength)
            // dst remains positioned at zero on success. Restore caller limit on
            // failure; callers always pass a fresh/cleared contiguous buffer.
            if(dst.limit()!=bytes) {dst.position(saved);dst.limit(savedLimit)}
        }
    }
    override fun close() {
        requireOwner()
        try {GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)} finally {
            fbo=0;closed=true
            state.restore()
        }
    }
}
