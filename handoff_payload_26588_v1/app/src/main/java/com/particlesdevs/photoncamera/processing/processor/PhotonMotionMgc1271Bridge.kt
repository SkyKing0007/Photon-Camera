package com.particlesdevs.photoncamera.processing.processor

import android.graphics.ImageFormat
import android.graphics.Point
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.GLES20
import android.opengl.GLES30
import android.os.Build
import android.util.Half
import com.hinnka.mycamera.model.SafeImage
import com.hinnka.mycamera.processor.GlesGpuScheduler
import com.hinnka.mycamera.processor.GlesMgcRawFusion
import com.hinnka.mycamera.processor.GpuLinearRgbStorage
import com.hinnka.mycamera.processor.RawBurstFrameRole
import com.hinnka.mycamera.processor.RawNoiseProfileSelection
import com.hinnka.mycamera.processor.RawNoiseModel
import com.hinnka.mycamera.processor.RawStackBufferLayout
import com.hinnka.mycamera.processor.RawStackFrame
import com.hinnka.mycamera.raw.MgcFullResolutionDenoise
import com.hinnka.mycamera.raw.RawMetadata
import com.hinnka.mycamera.raw.RawNoiseProfileLayout
import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.app.PhotonCamera
import com.particlesdevs.photoncamera.processing.ImageFrame
import com.particlesdevs.photoncamera.processing.MotionBatch
import com.particlesdevs.photoncamera.processing.render.Parameters
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * IRIS_26560_SABRE_ONLY_BRIDGE_OWNER
 *
 * Photon capture/AE feeds one proven reconstruction owner: Sabre. Spatial-RGB selection,
 * Spatial-only reliability/source-restore, and the old Wronski/hybrid SR backend are removed.
 * The public Super Res switch remains frozen into Parameters for the following Sabre-SR step,
 * but 26560 deliberately keeps the proven Sabre native-grid output contract.
 */
object PhotonMotionMgc1271Bridge {
    private const val TAG = "Mgc1271Bridge"
    private const val EGL_OPENGL_ES3_BIT_KHR = 0x40
    private const val HALF_ONE: Short = 0x3c00

    init {
        System.loadLibrary("my-native-lib")
    }

    @JvmStatic
    fun reconstruct(
        size: Point,
        inputImages: List<ImageFrame>,
        referenceTimestamp: Long,
        parameters: Parameters,
        shortSlot: MotionBatch.ShortHighlightSlot?,
        /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_REQUEST */
        produceNormalStackedDng: Boolean,
    ): MotionV2Merger.Result {
        var shortFrame: ImageFrame? = null
        var longFrame: ImageFrame? = null
        var egl: EglOwner? = null
        var halfBuffer: ByteBuffer? = null
        var resultTexture = 0
        var true2xLinearRgbPathForCleanup: String? = null
        var true2xNativeVgnGuidePathForCleanup: String? = null
        var true2xPhaseSupportPathForCleanup: String? = null
        var true2xRenderRgbPathForCleanup: String? = null
        var true2xOutputHandedOff = false
        val iris26535TotalStartNs = System.nanoTime()
        var iris26535FusionMs = -1L
        var iris26535DenoiseMs = -1L
        try {
            requireParity(Build.SUPPORTED_ABIS.any { it == "arm64-v8a" },
                "pinned MGC 1.27.1 AOT is arm64-only; device ABIs=${Build.SUPPORTED_ABIS.contentToString()}")
            requireParity(size.x > 1 && size.y > 1 && (size.x and 1) == 0 && (size.y and 1) == 0,
                "invalid RAW geometry ${size.x}x${size.y}")
            requireParity(parameters.cfaPattern.toInt() in 0..3,
                "unsupported CFA=${parameters.cfaPattern}")
            requireParity(inputImages.isNotEmpty(), "no equal-exposure Normal frames")

            val reference = inputImages.firstOrNull { it.timestamp == referenceTimestamp }
                ?: invalid("owned reference is absent timestamp=$referenceTimestamp")
            requireParity(reference.buffer != null, "26543 Night/Motion owned reference must remain in-memory")

            shortFrame = shortSlot?.takeAndSeal()
            longFrame = shortSlot?.shadowAuxSlot?.takeAndSeal()

            // The pinned 1.27.1 GlesMgcRawFusion contract chooses the first supplied NORMAL
            // as its base, preserves the remaining NORMAL order, then admits valid Long and the
            // one lowest-TET Short. HdrxProcessor has already timestamp-sorted the Normal list.
            // Do not impose the old Wronski nearest-reference ordering here.
            val mgcBase = inputImages.firstOrNull { it.motionV2FrameRole == ImageFrame.MotionV2FrameRole.NORMAL }
                ?: invalid("MGC SHORT/NORMAL base is absent")
            val orderedPhysical = ArrayList<Pair<ImageFrame, RawBurstFrameRole>>()
            inputImages.forEachIndexed { index, frame ->
                val role = when (frame.motionV2FrameRole) {
                    ImageFrame.MotionV2FrameRole.NORMAL -> RawBurstFrameRole.NORMAL
                    ImageFrame.MotionV2FrameRole.SHADOW_LONG -> {
                        requireParity(parameters.irisNightActive,
                            "main-list SHADOW_LONG is Night-only index=$index")
                        RawBurstFrameRole.SHADOW_LONG
                    }
                    ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT ->
                        invalid("main-list HIGHLIGHT_SHORT is forbidden; Motion Short keeps isolated slot ownership")
                }
                orderedPhysical += frame to role
            }
            longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }
            shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }

            orderedPhysical.forEachIndexed { index, (frame, role) ->
                validateFrame(frame, size, role, reference.motionV2ExposureEnergy, index)
            }

            // IRIS_26514_STRICT_NOISE_AUTHORITY: no Camera2 base-frame, Pixel, or custom->Camera2 fallback.
            // IRIS_26540_NIGHT_FROZEN_IRIS_SETTINGS
            val irisSettings = if (parameters.irisNightActive) {
                parameters.irisNightSettingsSnapshot
                    ?: throw IllegalStateException("26540 Night missing frozen Iris settings")
            } else {
                IrisMotionSettings.current()
            }
            /* IRIS_26560_SABRE_ONLY_RECONSTRUCTION_AUTHORITY
             * Motion and Night now publish the same sole reconstruction owner. The Super Res
             * request remains frozen in Parameters but cannot reactivate Spatial RGB.
             */
            val vgnChromaCorrectionStrength = if (parameters.irisNightActive) {
                1.0f
            } else {
                irisSettings.vgnChromaCorrection.coerceIn(0.0f, 1.0f)
            }
            parameters.motionV2ReconstructionOwner = Parameters.MOTION_V2_RECONSTRUCTION_SABRE
            PLog.i(TAG, "IRIS_26560_SABRE_ONLY_RECONSTRUCTION " +
                "method=SABRE vgnChromaCorrection=$vgnChromaCorrectionStrength " +
                "night=${parameters.irisNightActive} dngRequested=$produceNormalStackedDng " +
                "superResRequested=${parameters.motionV2SuperResOutputEnabled}")

