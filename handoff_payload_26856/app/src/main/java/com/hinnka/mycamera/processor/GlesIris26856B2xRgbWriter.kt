package com.hinnka.mycamera.processor

import java.io.Closeable
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/**
 * IRIS_26856_B_2X_ONLY_SEAM_EXACT_RGB16F_PUBLICATION
 *
 * Publish the exact, non-overlapping interior of each pinned RAWR AMaZE tile
 * to one B-owned RGB16F intermediate. This does NOT borrow A/VGN color, apply
 * a scaler, or perform a hidden GPU->CPU readback; the explicit caller supplies
 * its already-completed bounded tile readback. It may not publish an incomplete
 * file or contaminate the historical 26850/Sabre 2x or DNG owner.
 *
 * Coordinate convention matches Iris's existing true2x tile-file contract:
 * rows are bottom-to-top from GLES framebuffer readback, with x increasing
 * to the right. The final HDR/JPEG owner consumes the complete file only.
 */
internal class GlesIris26856B2xRgbWriter(
    private val rawWidth: Int,
    private val rawHeight: Int,
    private val target: File,
) : Closeable {
    private val width: Int
    private val height: Int
    private val pending: File
    private val file: RandomAccessFile
    private var nextX = 0
    private var nextY = 0
    private var rowHeight = 0
    private var finished = false
    private var closed = false

    init {
        require(rawWidth in 32..(Int.MAX_VALUE / 2) && rawHeight in 32..(Int.MAX_VALUE / 2))
        width = Math.multiplyExact(rawWidth, 2)
        height = Math.multiplyExact(rawHeight, 2)
        require(target.extension == "rgb16f" && !target.exists()) {
            "26856 B requires a unique unpublished RGB16F destination"
        }
        val parent = requireNotNull(target.absoluteFile.parentFile)
        require(parent.isDirectory || parent.mkdirs())
        val total = Math.multiplyExact(Math.multiplyExact(width.toLong(), height.toLong()), 6L)
        pending = File.createTempFile("iris26856_b2x_incomplete_", ".tmp", parent)
        file = try {
            RandomAccessFile(pending, "rw").also { it.setLength(total) }
        } catch (e: Exception) {
            pending.delete()
            throw e
        }
    }

    /**
     * The input buffer contains the RGBA16F output of AMaZE for the entire
     * expanded tile, after GPU completion; rows are tightly packed with no GL
     * pixel-pack padding. The core is cropped BEFORE any file publication.
     * Each input RGBA half float is passed through unchanged: no [0,1] clamp,
     * color-matrix application, gamma, half->float->half conversion or UHDR
     * headroom loss. Alpha does not become an RGB/color authority.
     */
    fun writeExpandedRgba16f(
        tile: GlesIris26856True2xCfa.StreamingTile,
        expandedRgba16f: ByteBuffer,
    ) {
        check(!closed && !finished) { "26856 B 2x output already released" }
        require(tile.outputLeft == nextX && tile.outputTop == nextY) {
            "26856 B 2x tile order overlaps or skips prior output"
        }
        require((rowHeight == 0 || rowHeight == tile.outputHeight) &&
            tile.outputLeft + tile.outputWidth <= width &&
            tile.outputTop + tile.outputHeight <= height)
        require(tile.expandedLeft + tile.cropLeft == tile.outputLeft &&
            tile.expandedTop + tile.cropTop == tile.outputTop)
        val incomingBytes = Math.multiplyExact(
            Math.multiplyExact(tile.expandedWidth.toLong(), tile.expandedHeight.toLong()), 8L)
        require(incomingBytes <= Int.MAX_VALUE && expandedRgba16f.capacity() == incomingBytes.toInt()) {
            "26856 B missing or noncontiguous complete RGBA16F AMaZE tile"
        }
        val source = expandedRgba16f.duplicate().order(ByteOrder.nativeOrder())
        val rowBuffer = ByteBuffer.allocate(Math.multiplyExact(tile.outputWidth, 6))
            .order(ByteOrder.nativeOrder())
        // No mutation of the destination file's public name until all tiles pass.
        for (y in 0 until tile.outputHeight) {
            rowBuffer.clear()
            val basePixel = (tile.cropTop + y) * tile.expandedWidth + tile.cropLeft
            for (x in 0 until tile.outputWidth) {
                val sourceByte = (basePixel + x) * 8
                rowBuffer.putShort(source.getShort(sourceByte))
                rowBuffer.putShort(source.getShort(sourceByte + 2))
                rowBuffer.putShort(source.getShort(sourceByte + 4))
            }
            file.seek(((tile.outputTop + y).toLong() * width + tile.outputLeft) * 6L)
            file.write(rowBuffer.array())
        }
        nextX += tile.outputWidth
        rowHeight = tile.outputHeight
        if (nextX == width) {
            nextX = 0
            nextY += rowHeight
            rowHeight = 0
        }
    }

    /** Throws rather than making a partial B output visible. */
    fun finish(): File {
        check(!closed && !finished)
        check(nextX == 0 && nextY == height && rowHeight == 0) {
            "26856 B tile publication is incomplete"
        }
        file.fd.sync()
        file.close()
        closed = true
        try {
            Files.move(pending.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE)
        } catch (e: Exception) {
            pending.delete()
            throw e
        }
        finished = true
        return target
    }

    override fun close() {
        if (!closed) {
            closed = true
            try { file.close() } finally { pending.delete() }
        }
    }
}
