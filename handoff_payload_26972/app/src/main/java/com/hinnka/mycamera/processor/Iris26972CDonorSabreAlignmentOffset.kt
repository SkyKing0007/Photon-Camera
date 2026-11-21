package com.hinnka.mycamera.processor

import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.sign

/** C-only exact bjzhou 1.29.0 per-alternate-frame Sabre grid shifts; source MgcSabreAlignmentOffset.kt. */
internal data class Iris26972CDonorSabreAlignmentOffset(val x: Int, val y: Int) {
    companion object {
        val ZERO = Iris26972CDonorSabreAlignmentOffset(0, 0)
        private val xSequence = floatArrayOf(-0.45f,-0.05f,0.35f,-0.15f,0.25f,-0.25f,0.15f,-0.35f,0.05f,0.45f)
        private val ySequence = floatArrayOf(
            -0.4811529517f, -0.00901698973f, 0.4631189704f, 0.372949034f,
            -0.1549150348f, -0.2450849712f, 0.227050975f, 0.1368810385f,
            -0.3909830153f, 0.08115295321f,
        )
        fun tileSupport(baseFrameSnr: Float): Int {
            require(baseFrameSnr.isFinite() && baseFrameSnr >= 0f)
            return when {
                baseFrameSnr < 0.5f -> 32
                baseFrameSnr < 2.7f -> 64
                else -> 16
            }
        }
        fun forFrame(frameIndex: Int, tileStride: Int): Iris26972CDonorSabreAlignmentOffset {
            require(frameIndex in 0..49 && tileStride > 0)
            if (frameIndex == 0) return ZERO
            val index = (frameIndex - 1) % xSequence.size
            fun scaled(value: Float): Int {
                val product = value * tileStride
                // Donor FRINTA: nearest integer, halfway away from zero.
                return (sign(product) * floor(abs(product) + 0.5f)).toInt()
            }
            return Iris26972CDonorSabreAlignmentOffset(
                scaled(xSequence[index]), scaled(ySequence[index]))
        }
    }
}
