package com.hinnka.mycamera.processor

/** C's immutable, real donor-R8 measured residual readback. */
internal class Iris26975CMeasuredSabreResidual(
    val width: Int,
    val height: Int,
    q8: ShortArray,
    val meanVarianceMultiplier: Float,
) {
    private val frozenQ8 = q8.copyOf()
    init {
        require(width > 0 && height > 0 && frozenQ8.size == width*height &&
            frozenQ8.all { it.toInt() in 1..256 } &&
            meanVarianceMultiplier.isFinite() && meanVarianceMultiplier in 0f..1f)
    }
    /** No reference to shared A/B Spatial strength-map models from Experiment C. */
    fun copyQ8ForAudit(): ShortArray = frozenQ8.copyOf()
}
