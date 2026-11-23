package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

// Exact data-class excerpt from pinned bjzhou DcpProfile.kt (not its DCP parser).
data class DcpRenderPlan(
    val profileName: String,
    val workingColorSpace: ColorSpace,
    val baselineExposureOffset: Float,
    val defaultBlackRender: DcpDefaultBlackRender,
    val supportsOverrange: Boolean = false,
    val colorCorrectionMatrix: FloatArray,
    val cameraWhite: FloatArray = floatArrayOf(1f, 1f, 1f),
    val hueSatMap: DcpHueSatMap?,
    val lookTable: DcpHueSatMap?,
    val toneCurveLut: FloatArray?
)