            val noiseSelection: RawNoiseProfileSelection
            val noiseAuthority: String
            var denoiseNoiseProfileLayout = RawNoiseProfileLayout.NONE
            var denoiseChannelNoiseProfile = floatArrayOf()
            if (irisSettings.customNoiseModelEnabled) {
                val profile = IrisNoiseProfileStore.loadSelectedProfile(
                    PhotonCamera.getApplicationContextStatic())
                    ?: throw IllegalStateException(
                        "IRIS_26514 custom noise model selected but stored profile is unavailable")
                orderedPhysical.forEachIndexed { index, (frame, _) ->
                    val iso = frame.motionV2ActualIso
                    val model = profile.evaluate(iso)
                        ?: throw IllegalStateException(
                            "IRIS_26514 custom noise model cannot evaluate frame=$index iso=$iso")
                    if (model.shotNoise.any { !it.isFinite() || it <= 0f } ||
                        model.readNoise.any { !it.isFinite() } || model.readNoise.none { it > 0f }) {
                        throw IllegalStateException(
                            "IRIS_26514 custom noise model invalid at frame=$index iso=$iso")
                    }
                }
                val baseNoiseModel = profile.evaluate(mgcBase.motionV2ActualIso)
                    ?: throw IllegalStateException(
                        "IRIS_26545 custom noise model cannot evaluate MGC base iso=${mgcBase.motionV2ActualIso}")
                denoiseNoiseProfileLayout = RawNoiseProfileLayout.CANONICAL_BAYER
                denoiseChannelNoiseProfile = baseNoiseModel.canonicalChannelPairs()
                requireParity(
                    denoiseChannelNoiseProfile.size == 8 &&
                        denoiseChannelNoiseProfile.all { it.isFinite() && it >= 0f } &&
                        (0 until 4).all { denoiseChannelNoiseProfile[it * 2] > 0f } &&
                        (0 until 4).any { denoiseChannelNoiseProfile[it * 2 + 1] > 0f },
                    "invalid custom MGC-base denoise noise pairs",
                )
                noiseSelection = RawNoiseProfileSelection.Calibrated(profile)
                noiseAuthority = "CUSTOM:" +
                    irisSettings.profileDisplayName.ifBlank { irisSettings.profileId }
            } else {
                orderedPhysical.forEachIndexed { index, (frame, _) ->
                    if (frame.motionV2NoiseProfileSource != "CAMERA2_PER_FRAME") {
                        throw IllegalStateException(
                            "IRIS_26514 strict Camera2 noise requires per-frame metadata; " +
                                "frame=$index source=${frame.motionV2NoiseProfileSource}")
                    }
                    val model = RawNoiseModel.fromCamera2NoiseProfile(frame.motionV2NoiseProfile)
                    if (!model.hasValidCamera2Profile) {
                        throw IllegalStateException(
                            "IRIS_26514 invalid Camera2 SENSOR_NOISE_PROFILE frame=$index")
                    }
                }
                denoiseNoiseProfileLayout = RawNoiseProfileLayout.CAMERA2_CFA
                denoiseChannelNoiseProfile = mgcBase.motionV2NoiseProfile.copyOf()
                requireParity(
                    RawNoiseModel.fromCamera2NoiseProfile(denoiseChannelNoiseProfile)
                        .hasValidCamera2Profile,
                    "invalid Camera2 MGC-base denoise noise profile",
                )
                noiseSelection = RawNoiseProfileSelection.Camera2
                noiseAuthority = "CAMERA2_PER_FRAME"
            }
            PLog.i(TAG, "IRIS_26514_NOISE_AUTHORITY source=$noiseAuthority " +
                "frames=${orderedPhysical.size} mgcBaseIso=${mgcBase.motionV2ActualIso} " +
                "residualDenoiseBase=${mgcBase.timestamp} baseFallback=0 pixelFallback=0 " +
                "crossSourceFallback=false")

            parameters.motionCanonicalExposureGain = 1.0f
            parameters.motionV2ShortHighlightRecoveryExecuted = false
            // Preserve the successful-26507 display-gain sampling contract separately from
            // MGC's logical RAW geometry. ImageFrame.width/height are the exact geometry that
            // computeDisplayGain() received in 26507 (including any RAW row-stride padding).
            val referenceDisplayGain = MotionV2Merger.computeDisplayGain(
                reference.buffer,
                reference.width,
                reference.height,
                parameters,
                reference.motionV2ExposureEnergy,
            )
            parameters.motionV2DisplayGain = 1.0f

            val cfa = parameters.cfaPattern.toInt()
            val masterBlack = canonicalBlack(parameters.blackLevel, cfa)
            val whiteLevel = if (mgcBase.motionV2WhiteLevelValid && mgcBase.motionV2WhiteLevel > 0) {
                mgcBase.motionV2WhiteLevel
            } else {
                parameters.whiteLevel
            }
            requireParity(whiteLevel > 0, "invalid reference white level=$whiteLevel")
            val wb = parameters.motionV2ColorGains?.copyOf()
                ?.takeIf { it.size >= 4 && it.take(4).all { v -> v.isFinite() && v > 0f } }
                ?: floatArrayOf(1f, 1f, 1f, 1f)
            val lsc = parameters.gainMap?.copyOf()?.takeIf { values ->
                parameters.mapSize != null && parameters.mapSize.x > 0 && parameters.mapSize.y > 0 &&
                    values.size == parameters.mapSize.x * parameters.mapSize.y * 4 &&
                    values.all { it.isFinite() && it > 0f }
            }
            val lscWidth = if (lsc != null) parameters.mapSize.x else 0
            val lscHeight = if (lsc != null) parameters.mapSize.y else 0

            val frames = orderedPhysical.map { (frame, role) ->
                RawStackFrame(
                    image = safeImage(frame, size),
                    sensorTimestampNs = frame.motionV2ResultSensorTimestampNs.takeIf { it > 0L }
                        ?: frame.timestamp,
                    frameNumber = frame.motionV2FrameNumber,
                    exposureTimeNs = frame.motionV2ActualExposureNs,
                    sensitivityIso = frame.motionV2ActualIso,
                    exposureProduct = frame.motionV2ExposureEnergy,
                    desiredExposureProduct = null,
                    focusDistanceDiopters = frame.motionV2FocusDistanceDiopters,
                    lensState = frame.motionV2LensState.takeIf { it >= 0 },
                    rollingShutterSkewNs = frame.motionV2RollingShutterSkewNs.takeIf { it > 0L },
                    channelNoiseProfile = if (irisSettings.customNoiseModelEnabled) {
                        null
                    } else {
                        frame.motionV2NoiseProfile.copyOf()
                    },
                    dynamicBlackLevelByCfaPosition = frame.motionV2BlackLevel.copyOf(),
                    role = role,
                )
            }

            /* IRIS_26564_TRUE_2X_SR_DNG_AUTHORITY
             * Native Sabre remains unchanged for the 1x PostPipeline authority. When Super Res is
             * on, the same Sabre flow/covariance/rejection evidence directly reconstructs a 2x
             * camera-linear RGB16F carrier from NORMAL RAW/CFA observations. JPEG and DNG consume
             * that same carrier; no native-RGB interpolation/detail owner is permitted.
             */
            val displayedGlobalZoom = parameters.motionV2GlobalZoom
                .takeIf { it.isFinite() }?.coerceAtLeast(1f) ?: 1f
            val localOutputZoom = parameters.motionV2OutputZoom
                .takeIf { it.isFinite() }?.coerceAtLeast(1f) ?: 1f
            val reconstructionZoom = 1f
            val renderResidualZoom = localOutputZoom
            parameters.motionV2SpatialReconstructionZoom = 1f // compatibility field until Sabre-SR rebase
            parameters.motionV2ReconstructionZoom = reconstructionZoom
            parameters.motionV2RenderResidualZoom = renderResidualZoom
            val sabreSuperResEnabled = parameters.motionV2SuperResOutputEnabled
            val sabreSuperResOutputScale = if (sabreSuperResEnabled) 2f else 1f
            parameters.motionV2SuperResOutputScale = sabreSuperResOutputScale
            PLog.i(TAG, "IRIS_26564_TRUE_2X_SR_DNG_AUTHORITY " +
                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +
                "reconstructionZoom=$reconstructionZoom renderResidualZoom=$renderResidualZoom " +
                "superResRequested=$sabreSuperResEnabled outputScale=$sabreSuperResOutputScale " +
                "baseRgbScale=1.0 detailScale=${if (sabreSuperResEnabled) 2.0 else 1.0} " +
                "colorOwner=NATIVE_SABRE_VGN dngScale=${if (sabreSuperResEnabled && produceNormalStackedDng) 2.0 else 1.0} " +
                "dngOwner=${if (sabreSuperResEnabled && produceNormalStackedDng) "SABRE_LINEAR_RAW_2X" else "NORMALIZED16_NATIVE"}")

