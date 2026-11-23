package com.hinnka.mycamera.processor.experimentc.original129.model

import android.graphics.ImageFormat
import com.hinnka.mycamera.processor.experimentc.Iris26975COriginalRawBurst
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Experiment C-only in-memory equivalent of the original bjzhou SafeImage input.
 *
 * The shell's real Camera2 RAW_SENSOR Image has already been closed after a verified
 * RAW16 copy. This exposes the original MGC stacker's required SafeImage surface
 * without wrapping the Iris A/B Camera2Controller or handing the GPU a stale HAL
 * buffer. No algorithm is implemented here. Its lifetime is strictly inside the
 * synchronous C RAW-spool lease; closing it never closes the original mmap owner.
 */
class SafeImage private constructor(
    val width: Int,
    val height: Int,
    val timestamp: Long,
    private val raw: ByteBuffer,
) : AutoCloseable {
    private val closed = AtomicBoolean(false)

    interface Plane {
        val buffer: ByteBuffer
        val rowStride: Int
        val pixelStride: Int
    }

    val format: Int get() = ImageFormat.RAW_SENSOR
    val sourceFormat: Int get() = ImageFormat.RAW_SENSOR
    val planes: Array<Plane>
        get() {
            check(!closed.get()) { "C physical RAW donor SafeImage already closed" }
            return arrayOf(object : Plane {
                override val buffer: ByteBuffer
                    get() = raw.asReadOnlyBuffer().order(ByteOrder.nativeOrder()).apply { position(0) }
                override val rowStride: Int get() = Math.multiplyExact(width, 2)
                override val pixelStride: Int get() = 2
            })
        }

    override fun close() {
        closed.compareAndSet(false, true)
    }

    companion object {
        internal fun fromOriginalFrame(frame: Iris26975COriginalRawBurst.Frame): SafeImage {
            val samples = frame.raw16()
            val expected = Math.multiplyExact(Math.multiplyExact(frame.rawWidth, frame.rawHeight), 2)
            require(frame.metadata.sensorTimestampNs > 0L && frame.rawWidth % 2 == 0 &&
                frame.rawHeight % 2 == 0 && samples.remaining() == expected &&
                samples.isReadOnly && frame.rawWidth > 0 && frame.rawHeight > 0) {
                "C original donor needs a complete physical Camera2 RAW16 plane"
            }
            return SafeImage(frame.rawWidth, frame.rawHeight,
                frame.metadata.sensorTimestampNs,
                samples.asReadOnlyBuffer().order(ByteOrder.nativeOrder()).apply { position(0) })
        }
    }
}
