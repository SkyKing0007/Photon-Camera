package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.DcpTextureResources
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawCurveTextureResources
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawEngineTonePass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawFullscreenQuad
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawHdrReferencePass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawLinearRcdPass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawProfileExposureGl
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawRenderingEngine
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawToneMappingParameters

/**
 * Experiment C texture-ownership adapter, NOT a substitute image algorithm.
 *
 * The fully denoised, shutter-frozen Sabre merged camera RGB is developed with the original
 * donor RawLinearRcdPass and then its original Adobe HDR-reference pass. The first
 * RGBA16F output is a TEMPORARY ProPhoto input to HDR, reused by the
 * subsequent native-1x guided SDR output. No third 50MP F16 surface.
 *
 * The resulting scalar texture is donor HDR gain AFTER denoise, BEFORE final SDR sharpening, exactly
 * the original RawDemosaicProcessor's HDR-reference contract. With genuinely paired
 * pinned HDRNet metadata, the donor's separate HDR scene gain is used exactly once.
 * The full donor RAW engine, HDRNet PGTM generator and JPEG/R finalizer are not yet wired;
 * publication remains fail closed. No Android device/GL driver proof is implied.
 */
internal object Iris26975COriginalHdrAfterDenoise {
    private const val COMPONENT = "Experiment C exact donor Adobe HDR after denoise"
    private val gpu = Iris26972CDonorSabreGpuMerge

