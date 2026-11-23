package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/** C-owned MGC Sabre reverse-rejection -> forward RAW/4 mask stage. */
internal object Iris26975COriginalSabreGpuDilation {
    private const val COMPONENT = "26972 C donor Sabre rejection dilation"
    private val gl = Iris26972CDonorSabreGpuMerge

    internal data class Plan(
        val rawWidth: Int,
        val rawHeight: Int,
        val reverseRejectionTextures: IntArray,
    ) {
        val inputWidth: Int get() = rawWidth / 2
        val inputHeight: Int get() = rawHeight / 2
        val outputWidth: Int get() = (inputWidth + 1) / 2
        val outputHeight: Int get() = (inputHeight + 1) / 2
    }

    internal class Result private constructor(
        val mergeWeights: IntArray,
        val rawWidth: Int,
        val rawHeight: Int,
        private val context: EGLContext,
    ) : AutoCloseable {
        private var released = false
        internal fun requireOwner() {
            check(!released && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT context/ownership violation"
            }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(mergeWeights.size, mergeWeights, 0)
            released = true
        }
        internal companion object {
            fun owned(weights: IntArray, width: Int, height: Int) =
                Result(weights, width, height, EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan: Plan) {
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            (plan.rawWidth and 1) == 0 && (plan.rawHeight and 1) == 0) {
            "$COMPONENT requires even sensor Bayer geometry"
        }
        require(plan.reverseRejectionTextures.size in 1..49 &&
            plan.reverseRejectionTextures.all { it > 0 } &&
            plan.reverseRejectionTextures.toSet().size == plan.reverseRejectionTextures.size) {
            "$COMPONENT requires one distinct donor reverse mask per NORMAL alternate frame"
        }
    }

    /** Accept actual C-owned rejection results, not arbitrary A/B rejection texture ids. */
    internal fun process(source: Iris26975COriginalSabreGpuRejection.Result): Result {
        source.checkOwner()
        return process(Plan(source.rawWidth, source.rawHeight,
            source.reverseRejection.copyOf()))
    }

    /**
     * Only the donor R8 reverse masks are permitted; caller must supply the
     * results of Iris26975COriginalSabreGpuRejection, not an A/B spatial mask.
     * This is a GPU-only preparation stage. It does not publish a photograph.
     */
    internal fun process(plan: Plan): Result {
        validate(plan)
        gl.requireCurrentContext()
        require(plan.rawWidth <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            plan.rawHeight <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 1) {
            "$COMPONENT GL texture capacity missing"
        }
        val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val outputs = IntArray(plan.reverseRejectionTextures.size)
        var program = 0
        var framebuffer = 0
        var vertexArray = 0
        var success = false
        try {
            program = gl.compileProgram(gl.VERTEX,
                Iris26972CDonorSabreDilateShaders.dilateRejection)
            GLES30.glGenTextures(outputs.size, outputs, 0)
            check(outputs.all { it > 0 && it !in plan.reverseRejectionTextures }) {
                "$COMPONENT invalid/aliased R8 output allocation"
            }
            for (output in outputs) {
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, output)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_R8,
                    plan.outputWidth,plan.outputHeight,0,GLES30.GL_RED,GLES30.GL_UNSIGNED_BYTE,null)
                gl.checkGl("donor R8 forward-mask allocation")
            }
            val fbo = IntArray(1)
            GLES30.glGenFramebuffers(1,fbo,0)
            framebuffer = fbo[0]
            val vao = IntArray(1)
            GLES30.glGenVertexArrays(1,vao,0)
            vertexArray = vao[0]
            check(framebuffer > 0 && vertexArray > 0) {
                "$COMPONENT failed to allocate GL objects"
            }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glBindVertexArray(vertexArray)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glUseProgram(program)
            val source = GLES30.glGetUniformLocation(program,"uRejection")
            val dimensions = GLES30.glGetUniformLocation(program,"uInputSize")
            check(source >= 0 && dimensions >= 0) {
                "$COMPONENT missing donor sampler/size uniform"
            }
            GLES30.glUniform1i(source,0)
            GLES30.glUniform2i(dimensions,plan.inputWidth,plan.inputHeight)
            GLES30.glViewport(0,0,plan.outputWidth,plan.outputHeight)
            for (i in outputs.indices) {
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,plan.reverseRejectionTextures[i])
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,outputs[i],0)
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT1,
                    GLES30.GL_TEXTURE_2D,0,0)
                GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "$COMPONENT R8 output FBO incomplete"
                }
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                gl.checkGl("donor dilation draw")
            }
            success = true
            return Result.owned(outputs,plan.rawWidth,plan.rawHeight)
        } finally {
            if (program > 0) GLES30.glDeleteProgram(program)
            if (framebuffer > 0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if (vertexArray > 0) GLES30.glDeleteVertexArrays(1,intArrayOf(vertexArray),0)
            if (!success) {
                val allocated = outputs.filter { it > 0 }.toIntArray()
                if (allocated.isNotEmpty()) GLES30.glDeleteTextures(allocated.size,allocated,0)
            }
            restore.restore()
        }
    }
}
