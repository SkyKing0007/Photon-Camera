package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.opengl.EGL14
import android.opengl.GLES30

/**
 * Experiment C only: execution of the pinned bjzhou 1.29.0 Sabre `merge` shader.
 *
 * This implements the donor's two-render-target additive RAW Sabre accumulation;
 * it is NOT a replacement for the donor's covariance/guide, optical flow,
 * rejection-mask, dehomogenization, ResolveSabre or RAW development stages.
 * All upstream textures must originate in C's own verified, still-pending stages.
 * No synthetic alignment, fixed rejection or A/B input is substituted.
 *
 * Caller owns a current GLES 3.0 context and must retain it for Result.close().
 * No GL objects are persisted between captures. The result owns only two textures.
 */
internal object Iris26972CDonorSabreGpuMerge {
    private const val COMPONENT = "26972 C donor Sabre GPU merge"
    private const val MAX_FRAMES = Iris26972CContract.MAX_NORMAL_FRAMES
    private const val BORDER_PIXELS = 1.5f // Exact donor 1.29.0 SABRE_SAMPLE_BORDER_PIXELS (line 8344).

    internal data class Frame(
        val extractedBayerTexture: Int,
        val flowTexture: Int,
        val covarianceTexture: Int,
        val rejectionTexture: Int,
        val flowScaleOffset: FloatArray,
        val gains: FloatArray,
        val blackLevelsTimesGains: FloatArray,
        val isReference: Boolean,
    )

    internal data class Plan(
        val width: Int,
        val height: Int,
        val cfaPattern: Int,
        val frames: List<Frame>,
    )

    /**
     * Explicit ownership; output 0 is RGBA16F (RGB unnormalized, R weight in alpha),
     * output 1 is RG16F (separate G/B accumulated weights). Output is NOT RGB yet.
     */
    internal class Result private constructor(
        val accumulatedColorAndRedWeight: Int,
        val accumulatedGreenBlueWeights: Int,
        val width: Int,
        val height: Int,
        internal val frozenCfaPattern: Int,
        internal val frozenFrameCount: Int,
        private val owningContext: android.opengl.EGLContext,
        private val frozenRejectionTextureIds: IntArray,
    ) : AutoCloseable {
        private var released = false
        private var normalizationStarted = false
        private var normalizationFinished = false
        private var resolveStarted = false
        internal fun validateNormalizeContext() {
            check(!released && !normalizationStarted) { "$COMPONENT cannot normalize released/consumed accumulation" }
            requireCurrentContext()
            check(EGL14.eglGetCurrentContext() == owningContext) {
                "$COMPONENT normalization requires original EGL context"
            }
        }
        internal fun verifyNormalizationPlan(plan: Plan) {
            validateNormalizeContext()
            check(plan.width == width && plan.height == height &&
                plan.frames.size == frozenRejectionTextureIds.size &&
                plan.frames.map { it.rejectionTexture }.toIntArray()
                    .contentEquals(frozenRejectionTextureIds)) {
                "$COMPONENT normalization metadata no longer matches merged RAW burst"
            }
        }
        /** Streaming burst owner freezes real donor mask IDs, no stale source textures required. */
        internal fun verifyNormalizationWeights(w: Int, h: Int, weights: IntArray) {
            validateNormalizeContext()
            check(w == width && h == height &&
                weights.size == frozenFrameCount &&
                weights.contentEquals(frozenRejectionTextureIds)) {
                "$COMPONENT streamed normalization mask provenance mismatch"
            }
        }
        internal fun beginNormalization() {
            validateNormalizeContext()
            normalizationStarted = true // errors must fail closed; never retry after partial FBO mutation
        }
        internal fun finishNormalization() {
            check(normalizationStarted && !released)
            normalizationFinished = true
        }
        internal val isNormalizedForResolve: Boolean
            get() = normalizationFinished && !released && !resolveStarted
        internal fun beginResolve() {
            check(isNormalizedForResolve) { "$COMPONENT must be normalized exactly once before resolve" }
            requireCurrentContext()
            check(EGL14.eglGetCurrentContext() == owningContext) { "$COMPONENT resolve requires original EGL context" }
            // Fail closed even after a partial shader draw: no repeated ResolveSabre.
            resolveStarted = true
        }
        override fun close() {
            check(!released) { "$COMPONENT texture ownership already released" }
            requireCurrentContext()
            check(EGL14.eglGetCurrentContext() == owningContext) {
                "$COMPONENT texture release requires its original EGL context"
            }
            GLES30.glDeleteTextures(2, intArrayOf(accumulatedColorAndRedWeight, accumulatedGreenBlueWeights), 0)
            released = true
        }
        companion object {
            fun create(r: Int, gb: Int, plan: Plan) =
                Result(r, gb, plan.width, plan.height, plan.cfaPattern, plan.frames.size, EGL14.eglGetCurrentContext(),
                    plan.frames.map { it.rejectionTexture }.toIntArray())
            internal fun fromStream(r: Int, gb: Int, width: Int, height: Int,
                                    cfa: Int, masks: IntArray) =
                Result(r, gb, width, height, cfa, masks.size,
                    EGL14.eglGetCurrentContext(), masks.copyOf())
        }
    }

