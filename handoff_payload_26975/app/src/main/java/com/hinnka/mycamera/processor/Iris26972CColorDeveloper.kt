package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawHdrReferenceMath
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Isolated C-only RAW color development of the *pre-SDR-clamp* donor Sabre camera RGB.
 *
 * This stage consumes actual immutable Camera2/DNG-calibrated matrices passed by its
 * owner, the pinned 1025-sample Adobe ACR3 curve, and actual optional donor-style DCP
 * tables. It creates two truly distinct outputs: encoded sRGB SDR for native-grid donor MGC finish and
 * scene-linear extended sRGB before Adobe/SDR clamping for a measured gainmap.
 *
 * It is NOT a producer of camera profiles. The isolated Camera2 capture owner MUST supply a
 * real shutter-frozen dual-illuminant D50 matrix solution for POST-donor-Resolve
 * camera RGB. The donor's final RGB gains have ALREADY been applied; the C
 * matrix must not apply as-shot WB a second time. Reject ambiguous metadata. No A/B classes are called.
 * No processing path may use the donor U16 `texture` as an invented HDR source;
 * the 1024-sample Adobe neutral HDR curve is measured by the GPU into RGBA16F.
 * Source-wired to C-only shutter and publishing, but production-gated and not device-proven.
 */
internal object Iris26972CColorDeveloper {
    private const val COMPONENT = "26972 C independent RAW color"
    private val gpu = Iris26972CDonorSabreGpuMerge

    internal class ProfileMap(
        val hueBins: Int, val saturationBins: Int, val valueBins: Int,
        /** RGB triplets in x=saturation, y=value*hueBins+hue row order. */
        val values: FloatArray,
        /** DNG table encoding: 0 = linear, 1 = sRGB. Must come from the real DCP tag. */
        val encoding: Int,
    ) {
        internal fun validate() {
            val count = hueBins.toLong() * saturationBins * valueBins
            require(hueBins in 2..360 && saturationBins in 2..256 && valueBins in 1..256 &&
                count in 1..2_000_000 && values.size.toLong() == count * 3 &&
                encoding in 0..1 && values.all { it.isFinite() }) {
                "$COMPONENT invalid actual DCP HueSat/Look table"
            }
        }
    }

    internal class Plan(
        val width: Int, val height: Int,
        /** POST-donor-WB camera RGB -> D50 ProPhoto. No second as-shot WB permitted. */
        val sensorToProfileRows: FloatArray,
        /** D50 ProPhoto -> linear sRGB (NOT display gamma encoding). */
        val profileToLinearSrgbRows: FloatArray,
        val physicalCameraId: String,
        val calibrationProvenance: String,
        val cameraWhite: FloatArray,
        val profileExposure: Iris26975CDonorProfileExposure.Frozen =
            Iris26975CDonorProfileExposure.originalAdobeCameraDefault(),
        val hueSat: ProfileMap? = null,
        val look: ProfileMap? = null,
        /** Only a real DNG 52525/52544 asset may supply PGTM; Camera2 has no default. */
        val profileGainTable: Iris26975COriginalPgtmBinding.Frozen? = null,
        /** Frozen C-only user choice, never inherited from A/B or donor Standard. */
        val lutSelection: Iris26975CDonorLutSelection.Frozen =
            Iris26975CDonorLutSelection.freeze(),
        /** Actual shutter RAW timestamp; never the active preview or logical camera. */
        val referenceTimestampNs: Long? = null,
        /** Only real pinned HDRNet metadata paired with the actual PGTM and RAW. */
        val donorHdrNetExposure: Iris26975COriginalHdrNetExposure.Frozen? = null,
    )

