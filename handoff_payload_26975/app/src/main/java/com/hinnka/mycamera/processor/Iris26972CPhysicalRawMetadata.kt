package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcAlignmentInputScale
import com.hinnka.mycamera.processor.experimentc.Iris26975CDonorCamera2Noise
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.hardware.camera2.params.BlackLevelPattern
import android.hardware.camera2.params.RggbChannelVector
import android.os.Build
import kotlin.math.abs

/**
 * Strict C-only real Camera2 per-physical-lens RAW exposure, CFA, WB, noise and
 * black-level snapshot. Conversion equations are the pinned bjzhou 1.29.0
 * `GlesMgcRawSpatialStacker.calibrationForFrame`, `RawNoiseModel`, and
 * `MgcAlignmentInputScale`: Camera2 S/O is already sensor-normalized; QMC
 * scales by WB/exposure, while RAW16 unblocker needs S/O in sensor DN units.
 *
 * No invented noise model, 0.18 proxy signal, synthetic white level, logical
 * camera fallback, YUV fallback, or auto A/B dispatch. The physical RAW
 * ImageReader owner/shutter callbacks are source-wired, but NOT Android-build or device-proven.
 */
internal object Iris26972CPhysicalRawMetadata {
    private const val COMPONENT = "26972 C actual per-physical-Camera2 RAW metadata"