    /** Pure metadata gate: fail before touching GL when C producer stages are incomplete. */
    internal fun validate(plan: Plan) {
        require(plan.width in 8..16384 && plan.height in 8..16384 &&
            (plan.width and 1) == 0 && (plan.height and 1) == 0) {
            "$COMPONENT requires even native RAW geometry"
        }
        require(plan.cfaPattern in 0..3) { "$COMPONENT invalid Bayer CFA" }
        require(plan.frames.size in 2..MAX_FRAMES) { "$COMPONENT invalid frozen burst count" }
        require(plan.frames.first().isReference && plan.frames.drop(1).none { it.isReference }) {
            "$COMPONENT requires exactly one first reference"
        }
        for ((index, f) in plan.frames.withIndex()) {
            require(f.extractedBayerTexture > 0 && f.flowTexture > 0 &&
                f.covarianceTexture > 0 && f.rejectionTexture > 0) {
                "$COMPONENT missing frame $index guide/flow/rejection/covariance texture"
            }
            // The two calibration arrays are four CFA sites, not three RGB channels.
            require(f.gains.size == 4 && f.blackLevelsTimesGains.size == 4 &&
                f.gains.all { it.isFinite() && it > 0f } &&
                f.blackLevelsTimesGains.all { it.isFinite() } &&
                f.flowScaleOffset.size == 4 && f.flowScaleOffset.all { it.isFinite() } &&
                f.flowScaleOffset[0] > 0f && f.flowScaleOffset[1] > 0f) {
                "$COMPONENT invalid frame $index sensor calibration/flow transform"
            }
        }
    }

