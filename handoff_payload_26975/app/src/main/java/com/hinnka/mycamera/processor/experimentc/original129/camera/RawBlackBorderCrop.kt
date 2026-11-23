package com.hinnka.mycamera.processor.experimentc.original129.camera

import kotlin.math.roundToInt

data class RawBlackBorderCrop(
    val leftPx: Int = 0,
    val topPx: Int = 0,
    val rightPx: Int = 0,
    val bottomPx: Int = 0
) {
    val hasCrop: Boolean
        get() = leftPx > 0 || topPx > 0 || rightPx > 0 || bottomPx > 0

    /**
     * Maps native RAW crop margins onto a uniformly resampled output pixel grid.
     *
     * ISZ lens settings are recorded against the camera's native RAW dimensions. RAWmax may
     * produce a larger RAW grid, so keeping the native pixel counts would leave part of the
     * configured black border in the rendered image.
     */
    internal fun scaledForOutput(outputScale: Float): RawBlackBorderCrop {
        if (!hasCrop || !outputScale.isFinite() || outputScale <= 0f || outputScale == 1f) {
            return this
        }

        fun scaleMargin(value: Int): Int {
            return (value.coerceAtLeast(0).toFloat() * outputScale)
                .roundToInt()
                .coerceAtLeast(0)
        }

        return RawBlackBorderCrop(
            leftPx = scaleMargin(leftPx),
            topPx = scaleMargin(topPx),
            rightPx = scaleMargin(rightPx),
            bottomPx = scaleMargin(bottomPx)
        )
    }
}
