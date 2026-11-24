package com.hinnka.mycamera.processor

import android.content.Context
import android.graphics.Bitmap
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.GLES30
import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.api.ParseExif
import com.particlesdevs.photoncamera.processing.ImageSaver
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.Iris26983COnPostPipeline
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
import com.particlesdevs.photoncamera.processing.render.Parameters
import java.nio.file.Path

/** Synchronous C ON merge -> guide transfer -> post -> private publication owner.
 * Caller must be the serialized capture processor, with exclusive capture-local Parameters,
 * exact physical RAW/metadata, frozen tone and EXIF, and no current EGL context.
 * RAW ownership remains with caller until this returns. Only all-NORMAL JPEG/HEIC Motion is
 * supported by the current implementation; no DNG, LONG or Night fallback is provided.
 * No live capture route invokes this owner yet. Do not select it until capture parity is closed.
 */
object GlesIris26983COnPipeline {
    private const val TAG = "Iris26983COnPipeline"

    @JvmStatic
    fun execute(
        app: Context, frames: List<RawStackFrame>, expectedPhysical: String,
        expectedNormals: Int, referenceNumber: Long, referenceTimestamp: Long,
        referenceBlack: FloatArray, sensorWhite: Int, parameters: Parameters,
        tone: IrisMotionSettings.Snapshot, clipYFloor: Float,
        alternativeHighlight: Boolean, previewP995: Float, highlightCompression: Boolean,
        watermark: Boolean, aspect169: Boolean, energySaving: Boolean,
        output: Path, heic: Boolean, exif: ParseExif.ExifData,
    ): Boolean {
        require(parameters.iris26983COnSelected && !parameters.iris26906ExperimentBSelected &&
            parameters.motionV2Active && parameters.motionV2SuperResOutputEnabled &&
            !parameters.irisNightActive && !parameters.iris26983COnNight)
        val raw = requireNotNull(parameters.rawSize)
        val w = raw.x; val h = raw.y; val cfa = parameters.cfaPattern.toInt()
        require(w >= 64 && h >= 64 && w % 2 == 0 && h % 2 == 0 && cfa in 0..3)
        require(expectedPhysical.isNotBlank() && expectedNormals in 2..24 && frames.size == expectedNormals)
        require(frames.all { it.role == RawBurstFrameRole.NORMAL && it.physicalCameraId == expectedPhysical &&
            it.sensorTimestampNs > 0 && it.exposureProduct.isFinite() && it.exposureProduct > 0.0 })
        require(frames.map { it.sensorTimestampNs }.distinct().size == frames.size)
        require(frames.count { it.frameNumber == referenceNumber && it.sensorTimestampNs == referenceTimestamp } == 1)
        require(referenceBlack.size == 4 && sensorWhite > 0 && referenceBlack.all { it.isFinite() && it >= 0f && it < sensorWhite })
        require(clipYFloor.isFinite() && clipYFloor > 0f)
        require(parameters.cameraRotation in listOf(0,90,180,270))
        require(parameters.motionV2ReconstructionZoom == 1f && parameters.motionV2SpatialReconstructionZoom == 1f)
        check(EGL14.eglGetCurrentContext() == EGL14.EGL_NO_CONTEXT) { "26983 C ON must not replace a live GL context" }
        val wb = parameters.motionV2ColorGains?.copyOf()
            ?.takeIf { it.size >= 4 && it.take(4).all { v -> v.isFinite() && v > 0f } }
            ?: floatArrayOf(1f, 1f, 1f, 1f)
        val color = GlesIris26983COnColorContract.freeze(wb,parameters.motionV2ColorTransform.copyOf(),parameters.motionV2DirectColorValid)
        val exactClipWb = calculationWhiteBalance26836(wb)
        val lsc = parameters.gainMap?.copyOf()?.takeIf { values ->
            val map = parameters.mapSize
            map != null && map.x > 0 && map.y > 0 && values.size.toLong() == map.x.toLong()*map.y*4 &&
                values.all { it.isFinite() && it > 0f }
        }
        val lscWidth = if(lsc!=null) parameters.mapSize.x else 0
        val lscHeight = if(lsc!=null) parameters.mapSize.y else 0
        val frozenFrames=frames.toList()
        var carriers: GlesIris26983COnGuidePublication.Prepared?=null
        var true2x: Iris26983COnRgba16fCarrier?=null
        var bitmap: Bitmap?=null
        var saved=false
        try {
            MergeEgl.create().use {
                GlesIris26983COnGpuMerge(app,w,h,cfa,lsc,lscWidth,lscHeight).run(
                    frozenFrames,referenceNumber,referenceTimestamp,referenceBlack.copyOf(),sensorWhite,color,
                    alternativeHighlight,previewP995
                ).use { merge ->
                    val prepared=GlesIris26983COnGuidePublication.prepare(merge,w,h)
                    carriers=prepared
                    true2x=merge.takeTrue2x()
                    // B's primary is unselected; only the separate color sidecar reaches post.
                    prepared.primary.close()
                }
            }
            check(EGL14.eglGetCurrentContext()==EGL14.EGL_NO_CONTEXT)
            val prepared=checkNotNull(carriers)
            val packed=checkNotNull(true2x)
            check(packed.width==Math.multiplyExact(w,2) && packed.height==Math.multiplyExact(h,2) &&
                prepared.final1x.width==w && prepared.final1x.height==h)
            // Exact native B identity and lower-bound support diagnostic; no Sabre noise math.
            parameters.motionV2MgcSourceExposureGain=1f
            parameters.motionV2DisplayGain=1f
            parameters.motionV2ShortHighlightRecoveryExecuted=false
            parameters.motionV2ShortRadianceAuthorityMask=null
            parameters.motionV2ShortRadianceAuthorityWidth=0
            parameters.motionV2ShortRadianceAuthorityHeight=0
            parameters.motionV2EffectiveSupport=1f
            parameters.motionV2EdgeSuppressAll26792=tone.edgeFalseColorAllEdges26792
            parameters.motionV2SdrBodyContrast26792=tone.sdrBodyContrast26792
            parameters.prepareCOnPublication26983()
            val post=Iris26983COnPostPipeline()
            try {
                val preview=prepared.sidecar.consume { cpu,shared ->
                    post.runCOn(cpu,shared,parameters,tone,highlightCompression,watermark,aspect169,energySaving)
                }
                bitmap=preview
                check(!preview.isRecycled)
                saved=if(heic) ImageSaver.Util.saveC26983SuperResGpuHeic(output,preview,98,exif,packed,
                    prepared.final1x,parameters,post.cropSize,tone,watermark,exactClipWb,clipYFloor)
                else ImageSaver.Util.saveC26983SuperResGpuJpeg(output,preview,98,exif,packed,
                    prepared.final1x,parameters,post.cropSize,tone,watermark,exactClipWb,clipYFloor)
                check(saved) { "26983 C ON private publication failed; no 1x fallback" }
            } finally {
                // Final renderer restores post EGL before post's close. A durable save must
                // not become an apparent failed save due only to terminal cleanup telemetry.
                if(saved) runCatching { post.close() }.onFailure { PLog.e(TAG,"post close after save",it) }
                else post.close()
            }
            return true
        } finally {
            try { bitmap?.let { if(!it.isRecycled) it.recycle() } } finally {
                try { carriers?.close() } finally { true2x?.close() }
            }
        }
    }

