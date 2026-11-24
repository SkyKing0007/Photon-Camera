package com.hinnka.mycamera.processor

import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CameraCharacteristics
import com.hinnka.mycamera.model.SafeImage
import com.particlesdevs.photoncamera.api.ParseExif
import com.particlesdevs.photoncamera.processing.ImageFrame
import com.particlesdevs.photoncamera.processing.MotionBatch
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnCapturePreparation
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
import com.particlesdevs.photoncamera.processing.render.Parameters
import java.nio.file.Path

/** Independent C ON adapter for the neutral immutable MotionBatch transport.
 * The future C capture planner must supply the exact shutter-requested count and C-marked
 * physical frames. No B owner call or relabeling. This borrows already-owned RAW planes;
 * the existing batch executor remains the sole ImageFrame owner. JPEG Photo only (MotionBatch forbids SR+HEIC);
 * never consume a DNG or auxiliary frame by dropping it. Not yet an active dispatch site.
 */
object GlesIris26983COnMotionIngress {
    /** Prepare exact B-equivalent sensor metadata using C's own owner, never C OFF.
     * The shutter executor must supply the immutable exact NORMAL count and owned reference.
     */
    @JvmStatic
    fun executePreparedMotion(app: Context, characteristics: CameraCharacteristics, batch: MotionBatch,
            expectedNormals: Int, shutterReferenceTimestamp: Long, tone: IrisMotionSettings.Snapshot,
            clipYFloor: Float, highlightCompression: Boolean, watermark: Boolean, aspect169: Boolean,
            energySaving: Boolean, output: Path, exif: ParseExif.ExifData): Boolean {
        val prepared = Iris26983COnCapturePreparation.prepare(characteristics, batch)
        require(prepared.referenceTimestamp == shutterReferenceTimestamp) { "26983 C ON reference ownership mismatch" }
        return executeFrozenMotion(app,batch,expectedNormals,prepared.referenceTimestamp,prepared.parameters,
            tone,clipYFloor,highlightCompression,watermark,aspect169,energySaving,output,exif)
    }

