package com.hinnka.mycamera.processor

import android.graphics.ImageFormat
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.media.Image
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.util.Collections
import java.util.IdentityHashMap

/**
 * C-only lifecycle boundary for real Camera2 RAW_SENSOR Images + matching
 * TotalCaptureResults. Consumes RAW Images on entry and releases each exactly
 * once on BOTH successful and unsuccessful staging. Never reorders the frozen
 * shutter reference, guesses metadata, or returns an escaped Image plane after
 * the synchronous callback closes. This alternate C-only synchronous owner is
 * not used by the active disk-spool source route and never touches A/B callbacks.
 *
 * The reference green SNR is measured from the ORIGINAL physical RAW16 plane;
 * lens shading, DNG matrices, and all frame exposure/noise come from the same
 * sensor's actual completed Camera2 results.
 */
internal object Iris26972CPhysicalShutterOwner {
    private const val COMPONENT="26972 C physical Camera2 RAW image owner"

    internal data class Pairing(val image:Image,val total:TotalCaptureResult)
    internal class Frozen internal constructor(
        private val images:List<Image>,
        private val burst:Iris26972CDonorSabreGpuBurst.Plan,
        private val calibration:Iris26972CCamera2Calibration.Frozen,
        private val lensShading:Iris26972CPhysicalLensShading.Frozen,
        val measuredReferenceSnr:Float,
        val sourceFrameCount:Int,
    ):AutoCloseable {
        private var closed=false
        private var entered=false
        /**
         * The callback is synchronous by contract: all camera-owned native
         * buffers remain live until it returns, then every Image is closed.
         */
        internal fun <T> withFrozenBurst(
            block:(Iris26972CDonorSabreGpuBurst.Plan,
                Iris26972CCamera2Calibration.Frozen,
                Iris26972CPhysicalLensShading.Frozen)->T,
        ):T {
            check(!closed && !entered) {"$COMPONENT stale or repeated RAW lease"}
            entered=true
            return block(burst,calibration,lensShading)
        }
        override fun close() {
            check(!closed) {"$COMPONENT double close"}
            closed=true
            closeUnique(images)
        }
    }

    private fun closeUnique(images:List<Image>) {
        val seen=Collections.newSetFromMap(IdentityHashMap<Image,Boolean>())
        var cause:Throwable?=null
        for(image in images) if(seen.add(image)) {
            try{image.close()}catch(failure:Throwable){
                if(cause==null) cause=failure else cause.addSuppressed(failure)
            }
        }
        if(cause!=null)throw cause
    }

    internal fun acquire(
        cameraManager:CameraManager,
        logicalCameraId:String,
        physicalCameraId:String,
        shutter:Iris26972CContract.Plan,
        pairs:List<Pairing>,
    ):Frozen {
        // This method TAKES ownership immediately. Even pre-admission failure
        // must release each supplied Image; never strand RAW HAL buffers.
        val owned=pairs.map{it.image}
        var accepted=false
        try {
            require(pairs.size==shutter.frameCount && pairs.size in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
                shutter.physicalLensId==physicalCameraId &&
                logicalCameraId.isNotBlank() && physicalCameraId.isNotBlank()) {
                "$COMPONENT shutter RAW count/physical sensor mismatch"
            }
            val seen=Collections.newSetFromMap(IdentityHashMap<Image,Boolean>())
            require(owned.all {seen.add(it)}) {"$COMPONENT repeated Camera2 Image owner"}
            val frames=ArrayList<Iris26972CDonorSabreGpuBurst.Frame>(pairs.size)
            var ref:Iris26972CPhysicalRawMetadata.Frozen?=null
            var refPlane:Iris26972CDonorSabreGpuRawIngress.Plane?=null
            val sources=ArrayList<Pair<Iris26972CPhysicalRawMetadata.Frozen,
                Iris26972CDonorSabreGpuRawIngress.Plane>>(pairs.size)
            val frameNumbers=HashSet<Long>()
            val timestamps=HashSet<Long>()
            for((index,pair) in pairs.withIndex()) {
                val image=pair.image
                require(image.format==ImageFormat.RAW_SENSOR &&
                    image.width in 16..16384 && image.height in 16..16384 &&
                    image.planes.size==1 && image.timestamp>0L) {
                    "$COMPONENT expected one actual live RAW_SENSOR plane"
                }
                val crop=image.cropRect
                val source=image.planes.single()
                val plane=Iris26972CDonorSabreGpuRawIngress.Plane(
                    source.buffer, image.width,image.height,
                    source.rowStride,source.pixelStride,
                    crop.left,crop.top,crop.width(),crop.height())
                Iris26972CDonorSabreGpuRawIngress.validate(plane)
                val meta=Iris26972CPhysicalRawMetadata.freezeFromTotal(
                    cameraManager,logicalCameraId,physicalCameraId,pair.total)
                require(image.timestamp==meta.sensorTimestampNs &&
                    timestamps.add(image.timestamp) && frameNumbers.add(meta.frameNumber) &&
                    (index!=0 || image.timestamp==shutter.referenceTimestampNs)) {
                    "$COMPONENT RAW Image and physical Camera2 timestamps do not match"
                }
                sources += meta to plane
                if(index==0) {ref=meta;refPlane=plane}
            }
            val reference=checkNotNull(ref)
            val rawReference=checkNotNull(refPlane)
            val measured=Iris26972CMeasuredRawSnr.measure(reference,rawReference)
            for((meta,plane) in sources) {
                frames+=meta.toBurstFrame(reference,plane,measured.referenceSnr,pairs.size)
            }
            val finalWhiteBalance=reference.copyCanonicalWbForAudit()
            val appliedGains=floatArrayOf(1f/finalWhiteBalance[0],1f,1f/finalWhiteBalance[3])
            val resolveScale=maxOf((16384f/(reference.sensorWhiteLevel+1f)).toInt(),1)
            val scaledWhite=reference.sensorWhiteLevel.toLong()*resolveScale
            require(scaledWhite in 1..32767) {
                "$COMPONENT MGC 14-bit Resolve sensor white overflow"
            }
            val burst=Iris26972CDonorSabreGpuBurst.Plan(
                frames,shutter.referenceTimestampNs,
                Iris26972CDonorSabreGpuResolve.Plan(
                    reference.cfaPattern,pairs.size,measured.referenceSnr,
                    null,reference.exposureProduct,scaledWhite.toInt(),appliedGains,0))
            Iris26972CDonorSabreGpuBurst.validate(burst,metadataOnly=true)
            Iris26972CContract.validateBurst(shutter,
                frames.map { Iris26972CContract.Role.valueOf(it.role.name) },
                frames.map {it.sensorTimestampNs}, frames.map {it.exposureProduct})
            val firstTotal=pairs.first().total
            val color=Iris26972CCamera2Calibration.freezeFromTotalCaptureResult(
                cameraManager,logicalCameraId,physicalCameraId,firstTotal,
                shutter.referenceTimestampNs,appliedGains)
            val shading=Iris26972CPhysicalLensShading.freezeFromTotal(
                logicalCameraId,physicalCameraId,firstTotal,shutter.referenceTimestampNs)
            color.colorPlan(burst.rawWidth,burst.rawHeight,burst)
            accepted=true
            return Frozen(owned,burst,color,shading,measured.referenceSnr,pairs.size)
        } finally {
            if(!accepted) closeUnique(owned)
        }
    }
}
