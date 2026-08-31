package com.hinnka.mycamera.processor

import com.hinnka.mycamera.raw.MgcSpatialStrengthMap
import java.nio.ByteBuffer

enum class RawStackBufferLayout { CFA, LINEAR_RGB }
enum class MgcSpatialOutputMode { BAYER, RGB }
enum class MgcMergeMethod(val mgcValue: Int) {
    WIENER(0), SABRE(1), SPATIAL_BAYER(2), SPATIAL_RGB(3),
}
enum class GpuLinearRgbStorage { RGBA16UI, RGBA16F }

data class GpuLinearRgbSource(
    val textureId: Int,
    val width: Int,
    val height: Int,
    val samplesPerPixel: Int = 4,
    val stackCompletionTimeline: GpuStackCompletionTimeline? = null,
    val storage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
)

data class GpuBayerSource(
    val textureId: Int,
    val width: Int,
    val height: Int,
    val stackCompletionTimeline: GpuStackCompletionTimeline? = null,
)

data class RawStackResult(
    var fusedBayerBuffer: ByteBuffer?,
    val width: Int,
    val height: Int,
    val isNormalizedSensorData: Boolean,
    val blackLevel: FloatArray = floatArrayOf(0f, 0f, 0f, 0f),
    val fusedBayerUsesNativeAllocator: Boolean = false,
    val bufferLayout: RawStackBufferLayout = RawStackBufferLayout.CFA,
    val inputRowStepSamples: Int? = null,
    val inputColStepSamples: Int? = null,
    val baselineExposureEv: Float? = null,
    val gpuLinearRgbSource: GpuLinearRgbSource? = null,
    val gpuBayerSource: GpuBayerSource? = null,
    val lensShadingCorrectionApplied: Boolean = false,
    val mergedFrameCount: Int = 1,
    val mgcDenoiseCorrelation: FloatArray? = null,
    val mgcDenoiseReadNoise: FloatArray? = null,
    val mgcDenoiseShotNoise: FloatArray? = null,
    val mgcSpatialStrengthMap: MgcSpatialStrengthMap? = null,
    val mgcSabreNoiseModelScale: Float? = null,
    /* IRIS_26537_REFERENCE_SNR_PROVENANCE
     * Pre-merge/reference SNR is kept separate from propagated post-merge denoise SNR.
     * It is diagnostic/activation evidence only; FinishRaw denoise remains tuned by the
     * propagated output-noise model.
     */
    val mgcReferenceSnr: Float? = null,
    val mgcDenoiseTuningSnr: Float? = null,
    val mgcSharpenTuningSnr: Float? = null,
    val mgcSharpenAttenuationScale: Float? = null,
    val mgcSpatialReferenceOnlyDiagnostic: Boolean = false,
    /* IRIS_26532_STREAMED_SUPERRES_RESULT
     * High-resolution SR evidence is streamed while Spatial bands are resident. The normal
     * GPU source remains native-sized so the proven 26531 chroma/tone path never allocates
     * full-frame 2x post-processing surfaces.
     */
    val superResDetailPath: String? = null,
    val superResLinearRawPath: String? = null,
    val superResWidth: Int = 0,
    val superResHeight: Int = 0,
    /* IRIS_26564_TRUE_2X_CFA_RECONSTRUCTION
     * True 2x is a streamed camera-linear RGB16F carrier reconstructed directly from aligned
     * NORMAL RAW/CFA observations. It never names the native-RGB-upscale/detail sidecar as an
     * SR owner. Phase support counts independent 2x2 subpixel-flow bins, not accepted frames.
     */
    val true2xLinearRgbPath: String? = null,
    /* IRIS_26568_FUSED_TRUE2X_RENDER_CARRIER
     * JPEG-only RGB16F carrier generated while the direct-CFA tile, phase occupancy and native
     * Sabre/VGN guide are simultaneously GPU-resident. It preserves Sabre/VGN RGB ratios by
     * applying only the proven 26567 scalar detail factor. DNG never consumes this derivative.
     */
    val true2xRenderRgbPath: String? = null,
    /* Native-resolution post-VGN camera-linear RGB guide. JPEG rendering may consume this only
     * as the proven low-frequency VGN chroma correction; DNG must never consume it. */
    val true2xNativeVgnGuidePath: String? = null,
    /* One unsigned byte per true-2x pixel: exact accepted distinct 2x2 phase count 0..4.
     * JPEG-only reliability evidence; never consumed by DNG.
     */
    val true2xPhaseSupportPath: String? = null,
    val true2xWidth: Int = 0,
    val true2xHeight: Int = 0,
    val true2xBackend: String? = null,
    val true2xPhaseSupportMean: Float = 0f,
    val true2xPhaseSupportP10: Float = 0f,
    val true2xReconstructionMs: Long = 0L,
    /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
    val normalStackedDngRaw16: ByteBuffer? = null,
    val normalStackedDngFrameCount: Int = 0,
    /* IRIS_26522_NORMALIZED16_DNG_METADATA */
    val normalStackedDngNoiseProfile: DoubleArray? = null,
    val normalStackedDngSupportMin: Float = 1f,
    val normalStackedDngSupportP01: Float = 1f,
    val normalStackedDngSupportP10: Float = 1f,
    val normalStackedDngSupportMedian: Float = 1f,
    val normalStackedDngSupportMean: Float = 1f,
    val normalStackedDngSupportMax: Float = 1f,
    val normalStackedDngNoiseEquivalentSupport: Float = 1f,
)
