package com.hinnka.mycamera.processor.experimentc.original129.processor

import android.graphics.Rect
import com.hinnka.mycamera.processor.experimentc.original129.utils.PLog
import java.nio.ByteBuffer
import com.hinnka.mycamera.processor.experimentc.original129.raw.DngProfileGainTableMap
import com.hinnka.mycamera.processor.experimentc.original129.raw.MgcSpatialStrengthMap
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawProfileToneMapMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawSceneAERawStats

enum class RawStackBufferLayout {
    CFA,
    LINEAR_RGB,
}

enum class MgcSpatialOutputMode {
    BAYER,
    RGB,
}

/** Merge implementations exposed by MGC's ShotParams::merge_method_override. */
enum class MgcMergeMethod(val mgcValue: Int) {
    WIENER(0),
    SABRE(1),
    SPATIAL_BAYER(2),
    SPATIAL_RGB(3),
}

/** HDR+ fusion modes exposed in professional-mode settings. */
enum class MgcRawMaxMode {
    SABRE,
    SPATIAL;

    companion object {
        val DEFAULT: MgcRawMaxMode = SABRE
    }

    val supportsBracketExposure: Boolean
        get() = this == SPATIAL

    val outputMode: MgcSpatialOutputMode
        get() = MgcSpatialOutputMode.RGB

    val mergeMethod: MgcMergeMethod
        get() = when (this) {
            SABRE -> MgcMergeMethod.SABRE
            SPATIAL -> MgcMergeMethod.SPATIAL_RGB
        }
}

/**
 * Physical storage of an opaque LinearRaw texture. RGBA16F is used only for the direct Spatial
 * default-denoise handoff; persistent render/DNG sources use RGBA16UI.
 */
enum class GpuLinearRgbStorage {
    RGBA16UI,
    RGBA16F,
}

/** Opaque LinearRaw texture owned by the persistent RAW renderer context. */
data class GpuLinearRgbSource(
    val textureId: Int,
    val width: Int,
    val height: Int,
    val samplesPerPixel: Int = 4,
    val stackCompletionTimeline: GpuStackCompletionTimeline? = null,
    val storage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
)

/**
 * Opaque normalized Bayer texture exported by a stacker into the persistent RAW renderer context.
 * Storage is full-resolution R16UI CFA. It may only be consumed or released on that context's GL
 * dispatcher.
 */
data class GpuBayerSource(
    val textureId: Int,
    val width: Int,
    val height: Int,
    val stackCompletionTimeline: GpuStackCompletionTimeline? = null,
)

data class RawStackResult(
    /** Null when a GPU source is exported and CPU/DNG materialization has been deferred. */
    var fusedBayerBuffer: ByteBuffer?,
    val width: Int,
    val height: Int,
    val isNormalizedSensorData: Boolean,
    val blackLevel: FloatArray = floatArrayOf(0f, 0f, 0f, 0f),
    val fusedBayerUsesNativeAllocator: Boolean = false,
    val profileGainTableMap: DngProfileGainTableMap? = null,
    val profileToneMapMode: RawProfileToneMapMode = RawProfileToneMapMode.Default,
    val diagnostics: RawStackDiagnostics? = null,
    val bufferLayout: RawStackBufferLayout = RawStackBufferLayout.CFA,
    val inputRowStepSamples: Int? = null,
    val inputColStepSamples: Int? = null,
    val baselineExposureEv: Float? = null,
    val gpuLinearRgbSource: GpuLinearRgbSource? = null,
    val gpuBayerSource: GpuBayerSource? = null,
    /** Reference-frame sensor maxima used by MGC Fast Moments after a LinearRaw merge. */
    val fastMomentsRawStats: RawSceneAERawStats? = null,
    /** True only when lens-shading gain has already been multiplied into the fused pixels. */
    val lensShadingCorrectionApplied: Boolean = false,
    val mergedFrameCount: Int = 1,
    /**
     * MGC's normalized 128-bin merged NoiseModel correlation spectrum.
     *
     * Null means the merged model is unavailable; a requested default merge-denoise pass must fail.
     */
    val mgcDenoiseCorrelation: FloatArray? = null,
    /**
     * Normalized camera-RGB read variance emitted by the selected MGC merge branch.
     */
    val mgcDenoiseReadNoise: FloatArray? = null,
    /**
     * Normalized camera-RGB shot coefficient emitted by the selected MGC merge branch.
     */
    val mgcDenoiseShotNoise: FloatArray? = null,
    /**
     * Exact process-local Q8 variance multiplier emitted by MGC Spatial and consumed before
     * DNG write.
     */
    val mgcSpatialStrengthMap: MgcSpatialStrengthMap? = null,
    /**
     * Merged output-frame SNR used by MGC FinishRaw to select luma/chroma tuning.
     * This is the linear signal-domain SNR, not ISO or sensor gain.
     */
    val mgcDenoiseTuningSnr: Float? = null,
    /** Reference-frame SNR for original MGC sharpen curve selection; not the merged SNR. */
    val mgcSharpenTuningSnr: Float? = null,
    /** MGC-derived attenuation applied to the final sharpen kernel. */
    val mgcSharpenAttenuationScale: Float? = null,
    /**
     * True only for the debug reference-only isolation path. This state is process-local and is
     * never persisted into RAW/DNG metadata.
     */
    val mgcSpatialReferenceOnlyDiagnostic: Boolean = false,
)

