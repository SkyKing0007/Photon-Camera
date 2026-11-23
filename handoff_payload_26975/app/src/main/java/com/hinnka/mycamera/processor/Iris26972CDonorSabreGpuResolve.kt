package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.opengl.EGL14
import android.opengl.GLES30

/**
 * Experiment C-only ResolveSabre: pinned bjzhou PhotonCamera 1.29.0 4-pass integer-CFA
 * remosaic, Gr/Gb balance, edge-directed green, chroma interpolation, WB and lens shading.
 * Original four-pass GLSL remains donor-exact; C adds a fifth pre-clamp HDR replay.
 * Requires a *normalized* real C Sabre merge. Lens shading uses physical Camera2
 * values when present, otherwise the pinned donor's no-correction identity.
 * Does not demosaic or alter A/B, and cannot accept a synthetic substitute for upstream fusion.
 * Android driver, full GLSL compilation and image-quality verification are pending.
 */
internal object Iris26972CDonorSabreGpuResolve {
    private const val COMPONENT = "26972 C donor Sabre Resolve GPU"
    private const val MAX_SIDE = 16384
    private val gpu = Iris26972CDonorSabreGpuMerge

    internal data class Plan(
        val cfaPattern: Int,
        val frozenNormalFrameCount: Int,
        val referenceSnr: Float,
        val desiredExposureProduct: Double?,
        val actualExposureProduct: Double,
        val sensorWhiteLevelScaledToMgc14: Int,
        val finalCameraRgbGains: FloatArray,
        val lensShadingTexture: Int,
    )

