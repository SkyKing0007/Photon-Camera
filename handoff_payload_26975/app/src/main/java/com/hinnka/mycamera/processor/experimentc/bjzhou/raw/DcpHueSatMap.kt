package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

data class DcpHueSatMap(
    val hueDivisions: Int,
    val satDivisions: Int,
    val valueDivisions: Int,
    val values: FloatArray,
    val encoding: Int = ENCODING_LINEAR
) {
    companion object {
        const val ENCODING_LINEAR = 0
        const val ENCODING_SRGB = 1
    }

    val isValid: Boolean
        get() = hueDivisions > 0 &&
            satDivisions > 0 &&
            valueDivisions > 0 &&
            values.size == hueDivisions * satDivisions * valueDivisions * 3
}