            egl = EglOwner.create()
            val fusion = GlesMgcRawFusion(
                width = size.x,
                height = size.y,
                cfaPattern = cfa,
                blackLevel = masterBlack,
                whiteLevel = whiteLevel,
                whiteBalanceGains = wb,
                noiseProfileSelection = noiseSelection,
                lensShading = lsc,
                lensShadingWidth = lscWidth,
                lensShadingHeight = lscHeight,
                allowSabreShadowLong = parameters.irisNightActive,
                useCurrentGlContext = true,
                exportGpuLinearRgbSource = true,
                gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
                exportNormalStackedDng = produceNormalStackedDng,
                vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,
                enableSabreSuperRes = sabreSuperResEnabled,
                sabreSuperResTempDir = PhotonCamera.getApplicationContextStatic().cacheDir,
            )
            val iris26535FusionStartNs = System.nanoTime()
            val stacked = fusion.processFrames(frames)
                ?: invalid("Iris Sabre owner returned null")
            true2xLinearRgbPathForCleanup = stacked.true2xLinearRgbPath
            true2xRenderRgbPathForCleanup = stacked.true2xRenderRgbPath
            true2xPhaseSupportPathForCleanup = stacked.true2xPhaseSupportPath
            true2xNativeVgnGuidePathForCleanup = stacked.true2xNativeVgnGuidePath
            if (parameters.irisNightActive) {
                /* IRIS_26547_NIGHT_NO_SILENT_LONG_DROP
                 * A HAL-shortened batch may contain fewer than 15 physical frames, but every frame
                 * that reached the immutable Night batch must be admitted by Sabre. Never report a
                 * successful 12+3 path after quietly discarding one of the Long observations.
                 */
                requireParity(stacked.mergedFrameCount == frames.size,
                    "Night Sabre admitted=${stacked.mergedFrameCount} immutableBatch=${frames.size}")
            }
            iris26535FusionMs = (System.nanoTime() - iris26535FusionStartNs) / 1_000_000L
            requireParity(stacked.width == size.x && stacked.height == size.y,
                "Sabre native-grid output geometry ${stacked.width}x${stacked.height} != ${size.x}x${size.y}")
            val expectedSuperResWidth = if (sabreSuperResEnabled) size.x * 2 else 0
            val expectedSuperResHeight = if (sabreSuperResEnabled) size.y * 2 else 0
            /* IRIS_26564_TRUE_2X_SINGLE_CARRIER_CONTRACT
             * The retired 26561 detail/native-upscale and 26562 reconstructed-from-native LinearRaw
             * carriers are forbidden. JPEG and DNG share one direct-CFA RGB16F 2x reconstruction.
             */
            requireParity(
                stacked.superResDetailPath == null && stacked.superResLinearRawPath == null &&
                    stacked.superResWidth == 0 && stacked.superResHeight == 0,
                "26564 retired fake-SR carrier unexpectedly survived",
            )
            if (sabreSuperResEnabled) {
                requireParity(stacked.true2xWidth==expectedSuperResWidth&&stacked.true2xHeight==expectedSuperResHeight,
                    "26568 true2x geometry ${stacked.true2xWidth}x${stacked.true2xHeight} expected=${expectedSuperResWidth}x$expectedSuperResHeight")
                val expectedBytes=expectedSuperResWidth.toLong()*expectedSuperResHeight*3L*Short.SIZE_BYTES
                when(stacked.true2xBackend) {
                    "GPU" -> {
                        val render=stacked.true2xRenderRgbPath?.let(::File)
                        requireParity(render?.isFile==true&&render.length()==expectedBytes,"26568 fused GPU render carrier invalid")
                        requireParity((stacked.true2xLinearRgbPath!=null)==produceNormalStackedDng,"26568 direct-CFA DNG carrier ownership mismatch")
                        stacked.true2xLinearRgbPath?.let { path -> val f=File(path);requireParity(f.isFile&&f.length()==expectedBytes,"26568 direct-CFA DNG carrier invalid") }
                        requireParity(stacked.true2xNativeVgnGuidePath==null&&stacked.true2xPhaseSupportPath==null,"26568 GPU path serialized retired guide/phase intermediates")
                    }
                    "CPU" -> {
                        val direct=stacked.true2xLinearRgbPath?.let(::File); val guide=stacked.true2xNativeVgnGuidePath?.let(::File); val phase=stacked.true2xPhaseSupportPath?.let(::File)
                        requireParity(direct?.isFile==true&&direct.length()==expectedBytes,"26568 CPU direct carrier invalid")
                        requireParity(guide?.isFile==true&&guide.length()==size.x.toLong()*size.y*3L*Short.SIZE_BYTES,"26568 CPU guide invalid")
                        requireParity(phase?.isFile==true&&phase.length()==expectedSuperResWidth.toLong()*expectedSuperResHeight,"26568 CPU phase carrier invalid")
                        requireParity(stacked.true2xRenderRgbPath==null,"26568 CPU fallback must use proven file-based derivative builder")
                    }
                    else -> requireParity(false,"26568 true2x backend=${stacked.true2xBackend}")
                }
                requireParity(stacked.true2xPhaseSupportMean.isFinite()&&stacked.true2xPhaseSupportMean in 0f..4f&&stacked.true2xPhaseSupportP10.isFinite()&&stacked.true2xPhaseSupportP10 in 0f..4f,
                    "26568 phase support mean=${stacked.true2xPhaseSupportMean} p10=${stacked.true2xPhaseSupportP10}")
            } else {
                requireParity(stacked.true2xLinearRgbPath==null&&stacked.true2xRenderRgbPath==null&&stacked.true2xNativeVgnGuidePath==null&&stacked.true2xPhaseSupportPath==null&&stacked.true2xWidth==0&&stacked.true2xHeight==0&&stacked.true2xBackend==null,
                    "26568 SR disabled but true2x carrier was produced")
            }
            requireParity(stacked.bufferLayout == RawStackBufferLayout.LINEAR_RGB,
                "output layout=${stacked.bufferLayout}")
            requireParity(stacked.isNormalizedSensorData, "output is not normalized sensor data")
            val gpu = stacked.gpuLinearRgbSource
                ?: invalid("missing GPU Linear RGB source")
            requireParity(gpu.storage == GpuLinearRgbStorage.RGBA16F && gpu.samplesPerPixel == 4,
                "unexpected GPU RGB storage=${gpu.storage} samples=${gpu.samplesPerPixel}")
            requireParity(gpu.textureId != 0, "zero GPU RGB texture")
            requireParity(stacked.mergedFrameCount >= 1, "mergedFrameCount=${stacked.mergedFrameCount}")
            val expectedMergedFrames26587 = frames.count { it.role != RawBurstFrameRole.HIGHLIGHT_SHORT }
            requireParity(stacked.mergedFrameCount == expectedMergedFrames26587,
                "26587 SHORT leaked into mergedFrameCount merged=${stacked.mergedFrameCount} expected=$expectedMergedFrames26587")
            if (!parameters.irisNightActive && shortFrame != null) {
                requireParity(stacked.highlightShortAdmitted,
                    "26587 captured Motion SHORT was not admitted by Sabre auxiliary path")
                requireParity(stacked.highlightShortRestoreMaskGenerated,
                    "26587 admitted Motion SHORT has no whole-RGB restore mask")
                requireParity(stacked.highlightShortExposureRatio.isFinite() &&
                        stacked.highlightShortExposureRatio > 1f,
                    "26587 invalid SHORT exposure ratio=${stacked.highlightShortExposureRatio}")
                requireParity(
                    stacked.highlightShortAppliedToTrue2x == sabreSuperResEnabled,
                    "26587 true2x SHORT guide mismatch applied=${stacked.highlightShortAppliedToTrue2x} " +
                        "srEnabled=$sabreSuperResEnabled",
                )
                PLog.i(TAG, "IRIS_26587_SHORT_BRIDGE_PROOF captured=true admitted=true " +
                    "exposureRatio=${stacked.highlightShortExposureRatio} " +
                    "mergedFrameCount=${stacked.mergedFrameCount} normalOnlyMerged=true dngShortExcluded=true " +
                    "srShortEvidenceExcluded=true srNativeHighlightGuide=${stacked.highlightShortAppliedToTrue2x}")
            } else {
                requireParity(!stacked.highlightShortAdmitted,
                    "26587 SHORT auxiliary unexpectedly active without Motion SHORT capture")
            }
            val correlation = stacked.mgcDenoiseCorrelation
            val readNoise = stacked.mgcDenoiseReadNoise
            val shotNoise = stacked.mgcDenoiseShotNoise
            val strength = stacked.mgcSpatialStrengthMap
            val referenceSnr = stacked.mgcReferenceSnr
            val tuningSnr = stacked.mgcDenoiseTuningSnr
            val sabreNoiseScale = stacked.mgcSabreNoiseModelScale
            requireParity(correlation == null && readNoise == null && shotNoise == null && strength == null,
                "Sabre unexpectedly leaked Spatial-only denoise/reliability state")
            requireParity(referenceSnr != null && referenceSnr.isFinite() && referenceSnr >= 0f,
                "Sabre reference SNR missing/malformed")
            requireParity(tuningSnr != null && tuningSnr.isFinite() && tuningSnr >= 0f,
                "Sabre output SNR missing/malformed")
            requireParity(sabreNoiseScale != null && sabreNoiseScale.isFinite() && sabreNoiseScale > 0f,
                "Sabre propagated noise scale missing/malformed")
            requireParity(parameters.motionV2ReconstructionOwner == Parameters.MOTION_V2_RECONSTRUCTION_SABRE,
                "Sabre reconstruction owner was not durably published")
            requireParity(stacked.baselineExposureEv == null,
                "Sabre unexpectedly inherited Spatial/Bento BaselineExposure")
            requireParity(parameters.motionV2ReconstructionZoom == 1f &&
                    parameters.motionV2SuperResOutputScale == sabreSuperResOutputScale,
                "26561 Sabre base-grid/SR output-scale contract drifted")
            requireParity(lsc == null || stacked.lensShadingCorrectionApplied,
                "LSC supplied but MGC output did not apply it")

