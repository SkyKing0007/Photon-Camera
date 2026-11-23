package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.opengl.GLES30

/**
 * Experiment C only. The exact bjzhou PhotonCamera 1.29.0 Sabre `copyMask`, `copyAlpha`, and
 * `dehomogenize` shaders perform the coverage and weighted-RGB normalization after donor merge.
 * Reference: GlesMgcRawSpatialStacker.kt lines 2308, 2402, 2444 and 2762-2912 of pinned
 * commit 0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * This is NOT a complete Sabre producer: caller must first deliver authentic independently
 * aligned/rejected donor NORMAL RAW frames and the C-only accumulated merge textures.
 * The batched API needs its rejection textures alive through normalization. The bounded
 * streaming API instead consumes each actual R8 mask into one quarter-grid R8 coverage target
 * immediately after donor fusion, then lets the alternate's full-size mask be freed.
 * No synthetic weight, identity flow, A/B, or alternative algorithm is substituted.
 */
internal object Iris26972CDonorSabreGpuNormalize {
    private const val COMPONENT = "26972 C donor Sabre coverage/dehomogenize"
    private val gpu = Iris26972CDonorSabreGpuMerge

    /** Exact donor quantized R8 coverage lookup; R8 keeps sum(weights/scale) within [0,1]. */
    internal fun accumulatedWeightScale(count: Int): Float = when {
        count < 2 -> error("$COMPONENT requires at least two NORMAL RAW frames")
        count < 4 -> 3f
        count < 6 -> 5f
        count < 16 -> 15f
        count < 18 -> 17f
        count < 52 -> 51f
        count < 86 -> 85f
        else -> 255f
    }

    /** Result remains owned by caller. Any GL-stage failure poisons it; caller must close it. */
    internal fun normalize(
        plan: Iris26972CDonorSabreGpuMerge.Plan,
        result: Iris26972CDonorSabreGpuMerge.Result,
    ) {
        gpu.validate(plan)
        result.verifyNormalizationPlan(plan)
        performNormalize(plan.width, plan.height,
            plan.frames.map { it.rejectionTexture }.toIntArray(), result)
    }

