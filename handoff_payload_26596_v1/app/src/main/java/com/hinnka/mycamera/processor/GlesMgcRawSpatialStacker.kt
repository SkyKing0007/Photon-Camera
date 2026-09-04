package com.hinnka.mycamera.processor

import android.graphics.ImageFormat
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.GLES30
import android.opengl.GLES31
import android.util.Half
import com.hinnka.mycamera.camera.MultiFrameConfig
import com.hinnka.mycamera.model.SafeImage
import com.hinnka.mycamera.raw.MgcSpatialStrengthMap
import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative
import com.particlesdevs.photoncamera.util.MotionTrace
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.ceil
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.sqrt

internal enum class MgcRawProcessorPipeline {
    SPATIAL,
    SABRE,
}

/**
 * Independent GLES MGC Spatial RAW merge pipeline.
 *
 * The stage order, constants and shader equations come from this APK's libgcastartup.so. The
 * recovered MGC parameter-generation equations are cross-checked against Google's published
 * kernel units and SNR tuning range. The Bayer output preserves the CFA lattice. The RGB output
 * performs joint RAW-domain G/R-G/B-G reconstruction at the requested output scale while keeping
 * MGC alignment, rejection, Bento admission and propagated-noise postprocessing authoritative.
 */
internal class GlesMgcRawSpatialStacker(
    private val width: Int,
    private val height: Int,
    private val cfaPattern: Int,
    blackLevel: FloatArray,
    whiteLevel: Int,
    whiteBalanceGains: FloatArray,
    private val noiseProfileSelection: RawNoiseProfileSelection,
    private val lensShading: FloatArray?,
    private val lensShadingWidth: Int,
    private val lensShadingHeight: Int,
    private val outputMode: MgcSpatialOutputMode,
    private val mergeMethod: MgcMergeMethod = when (outputMode) {
        MgcSpatialOutputMode.BAYER -> MgcMergeMethod.SPATIAL_BAYER
        MgcSpatialOutputMode.RGB -> MgcMergeMethod.SPATIAL_RGB
    },
    outputScale: Float,
    private val useCurrentGlContext: Boolean,
    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
    private val processorPipeline: MgcRawProcessorPipeline = MgcRawProcessorPipeline.SPATIAL,
    private val exportNormalStackedDng: Boolean = false,
    // Iris has no PhotonCoreImagingTuning owner. Keep current-MGC's optional Sabre override
    // at this low-level boundary while defaulting to the exact adaptive SNR interpolation.
    private val sabreMergeGradientThreshold: Float? = null,
    private val vgnChromaCorrectionStrength: Float = 1f,
    private val enableSabreSuperRes: Boolean = false,
    private val sabreSuperResTempDir: File? = null,
) {
    private data class TextureLevel(
        val texture: Int,
        val width: Int,
        val height: Int,
        val scaleToBayerQuads: Float,
    )

    private data class Alignment(
        val texture: Int,
        val gridWidth: Int,
        val gridHeight: Int,
        val tileStride: Int,
        val scaleToBayerQuads: Float,
        val gridMin: Int,
    )

    /** IRIS_26545 Sabre owns sparse normalized flow plus its sampling transform. */
    private data class SabreConvertedAlignment(
        val texture: Int,
        val scaleX: Float,
        val scaleY: Float,
        val offsetX: Float,
        val offsetY: Float,
    ) {
        companion object {
            fun constant(texture: Int) = SabreConvertedAlignment(
                texture = texture,
                scaleX = 0f,
                scaleY = 0f,
                offsetX = 0.5f,
                offsetY = 0.5f,
            )
        }
    }

    /* IRIS_26564_TRUE_2X_PERSISTED_SABRE_EVIDENCE
     * Sabre's flow/covariance/rejection products are transient GPU resources. True 2x keeps only
     * compact immutable evidence required to reproduce the exact RBF estimator after the temporal
     * loop. RAW pixels stay owned by the existing SafeImage objects and are read by bounded region.
     */
    private data class True2xFrameEvidence(
        val frameIndex: Int,
        val calibration: FrameCalibration,
        val flowData: ByteBuffer,
        val flowWidth: Int,
        val flowHeight: Int,
        val flowScaleX: Float,
        val flowScaleY: Float,
        val flowOffsetX: Float,
        val flowOffsetY: Float,
        val covarianceFile: File,
        val covarianceWidth: Int,
        val covarianceHeight: Int,
        val rejectionFile: File?,
        val rejectionWidth: Int,
        val rejectionHeight: Int,
        val maxAbsFlowPixelsX: Float,
        val maxAbsFlowPixelsY: Float,
        val useFrameWeight: Boolean,
        val dominantPhaseBin: Int,
        val qualityScore: Float,
    )

    private data class True2xPhaseStats(
        val mean: Float,
        val p10: Float,
        val percentages: FloatArray,
    )

    private data class True2xResult(
        val linearRgbPath: String?,
        val renderRgbPath: String?,
        val nativeVgnGuidePath: String?,
        val phaseSupportPath: String?,
        val width: Int,
        val height: Int,
        val backend: String,
        val phaseSupportMean: Float,
        val phaseSupportP10: Float,
        val reconstructionMs: Long,
    )

    private data class True2xPackedRawRegion(
        val buffer: ByteBuffer,
        val width: Int,
        val height: Int,
        val rowStrideSamples: Int,
        val closeAction: () -> Unit,
    ) : AutoCloseable {
        override fun close() = closeAction()
    }

    /** Reference-only LK products shared by every current frame at one pyramid level. */
    private data class ReferenceAlignmentProducts(
        val referenceTexture: Int,
        val gridWidth: Int,
        val gridHeight: Int,
        val tileStride: Int,
        val tileSize: Int,
        val normalize: Boolean,
        val products0: Int,
        val products1: Int,
    )

    private data class PreparedTemporalFrame(
        val calibration: FrameCalibration,
        val flowTexture: Int,
        val bayerAlignmentTexture: Int,
        val weightTexture: Int,
    )

    private data class RgbMergeFrame(
        val imageIndex: Int,
        val calibration: FrameCalibration,
        val alignmentTexture: Int,
        val weightTexture: Int,
        val covarianceTexture: Int,
        val flowBounds: MgcSpatialRgbFlowBounds,
        val useFrameWeight: Boolean,
    )

    private data class RgbTileFrameRegion(
        val frame: RgbMergeFrame,
        val sourceRegion: MgcSpatialRgbRect,
        val uploadRegion: MgcSpatialRgbRect,
    )

    private data class RgbBandPlan(
        val bands: List<MgcSpatialRgbTile>,
        val work: List<Pair<MgcSpatialRgbTile, List<RgbTileFrameRegion>>>,
        val maximumOutputWidth: Int,
        val maximumOutputHeight: Int,
        val maximumDiagnosticWidth: Int,
        val maximumDiagnosticHeight: Int,
        val maximumSourceWidth: Int,
        val maximumSourceHeight: Int,
        val maximumUploadWidth: Int,
        val maximumUploadHeight: Int,
        val projectedGpuBytes: Long,
    )

    private data class RgbMergeOutput(
        val cpuBuffer: ByteBuffer?,
        val gpuTexture: Int,
        val diagnosticFixed16: PreparedTextureReadback?,
        val completionTimeline: GpuStackCompletionTimeline?,
    )

    /**
     * Full-output RGB accumulation used by the performance path.
     *
     * RAW stays frame-sequential: the current image is uploaded once, its temporal products are
     * consumed immediately, and only the two full-resolution additive accumulators survive until
     * normalization. Draw bands bound individual GPU jobs; they never trigger another RAW upload.
     */
    private data class OnlineRgbAccumulator(
        val semanticAccumulator: Int,
        val opponentWeightAccumulator: Int,
        val chromaGuideTexture: Int,
        val drawBands: List<MgcSpatialRgbTile>,
        val projectedGpuBytes: Long,
        var contributedFrames: Int = 0,
        var rawUploadCount: Int = 0,
        var rawUploadBytes: Long = 0L,
        var rawUploadNs: Long = 0L,
    )

    private data class TextureSpec(
        val width: Int,
        val height: Int,
        val internalFormat: Int,
        val filter: Int,
    )

    private data class ActiveMaskGpuCount(
        val activePixels: Int,
        val setupNs: Long,
        val submitNs: Long,
        val gpuWaitMs: Long,
        val mapNs: Long,
    )

    /**
     * Scratch textures reused by consecutive temporal frames in one GLES command stream.
     *
     * A frame may need multiple textures with the same specification, so acquisition is based on
     * both the specification and per-frame usage rather than call order. Reuse does not require a
     * fence: uploads, draws and later overwrites are submitted to the same context in dependency
     * order.
     */
    private class SequentialScratchTextures {
        private data class Entry(
            val spec: TextureSpec,
            val texture: Int,
            var used: Boolean = false,
        )

        private val entries = ArrayList<Entry>()
        private var active = false

        fun begin() {
            check(!active) { "Temporal scratch frame is already active" }
            active = true
            entries.forEach { it.used = false }
        }

        fun acquire(spec: TextureSpec, allocate: () -> Int): Int {
            check(active) { "Temporal scratch texture requested outside an active frame" }
            entries.firstOrNull { !it.used && it.spec == spec }?.let { entry ->
                entry.used = true
                return entry.texture
            }
            return allocate().also { texture ->
                entries += Entry(spec = spec, texture = texture, used = true)
            }
        }

        fun end() {
            check(active) { "Temporal scratch frame was not active" }
            active = false
        }

        fun clearTracking() {
            check(!active) { "Cannot clear active temporal scratch textures" }
            entries.clear()
        }
    }

    private data class FrameCalibration(
        val blackLevels: FloatArray,
        val gains: FloatArray,
        val blackTerms: FloatArray,
        val bayerPhaseGains: FloatArray,
        val bayerPhaseBlackTerms: FloatArray,
        val globalFrameWeight: Float,
        val kernelSigma: Float,
        val shotNoise: FloatArray,
        val readNoise: FloatArray,
        val greenClippingPoint: Float,
        val alignmentGain: Float,
        val unblockerShotNoise: FloatArray,
        val unblockerReadNoise: FloatArray,
        val cameraRgbShotNoise: FloatArray,
        val cameraRgbReadNoise: FloatArray,
    )

    private data class SpatialNoiseParameters(
        val read: FloatArray,
        val shot: FloatArray,
    )

    private data class StrengthCapture(
        val geometry: MgcSpatialDiagnosticGeometry,
        val outputMode: MgcSpatialOutputMode,
        val frameCount: Int,
        val alignmentLayout: MgcSpatialStrengthAtlasLayout,
        val rejectionLayout: MgcSpatialStrengthAtlasLayout,
        val alignmentAtlas: Int,
        val rejectionAtlas: Int,
        val inputReadNoise: FloatArray,
        val inputShotNoise: FloatArray,
        val frameWeights: FloatArray,
        val kernelSigmas: FloatArray,
        val captured: BooleanArray,
    ) {
        val alignmentWidth: Int get() = geometry.alignmentWidth
        val alignmentHeight: Int get() = geometry.alignmentHeight
        val rejectionWidth: Int get() = geometry.rejectionWidth
        val rejectionHeight: Int get() = geometry.rejectionHeight
    }

    private data class PixelPackBuffer(
        val buffer: Int,
        val byteCount: Int,
    )

    private data class QueuedTextureReadback(
        val storage: PixelPackBuffer,
        val mode: String,
        val targetBindMs: Long,
        val readSubmitMs: Long,
        val totalSubmitMs: Long,
    )

    private data class QueuedStrengthReadback(
        val alignment: PreparedTextureReadback,
        val rejection: PreparedTextureReadback,
        val fusedFixed16: PreparedTextureReadback,
        val fusedFixed16PrepareSubmitMs: Long,
    )

    private data class PreparedTextureReadback(
        val byteCount: Int,
        val queuedGpuReadback: QueuedTextureReadback?,
        val cpuBuffer: ByteBuffer?,
        val mode: String,
        val targetBindMs: Long,
        val readSubmitMs: Long,
        val totalSubmitMs: Long,
    ) {
        init {
            require(byteCount > 0)
            require((queuedGpuReadback == null) != (cpuBuffer == null)) {
                "Fixed16 readback must own exactly one GPU or CPU storage"
            }
            require(queuedGpuReadback?.storage?.byteCount == null ||
                queuedGpuReadback.storage.byteCount == byteCount)
            require(cpuBuffer?.capacity() == null || cpuBuffer.capacity() >= byteCount)
        }
    }

    private data class RgbDiagnosticPackTiming(
        val setupNs: Long,
        val dispatchNs: Long,
        val byteCount: Int,
        val destinationHeight: Int,
    )

    private data class PendingRgbDiagnosticBand(
        val storage: PixelPackBuffer,
        val outputCore: MgcSpatialRgbRect,
        val destinationHeight: Int,
        val byteCount: Int,
    )

    private enum class StrengthReadbackEncoding {
        FLOAT32,
        UNORM8,
        SINT16,
    }

    private data class BayerKernelTuning(
        val referenceSignal: Float,
        val referenceShadowReadVariance: Float,
        val referenceSnr: Float,
        val baseSpatialScale: Float,
    )

    private data class BentoAssessment(
        val accepted: Boolean,
        val reason: String,
        val clippedPixelRatio: Float,
        val largestInpaintingArea: Int,
        val largestTilingArea: Int,
        val ultrashortClippingOverlap: Float,
    )

    // MGC GuideRaw10 emits one guide sample for every 2x2 Bayer quad. Rejection and
    // MergeBayer therefore share the same half-resolution coordinate system.
    private val guideWidth = ceilDiv(width, 2)
    private val guideHeight = ceilDiv(height, 2)
    // MergeBayerRaw16's queried AOT contract requests one alignment sample per 8x8
    // Bayer-quad tile, i.e. one sample per 16x16 sensor pixels.
    private val bayerAlignmentWidth = ceilDiv(width, MERGE_BAYER_RAW_TILE_SIZE)
    private val bayerAlignmentHeight = ceilDiv(height, MERGE_BAYER_RAW_TILE_SIZE)
    private val rejectionWidth = ceilDiv(width, 2)
    private val rejectionHeight = ceilDiv(height, 2)
    private val mergeWeightWidth = ceilDiv(rejectionWidth, 2)
    private val mergeWeightHeight = ceilDiv(rejectionHeight, 2)
    private val rejectionFilterWidth = ceilDiv(rejectionWidth, REJECTION_FILTER_DOWNSAMPLE)
    private val rejectionFilterHeight = ceilDiv(rejectionHeight, REJECTION_FILTER_DOWNSAMPLE)
    private val normalizedOutputScale = MultiFrameConfig.normalizeOutputScale(outputScale)
    private val outputWidth = if (outputMode == MgcSpatialOutputMode.RGB) {
        MultiFrameConfig.scaledRawOutputDimension(width, normalizedOutputScale)
    } else {
        width
    }
    private val outputHeight = if (outputMode == MgcSpatialOutputMode.RGB) {
        MultiFrameConfig.scaledRawOutputDimension(height, normalizedOutputScale)
    } else {
        height
    }
    private val sensorWhiteLevel = max(1, whiteLevel).toFloat()
    // RawMetadata has already converted positional Camera2 black levels to R, Gr, Gb, B.
    private val canonicalBlackLevel = FloatArray(4) { channel ->
        blackLevel.getOrElse(channel) { blackLevel.firstOrNull() ?: 0f }
            .takeIf { it.isFinite() } ?: 0f
    }
    private val calculationWhiteBalance = run {
        fun safeGain(channel: Int, fallback: Float): Float =
            whiteBalanceGains.getOrElse(channel) { fallback }
                .takeIf { it.isFinite() && it > 0f } ?: fallback

        val greenEven = safeGain(1, 1f)
        val greenOdd = safeGain(2, greenEven)
        val greenBase = (0.5f * (greenEven + greenOdd))
            .takeIf { it.isFinite() && it > 0f } ?: 1f
        fun relative(gain: Float): Float =
            (gain / greenBase).coerceIn(MIN_WHITE_BALANCE_GAIN, MAX_WHITE_BALANCE_GAIN)

        // MGC performs guide/rejection/merge in a white-balanced calculation domain. Keep the
        // two greens unified, as Photon’s RCD calculation contract does before it removes the
        // calculation gains at output.
        floatArrayOf(
            relative(safeGain(0, greenBase)),
            1f,
            1f,
            relative(safeGain(3, greenBase)),
        )
    }
    private val cameraDomainScale = floatArrayOf(
        1f / calculationWhiteBalance[0],
        1f,
        1f / calculationWhiteBalance[3],
    )
    // SabreProcessor::Run scales RAW codes into MGC's 14-bit Resolve domain with
    // int(max(16384 / (white_level + 1), 1)). ResolveSabre receives black/white in
    // that domain, while final_gains undo the WB gains used by the GL merge.
    private val sabreResolveRawScale = max(
        (SABRE_RESOLVE_INPUT_WHITE_LEVEL / (sensorWhiteLevel + 1f)).toInt(),
        1,
    ).toFloat()
    private val sabreResolveFinalGains = cameraDomainScale.copyOf()
    private var eglDisplay: EGLDisplay = EGL14.EGL_NO_DISPLAY
    private var eglContext: EGLContext = EGL14.EGL_NO_CONTEXT
    private var eglSurface: EGLSurface = EGL14.EGL_NO_SURFACE
    private var ownsEglContext = false

    private val textures = ArrayList<Int>()
    private val framebuffers = ArrayList<Int>()
    private val buffers = ArrayList<Int>()
    private val programs = ArrayList<Int>()
    private val uniformLocations = HashMap<Int, HashMap<String, Int>>()
    private val textureSpecs = HashMap<Int, TextureSpec>()
    private val validatedRenderTargetSpecs = HashSet<List<TextureSpec>>()
    private val temporalScratchTextures = SequentialScratchTextures()
    private var activeSequentialScratchTextures: SequentialScratchTextures? = null
    private var renderFbo = 0
    private var renderTargetAttachmentCount = 0

    private var guideProgram = 0
    private var covarianceProgram = 0
    private var rgbChromaGuideProgram = 0
    private var rawToGrayProgram = 0
    private var downsampleProgram = 0
    private var downsample4Program = 0
    private var alignProgram = 0
    private var alignmentGradientProductsProgram = 0
    private var upsampleAlignmentProgram = 0
    private var blockLucasKanadeProgram = 0
    private var convertAlignmentProgram = 0
    private var convertBayerAlignmentProgram = 0
    private var strengthAlignmentProgram = 0
    private var strengthRejectionProgram = 0
    private var unblockerProgram = 0
    private var rejectionProgram = 0
    private var clippedGaussianHorizontalProgram = 0
    private var clippedGaussianVerticalProgram = 0
    private var rejectionFilterDownsampleProgram = 0
    private var rejectionFilterProgram = 0
    private var rejectionPostprocessProgram = 0
    private var dilationProgram = 0
    private var linearKernelMaskProgram = 0
    private var findBlockTilesGatherEdgesProgram = 0
    private var findBlockTilesFilterIntermediateProgram = 0
    private var findBlockTilesOutputProgram = 0
    private var bentoHighlightProgram = 0
    private var bentoHighlightCountProgram = 0
    private var bentoAdjustProgram = 0
    private var bentoRewriteWeightProgram = 0
    private var alignedRawClippingMaskProgram = 0
    private var mergeBayerProgram = 0
    private var sabreMergeBayerProgram = 0
    private var sabreExtractBayerProgram = 0
    private var sabreGuideAndCovarianceProgram = 0
    private var sabreMergeProgram = 0
    private var sabreSuperResDetailMergeProgram = 0
    private var sabreSuperResDetailResolveProgram = 0
    private var sabreSuperResLinearRawProgram = 0
    private var true2xMergeProgram26564 = 0
    private var true2xFlowRefineProgram26574 = 0
    private var true2xResolveProgram26564 = 0
    private var true2xGuideRenderProgram26568 = 0
    private var sabreShadowLongMergeProgram = 0
    private var sabreShadowLongCopyMaskProgram = 0
    private var sabreNormalDngMergeProgram = 0
    private var sabreCopyMaskProgram = 0
    private var sabreCopyAlphaProgram = 0
    private var sabreReciprocalGreenWeightProgram = 0
    private var sabreDehomogenizeProgram = 0
    private var sabreOutputTransformProgram = 0
    private var sabreRgb16ToFloatProgram = 0
    private var sabreShortRegionSeedProgram26595 = 0
    private var sabreShortRegionPropagateProgram26594 = 0
    private var sabreShortRestoreMaskProgram26595 = 0
    private var sabreShortRestoreMaskProbeProgram26590 = 0
    private var sabreShortMaskCountProgram26595 = 0
    private var sabreShortRestoreRgba16fProgram26587 = 0
    private var sabreRgbChromaPostprocessor: GlesIris26529SpatialRgbChromaPostprocessor? = null
    private var sabreConvertAlignmentSparseProgram = 0
    private var currentMergeCovariance = 0
    private var mergeRgbProgram = 0
    private var normalizeBayerProgram = 0
    private var normalizeRgbProgram = 0
    private var packBayerFixed16Program = 0
    private var packRgbFixed16FallbackProgram = 0
    private var strengthFloatPackProgram = 0
    private var strengthUnorm8PackProgram = 0
    private var strengthSint16PackProgram = 0
    private var supportsComputeReadback = false
    private var maxShaderStorageBlockBytes = 0L
    private var maxComputePackGroupsX = 0
    private var maxComputePackGroupsY = 0
    private var baseFrameCamera2Model: RawNoiseModel = RawNoiseModel.EMPTY
    private val pixelDifferenceKernel = gaussianKernel(
        size = PIXEL_DIFFERENCE_KERNEL_SIZE,
        sigma = PIXEL_DIFFERENCE_SMOOTH_SIGMA,
    )
    private val conservativeRgbFlowBounds = MgcSpatialRgbFlowBounds(
        -MAX_ALIGNMENT_DISPLACEMENT_BAYER_QUADS,
        -MAX_ALIGNMENT_DISPLACEMENT_BAYER_QUADS,
        MAX_ALIGNMENT_DISPLACEMENT_BAYER_QUADS,
        MAX_ALIGNMENT_DISPLACEMENT_BAYER_QUADS,
    )

    /** Moves shader compile/link work to the camera-idle persistent EGL context. */
    internal fun prewarmCapturePipeline(
        frameCount: Int,
        includeBento: Boolean,
    ) {
        require(useCurrentGlContext) {
            "MGC Spatial capture prewarm requires the caller-owned current EGL context"
        }
        val startNs = System.nanoTime()
        try {
            attachCurrentEgl()
            ensureGles3()
            if (processorPipeline == MgcRawProcessorPipeline.SABRE) {
                initSabrePrograms()
            } else {
                initPrograms(includeBentoAssessment = includeBento)
                if (includeBento) initBentoMergePrograms()
            }
            renderFbo = createFramebuffer()
            applyRawRenderState()
            PLog.d(
                TAG,
                "MGC ${processorPipeline.name} capture programs prewarmed size=${width}x$height " +
                    "frames=${frameCount.coerceAtLeast(1)} bento=$includeBento " +
                    "took=${(System.nanoTime() - startNs) / 1_000_000L}ms",
            )
        } finally {
            release()
        }
    }

    fun processFrames(frames: List<RawStackFrame>): RawStackResult? {
        if (frames.isNotEmpty()) {
            PLog.i(
                TAG,
                "MGC RAW black levels master=${canonicalBlackLevel.contentToString()} " +
                    "perFrame=${frames.map { frame ->
                        canonicalBlackLevelForFrame(frame).contentToString()
                    }}",
            )
        }
        if (processorPipeline == MgcRawProcessorPipeline.SABRE) {
            return processSabreFrames(frames)
        }
        val images = frames.map { it.image }
        require(
            outputMode != MgcSpatialOutputMode.RGB ||
                !exportGpuLinearRgbSource ||
                useCurrentGlContext
        ) {
            "MGC Spatial GPU RGB export requires the caller-owned current EGL context"
        }
        if (images.isEmpty() || width <= 1 || height <= 1) {
            images.forEach { it.close() }
            return null
        }
        if (images.any { it.width != width || it.height != height }) {
            PLog.e(TAG, "MGC Spatial merge received mixed RAW dimensions")
            images.forEach { it.close() }
            return null
        }
        if (images.any { it.format != ImageFormat.RAW_SENSOR }) {
            PLog.e(TAG, "MGC Spatial merge only accepts RAW_SENSOR images")
            images.forEach { it.close() }
            return null
        }
        baseFrameCamera2Model = frames.firstOrNull()
            ?.channelNoiseProfile
            ?.let(RawNoiseModel::fromCamera2NoiseProfile)
            ?.takeIf { it.hasValidCamera2Profile }
            ?: RawNoiseModel.EMPTY
        val resolvedNoiseModels = frames.map(::resolveNoiseModelForFrame)
        if (resolvedNoiseModels.any { it.source == RawNoiseModelSource.UNAVAILABLE }) {
            PLog.e(
                TAG,
                "MGC Spatial noise profile is unavailable for the selected source " +
                    "(${noiseProfileSelection.id})",
            )
            images.forEach { it.close() }
            return null
        }

        var cpuOutput: ByteBuffer? = null
        var returned = false
        var exportedBayerTexture = 0
        var exportedRgbTexture = 0
        var exportedRgbCompletionTimeline: GpuStackCompletionTimeline? = null
        var strengthAlignmentHostBuffer: ByteBuffer? = null
        var strengthRejectionHostBuffer: ByteBuffer? = null
        var rgbDiagnosticHostBuffer: ByteBuffer? = null
        var strengthCapture: StrengthCapture? = null
        var onlineRgbAccumulator: OnlineRgbAccumulator? = null
        val processStartNs = System.nanoTime()
        val originalThreadPriority = GlesGpuScheduler.lowerCurrentThreadPriority(TAG)
        return try {
            if (useCurrentGlContext) attachCurrentEgl() else initEgl()
            ensureGles3()
            val hasBentoCandidate = frames.any { frame ->
                frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT
            }
            val hasShadowLongFrame = frames.any { frame ->
                frame.role == RawBurstFrameRole.SHADOW_LONG
            }
            val programInitStartNs = System.nanoTime()
            initPrograms(
                includeBentoAssessment = hasBentoCandidate,
                includeReferenceHighlightMask = hasBentoCandidate || hasShadowLongFrame,
            )
            val programInitMs = (System.nanoTime() - programInitStartNs) / 1_000_000L
            renderFbo = createFramebuffer()
            applyRawRenderState()
            PLog.i(
                TAG,
                "MGC rejection domain=${rejectionWidth}x$rejectionHeight " +
                    "mergeWeight=${mergeWeightWidth}x$mergeWeightHeight " +
                    "pixelDiff=ClippedGaussian${PIXEL_DIFFERENCE_KERNEL_SIZE}" +
                    "(sigma=$PIXEL_DIFFERENCE_SMOOTH_SIGMA) " +
                    "downsample=${REJECTION_FILTER_DOWNSAMPLE}x " +
                    "colorSigma=$REJECTION_FILTER_COLOR_SIGMA " +
                    "spatialSigma=$REJECTION_FILTER_SPATIAL_SIGMA " +
                    "boost=$REJECTION_FILTER_COLOR_SIGMA_BOOST " +
                    "radius=$REJECTION_FILTER_MAX_RADIUS " +
                    "pixelDiffThreshold=$PIXEL_DIFFERENCE_THRESHOLD/255 " +
                    "clippedThreshold=$REJECTION_CLIPPED_THRESHOLD/255",
            )
            PLog.i(
                TAG,
                "MGC Raw10 unblocker fullresTile=$UNBLOCKER_FULLRES_TILE_SIZE " +
                    "domain=${ceilDiv(width, UNBLOCKER_FULLRES_TILE_SIZE * 2)}x" +
                    "${ceilDiv(height, UNBLOCKER_FULLRES_TILE_SIZE * 2)} " +
                    "scale=$UNBLOCKER_OUTPUT_SCALE offset=$UNBLOCKER_OUTPUT_OFFSET",
            )
            val referenceRaw = createTexture(
                width,
                height,
                GLES30.GL_R16UI,
                GLES30.GL_NEAREST,
            )
            val currentRaw = createTexture(
                width,
                height,
                GLES30.GL_R16UI,
                GLES30.GL_NEAREST,
            )
            val referenceGuide = createTexture(
                guideWidth,
                guideHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_LINEAR,
            )
            val currentGuide = createTexture(
                guideWidth,
                guideHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_LINEAR,
            )
            val needsSabreCovariance = mergeMethod == MgcMergeMethod.SABRE
            val referenceCovariance = if (outputMode == MgcSpatialOutputMode.RGB || needsSabreCovariance) {
                createTexture(
                    guideWidth,
                    guideHeight,
                    GLES30.GL_RGB10_A2,
                    GLES30.GL_LINEAR,
                )
            } else {
                0
            }
            val currentCovariance = if (outputMode == MgcSpatialOutputMode.RGB || needsSabreCovariance) {
                createTexture(
                    guideWidth,
                    guideHeight,
                    GLES30.GL_RGB10_A2,
                    GLES30.GL_LINEAR,
                )
            } else {
                0
            }
            val zeroFlow = createZeroFlowTexture()
            val identityWeight = createIdentityWeightTexture()
            val zeroLinearKernelMask = createZeroLinearKernelMaskTexture()
            val accumulatorColor = if (outputMode == MgcSpatialOutputMode.BAYER) {
                createTexture(
                    width,
                    height,
                    GLES30.GL_RGBA16F,
                    GLES30.GL_NEAREST,
                )
            } else {
                0
            }
            val rgbMergeFrames = ArrayList<RgbMergeFrame>(frames.size)
            val referenceExposure = validExposureProduct(frames.first().exposureProduct)
            val bayerKernelTuning = createBayerKernelTuning(
                frame = frames.first(),
                image = images.first(),
                frameCount = frames.size,
            )
            val finishRawSharpenAttenuationScale =
                MgcSabreResolveTuning.demosaicSharpness(
                    desiredExposureProduct = frames.first().desiredExposureProduct,
                    actualExposureProduct = frames.first().exposureProduct,
                )
            val perFrameCamera2Profiles = resolvedNoiseModels.count {
                it.source == RawNoiseModelSource.CAMERA2_PER_FRAME
            }
            val baseFrameCamera2Profiles = resolvedNoiseModels.count {
                it.source == RawNoiseModelSource.CAMERA2_BASE_FRAME
            }
            val calibratedProfiles = resolvedNoiseModels.count {
                it.source == RawNoiseModelSource.GCAM_CALIBRATED
            }
            val pixel3FallbackProfiles = resolvedNoiseModels.count {
                it.source == RawNoiseModelSource.PIXEL3_FALLBACK
            }
            val calibratedProfile = (noiseProfileSelection as? RawNoiseProfileSelection.Calibrated)
                ?.profile
            val profileSource = calibratedProfile?.let { profile ->
                profile.maxAnalogSensitivity?.let { maxAnalog ->
                    "gcam-c:${profile.id} profileMaxAnalog=$maxAnalog"
                } ?: "mgc-override:${profile.id} profileMaxAnalog=not-applicable"
            } ?: "Camera2 SENSOR_NOISE_PROFILE"
            PLog.i(
                TAG,
                "MGC Spatial noise profile source=$profileSource " +
                    "perFrame=$perFrameCamera2Profiles/${frames.size} " +
                    "baseFallback=$baseFrameCamera2Profiles/${frames.size} " +
                    "calibrated=$calibratedProfiles/${frames.size} " +
                    "pixel3Fallback=$pixel3FallbackProfiles/${frames.size}",
            )
            calibratedProfile?.let { profile ->
                PLog.i(
                    TAG,
                    "MGC Spatial calibrated per-frame gain " +
                        "iso=${frames.map { it.sensitivityIso }} " +
                        "overallGain=${frames.map { profile.overallGainAt(it.sensitivityIso) }} " +
                        "digitalGain=${frames.map { profile.digitalGainAt(it.sensitivityIso) }}",
                )
            }
            val referenceCalibration = calibrationForFrame(
                frame = frames.first(),
                exposureScale = 1f,
                kernelTuning = bayerKernelTuning,
            )
            PLog.i(
                TAG,
                "MGC Spatial Bayer kernel referenceSnr=${bayerKernelTuning.referenceSnr} " +
                    "baseSpatialScale=${bayerKernelTuning.baseSpatialScale} " +
                    "referenceSigma=${referenceCalibration.kernelSigma} " +
                    "alignmentInputGain=${referenceCalibration.alignmentGain} " +
                    "alignmentDomain=signed-s16",
            )
            val rawUploadStartNs = System.nanoTime()
            uploadRaw(images.first(), referenceRaw, "reference")
            PLog.i(
                TAG,
                "MGC Spatial RAW temporal window textures=2 " +
                    "bytes=${width.toLong() * height * RAW_BYTES_PER_PIXEL * 2L} " +
                    "referenceUpload=1 took=" +
                    "${(System.nanoTime() - rawUploadStartNs) / 1_000_000L}ms",
            )
            // MGC's GenerateBaseFrameLuma and GuideImage::Create prepare this noise-aware guide,
            // and alignment pyramid directly from the reference RAW. User-controlled luma/chroma
            // denoise remains a later RAW-render stage, not reference-frame preprocessing.
            val referenceNoiseLut = createNoiseLut(
                referenceCalibration,
                referenceCalibration,
            )
            renderGuide(
                rawTexture = referenceRaw,
                noiseTexture = referenceNoiseLut,
                calibration = referenceCalibration,
                guideTexture = referenceGuide,
                forceReferenceColorRgb = 0f,
            )
            if (outputMode == MgcSpatialOutputMode.RGB || needsSabreCovariance) {
                renderCovariance(
                    rawTexture = referenceRaw,
                    noiseTexture = referenceNoiseLut,
                    calibration = referenceCalibration,
                    outputTexture = referenceCovariance,
                )
                currentMergeCovariance = referenceCovariance
            }
            val referenceGrayPyramid = buildGrayPyramid(
                rawTexture = referenceRaw,
                calibration = referenceCalibration,
            )
            val referenceAlignmentProducts = buildReferenceAlignmentProducts(
                referenceGrayPyramid,
            )
            GlesGpuScheduler.yieldToUiRenderer()

            val diagnosticMode = RawStackRuntimeDebug.mgcSpatialDiagnosticMode
            val referenceOnly =
                diagnosticMode == MgcSpatialDiagnosticMode.REFERENCE_ONLY
            val identityTemporalWeights =
                diagnosticMode == MgcSpatialDiagnosticMode.IDENTITY_TEMPORAL_WEIGHTS
            val disableLinearKernel =
                diagnosticMode == MgcSpatialDiagnosticMode.DISABLE_LINEAR_KERNEL
            val forceLinearKernel =
                diagnosticMode == MgcSpatialDiagnosticMode.FORCE_LINEAR_KERNEL
            if (diagnosticMode != MgcSpatialDiagnosticMode.NONE) {
                PLog.i(
                    TAG,
                    "MGC Spatial diagnostic mode=${diagnosticMode.name} " +
                        when (diagnosticMode) {
                            MgcSpatialDiagnosticMode.REFERENCE_ONLY ->
                                "temporalAndBracketedContributions=disabled"
                            MgcSpatialDiagnosticMode.IDENTITY_TEMPORAL_WEIGHTS ->
                                "flowAndTemporalMerge=enabled rejectionWeights=identity"
                            MgcSpatialDiagnosticMode.MAIN_REJECTION_ONLY ->
                                "flowAndTemporalMerge=enabled rejectionWeights=measured " +
                                    "unblocker=disabled motionPrior=disabled"
                            MgcSpatialDiagnosticMode.DISABLE_UNBLOCKER ->
                                "flowAndTemporalMerge=enabled rejectionWeights=measured " +
                                    "unblocker=disabled motionPrior=enabled"
                            MgcSpatialDiagnosticMode.DISABLE_LINEAR_KERNEL ->
                                "flowAndTemporalMerge=enabled rejectionWeights=measured " +
                                    "linearKernelMask=zero"
                            MgcSpatialDiagnosticMode.FORCE_LINEAR_KERNEL ->
                                "flowAndTemporalMerge=enabled rejectionWeights=measured " +
                                    "linearKernelMask=identity"
                            MgcSpatialDiagnosticMode.NONE -> ""
                        },
                )
            }
            var mergedFrames = 1
            var bentoAccepted = false
            var bentoCalibration: FrameCalibration? = null
            var bentoFlowTexture = 0
            var bentoBayerAlignmentTexture = 0
            var bentoRgbCovarianceTexture = 0
            var acceptedBentoExposureRatio: Float? = null
            val ultrashortIndex = if (referenceOnly) {
                -1
            } else {
                frames.indexOfFirst { frame ->
                    frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT
                }
            }
            val referenceHighlightMask = if (
                !referenceOnly && (ultrashortIndex >= 0 || hasShadowLongFrame)
            ) {
                createTexture(
                    guideWidth,
                    guideHeight,
                    GLES30.GL_R8,
                    GLES30.GL_NEAREST,
                ).also { output ->
                    renderBentoHighlightMask(
                        baseFrame = referenceGuide,
                        outputMask = output,
                    )
                }
            } else {
                0
            }
            val bentoExposureRatio = ultrashortIndex.takeIf { it >= 0 }?.let { index ->
                (
                    referenceExposure /
                        validExposureProduct(frames[index].exposureProduct)
                    ).toFloat().also { ratio ->
                        check(ratio.isFinite() && ratio > 1f) {
                            "MGC Bento requires baseTET/ultrashortTET > 1.0, got $ratio"
                        }
                    }
            }
            var baseHighlightClippedRatio = 0f
            var baseHighlightMask: ByteArray? = null
            if (ultrashortIndex >= 0) {
                check(referenceHighlightMask != 0)
                val gateStartNs = System.nanoTime()
                if (bentoHighlightCountProgram != 0) {
                    val gpuCount = countActiveMaskPixelsGpu(
                        texture = referenceHighlightMask,
                        label = "MGC Bento base highlight gate",
                    )
                    baseHighlightClippedRatio =
                        gpuCount.activePixels.toFloat() / (guideWidth * guideHeight).toFloat()
                    PLog.i(
                        TAG,
                        "MGC Bento base gate mode=compute-ssbo eligible=" +
                            "${baseHighlightClippedRatio > BENTO_MIN_CLIPPED_PIXEL_RATIO} " +
                            "clipped=${gpuCount.activePixels}/${guideWidth * guideHeight} " +
                            "ratio=$baseHighlightClippedRatio " +
                            "threshold=$BENTO_MIN_CLIPPED_PIXEL_RATIO " +
                            "setup=${gpuCount.setupNs / 1_000_000L}ms " +
                            "submit=${gpuCount.submitNs / 1_000_000L}ms " +
                            "gpuWait=${gpuCount.gpuWaitMs}ms " +
                            "map=${gpuCount.mapNs / 1_000_000L}ms " +
                            "total=${elapsedMs(gateStartNs)}ms",
                    )
                } else {
                    val gpuWaitMs = GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Bento base highlight gate",
                        checkGlError = ::checkGlError,
                    )
                    val readStartNs = System.nanoTime()
                    val mask = readR8Mask(
                        texture = referenceHighlightMask,
                        label = "Bento base highlight gate",
                    )
                    val readNs = System.nanoTime() - readStartNs
                    val countStartNs = System.nanoTime()
                    val clippedPixels = countActiveMaskPixels(mask)
                    val countNs = System.nanoTime() - countStartNs
                    baseHighlightMask = mask
                    baseHighlightClippedRatio = clippedPixels.toFloat() / mask.size.toFloat()
                    PLog.i(
                        TAG,
                        "MGC Bento base gate mode=cpu-readback eligible=" +
                            "${baseHighlightClippedRatio > BENTO_MIN_CLIPPED_PIXEL_RATIO} " +
                            "clipped=$clippedPixels/${mask.size} " +
                            "ratio=$baseHighlightClippedRatio " +
                            "threshold=$BENTO_MIN_CLIPPED_PIXEL_RATIO " +
                            "gpuWait=${gpuWaitMs}ms " +
                            "read=${readNs / 1_000_000L}ms " +
                            "count=${countNs / 1_000_000L}ms " +
                            "total=${elapsedMs(gateStartNs)}ms",
                    )
                }
            }
            val evaluateBentoCandidate = ultrashortIndex >= 0 &&
                baseHighlightClippedRatio > BENTO_MIN_CLIPPED_PIXEL_RATIO
            val bentoMask = if (evaluateBentoCandidate) {
                createTexture(
                    guideWidth,
                    guideHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                )
            } else {
                null
            }
            if (ultrashortIndex >= 0 && !evaluateBentoCandidate) {
                PLog.i(
                    TAG,
                    "Bento assessment accepted=false reason=insufficient_clipped_pixels " +
                        "clippedRatio=$baseHighlightClippedRatio largestInpaintingArea=0 " +
                        "largestTilingArea=0 ultrashortOverlap=0.0 " +
                        "exposureRatio=$bentoExposureRatio earlyGate=true",
                )
            }
            val bentoRaw = currentRaw
            val bentoGuide = currentGuide
            if (evaluateBentoCandidate) {
                val bentoScheduleStartNs = System.nanoTime()
                var bentoUploadCallNs = 0L
                var bentoPreAlignSubmitNs = 0L
                var bentoAlignSubmitNs = 0L
                var bentoPostAlignNs = 0L
                val transientTextureStart = textures.size
                val ultrashortFrame = frames[ultrashortIndex]
                try {
                    val exposureRatio = checkNotNull(bentoExposureRatio)
                    val normalizedCalibration = calibrationForFrame(
                        ultrashortFrame,
                        exposureRatio,
                        bayerKernelTuning,
                    )
                    val uploadStartNs = System.nanoTime()
                    uploadRaw(images[ultrashortIndex], bentoRaw, "ultrashort")
                    bentoUploadCallNs = System.nanoTime() - uploadStartNs
                    val preAlignStartNs = System.nanoTime()
                    val normalizedNoiseLut = createNoiseLut(
                        referenceCalibration,
                        normalizedCalibration,
                    )
                    renderGuide(
                        rawTexture = bentoRaw,
                        noiseTexture = normalizedNoiseLut,
                        calibration = normalizedCalibration,
                        guideTexture = bentoGuide,
                        forceReferenceColorRgb = 0f,
                    )
                    if (outputMode == MgcSpatialOutputMode.RGB || needsSabreCovariance) {
                        renderCovariance(
                            rawTexture = bentoRaw,
                            noiseTexture = normalizedNoiseLut,
                            calibration = normalizedCalibration,
                            outputTexture = currentCovariance,
                        )
                        bentoRgbCovarianceTexture = copyPersistentTexture(
                            source = currentCovariance,
                            textureWidth = guideWidth,
                            textureHeight = guideHeight,
                            internalFormat = GLES30.GL_RGB10_A2,
                            filter = GLES30.GL_LINEAR,
                            label = "MGC Bento RGB covariance",
                        )
                    }
                    val ultrashortGrayPyramid = buildGrayPyramid(
                        rawTexture = bentoRaw,
                        calibration = normalizedCalibration,
                    )
                    bentoPreAlignSubmitNs = System.nanoTime() - preAlignStartNs
                    val alignmentStartNs = System.nanoTime()
                    val alignment = alignPyramids(
                        reference = referenceGrayPyramid,
                        current = ultrashortGrayPyramid,
                        referenceProducts = referenceAlignmentProducts,
                    )
                    bentoAlignSubmitNs = System.nanoTime() - alignmentStartNs
                    val postAlignStartNs = System.nanoTime()
                    val flow = createTexture(
                        rejectionWidth,
                        rejectionHeight,
                        GLES30.GL_RGBA16F,
                        GLES30.GL_LINEAR,
                    )
                    renderConvertedAlignment(alignment, flow)
                    val bayerAlignment = createTexture(
                        bayerAlignmentWidth,
                        bayerAlignmentHeight,
                        GLES30.GL_RGBA32F,
                        GLES30.GL_NEAREST,
                    )
                    renderBayerAlignment(alignment, bayerAlignment)
                    val tilingMask = renderFindBlockTiles(
                        baseRaw = referenceRaw,
                        ultrashortRaw = bentoRaw,
                        flowTexture = flow,
                        baseCalibration = referenceCalibration,
                        ultrashortCalibration = normalizedCalibration,
                    )

                    val unscaledCalibration = calibrationForFrame(
                        ultrashortFrame,
                        1f,
                        bayerKernelTuning,
                    )
                    val unscaledGuide = createTexture(
                        guideWidth,
                        guideHeight,
                        GLES30.GL_RGBA16F,
                        GLES30.GL_LINEAR,
                    )
                    val unscaledNoiseLut = createNoiseLut(
                        referenceCalibration,
                        unscaledCalibration,
                    )
                    renderGuide(
                        rawTexture = bentoRaw,
                        noiseTexture = unscaledNoiseLut,
                        calibration = unscaledCalibration,
                        guideTexture = unscaledGuide,
                        forceReferenceColorRgb = 0f,
                    )
                    val inpaintingMask = createTexture(
                        guideWidth,
                        guideHeight,
                        GLES30.GL_R8,
                        GLES30.GL_NEAREST,
                    )
                    val ultrashortClippingMask = createTexture(
                        guideWidth,
                        guideHeight,
                        GLES30.GL_R8,
                        GLES30.GL_NEAREST,
                    )
                    check(referenceHighlightMask != 0)
                    renderBentoAdjustedMask(
                        baseFrame = referenceGuide,
                        ultrashortFrame = unscaledGuide,
                        highlightMask = referenceHighlightMask,
                        flowTexture = flow,
                        exposureRatio = exposureRatio,
                        adjustedMask = checkNotNull(bentoMask),
                        inpaintingMask = inpaintingMask,
                        ultrashortClippingMask = ultrashortClippingMask,
                    )
                    val assessmentReadStartNs = System.nanoTime()
                    val assessmentGpuWaitMs = GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Bento assessment masks",
                        checkGlError = ::checkGlError,
                    )
                    val assessmentBaseHighlightMask = baseHighlightMask ?: readR8Mask(
                        texture = referenceHighlightMask,
                        label = "Bento base highlight mask",
                    ).also { mask -> baseHighlightMask = mask }
                    val assessment = assessBentoMasks(
                        baseHighlightMask = assessmentBaseHighlightMask,
                        inpaintingMask = readR8Mask(
                            inpaintingMask,
                            "Bento inpainting mask",
                        ),
                        ultrashortClippingMask = readR8Mask(
                            ultrashortClippingMask,
                            "Bento ultrashort clipping mask",
                        ),
                        tilingMask = readR8Mask(
                            texture = tilingMask,
                            label = "Bento FindBlockTiles mask",
                            maskWidth = bayerAlignmentWidth,
                            maskHeight = bayerAlignmentHeight,
                        ),
                    )
                    PLog.i(
                        TAG,
                        "Bento assessment accepted=${assessment.accepted} " +
                            "reason=${assessment.reason} " +
                            "clippedRatio=${assessment.clippedPixelRatio} " +
                            "largestInpaintingArea=${assessment.largestInpaintingArea} " +
                            "largestTilingArea=${assessment.largestTilingArea} " +
                            "ultrashortOverlap=${assessment.ultrashortClippingOverlap} " +
                            "exposureRatio=$exposureRatio earlyGate=false " +
                            "gpuWait=${assessmentGpuWaitMs}ms " +
                            "readAndAssess=${elapsedMs(assessmentReadStartNs)}ms",
                    )
                    if (assessment.accepted) {
                        bentoAccepted = true
                        acceptedBentoExposureRatio = exposureRatio
                        bentoCalibration = normalizedCalibration
                        bentoFlowTexture = flow
                        bentoBayerAlignmentTexture = bayerAlignment
                    }
                    bentoPostAlignNs = System.nanoTime() - postAlignStartNs
                } finally {
                    if (
                        bentoAccepted &&
                        bentoFlowTexture != 0 &&
                        bentoBayerAlignmentTexture != 0
                    ) {
                        // Keep the selected ultrashort flow until the single Bento-derived
                        // linear-kernel mask has been built and applied to every Bayer merge
                        // contribution. The current RAW texture is persistent.
                        releaseTexturesFromExcept(
                            startIndex = transientTextureStart,
                            retainedTextures = buildList {
                                add(bentoFlowTexture)
                                add(bentoBayerAlignmentTexture)
                                if (bentoRgbCovarianceTexture != 0) {
                                    add(bentoRgbCovarianceTexture)
                                }
                            }.toIntArray(),
                        )
                    } else {
                        releaseTexturesFrom(transientTextureStart)
                    }
                }
                PLog.i(
                    TAG,
                    "MGC Bento frame schedule index=$ultrashortIndex " +
                        "frame=${ultrashortFrame.frameNumber} " +
                        "uploadCall=${bentoUploadCallNs / 1_000_000L}ms " +
                        "preAlignSubmit=${bentoPreAlignSubmitNs / 1_000_000L}ms " +
                        "alignSubmit=${bentoAlignSubmitNs / 1_000_000L}ms " +
                        "postAlignAndAssessment=${bentoPostAlignNs / 1_000_000L}ms " +
                        "totalCpu=${elapsedMs(bentoScheduleStartNs)}ms",
                )
            }
            if (evaluateBentoCandidate && !bentoAccepted) {
                releaseOwnedTexture(checkNotNull(bentoMask), "rejected Bento mask")
            }
            if (ultrashortIndex >= 0 && !bentoAccepted) {
                images[ultrashortIndex].close()
            }

            val outputExposure = MgcSpatialOutputExposure.forAcceptedUltrashort(
                acceptedBentoExposureRatio,
            )
            PLog.i(
                TAG,
                "MGC Spatial output exposure normalizationScale=" +
                    "${outputExposure.normalizationScale} " +
                    "baselineExposureEv=${outputExposure.baselineExposureEv} " +
                    "domain=${if (bentoAccepted) "ultrashort" else "reference"}",
            )

            val temporalFrameRange = if (referenceOnly) {
                IntRange.EMPTY
            } else {
                1 until frames.size
            }
            val linearKernelMask = when {
                disableLinearKernel -> {
                    PLog.i(TAG, "MGC linear kernel mask mode=zero reason=diagnostic-disable")
                    zeroLinearKernelMask
                }
                forceLinearKernel -> {
                    PLog.i(TAG, "MGC linear kernel mask mode=identity reason=diagnostic-force")
                    identityWeight
                }
                identityTemporalWeights -> {
                    PLog.i(TAG, "MGC linear kernel mask mode=zero reason=identity-rejection")
                    zeroLinearKernelMask
                }
                bentoAccepted -> {
                    check(ultrashortIndex >= 0) {
                        "Accepted Bento merge has no selected ultrashort frame"
                    }
                    initBentoMergePrograms()
                    val selectedLinearKernelMask = createTexture(
                        mergeWeightWidth,
                        mergeWeightHeight,
                        GLES30.GL_R8,
                        GLES30.GL_LINEAR,
                    )
                    // MGC slices its 3-D rejection buffer once at the accepted Bento ultrashort
                    // index, then calls UpdateLinearKernelMask once. Bento's adjusted mask is the
                    // complement of the selected merge weight; because the recovered AOT only
                    // tests 3x3 equality, that complement produces the identical binary mask.
                    renderLinearKernelMask(
                        rejection = checkNotNull(bentoMask),
                        output = selectedLinearKernelMask,
                    )
                    if (diagnosticMode != MgcSpatialDiagnosticMode.NONE) {
                        logLinearKernelMask(
                            texture = selectedLinearKernelMask,
                            selectedFrameIndex = ultrashortIndex,
                        )
                    }
                    selectedLinearKernelMask
                }
                else -> {
                    PLog.i(
                        TAG,
                        "MGC linear kernel mask mode=zero " +
                            "reason=no-accepted-bento-selected-slice",
                    )
                    zeroLinearKernelMask
                }
            }

            if (bentoAccepted || hasShadowLongFrame) initBentoMergePrograms()
            val bentoBaseWeight = if (bentoAccepted) {
                createTexture(
                    mergeWeightWidth,
                    mergeWeightHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                ).also { output ->
                    renderBentoRewrittenWeight(
                        existingWeight = identityWeight,
                        bentoMask = checkNotNull(bentoMask),
                        outputWeight = output,
                        hasExistingWeight = false,
                    )
                }
            } else {
                0
            }
            val bentoShortWeight = if (bentoAccepted) {
                // Quantize Bento onto the exact MergeBayer/Spatial-noise mask domain. Since
                // bentoBaseWeight is (1 - mask), a second complement produces the selected
                // ultrashort slice with matching R8 quantization.
                createTexture(
                    mergeWeightWidth,
                    mergeWeightHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                ).also { output ->
                    renderBentoRewrittenWeight(
                        existingWeight = identityWeight,
                        bentoMask = bentoBaseWeight,
                        outputWeight = output,
                        hasExistingWeight = false,
                    )
                }
            } else {
                0
            }
            val temporalMergeCount = temporalFrameRange.count { index ->
                frames[index].role != RawBurstFrameRole.HIGHLIGHT_SHORT
            }
            val spatialNoiseFrameCount =
                1 + (if (bentoAccepted) 1 else 0) + temporalMergeCount
            if (MultiFrameConfig.ENABLE_MGC_SPATIAL_DEFAULT_DENOISE &&
                !referenceOnly &&
                spatialNoiseFrameCount > 1
            ) {
                strengthCapture = createStrengthCapture(
                    frameCount = spatialNoiseFrameCount,
                    referenceCalibration = referenceCalibration,
                )
            }
            if (
                outputMode == MgcSpatialOutputMode.RGB
            ) {
                onlineRgbAccumulator = createOnlineRgbAccumulator(
                    diagnosticCapture = strengthCapture,
                )?.also { online ->
                    online.rawUploadCount = 1 + if (evaluateBentoCandidate) 1 else 0
                    online.rawUploadBytes = online.rawUploadCount.toLong() *
                        width * height * RAW_BYTES_PER_PIXEL
                }
            }
            var capturedFrameIndex = 0

            fun submitOrRetainRgbFrame(
                frame: RgbMergeFrame,
                rawTexture: Int,
            ) {
                val online = onlineRgbAccumulator
                if (online != null) {
                    contributeOnlineRgbFrame(
                        accumulator = online,
                        frame = frame,
                        rawTexture = rawTexture,
                    )
                } else {
                    rgbMergeFrames += frame
                }
            }

            if (outputMode == MgcSpatialOutputMode.BAYER) {
                clearAccumulator(accumulatorColor)
            }
            if (bentoAccepted) {
                if (outputMode == MgcSpatialOutputMode.BAYER) {
                    currentMergeCovariance = referenceCovariance
                    renderMerge(
                        rawTexture = referenceRaw,
                        bayerAlignmentTexture = zeroFlow,
                        weightTexture = bentoBaseWeight,
                        linearKernelMaskTexture = linearKernelMask,
                        calibration = referenceCalibration,
                        accumulatorColor = accumulatorColor,
                        useFrameWeight = true,
                    )
                }
                if (outputMode == MgcSpatialOutputMode.RGB) {
                    submitOrRetainRgbFrame(
                        frame = RgbMergeFrame(
                            imageIndex = 0,
                            calibration = referenceCalibration,
                            alignmentTexture = zeroFlow,
                            weightTexture = bentoBaseWeight,
                            covarianceTexture = referenceCovariance,
                            flowBounds = MgcSpatialRgbFlowBounds.Zero,
                            useFrameWeight = true,
                        ),
                        rawTexture = referenceRaw,
                    )
                }
                strengthCapture?.let { capture ->
                    captureStrengthFrame(
                        capture = capture,
                        frameIndex = capturedFrameIndex++,
                        calibration = referenceCalibration,
                        flowTexture = zeroFlow,
                        weightTexture = bentoBaseWeight,
                        identityWeight = false,
                    )
                }
                // MGC overwrites the selected ultrashort rejection slice with the Bento mask.
                if (outputMode == MgcSpatialOutputMode.BAYER) {
                    currentMergeCovariance = currentCovariance
                    renderMerge(
                        rawTexture = bentoRaw,
                        bayerAlignmentTexture = bentoBayerAlignmentTexture,
                        weightTexture = bentoShortWeight,
                        linearKernelMaskTexture = linearKernelMask,
                        calibration = checkNotNull(bentoCalibration),
                        accumulatorColor = accumulatorColor,
                        useFrameWeight = true,
                    )
                }
                if (outputMode == MgcSpatialOutputMode.RGB) {
                    check(bentoRgbCovarianceTexture != 0) {
                        "Accepted MGC Bento RGB frame has no covariance texture"
                    }
                    submitOrRetainRgbFrame(
                        frame = RgbMergeFrame(
                            imageIndex = ultrashortIndex,
                            calibration = checkNotNull(bentoCalibration),
                            alignmentTexture = bentoBayerAlignmentTexture,
                            weightTexture = bentoShortWeight,
                            covarianceTexture = bentoRgbCovarianceTexture,
                            flowBounds = conservativeRgbFlowBounds,
                            useFrameWeight = true,
                        ),
                        rawTexture = bentoRaw,
                    )
                }
                strengthCapture?.let { capture ->
                    captureStrengthFrame(
                        capture = capture,
                        frameIndex = capturedFrameIndex++,
                        calibration = checkNotNull(bentoCalibration),
                        flowTexture = bentoFlowTexture,
                        weightTexture = bentoShortWeight,
                        identityWeight = false,
                    )
                }
                mergedFrames = 2
            } else {
                if (outputMode == MgcSpatialOutputMode.BAYER) {
                    currentMergeCovariance = referenceCovariance
                    renderMerge(
                        rawTexture = referenceRaw,
                        bayerAlignmentTexture = zeroFlow,
                        weightTexture = identityWeight,
                        linearKernelMaskTexture = linearKernelMask,
                        calibration = referenceCalibration,
                        accumulatorColor = accumulatorColor,
                        useFrameWeight = false,
                    )
                }
                if (outputMode == MgcSpatialOutputMode.RGB) {
                    submitOrRetainRgbFrame(
                        frame = RgbMergeFrame(
                            imageIndex = 0,
                            calibration = referenceCalibration,
                            alignmentTexture = zeroFlow,
                            weightTexture = identityWeight,
                            covarianceTexture = referenceCovariance,
                            flowBounds = MgcSpatialRgbFlowBounds.Zero,
                            useFrameWeight = false,
                        ),
                        rawTexture = referenceRaw,
                    )
                }
                strengthCapture?.let { capture ->
                    captureStrengthFrame(
                        capture = capture,
                        frameIndex = capturedFrameIndex++,
                        calibration = referenceCalibration,
                        flowTexture = zeroFlow,
                        weightTexture = identityWeight,
                        identityWeight = true,
                    )
                }
            }

            if (onlineRgbAccumulator != null) {
                images[0].close()
                if (bentoAccepted) images[ultrashortIndex].close()
            }
            GlesGpuScheduler.yieldToUiRenderer()

            for (index in temporalFrameRange) {
                val frame = frames[index]
                if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue
                val frameScheduleStartNs = System.nanoTime()
                var uploadCallNs = 0L
                var prepareCallNs = 0L
                var postPrepareSubmitNs = 0L
                beginTemporalScratchFrame()
                try {
                    val online = onlineRgbAccumulator
                    val temporalRaw = currentRaw.also { texture ->
                        val uploadStartNs = System.nanoTime()
                        uploadRaw(images[index], texture, "frame $index")
                        uploadCallNs = System.nanoTime() - uploadStartNs
                        if (online != null) {
                            online.rawUploadNs += uploadCallNs
                            online.rawUploadCount += 1
                            online.rawUploadBytes +=
                                width.toLong() * height * RAW_BYTES_PER_PIXEL
                        }
                    }
                    val prepareStartNs = System.nanoTime()
                    val prepared = prepareTemporalFrame(
                        frame = frame,
                        referenceExposure = referenceExposure,
                        referenceCalibration = referenceCalibration,
                        referenceGuide = referenceGuide,
                        referenceGrayPyramid = referenceGrayPyramid,
                        referenceAlignmentProducts = referenceAlignmentProducts,
                        currentRaw = temporalRaw,
                        currentGuide = currentGuide,
                        currentCovariance = currentCovariance,
                        kernelTuning = bayerKernelTuning,
                    )
                    prepareCallNs = System.nanoTime() - prepareStartNs
                    val postPrepareStartNs = System.nanoTime()
                    val mergeWeight = if (identityTemporalWeights) {
                        identityWeight
                    } else {
                        val exclusionMasks = when (frame.role) {
                            RawBurstFrameRole.SHADOW_LONG -> {
                                check(referenceHighlightMask != 0) {
                                    "Long-frame merge requires the reference highlight mask"
                                }
                                val alignedLongClippingMask =
                                    renderAlignedLongFrameClippingMask(
                                        rawTexture = temporalRaw,
                                        flowTexture = prepared.flowTexture,
                                        calibration = prepared.calibration,
                                    )
                                PLog.d(
                                    TAG,
                                    "MGC long-frame highlight guard frame=$index " +
                                        "referenceClipping=true sourceRawClipping=true " +
                                        "threshold=$LONG_FRAME_RAW_CLIPPING_THRESHOLD",
                                )
                                intArrayOf(referenceHighlightMask, alignedLongClippingMask)
                            }
                            else -> if (bentoAccepted) {
                                intArrayOf(checkNotNull(bentoMask))
                            } else {
                                IntArray(0)
                            }
                        }
                        var maskedWeight = prepared.weightTexture
                        exclusionMasks.forEach { exclusionMask ->
                            val outputWeight = createTexture(
                                mergeWeightWidth,
                                mergeWeightHeight,
                                GLES30.GL_R8,
                                GLES30.GL_LINEAR,
                            )
                            renderBentoRewrittenWeight(
                                existingWeight = maskedWeight,
                                bentoMask = exclusionMask,
                                outputWeight = outputWeight,
                                hasExistingWeight = true,
                            )
                            maskedWeight = outputWeight
                        }
                        maskedWeight
                    }
                    if (outputMode == MgcSpatialOutputMode.BAYER) {
                        currentMergeCovariance = currentCovariance
                        renderMerge(
                            rawTexture = temporalRaw,
                            bayerAlignmentTexture = prepared.bayerAlignmentTexture,
                            weightTexture = mergeWeight,
                            linearKernelMaskTexture = linearKernelMask,
                            calibration = prepared.calibration,
                            accumulatorColor = accumulatorColor,
                            useFrameWeight = true,
                        )
                    }
                    if (outputMode == MgcSpatialOutputMode.RGB) {
                        if (online != null) {
                            submitOrRetainRgbFrame(
                                frame = RgbMergeFrame(
                                    imageIndex = index,
                                    calibration = prepared.calibration,
                                    alignmentTexture = prepared.bayerAlignmentTexture,
                                    weightTexture = mergeWeight,
                                    covarianceTexture = currentCovariance,
                                    flowBounds = conservativeRgbFlowBounds,
                                    useFrameWeight = true,
                                ),
                                rawTexture = temporalRaw,
                            )
                        } else {
                            val retainedAlignment = copyPersistentTexture(
                                source = prepared.bayerAlignmentTexture,
                                textureWidth = bayerAlignmentWidth,
                                textureHeight = bayerAlignmentHeight,
                                internalFormat = GLES30.GL_RGBA32F,
                                filter = GLES30.GL_NEAREST,
                                label = "MGC RGB alignment frame $index",
                            )
                            val retainedWeight = if (mergeWeight == identityWeight) {
                                identityWeight
                            } else {
                                copyPersistentTexture(
                                    source = mergeWeight,
                                    textureWidth = mergeWeightWidth,
                                    textureHeight = mergeWeightHeight,
                                    internalFormat = GLES30.GL_R8,
                                    filter = GLES30.GL_LINEAR,
                                    label = "MGC RGB final weight frame $index",
                                )
                            }
                            val retainedCovariance = copyPersistentTexture(
                                source = currentCovariance,
                                textureWidth = guideWidth,
                                textureHeight = guideHeight,
                                internalFormat = GLES30.GL_RGB10_A2,
                                filter = GLES30.GL_LINEAR,
                                label = "MGC RGB covariance frame $index",
                            )
                            rgbMergeFrames += RgbMergeFrame(
                                imageIndex = index,
                                calibration = prepared.calibration,
                                alignmentTexture = retainedAlignment,
                                weightTexture = retainedWeight,
                                covarianceTexture = retainedCovariance,
                                flowBounds = conservativeRgbFlowBounds,
                                useFrameWeight = true,
                            )
                        }
                    }
                    strengthCapture?.let { capture ->
                        captureStrengthFrame(
                            capture = capture,
                            frameIndex = capturedFrameIndex++,
                            calibration = prepared.calibration,
                            flowTexture = prepared.flowTexture,
                            weightTexture = mergeWeight,
                            identityWeight = identityTemporalWeights,
                        )
                    }
                    mergedFrames += 1
                    if (online != null) images[index].close()
                    postPrepareSubmitNs = System.nanoTime() - postPrepareStartNs
                } finally {
                    endTemporalScratchFrame()
                }
                PLog.i(
                    TAG,
                    "MGC Spatial frame schedule index=$index frame=${frame.frameNumber} " +
                        "role=${frame.role} uploadCall=${uploadCallNs / 1_000_000L}ms " +
                        "prepareCall=${prepareCallNs / 1_000_000L}ms " +
                        "postPrepareSubmit=${postPrepareSubmitNs / 1_000_000L}ms " +
                        "totalCpu=${elapsedMs(frameScheduleStartNs)}ms",
                )
                GlesGpuScheduler.yieldToUiRenderer()
            }

            val readyStrengthCapture = strengthCapture?.also { capture ->
                check(capturedFrameIndex == capture.frameCount) {
                    "MGC Spatial noise capture count=$capturedFrameIndex, " +
                        "expected=${capture.frameCount}"
                }
            }
            var strengthQueueElapsedMs = 0L
            var queuedStrengthReadback = if (
                readyStrengthCapture?.outputMode == MgcSpatialOutputMode.BAYER
            ) {
                val startNs = System.nanoTime()
                queueStrengthReadback(readyStrengthCapture, accumulatorColor).also {
                    strengthQueueElapsedMs = (System.nanoTime() - startNs) / 1_000_000L
                }
            } else {
                null
            }
            val lensShadingCorrectionApplied: Boolean
            if (outputMode == MgcSpatialOutputMode.RGB) {
                val online = onlineRgbAccumulator
                val retainedTemporalTextures = if (online != null) {
                    check(online.contributedFrames == mergedFrames) {
                        "MGC Spatial online RGB admitted ${online.contributedFrames} frames, " +
                            "but Bayer/noise merge admitted $mergedFrames"
                    }
                    intArrayOf(
                        online.semanticAccumulator,
                        online.opponentWeightAccumulator,
                    )
                } else {
                    check(rgbMergeFrames.size == mergedFrames) {
                        "MGC Spatial RGB admitted ${rgbMergeFrames.size} frames, " +
                            "but Bayer/noise merge admitted $mergedFrames"
                    }
                    rgbMergeFrames.flatMap { frame ->
                        listOf(
                            frame.alignmentTexture,
                            frame.weightTexture,
                            frame.covarianceTexture,
                        )
                    }.toIntArray()
                }
                val temporalGpuBytes = estimatedOwnedTextureBytes()
                check(temporalGpuBytes <= RGB_TEXTURE_BUDGET_BYTES) {
                    "MGC Spatial RGB temporal resources=$temporalGpuBytes, " +
                        "budget=$RGB_TEXTURE_BUDGET_BYTES"
                }
                releaseRgbTemporalPhaseResources(
                    persistentTextures = retainedTemporalTextures,
                    strengthCapture = readyStrengthCapture,
                )
                val preparedStrengthAtlases = readyStrengthCapture?.let { capture ->
                    materializeRgbStrengthAtlases(capture).also { prepared ->
                        strengthAlignmentHostBuffer = prepared.first.cpuBuffer
                        strengthRejectionHostBuffer = prepared.second.cpuBuffer
                    }
                }
                val rgbMergeStartNs = System.nanoTime()
                val rgbOutput = if (online != null) {
                    finishOnlineRgbMerge(
                        accumulator = online,
                        outputExposureScale = outputExposure.normalizationScale,
                        diagnosticCapture = readyStrengthCapture,
                    )
                } else {
                    renderRgbMerge(
                        frames = resolveRgbFlowBounds(rgbMergeFrames),
                        images = images,
                        outputExposureScale = outputExposure.normalizationScale,
                        diagnosticCapture = readyStrengthCapture,
                    )
                }
                cpuOutput = rgbOutput.cpuBuffer
                exportedRgbTexture = rgbOutput.gpuTexture
                exportedRgbCompletionTimeline = rgbOutput.completionTimeline
                rgbDiagnosticHostBuffer = rgbOutput.diagnosticFixed16?.cpuBuffer
                readyStrengthCapture?.let { capture ->
                    val startNs = System.nanoTime()
                    queuedStrengthReadback = queueStrengthReadback(
                        capture = capture,
                        preparedAlignment = checkNotNull(preparedStrengthAtlases).first,
                        preparedRejection = preparedStrengthAtlases.second,
                        preparedFusedFixed16 = checkNotNull(rgbOutput.diagnosticFixed16),
                    )
                    strengthQueueElapsedMs = (System.nanoTime() - startNs) / 1_000_000L
                }
                lensShadingCorrectionApplied = hasLensShading()
                PLog.i(
                    TAG,
                    "MGC Spatial RGB dispatch complete frames=$mergedFrames " +
                        "took=${(System.nanoTime() - rgbMergeStartNs) / 1_000_000L}ms " +
                        "mode=${when {
                            online != null -> "online-full-accumulator"
                            else -> "streamed-band"
                        }} " +
                        "rawWindowSlots=${when {
                            online != null -> 1
                            else -> RGB_RAW_WINDOW_SLOTS
                        }} " +
                        "maxInFlight=${if (online != null) 1 else RGB_MAX_IN_FLIGHT_PASSES}",
                )
            } else {
                val bayer16 = renderBayer16(
                    accumulator = accumulatorColor,
                    outputExposureScale = outputExposure.normalizationScale,
                )
                GlesGpuScheduler.yieldToUiRenderer()
                if (useCurrentGlContext && exportGpuLinearRgbSource) {
                    exportedBayerTexture = bayer16
                    check(textures.remove(bayer16)) {
                        "Exported Spatial Bayer texture is not owned by the stacker"
                    }
                } else {
                    cpuOutput = readBayer16(bayer16)
                }
                lensShadingCorrectionApplied = false
            }
            if (queuedStrengthReadback != null) {
                PLog.i(
                    TAG,
                    "MGC Spatial strength readback queued mode=${outputMode.name} bytes=" +
                        "${queuedStrengthReadback.alignment.byteCount.toLong() +
                            queuedStrengthReadback.rejection.byteCount.toLong() +
                            queuedStrengthReadback.fusedFixed16.byteCount.toLong()} " +
                        "fixed16PrepareSubmit=" +
                        "${queuedStrengthReadback.fusedFixed16PrepareSubmitMs}ms " +
                        "modes=${queuedStrengthReadback.alignment.mode}/" +
                        "${queuedStrengthReadback.rejection.mode}/" +
                        "${queuedStrengthReadback.fusedFixed16.mode} " +
                        "alignmentSubmit=${queuedStrengthReadback.alignment.totalSubmitMs}ms " +
                        "rejectionSubmit=${queuedStrengthReadback.rejection.totalSubmitMs}ms " +
                        "fixed16Submit=${queuedStrengthReadback.fusedFixed16.totalSubmitMs}ms " +
                        "enqueue=${strengthQueueElapsedMs}ms",
                )
            }
            // Bayer queues all three diagnostics before output materialization. RGB packs the
            // exact merged camera-RGB signal during tiled reconstruction, then queues the two
            // matching RGB-resolution temporal atlases before resolving the RGB AOT.
            val strengthResolveStartNs = System.nanoTime()
            val spatialDenoiseEnabled =
                MultiFrameConfig.ENABLE_MGC_SPATIAL_DEFAULT_DENOISE && !referenceOnly
            val resolvedSpatialNoiseModel = if (
                strengthCapture != null && queuedStrengthReadback != null
            ) {
                resolveSpatialNoiseModel(strengthCapture, queuedStrengthReadback)
            } else {
                null
            }
            val spatialNoiseModel = if (spatialDenoiseEnabled) {
                resolvedSpatialNoiseModel ?: createIdentitySpatialNoiseModel(
                    referenceCalibration = referenceCalibration,
                    reason = when {
                        strengthCapture == null -> "single-admitted-frame"
                        queuedStrengthReadback == null -> "strength-readback-unavailable"
                        else -> "strength-aot-invalid"
                    },
                )
            } else {
                null
            }
            if (queuedStrengthReadback != null) {
                PLog.i(
                    TAG,
                    "MGC Spatial strength readback resolved mode=${outputMode.name} " +
                        "took=${(System.nanoTime() - strengthResolveStartNs) / 1_000_000L}ms",
                )
            }
            val denoiseModel = if (spatialNoiseModel != null) {
                when (outputMode) {
                    MgcSpatialOutputMode.BAYER ->
                        MgcSpatialDenoiseModel.fromBayerDiagnostics(
                            outputWeightsSumTotalDiag0 =
                                spatialNoiseModel.outputWeightsSumTotalDiag0,
                            outputWeightsSumTotalDiag1 =
                                spatialNoiseModel.outputWeightsSumTotalDiag1,
                        )
                    MgcSpatialOutputMode.RGB ->
                        MgcSpatialDenoiseModel.fromRgbDiagnostics(
                            outputWeightsSumTotalDiag0 =
                                spatialNoiseModel.outputWeightsSumTotalDiag0,
                            outputWeightsSumTotalDiag1 =
                                spatialNoiseModel.outputWeightsSumTotalDiag1,
                        )
                }
            } else {
                null
            }
            val outputShotNoise = spatialNoiseModel?.outputShotNoise?.let { values ->
                FloatArray(values.size) { channel ->
                    values[channel] * outputExposure.shotNoiseScale
                }
            }
            val outputReadNoise = spatialNoiseModel?.outputReadNoise?.let { values ->
                FloatArray(values.size) { channel ->
                    values[channel] * outputExposure.readNoiseVarianceScale
                }
            }
            if (spatialDenoiseEnabled) {
                checkNotNull(spatialNoiseModel) {
                    "MGC Spatial output noise coefficients were not produced"
                }
                checkNotNull(denoiseModel) {
                    "MGC Spatial correlation spectrum was not produced"
                }
            }
            if (spatialNoiseModel != null && denoiseModel != null) {
                PLog.i(
                    TAG,
                    "MGC Spatial denoise model aotMode=${outputMode.name} " +
                        "captureFrames=${strengthCapture?.frameCount} " +
                        "diag0=${spatialNoiseModel.outputWeightsSumTotalDiag0.contentToString()} " +
                        "diag1=${spatialNoiseModel.outputWeightsSumTotalDiag1.contentToString()} " +
                        "savannahRatio=${denoiseModel.diagnosticRatio} " +
                        "savannahTaps=[${denoiseModel.outerTap}," +
                        "${denoiseModel.centerTap},${denoiseModel.outerTap}] " +
                        "read=${outputReadNoise?.contentToString()} " +
                        "shot=${outputShotNoise?.contentToString()} " +
                        "outputExposureScale=${outputExposure.normalizationScale} " +
                        "strength=spatial-aot readback=atlas-pbo-deferred",
                )
            }
            checkGlError("MGC Spatial ${outputMode.name} merge")
            returned = true
            val resultLabel = when {
                exportedRgbTexture != 0 -> "${gpuLinearRgbStorage.name}_GPU"
                exportedBayerTexture != 0 -> "BAYER16_GPU"
                outputMode == MgcSpatialOutputMode.RGB -> "RGB16_CPU"
                else -> "BAYER16_CPU"
            }
            PLog.i(
                TAG,
                "MGC Spatial ${outputMode.name} merge complete frames=$mergedFrames " +
                    "output=${outputWidth}x$outputHeight " +
                    "lscApplied=$lensShadingCorrectionApplied result=$resultLabel " +
                    "programInit=${programInitMs}ms " +
                    "queueMode=${if (outputMode == MgcSpatialOutputMode.RGB) {
                        if (onlineRgbAccumulator != null) {
                            "online-raw-sequential-full-accumulator"
                        } else {
                            "streamed-raw-two-slot-two-in-flight-band"
                        }
                    } else {
                        "ordered-continuous"
                    }} " +
                    "total=${(System.nanoTime() - processStartNs) / 1_000_000L}ms",
            )
            val rgbOutput = outputMode == MgcSpatialOutputMode.RGB
            RawStackResult(
                fusedBayerBuffer = cpuOutput,
                width = outputWidth,
                height = outputHeight,
                isNormalizedSensorData = true,
                blackLevel = FloatArray(4),
                fusedBayerUsesNativeAllocator = cpuOutput != null,
                bufferLayout = if (rgbOutput) {
                    RawStackBufferLayout.LINEAR_RGB
                } else {
                    RawStackBufferLayout.CFA
                },
                inputRowStepSamples = outputWidth * if (rgbOutput) 3 else 1,
                inputColStepSamples = if (rgbOutput) 3 else 1,
                baselineExposureEv = outputExposure.baselineExposureEv,
                gpuLinearRgbSource = exportedRgbTexture.takeIf { it != 0 }?.let { textureId ->
                    GpuLinearRgbSource(
                        textureId = textureId,
                        width = outputWidth,
                        height = outputHeight,
                        samplesPerPixel = 4,
                        stackCompletionTimeline = exportedRgbCompletionTimeline,
                        storage = gpuLinearRgbStorage,
                    )
                },
                gpuBayerSource = exportedBayerTexture.takeIf { it != 0 }?.let { textureId ->
                    GpuBayerSource(
                        textureId = textureId,
                        width = outputWidth,
                        height = outputHeight,
                        stackCompletionTimeline = null,
                    )
                },
                lensShadingCorrectionApplied = lensShadingCorrectionApplied,
                mergedFrameCount = mergedFrames,
                mgcDenoiseCorrelation = denoiseModel?.correlation,
                mgcDenoiseReadNoise = outputReadNoise,
                mgcDenoiseShotNoise = outputShotNoise,
                mgcSpatialStrengthMap = spatialNoiseModel?.strengthMap?.let(
                    ::mapSpatialStrengthToOutputCoordinates,
                ),
                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenAttenuationScale = finishRawSharpenAttenuationScale,
                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
            )
        } catch (error: Exception) {
            PLog.e(TAG, "MGC Spatial ${outputMode.name} merge failed", error)
            null
        } finally {
            images.forEach { it.close() }
            release()
            GlesGpuScheduler.restoreCurrentThreadPriority(originalThreadPriority, TAG)
            LargeDirectBuffer.free(strengthAlignmentHostBuffer)
            LargeDirectBuffer.free(strengthRejectionHostBuffer)
            LargeDirectBuffer.free(rgbDiagnosticHostBuffer)
            if (!returned) {
                exportedRgbCompletionTimeline?.releasePending()
                LargeDirectBuffer.free(cpuOutput)
                if (exportedBayerTexture != 0) {
                    GLES30.glDeleteTextures(1, intArrayOf(exportedBayerTexture), 0)
                }
                if (exportedRgbTexture != 0) {
                    GLES30.glDeleteTextures(1, intArrayOf(exportedRgbTexture), 0)
                }
            }
        }
    }

    private fun processSabreFrames(frames: List<RawStackFrame>): RawStackResult? {
        require(processorPipeline == MgcRawProcessorPipeline.SABRE &&
            mergeMethod == MgcMergeMethod.SABRE) {
            "IRIS_26545_V1_2 Sabre semantic owner entered with non-Sabre pipeline/method"
        }
        val images = frames.map { it.image }
        require(outputMode == MgcSpatialOutputMode.RGB) {
            "The native MGC SabreProcessor resolves to linear RGB"
        }
        require(!exportGpuLinearRgbSource || useCurrentGlContext) {
            "MGC Sabre GPU RGB export requires the caller-owned current EGL context"
        }
        if (images.isEmpty() || width <= 1 || height <= 1) {
            images.forEach { it.close() }
            return null
        }
        if ((width and 1) != 0 || (height and 1) != 0) {
            PLog.e(SABRE_TAG, "MGC Sabre requires an even Bayer extent; size=${width}x$height")
            images.forEach { it.close() }
            return null
        }
        if (images.any { it.width != width || it.height != height }) {
            PLog.e(TAG, "MGC Sabre received mixed RAW dimensions")
            images.forEach { it.close() }
            return null
        }
        if (images.any { it.format != ImageFormat.RAW_SENSOR }) {
            PLog.e(TAG, "MGC Sabre only accepts RAW_SENSOR images")
            images.forEach { it.close() }
            return null
        }
        /* IRIS_26547_SABRE_12_PLUS_3_ROLE_CONTRACT */
        require(frames.first().role == RawBurstFrameRole.NORMAL) {
            "26547 Sabre first frame must remain the SHORT/NORMAL reference"
        }
        val normalFrameCount = frames.count { it.role == RawBurstFrameRole.NORMAL }
        val shadowLongFrameCount = frames.count { it.role == RawBurstFrameRole.SHADOW_LONG }
        val highlightShortFrameCount = frames.count { it.role == RawBurstFrameRole.HIGHLIGHT_SHORT }
        require(normalFrameCount >= 1 && highlightShortFrameCount <= 1 &&
            normalFrameCount + shadowLongFrameCount + highlightShortFrameCount == frames.size) {
            "26587 Sabre accepts NORMAL + SHADOW_LONG + at most one HIGHLIGHT_SHORT"
        }
        val referenceExposure = validExposureProduct(frames.first().exposureProduct)
        frames.filter { it.role == RawBurstFrameRole.SHADOW_LONG }.forEach { frame ->
            require(validExposureProduct(frame.exposureProduct) > referenceExposure) {
                "26547 Sabre SHADOW_LONG exposure must exceed SHORT reference exposure"
            }
        }
        frames.filter { it.role == RawBurstFrameRole.HIGHLIGHT_SHORT }.forEach { frame ->
            require(validExposureProduct(frame.exposureProduct) < referenceExposure) {
                "26587 HIGHLIGHT_SHORT exposure must be below NORMAL reference exposure"
            }
        }
        val mergedFrameCount = normalFrameCount + shadowLongFrameCount
        PLog.i(
            SABRE_TAG,
            "IRIS_26587_SABRE_ROLE_CONTRACT normal=$normalFrameCount shadowLong=$shadowLongFrameCount " +
                "highlightShort=$highlightShortFrameCount scheduled=${frames.size} merged=$mergedFrameCount " +
                "referenceRole=NORMAL shortNormalAccumulator=false shortDng=false shortSr=false",
        )
        if (shadowLongFrameCount > 0) {
            PLog.i(
                SABRE_TAG,
                "IRIS_26558_SABRE_LONG_SOURCE_CLIP_GUARD enabled=true role=SHADOW_LONG " +
                    "domain=unnormalized_sensor_raw footprint=exact_sabre_3x3 allCfa=true " +
                    "wholeLongObservationReject=true coverageSupportGuard=true shortHighlightAuthority=true " +
                    "sourceClippingPoint=${sabreShadowLongSourceClippingPoint()}",
            )
        }
        baseFrameCamera2Model = frames.firstOrNull()
            ?.channelNoiseProfile
            ?.let(RawNoiseModel::fromCamera2NoiseProfile)
            ?.takeIf { it.hasValidCamera2Profile }
            ?: RawNoiseModel.EMPTY
        val resolvedNoiseModels = frames.map(::resolveNoiseModelForFrame)
        if (resolvedNoiseModels.any { it.source == RawNoiseModelSource.UNAVAILABLE }) {
            PLog.e(
                TAG,
                "MGC Sabre noise profile is unavailable for ${noiseProfileSelection.id}",
            )
            images.forEach { it.close() }
            return null
        }

        var cpuOutput: ByteBuffer? = null
        var sabreAccumulatedReadback: ByteBuffer? = null
        var sabreResolvedRgb: ByteBuffer? = null
        var normalStackedDngRaw16: ByteBuffer? = null
        var normalStackedDngSupport = SabreNormalDngSupportStats.identity()
        var normalStackedDngNoiseProfile: DoubleArray? = null
        var superResDetailPath: String? = null
        var superResLinearRawPath: String? = null
        var true2xResult: True2xResult? = null
        val true2xEvidence = ArrayList<True2xFrameEvidence>()
        /* IRIS_26568_JPEG_TRUE2X_PHASE_RESERVOIR
         * DNG requests retain the exact full 26567 NORMAL evidence population. JPEG-only SR keeps
         * the best two accepted frames per global phase (max 8). The strongest 26567 member of
         * every phase is therefore preserved while a second observation can add local phase/SNR.
         */
        val true2xFastPhaseSlots: Array<True2xFrameEvidence?>? =
            if (enableSabreSuperRes && !exportNormalStackedDng) arrayOfNulls(TRUE2X_JPEG_MAX_EVIDENCE) else null
        var exportedTexture = 0
        var highlightShortTexture26587 = 0
        var highlightShortMask26587 = 0
        var highlightShortExposureRatio26587 = 1f
        var highlightShortAdmitted26587 = false
        var highlightShortMaskGenerated26587 = false
        var highlightShortAppliedToTrue2x26587 = false
        var highlightShortFullActivePixels26595: Int? = null
        var returned = false
        val originalThreadPriority = GlesGpuScheduler.lowerCurrentThreadPriority(SABRE_TAG)
        val processStartNs = System.nanoTime()
        return try {
            if (useCurrentGlContext) attachCurrentEgl() else initEgl()
            ensureGles3()
            initSabrePrograms()
            renderFbo = createFramebuffer()
            applyRawRenderState()

            val extractedWidth = ceilDiv(width, 2)
            val extractedHeight = ceilDiv(height, 2)
            val superResWidth = if (enableSabreSuperRes) width * 2 else 0
            val superResHeight = if (enableSabreSuperRes) height * 2 else 0
            if (enableSabreSuperRes) {
                requireNotNull(sabreSuperResTempDir) {
                    "26564 true 2x Sabre Super Res requires a temp directory"
                }
                /* The CPU fallback applies only to the new reconstruction stage. Native Sabre/VGN
                 * remains the proven GPU owner and supplies the low-frequency chroma guide.
                 */
                require(exportGpuLinearRgbSource && gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F) {
                    "26564 true2x requires the proven Sabre RGBA16F post-VGN carrier"
                }
                /* IRIS_26564_BOUNDED_TILES_NO_MONOLITHIC_50MP_TEXTURE
                 * Do not gate SR on full-output GL_MAX_TEXTURE_SIZE. GPU uses bounded tiles and
                 * CPU is the mandatory fallback when the accelerator is unavailable.
                 */
            }
            val coverageWidth = ceilDiv(extractedWidth, 2)
            val coverageHeight = ceilDiv(extractedHeight, 2)
            val referenceRaw = createTexture(width, height, GLES30.GL_R16UI, GLES30.GL_NEAREST)
            val currentRaw = createTexture(width, height, GLES30.GL_R16UI, GLES30.GL_NEAREST)
            val referenceExtracted = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_NEAREST,
            )
            val currentExtracted = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_NEAREST,
            )
            val referenceGuide = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_LINEAR,
            )
            val currentGuide = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGBA16F,
                GLES30.GL_LINEAR,
            )
            val referenceCovariance = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGB10_A2,
                GLES30.GL_LINEAR,
            )
            val currentCovariance = createTexture(
                extractedWidth,
                extractedHeight,
                GLES30.GL_RGB10_A2,
                GLES30.GL_LINEAR,
            )
            val accumulatedColor = createTexture(
                width,
                height,
                GLES30.GL_RGBA16F,
                GLES30.GL_NEAREST,
            )
            val accumulatedWeightsGb = createTexture(
                width,
                height,
                GLES30.GL_RG16F,
                GLES30.GL_NEAREST,
            )
            /* IRIS_26564_TRUE_2X_RETIRES_NATIVE_UPSCALE_DETAIL_OWNER
             * Keep the old carrier functions dormant for rollback provenance, but allocate no
             * full-frame 2x luma/detail surface. True 2x is direct multiframe CFA reconstruction.
             */
            val superResDetailAccumulator = 0
            val accumulatedCoverage = createTexture(
                coverageWidth,
                coverageHeight,
                GLES30.GL_R8,
                GLES30.GL_LINEAR,
            )
            /* IRIS_26545_SABRE_NORMALIZED16_DNG
             * Keep only signal+weight for the RAW sidecar. It uses the exact Sabre flow,
             * covariance and temporal rejection but never ResolveSabre, WB/color transform,
             * lens shading, denoise, tone, sharpening or JPEG processing.
             */
            val normalDngAccumulator = if (exportNormalStackedDng) {
                createTexture(width, height, GLES30.GL_RG16F, GLES30.GL_NEAREST)
            } else {
                0
            }
            /* IRIS_26547_V1_1_MOTION_DNG_26546_PRESERVATION
             * Motion has no SHADOW_LONG frames, so keep its exact 26546 Sabre DNG support owner:
             * the shared measured RGB coverage + measured average merge factor. Only bracketed Night
             * allocates a second NORMAL-only coverage map so Long support can never leak into DNG.
             */
            val normalDngCoverage = if (exportNormalStackedDng && shadowLongFrameCount > 0) {
                createTexture(coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_LINEAR)
            } else {
                0
            }
            clearSabreAccumulators(
                accumulatedColor,
                accumulatedWeightsGb,
                accumulatedCoverage,
                coverageWidth,
                coverageHeight,
            )
            if (normalDngAccumulator != 0) {
                clearSabreNormalDngAccumulator(normalDngAccumulator)
                if (normalDngCoverage != 0) {
                    clearSabreCoverage(
                        normalDngCoverage,
                        coverageWidth,
                        coverageHeight,
                        "Sabre NORMAL-only DNG coverage clear",
                    )
                }
            }

            val kernelTuning = createBayerKernelTuning(
                frame = frames.first(),
                image = images.first(),
                // Longs are opportunistic evidence, never guaranteed Short temporal support.
                frameCount = normalFrameCount,
            )
            val sabreKernelParameters = MgcSabreKernelTuning.build(
                referenceSnr = kernelTuning.referenceSnr,
                frameCount = normalFrameCount,
                mergeGradientThreshold = sabreMergeGradientThreshold,
            )
            val sabreResolveParameters = MgcSabreResolveTuning.build(
                referenceSnr = kernelTuning.referenceSnr,
                desiredExposureProduct = frames.first().desiredExposureProduct,
                actualExposureProduct = frames.first().exposureProduct,
            )
            val referenceCalibration = calibrationForFrame(
                frame = frames.first(),
                exposureScale = 1f,
                kernelTuning = kernelTuning,
            )
            val sabreResolveFinalBlackLevel =
                sabreResolveBlackLevel(referenceCalibration.blackLevels)
            PLog.i(
                SABRE_TAG,
                "MGC Sabre NoiseModel meanSignal=${kernelTuning.referenceSignal} " +
                    "snr=${kernelTuning.referenceSnr} " +
                    "effectiveSnr=${MgcSabreKernelTuning.effectiveSnr(kernelTuning.referenceSnr, normalFrameCount)} " +
                    "normalSupport=$normalFrameCount shadowLongEvidence=$shadowLongFrameCount " +
                    "kernelParams=${sabreKernelParameters.directionalScale}," +
                    "${sabreKernelParameters.isotropicScale}," +
                    "${sabreKernelParameters.gradientThreshold}," +
                    "${sabreKernelParameters.gradientTransition}," +
                    "${sabreKernelParameters.anisotropyScale}," +
                    "${sabreKernelParameters.coherenceScale} " +
                    "forceReferenceColorRgb=${sabreKernelParameters.forceReferenceColorRgb} " +
                    "mergeGradientThreshold=${sabreMergeGradientThreshold ?: "adaptive"} " +
                    "guideColorSpace=sqrt noiseLut=qmc64x10 " +
                    "alignmentInputGain=${referenceCalibration.alignmentGain} " +
                    "alignmentDomain=signed-s16",
            )
            uploadRaw(images.first(), referenceRaw, "Sabre reference")
            renderSabreExtract(referenceRaw, referenceExtracted, extractedWidth, extractedHeight)
            val referenceNoise = createSabreNoiseLut(
                referenceCalibration,
                referenceCalibration,
            )
            renderSabreGuideAndCovariance(
                extracted = referenceExtracted,
                noiseTexture = referenceNoise,
                calibration = referenceCalibration,
                guide = referenceGuide,
                covariance = referenceCovariance,
                guideWidth = extractedWidth,
                guideHeight = extractedHeight,
                kernelParameters = sabreKernelParameters,
            )
            val referenceGrayPyramid = buildGrayPyramid(referenceRaw, referenceCalibration)
            val referenceAlignmentProducts = buildReferenceAlignmentProducts(referenceGrayPyramid)
            val zeroFlow = SabreConvertedAlignment.constant(createZeroFlowTexture())
            val identityWeight = createIdentityWeightTexture()
            val accumulatedWeightScale = maxSabreAccumulatedWeight(mergedFrameCount)
            renderSabreMerge(
                extracted = referenceExtracted,
                flow = zeroFlow,
                covariance = referenceCovariance,
                weight = identityWeight,
                calibration = referenceCalibration,
                accumulatedColor = accumulatedColor,
                accumulatedWeightsGb = accumulatedWeightsGb,
                extractedWidth = extractedWidth,
                extractedHeight = extractedHeight,
                useFrameWeight = false,
                shadowLongSourceClipGuard = false,
            )
            if (enableSabreSuperRes) {
                val referenceEvidence = persistTrue2xEvidence(
                    frameIndex = 0,
                    calibration = referenceCalibration,
                    flow = zeroFlow,
                    covariance = referenceCovariance,
                    rejection = identityWeight,
                    covarianceWidth = extractedWidth,
                    covarianceHeight = extractedHeight,
                    rejectionWidth = coverageWidth,
                    rejectionHeight = coverageHeight,
                    useFrameWeight = false,
                    existingPhaseEvidence = true2xFastPhaseSlots,
                    referenceRawTexture = referenceRaw,
                    currentRawTexture = referenceRaw,
                    referenceCalibration = referenceCalibration,
                )
                if (true2xFastPhaseSlots == null) true2xEvidence += referenceEvidence
            }
            if (normalDngAccumulator != 0) {
                renderSabreNormalDngMerge(
                    raw = referenceRaw,
                    flow = zeroFlow,
                    covariance = referenceCovariance,
                    weight = identityWeight,
                    calibration = referenceCalibration,
                    accumulator = normalDngAccumulator,
                    useFrameWeight = false,
                )
            }
            GlesGpuScheduler.yieldToUiRenderer()

            for (index in 1 until frames.size) {
                val transientTextureStart = textures.size
                val frameStartNs = System.nanoTime()
                val frame = frames[index]
                val exposureScale = (
                    referenceExposure / validExposureProduct(frame.exposureProduct)
                    ).toFloat().coerceIn(MIN_EXPOSURE_SCALE, MAX_EXPOSURE_SCALE)
                val calibration = calibrationForFrame(frame, exposureScale, kernelTuning)
                uploadRaw(images[index], currentRaw, "Sabre frame $index")
                renderSabreExtract(currentRaw, currentExtracted, extractedWidth, extractedHeight)
                val noiseTexture = createSabreNoiseLut(referenceCalibration, calibration)
                renderSabreGuideAndCovariance(
                    extracted = currentExtracted,
                    noiseTexture = noiseTexture,
                    calibration = calibration,
                    guide = currentGuide,
                    covariance = currentCovariance,
                    guideWidth = extractedWidth,
                    guideHeight = extractedHeight,
                    kernelParameters = sabreKernelParameters,
                )
                val currentGrayPyramid = buildGrayPyramid(currentRaw, calibration)
                val alignment = alignPyramids(
                    referenceGrayPyramid,
                    currentGrayPyramid,
                    referenceAlignmentProducts,
                )
                val flow = createSabreConvertedAlignment(alignment)
                val unblockerWidth = ceilDiv(width, UNBLOCKER_FULLRES_TILE_SIZE * 2)
                val unblockerHeight = ceilDiv(height, UNBLOCKER_FULLRES_TILE_SIZE * 2)
                val unblocker = createTexture(
                    unblockerWidth,
                    unblockerHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                )
                renderUnblocker(
                    currentRaw,
                    calibration,
                    unblocker,
                    unblockerWidth,
                    unblockerHeight,
                )
                val reverseWeight = createTexture(
                    extractedWidth,
                    extractedHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                )
                val pixelDifference = createTexture(
                    extractedWidth,
                    extractedHeight,
                    GLES30.GL_R8,
                    GLES30.GL_NEAREST,
                )
                val durationRobustness = sabreExposureDurationRobustness(frames.first(), frame)
                renderSabreRejection(
                    referenceGuide,
                    currentGuide,
                    flow,
                    unblocker,
                    noiseTexture,
                    reverseWeight,
                    pixelDifference,
                    extractedWidth,
                    extractedHeight,
                    durationRobustness,
                )
                val frameWeight = createTexture(
                    coverageWidth,
                    coverageHeight,
                    GLES30.GL_R8,
                    GLES30.GL_LINEAR,
                )
                renderDilation(reverseWeight, frameWeight)
                if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {
                    /* IRIS_26587_SHORT_REFERENCE_DOMAIN_ALIGNMENT_NATIVE_RECONSTRUCTION
                     * Alignment/rejection above used exposure-normalized calibration. SHORT is never
                     * added to NORMAL coverage/color/weight accumulators. Reconstruct it separately
                     * at native exposure with the same flow/covariance geometry, then create one
                     * fail-closed whole-RGB mask while the exact RAW/alignment evidence is resident.
                     */
                    require(index == frames.lastIndex) {
                        "26587 HIGHLIGHT_SHORT must be scheduled after all NORMAL/LONG evidence"
                    }
                    val nativeShortCalibration = calibrationForFrame(frame, 1f, kernelTuning)
                    highlightShortExposureRatio26587 = exposureScale
                    highlightShortTexture26587 = resolveSabreShortNativeExposure26587(
                        extracted = currentExtracted,
                        flow = flow,
                        covariance = currentCovariance,
                        calibration = nativeShortCalibration,
                        identityWeight = identityWeight,
                        resolveParameters = sabreResolveParameters,
                    )
                    /* IRIS_26594_GPU_REGION_ANCHORED_SHORT_HANDOFF
                     * Build radiometric seeds only in the bright but still-measurable NORMAL/SHORT
                     * overlap band, then propagate them through an 8-connected highlight region.
                     * Every propagated cell and every final native pixel still passes the SHORT's
                     * own Sabre weight/flow/unblocker/headroom gates. NORMAL temporal coverage is
                     * intentionally not a SHORT-geometry authority.
                     */
                    val shortRegionSeed26594 = createTexture(
                        coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_NEAREST,
                    )
                    val shortRegion26594 = createTexture(
                        coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_NEAREST,
                    )
                    renderSabreShortRegionSeed26595(
                        referenceRaw = referenceRaw,
                        shortRaw = currentRaw,
                        flow = flow,
                        referenceCalibration = referenceCalibration,
                        shortCalibration = nativeShortCalibration,
                        exposureRatio = exposureScale,
                        outputSeed = shortRegionSeed26594,
                        outputRegion = shortRegion26594,
                    )
                    val shortRegionTrustA26594 = createTexture(
                        coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_NEAREST,
                    )
                    val shortRegionTrustB26594 = createTexture(
                        coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_NEAREST,
                    )
                    var shortRegionTrust26594 = shortRegionSeed26594
                    repeat(SHORT_REGION_PROPAGATION_PASSES_26594) { pass ->
                        val outputTrust = if ((pass and 1) == 0) {
                            shortRegionTrustA26594
                        } else {
                            shortRegionTrustB26594
                        }
                        renderSabreShortRegionPropagate26594(
                            seed = shortRegionSeed26594,
                            region = shortRegion26594,
                            current = shortRegionTrust26594,
                            output = outputTrust,
                        )
                        shortRegionTrust26594 = outputTrust
                    }
                    highlightShortMask26587 = createTexture(
                        width, height, GLES30.GL_R8, GLES30.GL_NEAREST,
                    )
                    renderSabreShortRestoreMask26595(
                        referenceRaw = referenceRaw,
                        shortRaw = currentRaw,
                        flow = flow,
                        regionTrust = shortRegionTrust26594,
                        referenceCalibration = referenceCalibration,
                        shortCalibration = nativeShortCalibration,
                        exposureRatio = exposureScale,
                        output = highlightShortMask26587,
                    )
                    val shortMaskProbe26590 = probeSabreShortRestoreMask26590(highlightShortMask26587)
                    highlightShortFullActivePixels26595 =
                        countSabreShortRestoreMaskFull26595(highlightShortMask26587)
                    val fullActiveText26595 = highlightShortFullActivePixels26595?.toString() ?: "UNAVAILABLE"
                    val shortMaskEffectDetails26591 =
                        "probe=${shortMaskProbe26590.width}x${shortMaskProbe26590.height} " +
                            "active=${shortMaskProbe26590.activePixels}/${shortMaskProbe26590.totalPixels} " +
                            "strong=${shortMaskProbe26590.strongPixels}/${shortMaskProbe26590.totalPixels} " +
                            "fullActive=$fullActiveText26595/${Math.multiplyExact(width, height)} " +
                            "maxHandoffWeight=${shortMaskProbe26590.maxConfidence} " +
                            "meanHandoffWeight=${shortMaskProbe26590.meanConfidence} " +
                            "handoffStart=0.90 fullShortAt=0.98 shortHeadroomThreshold=0.90 " +
                            "boundaryRadiometry=subpixelSameCfaPhase regionFloor=0.70 boundaryCeiling=0.90 " +
                            "regionPropagation=8connected passes=$SHORT_REGION_PROPAGATION_PASSES_26594 " +
                            "actualSensorClipBypass=true clipPhasesMin=1 clippedPhaseShortProof=true pureFlowGeometry=true " +
                            "flowVariationRawPxMax=2.0 sabrePhotometricGate=false unblockerGate=false " +
                            "normalCoverageGate=false sameSabreFlow=true wholeRgb=true maskFilter=NEAREST"
                    PLog.i(SABRE_TAG, "IRIS_26590_SHORT_MASK_EFFECT $shortMaskEffectDetails26591")
                    /* IRIS_26591_SHORT_MASK_EFFECT_MOTIONTRACE
                     * Telemetry only: expose the already-computed 26590 read-only mask probe in the
                     * capture's durable MotionTrace. No mask, flow, weight, or RGB math changes.
                     */
                    MotionTrace.processingState(
                        "IRIS_26592_SHORT_HANDOFF_EFFECT",
                        shortMaskEffectDetails26591,
                    )
                    highlightShortAdmitted26587 = true
                    highlightShortMaskGenerated26587 = true
                    PLog.i(
                        SABRE_TAG,
                        "IRIS_26596_SHORT_REGION_AUXILIARY_READY exposureRatio=$exposureScale " +
                            "normalFrames=$normalFrameCount boundaryRadiometry=subpixelSameCfaPhase " +
                            "regionPropagationPasses=$SHORT_REGION_PROPAGATION_PASSES_26594 " +
                            "actualSensorClipBypass=true fullActive=${highlightShortFullActivePixels26595 ?: -1} " +
                            "photometricWeightAuthority=false unblockerAuthority=false pureFlowGeometry=true " +
                            "normalCoverageAuthority=false normalAccumulator=false dng=false srEvidence=false " +
                            "nativeExposureReconstruction=true wholeRgbMask=true",
                    )
                } else {
                    if (frame.role == RawBurstFrameRole.SHADOW_LONG) {
                        renderSabreShadowLongCoverage(
                            weight = frameWeight,
                            extracted = currentExtracted,
                            flow = flow,
                            accumulatedCoverage = accumulatedCoverage,
                            coverageWidth = coverageWidth,
                            coverageHeight = coverageHeight,
                            extractedWidth = extractedWidth,
                            extractedHeight = extractedHeight,
                            accumulatedWeightScale = accumulatedWeightScale,
                        )
                    } else {
                        renderSabreCoverage(
                            frameWeight,
                            accumulatedCoverage,
                            coverageWidth,
                            coverageHeight,
                            accumulatedWeightScale,
                        )
                    }
                    renderSabreMerge(
                        extracted = currentExtracted,
                        flow = flow,
                        covariance = currentCovariance,
                        weight = frameWeight,
                        calibration = calibration,
                        accumulatedColor = accumulatedColor,
                        accumulatedWeightsGb = accumulatedWeightsGb,
                        extractedWidth = extractedWidth,
                        extractedHeight = extractedHeight,
                        useFrameWeight = true,
                        shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG,
                    )
                }
                /* IRIS_26564_NIGHT_LONG_EXCLUDED_FROM_TRUE_2X
                 * Native Sabre still admits validated SHADOW_LONG evidence for Night SNR. True 2x
                 * spatial reconstruction accepts NORMAL/Short frames only, preserving the proven
                 * rule that long-exposure blur cannot become high-frequency SR evidence.
                 */
                if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL) {
                    val candidateEvidence = persistTrue2xEvidence(
                        frameIndex = index,
                        calibration = calibration,
                        flow = flow,
                        covariance = currentCovariance,
                        rejection = frameWeight,
                        covarianceWidth = extractedWidth,
                        covarianceHeight = extractedHeight,
                        rejectionWidth = coverageWidth,
                        rejectionHeight = coverageHeight,
                        useFrameWeight = true,
                        existingPhaseEvidence = true2xFastPhaseSlots,
                        referenceRawTexture = referenceRaw,
                        currentRawTexture = currentRaw,
                        referenceCalibration = referenceCalibration,
                    )
                    if (true2xFastPhaseSlots == null) true2xEvidence += candidateEvidence
                }
                if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL) {
                    renderSabreNormalDngMerge(
                        raw = currentRaw,
                        flow = flow,
                        covariance = currentCovariance,
                        weight = frameWeight,
                        calibration = calibration,
                        accumulator = normalDngAccumulator,
                        useFrameWeight = true,
                    )
                    if (normalDngCoverage != 0) {
                        renderSabreCoverage(
                            frameWeight,
                            normalDngCoverage,
                            coverageWidth,
                            coverageHeight,
                            maxSabreAccumulatedWeight(normalFrameCount),
                        )
                    }
                }
                PLog.i(
                    SABRE_TAG,
                    "MGC Sabre frame=$index/${frames.lastIndex} number=${frame.frameNumber} " +
                        "role=${frame.role} exposureScale=$exposureScale " +
                        "durationRobustness=$durationRobustness submit=${elapsedMs(frameStartNs)}ms",
                )
                if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT && highlightShortAdmitted26587) {
                    /* IRIS_26587_SHORT_TRANSIENT_LIFETIME
                     * Preserve only the native SHORT RGBA16F carrier and scalar restore mask beyond
                     * this frame. All alignment/rejection/raw temporaries still follow the exact
                     * 26586 per-frame cleanup boundary.
                     */
                    releaseTexturesFromExcept(
                        transientTextureStart,
                        intArrayOf(highlightShortTexture26587, highlightShortMask26587),
                    )
                } else {
                    releaseTexturesFrom(transientTextureStart)
                }
                GlesGpuScheduler.yieldToUiRenderer()
            }

            /* IRIS_26545_SABRE_MEASURED_SUPPORT
             * Match current MGC/Sabre behavior: derive the merged noise coefficient from the
             * actual accumulated green weights after all temporal rejection/merge decisions.
             * This is measured support, not a pre-merge SNR lookup.
             */
            val sabreAverageMergeFactor = readSabreAverageMergeFactor(
                accumulatedWeightsGb = accumulatedWeightsGb,
            )
            val sabreNoiseModelScale = sabreAverageMergeFactor
            PLog.i(
                SABRE_TAG,
                "MGC Sabre merged NoiseModel averageMergeFactor=$sabreAverageMergeFactor " +
                    "coefficientScale=$sabreNoiseModelScale",
            )

            if (normalDngAccumulator != 0) {
                val normalizedDngTexture = renderBayer16(
                    accumulator = normalDngAccumulator,
                    outputExposureScale = 1f,
                )
                normalStackedDngRaw16 = readBayer16(normalizedDngTexture)
                releaseOwnedTexture(normalizedDngTexture, "Sabre normalized16 DNG readback")
                if (normalDngCoverage != 0) {
                    // Night 12+3: DNG owns only measured NORMAL coverage; Long RGB support is excluded.
                    normalStackedDngSupport = resolveSabreNormalDngSupportStats(
                        accumulatedCoverage = normalDngCoverage,
                        coverageWidth = coverageWidth,
                        coverageHeight = coverageHeight,
                        accumulatedWeightScale = maxSabreAccumulatedWeight(normalFrameCount),
                        frameCount = normalFrameCount,
                        sabreNoiseModelScale = 1f / normalFrameCount.coerceAtLeast(1).toFloat(),
                    )
                    normalStackedDngNoiseProfile = createSabreNormalDngNoiseProfile(
                        frames = frames.filter { it.role == RawBurstFrameRole.NORMAL },
                        support = normalStackedDngSupport,
                    )
                } else {
                    /* IRIS_26587_MOTION_DNG_NORMAL_ONLY_SUPPORT
                     * Motion may schedule one HIGHLIGHT_SHORT auxiliary, but stacked DNG support and
                     * noise ownership remain the exact NORMAL set. SHORT never changes DNG frame
                     * count, support statistics, or per-frame noise aggregation.
                     */
                    normalStackedDngSupport = resolveSabreNormalDngSupportStats(
                        accumulatedCoverage = accumulatedCoverage,
                        coverageWidth = coverageWidth,
                        coverageHeight = coverageHeight,
                        accumulatedWeightScale = accumulatedWeightScale,
                        frameCount = normalFrameCount,
                        sabreNoiseModelScale = sabreNoiseModelScale,
                    )
                    normalStackedDngNoiseProfile = createSabreNormalDngNoiseProfile(
                        frames = frames.filter { it.role == RawBurstFrameRole.NORMAL },
                        support = normalStackedDngSupport,
                    )
                }
                PLog.i(
                    SABRE_TAG,
                    "IRIS_26547_SABRE_NORMALIZED16_DNG_READY normalFrames=$normalFrameCount " +
                        "shadowLongExcluded=$shadowLongFrameCount " +
                        "sameSabreFlow=true sameSabreRejection=true sameSabreCovariance=true " +
                        "resolveSabre=false demosaic=false wb=false lsc=false denoise=false " +
                        "tone=false sharpen=false fullRangeNormalized16=true blackLevel=0 whiteLevel=65535 " +
                        "support=${normalStackedDngSupport}",
                )
            }

            renderSabreDehomogenize(
                accumulatedColor,
                accumulatedWeightsGb,
                accumulatedCoverage,
                alphaScale = accumulatedWeightScale / mergedFrameCount.toFloat(),
                alphaBias = 1f / mergedFrameCount.toFloat(),
            )
            // The original merge shaders write normalized, white-balanced half floats. The
            // Resolve AOT accepts those RGBA16F bit patterns directly; rawScale applies only to
            // the black/white scalar parameters below.
            sabreAccumulatedReadback = readSabreAccumulatedRgba16f(accumulatedColor)
            sabreResolvedRgb = checkNotNull(
                LargeDirectBuffer.allocate(
                    width.toLong() * height * 3L * Short.SIZE_BYTES,
                    "MGC Sabre Resolve RGB16",
                ),
            ) { "Unable to allocate MGC Sabre Resolve output" }
            val demosaicWhiteLevel = minOf(
                (sensorWhiteLevel * sabreResolveRawScale).toInt(),
                Short.MAX_VALUE.toInt(),
            )
                .coerceAtLeast(1)
            val demosaicBlendRange =
                SABRE_DEMOSAIC_BLEND_END - SABRE_DEMOSAIC_BLEND_START
            PLog.i(
                SABRE_TAG,
                "MGC Sabre Resolve domain=mgc14 rawScale=$sabreResolveRawScale " +
                    "black=${sabreResolveFinalBlackLevel.contentToString()} " +
                    "gains=${sabreResolveFinalGains.contentToString()} " +
                    "demosaicWhite=$demosaicWhiteLevel " +
                    "outputWhite=${sabreResolveParameters.outputWhiteLevel} " +
                    "demosaicSharpness=${sabreResolveParameters.demosaicSharpness}",
            )
            MgcSabreResolver.resolve(
                accumulatedColorRgba16f = sabreAccumulatedReadback,
                outputRgb16Planar = sabreResolvedRgb,
                width = width,
                height = height,
                cfaPattern = cfaPattern,
                finalBlackLevel = sabreResolveFinalBlackLevel,
                finalGains = sabreResolveFinalGains,
                demosaicWhiteLevel = demosaicWhiteLevel,
                outputWhiteLevel = sabreResolveParameters.outputWhiteLevel,
                demosaicBlendScale = -demosaicBlendRange * mergedFrameCount,
                demosaicBlendBias = SABRE_DEMOSAIC_BLEND_END / demosaicBlendRange,
                demosaicSharpnessScale =
                    demosaicWhiteLevel * sabreResolveParameters.demosaicSharpness,
            )
            logSabreResolvedRgbStats(sabreResolvedRgb)
            LargeDirectBuffer.free(sabreAccumulatedReadback)
            sabreAccumulatedReadback = null

            val nativeResolvedPlanes = IntArray(3) {
                createTexture(
                    width,
                    height,
                    GLES30.GL_R16UI,
                    GLES30.GL_NEAREST,
                )
            }
            uploadSabreResolvedRgb16Planar(sabreResolvedRgb, nativeResolvedPlanes)
            LargeDirectBuffer.free(sabreResolvedRgb)
            sabreResolvedRgb = null
            val lensShadingTexture = createLensShadingTexture()
            val fullOutput = MgcSpatialRgbRect(0, 0, width, height)
            val fullOutputTile = MgcSpatialRgbTile(index = 0, outputCore = fullOutput)
            val chromaPostprocessor = checkNotNull(sabreRgbChromaPostprocessor) {
                "Iris current-MGC Sabre VGN color noise/IIR postprocessor is not initialized"
            }
            chromaPostprocessor.beginFullFrame(listOf(fullOutputTile))
            renderSabreOutputTransform(
                resolvedRgbPlanes = nativeResolvedPlanes,
                lensShadingTexture = lensShadingTexture,
                finalBlackLevel = sabreResolveFinalBlackLevel,
                demosaicWhiteLevel = demosaicWhiteLevel.toFloat(),
                output = chromaPostprocessor.normalizationTargetTexture(),
            )
            /* IRIS_26564_TRUE2X_DNG_CARRIER
             * DNG and JPEG share the same direct-CFA RGB16F carrier. No native-RGB interpolation
             * or detail multiplication is produced here.
             */
            chromaPostprocessor.markBandWritten(fullOutputTile)
            if (!exportGpuLinearRgbSource) {
                val outputBytes = width.toLong() * height * 3L * Short.SIZE_BYTES
                cpuOutput = LargeDirectBuffer.allocate(outputBytes, "MGC Sabre VGN RGB16 output")
                    ?.order(ByteOrder.nativeOrder()) ?: error(
                    "Unable to allocate MGC Sabre VGN RGB16 output",
                )
            }
            GlesGpuScheduler.memoryBarrier()
            val chromaResult = chromaPostprocessor.process(
                obtainCpuOutput = { checkNotNull(cpuOutput) },
                deferCpuReadback = exportGpuLinearRgbSource,
                onFinalSubmitted = if (exportGpuLinearRgbSource) {
                    { GLES30.glFlush() }
                } else {
                    null
                },
            )
            var postprocessedUi = chromaResult.exportedTextureId
            if (exportGpuLinearRgbSource) {
                check(postprocessedUi != 0) {
                    "MGC Sabre VGN color noise/IIR did not export its filtered texture"
                }
                exportedTexture = if (gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16UI) {
                    postprocessedUi.also { postprocessedUi = 0 }
                } else {
                    createTexture(
                        width,
                        height,
                        GLES30.GL_RGBA16F,
                        GLES30.GL_NEAREST,
                    ).also { target ->
                        renderSabreRgb16ToFloat(postprocessedUi, target)
                        GLES30.glDeleteTextures(1, intArrayOf(postprocessedUi), 0)
                        postprocessedUi = 0
                        check(textures.remove(target)) {
                            "Exported Sabre RGBA16F texture is not owned by the processor"
                        }
                        textureSpecs.remove(target)
                    }
                }
            }
            /* IRIS_26587_SHARED_NATIVE_HIGHLIGHT_AUTHORITY
             * Build one restored native Sabre/VGN RGB authority after NORMAL fusion/VGN. True-2x
             * still reconstructs geometry/detail from NORMAL CFA evidence only; this restored native
             * RGB is consumed only at the existing post-reconstruction color/detail-guide boundary.
             * The exact same texture becomes the native 1x output after SR has finished.
             */
            val nativeHighlightAuthority26587 = if (highlightShortAdmitted26587) {
                require(highlightShortTexture26587 != 0 && highlightShortMask26587 != 0)
                createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST).also { restored ->
                    renderSabreShortRestoreRgba16f26587(
                        normalRgb = exportedTexture,
                        shortRgb = highlightShortTexture26587,
                        mask = highlightShortMask26587,
                        exposureRatio = highlightShortExposureRatio26587,
                        output = restored,
                    )
                }
            } else {
                exportedTexture
            }
            if (enableSabreSuperRes) {
                val reconstructionStartNs=System.nanoTime()
                val reconstructionEvidence=true2xFastPhaseSlots?.filterNotNull()?:true2xEvidence
                val evidencePolicy = "dngRequested=$exportNormalStackedDng normalFrames=$normalFrameCount " +
                    "retained=${reconstructionEvidence.size} jpegTop2PerPhase=${true2xFastPhaseSlots!=null} " +
                    "maxEvidence=${if (true2xFastPhaseSlots!=null) TRUE2X_JPEG_MAX_EVIDENCE else reconstructionEvidence.size} " +
                    "shortEvidence=false shortNativeGuide=${highlightShortAdmitted26587} " +
                    "shortGuideFullActive=${highlightShortFullActivePixels26595 ?: -1} " +
                    "shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE"
                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_EVIDENCE_POLICY $evidencePolicy")
                MotionTrace.processingState("IRIS_26576_SR_EVIDENCE", evidencePolicy)
                val rawResult=reconstructTrue2x(
                    frames, images, reconstructionEvidence, nativeHighlightAuthority26587, exportNormalStackedDng,
                )
                require(rawResult.width==superResWidth&&rawResult.height==superResHeight)
                val expectedTrueBytes=rawResult.width.toLong()*rawResult.height*TRUE2X_RGB16F_BYTES_PER_PIXEL
                if(rawResult.backend=="GPU") {
                    require(rawResult.renderRgbPath?.let { File(it).length()==expectedTrueBytes }==true) { "26568 fused true2x render carrier invalid" }
                    require((rawResult.linearRgbPath!=null)==exportNormalStackedDng) { "26568 GPU direct-CFA DNG carrier ownership mismatch" }
                    rawResult.linearRgbPath?.let { require(File(it).length()==expectedTrueBytes) }
                    require(rawResult.nativeVgnGuidePath==null&&rawResult.phaseSupportPath==null) { "26568 GPU path must not serialize guide/phase intermediates" }
                } else {
                    require(rawResult.backend=="CPU"&&rawResult.renderRgbPath==null)
                    require(rawResult.linearRgbPath?.let { File(it).length()==expectedTrueBytes }==true)
                    require(rawResult.nativeVgnGuidePath?.let { File(it).length()==width.toLong()*height*TRUE2X_RGB16F_BYTES_PER_PIXEL }==true)
                    require(rawResult.phaseSupportPath?.let { File(it).length()==rawResult.width.toLong()*rawResult.height }==true)
                }
                /* IRIS_26568_TRUE2X_DNG_PRE_VGN_BOUNDARY
                 * GPU DNG keeps the exact direct-CFA ResolveSabre-equivalent RGBA16F->RGB16F boundary
                 * before the new scalar-detail render. CPU fallback retains 26567's same boundary.
                 */
                true2xResult=rawResult.copy(reconstructionMs=elapsedMs(reconstructionStartNs))
                if (highlightShortAdmitted26587) highlightShortAppliedToTrue2x26587 = true
                val result=checkNotNull(true2xResult)
                val readyDetails = "normalFrames=$normalFrameCount shadowLongExcluded=$shadowLongFrameCount " +
                    "size=${result.width}x${result.height} backend=${result.backend} phaseMean=${result.phaseSupportMean} phaseP10=${result.phaseSupportP10} " +
                    "reconstruction=${result.reconstructionMs}ms dngBoundary=PRE_VGN sabreRgbChromaOwner=true " +
                    "highResLumaOwner=DIRECT_CFA directChromaOwner=false trueDetail26573=temporal-cross-frame " +
                    "directDng=${result.linearRgbPath!=null} fusedRender=${result.renderRgbPath!=null}"
                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_READY $readyDetails")
                MotionTrace.processingState("IRIS_26576_SR_RECONSTRUCTION_SUMMARY", readyDetails)
                cleanupTrue2xEvidence(true2xFastPhaseSlots?.filterNotNull()?:true2xEvidence); true2xEvidence.clear(); true2xFastPhaseSlots?.fill(null)
            }
            /* IRIS_26587_POST_SR_RGBA16F_SHORT_PUBLICATION
             * SR has now completed all NORMAL-only CFA/detail decisions using the restored native
             * color/highlight guide only at its existing guide boundary. Publish that exact same
             * restored RGB as the native 1x carrier, then retire the private SHORT evidence.
             */
            if (highlightShortAdmitted26587) {
                require(nativeHighlightAuthority26587 != exportedTexture)
                GLES30.glDeleteTextures(1, intArrayOf(exportedTexture), 0)
                exportedTexture = nativeHighlightAuthority26587
                check(textures.remove(exportedTexture)) { "26587 restored RGBA16F texture is not owned" }
                textureSpecs.remove(exportedTexture)
                releaseOwnedTexture(highlightShortTexture26587, "26587 native SHORT RGBA16F")
                releaseOwnedTexture(highlightShortMask26587, "26587 whole-RGB SHORT mask")
                highlightShortTexture26587 = 0
                highlightShortMask26587 = 0
                PLog.i(
                    SABRE_TAG,
                    "IRIS_26596_SHORT_RESTORE_RESULT exposureRatio=$highlightShortExposureRatio26587 " +
                        "fullActive=${highlightShortFullActivePixels26595 ?: -1} " +
                        "actualContribution=${(highlightShortFullActivePixels26595 ?: 0) > 0} " +
                        "domain=RGBA16F wholeRgb=true afterTrue2x=true " +
                        "true2xGuide=${enableSabreSuperRes} true2xDetailEvidenceShort=false",
                )
            }
            checkGlError("MGC Sabre Resolve/VGN color noise")
            returned = true
            PLog.i(
                SABRE_TAG,
                "MGC Sabre complete scheduled=${frames.size} merged=$mergedFrameCount output=${width}x$height " +
                    "result=${if (exportedTexture != 0) gpuLinearRgbStorage.name + "_GPU" else "RGB16_CPU"} " +
                    "colorNoiseIir=${chromaResult.chromaSubmissionMs}ms " +
                    "chromaFinal=${chromaResult.finalSubmissionMs}ms " +
                    "total=${elapsedMs(processStartNs)}ms",
            )
            RawStackResult(
                fusedBayerBuffer = cpuOutput,
                width = width,
                height = height,
                isNormalizedSensorData = true,
                blackLevel = FloatArray(4),
                fusedBayerUsesNativeAllocator = cpuOutput != null,
                bufferLayout = RawStackBufferLayout.LINEAR_RGB,
                inputRowStepSamples = width * 3,
                inputColStepSamples = 3,
                gpuLinearRgbSource = exportedTexture.takeIf { it != 0 }?.let { textureId ->
                    GpuLinearRgbSource(
                        textureId = textureId,
                        width = width,
                        height = height,
                        samplesPerPixel = 4,
                        storage = gpuLinearRgbStorage,
                    )
                },
                lensShadingCorrectionApplied = hasLensShading(),
                mergedFrameCount = mergedFrameCount,
                mgcSabreNoiseModelScale = sabreNoiseModelScale,
                mgcReferenceSnr = kernelTuning.referenceSnr,
                mgcDenoiseTuningSnr = kernelTuning.referenceSnr / sqrt(sabreNoiseModelScale),
                mgcSharpenTuningSnr = kernelTuning.referenceSnr,
                mgcSharpenAttenuationScale = sabreResolveParameters.demosaicSharpness,
                highlightShortAdmitted = highlightShortAdmitted26587,
                highlightShortRestoreMaskGenerated = highlightShortMaskGenerated26587,
                highlightShortAppliedToTrue2x = highlightShortAppliedToTrue2x26587,
                highlightShortExposureRatio = highlightShortExposureRatio26587,
                normalStackedDngRaw16 = normalStackedDngRaw16,
                normalStackedDngFrameCount = if (exportNormalStackedDng) normalFrameCount else 0,
                normalStackedDngNoiseProfile = normalStackedDngNoiseProfile,
                normalStackedDngSupportMin = normalStackedDngSupport.minimum,
                normalStackedDngSupportP01 = normalStackedDngSupport.p01,
                normalStackedDngSupportP10 = normalStackedDngSupport.p10,
                normalStackedDngSupportMedian = normalStackedDngSupport.median,
                normalStackedDngSupportMean = normalStackedDngSupport.mean,
                normalStackedDngSupportMax = normalStackedDngSupport.maximum,
                normalStackedDngNoiseEquivalentSupport = normalStackedDngSupport.noiseEquivalent,
                superResDetailPath = null,
                superResLinearRawPath = null,
                superResWidth = 0,
                superResHeight = 0,
                true2xLinearRgbPath = true2xResult?.linearRgbPath,
                true2xRenderRgbPath = true2xResult?.renderRgbPath,
                true2xNativeVgnGuidePath = true2xResult?.nativeVgnGuidePath,
                true2xPhaseSupportPath = true2xResult?.phaseSupportPath,
                true2xWidth = true2xResult?.width ?: 0,
                true2xHeight = true2xResult?.height ?: 0,
                true2xBackend = true2xResult?.backend,
                true2xPhaseSupportMean = true2xResult?.phaseSupportMean ?: 0f,
                true2xPhaseSupportP10 = true2xResult?.phaseSupportP10 ?: 0f,
                true2xReconstructionMs = true2xResult?.reconstructionMs ?: 0L,
            )
        } catch (error: Exception) {
            PLog.e(SABRE_TAG, "MGC Sabre merge failed", error)
            null
        } finally {
            images.forEach { it.close() }
            if (highlightShortTexture26587 != 0) {
                releaseOwnedTexture(highlightShortTexture26587, "26587 failed SHORT RGBA16F")
                highlightShortTexture26587 = 0
            }
            if (highlightShortMask26587 != 0) {
                releaseOwnedTexture(highlightShortMask26587, "26587 failed SHORT mask")
                highlightShortMask26587 = 0
            }
            release()
            GlesGpuScheduler.restoreCurrentThreadPriority(originalThreadPriority, SABRE_TAG)
            LargeDirectBuffer.free(sabreAccumulatedReadback)
            LargeDirectBuffer.free(sabreResolvedRgb)
            cleanupTrue2xEvidence(true2xEvidence)
            if (!returned) {
                runCatching { true2xResult?.linearRgbPath?.let { File(it).delete() } }
                runCatching { true2xResult?.renderRgbPath?.let { File(it).delete() } }
                runCatching { true2xResult?.nativeVgnGuidePath?.takeIf { it.isNotEmpty() }?.let { File(it).delete() } }
                runCatching { true2xResult?.phaseSupportPath?.takeIf { it.isNotEmpty() }?.let { File(it).delete() } }
                runCatching { superResDetailPath?.let { File(it).delete() } }
                runCatching { superResLinearRawPath?.let { File(it).delete() } }
                LargeDirectBuffer.free(cpuOutput)
                LargeDirectBuffer.free(normalStackedDngRaw16)
                if (exportedTexture != 0) {
                    GLES30.glDeleteTextures(1, intArrayOf(exportedTexture), 0)
                }
            }
        }
    }

    private data class SabreNormalDngSupportStats(
        val minimum: Float,
        val p01: Float,
        val p10: Float,
        val median: Float,
        val mean: Float,
        val maximum: Float,
        val noiseEquivalent: Float,
    ) {
        companion object {
            fun identity() = SabreNormalDngSupportStats(1f, 1f, 1f, 1f, 1f, 1f, 1f)
        }
    }

    private fun clearSabreNormalDngAccumulator(accumulator: Int) {
        check(accumulator != 0)
        bindRenderTargets(intArrayOf(accumulator), "clear Sabre normalized16 DNG accumulator")
        GLES30.glViewport(0, 0, width, height)
        GLES30.glClearBufferfv(
            GLES30.GL_COLOR,
            0,
            floatArrayOf(0f, 0f, 0f, 0f),
            0,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    private fun renderSabreNormalDngMerge(
        raw: Int,
        flow: SabreConvertedAlignment,
        covariance: Int,
        weight: Int,
        calibration: FrameCalibration,
        accumulator: Int,
        useFrameWeight: Boolean,
    ) {
        check(exportNormalStackedDng && sabreNormalDngMergeProgram != 0 && accumulator != 0)
        val program = sabreNormalDngMergeProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uRaw", 0, raw)
        bindTexture(program, "uFlow", 1, flow.texture)
        bindTexture(program, "uCovariance", 2, covariance)
        bindTexture(program, "uRejection", 3, weight)
        uniformSabreFlowScaleOffset(program, flow)
        uniform2i(program, "uRawSize", width, height)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniform1i(program, "uCfaPattern", cfaPattern)
        uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        uniform4fv(program, "uPhaseGains", calibration.bayerPhaseGains)
        uniform4fv(program, "uPhaseBlackTerms", calibration.bayerPhaseBlackTerms)
        uniform4f(
            program,
            "uCovRangeRg",
            COV_MIN_R,
            COV_MAX_R - COV_MIN_R,
            COV_MIN_G,
            COV_MAX_G - COV_MIN_G,
        )
        uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                width,
                height,
                intArrayOf(accumulator),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun resolveSabreNormalDngSupportStats(
        accumulatedCoverage: Int,
        coverageWidth: Int,
        coverageHeight: Int,
        accumulatedWeightScale: Float,
        frameCount: Int,
        sabreNoiseModelScale: Float,
    ): SabreNormalDngSupportStats {
        require(exportNormalStackedDng && accumulatedCoverage != 0 && frameCount >= 1)
        val byteCount = Math.multiplyExact(coverageWidth, coverageHeight)
        val readback = ByteBuffer.allocateDirect(byteCount).order(ByteOrder.nativeOrder())
        bindRenderTargets(intArrayOf(accumulatedCoverage), "Sabre DNG temporal support readback")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        GLES30.glReadPixels(
            0, 0, coverageWidth, coverageHeight,
            GLES30.GL_RED, GLES30.GL_UNSIGNED_BYTE, readback,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("Sabre DNG temporal support readback")

        val total = coverageWidth * coverageHeight
        val stride = max(1, total / SABRE_DNG_SUPPORT_MAX_SAMPLES)
        val sampleCount = (total + stride - 1) / stride
        val values = FloatArray(sampleCount)
        var out = 0
        var index = 0
        while (index < total) {
            val encoded = readback.get(index).toInt() and 0xff
            val temporal = encoded / 255f * accumulatedWeightScale
            values[out++] = (1f + temporal).coerceIn(1f, frameCount.toFloat())
            index += stride
        }
        val used = if (out == values.size) values else values.copyOf(out)
        used.sort()
        var sum = 0.0
        var reciprocal = 0.0
        used.forEach { value ->
            sum += value.toDouble()
            reciprocal += 1.0 / value.toDouble()
        }
        fun percentile(fraction: Float): Float {
            val i = ((used.size - 1) * fraction).toInt().coerceIn(0, used.lastIndex)
            return used[i]
        }
        val harmonicCoverage = (used.size.toDouble() / reciprocal).toFloat()
            .coerceIn(1f, frameCount.toFloat())
        val mergeEquivalent = (1f / sabreNoiseModelScale.coerceAtLeast(1.0e-6f))
            .coerceIn(1f, frameCount.toFloat())
        val noiseEquivalent = minOf(harmonicCoverage, mergeEquivalent)
        return SabreNormalDngSupportStats(
            minimum = used.first(),
            p01 = percentile(0.01f),
            p10 = percentile(0.10f),
            median = percentile(0.50f),
            mean = (sum / used.size.toDouble()).toFloat(),
            maximum = used.last(),
            noiseEquivalent = noiseEquivalent,
        )
    }

    private fun createSabreNormalDngNoiseProfile(
        frames: List<RawStackFrame>,
        support: SabreNormalDngSupportStats,
    ): DoubleArray {
        require(frames.isNotEmpty())
        val referenceModel = frames.first().channelNoiseProfile
            ?.let(RawNoiseModel::fromCamera2NoiseProfile)
            ?.takeIf { it.hasValidCamera2Profile }
            ?: noiseModelForFrame(frames.first())
        val shot = referenceModel.normalizedShotNoiseForShader(cfaPattern)
        val read = referenceModel.normalizedReadNoiseForShader(cfaPattern)
        val divisor = support.noiseEquivalent.coerceAtLeast(1f).toDouble()
        fun sane(value: Float): Double =
            value.takeIf { it.isFinite() && it >= 0f }?.toDouble() ?: 0.0
        return doubleArrayOf(
            sane(shot[0]) / divisor,
            sane(read[0]) / divisor,
            0.5 * (sane(shot[1]) + sane(shot[2])) / divisor,
            0.5 * (sane(read[1]) + sane(read[2])) / divisor,
            sane(shot[3]) / divisor,
            sane(read[3]) / divisor,
        ).also { profile ->
            check(profile.all { it.isFinite() && it >= 0.0 }) {
                "26545 Sabre normalized16 DNG noise profile is invalid"
            }
        }
    }

    private fun renderSabreExtract(
        raw: Int,
        output: Int,
        extractedWidth: Int,
        extractedHeight: Int,
    ) {
        GLES30.glUseProgram(sabreExtractBayerProgram)
        bindTexture(sabreExtractBayerProgram, "uRaw", 0, raw)
        uniform2i(sabreExtractBayerProgram, "uRawSize", width, height)
        draw(sabreExtractBayerProgram, extractedWidth, extractedHeight, intArrayOf(output))
    }

    private fun renderSabreGuideAndCovariance(
        extracted: Int,
        noiseTexture: Int,
        calibration: FrameCalibration,
        guide: Int,
        covariance: Int,
        guideWidth: Int,
        guideHeight: Int,
        kernelParameters: MgcSabreKernelTuning.Parameters,
    ) {
        val program = sabreGuideAndCovarianceProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uExtractedBayer", 0, extracted)
        bindTexture(program, "uNoiseEstimates", 1, noiseTexture)
        uniform2i(program, "uGuideSize", guideWidth, guideHeight)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_GUIDE_BORDER_PIXELS / width,
            SABRE_GUIDE_BORDER_PIXELS / height,
            1f - SABRE_GUIDE_BORDER_PIXELS / width,
            1f - SABRE_GUIDE_BORDER_PIXELS / height,
        )
        uniform1i(program, "uCfaPattern", cfaPattern)
        uniform4fv(program, "uGains", calibration.gains)
        uniform4fv(program, "uBlackLevelsTimesGains", calibration.blackTerms)
        uniform4f(program, "uNoiseTextureScaleBias", 0.9f, 0.5f, 0.05f, 0.25f)
        uniform4fv(program, "uCovarianceParameters1", kernelParameters.covarianceParameters1)
        uniform4fv(program, "uCovarianceParameters2", kernelParameters.covarianceParameters2)
        uniform4f(
            program,
            "uCovRangeRgFactors",
            covariancePackOffset(kernelParameters.covarianceMinR, kernelParameters.covarianceMaxR),
            covariancePackScale(kernelParameters.covarianceMinR, kernelParameters.covarianceMaxR),
            covariancePackOffset(kernelParameters.covarianceMinG, kernelParameters.covarianceMaxG),
            covariancePackScale(kernelParameters.covarianceMinG, kernelParameters.covarianceMaxG),
        )
        uniform2f(
            program,
            "uCovRangeBFactor",
            covariancePackOffset(kernelParameters.covarianceMinB, kernelParameters.covarianceMaxB),
            covariancePackScale(kernelParameters.covarianceMinB, kernelParameters.covarianceMaxB),
        )
        /* IRIS_26547_SABRE_SQRT_CLIP_DOMAIN
         * guideAndCovariance applies sqrt() to normalized Bayer values. Transport the clipping
         * threshold through the same monotonic transform so a 4x Long normalized to 0.25 clips
         * at sqrt(0.25)=0.5 in guide space, not at linear 0.25 (which rejected valid data early).
         */
        uniform1f(
            program,
            "uGreenClippingPoint",
            sqrt(calibration.greenClippingPoint.coerceAtLeast(0f)),
        )
        uniform4f(
            program,
            "uForceReferenceColorRgb",
            if (kernelParameters.forceReferenceColorRgb) 1f else 0f,
            0f, 0f, 0f,
        )
        draw(program, guideWidth, guideHeight, intArrayOf(guide, covariance))
    }

    /* IRIS_26547_SABRE_LONG_DURATION_ROBUSTNESS
     * Sabre already subtracts heteroscedastic reference+frame noise before forming its squared
     * residual statistic. For SHADOW_LONG only, scale that statistic by the actual shutter-time
     * ratio. Static, noise-consistent pixels still have near-zero excess residual and are not
     * assigned an arbitrary lower merge weight; disagreement is simply held to a tighter
     * likelihood threshold as intra-frame blur risk rises with integration time. Cap the factor
     * at 4x so an extreme HAL shutter does not turn the Long path into an all-or-nothing gate.
     */
    private fun sabreExposureDurationRobustness(
        reference: RawStackFrame,
        frame: RawStackFrame,
    ): Float {
        if (frame.role != RawBurstFrameRole.SHADOW_LONG) return 1f
        val referenceNs = reference.exposureTimeNs.takeIf { it > 0L } ?: return 1f
        val frameNs = frame.exposureTimeNs.takeIf { it > 0L } ?: return 1f
        val ratio = frameNs.toDouble() / referenceNs.toDouble()
        return ratio.takeIf { it.isFinite() }
            ?.coerceIn(1.0, SABRE_LONG_DURATION_ROBUSTNESS_MAX.toDouble())
            ?.toFloat() ?: 1f
    }

    private fun renderSabreRejection(
        referenceGuide: Int,
        currentGuide: Int,
        flow: SabreConvertedAlignment,
        unblocker: Int,
        noiseTexture: Int,
        reverseWeight: Int,
        pixelDifference: Int,
        guideWidth: Int,
        guideHeight: Int,
        durationRobustness: Float = 1f,
    ) {
        val program = rejectionProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uBaseGuide", 0, referenceGuide)
        bindTexture(program, "uAltGuide", 1, currentGuide)
        bindTexture(program, "uFlow", 2, flow.texture)
        bindTexture(program, "uUnblocker", 3, unblocker)
        bindTexture(program, "uNoiseEstimates", 4, noiseTexture)
        uniform2i(program, "uGuideSize", guideWidth, guideHeight)
        uniform2i(program, "uRejectionSize", guideWidth, guideHeight)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniformSabreFlowScaleOffset(program, flow)
        uniform2f(program, "uUnblockerScale", 1f, 1f)
        uniform4f(program, "uNoiseTextureScaleBias", 0.9f, 0.5f, 0.05f, 0.25f)
        uniform2f(
            program,
            "uColorDifferenceMultiplier",
            MgcSabreRejectionTuning.COLOR_DIFFERENCE_RGB * durationRobustness,
            MgcSabreRejectionTuning.COLOR_DIFFERENCE_GREEN * durationRobustness,
        )
        val flowVariationThresholds =
            MgcSabreRejectionTuning.flowVariationThresholds(ceilDiv(width, 2))
        uniform1f(
            program,
            "uUnblockerReductionThreshold",
            flowVariationThresholds.unblockerReduction,
        )
        uniform1f(
            program,
            "uExtraMotionRobustnessBoost",
            MgcSabreRejectionTuning.EXTRA_MOTION_ROBUSTNESS_BOOST,
        )
        uniform1f(
            program,
            "uMotionRobustnessBoostVarianceThreshold",
            MgcSabreRejectionTuning.MOTION_ROBUSTNESS_VARIANCE_THRESHOLD,
        )
        uniform1f(
            program,
            "uExtraMotionRobustnessMotionThreshold",
            flowVariationThresholds.extraMotionRobustness,
        )
        draw(program, guideWidth, guideHeight, intArrayOf(reverseWeight, pixelDifference))
    }

    private fun renderSabreCoverage(
        weight: Int,
        accumulatedCoverage: Int,
        coverageWidth: Int,
        coverageHeight: Int,
        accumulatedWeightScale: Float,
    ) {
        val program = sabreCopyMaskProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uRejection", 0, weight)
        uniform1f(program, "uAccumulatedWeightScale", accumulatedWeightScale)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                coverageWidth,
                coverageHeight,
                intArrayOf(accumulatedCoverage),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun renderSabreShadowLongCoverage(
        weight: Int,
        extracted: Int,
        flow: SabreConvertedAlignment,
        accumulatedCoverage: Int,
        coverageWidth: Int,
        coverageHeight: Int,
        extractedWidth: Int,
        extractedHeight: Int,
        accumulatedWeightScale: Float,
    ) {
        if (sabreShadowLongCopyMaskProgram == 0) {
            sabreShadowLongCopyMaskProgram = linkProgram(
                GlesMgcRawSabreShaders.copyMaskShadowLong26558,
                "iris_26558_sabre_shadow_long_coverage",
            )
        }
        val program = sabreShadowLongCopyMaskProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uRejection", 0, weight)
        bindTexture(program, "uExtractedBayer", 1, extracted)
        bindTexture(program, "uFlow", 2, flow.texture)
        uniformSabreFlowScaleOffset(program, flow)
        uniform2i(program, "uExtractedSize", extractedWidth, extractedHeight)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniform1f(program, "uAccumulatedWeightScale", accumulatedWeightScale)
        uniform1f(program, "uSourceClippingPoint", sabreShadowLongSourceClippingPoint())
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                coverageWidth,
                coverageHeight,
                intArrayOf(accumulatedCoverage),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    /** Exact bucket mapping used by MGC's Sabre accumulated R8 mask uniform. */
    private fun maxSabreAccumulatedWeight(frameCount: Int): Float = when {
        frameCount < 2 -> 1f
        frameCount < 4 -> 3f
        frameCount < 6 -> 5f
        frameCount < 16 -> 15f
        frameCount < 18 -> 17f
        frameCount < 52 -> 51f
        frameCount < 86 -> 85f
        else -> 255f
    }

    /* IRIS_26558_SABRE_SHADOW_LONG_SOURCE_CLIP_GUARD
     * uExtractedBayer stores unnormalized integer sensor RAW (+1e-4 transport epsilon). Keep the
     * threshold at the actual sensor saturation code rather than a tuned highlight threshold: this
     * build rejects only genuinely lost Long evidence, not merely bright but recoverable samples.
     */
    private fun sabreShadowLongSourceClippingPoint(): Float =
        sensorWhiteLevel.coerceAtLeast(1f) - 0.5f

    private fun renderSabreMerge(
        extracted: Int,
        flow: SabreConvertedAlignment,
        covariance: Int,
        weight: Int,
        calibration: FrameCalibration,
        accumulatedColor: Int,
        accumulatedWeightsGb: Int,
        extractedWidth: Int,
        extractedHeight: Int,
        useFrameWeight: Boolean,
        shadowLongSourceClipGuard: Boolean,
    ) {
        val program = if (shadowLongSourceClipGuard) {
            if (sabreShadowLongMergeProgram == 0) {
                sabreShadowLongMergeProgram = linkProgram(
                    GlesMgcRawSabreShaders.mergeShadowLong26558,
                    "iris_26558_sabre_shadow_long_merge",
                )
            }
            sabreShadowLongMergeProgram
        } else {
            sabreMergeProgram
        }
        GLES30.glUseProgram(program)
        bindTexture(program, "uExtractedBayer", 0, extracted)
        bindTexture(program, "uFlow", 1, flow.texture)
        bindTexture(program, "uCovariance", 2, covariance)
        bindTexture(program, "uRejection", 3, weight)
        uniform2i(program, "uExtractedSize", extractedWidth, extractedHeight)
        uniform2i(program, "uOutputSize", width, height)
        uniformSabreFlowScaleOffset(program, flow)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniform1i(program, "uCfaPattern", cfaPattern)
        uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        if (shadowLongSourceClipGuard) {
            uniform1f(program, "uSourceClippingPoint", sabreShadowLongSourceClippingPoint())
        }
        uniform4fv(program, "uGains", calibration.gains)
        uniform4fv(program, "uBlackLevelsTimesGains", calibration.blackTerms)
        uniform4f(
            program,
            "uCovRangeRg",
            COV_MIN_R,
            COV_MAX_R - COV_MIN_R,
            COV_MIN_G,
            COV_MAX_G - COV_MIN_G,
        )
        uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                width,
                height,
                intArrayOf(accumulatedColor, accumulatedWeightsGb),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun clearSabreSuperResAccumulator(
        accumulator: Int,
        superResWidth: Int,
        superResHeight: Int,
    ) {
        check(accumulator != 0)
        bindRenderTargets(intArrayOf(accumulator), "IRIS 26561 Sabre SR luma/support clear")
        GLES30.glViewport(0, 0, superResWidth, superResHeight)
        GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f, 0f, 0f, 0f), 0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("IRIS 26561 Sabre SR luma/support clear")
    }

    private fun renderSabreSuperResDetailMerge(
        extracted: Int,
        flow: SabreConvertedAlignment,
        covariance: Int,
        weight: Int,
        calibration: FrameCalibration,
        accumulator: Int,
        extractedWidth: Int,
        extractedHeight: Int,
        superResWidth: Int,
        superResHeight: Int,
        useFrameWeight: Boolean,
    ) {
        check(enableSabreSuperRes && sabreSuperResDetailMergeProgram != 0 && accumulator != 0)
        val program = sabreSuperResDetailMergeProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uExtractedBayer", 0, extracted)
        bindTexture(program, "uFlow", 1, flow.texture)
        bindTexture(program, "uCovariance", 2, covariance)
        bindTexture(program, "uRejection", 3, weight)
        uniform2i(program, "uExtractedSize", extractedWidth, extractedHeight)
        uniform2i(program, "uOutputSize", superResWidth, superResHeight)
        uniformSabreFlowScaleOffset(program, flow)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniform1i(program, "uCfaPattern", cfaPattern)
        uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        uniform4fv(program, "uGains", calibration.gains)
        uniform4fv(program, "uBlackLevelsTimesGains", calibration.blackTerms)
        uniform4f(
            program,
            "uCovRangeRg",
            COV_MIN_R,
            COV_MAX_R - COV_MIN_R,
            COV_MIN_G,
            COV_MAX_G - COV_MIN_G,
        )
        uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                superResWidth,
                superResHeight,
                intArrayOf(accumulator),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun streamSabreSuperResDetail(
        accumulator: Int,
        superResWidth: Int,
        superResHeight: Int,
        normalFrameCount: Int,
    ): String {
        check(enableSabreSuperRes && sabreSuperResDetailResolveProgram != 0)
        require((superResWidth and 1) == 0 && (superResHeight and 1) == 0)
        val directory = requireNotNull(sabreSuperResTempDir)
        if (!directory.exists()) check(directory.mkdirs()) {
            "Unable to create 26561 Sabre Super Res temp directory: $directory"
        }
        val detailFile = File.createTempFile("iris26561-sabre-detail-", ".q8", directory)
        val maximumBandHeight = minOf(SABRE_SUPER_RES_DETAIL_BAND_HEIGHT, superResHeight)
        val bandTexture = createTexture(
            superResWidth,
            maximumBandHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        try {
            BufferedOutputStream(FileOutputStream(detailFile), 1024 * 1024).use { output ->
                var bandTop = 0
                while (bandTop < superResHeight) {
                    val bandHeight = minOf(maximumBandHeight, superResHeight - bandTop)
                    GLES30.glUseProgram(sabreSuperResDetailResolveProgram)
                    bindTexture(sabreSuperResDetailResolveProgram, "uAccumulatedDetail", 0, accumulator)
                    uniform2i(
                        sabreSuperResDetailResolveProgram,
                        "uOutputSize",
                        superResWidth,
                        superResHeight,
                    )
                    uniform1i(sabreSuperResDetailResolveProgram, "uBandTop", bandTop)
                    uniform1f(
                        sabreSuperResDetailResolveProgram,
                        "uExpectedNormalFrames",
                        normalFrameCount.coerceAtLeast(1).toFloat(),
                    )
                    draw(
                        sabreSuperResDetailResolveProgram,
                        superResWidth,
                        bandHeight,
                        intArrayOf(bandTexture),
                    )
                    val bytes = readR8Mask(
                        texture = bandTexture,
                        label = "IRIS 26561 Sabre SR detail band $bandTop",
                        maskWidth = superResWidth,
                        maskHeight = bandHeight,
                    )
                    output.write(bytes)
                    bandTop += bandHeight
                    GlesGpuScheduler.yieldToUiRenderer()
                }
            }
            val expectedBytes = superResWidth.toLong() * superResHeight.toLong()
            check(detailFile.length() == expectedBytes) {
                "26561 Sabre SR detail bytes=${detailFile.length()} expected=$expectedBytes"
            }
            return detailFile.absolutePath
        } catch (error: Throwable) {
            runCatching { detailFile.delete() }
            throw error
        }
    }

    private fun streamSabreSuperResLinearRaw(
        nativeRgb: Int,
        accumulator: Int,
        superResWidth: Int,
        superResHeight: Int,
        normalFrameCount: Int,
    ): String {
        check(enableSabreSuperRes && exportNormalStackedDng && sabreSuperResLinearRawProgram != 0)
        require(superResWidth == width * 2 && superResHeight == height * 2)
        val directory = requireNotNull(sabreSuperResTempDir)
        if (!directory.exists()) check(directory.mkdirs()) {
            "Unable to create 26562 Sabre Super Res DNG temp directory: $directory"
        }
        val linearRawFile = File.createTempFile("iris26562-sabre-linear-raw-", ".rgb16", directory)
        val maximumBandHeight = minOf(SABRE_SUPER_RES_LINEAR_RAW_BAND_HEIGHT, superResHeight)
        val bandTexture = createTexture(
            superResWidth,
            maximumBandHeight,
            GLES30.GL_RGBA16UI,
            GLES30.GL_NEAREST,
        )
        val readback = checkNotNull(
            LargeDirectBuffer.allocate(
                superResWidth.toLong() * maximumBandHeight * 4L * Short.SIZE_BYTES,
                "IRIS 26562 Sabre SR LinearRaw readback",
            ),
        ) { "Unable to allocate 26562 Sabre SR LinearRaw readback band" }
        val rgbBand = ByteArray(superResWidth * maximumBandHeight * 3 * Short.SIZE_BYTES)
        try {
            BufferedOutputStream(FileOutputStream(linearRawFile), 1024 * 1024).use { output ->
                var bandTop = 0
                while (bandTop < superResHeight) {
                    val bandHeight = minOf(maximumBandHeight, superResHeight - bandTop)
                    GLES30.glUseProgram(sabreSuperResLinearRawProgram)
                    bindTexture(sabreSuperResLinearRawProgram, "uNativeRgb", 0, nativeRgb)
                    bindTexture(sabreSuperResLinearRawProgram, "uAccumulatedDetail", 1, accumulator)
                    uniform2i(sabreSuperResLinearRawProgram, "uNativeSize", width, height)
                    uniform2i(
                        sabreSuperResLinearRawProgram,
                        "uOutputSize",
                        superResWidth,
                        superResHeight,
                    )
                    uniform1i(sabreSuperResLinearRawProgram, "uBandTop", bandTop)
                    uniform1f(
                        sabreSuperResLinearRawProgram,
                        "uExpectedNormalFrames",
                        normalFrameCount.coerceAtLeast(1).toFloat(),
                    )
                    draw(
                        sabreSuperResLinearRawProgram,
                        superResWidth,
                        bandHeight,
                        intArrayOf(bandTexture),
                    )
                    readback.clear()
                    readback.limit(superResWidth * bandHeight * 4 * Short.SIZE_BYTES)
                    bindRenderTargets(intArrayOf(bandTexture), "IRIS 26562 Sabre SR LinearRaw readback")
                    GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
                    GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
                    GLES30.glReadPixels(
                        0,
                        0,
                        superResWidth,
                        bandHeight,
                        GLES30.GL_RGBA_INTEGER,
                        GLES30.GL_UNSIGNED_SHORT,
                        readback,
                    )
                    GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                    checkGlError("IRIS 26562 Sabre SR LinearRaw band $bandTop")
                    val source = readback.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
                    var destination = 0
                    val pixelCount = superResWidth * bandHeight
                    for (pixel in 0 until pixelCount) {
                        val sourceIndex = pixel * 4
                        for (channel in 0 until 3) {
                            val value = source.get(sourceIndex + channel).toInt() and 0xffff
                            rgbBand[destination++] = (value and 0xff).toByte()
                            rgbBand[destination++] = ((value ushr 8) and 0xff).toByte()
                        }
                    }
                    output.write(rgbBand, 0, destination)
                    bandTop += bandHeight
                    GlesGpuScheduler.yieldToUiRenderer()
                }
            }
            val expectedBytes = superResWidth.toLong() * superResHeight.toLong() * 3L * Short.SIZE_BYTES
            check(linearRawFile.length() == expectedBytes) {
                "26562 Sabre SR LinearRaw bytes=${linearRawFile.length()} expected=$expectedBytes"
            }
            return linearRawFile.absolutePath
        } catch (error: Throwable) {
            runCatching { linearRawFile.delete() }
            throw error
        } finally {
            LargeDirectBuffer.free(readback)
        }
    }

    private fun clearSabreAccumulators(
        accumulatedColor: Int,
        accumulatedWeightsGb: Int,
        accumulatedCoverage: Int,
        coverageWidth: Int,
        coverageHeight: Int,
    ) {
        clearRgbAccumulators(accumulatedColor, accumulatedWeightsGb, width, height)
        clearSabreCoverage(
            accumulatedCoverage,
            coverageWidth,
            coverageHeight,
            "MGC Sabre coverage clear",
        )
    }

    private fun clearSabreCoverage(
        coverage: Int,
        coverageWidth: Int,
        coverageHeight: Int,
        label: String,
    ) {
        check(coverage != 0)
        bindRenderTargets(intArrayOf(coverage), label)
        GLES30.glViewport(0, 0, coverageWidth, coverageHeight)
        GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f, 0f, 0f, 0f), 0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    private fun renderSabreDehomogenize(
        accumulatedColor: Int,
        accumulatedWeightsGb: Int,
        accumulatedCoverage: Int,
        alphaScale: Float,
        alphaBias: Float,
    ) {
        val copiedRWeight = createTexture(width, height, GLES30.GL_R16F, GLES30.GL_NEAREST)
        GLES30.glUseProgram(sabreCopyAlphaProgram)
        bindTexture(sabreCopyAlphaProgram, "uSource", 0, accumulatedColor)
        draw(sabreCopyAlphaProgram, width, height, intArrayOf(copiedRWeight))

        val program = sabreDehomogenizeProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uSourceWeightR", 0, copiedRWeight)
        bindTexture(program, "uSourceWeightGb", 1, accumulatedWeightsGb)
        bindTexture(program, "uSourceAlpha", 2, accumulatedCoverage)
        uniform1f(program, "uAlphaScale", alphaScale)
        uniform1f(program, "uAlphaBias", alphaBias)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFuncSeparate(
                GLES30.GL_ZERO,
                GLES30.GL_SRC_COLOR,
                GLES30.GL_ONE,
                GLES30.GL_ZERO,
            )
            draw(
                program,
                width,
                height,
                intArrayOf(accumulatedColor),
                preserveBlend = true,
            )
        } finally {
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    /**
     * IRIS_26545_SABRE_MEASURED_SUPPORT
     * Reproduce the current Sabre global mean of 256 / accumulated-green-weight-Q8.
     * The value is transported as the merged-noise coefficient scale and therefore reflects
     * the frames Sabre actually trusted, rather than the nominal burst length.
     */
    private fun readSabreAverageMergeFactor(
        accumulatedWeightsGb: Int,
    ): Float {
        val reducedWidth = ceilDiv(width, 4)
        val reducedHeight = ceilDiv(height, 4)
        val reduced = createTexture(
            reducedWidth,
            reducedHeight,
            GLES30.GL_RG16F,
            GLES30.GL_NEAREST,
        )
        try {
            GLES30.glUseProgram(sabreReciprocalGreenWeightProgram)
            bindTexture(
                sabreReciprocalGreenWeightProgram,
                "uAccumulatedWeightsGb",
                0,
                accumulatedWeightsGb,
            )
            uniform2i(sabreReciprocalGreenWeightProgram, "uInputSize", width, height)
            draw(
                sabreReciprocalGreenWeightProgram,
                reducedWidth,
                reducedHeight,
                intArrayOf(reduced),
            )

            val valueCount = Math.multiplyExact(
                Math.multiplyExact(reducedWidth, reducedHeight),
                2,
            )
            val readback = ByteBuffer.allocateDirect(
                Math.multiplyExact(valueCount, Short.SIZE_BYTES),
            ).order(ByteOrder.nativeOrder())
            bindRenderTargets(intArrayOf(reduced), "Iris Sabre reciprocal green-weight readback")
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glReadPixels(
                0,
                0,
                reducedWidth,
                reducedHeight,
                GLES30.GL_RG,
                GLES30.GL_HALF_FLOAT,
                readback,
            )
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            checkGlError("read Iris Sabre reciprocal green weights")

            val values = readback.asShortBuffer()
            var reciprocalSum = 0.0
            var sampleCount = 0.0
            for (index in 0 until reducedWidth * reducedHeight) {
                reciprocalSum += Half.toFloat(values.get(index * 2)).toDouble()
                sampleCount += Half.toFloat(values.get(index * 2 + 1)).toDouble()
            }
            check(
                reciprocalSum.isFinite() && sampleCount.isFinite() &&
                    reciprocalSum > 0.0 && sampleCount > 0.0
            ) {
                "Iris Sabre accumulated green weights produced an invalid merge factor: " +
                    "sum=$reciprocalSum count=$sampleCount"
            }
            return (reciprocalSum / sampleCount).toFloat()
        } finally {
            releaseOwnedTexture(reduced, "Iris Sabre reciprocal green-weight reduction")
        }
    }

    private fun renderSabreOutputTransform(
        resolvedRgbPlanes: IntArray,
        lensShadingTexture: Int,
        finalBlackLevel: FloatArray,
        demosaicWhiteLevel: Float,
        output: Int,
    ) {
        require(resolvedRgbPlanes.size == 3)
        require(finalBlackLevel.size == 3)
        val program = sabreOutputTransformProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uResolvedR", 0, resolvedRgbPlanes[0])
        bindTexture(program, "uResolvedG", 1, resolvedRgbPlanes[1])
        bindTexture(program, "uResolvedB", 2, resolvedRgbPlanes[2])
        bindTexture(program, "uLensShading", 3, lensShadingTexture)
        uniform2i(program, "uOutputSize", width, height)
        uniform1i(program, "uUseLensShading", if (hasLensShading()) 1 else 0)
        uniform3f(
            program,
            "uFinalBlackLevel",
            finalBlackLevel[0],
            finalBlackLevel[1],
            finalBlackLevel[2],
        )
        uniform1f(program, "uDemosaicWhiteLevel", demosaicWhiteLevel)
        uniform1f(program, "uOutputExposureScale", 1f)
        draw(program, width, height, intArrayOf(output))
    }

    private fun positionalBlackLevels26587(calibration: FrameCalibration): FloatArray =
        FloatArray(4) { phase -> calibration.blackLevels[canonicalChannelAtPhase(phase)] }

    private fun resolveSabreShortNativeExposure26587(
        extracted: Int,
        flow: SabreConvertedAlignment,
        covariance: Int,
        calibration: FrameCalibration,
        identityWeight: Int,
        resolveParameters: MgcSabreResolveTuning.Parameters,
    ): Int {
        require(exportGpuLinearRgbSource && gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F)
        val color = createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
        val weightsGb = createTexture(width, height, GLES30.GL_RG16F, GLES30.GL_NEAREST)
        val coverage = createTexture(1, 1, GLES30.GL_R8, GLES30.GL_NEAREST)
        clearSabreAccumulators(color, weightsGb, coverage, 1, 1)
        renderSabreMerge(
            extracted = extracted,
            flow = flow,
            covariance = covariance,
            weight = identityWeight,
            calibration = calibration,
            accumulatedColor = color,
            accumulatedWeightsGb = weightsGb,
            extractedWidth = ceilDiv(width, 2),
            extractedHeight = ceilDiv(height, 2),
            useFrameWeight = false,
            shadowLongSourceClipGuard = false,
        )
        renderSabreDehomogenize(
            accumulatedColor = color,
            accumulatedWeightsGb = weightsGb,
            accumulatedCoverage = coverage,
            alphaScale = 0f,
            alphaBias = 1f,
        )
        val accumulated = readSabreAccumulatedRgba16f(color)
        val resolved = checkNotNull(
            LargeDirectBuffer.allocate(width.toLong() * height * 3L * Short.SIZE_BYTES,
                "26587 native SHORT Resolve RGB16"),
        )
        try {
            val finalBlack = sabreResolveBlackLevel(calibration.blackLevels)
            val demosaicWhite = minOf(
                (sensorWhiteLevel * sabreResolveRawScale).toInt(),
                Short.MAX_VALUE.toInt(),
            ).coerceAtLeast(1)
            val blendRange = SABRE_DEMOSAIC_BLEND_END - SABRE_DEMOSAIC_BLEND_START
            MgcSabreResolver.resolve(
                accumulatedColorRgba16f = accumulated,
                outputRgb16Planar = resolved,
                width = width,
                height = height,
                cfaPattern = cfaPattern,
                finalBlackLevel = finalBlack,
                finalGains = sabreResolveFinalGains,
                demosaicWhiteLevel = demosaicWhite,
                outputWhiteLevel = resolveParameters.outputWhiteLevel,
                demosaicBlendScale = -blendRange,
                demosaicBlendBias = SABRE_DEMOSAIC_BLEND_END / blendRange,
                demosaicSharpnessScale = demosaicWhite * resolveParameters.demosaicSharpness,
            )
            val planes = IntArray(3) { createTexture(width, height, GLES30.GL_R16UI, GLES30.GL_NEAREST) }
            uploadSabreResolvedRgb16Planar(resolved, planes)
            val lensShadingTexture = createLensShadingTexture()
            val fullOutput = MgcSpatialRgbRect(0, 0, width, height)
            val tile = MgcSpatialRgbTile(index = 0, outputCore = fullOutput)
            val chroma = checkNotNull(sabreRgbChromaPostprocessor)
            chroma.beginFullFrame(listOf(tile))
            renderSabreOutputTransform(
                resolvedRgbPlanes = planes,
                lensShadingTexture = lensShadingTexture,
                finalBlackLevel = finalBlack,
                demosaicWhiteLevel = demosaicWhite.toFloat(),
                output = chroma.normalizationTargetTexture(),
            )
            chroma.markBandWritten(tile)
            GlesGpuScheduler.memoryBarrier()
            val chromaResult = chroma.process(
                obtainCpuOutput = { error("26587 SHORT VGN unexpectedly requested CPU output") },
                deferCpuReadback = true,
                onFinalSubmitted = { GLES30.glFlush() },
            )
            var ui = chromaResult.exportedTextureId
            check(ui != 0) { "26587 SHORT VGN did not export RGBA16UI" }
            val output = createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
            renderSabreRgb16ToFloat(ui, output)
            GLES30.glDeleteTextures(1, intArrayOf(ui), 0)
            ui = 0
            return output
        } finally {
            LargeDirectBuffer.free(accumulated)
            LargeDirectBuffer.free(resolved)
        }
    }

    private fun renderSabreShortRegionSeed26595(
        referenceRaw: Int,
        shortRaw: Int,
        flow: SabreConvertedAlignment,
        referenceCalibration: FrameCalibration,
        shortCalibration: FrameCalibration,
        exposureRatio: Float,
        outputSeed: Int,
        outputRegion: Int,
    ) {
        val program = sabreShortRegionSeedProgram26595
        check(program != 0)
        GLES30.glUseProgram(program)
        bindTexture(program, "uReferenceRaw", 0, referenceRaw)
        bindTexture(program, "uShortRaw", 1, shortRaw)
        bindTexture(program, "uFlow", 2, flow.texture)
        uniform2i(program, "uRawSize", width, height)
        uniform2i(program, "uRegionSize", ceilDiv(ceilDiv(width, 2), 2), ceilDiv(ceilDiv(height, 2), 2))
        uniformSabreFlowScaleOffset(program, flow)
        uniform4fv(program, "uReferenceBlackByPhase", positionalBlackLevels26587(referenceCalibration))
        uniform4fv(program, "uShortBlackByPhase", positionalBlackLevels26587(shortCalibration))
        uniform1f(program, "uWhiteLevel", sensorWhiteLevel)
        uniform1f(program, "uExposureRatio", exposureRatio)
        uniform1f(program, "uRegionFloor", 0.70f)
        uniform1f(program, "uBoundaryCeiling", 0.90f)
        uniform1f(program, "uShortHeadroomThreshold", 0.90f)
        // One Bayer period in RAW-pixel space: pure geometry, not Sabre photometric rejection.
        uniform1f(program, "uFlowVariationPixelsThreshold", 2.0f)
        uniform1f(program, "uConsistencyThreshold", 0.05f)
        draw(
            program,
            ceilDiv(ceilDiv(width, 2), 2),
            ceilDiv(ceilDiv(height, 2), 2),
            intArrayOf(outputSeed, outputRegion),
        )
    }

    private fun renderSabreShortRegionPropagate26594(
        seed: Int,
        region: Int,
        current: Int,
        output: Int,
    ) {
        val program = sabreShortRegionPropagateProgram26594
        check(program != 0)
        GLES30.glUseProgram(program)
        bindTexture(program, "uSeed", 0, seed)
        bindTexture(program, "uRegion", 1, region)
        bindTexture(program, "uCurrent", 2, current)
        val regionWidth = ceilDiv(ceilDiv(width, 2), 2)
        val regionHeight = ceilDiv(ceilDiv(height, 2), 2)
        uniform2i(program, "uSize", regionWidth, regionHeight)
        draw(program, regionWidth, regionHeight, intArrayOf(output))
    }

    private fun renderSabreShortRestoreMask26595(
        referenceRaw: Int,
        shortRaw: Int,
        flow: SabreConvertedAlignment,
        regionTrust: Int,
        referenceCalibration: FrameCalibration,
        shortCalibration: FrameCalibration,
        exposureRatio: Float,
        output: Int,
    ) {
        val program = sabreShortRestoreMaskProgram26595
        check(program != 0)
        GLES30.glUseProgram(program)
        bindTexture(program, "uReferenceRaw", 0, referenceRaw)
        bindTexture(program, "uShortRaw", 1, shortRaw)
        bindTexture(program, "uFlow", 2, flow.texture)
        bindTexture(program, "uRegionTrust", 3, regionTrust)
        uniform2i(program, "uRawSize", width, height)
        uniformSabreFlowScaleOffset(program, flow)
        uniform4fv(program, "uReferenceBlackByPhase", positionalBlackLevels26587(referenceCalibration))
        uniform4fv(program, "uShortBlackByPhase", positionalBlackLevels26587(shortCalibration))
        uniform1f(program, "uWhiteLevel", sensorWhiteLevel)
        uniform1f(program, "uExposureRatio", exposureRatio)
        uniform1f(program, "uReferenceNearClipThreshold", 0.98f)
        uniform1f(program, "uShortHeadroomThreshold", 0.90f)
        uniform1f(program, "uFlowVariationPixelsThreshold", 2.0f)
        draw(program, width, height, intArrayOf(output))
    }

    private data class ShortMaskProbe26590(
        val width: Int,
        val height: Int,
        val activePixels: Int,
        val strongPixels: Int,
        val totalPixels: Int,
        val maxConfidence: Float,
        val meanConfidence: Float,
    )

    /* IRIS_26595_FULL_MASK_CONTRIBUTION_PROOF
     * Permanent correctness telemetry: count the exact finalized full-resolution SHORT mask on GPU
     * and read back one uint only. This is the same mask consumed by RGBA16F restore and true-2x
     * native highlight guide; unlike the 64x48 probe it cannot miss thin or sparse active regions.
     */
    private fun countSabreShortRestoreMaskFull26595(mask: Int): Int? {
        val program = sabreShortMaskCountProgram26595
        if (program == 0) return null
        val ids = IntArray(1)
        GLES31.glGenBuffers(1, ids, 0)
        val buffer = ids[0]
        check(buffer != 0) { "26595 SHORT full-mask count glGenBuffers returned 0" }
        buffers += buffer
        var mapped = false
        try {
            val zero = ByteBuffer.allocateDirect(Int.SIZE_BYTES).order(ByteOrder.nativeOrder())
                .apply { putInt(0); rewind() }
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
            GLES31.glBufferData(
                GLES31.GL_SHADER_STORAGE_BUFFER, Int.SIZE_BYTES, zero, GLES31.GL_STREAM_READ,
            )
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, buffer)
            GLES31.glUseProgram(program)
            GLES31.glActiveTexture(GLES31.GL_TEXTURE0)
            GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, mask)
            GLES31.glUniform1i(uniformLocation(program, "uMask"), 0)
            GLES31.glUniform2i(uniformLocation(program, "uSize"), width, height)
            GLES31.glDispatchCompute(
                GlesComputeWorkGroup.imageGroupCount(width),
                GlesComputeWorkGroup.imageGroupCount(height),
                1,
            )
            GLES31.glMemoryBarrier(
                GLES31.GL_SHADER_STORAGE_BARRIER_BIT or GLES31.GL_BUFFER_UPDATE_BARRIER_BIT,
            )
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, 0)
            GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, 0)
            GLES31.glUseProgram(0)
            checkGlError("26595 SHORT full-mask count submit")
            GlesGpuCompletion.awaitSubmittedWork(
                label = "26595 SHORT full-mask count", checkGlError = ::checkGlError,
            )
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
            val bb = GLES31.glMapBufferRange(
                GLES31.GL_SHADER_STORAGE_BUFFER, 0, Int.SIZE_BYTES, GLES31.GL_MAP_READ_BIT,
            ) as? ByteBuffer ?: error("Unable to map 26595 SHORT full-mask count")
            mapped = true
            val active = bb.order(ByteOrder.nativeOrder()).getInt(0)
            check(GLES31.glUnmapBuffer(GLES31.GL_SHADER_STORAGE_BUFFER)) {
                "26595 SHORT full-mask count buffer invalid"
            }
            mapped = false
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, 0)
            check(active in 0..Math.multiplyExact(width, height))
            return active
        } finally {
            if (mapped) {
                GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
                GLES31.glUnmapBuffer(GLES31.GL_SHADER_STORAGE_BUFFER)
            }
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, 0)
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, 0)
            if (buffers.remove(buffer)) GLES31.glDeleteBuffers(1, intArrayOf(buffer), 0)
        }
    }

    private fun probeSabreShortRestoreMask26590(mask: Int): ShortMaskProbe26590 {
        val probeWidth = 64
        val probeHeight = 48
        val probe = createTexture(probeWidth, probeHeight, GLES30.GL_R8, GLES30.GL_NEAREST)
        try {
            val program = sabreShortRestoreMaskProbeProgram26590
            check(program != 0)
            GLES30.glUseProgram(program)
            bindTexture(program, "uMask", 0, mask)
            uniform2i(program, "uProbeSize", probeWidth, probeHeight)
            draw(program, probeWidth, probeHeight, intArrayOf(probe))
            val bytes = readR8Mask(
                probe,
                "26590 SHORT restore mask effect probe",
                maskWidth = probeWidth,
                maskHeight = probeHeight,
            )
            var active = 0
            var strong = 0
            var maximum = 0
            var sum = 0L
            bytes.forEach { raw ->
                val value = raw.toInt() and 0xff
                if (value != 0) active++
                if (value >= 128) strong++
                maximum = maxOf(maximum, value)
                sum += value.toLong()
            }
            val total = bytes.size.coerceAtLeast(1)
            return ShortMaskProbe26590(
                width = probeWidth,
                height = probeHeight,
                activePixels = active,
                strongPixels = strong,
                totalPixels = bytes.size,
                maxConfidence = maximum / 255f,
                meanConfidence = sum.toFloat() / (255f * total.toFloat()),
            )
        } finally {
            releaseOwnedTexture(probe, "26590 SHORT mask effect probe")
        }
    }

    private fun renderSabreShortRestoreRgba16f26587(
        normalRgb: Int,
        shortRgb: Int,
        mask: Int,
        exposureRatio: Float,
        output: Int,
    ) {
        val program = sabreShortRestoreRgba16fProgram26587
        check(program != 0)
        GLES30.glUseProgram(program)
        bindTexture(program, "uNormalRgb", 0, normalRgb)
        bindTexture(program, "uShortRgb", 1, shortRgb)
        bindTexture(program, "uMask", 2, mask)
        uniform1f(program, "uExposureRatio", exposureRatio)
        draw(program, width, height, intArrayOf(output))
    }

    private fun readSabreAccumulatedRgba16f(texture: Int): ByteBuffer {
        val output = checkNotNull(
            LargeDirectBuffer.allocate(
                width.toLong() * height * 4L * Short.SIZE_BYTES,
                "MGC Sabre accumulated RGBA16F",
            ),
        ) { "Unable to allocate MGC Sabre accumulated-color readback" }
        try {
            bindRenderTargets(intArrayOf(texture), "MGC Sabre accumulated-color readback")
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glReadPixels(
                0,
                0,
                width,
                height,
                GLES30.GL_RGBA,
                GLES30.GL_HALF_FLOAT,
                output,
            )
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            checkGlError("read MGC Sabre accumulated RGBA16F")
            output.position(0)
            output.limit(output.capacity())
            return output
        } catch (error: Exception) {
            LargeDirectBuffer.free(output)
            throw error
        }
    }

    private fun uploadSabreResolvedRgb16Planar(buffer: ByteBuffer, textures: IntArray) {
        require(textures.size == 3)
        val planeBytes = Math.multiplyExact(
            Math.multiplyExact(width, height),
            Short.SIZE_BYTES,
        )
        require(buffer.capacity() >= Math.multiplyExact(planeBytes, textures.size))
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
        textures.forEachIndexed { channel, texture ->
            val plane = buffer.duplicate().order(ByteOrder.nativeOrder())
            plane.position(channel * planeBytes)
            plane.limit((channel + 1) * planeBytes)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
            GLES30.glTexSubImage2D(
                GLES30.GL_TEXTURE_2D,
                0,
                0,
                0,
                width,
                height,
                GLES30.GL_RED_INTEGER,
                GLES30.GL_UNSIGNED_SHORT,
                plane,
            )
        }
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("upload MGC Sabre Resolve planar RGB16")
    }

    private fun logSabreResolvedRgbStats(buffer: ByteBuffer) {
        val pixelCount = Math.multiplyExact(width, height)
        val samplesPerPlane = 4096
        val sampleStep = max(1, pixelCount / samplesPerPlane)
        val values = buffer.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val minimum = IntArray(3) { 0xffff }
        val maximum = IntArray(3)
        val sum = LongArray(3)
        val count = IntArray(3)
        for (channel in 0 until 3) {
            val planeOffset = channel * pixelCount
            var pixel = 0
            while (pixel < pixelCount) {
                val value = values.get(planeOffset + pixel).toInt() and 0xffff
                minimum[channel] = minOf(minimum[channel], value)
                maximum[channel] = maxOf(maximum[channel], value)
                sum[channel] += value.toLong()
                count[channel]++
                pixel += sampleStep
            }
        }
        val mean = FloatArray(3) { channel ->
            if (count[channel] > 0) {
                sum[channel].toFloat() / count[channel].toFloat()
            } else {
                0f
            }
        }
        PLog.i(
            SABRE_TAG,
            "MGC Sabre Resolve output samples min=${minimum.contentToString()} " +
                "max=${maximum.contentToString()} mean=${mean.contentToString()} " +
                "step=$sampleStep",
        )
    }

    private fun createSabreRgbChromaPostprocessor(): GlesIris26529SpatialRgbChromaPostprocessor =
        GlesIris26529SpatialRgbChromaPostprocessor(
            imageWidth = width,
            imageHeight = height,
            calculationWbGains = calculationWhiteBalance,
            outputScale = 1f,
            chromaCorrectionStrength = vgnChromaCorrectionStrength,
            host = object : GlesIris26529SpatialRgbChromaPostprocessor.Host {
                override fun linkComputeProgram(source: String, name: String): Int =
                    this@GlesMgcRawSpatialStacker.linkComputeProgram(source, name)

                override fun createRgba16UiTexture(width: Int, height: Int, label: String): Int =
                    createTexture(width, height, GLES30.GL_RGBA16UI, GLES30.GL_NEAREST)

                override fun releaseTexture(texture: Int, label: String) =
                    releaseOwnedTexture(texture, label)

                override fun transferTextureOwnership(texture: Int, label: String) {
                    check(textures.remove(texture)) { "$label texture=$texture is not owned" }
                    textureSpecs.remove(texture)
                }

                override fun uniformLocation(program: Int, name: String): Int =
                    this@GlesMgcRawSpatialStacker.uniformLocation(program, name)

                override fun checkGlError(label: String) =
                    this@GlesMgcRawSpatialStacker.checkGlError(label)

                override fun yieldToUiRenderer() = GlesGpuScheduler.yieldToUiRenderer()
            },
            exportFullSizeTexture = exportGpuLinearRgbSource,
        )

    private fun renderSabreRgb16ToFloat(source: Int, target: Int) {
        check(sabreRgb16ToFloatProgram != 0) {
            "MGC Sabre VGN RGB16-to-float program is not initialized"
        }
        GLES31.glUseProgram(sabreRgb16ToFloatProgram)
        uniform2i(sabreRgb16ToFloatProgram, "uImageSize", width, height)
        GLES31.glBindImageTexture(
            0, source, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16UI,
        )
        GLES31.glBindImageTexture(
            1, target, 0, false, 0, GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA16F,
        )
        GLES31.glDispatchCompute(
            GlesComputeWorkGroup.imageGroupCount(width),
            GlesComputeWorkGroup.imageGroupCount(height),
            1,
        )
        GlesGpuScheduler.memoryBarrier()
        GLES31.glBindImageTexture(0, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16UI)
        GLES31.glBindImageTexture(1, 0, 0, false, 0, GLES31.GL_WRITE_ONLY, GLES30.GL_RGBA16F)
        checkGlError("MGC Sabre VGN RGBA16F handoff")
    }

    private fun readSabreRgb16(texture: Int): ByteBuffer {
        val outputBytes = width.toLong() * height * 3L * Short.SIZE_BYTES
        val output = checkNotNull(
            LargeDirectBuffer.allocate(outputBytes, "MGC Sabre RGB16 output"),
        ) { "Unable to allocate MGC Sabre RGB16 output" }
        val rowsPerBand = minOf(SABRE_READBACK_ROWS, height)
        val readback = checkNotNull(
            LargeDirectBuffer.allocate(
                width.toLong() * rowsPerBand * 4L * Short.SIZE_BYTES,
                "MGC Sabre RGB16 readback band",
            ),
        ) { "Unable to allocate MGC Sabre RGB16 readback band" }
        try {
            bindRenderTargets(intArrayOf(texture), "MGC Sabre RGB16 readback")
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            var y = 0
            while (y < height) {
                val rows = minOf(rowsPerBand, height - y)
                readback.clear()
                readback.limit(width * rows * 4 * Short.SIZE_BYTES)
                GLES30.glReadPixels(
                    0,
                    y,
                    width,
                    rows,
                    GLES30.GL_RGBA_INTEGER,
                    GLES30.GL_UNSIGNED_SHORT,
                    readback,
                )
                val source = readback.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
                for (row in 0 until rows) {
                    for (x in 0 until width) {
                        val sourceIndex = (row * width + x) * 4
                        val destinationIndex = ((y + row) * width + x) * 3 * Short.SIZE_BYTES
                        output.putShort(destinationIndex, source.get(sourceIndex))
                        output.putShort(destinationIndex + Short.SIZE_BYTES, source.get(sourceIndex + 1))
                        output.putShort(destinationIndex + 2 * Short.SIZE_BYTES, source.get(sourceIndex + 2))
                    }
                }
                y += rows
            }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            checkGlError("read MGC Sabre RGB16")
            output.position(0)
            output.limit(output.capacity())
            return output
        } catch (error: Exception) {
            LargeDirectBuffer.free(output)
            throw error
        } finally {
            LargeDirectBuffer.free(readback)
        }
    }

    private fun initSabrePrograms() {
        /* IRIS_26545_V1_2_SABRE_PROGRAM_ISOLATION
         * Sabre-specific reconstruction/resolve programs are initialized here. The few
         * GlesMgcRawSpatialShaders references below are neutral utilities also shared by
         * bjzhou's current Sabre (RAW->gray pyramid/LK, unblocker, dilation and DNG normalize);
         * Spatial guide/chroma-guide/strength/Spatial-RGB merge programs are never initialized.
         */
        sabreConvertAlignmentSparseProgram = linkProgram(
            GlesMgcRawSabreShaders.convertAlignmentSparse,
            "iris_26545_sabre_convert_alignment_sparse",
        )
        sabreExtractBayerProgram = linkProgram(
            GlesMgcRawSabreShaders.extractBayer,
            "mgc_sabre_extract_bayer",
        )
        sabreGuideAndCovarianceProgram = linkProgram(
            GlesMgcRawSabreShaders.guideAndCovariance,
            "mgc_sabre_guide_covariance",
        )
        rawToGrayProgram = linkProgram(GlesMgcRawSpatialShaders.rawToGray, "mgc_sabre_raw_to_gray")
        downsampleProgram = linkProgram(
            GlesMgcRawSpatialShaders.grayDownsample,
            "mgc_sabre_gray_downsample",
        )
        downsample4Program = linkProgram(
            GlesMgcRawSpatialShaders.grayDownsample4,
            "mgc_sabre_gray_downsample_4x",
        )
        alignmentGradientProductsProgram = linkProgram(
            GlesMgcRawSpatialShaders.alignmentGradientProducts,
            "mgc_sabre_alignment_gradient_products",
        )
        upsampleAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.upsampleAlignment,
            "mgc_sabre_upsample_alignment",
        )
        blockLucasKanadeProgram = linkProgram(
            GlesMgcRawSpatialShaders.blockLucasKanade,
            "mgc_sabre_block_lucas_kanade",
        )
        convertAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.convertAlignment,
            "mgc_sabre_convert_alignment",
        )
        unblockerProgram = linkProgram(GlesMgcRawSpatialShaders.unblocker, "mgc_sabre_unblocker")
        rejectionProgram = linkProgram(
            GlesMgcRawSabreShaders.rejection,
            "mgc_sabre_rejection",
        )
        dilationProgram = linkProgram(
            GlesMgcRawSpatialShaders.dilateRejection,
            "mgc_sabre_dilate_rejection",
        )
        sabreMergeProgram = linkProgram(GlesMgcRawSabreShaders.merge, "mgc_sabre_merge")
        sabreShortRegionSeedProgram26595 = linkProgram(
            GlesMgcRawSabreShaders.shortRegionSeed26595,
            "iris_26595_sabre_short_region_seed",
        )
        sabreShortRegionPropagateProgram26594 = linkProgram(
            GlesMgcRawSabreShaders.shortRegionPropagate26594,
            "iris_26594_sabre_short_region_propagate",
        )
        sabreShortRestoreMaskProgram26595 = linkProgram(
            GlesMgcRawSabreShaders.shortRestoreMask26596,
            "iris_26596_sabre_short_restore_mask",
        )
        sabreShortRestoreMaskProbeProgram26590 = linkProgram(
            GlesMgcRawSabreShaders.shortRestoreMaskProbe26590,
            "iris_26590_sabre_short_restore_mask_probe",
        )
        if (supportsComputeReadback) {
            runCatching {
                sabreShortMaskCountProgram26595 = linkComputeProgram(
                    GlesMgcRawSpatialShaders.bentoCountHighlightMask,
                    "iris_26595_sabre_short_full_mask_count",
                )
            }.onFailure { error ->
                sabreShortMaskCountProgram26595 = 0
                PLog.w(SABRE_TAG, "26595 SHORT full-mask GPU count unavailable", error)
            }
        }
        sabreShortRestoreRgba16fProgram26587 = linkProgram(
            GlesMgcRawSabreShaders.shortRestoreRgba16f26587,
            "iris_26587_sabre_short_restore_rgba16f",
        )
        /* IRIS_26564_TRUE_2X_NO_FAKE_SR_OWNER
         * Do not eagerly link the 26561/26562 native-RGB-upscale/detail shaders. The true-2x GPU
         * shaders are linked lazily inside the accelerator attempt so shader/driver failure can
         * fall back to the CPU implementation without failing capture.
         */
        // IRIS_26558: keep Motion/NORMAL on the exact proven merge program. The Long program
        // is linked lazily only when a SHADOW_LONG frame is actually processed.
        if (exportNormalStackedDng) {
            sabreNormalDngMergeProgram = linkProgram(
                GlesMgcRawSabreShaders.normalDngMerge,
                "iris_26545_sabre_normal_dng_merge",
            )
            normalizeBayerProgram = linkProgram(
                GlesMgcRawSpatialShaders.normalizeBayer,
                "iris_26545_sabre_normal_dng_normalize16",
            )
        }
        sabreCopyMaskProgram = linkProgram(
            GlesMgcRawSabreShaders.copyMask,
            "mgc_sabre_copy_mask",
        )
        sabreCopyAlphaProgram = linkProgram(
            GlesMgcRawSabreShaders.copyAlpha,
            "mgc_sabre_copy_alpha",
        )
        sabreReciprocalGreenWeightProgram = linkProgram(
            GlesMgcRawSabreShaders.reciprocalGreenWeight4x4,
            "iris_26545_sabre_reciprocal_green_weight_4x4",
        )
        sabreDehomogenizeProgram = linkProgram(
            GlesMgcRawSabreShaders.dehomogenize,
            "mgc_sabre_dehomogenize",
        )
        sabreOutputTransformProgram = linkProgram(
            GlesMgcRawSabreShaders.outputTransformUint16,
            "mgc_sabre_output_transform_rgba16ui_pre_vgn",
        )
        if (exportGpuLinearRgbSource && gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F) {
            sabreRgb16ToFloatProgram = linkComputeProgram(
                GlesIris26521SpatialRgbShaders.copyRgb16ToFloat,
                "mgc_sabre_vgn_rgb16_to_rgba16f",
            )
        }
        sabreRgbChromaPostprocessor = createSabreRgbChromaPostprocessor().also {
            it.initPrograms()
        }
    }

    private fun initPrograms(
        includeBentoAssessment: Boolean,
        includeReferenceHighlightMask: Boolean = includeBentoAssessment,
    ) {
        guideProgram = linkProgram(GlesMgcRawSpatialShaders.guide, "mgc_spatial_guide")
        if (outputMode == MgcSpatialOutputMode.RGB || mergeMethod == MgcMergeMethod.SABRE) {
            covarianceProgram = linkProgram(
                GlesMgcRawSpatialShaders.covariance,
                "mgc_spatial_rgb_covariance",
            )
            rgbChromaGuideProgram = linkProgram(
                GlesMgcRawSpatialShaders.rgbChromaGuide,
                "mgc_spatial_rgb_chroma_guide",
            )
        }
        rawToGrayProgram = linkProgram(GlesMgcRawSpatialShaders.rawToGray, "mgc_raw_to_gray")
        downsampleProgram = linkProgram(
            GlesMgcRawSpatialShaders.grayDownsample,
            "mgc_gray_downsample",
        )
        downsample4Program = linkProgram(
            GlesMgcRawSpatialShaders.grayDownsample4,
            "mgc_gray_downsample_4x",
        )
        alignmentGradientProductsProgram = linkProgram(
            GlesMgcRawSpatialShaders.alignmentGradientProducts,
            "mgc_alignment_gradient_products",
        )
        upsampleAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.upsampleAlignment,
            "mgc_upsample_alignment",
        )
        blockLucasKanadeProgram = linkProgram(
            GlesMgcRawSpatialShaders.blockLucasKanade,
            "mgc_block_lucas_kanade",
        )
        alignProgram = linkProgram(GlesMgcRawSpatialShaders.alignL1, "mgc_align_l1")
        convertAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.convertAlignment,
            "mgc_convert_alignment",
        )
        convertBayerAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.convertBayerAlignment,
            "mgc_convert_bayer_alignment",
        )
        strengthAlignmentProgram = linkProgram(
            GlesMgcRawSpatialShaders.strengthAlignment,
            "mgc_strength_alignment",
        )
        strengthRejectionProgram = linkProgram(
            GlesMgcRawSpatialShaders.strengthRejection,
            "mgc_strength_rejection",
        )
        unblockerProgram = linkProgram(GlesMgcRawSpatialShaders.unblocker, "mgc_unblocker")
        rejectionProgram = linkProgram(
            GlesMgcRawSpatialShaders.rejection,
            "mgc_spatial_rejection",
        )
        clippedGaussianHorizontalProgram = linkProgram(
            GlesMgcRawSpatialShaders.clippedGaussianHorizontal,
            "mgc_pixel_diff_clipped_gaussian_x",
        )
        clippedGaussianVerticalProgram = linkProgram(
            GlesMgcRawSpatialShaders.clippedGaussianVertical,
            "mgc_pixel_diff_clipped_gaussian_y",
        )
        rejectionFilterDownsampleProgram = linkProgram(
            GlesMgcRawSpatialShaders.rejectionFilterDownsample,
            "mgc_rejection_filter_downsample",
        )
        rejectionFilterProgram = linkProgram(
            GlesMgcRawSpatialShaders.rejectionFilter,
            "mgc_rejection_filter",
        )
        rejectionPostprocessProgram = linkProgram(
            GlesMgcRawSpatialShaders.rejectionPostprocess,
            "mgc_rejection_postprocess",
        )
        dilationProgram = linkProgram(
            GlesMgcRawSpatialShaders.dilateRejection,
            "mgc_rejection_dilation",
        )
        if (includeBentoAssessment) {
            findBlockTilesGatherEdgesProgram = linkProgram(
                GlesMgcRawSpatialShaders.findBlockTilesGatherEdges,
                "mgc_find_block_tiles_gather_edges",
            )
            findBlockTilesFilterIntermediateProgram = linkProgram(
                GlesMgcRawSpatialShaders.findBlockTilesFilterIntermediate,
                "mgc_find_block_tiles_filter_intermediate",
            )
            findBlockTilesOutputProgram = linkProgram(
                GlesMgcRawSpatialShaders.findBlockTilesOutput,
                "mgc_find_block_tiles_output",
            )
            bentoAdjustProgram = linkProgram(
                GlesMgcRawSpatialShaders.bentoAdjustHighlightMask,
                "mgc_bento_adjust_mask",
            )
            if (supportsComputeReadback) {
                runCatching {
                    bentoHighlightCountProgram = linkComputeProgram(
                        GlesMgcRawSpatialShaders.bentoCountHighlightMask,
                        "mgc_bento_count_highlight_mask",
                    )
                }.onFailure { error ->
                    bentoHighlightCountProgram = 0
                    PLog.w(
                        TAG,
                        "MGC Bento GPU highlight count unavailable; using CPU readback",
                        error,
                    )
                }
            }
        }
        if (includeReferenceHighlightMask) {
            bentoHighlightProgram = linkProgram(
                GlesMgcRawSpatialShaders.bentoGenerateHighlightMask,
                "mgc_bento_highlight_mask",
            )
            alignedRawClippingMaskProgram = linkProgram(
                GlesMgcRawSpatialShaders.alignedRawClippingMask,
                "mgc_aligned_raw_clipping_mask",
            )
        }
        mergeBayerProgram = linkProgram(
            GlesMgcRawSpatialShaders.mergeBayer,
            "mgc_spatial_bayer_merge",
        )
        if (mergeMethod == MgcMergeMethod.SABRE) {
            sabreMergeBayerProgram = linkProgram(
                GlesMgcRawSpatialShaders.sabreMergeBayer,
                "mgc_sabre_bayer_merge",
            )
        }
        if (outputMode == MgcSpatialOutputMode.RGB) {
            mergeRgbProgram = linkProgram(
                GlesMgcRawSpatialShaders.mergeRgb,
                "mgc_spatial_rgb_merge",
            )
            normalizeRgbProgram = linkProgram(
                if (exportGpuLinearRgbSource &&
                    gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F
                ) {
                    GlesMgcRawSpatialShaders.normalizeRgbFloat
                } else {
                    GlesMgcRawSpatialShaders.normalizeRgb16
                },
                if (exportGpuLinearRgbSource &&
                    gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F
                ) {
                    "mgc_spatial_rgb16f"
                } else {
                    "mgc_spatial_rgb16ui"
                },
            )
            packRgbFixed16FallbackProgram = linkProgram(
                MgcStrengthReadbackShaders.RGB_FIXED16_FRAGMENT,
                "mgc_spatial_rgb_fixed16_fallback",
            )
        }
        normalizeBayerProgram = linkProgram(
            GlesMgcRawSpatialShaders.normalizeBayer,
            "mgc_spatial_bayer16",
        )
        packBayerFixed16Program = linkProgram(
            GlesMgcRawSpatialShaders.packBayerFixed16,
            "mgc_spatial_bayer_fixed16",
        )
        if (supportsComputeReadback) {
            runCatching {
                strengthFloatPackProgram = linkComputeProgram(
                    MgcStrengthReadbackShaders.FLOAT32,
                    "mgc_strength_pack_float32",
                )
                strengthUnorm8PackProgram = linkComputeProgram(
                    MgcStrengthReadbackShaders.UNORM8,
                    "mgc_strength_pack_unorm8",
                )
                strengthSint16PackProgram = linkComputeProgram(
                    MgcStrengthReadbackShaders.SINT16,
                    "mgc_strength_pack_sint16",
                )
            }.onFailure { error ->
                strengthFloatPackProgram = 0
                strengthUnorm8PackProgram = 0
                strengthSint16PackProgram = 0
                PLog.w(TAG, "MGC strength SSBO pack unavailable; using framebuffer readback", error)
            }
        }
    }

    private fun initBentoMergePrograms() {
        if (bentoRewriteWeightProgram == 0) {
            bentoRewriteWeightProgram = linkProgram(
                GlesMgcRawSpatialShaders.bentoRewriteWeight,
                "mgc_bento_rewrite_weight",
            )
        }
        if (linearKernelMaskProgram == 0) {
            linearKernelMaskProgram = linkProgram(
                GlesMgcRawSpatialShaders.updateLinearKernelMask,
                "mgc_bento_linear_kernel_mask",
            )
        }
    }

    private fun calibrationForFrame(
        frame: RawStackFrame,
        exposureScale: Float,
        kernelTuning: BayerKernelTuning,
    ): FrameCalibration {
        val frameBlackLevel = canonicalBlackLevelForFrame(frame)
        val gains = FloatArray(4)
        val blackTerms = FloatArray(4)
        for (channel in 0 until 4) {
            val range = max(sensorWhiteLevel - frameBlackLevel[channel], 1f)
            gains[channel] =
                calculationWhiteBalance[channel] * exposureScale / range
            blackTerms[channel] = -frameBlackLevel[channel] * gains[channel]
        }
        val bayerPhaseGains = FloatArray(4)
        val bayerPhaseBlackTerms = FloatArray(4)
        for (phase in 0 until 4) {
            val canonicalChannel = canonicalChannelAtPhase(phase)
            val range = max(sensorWhiteLevel - frameBlackLevel[canonicalChannel], 1f)
            bayerPhaseGains[phase] = exposureScale / range
            bayerPhaseBlackTerms[phase] =
                -frameBlackLevel[canonicalChannel] * bayerPhaseGains[phase]
        }

        val frameNoiseModel = noiseModelForFrame(frame)
        val sourceShot = frameNoiseModel.normalizedShotNoiseForShader(cfaPattern)
        val sourceRead = frameNoiseModel.normalizedReadNoiseForShader(cfaPattern)
        val shot = FloatArray(4)
        val read = FloatArray(4)
        val unblockerShot = FloatArray(4)
        val unblockerRead = FloatArray(4)
        for (channel in 0 until 4) {
            val relativeGain = calculationWhiteBalance[channel] * exposureScale
            val normalizedShot = sourceShot[channel]
            val normalizedRead = sourceRead[channel]
            shot[channel] = normalizedShot * relativeGain
            read[channel] = normalizedRead *
                relativeGain * relativeGain
            val sensorRange = max(sensorWhiteLevel - frameBlackLevel[channel], 1f)
            unblockerShot[channel] = normalizedShot * sensorRange
            unblockerRead[channel] = normalizedRead * sensorRange * sensorRange
        }
        val cameraRgbShot = RawNoiseModel
            .bayerNoiseModelToRgb(sourceShot)
            .also { channels ->
                channels.indices.forEach { channel -> channels[channel] *= exposureScale }
            }
        val exposureScaleSquared = exposureScale * exposureScale
        val cameraRgbRead = RawNoiseModel
            .bayerNoiseModelToRgb(sourceRead)
            .also { channels ->
                channels.indices.forEach { channel ->
                    channels[channel] *= exposureScaleSquared
                }
            }
        val greenClip = 0.5f * (
            (sensorWhiteLevel * gains[1] + blackTerms[1]) +
                (sensorWhiteLevel * gains[2] + blackTerms[2])
            )
        val globalFrameWeight = if (processorPipeline == MgcRawProcessorPipeline.SPATIAL) {
            MgcSpatialMergeTuning.maximumMergeWeight(
                baseReadVariance = kernelTuning.referenceShadowReadVariance,
                alternateReadVariance = sourceRead.getOrElse(1) { 0f },
                exposureScale = exposureScale,
            )
        } else {
            SPATIAL_IDENTITY_MULTIPLIER
        }
        val kernelSigma = if (processorPipeline == MgcRawProcessorPipeline.SPATIAL) {
            MgcSpatialMergeTuning.kernelSigma(
                baseSpatialScale = kernelTuning.baseSpatialScale,
                maximumMergeWeight = globalFrameWeight,
            )
        } else {
            SPATIAL_IDENTITY_MULTIPLIER
        }
        return FrameCalibration(
            blackLevels = frameBlackLevel,
            gains = gains,
            blackTerms = blackTerms,
            bayerPhaseGains = bayerPhaseGains,
            bayerPhaseBlackTerms = bayerPhaseBlackTerms,
            globalFrameWeight = globalFrameWeight,
            kernelSigma = kernelSigma,
            shotNoise = shot,
            readNoise = read,
            greenClippingPoint = greenClip.takeIf { it.isFinite() && it > 0f } ?: Float.MAX_VALUE,
            // BuildAlignPyramidForBurst computes the scalar passed to
            // DownsampleRawToGray as frame_gain * 16384 / (white_level + 1).
            // Keeping only frame_gain leaves 10-bit RAW alignment gradients 16x too small,
            // so the generated LK kernel's fixed +1 Hessian regularizer suppresses the
            // finest-level subpixel update and temporal merging loses high-frequency detail.
            alignmentGain = MgcAlignmentInputScale.compute(
                frameGain = exposureScale,
                whiteLevel = sensorWhiteLevel,
            ),
            unblockerShotNoise = unblockerShot,
            unblockerReadNoise = unblockerRead,
            cameraRgbShotNoise = cameraRgbShot,
            cameraRgbReadNoise = cameraRgbRead,
        )
    }

    private fun canonicalBlackLevelForFrame(frame: RawStackFrame): FloatArray {
        val positional = frame.dynamicBlackLevelByCfaPosition
            ?.takeIf { values ->
                values.size >= 4 && (0 until 4).all { index ->
                    val value = values[index]
                    value.isFinite() && value >= 0f && value < sensorWhiteLevel
                }
            }
            ?: return canonicalBlackLevel.copyOf()
        return FloatArray(4).also { canonical ->
            for (phase in 0 until 4) {
                canonical[canonicalChannelAtPhase(phase)] = positional[phase]
            }
        }
    }

    private fun sabreResolveBlackLevel(referenceBlackLevel: FloatArray): FloatArray =
        floatArrayOf(
            referenceBlackLevel[0] * sabreResolveRawScale,
            0.5f * (referenceBlackLevel[1] + referenceBlackLevel[2]) *
                sabreResolveRawScale,
            referenceBlackLevel[3] * sabreResolveRawScale,
        )

    private fun createBayerKernelTuning(
        frame: RawStackFrame,
        image: SafeImage,
        frameCount: Int,
    ): BayerKernelTuning {
        val referenceSignal = estimateReferenceGreenSignal(
            image = image,
            blackLevel = canonicalBlackLevelForFrame(frame),
        )
        val noiseModel = noiseModelForFrame(frame)
        val shotNoise = noiseModel.normalizedShotNoiseForShader(cfaPattern)
        val readNoise = noiseModel.normalizedReadNoiseForShader(cfaPattern)
        val referenceNoiseVariance = noiseVarianceAtSignal(
            signal = referenceSignal,
            shotNoise = shotNoise,
            readNoise = readNoise,
        )
        val referenceSnr = if (referenceNoiseVariance > MIN_NOISE_VARIANCE) {
            referenceSignal / sqrt(referenceNoiseVariance)
        } else {
            0f
        }.takeIf { it.isFinite() }?.coerceAtLeast(0f) ?: 0f
        val baseSpatialScale = MgcSpatialMergeTuning.baseSpatialScale(
            referenceSnr = referenceSnr,
            frameCount = frameCount,
            outputMode = outputMode,
        )
        return BayerKernelTuning(
            referenceSignal = referenceSignal,
            referenceShadowReadVariance = readNoise.getOrElse(1) { 0f },
            referenceSnr = referenceSnr,
            baseSpatialScale = baseSpatialScale,
        )
    }

    private fun estimateReferenceGreenSignal(
        image: SafeImage,
        blackLevel: FloatArray,
    ): Float {
        val plane = image.planes.firstOrNull() ?: return 0f
        if (
            plane.pixelStride != RAW_BYTES_PER_PIXEL ||
            plane.rowStride < width * plane.pixelStride
        ) {
            return 0f
        }
        val buffer = plane.buffer.duplicate().order(ByteOrder.nativeOrder())
        val bufferStart = buffer.position()
        // MeasureMeanSignalLevelNormalized (libgcastartup.so+0x5b047e8) shrinks the valid RAW
        // rectangle to its central 3/4, aligns X to four pixels and Y to two pixels, samples the
        // green phase on the first Bayer row every two columns/eight rows, and averages in the
        // variance-stabilized sqrt domain.
        val cropLeft = (width / 8) and -4
        val cropRight = ((width * 7) / 8) and -4
        val cropTop = (height / 8) and -2
        val cropBottom = ((height * 7) / 8) and -2
        if (cropRight <= cropLeft || cropBottom <= cropTop) return 0f

        val firstRowGreenPhase = when (cfaPattern.mod(4)) {
            0, 3 -> 1 // RGGB/BGGR
            else -> 0 // GRBG/GBRG
        }
        val greenChannel = canonicalChannelAtPhase(firstRowGreenPhase)
        val black = blackLevel[greenChannel]
        val range = sensorWhiteLevel - black
        if (!black.isFinite() || !range.isFinite() || range <= 0f) return 0f

        val histogramShift = run {
            val tail = sensorWhiteLevel.toInt() - SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS
            if (tail < SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS) {
                0
            } else {
                Int.SIZE_BITS - Integer.numberOfLeadingZeros(
                    tail ushr SABRE_SIGNAL_LINEAR_HISTOGRAM_BITS,
                )
            }
        }
        val quantizationWidth = 1 shl histogramShift
        val quantizationHalf = quantizationWidth / 2
        fun histogramBinCenter(raw: Int): Int {
            if (histogramShift == 0 || raw < SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS) return raw
            val bucket = (raw - SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS) shr histogramShift
            return SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS +
                (bucket shl histogramShift) + quantizationHalf
        }

        var sqrtSignalSum = 0.0
        var sampleCount = 0
        var y = cropTop
        while (y < cropBottom) {
            var x = cropLeft + (firstRowGreenPhase and 1)
            while (x < cropRight) {
                val byteOffset = bufferStart + y * plane.rowStride + x * plane.pixelStride
                if (byteOffset >= bufferStart && byteOffset + 1 < buffer.limit()) {
                    val raw = buffer.getShort(byteOffset).toInt() and 0xffff
                    val stabilizedSignal = max(histogramBinCenter(raw) - black, 0f)
                    sqrtSignalSum += sqrt(stabilizedSignal.toDouble())
                    sampleCount += 1
                }
                x += 2
            }
            y += SABRE_SIGNAL_ROW_STEP
        }
        return if (sampleCount > 0) {
            val meanSqrtSignal = sqrtSignalSum / sampleCount.toDouble()
            ((meanSqrtSignal * meanSqrtSignal) / range.toDouble())
                .toFloat()
                .takeIf { it.isFinite() && it >= 0f }
                ?: 0f
        } else {
            0f
        }
    }

    /** Classic Sabre table at libgcastartup.so+0x00bc67dc, consumed by 0x388396c. */
    private fun resolveNoiseModelForFrame(frame: RawStackFrame): ResolvedRawNoiseModel =
        RawNoiseModelResolver.resolve(
            selection = noiseProfileSelection,
            sensitivity = frame.sensitivityIso,
            perFrameCamera2Profile = frame.channelNoiseProfile,
            baseFrameCamera2Model = baseFrameCamera2Model,
        )

    private fun noiseModelForFrame(frame: RawStackFrame): RawNoiseModel =
        resolveNoiseModelForFrame(frame).model

    private fun noiseVarianceAtSignal(
        signal: Float,
        shotNoise: FloatArray,
        readNoise: FloatArray,
    ): Float {
        val greenShot = 0.5f * (
            shotNoise.getOrElse(1) { 0f } +
                shotNoise.getOrElse(2) { shotNoise.getOrElse(1) { 0f } }
            )
        val greenRead = 0.5f * (
            readNoise.getOrElse(1) { 0f } +
                readNoise.getOrElse(2) { readNoise.getOrElse(1) { 0f } }
            )
        return (greenShot * signal.coerceAtLeast(0f) + greenRead)
            .takeIf { it.isFinite() && it >= 0f } ?: 0f
    }

    private fun buildGrayPyramid(
        rawTexture: Int,
        calibration: FrameCalibration,
    ): List<TextureLevel> {
        val levels = ArrayList<TextureLevel>()
        // Raw16ToGrayHalide's finest level is one sample per Bayer quad. Runtime
        // buffers on 4080x3064 are 2040x1532, 1021x767, 256x193 and 65x49.
        val finestWidth = ceilDiv(width, 2)
        val finestHeight = ceilDiv(height, 2)
        val firstTexture = createTexture(
            finestWidth,
            finestHeight,
            GLES30.GL_R16I,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(rawToGrayProgram)
        bindTexture(rawToGrayProgram, "uRaw", 0, rawTexture)
        uniform2i(rawToGrayProgram, "uRawSize", width, height)
        uniform2i(rawToGrayProgram, "uGraySize", finestWidth, finestHeight)
        uniform1i(rawToGrayProgram, "uCfaPattern", cfaPattern)
        uniform4fv(rawToGrayProgram, "uBlackLevels", calibration.blackLevels)
        uniform1f(rawToGrayProgram, "uGain", calibration.alignmentGain)
        draw(rawToGrayProgram, finestWidth, finestHeight, intArrayOf(firstTexture))
        levels += TextureLevel(
            texture = firstTexture,
            width = finestWidth,
            height = finestHeight,
            scaleToBayerQuads = 1f,
        )

        var levelWidth = finestWidth
        var levelHeight = finestHeight
        var scaleToBayerQuads = 1
        for (step in ALIGN_PYRAMID_DOWNSAMPLE_STEPS) {
            check(step == 2 || step == 4)
            scaleToBayerQuads *= step
            // Every downsampled level carries the positive-side support sample used by
            // Halide's clamped interpolation. The finest level itself has no extra sample.
            val nextWidth = ceilDiv(finestWidth, scaleToBayerQuads) + 1
            val nextHeight = ceilDiv(finestHeight, scaleToBayerQuads) + 1
            val nextTexture = createTexture(
                nextWidth,
                nextHeight,
                GLES30.GL_R16I,
                GLES30.GL_NEAREST,
            )
            val program = if (step == 4) downsample4Program else downsampleProgram
            GLES30.glUseProgram(program)
            bindTexture(program, "uInput", 0, levels.last().texture)
            uniform2i(program, "uInputSize", levelWidth, levelHeight)
            draw(program, nextWidth, nextHeight, intArrayOf(nextTexture))
            levelWidth = nextWidth
            levelHeight = nextHeight
            levels += TextureLevel(
                texture = nextTexture,
                width = nextWidth,
                height = nextHeight,
                scaleToBayerQuads = scaleToBayerQuads.toFloat(),
            )
        }
        return levels
    }

    /**
     * Computes the reference-only half of LK once for the burst.
     *
     * Gradient products depend on neither the current frame nor its initial flow. Keeping these
     * small textures alive across temporal frames removes four serial tile reductions per frame
     * without changing LK iterations, accumulation order, or output precision.
     */
    private fun buildReferenceAlignmentProducts(
        reference: List<TextureLevel>,
    ): List<ReferenceAlignmentProducts> {
        check(reference.size == ALIGN_LEVEL_TILE_STRIDES.size)
        val startNs = System.nanoTime()
        return reference.mapIndexed { levelIndex, level ->
            val tileSize = ALIGN_LEVEL_TILE_STRIDES[levelIndex]
            val normalize = levelIndex != 0
            val gridWidth = alignmentGridWidth(level, tileSize)
            val gridHeight = alignmentGridHeight(level, tileSize)
            val products0 = createTexture(
                gridWidth,
                gridHeight,
                GLES30.GL_RGBA32F,
                GLES30.GL_NEAREST,
            )
            val products1 = createTexture(
                gridWidth,
                gridHeight,
                GLES30.GL_R32F,
                GLES30.GL_NEAREST,
            )
            GLES30.glUseProgram(alignmentGradientProductsProgram)
            bindTexture(
                alignmentGradientProductsProgram,
                "uReference",
                0,
                level.texture,
            )
            uniform2i(
                alignmentGradientProductsProgram,
                "uImageSize",
                level.width,
                level.height,
            )
            uniform1i(alignmentGradientProductsProgram, "uTileStride", tileSize)
            uniform1i(alignmentGradientProductsProgram, "uTileSize", tileSize)
            uniform1i(
                alignmentGradientProductsProgram,
                "uNormalize",
                if (normalize) 1 else 0,
            )
            draw(
                alignmentGradientProductsProgram,
                gridWidth,
                gridHeight,
                intArrayOf(products0, products1),
            )
            ReferenceAlignmentProducts(
                referenceTexture = level.texture,
                gridWidth = gridWidth,
                gridHeight = gridHeight,
                tileStride = tileSize,
                tileSize = tileSize,
                normalize = normalize,
                products0 = products0,
                products1 = products1,
            )
        }.also { products ->
            PLog.i(
                TAG,
                "MGC Align reference products cached levels=${products.size} " +
                    "grids=${products.joinToString { "${it.gridWidth}x${it.gridHeight}" }} " +
                    "cpuSubmit=${elapsedMs(startNs)}ms",
            )
        }
    }

    /**
     * BuildAlignPyramidForBurst (0x3883e98), using the options captured at runtime from this
     * MGC build:
     *
     *   [target=256, minTile=8, maxTile=64, finestTile=-1,
     *    finestLkIterations=2, coarserLkIterations=3]
     *   normalizeFinest=false, normalizeCoarser=true, useL1Search=false
     *
     * Runtime Halide entry tracing gives the complete execution geometry for 4080x3064:
     *
     *   65x49 / tile 8 / grid 6x4 / normalize
     *   256x193 / tile 16 / grid 14x10 / normalize
     *   1021x767 / tile 32 / grid 30x22 / normalize
     *   2040x1532 / tile 32 / grid 62x46 / no normalization
     *
     * The first three levels use three LK iterations; the finest uses two. The standalone
     * AlignL1 search is absent, but UpsampleAlignment still selects among three neighboring
     * coarse-flow candidates using target-level L1 residuals before every finer LK level.
     * AlignPyramid::AlignAlt exits after the finest LK pass; its level loop does not run an
     * additional UpsampleAlignment pass to the MergeBayer tile grid. Spatial merge transports
     * the resulting 62x46 flow with ConvertAlignmentHalide instead.
     */
    private fun alignPyramids(
        reference: List<TextureLevel>,
        current: List<TextureLevel>,
        referenceProducts: List<ReferenceAlignmentProducts>,
    ): Alignment {
        check(reference.size == current.size)
        check(reference.size == ALIGN_LEVEL_TILE_STRIDES.size)
        check(referenceProducts.size == reference.size)
        val coarseIndex = reference.lastIndex
        val coarse = reference[coarseIndex]
        var alignment = renderLucasKanadeLevel(
            reference = coarse,
            current = current[coarseIndex],
            initial = null,
            tileStride = ALIGN_LEVEL_TILE_STRIDES[coarseIndex],
            tileSize = ALIGN_LEVEL_TILE_STRIDES[coarseIndex],
            iterations = ALIGN_LK_ITERATIONS_COARSER,
            normalize = true,
            referenceProducts = referenceProducts[coarseIndex],
        )

        val schedule = ArrayList<String>().apply {
            add(
                "${coarse.width}x${coarse.height}:" +
                    "${ALIGN_LEVEL_TILE_STRIDES[coarseIndex]}px," +
                    "LK${ALIGN_LK_ITERATIONS_COARSER},normalize=true"
            )
        }
        for (levelIndex in coarseIndex - 1 downTo 0) {
            val level = reference[levelIndex]
            val coarser = reference[levelIndex + 1]
            val tileSize = ALIGN_LEVEL_TILE_STRIDES[levelIndex]
            val scale =
                coarser.scaleToBayerQuads / level.scaleToBayerQuads
            val finest = levelIndex == 0
            val iterations = if (finest) {
                ALIGN_LK_ITERATIONS_FINEST
            } else {
                ALIGN_LK_ITERATIONS_COARSER
            }
            val normalize = !finest
            val upsampled = renderUpsampledAlignment(
                reference = level,
                current = current[levelIndex],
                initial = alignment,
                targetGridWidth = alignmentGridWidth(level, tileSize),
                targetGridHeight = alignmentGridHeight(level, tileSize),
                targetGridMin = ALIGN_LK_GRID_MIN,
                targetTileStride = tileSize,
                targetTileSize = tileSize,
            )
            alignment = renderLucasKanadeLevel(
                reference = level,
                current = current[levelIndex],
                initial = upsampled,
                tileStride = tileSize,
                tileSize = tileSize,
                iterations = iterations,
                normalize = normalize,
                referenceProducts = referenceProducts[levelIndex],
            )
            schedule +=
                "${level.width}x${level.height}:${tileSize}px," +
                "LK$iterations,normalize=$normalize," +
                "levelScale=$scale"
        }
        PLog.i(
            TAG,
                "MGC AlignPyramid target=$ALIGN_TARGET_FINEST_DIMENSION " +
                "guide=${guideWidth}x$guideHeight final=" +
                "${reference.first().width}x${reference.first().height} " +
                "flowGrid=${alignment.gridWidth}x${alignment.gridHeight} " +
                "flowScale=${alignment.scaleToBayerQuads} useL1=false " +
                "gradientProducts=cached " +
                "upsampleL1=level-transitions-only/3-candidate median=false " +
                "runtimeOptions=256/8/64/-1/2/3/0/1/0 " +
                "schedule=${schedule.joinToString(" -> ")}",
        )
        return alignment
    }

    /**
     * UpsampleAlignmentI16Halide selects a whole coarse-flow candidate rather than blending
     * neighboring motion vectors. This preserves discontinuities at moving-object boundaries.
     *
     * The original runtime has both three- and four-candidate workers. The fourth input is an
     * external geometric candidate; this pipeline has no geometric alignment source, so it uses
     * the original three-candidate contract: the nearest coarse tile by tile-center distance plus
     * the next-nearest tile on each axis, selected by target-level block L1 residual.
     */
    private fun renderUpsampledAlignment(
        reference: TextureLevel,
        current: TextureLevel,
        initial: Alignment,
        targetGridWidth: Int,
        targetGridHeight: Int,
        targetGridMin: Int,
        targetTileStride: Int,
        targetTileSize: Int,
    ): Alignment {
        require(reference.width == current.width && reference.height == current.height)
        require(targetGridWidth > 0 && targetGridHeight > 0)
        require(targetTileStride > 0 && targetTileSize in 1..64)
        val initialScale =
            initial.scaleToBayerQuads / reference.scaleToBayerQuads
        require(initialScale.isFinite() && initialScale > 0f)
        val output = createTexture(
            targetGridWidth,
            targetGridHeight,
            GLES30.GL_RGBA32F,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(upsampleAlignmentProgram)
        bindTexture(upsampleAlignmentProgram, "uReference", 0, reference.texture)
        bindTexture(upsampleAlignmentProgram, "uCurrent", 1, current.texture)
        bindTexture(upsampleAlignmentProgram, "uInitialAlignment", 2, initial.texture)
        uniform2i(
            upsampleAlignmentProgram,
            "uImageSize",
            reference.width,
            reference.height,
        )
        uniform2i(
            upsampleAlignmentProgram,
            "uInitialGridSize",
            initial.gridWidth,
            initial.gridHeight,
        )
        uniform1i(upsampleAlignmentProgram, "uInitialGridMin", initial.gridMin)
        uniform1i(upsampleAlignmentProgram, "uTargetGridMin", targetGridMin)
        uniform1i(upsampleAlignmentProgram, "uInitialTileStride", initial.tileStride)
        uniform1i(upsampleAlignmentProgram, "uTargetTileStride", targetTileStride)
        uniform1i(upsampleAlignmentProgram, "uTargetTileSize", targetTileSize)
        uniform1f(upsampleAlignmentProgram, "uInitialScale", initialScale)
        draw(
            upsampleAlignmentProgram,
            targetGridWidth,
            targetGridHeight,
            intArrayOf(output),
        )
        GlesGpuScheduler.yieldToUiRenderer()
        return Alignment(
            texture = output,
            gridWidth = targetGridWidth,
            gridHeight = targetGridHeight,
            tileStride = targetTileStride,
            scaleToBayerQuads = reference.scaleToBayerQuads,
            gridMin = targetGridMin,
        )
    }

    private fun renderLucasKanadeLevel(
        reference: TextureLevel,
        current: TextureLevel,
        initial: Alignment?,
        tileStride: Int,
        tileSize: Int,
        iterations: Int,
        normalize: Boolean,
        referenceProducts: ReferenceAlignmentProducts,
    ): Alignment {
        check(iterations > 0)
        val gridWidth = alignmentGridWidth(reference, tileStride)
        val gridHeight = alignmentGridHeight(reference, tileStride)
        require(
            initial == null ||
                (
                    initial.gridWidth == gridWidth &&
                        initial.gridHeight == gridHeight &&
                        initial.tileStride == tileStride &&
                        initial.gridMin == ALIGN_LK_GRID_MIN &&
                        initial.scaleToBayerQuads == reference.scaleToBayerQuads
                )
        ) {
            "LK initial flow must already match the target grid"
        }
        check(
            referenceProducts.referenceTexture == reference.texture &&
                referenceProducts.gridWidth == gridWidth &&
                referenceProducts.gridHeight == gridHeight &&
                referenceProducts.tileStride == tileStride &&
                referenceProducts.tileSize == tileSize &&
                referenceProducts.normalize == normalize
        ) {
            "Cached LK reference products do not match the requested pyramid level"
        }

        var input = initial
        repeat(iterations) {
            val output = createTexture(
                gridWidth,
                gridHeight,
                GLES30.GL_RGBA32F,
                GLES30.GL_NEAREST,
            )
            GLES30.glUseProgram(blockLucasKanadeProgram)
            bindTexture(blockLucasKanadeProgram, "uReference", 0, reference.texture)
            bindTexture(blockLucasKanadeProgram, "uCurrent", 1, current.texture)
            bindTexture(
                blockLucasKanadeProgram,
                "uProducts0",
                2,
                referenceProducts.products0,
            )
            bindTexture(
                blockLucasKanadeProgram,
                "uProducts1",
                3,
                referenceProducts.products1,
            )
            val inputTexture = input?.texture ?: createZeroFlowTexture()
            bindTexture(
                blockLucasKanadeProgram,
                "uInitialAlignment",
                4,
                inputTexture,
            )
            uniform2i(
                blockLucasKanadeProgram,
                "uImageSize",
                reference.width,
                reference.height,
            )
            uniform2i(
                blockLucasKanadeProgram,
                "uGridSize",
                gridWidth,
                gridHeight,
            )
            uniform1i(blockLucasKanadeProgram, "uTileStride", tileStride)
            uniform1i(blockLucasKanadeProgram, "uTileSize", tileSize)
            uniform1i(
                blockLucasKanadeProgram,
                "uNormalize",
                if (normalize) 1 else 0,
            )
            uniform1i(
                blockLucasKanadeProgram,
                "uHasInitialAlignment",
                if (input != null) 1 else 0,
            )
            draw(
                blockLucasKanadeProgram,
                gridWidth,
                gridHeight,
                intArrayOf(output),
            )
            GlesGpuScheduler.yieldToUiRenderer()
            input = Alignment(
                texture = output,
                gridWidth = gridWidth,
                gridHeight = gridHeight,
                tileStride = tileStride,
                scaleToBayerQuads = reference.scaleToBayerQuads,
                gridMin = ALIGN_LK_GRID_MIN,
            )
        }
        return checkNotNull(input)
    }

    private fun renderAlignmentLevel(
        reference: TextureLevel,
        current: TextureLevel,
        initial: Alignment?,
        tileStride: Int,
        tileSize: Int,
        searchRadius: Int,
        initialScale: Float,
    ): Alignment {
        val gridWidth = ceilDiv(reference.width, tileStride)
        val gridHeight = ceilDiv(reference.height, tileStride)
        val output = createTexture(
            gridWidth,
            gridHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(alignProgram)
        bindTexture(alignProgram, "uReference", 0, reference.texture)
        bindTexture(alignProgram, "uCurrent", 1, current.texture)
        val initialTexture = initial?.texture ?: createZeroFlowTexture()
        bindTexture(
            alignProgram,
            "uInitialAlignment",
            2,
            initialTexture,
        )
        uniform2i(alignProgram, "uImageSize", reference.width, reference.height)
        uniform2i(alignProgram, "uGridSize", gridWidth, gridHeight)
        uniform2i(
            alignProgram,
            "uInitialGridSize",
            initial?.gridWidth ?: gridWidth,
            initial?.gridHeight ?: gridHeight,
        )
        uniform1i(alignProgram, "uTileStride", tileStride)
        uniform1i(alignProgram, "uTileSize", tileSize)
        uniform1i(alignProgram, "uSearchRadius", searchRadius)
        uniform1f(alignProgram, "uInitialScale", initialScale)
        uniform1i(alignProgram, "uHasInitialAlignment", if (initial != null) 1 else 0)
        draw(alignProgram, gridWidth, gridHeight, intArrayOf(output))
        return Alignment(
            texture = output,
            gridWidth = gridWidth,
            gridHeight = gridHeight,
            tileStride = tileStride,
            scaleToBayerQuads = reference.scaleToBayerQuads,
            gridMin = 0,
        )
    }

    private fun createSabreConvertedAlignment(alignment: Alignment): SabreConvertedAlignment {
        require(alignment.gridWidth > 0 && alignment.gridHeight > 0)
        val strideInBayerQuads = alignment.tileStride.toFloat() * alignment.scaleToBayerQuads
        require(strideInBayerQuads.isFinite() && strideInBayerQuads > 0f)
        val output = createTexture(
            alignment.gridWidth,
            alignment.gridHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_LINEAR,
        )
        GLES30.glUseProgram(sabreConvertAlignmentSparseProgram)
        bindTexture(sabreConvertAlignmentSparseProgram, "uAlignment", 0, alignment.texture)
        uniform2i(
            sabreConvertAlignmentSparseProgram,
            "uGridSize",
            alignment.gridWidth,
            alignment.gridHeight,
        )
        uniform1f(
            sabreConvertAlignmentSparseProgram,
            "uAlignmentScale",
            alignment.scaleToBayerQuads,
        )
        val bayerQuadWidth = ceilDiv(width, 2)
        val bayerQuadHeight = ceilDiv(height, 2)
        uniform2f(
            sabreConvertAlignmentSparseProgram,
            "uFlowNormalizationSize",
            bayerQuadWidth.toFloat(),
            bayerQuadHeight.toFloat(),
        )
        draw(
            sabreConvertAlignmentSparseProgram,
            alignment.gridWidth,
            alignment.gridHeight,
            intArrayOf(output),
        )
        val scaleX = bayerQuadWidth.toFloat() /
            (strideInBayerQuads * alignment.gridWidth.toFloat())
        val scaleY = bayerQuadHeight.toFloat() /
            (strideInBayerQuads * alignment.gridHeight.toFloat())
        val offsetX = -alignment.gridMin.toFloat() / alignment.gridWidth.toFloat()
        val offsetY = -alignment.gridMin.toFloat() / alignment.gridHeight.toFloat()
        check(scaleX.isFinite() && scaleY.isFinite() && offsetX.isFinite() && offsetY.isFinite())
        return SabreConvertedAlignment(output, scaleX, scaleY, offsetX, offsetY)
    }

    private fun uniformSabreFlowScaleOffset(program: Int, flow: SabreConvertedAlignment) {
        uniform4f(
            program,
            "uFlowScaleOffset",
            flow.scaleX, flow.scaleY, flow.offsetX, flow.offsetY,
        )
    }

    private fun renderConvertedAlignment(alignment: Alignment, output: Int) {
        GLES30.glUseProgram(convertAlignmentProgram)
        bindTexture(convertAlignmentProgram, "uAlignment", 0, alignment.texture)
        uniform2i(
            convertAlignmentProgram,
            "uGridSize",
            alignment.gridWidth,
            alignment.gridHeight,
        )
        uniform2i(
            convertAlignmentProgram,
            "uOutputSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform1f(
            convertAlignmentProgram,
            "uTileStride",
            alignment.tileStride * alignment.scaleToBayerQuads,
        )
        uniform1f(
            convertAlignmentProgram,
            "uAlignmentScale",
            alignment.scaleToBayerQuads,
        )
        uniform1f(convertAlignmentProgram, "uOutputToAlignmentScale", 1f)
        uniform1f(convertAlignmentProgram, "uGridMin", alignment.gridMin.toFloat())
        uniform1f(
            convertAlignmentProgram,
            "uInterpolationFlowTolerance",
            SPATIAL_INTERPOLATION_FLOW_TOLERANCE,
        )
        uniform2f(
            convertAlignmentProgram,
            "uFlowNormalizationSize",
            ceilDiv(width, 2).toFloat(),
            ceilDiv(height, 2).toFloat(),
        )
        draw(
            convertAlignmentProgram,
            rejectionWidth,
            rejectionHeight,
            intArrayOf(output),
        )
    }

    private fun renderBayerAlignment(alignment: Alignment, output: Int) {
        require(
            alignment.gridWidth > 0 &&
                alignment.gridHeight > 0 &&
                alignment.tileStride > 0 &&
                alignment.scaleToBayerQuads.isFinite() &&
                alignment.scaleToBayerQuads > 0f
        ) {
            "MergeBayer requires a valid finest-level LK alignment"
        }
        GLES30.glUseProgram(convertBayerAlignmentProgram)
        bindTexture(
            convertBayerAlignmentProgram,
            "uAlignment",
            0,
            alignment.texture,
        )
        uniform2i(
            convertBayerAlignmentProgram,
            "uGridSize",
            alignment.gridWidth,
            alignment.gridHeight,
        )
        uniform1f(
            convertBayerAlignmentProgram,
            "uTileStride",
            alignment.tileStride * alignment.scaleToBayerQuads,
        )
        uniform1f(
            convertBayerAlignmentProgram,
            "uAlignmentScale",
            alignment.scaleToBayerQuads,
        )
        uniform1f(
            convertBayerAlignmentProgram,
            "uGridMin",
            alignment.gridMin.toFloat(),
        )
        uniform1f(
            convertBayerAlignmentProgram,
            "uInterpolationFlowTolerance",
            SPATIAL_INTERPOLATION_FLOW_TOLERANCE,
        )
        uniform1f(
            convertBayerAlignmentProgram,
            "uTargetTileStride",
            (MERGE_BAYER_RAW_TILE_SIZE / 2).toFloat(),
        )
        uniform2f(
            convertBayerAlignmentProgram,
            "uFlowNormalizationSize",
            ceilDiv(width, 2).toFloat(),
            ceilDiv(height, 2).toFloat(),
        )
        draw(
            convertBayerAlignmentProgram,
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            intArrayOf(output),
        )
    }

    private fun renderGuide(
        rawTexture: Int,
        noiseTexture: Int,
        calibration: FrameCalibration,
        guideTexture: Int,
        forceReferenceColorRgb: Float,
    ) {
        GLES30.glUseProgram(guideProgram)
        bindTexture(guideProgram, "uRaw", 0, rawTexture)
        bindTexture(guideProgram, "uNoiseEstimates", 1, noiseTexture)
        uniform2i(guideProgram, "uRawSize", width, height)
        uniform2i(guideProgram, "uGuideSize", guideWidth, guideHeight)
        uniform1i(guideProgram, "uCfaPattern", cfaPattern)
        uniform4fv(guideProgram, "uGains", calibration.gains)
        uniform4fv(
            guideProgram,
            "uBlackLevelsTimesGains",
            calibration.blackTerms,
        )
        uniform4f(guideProgram, "uNoiseTextureScaleBias", 0.9f, 0.5f, 0.05f, 0.25f)
        uniform1f(
            guideProgram,
            "uGreenClippingPoint",
            calibration.greenClippingPoint,
        )
        uniform1f(guideProgram, "uForceReferenceColorRgb", forceReferenceColorRgb)
        draw(
            guideProgram,
            guideWidth,
            guideHeight,
            intArrayOf(guideTexture),
        )
    }

    private fun renderCovariance(
        rawTexture: Int,
        noiseTexture: Int,
        calibration: FrameCalibration,
        outputTexture: Int,
    ) {
        check(
            (outputMode == MgcSpatialOutputMode.RGB || mergeMethod == MgcMergeMethod.SABRE) &&
                covarianceProgram != 0,
        )
        GLES30.glUseProgram(covarianceProgram)
        bindTexture(covarianceProgram, "uRaw", 0, rawTexture)
        bindTexture(covarianceProgram, "uNoiseEstimates", 1, noiseTexture)
        uniform2i(covarianceProgram, "uRawSize", width, height)
        uniform2i(covarianceProgram, "uGuideSize", guideWidth, guideHeight)
        uniform1i(covarianceProgram, "uCfaPattern", cfaPattern)
        uniform4fv(covarianceProgram, "uGains", calibration.gains)
        uniform4fv(
            covarianceProgram,
            "uBlackLevelsTimesGains",
            calibration.blackTerms,
        )
        uniform4f(covarianceProgram, "uNoiseTextureScaleBias", 0.9f, 0.5f, 0.05f, 0.25f)
        uniform4f(
            covarianceProgram,
            "uCovarianceParameters1",
            6f,
            1.3333333333333333f,
            0.001f,
            4f,
        )
        uniform4f(
            covarianceProgram,
            "uCovarianceParameters2",
            1f,
            142.85714285714286f,
            0f,
            0f,
        )
        uniform4f(
            covarianceProgram,
            "uCovRangeRgFactors",
            covariancePackOffset(COV_MIN_R, COV_MAX_R),
            covariancePackScale(COV_MIN_R, COV_MAX_R),
            covariancePackOffset(COV_MIN_G, COV_MAX_G),
            covariancePackScale(COV_MIN_G, COV_MAX_G),
        )
        uniform2f(
            covarianceProgram,
            "uCovRangeBFactor",
            covariancePackOffset(COV_MIN_B, COV_MAX_B),
            covariancePackScale(COV_MIN_B, COV_MAX_B),
        )
        draw(
            covarianceProgram,
            guideWidth,
            guideHeight,
            intArrayOf(outputTexture),
        )
    }

    private fun covariancePackOffset(minimum: Float, maximum: Float): Float =
        -minimum / (maximum - minimum)

    private fun covariancePackScale(minimum: Float, maximum: Float): Float =
        1f / (maximum - minimum)

    private fun renderUnblocker(
        rawTexture: Int,
        calibration: FrameCalibration,
        outputTexture: Int,
        outputWidth: Int,
        outputHeight: Int,
    ) {
        GLES30.glUseProgram(unblockerProgram)
        bindTexture(unblockerProgram, "uRaw", 0, rawTexture)
        uniform2i(unblockerProgram, "uRawSize", width, height)
        uniform2i(unblockerProgram, "uGridSize", outputWidth, outputHeight)
        uniform1i(unblockerProgram, "uCfaPattern", cfaPattern)
        uniform1f(
            unblockerProgram,
            "uBlackLevelGreen",
            0.5f * (calibration.blackLevels[1] + calibration.blackLevels[2]),
        )
        val greenShot = 0.25f * (
            calibration.unblockerShotNoise[1] + calibration.unblockerShotNoise[2]
            )
        val greenRead = 0.25f * (
            calibration.unblockerReadNoise[1] + calibration.unblockerReadNoise[2]
            )
        uniform1f(unblockerProgram, "uNoiseQuadratic", 0f)
        uniform1f(unblockerProgram, "uNoiseScale", greenShot)
        uniform1f(unblockerProgram, "uNoiseOffset", greenRead)
        uniform1f(unblockerProgram, "uOutputScale", UNBLOCKER_OUTPUT_SCALE)
        uniform1f(unblockerProgram, "uOutputOffset", UNBLOCKER_OUTPUT_OFFSET)
        draw(
            unblockerProgram,
            outputWidth,
            outputHeight,
            intArrayOf(outputTexture),
        )
    }

    private fun renderRejection(
        referenceGuide: Int,
        currentGuide: Int,
        flowTexture: Int,
        unblockerTexture: Int,
        noiseTexture: Int,
        reverseWeightTexture: Int,
        pixelDifferenceTexture: Int,
    ) {
        GLES30.glUseProgram(rejectionProgram)
        bindTexture(rejectionProgram, "uBaseGuide", 0, referenceGuide)
        bindTexture(rejectionProgram, "uAltGuide", 1, currentGuide)
        bindTexture(rejectionProgram, "uFlow", 2, flowTexture)
        bindTexture(rejectionProgram, "uUnblocker", 3, unblockerTexture)
        bindTexture(rejectionProgram, "uNoiseEstimates", 4, noiseTexture)
        uniform2i(rejectionProgram, "uGuideSize", guideWidth, guideHeight)
        uniform2i(
            rejectionProgram,
            "uRejectionSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform4f(rejectionProgram, "uFlowScaleOffset", 1f, 1f, 0f, 0f)
        uniform2f(rejectionProgram, "uUnblockerScale", 1f, 1f)
        uniform4f(
            rejectionProgram,
            "uNoiseTextureScaleBias",
            0.9f,
            0.5f,
            0.05f,
            0.25f,
        )
        uniform2f(
            rejectionProgram,
            "uColorDifferenceMultiplier",
            MgcSabreRejectionTuning.COLOR_DIFFERENCE_RGB,
            MgcSabreRejectionTuning.COLOR_DIFFERENCE_GREEN,
        )
        val flowVariationThreshold =
            MgcSabreRejectionTuning.flowVariationThreshold(guideWidth)
        val diagnosticMode = RawStackRuntimeDebug.mgcSpatialDiagnosticMode
        val unblockerReductionThreshold =
            if (
                diagnosticMode == MgcSpatialDiagnosticMode.MAIN_REJECTION_ONLY ||
                diagnosticMode == MgcSpatialDiagnosticMode.DISABLE_UNBLOCKER
            ) {
                Float.MAX_VALUE
            } else {
                flowVariationThreshold
            }
        val motionPriorThreshold =
            if (diagnosticMode == MgcSpatialDiagnosticMode.MAIN_REJECTION_ONLY) {
                Float.MAX_VALUE
            } else {
                flowVariationThreshold
            }
        uniform1f(
            rejectionProgram,
            "uUnblockerReductionThreshold",
            unblockerReductionThreshold,
        )
        uniform1f(
            rejectionProgram,
            "uExtraMotionRobustnessBoost",
            MgcSabreRejectionTuning.EXTRA_MOTION_ROBUSTNESS_BOOST,
        )
        uniform1f(
            rejectionProgram,
            "uMotionRobustnessBoostVarianceThreshold",
            MgcSabreRejectionTuning.MOTION_ROBUSTNESS_VARIANCE_THRESHOLD,
        )
        uniform1f(
            rejectionProgram,
            "uExtraMotionRobustnessMotionThreshold",
            motionPriorThreshold,
        )
        GlesGpuScheduler.yieldToUiRenderer()
        draw(
            rejectionProgram,
            rejectionWidth,
            rejectionHeight,
            intArrayOf(reverseWeightTexture, pixelDifferenceTexture),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderClippedGaussianPixelDifference(
        input: Int,
        horizontal: Int,
        output: Int,
    ) {
        GLES30.glUseProgram(clippedGaussianHorizontalProgram)
        bindTexture(clippedGaussianHorizontalProgram, "uInput", 0, input)
        uniform2i(
            clippedGaussianHorizontalProgram,
            "uSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform1fv(
            clippedGaussianHorizontalProgram,
            "uKernel",
            pixelDifferenceKernel,
        )
        draw(
            clippedGaussianHorizontalProgram,
            rejectionWidth,
            rejectionHeight,
            intArrayOf(horizontal),
        )
        GlesGpuScheduler.yieldToUiRenderer()

        GLES30.glUseProgram(clippedGaussianVerticalProgram)
        bindTexture(clippedGaussianVerticalProgram, "uInput", 0, horizontal)
        uniform2i(
            clippedGaussianVerticalProgram,
            "uSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform1fv(
            clippedGaussianVerticalProgram,
            "uKernel",
            pixelDifferenceKernel,
        )
        draw(
            clippedGaussianVerticalProgram,
            rejectionWidth,
            rejectionHeight,
            intArrayOf(output),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderRejectionFilterDownsample(
        baseLuma: Int,
        rejection: Int,
        downsampledLuma: Int,
        downsampledRejection: Int,
    ) {
        GLES30.glUseProgram(rejectionFilterDownsampleProgram)
        bindTexture(rejectionFilterDownsampleProgram, "uBaseLuma", 0, baseLuma)
        bindTexture(rejectionFilterDownsampleProgram, "uRejection", 1, rejection)
        uniform2i(
            rejectionFilterDownsampleProgram,
            "uInputSize",
            rejectionWidth,
            rejectionHeight,
        )
        draw(
            rejectionFilterDownsampleProgram,
            rejectionFilterWidth,
            rejectionFilterHeight,
            intArrayOf(downsampledLuma, downsampledRejection),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderFilteredRejection(
        downsampledLuma: Int,
        downsampledRejection: Int,
        output: Int,
    ) {
        GLES30.glUseProgram(rejectionFilterProgram)
        bindTexture(rejectionFilterProgram, "uLuma", 0, downsampledLuma)
        bindTexture(rejectionFilterProgram, "uRejection", 1, downsampledRejection)
        uniform2i(
            rejectionFilterProgram,
            "uSize",
            rejectionFilterWidth,
            rejectionFilterHeight,
        )
        uniform1i(rejectionFilterProgram, "uRadius", REJECTION_FILTER_MAX_RADIUS)
        uniform1f(
            rejectionFilterProgram,
            "uSigmaSpatial",
            REJECTION_FILTER_SPATIAL_SIGMA,
        )
        uniform1f(
            rejectionFilterProgram,
            "uColorSigma",
            REJECTION_FILTER_COLOR_SIGMA,
        )
        uniform1f(
            rejectionFilterProgram,
            "uColorSigmaBoost",
            REJECTION_FILTER_COLOR_SIGMA_BOOST,
        )
        uniform1i(rejectionFilterProgram, "uClipRejection", 1)
        draw(
            rejectionFilterProgram,
            rejectionFilterWidth,
            rejectionFilterHeight,
            intArrayOf(output),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderRejectionPostprocess(
        originalRejection: Int,
        filteredRejection: Int,
        pixelDifference: Int,
        output: Int,
    ) {
        GLES30.glUseProgram(rejectionPostprocessProgram)
        bindTexture(
            rejectionPostprocessProgram,
            "uOriginalRejection",
            0,
            originalRejection,
        )
        bindTexture(
            rejectionPostprocessProgram,
            "uFilteredRejection",
            1,
            filteredRejection,
        )
        bindTexture(
            rejectionPostprocessProgram,
            "uPixelDifference",
            2,
            pixelDifference,
        )
        uniform2i(
            rejectionPostprocessProgram,
            "uSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform1f(
            rejectionPostprocessProgram,
            "uPixelDifferenceThreshold",
            PIXEL_DIFFERENCE_THRESHOLD / 255f,
        )
        uniform1f(
            rejectionPostprocessProgram,
            "uClippedThreshold",
            REJECTION_CLIPPED_THRESHOLD / 255f,
        )
        draw(
            rejectionPostprocessProgram,
            rejectionWidth,
            rejectionHeight,
            intArrayOf(output),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderDilation(reverseWeight: Int, outputWeight: Int) {
        GLES30.glUseProgram(dilationProgram)
        bindTexture(dilationProgram, "uRejection", 0, reverseWeight)
        uniform2i(
            dilationProgram,
            "uInputSize",
            rejectionWidth,
            rejectionHeight,
        )
        draw(
            dilationProgram,
            mergeWeightWidth,
            mergeWeightHeight,
            intArrayOf(outputWeight),
        )
        GlesGpuScheduler.yieldToUiRenderer()
    }

    private fun renderLinearKernelMask(
        rejection: Int,
        output: Int,
    ) {
        check(linearKernelMaskProgram != 0) {
            "UpdateLinearKernelMask program is not initialized"
        }
        GLES30.glUseProgram(linearKernelMaskProgram)
        bindTexture(linearKernelMaskProgram, "uRejection", 0, rejection)
        uniform2i(
            linearKernelMaskProgram,
            "uSize",
            mergeWeightWidth,
            mergeWeightHeight,
        )
        draw(
            linearKernelMaskProgram,
            mergeWeightWidth,
            mergeWeightHeight,
            intArrayOf(output),
        )
    }

    private fun prepareTemporalFrame(
        frame: RawStackFrame,
        referenceExposure: Double,
        referenceCalibration: FrameCalibration,
        referenceGuide: Int,
        referenceGrayPyramid: List<TextureLevel>,
        referenceAlignmentProducts: List<ReferenceAlignmentProducts>,
        currentRaw: Int,
        currentGuide: Int,
        currentCovariance: Int,
        kernelTuning: BayerKernelTuning,
    ): PreparedTemporalFrame {
        val totalStartNs = System.nanoTime()
        val exposureScale = (
            referenceExposure / validExposureProduct(frame.exposureProduct)
            ).toFloat().coerceIn(MIN_EXPOSURE_SCALE, MAX_EXPOSURE_SCALE)
        if (frame.role == RawBurstFrameRole.SHADOW_LONG) {
            check(exposureScale < 1f) {
                "Tet ratio expected to normalize bracketed SHADOW_LONG frame and " +
                    "be < 1.0, got $exposureScale"
            }
        }
        val calibration = calibrationForFrame(
            frame = frame,
            exposureScale = exposureScale,
            kernelTuning = kernelTuning,
        )
        val guideStartNs = System.nanoTime()
        val currentNoiseLut = createNoiseLut(referenceCalibration, calibration)
        renderGuide(
            rawTexture = currentRaw,
            noiseTexture = currentNoiseLut,
            calibration = calibration,
            guideTexture = currentGuide,
            forceReferenceColorRgb = 0f,
        )
        if (outputMode == MgcSpatialOutputMode.RGB || mergeMethod == MgcMergeMethod.SABRE) {
            renderCovariance(
                rawTexture = currentRaw,
                noiseTexture = currentNoiseLut,
                calibration = calibration,
                outputTexture = currentCovariance,
            )
            if (mergeMethod == MgcMergeMethod.SABRE) {
                currentMergeCovariance = currentCovariance
            }
        }
        val guideNs = System.nanoTime() - guideStartNs
        val pyramidStartNs = System.nanoTime()
        val currentGrayPyramid = buildGrayPyramid(
            rawTexture = currentRaw,
            calibration = calibration,
        )
        val pyramidNs = System.nanoTime() - pyramidStartNs
        val alignmentStartNs = System.nanoTime()
        val alignment = alignPyramids(
            reference = referenceGrayPyramid,
            current = currentGrayPyramid,
            referenceProducts = referenceAlignmentProducts,
        )
        val alignmentNs = System.nanoTime() - alignmentStartNs
        val flowStartNs = System.nanoTime()
        val flow = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_LINEAR,
        )
        renderConvertedAlignment(alignment, flow)
        val bayerAlignment = createTexture(
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            GLES30.GL_RGBA32F,
            GLES30.GL_NEAREST,
        )
        renderBayerAlignment(alignment, bayerAlignment)
        val flowNs = System.nanoTime() - flowStartNs
        val rejectionStartNs = System.nanoTime()
        val unblockerWidth = ceilDiv(width, UNBLOCKER_FULLRES_TILE_SIZE * 2)
        val unblockerHeight = ceilDiv(height, UNBLOCKER_FULLRES_TILE_SIZE * 2)
        val unblocker = createTexture(
            unblockerWidth,
            unblockerHeight,
            GLES30.GL_R8,
            GLES30.GL_LINEAR,
        )
        renderUnblocker(
            rawTexture = currentRaw,
            calibration = calibration,
            outputTexture = unblocker,
            outputWidth = unblockerWidth,
            outputHeight = unblockerHeight,
        )
        val reverseWeight = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_R8,
            GLES30.GL_LINEAR,
        )
        val pixelDifference = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        val pixelDifferenceHorizontal = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_R32F,
            GLES30.GL_NEAREST,
        )
        val smoothedPixelDifference = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        val downsampledLuma = createTexture(
            rejectionFilterWidth,
            rejectionFilterHeight,
            GLES30.GL_R32F,
            GLES30.GL_NEAREST,
        )
        val downsampledRejection = createTexture(
            rejectionFilterWidth,
            rejectionFilterHeight,
            GLES30.GL_R32F,
            GLES30.GL_NEAREST,
        )
        val filteredRejection = createTexture(
            rejectionFilterWidth,
            rejectionFilterHeight,
            GLES30.GL_R8,
            GLES30.GL_LINEAR,
        )
        val postprocessedRejection = createTexture(
            rejectionWidth,
            rejectionHeight,
            GLES30.GL_R8,
            GLES30.GL_LINEAR,
        )
        val frameWeight = createTexture(
            mergeWeightWidth,
            mergeWeightHeight,
            GLES30.GL_R8,
            GLES30.GL_LINEAR,
        )
        renderRejection(
            referenceGuide = referenceGuide,
            currentGuide = currentGuide,
            flowTexture = flow,
            unblockerTexture = unblocker,
            noiseTexture = currentNoiseLut,
            reverseWeightTexture = reverseWeight,
            pixelDifferenceTexture = pixelDifference,
        )
        renderClippedGaussianPixelDifference(
            input = pixelDifference,
            horizontal = pixelDifferenceHorizontal,
            output = smoothedPixelDifference,
        )
        renderRejectionFilterDownsample(
            baseLuma = referenceGrayPyramid.first().texture,
            rejection = reverseWeight,
            downsampledLuma = downsampledLuma,
            downsampledRejection = downsampledRejection,
        )
        renderFilteredRejection(
            downsampledLuma = downsampledLuma,
            downsampledRejection = downsampledRejection,
            output = filteredRejection,
        )
        renderRejectionPostprocess(
            originalRejection = reverseWeight,
            filteredRejection = filteredRejection,
            pixelDifference = smoothedPixelDifference,
            output = postprocessedRejection,
        )
        renderDilation(postprocessedRejection, frameWeight)
        val rejectionNs = System.nanoTime() - rejectionStartNs
        PLog.i(
            TAG,
            "MGC Spatial temporal cpuSubmit frame=${frame.frameNumber} role=${frame.role} " +
                "guideCov=${guideNs / 1_000_000L}ms " +
                "pyramid=${pyramidNs / 1_000_000L}ms " +
                "align=${alignmentNs / 1_000_000L}ms " +
                "flow=${flowNs / 1_000_000L}ms " +
                "rejection=${rejectionNs / 1_000_000L}ms " +
                "total=${elapsedMs(totalStartNs)}ms",
        )
        return PreparedTemporalFrame(
            calibration = calibration,
            flowTexture = flow,
            bayerAlignmentTexture = bayerAlignment,
            weightTexture = frameWeight,
        )
    }

    /**
     * GLES translation of FindBlockTiles' recovered three-stage contract:
     * GatherEdges (RGBA16) -> FilterIntermediate (R8) -> Output (R8).
     * The mask remains in the 16x16-RAW tile domain used by Bento's component-area gate.
     */
    private fun renderFindBlockTiles(
        baseRaw: Int,
        ultrashortRaw: Int,
        flowTexture: Int,
        baseCalibration: FrameCalibration,
        ultrashortCalibration: FrameCalibration,
    ): Int {
        val gatheredEdges = createTexture(
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(findBlockTilesGatherEdgesProgram)
        bindTexture(findBlockTilesGatherEdgesProgram, "uBaseRaw", 0, baseRaw)
        bindTexture(findBlockTilesGatherEdgesProgram, "uAltRaw", 1, ultrashortRaw)
        bindTexture(findBlockTilesGatherEdgesProgram, "uFlow", 2, flowTexture)
        uniform2i(findBlockTilesGatherEdgesProgram, "uRawSize", width, height)
        uniform2i(
            findBlockTilesGatherEdgesProgram,
            "uBayerSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform2i(
            findBlockTilesGatherEdgesProgram,
            "uTileGridSize",
            bayerAlignmentWidth,
            bayerAlignmentHeight,
        )
        uniform1i(findBlockTilesGatherEdgesProgram, "uCfaPattern", cfaPattern)
        uniform4fv(
            findBlockTilesGatherEdgesProgram,
            "uBasePhaseGains",
            baseCalibration.bayerPhaseGains,
        )
        uniform4fv(
            findBlockTilesGatherEdgesProgram,
            "uBasePhaseBlackTerms",
            baseCalibration.bayerPhaseBlackTerms,
        )
        uniform4fv(
            findBlockTilesGatherEdgesProgram,
            "uAltPhaseGains",
            ultrashortCalibration.bayerPhaseGains,
        )
        uniform4fv(
            findBlockTilesGatherEdgesProgram,
            "uAltPhaseBlackTerms",
            ultrashortCalibration.bayerPhaseBlackTerms,
        )
        draw(
            findBlockTilesGatherEdgesProgram,
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            intArrayOf(gatheredEdges),
        )

        val filtered = createTexture(
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(findBlockTilesFilterIntermediateProgram)
        bindTexture(
            findBlockTilesFilterIntermediateProgram,
            "uGatheredEdges",
            0,
            gatheredEdges,
        )
        uniform2i(
            findBlockTilesFilterIntermediateProgram,
            "uSize",
            bayerAlignmentWidth,
            bayerAlignmentHeight,
        )
        draw(
            findBlockTilesFilterIntermediateProgram,
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            intArrayOf(filtered),
        )

        val output = createTexture(
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(findBlockTilesOutputProgram)
        bindTexture(findBlockTilesOutputProgram, "uFiltered", 0, filtered)
        uniform2i(
            findBlockTilesOutputProgram,
            "uSize",
            bayerAlignmentWidth,
            bayerAlignmentHeight,
        )
        draw(
            findBlockTilesOutputProgram,
            bayerAlignmentWidth,
            bayerAlignmentHeight,
            intArrayOf(output),
        )
        return output
    }

    private fun renderBentoHighlightMask(
        baseFrame: Int,
        outputMask: Int,
    ) {
        GLES30.glUseProgram(bentoHighlightProgram)
        bindTexture(bentoHighlightProgram, "uBaseFrame", 0, baseFrame)
        uniform2i(bentoHighlightProgram, "uSize", guideWidth, guideHeight)
        uniform1f(
            bentoHighlightProgram,
            "uMaxRgbClippingThreshold",
            BENTO_MAX_RGB_CLIPPING / 255f,
        )
        draw(
            bentoHighlightProgram,
            guideWidth,
            guideHeight,
            intArrayOf(outputMask),
        )
    }

    private fun renderAlignedLongFrameClippingMask(
        rawTexture: Int,
        flowTexture: Int,
        calibration: FrameCalibration,
    ): Int {
        check(alignedRawClippingMaskProgram != 0) {
            "Aligned RAW clipping-mask program is not initialized"
        }
        val output = createTexture(
            mergeWeightWidth,
            mergeWeightHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        val phaseClippingLevels = FloatArray(4) { phase ->
            val blackLevel = calibration.blackLevels[canonicalChannelAtPhase(phase)]
            blackLevel +
                (sensorWhiteLevel - blackLevel) * LONG_FRAME_RAW_CLIPPING_THRESHOLD
        }
        GLES30.glUseProgram(alignedRawClippingMaskProgram)
        bindTexture(alignedRawClippingMaskProgram, "uRaw", 0, rawTexture)
        bindTexture(alignedRawClippingMaskProgram, "uFlow", 1, flowTexture)
        uniform2i(alignedRawClippingMaskProgram, "uRawSize", width, height)
        uniform2i(
            alignedRawClippingMaskProgram,
            "uBayerSize",
            rejectionWidth,
            rejectionHeight,
        )
        uniform2i(
            alignedRawClippingMaskProgram,
            "uOutputSize",
            mergeWeightWidth,
            mergeWeightHeight,
        )
        uniform4fv(
            alignedRawClippingMaskProgram,
            "uPhaseClippingLevels",
            phaseClippingLevels,
        )
        draw(
            alignedRawClippingMaskProgram,
            mergeWeightWidth,
            mergeWeightHeight,
            intArrayOf(output),
        )
        return output
    }

    private fun renderBentoAdjustedMask(
        baseFrame: Int,
        ultrashortFrame: Int,
        highlightMask: Int,
        flowTexture: Int,
        exposureRatio: Float,
        adjustedMask: Int,
        inpaintingMask: Int,
        ultrashortClippingMask: Int,
    ) {
        GLES30.glUseProgram(bentoAdjustProgram)
        bindTexture(bentoAdjustProgram, "uBaseFrame", 0, baseFrame)
        bindTexture(bentoAdjustProgram, "uUltrashortFrame", 1, ultrashortFrame)
        bindTexture(bentoAdjustProgram, "uHighlightMask", 2, highlightMask)
        bindTexture(bentoAdjustProgram, "uFlow", 3, flowTexture)
        uniform2i(bentoAdjustProgram, "uSize", guideWidth, guideHeight)
        uniform1f(bentoAdjustProgram, "uExposureRatio", exposureRatio)
        uniform1f(
            bentoAdjustProgram,
            "uMinNormalizedIntensityError",
            BENTO_MIN_NORMALIZED_INTENSITY_ERROR,
        )
        uniform1f(
            bentoAdjustProgram,
            "uMaxRgbClippingThreshold",
            BENTO_MAX_RGB_CLIPPING / 255f,
        )
        uniform1f(
            bentoAdjustProgram,
            "uMinRgbForInpainting",
            BENTO_MIN_RGB_FOR_INPAINTING / 255f,
        )
        draw(
            bentoAdjustProgram,
            guideWidth,
            guideHeight,
            intArrayOf(
                adjustedMask,
                inpaintingMask,
                ultrashortClippingMask,
            ),
        )
    }

    private fun renderBentoRewrittenWeight(
        existingWeight: Int,
        bentoMask: Int,
        outputWeight: Int,
        hasExistingWeight: Boolean,
    ) {
        GLES30.glUseProgram(bentoRewriteWeightProgram)
        bindTexture(bentoRewriteWeightProgram, "uExistingWeight", 0, existingWeight)
        bindTexture(bentoRewriteWeightProgram, "uBentoMask", 1, bentoMask)
        uniform2i(
            bentoRewriteWeightProgram,
            "uSize",
            mergeWeightWidth,
            mergeWeightHeight,
        )
        uniform1i(
            bentoRewriteWeightProgram,
            "uHasExistingWeight",
            if (hasExistingWeight) 1 else 0,
        )
        draw(
            bentoRewriteWeightProgram,
            mergeWeightWidth,
            mergeWeightHeight,
            intArrayOf(outputWeight),
        )
    }

    private fun readR8Mask(
        texture: Int,
        label: String,
        maskWidth: Int = guideWidth,
        maskHeight: Int = guideHeight,
    ): ByteArray {
        val totalStartNs = System.nanoTime()
        val byteCount = maskWidth.toLong() * maskHeight.toLong()
        require(byteCount <= Int.MAX_VALUE) { "$label is too large: $byteCount" }
        val buffer = ByteBuffer.allocateDirect(byteCount.toInt())
        val bindStartNs = System.nanoTime()
        bindRenderTargets(intArrayOf(texture), label)
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        val bindNs = System.nanoTime() - bindStartNs
        val readStartNs = System.nanoTime()
        GLES30.glReadPixels(
            0,
            0,
            maskWidth,
            maskHeight,
            GLES30.GL_RED,
            GLES30.GL_UNSIGNED_BYTE,
            buffer,
        )
        val readCallNs = System.nanoTime() - readStartNs
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError(label)
        buffer.rewind()
        val copyStartNs = System.nanoTime()
        return ByteArray(byteCount.toInt()).also { output ->
            buffer.get(output)
            PLog.i(
                TAG,
                "MGC R8 readback label=$label size=${maskWidth}x$maskHeight " +
                    "bytes=$byteCount bind=${bindNs / 1_000_000L}ms " +
                    "readCall=${readCallNs / 1_000_000L}ms " +
                    "cpuCopy=${elapsedMs(copyStartNs)}ms total=${elapsedMs(totalStartNs)}ms",
            )
        }
    }

    /**
     * Reduces an R8 mask to one exact active-pixel count on GLES 3.1+.
     *
     * The source texture stays on the GPU and each 8x8 work group contributes one atomic add to a
     * four-byte SSBO. The CPU synchronization is required by Bento admission either way, but this
     * avoids both the full 786 KiB transfer and the background-priority Kotlin scan.
     */
    private fun countActiveMaskPixelsGpu(
        texture: Int,
        label: String,
    ): ActiveMaskGpuCount {
        check(bentoHighlightCountProgram != 0) {
            "$label compute program is unavailable"
        }
        val setupStartNs = System.nanoTime()
        val ids = IntArray(1)
        GLES31.glGenBuffers(1, ids, 0)
        val buffer = ids[0]
        check(buffer != 0) { "$label glGenBuffers returned 0" }
        buffers += buffer
        var bufferMapped = false
        try {
            val zero = ByteBuffer.allocateDirect(Int.SIZE_BYTES)
                .order(ByteOrder.nativeOrder())
                .apply {
                    putInt(0)
                    rewind()
                }
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
            GLES31.glBufferData(
                GLES31.GL_SHADER_STORAGE_BUFFER,
                Int.SIZE_BYTES,
                zero,
                GLES31.GL_STREAM_READ,
            )
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, buffer)
            GLES31.glUseProgram(bentoHighlightCountProgram)
            GLES31.glActiveTexture(GLES31.GL_TEXTURE0)
            GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, texture)
            GLES31.glUniform1i(
                uniformLocation(bentoHighlightCountProgram, "uMask"),
                0,
            )
            GLES31.glUniform2i(
                uniformLocation(bentoHighlightCountProgram, "uSize"),
                guideWidth,
                guideHeight,
            )
            val setupNs = System.nanoTime() - setupStartNs
            val submitStartNs = System.nanoTime()
            GLES31.glDispatchCompute(
                GlesComputeWorkGroup.imageGroupCount(guideWidth),
                GlesComputeWorkGroup.imageGroupCount(guideHeight),
                1,
            )
            GLES31.glMemoryBarrier(
                GLES31.GL_SHADER_STORAGE_BARRIER_BIT or
                    GLES31.GL_BUFFER_UPDATE_BARRIER_BIT,
            )
            val submitNs = System.nanoTime() - submitStartNs
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, 0)
            GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, 0)
            GLES31.glUseProgram(0)
            checkGlError("submit $label GPU count")

            val gpuWaitMs = GlesGpuCompletion.awaitSubmittedWork(
                label = "$label GPU count",
                checkGlError = ::checkGlError,
            )
            val mapStartNs = System.nanoTime()
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
            val mapped = GLES31.glMapBufferRange(
                GLES31.GL_SHADER_STORAGE_BUFFER,
                0,
                Int.SIZE_BYTES,
                GLES31.GL_MAP_READ_BIT,
            ) as? ByteBuffer ?: error("Unable to map $label GPU count")
            bufferMapped = true
            val activePixels = mapped.order(ByteOrder.nativeOrder()).getInt(0)
            check(GLES31.glUnmapBuffer(GLES31.GL_SHADER_STORAGE_BUFFER)) {
                "$label GPU count buffer contents became invalid"
            }
            bufferMapped = false
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, 0)
            val mapNs = System.nanoTime() - mapStartNs
            check(activePixels in 0..guideWidth * guideHeight) {
                "$label GPU count is out of range: $activePixels"
            }
            checkGlError("read $label GPU count")
            return ActiveMaskGpuCount(
                activePixels = activePixels,
                setupNs = setupNs,
                submitNs = submitNs,
                gpuWaitMs = gpuWaitMs,
                mapNs = mapNs,
            )
        } finally {
            if (bufferMapped) {
                GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, buffer)
                GLES31.glUnmapBuffer(GLES31.GL_SHADER_STORAGE_BUFFER)
            }
            GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, 0)
            GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER, 0)
            if (buffers.remove(buffer)) {
                GLES31.glDeleteBuffers(1, intArrayOf(buffer), 0)
            }
        }
    }

    private fun createStrengthCapture(
        frameCount: Int,
        referenceCalibration: FrameCalibration,
    ): StrengthCapture {
        val geometry = mgcSpatialDiagnosticGeometry(
            outputMode = outputMode,
            imageWidth = if (outputMode == MgcSpatialOutputMode.RGB) outputWidth else width,
            imageHeight = if (outputMode == MgcSpatialOutputMode.RGB) outputHeight else height,
        )
        if (outputMode == MgcSpatialOutputMode.RGB) {
            check(packRgbFixed16FallbackProgram != 0) {
                "MGC Spatial RGB diagnostic pack program is unavailable"
            }
        }
        require(frameCount > 1)
        val maximumTextureSize = IntArray(1)
        GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE, maximumTextureSize, 0)
        val alignmentLayout = createMgcSpatialStrengthAtlasLayout(
            planeWidth = geometry.alignmentWidth,
            planeHeight = geometry.alignmentHeight,
            planeCount = frameCount * 2,
            maximumTextureSize = maximumTextureSize[0],
        )
        val rejectionLayout = createMgcSpatialStrengthAtlasLayout(
            planeWidth = geometry.rejectionWidth,
            planeHeight = geometry.rejectionHeight,
            planeCount = frameCount,
            maximumTextureSize = maximumTextureSize[0],
        )
        PLog.i(
            TAG,
            "MGC Spatial strength atlas layout frames=$frameCount " +
                "maxTexture=${maximumTextureSize[0]} " +
                "alignment=${alignmentLayout.atlasWidth}x${alignmentLayout.atlasHeight} " +
                "grid=${alignmentLayout.columns}x${alignmentLayout.rows} " +
                "rejection=${rejectionLayout.atlasWidth}x${rejectionLayout.atlasHeight} " +
                "grid=${rejectionLayout.columns}x${rejectionLayout.rows}",
        )
        val identityNoise = spatialNoiseParameters(referenceCalibration)
        return StrengthCapture(
            geometry = geometry,
            outputMode = outputMode,
            frameCount = frameCount,
            alignmentLayout = alignmentLayout,
            rejectionLayout = rejectionLayout,
            alignmentAtlas = createTexture(
                alignmentLayout.atlasWidth,
                alignmentLayout.atlasHeight,
                GLES30.GL_R32F,
                GLES30.GL_NEAREST,
            ),
            rejectionAtlas = createTexture(
                rejectionLayout.atlasWidth,
                rejectionLayout.atlasHeight,
                GLES30.GL_R8,
                GLES30.GL_NEAREST,
            ),
            inputReadNoise = FloatArray(frameCount * 3) { index ->
                identityNoise.read[index / frameCount]
            },
            inputShotNoise = FloatArray(frameCount * 3) { index ->
                identityNoise.shot[index / frameCount]
            },
            frameWeights = FloatArray(frameCount) { SPATIAL_IDENTITY_MULTIPLIER },
            kernelSigmas = FloatArray(frameCount) { SPATIAL_IDENTITY_MULTIPLIER },
            captured = BooleanArray(frameCount),
        )
    }

    private fun captureStrengthFrame(
        capture: StrengthCapture,
        frameIndex: Int,
        calibration: FrameCalibration,
        flowTexture: Int,
        weightTexture: Int,
        identityWeight: Boolean,
    ) {
        require(frameIndex in 0 until capture.frameCount)
        require(!capture.captured[frameIndex])
        for (component in 0 until 2) {
            val slot = component * capture.frameCount + frameIndex
            val outputOriginX = capture.alignmentLayout.originX(slot)
            val outputOriginY = capture.alignmentLayout.originY(slot)
            GLES30.glUseProgram(strengthAlignmentProgram)
            bindTexture(strengthAlignmentProgram, "uFlow", 0, flowTexture)
            uniform2i(
                strengthAlignmentProgram,
                "uOutputSize",
                capture.alignmentWidth,
                capture.alignmentHeight,
            )
            uniform2i(
                strengthAlignmentProgram,
                "uOutputOrigin",
                outputOriginX,
                outputOriginY,
            )
            uniform1i(strengthAlignmentProgram, "uComponent", component)
            drawRegion(
                program = strengthAlignmentProgram,
                target = capture.alignmentAtlas,
                viewportLeft = outputOriginX,
                viewportTop = outputOriginY,
                viewportWidth = capture.alignmentWidth,
                viewportHeight = capture.alignmentHeight,
            )
        }
        val rejectionOriginX = capture.rejectionLayout.originX(frameIndex)
        val rejectionOriginY = capture.rejectionLayout.originY(frameIndex)
        GLES30.glUseProgram(strengthRejectionProgram)
        bindTexture(strengthRejectionProgram, "uWeight", 0, weightTexture)
        uniform2i(
            strengthRejectionProgram,
            "uOutputSize",
            capture.rejectionWidth,
            capture.rejectionHeight,
        )
        uniform2i(
            strengthRejectionProgram,
            "uOutputOrigin",
            rejectionOriginX,
            rejectionOriginY,
        )
        uniform1i(
            strengthRejectionProgram,
            "uIdentityWeight",
            if (identityWeight) 1 else 0,
        )
        drawRegion(
            program = strengthRejectionProgram,
            target = capture.rejectionAtlas,
            viewportLeft = rejectionOriginX,
            viewportTop = rejectionOriginY,
            viewportWidth = capture.rejectionWidth,
            viewportHeight = capture.rejectionHeight,
        )
        val noise = spatialNoiseParameters(calibration)
        var usedIdentity = false
        for (channel in 0 until 3) {
            val destination = channel * capture.frameCount + frameIndex
            capture.inputReadNoise[destination] = noise.read[channel]
            capture.inputShotNoise[destination] = noise.shot[channel]
            usedIdentity = usedIdentity ||
                noise.read[channel] != calibration.cameraRgbReadNoise.getOrElse(channel) { Float.NaN } ||
                noise.shot[channel] != calibration.cameraRgbShotNoise.getOrElse(channel) { Float.NaN }
        }
        capture.frameWeights[frameIndex] = calibration.globalFrameWeight
            .takeIf { it.isFinite() && it > 0f }
            ?: SPATIAL_IDENTITY_MULTIPLIER.also { usedIdentity = true }
        capture.kernelSigmas[frameIndex] = calibration.kernelSigma
            .takeIf { it.isFinite() && it > 0f }
            ?: SPATIAL_IDENTITY_MULTIPLIER.also { usedIdentity = true }
        capture.captured[frameIndex] = true
        if (usedIdentity) {
            PLog.w(
                TAG,
                "MGC Spatial strength frame=$frameIndex contained invalid parameters; " +
                    "using identity inputs read=${noise.read.contentToString()} " +
                    "shot=${noise.shot.contentToString()} " +
                    "frameWeight=${capture.frameWeights[frameIndex]} " +
                    "kernelSigma=${capture.kernelSigmas[frameIndex]}",
            )
        }
    }

    private fun spatialNoiseParameters(
        calibration: FrameCalibration,
    ): SpatialNoiseParameters {
        fun validPair(channel: Int): Boolean {
            val read = calibration.cameraRgbReadNoise.getOrElse(channel) { Float.NaN }
            val shot = calibration.cameraRgbShotNoise.getOrElse(channel) { Float.NaN }
            return read.isFinite() && read >= 0f &&
                shot.isFinite() && shot >= 0f &&
                (read > 0f || shot > 0f)
        }

        val fallbackChannel = intArrayOf(1, 0, 2).firstOrNull(::validPair)
        val fallbackRead = fallbackChannel?.let(calibration.cameraRgbReadNoise::get)
            ?: SPATIAL_IDENTITY_READ_NOISE
        val fallbackShot = fallbackChannel?.let(calibration.cameraRgbShotNoise::get)
            ?: SPATIAL_IDENTITY_SHOT_NOISE
        return SpatialNoiseParameters(
            read = FloatArray(3) { channel ->
                if (validPair(channel)) calibration.cameraRgbReadNoise[channel] else fallbackRead
            },
            shot = FloatArray(3) { channel ->
                if (validPair(channel)) calibration.cameraRgbShotNoise[channel] else fallbackShot
            },
        )
    }

    private fun createIdentitySpatialNoiseModel(
        referenceCalibration: FrameCalibration,
        reason: String,
    ): MgcSpatialStrengthMapGenerator.Result {
        val geometry = mgcSpatialDiagnosticGeometry(
            outputMode = outputMode,
            imageWidth = if (outputMode == MgcSpatialOutputMode.RGB) outputWidth else width,
            imageHeight = if (outputMode == MgcSpatialOutputMode.RGB) outputHeight else height,
        )
        val noise = spatialNoiseParameters(referenceCalibration)
        PLog.w(
            TAG,
            "MGC Spatial denoise model fallback=identity reason=$reason " +
                "strengthQ8=$SPATIAL_IDENTITY_STRENGTH_Q8 " +
                "read=${noise.read.contentToString()} shot=${noise.shot.contentToString()}",
        )
        return MgcSpatialStrengthMapGenerator.Result(
            strengthMap = MgcSpatialStrengthMap(
                width = geometry.rejectionWidth,
                height = geometry.rejectionHeight,
                q8 = ShortArray(geometry.rejectionWidth * geometry.rejectionHeight) {
                    SPATIAL_IDENTITY_STRENGTH_Q8.toShort()
                },
            ),
            outputReadNoise = noise.read,
            outputShotNoise = noise.shot,
            outputWeightsSumTotalDiag0 = FloatArray(3) { SPATIAL_IDENTITY_MULTIPLIER },
            outputWeightsSumTotalDiag1 = FloatArray(3),
        )
    }

    private fun queueStrengthReadback(
        capture: StrengthCapture,
        accumulator: Int = 0,
        preparedAlignment: PreparedTextureReadback? = null,
        preparedRejection: PreparedTextureReadback? = null,
        preparedFusedFixed16: PreparedTextureReadback? = null,
    ): QueuedStrengthReadback {
        check(capture.captured.all { it }) {
            "MGC Spatial noise capture incomplete: ${capture.captured.contentToString()}"
        }
        val allocationStartNs = System.nanoTime()
        val alignment: PreparedTextureReadback
        val rejection: PreparedTextureReadback
        if (capture.outputMode == MgcSpatialOutputMode.RGB) {
            alignment = checkNotNull(preparedAlignment) {
                "MGC Spatial RGB alignment diagnostics were not prepared"
            }
            rejection = checkNotNull(preparedRejection) {
                "MGC Spatial RGB rejection diagnostics were not prepared"
            }
        } else {
            check(preparedAlignment == null && preparedRejection == null)
            alignment = queuePreparedTextureReadback(
                texture = capture.alignmentAtlas,
                textureWidth = capture.alignmentLayout.atlasWidth,
                textureHeight = capture.alignmentLayout.atlasHeight,
                encoding = StrengthReadbackEncoding.FLOAT32,
                byteCount = strengthAlignmentReadbackByteCount(capture),
                label = "MGC Spatial strength alignment atlas",
                atlasLayout = capture.alignmentLayout,
            )
            rejection = queuePreparedTextureReadback(
                texture = capture.rejectionAtlas,
                textureWidth = capture.rejectionLayout.atlasWidth,
                textureHeight = capture.rejectionLayout.atlasHeight,
                encoding = StrengthReadbackEncoding.UNORM8,
                byteCount = strengthRejectionReadbackByteCount(capture),
                label = "MGC Spatial strength rejection atlas",
                atlasLayout = capture.rejectionLayout,
            )
        }
        val fusedFixed16: PreparedTextureReadback
        val fusedFixed16PrepareSubmitMs: Long
        if (capture.outputMode == MgcSpatialOutputMode.BAYER) {
            check(accumulator != 0 && preparedFusedFixed16 == null)
            val fusedFixed16Readback = allocatePixelPackBuffer(
                strengthFixed16ReadbackByteCount(capture),
                "MGC Spatial Bayer Fixed16 noise source",
            )
            val quadWidth = ceilDiv(capture.geometry.imageWidth, 16) * 8
            val quadHeight = ceilDiv(capture.geometry.imageHeight, 16) * 8
            val fusedFixed16StartNs = System.nanoTime()
            val fusedFixed16Texture = renderBayerFixed16Planes(accumulator)
            fusedFixed16PrepareSubmitMs =
                (System.nanoTime() - fusedFixed16StartNs) / 1_000_000L
            val queued = queueTextureReadback(
                texture = fusedFixed16Texture,
                textureWidth = quadWidth,
                textureHeight = quadHeight * 4,
                encoding = StrengthReadbackEncoding.SINT16,
                storage = fusedFixed16Readback,
                label = "MGC Spatial Bayer Fixed16 noise source",
            )
            fusedFixed16 = PreparedTextureReadback(
                byteCount = queued.storage.byteCount,
                queuedGpuReadback = queued,
                cpuBuffer = null,
                mode = queued.mode,
                targetBindMs = queued.targetBindMs,
                readSubmitMs = queued.readSubmitMs,
                totalSubmitMs = queued.totalSubmitMs,
            )
        } else {
            check(accumulator == 0)
            fusedFixed16 = checkNotNull(preparedFusedFixed16) {
                "MGC Spatial RGB Fixed16 diagnostic signal was not prepared"
            }
            check(
                fusedFixed16.byteCount == strengthFixed16ReadbackByteCount(capture)
            ) {
                "MGC Spatial RGB Fixed16 readback size=${fusedFixed16.byteCount}, " +
                    "expected=${strengthFixed16ReadbackByteCount(capture)}"
            }
            fusedFixed16PrepareSubmitMs = fusedFixed16.totalSubmitMs
        }
        PLog.i(
            TAG,
            "MGC Spatial strength PBOs prepared mode=${capture.outputMode.name} " +
                "image=${capture.geometry.imageWidth}x${capture.geometry.imageHeight} bytes=" +
                "${alignment.byteCount.toLong() + rejection.byteCount +
                    fusedFixed16.byteCount} " +
                "took=${(System.nanoTime() - allocationStartNs) / 1_000_000L}ms",
        )
        return QueuedStrengthReadback(
            alignment = alignment,
            rejection = rejection,
            fusedFixed16 = fusedFixed16,
            fusedFixed16PrepareSubmitMs = fusedFixed16PrepareSubmitMs,
        )
    }

    private fun strengthAlignmentReadbackByteCount(capture: StrengthCapture): Int =
        (
            capture.alignmentWidth.toLong() * capture.alignmentHeight *
                capture.frameCount * 2L * Float.SIZE_BYTES
            ).also { bytes -> require(bytes in 1..Int.MAX_VALUE.toLong()) }
            .toInt()

    private fun strengthRejectionReadbackByteCount(capture: StrengthCapture): Int =
        (
            capture.rejectionWidth.toLong() * capture.rejectionHeight * capture.frameCount
            ).also { bytes -> require(bytes in 1..Int.MAX_VALUE.toLong()) }
            .toInt()

    private fun strengthFixed16ReadbackByteCount(capture: StrengthCapture): Int =
        (capture.geometry.fixed16SampleCount * Short.SIZE_BYTES)
            .also { bytes -> require(bytes in 1..Int.MAX_VALUE.toLong()) }
            .toInt()

    private fun allocatePixelPackBuffer(
        byteCount: Int,
        label: String,
    ): PixelPackBuffer {
        require(byteCount > 0)
        val ids = IntArray(1)
        GLES30.glGenBuffers(1, ids, 0)
        val buffer = ids[0]
        check(buffer != 0) { "$label glGenBuffers returned 0" }
        buffers += buffer
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, buffer)
        val allocationByteCount = ((byteCount.toLong() + 3L) and -4L)
            .also { bytes -> require(bytes <= Int.MAX_VALUE) }
            .toInt()
        GLES30.glBufferData(
            GLES30.GL_PIXEL_PACK_BUFFER,
            allocationByteCount,
            null,
            GLES30.GL_STREAM_READ,
        )
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        checkGlError("allocate $label PBO")
        return PixelPackBuffer(buffer, byteCount)
    }

    private fun releasePixelPackBuffer(storage: PixelPackBuffer, label: String) {
        if (!buffers.remove(storage.buffer)) return
        GLES30.glDeleteBuffers(1, intArrayOf(storage.buffer), 0)
        checkGlError("release $label")
    }

    private fun queueTextureReadback(
        texture: Int,
        textureWidth: Int,
        textureHeight: Int,
        encoding: StrengthReadbackEncoding,
        storage: PixelPackBuffer,
        label: String,
        atlasLayout: MgcSpatialStrengthAtlasLayout? = null,
    ): QueuedTextureReadback {
        atlasLayout?.let { layout ->
            require(layout.atlasWidth == textureWidth && layout.atlasHeight == textureHeight)
        }
        val bytesPerValue = when (encoding) {
            StrengthReadbackEncoding.FLOAT32 -> Float.SIZE_BYTES
            StrengthReadbackEncoding.UNORM8 -> Byte.SIZE_BYTES
            StrengthReadbackEncoding.SINT16 -> Short.SIZE_BYTES
        }
        val logicalValueCount = atlasLayout?.logicalValueCount
            ?: textureWidth.toLong() * textureHeight
        require(logicalValueCount * bytesPerValue == storage.byteCount.toLong()) {
            "$label logical readback size does not match storage: " +
                "values=$logicalValueCount bytesPerValue=$bytesPerValue " +
                "storage=${storage.byteCount}"
        }
        val packProgram = when (encoding) {
            StrengthReadbackEncoding.FLOAT32 -> strengthFloatPackProgram
            StrengthReadbackEncoding.UNORM8 -> strengthUnorm8PackProgram
            StrengthReadbackEncoding.SINT16 -> strengthSint16PackProgram
        }
        val invocationCount = when (encoding) {
            StrengthReadbackEncoding.FLOAT32 -> logicalValueCount
            StrengthReadbackEncoding.UNORM8 -> (logicalValueCount + 3L) / 4L
            StrengthReadbackEncoding.SINT16 -> (logicalValueCount + 1L) / 2L
        }
        val requiredGroupCount =
            (invocationCount + GlesComputeWorkGroup.LINEAR_SIZE - 1L) /
                GlesComputeWorkGroup.LINEAR_SIZE
        val packedStorageBytes = (storage.byteCount.toLong() + 3L) and -4L
        val hasComputeDispatchCapacity =
            requiredGroupCount <= maxComputePackGroupsX.toLong() * maxComputePackGroupsY
        if (packProgram != 0 &&
            packedStorageBytes <= maxShaderStorageBlockBytes &&
            hasComputeDispatchCapacity
        ) {
            val dispatch = createMgcSpatialStrengthPackDispatch(
                invocationCount = invocationCount,
                localSize = GlesComputeWorkGroup.LINEAR_SIZE,
                maximumGroupsX = maxComputePackGroupsX,
                maximumGroupsY = maxComputePackGroupsY,
            )
            return queueTextureSsboPack(
                texture = texture,
                textureWidth = textureWidth,
                textureHeight = textureHeight,
                encoding = encoding,
                storage = storage,
                program = packProgram,
                label = label,
                atlasLayout = atlasLayout,
                invocationCount = invocationCount,
                dispatch = dispatch,
            )
        }
        if (packProgram != 0 && packedStorageBytes > maxShaderStorageBlockBytes) {
            PLog.w(
                TAG,
                "MGC Spatial strength SSBO pack exceeds device block limit; " +
                    "label=$label bytes=$packedStorageBytes " +
                    "max=$maxShaderStorageBlockBytes, using framebuffer readback",
            )
        }
        if (packProgram != 0 && !hasComputeDispatchCapacity) {
            PLog.w(
                TAG,
                "MGC Spatial strength SSBO pack exceeds device dispatch grid; " +
                    "label=$label groups=$requiredGroupCount " +
                    "max=${maxComputePackGroupsX}x$maxComputePackGroupsY, " +
                    "using framebuffer readback",
            )
        }
        val totalStartNs = System.nanoTime()
        val targetBindStartNs = System.nanoTime()
        bindRenderTargets(intArrayOf(texture), label)
        val targetBindMs = (System.nanoTime() - targetBindStartNs) / 1_000_000L
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, storage.buffer)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
        val readSubmitStartNs = System.nanoTime()
        val readFormat = when (encoding) {
            StrengthReadbackEncoding.FLOAT32,
            StrengthReadbackEncoding.UNORM8 -> GLES30.GL_RED
            StrengthReadbackEncoding.SINT16 -> GLES30.GL_RED_INTEGER
        }
        val readType = when (encoding) {
            StrengthReadbackEncoding.FLOAT32 -> GLES30.GL_FLOAT
            StrengthReadbackEncoding.UNORM8 -> GLES30.GL_UNSIGNED_BYTE
            StrengthReadbackEncoding.SINT16 -> GLES30.GL_SHORT
        }
        if (atlasLayout == null || atlasLayout.columns == 1) {
            GLES30.glReadPixels(
                0,
                0,
                textureWidth,
                textureHeight,
                readFormat,
                readType,
                0,
            )
        } else {
            for (plane in 0 until atlasLayout.planeCount) {
                val byteOffset = (atlasLayout.planeValueCount * plane * bytesPerValue)
                    .also { offset -> require(offset <= Int.MAX_VALUE) }
                    .toInt()
                GLES30.glReadPixels(
                    atlasLayout.originX(plane),
                    atlasLayout.originY(plane),
                    atlasLayout.planeWidth,
                    atlasLayout.planeHeight,
                    readFormat,
                    readType,
                    byteOffset,
                )
            }
        }
        val readSubmitMs = (System.nanoTime() - readSubmitStartNs) / 1_000_000L
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("queue $label")
        return QueuedTextureReadback(
            storage = storage,
            mode = if (atlasLayout == null || atlasLayout.columns == 1) {
                "framebuffer-readpixels"
            } else {
                "framebuffer-readpixels-atlas"
            },
            targetBindMs = targetBindMs,
            readSubmitMs = readSubmitMs,
            totalSubmitMs = (System.nanoTime() - totalStartNs) / 1_000_000L,
        ).also { queued ->
            PLog.i(
                TAG,
                "MGC Spatial strength PBO submit label=$label " +
                    "mode=${queued.mode} bytes=${storage.byteCount} " +
                    "setup=${queued.targetBindMs}ms submit=${queued.readSubmitMs}ms " +
                    "total=${queued.totalSubmitMs}ms",
            )
        }
    }

    private fun queuePreparedTextureReadback(
        texture: Int,
        textureWidth: Int,
        textureHeight: Int,
        encoding: StrengthReadbackEncoding,
        byteCount: Int,
        label: String,
        atlasLayout: MgcSpatialStrengthAtlasLayout? = null,
    ): PreparedTextureReadback {
        val storage = allocatePixelPackBuffer(byteCount, label)
        val queued = queueTextureReadback(
            texture = texture,
            textureWidth = textureWidth,
            textureHeight = textureHeight,
            encoding = encoding,
            storage = storage,
            label = label,
            atlasLayout = atlasLayout,
        )
        return PreparedTextureReadback(
            byteCount = queued.storage.byteCount,
            queuedGpuReadback = queued,
            cpuBuffer = null,
            mode = queued.mode,
            targetBindMs = queued.targetBindMs,
            readSubmitMs = queued.readSubmitMs,
            totalSubmitMs = queued.totalSubmitMs,
        )
    }

    private fun queueTextureSsboPack(
        texture: Int,
        textureWidth: Int,
        textureHeight: Int,
        encoding: StrengthReadbackEncoding,
        storage: PixelPackBuffer,
        program: Int,
        label: String,
        atlasLayout: MgcSpatialStrengthAtlasLayout?,
        invocationCount: Long,
        dispatch: MgcSpatialStrengthPackDispatch,
    ): QueuedTextureReadback {
        val totalStartNs = System.nanoTime()
        val setupStartNs = System.nanoTime()
        GLES31.glUseProgram(program)
        GLES31.glActiveTexture(GLES31.GL_TEXTURE0)
        GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, texture)
        GLES31.glUniform1i(GLES31.glGetUniformLocation(program, "uSource"), 0)
        val planeWidth = atlasLayout?.planeWidth ?: textureWidth
        val planeHeight = atlasLayout?.planeHeight ?: textureHeight
        val planeCount = atlasLayout?.planeCount ?: 1
        val atlasColumns = atlasLayout?.columns ?: 1
        GLES31.glUniform2i(
            GLES31.glGetUniformLocation(program, "uPlaneSize"),
            planeWidth,
            planeHeight,
        )
        GLES31.glUniform1i(
            GLES31.glGetUniformLocation(program, "uPlaneCount"),
            planeCount,
        )
        GLES31.glUniform1i(
            GLES31.glGetUniformLocation(program, "uAtlasColumns"),
            atlasColumns,
        )
        GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, storage.buffer)
        val setupMs = (System.nanoTime() - setupStartNs) / 1_000_000L
        val valueCount = planeWidth.toLong() * planeHeight * planeCount
        val expectedInvocationCount = when (encoding) {
            StrengthReadbackEncoding.FLOAT32 -> valueCount
            StrengthReadbackEncoding.UNORM8 -> (valueCount + 3L) / 4L
            StrengthReadbackEncoding.SINT16 -> (valueCount + 1L) / 2L
        }
        check(invocationCount == expectedInvocationCount)
        require(invocationCount in 1..Int.MAX_VALUE.toLong()) {
            "$label pack invocation count is invalid: $invocationCount"
        }
        val submitStartNs = System.nanoTime()
        GLES31.glDispatchCompute(
            dispatch.groupsX,
            dispatch.groupsY,
            1,
        )
        GLES31.glMemoryBarrier(
            GLES31.GL_SHADER_STORAGE_BARRIER_BIT or GLES31.GL_BUFFER_UPDATE_BARRIER_BIT,
        )
        val submitMs = (System.nanoTime() - submitStartNs) / 1_000_000L
        GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER, 0, 0)
        GLES31.glBindTexture(GLES31.GL_TEXTURE_2D, 0)
        GLES31.glUseProgram(0)
        checkGlError("queue $label SSBO pack")
        return QueuedTextureReadback(
            storage = storage,
            mode = "compute-ssbo-pack-${dispatch.groupsX}x${dispatch.groupsY}",
            targetBindMs = setupMs,
            readSubmitMs = submitMs,
            totalSubmitMs = (System.nanoTime() - totalStartNs) / 1_000_000L,
        ).also { queued ->
            PLog.i(
                TAG,
                "MGC Spatial strength PBO submit label=$label mode=${queued.mode} " +
                    "bytes=${storage.byteCount} setup=${queued.targetBindMs}ms " +
                    "submit=${queued.readSubmitMs}ms total=${queued.totalSubmitMs}ms",
            )
        }
    }

    private fun mapPixelPackBuffer(
        buffer: Int,
        byteCount: Int,
        label: String,
    ): ByteBuffer {
        val startNs = System.nanoTime()
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, buffer)
        val mapped = GLES30.glMapBufferRange(
            GLES30.GL_PIXEL_PACK_BUFFER,
            0,
            byteCount,
            GLES30.GL_MAP_READ_BIT,
        ) as? ByteBuffer ?: error("Unable to map $label")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        PLog.i(
            TAG,
            "MGC Spatial strength PBO mapped label=$label bytes=$byteCount " +
                "wait=${(System.nanoTime() - startNs) / 1_000_000L}ms",
        )
        return mapped.order(ByteOrder.nativeOrder()).apply {
            position(0)
            limit(byteCount)
        }
    }

    private fun unmapPixelPackBuffer(buffer: Int) {
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, buffer)
        check(GLES30.glUnmapBuffer(GLES30.GL_PIXEL_PACK_BUFFER)) {
            "MGC Spatial readback buffer contents became invalid"
        }
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
    }

    private fun materializePreparedReadbackToHost(
        prepared: PreparedTextureReadback,
        label: String,
    ): PreparedTextureReadback {
        val queued = checkNotNull(prepared.queuedGpuReadback) {
            "$label is already host-resident"
        }
        check(prepared.cpuBuffer == null)
        val host = LargeDirectBuffer.allocate(prepared.byteCount.toLong(), label)
            ?.order(ByteOrder.nativeOrder()) ?: error("Unable to allocate $label")
        var mapped: ByteBuffer? = null
        val materializeStartNs = System.nanoTime()
        try {
            try {
                mapped = mapPixelPackBuffer(
                    queued.storage.buffer,
                    prepared.byteCount,
                    label,
                )
                host.clear()
                host.put(checkNotNull(mapped).duplicate())
                host.rewind()
            } finally {
                try {
                    if (mapped != null) {
                        unmapPixelPackBuffer(queued.storage.buffer)
                    }
                } finally {
                    releasePixelPackBuffer(queued.storage, label)
                }
            }
        } catch (throwable: Throwable) {
            LargeDirectBuffer.free(host)
            throw throwable
        }
        val materializeMs = (System.nanoTime() - materializeStartNs) / 1_000_000L
        return PreparedTextureReadback(
            byteCount = prepared.byteCount,
            queuedGpuReadback = null,
            cpuBuffer = host,
            mode = "${prepared.mode}-host",
            targetBindMs = prepared.targetBindMs,
            readSubmitMs = prepared.readSubmitMs,
            totalSubmitMs = prepared.totalSubmitMs + materializeMs,
        ).also {
            PLog.i(
                TAG,
                "MGC Spatial diagnostic host materialized label=$label " +
                    "bytes=${prepared.byteCount} took=${materializeMs}ms",
            )
        }
    }

    private fun resolveSpatialNoiseModel(
        capture: StrengthCapture,
        queued: QueuedStrengthReadback,
    ): MgcSpatialStrengthMapGenerator.Result? {
        val totalStartNs = System.nanoTime()
        var diagnosticsMs = 0L
        var aotMs = 0L
        var alignment: ByteBuffer? = null
        var rejection: ByteBuffer? = null
        var fusedFixed16: ByteBuffer? = null
        var alignmentGpuMapped = false
        var rejectionGpuMapped = false
        var fusedFixed16GpuMapped = false
        return try {
            alignment = queued.alignment.queuedGpuReadback?.let { gpuReadback ->
                mapPixelPackBuffer(
                    gpuReadback.storage.buffer,
                    gpuReadback.storage.byteCount,
                    "MGC Spatial strength alignment atlas",
                ).also { alignmentGpuMapped = true }
            } ?: checkNotNull(queued.alignment.cpuBuffer).duplicate()
                .order(ByteOrder.nativeOrder())
                .apply {
                    position(0)
                    limit(queued.alignment.byteCount)
                }
            rejection = queued.rejection.queuedGpuReadback?.let { gpuReadback ->
                mapPixelPackBuffer(
                    gpuReadback.storage.buffer,
                    gpuReadback.storage.byteCount,
                    "MGC Spatial strength rejection atlas",
                ).also { rejectionGpuMapped = true }
            } ?: checkNotNull(queued.rejection.cpuBuffer).duplicate()
                .order(ByteOrder.nativeOrder())
                .apply {
                    position(0)
                    limit(queued.rejection.byteCount)
                }
            fusedFixed16 = queued.fusedFixed16.queuedGpuReadback?.let { gpuReadback ->
                mapPixelPackBuffer(
                    gpuReadback.storage.buffer,
                    gpuReadback.storage.byteCount,
                    "MGC Spatial ${capture.outputMode.name} Fixed16 noise source",
                ).also { fusedFixed16GpuMapped = true }
            } ?: checkNotNull(queued.fusedFixed16.cpuBuffer).duplicate()
                .order(ByteOrder.nativeOrder())
                .apply {
                    position(0)
                    limit(queued.fusedFixed16.byteCount)
                }
            val mappedAlignment = checkNotNull(alignment)
            val mappedRejection = checkNotNull(rejection)
            val mappedFusedFixed16 = checkNotNull(fusedFixed16)
            if (RawStackRuntimeDebug.mgcSpatialInputDiagnosticsEnabled) {
                val diagnosticsStartNs = System.nanoTime()
                logSpatialNoiseInputs(capture, mappedAlignment, mappedRejection)
                diagnosticsMs = (System.nanoTime() - diagnosticsStartNs) / 1_000_000L
            }
            val aotStartNs = System.nanoTime()
            MgcSpatialStrengthMapGenerator.compute(
                outputMode = capture.outputMode,
                fusedFixed16 = mappedFusedFixed16,
                width = capture.geometry.imageWidth,
                height = capture.geometry.imageHeight,
                cfaPattern = cfaPattern,
                alignment = mappedAlignment,
                alignmentWidth = capture.alignmentWidth,
                alignmentHeight = capture.alignmentHeight,
                rejection = mappedRejection,
                rejectionWidth = capture.rejectionWidth,
                rejectionHeight = capture.rejectionHeight,
                frameCount = capture.frameCount,
                inputReadNoise = capture.inputReadNoise,
                inputShotNoise = capture.inputShotNoise,
                frameWeights = capture.frameWeights,
                kernelSigmas = capture.kernelSigmas,
            ).also {
                aotMs = (System.nanoTime() - aotStartNs) / 1_000_000L
            }
        } finally {
            val unmapStartNs = System.nanoTime()
            if (fusedFixed16GpuMapped) {
                unmapPixelPackBuffer(
                    checkNotNull(queued.fusedFixed16.queuedGpuReadback).storage.buffer,
                )
            }
            if (rejectionGpuMapped) {
                unmapPixelPackBuffer(
                    checkNotNull(queued.rejection.queuedGpuReadback).storage.buffer,
                )
            }
            if (alignmentGpuMapped) {
                unmapPixelPackBuffer(
                    checkNotNull(queued.alignment.queuedGpuReadback).storage.buffer,
                )
            }
            PLog.i(
                TAG,
                "MGC Spatial strength resolve mode=${capture.outputMode.name} " +
                    "diagnostics=${diagnosticsMs}ms " +
                    "aot=${aotMs}ms " +
                    "unmap=${(System.nanoTime() - unmapStartNs) / 1_000_000L}ms " +
                    "total=${(System.nanoTime() - totalStartNs) / 1_000_000L}ms",
            )
        }
    }

    private fun logSpatialNoiseInputs(
        capture: StrengthCapture,
        alignmentStorage: ByteBuffer,
        rejectionStorage: ByteBuffer,
    ) {
        val alignmentPlane = capture.alignmentWidth * capture.alignmentHeight
        val alignment = alignmentStorage.duplicate()
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
        val alignmentMeanAbs = FloatArray(capture.frameCount)
        val alignmentMaxAbs = FloatArray(capture.frameCount)
        for (frame in 0 until capture.frameCount) {
            var sum = 0.0
            var maximum = 0f
            for (component in 0 until 2) {
                val base = (component * capture.frameCount + frame) * alignmentPlane
                for (pixel in 0 until alignmentPlane) {
                    val absolute = kotlin.math.abs(alignment.get(base + pixel))
                    sum += absolute.toDouble()
                    maximum = max(maximum, absolute)
                }
            }
            alignmentMeanAbs[frame] =
                (sum / (alignmentPlane * 2).toDouble()).toFloat()
            alignmentMaxAbs[frame] = maximum
        }

        val rejectionPlane = capture.rejectionWidth * capture.rejectionHeight
        val rejection = rejectionStorage.duplicate()
        val acceptedWeightMean = FloatArray(capture.frameCount)
        for (frame in 0 until capture.frameCount) {
            var sum = 0L
            val base = frame * rejectionPlane
            for (pixel in 0 until rejectionPlane) {
                sum += rejection.get(base + pixel).toInt() and 0xff
            }
            acceptedWeightMean[frame] =
                sum.toFloat() / (rejectionPlane.toFloat() * 255f)
        }

        PLog.i(
            TAG,
            "MGC Spatial noise inputs mode=${capture.outputMode.name} " +
                "image=${capture.geometry.imageWidth}x${capture.geometry.imageHeight} " +
                "frames=${capture.frameCount} " +
                "alignmentMeanAbs=${alignmentMeanAbs.contentToString()} " +
                "alignmentMaxAbs=${alignmentMaxAbs.contentToString()} " +
                "acceptedWeightMean=${acceptedWeightMean.contentToString()} " +
                "read(channel-major)=${capture.inputReadNoise.contentToString()} " +
                "shot(channel-major)=${capture.inputShotNoise.contentToString()} " +
                "frameWeight=${capture.frameWeights.contentToString()} " +
                "kernelSigma=${capture.kernelSigmas.contentToString()}",
        )
    }

    private fun logLinearKernelMask(
        texture: Int,
        selectedFrameIndex: Int,
    ) {
        val binaryMask = readR8Mask(
            texture = texture,
            label = "MGC Bento linear kernel mask",
            maskWidth = mergeWeightWidth,
            maskHeight = mergeWeightHeight,
        )
        val activePixels = binaryMask.count { (it.toInt() and 0xff) != 0 }
        PLog.i(
            TAG,
            "MGC linear kernel mask size=${mergeWeightWidth}x$mergeWeightHeight " +
                "mode=bento-selected-slice selectedFrame=$selectedFrameIndex " +
                "rule=binary-3x3-nonuniform " +
                "active=$activePixels/${binaryMask.size}",
        )
    }

    private fun countActiveMaskPixels(mask: ByteArray): Int =
        mask.count { (it.toInt() and 0xff) != 0 }

    private fun elapsedMs(startNs: Long): Long =
        (System.nanoTime() - startNs) / 1_000_000L

    private fun assessBentoMasks(
        baseHighlightMask: ByteArray,
        inpaintingMask: ByteArray,
        ultrashortClippingMask: ByteArray,
        tilingMask: ByteArray,
    ): BentoAssessment {
        val guideMaskSize = guideWidth * guideHeight
        require(
            baseHighlightMask.size == guideMaskSize &&
                inpaintingMask.size == guideMaskSize &&
                ultrashortClippingMask.size == guideMaskSize,
        )
        require(tilingMask.size == bayerAlignmentWidth * bayerAlignmentHeight)
        var clippedPixels = 0
        var clippedByUltrashortPixels = 0
        for (index in 0 until guideMaskSize) {
            if ((baseHighlightMask[index].toInt() and 0xff) == 0) continue
            clippedPixels += 1
            if ((ultrashortClippingMask[index].toInt() and 0xff) != 0) {
                clippedByUltrashortPixels += 1
            }
        }
        val clippedRatio = clippedPixels.toFloat() / guideMaskSize.toFloat()
        val ultrashortOverlap = if (clippedPixels > 0) {
            clippedByUltrashortPixels.toFloat() / clippedPixels.toFloat()
        } else {
            0f
        }
        val largestInpaintingArea = BentoFallbackTopology.largestEightConnectedComponentArea(
            inpaintingMask,
            guideWidth,
            guideHeight,
        )
        val largestTilingArea = BentoFallbackTopology.largestEightConnectedComponentArea(
            tilingMask,
            bayerAlignmentWidth,
            bayerAlignmentHeight,
        )
        val reason = when {
            clippedRatio <= BENTO_MIN_CLIPPED_PIXEL_RATIO ->
                "insufficient_clipped_pixels"
            largestInpaintingArea >= BENTO_MAX_INPAINTING_COMPONENT_AREA ->
                "large_hole_needing_inpainting"
            ultrashortOverlap > BENTO_MAX_ULTRASHORT_CLIPPING_OVERLAP ->
                "high_ultrashort_clipping_overlap"
            largestTilingArea > BENTO_MAX_TILING_COMPONENT_AREA ->
                "tiling_artifacts"
            else -> "none"
        }
        return BentoAssessment(
            accepted = reason == "none",
            reason = reason,
            clippedPixelRatio = clippedRatio,
            largestInpaintingArea = largestInpaintingArea,
            largestTilingArea = largestTilingArea,
            ultrashortClippingOverlap = ultrashortOverlap,
        )
    }

    private fun renderMerge(
        rawTexture: Int,
        bayerAlignmentTexture: Int,
        weightTexture: Int,
        linearKernelMaskTexture: Int,
        calibration: FrameCalibration,
        accumulatorColor: Int,
        useFrameWeight: Boolean,
    ) {
        renderBayerMerge(
            rawTexture = rawTexture,
            alignmentTexture = bayerAlignmentTexture,
            weightTexture = weightTexture,
            linearKernelMaskTexture = linearKernelMaskTexture,
            calibration = calibration,
            accumulator = accumulatorColor,
            useFrameWeight = useFrameWeight,
        )
    }

    private fun renderBayerMerge(
        rawTexture: Int,
        alignmentTexture: Int,
        weightTexture: Int,
        linearKernelMaskTexture: Int,
        calibration: FrameCalibration,
        accumulator: Int,
        useFrameWeight: Boolean,
    ) {
        val program = if (mergeMethod == MgcMergeMethod.SABRE) sabreMergeBayerProgram else mergeBayerProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uRaw", 0, rawTexture)
        bindTexture(program, "uAlignment", 1, alignmentTexture)
        bindTexture(program, "uFrameWeight", 2, weightTexture)
        uniform1f(program, "uGlobalFrameWeight", calibration.globalFrameWeight)
        if (mergeMethod == MgcMergeMethod.SABRE) {
            bindTexture(program, "uCovariance", 3, currentMergeCovariance)
            uniform2i(program, "uRawSize", width, height)
            uniform1i(program, "uCfaPattern", cfaPattern)
            uniform4fv(program, "uGains", calibration.bayerPhaseGains)
            uniform4fv(program, "uBlackLevelsTimesGains", calibration.bayerPhaseBlackTerms)
            uniform4f(
                program,
                "uCovRangeRg",
                covariancePackOffset(COV_MIN_R, COV_MAX_R),
                covariancePackScale(COV_MIN_R, COV_MAX_R),
                covariancePackOffset(COV_MIN_G, COV_MAX_G),
                covariancePackScale(COV_MIN_G, COV_MAX_G),
            )
            uniform2f(
                program,
                "uCovRangeB",
                covariancePackOffset(COV_MIN_B, COV_MAX_B),
                covariancePackScale(COV_MIN_B, COV_MAX_B),
            )
            uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        } else {
            bindTexture(program, "uLinearKernelMask", 3, linearKernelMaskTexture)
            uniform2i(program, "uRawSize", width, height)
            uniform1i(program, "uCfaPattern", cfaPattern)
            uniform4fv(program, "uGains", calibration.bayerPhaseGains)
            uniform4fv(program, "uBlackLevelsTimesGains", calibration.bayerPhaseBlackTerms)
            uniform1f(program, "uKernelSigma", calibration.kernelSigma)
            uniform1f(program, "uInterpolationFlowTolerance", SPATIAL_INTERPOLATION_FLOW_TOLERANCE)
            uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        }
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                width,
                height,
                intArrayOf(accumulator),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun clearAccumulator(color: Int) {
        bindRenderTargets(intArrayOf(color), "clear accumulator")
        GLES30.glViewport(0, 0, width, height)
        GLES30.glClearBufferfv(
            GLES30.GL_COLOR,
            0,
            floatArrayOf(0f, 0f, 0f, 0f),
            0,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    /**
     * Selects the one-upload-per-frame path when both its temporal and final phases fit the hard
     * RAW GPU budget. The estimates are phase-aware: final output/diagnostic storage never
     * overlaps temporal scratch, while the two additive accumulators span both phases.
     */
    private fun createOnlineRgbAccumulator(
        diagnosticCapture: StrengthCapture?,
    ): OnlineRgbAccumulator? {
        check(outputMode == MgcSpatialOutputMode.RGB)
        val rawBytes = width.toLong() * height * RAW_BYTES_PER_PIXEL
        val accumulatorBytes = outputWidth.toLong() * outputHeight * 16L
        val chromaGuideBytes = width.toLong() * height * 2L
        val outputStorageBytes = outputWidth.toLong() * outputHeight * 8L
        val diagnosticTextureBytes = diagnosticCapture?.let { capture ->
            capture.geometry.fixed16Width.toLong() * capture.geometry.fixed16Height * 2L
        } ?: 0L
        val diagnosticPboBytes = diagnosticCapture?.let { capture ->
            strengthFixed16ReadbackByteCount(capture).toLong()
        } ?: 0L
        // Sequential temporal scratch is allocated lazily by the first non-reference frame.
        // Reserve two RAW-sized scratch surfaces before choosing the online path so a near-budget
        // burst falls back to reconstruction bands before capture buffers have started to close.
        val temporalScratchReserveBytes = maxOf(
            RGB_TEXTURE_BUDGET_RESERVE_BYTES,
            rawBytes * 2L,
        )
        val temporalProjectedBytes = estimatedOwnedTextureBytes() +
            accumulatorBytes + chromaGuideBytes + temporalScratchReserveBytes
        val finalProjectedBytes = accumulatorBytes + outputStorageBytes +
            diagnosticTextureBytes + diagnosticPboBytes + RGB_TEXTURE_BUDGET_RESERVE_BYTES
        val projectedGpuBytes = maxOf(temporalProjectedBytes, finalProjectedBytes)
        if (projectedGpuBytes > RGB_TEXTURE_BUDGET_BYTES) {
            PLog.i(
                TAG,
                "MGC Spatial RGB online path skipped projectedGpuBytes=$projectedGpuBytes " +
                    "temporalProjectedBytes=$temporalProjectedBytes " +
                    "finalProjectedBytes=$finalProjectedBytes " +
                    "budgetBytes=$RGB_TEXTURE_BUDGET_BYTES",
            )
            return null
        }

        val chromaGuideTexture = createTexture(
            width,
            height,
            GLES30.GL_R16F,
            GLES30.GL_NEAREST,
        )
        val semanticAccumulator = createTexture(
            outputWidth,
            outputHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        val opponentWeightAccumulator = createTexture(
            outputWidth,
            outputHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        clearRgbAccumulators(
            semanticAccumulator = semanticAccumulator,
            opponentWeightAccumulator = opponentWeightAccumulator,
            tileWidth = outputWidth,
            tileHeight = outputHeight,
        )
        val actualTemporalBytes = estimatedOwnedTextureBytes() +
            RGB_TEXTURE_BUDGET_RESERVE_BYTES
        check(actualTemporalBytes <= RGB_TEXTURE_BUDGET_BYTES) {
            "MGC Spatial RGB online temporal allocation=$actualTemporalBytes, " +
                "budget=$RGB_TEXTURE_BUDGET_BYTES"
        }
        val drawBands = MgcSpatialRgbTilePlanner.planHorizontalBands(
            outputWidth = outputWidth,
            outputHeight = outputHeight,
            maximumBandHeight = RGB_ONLINE_DRAW_BAND_HEIGHT,
        )
        PLog.i(
            TAG,
            "MGC Spatial RGB online accumulator selected bands=${drawBands.size} " +
                "drawBandHeight=$RGB_ONLINE_DRAW_BAND_HEIGHT rawSlots=1 " +
                "textureBytes=${estimatedOwnedTextureBytes()} " +
                "temporalProjectedBytes=$temporalProjectedBytes " +
                "finalProjectedBytes=$finalProjectedBytes " +
                "budgetBytes=$RGB_TEXTURE_BUDGET_BYTES",
        )
        return OnlineRgbAccumulator(
            semanticAccumulator = semanticAccumulator,
            opponentWeightAccumulator = opponentWeightAccumulator,
            chromaGuideTexture = chromaGuideTexture,
            drawBands = drawBands,
            projectedGpuBytes = projectedGpuBytes,
        )
    }

    private fun contributeOnlineRgbFrame(
        accumulator: OnlineRgbAccumulator,
        frame: RgbMergeFrame,
        rawTexture: Int,
    ) {
        val fullRaw = MgcSpatialRgbRect(0, 0, width, height)
        renderRgbChromaGuide(
            frame = frame,
            rawTexture = rawTexture,
            rawTextureOrigin = fullRaw,
            sourceRegion = fullRaw,
            outputTexture = accumulator.chromaGuideTexture,
        )
        accumulator.drawBands.forEach { band ->
            renderRgbFrameContribution(
                frame = frame,
                rawTexture = rawTexture,
                rawTextureOrigin = fullRaw,
                sourceRegion = fullRaw,
                outputCores = listOf(band.outputCore),
                chromaGuideRegionTexture = accumulator.chromaGuideTexture,
                semanticAccumulator = accumulator.semanticAccumulator,
                opponentWeightAccumulator = accumulator.opponentWeightAccumulator,
                accumulatorIsFullOutput = true,
            )
        }
        accumulator.contributedFrames += 1
    }

    private fun finishOnlineRgbMerge(
        accumulator: OnlineRgbAccumulator,
        outputExposureScale: Float,
        diagnosticCapture: StrengthCapture?,
    ): RgbMergeOutput {
        require(outputExposureScale.isFinite() && outputExposureScale > 0f)
        val fullOutput = MgcSpatialRgbRect(0, 0, outputWidth, outputHeight)
        val lensShadingTexture = createLensShadingTexture()
        val gpuOutput = if (exportGpuLinearRgbSource) {
            createTexture(
                outputWidth,
                outputHeight,
                when (gpuLinearRgbStorage) {
                    GpuLinearRgbStorage.RGBA16UI -> GLES30.GL_RGBA16UI
                    GpuLinearRgbStorage.RGBA16F -> GLES30.GL_RGBA16F
                },
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val cpuOutputTexture = if (gpuOutput == 0) {
            createTexture(
                outputWidth,
                outputHeight,
                GLES30.GL_RGBA16UI,
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val outputBytes = outputWidth.toLong() * outputHeight * 3L * Short.SIZE_BYTES
        require(outputBytes in 1..Int.MAX_VALUE.toLong())
        val cpuOutput = if (gpuOutput == 0) {
            LargeDirectBuffer.allocate(outputBytes, "MGC Spatial online RGB16 output")
                ?.order(ByteOrder.nativeOrder()) ?: error(
                "Unable to allocate MGC Spatial online RGB16 output",
            )
        } else {
            null
        }
        val cpuReadback = if (cpuOutput != null) {
            ByteBuffer.allocateDirect(
                outputWidth * outputHeight * 4 * Short.SIZE_BYTES,
            ).order(ByteOrder.nativeOrder())
        } else {
            null
        }
        var diagnosticStorage: PixelPackBuffer? = null
        val completionRecorder = GlesGpuCompletion.StackTimelineRecorder()
        var completionTimeline: GpuStackCompletionTimeline? = null
        try {
            val target = if (gpuOutput != 0) gpuOutput else cpuOutputTexture
            renderRgbNormalizedTile(
                semanticAccumulator = accumulator.semanticAccumulator,
                opponentWeightAccumulator = accumulator.opponentWeightAccumulator,
                lensShadingTexture = lensShadingTexture,
                outputCore = fullOutput,
                target = target,
                targetIsFullOutput = gpuOutput != 0,
                outputExposureScale = outputExposureScale,
            )
            if (cpuOutput != null) {
                readRgbTile(
                    texture = cpuOutputTexture,
                    outputCore = fullOutput,
                    readback = checkNotNull(cpuReadback),
                    output = cpuOutput,
                )
                cpuOutput.rewind()
            }

            val diagnosticFixed16 = diagnosticCapture?.let { capture ->
                val fixed16Texture = createTexture(
                    capture.geometry.fixed16Width,
                    capture.geometry.fixed16Height,
                    GLES30.GL_R16I,
                    GLES30.GL_NEAREST,
                )
                val diagnosticFramebuffer = createFramebuffer()
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, diagnosticFramebuffer)
                GLES30.glFramebufferTexture2D(
                    GLES30.GL_FRAMEBUFFER,
                    GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D,
                    fixed16Texture,
                    0,
                )
                GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "MGC online RGB Fixed16 framebuffer is incomplete"
                }
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                diagnosticStorage = allocatePixelPackBuffer(
                    strengthFixed16ReadbackByteCount(capture),
                    "MGC Spatial online RGB Fixed16 source",
                )
                val timing = packRgbFixed16TileReadback(
                    capture = capture,
                    semanticAccumulator = accumulator.semanticAccumulator,
                    opponentWeightAccumulator = accumulator.opponentWeightAccumulator,
                    outputCore = fullOutput,
                    fixed16Texture = fixed16Texture,
                    diagnosticFramebuffer = diagnosticFramebuffer,
                    storage = checkNotNull(diagnosticStorage),
                )
                val queued = QueuedTextureReadback(
                    storage = checkNotNull(diagnosticStorage),
                    mode = "online-full-accumulator-pbo-rgb-planar-q14",
                    targetBindMs = timing.setupNs / 1_000_000L,
                    readSubmitMs = timing.dispatchNs / 1_000_000L,
                    totalSubmitMs = (timing.setupNs + timing.dispatchNs) / 1_000_000L,
                )
                PreparedTextureReadback(
                    byteCount = strengthFixed16ReadbackByteCount(capture),
                    queuedGpuReadback = queued,
                    cpuBuffer = null,
                    mode = queued.mode,
                    targetBindMs = queued.targetBindMs,
                    readSubmitMs = queued.readSubmitMs,
                    totalSubmitMs = queued.totalSubmitMs,
                )
            }

            val gpuDeclaredBytes = estimatedOwnedTextureBytes() +
                (diagnosticStorage?.byteCount?.toLong() ?: 0L)
            check(gpuDeclaredBytes <= RGB_TEXTURE_BUDGET_BYTES) {
                "MGC Spatial online RGB allocated $gpuDeclaredBytes GPU bytes, " +
                    "budget=$RGB_TEXTURE_BUDGET_BYTES"
            }
            if (gpuOutput != 0) {
                completionRecorder.mark(GpuStackCompletionStage.FINAL_EXPORT)
                completionTimeline = completionRecorder.finish()
                if (completionTimeline == null) {
                    GlesGpuCompletion.awaitSubmittedWork(
                        label = "MGC Spatial online RGB export",
                        checkGlError = ::checkGlError,
                    )
                }
                check(textures.remove(gpuOutput)) {
                    "Exported online MGC Spatial RGB texture is not owned by the stacker"
                }
                textureSpecs.remove(gpuOutput)
            }
            PLog.i(
                TAG,
                "MGC Spatial RGB online RAW uploads=${accumulator.rawUploadCount} " +
                    "bytes=${accumulator.rawUploadBytes} " +
                    "submit=${accumulator.rawUploadNs / 1_000_000L}ms " +
                    "frames=${accumulator.contributedFrames} drawBands=${accumulator.drawBands.size} " +
                    "gpuDeclaredBytes=$gpuDeclaredBytes " +
                    "projectedGpuBytes=${accumulator.projectedGpuBytes}",
            )
            return RgbMergeOutput(
                cpuBuffer = cpuOutput,
                gpuTexture = gpuOutput,
                diagnosticFixed16 = diagnosticFixed16,
                completionTimeline = completionTimeline,
            )
        } catch (throwable: Throwable) {
            completionTimeline?.releasePending()
            completionRecorder.releasePending()
            diagnosticStorage?.let { storage ->
                releasePixelPackBuffer(storage, "failed MGC Spatial online RGB Fixed16")
            }
            LargeDirectBuffer.free(cpuOutput)
            throw throwable
        }
    }

    private fun createRgbBandPlan(
        frames: List<RgbMergeFrame>,
        diagnosticCapture: StrengthCapture?,
        maximumBandHeight: Int,
    ): RgbBandPlan {
        val bands = MgcSpatialRgbTilePlanner.planHorizontalBands(
            outputWidth = outputWidth,
            outputHeight = outputHeight,
            maximumBandHeight = maximumBandHeight,
        )
        val work = bands.map { band ->
            band to frames.map { frame ->
                val sourceRegion = MgcSpatialRgbTilePlanner.sourceRegion(
                    tile = band,
                    rawWidth = width,
                    rawHeight = height,
                    outputWidth = outputWidth,
                    outputHeight = outputHeight,
                    flowBounds = frame.flowBounds,
                )
                RgbTileFrameRegion(
                    frame = frame,
                    sourceRegion = sourceRegion,
                    uploadRegion = expandRgbRawRegion(
                        sourceRegion,
                        RGB_CHROMA_GUIDE_RAW_RADIUS,
                    ),
                )
            }
        }
        val maximumOutputWidth = bands.maxOf { it.outputCore.width }
        val maximumOutputHeight = bands.maxOf { it.outputCore.height }
        val diagnosticPaddingWidth = diagnosticCapture?.let { capture ->
            capture.geometry.fixed16Width - outputWidth
        } ?: 0
        val diagnosticPaddingHeight = diagnosticCapture?.let { capture ->
            capture.geometry.fixed16Height - outputHeight
        } ?: 0
        val maximumDiagnosticWidth = bands.maxOf { band ->
            band.outputCore.width +
                if (band.outputCore.right == outputWidth) diagnosticPaddingWidth else 0
        }
        val maximumDiagnosticHeight = bands.maxOf { band ->
            band.outputCore.height +
                if (band.outputCore.bottom == outputHeight) diagnosticPaddingHeight else 0
        }
        val maximumSourceWidth = work.maxOf { (_, regions) ->
            regions.maxOf { it.sourceRegion.width }
        }
        val maximumSourceHeight = work.maxOf { (_, regions) ->
            regions.maxOf { it.sourceRegion.height }
        }
        val maximumUploadWidth = work.maxOf { (_, regions) ->
            regions.maxOf { it.uploadRegion.width }
        }
        val maximumUploadHeight = work.maxOf { (_, regions) ->
            regions.maxOf { it.uploadRegion.height }
        }
        val rawWindowBytes = maximumUploadWidth.toLong() * maximumUploadHeight *
            RAW_BYTES_PER_PIXEL * RGB_RAW_WINDOW_SLOTS
        val chromaGuideBytes = maximumSourceWidth.toLong() * maximumSourceHeight * 2L
        val accumulatorBytes = maximumOutputWidth.toLong() * maximumOutputHeight * 16L
        val outputStorageBytes = if (exportGpuLinearRgbSource) {
            outputWidth.toLong() * outputHeight * 8L
        } else {
            maximumOutputWidth.toLong() * maximumOutputHeight * 8L
        }
        val diagnosticTextureBytes = if (diagnosticCapture != null) {
            maximumDiagnosticWidth.toLong() * maximumDiagnosticHeight * 2L
        } else {
            0L
        }
        val diagnosticPboBytes = if (diagnosticCapture != null) {
            maximumDiagnosticWidth.toLong() * maximumDiagnosticHeight * 3L *
                Short.SIZE_BYTES * minOf(RGB_DIAGNOSTIC_PBO_SLOTS, bands.size)
        } else {
            0L
        }
        val projectedGpuBytes = estimatedOwnedTextureBytes() + rawWindowBytes +
            chromaGuideBytes + accumulatorBytes + outputStorageBytes +
            diagnosticTextureBytes + diagnosticPboBytes + RGB_TEXTURE_BUDGET_RESERVE_BYTES
        return RgbBandPlan(
            bands = bands,
            work = work,
            maximumOutputWidth = maximumOutputWidth,
            maximumOutputHeight = maximumOutputHeight,
            maximumDiagnosticWidth = maximumDiagnosticWidth,
            maximumDiagnosticHeight = maximumDiagnosticHeight,
            maximumSourceWidth = maximumSourceWidth,
            maximumSourceHeight = maximumSourceHeight,
            maximumUploadWidth = maximumUploadWidth,
            maximumUploadHeight = maximumUploadHeight,
            projectedGpuBytes = projectedGpuBytes,
        )
    }

    private fun renderRgbMerge(
        frames: List<RgbMergeFrame>,
        images: List<SafeImage>,
        outputExposureScale: Float,
        diagnosticCapture: StrengthCapture?,
    ): RgbMergeOutput {
        check(outputMode == MgcSpatialOutputMode.RGB)
        check(mergeRgbProgram != 0 && normalizeRgbProgram != 0)
        require(frames.isNotEmpty())
        require(frames.all { it.imageIndex in images.indices })
        require(outputExposureScale.isFinite() && outputExposureScale > 0f)
        diagnosticCapture?.let { capture ->
            check(capture.outputMode == MgcSpatialOutputMode.RGB)
            check(
                capture.geometry.imageWidth == outputWidth &&
                    capture.geometry.imageHeight == outputHeight
            ) {
                "MGC RGB diagnostic geometry ${capture.geometry.imageWidth}x" +
                    "${capture.geometry.imageHeight} does not match output ${outputWidth}x$outputHeight"
            }
        }
        val bandPlan = rgbBandHeightCandidates().asSequence()
            .map { maximumBandHeight ->
                createRgbBandPlan(
                    frames = frames,
                    diagnosticCapture = diagnosticCapture,
                    maximumBandHeight = maximumBandHeight,
                )
            }
            .firstOrNull { plan -> plan.projectedGpuBytes <= RGB_TEXTURE_BUDGET_BYTES }
            ?: error(
                "MGC Spatial RGB cannot fit reconstruction within " +
                    "$RGB_TEXTURE_BUDGET_BYTES bytes",
            )
        val bands = bandPlan.bands
        val work = bandPlan.work
        val maximumOutputWidth = bandPlan.maximumOutputWidth
        val maximumOutputHeight = bandPlan.maximumOutputHeight
        val maximumDiagnosticWidth = bandPlan.maximumDiagnosticWidth
        val maximumDiagnosticHeight = bandPlan.maximumDiagnosticHeight
        val maximumSourceWidth = bandPlan.maximumSourceWidth
        val maximumSourceHeight = bandPlan.maximumSourceHeight
        val maximumUploadWidth = bandPlan.maximumUploadWidth
        val maximumUploadHeight = bandPlan.maximumUploadHeight
        val rawBandTextures = List(RGB_RAW_WINDOW_SLOTS) {
            createTexture(
                maximumUploadWidth,
                maximumUploadHeight,
                GLES30.GL_R16UI,
                GLES30.GL_NEAREST,
            )
        }
        val chromaGuideRegionTexture = createTexture(
            maximumSourceWidth,
            maximumSourceHeight,
            GLES30.GL_R16F,
            GLES30.GL_NEAREST,
        )
        val semanticAccumulator = createTexture(
            maximumOutputWidth,
            maximumOutputHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        val opponentWeightAccumulator = createTexture(
            maximumOutputWidth,
            maximumOutputHeight,
            GLES30.GL_RGBA16F,
            GLES30.GL_NEAREST,
        )
        val lensShadingTexture = createLensShadingTexture()
        val gpuOutput = if (exportGpuLinearRgbSource) {
            createTexture(
                outputWidth,
                outputHeight,
                when (gpuLinearRgbStorage) {
                    GpuLinearRgbStorage.RGBA16UI -> GLES30.GL_RGBA16UI
                    GpuLinearRgbStorage.RGBA16F -> GLES30.GL_RGBA16F
                },
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val cpuTileOutput = if (gpuOutput == 0) {
            createTexture(
                maximumOutputWidth,
                maximumOutputHeight,
                GLES30.GL_RGBA16UI,
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val outputBytes = outputWidth.toLong() * outputHeight.toLong() * 3L * Short.SIZE_BYTES
        require(outputBytes <= Int.MAX_VALUE) {
            "MGC Spatial RGB CPU output is too large: $outputBytes bytes"
        }
        val cpuOutput = if (gpuOutput == 0) {
            LargeDirectBuffer.allocate(
                outputBytes,
                "MGC Spatial fused linear RGB16",
            )?.order(ByteOrder.nativeOrder()) ?: error(
                "Unable to allocate MGC Spatial RGB16 output",
            )
        } else {
            null
        }
        val tileReadback = if (cpuOutput != null) {
            ByteBuffer.allocateDirect(
                maximumOutputWidth * maximumOutputHeight * 4 * Short.SIZE_BYTES,
            ).order(ByteOrder.nativeOrder())
        } else {
            null
        }
        val diagnosticTexture = if (diagnosticCapture != null) {
            createTexture(
                maximumDiagnosticWidth,
                maximumDiagnosticHeight,
                GLES30.GL_R16I,
                GLES30.GL_NEAREST,
            )
        } else {
            0
        }
        val diagnosticFramebuffer = if (diagnosticCapture != null) createFramebuffer() else 0
        val diagnosticBandByteCount = (
            maximumDiagnosticWidth.toLong() * maximumDiagnosticHeight * 3L * Short.SIZE_BYTES
            ).also { bytes -> require(bytes in 1..Int.MAX_VALUE.toLong()) }
            .toInt()
        val diagnosticStorages = if (diagnosticCapture != null) {
            // A second slot only overlaps readback with useful work when another band exists.
            // Keeping one full-frame PBO makes the one-band fast path fit the same hard budget.
            List(minOf(RGB_DIAGNOSTIC_PBO_SLOTS, bands.size)) { slot ->
                allocatePixelPackBuffer(
                    diagnosticBandByteCount,
                    "MGC Spatial RGB Fixed16 band slot $slot",
                )
            }
        } else {
            emptyList()
        }
        val diagnosticHostBuffer = diagnosticCapture?.let { capture ->
            val byteCount = strengthFixed16ReadbackByteCount(capture)
            LargeDirectBuffer.allocate(
                byteCount.toLong(),
                "MGC Spatial RGB Fixed16 host source",
            )?.order(ByteOrder.nativeOrder()) ?: error(
                "Unable to allocate MGC Spatial RGB Fixed16 host source",
            )
        }
        val pendingDiagnosticBands = arrayOfNulls<PendingRgbDiagnosticBand>(
            diagnosticStorages.size,
        )
        if (diagnosticCapture != null) {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, diagnosticFramebuffer)
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,
                diagnosticTexture,
                0,
            )
            GLES30.glDrawBuffers(1, intArrayOf(GLES30.GL_COLOR_ATTACHMENT0), 0)
            val status = GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)
            check(status == GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "MGC RGB Fixed16 diagnostic framebuffer incomplete: 0x${status.toString(16)}"
            }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            applyRawRenderState()
            checkGlError("MGC Spatial RGB post-output diagnostic resources")
        }
        PLog.i(
            TAG,
            "MGC Spatial RGB streamed-raw " +
                "bands=${bands.size} rawWindowSlots=${rawBandTextures.size} " +
                "rawWindow=${maximumUploadWidth}x$maximumUploadHeight " +
                "rawWindowBytes=" +
                "${maximumUploadWidth.toLong() * maximumUploadHeight * RAW_BYTES_PER_PIXEL * rawBandTextures.size} " +
                "maxOutput=${maximumOutputWidth}x$maximumOutputHeight " +
                "maxChromaGuide=${maximumSourceWidth}x$maximumSourceHeight " +
                "frames=${frames.size} reconstruction=joint-G/R-G/B-G " +
                "chromaGuide=separate-pass diagnosticPack=${when {
                    diagnosticCapture == null -> "disabled"
                    diagnosticStorages.size == 1 -> "one-slot-band-pbo-to-host"
                    else -> "two-slot-band-pbo-to-host"
                }}",
        )
        var diagnosticSetupNs = 0L
        var diagnosticDispatchNs = 0L
        var rawBandUploadNs = 0L
        var rawBandUploadBytes = 0L
        var rawBandUploadCount = 0
        val passWindow = GlesGpuScheduler.PassWindow(
            tag = TAG,
            maxInFlight = RGB_MAX_IN_FLIGHT_PASSES,
        )
        val completionRecorder = GlesGpuCompletion.StackTimelineRecorder()
        var diagnosticStoragesReleased = false
        val gpuDeclaredBytes = estimatedOwnedTextureBytes() +
            diagnosticBandByteCount.toLong() * diagnosticStorages.size
        check(gpuDeclaredBytes <= RGB_TEXTURE_BUDGET_BYTES) {
            "MGC Spatial RGB allocated $gpuDeclaredBytes GPU bytes, " +
                "budget=$RGB_TEXTURE_BUDGET_BYTES"
        }
        PLog.i(
            TAG,
            "MGC Spatial RGB reconstruction textureBytes=${estimatedOwnedTextureBytes()} " +
                "diagnosticPboBytes=" +
                "${diagnosticBandByteCount.toLong() * diagnosticStorages.size} " +
                "diagnosticHostBytes=${diagnosticHostBuffer?.capacity() ?: 0} " +
                "gpuDeclaredBytes=$gpuDeclaredBytes " +
                "projectedGpuBytes=${bandPlan.projectedGpuBytes} " +
                "budgetBytes=$RGB_TEXTURE_BUDGET_BYTES " +
                "bandHeight=${bands.maxOf { it.outputCore.height }} " +
                "maxInFlight=$RGB_MAX_IN_FLIGHT_PASSES",
        )

        try {
            for ((band, frameRegions) in work) {
                val diagnosticSlotIndex = if (diagnosticStorages.isEmpty()) {
                    -1
                } else {
                    band.index % diagnosticStorages.size
                }
                if (diagnosticSlotIndex >= 0) {
                    pendingDiagnosticBands[diagnosticSlotIndex]?.let { pending ->
                        passWindow.awaitResources(
                            label = "MGC RGB diagnostic band ${pending.outputCore.top} host copy",
                            resources = longArrayOf(
                                GlesGpuScheduler.bufferResource(pending.storage.buffer),
                            ),
                        )
                        copyRgbFixed16BandToHost(
                            capture = checkNotNull(diagnosticCapture),
                            pending = pending,
                            destination = checkNotNull(diagnosticHostBuffer),
                        )
                        pendingDiagnosticBands[diagnosticSlotIndex] = null
                    }
                }
                frameRegions.forEachIndexed { framePosition, frameRegion ->
                    if (framePosition == 0) {
                        clearRgbAccumulators(
                            semanticAccumulator = semanticAccumulator,
                            opponentWeightAccumulator = opponentWeightAccumulator,
                            tileWidth = band.outputCore.width,
                            tileHeight = band.outputCore.height,
                        )
                    }
                    val rawBandTexture = rawBandTextures[framePosition % rawBandTextures.size]
                    val rawResource = GlesGpuScheduler.textureResource(rawBandTexture)
                    passWindow.beginPass(
                        label = "MGC RGB band ${band.index} frame $framePosition",
                        reads = longArrayOf(rawResource),
                        writes = longArrayOf(rawResource),
                    )
                    try {
                        val uploadStartNs = System.nanoTime()
                        uploadRawRegion(
                            image = images[frameRegion.frame.imageIndex],
                            texture = rawBandTexture,
                            region = frameRegion.uploadRegion,
                            label =
                                "RGB band ${band.index} frame ${frameRegion.frame.imageIndex}",
                        )
                        rawBandUploadNs += System.nanoTime() - uploadStartNs
                        rawBandUploadBytes += frameRegion.uploadRegion.width.toLong() *
                            frameRegion.uploadRegion.height * RAW_BYTES_PER_PIXEL
                        rawBandUploadCount += 1
                        renderRgbChromaGuide(
                            frame = frameRegion.frame,
                            rawTexture = rawBandTexture,
                            rawTextureOrigin = frameRegion.uploadRegion,
                            sourceRegion = frameRegion.sourceRegion,
                            outputTexture = chromaGuideRegionTexture,
                        )
                        renderRgbFrameContribution(
                            frame = frameRegion.frame,
                            rawTexture = rawBandTexture,
                            rawTextureOrigin = frameRegion.uploadRegion,
                            sourceRegion = frameRegion.sourceRegion,
                            outputCores = listOf(band.outputCore),
                            chromaGuideRegionTexture = chromaGuideRegionTexture,
                            semanticAccumulator = semanticAccumulator,
                            opponentWeightAccumulator = opponentWeightAccumulator,
                        )
                    } finally {
                        passWindow.endPass()
                    }
                }
                val diagnosticStorage = diagnosticSlotIndex.takeIf { it >= 0 }?.let {
                    diagnosticStorages[it]
                }
                passWindow.beginPass(
                    label = "MGC RGB band ${band.index} normalize",
                    writes = longArrayOf(
                        GlesGpuScheduler.bufferResource(diagnosticStorage?.buffer ?: 0),
                    ),
                )
                var pendingDiagnosticBand: PendingRgbDiagnosticBand? = null
                try {
                    val target = if (gpuOutput != 0) gpuOutput else cpuTileOutput
                    renderRgbNormalizedTile(
                        semanticAccumulator = semanticAccumulator,
                        opponentWeightAccumulator = opponentWeightAccumulator,
                        lensShadingTexture = lensShadingTexture,
                        outputCore = band.outputCore,
                        target = target,
                        targetIsFullOutput = gpuOutput != 0,
                        outputExposureScale = outputExposureScale,
                    )
                    GlesGpuScheduler.yieldToUiRenderer()
                    if (cpuOutput != null) {
                        readRgbTile(
                            texture = cpuTileOutput,
                            outputCore = band.outputCore,
                            readback = checkNotNull(tileReadback),
                            output = cpuOutput,
                        )
                    }
                    diagnosticCapture?.let { capture ->
                        // The production output for this band has already been submitted. The
                        // accumulator remains valid until the next band begins with an explicit
                        // clear, so pack diagnostics now without replaying any frame contribution.
                        val timing = packRgbFixed16TileReadback(
                            capture = capture,
                            semanticAccumulator = semanticAccumulator,
                            opponentWeightAccumulator = opponentWeightAccumulator,
                            outputCore = band.outputCore,
                            fixed16Texture = diagnosticTexture,
                            diagnosticFramebuffer = diagnosticFramebuffer,
                            storage = checkNotNull(diagnosticStorage),
                        )
                        diagnosticSetupNs += timing.setupNs
                        diagnosticDispatchNs += timing.dispatchNs
                        pendingDiagnosticBand = PendingRgbDiagnosticBand(
                            storage = diagnosticStorage,
                            outputCore = band.outputCore,
                            destinationHeight = timing.destinationHeight,
                            byteCount = timing.byteCount,
                        )
                    }
                } finally {
                    passWindow.endPass()
                }
                if (diagnosticSlotIndex >= 0) {
                    pendingDiagnosticBands[diagnosticSlotIndex] =
                        checkNotNull(pendingDiagnosticBand)
                }
            }
            pendingDiagnosticBands.forEachIndexed { slot, pending ->
                pending ?: return@forEachIndexed
                passWindow.awaitResources(
                    label = "MGC RGB final diagnostic band ${pending.outputCore.top} host copy",
                    resources = longArrayOf(
                        GlesGpuScheduler.bufferResource(pending.storage.buffer),
                    ),
                )
                copyRgbFixed16BandToHost(
                    capture = checkNotNull(diagnosticCapture),
                    pending = pending,
                    destination = checkNotNull(diagnosticHostBuffer),
                )
                pendingDiagnosticBands[slot] = null
            }
            diagnosticStorages.forEach { storage ->
                releasePixelPackBuffer(storage, "MGC Spatial RGB Fixed16 band slot")
            }
            diagnosticStoragesReleased = true
            PLog.i(
                TAG,
                "MGC Spatial RGB streamed RAW uploads=$rawBandUploadCount " +
                    "bytes=$rawBandUploadBytes submit=" +
                    "${rawBandUploadNs / 1_000_000L}ms slots=${rawBandTextures.size}",
            )
            cpuOutput?.rewind()
            val diagnosticFixed16 = diagnosticCapture?.let {
                checkGlError("MGC Spatial RGB Fixed16 diagnostic pack")
                PreparedTextureReadback(
                    byteCount = strengthFixed16ReadbackByteCount(it),
                    queuedGpuReadback = null,
                    cpuBuffer = checkNotNull(diagnosticHostBuffer),
                    mode = "${diagnosticStorages.size}-slot-band-pbo-host-rgb-planar-q14",
                    targetBindMs = diagnosticSetupNs / 1_000_000L,
                    readSubmitMs = diagnosticDispatchNs / 1_000_000L,
                    totalSubmitMs =
                        (diagnosticSetupNs + diagnosticDispatchNs) / 1_000_000L,
                )
            }
            val completionTimeline = if (gpuOutput != 0) {
                completionRecorder.mark(GpuStackCompletionStage.FINAL_EXPORT)
                completionRecorder.finish().also { timeline ->
                    if (timeline != null) {
                        passWindow.clearAfterCheckpoint()
                    } else {
                        passWindow.drain("MGC RGB final export without completion checkpoint")
                    }
                }
            } else {
                passWindow.drain("MGC RGB CPU output completion")
                null
            }
            if (gpuOutput != 0) {
                check(textures.remove(gpuOutput)) {
                    "Exported MGC Spatial RGB texture is not owned by the stacker"
                }
                textureSpecs.remove(gpuOutput)
            }
            return RgbMergeOutput(
                cpuBuffer = cpuOutput,
                gpuTexture = gpuOutput,
                diagnosticFixed16 = diagnosticFixed16,
                completionTimeline = completionTimeline,
            )
        } catch (throwable: Throwable) {
            completionRecorder.releasePending()
            passWindow.drain("MGC RGB reconstruction failure")
            if (!diagnosticStoragesReleased) {
                diagnosticStorages.forEach { storage ->
                    releasePixelPackBuffer(
                        storage,
                        "failed MGC Spatial RGB Fixed16 band slot",
                    )
                }
            }
            LargeDirectBuffer.free(diagnosticHostBuffer)
            LargeDirectBuffer.free(cpuOutput)
            throw throwable
        }
    }

    /**
     * Packs the isolated semantic merge accumulator before LSC and output-exposure scaling.
     * Applying only cameraDomainScale produces the normalized camera-RGB domain expected by
     * ComputeRgbNoiseModel; output noise coefficients are exposure-scaled once after the AOT.
     */
    private fun packRgbFixed16TileReadback(
        capture: StrengthCapture,
        semanticAccumulator: Int,
        opponentWeightAccumulator: Int,
        outputCore: MgcSpatialRgbRect,
        fixed16Texture: Int,
        diagnosticFramebuffer: Int,
        storage: PixelPackBuffer,
    ): RgbDiagnosticPackTiming {
        check(capture.outputMode == MgcSpatialOutputMode.RGB)
        check(
            packRgbFixed16FallbackProgram != 0 &&
                fixed16Texture != 0 &&
                diagnosticFramebuffer != 0
        )
        check(storage.buffer != 0)
        val imageWidth = capture.geometry.imageWidth
        val imageHeight = capture.geometry.imageHeight
        val fixed16Width = capture.geometry.fixed16Width
        val fixed16Height = capture.geometry.fixed16Height
        require(outputCore.right <= imageWidth && outputCore.bottom <= imageHeight)
        val destinationWidth = outputCore.width +
            if (outputCore.right == imageWidth) fixed16Width - imageWidth else 0
        val destinationHeight = outputCore.height +
            if (outputCore.bottom == imageHeight) fixed16Height - imageHeight else 0
        check(outputCore.left == 0 && destinationWidth == fixed16Width) {
            "RGB Fixed16 band packing requires full-width horizontal bands"
        }
        val rowBytes = destinationWidth.toLong() * Short.SIZE_BYTES
        val planeBytes = rowBytes * destinationHeight.toLong()
        val packedByteCount = (planeBytes * 3L)
            .also { bytes -> require(bytes in 1..storage.byteCount.toLong()) }
            .toInt()
        var setupNs = 0L
        var submitNs = 0L
        try {
            for (channel in 0 until 3) {
                val setupStartNs = System.nanoTime()
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, diagnosticFramebuffer)
                GLES30.glViewport(0, 0, destinationWidth, destinationHeight)
                GLES30.glDisable(GLES30.GL_BLEND)
                GLES30.glUseProgram(packRgbFixed16FallbackProgram)
                bindTexture(
                    packRgbFixed16FallbackProgram,
                    "uColorAndRWeight",
                    0,
                    semanticAccumulator,
                )
                bindTexture(
                    packRgbFixed16FallbackProgram,
                    "uGbWeights",
                    1,
                    opponentWeightAccumulator,
                )
                uniform1i(packRgbFixed16FallbackProgram, "uChannel", channel)
                uniform2i(
                    packRgbFixed16FallbackProgram,
                    "uSourceSize",
                    outputCore.width,
                    outputCore.height,
                )
                uniform3f(
                    packRgbFixed16FallbackProgram,
                    "uCameraDomainScale",
                    cameraDomainScale[0],
                    cameraDomainScale[1],
                    cameraDomainScale[2],
                )
                setupNs += System.nanoTime() - setupStartNs

                val submitStartNs = System.nanoTime()
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
                GLES30.glBindBuffer(
                    GLES30.GL_PIXEL_PACK_BUFFER,
                    storage.buffer,
                )
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, destinationWidth)
                val destinationOffset = channel.toLong() * planeBytes
                val destinationEnd =
                    destinationOffset +
                        (destinationHeight - 1L) * rowBytes +
                        destinationWidth.toLong() * Short.SIZE_BYTES
                check(
                    destinationOffset in 0..Int.MAX_VALUE.toLong() &&
                        destinationEnd <= storage.byteCount.toLong()
                )
                GLES30.glReadPixels(
                    0,
                    0,
                    destinationWidth,
                    destinationHeight,
                    GLES30.GL_RED_INTEGER,
                    GLES30.GL_SHORT,
                    destinationOffset.toInt(),
                )
                GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                submitNs += System.nanoTime() - submitStartNs
            }
        } finally {
            GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE1)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glUseProgram(0)
        }
        checkGlError("MGC Spatial RGB Fixed16 fallback pack $outputCore")
        return RgbDiagnosticPackTiming(
            setupNs = setupNs,
            dispatchNs = submitNs,
            byteCount = packedByteCount,
            destinationHeight = destinationHeight,
        )
    }

    private fun copyRgbFixed16BandToHost(
        capture: StrengthCapture,
        pending: PendingRgbDiagnosticBand,
        destination: ByteBuffer,
    ) {
        check(capture.outputMode == MgcSpatialOutputMode.RGB)
        check(pending.outputCore.left == 0)
        val fixed16Width = capture.geometry.fixed16Width
        val fixed16Height = capture.geometry.fixed16Height
        val rowBytes = fixed16Width * Short.SIZE_BYTES
        val sourcePlaneBytes = rowBytes * pending.destinationHeight
        val destinationPlaneBytes = rowBytes * fixed16Height
        check(pending.byteCount == sourcePlaneBytes * 3)
        check(destination.capacity() >= destinationPlaneBytes * 3)
        val mapped = mapPixelPackBuffer(
            pending.storage.buffer,
            pending.byteCount,
            "MGC Spatial RGB Fixed16 band top=${pending.outputCore.top}",
        )
        try {
            for (channel in 0 until 3) {
                val sourceOffset = channel * sourcePlaneBytes
                val destinationOffset =
                    channel * destinationPlaneBytes + pending.outputCore.top * rowBytes
                val source = mapped.duplicate().apply {
                    position(sourceOffset)
                    limit(sourceOffset + sourcePlaneBytes)
                }
                destination.duplicate().apply {
                    position(destinationOffset)
                    put(source)
                }
            }
        } finally {
            unmapPixelPackBuffer(pending.storage.buffer)
        }
    }

    private fun clearRgbAccumulators(
        semanticAccumulator: Int,
        opponentWeightAccumulator: Int,
        tileWidth: Int,
        tileHeight: Int,
    ) {
        bindRenderTargets(
            intArrayOf(semanticAccumulator, opponentWeightAccumulator),
            "MGC RGB accumulator clear",
        )
        GLES30.glViewport(0, 0, tileWidth, tileHeight)
        GLES30.glClearBufferfv(
            GLES30.GL_COLOR,
            0,
            floatArrayOf(0f, 0f, 0f, 0f),
            0,
        )
        GLES30.glClearBufferfv(
            GLES30.GL_COLOR,
            1,
            floatArrayOf(0f, 0f, 0f, 0f),
            0,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    private fun renderRgbFrameContribution(
        frame: RgbMergeFrame,
        rawTexture: Int,
        rawTextureOrigin: MgcSpatialRgbRect,
        sourceRegion: MgcSpatialRgbRect,
        outputCores: List<MgcSpatialRgbRect>,
        chromaGuideRegionTexture: Int,
        semanticAccumulator: Int,
        opponentWeightAccumulator: Int,
        accumulatorIsFullOutput: Boolean = false,
    ) {
        require(outputCores.isNotEmpty())
        GLES30.glUseProgram(mergeRgbProgram)
        bindTexture(mergeRgbProgram, "uRaw", 0, rawTexture)
        bindTexture(mergeRgbProgram, "uChromaGuideRegion", 1, chromaGuideRegionTexture)
        bindTexture(mergeRgbProgram, "uAlignment", 2, frame.alignmentTexture)
        bindTexture(mergeRgbProgram, "uFrameWeight", 3, frame.weightTexture)
        bindTexture(mergeRgbProgram, "uCovariance", 4, frame.covarianceTexture)
        uniform1f(
            mergeRgbProgram,
            "uGlobalFrameWeight",
            frame.calibration.globalFrameWeight,
        )
        uniform2i(mergeRgbProgram, "uRawSize", width, height)
        uniform2i(
            mergeRgbProgram,
            "uRawTextureOrigin",
            rawTextureOrigin.left,
            rawTextureOrigin.top,
        )
        uniform2i(
            mergeRgbProgram,
            "uRawRegionOrigin",
            sourceRegion.left,
            sourceRegion.top,
        )
        uniform2i(
            mergeRgbProgram,
            "uRawRegionSize",
            sourceRegion.width,
            sourceRegion.height,
        )
        uniform2i(mergeRgbProgram, "uOutputSize", outputWidth, outputHeight)
        uniform4f(
            mergeRgbProgram,
            "uCovRangeRg",
            COV_MIN_R,
            COV_MAX_R - COV_MIN_R,
            COV_MIN_G,
            COV_MAX_G - COV_MIN_G,
        )
        uniform2f(
            mergeRgbProgram,
            "uCovRangeB",
            COV_MIN_B,
            COV_MAX_B - COV_MIN_B,
        )
        uniform4fv(mergeRgbProgram, "uGains", frame.calibration.gains)
        uniform4fv(
            mergeRgbProgram,
            "uBlackLevelsTimesGains",
            frame.calibration.blackTerms,
        )
        uniform2f(
            mergeRgbProgram,
            "uGreenNoise",
            0.5f * (frame.calibration.shotNoise[1] + frame.calibration.shotNoise[2]),
            0.5f * (frame.calibration.readNoise[1] + frame.calibration.readNoise[2]),
        )
        uniform1f(
            mergeRgbProgram,
            "uChromaEdgeNoiseSigmas",
            RGB_CHROMA_EDGE_NOISE_SIGMAS,
        )
        uniform1f(
            mergeRgbProgram,
            "uChromaEdgeSigmaFloor",
            RGB_CHROMA_EDGE_SIGMA_FLOOR,
        )
        uniform1f(
            mergeRgbProgram,
            "uInterpolationFlowTolerance",
            SPATIAL_INTERPOLATION_FLOW_TOLERANCE,
        )
        uniform1i(mergeRgbProgram, "uCfaPattern", cfaPattern)
        uniform1i(
            mergeRgbProgram,
            "uUseFrameWeight",
            if (frame.useFrameWeight) 1 else 0,
        )
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            bindRenderTargets(
                intArrayOf(semanticAccumulator, opponentWeightAccumulator),
                "MGC RGB contributions",
            )
            outputCores.forEach { outputCore ->
                val accumulatorLeft = if (accumulatorIsFullOutput) outputCore.left else 0
                val accumulatorTop = if (accumulatorIsFullOutput) outputCore.top else 0
                uniform2i(
                    mergeRgbProgram,
                    "uOutputOrigin",
                    outputCore.left,
                    outputCore.top,
                )
                uniform2i(
                    mergeRgbProgram,
                    "uAccumulatorOrigin",
                    accumulatorLeft,
                    accumulatorTop,
                )
                GLES30.glViewport(
                    accumulatorLeft,
                    accumulatorTop,
                    outputCore.width,
                    outputCore.height,
                )
                GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
            }
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            checkGlError("MGC RGB contributions=${outputCores.size}")
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun renderRgbChromaGuide(
        frame: RgbMergeFrame,
        rawTexture: Int,
        rawTextureOrigin: MgcSpatialRgbRect,
        sourceRegion: MgcSpatialRgbRect,
        outputTexture: Int,
    ) {
        GLES30.glUseProgram(rgbChromaGuideProgram)
        bindTexture(rgbChromaGuideProgram, "uRaw", 0, rawTexture)
        uniform2i(rgbChromaGuideProgram, "uRawSize", width, height)
        uniform2i(
            rgbChromaGuideProgram,
            "uRawTextureOrigin",
            rawTextureOrigin.left,
            rawTextureOrigin.top,
        )
        uniform2i(
            rgbChromaGuideProgram,
            "uRegionOrigin",
            sourceRegion.left,
            sourceRegion.top,
        )
        uniform2i(
            rgbChromaGuideProgram,
            "uRegionSize",
            sourceRegion.width,
            sourceRegion.height,
        )
        uniform4fv(rgbChromaGuideProgram, "uGains", frame.calibration.gains)
        uniform4fv(
            rgbChromaGuideProgram,
            "uBlackLevelsTimesGains",
            frame.calibration.blackTerms,
        )
        uniform1i(rgbChromaGuideProgram, "uCfaPattern", cfaPattern)
        draw(
            rgbChromaGuideProgram,
            sourceRegion.width,
            sourceRegion.height,
            intArrayOf(outputTexture),
        )
    }

    private fun renderRgbNormalizedTile(
        semanticAccumulator: Int,
        opponentWeightAccumulator: Int,
        lensShadingTexture: Int,
        outputCore: MgcSpatialRgbRect,
        target: Int,
        targetIsFullOutput: Boolean,
        outputExposureScale: Float,
    ) {
        val targetLeft = if (targetIsFullOutput) outputCore.left else 0
        val targetTop = if (targetIsFullOutput) outputCore.top else 0
        bindRenderTargets(intArrayOf(target), "MGC RGB normalize tile ${outputCore.left},${outputCore.top}")
        GLES30.glViewport(targetLeft, targetTop, outputCore.width, outputCore.height)
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glUseProgram(normalizeRgbProgram)
        bindTexture(normalizeRgbProgram, "uColorAndRWeight", 0, semanticAccumulator)
        bindTexture(normalizeRgbProgram, "uGbWeights", 1, opponentWeightAccumulator)
        bindTexture(normalizeRgbProgram, "uLensShading", 2, lensShadingTexture)
        uniform2i(
            normalizeRgbProgram,
            "uAccumulatorSize",
            outputCore.width,
            outputCore.height,
        )
        uniform2i(normalizeRgbProgram, "uTargetOrigin", targetLeft, targetTop)
        uniform2i(
            normalizeRgbProgram,
            "uOutputOrigin",
            outputCore.left,
            outputCore.top,
        )
        uniform2i(normalizeRgbProgram, "uOutputSize", outputWidth, outputHeight)
        uniform3f(
            normalizeRgbProgram,
            "uCameraDomainScale",
            cameraDomainScale[0],
            cameraDomainScale[1],
            cameraDomainScale[2],
        )
        uniform1f(
            normalizeRgbProgram,
            "uOutputExposureScale",
            outputExposureScale,
        )
        uniform1i(normalizeRgbProgram, "uUseLensShading", if (hasLensShading()) 1 else 0)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("MGC Spatial RGB normalize tile $outputCore")
    }

    private fun readRgbTile(
        texture: Int,
        outputCore: MgcSpatialRgbRect,
        readback: ByteBuffer,
        output: ByteBuffer,
    ) {
        val byteCount = outputCore.width * outputCore.height * 4 * Short.SIZE_BYTES
        readback.clear()
        readback.limit(byteCount)
        bindRenderTargets(intArrayOf(texture), "MGC RGB tile readback")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        GLES30.glReadPixels(
            0,
            0,
            outputCore.width,
            outputCore.height,
            GLES30.GL_RGBA_INTEGER,
            GLES30.GL_UNSIGNED_SHORT,
            readback,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("MGC Spatial RGB tile readback $outputCore")
        readback.position(0)
        val source = readback.asShortBuffer()
        for (localY in 0 until outputCore.height) {
            for (localX in 0 until outputCore.width) {
                val sourceIndex = (localY * outputCore.width + localX) * 4
                val destinationPixel =
                    (outputCore.top + localY) * outputWidth + outputCore.left + localX
                val destinationByte = destinationPixel * 3 * Short.SIZE_BYTES
                output.putShort(destinationByte, source.get(sourceIndex))
                output.putShort(destinationByte + Short.SIZE_BYTES, source.get(sourceIndex + 1))
                output.putShort(destinationByte + 2 * Short.SIZE_BYTES, source.get(sourceIndex + 2))
            }
        }
    }

    private fun createLensShadingTexture(): Int {
        val valid = hasLensShading()
        val textureWidth = if (valid) lensShadingWidth else 1
        val textureHeight = if (valid) lensShadingHeight else 1
        val values = FloatArray(textureWidth * textureHeight * 4) { 1f }
        if (valid) {
            val source = checkNotNull(lensShading)
            for (index in values.indices) {
                values[index] = source[index]
                    .takeIf { it.isFinite() && it > 0f } ?: 1f
            }
        }
        return createFloatTexture(
            width = textureWidth,
            height = textureHeight,
            internalFormat = GLES30.GL_RGBA16F,
            format = GLES30.GL_RGBA,
            values = values,
            filter = GLES30.GL_LINEAR,
        )
    }

    private fun hasLensShading(): Boolean = lensShading != null &&
        lensShadingWidth > 0 &&
        lensShadingHeight > 0 &&
        lensShading.size >= lensShadingWidth * lensShadingHeight * 4

    private fun mapSpatialStrengthToOutputCoordinates(
        source: MgcSpatialStrengthMap,
    ): MgcSpatialStrengthMap {
        val targetWidth = ceilDiv(outputWidth, 4)
        val targetHeight = ceilDiv(outputHeight, 4)
        if (source.width == targetWidth && source.height == targetHeight) return source
        val startNs = System.nanoTime()
        val mapped = MgcSpatialStrengthMapScaler.scaleBilinear(
            source = source,
            targetWidth = targetWidth,
            targetHeight = targetHeight,
        )
        PLog.i(
            TAG,
            "MGC Spatial strength coordinates mapped ${source.width}x${source.height} -> " +
                "${targetWidth}x$targetHeight for ${normalizedOutputScale}x RGB output " +
                "backend=native-openmp took=" +
                "${(System.nanoTime() - startNs) / 1_000_000L}ms",
        )
        return mapped
    }

    private fun createNoiseLut(
        reference: FrameCalibration,
        current: FrameCalibration,
    ): Int {
        val values = FloatArray(NOISE_LUT_WIDTH * 2 * 4)
        val rows = arrayOf(reference, current)
        for (row in rows.indices) {
            val calibration = rows[row]
            for (x in 0 until NOISE_LUT_WIDTH) {
                val luma = (x + 0.5f) / NOISE_LUT_WIDTH.toFloat()
                val offset = (row * NOISE_LUT_WIDTH + x) * 4
                values[offset] =
                    calibration.shotNoise[0] * luma + calibration.readNoise[0]
                values[offset + 1] = 0.25f * (
                    calibration.shotNoise[1] * luma + calibration.readNoise[1] +
                        calibration.shotNoise[2] * luma + calibration.readNoise[2]
                    )
                values[offset + 2] =
                    calibration.shotNoise[3] * luma + calibration.readNoise[3]
                values[offset + 3] = 0f
            }
        }
        return createFloatTexture(
            width = NOISE_LUT_WIDTH,
            height = 2,
            internalFormat = GLES30.GL_RGBA16F,
            format = GLES30.GL_RGBA,
            values = values,
            filter = GLES30.GL_LINEAR,
        )
    }

    private fun createSabreNoiseLut(
        reference: FrameCalibration,
        current: FrameCalibration,
    ): Int {
        val values = MgcSabreNoiseEstimatesLut.create(
            referenceShotNoise = reference.shotNoise,
            referenceReadNoise = reference.readNoise,
            currentShotNoise = current.shotNoise,
            currentReadNoise = current.readNoise,
        )
        return createFloatTexture(
            width = MgcSabreNoiseEstimatesLut.WIDTH,
            height = MgcSabreNoiseEstimatesLut.ROWS,
            internalFormat = GLES30.GL_RGBA16F,
            format = GLES30.GL_RGBA,
            values = values,
            filter = GLES30.GL_LINEAR,
        )
    }

    private fun createZeroFlowTexture(): Int = createFloatTexture(
        width = 1,
        height = 1,
        internalFormat = GLES30.GL_RGBA16F,
        format = GLES30.GL_RGBA,
        values = floatArrayOf(0f, 0f, 0f, 0f),
        filter = GLES30.GL_NEAREST,
    )

    private fun createIdentityWeightTexture(): Int = createFloatTexture(
        width = 1,
        height = 1,
        internalFormat = GLES30.GL_R16F,
        format = GLES30.GL_RED,
        values = floatArrayOf(1f),
        filter = GLES30.GL_NEAREST,
    )

    private fun createZeroLinearKernelMaskTexture(): Int = createFloatTexture(
        width = 1,
        height = 1,
        internalFormat = GLES30.GL_R16F,
        format = GLES30.GL_RED,
        values = floatArrayOf(0f),
        filter = GLES30.GL_NEAREST,
    )

    private fun renderBayer16(
        accumulator: Int,
        outputExposureScale: Float,
    ): Int {
        require(outputExposureScale.isFinite() && outputExposureScale > 0f)
        val bayer16 = createTexture(
            width,
            height,
            GLES30.GL_R16UI,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(normalizeBayerProgram)
        bindTexture(normalizeBayerProgram, "uBayerAndWeight", 0, accumulator)
        uniform2i(normalizeBayerProgram, "uOutputSize", width, height)
        uniform1f(
            normalizeBayerProgram,
            "uOutputExposureScale",
            outputExposureScale,
        )
        draw(normalizeBayerProgram, width, height, intArrayOf(bayer16))
        return bayer16
    }

    private fun renderBayerFixed16Planes(accumulator: Int): Int {
        // The lifted AOT consumes complete 8x8 Bayer-quad tiles (16x16 sensor
        // pixels), including a clamped edge tile when the RAW size is odd.
        val quadWidth = ceilDiv(width, 16) * 8
        val quadHeight = ceilDiv(height, 16) * 8
        val packedHeight = quadHeight * 4
        val bayerFixed16 = createTexture(
            quadWidth,
            packedHeight,
            GLES30.GL_R16I,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(packBayerFixed16Program)
        bindTexture(packBayerFixed16Program, "uBayerAndWeight", 0, accumulator)
        uniform2i(
            packBayerFixed16Program,
            "uSourceSize",
            width,
            height,
        )
        uniform2i(
            packBayerFixed16Program,
            "uQuadSize",
            quadWidth,
            quadHeight,
        )
        draw(
            packBayerFixed16Program,
            quadWidth,
            packedHeight,
            intArrayOf(bayerFixed16),
        )
        return bayerFixed16
    }

    private fun readBayer16(bayer16: Int): ByteBuffer {
        val outputBytes = width.toLong() * height.toLong() * 2L
        val allocationStartNs = System.nanoTime()
        val output = LargeDirectBuffer.allocate(
            outputBytes,
            "MGC Spatial fused Bayer16",
        )?.order(ByteOrder.nativeOrder()) ?: throw IllegalStateException(
            "Unable to allocate MGC Spatial Bayer16 output",
        )
        val allocationMs = (System.nanoTime() - allocationStartNs) / 1_000_000L
        bindRenderTargets(intArrayOf(bayer16), "Bayer16 readback")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        val transferStartNs = System.nanoTime()
        GLES30.glReadPixels(
            0,
            0,
            width,
            height,
            GLES30.GL_RED_INTEGER,
            GLES30.GL_UNSIGNED_SHORT,
            output,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("MGC Spatial Bayer16 readback")
        output.rewind()
        PLog.i(
            TAG,
            "MGC Spatial Bayer16 CPU materialization " +
                "pixelTransfer=${(System.nanoTime() - transferStartNs) / 1_000_000L}ms " +
                "alloc=${allocationMs}ms",
        )
        return output
    }

    private fun uploadRaw(image: SafeImage, texture: Int, label: String) {
        /* IRIS_26547_SABRE_DISK_RAW_STREAM_UPLOAD
         * Night retains exactly one full RAW in native RAM. Every auxiliary is file-backed and is
         * materialized only for this single glTexSubImage2D call, then FileRegion.close() frees the
         * temporary native buffer before the next frame begins. Motion's in-memory path is unchanged.
         */
        if (image.isFileBacked) {
            val region = image.readFileRegion(0, 0, width, height)
            try {
                uploadRawBuffer(
                    buffer = region.buffer,
                    rowStride = region.rowStride,
                    pixelStride = region.pixelStride,
                    texture = texture,
                    label = "$label disk-backed",
                )
            } finally {
                region.close()
            }
            return
        }
        val plane = image.planes.firstOrNull()
            ?: throw IllegalArgumentException("$label has no RAW plane")
        uploadRawBuffer(
            buffer = plane.buffer,
            rowStride = plane.rowStride,
            pixelStride = plane.pixelStride,
            texture = texture,
            label = label,
        )
    }

    private fun uploadRawBuffer(
        buffer: ByteBuffer,
        rowStride: Int,
        pixelStride: Int,
        texture: Int,
        label: String,
    ) {
        require(pixelStride == RAW_BYTES_PER_PIXEL) {
            "$label RAW pixel stride=$pixelStride, expected 2"
        }
        require(rowStride >= width * RAW_BYTES_PER_PIXEL) {
            "$label RAW row stride=$rowStride is smaller than width=$width"
        }
        require(rowStride % RAW_BYTES_PER_PIXEL == 0) {
            "$label RAW row stride is not 16-bit aligned"
        }
        val upload = buffer.duplicate().order(ByteOrder.nativeOrder())
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, rowStride / RAW_BYTES_PER_PIXEL)
        try {
            GLES30.glTexSubImage2D(
                GLES30.GL_TEXTURE_2D,
                0,
                0,
                0,
                width,
                height,
                GLES30.GL_RED_INTEGER,
                GLES30.GL_UNSIGNED_SHORT,
                upload,
            )
        } finally {
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, 0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        }
        checkGlError("upload $label")
    }

    private fun uploadRawRegion(
        image: SafeImage,
        texture: Int,
        region: MgcSpatialRgbRect,
        label: String,
    ) {
        require(region.right <= width && region.bottom <= height)
        val plane = image.planes.firstOrNull()
            ?: throw IllegalArgumentException("$label has no RAW plane")
        require(plane.pixelStride == RAW_BYTES_PER_PIXEL) {
            "$label RAW pixel stride=${plane.pixelStride}, expected 2"
        }
        require(plane.rowStride >= width * RAW_BYTES_PER_PIXEL) {
            "$label RAW row stride=${plane.rowStride} is smaller than width=$width"
        }
        require(plane.rowStride % RAW_BYTES_PER_PIXEL == 0) {
            "$label RAW row stride is not 16-bit aligned"
        }
        val buffer = plane.buffer.duplicate().order(ByteOrder.nativeOrder())
        val sourceOffset = buffer.position().toLong() +
            region.top.toLong() * plane.rowStride +
            region.left.toLong() * RAW_BYTES_PER_PIXEL
        val sourceEnd = sourceOffset +
            (region.height - 1L) * plane.rowStride +
            region.width.toLong() * RAW_BYTES_PER_PIXEL
        require(sourceOffset in 0..Int.MAX_VALUE.toLong() && sourceEnd <= buffer.limit()) {
            "$label RAW region=$region exceeds plane buffer limit=${buffer.limit()}"
        }
        buffer.position(sourceOffset.toInt())
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
        GLES30.glPixelStorei(
            GLES30.GL_UNPACK_ROW_LENGTH,
            plane.rowStride / RAW_BYTES_PER_PIXEL,
        )
        GLES30.glTexSubImage2D(
            GLES30.GL_TEXTURE_2D,
            0,
            0,
            0,
            region.width,
            region.height,
            GLES30.GL_RED_INTEGER,
            GLES30.GL_UNSIGNED_SHORT,
            buffer,
        )
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("upload $label region=$region")
    }

    private fun expandRgbRawRegion(
        region: MgcSpatialRgbRect,
        radius: Int,
    ): MgcSpatialRgbRect {
        require(radius >= 0)
        return MgcSpatialRgbRect(
            left = max(0, region.left - radius),
            top = max(0, region.top - radius),
            right = minOf(width, region.right + radius),
            bottom = minOf(height, region.bottom + radius),
        )
    }

    private fun createTexture(
        textureWidth: Int,
        textureHeight: Int,
        internalFormat: Int,
        filter: Int,
    ): Int {
        val spec = TextureSpec(
            width = textureWidth,
            height = textureHeight,
            internalFormat = internalFormat,
            filter = filter,
        )
        val scratchTextures = activeSequentialScratchTextures
        return if (scratchTextures != null) {
            scratchTextures.acquire(spec) { allocateTexture(spec) }
        } else {
            allocateTexture(spec)
        }
    }

    private fun allocateTexture(spec: TextureSpec): Int {
        val ids = IntArray(1)
        GLES30.glGenTextures(1, ids, 0)
        val texture = ids[0]
        check(texture != 0) { "glGenTextures returned 0" }
        textures += texture
        textureSpecs[texture] = spec
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_MIN_FILTER,
            spec.filter,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_MAG_FILTER,
            spec.filter,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_WRAP_S,
            GLES30.GL_CLAMP_TO_EDGE,
        )
        GLES30.glTexParameteri(
            GLES30.GL_TEXTURE_2D,
            GLES30.GL_TEXTURE_WRAP_T,
            GLES30.GL_CLAMP_TO_EDGE,
        )
        GLES30.glTexStorage2D(
            GLES30.GL_TEXTURE_2D,
            1,
            spec.internalFormat,
            spec.width,
            spec.height,
        )
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("create texture ${spec.width}x${spec.height}")
        return texture
    }

    private fun createFloatTexture(
        width: Int,
        height: Int,
        internalFormat: Int,
        format: Int,
        values: FloatArray,
        filter: Int,
    ): Int {
        val buffer = ByteBuffer.allocateDirect(values.size * Float.SIZE_BYTES)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .apply {
                put(values)
                rewind()
            }
        val texture = createTexture(
            textureWidth = width,
            textureHeight = height,
            internalFormat = internalFormat,
            filter = filter,
        )
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glTexSubImage2D(
            GLES30.GL_TEXTURE_2D,
            0,
            0,
            0,
            width,
            height,
            format,
            GLES30.GL_FLOAT,
            buffer,
        )
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        checkGlError("create float texture ${width}x$height")
        return texture
    }

    private fun createFramebuffer(): Int {
        val ids = IntArray(1)
        GLES30.glGenFramebuffers(1, ids, 0)
        check(ids[0] != 0) { "glGenFramebuffers returned 0" }
        framebuffers += ids[0]
        return ids[0]
    }

    /** Copies a scratch result into storage that survives the next sequential temporal frame. */
    private fun copyPersistentTexture(
        source: Int,
        textureWidth: Int,
        textureHeight: Int,
        internalFormat: Int,
        filter: Int,
        label: String,
    ): Int {
        val destination = allocateTexture(
            TextureSpec(
                width = textureWidth,
                height = textureHeight,
                internalFormat = internalFormat,
                filter = filter,
            ),
        )
        bindRenderTargets(intArrayOf(source), "$label source")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, destination)
        GLES30.glCopyTexSubImage2D(
            GLES30.GL_TEXTURE_2D,
            0,
            0,
            0,
            0,
            0,
            textureWidth,
            textureHeight,
        )
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError(label)
        return destination
    }

    private fun beginTemporalScratchFrame() {
        check(activeSequentialScratchTextures == null) {
            "Temporal scratch frame overlap is not supported"
        }
        temporalScratchTextures.begin()
        activeSequentialScratchTextures = temporalScratchTextures
    }

    private fun endTemporalScratchFrame() {
        check(activeSequentialScratchTextures === temporalScratchTextures) {
            "Ending a Spatial temporal scratch frame that is not active"
        }
        activeSequentialScratchTextures = null
        temporalScratchTextures.end()
    }

    private fun releaseTexturesFrom(startIndex: Int) {
        if (startIndex >= textures.size) return
        val count = textures.size - startIndex
        val transientTextures = IntArray(count) { offset -> textures[startIndex + offset] }
        GLES30.glDeleteTextures(count, transientTextures, 0)
        transientTextures.forEach(textureSpecs::remove)
        repeat(count) { textures.removeAt(textures.lastIndex) }
    }

    private fun releaseTexturesFromExcept(
        startIndex: Int,
        retainedTextures: IntArray,
    ) {
        if (startIndex >= textures.size) return
        val retained = retainedTextures.toHashSet()
        val toDelete = textures.subList(startIndex, textures.size)
            .filterNot { it in retained }
            .toIntArray()
        if (toDelete.isNotEmpty()) {
            GLES30.glDeleteTextures(toDelete.size, toDelete, 0)
            toDelete.forEach(textureSpecs::remove)
        }
        for (index in textures.lastIndex downTo startIndex) {
            if (textures[index] !in retained) textures.removeAt(index)
        }
    }

    private fun draw(
        program: Int,
        viewportWidth: Int,
        viewportHeight: Int,
        targets: IntArray,
        preserveBlend: Boolean = false,
    ) {
        bindRenderTargets(targets, "program $program")
        GLES30.glViewport(0, 0, viewportWidth, viewportHeight)
        if (!preserveBlend) GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glUseProgram(program)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("draw program $program")
    }

    private fun releaseOwnedTexture(texture: Int, label: String) {
        if (texture == 0) return
        check(textures.remove(texture)) { "$label texture=$texture is not owned" }
        textureSpecs.remove(texture)
        GLES30.glDeleteTextures(1, intArrayOf(texture), 0)
        checkGlError("release $label")
    }

    /**
     * Closes the temporal resource arena before allocating the full RGB output and band storage.
     *
     * The caller supplies the complete texture contract consumed by the selected RGB path.
     * Waiting once at this phase boundary allows the driver to reclaim every other temporal
     * texture instead of overlapping deferred deletion with final output allocation.
     */
    private fun releaseRgbTemporalPhaseResources(
        persistentTextures: IntArray,
        strengthCapture: StrengthCapture?,
    ) {
        check(activeSequentialScratchTextures == null) {
            "RGB temporal resources cannot be released during an active scratch frame"
        }
        val retained = HashSet<Int>(persistentTextures.size + 2)
        persistentTextures.forEach(retained::add)
        strengthCapture?.let { capture ->
            retained += capture.alignmentAtlas
            retained += capture.rejectionAtlas
        }
        retained.remove(0)
        check(retained.all(textures::contains)) {
            "RGB persistent temporal resource is not owned by the stacker"
        }

        val beforeBytes = estimatedOwnedTextureBytes()
        val waitMs = GlesGpuCompletion.awaitSubmittedWork(
            label = "MGC Spatial RGB temporal resource handoff",
            checkGlError = ::checkGlError,
        )
        detachRenderTargets()
        val releasedTextures = textures.filterNot(retained::contains).toIntArray()
        val releasedBytes = estimatedTextureBytes(releasedTextures)
        if (releasedTextures.isNotEmpty()) {
            GLES30.glDeleteTextures(releasedTextures.size, releasedTextures, 0)
            releasedTextures.forEach { texture ->
                check(textures.remove(texture))
                textureSpecs.remove(texture)
            }
        }
        temporalScratchTextures.clearTracking()
        checkGlError("release MGC Spatial RGB temporal resource arena")
        PLog.i(
            TAG,
            "MGC Spatial RGB temporal arena released textures=${releasedTextures.size} " +
                "releasedBytes=$releasedBytes retainedTextures=${retained.size} " +
                "retainedBytes=${estimatedOwnedTextureBytes()} beforeBytes=$beforeBytes " +
                "gpuWait=${waitMs}ms",
        )
    }

    /** Moves strength atlases out of GL storage before the full-resolution RGB output exists. */
    private fun materializeRgbStrengthAtlases(
        capture: StrengthCapture,
    ): Pair<PreparedTextureReadback, PreparedTextureReadback> {
        check(capture.outputMode == MgcSpatialOutputMode.RGB)
        var alignmentHost: PreparedTextureReadback? = null
        var rejectionHost: PreparedTextureReadback? = null
        return try {
            alignmentHost = materializePreparedReadbackToHost(
                prepared = queuePreparedTextureReadback(
                    texture = capture.alignmentAtlas,
                    textureWidth = capture.alignmentLayout.atlasWidth,
                    textureHeight = capture.alignmentLayout.atlasHeight,
                    encoding = StrengthReadbackEncoding.FLOAT32,
                    byteCount = strengthAlignmentReadbackByteCount(capture),
                    label = "MGC Spatial RGB strength alignment atlas",
                    atlasLayout = capture.alignmentLayout,
                ),
                label = "MGC Spatial RGB strength alignment host",
            )
            detachRenderTargets()
            releaseOwnedTexture(capture.alignmentAtlas, "RGB strength alignment atlas")

            rejectionHost = materializePreparedReadbackToHost(
                prepared = queuePreparedTextureReadback(
                    texture = capture.rejectionAtlas,
                    textureWidth = capture.rejectionLayout.atlasWidth,
                    textureHeight = capture.rejectionLayout.atlasHeight,
                    encoding = StrengthReadbackEncoding.UNORM8,
                    byteCount = strengthRejectionReadbackByteCount(capture),
                    label = "MGC Spatial RGB strength rejection atlas",
                    atlasLayout = capture.rejectionLayout,
                ),
                label = "MGC Spatial RGB strength rejection host",
            )
            detachRenderTargets()
            releaseOwnedTexture(capture.rejectionAtlas, "RGB strength rejection atlas")
            checkNotNull(alignmentHost) to checkNotNull(rejectionHost)
        } catch (throwable: Throwable) {
            LargeDirectBuffer.free(alignmentHost?.cpuBuffer)
            LargeDirectBuffer.free(rejectionHost?.cpuBuffer)
            throw throwable
        }
    }

    /**
     * Resolves the small persistent alignment grids once after temporal completion. Exact bounds
     * avoid replaying hundreds of unused RAW halo rows for every reconstruction band.
     */
    private fun resolveRgbFlowBounds(frames: List<RgbMergeFrame>): List<RgbMergeFrame> {
        val byteCount = bayerAlignmentWidth.toLong() * bayerAlignmentHeight * 4L * Float.SIZE_BYTES
        require(byteCount in 1..Int.MAX_VALUE.toLong())
        val readback = ByteBuffer.allocateDirect(byteCount.toInt()).order(ByteOrder.nativeOrder())
        return frames.map { frame ->
            if (frame.flowBounds == MgcSpatialRgbFlowBounds.Zero) {
                frame
            } else {
                bindRenderTargets(
                    intArrayOf(frame.alignmentTexture),
                    "MGC RGB alignment bounds frame ${frame.imageIndex}",
                )
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, Float.SIZE_BYTES)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
                readback.clear()
                GLES30.glReadPixels(
                    0,
                    0,
                    bayerAlignmentWidth,
                    bayerAlignmentHeight,
                    GLES30.GL_RGBA,
                    GLES30.GL_FLOAT,
                    readback,
                )
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                checkGlError("read MGC RGB alignment bounds frame ${frame.imageIndex}")
                val values = readback.asFloatBuffer()
                var minimumX = Float.POSITIVE_INFINITY
                var minimumY = Float.POSITIVE_INFINITY
                var maximumX = Float.NEGATIVE_INFINITY
                var maximumY = Float.NEGATIVE_INFINITY
                for (pixel in 0 until bayerAlignmentWidth * bayerAlignmentHeight) {
                    val x = values.get(pixel * 4)
                    val y = values.get(pixel * 4 + 1)
                    check(x.isFinite() && y.isFinite()) {
                        "MGC RGB alignment frame ${frame.imageIndex} contains non-finite flow"
                    }
                    minimumX = minOf(minimumX, x)
                    minimumY = minOf(minimumY, y)
                    maximumX = maxOf(maximumX, x)
                    maximumY = maxOf(maximumY, y)
                }
                val bounds = MgcSpatialRgbFlowBounds(
                    minX = minimumX,
                    minY = minimumY,
                    maxX = maximumX,
                    maxY = maximumY,
                )
                check(
                    bounds.minX >= conservativeRgbFlowBounds.minX &&
                        bounds.minY >= conservativeRgbFlowBounds.minY &&
                        bounds.maxX <= conservativeRgbFlowBounds.maxX &&
                        bounds.maxY <= conservativeRgbFlowBounds.maxY
                ) {
                    "MGC RGB alignment frame ${frame.imageIndex} exceeds analytical bounds: " +
                        "$bounds expected=$conservativeRgbFlowBounds"
                }
                PLog.d(TAG, "MGC RGB flow bounds frame=${frame.imageIndex} $bounds")
                frame.copy(flowBounds = bounds)
            }
        }.also {
            detachRenderTargets()
        }
    }

    private fun detachRenderTargets() {
        if (renderFbo == 0 || renderTargetAttachmentCount == 0) return
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, renderFbo)
        for (index in 0 until renderTargetAttachmentCount) {
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0 + index,
                GLES30.GL_TEXTURE_2D,
                0,
                0,
            )
        }
        renderTargetAttachmentCount = 0
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    private fun estimatedOwnedTextureBytes(): Long =
        textureSpecs.values.sumOf(::estimatedTextureBytes)

    private fun estimatedTextureBytes(textures: IntArray): Long = textures.sumOf { texture ->
        textureSpecs[texture]?.let(::estimatedTextureBytes) ?: 0L
    }

    private fun estimatedTextureBytes(spec: TextureSpec): Long {
        val bytesPerPixel = when (spec.internalFormat) {
            GLES30.GL_R8 -> 1
            GLES30.GL_R16F,
            GLES30.GL_R16I,
            GLES30.GL_R16UI -> 2
            GLES30.GL_R32F,
            GLES30.GL_RGB10_A2 -> 4
            GLES30.GL_RGB16UI -> 6
            GLES30.GL_RGBA16F,
            GLES30.GL_RGBA16UI -> 8
            GLES30.GL_RGBA32F -> 16
            else -> error(
                "Missing MGC texture byte size for format=0x" +
                    spec.internalFormat.toString(16),
            )
        }
        return spec.width.toLong() * spec.height * bytesPerPixel
    }

    private fun drawRegion(
        program: Int,
        target: Int,
        viewportLeft: Int,
        viewportTop: Int,
        viewportWidth: Int,
        viewportHeight: Int,
    ) {
        bindRenderTargets(intArrayOf(target), "program $program region")
        GLES30.glViewport(
            viewportLeft,
            viewportTop,
            viewportWidth,
            viewportHeight,
        )
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glUseProgram(program)
        GLES30.glDrawArrays(GLES30.GL_TRIANGLES, 0, 3)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("draw program $program region")
    }

    private fun bindRenderTargets(targets: IntArray, label: String) {
        require(targets.isNotEmpty())
        val targetSpecs = targets.map { texture ->
            checkNotNull(textureSpecs[texture]) {
                "$label target texture $texture is not owned by the Spatial stacker"
            }
        }
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, renderFbo)
        val attachments = IntArray(targets.size)
        for (index in targets.indices) {
            val attachment = GLES30.GL_COLOR_ATTACHMENT0 + index
            attachments[index] = attachment
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                attachment,
                GLES30.GL_TEXTURE_2D,
                targets[index],
                0,
            )
        }
        // A framebuffer retains attachments that are not explicitly replaced. Bento writes three
        // half-resolution masks, while the following SpatialMerge draw writes two full-resolution
        // accumulators. Leaving COLOR_ATTACHMENT2 attached makes the framebuffer dimensions the
        // intersection of both sizes on Adreno, clipping the merge to one quarter of the image.
        for (index in targets.size until renderTargetAttachmentCount) {
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0 + index,
                GLES30.GL_TEXTURE_2D,
                0,
                0,
            )
        }
        renderTargetAttachmentCount = targets.size
        GLES30.glDrawBuffers(attachments.size, attachments, 0)
        // Completeness is a property of these immutable attachment specifications. Validate each
        // format/size combination once instead of forcing driver validation in every hot pass.
        if (validatedRenderTargetSpecs.add(targetSpecs)) {
            val status = GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)
            check(status == GLES30.GL_FRAMEBUFFER_COMPLETE) {
                "$label framebuffer incomplete: 0x${status.toString(16)}"
            }
        }
    }

    private fun bindTexture(program: Int, name: String, unit: Int, texture: Int) {
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + unit)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glUniform1i(uniformLocation(program, name), unit)
    }

    private fun uniform1i(program: Int, name: String, value: Int) {
        GLES30.glUniform1i(uniformLocation(program, name), value)
    }

    private fun uniform1f(program: Int, name: String, value: Float) {
        GLES30.glUniform1f(uniformLocation(program, name), value)
    }

    private fun uniform1fv(program: Int, name: String, value: FloatArray) {
        GLES30.glUniform1fv(
            uniformLocation(program, name),
            value.size,
            value,
            0,
        )
    }

    private fun uniform2i(program: Int, name: String, x: Int, y: Int) {
        GLES30.glUniform2i(uniformLocation(program, name), x, y)
    }

    private fun uniform2f(program: Int, name: String, x: Float, y: Float) {
        GLES30.glUniform2f(uniformLocation(program, name), x, y)
    }

    private fun uniform3f(program: Int, name: String, x: Float, y: Float, z: Float) {
        GLES30.glUniform3f(uniformLocation(program, name), x, y, z)
    }

    private fun uniform4f(
        program: Int,
        name: String,
        x: Float,
        y: Float,
        z: Float,
        w: Float,
    ) {
        GLES30.glUniform4f(uniformLocation(program, name), x, y, z, w)
    }

    private fun uniform4fv(program: Int, name: String, value: FloatArray) {
        GLES30.glUniform4fv(uniformLocation(program, name), 1, value, 0)
    }

    private fun uniformLocation(program: Int, name: String): Int {
        val locations = uniformLocations.getOrPut(program) { HashMap() }
        return locations.getOrPut(name) { GLES30.glGetUniformLocation(program, name) }
    }

    private fun linkProgram(fragmentSource: String, name: String): Int {
        val vertexSource = GlesGraphicsShaderSources.fullscreenVertexFor(fragmentSource)
        val vertex = compileShader(GLES30.GL_VERTEX_SHADER, vertexSource, "$name vertex")
        val fragment = compileShader(GLES30.GL_FRAGMENT_SHADER, fragmentSource, "$name fragment")
        val program = GLES30.glCreateProgram()
        GLES30.glAttachShader(program, vertex)
        GLES30.glAttachShader(program, fragment)
        GLES30.glLinkProgram(program)
        GLES30.glDeleteShader(vertex)
        GLES30.glDeleteShader(fragment)
        val status = IntArray(1)
        GLES30.glGetProgramiv(program, GLES30.GL_LINK_STATUS, status, 0)
        if (status[0] == 0) {
            val log = GLES30.glGetProgramInfoLog(program)
            GLES30.glDeleteProgram(program)
            throw IllegalStateException("$name link failed: $log")
        }
        programs += program
        return program
    }

    private fun linkComputeProgram(source: String, name: String): Int {
        GlesComputeWorkGroup.requireBaselineCompatible(source, name)
        val shader = compileShader(GLES31.GL_COMPUTE_SHADER, source, "$name compute")
        val program = GLES31.glCreateProgram()
        GLES31.glAttachShader(program, shader)
        GLES31.glLinkProgram(program)
        GLES31.glDeleteShader(shader)
        val status = IntArray(1)
        GLES31.glGetProgramiv(program, GLES31.GL_LINK_STATUS, status, 0)
        if (status[0] == 0) {
            val log = GLES31.glGetProgramInfoLog(program)
            GLES31.glDeleteProgram(program)
            throw IllegalStateException("$name link failed: $log")
        }
        programs += program
        return program
    }

    private fun compileShader(type: Int, source: String, name: String): Int {
        val shader = GLES30.glCreateShader(type)
        GLES30.glShaderSource(shader, source)
        GLES30.glCompileShader(shader)
        val status = IntArray(1)
        GLES30.glGetShaderiv(shader, GLES30.GL_COMPILE_STATUS, status, 0)
        if (status[0] == 0) {
            val log = GLES30.glGetShaderInfoLog(shader)
            GLES30.glDeleteShader(shader)
            throw IllegalStateException("$name compile failed: $log")
        }
        return shader
    }

    private fun initEgl() {
        ownsEglContext = true
        eglDisplay = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
        check(eglDisplay != EGL14.EGL_NO_DISPLAY) { "eglGetDisplay failed" }
        val version = IntArray(2)
        check(EGL14.eglInitialize(eglDisplay, version, 0, version, 1)) {
            "eglInitialize failed: ${EGL14.eglGetError()}"
        }
        val config = chooseConfig(EGL_OPENGL_ES3_BIT_KHR)
            ?: chooseConfig(EGL14.EGL_OPENGL_ES2_BIT)
            ?: throw IllegalStateException("No EGL config for GLES3")
        eglContext = GlesGpuScheduler.createBackgroundContext(eglDisplay, config, TAG)
        check(eglContext != EGL14.EGL_NO_CONTEXT) {
            "eglCreateContext failed: ${EGL14.eglGetError()}"
        }
        eglSurface = EGL14.eglCreatePbufferSurface(
            eglDisplay,
            config,
            intArrayOf(
                EGL14.EGL_WIDTH,
                1,
                EGL14.EGL_HEIGHT,
                1,
                EGL14.EGL_NONE,
            ),
            0,
        )
        check(eglSurface != EGL14.EGL_NO_SURFACE) {
            "eglCreatePbufferSurface failed: ${EGL14.eglGetError()}"
        }
        check(EGL14.eglMakeCurrent(eglDisplay, eglSurface, eglSurface, eglContext)) {
            "eglMakeCurrent failed: ${EGL14.eglGetError()}"
        }
    }

    private fun attachCurrentEgl() {
        eglDisplay = EGL14.eglGetCurrentDisplay()
        eglContext = EGL14.eglGetCurrentContext()
        eglSurface = EGL14.eglGetCurrentSurface(EGL14.EGL_DRAW)
        ownsEglContext = false
        check(eglDisplay != EGL14.EGL_NO_DISPLAY) { "No current EGL display" }
        check(eglContext != EGL14.EGL_NO_CONTEXT) { "No current EGL context" }
        check(eglSurface != EGL14.EGL_NO_SURFACE) { "No current EGL draw surface" }
    }

    private fun chooseConfig(renderableType: Int): EGLConfig? {
        val attributes = intArrayOf(
            EGL14.EGL_RED_SIZE,
            8,
            EGL14.EGL_GREEN_SIZE,
            8,
            EGL14.EGL_BLUE_SIZE,
            8,
            EGL14.EGL_ALPHA_SIZE,
            8,
            EGL14.EGL_RENDERABLE_TYPE,
            renderableType,
            EGL14.EGL_SURFACE_TYPE,
            EGL14.EGL_PBUFFER_BIT,
            EGL14.EGL_NONE,
        )
        val configurations = arrayOfNulls<EGLConfig>(1)
        val count = IntArray(1)
        return if (
            EGL14.eglChooseConfig(
                eglDisplay,
                attributes,
                0,
                configurations,
                0,
                configurations.size,
                count,
                0,
            ) && count[0] > 0
        ) {
            configurations[0]
        } else {
            null
        }
    }

    private fun ensureGles3() {
        val version = GLES30.glGetString(GLES30.GL_VERSION).orEmpty()
        check(version.contains("OpenGL ES 3.")) {
            "MGC Spatial merge requires GLES3, got: $version"
        }
        maxShaderStorageBlockBytes = 0L
        maxComputePackGroupsX = 0
        maxComputePackGroupsY = 0
        supportsComputeReadback = version.contains("OpenGL ES 3.1") ||
            version.contains("OpenGL ES 3.2")
        if (supportsComputeReadback) {
            val maximumBlockSize = LongArray(1)
            GLES30.glGetInteger64v(
                GLES31.GL_MAX_SHADER_STORAGE_BLOCK_SIZE,
                maximumBlockSize,
                0,
            )
            val queryError = GLES30.glGetError()
            if (queryError == GLES30.GL_NO_ERROR && maximumBlockSize[0] > 0L) {
                maxShaderStorageBlockBytes = maximumBlockSize[0]
                val maximumGroupCount = IntArray(2)
                GLES31.glGetIntegeri_v(
                    GLES31.GL_MAX_COMPUTE_WORK_GROUP_COUNT,
                    0,
                    maximumGroupCount,
                    0,
                )
                GLES31.glGetIntegeri_v(
                    GLES31.GL_MAX_COMPUTE_WORK_GROUP_COUNT,
                    1,
                    maximumGroupCount,
                    1,
                )
                val groupQueryError = GLES30.glGetError()
                if (groupQueryError == GLES30.GL_NO_ERROR &&
                    maximumGroupCount[0] > 0 &&
                    maximumGroupCount[1] > 0
                ) {
                    maxComputePackGroupsX = maximumGroupCount[0]
                    maxComputePackGroupsY = maximumGroupCount[1]
                } else {
                    supportsComputeReadback = false
                    maxShaderStorageBlockBytes = 0L
                    PLog.w(
                        TAG,
                        "MGC strength SSBO pack disabled: unable to query dispatch limits " +
                            "value=${maximumGroupCount.contentToString()} " +
                            "glError=$groupQueryError",
                    )
                }
            } else {
                supportsComputeReadback = false
                maxShaderStorageBlockBytes = 0L
                PLog.w(
                    TAG,
                    "MGC strength SSBO pack disabled: unable to query block limit " +
                        "value=${maximumBlockSize[0]} glError=$queryError",
                )
            }
        }
        PLog.i(
            TAG,
            "MGC Spatial GL vendor=${GLES30.glGetString(GLES30.GL_VENDOR).orEmpty()} " +
            "renderer=${GLES30.glGetString(GLES30.GL_RENDERER).orEmpty()} version=$version " +
                "strengthSsboMax=$maxShaderStorageBlockBytes " +
                "strengthPackGroups=${maxComputePackGroupsX}x$maxComputePackGroupsY",
        )
    }

    private fun applyRawRenderState() {
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        GLES30.glDisable(GLES30.GL_BLEND)
        GLES30.glDisable(GLES30.GL_DITHER)
        GLES30.glDisable(GLES30.GL_SCISSOR_TEST)
        GLES30.glDisable(GLES30.GL_DEPTH_TEST)
        GLES30.glDisable(GLES30.GL_STENCIL_TEST)
        GLES30.glDisable(GLES30.GL_CULL_FACE)
    }

    private fun checkGlError(label: String) {
        var error = GLES30.glGetError()
        if (error == GLES30.GL_NO_ERROR) return
        val first = error
        while (error != GLES30.GL_NO_ERROR) {
            error = GLES30.glGetError()
        }
        throw IllegalStateException("$label GL error: 0x${first.toString(16)}")
    }

    private fun release() {
        sabreRgbChromaPostprocessor?.release()
        sabreRgbChromaPostprocessor = null
        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {
            if (programs.isNotEmpty()) {
                for (program in programs) GLES30.glDeleteProgram(program)
            }
            uniformLocations.clear()
            textureSpecs.clear()
            validatedRenderTargetSpecs.clear()
            if (textures.isNotEmpty()) {
                GLES30.glDeleteTextures(textures.size, textures.toIntArray(), 0)
            }
            if (framebuffers.isNotEmpty()) {
                GLES30.glDeleteFramebuffers(framebuffers.size, framebuffers.toIntArray(), 0)
            }
            if (buffers.isNotEmpty()) {
                GLES30.glDeleteBuffers(buffers.size, buffers.toIntArray(), 0)
            }
            if (ownsEglContext) {
                EGL14.eglMakeCurrent(
                    eglDisplay,
                    EGL14.EGL_NO_SURFACE,
                    EGL14.EGL_NO_SURFACE,
                    EGL14.EGL_NO_CONTEXT,
                )
                if (eglSurface != EGL14.EGL_NO_SURFACE) {
                    EGL14.eglDestroySurface(eglDisplay, eglSurface)
                }
                if (eglContext != EGL14.EGL_NO_CONTEXT) {
                    EGL14.eglDestroyContext(eglDisplay, eglContext)
                }
                EGL14.eglTerminate(eglDisplay)
            }
        }
        programs.clear()
        textures.clear()
        framebuffers.clear()
        buffers.clear()
        eglDisplay = EGL14.EGL_NO_DISPLAY
        eglContext = EGL14.EGL_NO_CONTEXT
        eglSurface = EGL14.EGL_NO_SURFACE
        ownsEglContext = false
    }

    private fun canonicalChannelAtPhase(phase: Int): Int {
        val phaseToCanonical = when (cfaPattern.mod(4)) {
            1 -> intArrayOf(1, 0, 3, 2)
            2 -> intArrayOf(2, 3, 0, 1)
            3 -> intArrayOf(3, 2, 1, 0)
            else -> intArrayOf(0, 1, 2, 3)
        }
        return phaseToCanonical[phase.coerceIn(0, 3)]
    }

    private fun validExposureProduct(value: Double): Double =
        value.takeIf { it.isFinite() && it > 0.0 } ?: 1.0

    private fun ceilDiv(value: Int, divisor: Int): Int =
        ceil(value.toDouble() / divisor.toDouble()).toInt().coerceAtLeast(1)

    private fun alignmentGridExtent(
        nominalLevelExtent: Int,
        tileStride: Int,
    ): Int = max(1, ceilDiv(nominalLevelExtent, tileStride) - 2)

    private fun alignmentGridWidth(
        level: TextureLevel,
        tileStride: Int,
    ): Int = alignmentGridExtent(
        ceilDiv(ceilDiv(width, 2), level.scaleToBayerQuads.toInt()),
        tileStride,
    )

    private fun alignmentGridHeight(
        level: TextureLevel,
        tileStride: Int,
    ): Int = alignmentGridExtent(
        ceilDiv(ceilDiv(height, 2), level.scaleToBayerQuads.toInt()),
        tileStride,
    )

    private fun rgbBandHeightCandidates(): IntArray = intArrayOf(
        outputHeight,
        4096,
        3072,
        2048,
        1536,
        MgcSpatialRgbTilePlanner.DEFAULT_OUTPUT_TILE_SIZE,
        768,
        512,
        384,
        256,
        192,
        128,
        64,
        32,
    ).filter { it in 1..outputHeight }
        .distinct()
        .sortedDescending()
        .toIntArray()

    private fun persistTrue2xTexture(
        texture: Int,
        width: Int,
        height: Int,
        format: Int,
        type: Int,
        bytesPerPixel: Int,
        file: File,
        label: String,
    ) {
        val bytes = Math.multiplyExact(Math.multiplyExact(width, height), bytesPerPixel)
        val buffer = LargeDirectBuffer.allocate(bytes.toLong(), label)
            ?.order(ByteOrder.nativeOrder())
            ?: throw IllegalStateException("Unable to allocate $bytes bytes for $label")
        try {
            bindRenderTargets(intArrayOf(texture), label)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glReadPixels(0, 0, width, height, format, type, buffer)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            checkGlError(label)
            buffer.position(0)
            buffer.limit(bytes)
            FileOutputStream(file).channel.use { channel ->
                while (buffer.hasRemaining()) channel.write(buffer)
            }
        } finally {
            LargeDirectBuffer.free(buffer)
        }
        require(file.isFile && file.length() == bytes.toLong()) {
            "$label persisted byte count=${file.length()}, expected=$bytes"
        }
    }

    private fun readTrue2xFlow(flow: SabreConvertedAlignment): Triple<ByteBuffer, Float, Float> {
        val spec = checkNotNull(textureSpecs[flow.texture]) { "True2x flow texture is not owned" }
        val bytes = Math.multiplyExact(Math.multiplyExact(spec.width, spec.height), 8)
        val output = LargeDirectBuffer.allocate(bytes.toLong(), "IRIS26564 true2x flow")
            ?.order(ByteOrder.nativeOrder())
            ?: throw IllegalStateException("Unable to allocate $bytes bytes for true2x flow")
        bindRenderTargets(intArrayOf(flow.texture), "IRIS26564 true2x flow readback")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        GLES30.glReadPixels(
            0, 0, spec.width, spec.height,
            GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, output,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("IRIS26564 true2x flow readback")
        output.position(0)
        val shorts = output.asShortBuffer()
        var maxX = 0f
        var maxY = 0f
        for (index in 0 until spec.width * spec.height) {
            val x = kotlin.math.abs(Half.toFloat(shorts.get(index * 4))) * width
            val y = kotlin.math.abs(Half.toFloat(shorts.get(index * 4 + 1))) * height
            if (x.isFinite()) maxX = max(maxX, x)
            if (y.isFinite()) maxY = max(maxY, y)
        }
        output.position(0)
        return Triple(output, maxX, maxY)
    }

    private fun dominantTrue2xPhaseBin(flowData: ByteBuffer, flowWidth: Int, flowHeight: Int): Int {
        val values = flowData.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val bins = IntArray(4)
        val pixels = flowWidth * flowHeight
        val step = max(1, pixels / 2048)
        var index = 0
        while (index < pixels) {
            val fx = Half.toFloat(values.get(index * 4)) * width
            val fy = Half.toFloat(values.get(index * 4 + 1)) * height
            if (fx.isFinite() && fy.isFinite()) {
                val px = fx - kotlin.math.floor(fx)
                val py = fy - kotlin.math.floor(fy)
                val bin = (if (px >= 0.5f) 1 else 0) + (if (py >= 0.5f) 2 else 0)
                bins[bin]++
            }
            index += step
        }
        return bins.indices.maxByOrNull { bins[it] } ?: 0
    }

    private fun true2xRejectionQuality(bytes: ByteArray?): Float {
        if (bytes == null || bytes.isEmpty()) return 1f
        var sum = 0L
        for (value in bytes) sum += value.toInt() and 0xff
        return (sum.toDouble() / (bytes.size.toDouble() * 255.0)).toFloat().coerceIn(0f, 1f)
    }

    private fun renderTrue2xFlowRefinement26574(
        referenceRawTexture: Int,
        currentRawTexture: Int,
        sparseFlow: SabreConvertedAlignment,
        referenceCalibration: FrameCalibration,
        currentCalibration: FrameCalibration,
    ): SabreConvertedAlignment {
        if (true2xFlowRefineProgram26574 == 0) {
            true2xFlowRefineProgram26574 = linkProgram(
                GlesMgcRawSabreShaders.true2xFlowRefine26574,
                "iris_26574_true2x_flow_refine",
            )
        }
        val outputWidth = ceilDiv(width, TRUE2X_REFINE_CELL_RAW_PIXELS)
        val outputHeight = ceilDiv(height, TRUE2X_REFINE_CELL_RAW_PIXELS)
        val output = createTexture(outputWidth, outputHeight, GLES30.GL_RGBA16F, GLES30.GL_LINEAR)
        val program = true2xFlowRefineProgram26574
        GLES30.glUseProgram(program)
        bindTexture(program, "uReferenceRaw", 0, referenceRawTexture)
        bindTexture(program, "uCurrentRaw", 1, currentRawTexture)
        bindTexture(program, "uSparseFlow", 2, sparseFlow.texture)
        uniform2i(program, "uRawSize", width, height)
        uniform2i(program, "uOutputSize", outputWidth, outputHeight)
        uniform4f(program, "uSparseFlowScaleOffset", sparseFlow.scaleX, sparseFlow.scaleY, sparseFlow.offsetX, sparseFlow.offsetY)
        uniform4fv(program, "uReferencePhaseGains", referenceCalibration.bayerPhaseGains)
        uniform4fv(program, "uReferencePhaseBlackTerms", referenceCalibration.bayerPhaseBlackTerms)
        uniform4fv(program, "uCurrentPhaseGains", currentCalibration.bayerPhaseGains)
        uniform4fv(program, "uCurrentPhaseBlackTerms", currentCalibration.bayerPhaseBlackTerms)
        draw(program, outputWidth, outputHeight, intArrayOf(output))
        checkGlError("IRIS26574 true2x flow refinement")
        return SabreConvertedAlignment(output, 1f, 1f, 0f, 0f)
    }

    private fun true2xFlowRefineAcceptance(
        flowData: ByteBuffer,
        flow: SabreConvertedAlignment,
    ): Triple<Int, Int, Float> {
        val spec = checkNotNull(textureSpecs[flow.texture])
        val values = flowData.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val pixels = spec.width * spec.height
        var accepted = 0
        for (index in 0 until pixels) {
            val confidence = Half.toFloat(values.get(index * 4 + 3))
            if (confidence.isFinite() && confidence > 0.5f) accepted++
        }
        val pct = if (pixels > 0) 100f * accepted.toFloat() / pixels.toFloat() else 0f
        return Triple(accepted, pixels, pct)
    }

    private fun persistTrue2xEvidence(
        frameIndex: Int,
        calibration: FrameCalibration,
        flow: SabreConvertedAlignment,
        covariance: Int,
        rejection: Int,
        covarianceWidth: Int,
        covarianceHeight: Int,
        rejectionWidth: Int,
        rejectionHeight: Int,
        useFrameWeight: Boolean,
        existingPhaseEvidence: Array<True2xFrameEvidence?>?,
        referenceRawTexture: Int,
        currentRawTexture: Int,
        referenceCalibration: FrameCalibration,
    ): True2xFrameEvidence {
        val directory = checkNotNull(sabreSuperResTempDir) { "True2x temp directory is absent" }
        require(directory.exists() || directory.mkdirs()) { "Unable to create ${directory.absolutePath}" }
        val (selectionFlowData, selectionMaxX, selectionMaxY) = readTrue2xFlow(flow)
        val spec = checkNotNull(textureSpecs[flow.texture])
        val phaseBin = dominantTrue2xPhaseBin(selectionFlowData, spec.width, spec.height)
        val rejectionBytes = if (useFrameWeight) readR8Mask(
            rejection, "IRIS26568 rejection quality frame=$frameIndex", rejectionWidth, rejectionHeight,
        ) else null
        val quality = true2xRejectionQuality(rejectionBytes)
        var retainedRank = 0
        var displaced: True2xFrameEvidence? = null
        if (existingPhaseEvidence != null) {
            require(existingPhaseEvidence.size == TRUE2X_JPEG_MAX_EVIDENCE)
            val firstIndex = phaseBin * TRUE2X_JPEG_EVIDENCE_PER_PHASE
            val secondIndex = firstIndex + 1
            val first = existingPhaseEvidence[firstIndex]
            val second = existingPhaseEvidence[secondIndex]
            /* IRIS_26568_PHASE_TOP2_MONOTONIC_SUPPORT
             * Final rank-0 equals 26567's strongest-per-phase choice. Rank-1 only adds evidence;
             * it can never evict rank-0 with a weaker frame. Local RGBA phase occupancy therefore
             * cannot lose a phase that 26567 had, while local flow may add a missing phase.
             */
            when {
                first == null -> retainedRank = 0
                quality > first.qualityScore -> {
                    retainedRank = 0
                    displaced = second
                    existingPhaseEvidence[secondIndex] = first
                }
                second == null -> retainedRank = 1
                quality > second.qualityScore -> { retainedRank = 1; displaced = second }
                else -> {
                    LargeDirectBuffer.free(selectionFlowData)
                    PLog.i(SABRE_TAG, "IRIS_26568_TRUE2X_PHASE_SKIP frame=$frameIndex phase=$phaseBin " +
                        "quality=$quality retained=${first.frameIndex}:${first.qualityScore}," +
                        "${second.frameIndex}:${second.qualityScore}")
                    return second
                }
            }
        }
        var persistedFlowData = selectionFlowData
        var persistedFlowWidth = spec.width
        var persistedFlowHeight = spec.height
        var persistedFlowScaleX = flow.scaleX
        var persistedFlowScaleY = flow.scaleY
        var persistedFlowOffsetX = flow.offsetX
        var persistedFlowOffsetY = flow.offsetY
        var persistedMaxX = selectionMaxX
        var persistedMaxY = selectionMaxY
        /* IRIS_26574_JPEG_RETAINED_FLOW_REFINEMENT_ONLY
         * Selection remains the exact 26568 global top-two-per-phase contract. Only after a frame
         * wins that bounded JPEG reservoir do we spend work on local SR alignment. DNG/full-evidence
         * mode is byte-semantically the 26573 sparse-flow path. Any GL/refinement failure keeps the
         * exact sparse flow rather than failing capture or introducing an unaligned fallback.
         */
        if (existingPhaseEvidence != null && frameIndex != 0) {
            runCatching {
                val refinedFlow = renderTrue2xFlowRefinement26574(
                    referenceRawTexture = referenceRawTexture,
                    currentRawTexture = currentRawTexture,
                    sparseFlow = flow,
                    referenceCalibration = referenceCalibration,
                    currentCalibration = calibration,
                )
                var refinedDataToFree: ByteBuffer? = null
                try {
                    val (refinedData, refinedMaxX, refinedMaxY) = readTrue2xFlow(refinedFlow)
                    refinedDataToFree = refinedData
                    val refineStats = true2xFlowRefineAcceptance(refinedData, refinedFlow)
                    val refinedSpec = checkNotNull(textureSpecs[refinedFlow.texture])
                    val previousFlowData = persistedFlowData
                    persistedFlowData = refinedData
                    refinedDataToFree = null
                    persistedFlowWidth = refinedSpec.width
                    persistedFlowHeight = refinedSpec.height
                    persistedFlowScaleX = refinedFlow.scaleX
                    persistedFlowScaleY = refinedFlow.scaleY
                    persistedFlowOffsetX = refinedFlow.offsetX
                    persistedFlowOffsetY = refinedFlow.offsetY
                    persistedMaxX = refinedMaxX
                    persistedMaxY = refinedMaxY
                    LargeDirectBuffer.free(previousFlowData)
                    val details = "frame=$frameIndex phase=$phaseBin accepted=${refineStats.first}/${refineStats.second} " +
                        "acceptedPct=${refineStats.third} deltaBoundRawPx=0.5"
                    PLog.i(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE $details")
                    MotionTrace.processingState("IRIS_26574_TRUE2X_FLOW_REFINE", details)
                } finally {
                    LargeDirectBuffer.free(refinedDataToFree)
                    runCatching { releaseOwnedTexture(refinedFlow.texture, "IRIS26574 true2x refined flow") }
                }
            }.onFailure { error ->
                PLog.e(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE_FALLBACK frame=$frameIndex reason=${error.message}", error)
            }
        }

        val covarianceFile = File(directory, "iris26568_cov_${frameIndex}_${System.nanoTime()}.rgb10a2")
        persistTrue2xTexture(
            covariance, covarianceWidth, covarianceHeight,
            GLES30.GL_RGBA, GLES30.GL_UNSIGNED_INT_2_10_10_10_REV, 4,
            covarianceFile, "IRIS26568 covariance frame=$frameIndex",
        )
        val rejectionFile = rejectionBytes?.let { bytes ->
            File(directory, "iris26568_rej_${frameIndex}_${System.nanoTime()}.r8").also { file ->
                file.outputStream().use { it.write(bytes) }
                require(file.length() == bytes.size.toLong())
            }
        }
        val result = True2xFrameEvidence(
            frameIndex = frameIndex,
            calibration = calibration,
            flowData = persistedFlowData,
            flowWidth = persistedFlowWidth,
            flowHeight = persistedFlowHeight,
            flowScaleX = persistedFlowScaleX,
            flowScaleY = persistedFlowScaleY,
            flowOffsetX = persistedFlowOffsetX,
            flowOffsetY = persistedFlowOffsetY,
            covarianceFile = covarianceFile,
            covarianceWidth = covarianceWidth,
            covarianceHeight = covarianceHeight,
            rejectionFile = rejectionFile,
            rejectionWidth = rejectionWidth,
            rejectionHeight = rejectionHeight,
            maxAbsFlowPixelsX = persistedMaxX,
            maxAbsFlowPixelsY = persistedMaxY,
            useFrameWeight = useFrameWeight,
            dominantPhaseBin = phaseBin,
            qualityScore = quality,
        )
        if (existingPhaseEvidence != null) {
            val slot = phaseBin * TRUE2X_JPEG_EVIDENCE_PER_PHASE + retainedRank
            existingPhaseEvidence[slot] = result
            displaced?.let { cleanupTrue2xEvidence(listOf(it)) }
            PLog.i(SABRE_TAG, "IRIS_26568_TRUE2X_PHASE_RETAIN frame=$frameIndex phase=$phaseBin " +
                "rank=$retainedRank quality=$quality")
        }
        return result
    }

    private fun readTrue2xFileRegion(
        file: File,
        fullWidth: Int,
        bytesPerPixel: Int,
        left: Int,
        top: Int,
        regionWidth: Int,
        regionHeight: Int,
        label: String,
    ): ByteBuffer {
        require(left >= 0 && top >= 0 && regionWidth > 0 && regionHeight > 0)
        val byteCount = Math.multiplyExact(Math.multiplyExact(regionWidth, regionHeight), bytesPerPixel)
        val output = LargeDirectBuffer.allocate(byteCount.toLong(), label)
            ?.order(ByteOrder.nativeOrder())
            ?: throw IllegalStateException("Unable to allocate $byteCount bytes for $label")
        RandomAccessFile(file, "r").channel.use { channel ->
            for (row in 0 until regionHeight) {
                val offset = ((top + row).toLong() * fullWidth + left) * bytesPerPixel
                output.position(row * regionWidth * bytesPerPixel)
                output.limit((row + 1) * regionWidth * bytesPerPixel)
                var position = offset
                while (output.hasRemaining()) {
                    val read = channel.read(output, position)
                    if (read < 0) throw IllegalStateException("Unexpected EOF reading $label")
                    if (read == 0) continue
                    position += read
                }
            }
        }
        output.position(0)
        output.limit(byteCount)
        return output
    }

    private fun readTrue2xRawRegion(
        image: SafeImage,
        left: Int,
        top: Int,
        regionWidth: Int,
        regionHeight: Int,
    ): True2xPackedRawRegion {
        if (image.isFileBacked) {
            val region = image.readFileRegion(left, top, regionWidth, regionHeight)
            require(region.pixelStride == RAW_BYTES_PER_PIXEL)
            require(region.rowStride % RAW_BYTES_PER_PIXEL == 0)
            return True2xPackedRawRegion(
                region.buffer, regionWidth, regionHeight,
                region.rowStride / RAW_BYTES_PER_PIXEL,
            ) { region.close() }
        }
        val plane = image.planes.firstOrNull()
            ?: throw IllegalArgumentException("True2x in-memory RAW has no plane")
        require(plane.pixelStride == RAW_BYTES_PER_PIXEL)
        require(plane.rowStride >= width * RAW_BYTES_PER_PIXEL)
        require(plane.rowStride % RAW_BYTES_PER_PIXEL == 0)
        val source = plane.buffer.duplicate().order(ByteOrder.nativeOrder())
        val sourceStart = top.toLong() * plane.rowStride + left.toLong() * RAW_BYTES_PER_PIXEL
        val sourceEnd = sourceStart +
            (regionHeight - 1L) * plane.rowStride + regionWidth.toLong() * RAW_BYTES_PER_PIXEL
        require(sourceStart in 0..Int.MAX_VALUE.toLong() && sourceEnd <= source.limit()) {
            "True2x RAW region exceeds in-memory plane: left=$left top=$top size=${regionWidth}x$regionHeight"
        }
        source.position(sourceStart.toInt())
        source.limit(sourceEnd.toInt())
        val slice = source.slice().order(ByteOrder.nativeOrder())
        return True2xPackedRawRegion(
            slice, regionWidth, regionHeight, plane.rowStride / RAW_BYTES_PER_PIXEL,
        ) { }
    }

    private fun true2xRegionForOutput(
        outputLeft: Int,
        outputTop: Int,
        outputWidth: Int,
        outputHeight: Int,
        maximumFlowX: Float,
        maximumFlowY: Float,
    ): IntArray {
        val haloX = kotlin.math.ceil(maximumFlowX + TRUE2X_RAW_RBF_HALO).toInt()
        val haloY = kotlin.math.ceil(maximumFlowY + TRUE2X_RAW_RBF_HALO).toInt()
        val nativeLeft = kotlin.math.floor(outputLeft * 0.5f).toInt() - haloX
        val nativeTop = kotlin.math.floor(outputTop * 0.5f).toInt() - haloY
        val nativeRight = kotlin.math.ceil((outputLeft + outputWidth) * 0.5f).toInt() + haloX
        val nativeBottom = kotlin.math.ceil((outputTop + outputHeight) * 0.5f).toInt() + haloY
        return intArrayOf(
            nativeLeft.coerceIn(0, width - 1),
            nativeTop.coerceIn(0, height - 1),
            nativeRight.coerceIn(1, width),
            nativeBottom.coerceIn(1, height),
        )
    }

    private fun true2xScaledRegion(
        outputLeft: Int,
        outputTop: Int,
        outputWidth: Int,
        outputHeight: Int,
        fullOutputWidth: Int,
        fullOutputHeight: Int,
        targetWidth: Int,
        targetHeight: Int,
        halo: Int,
    ): IntArray {
        val left = kotlin.math.floor(outputLeft.toDouble() * targetWidth / fullOutputWidth).toInt() - halo
        val top = kotlin.math.floor(outputTop.toDouble() * targetHeight / fullOutputHeight).toInt() - halo
        val right = kotlin.math.ceil((outputLeft + outputWidth).toDouble() * targetWidth / fullOutputWidth).toInt() + halo
        val bottom = kotlin.math.ceil((outputTop + outputHeight).toDouble() * targetHeight / fullOutputHeight).toInt() + halo
        return intArrayOf(
            left.coerceIn(0, targetWidth - 1),
            top.coerceIn(0, targetHeight - 1),
            right.coerceIn(1, targetWidth),
            bottom.coerceIn(1, targetHeight),
        )
    }

    private fun true2xRawScaledRegion(
        rawRegion: IntArray,
        targetWidth: Int,
        targetHeight: Int,
        halo: Int,
    ): IntArray {
        require(rawRegion.size == 4)
        val left = kotlin.math.floor(rawRegion[0].toDouble() * targetWidth / width).toInt() - halo
        val top = kotlin.math.floor(rawRegion[1].toDouble() * targetHeight / height).toInt() - halo
        val right = kotlin.math.ceil(rawRegion[2].toDouble() * targetWidth / width).toInt() + halo
        val bottom = kotlin.math.ceil(rawRegion[3].toDouble() * targetHeight / height).toInt() + halo
        return intArrayOf(
            left.coerceIn(0, targetWidth - 1),
            top.coerceIn(0, targetHeight - 1),
            right.coerceIn(1, targetWidth),
            bottom.coerceIn(1, targetHeight),
        )
    }

    private fun allocateTrue2xHostBuffer(
        byteCount: Int,
        label: String,
        zero: Boolean = false,
    ): ByteBuffer {
        require(byteCount > 0)
        val buffer = LargeDirectBuffer.allocate(byteCount.toLong(), label)
            ?.order(ByteOrder.nativeOrder())
            ?: throw IllegalStateException("Unable to allocate $byteCount bytes for $label")
        if (zero) {
            val longs = buffer.asLongBuffer()
            for (index in 0 until longs.capacity()) longs.put(index, 0L)
            for (index in longs.capacity() * java.lang.Long.BYTES until byteCount) buffer.put(index, 0.toByte())
        }
        buffer.position(0)
        buffer.limit(byteCount)
        return buffer
    }

    private fun writeTrue2xTileRows(
        output: RandomAccessFile,
        tile: ByteBuffer,
        outputLeft: Int,
        outputTop: Int,
        tileWidth: Int,
        tileHeight: Int,
        fullOutputWidth: Int,
        bytesPerPixel: Int,
    ) {
        val rowBytes = tileWidth * bytesPerPixel
        val source = tile.duplicate().order(ByteOrder.nativeOrder())
        for (row in 0 until tileHeight) {
            source.position(row * rowBytes)
            source.limit((row + 1) * rowBytes)
            output.channel.position(((outputTop + row).toLong() * fullOutputWidth + outputLeft) * bytesPerPixel)
            while (source.hasRemaining()) output.channel.write(source)
            source.clear()
        }
    }

    private fun writeTrue2xGpuRgbTile(
        output: RandomAccessFile,
        texture: Int,
        left: Int,
        top: Int,
        tileWidth: Int,
        tileHeight: Int,
        fullOutputWidth: Int,
        label: String,
        phaseHistogram: LongArray? = null,
        reasonHistogram: LongArray? = null,
        activityGrid: LongArray? = null,
        fullOutputHeight: Int = 0,
    ) {
        val rgba = allocateTrue2xHostBuffer(
            Math.multiplyExact(Math.multiplyExact(tileWidth, tileHeight), 4 * Short.SIZE_BYTES),
            "$label RGBA16F readback",
        )
        val rgb = allocateTrue2xHostBuffer(
            Math.multiplyExact(Math.multiplyExact(tileWidth, tileHeight), TRUE2X_RGB16F_BYTES_PER_PIXEL),
            "$label RGB16F pack",
        )
        try {
            bindRenderTargets(intArrayOf(texture), "$label framebuffer")
            GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            rgba.clear()
            GLES30.glReadPixels(
                0, 0, tileWidth, tileHeight,
                GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, rgba,
            )
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            val rgbaShort = rgba.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
            val rgbShort = rgb.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
            for (index in 0 until tileWidth * tileHeight) {
                rgbShort.put(index * 3, rgbaShort.get(index * 4))
                rgbShort.put(index * 3 + 1, rgbaShort.get(index * 4 + 1))
                rgbShort.put(index * 3 + 2, rgbaShort.get(index * 4 + 2))
                phaseHistogram?.let { histogram ->
                    /* IRIS_26573_REQUIRED_SR_PROOF_NO_SECOND_READBACK
                     * Alpha is diagnostic-only phaseCount*8 + reasonClass, written as an exact
                     * binary16 integer by the render shader. Decode it while packing the one
                     * RGBA16F readback already required for the 50MP publication carrier.
                     */
                    val diagnostic = Half.toFloat(rgbaShort.get(index * 4 + 3)).toInt()
                    require(diagnostic in 0..39) { "26573 invalid SR diagnostic code=$diagnostic" }
                    val phaseCount = (diagnostic / 8).coerceIn(0, 4)
                    val reasonClass = diagnostic % 8
                    histogram[phaseCount]++
                    reasonHistogram?.let { reasons ->
                        require(reasons.size >= 8)
                        reasons[reasonClass] = reasons[reasonClass] + 1L
                    }
                    activityGrid?.let { grid ->
                        require(fullOutputHeight > 0 && grid.size == TRUE2X_PROOF_GRID_WIDTH * TRUE2X_PROOF_GRID_HEIGHT * 3)
                        val gx = left + (index % tileWidth)
                        val gy = top + (index / tileWidth)
                        val cellX = (gx.toLong() * TRUE2X_PROOF_GRID_WIDTH / fullOutputWidth).toInt().coerceIn(0, TRUE2X_PROOF_GRID_WIDTH - 1)
                        val cellY = (gy.toLong() * TRUE2X_PROOF_GRID_HEIGHT / fullOutputHeight).toInt().coerceIn(0, TRUE2X_PROOF_GRID_HEIGHT - 1)
                        val q = (cellY * TRUE2X_PROOF_GRID_WIDTH + cellX) * 3
                        grid[q]++
                        if (reasonClass == 1 || reasonClass == 2) grid[q + 1]++
                        if (reasonClass == 2) grid[q + 2]++
                    }
                }
            }
            rgb.position(0)
            writeTrue2xTileRows(
                output, rgb, left, top, tileWidth, tileHeight,
                fullOutputWidth, TRUE2X_RGB16F_BYTES_PER_PIXEL,
            )
        } finally {
            LargeDirectBuffer.free(rgb)
            LargeDirectBuffer.free(rgba)
        }
    }

    private fun streamTrue2xNativeVgnGuideRgb16f(texture: Int): File {
        require(enableSabreSuperRes)
        require(texture != 0)
        require(exportGpuLinearRgbSource && gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F) {
            "26564 true2x VGN guide requires the proven RGBA16F Sabre GPU carrier"
        }
        val directory = checkNotNull(sabreSuperResTempDir)
        require(directory.exists() || directory.mkdirs())
        val guide = File.createTempFile("iris26564_native_vgn_guide_", ".rgb16f", directory)
        val bandHeightMax = minOf(TRUE2X_VGN_GUIDE_BAND_HEIGHT, height)
        val rgba = allocateTrue2xHostBuffer(
            Math.multiplyExact(Math.multiplyExact(width, bandHeightMax), 4 * Short.SIZE_BYTES),
            "IRIS26564 native VGN RGBA16F guide readback",
        )
        val rgb = allocateTrue2xHostBuffer(
            Math.multiplyExact(Math.multiplyExact(width, bandHeightMax), TRUE2X_RGB16F_BYTES_PER_PIXEL),
            "IRIS26564 native VGN RGB16F guide pack",
        )
        val fbo = IntArray(1)
        GLES30.glGenFramebuffers(1, fbo, 0)
        check(fbo[0] != 0)
        try {
            BufferedOutputStream(FileOutputStream(guide), 1024 * 1024).use { output ->
                GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbo[0])
                GLES30.glFramebufferTexture2D(
                    GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                    GLES30.GL_TEXTURE_2D, texture, 0,
                )
                check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE) {
                    "26564 native VGN guide framebuffer incomplete"
                }
                GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
                GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
                GLES30.glPixelStorei(GLES30.GL_PACK_ROW_LENGTH, 0)
                var top = 0
                while (top < height) {
                    val bandHeight = minOf(bandHeightMax, height - top)
                    val rgbaBytes = Math.multiplyExact(
                        Math.multiplyExact(width, bandHeight), 4 * Short.SIZE_BYTES,
                    )
                    rgba.clear(); rgba.limit(rgbaBytes)
                    GLES30.glReadPixels(
                        0, top, width, bandHeight,
                        GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, rgba,
                    )
                    checkGlError("IRIS26564 native VGN guide band $top")
                    val rgbaShorts = rgba.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
                    val rgbShorts = rgb.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
                    val pixels = width * bandHeight
                    for (index in 0 until pixels) {
                        rgbShorts.put(index * 3, rgbaShorts.get(index * 4))
                        rgbShorts.put(index * 3 + 1, rgbaShorts.get(index * 4 + 1))
                        rgbShorts.put(index * 3 + 2, rgbaShorts.get(index * 4 + 2))
                    }
                    val rgbBytes = pixels * TRUE2X_RGB16F_BYTES_PER_PIXEL
                    val bytes = ByteArray(rgbBytes)
                    val packed = rgb.duplicate().order(ByteOrder.nativeOrder())
                    packed.position(0); packed.limit(rgbBytes); packed.get(bytes)
                    output.write(bytes)
                    top += bandHeight
                    GlesGpuScheduler.yieldToUiRenderer()
                }
            }
            val expected = width.toLong() * height * TRUE2X_RGB16F_BYTES_PER_PIXEL
            check(guide.length() == expected) {
                "26564 native VGN guide size=${guide.length()} expected=$expected"
            }
            return guide
        } catch (error: Throwable) {
            runCatching { guide.delete() }
            throw error
        } finally {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            if (fbo[0] != 0) GLES30.glDeleteFramebuffers(1, fbo, 0)
            LargeDirectBuffer.free(rgb)
            LargeDirectBuffer.free(rgba)
        }
    }

    private fun updateTrue2xPhaseHistogram(mask: ByteBuffer, pixels: Int, histogram: LongArray) {
        for (index in 0 until pixels) {
            val bits = mask.get(index).toInt() and 0x0f
            val count = Integer.bitCount(bits).coerceIn(0, 4)
            histogram[count]++
        }
    }

    private fun true2xPhaseStats(histogram: LongArray): True2xPhaseStats {
        val total = (0..4).sumOf { histogram[it] }.coerceAtLeast(1L)
        val mean = (0..4).sumOf { it.toDouble() * histogram[it] }.div(total).toFloat()
        val target = kotlin.math.ceil(total * 0.10).toLong().coerceAtLeast(1L)
        var cumulative = 0L
        var p10 = 0
        for (support in 0..4) {
            cumulative += histogram[support]
            if (cumulative >= target) { p10 = support; break }
        }
        val percentages = FloatArray(5) { support ->
            (100.0 * histogram[support].toDouble() / total.toDouble()).toFloat()
        }
        PLog.i(SABRE_TAG, "IRIS_26568_TRUE2X_PHASE_SUPPORT zero=${percentages[0]} one=${percentages[1]} " +
            "two=${percentages[2]} three=${percentages[3]} four=${percentages[4]} mean=$mean p10=$p10")
        return True2xPhaseStats(mean, p10.toFloat(), percentages)
    }

    private fun true2xSmooth01(value: Float): Float {
        val t = value.coerceIn(0f, 1f)
        return t * t * (3f - 2f * t)
    }

    private fun true2xTemporalAgreementFromAccumulator(values: java.nio.FloatBuffer, index: Int): Float {
        val q = index * TRUE2X_ACCUMULATOR_FLOATS_PER_PIXEL
        val sumWY = values.get(q + 6).coerceAtLeast(0f)
        val sumWY2 = values.get(q + 7).coerceAtLeast(0f)
        val sumW = values.get(q + 8).coerceAtLeast(0f)
        val sumW2 = values.get(q + 9).coerceAtLeast(0f)
        if (sumW <= 0.08f || sumW2 <= 1.0e-6f) return 0f
        val meanY = sumWY / sumW
        val varianceY = (sumWY2 / sumW - meanY * meanY).coerceAtLeast(0f)
        val effectiveN = (sumW * sumW) / sumW2.coerceAtLeast(1.0e-6f)
        val supportGate = true2xSmooth01((effectiveN - 1.50f) / 1.50f)
        val relativeSigma = sqrt(varianceY) / kotlin.math.abs(meanY).coerceAtLeast(0.030f)
        val stabilityGate = 1f - true2xSmooth01((relativeSigma - 0.060f) / 0.120f)
        return (supportGate * stabilityGate).coerceIn(0f, 1f)
    }

    /* IRIS_26573_CPU_PACKED_PHASE_TEMPORAL_PROOF
     * One byte remains the complete CPU fallback sidecar: low three bits are phase count (0..4),
     * high five bits quantize cross-frame temporal agreement (0..31). File size and publication
     * ownership remain unchanged while CPU/GPU true-detail admission gains the same temporal proof.
     */
    private fun writeTrue2xPhaseSupportTile(
        output: RandomAccessFile, support: ByteBuffer, left: Int, top: Int,
        tileWidth: Int, tileHeight: Int, fullWidth: Int, rgbaMask: Boolean,
        temporalAccumulator: ByteBuffer? = null,
    ) {
        val row = ByteArray(tileWidth)
        val temporalValues = temporalAccumulator?.duplicate()?.order(ByteOrder.nativeOrder())?.asFloatBuffer()
        for (y in 0 until tileHeight) {
            for (x in 0 until tileWidth) {
                val index = y * tileWidth + x
                val count = if (rgbaMask) {
                    var value = 0
                    for (channel in 0 until 4) if ((support.get(index * 4 + channel).toInt() and 0xff) > 0) value++
                    value
                } else Integer.bitCount(support.get(index).toInt() and 0x0f)
                val temporalCode = temporalValues?.let {
                    (true2xTemporalAgreementFromAccumulator(it, index) * 31f + 0.5f).toInt().coerceIn(0, 31)
                } ?: 31
                row[x] = ((count.coerceIn(0, 4) and 0x07) or (temporalCode shl 3)).toByte()
            }
            output.seek(((top + y).toLong() * fullWidth + left).toLong())
            output.write(row)
        }
    }

    private fun runTrue2xCpu(
        frames: List<RawStackFrame>,
        images: List<SafeImage>,
        evidence: List<True2xFrameEvidence>,
        outputFile: File,
        phaseSupportFile: File,
        fullOutputWidth: Int,
        fullOutputHeight: Int,
    ): True2xPhaseStats {
        val maxFlowX = evidence.maxOfOrNull { it.maxAbsFlowPixelsX } ?: 0f
        val maxFlowY = evidence.maxOfOrNull { it.maxAbsFlowPixelsY } ?: 0f
        val phaseHistogram = LongArray(5)
        RandomAccessFile(outputFile, "rw").use { out ->
            RandomAccessFile(phaseSupportFile, "rw").use { phaseOut ->
            out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)
            phaseOut.setLength(fullOutputWidth.toLong() * fullOutputHeight)
            var top = 0
            while (top < fullOutputHeight) {
                val tileHeight = minOf(TRUE2X_CPU_TILE_HEIGHT, fullOutputHeight - top)
                var left = 0
                while (left < fullOutputWidth) {
                    val tileWidth = minOf(TRUE2X_CPU_TILE_WIDTH, fullOutputWidth - left)
                    val pixelCount = Math.multiplyExact(tileWidth, tileHeight)
                    val accumulator = allocateTrue2xHostBuffer(
                        Math.multiplyExact(pixelCount, TRUE2X_ACCUMULATOR_BYTES_PER_PIXEL),
                        "IRIS26564 CPU accumulator",
                        zero = true,
                    )
                    val phase = allocateTrue2xHostBuffer(
                        pixelCount, "IRIS26564 CPU phase occupancy", zero = true,
                    )
                    var resolved: ByteBuffer? = null
                    try {
                    for (ev in evidence) {
                        val rawRect = true2xRegionForOutput(
                            left, top, tileWidth, tileHeight,
                            ev.maxAbsFlowPixelsX, ev.maxAbsFlowPixelsY,
                        )
                        val rawLeft = rawRect[0]; val rawTop = rawRect[1]
                        val rawWidth = rawRect[2] - rawLeft; val rawHeight = rawRect[3] - rawTop
                        val covRect = true2xRawScaledRegion(
                            rawRect, ev.covarianceWidth, ev.covarianceHeight, TRUE2X_EVIDENCE_HALO,
                        )
                        val covLeft = covRect[0]; val covTop = covRect[1]
                        val covWidth = covRect[2] - covLeft; val covHeight = covRect[3] - covTop
                        val rejRect = true2xScaledRegion(
                            left, top, tileWidth, tileHeight,
                            fullOutputWidth, fullOutputHeight,
                            ev.rejectionWidth, ev.rejectionHeight, TRUE2X_EVIDENCE_HALO,
                        )
                        val rejLeft = rejRect[0]; val rejTop = rejRect[1]
                        val rejWidth = rejRect[2] - rejLeft; val rejHeight = rejRect[3] - rejTop
                        readTrue2xRawRegion(images[ev.frameIndex], rawLeft, rawTop, rawWidth, rawHeight).use { raw ->
                            val cov = readTrue2xFileRegion(
                                ev.covarianceFile, ev.covarianceWidth, 4,
                                covLeft, covTop, covWidth, covHeight, "True2x covariance",
                            )
                            val rejection = ev.rejectionFile?.let { file ->
                                readTrue2xFileRegion(
                                    file, ev.rejectionWidth, 1,
                                    rejLeft, rejTop, rejWidth, rejHeight, "True2x rejection",
                                )
                            }
                            try {
                                check(
                                    IrisTrue2xSrNative.accumulateCpuTileFrame(
                                        accumulator, phase,
                                        tileWidth, tileHeight, left, top,
                                        fullOutputWidth, fullOutputHeight,
                                        raw.buffer, rawLeft, rawTop, rawWidth, rawHeight,
                                        raw.rowStrideSamples,
                                        ev.flowData.duplicate().order(ByteOrder.nativeOrder()),
                                        ev.flowWidth, ev.flowHeight,
                                        ev.flowScaleX, ev.flowScaleY, ev.flowOffsetX, ev.flowOffsetY,
                                        cov, covLeft, covTop, covWidth, covHeight,
                                        ev.covarianceWidth, ev.covarianceHeight,
                                        rejection, rejLeft, rejTop, rejWidth, rejHeight,
                                        ev.rejectionWidth, ev.rejectionHeight,
                                        width, height, cfaPattern,
                                        ev.calibration.gains, ev.calibration.blackTerms,
                                        floatArrayOf(
                                            COV_MIN_R, COV_MAX_R - COV_MIN_R,
                                            COV_MIN_G, COV_MAX_G - COV_MIN_G,
                                        ),
                                        floatArrayOf(COV_MIN_B, COV_MAX_B - COV_MIN_B),
                                        ev.useFrameWeight, sensorWhiteLevel * 0.985f,
                                    )
                                ) { "IRIS26564 CPU accumulation failed frame=${ev.frameIndex}" }
                            } finally {
                                LargeDirectBuffer.free(cov)
                                LargeDirectBuffer.free(rejection)
                            }
                        }
                    }
                    resolved = allocateTrue2xHostBuffer(
                        Math.multiplyExact(pixelCount, TRUE2X_RGB16F_BYTES_PER_PIXEL),
                        "IRIS26564 CPU RGB16F resolve",
                    )
                    check(
                        IrisTrue2xSrNative.resolveCpuTile(
                            accumulator, checkNotNull(resolved), tileWidth, tileHeight,
                            left, top, fullOutputWidth, fullOutputHeight,
                            cameraDomainScale, lensShading, lensShadingWidth, lensShadingHeight,
                        )
                    ) { "IRIS26564 CPU resolve failed tile=$left,$top" }
                    checkNotNull(resolved).position(0)
                    writeTrue2xTileRows(
                        out, checkNotNull(resolved), left, top, tileWidth, tileHeight,
                        fullOutputWidth, TRUE2X_RGB16F_BYTES_PER_PIXEL,
                    )
                    phase.position(0)
                    updateTrue2xPhaseHistogram(phase, pixelCount, phaseHistogram)
                    writeTrue2xPhaseSupportTile(
                        phaseOut, phase, left, top, tileWidth, tileHeight, fullOutputWidth, false,
                        temporalAccumulator = accumulator,
                    )
                    } finally {
                        LargeDirectBuffer.free(resolved)
                        LargeDirectBuffer.free(phase)
                        LargeDirectBuffer.free(accumulator)
                    }
                    left += tileWidth
                }
                top += tileHeight
            }
            phaseOut.fd.sync()
            }
        }
        return true2xPhaseStats(phaseHistogram)
    }

    private fun uploadTrue2xTexture(
        width: Int,
        height: Int,
        internalFormat: Int,
        format: Int,
        type: Int,
        filter: Int,
        data: ByteBuffer,
        label: String,
        unpackRowLength: Int = 0,
    ): Int {
        val texture = createTexture(width, height, internalFormat, filter)
        GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, unpackRowLength)
        data.position(0)
        try {
            GLES30.glTexSubImage2D(
                GLES30.GL_TEXTURE_2D, 0, 0, 0, width, height, format, type, data,
            )
        } finally {
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, 0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        }
        checkGlError(label)
        return texture
    }

    private fun encodeTrue2xActivityGrid(grid: LongArray, channel: Int): String {
        require(channel in 1..2)
        require(grid.size == TRUE2X_PROOF_GRID_WIDTH * TRUE2X_PROOF_GRID_HEIGHT * 3)
        val digits = "0123456789abcdef"
        return buildString(TRUE2X_PROOF_GRID_WIDTH * TRUE2X_PROOF_GRID_HEIGHT + TRUE2X_PROOF_GRID_HEIGHT - 1) {
            for (y in 0 until TRUE2X_PROOF_GRID_HEIGHT) {
                if (y > 0) append('/')
                for (x in 0 until TRUE2X_PROOF_GRID_WIDTH) {
                    val q = (y * TRUE2X_PROOF_GRID_WIDTH + x) * 3
                    val total = grid[q]
                    val value = if (total > 0L) ((15.0 * grid[q + channel].toDouble() / total.toDouble()) + 0.5).toInt().coerceIn(0, 15) else 0
                    append(digits[value])
                }
            }
        }
    }

    private fun runTrue2xGpu(
        images: List<SafeImage>,
        evidence: List<True2xFrameEvidence>,
        directOutputFile: File?,
        renderOutputFile: File,
        nativeVgnGuideTexture: Int,
        fullOutputWidth: Int,
        fullOutputHeight: Int,
    ): True2xPhaseStats {
        if (true2xMergeProgram26564 == 0) {
            true2xMergeProgram26564 = linkProgram(
                GlesMgcRawSabreShaders.true2xMerge26564, "iris_26564_true2x_merge",
            )
        }
        if (true2xResolveProgram26564 == 0) {
            true2xResolveProgram26564 = linkProgram(
                GlesMgcRawSabreShaders.true2xResolve26564, "iris_26564_true2x_resolve",
            )
        }
        if (true2xGuideRenderProgram26568 == 0) {
            true2xGuideRenderProgram26568 = linkProgram(
                GlesMgcRawSabreShaders.true2xGuideRender26568, "iris_26568_true2x_guide_render",
            )
        }
        require(nativeVgnGuideTexture != 0) { "26568 true2x requires live native Sabre/VGN guide texture" }
        val maxTexture = IntArray(1)
        GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE, maxTexture, 0)
        checkGlError("IRIS26568 query GL_MAX_TEXTURE_SIZE")
        require(maxTexture[0] >= TRUE2X_GPU_MIN_TEXTURE_SIZE) {
            "GPU max texture ${maxTexture[0]} below true2x minimum $TRUE2X_GPU_MIN_TEXTURE_SIZE"
        }
        /* IRIS_26568_WIDE_EVEN_TRUE2X_BANDS
         * 2x2 true-detail luminance blocks must never cross a tile edge. fullOutput dimensions are even;
         * force even origins/extents and widen to the device limit to eliminate repeated evidence
         * file reads/uploads without changing per-pixel RBF equations or per-frame blend order.
         */
        val tileWidthLimit = minOf(fullOutputWidth, maxTexture[0], TRUE2X_GPU_MAX_BAND_WIDTH).and(-2)
        val tileHeightLimit = minOf(TRUE2X_GPU_TILE_HEIGHT, maxTexture[0]).and(-2)
        require(tileWidthLimit >= 2 && tileHeightLimit >= 2)
        val phaseHistogram = LongArray(5)
        val reasonHistogram = LongArray(8)
        val activityGrid = LongArray(TRUE2X_PROOF_GRID_WIDTH * TRUE2X_PROOF_GRID_HEIGHT * 3)
        val lensTexture = if (hasLensShading()) createLensShadingTexture() else 0
        val directOut = directOutputFile?.let { RandomAccessFile(it, "rw") }
        try {
            RandomAccessFile(renderOutputFile, "rw").use { renderOut ->
                val bytes = fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL
                directOut?.setLength(bytes)
                renderOut.setLength(bytes)
                var top = 0
                var bands = 0
                while (top < fullOutputHeight) {
                    var tileHeight = minOf(tileHeightLimit, fullOutputHeight - top)
                    if ((tileHeight and 1) != 0) tileHeight--
                    require(tileHeight > 0)
                    var left = 0
                    while (left < fullOutputWidth) {
                        var tileWidth = minOf(tileWidthLimit, fullOutputWidth - left)
                        if ((tileWidth and 1) != 0) tileWidth--
                        require(tileWidth > 0 && (left and 1) == 0 && (top and 1) == 0)
                        val tileStart = textures.size
                        val color = createTexture(tileWidth, tileHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
                        val weights = createTexture(tileWidth, tileHeight, GLES30.GL_RG16F, GLES30.GL_NEAREST)
                        val phase = createTexture(tileWidth, tileHeight, GLES30.GL_RGBA8, GLES30.GL_NEAREST)
                        val temporal = createTexture(tileWidth, tileHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
                        try {
                            bindRenderTargets(intArrayOf(color, weights, phase, temporal), "IRIS26573 true2x band clear")
                            GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f, 0f, 0f, 0f), 0)
                            GLES30.glClearBufferfv(GLES30.GL_COLOR, 1, floatArrayOf(0f, 0f, 0f, 0f), 0)
                            GLES30.glClearBufferfv(GLES30.GL_COLOR, 2, floatArrayOf(0f, 0f, 0f, 0f), 0)
                            GLES30.glClearBufferfv(GLES30.GL_COLOR, 3, floatArrayOf(0f, 0f, 0f, 0f), 0)
                            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
                            for (ev in evidence) {
                                val rawRect = true2xRegionForOutput(
                                    left, top, tileWidth, tileHeight, ev.maxAbsFlowPixelsX, ev.maxAbsFlowPixelsY,
                                )
                                val rawLeft=rawRect[0]; val rawTop=rawRect[1]
                                val rawWidth=rawRect[2]-rawLeft; val rawHeight=rawRect[3]-rawTop
                                val covRect=true2xRawScaledRegion(rawRect,ev.covarianceWidth,ev.covarianceHeight,TRUE2X_EVIDENCE_HALO)
                                val covLeft=covRect[0]; val covTop=covRect[1]
                                val covWidth=covRect[2]-covLeft; val covHeight=covRect[3]-covTop
                                val rejRect=true2xScaledRegion(left,top,tileWidth,tileHeight,fullOutputWidth,fullOutputHeight,ev.rejectionWidth,ev.rejectionHeight,TRUE2X_EVIDENCE_HALO)
                                val rejLeft=rejRect[0]; val rejTop=rejRect[1]
                                val rejWidth=rejRect[2]-rejLeft; val rejHeight=rejRect[3]-rejTop
                                readTrue2xRawRegion(images[ev.frameIndex],rawLeft,rawTop,rawWidth,rawHeight).use { raw ->
                                    val cov=readTrue2xFileRegion(ev.covarianceFile,ev.covarianceWidth,4,covLeft,covTop,covWidth,covHeight,"True2x GPU covariance")
                                    val rejection=ev.rejectionFile?.let { file ->
                                        readTrue2xFileRegion(file,ev.rejectionWidth,1,rejLeft,rejTop,rejWidth,rejHeight,"True2x GPU rejection")
                                    } ?: allocateTrue2xHostBuffer(1,"IRIS26568 identity rejection").apply { put(0,0xff.toByte()) }
                                    try {
                                        val rawTexture=uploadTrue2xTexture(rawWidth,rawHeight,GLES30.GL_R16UI,GLES30.GL_RED_INTEGER,GLES30.GL_UNSIGNED_SHORT,GLES30.GL_NEAREST,raw.buffer,"IRIS26568 true2x raw upload",unpackRowLength=raw.rowStrideSamples)
                                        val flowTexture=uploadTrue2xTexture(ev.flowWidth,ev.flowHeight,GLES30.GL_RGBA16F,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,GLES30.GL_LINEAR,ev.flowData.duplicate().order(ByteOrder.nativeOrder()),"IRIS26568 true2x flow upload")
                                        val covTexture=uploadTrue2xTexture(covWidth,covHeight,GLES30.GL_RGB10_A2,GLES30.GL_RGBA,GLES30.GL_UNSIGNED_INT_2_10_10_10_REV,GLES30.GL_LINEAR,cov,"IRIS26568 true2x covariance upload")
                                        val rejectionTexture=uploadTrue2xTexture(if(ev.useFrameWeight)rejWidth else 1,if(ev.useFrameWeight)rejHeight else 1,GLES30.GL_R8,GLES30.GL_RED,GLES30.GL_UNSIGNED_BYTE,GLES30.GL_LINEAR,rejection,"IRIS26568 true2x rejection upload")
                                        try {
                                            val program=true2xMergeProgram26564
                                            GLES30.glUseProgram(program)
                                            bindTexture(program,"uRawRegion",0,rawTexture); bindTexture(program,"uFlow",1,flowTexture); bindTexture(program,"uCovarianceRegion",2,covTexture); bindTexture(program,"uRejectionRegion",3,rejectionTexture)
                                            uniform2i(program,"uRawOrigin",rawLeft,rawTop); uniform2i(program,"uRawRegionSize",rawWidth,rawHeight); uniform2i(program,"uRawFullSize",width,height)
                                            uniform2i(program,"uCovarianceOrigin",covLeft,covTop); uniform2i(program,"uCovarianceRegionSize",covWidth,covHeight); uniform2i(program,"uCovarianceFullSize",ev.covarianceWidth,ev.covarianceHeight)
                                            uniform2i(program,"uRejectionOrigin",rejLeft,rejTop); uniform2i(program,"uRejectionRegionSize",rejWidth,rejHeight); uniform2i(program,"uRejectionFullSize",ev.rejectionWidth,ev.rejectionHeight)
                                            uniform2i(program,"uOutputOrigin",left,top); uniform2i(program,"uOutputFullSize",fullOutputWidth,fullOutputHeight)
                                            uniform4f(program,"uFlowScaleOffset",ev.flowScaleX,ev.flowScaleY,ev.flowOffsetX,ev.flowOffsetY)
                                            uniform1i(program,"uCfaPattern",cfaPattern); uniform1i(program,"uUseFrameWeight",if(ev.useFrameWeight)1 else 0)
                                            uniform4fv(program,"uGains",ev.calibration.gains); uniform4fv(program,"uBlackLevelsTimesGains",ev.calibration.blackTerms)
                                            uniform4f(program,"uCovRangeRg",COV_MIN_R,COV_MAX_R-COV_MIN_R,COV_MIN_G,COV_MAX_G-COV_MIN_G); uniform2f(program,"uCovRangeB",COV_MIN_B,COV_MAX_B-COV_MIN_B)
                                            uniform1f(program,"uRawClipThreshold",sensorWhiteLevel*0.985f)
                                            GLES30.glEnable(GLES30.GL_BLEND); GLES30.glBlendEquation(GLES30.GL_FUNC_ADD); GLES30.glBlendFunc(GLES30.GL_ONE,GLES30.GL_ONE)
                                            draw(program,tileWidth,tileHeight,intArrayOf(color,weights,phase,temporal),preserveBlend=true); GLES30.glDisable(GLES30.GL_BLEND)
                                        } finally {
                                            releaseOwnedTexture(rawTexture,"IRIS26568 raw band"); releaseOwnedTexture(flowTexture,"IRIS26568 flow band"); releaseOwnedTexture(covTexture,"IRIS26568 covariance band"); releaseOwnedTexture(rejectionTexture,"IRIS26568 rejection band")
                                        }
                                    } finally { LargeDirectBuffer.free(rejection); LargeDirectBuffer.free(cov) }
                                }
                            }
                            val resolved=createTexture(tileWidth,tileHeight,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
                            var program=true2xResolveProgram26564
                            GLES30.glUseProgram(program); bindTexture(program,"uAccumulatedColor",0,color); bindTexture(program,"uAccumulatedWeightsGb",1,weights); if(lensTexture!=0)bindTexture(program,"uLensShading",2,lensTexture)
                            uniform2i(program,"uOutputOrigin",left,top); uniform2i(program,"uOutputFullSize",fullOutputWidth,fullOutputHeight); uniform3f(program,"uCameraDomainScale",cameraDomainScale[0],cameraDomainScale[1],cameraDomainScale[2]); uniform1i(program,"uUseLensShading",if(lensTexture!=0)1 else 0)
                            draw(program,tileWidth,tileHeight,intArrayOf(resolved))
                            // DNG, when requested, sees the exact existing resolved RGBA16F boundary before VGN.
                            directOut?.let { writeTrue2xGpuRgbTile(it,resolved,left,top,tileWidth,tileHeight,fullOutputWidth,"IRIS26568 direct DNG") }
                            val render=createTexture(tileWidth,tileHeight,GLES30.GL_RGBA16F,GLES30.GL_NEAREST)
                            program=true2xGuideRenderProgram26568; GLES30.glUseProgram(program); bindTexture(program,"uDirectRgb",0,resolved); bindTexture(program,"uPhaseOccupancy",1,phase); bindTexture(program,"uNativeVgnGuide",2,nativeVgnGuideTexture); bindTexture(program,"uTemporalLumaStats",3,temporal)
                            uniform2i(program,"uOutputOrigin",left,top); uniform2i(program,"uOutputFullSize",fullOutputWidth,fullOutputHeight); uniform2i(program,"uGuideSize",width,height)
                            draw(program,tileWidth,tileHeight,intArrayOf(render))
                            writeTrue2xGpuRgbTile(renderOut,render,left,top,tileWidth,tileHeight,fullOutputWidth,"IRIS26573 fused render",phaseHistogram,reasonHistogram,activityGrid,fullOutputHeight)
                            checkGlError("IRIS26568 true2x GPU band")
                        } finally { releaseTexturesFrom(tileStart) }
                        left += tileWidth
                    }
                    top += tileHeight; bands++; GlesGpuScheduler.yieldToUiRenderer()
                }
                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_GPU_BANDS width=$tileWidthLimit height=$tileHeightLimit bands=$bands evidence=${evidence.size} directDng=${directOut!=null} ephemeralFsync=false")
            }
        } finally {
            directOut?.close()
            if(lensTexture!=0&&textures.contains(lensTexture))releaseOwnedTexture(lensTexture,"IRIS26568 lens shading")
        }
        val phaseStats = true2xPhaseStats(phaseHistogram)
        val expectedPixels = fullOutputWidth.toLong() * fullOutputHeight.toLong()
        val reasonTotal = reasonHistogram.sum()
        check(phaseHistogram.sum() == expectedPixels) { "26573 phase proof incomplete ${phaseHistogram.sum()}/$expectedPixels" }
        check(reasonTotal == expectedPixels) { "26573 SR reason proof incomplete $reasonTotal/$expectedPixels" }
        check(activityGrid.indices.filter { it % 3 == 0 }.sumOf { activityGrid[it] } == expectedPixels) {
            "26573 SR activity grid incomplete"
        }
        val activePixels = reasonHistogram[1] + reasonHistogram[2]
        val strongPixels = reasonHistogram[2]
        fun pct(value: Long) = 100.0 * value.toDouble() / expectedPixels.toDouble()
        val activeMap = encodeTrue2xActivityGrid(activityGrid, 1)
        val strongMap = encodeTrue2xActivityGrid(activityGrid, 2)
        val proof = "backend=GPU totalPixels=$expectedPixels activePixels=$activePixels activePct=${pct(activePixels)} " +
            "strongPixels=$strongPixels strongPct=${pct(strongPixels)} temporalRejected=${reasonHistogram[3]} temporalRejectedPct=${pct(reasonHistogram[3])} " +
            "highlightRejected=${reasonHistogram[4]} disagreementRejected=${reasonHistogram[5]} phaseRejected=${reasonHistogram[6]} " +
            "signalRejected=${reasonHistogram[7]} fallbackOther=${reasonHistogram[0]} phase0=${phaseHistogram[0]} phase1=${phaseHistogram[1]} " +
            "phase2=${phaseHistogram[2]} phase3=${phaseHistogram[3]} phase4=${phaseHistogram[4]} highResLumaOwner=DIRECT_CFA_TEMPORAL " +
            "sabreRgbChromaOwner=true directChromaOwner=false secondReadback=false activeMap32x24=$activeMap strongMap32x24=$strongMap"
        PLog.i(SABRE_TAG, "IRIS_26573_SR_PROOF $proof")
        MotionTrace.processingState("IRIS_26573_SR_PROOF", proof)
        return phaseStats
    }

    private fun reconstructTrue2x(
        frames: List<RawStackFrame>,
        images: List<SafeImage>,
        evidence: List<True2xFrameEvidence>,
        nativeVgnGuideTexture: Int,
        preserveLinearRgbForDng: Boolean,
    ): True2xResult {
        require(enableSabreSuperRes)
        require(evidence.isNotEmpty()) { "True2x has no NORMAL Sabre evidence" }
        val directory=checkNotNull(sabreSuperResTempDir); require(directory.exists()||directory.mkdirs())
        val outputWidth=Math.multiplyExact(width,2); val outputHeight=Math.multiplyExact(height,2); val start=System.nanoTime()
        val directGpuFile=if(preserveLinearRgbForDng) File(directory,"iris26568_true2x_direct_${System.nanoTime()}.rgb16f") else null
        val renderGpuFile=File(directory,"iris26568_true2x_render_${System.nanoTime()}.rgb16f")
        val gpuAttempt=runCatching {
            val phase=runTrue2xGpu(images,evidence,directGpuFile,renderGpuFile,nativeVgnGuideTexture,outputWidth,outputHeight)
            True2xResult(directGpuFile?.absolutePath,renderGpuFile.absolutePath,null,null,outputWidth,outputHeight,"GPU",phase.mean,phase.p10,elapsedMs(start))
        }
        if(gpuAttempt.isSuccess)return gpuAttempt.getOrThrow()
        val gpuFailure=gpuAttempt.exceptionOrNull()?:IllegalStateException("IRIS_26568_TRUE2X_GPU_FALLBACK_CPU unknown GPU failure")
        PLog.e(SABRE_TAG,"IRIS_26568_TRUE2X_GPU_FALLBACK_CPU reason=${gpuFailure.message}",gpuFailure)
        MotionTrace.processingState(
            "IRIS_26576_SR_RECONSTRUCTION_GPU_FALLBACK",
            "reason=${gpuFailure.javaClass.simpleName}:${gpuFailure.message} gpuAttemptMs=${elapsedMs(start)} cpuFallback=true",
        )
        runCatching { directGpuFile?.delete() }; runCatching { renderGpuFile.delete() }
        // CPU fallback intentionally retains the exact 26567 file-based guide/phase derivative path.
        val nativeGuide=streamTrue2xNativeVgnGuideRgb16f(nativeVgnGuideTexture)
        val cpuStart=System.nanoTime(); val cpuFile=File(directory,"iris26568_true2x_cpu_${System.nanoTime()}.rgb16f"); val cpuPhaseFile=File(directory,"iris26568_true2x_phase_cpu_${System.nanoTime()}.u8")
        return try {
            val phase=runTrue2xCpu(frames,images,evidence,cpuFile,cpuPhaseFile,outputWidth,outputHeight)
            val cpuMs = elapsedMs(cpuStart)
            /* IRIS_26576_CPU_SR_PROOF_NO_EXTRA_READBACK
             * CPU reconstruction already packs phase count + temporal agreement into the existing
             * 26573 phase-support carrier. Report that authority without rereading the carrier.
             */
            MotionTrace.processingState(
                "IRIS_26576_SR_CPU_PROOF",
                "backend=CPU evidence=${evidence.size} crossFrame=${evidence.size > 1} " +
                    "phaseMean=${phase.mean} phaseP10=${phase.p10} temporalProofPacked=true " +
                    "highResLumaOwner=DIRECT_CFA_TEMPORAL directChromaOwner=false cpuMs=$cpuMs",
            )
            True2xResult(cpuFile.absolutePath,null,nativeGuide.absolutePath,cpuPhaseFile.absolutePath,outputWidth,outputHeight,"CPU",phase.mean,phase.p10,cpuMs)
        } catch(error:Throwable) { runCatching{nativeGuide.delete()};runCatching{cpuFile.delete()};runCatching{cpuPhaseFile.delete()};throw error }
    }

    private fun cleanupTrue2xEvidence(evidence: List<True2xFrameEvidence>) {
        evidence.forEach { ev ->
            LargeDirectBuffer.free(ev.flowData)
            runCatching { ev.covarianceFile.delete() }
            runCatching { ev.rejectionFile?.delete() }
        }
    }

    private companion object {
        fun gaussianKernel(size: Int, sigma: Float): FloatArray {
            require(size > 0)
            require(sigma.isFinite() && sigma > 0f)
            val center = (size - 1) / 2
            val sigmaSquaredTimesTwo = 2.0 * sigma.toDouble() * sigma.toDouble()
            val values = DoubleArray(size) { index ->
                val distance = (index - center).toDouble()
                exp(-(distance * distance) / sigmaSquaredTimesTwo)
            }
            val sum = values.sum()
            return FloatArray(size) { index -> (values[index] / sum).toFloat() }
        }

        const val TAG = "GlesMgcRawSpatial"
        const val SABRE_TAG = "GlesMgcRawSabre"
        const val SABRE_READBACK_ROWS = 64
        const val SABRE_DNG_SUPPORT_MAX_SAMPLES = 262144
        // MGC 9.6.080 SabreKernelParams defaults. BuildSabreKernelParamsForSnr tunes only the
        // first six floats; these two Resolve interpolation endpoints remain 3 and 4. The
        // original wrapper converts them to scale=-range*frameCount and bias=end/range.
        const val SABRE_DEMOSAIC_BLEND_START = 3f
        const val SABRE_DEMOSAIC_BLEND_END = 4f
        const val SABRE_RESOLVE_INPUT_WHITE_LEVEL = 16384f
        // Guide/covariance has a wider MGC footprint than rejection/RBF sampling.
        const val SABRE_GUIDE_BORDER_PIXELS = 2.5f
        const val SABRE_SAMPLE_BORDER_PIXELS = 1.5f
        private const val SHORT_REGION_PROPAGATION_PASSES_26594 = 32
        private const val SABRE_SUPER_RES_LINEAR_RAW_BAND_HEIGHT = 64
        private const val SABRE_SUPER_RES_DETAIL_BAND_HEIGHT = 256
        private const val TRUE2X_CPU_TILE_WIDTH = 512
        private const val TRUE2X_CPU_TILE_HEIGHT = 128
        // 26567 used 1024x128 tiles. 26568 keeps the proven 128-row memory bound but widens
        // the band to reduce repeated RAW/covariance/rejection/flow uploads.
        private const val TRUE2X_GPU_MAX_BAND_WIDTH = 8192
        private const val TRUE2X_GPU_TILE_HEIGHT = 128
        /* 16 RAW pixels = 8 Bayer quads. This is four times denser per axis than the finest
         * ~32-Bayer-quad LK grid while remaining a small bounded flow sidecar (~255x192 at 4080x3064).
         */
        private const val TRUE2X_REFINE_CELL_RAW_PIXELS = 16
        private const val TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2
        private const val TRUE2X_JPEG_MAX_EVIDENCE = 4 * TRUE2X_JPEG_EVIDENCE_PER_PHASE
        private const val TRUE2X_GPU_MIN_TEXTURE_SIZE = 1024
        private const val TRUE2X_RAW_RBF_HALO = 4f
        private const val TRUE2X_EVIDENCE_HALO = 2
        private const val TRUE2X_VGN_GUIDE_BAND_HEIGHT = 128
        private const val TRUE2X_ACCUMULATOR_FLOATS_PER_PIXEL = 10
        private const val TRUE2X_ACCUMULATOR_BYTES_PER_PIXEL = TRUE2X_ACCUMULATOR_FLOATS_PER_PIXEL * Float.SIZE_BYTES
        private const val TRUE2X_RGB16F_BYTES_PER_PIXEL = 3 * Short.SIZE_BYTES
        private const val TRUE2X_PROOF_GRID_WIDTH = 32
        private const val TRUE2X_PROOF_GRID_HEIGHT = 24
        private const val SABRE_LONG_DURATION_ROBUSTNESS_MAX = 4f
        const val SABRE_SIGNAL_LINEAR_HISTOGRAM_BITS = 10
        const val SABRE_SIGNAL_LINEAR_HISTOGRAM_BINS = 1 shl SABRE_SIGNAL_LINEAR_HISTOGRAM_BITS
        const val SABRE_SIGNAL_ROW_STEP = 8
        const val EGL_OPENGL_ES3_BIT_KHR = 0x00000040
        const val RAW_BYTES_PER_PIXEL = 2
        const val RGB_RAW_WINDOW_SLOTS = 2
        const val RGB_MAX_IN_FLIGHT_PASSES = 2
        const val RGB_DIAGNOSTIC_PBO_SLOTS = 2
        const val RGB_TEXTURE_BUDGET_BYTES = 640L * 1024L * 1024L
        const val RGB_TEXTURE_BUDGET_RESERVE_BYTES = 8L * 1024L * 1024L
        const val RGB_ONLINE_DRAW_BAND_HEIGHT = 1024
        const val RGB_CHROMA_GUIDE_RAW_RADIUS = 2
        const val NOISE_LUT_WIDTH = 10
        const val ALIGN_TARGET_FINEST_DIMENSION = 256
        const val ALIGN_MIN_TILE_SIZE = 8
        const val ALIGN_MAX_TILE_SIZE = 64
        const val ALIGN_LK_ITERATIONS_FINEST = 2
        const val ALIGN_LK_ITERATIONS_COARSER = 3
        // Every LK iteration clamps its update to one pixel in that pyramid level. Mapped back
        // to Bayer quads, the 32x/8x/2x/1x schedule is bounded by
        // 3*32 + 3*8 + 3*2 + 2*1 = 128. Using the analytical bound keeps RGB tile planning on
        // the GPU command stream instead of synchronously reading every alignment texture.
        const val MAX_ALIGNMENT_DISPLACEMENT_BAYER_QUADS = 128f
        const val ALIGN_LK_GRID_MIN = 1
        const val MERGE_BAYER_RAW_TILE_SIZE = 16
        // MGC defines the tolerance as a fraction of its 8 Bayer-quad tile. Keep
        // interpolation only where every neighboring flow is within one raw pixel
        // (half a Bayer quad) of the current tile; larger discontinuities retain the
        // piecewise-constant flow and are handled by rejection.
        const val SPATIAL_INTERPOLATION_FLOW_TOLERANCE = 1f / 16f
        val ALIGN_PYRAMID_DOWNSAMPLE_STEPS = intArrayOf(2, 4, 4)
        // Indexed from the finest one-sample-per-Bayer-quad level to the coarsest.
        val ALIGN_LEVEL_TILE_STRIDES = intArrayOf(32, 32, 16, 8)
        // Captured at UnblockerRaw10Halide entry on the original MGC full-resolution path.
        const val UNBLOCKER_FULLRES_TILE_SIZE = 8
        const val UNBLOCKER_OUTPUT_SCALE = 1f
        const val UNBLOCKER_OUTPUT_OFFSET = 0.45f
        const val MIN_EXPOSURE_SCALE = 1f / 64f
        const val MAX_EXPOSURE_SCALE = 64f
        const val MIN_WHITE_BALANCE_GAIN = 1e-3f
        const val MAX_WHITE_BALANCE_GAIN = 64f
        const val MIN_NOISE_VARIANCE = 1e-12f
        const val SPATIAL_IDENTITY_MULTIPLIER = 1f
        const val SPATIAL_IDENTITY_READ_NOISE = 0f
        const val SPATIAL_IDENTITY_SHOT_NOISE = 1f
        const val SPATIAL_IDENTITY_STRENGTH_Q8 = 256
        // FilterRejectionMap runtime values read from the original MGC process. The
        // ClippedGaussian formula and tap center were independently verified against its AOT.
        const val PIXEL_DIFFERENCE_KERNEL_SIZE = 20
        // Packed precision-matrix ranges used by MGC MergeRgbRaw.
        const val COV_MIN_R = 0.3671880066f
        const val COV_MAX_R = 24.8149185f
        const val COV_MIN_G = 0.3671880066f
        const val COV_MAX_G = 26.0516777f
        const val COV_MIN_B = -6.97557068f
        const val COV_MAX_B = 7.02652168f
        const val RGB_CHROMA_EDGE_NOISE_SIGMAS = 2.5f
        const val RGB_CHROMA_EDGE_SIGMA_FLOOR = 1f / 160f
        const val PIXEL_DIFFERENCE_SMOOTH_SIGMA = 500f
        const val PIXEL_DIFFERENCE_THRESHOLD = 150f
        const val REJECTION_FILTER_DOWNSAMPLE = 4
        const val REJECTION_FILTER_COLOR_SIGMA = 0.00005f
        const val REJECTION_FILTER_SPATIAL_SIGMA = 4f
        const val REJECTION_FILTER_COLOR_SIGMA_BOOST = 500f
        const val REJECTION_FILTER_MAX_RADIUS = 3
        const val REJECTION_CLIPPED_THRESHOLD = 3f

        // Bento option instances recovered from libgcastartup.so.
        const val BENTO_MIN_NORMALIZED_INTENSITY_ERROR = 0.9f
        const val BENTO_MAX_RGB_CLIPPING = 250f
        const val BENTO_MIN_RGB_FOR_INPAINTING = 128f
        const val BENTO_MIN_CLIPPED_PIXEL_RATIO = 0.00039f
        const val BENTO_MAX_INPAINTING_COMPONENT_AREA = 80
        const val BENTO_MAX_TILING_COMPONENT_AREA = 5
        const val BENTO_MAX_ULTRASHORT_CLIPPING_OVERLAP = 0.62f
        const val LONG_FRAME_RAW_CLIPPING_THRESHOLD = 250f / 255f

    }
}
