package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreRejectionTuning
import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/**
 * Experiment C-only pinned bjzhou 1.29.0 base-reference-color + Sabre reverse rejection.
 * This consumes genuine donor-generated guide, flow, unblocker and QMC noise textures.
 * It DOES NOT synthesize alignment or noise estimates. Returned reverse weights MUST
 * be run through the donor dilation stage before C's Sabre merge/coverage; they are
 * not directly usable as the forward acceptance masks.
 *
 * A/B source is not touched. Caller must hold one current GL context throughout.
 */
internal object Iris26975COriginalSabreGpuRejection {
    private const val COMPONENT = "26972 C donor Sabre rejection"
    private const val BORDER_PIXELS = 1.5f
    private val gl = Iris26972CDonorSabreGpuMerge

    internal data class Alternative(
        val guideTexture: Int,
        val flowTexture: Int,
        val unblockerTexture: Int,
        val qmcNoiseTexture: Int,
        val flowScaleOffset: FloatArray,
    )
    internal data class Plan(
        val rawWidth: Int,
        val rawHeight: Int,
        val referenceGuideTexture: Int,
        val alternatives: List<Alternative>,
    ) {
        val guideWidth: Int get() = (rawWidth + 1) / 2
        val guideHeight: Int get() = (rawHeight + 1) / 2
    }
    /**
     * Pinned V25 builds BaseFrameReferenceColor ONCE before iterating alternates.
     * This C-only owner retains that exact donor shader output for the complete
     * burst, preventing N-1 redundant filters/allocations on 30-frame captures.
     */
    internal class ReferenceColor private constructor(
        val texture: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        val originalReferenceGuideTexture: Int,
        private val context: EGLContext,
    ) : AutoCloseable {
        private var closed = false
        internal fun requireOwner(plan: Plan) {
            check(!closed && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context && texture > 0 &&
                rawWidth == plan.rawWidth && rawHeight == plan.rawHeight &&
                originalReferenceGuideTexture == plan.referenceGuideTexture) {
                "$COMPONENT reference color cannot be reused across sensors, guides or EGL contexts"
            }
        }
        override fun close() {
            check(!closed && texture > 0 && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT reference color released from wrong GL owner"
            }
            GLES30.glDeleteTextures(1, intArrayOf(texture), 0)
            closed = true
        }
        internal companion object {
            fun own(texture:Int,rawWidth:Int,rawHeight:Int,guide:Int):ReferenceColor =
                ReferenceColor(texture,rawWidth,rawHeight,guide,EGL14.eglGetCurrentContext())
        }
    }

    internal class Result private constructor(
        val baseReferenceColor: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        val reverseRejection: IntArray,
        val pixelDifference: IntArray,
        private val context: EGLContext,
        private val ownsBaseReferenceColor: Boolean,
    ) : AutoCloseable {
        private var closed = false
        internal fun checkOwner() {
            check(!closed && EGL14.eglGetCurrentContext() == context &&
                context != EGL14.EGL_NO_CONTEXT) { "$COMPONENT invalid result/context" }
        }
        override fun close() {
            checkOwner()
            val owned = if (ownsBaseReferenceColor) {
                intArrayOf(baseReferenceColor, *reverseRejection, *pixelDifference)
            } else {
                intArrayOf(*reverseRejection, *pixelDifference)
            }
            GLES30.glDeleteTextures(owned.size, owned, 0)
            closed = true
        }
        internal companion object {
            fun own(base: Int, width: Int, height: Int, rejection: IntArray,
                difference: IntArray, ownsBase: Boolean = true) = Result(
                base, width, height, rejection, difference,
                EGL14.eglGetCurrentContext(), ownsBase)
        }
    }