    /**
     * The donor's original R8 mask accumulation, evaluated in exactly the original frame order.
     * This replaces O(N * full-resolution) resident R8 masks with ONE quarter-resolution R8
     * texture (50MP / 16 = ~3.1MB), without changing the copyMask shader or GL_ONE blending.
     *
     * Every append must occur AFTER the same genuine mask was used by Merge.Stream, BEFORE
     * its owning alternate is released. IDs are retained as immutable provenance ONLY:
     * deleted GL names must never be dereferenced here or by the final normalizer.
     */
    internal class CoverageStream private constructor(
        val width: Int, val height: Int, private val expectedFrames: Int,
        private val context: android.opengl.EGLContext,
        val texture: Int, private val framebuffer: Int,
        private val vertexArray: Int, private val program: Int,
    ) : AutoCloseable {
        private val originals = ArrayList<Int>(expectedFrames)
        private var released = false
        private var poisoned = false
        private var normalized = false
        internal val consumed: Int get() = originals.size
        /**
         * Exact donor quarter-grid R8 coverage is the only residual-noise
         * evidence. The reference contributes one accepted RAW; each R8
         * alternate-mask weight contributes its measured fractional support.
         * Transport variance multiplier = 1 / effective accepted samples.
         */
        internal fun readMeasuredResidual(): Iris26975CMeasuredSabreResidual {
            requireOwner()
            check(normalized && originals.size == expectedFrames) {
                "$COMPONENT residual map requires completed real donor normalization"
            }
            val w=(width+3)/4
            val h=(height+3)/4
            val raw=java.nio.ByteBuffer.allocateDirect(w*h)
            val saved=Iris26972CDonorSabreGpuMerge.GlState.capture()
            val pack=gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
            val packAlign=gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
            val packRows=gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
            try {
                GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,framebuffer)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_READ_FRAMEBUFFER)==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) { "$COMPONENT missing measured R8 coverage FBO" }
                GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
                GLES30.glReadPixels(0,0,w,h,GLES30.GL_RED,GLES30.GL_UNSIGNED_BYTE,raw)
                gpu.checkGl("C real donor R8 residual map readback")
            } finally {
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,pack)
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,packAlign)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,packRows)
                saved.restore()
            }
            val scale=accumulatedWeightScale(expectedFrames)
            val values=ShortArray(w*h)
            var total=0.0
            for (i in values.indices) {
                val actualCoverage=(raw.get(i).toInt() and 255)/255.0
                val effective=1.0 + scale*actualCoverage
                val variance=1.0/effective
                val q8=(variance*256.0).toInt().coerceIn(1,256)
                values[i]=q8.toShort()
                total+=variance
            }
            val measuredMean=(total/values.size).toFloat()
            check(measuredMean.isFinite() && measuredMean > 0f && measuredMean <= 1f) {
                "$COMPONENT invalid measured physical Sabre residual"
            }
            return Iris26975CMeasuredSabreResidual(w,h,values,measuredMean)
        }
        private fun requireOwner() {
            check(!released && !poisoned && context != android.opengl.EGL14.EGL_NO_CONTEXT &&
                context == android.opengl.EGL14.eglGetCurrentContext()) {
                "$COMPONENT incremental coverage invalid owner/poisoned/released"
            }
        }
        internal fun appendReference(maskId: Int) {
            requireOwner()
            check(originals.isEmpty() && maskId > 0) {
                "$COMPONENT reference identity must be consumed first and only once"
            }
            // Donor copyMask intentionally skips reference index zero.
            originals.add(maskId)
        }
        internal fun appendAlternate(maskId: Int) {
            requireOwner()
            check(originals.isNotEmpty() && originals.size < expectedFrames && maskId > 0) {
                "$COMPONENT extra/missing alternate donor R8 rejection mask"
            }
            val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
            try {
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D, texture, 0)
                GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) { "$COMPONENT coverage framebuffer lost" }
                GLES30.glViewport(0,0,(width+3)/4,(height+3)/4)
                GLES30.glBindVertexArray(vertexArray)
                GLES30.glUseProgram(program)
                GLES30.glDisable(GLES30.GL_DEPTH_TEST)
                GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
                GLES30.glColorMask(true,true,true,true)
                GLES30.glEnable(GLES30.GL_BLEND)
                GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
                GLES30.glBlendFunc(GLES30.GL_ONE,GLES30.GL_ONE)
                bind(program,"uRejection",0,maskId)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
                gpu.checkGl("C donor incremental R8 coverage frame=${originals.size}")
                originals.add(maskId)
            } catch (cause: Throwable) {
                poisoned = true // after a partially written FBO, never replay the mask
                throw cause
            } finally { restore.restore() }
        }
        internal fun verifyAndConsume(realMergedMasks: IntArray, result: Iris26972CDonorSabreGpuMerge.Result) {
            requireOwner()
            check(!normalized && originals.size == expectedFrames &&
                originals.toIntArray().contentEquals(realMergedMasks) &&
                result.width == width && result.height == height &&
                result.frozenFrameCount == expectedFrames &&
                texture != result.accumulatedColorAndRedWeight &&
                texture != result.accumulatedGreenBlueWeights) {
                "$COMPONENT incremental coverage count/provenance mismatch"
            }
            normalized = true // one-shot: failed dehomogenization must never retry
        }
        override fun close() {
            check(!released && context == android.opengl.EGL14.eglGetCurrentContext()) {
                "$COMPONENT incremental coverage cleanup must use original EGL context"
            }
            val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
            try {
                GLES30.glDeleteTextures(1,intArrayOf(texture),0)
                GLES30.glDeleteProgram(program)
                GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
                GLES30.glDeleteVertexArrays(1,intArrayOf(vertexArray),0)
                released = true
            } finally { restore.restore() }
        }
        companion object {
            internal fun begin(width: Int, height: Int, frames: Int): CoverageStream {
                require(width in 8..16384 && height in 8..16384 &&
                    width % 2 == 0 && height % 2 == 0 && frames in 2..Iris26972CContract.MAX_NORMAL_FRAMES) {
                    "$COMPONENT invalid frozen coverage size/count"
                }
                gpu.requireCurrentContext()
                val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
                var program=0;var tex=0;var fbo=0;var vao=0
                var success=false
                try {
                    program = gpu.compileProgram(gpu.VERTEX,Iris26972CDonorSabreMergeShaders.copyMask)
                    val textures=IntArray(1)
                    GLES30.glGenTextures(1,textures,0)
                    tex=textures[0]
                    check(tex>0) { "$COMPONENT coverage R8 allocation failure" }
                    makeTexture(tex,(width+3)/4,(height+3)/4,GLES30.GL_R8,
                        GLES30.GL_RED,GLES30.GL_UNSIGNED_BYTE,GLES30.GL_LINEAR)
                    val fbos=IntArray(1);GLES30.glGenFramebuffers(1,fbos,0);fbo=fbos[0]
                    check(fbo>0) { "$COMPONENT coverage framebuffer allocation failure" }
                    val vaos=IntArray(1);GLES30.glGenVertexArrays(1,vaos,0);vao=vaos[0]
                    check(vao>0) { "$COMPONENT coverage VAO allocation failure" }
                    GLES30.glBindVertexArray(vao)
                    GLES30.glDisable(GLES30.GL_DEPTH_TEST)
                    GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
                    GLES30.glColorMask(true,true,true,true)
                    attach(fbo,tex,(width+3)/4,(height+3)/4)
                    GLES30.glClearBufferfv(GLES30.GL_COLOR,0,floatArrayOf(0f,0f,0f,0f),0)
                    GLES30.glUseProgram(program)
                    GLES30.glUniform1f(uniform(program,"uAccumulatedWeightScale"),
                        accumulatedWeightScale(frames))
                    gpu.checkGl("C donor initial quarter R8 coverage")
                    success=true
                    return CoverageStream(width,height,frames,
                        android.opengl.EGL14.eglGetCurrentContext(),tex,fbo,vao,program)
                } finally {
                    if(!success) {
                        if(tex>0) GLES30.glDeleteTextures(1,intArrayOf(tex),0)
                        if(program>0) GLES30.glDeleteProgram(program)
                        if(fbo>0) GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
                        if(vao>0) GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
                    }
                    restore.restore()
                }
            }
        }
    }

    /** Full immutable provenance remains frozen in Merge.Result, but masks may be deleted. */
    internal fun normalizeAccumulatedStream(
        rawWidth: Int, rawHeight: Int, realMasks: IntArray,
        result: Iris26972CDonorSabreGpuMerge.Result,
        coverage: CoverageStream,
    ) {
        require(rawWidth in 8..16384 && rawHeight in 8..16384 &&
            rawWidth % 2 == 0 && rawHeight % 2 == 0 &&
            realMasks.size in 2..Iris26972CContract.MAX_NORMAL_FRAMES && realMasks.all { it > 0 }) {
            "$COMPONENT invalid frozen NORMAL burst mask provenance"
        }
        result.verifyNormalizationWeights(rawWidth,rawHeight,realMasks)
        coverage.verifyAndConsume(realMasks,result)
        performNormalize(rawWidth,rawHeight,realMasks,result,coverage.texture)
    }

    /** Legacy/batched normalization: requires every live alternate R8 mask until return. */
    internal fun normalizeStream(
        rawWidth: Int, rawHeight: Int, realMasks: IntArray,
        result: Iris26972CDonorSabreGpuMerge.Result,
    ) {
        require(rawWidth in 8..16384 && rawHeight in 8..16384 &&
            rawWidth % 2 == 0 && rawHeight % 2 == 0 &&
            realMasks.size in 2..Iris26972CContract.MAX_NORMAL_FRAMES && realMasks.all { it > 0 }) {
            "$COMPONENT invalid frozen NORMAL burst masks"
        }
        result.verifyNormalizationWeights(rawWidth, rawHeight, realMasks)
        performNormalize(rawWidth,rawHeight,realMasks,result)
    }

    private fun performNormalize(
        rawWidth: Int, rawHeight: Int, realMasks: IntArray,
        result: Iris26972CDonorSabreGpuMerge.Result,
        preaccumulatedCoverage: Int = 0,
    ) {
        require(result.accumulatedColorAndRedWeight != result.accumulatedGreenBlueWeights &&
            result.accumulatedColorAndRedWeight > 0 && result.accumulatedGreenBlueWeights > 0 &&
            realMasks.none { mask ->
                mask == result.accumulatedColorAndRedWeight ||
                    mask == result.accumulatedGreenBlueWeights
            }
        ) { "$COMPONENT input/output alias is forbidden" }
        gpu.requireCurrentContext()
        val coverageWidth = (rawWidth + 3) / 4
        val coverageHeight = (rawHeight + 3) / 4
        val scale = accumulatedWeightScale(realMasks.size)
        val restore = Iris26972CDonorSabreGpuMerge.GlState.capture()
        result.beginNormalization() // any subsequent failure is fatal; never reuse partial donor accumulation
        val isLiveMaskBatch = preaccumulatedCoverage == 0
        // Streaming: coverage already exists in one R8 quarter-grid target.
        // Batched: allocate the original R8 target now and consume live masks.
        val textures = IntArray(if (isLiveMaskBatch) 2 else 1)
        val coverageTexture = if (isLiveMaskBatch) -1 else preaccumulatedCoverage
        var coverageProgram = 0
        var alphaProgram = 0
        var normalizeProgram = 0
        var framebuffer = 0
        var vao = 0
        try {
            if (isLiveMaskBatch)
                coverageProgram = gpu.compileProgram(gpu.VERTEX, Iris26972CDonorSabreMergeShaders.copyMask)
            alphaProgram = gpu.compileProgram(gpu.VERTEX, Iris26972CDonorSabreMergeShaders.copyAlpha)
            normalizeProgram = gpu.compileProgram(gpu.VERTEX, Iris26972CDonorSabreMergeShaders.dehomogenize)
            GLES30.glGenTextures(textures.size, textures, 0)
            check(textures.all { it > 0 && it !in setOf(result.accumulatedColorAndRedWeight,
                result.accumulatedGreenBlueWeights) }) { "$COMPONENT scratch texture allocation failed" }
            // The actual donor uses R8 + GL_LINEAR at 1/4 resolution for accumulated coverage.
            if (isLiveMaskBatch)
                makeTexture(textures[0], coverageWidth, coverageHeight, GLES30.GL_R8,
                    GLES30.GL_RED, GLES30.GL_UNSIGNED_BYTE, GLES30.GL_LINEAR)
            val alphaTexture = textures.last()
            makeTexture(alphaTexture, rawWidth, rawHeight, GLES30.GL_R16F,
                GLES30.GL_RED, GLES30.GL_HALF_FLOAT, GLES30.GL_NEAREST)
            val fbos = IntArray(1)
            GLES30.glGenFramebuffers(1, fbos, 0)
            framebuffer = fbos[0]
            check(framebuffer != 0) { "$COMPONENT failed to allocate framebuffer" }
            val vaos = IntArray(1)
            GLES30.glGenVertexArrays(1, vaos, 0)
            vao = vaos[0]
            check(vao != 0) { "$COMPONENT failed to allocate VAO" }
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true, true, true, true)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
            if (isLiveMaskBatch) {
                attach(framebuffer, textures[0], coverageWidth, coverageHeight)
                GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f,0f,0f,0f), 0)
                GLES30.glUseProgram(coverageProgram)
                bind(coverageProgram, "uRejection", 0, 0)
                GLES30.glUniform1f(uniform(coverageProgram, "uAccumulatedWeightScale"), scale)
                GLES30.glEnable(GLES30.GL_BLEND)
                GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
                GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
                for (index in 1 until realMasks.size) {
                    bind(coverageProgram, "uRejection", 0, realMasks[index])
                    GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
                    gpu.checkGl("C donor R8 coverage accumulation frame=$index")
                }
                GLES30.glDisable(GLES30.GL_BLEND)
            }

            // Copy alpha before modifying the same RGB accumulator: direct simultaneous
            // sampling of and drawing to that accumulator would be undefined GL feedback.
            attach(framebuffer, alphaTexture, rawWidth, rawHeight)
            GLES30.glUseProgram(alphaProgram)
            bind(alphaProgram, "uSource", 0, result.accumulatedColorAndRedWeight)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
            gpu.checkGl("C donor red-weight snapshot")

            attach(framebuffer, result.accumulatedColorAndRedWeight, rawWidth, rawHeight)
            GLES30.glUseProgram(normalizeProgram)
            bind(normalizeProgram, "uSourceWeightR", 0, alphaTexture)
            bind(normalizeProgram, "uSourceWeightGb", 1, result.accumulatedGreenBlueWeights)
            bind(normalizeProgram, "uSourceAlpha", 2,
                if (isLiveMaskBatch) textures[0] else coverageTexture)
            GLES30.glUniform1f(uniform(normalizeProgram, "uAlphaScale"), scale / realMasks.size)
            GLES30.glUniform1f(uniform(normalizeProgram, "uAlphaBias"), 1f / realMasks.size)
            // Sabre original: RGB = (sum weighted RGB) / (sum independent color weights).
            // The shader emits 1/weight; blending multiplies destination RGB by source RGB,
            // with destination alpha overwritten by coverage-derived weight.
            GLES30.glEnable(GLES30.GL_BLEND)
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFuncSeparate(GLES30.GL_ZERO, GLES30.GL_SRC_COLOR,
                GLES30.GL_ONE, GLES30.GL_ZERO)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
            gpu.checkGl("C donor in-place RGB dehomogenize")
            GLES30.glDisable(GLES30.GL_BLEND)
            result.finishNormalization()
        } finally {
            if (coverageProgram != 0) GLES30.glDeleteProgram(coverageProgram)
            if (alphaProgram != 0) GLES30.glDeleteProgram(alphaProgram)
            if (normalizeProgram != 0) GLES30.glDeleteProgram(normalizeProgram)
            if (vao != 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
            if (framebuffer != 0) GLES30.glDeleteFramebuffers(1, intArrayOf(framebuffer), 0)
            val allocated = textures.filter { it > 0 }.toIntArray()
            if (allocated.isNotEmpty()) GLES30.glDeleteTextures(allocated.size, allocated, 0)
            restore.restore()
        }
    }

    private fun uniform(program: Int, name: String): Int =
        GLES30.glGetUniformLocation(program, name).also { check(it >= 0) {
            "$COMPONENT missing donor uniform $name" } }

    private fun bind(program: Int, name: String, unit: Int, texture: Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glUniform1i(uniform(program, name), unit)
    }

    private fun attach(framebuffer: Int, texture: Int, width: Int, height: Int) {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D, texture, 0)
        GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) == GLES30.GL_FRAMEBUFFER_COMPLETE) {
            "$COMPONENT R8/R16F FBO not supported"
        }
        GLES30.glViewport(0, 0, width, height)
        gpu.checkGl("C donor framebuffer setup")
    }

    private fun makeTexture(id: Int, width: Int, height: Int, internalFormat: Int,
                            format: Int, type: Int, filter: Int) {
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, internalFormat, width, height, 0,
            format, type, null)
        gpu.checkGl("C donor coverage/red-weight scratch allocation")
    }
}
