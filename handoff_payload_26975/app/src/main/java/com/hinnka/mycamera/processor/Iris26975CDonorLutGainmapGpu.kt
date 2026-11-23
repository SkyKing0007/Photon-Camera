package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Detached C-only, original bjzhou RAW LUT sidecar + GPU residual gainmap.
 * Exact equations from pinned `LutImageProcessor` and `GpuReferenceGainmapProducer`
 * at 0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * All three inputs must already be pixel-aligned on the same finalized output
 * geometry: before-LUT encoded SDR, after-LUT encoded SDR, linear extended-sRGB
 * HDR reference. The actual original donor LUT stack MUST supply `afterLut`;
 * this stage does not invent an identity LUT or invent HDR color from clipped
 * SDR. 2x sidecar and encoded gainmaps match the donor downsample grid.
 *
 * Not attached to the live capture owner until the complete original LUT,
 * Adobe/Guided HDR reference, and JPEG/R chain is present and verified.
 */
internal class Iris26975CDonorLutGainmapGpu:AutoCloseable {
    private val gpu=Iris26972CDonorSabreGpuMerge
    private val owner:EGLContext=EGL14.eglGetCurrentContext()
    private val programs=IntArray(2)
    private var vao=0
    private var closed=false

    private fun requireOwner() {
        check(!closed && owner!=EGL14.EGL_NO_CONTEXT && owner==EGL14.eglGetCurrentContext()) {
            "C bjzhou UHDR GPU EGL context ownership mismatch"
        }
        gpu.requireCurrentContext()
    }
    private fun alloc(internal:Int,w:Int,h:Int):Int {
        check(w>0 && h>0 && maxOf(w,h)<=gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE))
        val ids=IntArray(1);GLES30.glGenTextures(1,ids,0)
        check(ids[0]>0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        val fmt=if(internal==GLES30.GL_RGBA16F) GLES30.GL_HALF_FLOAT else GLES30.GL_UNSIGNED_BYTE
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,internal,w,h,0,GLES30.GL_RGBA,fmt,null)
        return ids[0]
    }
    private fun framebuffer(texture:Int):Int {
        val ids=IntArray(1);GLES30.glGenFramebuffers(1,ids,0)
        check(ids[0]>0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,ids[0])
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D,texture,0)
        GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE)
        return ids[0]
    }
    private fun bind(p:Int,name:String,index:Int,id:Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0+index)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        GLES30.glUniform1i(GLES30.glGetUniformLocation(p,name),index)
    }
    private fun draw(p:Int,fbo:Int,w:Int,h:Int,setup:()->Unit) {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
        GLES30.glViewport(0,0,w,h)
        GLES30.glUseProgram(p)
        GLES30.glBindVertexArray(vao)
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
        GLES30.glDisable(GLES30.GL_DEPTH_TEST)
        GLES30.glColorMask(true,true,true,true)
        setup()
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
    }
    private fun initPrograms() {
        if(programs[0]!=0)return
        programs[0]=gpu.compileProgram(gpu.VERTEX,Iris26975CDonorLutLuminanceShader.fragment)
        programs[1]=gpu.compileProgram(gpu.VERTEX,Iris26975CDonorGpuLutResidualShader.fragment)
        val ids=IntArray(1);GLES30.glGenVertexArrays(1,ids,0);vao=ids[0]
        check(programs.all{it>0} && vao>0)
    }

    /** Top-left, 8-bit donor encoded gainmap pixels ready for original JPEG/R metadata. */
    fun compute(beforeLut:Int,afterLut:Int,hdrLinear:Int,
        width:Int,height:Int,strength:Float):ByteBuffer {
        requireOwner()
        require(width>0 && height>0 && beforeLut>0 && afterLut>0 && hdrLinear>0 &&
            strength.isFinite() && strength>=0.25f && strength<=2.0f)
        val w=(width+1)/2;val h=(height+1)/2
        require(w.toLong()*h.toLong()<=80_000_000L)
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=3)
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        // glPixelStore/PBO state is independent of framebuffer/texture bindings.
        val oldPackBuffer=gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldPackAlign=gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldPackRows=gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        val tex=IntArray(2);val fb=IntArray(2)
        try {
            initPrograms()
            tex[0]=alloc(GLES30.GL_RGBA16F,w,h)
            tex[1]=alloc(GLES30.GL_RGBA8,w,h)
            fb[0]=framebuffer(tex[0]);fb[1]=framebuffer(tex[1])
            val p0=programs[0]
            draw(p0,fb[0],w,h){
                bind(p0,"uBeforeLutTexture",0,beforeLut)
                bind(p0,"uAfterLutTexture",1,afterLut)
                GLES30.glUniform1f(GLES30.glGetUniformLocation(p0,"uOffset"),1e-4f)
            }
            val p1=programs[1]
            draw(p1,fb[1],w,h){
                bind(p1,"uLutLuminanceGainTexture",0,tex[0])
                bind(p1,"uSdrTexture",1,afterLut)
                bind(p1,"uHdrTexture",2,hdrLinear)
                GLES30.glUniform1f(GLES30.glGetUniformLocation(p1,"uMinGainRatio"),.25f)
                GLES30.glUniform1f(GLES30.glGetUniformLocation(p1,"uMaxGainRatio"),4f)
                GLES30.glUniform1f(GLES30.glGetUniformLocation(p1,"uOffset"),1e-4f)
                GLES30.glUniform1f(GLES30.glGetUniformLocation(p1,"uStrength"),strength)
            }
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,fb[1])
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
            val rgba=ByteBuffer.allocateDirect(w*h*4).order(ByteOrder.nativeOrder())
            GLES30.glReadPixels(0,0,w,h,GLES30.GL_RGBA,GLES30.GL_UNSIGNED_BYTE,rgba)
            gpu.checkGl("C bjzhou GPU UHDR measured LUT + residual readback")
            // Original donor maps GL RGBA R channel to ALPHA_8 Bitmap and
            // reverses bottom-origin GL readPixels into Android's top-origin.
            val alpha=ByteBuffer.allocateDirect(w*h)
            for(y in 0 until h)for(x in 0 until w) {
                alpha.put(rgba.get(((h-1-y)*w+x)*4))
            }
            alpha.position(0)
            return alpha
        }finally {
            if(fb.any{it>0})GLES30.glDeleteFramebuffers(fb.count{it>0},fb.filter{it>0}.toIntArray(),0)
            if(tex.any{it>0})GLES30.glDeleteTextures(tex.count{it>0},tex.filter{it>0}.toIntArray(),0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,oldPackBuffer)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,oldPackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,oldPackRows)
            state.restore()
        }
    }
    override fun close(){
        if(closed)return
        requireOwner()
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        try {
            programs.forEach{if(it>0)GLES30.glDeleteProgram(it)}
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            vao=0;closed=true
        } finally {state.restore()}
    }
}
