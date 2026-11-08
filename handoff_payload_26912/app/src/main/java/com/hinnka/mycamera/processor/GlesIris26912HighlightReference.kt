package com.hinnka.mycamera.processor

import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs

/**
 * IRIS_26912_B_OFF_ALTERNATIVE_HIGHLIGHT_REFERENCE.
 * Optional, evidence-gated RAW-only pre-fusion reference arbitration.
 * Never changes any RAW pixel or creates saturated RGB hue. A missing fresh
 * viewfinder indication or uncertain scene leaves the 26911 sharpest reference
 * untouched. The existing B OFF sensor-clipped smooth-white reconstruction
 * remains the only fallback when no physically recorded highlight exists.
 */
internal object GlesIris26912HighlightReference {
    private const val GRID_X = 40
    private const val GRID_Y = 30

    private fun clippedSites(
        buffer: ByteBuffer, strideBytes: Int, width: Int, height: Int,
        blackByPhase: FloatArray, whiteLevel: Float, frame: Int,
    ): Int {
        val view = buffer.duplicate().order(ByteOrder.nativeOrder())
        var clipped = 0
        // Interleaved CFA sites are sampled at exactly matching pixel coordinates
        // across frames, with physical sensor-black and white per frame.
        for (cy in 0 until GRID_Y) {
            val y = 4 + (cy * (height - 8) / GRID_Y and -2)
            for (cx in 0 until GRID_X) {
                val x = 4 + (cx * (width - 8) / GRID_X and -2)
                for (dy in 0..1) for (dx in 0..1) {
                    val phase = dy * 2 + dx
                    val b = blackByPhase[frame * 4 + phase]
                    val normalized = ((view.getShort((y + dy) * strideBytes + (x + dx) * 2).toInt()
                        and 0xffff).toFloat() - b) / (whiteLevel - b)
                    if (normalized >= 0.992f) clipped++
                }
            }
        }
        return clipped
    }

    fun select(
        buffers: Array<ByteBuffer>, strides: IntArray, exposure: FloatArray,
        blackByPhase: FloatArray, whiteByFrame: FloatArray, width: Int, height: Int,
        original: Int, shutterIndex: Int, previewP995: Float, staticTrusted: Boolean,
    ): Int {
        if (!staticTrusted || !previewP995.isFinite() || previewP995 < 0.94f ||
            width < 128 || height < 128 || original !in buffers.indices ||
            shutterIndex !in buffers.indices || buffers.size < 2 ||
            strides.size != buffers.size || exposure.size != buffers.size ||
            whiteByFrame.size != buffers.size || blackByPhase.size != buffers.size * 4) return original
        val refExposure = exposure[original]
        if (!refExposure.isFinite() || refExposure <= 0f) return original
        val sampleCount = GRID_X * GRID_Y * 4
        val scores = IntArray(buffers.size) { i ->
            if (!exposure[i].isFinite() || exposure[i] <= 0f ||
                abs(exposure[i] / refExposure - 1f) > 0.025f ||
                !whiteByFrame[i].isFinite() || whiteByFrame[i] <= 0f ||
                strides[i] < width * 2 ||
                blackByPhase.sliceArray(i * 4 until (i + 1) * 4).any { !it.isFinite() || it < 0f || it >= whiteByFrame[i] } ||
                buffers[i].capacity().toLong() < (height - 1L) * strides[i] + width * 2L) {
                Int.MAX_VALUE
            } else clippedSites(buffers[i], strides[i], width, height, blackByPhase, whiteByFrame[i], i)
        }
        val originalClip = scores[original]
        // If reference has too little saturation for reliable discrimination,
        // a different frame cannot make meaningful improvement.
        if (originalClip == Int.MAX_VALUE || originalClip < 16 || originalClip < sampleCount / 400) return original
        var best = original
        for (i in buffers.indices) {
            if (i != original && scores[i] < scores[best]) best = i
        }
        val saved = originalClip - scores[best]
        // At least 24 actual CFA sites and 20% of the clipped reference sites
        // must have physically measured unclipped alternatives.
        return if (best != original && saved >= 24 && saved * 5 >= originalClip) best else original
    }
}