    @JvmStatic
    fun executeFrozenMotion(app: Context, batch: MotionBatch, expectedNormals: Int,
            referenceTimestamp: Long, parameters: Parameters, tone: IrisMotionSettings.Snapshot,
            clipYFloor: Float, highlightCompression: Boolean, watermark: Boolean, aspect169: Boolean,
            energySaving: Boolean, output: Path, exif: ParseExif.ExifData): Boolean {
        require(batch.superResEnabled && !batch.heicOutputEnabled && batch.imageFormat==ImageFormat.RAW_SENSOR)
        require(parameters.iris26983COnSelected && !parameters.iris26906ExperimentBSelected &&
            parameters.motionV2Active && parameters.motionV2SuperResOutputEnabled &&
            !parameters.irisNightActive && !parameters.iris26983COnNight)
        require(batch.frames.size==expectedNormals && batch.processingFrameCount==expectedNormals &&
            batch.totalFrameCount==expectedNormals && batch.candidateCount==expectedNormals &&
            batch.retainedCount==expectedNormals && expectedNormals in 2..24)
        val slot=batch.shortHighlightSlot
        require(slot!=null && slot.requiredFreezeComplete() && !slot.shortWasExpected() &&
            !slot.shadowWasExpected() && !slot.hasFrame() && !slot.shadowAuxSlot.hasFrame())
        val physical=requireNotNull(batch.iris26524OwnerCameraId)
        require(physical.isNotBlank())
        val raw=requireNotNull(parameters.rawSize)
        val frames=batch.frames.toList()
        val reference=frames.singleOrNull { it.timestamp==referenceTimestamp }
            ?: error("26983 C ON exact shutter-owned NORMAL is absent")
        require(reference.buffer!=null)
        val ordered=Iris26983COnCapturePreparation.order(batch,referenceTimestamp)
        require(ordered.size==expectedNormals && ordered.map{it.frame.timestamp}.distinct().size==expectedNormals)
        require(parameters.cfaPattern.toInt() in 0..3)
        val white=if(reference.motionV2WhiteLevelValid && reference.motionV2WhiteLevel>0) reference.motionV2WhiteLevel else parameters.whiteLevel
        require(white>0)
        val positionalBlack=parameters.blackLevel.copyOfRange(0,4)
        // Validate the entire batch before borrowing any plane, including exact physical result identity.
        ordered.forEach { entry ->
            val frame=entry.frame
            require(frame.motionV2ReconstructionExperiment26856=="C" && frame.motionV2PhysicalCameraId==physical &&
                frame.motionV2FrameRole==ImageFrame.MotionV2FrameRole.NORMAL && !frame.motionV2ShortHighlightFrame)
            require(frame.timestamp>0L && frame.motionV2ResultSensorTimestampNs==frame.timestamp && frame.motionV2FrameNumber>=0L)
            require(frame.motionV2PlaneLayoutValid && !frame.motionV2PlaneTransformedByBinning &&
                frame.motionV2PlaneFormat==ImageFormat.RAW_SENSOR && frame.motionV2PlaneLogicalWidth==raw.x &&
                frame.motionV2PlaneLogicalHeight==raw.y && frame.motionV2PlanePixelStrideBytes==2 &&
                frame.motionV2PlaneRowStrideBytes>=raw.x*2 && frame.motionV2PlaneRowStrideBytes%2==0)
            val bytes=(raw.y.toLong()-1L)*frame.motionV2PlaneRowStrideBytes+raw.x.toLong()*2L
            val buffer=requireNotNull(frame.buffer) { "26983 C Photo ON requires in-memory immutable RAW" }
            require(buffer.isDirect && buffer.capacity().toLong()>=bytes)
            require(frame.motionV2ActualExposureNs>0L && frame.motionV2ActualIso>0 &&
                frame.motionV2ExposureEnergy.isFinite() && frame.motionV2ExposureEnergy>0.0)
            require(frame.motionV2BlackLevelValid && frame.motionV2BlackLevel.size==4 &&
                frame.motionV2BlackLevel.all{it.isFinite() && it>=0f && it<white})
        }
        val stack=ordered.map { entry ->
            val frame=entry.frame
            val image=SafeImage(width=raw.x,height=raw.y,format=frame.motionV2PlaneFormat,timestamp=frame.timestamp,
                buffer=requireNotNull(frame.buffer),rowStride=frame.motionV2PlaneRowStrideBytes,
                pixelStride=frame.motionV2PlanePixelStrideBytes,closeAction=null)
            RawStackFrame(image=image,sensorTimestampNs=frame.motionV2ResultSensorTimestampNs,
                frameNumber=frame.motionV2FrameNumber,exposureTimeNs=frame.motionV2ActualExposureNs,
                sensitivityIso=frame.motionV2ActualIso,exposureProduct=frame.motionV2ExposureEnergy,
                desiredExposureProduct=null,focusDistanceDiopters=frame.motionV2FocusDistanceDiopters,
                lensState=frame.motionV2LensState.takeIf{it>=0},physicalCameraId=frame.motionV2PhysicalCameraId,
                rollingShutterSkewNs=frame.motionV2RollingShutterSkewNs.takeIf{it>0L},
                verifiedHotPixelCoordinates26855=frame.motionV2VerifiedHotPixels26855.copyOf(),
                channelNoiseProfile=if(tone.customNoiseModelEnabled) null else entry.noise.copyOf(),
                dynamicBlackLevelByCfaPosition=frame.motionV2BlackLevel.copyOf(),
                rowFlickerHarmonic=if(frame.motionV2RowFlickerValid)frame.motionV2RowFlickerHarmonic else 0,
                rowFlickerA=if(frame.motionV2RowFlickerValid)frame.motionV2RowFlickerA else 0f,
                rowFlickerB=if(frame.motionV2RowFlickerValid)frame.motionV2RowFlickerB else 0f,
                rowFlickerStrength=if(frame.motionV2RowFlickerValid)frame.motionV2RowFlickerStrength else 0f,
                gyroShakiness=entry.gyro.shakiness.takeIf{it.isFinite()&&it>=0f}?:Float.NaN,
                gyroSampleCount=entry.gyro.samples,dngOptions26786=batch.dngOptions26786,
                role=RawBurstFrameRole.NORMAL)
        }
        try {
            // B Photo selects the actual reference protection, no C OFF highlight/exposure state.
            parameters.motionCanonicalExposureGain=1f
            parameters.motionV2ReferenceProtectionEv=reference.motionV2ReferenceProtectionEv.coerceIn(0f,1.50f)
            parameters.motionV2SpatialReconstructionZoom=1f
            parameters.motionV2ReconstructionZoom=1f
            parameters.motionV2RenderResidualZoom=parameters.motionV2OutputZoom.takeIf{it.isFinite()}?.coerceAtLeast(1f)?:1f
            return GlesIris26983COnPipeline.execute(app,stack,physical,expectedNormals,reference.motionV2FrameNumber,
                referenceTimestamp,positionalBlack,white,parameters,tone,clipYFloor,
                reference.motionV2AlternativeHighlight26912,reference.motionV2PreviewHighlightP99526912,
                highlightCompression,watermark,aspect169,energySaving,output,batch.heicOutputEnabled,exif)
        } finally {
            // SafeImage only releases its borrowing wrapper, never the ImageFrame bytes.
            stack.asReversed().forEach{it.image.close()}
        }
    }

    internal fun canonicalBlack(positional: FloatArray,cfa:Int):FloatArray {
        require(positional.size>=4 && cfa in 0..3)
        val phaseToCanonical=when(cfa){1->intArrayOf(1,0,3,2);2->intArrayOf(2,3,0,1);3->intArrayOf(3,2,1,0);else->intArrayOf(0,1,2,3)}
        return FloatArray(4).also{out->phaseToCanonical.forEachIndexed{phase,canonical->
            val value=positional[phase];require(value.isFinite()&&value>=0f);out[canonical]=value
        }}
    }
}