    private data class ExternalSamplerState(
        val previousActive: Int,
        val unit7Texture2D: Int,
        val unit2Texture3D: Int,
        val unit3Texture3D: Int,
    ) {
        fun restore() {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, unit7Texture2D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_3D, unit2Texture3D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_3D, unit3Texture3D)
            GLES30.glActiveTexture(previousActive)
        }
    }

    private fun captureExternalSamplers(): ExternalSamplerState {
        val active = gpu.glInt(GLES30.GL_ACTIVE_TEXTURE)
        return try {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
            val t7 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_2D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            val t2 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_3D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            val t3 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_3D)
            ExternalSamplerState(active, t7, t2, t3)
        } finally {
            GLES30.glActiveTexture(active)
        }
    }

    private fun targetTexture(width: Int, height: Int): Int {
        val ids = IntArray(1)
        GLES30.glGenTextures(1, ids, 0)
        val id = ids[0]
        check(id > 0) { "$COMPONENT texture allocation failed" }
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, GLES30.GL_RGBA16F,
            width, height, 0, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, null)
        return id
    }

    private fun targetFramebuffer(texture: Int): Int {
        val ids = IntArray(1)
        GLES30.glGenFramebuffers(1, ids, 0)
        val id = ids[0]
        check(id > 0) { "$COMPONENT framebuffer allocation failed" }
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, id)
        GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_TEXTURE_2D, texture, 0)
        GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
            GLES30.GL_FRAMEBUFFER_COMPLETE) { "$COMPONENT HDR/profile F16 framebuffer incomplete" }
        return id
    }

    /** Original Adobe/DCP HDR reference; only caller-supplied real DNG PGTM is bound. */
    internal fun develop(
        plan: Iris26972CColorDeveloper.Plan,
        sabre: Iris26972CDonorSabreGpuResolve.Result,
        referenceSnr: Float,
        sharpenAttenuation: Float,
    ): Iris26972CColorDeveloper.Result {
        Iris26972CColorDeveloper.validate(plan)
        sabre.requireOwner()
        require(plan.width == sabre.width && plan.height == sabre.height &&
            sabre.extendedCameraRgbTexture > 0 &&
            sabre.extendedCameraRgbTexture != sabre.texture &&
            referenceSnr.isFinite() && referenceSnr >= 0f &&
            sharpenAttenuation.isFinite() && sharpenAttenuation in 0f..1f &&
            plan.lutSelection.isNoLut) {
            "$COMPONENT requires genuine merged extended RAW and no creative LUT"
        }
        val dcp = Iris26975CDonorDcpBridge.resolve(plan)
        val pgtm = Iris26975COriginalPgtmBinding(plan.profileGainTable)
        gpu.requireCurrentContext()
        require(EGL14.eglGetCurrentContext() != EGL14.EGL_NO_CONTEXT &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= maxOf(plan.width, plan.height) &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 8 &&
            gpu.glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 1) {
            "$COMPONENT requires native-grid F16 targets and eight texture units"
        }
        gpu.checkGl("C donor HDR entry")
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val samplers = captureExternalSamplers()
        val savedPackBuffer = gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val savedUnpackBuffer = gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val savedPackAlignment = gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val savedUnpackAlignment = gpu.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val savedPackRowLength = gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        val savedUnpackRowLength = gpu.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        val textures = IntArray(2)
        val framebuffers = IntArray(2)
        var vao = 0
        var delivered = false
        val quad = RawFullscreenQuad()
        val dcpTextures = DcpTextureResources()
        val curveTextures = RawCurveTextureResources()
        val linear = RawLinearRcdPass(quad)
        val tone = RawEngineTonePass(quad, dcpTextures, curveTextures)
        val hdr = RawHdrReferencePass(tone)
        try {
            // Donor shader uploads/curve measurements use direct Buffers, never PBO offsets.
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, 0)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true, true, true, true)
            val ids = IntArray(1)
            GLES30.glGenVertexArrays(1, ids, 0)
            vao = ids[0]
            check(vao > 0) { "$COMPONENT private donor VAO missing" }
            GLES30.glBindVertexArray(vao)
            textures[0] = targetTexture(plan.width, plan.height)
            textures[1] = targetTexture(plan.width, plan.height)
            check(textures.toSet().size == 2 &&
                textures.none { it == sabre.texture || it == sabre.extendedCameraRgbTexture }) {
                "$COMPONENT source/result texture IDs overlap"
            }
            framebuffers[0] = targetFramebuffer(textures[0])
            framebuffers[1] = targetFramebuffer(textures[1])

            val calibrated = linear.render(RawLinearRcdPass.Input(
                textureId = sabre.extendedCameraRgbTexture,
                targetFramebufferId = framebuffers[0],
                targetTextureId = textures[0],
                width = plan.width,
                height = plan.height,
                colorCorrectionMatrix = plan.sensorToProfileRows,
                cameraWhite = plan.cameraWhite,
                exposureGain = 1f,
                hncsCameraDomainGain = null,
                hncsInputEv = 1f,
                hncsHighlightTruncation = 1f,
                hncsHighlightMaximum = 1f,
                clampProfileRgb = true,
                hueSatMapSupportsOverrange = plan.profileExposure.supportOverrange,
                bindHueSatMap = { program ->
                    Iris26975CDonorDcpBridge.bindLinearHueSat(
                        program, dcpTextures, dcp.linearHueSat)
                },
                label = "C bjzhou original post-denoise HDR linear profile",
            )) ?: error("$COMPONENT original RawLinearRcdPass failed")
            check(calibrated.textureId == textures[0] && calibrated.width == plan.width &&
                calibrated.height == plan.height)

            val e = plan.profileExposure.also { it.validate() }
            val originalUniforms = RawProfileExposureGl.Uniforms(
                exposureEv=e.exposureEv, useRamp=true, linearGain=e.linearGain,
                rampSlope=e.slope, rampBlack=e.black, rampRadius=e.radius,
                rampQScale=e.qScale, supportOverrange=e.supportOverrange,
                toneEnabled=e.toneEnabled, toneSlope=e.toneSlope,
                toneA=e.toneA, toneB=e.toneB, toneC=e.toneC,
            )
            val identity = floatArrayOf(1f,0f,0f,0f,1f,0f,0f,0f,1f)
            val input = RawEngineTonePass.Input(
                textureId = textures[0],
                targetFramebufferId = framebuffers[1],
                targetTextureId = textures[1],
                colorEngine = RawRenderingEngine.AdobeCurve,
                profileToEngineTransform = identity,
                outputTransform = plan.profileToLinearSrgbRows,
                globalOriginX = 0, globalOriginY = 0,
                fullImageWidth = plan.width, fullImageHeight = plan.height,
                width = plan.width, height = plan.height,
                toneMappingParameters = RawToneMappingParameters(),
                profileExposure = originalUniforms,
                dcpRenderPlan = dcp.dcpRenderPlan,
                applyDcpHueSatMap = false, // HueSat already applied by RawLinearRcdPass.
                spectralFilmLut = null,
                hncsRenderPlan = null,
                bindProfileGainTable = { program -> pgtm.bind(program, textures[0]) },
            )
            // Original RawDemosaicProcessor separates the HDRNet long-scene gain
            // from DNG BaselineExposure / Adobe SDR. Do not derive it from PGTM
            // weights or multiply baseline/user exposure twice.
            val sceneExposureGain = plan.donorHdrNetExposure?.originalSceneGain()
                ?: originalUniforms.linearGain
            // Donor's measured 1024-sample FP16 base-curve shader, and matching HDR
            // engine shader. In no-HDRNet Adobe the original profile gain applies.
            val ratio = hdr.render(RawHdrReferencePass.Input(
                engineInput = input,
                sceneExposureGain = sceneExposureGain,
                coordinateInput = if (plan.profileGainTable != null)
                    RawEngineTonePass.HdrCoordinateInput(
                        textureId = textures[0],
                        profileToEngineTransform = identity,
                        profileExposureLinearGain = originalUniforms.linearGain,
                    ) else null,
            )) ?: error("$COMPONENT original RawHdrReferencePass failed")
            check(ratio.textureId == textures[1] && ratio.width == plan.width &&
                ratio.height == plan.height)
            gpu.checkGl("C original Adobe HDR ratio post-denoise")
            // textures[0] holds temporary linear ProPhoto. Following this reference pass,
            // guided original MGC overwrites it with the final encoded SDR.
            val result = Iris26972CColorDeveloper.Result.owned(
                textures[0], textures[1], plan.width, plan.height,
                plan.physicalCameraId, referenceSnr, sharpenAttenuation)
            delivered = true
            return result
        } finally {
            try {
                pgtm.close()
                hdr.release()
                linear.release()
                tone.release() // releases shared DCP/curve resources and HDR FBO
            } finally {
                if (vao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(vao), 0)
                val validFramebuffers = framebuffers.filter { it > 0 }.toIntArray()
                if (validFramebuffers.isNotEmpty())
                    GLES30.glDeleteFramebuffers(validFramebuffers.size, validFramebuffers, 0)
                if (!delivered) {
                    val created = textures.filter { it > 0 }.toIntArray()
                    if (created.isNotEmpty()) GLES30.glDeleteTextures(created.size, created, 0)
                }
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, savedPackBuffer)
                GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, savedUnpackBuffer)
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, savedPackAlignment)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, savedUnpackAlignment)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, savedPackRowLength)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, savedUnpackRowLength)
                try { samplers.restore() } finally { state.restore() }
            }
        }
    }
}
