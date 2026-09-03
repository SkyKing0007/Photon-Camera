package com.hinnka.mycamera.processor

import com.hinnka.mycamera.utils.PLog
import java.io.File

/**
 * IRIS_26545_SABRE_OWNER
 * Iris-owned adapter for the pinned MGC Sabre algorithm.
 *
 * Native MGC SabreProcessor entry point.
 *
 * Sabre has its own frame admission and full merge/resolve pipeline. It does not use Spatial's
 * Shasta bracket composition, Bento ultrashort path, Spatial Bayer normalization, or Spatial RGB
 * reconstruction.
 */
internal class GlesIris26545SabreProcessor(
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
    private val useCurrentGlContext: Boolean,
    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage,
    private val exportNormalStackedDng: Boolean,
    private val vgnChromaCorrectionStrength: Float = 1f,
    private val allowShadowLong: Boolean = false,
    private val enableSuperRes: Boolean = false,
    private val superResTempDir: File? = null,
) {
    fun processFrames(frames: List<RawStackFrame>): RawStackResult? {
        if (frames.isEmpty()) return null
        if (cfaPattern !in 0..3) {
            PLog.e(TAG, "MGC Sabre supports only the four 2x2 Bayer layouts; cfa=$cfaPattern")
            frames.forEach { it.image.close() }
            return null
        }

        val baseIndex = frames.indexOfFirst { it.role == RawBurstFrameRole.NORMAL }
        if (baseIndex < 0) {
            PLog.e(TAG, "MGC Sabre has no NORMAL base frame")
            frames.forEach { it.image.close() }
            return null
        }
        val baseExposure = frames[baseIndex].exposureProduct
            .takeIf { it.isFinite() && it > 0.0 }
        val highlightShortIndices = frames.indices.filter { index ->
            frames[index].role == RawBurstFrameRole.HIGHLIGHT_SHORT
        }
        require(highlightShortIndices.size <= 1) {
            "26587 Sabre accepts at most one HIGHLIGHT_SHORT, got ${highlightShortIndices.size}"
        }
        highlightShortIndices.forEach { index ->
            val exposure = frames[index].exposureProduct
            require(baseExposure != null && exposure.isFinite() && exposure > 0.0 && exposure < baseExposure) {
                "26587 HIGHLIGHT_SHORT must be lower exposure than NORMAL base"
            }
        }
        val admittedIndices = buildList {
            add(baseIndex)
            frames.indices.filterTo(this) { index ->
                index != baseIndex && frames[index].role == RawBurstFrameRole.NORMAL
            }
            if (allowShadowLong && baseExposure != null) {
                frames.indices.filterTo(this) { index ->
                    val frame = frames[index]
                    frame.role == RawBurstFrameRole.SHADOW_LONG &&
                        frame.exposureProduct.isFinite() && frame.exposureProduct > baseExposure
                }
            }
            // IRIS_26587: keep SHORT last so NORMAL Sabre support is frozen before auxiliary tests.
            addAll(highlightShortIndices)
        }
        val admittedSet = admittedIndices.toSet()
        val excluded = frames.indices.filterNot(admittedSet::contains)
        excluded.forEach { frames[it].image.close() }
        val admitted = admittedIndices.map(frames::get)
        val normalCount = admitted.count { it.role == RawBurstFrameRole.NORMAL }
        val longCount = admitted.count { it.role == RawBurstFrameRole.SHADOW_LONG }
        val highlightShortCount = admitted.count { it.role == RawBurstFrameRole.HIGHLIGHT_SHORT }
        PLog.i(
            TAG,
            "IRIS_26587_SABRE_OWNER_ACTIVE base=${frames[baseIndex].frameNumber} " +
                "normal=$normalCount shadowLong=$longCount highlightShort=$highlightShortCount " +
                "allowShadowLong=$allowShadowLong excluded=${excluded.size} " +
                "normalMergeOwner=true shortReferenceImmutable=true spatial=false bento=false output=linear-rgb " +
                "superRes=$enableSuperRes srEvidence=NORMAL_ONLY shortContribution=NORMAL_ACCUMULATOR_EXCLUDED",
        )
        /* IRIS_26545_V1_2_SABRE_LOW_LEVEL_ISOLATION
         * Match bjzhou's current Sabre architecture: the shared low-level GL class is used only
         * as a carrier for processSabreFrames(). Its processFrames() dispatches SABRE before any
         * Spatial scheduling/reconstruction code, and the low-level method now hard-asserts both
         * processorPipeline=SABRE and mergeMethod=SABRE.
         */
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
            enableSabreSuperRes = enableSuperRes,
            sabreSuperResTempDir = superResTempDir,
        ).processFrames(admitted)
    }

    private companion object {
        const val TAG = "Iris26545Sabre"
    }
}
