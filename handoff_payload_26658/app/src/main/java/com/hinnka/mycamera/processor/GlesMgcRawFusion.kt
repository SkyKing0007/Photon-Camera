package com.hinnka.mycamera.processor

import com.hinnka.mycamera.utils.PLog
import java.io.File

/**
 * IRIS_26560_SABRE_ONLY_RAW_FUSION_OWNER
 *
 * Motion and Night now have one reconstruction owner: GlesIris26545SabreProcessor. The obsolete
 * selectable Spatial-RGB entry point was removed, while the proven Sabre host and every low-level
 * Spatial-named utility that Sabre still compiles/calls remain untouched.
 */
internal class GlesMgcRawFusion(
    private val width: Int,
    private val height: Int,
    private val cfaPattern: Int,
    private val blackLevel: FloatArray,
    private val whiteLevel: Int,
    private val whiteBalanceGains: FloatArray,
    private val noiseProfileSelection: RawNoiseProfileSelection,
    private val lensShading: FloatArray?,
    private val lensShadingWidth: Int,
    private val lensShadingHeight: Int,
    private val allowSabreShadowLong: Boolean = false,
    private val preserveExtendedHdrThroughVgn: Boolean = false,
    private val useCurrentGlContext: Boolean,
    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage,
    private val exportNormalStackedDng: Boolean = false,
    private val vgnChromaCorrectionStrength: Float = 1f,
    private val enableSabreSuperRes: Boolean = false,
    private val sabreSuperResTempDir: File? = null,
) {
    fun processFrames(frames: List<RawStackFrame>): RawStackResult? {
        if (frames.isEmpty()) return null
        if (cfaPattern !in 0..3) {
            PLog.e(TAG, "Iris Sabre reconstruction supports only the four 2x2 Bayer layouts; cfa=$cfaPattern")
            frames.forEach { it.image.close() }
            return null
        }
        return GlesIris26545SabreProcessor(
            width = width,
            height = height,
            cfaPattern = cfaPattern,
            blackLevel = blackLevel,
            whiteLevel = whiteLevel,
            whiteBalanceGains = whiteBalanceGains,
            noiseProfileSelection = noiseProfileSelection,
            lensShading = lensShading,
            lensShadingWidth = lensShadingWidth,
            lensShadingHeight = lensShadingHeight,
            useCurrentGlContext = useCurrentGlContext,
            exportGpuLinearRgbSource = exportGpuLinearRgbSource,
            gpuLinearRgbStorage = gpuLinearRgbStorage,
            exportNormalStackedDng = exportNormalStackedDng,
            vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,
            allowShadowLong = allowSabreShadowLong,
            preserveExtendedHdrThroughVgn = preserveExtendedHdrThroughVgn,
            enableSuperRes = enableSabreSuperRes,
            superResTempDir = sabreSuperResTempDir,
        ).processFrames(frames)
    }

    private companion object {
        const val TAG = "GlesMgcRawFusion"
    }
}
