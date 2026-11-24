package com.hinnka.mycamera.processor

import android.graphics.Rect
import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawFullscreenQuad
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawOutputGeometry
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawOutputPass
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawOutputUpscaleMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawTileRect
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975CNativeOneX
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Experiment-C resource/readback adapter around the ORIGINAL pinned bjzhou RawOutputPass.
 *
 * Only resource ownership, bounded RGBA16F targets and transferring donor-rendered pixels are
 * C-specific. The output crop, orientation, Lanczos-3 and HDR-ratio math are executed by the
 * unchanged pinned donor shader, on the original full-resolution source textures. No CPU pixel
 * interpolation, no invented second sharpening, no fallback output and no 50MP output scratch.
 *
 * The publication gate remains locked until the complete donor RAW and JPEG/R path is proven.
 */
internal class Iris26975COriginalOutputGpu(
    private val geometry: Iris26975COutputGeometry,
    private val color: Iris26972CColorDeveloper.Result,
) : AutoCloseable {
    private val component = "26975 C original bjzhou RawOutputPass final geometry"
    private val owner: EGLContext = EGL14.eglGetCurrentContext()
    private val gl = Iris26972CDonorSabreGpuMerge
    private val quad = RawFullscreenQuad()
    private val originalPass = RawOutputPass(quad)
    private val crop = Rect(geometry.cropLeft, geometry.cropTop, geometry.cropRight, geometry.cropBottom)
    private val donorGeometry: RawOutputGeometry
    private val textures = IntArray(2)
    private val framebuffers = IntArray(2)
    private var vao = 0
    private var closed = false

    init {
        color.requireOwner()
        check(owner != EGL14.EGL_NO_CONTEXT && geometry.rawWidth == color.width &&
            geometry.rawHeight == color.height && color.encodedSrgbTexture > 0 &&
            color.donorHdrRatioTexture > 0 &&
            color.donorHdrRatioTexture != color.encodedSrgbTexture) {
            "$component requires two real donor full-resolution SDR/HDR sources"
        }
        val swapped = geometry.rotation == 90 || geometry.rotation == 270
        donorGeometry = RawOutputGeometry(
            sourceBounds = RawTileRect(geometry.cropLeft, geometry.cropTop,
                geometry.cropRight, geometry.cropBottom),
            rotation = geometry.rotation,
            scale = 1f,
            referenceWidth = if (swapped) geometry.outputHeight else geometry.outputWidth,
            referenceHeight = if (swapped) geometry.outputWidth else geometry.outputHeight,
            upscaleMode = RawOutputUpscaleMode.LANCZOS3,
        )
        check(donorGeometry.width == geometry.outputWidth &&
            donorGeometry.height == geometry.outputHeight) {
            "$component donor geometry changed the shutter-frozen physical output"
        }
    }

    fun fits(left: Int, top: Int, width: Int, height: Int): Boolean =
        !closed && left >= 0 && top >= 0 && width in 1..256 && height in 1..256 &&
            left <= geometry.outputWidth - width && top <= geometry.outputHeight - height

    private fun requireOwner() {
        color.requireOwner()
        check(!closed && owner == EGL14.eglGetCurrentContext()) {
            "$component expired EGL context or output renderer"
        }
    }

    private fun allocateSurfaces() {
        if (vao != 0) return
        check(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= maxOf(geometry.rawWidth,
            geometry.rawHeight, 256)) { "$component donor output exceeds hardware texture size" }
        val ids = IntArray(1)
        GLES30.glGenVertexArrays(1, ids, 0)
        vao = ids[0]
        check(vao > 0) { "$component private donor VAO allocation failed" }
        for (index in 0..1) {
            GLES30.glGenTextures(1, ids, 0)
            textures[index] = ids[0]
            check(textures[index] > 0) { "$component F16 tile allocation failed" }
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, textures[index])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, GLES30.GL_RGBA16F,
                256, 256, 0, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, null)
            GLES30.glGenFramebuffers(1, ids, 0)
            framebuffers[index] = ids[0]
            check(framebuffers[index] > 0)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, framebuffers[index])
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0, GLES30.GL_TEXTURE_2D, textures[index], 0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$component 16F output target is not framebuffer complete"
            }
        }
        gl.checkGl("$component F16 tile setup")
    }

    fun render(left: Int, top: Int, width: Int, height: Int): Iris26975CGeometryResampler.Tile {
        requireOwner()
        require(fits(left, top, width, height)) { "$component output region exceeds donor tile" }
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val oldPack = gl.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldPackAlign = gl.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldPackRows = gl.glInt(GLES30.GL_PACK_ROW_LENGTH)
        try {
            allocateSurfaces()
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true, true, true, true)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
            val region = RawTileRect(left, top, left + width, top + height)
            fun draw(index: Int, source: Int, base: Int?): ByteBuffer {
                val output = originalPass.render(RawOutputPass.Input(
                    textureId = source,
                    sourceWidth = color.width,
                    sourceHeight = color.height,
                    rotation = geometry.rotation,
                    bounds = crop,
                    targetFramebufferId = framebuffers[index],
                    targetTextureId = textures[index],
                    targetWidth = width,
                    targetHeight = height,
                    hdrSdrBaseTextureId = base,
                    geometry = donorGeometry,
                    outputRegion = region,
                )) ?: error("$component original donor rendering refused output")
                check(output.textureId == textures[index] && output.width == width &&
                    output.height == height)
                GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER, framebuffers[index])
                GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
                val values = ByteBuffer.allocateDirect(width * height * 16)
                    .order(ByteOrder.nativeOrder())
                GLES30.glReadPixels(0, 0, width, height, GLES30.GL_RGBA, GLES30.GL_FLOAT, values)
                gl.checkGl("$component ${if (base == null) "SDR" else "HDR"} original readback")
                values.position(0)
                return values
            }
            // The second original output draw reuses the unrounded source SDR texture,
            // *not* the prior rounded output tile: exactly bjzhou's HDR reference contract.
            val sdr = draw(0, color.encodedSrgbTexture, null)
            val hdrRgba = draw(1, color.donorHdrRatioTexture, color.encodedSrgbTexture)
            val sdr8 = ByteBuffer.allocateDirect(width * height * 4)
            check(Iris26975CNativeOneX.render(sdr, width, height, width * 16,
                sdr8, width * 4)) { "$component cannot pack original SDR output" }
            val hdrRgb = ByteBuffer.allocateDirect(width * height * 3 * Float.SIZE_BYTES)
                .order(ByteOrder.nativeOrder())
            val rgb = hdrRgb.asFloatBuffer()
            val hdr = hdrRgba.asFloatBuffer()
            val encoded = sdr.asFloatBuffer()
            for (pixel in 0 until width * height) {
                val offset = pixel * 4
                for (channel in 0..2) {
                    val v = hdr.get(offset + channel)
                    check(v.isFinite() && v >= 0f) { "$component non-finite donor HDR pixel" }
                    rgb.put(pixel * 3 + channel, v)
                }
                check(encoded.get(offset + 3) >= 0.999f) {
                    "$component invalid original SDR output alpha"
                }
            }
            hdrRgb.position(0)
            sdr.position(0)
            sdr8.position(0)
            return Iris26975CGeometryResampler.Tile(sdr8, hdrRgb, sdr)
        } finally {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, oldPack)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, oldPackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, oldPackRows)
            state.restore()
        }
    }

    override fun close() {
        requireOwner()
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        try {
            originalPass.release()
            if (vao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
            val fbos = framebuffers.filter { it > 0 }.toIntArray()
            if (fbos.isNotEmpty()) GLES30.glDeleteFramebuffers(fbos.size, fbos, 0)
            val tex = textures.filter { it > 0 }.toIntArray()
            if (tex.isNotEmpty()) GLES30.glDeleteTextures(tex.size, tex, 0)
            vao = 0
            framebuffers.fill(0)
            textures.fill(0)
            closed = true
        } finally {
            state.restore()
        }
    }
}
