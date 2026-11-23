package com.hinnka.mycamera.processor

import java.nio.ByteBuffer
import kotlin.math.ceil
import kotlin.math.floor

/**
 * C-only bounded assembly of the pinned donor RAW gainmap's GLOBAL downsample-2
 * grid. Every input strip is FULL HEIGHT because the donor's separate LUT and
 * gainmap EGL readbacks use an asymmetric vertical-coordinate convention.
 * Truncating vertical input changes gainmap values even when interpolation
 * appears locally covered. A strip's source X support includes both GL_LINEAR
 * taps at every global gainmap pixel center, including odd physical widths.
 *
 * This is a geometry/assembly owner, NOT an HDR developer: the caller MUST
 * supply three real, mutually pixel-aligned donor inputs (before LUT SDR,
 * after LUT SDR, independent linear HDR reference) to the GPU producer. This
 * owner cannot authorize use of a synthetic or legacy Iris HDR image.
 */
internal object Iris26975CDonorGainmapStripAssembly {
    private const val MAX_SOURCE_WIDTH = 256
    private const val MAX_GAIN_WIDTH = 128

    data class Strip(
        val sourceLeft: Int,
        val sourceWidth: Int,
        val gainLeft: Int,
        val gainWidth: Int,
        val imageWidth: Int,
        val imageHeight: Int,
    ) {
        val gainImageWidth: Int get() = (imageWidth + 1) / 2
        val gainImageHeight: Int get() = (imageHeight + 1) / 2

        fun verify() {
            require(imageWidth in 2..16384 && imageHeight in 2..16384 &&
                sourceLeft >= 0 && sourceWidth in 1..MAX_SOURCE_WIDTH &&
                sourceLeft + sourceWidth <= imageWidth &&
                gainLeft >= 0 && gainWidth in 1..MAX_GAIN_WIDTH &&
                gainLeft + gainWidth <= gainImageWidth) {
                "26975 C donor gainmap strip dimensions exceed the original source"
            }
            fun tap(index: Int): Double =
                (index.toDouble() + .5) * imageWidth / gainImageWidth - .5
            val first = floor(tap(gainLeft)).toInt().coerceIn(0, imageWidth - 1)
            val last = ceil(tap(gainLeft + gainWidth - 1)).toInt().coerceIn(0, imageWidth - 1)
            require(sourceLeft <= first && last < sourceLeft + sourceWidth) {
                "26975 C donor strip truncates global GL_LINEAR support"
            }
        }
    }

    fun plan(imageWidth: Int, imageHeight: Int): List<Strip> {
        require(imageWidth in 2..16384 && imageHeight in 2..16384) {
            "26975 C invalid physical output for donor gainmap"
        }
        val gainWidth = (imageWidth + 1) / 2
        val strips = ArrayList<Strip>()
        fun tap(index: Int): Double =
            (index.toDouble() + .5) * imageWidth / gainWidth - .5
        var left = 0
        while (left < gainWidth) {
            val sourceLeft = floor(tap(left)).toInt().coerceIn(0, imageWidth - 1)
            var width = minOf(MAX_GAIN_WIDTH, gainWidth - left)
            var sourceRight: Int
            while (true) {
                sourceRight = (ceil(tap(left + width - 1)).toInt() + 1)
                    .coerceIn(1, imageWidth)
                if (sourceRight - sourceLeft <= MAX_SOURCE_WIDTH) break
                check(width > 1) { "26975 C one donor gain pixel exceeds bounded support" }
                width--
            }
            val strip = Strip(sourceLeft, sourceRight - sourceLeft, left, width,
                imageWidth, imageHeight)
            strip.verify()
            strips.add(strip)
            left += width
        }
        check(strips.isNotEmpty() && strips.first().gainLeft == 0 &&
            strips.last().gainLeft + strips.last().gainWidth == gainWidth &&
            strips.zipWithNext().all { (a, b) ->
                a.gainLeft + a.gainWidth == b.gainLeft
            }) { "26975 C donor gainmap strips have a hole or duplicate" }
        return strips
    }