            GLES30.glFinish()
            gpu.stackCompletionTimeline?.releasePending()
            resultTexture = gpu.textureId

            val denoiseMetadata = RawMetadata(
                cfaPattern = cfa,
                whiteBalanceGains = wb,
                lensShadingMap = lsc,
                lensShadingMapWidth = lscWidth,
                lensShadingMapHeight = lscHeight,
                mgcDenoiseCorrelation = correlation,
                mgcDenoiseReadNoise = readNoise,
                mgcDenoiseShotNoise = shotNoise,
                mgcSpatialStrengthMap = strength,
                mgcSabreNoiseModelScale = sabreNoiseScale,
                noiseProfileLayout = denoiseNoiseProfileLayout,
                channelNoiseProfile = denoiseChannelNoiseProfile,
            )
            /* IRIS_26540_RESIDUAL_ONLY_DENOISE_AUTHORITY
             * Sabre temporal reconstruction is the first noise reducer. Residual denoise runs only on
             * the residual model exported by the finished stack. Source/reference SNR chooses the
             * Pecan frequency profile; it does NOT create a low-light strength floor. ISO, scene
             * brightness and preview darkness never independently increase denoise strength.
             */
            val requestedLumaScale = irisSettings.lumaDenoise.coerceIn(0f, 2f)
            val noiseEquivalentSupport =
                (1f / checkNotNull(sabreNoiseScale)).coerceIn(1f, stacked.mergedFrameCount.toFloat())
            requireParity(noiseEquivalentSupport.isFinite() && noiseEquivalentSupport >= 1f,
                "missing/malformed noise-equivalent temporal support")
            /* IRIS_26545_SHARED_RESIDUAL_DENOISE_CONTROLS
             * The reconstruction owns temporal noise reduction. These two user controls act only
             * on the completed linear-RGB carrier, before PostPipeline/tone/UHDR. They never alter
             * capture exposure, frame admission, Spatial merge math, Sabre rejection, or Resolve.
             * Luma uses a new preference key and defaults to zero to preserve the proven 26544
             * zero-luma behavior until the user deliberately opts in. Chroma keeps its prior value.
             */
            val lumaScale = requestedLumaScale
            val chromaScale = irisSettings.chromaDenoise.coerceIn(0f, 2f)
            val denoisePass = MgcFullResolutionDenoise.Pass.SABRE_DEFAULT
            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&
                (lumaScale > 0f || chromaScale > 0f)
            var resultTrue2xLinearRawPath: String? = null
            var resultTrue2xRenderRgbPath: String? = null
            var iris26564True2xRenderPrepMs = 0L
            if (runFullResolutionDenoise) {
                requireParity(MgcFullResolutionDenoise.ensureInitialized(
                    PhotonCamera.getApplicationContextStatic()),
                    "MGC denoise tuning assets failed initialization")
            }

            /* IRIS_26561_SABRE_SR_DETAIL_ONLY_BACKEND
             * Full-resolution residual denoise remains native 1x Sabre RGB. The optional 2x
             * detail sidecar is already frozen from Sabre NORMAL-frame evidence and is consumed
             * only by the streamed Super Res JPEG encoder after this native color path completes.
             */
            val denoiseBuffer = readRgba16f(resultTexture, size.x, size.y)
            halfBuffer = denoiseBuffer
            val iris26535DenoiseStartNs = System.nanoTime()
            if (runFullResolutionDenoise) {
                requireParity(MgcFullResolutionDenoise.denoise(
                    rgba16f = denoiseBuffer,
                    width = size.x,
                    height = size.y,
                    globalOriginX = 0,
                    globalOriginY = 0,
                    fullWidth = size.x,
                    fullHeight = size.y,
                    outputScale = 1f,
                    inputLayout = MgcFullResolutionDenoise.InputLayout.CAMERA_RGBA16F,
                    applyLensShadingInBayerAot = false,
                    metadata = denoiseMetadata,
                    preparedYuvNoiseModel = null,
                    applyLensShadingToDenoiseStrength = false,
                    tuningSnr = tuningSnr!!,
                    pass = denoisePass,
                    lumaStrengthScale = lumaScale,
                    chromaStrengthScale = chromaScale,
                ), "MGC $denoisePass pre-PostPipeline linear-RGB denoise rejected its noise state")
            }
            iris26535DenoiseMs = (System.nanoTime() - iris26535DenoiseStartNs) / 1_000_000L

