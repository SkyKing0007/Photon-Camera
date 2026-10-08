package com.hinnka.mycamera.processor

import com.hinnka.mycamera.model.SafeImage
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings

enum class RawBurstFrameRole {
    NORMAL,
    HIGHLIGHT_SHORT,
    SHADOW_LONG,
    HDR_SHORT,
    HDR_LONG,
}

data class RawStackFrame(
    val image: SafeImage,
    val sensorTimestampNs: Long = image.timestamp,
    val frameNumber: Long = -1L,
    val exposureTimeNs: Long = 0L,
    val sensitivityIso: Int = 0,
    val exposureProduct: Double = 1.0,
    val desiredExposureProduct: Double? = null,
    val focusDistanceDiopters: Float = Float.NaN,
    val lensState: Int? = null,
    /* IRIS_26754_EXACT_PHYSICAL_CAMERA_ID */
    val physicalCameraId: String? = null,
    val rollingShutterSkewNs: Long? = null,
    val channelNoiseProfile: FloatArray? = null,
    val dynamicBlackLevelByCfaPosition: FloatArray? = null,
    /* IRIS_26720_NORMAL_CONFIDENCE_METADATA
     * Read-only NORMAL confidence inputs. No source sample or exposure authority is transferred.
     */
    val rowFlickerHarmonic: Int = 0,
    val rowFlickerA: Float = 0f,
    val rowFlickerB: Float = 0f,
    val rowFlickerStrength: Float = 0f,
    val gyroShakiness: Float = Float.NaN,
    val gyroSampleCount: Int = 0,
    val dngOptions26786: IrisMotionSettings.DngOptions.Snapshot = IrisMotionSettings.DngOptions.defaults(),
    val role: RawBurstFrameRole = RawBurstFrameRole.NORMAL,
)
