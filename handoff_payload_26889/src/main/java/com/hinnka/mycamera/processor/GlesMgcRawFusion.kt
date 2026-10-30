package com.hinnka.mycamera.processor

import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
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
    /* IRIS_26718_NORMAL_HIGH_ZOOM_DETAIL_TRANSPORT
     * Independent of the user Super Res switch. Native Sabre RGB remains the color owner.
     */
    private val enableHighZoomDetail: Boolean = false,
    private val highZoomSourceZoom: Float = 1f,
    /* IRIS_26762_FROZEN_ADAPTIVE_CHROMA_TRANSPORT */
    private val adaptiveSnrChromaDenoise: Float = 1f,
    private val residualChromaCustom: Boolean = false,
    private val edgeFalseColor26778: IrisMotionSettings.EdgeFalseColorTunables.Snapshot = IrisMotionSettings.EdgeFalseColorTunables.defaults(),
    /* IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION_CONTEXT: downstream fusion context only. */
    private val referenceProtectionEv: Float = 0f,
    private val exactHistorical26850: Boolean = false,
    /* IRIS_26856_B_ONLY_PACKED_CFA_CONSUMER_TRANSPORT
     * Only the B owner supplies this callback. A/26850 keeps null and never
     * allocates the packed-CFA handoff. Synchronous: no texture escapes scope. */
    private val iris26856AmazeCfaConsumer: ((packed: Int, outputRgb: Int,
        rawWidth: Int, rawHeight: Int, bayerPattern: Int, wb: FloatArray) -> Int)? = null,
    private val iris26856RawrColor: GlesIris26856RawrColorContract.Snapshot? = null,
    /* 26856 B-only independently phase-reconstructed 2x CFA. Never enables A/VGN 2x. */
    private val iris26856BTrue2x: Boolean = false,
    /* 26856 B-only fast publication: A+B and historical A keep their exact old sequence. */
    private val iris26856BOnlyIndependentPublication: Boolean = false,
    /* IRIS_26864_KOTLIN_ADAPTER_TRANSPORT_FAILURE_39708593393
     * Pass the frozen B-owned RAWR burst-noise authority and synchronous true-2x
     * Vulkan callback through Fusion -> Sabre to the live spatial stacker.
     * Historical A continues with the default false/null arguments. */
    private val iris26864RealRawrOwnsBurstNoise: Boolean = false,
    private val iris26868ReferenceTimestampNs: Long = -1L,
    private val iris26889BOffLongAllowed: () -> Boolean = { true },
    private val iris26864NativeWronski2x: ((outputRgb: Int, outputSensorClip: Int) -> Unit)? = null,
) {
    fun processFrames(frames: List<RawStackFrame>): RawStackResult? {
        if (frames.isEmpty()) return null
        if (cfaPattern !in 0..3) {
            PLog.e(TAG, "Iris Sabre reconstruction supports only the four 2x2 Bayer layouts; cfa=$cfaPattern")
            frames.forEach { it.image.close() }
            return null
        }
        /* IRIS_26868_BYPASS_SABRE_WRAPPER
         * Direct B uses the already-frozen complete RAW population, not
         * SabreProcessor's frame admission, flow/merge, shader initialization
         * or reference reordering. The low-level B dispatcher precedes any
         * MGC/Sabre allocation and invokes pinned native RAWR HDRq directly.
         * A/NIGHT and the exact >=1.10x A route never enter this branch.
         */
        if (iris26856BOnlyIndependentPublication && iris26864RealRawrOwnsBurstNoise) {
            check(!exactHistorical26850 && iris26856AmazeCfaConsumer != null &&
                iris26856RawrColor != null) {
                "26868 direct B requires an explicit real native ownership contract"
            }
            return GlesMgcRawSpatialStacker(
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
                outputMode = MgcSpatialOutputMode.RGB,
                mergeMethod = MgcMergeMethod.SABRE,
                outputScale = 1f,
                useCurrentGlContext = useCurrentGlContext,
                exportGpuLinearRgbSource = exportGpuLinearRgbSource,
                gpuLinearRgbStorage = gpuLinearRgbStorage,
                processorPipeline = MgcRawProcessorPipeline.SABRE,
                exportNormalStackedDng = exportNormalStackedDng,
                vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,
                preserveExtendedHdrThroughVgn = preserveExtendedHdrThroughVgn,
                enableSabreSuperRes = enableSabreSuperRes,
                sabreSuperResTempDir = sabreSuperResTempDir,
                enableHighZoomDetail = enableHighZoomDetail,
                highZoomSourceZoom = highZoomSourceZoom,
                adaptiveSnrChromaDenoise = adaptiveSnrChromaDenoise,
                residualChromaCustom = residualChromaCustom,
                edgeFalseColor26778 = edgeFalseColor26778,
                referenceProtectionEv = referenceProtectionEv,
                iris26856AmazeCfaConsumer = iris26856AmazeCfaConsumer,
                iris26856RawrColor = iris26856RawrColor,
                iris26856BTrue2x = iris26856BTrue2x,
                iris26856BOnlyIndependentPublication = true,
                iris26864RealRawrOwnsBurstNoise = true,
                iris26868ReferenceTimestampNs = iris26868ReferenceTimestampNs,
                iris26889BOffLongAllowed = iris26889BOffLongAllowed,
                iris26864NativeWronski2x = iris26864NativeWronski2x,
            ).processFrames(frames)
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
            enableHighZoomDetail = enableHighZoomDetail,
            highZoomSourceZoom = highZoomSourceZoom,
            adaptiveSnrChromaDenoise = adaptiveSnrChromaDenoise,
            residualChromaCustom = residualChromaCustom,
            edgeFalseColor26778 = edgeFalseColor26778,
            referenceProtectionEv = referenceProtectionEv,
            exactHistorical26850 = exactHistorical26850,
            iris26856AmazeCfaConsumer = iris26856AmazeCfaConsumer,
            iris26856RawrColor = iris26856RawrColor,
            iris26856BTrue2x = iris26856BTrue2x,
            iris26856BOnlyIndependentPublication = iris26856BOnlyIndependentPublication,
            iris26864RealRawrOwnsBurstNoise = iris26864RealRawrOwnsBurstNoise,
            iris26864NativeWronski2x = iris26864NativeWronski2x,
        ).processFrames(frames)
    }

    private companion object {
        const val TAG = "GlesMgcRawFusion"
    }
}
