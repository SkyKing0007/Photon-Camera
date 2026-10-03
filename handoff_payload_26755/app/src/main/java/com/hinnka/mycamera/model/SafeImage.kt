package com.hinnka.mycamera.model

import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.hinnka.mycamera.utils.PLog
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicBoolean

/**
 * IRIS_26512_MGC1271_IMMUTABLE_SAFE_IMAGE_ADAPTER
 * Minimal plane contract consumed by pinned bjzhou 1.27.1 MGC Spatial.
 *
 * IRIS_26543_NIGHT_BOUNDED_DISK_BACKING
 * Night may back non-reference RAWs with immutable cache files. The live Spatial owner reads only
 * the full frame or tile region needed for the current GPU upload into one temporary Photon native
 * buffer, then frees it immediately. Frame count therefore does not multiply anonymous RAW RAM.
 */
class SafeImage private constructor(
    val width: Int,
    val height: Int,
    val format: Int,
    val timestamp: Long,
    buffer: ByteBuffer?,
    val rowStrideBytes: Int,
    val pixelStrideBytes: Int,
    private val backingFile: File?,
    private val backingByteCount: Int,
    private val closeAction: (() -> Unit)? = null,
) : AutoCloseable {
    class Plane(
        val buffer: ByteBuffer,
        val rowStride: Int,
        val pixelStride: Int,
    )

    class FileRegion internal constructor(
        val buffer: ByteBuffer,
        val rowStride: Int,
        val pixelStride: Int,
    ) : AutoCloseable {
        private val closed = AtomicBoolean(false)
        override fun close() {
            if (closed.compareAndSet(false, true)) LargeDirectBuffer.free(buffer)
        }
    }

    private val closed = AtomicBoolean(false)
    private val memoryPlane: Array<Plane> = if (buffer != null) {
        arrayOf(Plane(buffer.duplicate().apply { position(0) }, rowStrideBytes, pixelStrideBytes))
    } else {
        emptyArray()
    }

    val planes: Array<Plane> get() = memoryPlane
    val isFileBacked: Boolean get() = backingFile != null

    constructor(
        width: Int, height: Int, format: Int, timestamp: Long, buffer: ByteBuffer,
        rowStride: Int, pixelStride: Int, closeAction: (() -> Unit)? = null,
    ) : this(
        width, height, format, timestamp, buffer, rowStride, pixelStride,
        null, 0, closeAction,
    )

    constructor(
        width: Int, height: Int, format: Int, timestamp: Long, backingFile: File,
        backingByteCount: Int, rowStride: Int, pixelStride: Int,
        closeAction: (() -> Unit)? = null,
    ) : this(
        width, height, format, timestamp, null, rowStride, pixelStride,
        backingFile, backingByteCount, closeAction,
    ) {
        require(backingByteCount > 0) { "Disk-backed RAW byte count must be positive" }
        require(backingFile.isFile && backingFile.length() >= backingByteCount.toLong()) {
            "Disk-backed RAW is unavailable: ${backingFile.absolutePath}"
        }
    }

    /** IRIS_26755_PLAN_B_RAW_LIFETIME_OWNER
     * Create an independent immutable disk-backed copy of this exact RAW plane without changing
     * row/pixel stride. The caller decides when to close the original owner, so a complete staged
     * population can be proven before any in-memory RAW is released.
     */
    fun copyRawBackingTo(destination: File, deadlineNs: Long): SafeImage {
        check(!closed.get()) { "SafeImage is closed" }
        require(deadlineNs > System.nanoTime()) { "RAW staging deadline already expired" }
        val byteCountLong = rowStrideBytes.toLong() * height.toLong()
        require(byteCountLong in 1..Int.MAX_VALUE.toLong())
        val byteCount = byteCountLong.toInt()
        destination.parentFile?.let { require(it.exists() || it.mkdirs()) }
        if (destination.exists()) require(destination.delete())
        val chunk = 1L shl 20
        try {
            FileOutputStream(destination).channel.use { out ->
                if (backingFile != null) {
                    FileInputStream(backingFile).channel.use { input ->
                        require(backingByteCount >= byteCount) {
                            "Disk-backed RAW bytes=$backingByteCount required=$byteCount"
                        }
                        var position = 0L
                        while (position < byteCountLong) {
                            check(System.nanoTime() < deadlineNs) { "RAW staging deadline exceeded" }
                            val amount = minOf(chunk, byteCountLong - position)
                            out.position(position)
                            val moved = input.transferTo(position, amount, out)
                            if (moved <= 0L) throw IllegalStateException("RAW staging made no progress")
                            position += moved
                        }
                    }
                } else {
                    val plane = memoryPlane.singleOrNull()
                        ?: throw IllegalStateException("In-memory RAW plane is unavailable")
                    val source = plane.buffer.duplicate().order(ByteOrder.nativeOrder())
                    require(source.capacity() >= byteCount) {
                        "In-memory RAW capacity=${source.capacity()} required=$byteCount"
                    }
                    source.position(0)
                    source.limit(byteCount)
                    while (source.hasRemaining()) {
                        check(System.nanoTime() < deadlineNs) { "RAW staging deadline exceeded" }
                        val oldLimit = source.limit()
                        source.limit(minOf(oldLimit, source.position() + chunk.toInt()))
                        while (source.hasRemaining()) {
                            val written = out.write(source)
                            if (written <= 0) throw IllegalStateException("RAW staging made no progress")
                        }
                        source.limit(oldLimit)
                    }
                }
            }
            require(destination.length() == byteCountLong) {
                "Staged RAW bytes=${destination.length()} expected=$byteCountLong"
            }
            return SafeImage(
                width = width, height = height, format = format, timestamp = timestamp,
                backingFile = destination, backingByteCount = byteCount,
                rowStride = rowStrideBytes, pixelStride = pixelStrideBytes,
                closeAction = { runCatching { destination.delete() } },
            )
        } catch (t: Throwable) {
            runCatching { destination.delete() }
            throw t
        }
    }

    /** Read a packed RAW16 rectangle without retaining the entire disk-backed frame in RAM. */
    fun readFileRegion(left: Int, top: Int, regionWidth: Int, regionHeight: Int): FileRegion {
        check(!closed.get()) { "SafeImage is closed" }
        val file = checkNotNull(backingFile) { "SafeImage is not disk-backed" }
        require(pixelStrideBytes == 2) { "Disk-backed RAW pixel stride=$pixelStrideBytes, expected 2" }
        require(left >= 0 && top >= 0 && regionWidth > 0 && regionHeight > 0)
        require(left + regionWidth <= width && top + regionHeight <= height)
        require(rowStrideBytes >= width * pixelStrideBytes)
        val packedRowStride = regionWidth * pixelStrideBytes
        val byteCountLong = packedRowStride.toLong() * regionHeight
        require(byteCountLong in 1..Int.MAX_VALUE.toLong())
        val byteCount = byteCountLong.toInt()
        val output = LargeDirectBuffer.allocate(byteCountLong, "IRIS26543 Night RAW region")
            ?: throw IllegalStateException("Unable to allocate $byteCount byte Night RAW upload region")
        output.order(ByteOrder.nativeOrder())
        try {
            FileInputStream(file).channel.use { channel ->
                if (left == 0 && packedRowStride == rowStrideBytes) {
                    val sourceOffset = top.toLong() * rowStrideBytes
                    val sourceEnd = sourceOffset + byteCountLong
                    require(sourceOffset >= 0 && sourceEnd <= backingByteCount.toLong()) {
                        "Disk RAW region exceeds backing bytes=$backingByteCount"
                    }
                    output.position(0)
                    output.limit(byteCount)
                    var position = sourceOffset
                    while (output.hasRemaining()) {
                        val read = channel.read(output, position)
                        if (read < 0) throw IllegalStateException("Unexpected EOF in Night RAW spool")
                        if (read == 0) continue
                        position += read
                    }
                } else {
                    for (row in 0 until regionHeight) {
                        val sourceOffset =
                            (top + row).toLong() * rowStrideBytes + left.toLong() * pixelStrideBytes
                        val sourceEnd = sourceOffset + packedRowStride
                        require(sourceOffset >= 0 && sourceEnd <= backingByteCount.toLong()) {
                            "Disk RAW region exceeds backing bytes=$backingByteCount"
                        }
                        output.position(row * packedRowStride)
                        output.limit((row + 1) * packedRowStride)
                        var position = sourceOffset
                        while (output.hasRemaining()) {
                            val read = channel.read(output, position)
                            if (read < 0) throw IllegalStateException("Unexpected EOF in Night RAW spool")
                            if (read == 0) continue
                            position += read
                        }
                    }
                }
            }
            output.position(0)
            output.limit(byteCount)
            return FileRegion(output, packedRowStride, pixelStrideBytes)
        } catch (t: Throwable) {
            LargeDirectBuffer.free(output)
            throw t
        }
    }

    override fun close() {
        if (closed.compareAndSet(false, true)) {
            closeAction?.invoke()
        }
    }
}