    internal class Result private constructor(
        val encodedSrgbTexture: Int,
        /** Scalar donor HDR/SDR ratio, NOT a pre-sharpen synthetic HDR image. */
        val donorHdrRatioTexture: Int,
        val width: Int, val height: Int,
        val physicalCameraId: String,
        /** Original reference-frame RAW SNR (never fused output-frame SNR). */
        val referenceSnr: Float,
        val sharpenAttenuation: Float,
        private val owner: EGLContext,
    ) : AutoCloseable {
        private var released = false
        // Donor Guided V25 has already applied the full-resolution MGC kernel.
        // A second tile sharpener is forbidden, even if legacy C source still exists.
        internal var donorGuidedSdrComplete: Boolean = false
            private set
        // Until the original HDR reference + LUT sidecar are wired, publication
        // must remain fail-closed instead of passing the older C HDR substitute.
        internal val donorUltraHdrComplete: Boolean get() = false

        internal fun markDonorGuidedSdrComplete() {
            requireOwner()
            check(!donorGuidedSdrComplete) { "$COMPONENT duplicate guided SDR finishing" }
            donorGuidedSdrComplete = true
        }
        internal fun requireOwner() {
            check(!released && owner != EGL14.EGL_NO_CONTEXT &&
                owner == EGL14.eglGetCurrentContext()) { "$COMPONENT wrong EGL owner" }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(2, intArrayOf(encodedSrgbTexture,donorHdrRatioTexture), 0)
            released = true
        }
        companion object {
            internal fun owned(sdr: Int,hdr: Int,width: Int,height: Int,lens: String,
                referenceSnr: Float,sharpenAttenuation: Float):Result =
                Result(sdr,hdr,width,height,lens,referenceSnr,sharpenAttenuation,
                    EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan: Plan) {
        require(plan.width in 16..16384 && plan.height in 16..16384 &&
            (plan.width and 1)==0 && (plan.height and 1)==0 &&
            plan.physicalCameraId.isNotBlank() &&
            plan.calibrationProvenance == "CAMERA2_DNG_POST_DONOR_WB_ONCE" &&
            plan.sensorToProfileRows.size == 9 &&
            plan.profileToLinearSrgbRows.size == 9 &&
            plan.cameraWhite.size == 3 &&
            // Actual DCP camera-profile tables may be present. Adobe applies
            // them through its original GPU shaders; they are NOT creative LUTs.
            // Only the user-approved No creative LUT route is implemented in live C.
            // Reject an explicit Standard/other LUT rather than silently ignore it.
            plan.lutSelection.isNoLut &&
            plan.cameraWhite.all { it.isFinite() && it in 0.001f..1f } &&
            plan.sensorToProfileRows.all { it.isFinite() } &&
            plan.profileToLinearSrgbRows.all { it.isFinite() }) {
            "$COMPONENT requires valid genuine frozen Camera2/DNG color calibration"
        }
        fun det(m:FloatArray): Double {
            val a=m.map { it.toDouble() }
            return a[0]*(a[4]*a[8]-a[5]*a[7])-
                a[1]*(a[3]*a[8]-a[5]*a[6])+
                a[2]*(a[3]*a[7]-a[4]*a[6])
        }
        require(kotlin.math.abs(det(plan.sensorToProfileRows)) > 1e-8 &&
            kotlin.math.abs(det(plan.profileToLinearSrgbRows)) > 1e-8) {
            "$COMPONENT singular sensor/profile matrix"
        }
        plan.profileExposure.validate()
        plan.donorHdrNetExposure?.let { exposure ->
            require(plan.profileGainTable != null &&
                plan.referenceTimestampNs != null &&
                exposure.matches(plan.physicalCameraId, plan.referenceTimestampNs)) {
                "$COMPONENT HDRNet metadata lacks matching real PGTM/physical RAW reference"
            }
            exposure.originalSceneGain()
        }
        plan.hueSat?.validate()
        plan.look?.validate()
        check(Iris26972CAdobeAcr3.size == 1025) {
            "$COMPONENT pinned donor ACR3 samples unavailable"
        }
    }

    @Deprecated(
        message = "Experiment C requires original RawLinearRcdPass and RawHdrReferencePass; custom color developing is forbidden",
        level = DeprecationLevel.ERROR,
    )
    internal fun develop(
        plan: Plan,
        sabre: Iris26972CDonorSabreGpuResolve.Result,
        referenceSnr: Float,
        sharpenAttenuation: Float = 1f,
    ): Result {
        validate(plan)
        require(referenceSnr.isFinite() && referenceSnr >= 0f &&
            sharpenAttenuation.isFinite() && sharpenAttenuation >= 0f &&
            sharpenAttenuation <= 1f) {
            "$COMPONENT missing original RAW sharpen reference SNR"
        }
        sabre.requireOwner()
        require(plan.width == sabre.width && plan.height == sabre.height) {
            "$COMPONENT C-only RAW / calibration size mismatch"
        }
        require(sabre.extendedCameraRgbTexture != sabre.texture &&
            sabre.extendedCameraRgbTexture > 0) {
            "$COMPONENT refuses clipped donor U16 as synthetic HDR"
        }
        gpu.requireCurrentContext()
        require(gpu.glInt(GLES30.GL_MAX_DRAW_BUFFERS)>=2 &&
            gpu.glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS)>=2 &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=5 &&
            gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE)>=maxOf(plan.width,plan.height)) {
            "$COMPONENT dual SDR/HDR F16 attachments unavailable"
        }
        gpu.checkGl("C color developer before calibration")
        val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val unpackBuffer=gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val unpackAlign=gpu.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val unpackRowLength=gpu.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        var program=0;var fbo=0;var vao=0;var successful=false
        val images=IntArray(2)
        val lookups=IntArray(4)
        try {
            program=gpu.compileProgram(gpu.VERTEX,Iris26972CColorDevelopShaders.color)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
            GLES30.glGenTextures(2,images,0)
            GLES30.glGenTextures(4,lookups,0)
            check(images.all { it>0 } && lookups.all { it>0 } &&
                (images.toList()+lookups.toList()+sabre.texture+
                    sabre.extendedCameraRgbTexture).toSet().size==8) {
                "$COMPONENT duplicate C color texture name"
            }
            images.forEach { id ->
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
                textureParams()
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                    plan.width,plan.height,0,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,null)
            }
            uploadLut(lookups[0], Iris26972CAdobeAcr3.samples(),1025,1,
                GLES30.GL_R16F,GLES30.GL_RED)
            uploadLut(lookups[1],plan.hueSat?.values ?: floatArrayOf(0f,1f,1f),
                plan.hueSat?.saturationBins ?: 1,
                (plan.hueSat?.hueBins ?: 1)*(plan.hueSat?.valueBins ?: 1),
                GLES30.GL_RGB32F,GLES30.GL_RGB)
            uploadLut(lookups[2],plan.look?.values ?: floatArrayOf(0f,1f,1f),
                plan.look?.saturationBins ?: 1,
                (plan.look?.hueBins ?: 1)*(plan.look?.valueBins ?: 1),
                GLES30.GL_RGB32F,GLES30.GL_RGB)
            // The pinned donor renders neutral Adobe engine response into a
            // 1024x1 RGBA16F FBO and solves the shoulder using measured values.
            // Do not estimate this curve on the CPU; a half-float GPU roundtrip
            // changes the tangent/join in HDR highlights on real devices.
            // No A/B renderer is consulted, and unavailable FP16 readback is a
            // hard C-only failure rather than an approximate CPU fallback.
            val neutralCurve = measureDonorAdobeNeutralCurveOnGpu(
                lookups[0], plan.profileToLinearSrgbRows, plan.profileExposure)
            // Execute the original pinned bjzhou RawHdrReferenceMath in the C-only
            // namespace. Its Git blob is verified after restoring the donor package;
            // the earlier independently transcribed solver is NOT runtime authority.
            val extension = RawHdrReferenceMath.solve(neutralCurve)
            uploadLut(lookups[3],neutralCurve,
                RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT,1,GLES30.GL_R16F,GLES30.GL_RED)
            gpu.checkGl("C donor Adobe HDR neutral response upload")
            val ids=IntArray(1)
            GLES30.glGenFramebuffers(1,ids,0);fbo=ids[0]
            GLES30.glGenVertexArrays(1,ids,0);vao=ids[0]
            check(fbo>0 && vao>0){"$COMPONENT no isolated framebuffer or VAO"}
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,images[0],0)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT1,
                GLES30.GL_TEXTURE_2D,images[1],0)
            GLES30.glDrawBuffers(2,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_COLOR_ATTACHMENT1),0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                GLES30.GL_FRAMEBUFFER_COMPLETE){"$COMPONENT real HDR MRT incomplete"}
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glUseProgram(program)
            val sources=intArrayOf(sabre.extendedCameraRgbTexture,lookups[0],lookups[1],lookups[2],lookups[3])
            val names=arrayOf("uExtendedCameraRgb","uAdobeAcr3","uHueSatMap","uLookMap",
                "uHdrNeutralCurve")
            sources.forEachIndexed { index, id ->
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0+index)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
                GLES30.glUniform1i(loc(program,names[index]),index)
            }
            GLES30.glUniform1i(loc(program,"uAcr3Size"),1025)
            GLES30.glUniform1f(loc(program,"uHdrJoinInput"),extension.joinInput)
            GLES30.glUniform1f(loc(program,"uHdrJoinOutput"),extension.joinOutput)
            GLES30.glUniform1f(loc(program,"uHdrJoinSlope"),extension.joinSlope)
            GLES30.glUniform1f(loc(program,"uHdrQuadratic"),extension.quadraticCoefficient)
            GLES30.glUniform1f(loc(program,"uHdrWhiteOutput"),extension.whiteOutput)
            GLES30.glUniform1f(loc(program,"uHdrWhiteSlope"),extension.whiteSlope)
            GLES30.glUniform1i(loc(program,"uHdrExtendsBase"),if(extension.extendsBaseCurve)1 else 0)
            val donorExposure=plan.profileExposure
            GLES30.glUniform1f(loc(program,"uProfileRampSlope"),donorExposure.slope)
            GLES30.glUniform1f(loc(program,"uProfileRampBlack"),donorExposure.black)
            GLES30.glUniform1f(loc(program,"uProfileRampRadius"),donorExposure.radius)
            GLES30.glUniform1f(loc(program,"uProfileRampQScale"),donorExposure.qScale)
            GLES30.glUniform1i(loc(program,"uProfileToneEnabled"),
                if (donorExposure.toneEnabled) 1 else 0)
            GLES30.glUniform1f(loc(program,"uProfileToneSlope"),donorExposure.toneSlope)
            GLES30.glUniform1f(loc(program,"uProfileToneA"),donorExposure.toneA)
            GLES30.glUniform1f(loc(program,"uProfileToneB"),donorExposure.toneB)
            GLES30.glUniform1f(loc(program,"uProfileToneC"),donorExposure.toneC)
            GLES30.glUniform3f(loc(program,"uCameraWhite"),
                plan.cameraWhite[0],plan.cameraWhite[1],plan.cameraWhite[2])
            GLES30.glUniform1i(loc(program,"uHueSatEnabled"),if(plan.hueSat!=null)1 else 0)
            GLES30.glUniform1i(loc(program,"uLookEnabled"),if(plan.look!=null)1 else 0)
            fun dims(name:String,map:ProfileMap?) {
                GLES30.glUniform3i(loc(program,name),
                    map?.hueBins ?: 1,map?.saturationBins ?: 1,map?.valueBins ?: 1)
            }
            dims("uHueSatDims",plan.hueSat);dims("uLookDims",plan.look)
            listOf("uSensorToProfile","uProfileToLinearSrgb").forEachIndexed { index,name ->
                val matrix=if(index==0)plan.sensorToProfileRows else plan.profileToLinearSrgbRows
                for(row in 0..2)GLES30.glUniform3f(loc(program,"${name}$row"),
                    matrix[row*3],matrix[row*3+1],matrix[row*3+2])
            }
            GLES30.glViewport(0,0,plan.width,plan.height)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gpu.checkGl("C isolated SDR and measured pre-tone HDR color")
            successful=true
            return Result.owned(images[0],images[1],plan.width,plan.height,plan.physicalCameraId,
                referenceSnr,sharpenAttenuation)
        } finally {
            if(program>0)GLES30.glDeleteProgram(program)
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(fbo>0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
            if(lookups.any { it>0 }) GLES30.glDeleteTextures(4,lookups,0)
            if(!successful && images.any { it>0 }) GLES30.glDeleteTextures(2,images,0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,unpackBuffer)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,unpackAlign)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,unpackRowLength)
            state.restore()
        }
    }
    /** Original RawEngineTonePass.hdrBaseCurveFragmentShader, Adobe/no-DCP only. */
    private fun measureDonorAdobeNeutralCurveOnGpu(
        acr3Texture: Int,
        outputRows: FloatArray,
        exposure: Iris26975CDonorProfileExposure.Frozen,
    ): FloatArray {
        require(acr3Texture > 0 && outputRows.size == 9 &&
            outputRows.all(Float::isFinite))
        val ids = IntArray(1)
        val oldPackBuffer=gpu.glInt(GLES30.GL_PIXEL_PACK_BUFFER_BINDING)
        val oldPackAlign=gpu.glInt(GLES30.GL_PACK_ALIGNMENT)
        val oldPackRows=gpu.glInt(GLES30.GL_PACK_ROW_LENGTH)
        var program=0;var fbo=0;var target=0;var vao=0
        try {
            program=gpu.compileProgram(gpu.VERTEX,
                Iris26972CColorDevelopShaders.donorAdobeNeutralMeasure)
            GLES30.glGenTextures(1,ids,0);target=ids[0]
            GLES30.glGenFramebuffers(1,ids,0);fbo=ids[0]
            GLES30.glGenVertexArrays(1,ids,0);vao=ids[0]
            check(program>0 && fbo>0 && target>0 && vao>0 &&
                acr3Texture != target) { "$COMPONENT GPU donor neutral F16 allocation failed" }
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,target)
            textureParams()
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT,1,0,
                GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,null)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,target,0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$COMPONENT original donor HDR neutral F16 framebuffer unsupported"
            }
            GLES30.glBindVertexArray(vao)
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glViewport(0,0,RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT,1)
            GLES30.glUseProgram(program)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,acr3Texture)
            GLES30.glUniform1i(loc(program,"uNeutralAcr3"),0)
            GLES30.glUniform1i(loc(program,"uNeutralToneEnabled"),
                if (exposure.toneEnabled) 1 else 0)
            GLES30.glUniform1f(loc(program,"uNeutralToneSlope"),exposure.toneSlope)
            GLES30.glUniform1f(loc(program,"uNeutralToneA"),exposure.toneA)
            GLES30.glUniform1f(loc(program,"uNeutralToneB"),exposure.toneB)
            GLES30.glUniform1f(loc(program,"uNeutralToneC"),exposure.toneC)
            for(row in 0..2) GLES30.glUniform3f(loc(program,"uNeutralOutputRow$row"),
                outputRows[row*3],outputRows[row*3+1],outputRows[row*3+2])
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gpu.checkGl("C original donor GPU-neutral render")
            GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,fbo)
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,0)
            val pixelBuffer=ByteBuffer.allocateDirect(
                RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT*4*4)
                .order(ByteOrder.nativeOrder())
            GLES30.glReadPixels(0,0,RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT,1,
                GLES30.GL_RGBA,GLES30.GL_FLOAT,pixelBuffer)
            gpu.checkGl("C original donor GPU-neutral F16 readback")
            val rgba=pixelBuffer.asFloatBuffer()
            val result=FloatArray(RawHdrReferenceMath.BASE_CURVE_SAMPLE_COUNT) { i ->
                val measured=rgba.get(i*4)
                require(measured.isFinite() && measured>=0f) {
                    "$COMPONENT invalid actual donor neutral GPU sample $i"
                }
                measured
            }
            require(result.last()>0f) { "$COMPONENT donor HDR neutral GPU curve is blank" }
            return result
        } finally {
            if(program>0)GLES30.glDeleteProgram(program)
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(fbo>0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
            if(target>0)GLES30.glDeleteTextures(1,intArrayOf(target),0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER,oldPackBuffer)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,oldPackAlign)
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH,oldPackRows)
        }
    }

    private fun textureParams() {
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_NEAREST)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
    }
    private fun uploadLut(id:Int,values:FloatArray,w:Int,h:Int,internal:Int,format:Int) {
        require(values.size.toLong()==w.toLong()*h*(if(format==GLES30.GL_RGB)3 else 1))
        val buffer=ByteBuffer.allocateDirect(values.size*4).order(ByteOrder.nativeOrder())
            .asFloatBuffer().apply { put(values);position(0) }
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        textureParams()
        if (internal == GLES30.GL_R16F) {
            // Pinned RawCurveTextureResources uses GL_R16F, not GL_R32F.
            // Its GPU half rounding is part of the donor ACR3 pixel contract.
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,
                GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
        }
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,internal,w,h,0,format,GLES30.GL_FLOAT,buffer)
    }
    private fun loc(program:Int,name:String):Int = GLES30.glGetUniformLocation(program,name).also {
        check(it>=0){"$COMPONENT required shader uniform was optimized out: $name"}
    }
}
