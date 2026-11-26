package com.hinnka.mycamera.processor

import java.nio.ByteBuffer
import java.nio.ByteOrder

/** C Motion-only native allocation lease; no HAL Image, file or mutable buffer escapes. */
internal class Iris26989CRawMemory private constructor(
    private var owner: ByteBuffer?, private val free: (ByteBuffer) -> Unit,
) : AutoCloseable {
    @Synchronized fun readOnly(): ByteBuffer = checkNotNull(owner) { "released C RAW" }
        .asReadOnlyBuffer().order(ByteOrder.nativeOrder())
    @Synchronized override fun close() {
        val b = owner ?: return
        owner = null
        free(b)
    }
    companion object {
        private var reserved = 0L
        /** Account for overlapping cancelled workers; never silently shorten the requested burst. */
        @Synchronized fun reserve(bytes: Long, budget: Long) {
            require(bytes > 0 && budget >= bytes && reserved <= budget - bytes) { "C RAW memory budget exhausted" }
            reserved += bytes
        }
        @Synchronized fun release(bytes: Long) {
            check(bytes > 0 && bytes <= reserved) { "C RAW memory reservation mismatch" }
            reserved -= bytes
        }
        fun copy(src: ByteBuffer, rowStride: Int, left: Int, top: Int, width: Int, height: Int,
                 allocate: (Long) -> ByteBuffer?, free: (ByteBuffer) -> Unit): Iris26989CRawMemory {
            require(src.isDirect && width > 0 && height > 0 && left >= 0 && top >= 0 &&
                width % 2 == 0 && height % 2 == 0 && left % 2 == 0 && top % 2 == 0)
            val row = Math.multiplyExact(width, 2)
            require(rowStride >= (left.toLong() + width) * 2L && rowStride % 2 == 0)
            val start = src.position().toLong() + top.toLong() * rowStride + left.toLong() * 2
            val end = start + (height.toLong() - 1L) * rowStride + row
            val bytes = Math.multiplyExact(row, height)
            require(start >= 0 && end >= start && end <= src.limit().toLong()) { "C RAW crop exceeds source" }
            val b = checkNotNull(allocate(bytes.toLong())) { "C RAW native allocation failed" }
            try {
                require(b.isDirect && !b.isReadOnly && b.capacity() == bytes)
                b.clear(); b.order(ByteOrder.nativeOrder())
                val input = src.duplicate().order(ByteOrder.nativeOrder())
                if (rowStride == row) {
                    input.position(start.toInt()); input.limit(end.toInt()); b.put(input)
                } else {
                    for (y in 0 until height) {
                        val pos = (start + y.toLong() * rowStride).toInt()
                        input.limit(pos + row); input.position(pos); b.put(input)
                    }
                }
                check(b.position() == bytes); b.flip()
                return Iris26989CRawMemory(b, free)
            } catch (failure: Throwable) {
                try { free(b) } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
                throw failure
            }
        }
    }
}
