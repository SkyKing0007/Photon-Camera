package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/**
 * C-only original RAW16 -> donor 1.29.0 S16 Bayer-quad gray pyramid.
 * Inputs are the retained real RAW_SENSOR R16UI texture, calibrated per frame.
 * No synthetic motion, A/B registration, YUV or fallback is used.
 *
 * This pyramid feeds C's implemented Lucas-Kanade flow driver; the combined
 * stages are host-validated only, not Android-driver or device-proven.
 */
internal object Iris26972CDonorSabreGpuGrayPyramid {
    private const val COMPONENT = "26972 C donor signed-S16 LK pyramid"
    private val gl = Iris26972CDonorSabreGpuMerge

    internal data class Plan(
        val rawWidth: Int,
        val rawHeight: Int,
        val raw16Texture: Int,
        val cfaPattern: Int,
        val blackLevels: FloatArray,
        val alignmentGain: Float,
        val maximumTileSize: Int,
    )

    internal data class Level(
        val texture: Int,
        val width: Int,
        val height: Int,
        val scale: Int,
        val tileSize: Int,
        val gridWidth: Int,
        val gridHeight: Int,
    )

    internal class Result private constructor(
        val levels: List<Level>,
        val rawWidth: Int,
        val rawHeight: Int,
        val maximumTileSize: Int,
        private val context: EGLContext,
    ) : AutoCloseable {
        private var closed = false
        internal fun requireOwner() {
            check(!closed && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT released or wrong EGL owner"
            }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(levels.size,levels.map{it.texture}.toIntArray(),0)
            closed=true
        }
        internal companion object {
            fun owned(levels:List<Level>,plan:Plan):Result=Result(
                levels,plan.rawWidth,plan.rawHeight,plan.maximumTileSize,
                EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan:Plan):Iris26972CDonorSabreLkPyramidPlan {
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            plan.rawWidth % 2==0 && plan.rawHeight % 2==0 &&
            plan.raw16Texture>0 && plan.cfaPattern in 0..3) {
            "$COMPONENT requires real even RAW_SENSOR R16UI geometry"
        }
        require(plan.blackLevels.size==4 &&
            plan.blackLevels.all{it.isFinite() && it in 0f..65535f} &&
            plan.alignmentGain.isFinite() && plan.alignmentGain>0f &&
            plan.alignmentGain<=64f) {
            "$COMPONENT requires actual sensor black levels and finite alignment gain"
        }
        return Iris26972CDonorSabreLkPyramidPlan(
            plan.rawWidth,plan.rawHeight,plan.maximumTileSize)
    }

    internal fun build(plan:Plan):Result {
        val schedule=validate(plan)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)>=
            maxOf(plan.rawWidth,plan.rawHeight) &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=1) {
            "$COMPONENT device cannot store original RAW16 and gray levels"
        }
        gl.checkGl("before donor raw-to-gray pyramid")
        val saved=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val textures=ArrayList<Int>()
        val levels=ArrayList<Level>()
        val programs=IntArray(3)
        var fbo=0
        var vao=0
        var success=false
        try {
            programs[0]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkGrayShaders.rawToGray)
            programs[1]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkGrayShaders.grayDownsample)
            programs[2]=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreLkGrayShaders.grayDownsample4)
            val ids=IntArray(1)
            GLES30.glGenFramebuffers(1,ids,0);fbo=ids[0]
            GLES30.glGenVertexArrays(1,ids,0);vao=ids[0]
            check(fbo>0 && vao>0){"$COMPONENT FBO/VAO failed"}
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true,true,true,true)
            fun location(program:Int,name:String):Int=
                GLES30.glGetUniformLocation(program,name).also { check(it>=0){"$COMPONENT missing $name"} }
            for ((index, geometry) in schedule.levels.withIndex()) {
                val textureIds=IntArray(1)
                GLES30.glGenTextures(1,textureIds,0)
                val out=textureIds[0]
                check(out>0 && out!=plan.raw16Texture && out !in textures) {
                    "$COMPONENT invalid/aliasing intermediate gray texture"
                }
                textures+=out
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,out)
                for (parameter in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,parameter,GLES30.GL_NEAREST)
                for (parameter in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,parameter,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_R16I,
                    geometry.width,geometry.height,0,GLES30.GL_RED_INTEGER,GLES30.GL_SHORT,null)
                gl.checkGl("C signed S16 level allocation")
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,out,0)
                GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                    GLES30.GL_FRAMEBUFFER_COMPLETE){"$COMPONENT GL_R16I FBO rejected"}
                val shader=if(index==0)0 else if(geometry.downsample==4)2 else 1
                val program=programs[shader]
                GLES30.glUseProgram(program)
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,
                    if(index==0)plan.raw16Texture else levels.last().texture)
                if(index==0){
                    GLES30.glUniform1i(location(program,"uRaw"),0)
                    GLES30.glUniform2i(location(program,"uRawSize"),plan.rawWidth,plan.rawHeight)
                    GLES30.glUniform2i(location(program,"uGraySize"),geometry.width,geometry.height)
                    // Original donor GLSL declares uCfaPattern but its quad-sum kernel
                    // does not read it. Real GLES linkers remove this uniform (location=-1).
                    // Preserve the exact shader and set the value only if it survives.
                    val cfaLocation=GLES30.glGetUniformLocation(program,"uCfaPattern")
                    if(cfaLocation>=0) GLES30.glUniform1i(cfaLocation,plan.cfaPattern)
                    GLES30.glUniform4fv(location(program,"uBlackLevels"),1,plan.blackLevels,0)
                    GLES30.glUniform1f(location(program,"uGain"),plan.alignmentGain)
                }else{
                    GLES30.glUniform1i(location(program,"uInput"),0)
                    GLES30.glUniform2i(location(program,"uInputSize"),
                        levels.last().width,levels.last().height)
                }
                GLES30.glViewport(0,0,geometry.width,geometry.height)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                gl.checkGl("donor S16 LK level $index")
                levels+=Level(out,geometry.width,geometry.height,
                    geometry.scale,geometry.tileSize,geometry.gridWidth,geometry.gridHeight)
            }
            success=true
            return Result.owned(levels,plan)
        }finally{
            for(program in programs)if(program>0)GLES30.glDeleteProgram(program)
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(fbo>0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
            if(!success && textures.isNotEmpty())
                GLES30.glDeleteTextures(textures.size,textures.toIntArray(),0)
            saved.restore()
        }
    }
}
