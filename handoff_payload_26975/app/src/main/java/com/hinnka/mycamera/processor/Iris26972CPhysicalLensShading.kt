package com.hinnka.mycamera.processor

import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.os.Build
import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Actual physical Camera2 LensShadingMap -> pinned donor's linear RGBA16F
 * RGGB/Gr/Gb/B bilinear texture. Where Camera2 supplies no LSC map,
 * bjzhou's RAW developer applies no lens correction; we bind a neutral
 * sampler without representing it as measured physical Camera2 metadata.
 * No buffer or GLES texture is created until the physical RAW reference matches.
 */
internal object Iris26972CPhysicalLensShading {
    private const val COMPONENT = "26972 C shutter-frozen physical RAW lens shading"
    private val gl = Iris26972CDonorSabreGpuMerge

    internal class Frozen private constructor(
        val physicalCameraId: String,
        val referenceTimestampNs: Long,
        val mapWidth: Int,
        val mapHeight: Int,
        val hasMeasuredMap: Boolean,
        values: FloatArray,
    ) {
        private val frozenValues = values.copyOf()
        internal fun copyValuesForHostAudit(): FloatArray = if (hasMeasuredMap)
            frozenValues.copyOf() else floatArrayOf() // no invented Camera2 map
        internal fun requireMatches(physical: String, timestampNs: Long) {
            require(physical == physicalCameraId && timestampNs == referenceTimestampNs) {
                "$COMPONENT physical RAW identity changed"
            }
        }
        /** Must be invoked on the same EGL thread as donor ResolveSabre. */
        internal fun allocate(): Texture {
            gl.requireCurrentContext()
            gl.checkGl("before C physical lens shading")
            val state=Iris26972CDonorSabreGpuMerge.GlState.capture()
            val unpackBuffer=gl.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
            val unpackAlign=gl.glInt(GLES30.GL_UNPACK_ALIGNMENT)
            val unpackRows=gl.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
            val ids=IntArray(1)
            var delivered=false
            try {
                require(mapWidth <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE) &&
                    mapHeight <= gl.glInt(GLES30.GL_MAX_TEXTURE_SIZE)) {
                    "$COMPONENT map exceeds hardware GL limits"
                }
                val data=ByteBuffer.allocateDirect(frozenValues.size * Float.SIZE_BYTES)
                    .order(ByteOrder.nativeOrder())
                for (value in frozenValues) data.putFloat(value)
                data.flip()
                GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,4)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glGenTextures(1,ids,0)
                check(ids[0] > 0) { "$COMPONENT texture allocation failed" }
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[0])
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA16F,
                    mapWidth,mapHeight,0,GLES30.GL_RGBA,GLES30.GL_FLOAT,data)
                gl.checkGl("physical RGGB lens map upload")
                delivered=true
                return Texture(ids[0],EGL14.eglGetCurrentContext())
            } finally {
                if(!delivered && ids[0] > 0) GLES30.glDeleteTextures(1,ids,0)
                GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,unpackBuffer)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,unpackAlign)
                GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,unpackRows)
                state.restore()
            }
        }
        internal companion object {
            fun create(physical:String,ts:Long,w:Int,h:Int,values:FloatArray,
                measured:Boolean=true):Frozen {
                require(physical.isNotBlank() && ts>0L && w in 1..256 && h in 1..256 &&
                    values.size.toLong() == w.toLong()*h*4L &&
                    values.all { it.isFinite() && it > 0f && it <= 64f }) {
                    "$COMPONENT invalid real RGGB lens shading matrix"
                }
                return Frozen(physical,ts,w,h,measured,values)
            }
        }
    }
    internal class Texture internal constructor(
        val id:Int, private val owner:EGLContext,
    ):AutoCloseable {
        private var closed=false
        override fun close() {
            check(!closed && id>0 && owner != EGL14.EGL_NO_CONTEXT &&
                EGL14.eglGetCurrentContext()==owner) {
                "$COMPONENT texture close requires original EGL owner"
            }
            GLES30.glDeleteTextures(1,intArrayOf(id),0)
            closed=true
        }
    }

    internal fun freezeFromTotal(
        logicalCameraId:String,
        physicalCameraId:String,
        total:TotalCaptureResult,
        referenceTimestampNs:Long,
    ):Frozen {
        require(logicalCameraId.isNotBlank() && physicalCameraId.isNotBlank()) {
            "$COMPONENT missing actual RAW camera identity"
        }
        require(logicalCameraId == physicalCameraId || Build.VERSION.SDK_INT >= 28) {
            "$COMPONENT physical result unsupported before Android 9"
        }
        val result:CaptureResult = if(logicalCameraId==physicalCameraId) total
            else total.physicalCameraResults[physicalCameraId]
                ?: throw IllegalArgumentException("$COMPONENT missing physical RAW result")
        return freeze(physicalCameraId,result,referenceTimestampNs)
    }

    /** Missing Camera2 LSC is an absent correction, not missing RAW provenance. */
    internal fun freeze(physicalCameraId:String,result:CaptureResult,
        referenceTimestampNs:Long):Frozen {
        require(physicalCameraId.isNotBlank() && referenceTimestampNs>0L &&
            result.get(CaptureResult.SENSOR_TIMESTAMP)==referenceTimestampNs) {
            "$COMPONENT actual physical RAW reference timestamp missing/mismatched"
        }
        val map=result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP)
            ?: return Frozen.create(physicalCameraId,referenceTimestampNs,
                1,1,floatArrayOf(1f,1f,1f,1f),measured=false)
        val w=map.columnCount
        val h=map.rowCount
        require(w in 1..256 && h in 1..256) { "$COMPONENT invalid Camera2 map shape" }
        val values=FloatArray(w*h*4)
        for (row in 0 until h) for(column in 0 until w) for(channel in 0..3) {
            values[(row*w+column)*4+channel]=map.getGainFactor(channel,column,row)
        }
        return Frozen.create(physicalCameraId,referenceTimestampNs,w,h,values)
    }
}