    // Byte-for-byte arithmetic of the proven B clip-zone WB calculation (not the
    // double-precision temporary-WB preparation used for LKR and Lab).
    internal fun calculationWhiteBalance26836(wb: FloatArray): FloatArray {
        fun safeGain(channel: Int, fallback: Float): Float = wb.getOrElse(channel) { fallback }
            .takeIf { it.isFinite() && it > 0f } ?: fallback
        val greenEven = safeGain(1, 1f)
        val greenOdd = safeGain(2, greenEven)
        val greenBase = (0.5f * (greenEven + greenOdd)).takeIf { it.isFinite() && it > 0f } ?: 1f
        fun relative(v: Float) = (v / greenBase).coerceIn(1.0e-3f, 64f)
        return floatArrayOf(relative(safeGain(0, greenBase)), 1f, relative(safeGain(3, greenBase)))
    }

    private class MergeEgl(private val display:EGLDisplay,private val context:EGLContext,
                           private val surface:EGLSurface):AutoCloseable {
        private var closed=false
        companion object {
            fun create():MergeEgl {
                val display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
                check(display!=EGL14.EGL_NO_DISPLAY)
                val versions=IntArray(2)
                check(EGL14.eglInitialize(display,versions,0,versions,1))
                var context=EGL14.EGL_NO_CONTEXT
                var surface=EGL14.EGL_NO_SURFACE
                try {
                    val attrs=intArrayOf(EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,
                        EGL14.EGL_ALPHA_SIZE,8,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_PBUFFER_BIT,
                        EGL14.EGL_RENDERABLE_TYPE,0x40,EGL14.EGL_NONE)
                    val configs=arrayOfNulls<EGLConfig>(1); val count=IntArray(1)
                    check(EGL14.eglChooseConfig(display,attrs,0,configs,0,1,count,0) && count[0]>0)
                    val config=checkNotNull(configs[0])
                    context=GlesGpuScheduler.createBackgroundContext(display,config,TAG)
                    check(context!=EGL14.EGL_NO_CONTEXT)
                    surface=EGL14.eglCreatePbufferSurface(display,config,intArrayOf(EGL14.EGL_WIDTH,1,EGL14.EGL_HEIGHT,1,EGL14.EGL_NONE),0)
                    check(surface!=EGL14.EGL_NO_SURFACE)
                    check(EGL14.eglMakeCurrent(display,surface,surface,context))
                    return MergeEgl(display,context,surface)
                } catch(t:Throwable) {
                    if(surface!=EGL14.EGL_NO_SURFACE) EGL14.eglDestroySurface(display,surface)
                    if(context!=EGL14.EGL_NO_CONTEXT) EGL14.eglDestroyContext(display,context)
                    EGL14.eglTerminate(display)
                    throw t
                }
            }
        }
        override fun close() {
            if(closed)return
            closed=true
            try { GLES30.glFinish() } finally {
                try { check(EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT)) }
                finally {
                    try { EGL14.eglDestroySurface(display,surface) } finally {
                        try { EGL14.eglDestroyContext(display,context) } finally { EGL14.eglTerminate(display) }
                    }
                }
            }
        }
    }
}