    /** One immutable final output tile: encoded RGBA8 plus linear HDR RGB float32. */
    data class FinalizedTile(
        /** 8-bit bytes used solely for the final JPEG444. */
        val sdr: ByteBuffer,
        val hdr: ByteBuffer,
        /** Encoded sRGB in native-endian RGBA FLOAT32; GL stores RGBA16F. */
        val encodedSdrF32: ByteBuffer,
    )

    data class NoLutInputs(
        val beforeLutEncodedSrgb: ByteBuffer,
        val afterLutEncodedSrgb: ByteBuffer,
        val independentHdrLinearSrgb: ByteBuffer,
        val physicalCameraId: String,
        val referenceTimestampNs: Long,
    )

    /**
     * Materialize only ONE bounded full-height source strip for the original
     * donor's two-pass sidecar/gainmap shader. The user explicitly chose No LUT:
     * the before/after float arrays therefore come from the SAME ACTUAL
     * pre-JPEG encoded SDR. Do not substitute JPEG-rounded RGBA8 bytes.
     * They are not a fabricated constant gain sidecar; the shader
     * still measures their ratio (1 for No LUT). A selected nonempty LUT is
     * rejected until its genuine after-LUT renderer is wired.
     *
     * `render` MUST be the physically matched donor GuidedUpsample/Adobe output
     * plus the independently derived donor HDR reference after Lanczos/rotation.
     * This assembler cannot validate numerical donor HDR parity by itself.
     */
    fun materializeNoLutSourceStrip(
        strip: Strip,
        selection: Iris26975CDonorLutSelection.Frozen,
        physicalCameraId: String,
        referenceTimestampNs: Long,
        fits: (Int, Int, Int, Int) -> Boolean,
        render: (Int, Int, Int, Int) -> FinalizedTile,
    ): NoLutInputs {
        strip.verify()
        require(selection.isNoLut && physicalCameraId.isNotBlank() &&
            referenceTimestampNs > 0L) {
            "26975 C donor No LUT strip requires frozen real physical RAW provenance"
        }
        val width = strip.sourceWidth
        val height = strip.imageHeight
        val byteSize = width * height * 4
        // The pinned donor's bitmap upload is RGBA_F16.  Keep the original
        // encoded floating-point samples until the GPU rounds them to half;
        // 8-bit JPEG bytes must never supply the UHDR sampler.
        val before = ByteBuffer.allocateDirect(byteSize * 4)
            .order(java.nio.ByteOrder.nativeOrder())
        // With explicitly frozen No LUT, source and target SDR are the SAME
        // encoded float pixels. Reuse one immutable CPU strip for both GPU
        // uploads instead of allocating a second up-to-64MiB direct buffer.
        val after = before
        val hdr = ByteBuffer.allocateDirect(byteSize * 4)
            .order(java.nio.ByteOrder.nativeOrder())
        var y = 0
        while (y < height) {
            var tileHeight = minOf(256, height - y)
            while (tileHeight > 1 && !fits(strip.sourceLeft, y, 1, tileHeight))
                tileHeight /= 2
            require(fits(strip.sourceLeft, y, 1, tileHeight)) {
                "26975 C donor No LUT source exceeds physical RAW support"
            }
            var x = 0
            while (x < width) {
                var tileWidth = minOf(256, width - x)
                while (tileWidth > 1 &&
                    !fits(strip.sourceLeft + x, y, tileWidth, tileHeight))
                    tileWidth /= 2
                require(fits(strip.sourceLeft + x, y, tileWidth, tileHeight)) {
                    "26975 C donor gainmap strip truncates Lanczos source footprint"
                }
                val tile = render(strip.sourceLeft + x, y, tileWidth, tileHeight)
                val pixels = tileWidth * tileHeight
                require(tile.sdr.isDirect && tile.hdr.isDirect &&
                    tile.sdr.capacity() == pixels * 4 &&
                    tile.hdr.capacity() == pixels * 12 &&
                    tile.encodedSdrF32.isDirect && !tile.encodedSdrF32.isReadOnly &&
                    tile.encodedSdrF32.capacity() == pixels * 16 &&
                    tile.encodedSdrF32.order() == java.nio.ByteOrder.nativeOrder() &&
                    tile.hdr.order() == java.nio.ByteOrder.nativeOrder()) {
                    "26975 C donor strip received incomplete SDR/HDR pixels"
                }
                val sourceHdr = tile.hdr.duplicate()
                    .order(java.nio.ByteOrder.nativeOrder())
                val sourceSdr = tile.encodedSdrF32.duplicate()
                    .order(java.nio.ByteOrder.nativeOrder())
                for (ty in 0 until tileHeight) for (tx in 0 until tileWidth) {
                    val from = (ty * tileWidth + tx) * 4
                    val to = ((y + ty) * width + x + tx) * 4
                    for (channel in 0..3) {
                        val jpegByte = tile.sdr.get(from + channel).toInt() and 255
                        val encoded = sourceSdr.getFloat((ty * tileWidth + tx) * 16 + channel * 4)
                        require(encoded.isFinite() &&
                            (if (channel == 3) encoded == 1f && jpegByte == 255
                             else encoded in 0f..1f)) {
                            "26975 C donor No LUT invalid pre-JPEG RGBA_F16 source"
                        }
                        // The floating SDR fed to bjzhou's UHDR gainmap and the
                        // RGB8 fed to the JPEG444 encoder MUST be the same
                        // finalized pixel.  Both originate from GeometryResampler;
                        // NativeOneX uses Java Math.round(encoded * 255f).
                        // Do not accept a plausible but differently rendered
                        // SDR stream: it would pair a gainmap with a false base.
                        if (channel != 3) require(
                            jpegByte == java.lang.Math.round(encoded * 255f).coerceIn(0, 255)
                        ) {
                            "26975 C donor UHDR/JPEG444 SDR pixel mismatch at global " +
                                "(${strip.sourceLeft + x + tx}, ${y + ty}) channel=$channel"
                        }
                        before.putFloat(to * 4 + channel * 4, encoded)
                    }
                    for (channel in 0..2) {
                        val value = sourceHdr.getFloat((ty * tileWidth + tx) * 12 + channel * 4)
                        require(value.isFinite() && value >= 0f && value <= 65504f) {
                            "26975 C donor No LUT invalid linear HDR reference"
                        }
                        hdr.putFloat(to * 4 + channel * 4, value)
                    }
                    hdr.putFloat(to * 4 + 12, 1f)
                }
                x += tileWidth
            }
            y += tileHeight
        }
        // All three inputs begin at zero: GLSL uploads must not silently drop
        // their first scanline after a prior consumer changed a buffer position.
        before.position(0); after.position(0); hdr.position(0)
        return NoLutInputs(before, after, hdr, physicalCameraId, referenceTimestampNs)
    }

    /**
     * Returns top-left ALPHA_8 bytes only after EVERY strip succeeds. The
     * producer must be the original donor GPU LUT-sidecar + gainmap pipeline;
     * an incomplete, wrong-sized, indirect or read-only strip is rejected.
     */
    fun assemble(imageWidth: Int, imageHeight: Int,
        producer: (Strip) -> ByteBuffer): ByteBuffer {
        val strips = plan(imageWidth, imageHeight)
        val gainWidth = (imageWidth + 1) / 2
        val gainHeight = (imageHeight + 1) / 2
        val finalBytes = ByteBuffer.allocateDirect(gainWidth * gainHeight)
        for (strip in strips) {
            val input = producer(strip)
            val needed = strip.gainWidth * gainHeight
            require(input.isDirect && input.remaining() == needed) {
                "26975 C donor gainmap GPU strip missing/corrupt: x=${strip.gainLeft}"
            }
            val start = input.position()
            for (row in 0 until gainHeight) for (column in 0 until strip.gainWidth) {
                val byte = input.get(start + row * strip.gainWidth + column)
                finalBytes.put(row * gainWidth + strip.gainLeft + column, byte)
            }
        }
        finalBytes.position(0)
        return finalBytes
    }
}