    internal fun validate(plan: Plan) {
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            plan.rawWidth % 2 == 0 && plan.rawHeight % 2 == 0) {
            "$COMPONENT requires even RAW Bayer geometry"
        }
        require(plan.referenceGuideTexture > 0 && plan.alternatives.size in 1..49) {
            "$COMPONENT missing reference guide or NORMAL RAW alternatives"
        }
        for ((index, alt) in plan.alternatives.withIndex()) {
            require(alt.guideTexture > 0 && alt.flowTexture > 0 &&
                alt.unblockerTexture > 0 && alt.qmcNoiseTexture > 0 &&
                alt.flowScaleOffset.size == 4 &&
                alt.flowScaleOffset.all { it.isFinite() } &&
                alt.flowScaleOffset[0] > 0f && alt.flowScaleOffset[1] > 0f) {
                "$COMPONENT incomplete donor alignment/noise for alternate $index"
            }
            require(alt.guideTexture != plan.referenceGuideTexture) {
                "$COMPONENT guide must not alias base reference input"
            }
        }
    }

    /**
     * Original donor V25 base-frame reference color, calculated exactly once.
     * C owns the texture until the entire admitted NORMAL burst is processed.
     */
    internal fun prepareReferenceColor(
        rawWidth: Int, rawHeight: Int, referenceGuideTexture: Int,
    ): ReferenceColor {
        require(rawWidth in 16..16384 && rawHeight in 16..16384 &&
            rawWidth % 2 == 0 && rawHeight % 2 == 0 && referenceGuideTexture > 0) {
            "$COMPONENT invalid donor reference RAW dimensions or input"
        }
        gl.requireCurrentContext()
        require(rawWidth <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            rawHeight <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 1) {
            "$COMPONENT donor base-frame reference filter unavailable"
        }
        val saved = Iris26972CDonorSabreGpuMerge.GlState.capture()
        var program = 0
        var texture = 0
        var framebuffer = 0
        var vao = 0
        var finished = false
        try {
            program = gl.compileProgram(gl.VERTEX,
                Iris26972CDonorSabreRejectShaders.baseFrameReferenceColor)
            val textures = IntArray(1)
            GLES30.glGenTextures(1, textures, 0)
            texture = textures[0]
            check(texture > 0 && texture != referenceGuideTexture) {
                "$COMPONENT base reference output aliases donor input"
            }
            val guideWidth = rawWidth / 2
            val guideHeight = rawHeight / 2
            makeTexture(texture, guideWidth, guideHeight,
                GLES30.GL_RGBA16F, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, GLES30.GL_LINEAR)
            val fbos = IntArray(1)
            GLES30.glGenFramebuffers(1, fbos, 0)
            framebuffer = fbos[0]
            val vaos = IntArray(1)
            GLES30.glGenVertexArrays(1, vaos, 0)
            vao = vaos[0]
            check(framebuffer > 0 && vao > 0) {
                "$COMPONENT reference VAO/FBO creation failed"
            }
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glUseProgram(program)
            bind(program,"uBaseGuide",0,referenceGuideTexture)
            GLES30.glUniform2i(loc(program,"uGuideSize"),guideWidth,guideHeight)
            attach(intArrayOf(texture))
            GLES30.glViewport(0,0,guideWidth,guideHeight)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gl.checkGl("donor single base reference color draw")
            finished = true
            return ReferenceColor.own(texture,rawWidth,rawHeight,referenceGuideTexture)
        } finally {
            if(program>0) GLES30.glDeleteProgram(program)
            if(vao>0) GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(framebuffer>0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if(!finished && texture>0) GLES30.glDeleteTextures(1,intArrayOf(texture),0)
            saved.restore()
        }
    }

    /**
     * Donor reverse rejection; accepts an optional authentic, same-burst cached
     * base color. Legacy single-call ownership remains unchanged for host audit.
     */
    internal fun process(plan: Plan, referenceColor: ReferenceColor? = null): Result {
        validate(plan)
        gl.requireCurrentContext()
        val limit = gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)
        require(plan.rawWidth <= limit && plan.rawHeight <= limit &&
            gl.glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 2 &&
            gl.glInt(GLES30.GL_MAX_DRAW_BUFFERS) >= 2 &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 5) {
            "$COMPONENT requires full-resolution support, two MRTs and five samplers"
        }
        referenceColor?.requireOwner(plan)
        val reuseBase = referenceColor != null
        val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val maskOffset = if (reuseBase) 0 else 1
        val owned = IntArray(maskOffset + 2 * plan.alternatives.size)
        var baseProgram = 0
        var rejectProgram = 0
        var framebuffer = 0
        var vao = 0
        var completed = false
        try {
            if (!reuseBase) baseProgram = gl.compileProgram(gl.VERTEX,
                Iris26972CDonorSabreRejectShaders.baseFrameReferenceColor)
            rejectProgram = gl.compileProgram(gl.VERTEX,
                Iris26972CDonorSabreRejectShaders.rejection)
            GLES30.glGenTextures(owned.size, owned, 0)
            val sharedTexture = referenceColor?.texture ?: 0
            check(owned.all { it > 0 && it != plan.referenceGuideTexture &&
                (sharedTexture == 0 || it != sharedTexture) &&
                plan.alternatives.none { a -> it == a.guideTexture || it == a.flowTexture ||
                    it == a.unblockerTexture || it == a.qmcNoiseTexture } }) {
                "$COMPONENT output allocation/alias failure"
            }
            if (!reuseBase) makeTexture(owned[0], plan.guideWidth, plan.guideHeight,
                GLES30.GL_RGBA16F, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, GLES30.GL_LINEAR)
            for (index in plan.alternatives.indices) {
                makeTexture(owned[maskOffset + index * 2], plan.guideWidth, plan.guideHeight,
                    GLES30.GL_R8, GLES30.GL_RED, GLES30.GL_UNSIGNED_BYTE, GLES30.GL_LINEAR)
                makeTexture(owned[maskOffset + index * 2 + 1], plan.guideWidth, plan.guideHeight,
                    GLES30.GL_R8, GLES30.GL_RED, GLES30.GL_UNSIGNED_BYTE, GLES30.GL_NEAREST)
            }
            val fbos = IntArray(1)
            GLES30.glGenFramebuffers(1, fbos, 0)
            framebuffer = fbos[0]
            val vaos = IntArray(1)
            GLES30.glGenVertexArrays(1, vaos, 0)
            vao = vaos[0]
            check(framebuffer != 0 && vao != 0) { "$COMPONENT VAO/FBO allocation failed" }
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
            if (!reuseBase) {
                GLES30.glUseProgram(baseProgram)
                bind(baseProgram, "uBaseGuide",0,plan.referenceGuideTexture)
                GLES30.glUniform2i(loc(baseProgram, "uGuideSize"),plan.guideWidth,plan.guideHeight)
                attach(intArrayOf(owned[0]))
                draw(plan)
            }
            val baseReferenceTexture = referenceColor?.texture ?: owned[0]
            GLES30.glUseProgram(rejectProgram)
            GLES30.glUniform2i(loc(rejectProgram,"uGuideSize"),plan.guideWidth,plan.guideHeight)
            GLES30.glUniform2i(loc(rejectProgram,"uRejectionSize"),plan.guideWidth,plan.guideHeight)
            GLES30.glUniform4f(loc(rejectProgram,"uFrameBorderPadded"),
                BORDER_PIXELS/plan.rawWidth,BORDER_PIXELS/plan.rawHeight,
                1f-BORDER_PIXELS/plan.rawWidth,1f-BORDER_PIXELS/plan.rawHeight)
            GLES30.glUniform2f(loc(rejectProgram,"uUnblockerScale"),1f,1f)
            GLES30.glUniform4f(loc(rejectProgram,"uNoiseTextureScaleBias"),.9f,.5f,.05f,.25f)
            GLES30.glUniform2f(loc(rejectProgram,"uColorDifferenceMultiplier"),
                MgcSabreRejectionTuning.COLOR_DIFFERENCE_RGB,
                MgcSabreRejectionTuning.COLOR_DIFFERENCE_GREEN)
            val flowThresholds = MgcSabreRejectionTuning.flowVariationThresholds(plan.guideWidth)
            GLES30.glUniform1f(loc(rejectProgram,"uUnblockerReductionThreshold"),flowThresholds.unblockerReduction)
            GLES30.glUniform1f(loc(rejectProgram,"uExtraMotionRobustnessBoost"),MgcSabreRejectionTuning.EXTRA_MOTION_ROBUSTNESS_BOOST)
            GLES30.glUniform1f(loc(rejectProgram,"uMotionRobustnessBoostVarianceThreshold"),MgcSabreRejectionTuning.MOTION_ROBUSTNESS_VARIANCE_THRESHOLD)
            GLES30.glUniform1f(loc(rejectProgram,"uExtraMotionRobustnessMotionThreshold"),flowThresholds.extraMotionRobustness)
            for ((index, a) in plan.alternatives.withIndex()) {
                bind(rejectProgram,"uBaseGuide",0,baseReferenceTexture)
                bind(rejectProgram,"uAltGuide",1,a.guideTexture)
                bind(rejectProgram,"uFlow",2,a.flowTexture)
                bind(rejectProgram,"uUnblocker",3,a.unblockerTexture)
                bind(rejectProgram,"uNoiseEstimates",4,a.qmcNoiseTexture)
                GLES30.glUniform4fv(loc(rejectProgram,"uFlowScaleOffset"),1,a.flowScaleOffset,0)
                attach(intArrayOf(owned[maskOffset+index*2],owned[maskOffset+index*2+1]))
                draw(plan)
            }
            completed = true
            return Result.own(baseReferenceTexture,plan.rawWidth,plan.rawHeight,
                IntArray(plan.alternatives.size) { owned[maskOffset+it*2] },
                IntArray(plan.alternatives.size) { owned[maskOffset+it*2+1] },
                ownsBase = !reuseBase)
        } finally {
            if (baseProgram > 0) GLES30.glDeleteProgram(baseProgram)
            if (rejectProgram > 0) GLES30.glDeleteProgram(rejectProgram)
            if (vao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
            if (framebuffer > 0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if (!completed) {
                val allocated = owned.filter { it > 0 }.toIntArray()
                if (allocated.isNotEmpty()) GLES30.glDeleteTextures(allocated.size,allocated,0)
            }
            restore.restore()
        }
    }

    private fun loc(program: Int, name: String): Int =
        GLES30.glGetUniformLocation(program,name).also { check(it >= 0) {
            "$COMPONENT missing donor uniform $name"
        } }

    private fun bind(program: Int, uniform: String, unit: Int, texture: Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0+unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,texture)
        GLES30.glUniform1i(loc(program,uniform),unit)
    }

    private fun makeTexture(id:Int,w:Int,h:Int,internal:Int,format:Int,type:Int,filter:Int) {
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,internal,w,h,0,format,type,null)
        gl.checkGl("donor rejection texture allocation")
    }

    private fun attach(outputs: IntArray) {
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D,outputs[0],0)
        // Detach any old second MRT target before the single-target base pass.
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT1,
            GLES30.GL_TEXTURE_2D,if(outputs.size==2) outputs[1] else 0,0)
        GLES30.glDrawBuffers(outputs.size,
            IntArray(outputs.size) { GLES30.GL_COLOR_ATTACHMENT0+it },0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE) {
            "$COMPONENT donor rejection framebuffer not supported"
        }
        gl.checkGl("donor rejection framebuffer")
    }
    private fun draw(plan: Plan) {
        GLES30.glViewport(0,0,plan.guideWidth,plan.guideHeight)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
        gl.checkGl("donor rejection draw")
    }
}