/**
 * Multi-Frame Stacker
 * 
 * Manages the native stacking process for burst captures.
 * Aligns and merges multiple frames to reduce noise and improve quality.
 */
object MultiFrameStacker {
    private const val TAG = "MultiFrameStacker"

    /** RAW-only Experiment C interface: original Pro-mode Sabre source below.
     * YUV/photo-mode merger removed: not reachable from Iris Experiment C.
     */
    @Synchronized
    fun processBurstRaw(
        frames: List<RawStackFrame>,
        cfaPattern: Int,
        outputMode: MgcSpatialOutputMode = MgcSpatialOutputMode.BAYER,
        mergeMethod: MgcMergeMethod = when (outputMode) {
            MgcSpatialOutputMode.BAYER -> MgcMergeMethod.SPATIAL_BAYER
            MgcSpatialOutputMode.RGB -> MgcMergeMethod.SPATIAL_RGB
        },
        masterBlackLevel: FloatArray = floatArrayOf(0f, 0f, 0f, 0f),
        whiteLevel: Int = 1023,
        whiteBalanceGains: FloatArray = floatArrayOf(1f, 1f, 1f, 1f),
        cameraWhite: FloatArray,
        noiseProfileSelection: RawNoiseProfileSelection,
        lensShading: FloatArray? = null,
        lensShadingWidth: Int = 0,
        lensShadingHeight: Int = 0,
        applyLensShadingCorrection: Boolean = true,
        sourceBounds: Rect? = null,
        useCurrentGlContext: Boolean = false,
        exportGpuLinearRgbSource: Boolean = false,
        gpuLinearRgbStorage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
        enableHdrFusion: Boolean = true,
        photo1291: Boolean = false,
    ): RawStackResult? {
        if (frames.isEmpty()) return null
        val images = frames.map { it.image }
        val sourceWidth = images[0].width
        val sourceHeight = images[0].height
        val physicalSourceBounds = sourceBounds ?: Rect(0, 0, sourceWidth, sourceHeight)
        require(
            physicalSourceBounds.left >= 0 && physicalSourceBounds.top >= 0 &&
                physicalSourceBounds.right <= sourceWidth &&
                physicalSourceBounds.bottom <= sourceHeight &&
                !physicalSourceBounds.isEmpty &&
                (physicalSourceBounds.width() and 1) == 0 &&
                (physicalSourceBounds.height() and 1) == 0
        ) { "RAW physical crop must contain complete Bayer cells: $physicalSourceBounds" }
        // Fusion and FinishRaw consume the native sensor grid. Display scaling follows sharpening.
        RawStackRuntimeDebug.d(TAG) {
            "Starting MGC ${if (mergeMethod == MgcMergeMethod.SABRE) "Sabre" else "Spatial ${outputMode.name}"} " +
                "fusion for ${images.size} frames source=${sourceWidth}x$sourceHeight " +
                "physicalCrop=$physicalSourceBounds " +
                "Pattern=$cfaPattern " +
                "BL=${masterBlackLevel.joinToString()} WL=$whiteLevel " +
                "noiseProfile=${noiseProfileSelection.id} " +
                "legacyHdrFlag=$enableHdrFusion"
        }
        val stackLensShading = validLensShadingOrNull(
            lensShading = lensShading,
            width = lensShadingWidth,
            height = lensShadingHeight,
            enabled = applyLensShadingCorrection && outputMode == MgcSpatialOutputMode.RGB,
        )
        return GlesMgcRawFusion(
            sourceWidth = sourceWidth,
            sourceHeight = sourceHeight,
            sourceBounds = physicalSourceBounds,
            cfaPattern = cfaPattern,
            blackLevel = masterBlackLevel,
            whiteLevel = whiteLevel,
            whiteBalanceGains = whiteBalanceGains,
            cameraWhite = cameraWhite,
            noiseProfileSelection = noiseProfileSelection,
            lensShading = stackLensShading,
            lensShadingWidth = if (stackLensShading != null) lensShadingWidth else 0,
            lensShadingHeight = if (stackLensShading != null) lensShadingHeight else 0,
            outputMode = outputMode,
            mergeMethod = mergeMethod,
            useCurrentGlContext = useCurrentGlContext,
            exportGpuLinearRgbSource = exportGpuLinearRgbSource,
            gpuLinearRgbStorage = gpuLinearRgbStorage,
            photo1291 = photo1291,
        ).processFrames(frames)
    }

    private fun validLensShadingOrNull(
        lensShading: FloatArray?,
        width: Int,
        height: Int,
        enabled: Boolean,
    ): FloatArray? {
        if (!enabled || lensShading == null || width <= 0 || height <= 0) return null
        return lensShading.takeIf { it.size >= width * height * 4 }
    }

}
