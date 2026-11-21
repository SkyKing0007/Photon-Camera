package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30

/**
 * C-owned original donor Bayer/Sabre sqrt-domain guide and covariance MRT producer.
 * Requires an extracted RAW16 Bayer texture and true donor QMC noise-estimates LUT;
 * never substitutes synthetic or A/B noise. No output publication is possible here.
 */
internal object Iris26972CDonorSabreGpuGuide {
    private const val COMPONENT = "26972 C donor Sabre guide/covariance"
    private val gl = Iris26972CDonorSabreGpuMerge
    private const val BORDER = 2.5f

    internal data class Frame(
        val extractedBayerTexture: Int,
        val qmcNoiseTexture: Int,
        val gains: FloatArray,
        val blackLevelsTimesGains: FloatArray,
        val greenClippingPoint: Float,
    )
    internal data class Plan(
        val rawWidth: Int,
        val rawHeight: Int,
        val cfaPattern: Int,
        val referenceSnr: Float,
        val frozenFrameCount: Int,
        val frame: Frame,
        val mergeGradientThreshold: Float? = null,
    ) {
        val guideWidth: Int get() = rawWidth / 2
        val guideHeight: Int get() = rawHeight / 2
    }
    internal class Result private constructor(
        val guideTexture: Int,
        val covarianceTexture: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        private val context: EGLContext,
    ) : AutoCloseable {
        private var released = false
        internal fun requireOwner() {
            check(!released && context != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext() == context) {
                "$COMPONENT wrong GL ownership"
            }
        }
        override fun close() {
            requireOwner()
            GLES30.glDeleteTextures(2,intArrayOf(guideTexture,covarianceTexture),0)
            released = true
        }
        internal companion object {
            fun owned(g: Int,c: Int,w: Int,h: Int) = Result(g,c,w,h,EGL14.eglGetCurrentContext())
        }
    }

    internal fun validate(plan: Plan) {
        require(plan.rawWidth in 16..16384 && plan.rawHeight in 16..16384 &&
            plan.rawWidth % 2 == 0 && plan.rawHeight % 2 == 0) {
            "$COMPONENT requires even native Bayer dimensions"
        }
        require(plan.cfaPattern in 0..3 && plan.frozenFrameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
            plan.referenceSnr.isFinite() && plan.referenceSnr >= 0f &&
            (plan.mergeGradientThreshold == null ||
                plan.mergeGradientThreshold.isFinite() && plan.mergeGradientThreshold > 0f)) {
            "$COMPONENT invalid capture-frozen CFA/kernel metadata"
        }
        require(plan.frame.extractedBayerTexture > 0 && plan.frame.qmcNoiseTexture > 0 &&
            plan.frame.extractedBayerTexture != plan.frame.qmcNoiseTexture &&
            plan.frame.gains.size == 4 && plan.frame.blackLevelsTimesGains.size == 4 &&
            plan.frame.gains.all { it.isFinite() && it > 0f } &&
            plan.frame.blackLevelsTimesGains.all { it.isFinite() } &&
            plan.frame.greenClippingPoint.isFinite() && plan.frame.greenClippingPoint > 0f) {
            "$COMPONENT missing donor extracted RAW16, QMC LUT or sensor calibration"
        }
    }

