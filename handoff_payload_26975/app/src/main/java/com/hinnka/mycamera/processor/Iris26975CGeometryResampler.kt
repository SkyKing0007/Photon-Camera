package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry
import java.nio.ByteBuffer

/**
 * Publication-side bounded tile adapter for the ORIGINAL pinned bjzhou RawOutputPass.
 * Source crop, orientation, Lanczos-3 and HDR ratio are no longer emulated on the CPU.
 * The original GPU shader samples the full-resolution donor textures, so the adapter
 * needs only <=256x256 output targets (not a full 50MP second framebuffer or crop halo).
 * Publication remains gated until the entire RAW-to-JPEG/R contract is proven.
 */
internal class Iris26975CGeometryResampler(
    geometry: Iris26975COutputGeometry,
    reader: Iris26972CGlReadback,
) : AutoCloseable {
    internal data class Tile(val sdr: ByteBuffer, val hdr: ByteBuffer,
        val encodedSdrF32: ByteBuffer)
    private val donor = Iris26975COriginalOutputGpu(geometry, reader.finalizedColorSource())
    fun fits(left: Int, top: Int, width: Int, height: Int): Boolean =
        donor.fits(left, top, width, height)
    fun render(left: Int, top: Int, width: Int, height: Int): Tile =
        donor.render(left, top, width, height)
    override fun close() = donor.close()
}
