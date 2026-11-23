package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

data class DcpProfile(
    val profileName: String,
    val calibrationIlluminant1: Int,
    val calibrationIlluminant2: Int,
    val baselineExposureOffset: Float,
    val defaultBlackRender: DcpDefaultBlackRender = DcpDefaultBlackRender.Auto,
    val supportsOverrange: Boolean = false,
    val colorMatrix1: FloatArray?,
    val colorMatrix2: FloatArray?,
    val forwardMatrix1: FloatArray?,
    val forwardMatrix2: FloatArray?,
    val hueSatDeltas1: DcpHueSatMap?,
    val hueSatDeltas2: DcpHueSatMap?,
    val lookTable: DcpHueSatMap?,
    val toneCurve: DcpToneCurve?,
    val analogBalance: FloatArray? = null,
    val cameraCalibration1: FloatArray? = null,
    val cameraCalibration2: FloatArray? = null
) {
    // Parsed profile assets are immutable. Share this curve across AWB-dependent
    // render plans; a reloaded or copied profile owns a fresh lazy cache.
    internal val toneCurveLut: FloatArray? by lazy {
        toneCurve?.takeIf { it.isValid }?.toLut()
    }
}
