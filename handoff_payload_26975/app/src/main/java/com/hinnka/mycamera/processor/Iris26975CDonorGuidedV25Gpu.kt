package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.DcpTextureResources
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.MgcGuidedUpsample
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawCurveTextureResources
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawEngineTonePass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawFullscreenQuad
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawLinearRcdPass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawProfileExposureGl
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawRenderingEngine
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawSrgbPass
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawToneMappingParameters

/**
 * C-private EGL and donor Adobe adapter; all MGC guided kernels, FBO layouts,
 * shader sources, and program lifetimes now belong to the pinned ORIGINAL
 * [MgcGuidedUpsample] rather than the handwritten Iris V25 port.
 *
 * The original code is unchanged except its package. We only adapt ownership,
 * the fixed Adobe-only RAW mode and the camera2 physical source contract.
 * This still does NOT prove Sabre/RAW/JPEG-R 1:1 parity or device GPU execution.
 */
internal class Iris26975CDonorGuidedV25Gpu : AutoCloseable {
    private val gpu = Iris26972CDonorSabreGpuMerge
    private val owner: EGLContext = EGL14.eglGetCurrentContext()
    private val donorGuided = MgcGuidedUpsample()
    private val donorQuad = RawFullscreenQuad()
    private val donorDcpTextures = DcpTextureResources()
    private val donorCurveTextures = RawCurveTextureResources()
    private val donorLinearRcd = RawLinearRcdPass(donorQuad)
    private val donorAdobeTone = RawEngineTonePass(donorQuad, donorDcpTextures, donorCurveTextures)
    private val donorSrgb = RawSrgbPass(donorQuad)
    private var rawWidth = 0
    private var rawHeight = 0
    private var donorVao = 0
    private var closed = false

    private fun requireOwner() {
        check(!closed && owner != EGL14.EGL_NO_CONTEXT && owner == EGL14.eglGetCurrentContext()) {
            "Experiment C original MGC guided EGL ownership mismatch"
        }
        gpu.requireCurrentContext()
    }

