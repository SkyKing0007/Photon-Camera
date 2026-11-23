package com.hinnka.mycamera.processor
import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreAlignmentOffset

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/**
 * C-only final donor Sabre AlignAlt sparse grid -> normalized RGBA16F flow for BOTH
 * rejection and RAW accumulation. Reads the actual finalized LK texture; it MUST
 * NOT be substituted with a zero-flow, A/B motion estimate, or identity mask.
 *
 * The genuine C-only LK solver now owns this input in the source-integrated burst;
 * actual Android GPU/device validation remains NOT RUN and C production is disabled.
 */
internal object Iris26975COriginalSabreGpuConvertedFlow {
    private const val COMPONENT = "26972 C donor sparse LK flow conversion"
    private val gl = Iris26972CDonorSabreGpuMerge
    private const val BAYER_TILE_STRIDE = 8 // Donor 16 RAW-pixel final alignment grid.

    /** Caller must have produced `sparseLkTexture` from the C-only donor final LK/AlignAlt. */
    internal data class Plan(
        val rawWidth: Int,
        val rawHeight: Int,
        val sparseLkTexture: Int,
        val finalGridWidth: Int,
        val finalGridHeight: Int,
        val frameIndex: Int,
        val sparseGridMin: Int = 0,
        val scaleToBayerQuads: Float = 1f,
        val tileStrideQuads: Int = BAYER_TILE_STRIDE,
    ) {
        val transform: FloatArray get() {
            val shift = MgcSabreAlignmentOffset.forFrame(frameIndex,tileStrideQuads)
            return floatArrayOf(
                (rawWidth / 2).toFloat() / (finalGridWidth.toFloat() * tileStrideQuads),
                (rawHeight / 2).toFloat() / (finalGridHeight.toFloat() * tileStrideQuads),
                2f * shift.x / rawWidth, 2f * shift.y / rawHeight,
            )
        }
    }

    internal class Result private constructor(
        val flowTexture: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        val frameIndex: Int,
        val flowScaleOffset: FloatArray,
        private val owner: EGLContext,
    ) : AutoCloseable {
        private var closed = false
        internal fun requireOwner() {
            check(!closed && owner != EGL14.EGL_NO_CONTEXT && EGL14.eglGetCurrentContext() == owner) {
                "$COMPONENT released or wrong EGL context"
            }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(1,intArrayOf(flowTexture),0)
            closed = true
        }
        internal companion object {
            fun owned(id:Int,plan:Plan) = Result(
                id,plan.rawWidth,plan.rawHeight,plan.frameIndex,plan.transform,EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan:Plan) {
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            plan.rawWidth % 2 == 0 && plan.rawHeight % 2 == 0) { "$COMPONENT invalid RAW dimensions" }
        require(plan.frameIndex in 1..49 && plan.sparseLkTexture > 0 &&
            plan.sparseGridMin == 0 && plan.tileStrideQuads == BAYER_TILE_STRIDE &&
            plan.scaleToBayerQuads == 1f) {
            "$COMPONENT requires a native-grid donor LK alternate, not an A/B or dense flow"
        }
        require(plan.finalGridWidth == (plan.rawWidth + 15) / 16 &&
            plan.finalGridHeight == (plan.rawHeight + 15) / 16) {
            "$COMPONENT sparse LK flow dimensions must match donor 16-RAW-pixel final grid"
        }
        require(plan.transform.all { it.isFinite() } &&
            plan.transform[0] > 0f && plan.transform[1] > 0f) {
            "$COMPONENT invalid normalized flow transform"
        }
    }

    internal fun convert(plan:Plan):Result {
        validate(plan)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >=
            maxOf(plan.finalGridWidth,plan.finalGridHeight) &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 1) {
            "$COMPONENT unsupported GPU capacity"
        }
        gl.checkGl("before sparse flow conversion")
        val saved = Iris26972CDonorSabreGpuMerge.GlState.capture()
        var program = 0
        var framebuffer = 0
        var vertex = 0
        var output = 0
        var success = false
        try {
            program=gl.compileProgram(gl.VERTEX,Iris26972CDonorSabreAlignmentShaders.convertAlignment)
            val ids=IntArray(1)
            GLES30.glGenTextures(1,ids,0)
            output=ids[0]
            check(output>0 && output!=plan.sparseLkTexture) { "$COMPONENT invalid/aliased output texture" }
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,output)
            for (pname in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,pname,GLES30.GL_NEAREST)
            for (pname in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,pname,GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                plan.finalGridWidth,plan.finalGridHeight,0,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,null)
            gl.checkGl("converted LK flow allocation")
            val fbo=IntArray(1); GLES30.glGenFramebuffers(1,fbo,0);framebuffer=fbo[0]
            val vao=IntArray(1); GLES30.glGenVertexArrays(1,vao,0);vertex=vao[0]
            check(framebuffer>0 && vertex>0) { "$COMPONENT framebuffer/VAO allocation failed" }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,output,0)
            GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$COMPONENT LK flow FBO not renderable"
            }
            GLES30.glBindVertexArray(vertex)
            GLES30.glViewport(0,0,plan.finalGridWidth,plan.finalGridHeight)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glUseProgram(program)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,plan.sparseLkTexture)
            fun loc(name:String):Int=GLES30.glGetUniformLocation(program,name).also {
                check(it>=0) { "$COMPONENT donor shader missing $name" }
            }
            GLES30.glUniform1i(loc("uAlignment"),0)
            GLES30.glUniform2i(loc("uGridSize"),plan.finalGridWidth,plan.finalGridHeight)
            GLES30.glUniform1i(loc("uAlignmentTileSize"),1)
            GLES30.glUniform1i(loc("uAlignmentGridMin"),0)
            GLES30.glUniform1f(loc("uAlignmentScale"),1f)
            GLES30.glUniform2f(loc("uFlowNormalizationSize"),plan.rawWidth/2f,plan.rawHeight/2f)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gl.checkGl("donor sparse LK ConvertAlignment")
            success=true
            return Result.owned(output,plan)
        } finally {
            if(program>0)GLES30.glDeleteProgram(program)
            if(vertex>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vertex),0)
            if(framebuffer>0)GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if(!success && output>0)GLES30.glDeleteTextures(1,intArrayOf(output),0)
            saved.restore()
        }
    }
}
