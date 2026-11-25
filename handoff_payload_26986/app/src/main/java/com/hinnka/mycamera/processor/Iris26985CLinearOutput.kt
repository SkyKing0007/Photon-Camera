// SPDX-License-Identifier: GPL-3.0-or-later
package com.hinnka.mycamera.processor

import android.content.ContentValues
import android.content.Context
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CaptureRequest
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.params.ColorSpaceTransform
import android.os.Build
import android.provider.MediaStore
import com.hinnka.mycamera.processor.experimentc.lkr2420.*
import com.particlesdevs.photoncamera.processing.MotionBatch
import com.particlesdevs.photoncamera.util.SimpleStorageHelper
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.file.Files
import java.nio.file.Path

/** One synchronous camera-linear buffer owner. DNG is written before display-domain GL transport. */
class Iris26985CLinearOutput internal constructor(
    private val context: Context, private val characteristics: CameraCharacteristics,
    private val batch: MotionBatch, private val destination: Path?,
) {
    var dngSaved=false
        private set
    private var consumed=false
    private val physical= requireNotNull(batch.iris26524OwnerCameraId)
    private fun capture(ts:Long):CaptureResult {
        val frame=batch.frames.single { it.timestamp==ts }
        require(frame.motionV2PhysicalCameraId==physical && frame.motionV2ResultSensorTimestampNs==ts)
        val total=requireNotNull(batch.results[ts]) { "Missing exact LKR reference metadata" }
        require(total.get(CaptureResult.SENSOR_TIMESTAMP)==ts)
        val result=if(Build.VERSION.SDK_INT>=28) total.physicalCameraResults[physical] ?: total else total
        require(result.get(CaptureResult.SENSOR_TIMESTAMP)==ts)
        return result
    }
    fun actualExposure(ts:Long):Float {
        val result=capture(ts)
        val t=requireNotNull(result.get(CaptureResult.SENSOR_EXPOSURE_TIME))
        val iso=requireNotNull(result.get(CaptureResult.SENSOR_SENSITIVITY))
        require(t>0L && iso>0)
        return (t.toDouble()*iso/1e9).toFloat().also{require(it.isFinite()&&it>0f)}
    }
    fun sensorWhite(ts:Long):Float {
        val result=capture(ts)
        val white=result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL)
            ?: characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL)
            ?: error("LKR exact physical white unavailable")
        require(white in 2..65535)
        return white.toFloat()
    }
    fun referenceWb(ts:Long):FloatArray {
        val result=capture(ts)
        val neutral=result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT)?.map { it.toDouble() }
        if(neutral!=null && neutral.size==3 && neutral.all{it.isFinite() && it>0.0}) {
            return floatArrayOf((neutral[1]/neutral[0]).toFloat(),1f,(neutral[1]/neutral[2]).toFloat())
                .also { require(it.all{v->v.isFinite()&&v>0f&&v<=64f}) }
        }
        // RawLens LkrMerge uses unity when neutral metadata is unavailable.
        return floatArrayOf(1f,1f,1f)
    }
    private fun matrix(t:ColorSpaceTransform?):ImmutableDoubleValues?=t?.let { m ->
        ImmutableDoubleValues(DoubleArray(9){m.getElement(it/3,it%3).toDouble()})
    }
    fun consume(rgb:ByteBuffer,w:Int,h:Int,ts:Long,wb:FloatArray,cfa:Int,selected:Int,accepted:Int,white:Float,stats:FloatArray) {
        check(!consumed);consumed=true
        val result=capture(ts)
        val f=batch.frames.single{it.timestamp==ts}
        val pixels=rgb.duplicate().order(ByteOrder.nativeOrder()).asFloatBuffer()
        require(pixels.capacity()>=Math.multiplyExact(Math.multiplyExact(w,h),3))
        val shading=result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP)
        if(shading!=null) {
            val a=characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE)
                ?: characteristics.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE)
                ?: error("LKR reference shading without active array")
            val gains=FloatArray(shading.gainFactorCount);shading.copyGainFactors(gains,0)
            val model=LensShadingModel(shading.rowCount,shading.columnCount,gains,IntRectSnapshot(a.left,a.top,a.right,a.bottom),
                characteristics.get(CameraCharacteristics.SENSOR_INFO_LENS_SHADING_APPLIED)==true)
            LkrLensShading.applyShadingMapped(pixels,w,h,model,0,f.iris26985CRawCropY,.5f,.5f,wb,white)
        }
        if(destination==null)return
        try {
            val neutral=ImmutableDoubleValues(doubleArrayOf(1.0/wb[0],1.0,1.0/wb[2]))
            val cm1=requireNotNull(matrix(characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1)))
            require(cm1.toDoubleArray().all(Double::isFinite))
            val noise=result.get(CaptureResult.SENSOR_NOISE_PROFILE)?.let{p->ImmutableDoubleValues(DoubleArray(p.size*2){i->if(i%2==0)p[i/2].first else p[i/2].second})}
            val metadata=RawFrameMetadata(cameraId=physical,exifOrientation=when(batch.rotation){90->6;180->3;270->8;else->1},
                sensitivityIso=f.motionV2ActualIso,exposureTimeNanos=f.motionV2ActualExposureNs,
                cfaPattern=BayerPattern.fromCamera2(cfa),blackLevels=ImmutableFloatValues(f.motionV2BlackLevel),
                whiteLevel=f.motionV2WhiteLevel.toFloat().takeIf{f.motionV2WhiteLevelValid&&it>0f}
                    ?:characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL)?.toFloat(),
                neutralColorPoint=neutral,colorMatrix1=cm1,
                colorMatrix2=matrix(characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2)),
                cameraCalibration1=matrix(characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1)),
                cameraCalibration2=matrix(characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2)),
                forwardMatrix1=matrix(characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1)),
                forwardMatrix2=matrix(characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2)),
                referenceIlluminant1=characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)?.toInt(),
                referenceIlluminant2=characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)?.toInt(),
                noiseProfile=noise,aperture=result.get(CaptureResult.LENS_APERTURE),focalLengthMm=result.get(CaptureResult.LENS_FOCAL_LENGTH),
                focusDistanceM=result.get(CaptureResult.LENS_FOCUS_DISTANCE)?.takeIf{it>0f}?.let{1f/it},
                flashFired=result.get(CaptureResult.FLASH_STATE)?.let{it==CaptureResult.FLASH_STATE_FIRED||it==CaptureResult.FLASH_STATE_PARTIAL},
                aeMode=result.get(CaptureResult.CONTROL_AE_MODE),awbMode=result.get(CaptureResult.CONTROL_AWB_MODE),
                exposureCompensationEv=result.get(CaptureResult.CONTROL_AE_EXPOSURE_COMPENSATION)?.let{s->characteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP)?.toDouble()?.times(s)},
                compositeSourceCount=selected,compositeUsedCount=accepted)
            val provenance=MergeProvenance("RawLens 2.4.20 / b8de711d",selected,accepted,selected-accepted,ts,2,physical,
                shading!=null || characteristics.get(CameraCharacteristics.SENSOR_INFO_LENS_SHADING_APPLIED)==true,
                effectiveFrames=accepted.toDouble(),engineLabel="LK-R Lite",
                details="Iris Experiment C Super Res ON; full sensor reconstruction; effective frames=accepted count (RawLens LK-R convention, not measured noise support); native stats=${stats.joinToString()}")
            val gps=batch.referenceRequest.get(CaptureRequest.JPEG_GPS_LOCATION)?.let{loc->GpsLocation(loc.latitude,loc.longitude,loc.altitude.takeIf{loc.hasAltitude()},loc.time)}
            publish(destination) { stream ->
                LinearRgbDngWriter.writeStriped(stream,w,h,metadata,provenance,gps,
                    captureTimeMillis=f.iris26985CCaptureWallTimeMillis.takeIf{it>0},white=white) { y,rows,band ->
                    val src=pixels.duplicate();src.position(y*w*3);src.get(band,0,rows*w*3)
                }
            }
            dngSaved=true
        } catch(failure:Exception) {
            com.particlesdevs.photoncamera.util.Log.e("Iris26985CLinear","C ON LK-R DNG publication failed",failure)
        }
    }
    private fun publish(path:Path,write:(java.io.OutputStream)->Unit) {
        if(Build.VERSION.SDK_INT>=29) {
            val resolver=context.contentResolver
            val values=ContentValues().apply {
                put(MediaStore.Images.Media.DISPLAY_NAME,path.fileName.toString())
                put(MediaStore.Images.Media.MIME_TYPE,"image/x-adobe-dng")
                put(MediaStore.Images.Media.RELATIVE_PATH,"DCIM/Camera")
                put(MediaStore.Images.Media.IS_PENDING,1)
            }
            val uri=requireNotNull(resolver.insert(MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),values))
            try {
                requireNotNull(resolver.openOutputStream(uri,"w")).buffered(1024*1024).use(write)
                values.clear();values.put(MediaStore.Images.Media.IS_PENDING,0)
                check(resolver.update(uri,values,null,null)==1)
            } catch(t:Throwable) { runCatching{resolver.delete(uri,null,null)};throw t }
        } else {
            val parent=path.toAbsolutePath().parent;Files.createDirectories(parent)
            val temp=Files.createTempFile(parent,".iris26985-",".tmp")
            try { Files.newOutputStream(temp).buffered(1024*1024).use(write);Files.move(temp,path) }
            finally { Files.deleteIfExists(temp) }
        }
    }
}
