package com.hinnka.mycamera.processor

import com.hinnka.mycamera.model.SafeImage
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * IRIS_26864_NATIVE_B_FROZEN_NORMAL_RAW16_INGRESS
 *
 * The real RAWR B engine consumes the same shutter-frozen NORMAL SafeImage
 * bytes and per-frame exposure/black/white metadata as Iris capture. This
 * class is a synchronous, borrowing ingress: it does not invent a noise
 * profile, perform alignment/merge, borrow A's calibrated noise, or release
 * a Camera2 image while JNI/Vulkan may still read its direct ByteBuffer.
 *
 * The caller must keep this object alive for the entire native GPU submit,
 * including any fence wait, and close it even when JNI throws. Closing this
 * object releases only temporary file-backed RAW materializations; original
 * SafeImage lifetime still belongs to the capture batch owner.
 */
internal class GlesIris26864FrozenRawrIngress private constructor(
    val width: Int,
    val height: Int,
    val buffers: Array<ByteBuffer>,
    val stridesBytes: IntArray,
    val exposures: FloatArray,
    val timestampsNs: LongArray,
    val blackByFrameByPhase: FloatArray,
    val sensorWhiteByFrame: FloatArray,
    private val fileRegions: List<SafeImage.FileRegion>,
) : AutoCloseable {
    private var closed = false

    override fun close() {
        if (!closed) {
            closed = true
            fileRegions.asReversed().forEach { it.close() }
        }
    }

    fun assertUsable() {
        check(!closed) { "26864 RAW burst ingress was released before native GPU completion" }
        check(buffers.size >= 2 && buffers.size == exposures.size &&
            buffers.size == timestampsNs.size && buffers.size == stridesBytes.size &&
            blackByFrameByPhase.size == buffers.size * 4 &&
            sensorWhiteByFrame.size == buffers.size) {
            "26864 frozen NORMAL burst ingress lost per-frame provenance"
        }
    }

    companion object {
        fun borrowNormals(
            frames: List<RawStackFrame>,
            width: Int, height: Int,
            referenceBlack: FloatArray,
            sensorWhite: Int,
        ): GlesIris26864FrozenRawrIngress {
            require(width in 32..16384 && height in 32..16384 && width % 2 == 0 && height % 2 == 0)
            require(sensorWhite > 0 && referenceBlack.size == 4)
            require(referenceBlack.all { it.isFinite() && it >= 0f && it < sensorWhite })
            val normal = frames.filter { it.role == RawBurstFrameRole.NORMAL }
            require(normal.size >= 2) { "26864 RAWR requires multi-frame NORMAL burst; no single-frame fallback" }
            val physicalIds = normal.map { it.physicalCameraId }.distinct()
            require(physicalIds.size == 1) { "26864 mixed physical camera in one RAWR burst" }
            val seen = HashSet<Long>(normal.size)
            val owners = ArrayList<SafeImage.FileRegion>()
            try {
                val byteBuffers = ArrayList<ByteBuffer>(normal.size)
                val strides = IntArray(normal.size)
                val exposures = FloatArray(normal.size)
                val timestamps = LongArray(normal.size)
                val black = FloatArray(normal.size * 4)
                val white = FloatArray(normal.size)
                normal.forEachIndexed { index, frame ->
                    val image = frame.image
                    require(image.width == width && image.height == height)
                    require(frame.sensorTimestampNs > 0L && seen.add(frame.sensorTimestampNs)) {
                        "26864 stale or duplicate RAW timestamp"
                    }
                    val product = frame.exposureProduct
                    require(product.isFinite() && product > 0.0 && product <= Float.MAX_VALUE.toDouble()) {
                        "26864 missing real per-frame exposure product"
                    }
                    exposures[index] = product.toFloat()
                    timestamps[index] = frame.sensorTimestampNs
                    val byPhase = frame.dynamicBlackLevelByCfaPosition ?: referenceBlack
                    require(byPhase.size == 4 && byPhase.all { it.isFinite() && it >= 0f && it < sensorWhite }) {
                        "26864 invalid physical black level"
                    }
                    for (phase in 0..3) black[index * 4 + phase] = byPhase[phase]
                    white[index] = sensorWhite.toFloat()
                    val region = if (image.isFileBacked) {
                        image.readFileRegion(0, 0, width, height).also { owners.add(it) }
                    } else null
                    val plane = image.planes.firstOrNull()
                    val source = region?.buffer ?: requireNotNull(plane?.buffer) {
                        "26864 NORMAL source has no RAW16 bytes"
                    }
                    val row = region?.rowStride ?: requireNotNull(plane).rowStride
                    val pixel = region?.pixelStride ?: requireNotNull(plane).pixelStride
                    require(pixel == 2 && row >= width * 2 && row % 2 == 0)
                    val used = (height.toLong() - 1L) * row + width * 2L
                    require(used in 1..Int.MAX_VALUE.toLong() && source.capacity() >= used) {
                        "26864 truncated immutable RAW16 source"
                    }
                    require(source.isDirect) { "26864 JNI RAW16 requires direct immutable source plane" }
                    val view = source.duplicate().order(ByteOrder.nativeOrder())
                    view.position(0)
                    view.limit(used.toInt())
                    byteBuffers.add(view.slice().order(ByteOrder.nativeOrder()))
                    strides[index] = row
                }
                return GlesIris26864FrozenRawrIngress(width, height, byteBuffers.toTypedArray(),
                    strides, exposures, timestamps, black, white, owners)
            } catch (t: Throwable) {
                owners.asReversed().forEach { it.close() }
                throw t
            }
        }
    }
}
