package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import android.opengl.GLES31

/**
 * Experiment C isolated counterpart of the pinned V25 GlesMgcRawSpatialStacker
 * hot-pixel boundary. The reference RAW creates one persistent, sensor-coordinate
 * mask. Every alternate is suppressed using that same mask BEFORE extractBayer,
 * RAW16 alignment, unblocker, rejection and Sabre accumulation.
 *
 * Actual donor GLSL lives in Iris26975COriginalRawHotPixelShaders, recovered from
 * pinned bjzhou/PhotonCamera 1.29.0's successfully built classes.dex.
 * This adapter owns only private GLES objects. No A/B/native/vendor changes.
 */
internal class Iris26975COriginalSabreHotPixel private constructor(
    private val width: Int,
    private val height: Int,
    private val expectedFrames: Int,
    private val cfaPattern: Int,
    private val sensorWhiteLevel: Float,
    private val black: FloatArray,
    private val shot: FloatArray,
    private val read: FloatArray,
    private val owner: EGLContext,
) : AutoCloseable {
    private val component = "26975 C pinned donor RAW hot pixel mask"
    private val gl = Iris26972CDonorSabreGpuMerge
    private val packedWidth = (width + 3) / 4
    private var detectionProgram = 0
    private var resolutionProgram = 0
    private var suppressionProgram = 0
    private var resolvedMask = 0
    private var count = 0
    private var closed = false

    private fun requireOwner() {
        check(!closed && owner != EGL14.EGL_NO_CONTEXT &&
            owner == EGL14.eglGetCurrentContext()) { "$component wrong/released EGL owner" }
    }

    private fun uniform(program: Int, name: String): Int =
        GLES30.glGetUniformLocation(program, name).also {
            check(it >= 0) { "$component missing donor uniform $name" }
        }

    private fun compileCompute(source: String, label: String): Int {
        val shader = GLES31.glCreateShader(GLES31.GL_COMPUTE_SHADER)
        check(shader != 0) { "$component $label shader allocation failed" }
        var program = 0
        try {
            GLES31.glShaderSource(shader, source)
            GLES31.glCompileShader(shader)
            val compiled = IntArray(1)
            GLES31.glGetShaderiv(shader, GLES31.GL_COMPILE_STATUS, compiled, 0)
            check(compiled[0] == GLES31.GL_TRUE) {
                "$component $label donor GLSL compile: ${GLES31.glGetShaderInfoLog(shader)}"
            }
            program = GLES31.glCreateProgram()
            check(program != 0) { "$component $label program allocation failed" }
            GLES31.glAttachShader(program, shader)
            GLES31.glLinkProgram(program)
            val linked = IntArray(1)
            GLES31.glGetProgramiv(program, GLES31.GL_LINK_STATUS, linked, 0)
            check(linked[0] == GLES31.GL_TRUE) {
                "$component $label donor GLSL link: ${GLES31.glGetProgramInfoLog(program)}"
            }
            return program
        } catch (cause: Throwable) {
            if (program != 0) GLES31.glDeleteProgram(program)
            throw cause
        } finally {
            GLES31.glDeleteShader(shader)
        }
    }

    private data class ImageBinding(
        val texture: Int, val level: Int, val layered: Boolean,
        val layer: Int, val access: Int, val format: Int,
    )

    private fun readImageBinding(unit: Int): ImageBinding {
        fun get(pname: Int) = IntArray(1).also {
            GLES31.glGetIntegeri_v(pname, unit, it, 0)
        }[0]
        return ImageBinding(
            get(GLES31.GL_IMAGE_BINDING_NAME),
            get(GLES31.GL_IMAGE_BINDING_LEVEL),
            get(GLES31.GL_IMAGE_BINDING_LAYERED) != 0,
            get(GLES31.GL_IMAGE_BINDING_LAYER),
            get(GLES31.GL_IMAGE_BINDING_ACCESS),
            get(GLES31.GL_IMAGE_BINDING_FORMAT),
        )
    }

    private fun restoreImageBinding(unit: Int, state: ImageBinding) {
        // Querying an unbound unit is well-defined, but some drivers report
        // GL_NONE as its format; a valid format must be supplied when clearing it.
        val format = if (state.texture == 0) GLES30.GL_RGBA8UI else state.format
        val access = if (state.texture == 0) GLES31.GL_READ_ONLY else state.access
        GLES31.glBindImageTexture(unit, state.texture, state.level,
            state.layered, state.layer, access, format)
    }

    private fun bindSourceAndMetadata(program: Int, raw: Int) {
        GLES31.glUseProgram(program)
        GLES31.glActiveTexture(GLES31.GL_TEXTURE0)
        GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, raw)
        GLES31.glUniform1i(uniform(program, "uRawTexture"), 0)
        GLES31.glUniform2i(uniform(program, "uImageSize"), width, height)
        GLES31.glUniform2i(uniform(program, "uGlobalOrigin"), 0, 0)
        GLES31.glUniform1i(uniform(program, "uCfaPattern"), cfaPattern)
        GLES31.glUniform4fv(uniform(program, "uBlackLevel"), 1, black, 0)
        GLES31.glUniform1f(uniform(program, "uWhiteLevel"), sensorWhiteLevel)
        GLES31.glUniform3f(uniform(program, "uNoiseSlope"),
            shot[0], 0.5f * (shot[1] + shot[2]), shot[3])
        GLES31.glUniform3f(uniform(program, "uNoiseOffset"),
            read[0], 0.5f * (read[1] + read[2]), read[3])
    }

    private fun allocateMask(): Int {
        val names = IntArray(1)
        GLES30.glGenTextures(1, names, 0)
        check(names[0] > 0) { "$component RGBA8UI mask allocation failed" }
        try {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, names[0])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, GLES30.GL_RGBA8UI,
                packedWidth, height, 0, GLES30.GL_RGBA_INTEGER, GLES30.GL_UNSIGNED_BYTE, null)
            gl.checkGl("allocate donor packed defect mask")
            return names[0]
        } catch (cause: Throwable) {
            GLES30.glDeleteTextures(1, names, 0)
            throw cause
        }
    }

    private fun detectFromReference(raw: Int) {
        check(resolvedMask == 0 && count == 0) { "$component reference detection already executed" }
        var isolatedMask = 0
        var finalMask = 0
        try {
            isolatedMask = allocateMask()
            finalMask = allocateMask()
            val groupsX = GlesComputeWorkGroup.imageGroupCount(packedWidth)
            val groupsY = GlesComputeWorkGroup.imageGroupCount(height)
            bindSourceAndMetadata(detectionProgram, raw)
            GLES31.glBindImageTexture(0, isolatedMask, 0, false, 0,
                GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA8UI)
            GLES31.glDispatchCompute(groupsX, groupsY, 1)
            GLES31.glMemoryBarrier(GLES31.GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
            bindSourceAndMetadata(resolutionProgram, raw)
            GLES31.glBindImageTexture(0, isolatedMask, 0, false, 0,
                GLES31.GL_READ_ONLY, GLES30.GL_RGBA8UI)
            GLES31.glBindImageTexture(1, finalMask, 0, false, 0,
                GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA8UI)
            GLES31.glDispatchCompute(groupsX, groupsY, 1)
            GLES31.glMemoryBarrier(GLES31.GL_TEXTURE_FETCH_BARRIER_BIT)
            gl.checkGl("pinned donor reference defect detect/resolve")
            resolvedMask = finalMask
            finalMask = 0
        } finally {
            if (isolatedMask != 0) GLES30.glDeleteTextures(1, intArrayOf(isolatedMask), 0)
            if (finalMask != 0) GLES30.glDeleteTextures(1, intArrayOf(finalMask), 0)
        }
    }

    /** One result per frame; output owns a new R16UI name, source stays caller-owned. */
    internal fun suppress(raw: Int, isReference: Boolean): Int {
        requireOwner()
        require(raw > 0 && count < expectedFrames) { "$component exceeded frozen burst or missing RAW" }
        require((count == 0) == isReference) {
            "$component only the first shutter-frozen reference may create the mask"
        }
        gl.checkGl("before original RAW defect stage")
        val saved = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val image0 = readImageBinding(0)
        val image1 = readImageBinding(1)
        var output = 0
        var framebuffer = 0
        var vao = 0
        var succeeded = false
        try {
            if (isReference) detectFromReference(raw)
            val names = IntArray(1)
            GLES30.glGenTextures(1, names, 0)
            output = names[0]
            check(output > 0 && output != raw) { "$component repaired RAW allocation failed" }
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, output)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, GLES30.GL_R16UI,
                width, height, 0, GLES30.GL_RED_INTEGER, GLES30.GL_UNSIGNED_SHORT, null)
            val fb = IntArray(1)
            GLES30.glGenFramebuffers(1, fb, 0)
            framebuffer = fb[0]
            val va = IntArray(1)
            GLES30.glGenVertexArrays(1, va, 0)
            vao = va[0]
            check(framebuffer > 0 && vao > 0) { "$component private FBO/VAO allocation failed" }
            GLES30.glBindVertexArray(vao)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffer)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, output, 0)
            GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                GLES30.GL_FRAMEBUFFER_COMPLETE) { "$component repaired RAW framebuffer incomplete" }
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true, true, true, true)
            GLES30.glUseProgram(suppressionProgram)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, raw)
            GLES30.glUniform1i(uniform(suppressionProgram, "uRaw"), 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE1)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, resolvedMask)
            GLES30.glUniform1i(uniform(suppressionProgram, "uHotPixelMask"), 1)
            GLES30.glUniform2i(uniform(suppressionProgram, "uImageSize"), width, height)
            GLES30.glViewport(0, 0, width, height)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
            gl.checkGl("pinned donor full-resolution RAW hot-pixel suppress")
            count++
            succeeded = true
            return output
        } finally {
            if (framebuffer != 0) GLES30.glDeleteFramebuffers(1, intArrayOf(framebuffer), 0)
            if (vao != 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
            if (!succeeded && output != 0) GLES30.glDeleteTextures(1, intArrayOf(output), 0)
            // Restore the two GLES image binding units, not just sampler state.
            // A/B code can share EGL contexts and must not see C's image bindings.
            try {
                restoreImageBinding(0, image0)
                restoreImageBinding(1, image1)
            } finally {
                saved.restore()
            }
        }
    }

    internal fun requireComplete() {
        requireOwner()
        check(count == expectedFrames && resolvedMask > 0) {
            "$component expected $expectedFrames frames, suppressed $count"
        }
    }

    override fun close() {
        requireOwner()
        if (resolvedMask > 0) GLES30.glDeleteTextures(1, intArrayOf(resolvedMask), 0)
        if (detectionProgram > 0) GLES30.glDeleteProgram(detectionProgram)
        if (resolutionProgram > 0) GLES30.glDeleteProgram(resolutionProgram)
        if (suppressionProgram > 0) GLES30.glDeleteProgram(suppressionProgram)
        resolvedMask = 0
        closed = true
    }

    internal companion object {
        fun begin(
            width: Int, height: Int, cfaPattern: Int,
            physical: Iris26972CPhysicalRawMetadata.Frozen,
            expectedFrames: Int,
        ): Iris26975COriginalSabreHotPixel {
            require(width in 16..16384 && height in 16..16384 && cfaPattern in 0..3 &&
                expectedFrames in 2..30 && physical.cfaPattern == cfaPattern &&
                physical.sensorWhiteLevel > 0) {
                "26975 C hot-pixel setup missing frozen sensor geometry/metadata"
            }
            val (shot, read) = physical.copyCanonicalNoiseForAudit()
            val black = physical.copyCanonicalBlackForAudit()
            require(shot.size == 4 && read.size == 4 && black.size == 4 &&
                shot.all { it.isFinite() && it > 0f } &&
                read.all { it.isFinite() && it >= 0f } &&
                black.all { it.isFinite() && it >= 0f && it < physical.sensorWhiteLevel.toFloat() }) {
                "26975 C hot-pixel detector requires genuine reference Camera2 S/O/black"
            }
            val gl = Iris26972CDonorSabreGpuMerge
            gl.requireCurrentContext()
            val major = gl.glInt(GLES30.GL_MAJOR_VERSION)
            val minor = gl.glInt(GLES30.GL_MINOR_VERSION)
            check(major > 3 || (major == 3 && minor >= 1)) {
                "26975 C original RAW hot-pixel compute requires GLES 3.1; no fallback"
            }
            check(gl.glInt(GLES31.GL_MAX_IMAGE_UNITS) >= 2 &&
                gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= width &&
                gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= height &&
                gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 2) {
                "26975 C original RAW hot-pixel GPU limits insufficient"
            }
            val owner = Iris26975COriginalSabreHotPixel(
                width, height, expectedFrames, cfaPattern,
                physical.sensorWhiteLevel.toFloat(), black, shot, read,
                EGL14.eglGetCurrentContext())
            val saved = Iris26972CDonorSabreGpuMerge.GlState.capture()
            try {
                owner.detectionProgram = owner.compileCompute(
                    Iris26975COriginalRawHotPixelShaders.DETECT, "DETECT")
                owner.resolutionProgram = owner.compileCompute(
                    Iris26975COriginalRawHotPixelShaders.RESOLVE, "RESOLVE")
                owner.suppressionProgram = gl.compileProgram(gl.VERTEX,
                    Iris26975COriginalRawHotPixelShaders.SUPPRESS)
                gl.checkGl("original donor hot-pixel shader setup")
                return owner
            } catch (cause: Throwable) {
                try { owner.close() } catch (cleanup: Throwable) { cause.addSuppressed(cleanup) }
                throw cause
            } finally {
                saved.restore()
            }
        }
    }
}