    internal class Result private constructor(
        val texture: Int,
        /** Genuine pre-SDR-clamp donor output, needed to make a measured HDR reference. */
        val extendedCameraRgbTexture: Int,
        val width: Int, val height: Int,
        private val owner: android.opengl.EGLContext,
    ) : AutoCloseable {
        internal var measuredResidual: Iris26975CMeasuredSabreResidual? = null
            private set
        internal fun attachMeasuredResidual(residual: Iris26975CMeasuredSabreResidual) {
            requireOwner()
            check(measuredResidual == null && residual.width == (width+3)/4 &&
                residual.height == (height+3)/4) {
                "$COMPONENT source measured residual cannot be replaced"
            }
            measuredResidual = residual
        }

        private var closed = false
        internal fun requireOwner() {
            check(!closed && EGL14.eglGetCurrentContext() == owner &&
                owner != EGL14.EGL_NO_CONTEXT) { "$COMPONENT must retain its EGL owner" }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(2, intArrayOf(texture, extendedCameraRgbTexture), 0)
            closed = true
        }
        companion object {
            internal fun create(texture: Int, extended: Int, width: Int, height: Int) =
                Result(texture, extended, width, height, EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan: Plan, width: Int, height: Int, metadataOnly: Boolean = false) {
        require(width in 8..MAX_SIDE && height in 8..MAX_SIDE &&
            width % 2 == 0 && height % 2 == 0 &&
            width <= Int.MAX_VALUE - 2 * Iris26972CDonorSabreGreenShaders.PLANE_PADDING &&
            height <= Int.MAX_VALUE - 2 * Iris26972CDonorSabreGreenShaders.PLANE_PADDING) {
            "$COMPONENT invalid native RAW geometry"
        }
        require(plan.cfaPattern in 0..3 && plan.frozenNormalFrameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
            plan.referenceSnr.isFinite() && plan.referenceSnr >= 0f &&
            plan.actualExposureProduct.isFinite() && plan.actualExposureProduct > 0.0 &&
            plan.sensorWhiteLevelScaledToMgc14 in 1..32767 &&
            plan.finalCameraRgbGains.size == 3 &&
            plan.finalCameraRgbGains.all { it.isFinite() && it > 0f } &&
            (if (metadataOnly) plan.lensShadingTexture == 0 else plan.lensShadingTexture > 0) &&
            (plan.desiredExposureProduct == null ||
                (plan.desiredExposureProduct.isFinite() && plan.desiredExposureProduct > 0.0))) {
            "$COMPONENT invalid donor RAW calibration or actual lens-shading input"
        }
    }

    internal fun resolve(
        plan: Plan,
        merged: Iris26972CDonorSabreGpuMerge.Result,
    ): Result {
        validate(plan, merged.width, merged.height)
        check(merged.isNormalizedForResolve) { "$COMPONENT requires normalized C Sabre fusion" }
        check(plan.cfaPattern == merged.frozenCfaPattern &&
            plan.frozenNormalFrameCount == merged.frozenFrameCount) {
            "$COMPONENT resolution metadata diverges from frozen Sabre RAW fusion"
        }
        check(plan.lensShadingTexture != merged.accumulatedColorAndRedWeight &&
            plan.lensShadingTexture != merged.accumulatedGreenBlueWeights) {
            "$COMPONENT lens-shading input must not alias merged RAW output"
        }
        gpu.requireCurrentContext()
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= merged.width + 8 &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= merged.height + 8) {
            "$COMPONENT donor integer intermediate texture exceeds GL limit"
        }
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 4) {
            "$COMPONENT requires four sampler units for donor color output"
        }
        gpu.checkGl("before donor ResolveSabre")
        // Validated calibration and GL capability before poisoning the donor input.
        merged.beginResolve()
        val saved = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val previousPbo = gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        var framebuffer = 0
        var vao = 0
        val programs = IntArray(5)
        val textures = IntArray(5)
        var delivered = false
        try {
            // The donor fragments are GLSL ES 3.10 and require signed R16I render targets.
            // No approximate RGB demosaic, FP16 stand-in or A/B fallback is permitted.
            programs[0] = gpu.compileProgram(VERTEX_ES31,
                Iris26972CDonorSabreResolveShaders.convertToInt)
            programs[1] = gpu.compileProgram(VERTEX_ES31,
                Iris26972CDonorSabreGreenShaders.greenBalance)
            programs[2] = gpu.compileProgram(VERTEX_ES31,
                Iris26972CDonorSabreGreenShaders.greenAtColor)
            programs[3] = gpu.compileProgram(VERTEX_ES31,
                Iris26972CDonorSabreResolveShaders.resolveOutput)
            programs[4] = gpu.compileProgram(VERTEX_ES31,
                Iris26972CDonorSabreResolveShaders.resolveExtendedLinearOutput)

            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
            GLES30.glGenTextures(textures.size, textures, 0)
            check(textures.all { it > 0 && it !in setOf(
                merged.accumulatedColorAndRedWeight, merged.accumulatedGreenBlueWeights,
                plan.lensShadingTexture) } && textures.toSet().size == textures.size) {
                "$COMPONENT invalid scratch texture ownership"
            }
            val width = merged.width
            val height = merged.height
            val padding = Iris26972CDonorSabreGreenShaders.PLANE_PADDING
            val planeWidth = width + padding * 2
            val planeHeight = height + padding * 2
            for (index in 0..2) {
                allocTexture(textures[index], planeWidth, planeHeight,
                    GLES30.GL_R16I, GLES30.GL_RED_INTEGER, GLES30.GL_SHORT)
            }
            allocTexture(textures[3], width, height,
                GLES30.GL_RGBA16UI, GLES30.GL_RGBA_INTEGER, GLES30.GL_UNSIGNED_SHORT)
            allocTexture(textures[4], width, height,
                GLES30.GL_RGBA16F, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT)

            val fbo = IntArray(1)
            GLES30.glGenFramebuffers(1, fbo, 0)
            framebuffer = fbo[0]
            check(framebuffer > 0) { "$COMPONENT failed to allocate FBO" }
            val vertexArray = IntArray(1)
            GLES30.glGenVertexArrays(1, vertexArray, 0)
            vao = vertexArray[0]
            check(vao > 0) { "$COMPONENT failed to allocate full-screen VAO" }
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true, true, true, true)

            val (redX, redY) = when (plan.cfaPattern) {
                0 -> 0 to 0; 1 -> 1 to 0; 2 -> 0 to 1; else -> 1 to 1
            }
            val parameters = com.hinnka.mycamera.processor.experimentc.original129.processor.MgcSabreResolveTuning.build(
                plan.referenceSnr, plan.desiredExposureProduct, plan.actualExposureProduct)
            val demosaicScale = plan.sensorWhiteLevelScaledToMgc14 * parameters.demosaicSharpness
            check(demosaicScale.isFinite() && demosaicScale > 0f) {
                "$COMPONENT cannot generate donor CFA quantization"
            }
            pass(programs[0], textures[0], planeWidth, planeHeight, framebuffer,
                listOf("uAccumulated" to merged.accumulatedColorAndRedWeight)) {
                uniform2i(programs[0], "uImageSize", width, height)
                uniform2i(programs[0], "uRedSite", redX, redY)
                uniform1f(programs[0], "uQuantizationScale", demosaicScale)
            }
            // 0x34A67F8: fcvtzs(clamp(retention * 65536, 0, 65535)).
            val retentionFixed16 = (parameters.greenImbalanceRetention * 65536f)
                .coerceIn(0f,65535f).toInt()
            pass(programs[1], textures[1], planeWidth, planeHeight, framebuffer,
                listOf("uConverted" to textures[0])) {
                uniform2i(programs[1], "uPlaneSize", planeWidth, planeHeight)
                uniform1i(programs[1], "uGreenImbalanceRetention", retentionFixed16)
            }
            pass(programs[2], textures[2], planeWidth, planeHeight, framebuffer,
                listOf("uBalanced" to textures[1])) {
                uniform2i(programs[2], "uPlaneSize", planeWidth, planeHeight)
            }
            pass(programs[3], textures[3], width, height, framebuffer, listOf(
                "uAccumulated" to merged.accumulatedColorAndRedWeight,
                "uBalanced" to textures[1],
                "uGreen" to textures[2],
                "uLensShading" to plan.lensShadingTexture)) {
                uniform2i(programs[3], "uImageSize", width, height)
                uniform2i(programs[3], "uPlaneSize", planeWidth, planeHeight)
                uniform2i(programs[3], "uRedSite", redX, redY)
                // Donor: demosaicBlendRange=4-3=1, scale=-frameCount, bias=4.
                uniform1f(programs[3], "uBlendBias", 4f)
                uniform1f(programs[3], "uBlendScale", -plan.frozenNormalFrameCount.toFloat())
                uniform1f(programs[3], "uInverseQuantizationScale", 1f/demosaicScale)
                val g=plan.finalCameraRgbGains
                uniform3f(programs[3], "uFinalGains", g[0],g[1],g[2])
            }
            // Compute the same donor CFA result a second time before its final U16/SDR
            // clamp. HDR never comes from previously clipped U16 or a synthetic gainmap.
            pass(programs[4], textures[4], width, height, framebuffer, listOf(
                "uAccumulated" to merged.accumulatedColorAndRedWeight,
                "uBalanced" to textures[1],
                "uGreen" to textures[2],
                "uLensShading" to plan.lensShadingTexture)) {
                uniform2i(programs[4], "uImageSize", width, height)
                uniform2i(programs[4], "uPlaneSize", planeWidth, planeHeight)
                uniform2i(programs[4], "uRedSite", redX, redY)
                // Donor: demosaicBlendRange=4-3=1, scale=-frameCount, bias=4.
                uniform1f(programs[4], "uBlendBias", 4f)
                uniform1f(programs[4], "uBlendScale", -plan.frozenNormalFrameCount.toFloat())
                uniform1f(programs[4], "uInverseQuantizationScale", 1f/demosaicScale)
                val g=plan.finalCameraRgbGains
                uniform3f(programs[4], "uFinalGains", g[0],g[1],g[2])
            }
            delivered = true
            return Result.create(textures[3], textures[4], width, height)
        } finally {
            programs.filter { it > 0 }.forEach(GLES30::glDeleteProgram)
            if (vao > 0) GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if (framebuffer > 0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            // Retain ONLY genuine SDR-U16 + pre-clamp linear HDR textures on success.
            // All three integer CFA planes are deleted, even after a shader failure.
            textures.indices.filter { !delivered || it < 3 }.forEach { i ->
                if (textures[i] > 0) GLES30.glDeleteTextures(1,intArrayOf(textures[i]),0)
            }
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, previousPbo)
            saved.restore()
        }
    }

    // GLSL ES 3.10 shader fragments must be linked to a matching ES 3.10 vertex shader.
    private const val VERTEX_ES31 = """
        #version 310 es
        precision highp float;
        void main() {
            vec2 position[3] = vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));
            gl_Position=vec4(position[gl_VertexID],0.0,1.0);
        }
    """

    private fun allocTexture(id: Int, width: Int, height: Int, format: Int, pixelFormat: Int, type: Int) {
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,format,width,height,0,pixelFormat,type,null)
        gpu.checkGl("donor int16 or RGB16UI texture allocation")
    }

    private fun pass(
        program: Int, target: Int, width: Int, height: Int, framebuffer: Int,
        samplers: List<Pair<String, Int>>, uniforms: () -> Unit,
    ) {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D,target,0)
        GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE) {
            "$COMPONENT integer render-target FBO unavailable"
        }
        GLES30.glUseProgram(program)
        samplers.forEachIndexed { i, (name, texture) ->
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0+i)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,texture)
            uniform1i(program,name,i)
        }
        uniforms()
        GLES30.glViewport(0,0,width,height)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
        gpu.checkGl("donor ResolveSabre pass draw")
    }

    private fun location(program:Int,name:String):Int =
        GLES30.glGetUniformLocation(program,name).also { check(it>=0) { "$COMPONENT donor uniform missing $name" } }
    private fun uniform1i(program:Int,name:String,v:Int) = GLES30.glUniform1i(location(program,name),v)
    private fun uniform1f(program:Int,name:String,v:Float) = GLES30.glUniform1f(location(program,name),v)
    private fun uniform2i(program:Int,name:String,x:Int,y:Int) = GLES30.glUniform2i(location(program,name),x,y)
    private fun uniform3f(program:Int,name:String,x:Float,y:Float,z:Float) = GLES30.glUniform3f(location(program,name),x,y,z)
}
