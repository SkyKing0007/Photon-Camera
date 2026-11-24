package com.hinnka.mycamera.processor.experimentc

import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import com.hinnka.mycamera.processor.Iris26972CPhysicalRawMetadata
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs

/**
 * Camera2 -> ORIGINAL donor RAW ingress, independent of the reconstructed C
 * Sabre GPU plan, denoiser, color developer and JPEG/R writer.
 *
 * Every RAW16 plane has already been copied from ImageReader, SHA-256 checked,
 * and mmap'ed read-only by the C capture spool. The donor receives sensor RAW
 * samples and genuine per-frame physical Camera2 results, not preprocessed RGB.
 * The caller may only use these mappings during its synchronous spool lease.
 */
internal class Iris26975COriginalRawBurst private constructor(
    val physicalCameraId: String,
    val referenceTimestampNs: Long,
    val frames: List<Frame>,
) {
    internal class Frame internal constructor(
        val metadata: Iris26972CPhysicalRawMetadata.Frozen,
        val totalCaptureResult: TotalCaptureResult,
        val physicalCaptureResult: CaptureResult,
        val sensorWidth: Int,
        val sensorHeight: Int,
        val cropLeft: Int,
        val cropTop: Int,
        val rawWidth: Int,
        val rawHeight: Int,
        raw16: ByteBuffer,
    ) {
        private val rawSource: ByteBuffer = raw16.asReadOnlyBuffer().order(ByteOrder.nativeOrder())
        val rawByteCount: Int = Math.multiplyExact(Math.multiplyExact(rawWidth, rawHeight), 2)

        init {
            require(rawWidth in 16..16384 && rawHeight in 16..16384 &&
                rawWidth % 2 == 0 && rawHeight % 2 == 0 &&
                sensorWidth >= rawWidth && sensorHeight >= rawHeight &&
                cropLeft >= 0 && cropTop >= 0 &&
                cropLeft + rawWidth <= sensorWidth && cropTop + rawHeight <= sensorHeight &&
                cropLeft % 2 == 0 && cropTop % 2 == 0 &&
                rawSource.isReadOnly && rawSource.remaining() == rawByteCount) {
                "C donor needs real, even-origin packed RAW16 from its physical sensor"
            }
        }

        /** A fresh independent read-only cursor; no A/B image or GPU buffer escape. */
        fun raw16(): ByteBuffer = rawSource.asReadOnlyBuffer().order(ByteOrder.nativeOrder())
    }

    val rawWidth: Int get() = frames.first().rawWidth
    val rawHeight: Int get() = frames.first().rawHeight
    val reference: Frame get() = frames.first()

    fun validateAgainst(shutter: Iris26972CContract.Plan) {
        require(shutter.physicalLensId == physicalCameraId &&
            shutter.referenceTimestampNs == referenceTimestampNs &&
            shutter.frameCount == frames.size &&
            frames.size in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
            reference.metadata.sensorTimestampNs == referenceTimestampNs) {
            "C donor RAW reference/slider/physical-lens identity mismatch"
        }
        val seenTimestamps = HashSet<Long>()
        val seenFrameNumbers = HashSet<Long>()
        val ref = reference
        val refExposure = ref.metadata.exposureProduct
        require(refExposure.isFinite() && refExposure > 0.0)
        frames.forEach { frame ->
            val meta = frame.metadata
            require(meta.physicalCameraId == physicalCameraId &&
                seenTimestamps.add(meta.sensorTimestampNs) &&
                seenFrameNumbers.add(meta.frameNumber) &&
                meta.cfaPattern == ref.metadata.cfaPattern &&
                meta.sensorWhiteLevel == ref.metadata.sensorWhiteLevel &&
                frame.rawWidth == ref.rawWidth && frame.rawHeight == ref.rawHeight &&
                frame.sensorWidth == ref.sensorWidth && frame.sensorHeight == ref.sensorHeight &&
                frame.cropLeft == ref.cropLeft && frame.cropTop == ref.cropTop &&
                frame.physicalCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP) == meta.sensorTimestampNs &&
                frame.physicalCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME) == meta.exposureTimeNs &&
                frame.physicalCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY) == meta.sensitivityIso &&
                meta.exposureTimeNs == ref.metadata.exposureTimeNs &&
                meta.sensitivityIso == ref.metadata.sensitivityIso &&
                meta.exposureProduct.isFinite() &&
                abs(meta.exposureProduct / refExposure - 1.0) <= 0.01) {
                "C donor rejects cross-lens/geometry/frame/exposure bracket"
            }
        }
        // Validate the original NORMAL-only Iris shutter admission without using
        // an A/B reconstructor or the prototype C Sabre GPU frame structures.
        Iris26972CContract.validateBurst(
            shutter,
            frames.map { Iris26972CContract.Role.NORMAL },
            frames.map { it.metadata.sensorTimestampNs },
            frames.map { it.metadata.exposureProduct },
        )
    }

    companion object {
        internal fun create(
            physicalCameraId: String,
            referenceTimestampNs: Long,
            frames: List<Frame>,
        ): Iris26975COriginalRawBurst {
            require(physicalCameraId.isNotBlank() && referenceTimestampNs > 0L && frames.isNotEmpty())
            return Iris26975COriginalRawBurst(physicalCameraId, referenceTimestampNs, frames.toList())
        }
    }
}