    internal fun process(plan: Plan): Result {
        validate(plan)
        gl.requireCurrentContext()
        require(gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= plan.rawWidth &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) >= plan.rawHeight &&
            gl.glInt(GLES30.GL_MAX_COLOR_ATTACHMENTS) >= 2 &&
            gl.glInt(GLES30.GL_MAX_DRAW_BUFFERS) >= 2 &&
            gl.glInt(GLES30.GL_MAX_TEXTURE_IMAGE_UNITS) >= 2) {
            "$COMPONENT GL MRT/texture limits unsupported"
        }
        val params = Iris26972CDonorSabreKernelTuning.build(
            plan.referenceSnr,plan.frozenFrameCount,plan.mergeGradientThreshold)
        val previous=Iris26972CDonorSabreGpuMerge.GlState.capture()
        val textures=IntArray(2)
        var program=0
        var framebuffer=0
        var vao=0
        var success=false
        try {
            program=gl.compileProgram(gl.VERTEX,
                Iris26972CDonorSabreGuideShaders.guideAndCovariance)
            GLES30.glGenTextures(2,textures,0)
            check(textures.all { it > 0 && it != plan.frame.extractedBayerTexture &&
                it != plan.frame.qmcNoiseTexture } && textures[0]!=textures[1]) {
                "$COMPONENT texture allocation/alias failure"
            }
            texture(textures[0],plan.guideWidth,plan.guideHeight,GLES30.GL_RGBA16F,
                GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT)
            texture(textures[1],plan.guideWidth,plan.guideHeight,GLES30.GL_RGB10_A2,
                GLES30.GL_RGBA,GLES30.GL_UNSIGNED_INT_2_10_10_10_REV)
            val fbos=IntArray(1)
            GLES30.glGenFramebuffers(1,fbos,0)
            framebuffer=fbos[0]
            val vaos=IntArray(1)
            GLES30.glGenVertexArrays(1,vaos,0)
            vao=vaos[0]
            check(framebuffer>0 && vao>0) { "$COMPONENT VAO/FBO allocation failed" }
            GLES30.glBindVertexArray(vao)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,framebuffer)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,textures[0],0)
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT1,
                GLES30.GL_TEXTURE_2D,textures[1],0)
            GLES30.glDrawBuffers(2,intArrayOf(GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_COLOR_ATTACHMENT1),0)
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==
                GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$COMPONENT donor guide/covariance MRT unsupported"
            }
            GLES30.glDisable(GLES30.GL_BLEND)
            GLES30.glDisable(GLES30.GL_DEPTH_TEST)
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
            GLES30.glColorMask(true,true,true,true)
            GLES30.glUseProgram(program)
            bind(program,"uExtractedBayer",0,plan.frame.extractedBayerTexture)
            bind(program,"uNoiseEstimates",1,plan.frame.qmcNoiseTexture)
            uniform2i(program,"uGuideSize",plan.guideWidth,plan.guideHeight)
            uniform4f(program,"uFrameBorderPadded",BORDER/plan.rawWidth,
                BORDER/plan.rawHeight,1f-BORDER/plan.rawWidth,1f-BORDER/plan.rawHeight)
            uniform1i(program,"uCfaPattern",plan.cfaPattern)
            uniform4fv(program,"uGains",plan.frame.gains)
            uniform4fv(program,"uBlackLevelsTimesGains",plan.frame.blackLevelsTimesGains)
            uniform4f(program,"uNoiseTextureScaleBias",.9f,.5f,.05f,.25f)
            uniform4fv(program,"uCovarianceParameters1",params.covarianceParameters1)
            uniform4fv(program,"uCovarianceParameters2",params.covarianceParameters2)
            uniform4f(program,"uCovRangeRgFactors",
                offset(params.covarianceMinR,params.covarianceMaxR),
                scale(params.covarianceMinR,params.covarianceMaxR),
                offset(params.covarianceMinG,params.covarianceMaxG),
                scale(params.covarianceMinG,params.covarianceMaxG))
            GLES30.glUniform2f(location(program,"uCovRangeBFactor"),
                offset(params.covarianceMinB,params.covarianceMaxB),
                scale(params.covarianceMinB,params.covarianceMaxB))
            GLES30.glUniform1f(location(program,"uGreenClippingPoint"),
                plan.frame.greenClippingPoint)
            uniform4f(program,"uForceReferenceColorRgb",
                if(params.forceReferenceColorRgb) 1f else 0f,0f,0f,0f)
            GLES30.glViewport(0,0,plan.guideWidth,plan.guideHeight)
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3)
            gl.checkGl("donor guide/covariance MRT render")
            success=true
            return Result.owned(textures[0],textures[1],plan.rawWidth,plan.rawHeight)
        } finally {
            if(program>0) GLES30.glDeleteProgram(program)
            if(framebuffer>0) GLES30.glDeleteFramebuffers(1,intArrayOf(framebuffer),0)
            if(vao>0) GLES30.glDeleteVertexArrays(1,intArrayOf(vao),0)
            if(!success) {
                val live=textures.filter { it>0 }.toIntArray()
                if(live.isNotEmpty()) GLES30.glDeleteTextures(live.size,live,0)
            }
            previous.restore()
        }
    }

    private fun location(p:Int,n:String) = GLES30.glGetUniformLocation(p,n).also {
        check(it>=0) { "$COMPONENT missing donor uniform $n" }
    }
    private fun bind(p:Int,n:String,u:Int,t:Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0+u)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,t)
        GLES30.glUniform1i(location(p,n),u)
    }
    private fun uniform1i(p:Int,n:String,v:Int)=GLES30.glUniform1i(location(p,n),v)
    private fun uniform2i(p:Int,n:String,x:Int,y:Int)=GLES30.glUniform2i(location(p,n),x,y)
    private fun uniform4fv(p:Int,n:String,v:FloatArray)=GLES30.glUniform4fv(location(p,n),1,v,0)
    private fun uniform4f(p:Int,n:String,x:Float,y:Float,z:Float,w:Float)=
        GLES30.glUniform4f(location(p,n),x,y,z,w)
    private fun scale(min:Float,max:Float)=1f/(max-min)
    private fun offset(min:Float,max:Float)=-min/(max-min)
    private fun texture(id:Int,w:Int,h:Int,storage:Int,format:Int,type:Int) {
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,storage,w,h,0,format,type,null)
        gl.checkGl("donor Sabre guide MRT texture allocation")
    }
}
