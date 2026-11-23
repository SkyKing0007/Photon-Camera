package com.hinnka.mycamera.processor.experimentc

import com.hinnka.mycamera.processor.experimentc.original129.model.SafeImage
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawBurstFrameRole
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackFrame
import java.util.ArrayList

/**
 * Exact original bjzhou GlesMgcRawSpatialStacker.processFrames() input schema.
 *
 * Iris acquires real RAW_SENSOR and Camera2 data; the original engine, not
 * this adapter, decides alignment, Sabre fusion, noise, RAW development and
 * output. Every frame is NORMAL with the original physical exposure; no
 * synthetic A/B image, YUV merge, or Camera2 noise-model substitute is used.
 */
internal object Iris26975CDonorStackFrameAdapter {
    private fun canonicalIndexBySensorPhase(cfa: Int): IntArray = when (cfa) {
        0 -> intArrayOf(0, 1, 2, 3) // RGGB
        1 -> intArrayOf(1, 0, 3, 2) // GRBG
        2 -> intArrayOf(2, 3, 0, 1) // GBRG
        3 -> intArrayOf(3, 2, 1, 0) // BGGR
        else -> throw IllegalArgumentException("Original donor only accepts 2x2 Bayer RAW")
    }

    fun toOriginalDonorFrames(burst: Iris26975COriginalRawBurst): List<RawStackFrame> {
        val result = ArrayList<RawStackFrame>(burst.frames.size)
        try {
            for (frame in burst.frames) {
                val metadata = frame.metadata
                require(metadata.physicalCameraId == burst.physicalCameraId &&
                    frame.rawWidth == burst.rawWidth && frame.rawHeight == burst.rawHeight &&
                    metadata.exposureProduct.isFinite() && metadata.exposureProduct > 0.0) {
                    "C original Sabre frame cross-lens or nonphysical RAW"
                }
                val (shot, read) = metadata.copyCanonicalNoiseForAudit()
                val black = metadata.copyCanonicalBlackForAudit()
                require(shot.size == 4 && read.size == 4 && black.size == 4)
                val phase = canonicalIndexBySensorPhase(metadata.cfaPattern)
                // Original RawNoiseModel.fromCamera2NoiseProfile receives 4 (S,O)
                // pairs in sensor CFA *phase* order, never canonical R/Gr/Gb/B.
                val pairs = FloatArray(8) { index ->
                    val canonical = phase[index / 2]
                    if (index % 2 == 0) shot[canonical] else read[canonical]
                }
                val dynamicBlack = FloatArray(4) { black[phase[it]] }
                require(pairs.all { it.isFinite() && it >= 0f } &&
                    dynamicBlack.all { it.isFinite() && it >= 0f } &&
                    metadata.exposureTimeNs > 0L && metadata.sensitivityIso > 0)
                val image = SafeImage.fromOriginalFrame(frame)
                result += RawStackFrame(
                    image = image,
                    sensorTimestampNs = metadata.sensorTimestampNs,
                    frameNumber = metadata.frameNumber,
                    exposureTimeNs = metadata.exposureTimeNs,
                    sensitivityIso = metadata.sensitivityIso,
                    minimumSensitivityIso = metadata.minimumSensitivityIso,
                    maximumAnalogSensitivityIso = metadata.maximumAnalogSensitivityIso,
                    focusDistanceDiopters = metadata.focusDistanceDiopters,
                    lensState = metadata.lensState,
                    rollingShutterSkewNs = metadata.rollingShutterSkewNs,
                    exposureProduct = metadata.exposureProduct,
                    channelNoiseProfile = pairs,
                    dynamicBlackLevelByCfaPosition = dynamicBlack,
                    role = RawBurstFrameRole.NORMAL,
                    // No synthetic desired TET, lens state, gyro or prealignment.
                    desiredExposureProduct = null,
                    preAlignmentToReference = null,
                )
            }
            return result
        } catch (failure: Throwable) {
            result.forEach { it.image.close() }
            throw failure
        }
    }

    internal inline fun <T> withOriginalDonorFrames(
        burst: Iris26975COriginalRawBurst,
        block: (List<RawStackFrame>) -> T,
    ): T {
        val frames = toOriginalDonorFrames(burst)
        try { return block(frames) }
        finally { frames.forEach { it.image.close() } }
    }
}