    internal class Frozen private constructor(
        val physicalCameraId:String,
        val frameNumber:Long,
        val sensorTimestampNs:Long,
        val exposureTimeNs:Long,
        val sensitivityIso:Int,
        /** Actual physical Camera2 ISO bounds; unknown remains zero. */
        val minimumSensitivityIso:Int,
        val maximumAnalogSensitivityIso:Int,
        /** Actual per-frame focus, lens state, and readout timing; never guessed. */
        val focusDistanceDiopters:Float,
        val lensState:Int?,
        val rollingShutterSkewNs:Long?,
        val cfaPattern:Int,
        val sensorWhiteLevel:Int,
        blacks:FloatArray,
        shot:FloatArray,
        read:FloatArray,
        whiteBalance:FloatArray,
    ) {
        private val canonicalBlack=blacks.copyOf()
        private val canonicalShot=shot.copyOf()
        private val canonicalRead=read.copyOf()
        private val canonicalWhiteBalance=whiteBalance.copyOf()
        val exposureProduct:Double get() = exposureTimeNs.toDouble()*sensitivityIso.toDouble()
        internal fun copyCanonicalNoiseForAudit():Pair<FloatArray,FloatArray> =
            canonicalShot.copyOf() to canonicalRead.copyOf()
        internal fun copyCanonicalBlackForAudit():FloatArray = canonicalBlack.copyOf()
        internal fun copyCanonicalWbForAudit():FloatArray = canonicalWhiteBalance.copyOf()

        /**
         * Binds an actual *live direct RAW16* plane to its matching physical
         * frame metadata. Caller owns plane and must keep it alive until the
         * synchronous GPU upload has completed. No copy or readback here.
         * `referenceSnr` must be measured from this shutter's RAW reference.
         */
        internal fun toBurstFrame(
            reference:Frozen,
            plane:Iris26972CDonorSabreGpuRawIngress.Plane,
            referenceSnr:Float,
            frozenNormalCount:Int,
        ):Iris26972CDonorSabreGpuBurst.Frame {
            require(reference.physicalCameraId == physicalCameraId &&
                reference.cfaPattern == cfaPattern &&
                reference.sensorWhiteLevel == sensorWhiteLevel &&
                reference.sensorTimestampNs > 0L &&
                sensorTimestampNs > 0L && frameNumber>=0L &&
                referenceSnr.isFinite() && referenceSnr >= 0f &&
                frozenNormalCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES) { "$COMPONENT stale/cross-sensor reference" }
            val scale=(reference.exposureProduct/exposureProduct).toFloat()
            require(scale.isFinite() && scale>0f && abs(scale-1f)<=.01f) {
                "$COMPONENT donor Sabre cannot accept physical exposure bracket"
            }
            Iris26972CDonorSabreGpuRawIngress.validate(plane)
            val gains=FloatArray(4)
            val blackTerms=FloatArray(4)
            val shot=FloatArray(4)
            val read=FloatArray(4)
            val unblockShot=FloatArray(4)
            val unblockRead=FloatArray(4)
            val refShot=FloatArray(4)
            val refRead=FloatArray(4)
            for (c in 0..3) {
                // Same frozen physical white balance for all NORMAL frames.
                val wb=reference.canonicalWhiteBalance[c]
                val referenceRelative=wb
                val relativeGain=wb*scale
                val range=sensorWhiteLevel.toFloat()-canonicalBlack[c]
                require(range>0f && range.isFinite()) { "$COMPONENT invalid physical black/white" }
                gains[c]=relativeGain/range
                blackTerms[c]=-canonicalBlack[c]*gains[c]
                shot[c]=canonicalShot[c]*relativeGain
                read[c]=canonicalRead[c]*relativeGain*relativeGain
                refShot[c]=reference.canonicalShot[c]*referenceRelative
                refRead[c]=reference.canonicalRead[c]*referenceRelative*referenceRelative
                // RAW16 unblocker shader consumes *sensor code values*, not
                // normalized QMC values or post-WB noise.
                unblockShot[c]=canonicalShot[c]*range
                unblockRead[c]=canonicalRead[c]*range*range
            }
            // Exact pinned donor calibrationForFrame FP32 evaluation order.
            // Squaring once before each RGB coefficient multiply is NOT
            // bitwise equivalent to multiplying by scale twice.
            val exposureScaleSquared=scale*scale
            val greenClip=.5f*((sensorWhiteLevel*gains[1]+blackTerms[1])+
                (sensorWhiteLevel*gains[2]+blackTerms[2]))
            val alignScale=MgcAlignmentInputScale.compute(scale,sensorWhiteLevel.toFloat())
            require(gains.all{it.isFinite()&&it>0f} &&
                shot.all{it.isFinite()&&it>0f} &&
                read.all{it.isFinite()&&it>=0f} &&
                refShot.all{it.isFinite()&&it>0f} &&
                refRead.all{it.isFinite()&&it>=0f} &&
                unblockShot.all{it.isFinite()&&it>0f} &&
                unblockRead.all{it.isFinite()&&it>=0f} &&
                alignScale.isFinite()&&alignScale>0f&&alignScale<=64f &&
                greenClip.isFinite()&&greenClip>0f) {
                "$COMPONENT physical noise/WB calibration exceeds donor GPU limits"
            }
            return Iris26972CDonorSabreGpuBurst.Frame(
                role=Iris26972CDonorSabreGpuBurst.CaptureRole.NORMAL,
                physicalCameraId=physicalCameraId,
                frameNumber=frameNumber,
                sensorTimestampNs=sensorTimestampNs,
                exposureProduct=exposureProduct,
                raw=Iris26975COriginalSabreGpuPreparedFrame.Plan(
                    raw=plane,cfaPattern=cfaPattern,referenceSnr=referenceSnr,
                    frozenFrameCount=frozenNormalCount,
                    referenceShotNoise=refShot,referenceReadNoise=refRead,
                    currentShotNoise=shot,currentReadNoise=read,
                    gains=gains,blackLevelsTimesGains=blackTerms,
                    greenClippingPoint=greenClip,
                    mergeGradientThreshold=-1f, // pinned PhotonFusionTuning.DEFAULT
                ),
                sensorBlackLevels=canonicalBlack.copyOf(),
                alignmentGain=alignScale,
                unblockerShotNoise=unblockShot,
                unblockerReadNoise=unblockRead,
                // Pinned donor calibrationForFrame: camera RGB (R, mean(Gr,Gb), B)
                // noise must be un-white-balanced, normalized Camera2 S/O.
                // Shot scales with exposure ratio; read scales with ratio squared.
                cameraRgbShotNoise=floatArrayOf(
                    canonicalShot[0], .5f*(canonicalShot[1]+canonicalShot[2]),
                    canonicalShot[3]).map { it*scale }.toFloatArray(),
                cameraRgbReadNoise=floatArrayOf(
                    canonicalRead[0], .5f*(canonicalRead[1]+canonicalRead[2]),
                    canonicalRead[3]).map { it*exposureScaleSquared }.toFloatArray(),
            )
        }
        internal companion object {
            fun create(physical:String, frameNumber:Long, sensorTimestampNs:Long,
                exposureTimeNs:Long, sensitivityIso:Int, cfa:Int, white:Int,
                black:FloatArray, shot:FloatArray, read:FloatArray, wb:FloatArray,
                minimumSensitivityIso:Int=0, maximumAnalogSensitivityIso:Int=0,
                focusDistanceDiopters:Float=Float.NaN,
                lensState:Int?=null, rollingShutterSkewNs:Long?=null):Frozen {
                // Pinned RawNoiseModel.fromCamera2NoiseProfile clamps each
                // negative/nonfinite O coefficient to zero, retaining a Camera2
                // model only when all four S terms are positive and at least
                // one authentic O term remains. Reject missing noise instead
                // of synthesizing a replacement; Spatial's stricter Gr-read
                // rule does NOT apply to this classic Sabre pipeline.
                require(physical.isNotBlank()&&frameNumber>=0&&sensorTimestampNs>0&&
                    exposureTimeNs>0&&sensitivityIso>0&&cfa in 0..3&&white in 2..65535&&
                    black.size==4&&black.all{it.isFinite()&&it>=0f&&it<white}&&
                    shot.size==4&&read.size==4&&
                    wb.size==4&&wb.all{it.isFinite()&&it>0f&&it<=64f}&&
                    minimumSensitivityIso>=0&&maximumAnalogSensitivityIso>=0&&
                    (maximumAnalogSensitivityIso==0||minimumSensitivityIso==0||
                        maximumAnalogSensitivityIso>=minimumSensitivityIso)&&
                    (focusDistanceDiopters.isNaN()||
                        (focusDistanceDiopters.isFinite()&&focusDistanceDiopters>=0f))&&
                    (rollingShutterSkewNs==null||rollingShutterSkewNs>=0)) {
                    "$COMPONENT unusable actual Camera2 RAW noise/black/exposure/WB"
                }
                // Use the pinned original bjzhou RawNoiseModel, not Iris's A/B fork.
                val donor = Iris26975CDonorCamera2Noise.normalize(cfa,shot,read)
                return Frozen(physical,frameNumber,sensorTimestampNs,exposureTimeNs,
                    sensitivityIso,minimumSensitivityIso,maximumAnalogSensitivityIso,
                    focusDistanceDiopters,lensState,rollingShutterSkewNs,
                    cfa,white,black,donor.copyShot(),donor.copyRead(),wb)
            }
        }
    }