            /* IRIS_26568_FUSED_TRUE2X_RENDER_HANDOFF
             * Normal GPU operation applies the 26572 Sabre/VGN-guided true-detail luminance owner
             * while direct-CFA/phase/guide evidence is resident. CPU fallback mirrors the exact same
             * cross-frame-temporal, zero-chroma-transfer 2x2 luminance structure contract in the bounded file builder.
             */
            if(parameters.motionV2SuperResOutputEnabled) {
                if(stacked.true2xBackend=="GPU") {
                    val fused=checkNotNull(stacked.true2xRenderRgbPath)
                    resultTrue2xRenderRgbPath=fused; true2xRenderRgbPathForCleanup=fused; iris26564True2xRenderPrepMs=0L
                    if(produceNormalStackedDng)resultTrue2xLinearRawPath=checkNotNull(stacked.true2xLinearRgbPath)
                    PLog.i(TAG,"IRIS_26573_TRUE_DETAIL_RENDER_FUSED size=${stacked.true2xWidth}x${stacked.true2xHeight} dngRawPreserved=${resultTrue2xLinearRawPath!=null} sabreRgbChromaOwner=true highResLumaOwner=DIRECT_CFA_TEMPORAL directChromaOwner=false prepMs=0")
                    PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26573_SR_PROOF_HANDOFF details=backend=GPU statsValidatedByStacker=true fusedCarrier=true")
                } else {
                    val rawPath=checkNotNull(stacked.true2xLinearRgbPath); val guidePath=checkNotNull(stacked.true2xNativeVgnGuidePath); val phaseSupportPath=checkNotNull(stacked.true2xPhaseSupportPath)
                    val prepStartNs=System.nanoTime(); val runTrue2xFullResolutionMgc=false
                    resultTrue2xRenderRgbPath=buildTrue2xRenderCarrier(rawPath,guidePath,phaseSupportPath,stacked.true2xWidth,stacked.true2xHeight,denoiseMetadata,checkNotNull(tuningSnr),denoisePass,runTrue2xFullResolutionMgc,lumaScale,chromaScale)
                    true2xRenderRgbPathForCleanup=resultTrue2xRenderRgbPath; iris26564True2xRenderPrepMs=(System.nanoTime()-prepStartNs)/1_000_000L
                    runCatching{File(guidePath).delete()};true2xNativeVgnGuidePathForCleanup=null;runCatching{File(phaseSupportPath).delete()};true2xPhaseSupportPathForCleanup=null
                    if(produceNormalStackedDng)resultTrue2xLinearRawPath=rawPath else {runCatching{File(rawPath).delete()};true2xLinearRgbPathForCleanup=null}
                    PLog.i(TAG,"IRIS_26568_TRUE2X_RENDER_CPU_FALLBACK size=${stacked.true2xWidth}x${stacked.true2xHeight} prepMs=$iris26564True2xRenderPrepMs")
                }
            }
            forceOpaqueHalfAlpha(denoiseBuffer, size.x, size.y)
            /* IRIS_26548_NIGHT_RGBA32F_MOTION_PARITY_HANDOFF
             * 26547 proved that the Night-only native-half CPU handoff can reach a native status-11
             * crash at the first PostPipeline input. GLTexture's FLOAT_16 internal format uses a
             * GL_FLOAT client upload contract, while that Night ByteBuffer physically contains
             * 16-bit half values. Reuse Motion's already-proven cross-context contract instead:
             * convert the finished MGC RGBA16F texture to an RGBA32F CPU carrier inside the MGC
             * context, then let the PostPipeline upload the exact same representation Motion uses.
             * Reconstruction/Sabre/VGN math is unchanged.
             */
            val output: ByteBuffer = convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)
            GLES30.glDeleteTextures(1, intArrayOf(resultTexture), 0)
            resultTexture = 0
            checkGl("delete exported MGC RGB")

            PLog.i(TAG, "IRIS_26545_DENOISE_NOISE_AUTHORITY " +
                "stage=PRE_POSTPIPELINE_LINEAR_RGB master=${irisSettings.noiseReductionEnabled} " +
                "luma=$lumaScale chroma=$chromaScale executed=$runFullResolutionDenoise " +
                "pass=$denoisePass noiseSource=$noiseAuthority mgcBase=${mgcBase.timestamp} " +
                "referenceSnr=$referenceSnr outputTuningSnr=$tuningSnr " +
                "noiseEquivalentSupport=$noiseEquivalentSupport " +
                "residualMagnitude=physicalBaseNoiseTimesMeasuredSabreMergeScale " +
                "sliderAffectsMerge=false sliderAffectsExposure=false sliderAffectsTone=false " +
                "structureAuthority=SABRE_REJECTION_RESOLVE " +
                "srScale=1.0 superResRequested=${parameters.motionV2SuperResOutputEnabled} requestedLocalZoom=$localOutputZoom " +
                "finalFovZoom=$displayedGlobalZoom renderResidual=$renderResidualZoom " +
                "outputScale=1.0 banded2x=false " +
                "fullHighResPostTexture=false baseCarrier=${size.x}x${size.y} " +
                "legacyPhotonNr=false sabreOwner=true")

            /* IRIS_26560_SABRE_SOURCE_DOMAIN_IDENTITY
             * Sabre Resolve emits the common linear-RGB source directly; obsolete Spatial/Bento
             * BaselineExposure restoration is forbidden.
             */
            requireParity(stacked.baselineExposureEv == null,
                "Sabre returned obsolete Spatial/Bento BaselineExposure")
            parameters.motionV2MgcSourceExposureGain = 1.0f
            parameters.motionV2DisplayGain = 1.0f
            parameters.motionV2ShortHighlightRecoveryExecuted = false
            PLog.i(TAG, "IRIS_26560_SABRE_SOURCE_DOMAIN_IDENTITY " +
                "sourceDomainGain=1.0 displayGain=${parameters.motionV2DisplayGain} " +
                "spatialSourceRestore=false solverAfterProfileColor=true")
            parameters.motionV2EffectiveSupport = noiseEquivalentSupport

            /* IRIS_26542_ROLE_AWARE_NORMAL_DNG_PARITY
             * The stacked DNG intentionally contains only same-exposure NORMAL observations.
             * Motion still has all-normal inputImages, while dedicated Night carries 12 NORMAL
             * shorts plus 3 SHADOW_LONG frames in the same MGC list. The old total-list comparison
             * therefore aborted a correct Night 12+3 merge after Spatial-RGB had already finished.
             */
            val expectedNormalDngFrames = inputImages.count {
                it.motionV2FrameRole == ImageFrame.MotionV2FrameRole.NORMAL
            }
            requireParity(expectedNormalDngFrames >= 1,
                "normal stacked DNG has no NORMAL source frames totalInputs=${inputImages.size}")
            var resultDngRaw16: ByteBuffer? = null
            var resultDngFrameCount = 0
            var resultDngNoiseProfile: DoubleArray? = null
            var resultDngSupportMin = 1f
            var resultDngSupportP01 = 1f
            var resultDngSupportP10 = 1f
            var resultDngSupportMedian = 1f
            var resultDngSupportMean = 1f
            var resultDngSupportMax = 1f
            var resultDngNoiseEquivalentSupport = 1f
            if (produceNormalStackedDng) {
                requireParity(stacked.normalStackedDngRaw16 != null,
                    "requested Sabre normal stacked DNG buffer is missing")
                requireParity(stacked.normalStackedDngFrameCount == expectedNormalDngFrames,
                    "normal stacked DNG population=${stacked.normalStackedDngFrameCount} expectedNormals=$expectedNormalDngFrames totalInputs=${inputImages.size}")
                requireParity(stacked.normalStackedDngNoiseProfile?.size == 6,
                    "normalized16 stacked DNG noise profile is missing/invalid")
                requireParity(stacked.normalStackedDngNoiseEquivalentSupport.isFinite() &&
                    stacked.normalStackedDngNoiseEquivalentSupport >= 1f &&
                    stacked.normalStackedDngNoiseEquivalentSupport <= expectedNormalDngFrames.toFloat() + 0.01f,
                    "normalized16 stacked DNG effective support is invalid normalLimit=$expectedNormalDngFrames")
                resultDngRaw16 = stacked.normalStackedDngRaw16
                resultDngFrameCount = stacked.normalStackedDngFrameCount
                resultDngNoiseProfile = stacked.normalStackedDngNoiseProfile
                resultDngSupportMin = stacked.normalStackedDngSupportMin
                resultDngSupportP01 = stacked.normalStackedDngSupportP01
                resultDngSupportP10 = stacked.normalStackedDngSupportP10
                resultDngSupportMedian = stacked.normalStackedDngSupportMedian
                resultDngSupportMean = stacked.normalStackedDngSupportMean
                resultDngSupportMax = stacked.normalStackedDngSupportMax
                resultDngNoiseEquivalentSupport = stacked.normalStackedDngNoiseEquivalentSupport
                PLog.i(TAG, "IRIS_26545_DNG_RECONSTRUCTION_PARITY " +
                    "reconstruction=SABRE " +
                    "domain=normalized16_bayer normalFrames=$resultDngFrameCount " +
                    "blackLevel=0 whiteLevel=65535 postProcessingBaked=false")
            } else {
                requireParity(stacked.normalStackedDngRaw16 == null && stacked.normalStackedDngFrameCount == 0,
                    "DNG sidecar produced without request")
                requireParity(stacked.normalStackedDngNoiseProfile == null,
                    "DNG metadata produced without request")
            }

            PLog.i(TAG, "IRIS_26568_SABRE_ONLY_RECONSTRUCTION_OWNERSHIP " +
                "pipeline=${if (parameters.irisNightActive) "NIGHT" else "MOTION"} " +
                "owner=SABRE spatialSourceRestoreAllowed=false spatialHighlightNodeAllowed=false " +
                "residualDenoise=$denoisePass carrier=RESOLVE_SABRE_LINEAR_RGB " +
                "superResRequested=${parameters.motionV2SuperResOutputEnabled} " +
                "true2x=${stacked.true2xRenderRgbPath != null || stacked.true2xLinearRgbPath != null} backend=${stacked.true2xBackend} " +
                "phaseMean=${stacked.true2xPhaseSupportMean} phaseP10=${stacked.true2xPhaseSupportP10} " +
                "adaptiveColor=POST_VGN_SHARED")
            PLog.i(TAG, "IRIS_26545_RECONSTRUCTION_TIMING " +
                "method=SABRE srEnabled=$sabreSuperResEnabled fusionMs=$iris26535FusionMs " +
                "true2xMs=${stacked.true2xReconstructionMs} true2xRenderPrepMs=$iris26564True2xRenderPrepMs " +
                "denoiseMs=$iris26535DenoiseMs srReliabilityGateMs=0 " +
                "totalMs=${(System.nanoTime() - iris26535TotalStartNs) / 1_000_000L} " +
                "frames=${frames.size} merged=${stacked.mergedFrameCount}")
            PLog.i(TAG, "IRIS_26512_MGC1271_PARITY_VALID " +
                "normals=$expectedNormalDngFrames totalInputs=${inputImages.size} totalScheduled=${frames.size} " +
                "photonReference=$referenceTimestamp mgcBase=${mgcBase.timestamp} " +
                "long=${if (longFrame != null) 1 else 0} short=${if (shortFrame != null) 1 else 0} " +
                "merged=${stacked.mergedFrameCount} cfa=$cfa " +
                "lsc=${stacked.lensShadingCorrectionApplied} " +
                "denoise=SABRE_RESOLVE_PLUS_SABRE_DEFAULT_RESIDUAL " +
                "baselineEv=${stacked.baselineExposureEv} " +
                "displayGain=${parameters.motionV2DisplayGain} " +
                "crossContext=${if (parameters.irisNightActive) "float32_rgba_cpu_night_motion_parity" else "float32_rgba_cpu_motion"} alphaSupport=disabled")

            return MotionV2Merger.Result(
                output,
                mgcBase.timestamp,
                frames.size,
                noiseEquivalentSupport,
                null,
                resultDngRaw16,
                resultDngFrameCount,
                resultDngNoiseProfile,
                resultDngSupportMin,
                resultDngSupportP01,
                resultDngSupportP10,
                resultDngSupportMedian,
                resultDngSupportMean,
                resultDngSupportMax,
                resultDngNoiseEquivalentSupport,
                null, 0, 0,
                null, 0, 0,
                resultTrue2xLinearRawPath,
                resultTrue2xRenderRgbPath,
                stacked.true2xWidth,
                stacked.true2xHeight,
                stacked.true2xBackend,
                stacked.true2xPhaseSupportMean,
                stacked.true2xPhaseSupportP10,
                stacked.true2xReconstructionMs,
            ).also { result ->
                result.sabreSelected = true
                true2xOutputHandedOff = resultTrue2xRenderRgbPath != null &&
                    (!produceNormalStackedDng || resultTrue2xLinearRawPath != null)
            }
        } catch (error: Throwable) {
            PLog.e(TAG, "MGC PARITY ARCHITECTURE INVALID", error)
            throw if (error is IllegalStateException &&
                error.message?.startsWith("MGC PARITY ARCHITECTURE INVALID") == true) {
                error
            } else {
                IllegalStateException("MGC PARITY ARCHITECTURE INVALID: ${error.message}", error)
            }
        } finally {
            if (resultTexture != 0) runCatching {
                GLES30.glDeleteTextures(1, intArrayOf(resultTexture), 0)
            }
            LargeDirectBuffer.free(halfBuffer)
            if (!true2xOutputHandedOff) {
                true2xLinearRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xNativeVgnGuidePathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xPhaseSupportPathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xRenderRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
            }
            egl?.close()
            inputImages.forEach { frame ->
                if (frame.hasMotionV2RawBacking()) runCatching { frame.close() }
            }
            if (shortFrame?.hasMotionV2RawBacking() == true && inputImages.none { it === shortFrame }) {
                runCatching { shortFrame?.close() }
            }
            if (longFrame?.hasMotionV2RawBacking() == true && inputImages.none { it === longFrame }) {
                runCatching { longFrame?.close() }
            }
            shortSlot?.sealAndClose()
        }
    }

    private fun validateFrame(
        frame: ImageFrame,
        size: Point,
        role: RawBurstFrameRole,
        referenceEnergy: Double,
        index: Int,
    ) {
        requireParity(frame.hasMotionV2RawBacking(), "frame[$index] $role RAW backing is missing")
        requireParity(frame.motionV2PlaneLayoutValid,
            "frame[$index] $role RAW plane layout missing")
        requireParity(!frame.motionV2PlaneTransformedByBinning,
            "frame[$index] $role uses transformed/binning RAW layout")
        requireParity(frame.motionV2PlaneFormat == ImageFormat.RAW_SENSOR,
            "frame[$index] $role format=${frame.motionV2PlaneFormat}, RAW_SENSOR required")
        requireParity(frame.motionV2PlaneLogicalWidth == size.x &&
                frame.motionV2PlaneLogicalHeight == size.y,
            "frame[$index] $role logical=${frame.motionV2PlaneLogicalWidth}x${frame.motionV2PlaneLogicalHeight} " +
                "expected=${size.x}x${size.y}")
        requireParity(frame.motionV2PlanePixelStrideBytes == 2,
            "frame[$index] $role pixelStride=${frame.motionV2PlanePixelStrideBytes}, expected=2")
        requireParity(frame.motionV2PlaneRowStrideBytes >= size.x * 2,
            "frame[$index] $role rowStride=${frame.motionV2PlaneRowStrideBytes}")
        val minimumRawBytes = frame.motionV2PlaneRowStrideBytes.toLong() * size.y
        if (frame.buffer != null) {
            requireParity(frame.buffer.capacity().toLong() >= minimumRawBytes,
                "frame[$index] $role copied RAW capacity=${frame.buffer.capacity()} stride=${frame.motionV2PlaneRowStrideBytes}")
        } else {
            requireParity(frame.irisNightRawDiskBacked && frame.irisNightRawSpoolFile?.isFile == true &&
                    frame.irisNightRawSpoolBytes >= minimumRawBytes,
                "frame[$index] $role disk RAW backing is incomplete bytes=${frame.irisNightRawSpoolBytes}")
        }
        requireParity(frame.motionV2ActualExposureNs > 0L && frame.motionV2ActualIso > 0 &&
                frame.motionV2ExposureEnergy.isFinite() && frame.motionV2ExposureEnergy > 0.0,
            "frame[$index] $role exposure metadata invalid")
        requireParity(frame.motionV2NoiseProfileValid && frame.motionV2NoiseProfile.size >= 8 &&
                (0 until 4).all { phase ->
                    val s = frame.motionV2NoiseProfile[phase * 2]
                    val o = frame.motionV2NoiseProfile[phase * 2 + 1]
                    s.isFinite() && s > 0f && o.isFinite() && o >= 0f
                }, "frame[$index] $role Camera2 noise profile invalid")
        requireParity(frame.motionV2BlackLevelValid && frame.motionV2BlackLevel.all {
            it.isFinite() && it >= 0f
        }, "frame[$index] $role dynamic black level invalid")
        if (role == RawBurstFrameRole.SHADOW_LONG) {
            requireParity(frame.motionV2ExposureEnergy > referenceEnergy,
                "Long TET is not above reference")
        }
        if (role == RawBurstFrameRole.HIGHLIGHT_SHORT) {
            requireParity(frame.motionV2ExposureEnergy < referenceEnergy,
                "Short TET is not below reference")
        }
    }

    private fun safeImage(frame: ImageFrame, size: Point): SafeImage {
        val raw = frame.buffer
        if (raw != null) {
            return SafeImage(
                width = size.x,
                height = size.y,
                format = frame.motionV2PlaneFormat,
                timestamp = frame.timestamp,
                buffer = raw,
                rowStride = frame.motionV2PlaneRowStrideBytes,
                pixelStride = frame.motionV2PlanePixelStrideBytes,
                closeAction = { frame.close() },
            )
        }
        val file = frame.irisNightRawSpoolFile
            ?: invalid("RAW backing vanished before disk SafeImage adapter")
        requireParity(frame.irisNightRawDiskBacked && file.isFile,
            "Night disk SafeImage backing is unavailable")
        requireParity(frame.irisNightRawSpoolBytes in 1..Int.MAX_VALUE.toLong(),
            "Night disk SafeImage byte count=${frame.irisNightRawSpoolBytes}")
        return SafeImage(
            width = size.x,
            height = size.y,
            format = frame.motionV2PlaneFormat,
            timestamp = frame.timestamp,
            backingFile = file,
            backingByteCount = frame.irisNightRawSpoolBytes.toInt(),
            rowStride = frame.motionV2PlaneRowStrideBytes,
            pixelStride = frame.motionV2PlanePixelStrideBytes,
            closeAction = { frame.close() },
        )
    }

    private fun canonicalBlack(positional: FloatArray, cfa: Int): FloatArray {
        requireParity(positional.size >= 4, "master black level has ${positional.size} phases")
        val phaseToCanonical = when (cfa) {
            1 -> intArrayOf(1, 0, 3, 2)
            2 -> intArrayOf(2, 3, 0, 1)
            3 -> intArrayOf(3, 2, 1, 0)
            else -> intArrayOf(0, 1, 2, 3)
        }
        return FloatArray(4).also { out ->
            phaseToCanonical.forEachIndexed { phase, canonical ->
                val value = positional[phase]
                requireParity(value.isFinite() && value >= 0f,
                    "invalid master black phase=$phase value=$value")
                out[canonical] = value
            }
        }
    }

    private fun readRgba16f(texture: Int, width: Int, height: Int): ByteBuffer {
        val bytes = width.toLong() * height * 4L * 2L
        val output = LargeDirectBuffer.allocate(bytes, "MGC1271 RGBA16F black-box input")
            ?: invalid("unable to allocate RGBA16F denoise buffer")
        val fbo = IntArray(1)
        GLES30.glGenFramebuffers(1, fbo, 0)
        requireParity(fbo[0] != 0, "unable to allocate RGBA16F readback FBO")
        try {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbo[0])
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, texture, 0)
            requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE,
                "RGBA16F readback FBO incomplete")
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 8)
            output.position(0)
            GLES30.glReadPixels(0, 0, width, height, GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, output)
            checkGl("read pinned MGC RGBA16F")
            output.position(0)
            return output
        } catch (error: Throwable) {
            LargeDirectBuffer.free(output)
            throw error
        } finally {
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            GLES30.glDeleteFramebuffers(1, fbo, 0)
        }
    }

    private fun forceOpaqueHalfAlpha(buffer: ByteBuffer, width: Int, height: Int) {
        val shorts = buffer.duplicate().order(ByteOrder.nativeOrder()).apply { position(0) }.asShortBuffer()
        val pixels = width * height
        requireParity(shorts.capacity() >= pixels * 4, "RGBA16F alpha buffer is short")
        for (pixel in 0 until pixels) shorts.put(pixel * 4 + 3, HALF_ONE)
        buffer.position(0)
    }

    private fun convertHalfRgbaToFloatRgba(half: ByteBuffer, width: Int, height: Int): ByteBuffer {
        val textureIds = IntArray(1)
        val fboIds = IntArray(1)
        GLES30.glGenTextures(1, textureIds, 0)
        GLES30.glGenFramebuffers(1, fboIds, 0)
        requireParity(textureIds[0] != 0 && fboIds[0] != 0,
            "half->float transfer allocation failed")
        val outputBytes = width.toLong() * height * 4L * 4L
        val output = LargeDirectBuffer.allocate(outputBytes, "MGC1271 Photon FLOAT32 RGBA")
            ?: invalid("unable to allocate Photon FLOAT32 carrier")
        try {
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, textureIds[0])
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 8)
            half.position(0)
            GLES30.glTexImage2D(
                GLES30.GL_TEXTURE_2D, 0, GLES30.GL_RGBA16F, width, height, 0,
                GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, half)
            checkGl("upload denoised RGBA16F")
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fboIds[0])
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, textureIds[0], 0)
            requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) ==
                    GLES30.GL_FRAMEBUFFER_COMPLETE,
                "half->float FBO incomplete")
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 4)
            output.position(0)
            GLES30.glReadPixels(0, 0, width, height, GLES30.GL_RGBA, GLES30.GL_FLOAT, output)
            checkGl("read Photon FLOAT32 RGBA")
            output.position(0)
            return output
        } catch (error: Throwable) {
            LargeDirectBuffer.free(output)
            throw error
        } finally {
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glDeleteFramebuffers(1, fboIds, 0)
            GLES30.glDeleteTextures(1, textureIds, 0)
        }
    }


    private fun buildTrue2xRenderCarrier(
        rawPath: String,
        guidePath: String,
        phaseSupportPath: String,
        width: Int,
        height: Int,
        metadata: RawMetadata,
        tuningSnr: Float,
        pass: MgcFullResolutionDenoise.Pass,
        runDenoise: Boolean,
        lumaScale: Float,
        chromaScale: Float,
    ): String {
        requireParity(width > 0 && height > 0 && (width and 1) == 0 && (height and 1) == 0,
            "26564 invalid true2x render geometry ${width}x$height")
        val rawFile = File(rawPath)
        val guideFile = File(guidePath)
        val phaseFile = File(phaseSupportPath)
        val expectedBytes = width.toLong() * height * 3L * Short.SIZE_BYTES
        requireParity(rawFile.isFile && rawFile.length() == expectedBytes,
            "26564 true2x pristine carrier size mismatch")
        requireParity(guideFile.isFile && guideFile.length() == expectedBytes / 4L,
            "26564 true2x VGN guide size mismatch")
        requireParity(phaseFile.isFile && phaseFile.length() == width.toLong() * height,
            "26567 true2x phase support size mismatch")
        val renderFile = File(rawFile.parentFile, rawFile.name + ".render26564")
        runCatching { renderFile.delete() }
        RandomAccessFile(renderFile, "rw").use { raf ->
            raf.setLength(expectedBytes)
        }
        val core = 512
        val halo = if (runDenoise) 128 else 0
        val proofGridWidth = 32
        val proofGridHeight = 24
        val proofGridOffset = 9
        val detailStats = LongArray(proofGridOffset + proofGridWidth * proofGridHeight * 3)
        /* IRIS_26573_CPU_INTERIOR_ONLY_PROOF
         * Native tile preparation includes denoise halos, so its legacy cumulative stats cannot be
         * used as a whole-frame count without double-counting overlapping halo pixels.  Harvest the
         * diagnostic alpha directly from the already-resident CPU RGBA16F tile, but count ONLY the
         * non-overlapping interior that will be published. This is not a second image readback.
         */
        val nativeScratchStats = LongArray(9)
        fun accumulateInteriorProof(
            rgba: ByteBuffer,
            regionLeft: Int,
            regionTop: Int,
            regionWidth: Int,
            left: Int,
            top: Int,
            interiorWidth: Int,
            interiorHeight: Int,
        ) {
            val half = rgba.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
            for (y in 0 until interiorHeight) {
                val localY = top + y - regionTop
                for (x in 0 until interiorWidth) {
                    val globalX = left + x
                    val globalY = top + y
                    val localX = globalX - regionLeft
                    val index = localY * regionWidth + localX
                    val diagnostic = Half.toFloat(half.get(index * 4 + 3)).toInt()
                    requireParity(diagnostic in 0..39, "26573 invalid CPU SR diagnostic code=$diagnostic")
                    val reasonClass = diagnostic % 8
                    detailStats[0]++
                    when (reasonClass) {
                        1 -> detailStats[1]++
                        2 -> detailStats[2]++
                        3 -> detailStats[3]++
                        4 -> detailStats[4]++
                        5 -> detailStats[5]++
                        6 -> detailStats[6]++
                        7 -> detailStats[7]++
                        else -> detailStats[8]++
                    }
                    val cellX = (globalX.toLong() * proofGridWidth / width).toInt().coerceIn(0, proofGridWidth - 1)
                    val cellY = (globalY.toLong() * proofGridHeight / height).toInt().coerceIn(0, proofGridHeight - 1)
                    val q = proofGridOffset + (cellY * proofGridWidth + cellX) * 3
                    detailStats[q]++
                    if (reasonClass == 1 || reasonClass == 2) detailStats[q + 1]++
                    if (reasonClass == 2) detailStats[q + 2]++
                }
            }
        }
        try {
            var top = 0
            while (top < height) {
                val interiorHeight = minOf(core, height - top)
                var left = 0
                while (left < width) {
                    val interiorWidth = minOf(core, width - left)
                    val regionLeft = maxOf(0, left - halo)
                    val regionTop = maxOf(0, top - halo)
                    val regionRight = minOf(width, left + interiorWidth + halo)
                    val regionBottom = minOf(height, top + interiorHeight + halo)
                    val regionWidth = regionRight - regionLeft
                    val regionHeight = regionBottom - regionTop
                    val bytes = regionWidth.toLong() * regionHeight * 4L * Short.SIZE_BYTES
                    val rgba = LargeDirectBuffer.allocate(bytes, "IRIS26564 true2x render tile")
                        ?: invalid("unable to allocate true2x render tile ${regionWidth}x$regionHeight")
                    try {
                        requireParity(
                            com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative.prepareVgnGuidedRenderTile(
                                rawPath, width, height, guidePath, width / 2, height / 2,
                                phaseSupportPath, regionLeft, regionTop, regionWidth, regionHeight,
                                rgba, nativeScratchStats,
                            ),
                            "26564 VGN-guided true2x tile preparation failed at $left,$top",
                        )
                        rgba.position(0)
                        accumulateInteriorProof(
                            rgba, regionLeft, regionTop, regionWidth,
                            left, top, interiorWidth, interiorHeight,
                        )
                        rgba.position(0)
                        if (runDenoise) {
                            requireParity(MgcFullResolutionDenoise.denoise(
                                rgba16f = rgba,
                                width = regionWidth,
                                height = regionHeight,
                                globalOriginX = regionLeft,
                                globalOriginY = regionTop,
                                fullWidth = width,
                                fullHeight = height,
                                outputScale = 2f,
                                inputLayout = MgcFullResolutionDenoise.InputLayout.CAMERA_RGBA16F,
                                applyLensShadingInBayerAot = false,
                                metadata = metadata,
                                preparedYuvNoiseModel = null,
                                applyLensShadingToDenoiseStrength = false,
                                tuningSnr = tuningSnr,
                                pass = pass,
                                lumaStrengthScale = lumaScale,
                                chromaStrengthScale = chromaScale,
                            ), "26564 true2x residual denoise rejected tile at $left,$top")
                        }
                        forceOpaqueHalfAlpha(rgba, regionWidth, regionHeight)
                        requireParity(
                            com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative.writeRenderTileInterior(
                                renderFile.absolutePath, width, height, rgba,
                                regionLeft, regionTop, regionWidth, regionHeight,
                                left, top, interiorWidth, interiorHeight,
                            ),
                            "26564 true2x render tile write failed at $left,$top",
                        )
                    } finally {
                        LargeDirectBuffer.free(rgba)
                    }
                    left += interiorWidth
                }
                top += interiorHeight
            }
            RandomAccessFile(renderFile, "rw").use { it.fd.sync() }
            requireParity(renderFile.length() == expectedBytes,
                "26564 true2x render derivative byte count mismatch")
            val expectedPixels = width.toLong() * height.toLong()
            requireParity(detailStats[0] == expectedPixels,
                "26573 CPU SR proof incomplete ${detailStats[0]}/$expectedPixels")
            val gridTotal = (0 until proofGridWidth * proofGridHeight).sumOf { cell ->
                detailStats[proofGridOffset + cell * 3]
            }
            requireParity(gridTotal == expectedPixels,
                "26573 CPU SR proof grid incomplete $gridTotal/$expectedPixels")
            val activePixels = detailStats[1] + detailStats[2]
            val strongPixels = detailStats[2]
            fun pct(value: Long) = 100.0 * value.toDouble() / expectedPixels.toDouble()
            fun encodeGrid(channel: Int): String {
                val digits = "0123456789abcdef"
                return buildString(proofGridWidth * proofGridHeight + proofGridHeight - 1) {
                    for (gy in 0 until proofGridHeight) {
                        if (gy > 0) append('/')
                        for (gx in 0 until proofGridWidth) {
                            val q = proofGridOffset + (gy * proofGridWidth + gx) * 3
                            val total = detailStats[q]
                            val value = if (total > 0L) ((15.0 * detailStats[q + channel].toDouble() / total.toDouble()) + 0.5).toInt().coerceIn(0, 15) else 0
                            append(digits[value])
                        }
                    }
                }
            }
            val proof = "backend=CPU totalPixels=$expectedPixels activePixels=$activePixels activePct=${pct(activePixels)} " +
                "strongPixels=$strongPixels strongPct=${pct(strongPixels)} temporalRejected=${detailStats[3]} temporalRejectedPct=${pct(detailStats[3])} " +
                "highlightRejected=${detailStats[4]} disagreementRejected=${detailStats[5]} phaseRejected=${detailStats[6]} signalRejected=${detailStats[7]} " +
                "fallbackOther=${detailStats[8]} highResLumaOwner=DIRECT_CFA_TEMPORAL sabreRgbChromaOwner=true directChromaOwner=false " +
                "activeMap32x24=${encodeGrid(1)} strongMap32x24=${encodeGrid(2)}"
            PLog.i(TAG, "IRIS_26573_SR_PROOF $proof")
            PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26573_SR_PROOF details=$proof")
            return renderFile.absolutePath
        } catch (error: Throwable) {
            runCatching { renderFile.delete() }
            throw error
        }
    }


    private fun checkGl(label: String) {
        val errors = ArrayList<String>()
        while (true) {
            val error = GLES30.glGetError()
            if (error == GLES20.GL_NO_ERROR) break
            errors += "0x${error.toString(16)}"
        }
        requireParity(errors.isEmpty(), "$label GL errors=$errors")
    }

    private fun requireParity(condition: Boolean, reason: String) {
        if (!condition) invalid(reason)
    }

    private fun invalid(reason: String): Nothing =
        throw IllegalStateException("MGC PARITY ARCHITECTURE INVALID: $reason")

    private class EglOwner(
        private val display: EGLDisplay,
        private val context: EGLContext,
        private val surface: EGLSurface,
    ) : AutoCloseable {
        companion object {
            fun create(): EglOwner {
                val display = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
                requireParity(display != EGL14.EGL_NO_DISPLAY, "eglGetDisplay failed")
                val versions = IntArray(2)
                requireParity(EGL14.eglInitialize(display, versions, 0, versions, 1),
                    "eglInitialize failed error=0x${EGL14.eglGetError().toString(16)}")
                val attrs = intArrayOf(
                    EGL14.EGL_RED_SIZE, 8,
                    EGL14.EGL_GREEN_SIZE, 8,
                    EGL14.EGL_BLUE_SIZE, 8,
                    EGL14.EGL_ALPHA_SIZE, 8,
                    EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT,
                    EGL14.EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR,
                    EGL14.EGL_NONE,
                )
                val configs = arrayOfNulls<EGLConfig>(1)
                val count = IntArray(1)
                requireParity(EGL14.eglChooseConfig(display, attrs, 0, configs, 0, 1, count, 0) &&
                        count[0] > 0 && configs[0] != null,
                    "no GLES3 pbuffer EGLConfig")
                val config = configs[0]!!
                val context = GlesGpuScheduler.createBackgroundContext(display, config, TAG)
                requireParity(context != EGL14.EGL_NO_CONTEXT,
                    "eglCreateContext failed error=0x${EGL14.eglGetError().toString(16)}")
                val surface = EGL14.eglCreatePbufferSurface(
                    display, config,
                    intArrayOf(EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE), 0)
                requireParity(surface != EGL14.EGL_NO_SURFACE,
                    "eglCreatePbufferSurface failed error=0x${EGL14.eglGetError().toString(16)}")
                requireParity(EGL14.eglMakeCurrent(display, surface, surface, context),
                    "eglMakeCurrent failed error=0x${EGL14.eglGetError().toString(16)}")
                PLog.i(TAG, "IRIS_26512_MGC1271_EGL_OWNER " +
                    "version=${GLES30.glGetString(GLES30.GL_VERSION)} " +
                    "renderer=${GLES30.glGetString(GLES30.GL_RENDERER)}")
                return EglOwner(display, context, surface)
            }
        }

        override fun close() {
            runCatching { GLES30.glFinish() }
            runCatching {
                EGL14.eglMakeCurrent(
                    display, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT)
            }
            runCatching { EGL14.eglDestroySurface(display, surface) }
            runCatching { EGL14.eglDestroyContext(display, context) }
            runCatching { EGL14.eglTerminate(display) }
        }
    }
}