    /** Restore donor-only sampler targets not tracked by the older 0..4 2D guard.
     * Adapter changes GL ownership, never bjzhou's original shader behavior.
     */
    private data class ExtraSamplerBindings(
        val activeUnit:Int, val unit7Texture2D:Int,
        val unit2Texture3D:Int, val unit3Texture3D:Int,
    ) {
        fun restore() {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, unit7Texture2D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_3D, unit2Texture3D)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_3D, unit3Texture3D)
            GLES30.glActiveTexture(activeUnit)
        }
    }
    private fun captureExtraSamplers():ExtraSamplerBindings {
        val active = gpu.glInt(GLES30.GL_ACTIVE_TEXTURE)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
        val t7 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_2D)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
        val t2 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_3D)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
        val t3 = gpu.glInt(GLES30.GL_TEXTURE_BINDING_3D)
        GLES30.glActiveTexture(active)
        return ExtraSamplerBindings(active,t7,t2,t3)
    }
    private fun location(program:Int,name:String):Int = GLES30.glGetUniformLocation(program,name)
    private fun bind(program:Int,name:String,unit:Int,texture:Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0+unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,texture)
        GLES30.glUniform1i(location(program,name),unit)
    }
    private fun allocate(format:Int,width:Int,height:Int,linear:Boolean=false):Int {
        require(width>0 && height>0 && width<=gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
            height<=gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE)) { "MGC guided surface outside device bounds" }
        val id=IntArray(1);GLES30.glGenTextures(1,id,0)
        check(id[0]>0) { "MGC guided texture allocation failed" }
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id[0])
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,
            if(linear) GLES30.GL_LINEAR else GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,
            if(linear) GLES30.GL_LINEAR else GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        val pair=when(format){
            GLES30.GL_R16I -> GLES30.GL_RED_INTEGER to GLES30.GL_SHORT
            GLES30.GL_RGBA32UI -> GLES30.GL_RGBA_INTEGER to GLES30.GL_UNSIGNED_INT
            GLES30.GL_R32F -> GLES30.GL_RED to GLES30.GL_FLOAT
            GLES30.GL_RGBA16F -> GLES30.GL_RGBA to GLES30.GL_HALF_FLOAT
            else -> error("Unsupported donor MGC guided format $format")
        }
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,format,width,height,0,pair.first,pair.second,null)
        return id[0]
    }
    private fun frame(vararg textures:Int):Int {
        require(textures.isNotEmpty() && textures.size<=2 && textures.all{it>0})
        val out=IntArray(1);GLES30.glGenFramebuffers(1,out,0)
        check(out[0]>0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,out[0])
        textures.forEachIndexed{index,texture->
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0+index,GLES30.GL_TEXTURE_2D,texture,0)
        }
        if(textures.size==2)GLES30.glDrawBuffers(2,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0,
            GLES30.GL_COLOR_ATTACHMENT1),0)
        else GLES30.glDrawBuffers(1,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0),0)
        check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE) {
            "MGC guided framebuffer incompatible with GLES device"
        }
        return out[0]
    }
    private fun freeTex(vararg names:Int){val ids=names.filter{it>0}.toIntArray();if(ids.isNotEmpty())GLES30.glDeleteTextures(ids.size,ids,0)}
    private fun freeFbo(vararg names:Int){val ids=names.filter{it>0}.toIntArray();if(ids.isNotEmpty())GLES30.glDeleteFramebuffers(ids.size,ids,0)}

    val prepared: Boolean get() = donorGuided.isPrepared

    fun prepare(source: Int, width: Int, height: Int, gains: FloatArray,
                resolution: Iris26975CDonorFinishResolution) {
        requireOwner()
        check(!prepared && source > 0 && width > 0 && height > 0 && resolution.needsGuidedUpsample)
        check(gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= maxOf((width + 127) and -128,
            (height + 15) and -16) && gpu.glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 2 &&
            gpu.glInt(GLES30.GL_MAX_DRAW_BUFFERS) >= 2 &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 8)
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        try {
            if (donorVao == 0) {
                val ids = IntArray(1)
                GLES30.glGenVertexArrays(1, ids, 0)
                donorVao = ids[0]
                check(donorVao > 0) { "Original donor private VAO allocation failed" }
            }
            GLES30.glBindVertexArray(donorVao)
            donorGuided.prepare(source, width, height, gains, resolution.originalPolicy())
            rawWidth = width
            rawHeight = height
            gpu.checkGl("C pinned original MgcGuidedUpsample.prepare")
        } catch (failure: Throwable) {
            donorGuided.releaseBuffers()
            rawWidth = 0
            rawHeight = 0
            throw failure
        } finally {
            state.restore()
        }
    }

    fun renderAdobeLowTone(plan: Iris26972CColorDeveloper.Plan) {
        requireOwner()
        check(prepared && plan.width == rawWidth && plan.height == rawHeight)
        Iris26972CColorDeveloper.validate(plan)
        val e = plan.profileExposure.also { it.validate() }
        val dcp = Iris26975CDonorDcpBridge.resolve(plan)
        val pgtm = Iris26975COriginalPgtmBinding(plan.profileGainTable)
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val extraSamplers = captureExtraSamplers()
        val tex = IntArray(2)
        val fbo = IntArray(2)
        try {
            // The donor consumes a floating-point linear intermediate at each
            // stage, not 8-bit sRGB; allocate C-private 16F intermediates.
            tex[0] = allocate(GLES30.GL_RGBA16F, donorGuided.lowWidth, donorGuided.lowHeight, true)
            tex[1] = allocate(GLES30.GL_RGBA16F, donorGuided.lowWidth, donorGuided.lowHeight, true)
            fbo[0] = frame(tex[0])
            fbo[1] = frame(tex[1])
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true, true, true, true)
            // Original RawFullscreenQuad owns attribute setup, on our private VAO only.
            GLES30.glBindVertexArray(donorVao)

            val linear = donorLinearRcd.render(RawLinearRcdPass.Input(
                textureId = donorGuided.cameraTexture,
                targetFramebufferId = fbo[0],
                targetTextureId = tex[0],
                width = donorGuided.lowWidth,
                height = donorGuided.lowHeight,
                colorCorrectionMatrix = plan.sensorToProfileRows,
                cameraWhite = plan.cameraWhite,
                exposureGain = 1f, // Adobe profile ramp alone owns render EV.
                hncsCameraDomainGain = null,
                hncsInputEv = 1f,
                hncsHighlightTruncation = 1f,
                hncsHighlightMaximum = 1f,
                clampProfileRgb = true,
                hueSatMapSupportsOverrange = e.supportOverrange,
                bindHueSatMap = { program ->
                    Iris26975CDonorDcpBridge.bindLinearHueSat(
                        program, donorDcpTextures, dcp.linearHueSat)
                },
                label = "C original bjzhou low linear RCD",
            )) ?: error("Pinned bjzhou RawLinearRcdPass failed")
            check(linear.textureId == tex[0] && linear.width == donorGuided.lowWidth &&
                linear.height == donorGuided.lowHeight)

            val donorExposure = RawProfileExposureGl.Uniforms(
                exposureEv = e.exposureEv,
                useRamp = true,
                linearGain = e.linearGain,
                rampSlope = e.slope,
                rampBlack = e.black,
                rampRadius = e.radius,
                rampQScale = e.qScale,
                supportOverrange = e.supportOverrange,
                toneEnabled = e.toneEnabled,
                toneSlope = e.toneSlope,
                toneA = e.toneA,
                toneB = e.toneB,
                toneC = e.toneC,
            )
            val identity = floatArrayOf(1f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f)
            val toned = donorAdobeTone.render(RawEngineTonePass.Input(
                textureId = tex[0],
                targetFramebufferId = fbo[1],
                targetTextureId = tex[1],
                colorEngine = RawRenderingEngine.AdobeCurve,
                profileToEngineTransform = identity,
                outputTransform = plan.profileToLinearSrgbRows,
                globalOriginX = 0,
                globalOriginY = 0,
                // Donor RawDemosaicProcessor uses the FULL sensor grid, not the
                // 4x box grid, for DNG ProfileGainTableMap spatial coordinates.
                fullImageWidth = plan.width,
                fullImageHeight = plan.height,
                width = donorGuided.lowWidth,
                height = donorGuided.lowHeight,
                globalWidth = donorGuided.globalWidth,
                globalHeight = donorGuided.globalHeight,
                toneMappingParameters = RawToneMappingParameters(),
                profileExposure = donorExposure,
                dcpRenderPlan = dcp.dcpRenderPlan,
                applyDcpHueSatMap = false, // Original linear pass has already applied HueSat.
                spectralFilmLut = null,
                hncsRenderPlan = null,
                bindProfileGainTable = { program -> pgtm.bind(program, tex[0]) },
            )) ?: error("Pinned bjzhou Adobe Curve tone rendering failed")
            check(toned.textureId == tex[1])

            val encoded = donorSrgb.render(RawSrgbPass.Input(
                textureId = tex[1],
                targetFramebufferId = donorGuided.profileFramebuffer,
                targetTextureId = donorGuided.profileTexture,
                width = donorGuided.lowWidth,
                height = donorGuided.lowHeight,
            )) ?: error("Pinned bjzhou final sRGB encoding failed")
            check(encoded.textureId == donorGuided.profileTexture)
            gpu.checkGl("C pinned bjzhou low linear->Adobe->sRGB")
        } finally {
            pgtm.close()
            freeFbo(*fbo)
            freeTex(*tex)
            extraSamplers.restore()
            state.restore()
        }
    }


    /** The unchanged donor controller performs every MGC guided + sharpening stage. */
    fun render(target: Int, referenceSnr: Float, attenuation: Float) {
        requireOwner()
        check(prepared && target > 0 && rawWidth > 0 && rawHeight > 0)
        require(referenceSnr.isFinite() && referenceSnr >= 0f &&
            attenuation.isFinite() && attenuation >= 0f)
        val curves = Iris26975CDonorMgcSharpenCurves.build(referenceSnr)
        check(curves.size == 30)
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        try {
            GLES30.glBindVertexArray(donorVao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true, true, true, true)
            donorGuided.render(donorGuided.profileTexture, target, rawWidth, rawHeight,
                attenuation, curves)
            gpu.checkGl("C pinned original MgcGuidedUpsample.render")
        } finally {
            // The original donor releases prepared textures and framebuffers itself.
            state.restore()
        }
    }

    override fun close() {
        if (closed) return
        requireOwner()
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val extraSamplers = captureExtraSamplers()
        try {
            donorGuided.release()
            donorLinearRcd.release()
            donorAdobeTone.release()
            donorSrgb.release()
            if (donorVao > 0) GLES30.glDeleteVertexArrays(1, intArrayOf(donorVao), 0)
            donorVao = 0
            rawWidth = 0
            rawHeight = 0
            closed = true
        } finally {
            extraSamplers.restore()
            state.restore()
        }
    }
}