    /** Converts the actual Camera2 2x2 CFA phases into canonical [R,Gr,Gb,B]. */
    private fun phaseToCanonical(cfa:Int):IntArray=when(cfa){
        0->intArrayOf(0,1,2,3)
        1->intArrayOf(1,0,3,2)
        2->intArrayOf(2,3,0,1)
        3->intArrayOf(3,2,1,0)
        else->throw IllegalArgumentException("$COMPONENT unsupported non-Bayer CFA")
    }
    internal fun freezeFromTotal(
        manager:CameraManager, logicalId:String, physicalId:String,
        total:TotalCaptureResult,
    ):Frozen {
        require(logicalId.isNotBlank() && physicalId.isNotBlank() &&
            (logicalId==physicalId || Build.VERSION.SDK_INT>=28)) {
            "$COMPONENT no actual physical camera support"
        }
        val result:CaptureResult=if(logicalId==physicalId)total else
            total.physicalCameraResults[physicalId]
                ?:throw IllegalArgumentException("$COMPONENT missing physical exposure result")
        val characteristics=manager.getCameraCharacteristics(physicalId)
        return freeze(physicalId,total.frameNumber,characteristics,result)
    }

    internal fun freeze(physicalId:String, frameNumber:Long,
        characteristics:CameraCharacteristics,result:CaptureResult):Frozen {
        val ts=result.get(CaptureResult.SENSOR_TIMESTAMP)
        val exp=result.get(CaptureResult.SENSOR_EXPOSURE_TIME)
        val iso=result.get(CaptureResult.SENSOR_SENSITIVITY)
        val cfa=characteristics.get(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT)
        val white=characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL)
        val blacks:BlackLevelPattern=characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN)
            ?:throw IllegalArgumentException("$COMPONENT missing physical black level pattern")
        val rawNoise=result.get(CaptureResult.SENSOR_NOISE_PROFILE)
            ?:throw IllegalArgumentException("$COMPONENT missing real Camera2 S/O noise profile")
        val rgbGains:RggbChannelVector=result.get(CaptureResult.COLOR_CORRECTION_GAINS)
            ?:throw IllegalArgumentException("$COMPONENT missing real physical RGGB white balance")
        require(ts!=null&&exp!=null&&iso!=null&&cfa!=null&&white!=null&&
            cfa in 0..3&&rawNoise.size==4) {
            "$COMPONENT incomplete actual physical RAW metadata"
        }
        val phaseToCanonical=phaseToCanonical(cfa)
        val dynamicBlack=result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL)
            ?.takeIf { it.size==4&&it.all { v->v.isFinite()&&v>=0f&&v<white } }
        val black=FloatArray(4)
        val shot=FloatArray(4)
        val read=FloatArray(4)
        for (phase in 0..3) {
            val canonical=phaseToCanonical[phase]
            black[canonical]=dynamicBlack?.get(phase)
                ?:blacks.getOffsetForIndex(phase%2,phase/2).toFloat()
            // The pinned donor interprets Camera2 profile pairs in CFA-phase
            // order and does not apply a second sensor-domain normalization.
            shot[canonical]=rawNoise[phase].first?.toFloat() ?: Float.NaN
            read[canonical]=rawNoise[phase].second?.toFloat() ?: Float.NaN
            // Sanitization stays in Frozen.create so both Camera2 and host
            // snapshots use precisely the donor's normalized S/O contract.
        }
        // Android RggbChannelVector's greenEven/greenOdd are SENSOR ROW
        // phases. Canonical Gr is the green on a RED row, Gb the one on a
        // BLUE row. These swap for GBRG/BGGR, unlike RGGB/GRBG.
        val evenIsRedRow=cfa==0 || cfa==1
        val wb=floatArrayOf(rgbGains.red,
            if(evenIsRedRow)rgbGains.greenEven else rgbGains.greenOdd,
            if(evenIsRedRow)rgbGains.greenOdd else rgbGains.greenEven,
            rgbGains.blue)
        // No A/B capture-state guesses. Freeze actual physical sensor limits and
        // per-frame lens/readout metadata before the image owner releases HAL data.
        val sensitivityRange=characteristics.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE)
        val minimumIso=sensitivityRange?.lower?.takeIf { it>0 } ?: 0
        val maximumAnalog=characteristics.get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY)
            ?.takeIf { it>0 } ?: 0
        val focusDistance=result.get(CaptureResult.LENS_FOCUS_DISTANCE)
            ?.takeIf { it.isFinite() && it>=0f } ?: Float.NaN
        val lensState=result.get(CaptureResult.LENS_STATE)
        val rollingShutter=result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW)
            ?.takeIf { it>=0L }
        return Frozen.create(physicalId,frameNumber,ts,exp,iso,cfa,white,black,shot,read,wb,
            minimumIso,maximumAnalog,focusDistance,lensState,rollingShutter)
    }
}
