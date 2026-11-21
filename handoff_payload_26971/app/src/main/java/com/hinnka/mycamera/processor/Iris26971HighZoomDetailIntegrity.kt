package com.hinnka.mycamera.processor

import kotlin.math.abs
import kotlin.math.min

/**
 * IRIS_26971_HIGH_ZOOM_INDEPENDENT_TILE_CONSENSUS
 *
 * The scalar sidecar is an optional correction to the native Sabre/VGN RGB master. Two GPU
 * reconstructions of exactly the same NORMAL RAW observations, with different (even) tile grids,
 * must agree within the unavoidable half-float arithmetic tolerance. Where they don't, the
 * existing Sabre/VGN value is the safe identity fallback (zero log-luma detail), never blur.
 *
 * A 2x2 single-sign high-amplitude detail block also violates the zero-DC intra-Bayer-quad
 * intent of the scalar shader. This catches a stripe that is identically corrupt in both tilings.
 * No RGB, RAW, color transform or global sharpness owner changes.
 */
internal object Iris26971HighZoomDetailIntegrity {
    private const val MAX_DETAIL_EV = 0.561f
    private const val INDEPENDENT_TOL_EV = 0.055f
    private const val SAMESIGN_FLOOR_EV = 0.090f
    private const val FADE_RADIUS = 6

    data class Result(
        val detail: FloatArray,
        val disagreementPixels: Int,
        val invalidQuadPixels: Int,
        val affectedPixels: Int,
        val fullNativeFallback: Boolean,
    )

    fun reconcile(primary: FloatArray, shifted: FloatArray, width: Int, height: Int): Result {
        require(width > 0 && height > 0 && width % 2 == 0 && height % 2 == 0)
        val size = Math.multiplyExact(width, height)
        require(primary.size == size && shifted.size == size)
        val failed = BooleanArray(size)
        var disagree = 0
        for (i in 0 until size) {
            val a = primary[i]
            val b = shifted[i]
            val invalid = !a.isFinite() || !b.isFinite() ||
                abs(a) > MAX_DETAIL_EV || abs(b) > MAX_DETAIL_EV ||
                abs(a - b) > INDEPENDENT_TOL_EV
            if (invalid) {
                failed[i] = true
                disagree++
            }
        }
        var quadCount = 0
        for (y in 0 until height step 2) {
            for (x in 0 until width step 2) {
                val at = y * width + x
                val ids = intArrayOf(at, at + 1, at + width, at + width + 1)
                // The shader's 2x2 direct CFA residual is centered about zero. Four strong
                // same-sign log gains cannot represent supported zero-DC microstructure.
                val aPos = ids.all { primary[it] >= SAMESIGN_FLOOR_EV }
                val aNeg = ids.all { primary[it] <= -SAMESIGN_FLOOR_EV }
                val bPos = ids.all { shifted[it] >= SAMESIGN_FLOOR_EV }
                val bNeg = ids.all { shifted[it] <= -SAMESIGN_FLOOR_EV }
                if (aPos || aNeg || bPos || bNeg) {
                    for (id in ids) {
                        if (!failed[id]) {
                            failed[id] = true
                            quadCount++
                        }
                    }
                }
            }
        }
        val failedCount = failed.count { it }
        if (failedCount == 0) return Result(primary, 0, 0, 0, false)
        // Extensive disagreement means the optional sidecar is not dependable. Keep the
        // original Sabre/VGN RGB image, rather than risking dense fallback boundaries.
        if (failedCount >= size / 20) {
            primary.fill(0f)
            return Result(primary, disagree, quadCount, size, true)
        }
        val distance = ByteArray(size) { i -> if (failed[i]) 0 else (FADE_RADIUS + 1).toByte() }
        // Two distance-transform passes produce a smooth 6-pixel guard around failed detail.
        for (y in 0 until height) {
            for (x in 0 until width) {
                val i = y * width + x
                var d = distance[i].toInt()
                if (x > 0) d = min(d, distance[i - 1].toInt() + 1)
                if (y > 0) d = min(d, distance[i - width].toInt() + 1)
                distance[i] = min(d, FADE_RADIUS + 1).toByte()
            }
        }
        for (y in height - 1 downTo 0) {
            for (x in width - 1 downTo 0) {
                val i = y * width + x
                var d = distance[i].toInt()
                if (x + 1 < width) d = min(d, distance[i + 1].toInt() + 1)
                if (y + 1 < height) d = min(d, distance[i + width].toInt() + 1)
                distance[i] = min(d, FADE_RADIUS + 1).toByte()
            }
        }
        var affected = 0
        for (i in 0 until size) {
            val d = distance[i].toInt()
            if (d > FADE_RADIUS) continue
            // At the failed pixel and its immediate neighbors: native identity. The
            // remaining 2..6 pixel transition is a gain on the optional detail only.
            val t = ((d - 1).toFloat() / (FADE_RADIUS - 1)).coerceIn(0f, 1f)
            val gain = t * t * (3f - 2f * t)
            primary[i] = if (primary[i].isFinite()) primary[i] * gain else 0f
            affected++
        }
        return Result(primary, disagree, quadCount, affected, false)
    }
}