    /**
     * Executes the upstream 1.29.0 `merge` fragment once per admitted NORMAL RAW.
     * The first frame ignores the rejection weight, exactly as donor Sabre does.
     * All other frames use their own rejection weight; no alternative fusion.
     */
    internal fun accumulate(plan: Plan): Result {
        validate(plan)
        requireCurrentContext()
        val maxSize = glInt(GLES30.GL_MAX_TEXTURE_SIZE)
        require(plan.width <= maxSize && plan.height <= maxSize) {
            "$COMPONENT exceeds GL texture limit"
        }
        require(glInt(GLES30.GL_MAX_DRAW_BUFFERS) >= 2 &&
            glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 2 &&
            glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 4) {
            "$COMPONENT requires two MRT targets and four texture samplers"
        }
        checkGl("before merge")
        val state = GlState.capture()
        var program = 0
        var framebuffer = 0
        var vertexArray = 0
        val outputs = IntArray(2)
        var success = false
        try {
            program = compileProgram(VERTEX, Iris26972CDonorSabreMergeShaders.merge)
            GLES30.glGenTextures(2, outputs, 0)
            require(outputs.all { it != 0 }) { "$COMPONENT failed to allocate accumulator textures" }
            makeTexture(outputs[0], plan.width, plan.height, GLES30.GL_RGBA16F, GLES30.GL_RGBA)
            makeTexture(outputs[1], plan.width, plan.height, GLES30.GL_RG16F, GLES30.GL_RG)
            val fbo = IntArray(1)
            GLES30.glGenFramebuffers(1, fbo, 0)
            framebuffer = fbo[0]
            check(framebuffer != 0) { "$COMPONENT failed to allocate framebuffer" }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, outputs[0], 0)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT1,
                GLES30.GL_TEXTURE_2D, outputs[1], 0)
            GLES30.glDrawBuffers(2, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0, GLES30.GL_COLOR_ATTACHMENT1), 0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) == GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$COMPONENT floating-point MRT framebuffer unsupported"
            }
            val vao = IntArray(1)
            GLES30.glGenVertexArrays(1, vao, 0)
            vertexArray = vao[0]
            check(vertexArray != 0) { "$COMPONENT failed to allocate VAO" }
            GLES30.glBindVertexArray(vertexArray)
            GLES30.glViewport(0, 0, plan.width, plan.height)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true, true, true, true)
            GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f,0f,0f,0f), 0)
            GLES30.glClearBufferfv(GLES30.GL_COLOR, 1, floatArrayOf(0f,0f,0f,0f), 0)
            GLES30.glUseProgram(program)
            val uniforms = Uniforms(program)
            GLES30.glEnable(GLES30.GL_BLEND)
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            for (frame in plan.frames) {
                uniforms.draw(frame, plan.width, plan.height, plan.cfaPattern)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
                checkGl("Sabre MRT draw")
            }
            checkGl("merged C RAW burst")
            success = true
            return Result.create(outputs[0], outputs[1], plan)
        } finally {
            if (program != 0) GLES30.glDeleteProgram(program)
            if (vertexArray != 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vertexArray), 0)
            if (framebuffer != 0) GLES30.glDeleteFramebuffers(1, intArrayOf(framebuffer), 0)
            if (!success && outputs.any { it != 0 }) GLES30.glDeleteTextures(2, outputs, 0)
            state.restore()
        }
    }

    private class Uniforms(private val program: Int) {
        private fun loc(name: String): Int = GLES30.glGetUniformLocation(program, name).also {
            check(it >= 0) { "$COMPONENT donor shader missing uniform $name" }
        }
        private val texture = arrayOf("uExtractedBayer", "uFlow", "uCovariance", "uRejection").map(::loc)
        private val extractedSize = loc("uExtractedSize")
        private val outputSize = loc("uOutputSize")
        private val flowScaleOffset = loc("uFlowScaleOffset")
        private val border = loc("uFrameBorderPadded")
        private val cfa = loc("uCfaPattern")
        private val frameWeight = loc("uUseFrameWeight")
        private val gains = loc("uGains")
        private val black = loc("uBlackLevelsTimesGains")
        private val covRg = loc("uCovRangeRg")
        private val covB = loc("uCovRangeB")
        fun draw(f: Frame, width: Int, height: Int, cfaPattern: Int) {
            val inputs = intArrayOf(f.extractedBayerTexture, f.flowTexture,
                f.covarianceTexture, f.rejectionTexture)
            inputs.forEachIndexed { index, id ->
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + index)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, id)
                GLES30.glUniform1i(texture[index], index)
            }
            GLES30.glUniform2i(extractedSize, width / 2, height / 2)
            GLES30.glUniform2i(outputSize, width, height)
            GLES30.glUniform4fv(flowScaleOffset, 1, f.flowScaleOffset, 0)
            GLES30.glUniform4f(border, BORDER_PIXELS / width, BORDER_PIXELS / height,
                1f - BORDER_PIXELS / width, 1f - BORDER_PIXELS / height)
            GLES30.glUniform1i(cfa, cfaPattern)
            GLES30.glUniform1i(frameWeight, if (f.isReference) 0 else 1)
            GLES30.glUniform4fv(gains, 1, f.gains, 0)
            GLES30.glUniform4fv(black, 1, f.blackLevelsTimesGains, 0)
            GLES30.glUniform4f(covRg, .3671880066f, 24.8149185f - .3671880066f,
                .3671880066f, 26.0516777f - .3671880066f)
            GLES30.glUniform2f(covB, -6.9755706787f, 7.0265216827f + 6.9755706787f)
        }
    }

    private fun makeTexture(id: Int, width: Int, height: Int, format: Int, channels: Int) {
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, format, width, height, 0,
            channels, GLES30.GL_HALF_FLOAT, null)
        checkGl("allocate native Sabre accumulator")
    }

    internal fun compileProgram(vertex: String, fragment: String): Int {
        fun shader(type: Int, source: String): Int {
            val id = GLES30.glCreateShader(type)
            check(id != 0) { "$COMPONENT shader allocation failed" }
            GLES30.glShaderSource(id, source)
            GLES30.glCompileShader(id)
            val status = IntArray(1)
            GLES30.glGetShaderiv(id, GLES30.GL_COMPILE_STATUS, status, 0)
            if (status[0] != GLES30.GL_TRUE) {
                val log = GLES30.glGetShaderInfoLog(id)
                GLES30.glDeleteShader(id)
                error("$COMPONENT GLSL compile error: $log")
            }
            return id
        }
        val vert = shader(GLES30.GL_VERTEX_SHADER, vertex)
        var frag = 0
        var program = 0
        try {
            frag = shader(GLES30.GL_FRAGMENT_SHADER, fragment)
            program = GLES30.glCreateProgram()
            check(program != 0) { "$COMPONENT program allocation failed" }
            GLES30.glAttachShader(program, vert)
            GLES30.glAttachShader(program, frag)
            GLES30.glLinkProgram(program)
            val status = IntArray(1)
            GLES30.glGetProgramiv(program, GLES30.GL_LINK_STATUS, status, 0)
            check(status[0] == GLES30.GL_TRUE) {
                "$COMPONENT shader link error: ${GLES30.glGetProgramInfoLog(program)}"
            }
            return program
        } catch (t: Throwable) {
            if (program != 0) GLES30.glDeleteProgram(program)
            throw t
        } finally {
            GLES30.glDeleteShader(vert)
            if (frag != 0) GLES30.glDeleteShader(frag)
        }
    }

    internal class GlState private constructor(
        private val program: Int, private val drawFramebuffer: Int, private val readFramebuffer: Int,
        private val viewport: IntArray, private val vao: Int,
        private val activeTexture: Int, private val activeTextureBinding: Int,
        private val bindings: IntArray,
        private val blendEnabled: Boolean, private val depthEnabled: Boolean,
        private val scissorEnabled: Boolean, private val colorMask: BooleanArray,
        private val blendSrcRgb: Int, private val blendDstRgb: Int,
        private val blendSrcAlpha: Int, private val blendDstAlpha: Int,
        private val blendEqRgb: Int, private val blendEqAlpha: Int,
    ) {
        fun restore() {
            // Always restore all caller-owned context state, including prior sampler bindings.
            GLES30.glBindFramebuffer(GLES30.GL_DRAW_FRAMEBUFFER, drawFramebuffer)
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER, readFramebuffer)
            GLES30.glUseProgram(program)
            GLES30.glBindVertexArray(vao)
            GLES30.glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
            for (index in bindings.indices) {
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0+index)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,bindings[index])
            }
            GLES30.glActiveTexture(activeTexture)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, activeTextureBinding)
            GLES30.glBlendEquationSeparate(blendEqRgb, blendEqAlpha)
            GLES30.glBlendFuncSeparate(blendSrcRgb,blendDstRgb,blendSrcAlpha,blendDstAlpha)
            GLES30.glColorMask(colorMask[0], colorMask[1], colorMask[2], colorMask[3])
            if (blendEnabled) GLES30.glEnable(GLES30.GL_BLEND) else GLES30.glDisable(GLES30.GL_BLEND)
            if (depthEnabled) GLES30.glEnable(GLES30.GL_DEPTH_TEST) else GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            if (scissorEnabled) GLES30.glEnable(GLES30.GL_SCISSOR_TEST) else GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
        }
        companion object {
            fun capture(): GlState {
                val active = glInt(GLES30.GL_ACTIVE_TEXTURE)
                val activeBinding = glInt(GLES30.GL_TEXTURE_BINDING_2D)
                // C rejection uses five samplers; save the fifth binding as well. A 4-unit
                // context is still legal for the earlier Sabre accumulation stage.
                val bindings = IntArray(minOf(5, glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS))) { index ->
                    GLES30.glActiveTexture(GLES30.GL_TEXTURE0+index)
                    glInt(GLES30.GL_TEXTURE_BINDING_2D)
                }
                GLES30.glActiveTexture(active)
                val viewport = IntArray(4)
                GLES30.glGetIntegerv(GLES30.GL_VIEWPORT, viewport, 0)
                val mask = BooleanArray(4)
                GLES30.glGetBooleanv(GLES30.GL_COLOR_WRITEMASK, mask, 0)
                return GlState(glInt(GLES30.GL_CURRENT_PROGRAM),
                    glInt(GLES30.GL_DRAW_FRAMEBUFFER_BINDING), glInt(GLES30.GL_READ_FRAMEBUFFER_BINDING),
                    viewport,glInt(GLES30.GL_VERTEX_ARRAY_BINDING),active,activeBinding,bindings,
                    GLES30.glIsEnabled(GLES30.GL_BLEND),GLES30.glIsEnabled(GLES30.GL_DEPTH_TEST),
                    GLES30.glIsEnabled(GLES30.GL_SCISSOR_TEST),mask,
                    glInt(GLES30.GL_BLEND_SRC_RGB),glInt(GLES30.GL_BLEND_DST_RGB),
                    glInt(GLES30.GL_BLEND_SRC_ALPHA),glInt(GLES30.GL_BLEND_DST_ALPHA),
                    glInt(GLES30.GL_BLEND_EQUATION_RGB),glInt(GLES30.GL_BLEND_EQUATION_ALPHA))
            }
        }
    }

    internal fun glInt(param: Int): Int = IntArray(1).also { GLES30.glGetIntegerv(param, it, 0) }[0]
    internal fun requireCurrentContext() {
        check(EGL14.eglGetCurrentContext() != EGL14.EGL_NO_CONTEXT) {
            "$COMPONENT requires a caller-owned current GLES context"
        }
    }
    internal fun checkGl(stage: String) {
        val error = GLES30.glGetError()
        check(error == GLES30.GL_NO_ERROR) { "$COMPONENT GL error 0x${error.toString(16)} at $stage" }
    }

    internal const val VERTEX = """
        #version 300 es
        precision highp float;
        void main() {
            vec2 position[3] = vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));
            gl_Position=vec4(position[gl_VertexID],0.0,1.0);
        }
    """
    /**
     * Authentic donor additive accumulation with one transient NORMAL alternate at a time.
     * Unlike accumulate(Plan), it never needs all extracted RAW/flow/covariance textures
     * alive simultaneously. It freezes authentic mask IDs in merge order; the C burst owner
     * consumes each mask into its quarter-grid coverage stream BEFORE releasing that mask.
     * Batched normalization still requires live masks. An aborted draw poisons this stream.
     *
     * This stage is C-only and not reachable from the disabled production capture gate.
     * Its GL execution is not Android-build or on-device verified.
     */
    internal class Stream private constructor(
        val width: Int, val height: Int, val cfaPattern: Int, val expectedFrames: Int,
        private val context: android.opengl.EGLContext,
        private val color: Int, private val greenBlue: Int,
        private val program: Int, private val framebuffer: Int, private val vertexArray: Int,
    ) : AutoCloseable {
        private val realRejectionTextures = ArrayList<Int>(expectedFrames)
        private var poisoned = false
        private var released = false
        private var transferred = false
        val mergedCount: Int get() = realRejectionTextures.size
        private fun requireOwner() {
            check(!released && !poisoned && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT streaming accumulation invalid owner/released/poisoned"
            }
        }
        internal fun append(frame: Frame) {
            requireOwner()
            check(realRejectionTextures.size < expectedFrames) {
                "$COMPONENT too many frames for frozen NORMAL burst"
            }
            check(frame.isReference == realRejectionTextures.isEmpty()) {
                "$COMPONENT reference must be first and unique"
            }
            validateFrame(frame, realRejectionTextures.size)
            // External stream producer owns each input; it must not alias either accumulator.
            check(listOf(frame.extractedBayerTexture, frame.flowTexture,
                frame.covarianceTexture, frame.rejectionTexture).none {
                it == color || it == greenBlue
            }) { "$COMPONENT RAW stream sampler/render target alias" }
            val restore = GlState.capture()
            try {
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D, color, 0)
                GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT1,
                    GLES30.GL_TEXTURE_2D, greenBlue, 0)
                GLES30.glDrawBuffers(2, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0, GLES30.GL_COLOR_ATTACHMENT1), 0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "$COMPONENT stream MRT incomplete"
                }
                GLES30.glBindVertexArray(vertexArray)
                GLES30.glViewport(0, 0, width, height)
                GLES30.glDisable(GLES30.GL_DEPTH_TEST)
                GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
                GLES30.glColorMask(true, true, true, true)
                if (realRejectionTextures.isEmpty()) {
                    GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f,0f,0f,0f), 0)
                    GLES30.glClearBufferfv(GLES30.GL_COLOR, 1, floatArrayOf(0f,0f,0f,0f), 0)
                }
                GLES30.glUseProgram(program)
                GLES30.glEnable(GLES30.GL_BLEND)
                GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
                GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
                Uniforms(program).draw(frame, width, height, cfaPattern)
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
                checkGl("C donor streaming Sabre frame ${realRejectionTextures.size}")
                realRejectionTextures.add(frame.rejectionTexture)
            } catch (failure: Throwable) {
                // Partial accumulation cannot safely be replayed or restarted.
                poisoned = true
                throw failure
            } finally {
                restore.restore()
            }
        }
        /** Transfer real accumulation ownership only once all planned NORMALs merged. */
        internal fun finish(): Result {
            requireOwner()
            check(realRejectionTextures.size == expectedFrames) {
                "$COMPONENT incomplete stream; cannot silently drop a NORMAL RAW frame"
            }
            transferred = true
            return Result.fromStream(color, greenBlue, width, height, cfaPattern,
                realRejectionTextures.toIntArray())
        }
        internal fun actualMaskIds(): IntArray {
            requireOwner()
            check(realRejectionTextures.size == expectedFrames)
            return realRejectionTextures.toIntArray()
        }
        override fun close() {
            check(!released && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT stream cleanup requires original context and one-shot owner"
            }
            val saved = GlState.capture()
            try {
                GLES30.glDeleteProgram(program)
                GLES30.glDeleteFramebuffers(1, intArrayOf(framebuffer), 0)
                GLES30.glDeleteVertexArrays(1, intArrayOf(vertexArray), 0)
                if (!transferred) GLES30.glDeleteTextures(2, intArrayOf(color, greenBlue), 0)
                released = true
            } finally { saved.restore() }
        }
        internal companion object {
            fun create(width: Int, height: Int, cfa: Int, count: Int,
                color: Int, gb: Int, program: Int, fbo: Int, vao: Int) = Stream(
                width, height, cfa, count, EGL14.eglGetCurrentContext(),
                color, gb, program, fbo, vao)
        }
    }

    private fun validateFrame(f: Frame, index: Int) {
        require(f.extractedBayerTexture > 0 && f.flowTexture > 0 &&
            f.covarianceTexture > 0 && f.rejectionTexture > 0) {
            "$COMPONENT absent real donor RAW component frame=$index"
        }
        require(f.gains.size == 4 && f.blackLevelsTimesGains.size == 4 &&
            f.gains.all { it.isFinite() && it > 0f } &&
            f.blackLevelsTimesGains.all { it.isFinite() } &&
            f.flowScaleOffset.size == 4 && f.flowScaleOffset.all { it.isFinite() } &&
            f.flowScaleOffset[0] > 0f && f.flowScaleOffset[1] > 0f) {
            "$COMPONENT invalid donor calibration/flow frame=$index"
        }
    }

    /** Fail-closed per-frame Sabre merge, never retain all burst RAW textures at once. */
    internal fun beginStream(width: Int, height: Int, cfa: Int, frameCount: Int): Stream {
        require(width in 8..16384 && height in 8..16384 && width % 2 == 0 &&
            height % 2 == 0 && cfa in 0..3 && frameCount in 2..MAX_FRAMES) {
            "$COMPONENT invalid streaming NORMAL RAW burst contract"
        }
        requireCurrentContext()
        require(width <= glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            height <= glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            glInt(GLES30.GL_MAX_DRAW_BUFFERS) >= 2 &&
            glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 2 &&
            glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 4) {
            "$COMPONENT insufficient donor Sabre merge capability"
        }
        checkGl("before donor streaming merge")
        val saved = GlState.capture()
        var program = 0; var fbo = 0; var vao = 0
        val textures = IntArray(2)
        var success = false
        try {
            program = compileProgram(VERTEX, Iris26972CDonorSabreMergeShaders.merge)
            GLES30.glGenTextures(2, textures, 0)
            check(textures.all { it > 0 } && textures[0] != textures[1]) {
                "$COMPONENT invalid streaming accumulation texture allocation"
            }
            makeTexture(textures[0], width, height, GLES30.GL_RGBA16F, GLES30.GL_RGBA)
            makeTexture(textures[1], width, height, GLES30.GL_RG16F, GLES30.GL_RG)
            val ids = IntArray(1)
            GLES30.glGenFramebuffers(1, ids, 0); fbo = ids[0]
            GLES30.glGenVertexArrays(1, ids, 0); vao = ids[0]
            check(fbo > 0 && vao > 0) { "$COMPONENT no streaming FBO/VAO" }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbo)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, textures[0], 0)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT1,
                GLES30.GL_TEXTURE_2D, textures[1], 0)
            GLES30.glDrawBuffers(2, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0, GLES30.GL_COLOR_ATTACHMENT1), 0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                GLES30.GL_FRAMEBUFFER_COMPLETE) { "$COMPONENT streaming MRT unsupported" }
            success = true
            return Stream.create(width, height, cfa, frameCount,
                textures[0], textures[1], program, fbo, vao)
        } finally {
            if (!success) {
                if (program > 0) GLES30.glDeleteProgram(program)
                if (fbo > 0) GLES30.glDeleteFramebuffers(1, intArrayOf(fbo), 0)
                if (vao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
                if (textures.any { it > 0 }) GLES30.glDeleteTextures(2, textures, 0)
            }
            saved.restore()
        }
    }

}
