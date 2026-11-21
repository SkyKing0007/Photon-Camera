package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.graphics.ImageFormat
import android.graphics.Rect
import com.hinnka.mycamera.model.SafeImage

/**
 * Photon 26972 C-only pinned bjzhou/PhotonCamera 1.29.0 Sabre RAW ingress.
 *
 * Staging boundary, NOT the Sabre GPU algorithm. Mirrors the upstream 1.29.0
 * Sabre NORMAL-reference admission and sourceBounds-to-RAW-plane contract,
 * while enforcing C's stricter frozen normal-only, single-lens/no-bracket policy.
 * There is deliberately no call to Iris A/B fusion, and no image-output method.
 * The real donor GPU merge/resolve must be attached before the C gate opens.
 *
 * Ownership: the caller transfers these images to this ingress; on rejection
 * all are closed, on success the future C GPU owner receives them exactly once.
 */
internal class Iris26972CDonorSabreIngress(
    private val width: Int,
    private val height: Int,
    sourceBounds: Rect,
    private val cfaPattern: Int,
    private val physicalLensId: String,
    private val referenceTimestampNs: Long,
    private val frozenFrameCount: Int,
) {
    private val frozenBounds = Rect(sourceBounds)

    internal data class PreparedBurst(
        val reference: RawStackFrame,
        val normalFrames: List<RawStackFrame>,
        val sensorBounds: Rect,
        val cfaPattern: Int,
    )

    fun prepareOwned(frames: List<RawStackFrame>): PreparedBurst {
        try {
            require(width > 1 && height > 1 && width % 2 == 0 && height % 2 == 0) {
                "26972 C requires a Bayer-even RAW dimensions"
            }
            require(cfaPattern in 0..3) { "26972 C invalid Bayer arrangement" }
            require(physicalLensId.isNotBlank() && referenceTimestampNs > 0L) {
                "26972 C missing frozen lens or reference"
            }
            require(frozenFrameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES && frames.size == frozenFrameCount) {
                "26972 C frozen RAW frame budget mismatch"
            }
            // Upstream GlesMgcRawSpatialStacker validates sourceBounds against the
            // image; C additionally requires Bayer-aligned crop origins until
            // exact donor odd-phase crop semantics are independently proven.
            require(frozenBounds.left >= 0 && frozenBounds.top >= 0 &&
                frozenBounds.width() == width && frozenBounds.height() == height &&
                (frozenBounds.left and 1) == 0 && (frozenBounds.top and 1) == 0) {
                "26972 C unverified sensor crop / CFA phase"
            }
            val timestamps = HashSet<Long>(frames.size * 2)
            var reference: RawStackFrame? = null
            var referenceExposure = Double.NaN
            for (frame in frames) {
                require(frame.role == RawBurstFrameRole.NORMAL) {
                    "26972 C Sabre rejects short/long/bracketed RAW rather than dropping them"
                }
                require(frame.physicalCameraId == physicalLensId) {
                    "26972 C RAW physical-lens identity changed"
                }
                val timestamp = frame.sensorTimestampNs
                require(timestamp > 0L && frame.image.timestamp == timestamp && timestamps.add(timestamp)) {
                    "26972 C RAW timestamp identity invalid or duplicated"
                }
                require(frame.exposureTimeNs > 0L && frame.sensitivityIso > 0 &&
                    frame.exposureProduct.isFinite() && frame.exposureProduct > 0.0) {
                    "26972 C invalid normal RAW exposure"
                }
                validateSourcePlane(frame.image)
                if (timestamp == referenceTimestampNs) {
                    reference = frame
                    referenceExposure = frame.exposureProduct
                }
            }
            require(reference != null) { "26972 C frozen NORMAL reference absent" }
            require(frames.all { kotlin.math.abs(it.exposureProduct / referenceExposure - 1.0) <= 0.01 }) {
                "26972 C intentional exposure brackets forbidden in Night and Photo"
            }
            // Same ordering as the pinned upstream Sabre entry: reference first,
            // remaining NORMAL observations in capture-list order.
            val ordered = ArrayList<RawStackFrame>(frames.size)
            ordered.add(reference)
            ordered.addAll(frames.filter { it !== reference })
            return PreparedBurst(reference, ordered, Rect(frozenBounds), cfaPattern)
        } catch (failure: Throwable) {
            frames.forEach { runCatching { it.image.close() } }
            throw failure
        }
    }

    private fun validateSourcePlane(image: SafeImage) {
        require(image.format == ImageFormat.RAW_SENSOR) { "26972 C only accepts RAW_SENSOR" }
        require(frozenBounds.right <= image.width && frozenBounds.bottom <= image.height) {
            "26972 C sourceBounds exceeds physical RAW sensor dimensions"
        }
        require(image.pixelStrideBytes == 2 &&
            image.rowStrideBytes.toLong() >= frozenBounds.right.toLong() * 2L) {
            "26972 C cannot address packed RAW16 crop row"
        }
        val lastByte = (frozenBounds.bottom.toLong() - 1L) * image.rowStrideBytes.toLong() +
            (frozenBounds.right.toLong() - 1L) * 2L + 2L
        require(lastByte > 0L && lastByte <= Int.MAX_VALUE.toLong()) {
            "26972 C RAW crop byte offset overflow"
        }
        if (!image.isFileBacked) {
            val plane = image.planes.singleOrNull()
                ?: throw IllegalArgumentException("26972 C requires a single RAW16 plane")
            require(plane.rowStride == image.rowStrideBytes && plane.pixelStride == 2 &&
                plane.buffer.limit().toLong() >= lastByte) {
                "26972 C RAW crop exceeds owned plane limit"
            }
        }
    }
}
