package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Isolated C-only RAW color development of the *pre-SDR-clamp* donor Sabre camera RGB.
 *
 * This stage consumes actual immutable Camera2/DNG-calibrated matrices passed by its
 * owner, the pinned 1025-sample Adobe ACR3 curve, and actual optional donor-style DCP
 * tables. It creates two truly distinct outputs: encoded sRGB SDR for real RAISR and
 * scene-linear extended sRGB before Adobe/SDR clamping for a measured gainmap.
 *
 * It is NOT a producer of camera profiles. The isolated Camera2 capture owner MUST supply a
 * real shutter-frozen dual-illuminant D50 matrix solution for POST-donor-Resolve
 * camera RGB. The donor's final RGB gains have ALREADY been applied; the C
 * matrix must not apply as-shot WB a second time. Reject ambiguous metadata. No A/B classes are called.
 * No processing path may use the normalized donor U16 `texture` as the HDR source.
 * Source-wired to C-only shutter and publishing, but production-gated and not device-proven.
 */
internal object Iris26972CColorDeveloper {
    private const val COMPONENT = "26972 C independent RAW color"
    private val gpu = Iris26972CDonorSabreGpuMerge

    internal class ProfileMap(
        val hueBins: Int, val saturationBins: Int, val valueBins: Int,
        /** RGB triplets in x=saturation, y=value*hueBins+hue row order. */
        val values: FloatArray,
    ) {
        internal fun validate() {
            val count = hueBins.toLong() * saturationBins * valueBins
            require(hueBins in 2..360 && saturationBins in 2..256 && valueBins in 1..256 &&
                count in 1..2_000_000 && values.size.toLong() == count * 3 &&
                values.all { it.isFinite() }) {
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
        val hueSat: ProfileMap? = null,
        val look: ProfileMap? = null,
    )

    internal class Result private constructor(
        val encodedSrgbTexture: Int,
        val sceneLinearHdrTexture: Int,
        val width: Int, val height: Int,
        val physicalCameraId: String,
        private val owner: EGLContext,
    ) : AutoCloseable {
        private var released = false
        internal fun requireOwner() {
            check(!released && owner != EGL14.EGL_NO_CONTEXT &&
                owner == EGL14.eglGetCurrentContext()) { "$COMPONENT wrong EGL owner" }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(2, intArrayOf(encodedSrgbTexture,sceneLinearHdrTexture), 0)
            released = true
        }
        companion object {
            internal fun owned(sdr: Int,hdr: Int,width: Int,height: Int,lens: String):Result =
                Result(sdr,hdr,width,height,lens,EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan: Plan) {
        require(plan.width in 16..16384 && plan.height in 16..16384 &&
            (plan.width and 1)==0 && (plan.height and 1)==0 &&
            plan.physicalCameraId.isNotBlank() &&
            plan.calibrationProvenance == "CAMERA2_DNG_POST_DONOR_WB_ONCE" &&
            plan.sensorToProfileRows.size == 9 &&
            plan.profileToLinearSrgbRows.size == 9 &&
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
        plan.hueSat?.validate()
        plan.look?.validate()
        check(Iris26972CAdobeAcr3.size == 1025) {
            "$COMPONENT pinned donor ACR3 samples unavailable"
        }
    }

    internal fun develop(
        plan: Plan,
        sabre: Iris26972CDonorSabreGpuResolve.Result,
    ): Result {
        validate(plan)
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
            gpu.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS)>=4 &&
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
        val lookups=IntArray(3)
        try {
            program=gpu.compileProgram(gpu.VERTEX,Iris26972CColorDevelopShaders.color)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
            GLES30.glGenTextures(2,images,0)
            GLES30.glGenTextures(3,lookups,0)
            check(images.all { it>0 } && lookups.all { it>0 } &&
                (images.toList()+lookups.toList()+sabre.texture+
                    sabre.extendedCameraRgbTexture).toSet().size==7) {
                "$COMPONENT duplicate C color texture name"
            }
            images.forEach { id ->
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
                textureParams()
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                    plan.width,plan.height,0,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,null)
            }
            uploadLut(lookups[0], Iris26972CAdobeAcr3.samples(),1025,1,
                GLES30.GL_R32F,GLES30.GL_RED)
            uploadLut(lookups[1],plan.hueSat?.values ?: floatArrayOf(0f,1f,1f),
                plan.hueSat?.saturationBins ?: 1,
                (plan.hueSat?.hueBins ?: 1)*(plan.hueSat?.valueBins ?: 1),
                GLES30.GL_RGB32F,GLES30.GL_RGB)
            uploadLut(lookups[2],plan.look?.values ?: floatArrayOf(0f,1f,1f),
                plan.look?.saturationBins ?: 1,
                (plan.look?.hueBins ?: 1)*(plan.look?.valueBins ?: 1),
                GLES30.GL_RGB32F,GLES30.GL_RGB)
            gpu.checkGl("C authentic Adobe/DCP LUT upload")
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
            val sources=intArrayOf(sabre.extendedCameraRgbTexture,lookups[0],lookups[1],lookups[2])
            val names=arrayOf("uExtendedCameraRgb","uAdobeAcr3","uHueSatMap","uLookMap")
            sources.forEachIndexed { index, id ->
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0+index)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
                GLES30.glUniform1i(loc(program,names[index]),index)
            }
            GLES30.glUniform1i(loc(program,"uAcr3Size"),1025)
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
            return Result.owned(images[0],images[1],plan.width,plan.height,plan.physicalCameraId)
        } finally {
            if(program>0)GLES30.glDeleteProgram(program)
            if(vao>0)GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(fbo>0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0)
            if(lookups.any { it>0 }) GLES30.glDeleteTextures(3,lookups,0)
            if(!successful && images.any { it>0 }) GLES30.glDeleteTextures(2,images,0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,unpackBuffer)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,unpackAlign)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,unpackRowLength)
            state.restore()
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
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,internal,w,h,0,format,GLES30.GL_FLOAT,buffer)
    }
    private fun loc(program:Int,name:String):Int = GLES30.glGetUniformLocation(program,name).also {
        check(it>=0){"$COMPONENT required shader uniform was optimized out: $name"}
    }
}
