package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/**
 * C-only genuine donor 1.29.0 two-pass RAW16 UnblockerRaw10 + UnblockerBlur.
 * Requires actual C RAW16 GPU upload and validated *per-frame* Camera2 noise metadata.
 * Runs with the 1-cell padded border and R8 integer rounding before Sabre rejection.
 * Connected to C's isolated LK/Sabre burst and shutter source; production gated OFF.
 * Android-driver and real RAW validation remain required.
 */
internal object Iris26972CDonorSabreGpuUnblocker {
    private const val COMPONENT = "26972 C donor RAW16 unblocker"
    private val gl = Iris26972CDonorSabreGpuMerge
    internal data class Plan(
        val rawWidth:Int,
        val rawHeight:Int,
        val raw16Texture:Int,
        val cfaPattern:Int,
        val blackLevels:FloatArray,
        val shotNoise:FloatArray,
        val readNoise:FloatArray,
    ) {
        val outputWidth:Int get()=(rawWidth+15)/16
        val outputHeight:Int get()=(rawHeight+15)/16
    }
    internal class Result private constructor(
        val texture:Int,val rawWidth:Int,val rawHeight:Int,private val owner:EGLContext
    ):AutoCloseable {
        private var closed=false
        internal fun requireOwner(){ check(!closed && owner!=EGL14.EGL_NO_CONTEXT &&
            EGL14.eglGetCurrentContext()==owner){"$COMPONENT wrong EGL owner/released"} }
        override fun close(){ requireOwner();GLES30.glDeleteTextures(1,intArrayOf(texture),0);closed=true }
        internal companion object { fun owned(id:Int,w:Int,h:Int)=Result(id,w,h,EGL14.eglGetCurrentContext()) }
    }
    internal fun validate(plan:Plan){
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            plan.rawWidth%2==0 && plan.rawHeight%2==0 && plan.raw16Texture>0 &&
            plan.cfaPattern in 0..3){"$COMPONENT invalid RAW sensor geometry/CFA"}
        require(plan.blackLevels.size==4 && plan.shotNoise.size==4 && plan.readNoise.size==4 &&
            plan.blackLevels.all{it.isFinite() && it>=0f && it<=65535f} &&
            plan.shotNoise.all{it.isFinite() && it>=0f} &&
            plan.readNoise.all{it.isFinite() && it>=0f}){
            "$COMPONENT missing/unusable donor green-noise calibration"
        }
    }
    internal fun compute(plan:Plan):Result{
        validate(plan)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)>=maxOf(plan.rawWidth,plan.rawHeight) &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=1){"$COMPONENT GL capacity unsupported"}
        gl.checkGl("before donor unblocker")
        val saved=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val outputs=IntArray(2)
        var rawProgram=0;var blurProgram=0;var framebuffer=0;var vertex=0
        var completed=false
        try {
            rawProgram=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreUnblockerShaders.unblocker)
            blurProgram=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreUnblockerShaders.unblockerBlur)
            GLES30.glGenTextures(2,outputs,0)
            check(outputs.all{it>0 && it!=plan.raw16Texture} && outputs[0]!=outputs[1]){
                "$COMPONENT invalid/aliased R8 allocations"
            }
            // Donor intermediate extends one whole cell beyond every output edge.
            allocateR8(outputs[0],plan.outputWidth+2,plan.outputHeight+2,GLES30.GL_NEAREST)
            allocateR8(outputs[1],plan.outputWidth,plan.outputHeight,GLES30.GL_LINEAR)
            val ids=IntArray(1);GLES30.glGenFramebuffers(1,ids,0);framebuffer=ids[0]
            GLES30.glGenVertexArrays(1,ids,0);vertex=ids[0]
            check(framebuffer>0 && vertex>0){"$COMPONENT GL framebuffer/VAO allocation failed"}
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glBindVertexArray(vertex)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glColorMask(true,true,true,true)
            fun attach(texture:Int){
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,texture,0)
                GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                    GLES30.GL_FRAMEBUFFER_COMPLETE){"$COMPONENT R8 FBO unsupported"}
            }
            fun loc(program:Int,name:String):Int=GLES30.glGetUniformLocation(program,name).also {
                check(it>=0){"$COMPONENT missing donor uniform $name"}
            }
            GLES30.glUseProgram(rawProgram)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,plan.raw16Texture)
            GLES30.glUniform1i(loc(rawProgram,"uRaw"),0)
            GLES30.glUniform2i(loc(rawProgram,"uRawSize"),plan.rawWidth,plan.rawHeight)
            // The exact donor fragment declares uGridSize but never reads it.
            // GLES compilers remove that uniform; requiring a linked location
            // would deterministically abort on real Android drivers.
            val gridLocation = GLES30.glGetUniformLocation(rawProgram,"uGridSize")
            if (gridLocation >= 0) GLES30.glUniform2i(
                gridLocation,plan.outputWidth,plan.outputHeight)
            GLES30.glUniform2i(loc(rawProgram,"uTileOffset"),-1,-1)
            GLES30.glUniform1i(loc(rawProgram,"uCfaPattern"),plan.cfaPattern)
            GLES30.glUniform1f(loc(rawProgram,"uBlackLevelGreen"),
                0.5f*(plan.blackLevels[1]+plan.blackLevels[2]))
            GLES30.glUniform1f(loc(rawProgram,"uNoiseQuadratic"),0f)
            GLES30.glUniform1f(loc(rawProgram,"uNoiseScale"),
                0.5f*(plan.shotNoise[1]+plan.shotNoise[2]))
            GLES30.glUniform1f(loc(rawProgram,"uNoiseOffset"),
                0.5f*(plan.readNoise[1]+plan.readNoise[2]))
            GLES30.glUniform1f(loc(rawProgram,"uOutputScale"),1f)
            GLES30.glUniform1f(loc(rawProgram,"uOutputOffset"),0.45f)
            attach(outputs[0]);GLES30.glViewport(0,0,plan.outputWidth+2,plan.outputHeight+2)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3);gl.checkGl("donor RAW16 unblocker")
            GLES30.glUseProgram(blurProgram)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,outputs[0])
            GLES30.glUniform1i(loc(blurProgram,"uPreBlur"),0)
            attach(outputs[1]);GLES30.glViewport(0,0,plan.outputWidth,plan.outputHeight)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3);gl.checkGl("donor R8 unblocker blur")
            completed=true
            return Result.owned(outputs[1],plan.rawWidth,plan.rawHeight)
        } finally {
            if(rawProgram>0)GLES30.glDeleteProgram(rawProgram)
            if(blurProgram>0)GLES30.glDeleteProgram(blurProgram)
            if(vertex>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vertex),0)
            if(framebuffer>0)GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if(outputs[0]>0)GLES30.glDeleteTextures(1,intArrayOf(outputs[0]),0)
            if(!completed && outputs[1]>0)GLES30.glDeleteTextures(1,intArrayOf(outputs[1]),0)
            saved.restore()
        }
    }
    private fun allocateR8(id:Int,w:Int,h:Int,filter:Int){
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        for(param in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,param,filter)
        for(param in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,param,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_R8,w,h,0,
            GLES30.GL_RED,GLES30.GL_UNSIGNED_BYTE,null)
        gl.checkGl("donor R8 unblocker allocation")
    }
}
