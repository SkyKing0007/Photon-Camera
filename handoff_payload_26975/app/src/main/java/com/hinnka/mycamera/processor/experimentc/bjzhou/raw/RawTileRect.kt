package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

internal data class RawTileRect(
    val left: Int,
    val top: Int,
    val right: Int,
    val bottom: Int,
) {
    init {
        require(left >= 0 && top >= 0)
        require(right > left && bottom > top)
    }

    val width: Int get() = right - left
    val height: Int get() = bottom - top

    fun contains(other: RawTileRect): Boolean {
        return left <= other.left && top <= other.top &&
            right >= other.right && bottom >= other.bottom
    }
}
