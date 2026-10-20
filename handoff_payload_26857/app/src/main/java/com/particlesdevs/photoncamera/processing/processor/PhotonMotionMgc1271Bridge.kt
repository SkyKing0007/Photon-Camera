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
import android.opengl.GLES31
import android.os.Build
import android.util.Half
import com.hinnka.mycamera.model.SafeImage
import com.hinnka.mycamera.processor.GlesGpuScheduler
import com.hinnka.mycamera.processor.GlesMgcRawFusion
import com.particlesdevs.photoncamera.settings.Iris26856ABSettings
import com.hinnka.mycamera.processor.GlesMgcRawSabreShaders
import com.hinnka.mycamera.processor.GpuLinearRgbStorage
import com.hinnka.mycamera.processor.MgcSabreKernelTuning
import com.hinnka.mycamera.processor.RawBurstFrameRole
import com.hinnka.mycamera.processor.RawNoiseProfileSelection
import com.hinnka.mycamera.processor.RawNoiseModel
import com.hinnka.mycamera.processor.RawStackBufferLayout
import com.hinnka.mycamera.processor.RawStackFrame
import com.hinnka.mycamera.processor.prewarmGlesMgcSabreCapturePrograms
import com.hinnka.mycamera.raw.MgcFullResolutionDenoise
import com.hinnka.mycamera.raw.RawMetadata
import com.hinnka.mycamera.raw.RawNoiseProfileLayout
import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.hinnka.mycamera.utils.PLog
import com.particlesdevs.photoncamera.app.PhotonCamera
import com.particlesdevs.photoncamera.processing.ImageFrame
import com.particlesdevs.photoncamera.processing.MotionBatch
import com.particlesdevs.photoncamera.processing.render.Parameters
import com.particlesdevs.photoncamera.util.MotionTrace
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicBoolean

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
    private val iris26715PrewarmStarted = AtomicBoolean(false)

    init {
        System.loadLibrary("my-native-lib")
    }

    /* IRIS_26715_IDLE_SABRE_PROGRAM_PREWARM
     * Best-effort first-shot latency optimization. It compiles only the existing Sabre GL program
     * set on an isolated pbuffer context while the camera is idle; failure is non-fatal and never
     * changes capture, merge, tone, or publication math.
     */
    @JvmStatic
    fun prewarmCapturePrograms(): Boolean {
        if (!iris26715PrewarmStarted.compareAndSet(false, true)) return true
        var egl: EglOwner? = null
        val tid = android.os.Process.myTid()
        val oldPriority = runCatching { android.os.Process.getThreadPriority(tid) }.getOrNull()
        val startNs = System.nanoTime()
        return try {
            runCatching { android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND) }
            egl = EglOwner.create()
            prewarmGlesMgcSabreCapturePrograms(4096, 3072, 0)
            PLog.i(TAG, "IRIS_26715_IDLE_SABRE_PROGRAM_PREWARM success=true tookMs=" +
                ((System.nanoTime() - startNs) / 1_000_000L))
            true
        } catch (error: Throwable) {
            iris26715PrewarmStarted.set(false)
            PLog.w(TAG, "IRIS_26715_IDLE_SABRE_PROGRAM_PREWARM success=false reason=" +
                error.javaClass.simpleName)
            false
        } finally {
            runCatching { egl?.close() }
            if (oldPriority != null) runCatching { android.os.Process.setThreadPriority(tid, oldPriority) }
        }
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
        var iris26826SharedCarrierForCleanup: MotionV2SharedRgba16fCarrier? = null
        // 26856 B: distinct post-RAWR camera-linear RGBA16F result, never Sabre/VGN.
        var iris26856BTextureForCleanup = 0
        var iris26856BSharedForCleanup: MotionV2SharedRgba16fCarrier? = null
        var iris26856BBufferForCleanup: ByteBuffer? = null
        var resultTexture = 0
        var clipZoneMaskTexture26836 = 0
        var true2xLinearRgbPathForCleanup: String? = null
        var true2xNativeVgnGuidePathForCleanup: String? = null
        var true2xPhaseSupportPathForCleanup: String? = null
        var true2xRenderRgbPathForCleanup: String? = null
        var true2xOutputHandedOff = false
        // B's sensor-neutral 2x RGB16F is independent of the historic A SR result.
        var iris26856BTrue2xPathForCleanup: String? = null
        var iris26856BTrue2xOutputHandedOff = false
        var highZoomDetailPathForCleanup: String? = null
        var highZoomDetailHandedOff = false
        var iris26856BHighZoomDetailHandedOff = false
        var highZoomRgbPathForCleanup: String? = null
        var highZoomRgbHandedOff = false
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

            val iris26593ShortExpected = shortSlot?.shortWasExpected() == true
            val iris26593LongExpected = shortSlot?.shadowWasExpected() == true
            val iris26593Frozen = shortSlot?.requiredFreezeComplete() == true
            shortFrame = shortSlot?.takeAndSeal()
            longFrame = shortSlot?.shadowAuxSlot?.takeAndSeal()
            requireParity(!iris26593ShortExpected || shortFrame != null,
                "IRIS_26593 requested SHORT disappeared after immutable batch freeze")
            requireParity(!iris26593LongExpected || longFrame != null,
                "IRIS_26593 requested LONG disappeared after immutable batch freeze")
            if (shortSlot != null) {
                requireParity(iris26593Frozen,
                    "IRIS_26593 bridge received an auxiliary slot before required freeze")
            }
            PLog.i(TAG, "IRIS_26593_AUX_OWNERSHIP_PROOF " +
                "shortExpected=$iris26593ShortExpected shortPresent=${shortFrame != null} " +
                "longExpected=$iris26593LongExpected longPresent=${longFrame != null} " +
                "normal=${inputImages.size} total=${inputImages.size + (if (shortFrame != null) 1 else 0) + (if (longFrame != null) 1 else 0)}")

            /* IRIS_26670_26660_NORMAL_MASTER_CAPTURE_TIME_SHORT_OWNER
             * Keep the successful 26660 reconstruction contract: the timestamp-owned ZSL NORMAL
             * frame is the structural/reference exposure, SHADOW_LONG is auxiliary shadow/SNR
             * evidence, and at most one generation-owned HIGHLIGHT_SHORT may be scheduled only as
             * the existing 26660 NORMAL-master radiometric highlight extension. SHORT never enters
             * the NORMAL temporal/motion/noise/DNG/SR body and must remain the final auxiliary frame.
             */
            if (!parameters.irisNightActive) {
                requireParity(shortFrame == null || iris26593ShortExpected,
                    "26670 unexpected Motion HIGHLIGHT_SHORT without capture-plan ownership")
            }
            val mgcBase = if (parameters.irisNightActive) {
                inputImages.firstOrNull { it.motionV2FrameRole == ImageFrame.MotionV2FrameRole.NORMAL }
                    ?: invalid("MGC Night NORMAL base is absent")
            } else {
                reference
            }
            val orderedPhysical = ArrayList<Pair<ImageFrame, RawBurstFrameRole>>()
            if (!parameters.irisNightActive) {
                orderedPhysical += reference to RawBurstFrameRole.NORMAL
                inputImages.forEachIndexed { index, frame ->
                    if (frame === reference) return@forEachIndexed
                    when (frame.motionV2FrameRole) {
                        ImageFrame.MotionV2FrameRole.NORMAL ->
                            orderedPhysical += frame to RawBurstFrameRole.NORMAL
                        ImageFrame.MotionV2FrameRole.SHADOW_LONG ->
                            invalid("main-list SHADOW_LONG is forbidden for Motion index=$index")
                        ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT ->
                            invalid("main-list HIGHLIGHT_SHORT is forbidden for Motion index=$index")
                    }
                }
            } else {
                inputImages.forEachIndexed { index, frame ->
                    val role = when (frame.motionV2FrameRole) {
                        ImageFrame.MotionV2FrameRole.NORMAL -> RawBurstFrameRole.NORMAL
                        ImageFrame.MotionV2FrameRole.SHADOW_LONG -> RawBurstFrameRole.SHADOW_LONG
                        ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT ->
                            invalid("main-list HIGHLIGHT_SHORT is forbidden; isolated slot ownership only index=$index")
                    }
                    orderedPhysical += frame to role
                }
            }
            /* IRIS_26674_PROTECTED_NORMAL_REFERENCE_HANDOFF
             * Preserve the successful-26673 NORMAL-master schedule, including isolated final
             * HIGHLIGHT_SHORT and fixed +2.5 EV SHADOW_LONG. The only restored 26661/26662
             * responsibility here is the immutable reference-protection EV carried by the selected
             * NORMAL reference into FLOAT-domain normalization/presentation. */
            longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }
            shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }
            parameters.motionV2ReferenceProtectionEv = if (parameters.irisNightActive) {
                0.0f
            } else {
                reference.motionV2ReferenceProtectionEv.coerceIn(0.0f, 1.50f)
            }
            PLog.i(TAG, "IRIS_26709_ADAPTIVE_NORMAL_REFERENCE_HANDOFF " +
                "night=${parameters.irisNightActive} referenceTimestamp=${mgcBase.timestamp} " +
                "referenceFromOwnedZsl=${!parameters.irisNightActive} shadowLong=${longFrame != null} " +
                "highlightShort=${shortFrame != null} shortFinal=${shortFrame == null || orderedPhysical.last().second == RawBurstFrameRole.HIGHLIGHT_SHORT} " +
                "referenceProtectionEv=${parameters.motionV2ReferenceProtectionEv} " +
                "normalTemporalOwner=true shortTemporalOwner=false longGlobalBrightnessAuthority=false")

            orderedPhysical.forEachIndexed { index, (frame, role) ->
                validateFrame(frame, size, role, reference.motionV2ExposureEnergy, index)
                if (role != RawBurstFrameRole.NORMAL) {
                    val ratioToNormal = frame.motionV2ExposureEnergy /
                        reference.motionV2ExposureEnergy
                    val admission = when (role) {
                        RawBurstFrameRole.HIGHLIGHT_SHORT -> "COMMON_SABRE_HIGHLIGHT_EVIDENCE"
                        RawBurstFrameRole.SHADOW_LONG -> if (parameters.irisNightActive) {
                            "SABRE_NIGHT_SHADOW_LUMINANCE_ONLY"
                        } else {
                            "SABRE_MOTION_SHADOW_LUMINANCE_ONLY"
                        }
                        else -> "NORMAL"
                    }
                    val details =
                        "role=$role exposureTimeNs=${frame.motionV2ActualExposureNs} " +
                            "iso=${frame.motionV2ActualIso} " +
                            "black=${frame.motionV2BlackLevel.contentToString()} " +
                            "white=${frame.motionV2WhiteLevel} exposureRatioToNormal=$ratioToNormal " +
                            "admission=$admission night=${parameters.irisNightActive}"
                    PLog.i(TAG, "IRIS_26605_AUX_PHYSICAL_METADATA $details")
                    PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26605_AUX_PHYSICAL_METADATA details=$details")
                }
            }

            /* IRIS_26856_AB_IMMUTABLE_RECONSTRUCTION_INTENT
             * The chosen physical-lens mode was captured at shutter into the NORMAL
             * reference ImageFrame. No processing-time preferences are consulted.
             * A/B results must not silently substitute inherited Sabre RGB
             * for the independent RAWR processing result. */
            val experiment26856 = if (parameters.irisNightActive) {
                Iris26856ABSettings.Mode.ORIGINAL_26850
            } else {
                val id = reference.motionV2ReconstructionExperiment26856
                    ?: invalid("26856 Motion reference missing shutter-frozen reconstruction mode")
                Iris26856ABSettings.Mode.parse(id)
            }
            /* IRIS_26856_AB_ACTIVE_FAIL_CLOSED_OWNERSHIP
             * B returns a native RAWR AMaZE/Lab/FCC linear carrier; A+B
             * independently invokes historical 26850 from the same frozen
             * RAW frames. Each selected result has its own HDR/JPEG owner.
             * Validation failures throw; they never convert B into A. */
            PLog.i(TAG, "IRIS_26856_AB_MODE_FREEZE mode=$experiment26856 physical=${reference.motionV2PhysicalCameraId} timestamp=$referenceTimestamp")

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
            /* IRIS_26767_LOCAL_MEDIAN_CHROMA_CORRECTION_CONTROL
             * Motion freezes the fresh per-lens experimental value once for this processing
             * generation. It is carried through the existing VGN parameter transport but consumed
             * only by localMedian. Night remains byte-behavior equivalent at the proven 1.0. */
            val vgnChromaCorrectionStrength = if (parameters.irisNightActive) {
                1.0f
            } else {
                irisSettings.chromaCorrectionStrength.coerceIn(0.0f, 1.0f)
            }
            parameters.motionV2ReconstructionOwner = Parameters.MOTION_V2_RECONSTRUCTION_SABRE
            PLog.i(TAG, "IRIS_26560_SABRE_ONLY_RECONSTRUCTION " +
                "method=SABRE localMedianChromaCorrection=$vgnChromaCorrectionStrength localMedianOnly26767=true nightForcedOne=${parameters.irisNightActive} " +
                "night=${parameters.irisNightActive} dngRequested=$produceNormalStackedDng " +
                "superResRequested=${parameters.motionV2SuperResOutputEnabled}")

            val noiseSelection: RawNoiseProfileSelection
            val noiseAuthority: String
            var denoiseNoiseProfileLayout = RawNoiseProfileLayout.NONE
            var denoiseChannelNoiseProfile = floatArrayOf()
            /* IRIS_26762_FROZEN_ADAPTIVE_CHROMA_CAPTURE_STATE
             * Freeze both controls once per processing generation before Sabre construction.
             * This avoids shared mutable settings reads inside the GPU path and makes the exact
             * Auto/Custom ownership decision available to Super Res before residual denoise. */
            val adaptiveSnrChroma26762 = irisSettings.adaptiveSnrChromaDenoise.coerceIn(0.5f, 2.0f)
            val frozenResidualChromaCustom26762 = !parameters.irisNightActive && irisSettings.residualChromaCustom
            parameters.motionV2EdgeSuppressAll26792 = irisSettings.edgeFalseColorAllEdges26792
            parameters.motionV2SdrBodyContrast26792 = irisSettings.sdrBodyContrast26792
            val edgeFalseColor26778 = IrisMotionSettings.EdgeFalseColorTunables.current(
                parameters.motionV2EdgeSuppressAll26792,
            )
            val dngOptions26786 = if (parameters.irisNightActive) {
                /* IRIS_26791_NIGHT_SHARED_PHYSICAL_NEUTRAL_RULE
                 * Night already uses the same normalDngMerge/normalizeBayer architecture and
                 * default-on fixed-phase LCA. The physical two-green censor condition is not a
                 * Motion aesthetic policy, so Night JPEG and Night DNG enable the same neutral
                 * clamp without changing Night exposure, frames, reconstruction, VGN or tone. */
                val nightBase26791 = IrisMotionSettings.DngOptions.defaults()
                IrisMotionSettings.DngOptions.Snapshot(
                    nightBase26791.lcaEnabled,
                    nightBase26791.kR,
                    nightBase26791.kB,
                    nightBase26791.quadScopedHeadroom,
                    nightBase26791.edgeDeAlias,
                    true,
                    "NIGHT_DEFAULTS_NEUTRAL_26791",
                )
            } else {
                parameters.motionV2DngOptions26786 ?: IrisMotionSettings.DngOptions.defaults()
            }
            val dngOptionsLine26791 =
                "lca=${dngOptions26786.lcaEnabled} kR=${dngOptions26786.kR} kB=${dngOptions26786.kB} " +
                    "headroomScope=${dngOptions26786.headroomScopeName()} deAlias=${dngOptions26786.edgeDeAlias} " +
                    "neutralClamp=${dngOptions26786.neutralClamp} settingsSource=${dngOptions26786.source}"
            PLog.i(
                TAG,
                if (parameters.irisNightActive) {
                    "IRIS_26791_NIGHT_DNG_JPEG_PHYSICAL_OPTIONS $dngOptionsLine26791"
                } else {
                    "IRIS_26786_DNG_OPTIONS $dngOptionsLine26791"
                },
            )
            PLog.i(
                TAG,
                "IRIS_26792_OPTIONS mode=${if (parameters.irisNightActive) "NIGHT" else "MOTION"} " +
                    "lca=${dngOptions26786.lcaEnabled} neutralClamp=${dngOptions26786.neutralClamp} " +
                    "lcaSnapCodePaths=0 edgeSuppressorEnabled=${edgeFalseColor26778.enabled} " +
                    "edgeSuppressAll=${edgeFalseColor26778.allEdges26792} " +
                    "contrastLo=${edgeFalseColor26778.contrastLo} contrastHi=${edgeFalseColor26778.contrastHi} " +
                    "outlierLo=${edgeFalseColor26778.outlierLo} outlierHi=${edgeFalseColor26778.outlierHi} " +
                    "sdrBodyContrast=${parameters.motionV2SdrBodyContrast26792} " +
                    "kR=${dngOptions26786.kR} kB=${dngOptions26786.kB} " +
                    "decodedUhHdrTargetFrozen=true identicalInputRebase=true",
            )

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
                    image = safeImage(
                        frame, size,
                        retainForDual26856 = experiment26856 == Iris26856ABSettings.Mode.BOTH,
                    ),
                    sensorTimestampNs = frame.motionV2ResultSensorTimestampNs.takeIf { it > 0L }
                        ?: frame.timestamp,
                    frameNumber = frame.motionV2FrameNumber,
                    exposureTimeNs = frame.motionV2ActualExposureNs,
                    sensitivityIso = frame.motionV2ActualIso,
                    exposureProduct = frame.motionV2ExposureEnergy,
                    desiredExposureProduct = null,
                    focusDistanceDiopters = frame.motionV2FocusDistanceDiopters,
                    lensState = frame.motionV2LensState.takeIf { it >= 0 },
                    physicalCameraId = frame.motionV2PhysicalCameraId,
                    rollingShutterSkewNs = frame.motionV2RollingShutterSkewNs.takeIf { it > 0L },
                    verifiedHotPixelCoordinates26855 = frame.motionV2VerifiedHotPixels26855.copyOf(),
                    channelNoiseProfile = if (irisSettings.customNoiseModelEnabled) {
                        null
                    } else {
                        frame.motionV2NoiseProfile.copyOf()
                    },
                    dynamicBlackLevelByCfaPosition = frame.motionV2BlackLevel.copyOf(),
                    rowFlickerHarmonic = if (role == RawBurstFrameRole.NORMAL && frame.motionV2RowFlickerValid)
                        frame.motionV2RowFlickerHarmonic else 0,
                    rowFlickerA = if (role == RawBurstFrameRole.NORMAL && frame.motionV2RowFlickerValid)
                        frame.motionV2RowFlickerA else 0f,
                    rowFlickerB = if (role == RawBurstFrameRole.NORMAL && frame.motionV2RowFlickerValid)
                        frame.motionV2RowFlickerB else 0f,
                    rowFlickerStrength = if (role == RawBurstFrameRole.NORMAL && frame.motionV2RowFlickerValid)
                        frame.motionV2RowFlickerStrength else 0f,
                    gyroShakiness = frame.frameGyro?.shakiness?.takeIf { it.isFinite() && it >= 0f } ?: Float.NaN,
                    gyroSampleCount = frame.frameGyro?.samples ?: 0,
                    dngOptions26786 = dngOptions26786,
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
            /* IRIS_26856_B_TRUE2X_GUARDED_ACTIVATION
             * The independent pinned-RAWR B 2x tile executor is now present.
             * It consumes all NORMAL CFA evidence, verifies every output site
             * before invoking AMaZE, and publishes its own atomic RGB16F file.
             * There is never an A/VGN RGB fallback. Preserve historical Night
             * routing rather than treating a Motion B-mode preference as Night.
             */
            requireParity(!sabreSuperResEnabled || !parameters.irisNightActive ||
                experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850,
                "26856 B true2x is Motion-only; Night Super Res belongs to historical A")
            val sabreSuperResOutputScale = if (sabreSuperResEnabled) 2f else 1f
            parameters.motionV2SuperResOutputScale = sabreSuperResOutputScale
            /* IRIS_26758_UNIVERSAL_LENS_RELATIVE_DIRECT_CFA_SR
             * Device-independent and physical-lens-relative: every optical lens may contribute
             * same-lens multiframe SR detail from local 1.10x upward. Super Res uses the full true-2x
             * GPU route. Ordinary zoom uses only the centered crop-first scalar sidecar. Sabre/VGN
             * remains the sole RGB/chroma/highlight owner and no cross-lens frame mixing is allowed.
             */
            /* IRIS_26856_B_NATIVE_ZOOM_SUPER_RES_OWNER
             * At local zoom >=1.10x, both A and B use the existing bounded
             * NORMAL-only, crop-first CFA luminance evidence, resolved against
             * their OWN independently reconstructed color master. B never
             * consumes an A/Sabre/VGN RGB or high-zoom file. This native-size
             * zoom path is independent of the optional B true-2x toggle.
             */
            val highZoomDetailEnabled = parameters.motionV2Active && !parameters.irisNightActive &&
                !sabreSuperResEnabled && localOutputZoom >= 1.10f
            parameters.motionV2HighZoomDetailPath = null
            parameters.motionV2HighZoomDetailWidth = 0
            parameters.motionV2HighZoomDetailHeight = 0
            parameters.motionV2HighZoomDetailOriginX = 0
            parameters.motionV2HighZoomDetailOriginY = 0
            parameters.motionV2HighZoomDetailFullWidth = 0
            parameters.motionV2HighZoomDetailFullHeight = 0
            parameters.motionV2HighZoomDetailScaleX = 1f
            parameters.motionV2HighZoomDetailScaleY = 1f
            parameters.motionV2HighZoomDetailOriginXF = 0f
            parameters.motionV2HighZoomDetailOriginYF = 0f
            parameters.motionV2HighZoomDetailSourceZoom = localOutputZoom
            parameters.motionV2HighZoomDetailActivePct = 0f
            parameters.motionV2HighZoomDetailStrongPct = 0f
            parameters.motionV2HighZoomRefineAcceptedPct = 0f
            parameters.motionV2HighZoomDetailFrames = 0
            parameters.motionV2HighZoomDetailReconstructionMs = 0L
            parameters.motionV2HighZoomRgbPath = null
            parameters.motionV2HighZoomRgbWidth = 0
            parameters.motionV2HighZoomRgbHeight = 0
            parameters.motionV2HighZoomRgbOriginX = 0
            parameters.motionV2HighZoomRgbOriginY = 0
            parameters.motionV2HighZoomRgbFullWidth = 0
            parameters.motionV2HighZoomRgbFullHeight = 0
            parameters.motionV2HighZoomRgbSourceZoom = localOutputZoom
            parameters.motionV2HighZoomRgbActivePct = 0f
            parameters.motionV2HighZoomRgbFullColorPct = 0f
            parameters.motionV2HighZoomRgbPhaseMean = 0f
            parameters.motionV2HighZoomRgbPhaseP10 = 0f
            parameters.motionV2HighZoomRgbRefineAcceptedPct = 0f
            parameters.motionV2HighZoomRgbFrames = 0
            parameters.motionV2HighZoomRgbReconstructionMs = 0L
            parameters.motionV2HighZoomRgbPrepared = false
            parameters.motionV2HighZoomRgbApplied = false
            val referenceStackFrame = frames.firstOrNull { it.frameNumber == mgcBase.motionV2FrameNumber } ?: frames.first()
            val highZoomActivation = "enabled=$highZoomDetailEnabled displayedGlobalZoom=$displayedGlobalZoom " +
                "localOutputZoom=$localOutputZoom localThreshold=1.10 opticalAnchor=${parameters.motionV2OpticalZoomAnchor} " +
                "superResRequested=$sabreSuperResEnabled focusDistanceDiopters=${referenceStackFrame.focusDistanceDiopters} " +
                "lensState=${referenceStackFrame.lensState} physicalCameraId=${referenceStackFrame.physicalCameraId} " +
                "rgbOwner=${if (experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855) "B_RAWR_AMAZE" else if (experiment26856 == Iris26856ABSettings.Mode.BOTH) "A_AND_B_INDEPENDENT" else "A_SABRE_VGN"} " +
                "lumaDetailOwner=${if (highZoomDetailEnabled || sabreSuperResEnabled) "DIRECT_CFA_TEMPORAL_ADAPTIVE" else "NATIVE"} " +
                "deviceGate=false cleanNativeFallback=true allNormalsSabre=true detailEvidenceBounded=true directNativePlanB=false " +
                "adaptiveReject=true flatHighlightVeto=true secondScaler=false"
            PLog.i(TAG, "IRIS_26758_UNIVERSAL_SR_ACTIVATION $highZoomActivation")
            MotionTrace.processingState("IRIS_26758_UNIVERSAL_SR_ACTIVATION", highZoomActivation)
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
                allowSabreShadowLong = parameters.irisNightActive || longFrame != null,
                preserveExtendedHdrThroughVgn = !parameters.irisNightActive,
                useCurrentGlContext = true,
                exportGpuLinearRgbSource = true,
                gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
                exportNormalStackedDng = produceNormalStackedDng,
                vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,
                /* IRIS_26856_SR_DISJOINT_ACTIVE_OWNERS
                 * The inherited A true2x path must not execute inside B. A+B
                 * reconstructs A separately using the exact historical 26850
                 * stacker; this B call consumes its own measured NORMAL CFA.
                 */
                enableSabreSuperRes = sabreSuperResEnabled &&
                    experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850,
                sabreSuperResTempDir = PhotonCamera.getApplicationContextStatic().cacheDir,
                enableHighZoomDetail = highZoomDetailEnabled,
                highZoomSourceZoom = localOutputZoom,
                /* IRIS_26762_FROZEN_ADAPTIVE_CHROMA_TRANSPORT */
                adaptiveSnrChromaDenoise = adaptiveSnrChroma26762,
                residualChromaCustom = frozenResidualChromaCustom26762,
                edgeFalseColor26778 = edgeFalseColor26778,
                /* IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION_CONTEXT
                 * Read-only downstream context. This value is already frozen from the selected
                 * 26674 NORMAL reference and cannot alter sensor/ZSL/capture exposure ownership. */
                referenceProtectionEv = 0f,
                exactHistorical26850 = !parameters.irisNightActive &&
                    experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850,
                /* IRIS_26856_B_ONLY_LIVE_RAW_CFA_TO_RAWR_CHAIN
                 * Executed only when the frozen shutter mode selects B/A+B;
                 * a missing native capability fails the capture. Does not
                 * run in A/26850. The GL callback is synchronous; both textures
                 * are owned by the same stacker invocation and the JNI import
                 * waits for completion before returning. */
                /* IRIS_26856_B_TRUE2X_SEPARATE_NORMAL_CFA_OWNER
                 * Native HDR/JPEG publication consumes the checked B-owned
                 * 2x RGB16F file. A remains an independent 26850 invocation;
                 * unsupported GPU, sparse phases and missing sites fail shut. */
                /* B-only bypasses unused A/VGN after the shared NORMAL + LONG CFA producers.
                 * BOTH deliberately retains the historical two-reconstruction contract. */
                iris26856BOnlyIndependentPublication = !parameters.irisNightActive &&
                    experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855,
                iris26856BTrue2x = sabreSuperResEnabled && !parameters.irisNightActive &&
                    experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850,
                iris26856RawrColor = if (!parameters.irisNightActive &&
                    experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850) {
                    com.hinnka.mycamera.processor.GlesIris26856RawrColorContract.freeze(
                        wb, parameters.motionV2ColorTransform.copyOf(),
                        parameters.motionV2DirectColorValid,
                    )
                } else null,
                iris26856AmazeCfaConsumer = if (!parameters.irisNightActive &&
                    experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850) {
                    { packed: Int, output: Int, rawWidth: Int, rawHeight: Int,
                      pattern: Int, gains: FloatArray ->
                        com.hinnka.mycamera.processor.GlesIris26856AmazeNative.execute(
                            PhotonCamera.getApplicationContextStatic(), packed, output,
                            rawWidth, rawHeight, pattern, gains,
                        )
                    }
                } else null,
            )
            val iris26535FusionStartNs = System.nanoTime()
            val stackB26856 = fusion.processFrames(frames)
                ?: invalid("Iris Sabre/RAWR owner returned null")
            iris26856BTrue2xPathForCleanup = stackB26856.iris26856BTrue2xRgbPath
            /* IRIS_26856_B_ZOOM_DETAIL_SEPARATE_POST_HANDOFF
             * Independently named B R16F sidecar, never overwritten by the
             * historical A processFrames call in A+B. The Hdrx B post snapshot
             * consumes this record; original A parameters remain unchanged.
             */
            parameters.iris26856BHighZoomDetail = if (
                experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850 &&
                highZoomDetailEnabled && stackB26856.highZoomDetailPath != null
            ) Parameters.Iris26856BHighZoomDetail(
                stackB26856.highZoomDetailPath!!,
                stackB26856.highZoomDetailWidth,
                stackB26856.highZoomDetailHeight,
                stackB26856.highZoomDetailOriginX,
                stackB26856.highZoomDetailOriginY,
                stackB26856.highZoomDetailFullWidth,
                stackB26856.highZoomDetailFullHeight,
                stackB26856.highZoomDetailScaleX,
                stackB26856.highZoomDetailScaleY,
                stackB26856.highZoomDetailOriginXF,
                stackB26856.highZoomDetailOriginYF,
                stackB26856.highZoomDetailSourceZoom,
                stackB26856.highZoomDetailActivePct,
                stackB26856.highZoomDetailStrongPct,
                stackB26856.highZoomRefineAcceptedPct,
                stackB26856.highZoomDetailFrames,
                stackB26856.highZoomDetailReconstructionMs,
            ) else null
            if (highZoomDetailEnabled && experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850) {
                PLog.i(TAG, "IRIS_26856_B_NATIVE_ZOOM_DETAIL_ROUTED " +
                    "zoom=$localOutputZoom ownBGuide=true ready=${parameters.iris26856BHighZoomDetail != null} " +
                    "aUnchanged=true independentTrue2x=false")
            }
            /* IRIS_26856_AB_TRUE_26850_PLUS_26855_TWO_RECONSTRUCTIONS
             * B first completes the 26855 all-NORMAL temporal-CFA + pinned AMaZE
             * pipeline. A then reconstructs from independent SafeImage adapters
             * over the SAME already-frozen ImageFrame RAW bytes using the exact
             * historical 26850 implementation. No second shutter, ring-buffer
             * admission, alignment reuse masquerading as A, or post-VGN RGB
             * substitution is allowed. The DNG stays owned once by B's 26855
             * normal stack; only A produces historical true-2x/zoom extras.
             */
            val stacked = if (experiment26856 == Iris26856ABSettings.Mode.BOTH) {
                val historicalFrames = frames.mapIndexed { index, f ->
                    val physical = orderedPhysical[index].first
                    f.copy(image = safeImage(physical, size, retainForDual26856 = true))
                }
                val historical = GlesMgcRawFusion(
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
                    allowSabreShadowLong = longFrame != null,
                    preserveExtendedHdrThroughVgn = true,
                    useCurrentGlContext = true,
                    exportGpuLinearRgbSource = true,
                    gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
                    exportNormalStackedDng = false, // exactly one 26855 DNG owner
                    vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,
                    enableSabreSuperRes = sabreSuperResEnabled,
                    sabreSuperResTempDir = PhotonCamera.getApplicationContextStatic().cacheDir,
                    enableHighZoomDetail = highZoomDetailEnabled,
                    highZoomSourceZoom = localOutputZoom,
                    adaptiveSnrChromaDenoise = adaptiveSnrChroma26762,
                    residualChromaCustom = frozenResidualChromaCustom26762,
                    edgeFalseColor26778 = edgeFalseColor26778,
                    referenceProtectionEv = 0f,
                    exactHistorical26850 = true,
                    iris26856AmazeCfaConsumer = null,
                    iris26856RawrColor = null,
                ).processFrames(historicalFrames)
                    ?: invalid("26856 AB exact 26850 reconstruction failed")
                requireParity(stackB26856.iris26856RawrRgbSidecar != null,
                    "26856 AB 26855 did not publish independent RAWR RGB")
                requireParity(historical.iris26856RawrRgbSidecar == null,
                    "26856 AB historical 26850 illegally generated B RGB")
                requireParity(stackB26856.mergedFrameCount == historical.mergedFrameCount,
                    "26856 AB actual NORMAL frame population diverged")
                requireParity(!produceNormalStackedDng ||
                    stackB26856.normalStackedDngRaw16 != null,
                    "26856 AB 26855 DNG evidence missing")
                // The second (historical A) reconstruction owns its own normal
                // RGB. The temporary 26855 post-VGN RGB is NOT B and cannot be
                // published, even when it happens to look visually reasonable.
                stackB26856.gpuLinearRgbSource?.let { rejected ->
                    rejected.stackCompletionTimeline?.releasePending()
                    GLES30.glDeleteTextures(1, intArrayOf(rejected.textureId), 0)
                    if (rejected.clipZoneMaskTextureId26836 != 0)
                        GLES30.glDeleteTextures(
                            1, intArrayOf(rejected.clipZoneMaskTextureId26836), 0)
                    checkGl("26856 discard interim 26855 Sabre RGB")
                }
                stackB26856.fusedBayerBuffer?.let(LargeDirectBuffer::free)
                PLog.i(TAG, "IRIS_26856_AB_TWO_TRUE_RECONSTRUCTIONS " +
                    "historicalA=26850 nativeB=26855_AMAZE sameRawBatch=true " +
                    "normalFrames=${historical.mergedFrameCount} dngOwner=B_26855 " +
                    "shortOwnedByBoth=true noSecondCapture=true")
                historical.copy(
                    iris26856RawrRgbSidecar = stackB26856.iris26856RawrRgbSidecar,
                    iris26856BTrue2xRgbPath = stackB26856.iris26856BTrue2xRgbPath,
                    iris26856BTrue2xWidth = stackB26856.iris26856BTrue2xWidth,
                    iris26856BTrue2xHeight = stackB26856.iris26856BTrue2xHeight,
                    normalStackedDngRaw16 = stackB26856.normalStackedDngRaw16,
                    normalStackedDngFrameCount = stackB26856.normalStackedDngFrameCount,
                    normalStackedDngNoiseProfile = stackB26856.normalStackedDngNoiseProfile,
                    normalStackedDngSupportMin = stackB26856.normalStackedDngSupportMin,
                    normalStackedDngSupportP01 = stackB26856.normalStackedDngSupportP01,
                    normalStackedDngSupportP10 = stackB26856.normalStackedDngSupportP10,
                    normalStackedDngSupportMedian = stackB26856.normalStackedDngSupportMedian,
                    normalStackedDngSupportMean = stackB26856.normalStackedDngSupportMean,
                    normalStackedDngSupportMax = stackB26856.normalStackedDngSupportMax,
                    normalStackedDngNoiseEquivalentSupport = stackB26856.normalStackedDngNoiseEquivalentSupport,
                )
            } else stackB26856
            parameters.motionV2ShortRadianceAuthorityMask = stacked.shortRadianceAuthorityMask?.copyOf()
            parameters.motionV2ShortRadianceAuthorityWidth = stacked.shortRadianceAuthorityWidth
            parameters.motionV2ShortRadianceAuthorityHeight = stacked.shortRadianceAuthorityHeight
            PLog.i(TAG, "IRIS_26708_SHORT_AUTHORITY_HANDOFF active=" +
                (parameters.motionV2ShortRadianceAuthorityMask?.count { it.toInt() != 0 } ?: 0) +
                " size=${parameters.motionV2ShortRadianceAuthorityWidth}x${parameters.motionV2ShortRadianceAuthorityHeight}")
            /* B true2x is never a replacement for A's DNG/SR or Sabre RGB. */
            val b2x26856 = stacked.iris26856BTrue2xRgbPath?.let(::File)
            if (sabreSuperResEnabled && experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850) {
                requireParity(b2x26856 != null && b2x26856.isFile &&
                    stacked.iris26856BTrue2xWidth == size.x * 2 &&
                    stacked.iris26856BTrue2xHeight == size.y * 2 &&
                    b2x26856.length() == stacked.iris26856BTrue2xWidth.toLong() *
                        stacked.iris26856BTrue2xHeight * 6L,
                    "26856 B 2x requires complete independent sensor-neutral RGB16F")
            } else {
                requireParity(b2x26856 == null,
                    "26856 B 2x must not run outside selected B/A+B Super Res")
            }
            true2xLinearRgbPathForCleanup = stacked.true2xLinearRgbPath
            true2xRenderRgbPathForCleanup = stacked.true2xRenderRgbPath
            true2xPhaseSupportPathForCleanup = stacked.true2xPhaseSupportPath
            true2xNativeVgnGuidePathForCleanup = stacked.true2xNativeVgnGuidePath
            highZoomDetailPathForCleanup = stacked.highZoomDetailPath
            /* In A+B, stacked is historical A; B's different file remains
             * independently owned by the Hdrx B post or error cleanup below. */
            highZoomRgbPathForCleanup = stacked.highZoomRgbPath
            if (highZoomDetailEnabled) {
                requireParity(stacked.highZoomRgbPath == null, "26758 direct-CFA detail must never publish high-zoom RGB/chroma")
                if (stacked.highZoomDetailPath != null) {
                    requireParity(stacked.highZoomDetailWidth > 0 && stacked.highZoomDetailHeight > 0 &&
                        stacked.highZoomDetailScaleX >= 1f && stacked.highZoomDetailScaleY >= 1f,
                        "26758 invalid direct-CFA detail geometry")
                    val expectedNormalFrames26758 = frames.count { it.role == RawBurstFrameRole.NORMAL }
                    /* IRIS_26758_DIRECT_CFA_DETAIL_HANDOFF
                     * The sidecar is a centered subset of the same lens's true-2x lattice and may
                     * therefore be up to 2x native dimensions at short digital zoom. Sabre still
                     * consumed every NORMAL; only auxiliary detail evidence is bounded to <=8.
                     */
                    requireParity(
                        stacked.highZoomDetailWidth in 1..(size.x * 2) && stacked.highZoomDetailHeight in 1..(size.y * 2),
                        "26758 direct-CFA detail lattice outside true2x bounds expected<=${size.x * 2}x${size.y * 2} " +
                            "actual=${stacked.highZoomDetailWidth}x${stacked.highZoomDetailHeight}",
                    )
                    requireParity(
                        stacked.highZoomDetailFrames in 2..minOf(8, expectedNormalFrames26758),
                        "26758 detail evidence count invalid baseNormals=$expectedNormalFrames26758 actual=${stacked.highZoomDetailFrames}",
                    )
                    requireParity(kotlin.math.abs(stacked.highZoomDetailSourceZoom - localOutputZoom) < 1.0e-5f,
                        "26758 direct-CFA source zoom mismatch")
                    parameters.motionV2HighZoomDetailPath = stacked.highZoomDetailPath
                    parameters.motionV2HighZoomDetailWidth = stacked.highZoomDetailWidth
                    parameters.motionV2HighZoomDetailHeight = stacked.highZoomDetailHeight
                    parameters.motionV2HighZoomDetailOriginX = stacked.highZoomDetailOriginX
                    parameters.motionV2HighZoomDetailOriginY = stacked.highZoomDetailOriginY
                    parameters.motionV2HighZoomDetailFullWidth = stacked.highZoomDetailFullWidth
                    parameters.motionV2HighZoomDetailFullHeight = stacked.highZoomDetailFullHeight
                    parameters.motionV2HighZoomDetailScaleX = stacked.highZoomDetailScaleX
                    parameters.motionV2HighZoomDetailScaleY = stacked.highZoomDetailScaleY
                    parameters.motionV2HighZoomDetailOriginXF = stacked.highZoomDetailOriginXF
                    parameters.motionV2HighZoomDetailOriginYF = stacked.highZoomDetailOriginYF
                    parameters.motionV2HighZoomDetailSourceZoom = stacked.highZoomDetailSourceZoom
                    parameters.motionV2HighZoomDetailActivePct = stacked.highZoomDetailActivePct
                    parameters.motionV2HighZoomDetailStrongPct = stacked.highZoomDetailStrongPct
                    parameters.motionV2HighZoomRefineAcceptedPct = stacked.highZoomRefineAcceptedPct
                    parameters.motionV2HighZoomDetailFrames = stacked.highZoomDetailFrames
                    parameters.motionV2HighZoomDetailReconstructionMs = stacked.highZoomDetailReconstructionMs
                    val handoff = "path=true size=${stacked.highZoomDetailWidth}x${stacked.highZoomDetailHeight} " +
                        "origin=${stacked.highZoomDetailOriginXF},${stacked.highZoomDetailOriginYF} " +
                        "scale=${stacked.highZoomDetailScaleX},${stacked.highZoomDetailScaleY} " +
                        "sourceZoom=${stacked.highZoomDetailSourceZoom} frames=${stacked.highZoomDetailFrames} " +
                        "activePct=${stacked.highZoomDetailActivePct} strongPct=${stacked.highZoomDetailStrongPct} " +
                        "ms=${stacked.highZoomDetailReconstructionMs} cropFirstTrue2xLattice=true baseNormals=$expectedNormalFrames26758 secondScaler=false " +
                        "rgbOwner=${if (experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855) "B_RAWR_AMAZE" else "A_SABRE_VGN"} " +
                        "chromaAndHighlightOwnedBySelectedReconstruction=true adaptiveReject=true"
                    PLog.i(TAG, "IRIS_26758_DIRECT_CFA_HIGH_ZOOM_HANDOFF $handoff")
                    MotionTrace.processingState("IRIS_26758_DIRECT_CFA_HIGH_ZOOM_HANDOFF", handoff)
                } else {
                    PLog.i(TAG, "IRIS_26758_DIRECT_CFA_HIGH_ZOOM_NATIVE_FALLBACK sourceZoom=$localOutputZoom")
                    MotionTrace.processingState("IRIS_26758_DIRECT_CFA_HIGH_ZOOM_NATIVE_FALLBACK",
                        "sourceZoom=$localOutputZoom rgbOwner=NATIVE_SABRE_VGN detail=false noExtraDelay=true")
                }
            } else {
                requireParity(stacked.highZoomRgbPath == null && stacked.highZoomDetailPath == null &&
                    stacked.highZoomRgbWidth == 0 && stacked.highZoomDetailWidth == 0,
                    "26758 direct-CFA sidecar survived disabled route")
            }
            val expectedRgbMergedFrames26833 = frames.count { it.role == RawBurstFrameRole.NORMAL }
            val scheduledLongLumaFrames26833 = frames.count { it.role == RawBurstFrameRole.SHADOW_LONG }
            if (parameters.irisNightActive) {
                /* IRIS_26833_NIGHT_LONG_LUMINANCE_ONLY_PARITY
                 * Every Night LONG stays in the immutable schedule, but none may count as RGB,
                 * chroma, temporal-noise or detail support. mergedFrameCount is NORMAL-only. */
                requireParity(stacked.mergedFrameCount == expectedRgbMergedFrames26833,
                    "26833 Night RGB merged=${stacked.mergedFrameCount} normals=$expectedRgbMergedFrames26833 " +
                        "longLuma=$scheduledLongLumaFrames26833 total=${frames.size}")
                PLog.i(TAG, "IRIS_26833_NIGHT_LONG_LUMINANCE_ONLY_PARITY " +
                    "normals=$expectedRgbMergedFrames26833 longLuma=$scheduledLongLumaFrames26833 " +
                    "total=${frames.size} longRgbAuthority=false longTemporalSupport=false")
            }
            iris26535FusionMs = (System.nanoTime() - iris26535FusionStartNs) / 1_000_000L
            requireParity(stacked.width == size.x && stacked.height == size.y,
                "Sabre native-grid output geometry ${stacked.width}x${stacked.height} != ${size.x}x${size.y}")
            val expectedSuperResWidth = if (sabreSuperResEnabled) size.x * 2 else 0
            val expectedSuperResHeight = if (sabreSuperResEnabled) size.y * 2 else 0
            /* IRIS_26752_TRUE_2X_PUBLICATION_SPLIT
             * Retired fake-SR carriers remain forbidden. JPEG/UHDR use Plan-B luma detail over the
             * native Sabre/VGN RGB/chroma/highlight owner. If DNG is requested, its established
             * 26733 direct-CFA linear-RAW boundary remains separate and unchanged.
             */
            requireParity(
                stacked.superResDetailPath == null && stacked.superResLinearRawPath == null &&
                    stacked.superResWidth == 0 && stacked.superResHeight == 0,
                "26564 retired fake-SR carrier unexpectedly survived",
            )
            // A and A+B retain exact 26850 true2x ownership. B-only uses its
            // separately byte-proven RAWR RGB16F carrier, never A's backend.
            if (sabreSuperResEnabled &&
                experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855) {
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
            /* IRIS_26856_B_SEPARATE_GPU_CARRIER_OWNER
             * The stacker transferred a distinct RAWR result texture. This bridge
             * owns its deletion and data transport; neither DNG nor the inherited
             * A Sabre RGB carrier may substitute for it. A/26850 must produce none. */
            val bGpu26856 = stacked.iris26856RawrRgbSidecar
            if (experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850) {
                requireParity(bGpu26856 == null, "26856 A unexpectedly generated an AMaZE RGB carrier")
            } else {
                requireParity(bGpu26856 != null, "26856 B missing AMaZE/Lab/FCC sensor-neutral RGB")
            }
            bGpu26856?.let { carrier ->
                requireParity(carrier.width == size.x && carrier.height == size.y &&
                    carrier.storage == GpuLinearRgbStorage.RGBA16F && carrier.samplesPerPixel == 4 &&
                    carrier.textureId != 0,
                    "26856 B RGBA16F geometry/storage mismatch")
                iris26856BTextureForCleanup = carrier.textureId
            }
            val gpu = stacked.gpuLinearRgbSource
                ?: invalid("missing GPU Linear RGB source")
            requireParity(gpu.storage == GpuLinearRgbStorage.RGBA16F && gpu.samplesPerPixel == 4,
                "unexpected GPU RGB storage=${gpu.storage} samples=${gpu.samplesPerPixel}")
            requireParity(gpu.textureId != 0, "zero GPU RGB texture")
            clipZoneMaskTexture26836 = gpu.clipZoneMaskTextureId26836
            if (clipZoneMaskTexture26836 != 0) {
                requireParity(gpu.clipZoneMaskWidth26836 == size.x && gpu.clipZoneMaskHeight26836 == size.y,
                    "26836 clip-zone mask geometry=${gpu.clipZoneMaskWidth26836}x${gpu.clipZoneMaskHeight26836} expected=${size.x}x${size.y}")
            }
            requireParity(stacked.mergedFrameCount >= 1, "mergedFrameCount=${stacked.mergedFrameCount}")
            /* IRIS_26833_LONG_ZERO_RGB_SUPPORT_PARITY
             * RGB/chroma/noise support is NORMAL-only. SHADOW_LONG remains scheduled but publishes
             * only post-VGN scalar shadow luminance; HIGHLIGHT_SHORT keeps its separate radiometric owner. */
            requireParity(stacked.mergedFrameCount == expectedRgbMergedFrames26833,
                "26833 RGB role mismatch merged=${stacked.mergedFrameCount} " +
                    "expectedNormals=$expectedRgbMergedFrames26833 longLuma=$scheduledLongLumaFrames26833 " +
                    "night=${parameters.irisNightActive}")
            if (!parameters.irisNightActive && shortFrame != null) {
                /* IRIS_26670_SHORT_SEMANTIC_STATE_CONTRACT
                 * SCHEDULED/confidence-generated is not a claim of nonzero contribution. The
                 * exact successful-26660 Sabre owner decides local radiometric contribution and
                 * keeps NORMAL as motion/chroma/noise authority wherever SHORT is not trustworthy.
                 */
                requireParity(stacked.highlightShortAdmitted,
                    "26670 captured Motion SHORT was not scheduled into successful-26660 Sabre")
                requireParity(stacked.highlightShortRestoreMaskGenerated,
                    "26670 scheduled Motion SHORT did not generate successful-26660 confidence")
                requireParity(stacked.highlightShortExposureRatio.isFinite() &&
                        stacked.highlightShortExposureRatio > 1f,
                    "26670 invalid SHORT exposure ratio=${stacked.highlightShortExposureRatio}")
                /* IRIS_26856_B2X_SHORT_GUIDE_OWNER_SEPARATION
                 * This inherited 26670 flag exclusively means the historical
                 * A/Sabre 2x guide was generated. B-only creates and consumes
                 * an independent physical SHORT scalar guide inside its own
                 * RAWR true2x tiles. A B-only shot must not require A's guide;
                 * A and A+B retain their exact 26670 parity check.
                 */
                val expectedA2xShortGuide26856 = sabreSuperResEnabled &&
                    experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855
                requireParity(
                    stacked.highlightShortAppliedToTrue2x == expectedA2xShortGuide26856,
                    "26670 A true2x SHORT guide mismatch applied=${stacked.highlightShortAppliedToTrue2x} " +
                        "aSrExpected=$expectedA2xShortGuide26856 mode=$experiment26856",
                )
                PLog.i(TAG, "IRIS_26670_SHORT_BRIDGE_SCHEDULE_STATE captured=true scheduled=true " +
                    "confidenceFieldGenerated=true contributionNotClaimedHere=true " +
                    "exposureRatio=${stacked.highlightShortExposureRatio} " +
                    "mergedFrameCount=${stacked.mergedFrameCount} normalBodyOwner=true " +
                    "shortTemporalExcluded=true dngShortExcluded=true srShortDetailExcluded=true " +
                    "radiometricOwner=IRIS_26651_NORMAL_MASTER_SHORT_FUSION")
            } else {
                requireParity(!stacked.highlightShortAdmitted,
                    "26670 SHORT auxiliary unexpectedly active without Motion capture-plan ownership")
            }
            val correlation = stacked.mgcDenoiseCorrelation
            val readNoise = stacked.mgcDenoiseReadNoise
            val shotNoise = stacked.mgcDenoiseShotNoise
            val strength = stacked.mgcSpatialStrengthMap
            val referenceSnr = stacked.mgcReferenceSnr
            val tuningSnr = stacked.mgcDenoiseTuningSnr
            val sabreNoiseScale = stacked.mgcSabreNoiseModelScale
            requireParity(correlation == null && readNoise == null && shotNoise == null,
                "Sabre unexpectedly leaked Spatial-only correlation/noise coefficients")
            requireParity(
                strength != null &&
                    strength.width == (size.x + 3) / 4 &&
                    strength.height == (size.y + 3) / 4 &&
                    strength.q8.size == strength.width * strength.height &&
                    strength.q8.all { (it.toInt() and 0xffff) in 192..256 },
                "26634 Sabre local residual-noise support missing/malformed",
            )
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
            /* IRIS_26758_DIRECT_CFA_ZOOM_GEOMETRY
             * Direct-CFA detail never owns FOV/crop. Native Sabre stays at reconstructionZoom=1
             * and the existing render residual remains the exact physical-lens-relative request.
             */
            requireParity(kotlin.math.abs(parameters.motionV2ReconstructionZoom - 1f) < 1.0e-5f &&
                    kotlin.math.abs(parameters.motionV2RenderResidualZoom - localOutputZoom) < 1.0e-5f &&
                    parameters.motionV2SuperResOutputScale == sabreSuperResOutputScale &&
                    !parameters.motionV2HighZoomRgbPrepared && !parameters.motionV2HighZoomRgbApplied,
                "26758 direct-CFA/Sabre zoom geometry contract drifted")
            requireParity(lsc == null || stacked.lensShadingCorrectionApplied,
                "LSC supplied but MGC output did not apply it")

            GLES30.glFinish()
            gpu.stackCompletionTimeline?.releasePending()
            /* IRIS_26856_B_SEPARATE_RESULT_TRANSPORT
             * No post-VGN A bytes can be consumed as B. B is completed on the
             * same GL thread while the separate AMaZE texture remains live.
             * GPU transport is preferred; exact B RGBA16F readback is a
             * transport-only fallback, not a reconstruction fallback. */
            if (iris26856BTextureForCleanup != 0) {
                val sharedB = MotionV2SharedRgba16fCarrier.tryCreate(size.x, size.y)
                if (sharedB != null && sharedB.copyFromCurrentGlTexture(iris26856BTextureForCleanup)) {
                    iris26856BSharedForCleanup = sharedB
                    PLog.i(TAG, "IRIS_26856_B_CARRIER_HANDOFF source=RAWR_LAB_FCC_SHORT " +
                        "storage=shared_rgba16f independentOfA=true")
                } else {
                    runCatching { sharedB?.close() }
                    iris26856BBufferForCleanup = readRgba16f(iris26856BTextureForCleanup, size.x, size.y)
                    requireParity(iris26856BBufferForCleanup?.capacity()?.toLong() ==
                        size.x.toLong() * size.y * 8L, "26856 B CPU RGBA16F transport mismatch")
                    PLog.i(TAG, "IRIS_26856_B_CARRIER_HANDOFF source=RAWR_LAB_FCC_SHORT " +
                        "storage=direct_rgba16f independentOfA=true")
                }
                GLES30.glDeleteTextures(1, intArrayOf(iris26856BTextureForCleanup), 0)
                iris26856BTextureForCleanup = 0
                checkGl("26856 release B-only AMaZE GPU carrier")
            }
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
            /* IRIS_26639_NO_SUPPORT_DERIVED_GLOBAL_LUMA
             * noiseEquivalentSupport is NORMAL RGB diagnostic/merge evidence, not captured-frame count and not
             * an image-wide noise authority. 26638 proved that a bright 13-NORMAL capture can report
             * support ~= 1 and falsely drive the completed linear carrier to 0.35 luma smoothing.
             * Automatic luma therefore returns to zero: only the explicit luma control may request
             * full-resolution residual luma cleanup. ISO, shutter and exposure are not substitutes.
             * Sabre reconstruction/rejection, the 26634 local support field and chroma cleanup remain
             * unchanged. */
            val automaticLumaScale26639 = 0.0f
            /* IRIS_26545_SHARED_RESIDUAL_DENOISE_CONTROLS
             * The reconstruction owns temporal noise reduction. These two user controls act only
             * on the completed linear-RGB carrier, before PostPipeline/tone/UHDR. They never alter
             * capture exposure, frame admission, Spatial merge math, Sabre rejection, or Resolve.
             * Luma uses a new preference key and defaults to zero to preserve the proven 26544
             * zero-luma behavior until the user deliberately opts in. Chroma keeps its prior value.
             */
            val lumaScale = maxOf(requestedLumaScale, automaticLumaScale26639).coerceIn(0f, 2f)
            val chromaScale = irisSettings.chromaDenoise.coerceIn(0f, 2f)
            /* IRIS_26729_ONE_PRIMARY_CHROMA_OWNER
             * VGN is the primary Motion chroma owner. The inherited MGC residual pass is subordinate:
             * Auto preserves 26728; Custom supplies exact per-lens five-level strengths. Night is
             * deliberately firewalled from Custom until its separate color ownership is audited. */
            val customResidualChroma = if (frozenResidualChromaCustom26762) {
                /* IRIS_26762_CUSTOM_BROAD_CHROMA_PRECEDENCE
                 * Manual levels remain the exact five-level authority; the restored broad Chroma
                 * Denoise control is the only permitted final scale. Adaptive never enters Custom. */
                irisSettings.residualChromaLevels.map { (it * chromaScale).coerceIn(0f, 5f) }.toFloatArray()
            } else {
                null
            }
            val customResidualChromaEnabled = customResidualChroma?.any { it > 0f } ?: false
            /* IRIS_26762_ADAPTIVE_SNR_CHROMA_USER_AUTHORITY
             * The measured RAW/Sabre noise model still derives the automatic five-level recipe.
             * The new per-lens slider is a direct 0.5..2.0 multiplier over that Auto recipe; the
             * restored broad Chroma Denoise control remains a separate final overall scale.
             * Custom Exact bypasses the Adaptive multiplier completely. */
            val automaticResidualChromaScale26762 = if (!parameters.irisNightActive && customResidualChroma == null) {
                (adaptiveSnrChroma26762 * chromaScale).coerceIn(0f, 4f)
            } else {
                chromaScale
            }
            val residualChromaEnabled = customResidualChromaEnabled ||
                (customResidualChroma == null && automaticResidualChromaScale26762 > 0f)
            val denoisePass = MgcFullResolutionDenoise.Pass.SABRE_DEFAULT
            /* IRIS_26853_MOTION_MERGE_NATIVE_DENOISE_OWNER
             * 26852 changed Motion temporal statistics to CFA-first reconstruction. The legacy
             * bjzhou/MGC RGB->YUV residual pass was calibrated for the old completed Sabre RGB
             * carrier, so Motion now retires it rather than stacking a second noise owner. Night
             * remains byte-semantic on its inherited path. User luma/chroma values are retained
             * as settings but do not modify Motion reconstruction in this build. */
            val motionMergeNativeDenoise26853 = !parameters.irisNightActive &&
                experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850
            val runFullResolutionDenoise = !motionMergeNativeDenoise26853 &&
                irisSettings.noiseReductionEnabled && (lumaScale > 0f || residualChromaEnabled)
            if (motionMergeNativeDenoise26853) {
                PLog.i(
                    TAG,
                    "IRIS_26853_MOTION_MERGE_NATIVE_DENOISE_OWNER legacyMgcResidual=false " +
                        "cfaTemporal=true localMoments=true samePhase=true requestedLuma=$lumaScale " +
                        "requestedChroma=$chromaScale nightUnaffected=true",
                )
            }
            if (!parameters.irisNightActive) {
                PLog.i("MotionTrace", "IRIS_26762_RESIDUAL_CHROMA_CONTROL mode=${if (customResidualChroma != null) "CUSTOM_EXACT" else "AUTO_ADAPTIVE"} levels=${customResidualChroma?.contentToString() ?: "AUTO"} broadScale=$chromaScale adaptiveMultiplier=$adaptiveSnrChroma26762 referenceSnr=$referenceSnr outputTuningSnr=$tuningSnr appliedAutoScale=$automaticResidualChromaScale26762 bypass=${customResidualChroma != null && !customResidualChromaEnabled}")
            }
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
            /* IRIS_26826_SHARED_RGBA16F_PRIMARY
             * Standard-Bayer Motion first tries same-format HardwareBuffer storage. Sabre/VGN
             * pixels are copied GPU->GPU, then the exact existing CPU denoiser edits the mapped
             * RGBA16F bytes in place. Any allocation/import/map failure falls back immediately to
             * the byte-identical 26825 glReadPixels direct-buffer route. */
            var denoiseBuffer: ByteBuffer
            if (!parameters.irisNightActive && parameters.cfaPattern in 0..3) {
                val shared = MotionV2SharedRgba16fCarrier.tryCreate(size.x, size.y)
                val mapped = if (shared != null && shared.copyFromCurrentGlTexture(resultTexture)) {
                    shared.lockCpu()
                } else null
                if (shared != null && mapped != null && mapped.capacity().toLong() == shared.expectedBytes()) {
                    iris26826SharedCarrierForCleanup = shared
                    denoiseBuffer = mapped
                    PLog.i(TAG, "IRIS_26826_SHARED_RGBA16F_PRIMARY producer=true cpuMapped=true bytes=${mapped.capacity()} fallback=false")
                } else {
                    runCatching { shared?.close() }
                    denoiseBuffer = readRgba16f(resultTexture, size.x, size.y)
                    halfBuffer = denoiseBuffer
                    PLog.w(TAG, "IRIS_26826_SHARED_RGBA16F_FALLBACK stage=producer_or_map owner=26825_readback")
                }
            } else {
                denoiseBuffer = readRgba16f(resultTexture, size.x, size.y)
                halfBuffer = denoiseBuffer
            }
            /* IRIS_26728_RESIDUAL_CHROMA_FLOOR_OWNER
             * Motion-only: alpha from the post-VGN RGBA16F carrier is temporary internal metadata
             * holding strict physically-supported pre-VGN chroma magnitude. Night never enters this
             * owner. The compact one-byte floor map is sqrt-coded to retain precision at low chroma. */
            // 26857: B-only native AMaZE output carries OPAQUE alpha, not A's
            // post-VGN chroma-floor metadata. Treating alpha=1 as VGN floor
            // selected ~100% of the B image (12-second device regression).
            // A and A+B still render A through the unchanged VGN floor owner;
            // A+B's independent B sidecar is never supplied to this owner.
            val iris26728ChromaFloor = if (!parameters.irisNightActive &&
                experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855) {
                captureIris26728ProtectedChromaFloor(denoiseBuffer, size.x, size.y)
            } else {
                null
            }
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
                    chromaStrengthScale = if (customResidualChroma != null) 0f else automaticResidualChromaScale26762,
                    customChromaStrength = customResidualChroma,
                ), "MGC $denoisePass pre-PostPipeline linear-RGB denoise rejected its noise state")
            }
            iris26535DenoiseMs = (System.nanoTime() - iris26535DenoiseStartNs) / 1_000_000L

            /* IRIS_26568_FUSED_TRUE2X_RENDER_HANDOFF
             * Normal GPU operation applies the 26572 Sabre/VGN-guided true-detail luminance owner
             * while direct-CFA/phase/guide evidence is resident. CPU fallback mirrors the exact same
             * cross-frame-temporal, zero-chroma-transfer 2x2 luminance structure contract in the bounded file builder.
             */
            if(parameters.motionV2SuperResOutputEnabled &&
                experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855) {
                if(stacked.true2xBackend=="GPU") {
                    val fused=checkNotNull(stacked.true2xRenderRgbPath)
                    resultTrue2xRenderRgbPath=fused; true2xRenderRgbPathForCleanup=fused; iris26564True2xRenderPrepMs=0L
                    if(produceNormalStackedDng)resultTrue2xLinearRawPath=checkNotNull(stacked.true2xLinearRgbPath)
                    val lumaOwner="DIRECT_CFA_TEMPORAL_ADAPTIVE"
                    PLog.i(TAG,"IRIS_26758_TRUE_DETAIL_RENDER_FUSED backend=${stacked.true2xBackend} size=${stacked.true2xWidth}x${stacked.true2xHeight} dngRawPreserved=${resultTrue2xLinearRawPath!=null} sabreRgbChromaOwner=true highResLumaOwner=$lumaOwner directChromaOwner=false prepMs=0")
                    PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26752_SR_PROOF_HANDOFF details=backend=${stacked.true2xBackend} statsValidatedByStacker=true fusedCarrier=true")
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
            if (iris26728ChromaFloor != null) {
                applyIris26728ProtectedChromaFloor(
                    denoiseBuffer, size.x, size.y, iris26728ChromaFloor, runFullResolutionDenoise,
                )
            } else {
                forceOpaqueHalfAlpha(denoiseBuffer, size.x, size.y)
            }
            /* IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER
             * Claude math/domain/stage are unchanged from 26836. 26837 changes only execution:
             * immutable texture storage plus the already-proven GLES3 framebuffer fragment path,
             * so final chroma no longer depends on compute image-store support. */
            if (!parameters.irisNightActive && clipZoneMaskTexture26836 != 0) {
                val calculationWb26836 = calculationWhiteBalance26836(wb)
                applyIris26837FinalClipZoneChroma(
                    denoiseBuffer, size.x, size.y, clipZoneMaskTexture26836,
                    calculationWb26836, edgeFalseColor26778,
                )
                if (resultTrue2xRenderRgbPath != null && stacked.true2xWidth > 0 && stacked.true2xHeight > 0) {
                    val maskR16f26836 = readR16f26836(clipZoneMaskTexture26836, size.x, size.y)
                    try {
                        requireParity(
                            com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative.applyFinalNativeClipZoneChromaGuide26836(
                                resultTrue2xRenderRgbPath, stacked.true2xWidth, stacked.true2xHeight,
                                denoiseBuffer, size.x, size.y, maskR16f26836, calculationWb26836,
                                edgeFalseColor26778.clipZoneYFloor,
                            ),
                            "26836 true2x bilinear-mask final chroma handoff failed",
                        )
                        PLog.i(TAG, "IRIS_26836_SR_CLIP_ZONE_CHROMA maskUpsample=BILINEAR nativeFinalChromaOwner=true true2xLumaPreserved=true dngUntouched=true")
                    } finally {
                        LargeDirectBuffer.free(maskR16f26836)
                    }
                }
                GLES30.glDeleteTextures(1, intArrayOf(clipZoneMaskTexture26836), 0)
                clipZoneMaskTexture26836 = 0
                checkGl("delete 26836 final clip-zone mask")
            } else if (clipZoneMaskTexture26836 != 0) {
                GLES30.glDeleteTextures(1, intArrayOf(clipZoneMaskTexture26836), 0)
                clipZoneMaskTexture26836 = 0
            }
            /* IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER
             * Standard-Bayer Motion and Night keep the already-accepted denoised RGBA16F pixels
             * as the cross-context carrier. Critical reconstruction/shader arithmetic remains
             * highp float; only image storage/transport stays half-float. Special-CFA fallback
             * retains the inherited RGBA32F transport because its carrier semantics differ.
             */
            val directRgba16fCarrier = parameters.irisNightActive ||
                parameters.cfaPattern in 0..3
            var output: ByteBuffer? = null
            var outputSharedCarrier: MotionV2SharedRgba16fCarrier? = null
            val outputCarrierFormat: Int
            if (directRgba16fCarrier) {
                val shared = iris26826SharedCarrierForCleanup
                if (shared != null) {
                    requireParity(shared.unlockCpu(), "26826 shared RGBA16F CPU unlock failed")
                    outputSharedCarrier = shared
                    iris26826SharedCarrierForCleanup = null // ownership transfers through Result
                    outputCarrierFormat = MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA16F
                    PLog.i(TAG, "IRIS_26826_SHARED_RGBA16F_HANDOFF bytes=${shared.expectedBytes()} owner=result fallback=false")
                } else {
                    output = denoiseBuffer
                    halfBuffer = null // ownership transfers through Result to PostPipeline
                    outputCarrierFormat = MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA16F
                    PLog.i(TAG, "IRIS_26726_UNIVERSAL_RGBA16F_CARRIER bytes=${output!!.capacity()} " +
                        "bytesPerPixel=8 source=denoisedRGBA16F transfer=RGBA16F deviceIndependent=true")
                }
            } else {
                output = convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)
                outputCarrierFormat = MotionV2Merger.Result.LINEAR_RGB_CARRIER_RGBA32F
                PLog.i(TAG, "IRIS_26726_SPECIAL_CFA_RGBA32F_FALLBACK bytes=${output!!.capacity()} " +
                    "source=denoisedRGBA16F specialCfa=true")
            }
            GLES30.glDeleteTextures(1, intArrayOf(resultTexture), 0)
            resultTexture = 0
            checkGl("delete exported MGC RGB")

            PLog.i(TAG, "IRIS_26545_DENOISE_NOISE_AUTHORITY " +
                "stage=PRE_POSTPIPELINE_LINEAR_RGB master=${irisSettings.noiseReductionEnabled} " +
                "luma=$lumaScale chroma=$chromaScale automaticLuma26639=$automaticLumaScale26639 " +
                "noiseEquivalentSupport=$noiseEquivalentSupport executed=$runFullResolutionDenoise " +
                "pass=$denoisePass motionNoiseOwner=${if (motionMergeNativeDenoise26853) "IRIS_26853_CFA_MERGE" else "LEGACY_MGC_RESIDUAL"} " +
                "noiseSource=$noiseAuthority mgcBase=${mgcBase.timestamp} " +
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
            parameters.motionV2ShortRadianceAuthorityMask = null
            parameters.motionV2ShortRadianceAuthorityWidth = 0
            parameters.motionV2ShortRadianceAuthorityHeight = 0
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
                "residualDenoise=${if (motionMergeNativeDenoise26853) "BYPASSED_IRIS_26853_MERGE_NATIVE" else denoisePass} carrier=RESOLVE_SABRE_LINEAR_RGB " +
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
                "crossContext=${if (outputSharedCarrier != null) "rgba16f_shared_26826" else if (directRgba16fCarrier) "rgba16f_cpu_26726_universal" else "rgba32f_cpu_special_cfa_fallback"} alphaSupport=disabled")

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
                result.linearRgbCarrierFormat = outputCarrierFormat
                result.sharedRgba16fCarrier = outputSharedCarrier
                outputSharedCarrier = null // Result owns it now
                result.iris26856RawrBSharedCarrier = iris26856BSharedForCleanup
                result.iris26856RawrBBuffer16f = iris26856BBufferForCleanup
                result.iris26856BTrue2xRgbPath = stacked.iris26856BTrue2xRgbPath
                result.iris26856BTrue2xWidth = stacked.iris26856BTrue2xWidth
                result.iris26856BTrue2xHeight = stacked.iris26856BTrue2xHeight
                iris26856BTrue2xOutputHandedOff = result.iris26856BTrue2xRgbPath != null
                iris26856BHighZoomDetailHandedOff =
                    parameters.iris26856BHighZoomDetail != null
                iris26856BSharedForCleanup = null // independent B Result ownership
                iris26856BBufferForCleanup = null
                /* IRIS_26726_CARRIER_OWNERSHIP: direct RGBA16F ownership was transferred above;
                 * special-CFA RGBA32F remains independently allocated and halfBuffer is released. */
                true2xOutputHandedOff = resultTrue2xRenderRgbPath != null &&
                    (!produceNormalStackedDng || resultTrue2xLinearRawPath != null)
                highZoomDetailHandedOff = !highZoomDetailEnabled || parameters.motionV2HighZoomRgbPrepared || parameters.motionV2HighZoomDetailPath != null
                highZoomRgbHandedOff = !parameters.motionV2HighZoomRgbPrepared || parameters.motionV2HighZoomRgbPath != null
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
            if (clipZoneMaskTexture26836 != 0) runCatching {
                GLES30.glDeleteTextures(1, intArrayOf(clipZoneMaskTexture26836), 0)
            }
            LargeDirectBuffer.free(halfBuffer)
            if (iris26856BTextureForCleanup != 0) runCatching {
                GLES30.glDeleteTextures(1, intArrayOf(iris26856BTextureForCleanup), 0)
            }
            iris26856BTextureForCleanup = 0
            runCatching { iris26856BSharedForCleanup?.close() }
            LargeDirectBuffer.free(iris26856BBufferForCleanup)
            iris26856BSharedForCleanup = null
            iris26856BBufferForCleanup = null
            runCatching { iris26826SharedCarrierForCleanup?.close() }
            iris26826SharedCarrierForCleanup = null
            if (!iris26856BTrue2xOutputHandedOff) {
                iris26856BTrue2xPathForCleanup?.let { path -> runCatching { File(path).delete() } }
            }
            if (!true2xOutputHandedOff) {
                true2xLinearRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xNativeVgnGuidePathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xPhaseSupportPathForCleanup?.let { path -> runCatching { File(path).delete() } }
                true2xRenderRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
            }
            if (!highZoomDetailHandedOff) {
                highZoomDetailPathForCleanup?.let { path -> runCatching { File(path).delete() } }
            }
            /* Bridge and Hdrx own distinct lifetimes; historical A's
             * highZoomDetailHandedOff cannot be used to decide B cleanup. */
            if (!iris26856BHighZoomDetailHandedOff) {
                parameters.iris26856BHighZoomDetail?.path?.let { path ->
                    runCatching { File(path).delete() }
                }
            }
            if (!highZoomRgbHandedOff) {
                highZoomRgbPathForCleanup?.let { path -> runCatching { File(path).delete() } }
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

    /* IRIS_26856_AB_RETAIN_SINGLE_IMMUTABLE_CAPTURE_COPY
     * Normally a SafeImage closes the original ImageFrame on completion.
     * Dual mode retains the SAME already-copied RAW bytes until BOTH branches
     * complete; existing bridge.finally alone then closes original buffers.
     * This must not read the ZSL ring again or create duplicate RAW captures.
     * Inactive until B/A-B no longer fail closed. */
    private fun safeImage(
        frame: ImageFrame, size: Point, retainForDual26856: Boolean = false,
    ): SafeImage {
        val closeRawOwner: (() -> Unit)? =
            if (retainForDual26856) null else ({ frame.close() })
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
                closeAction = closeRawOwner,
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
            closeAction = closeRawOwner,
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

    private data class Iris26728ProtectedChromaFloor(
        val pixelIndices: IntArray,
        val sqrtFloorQ8: ByteArray,
        val protectedPixels: Int,
    )

    private fun cameraChromaMagnitude26728(r: Float, g: Float, b: Float): Float {
        val y = 0.25f * r + 0.50f * g + 0.25f * b
        val cr = r - y
        val cg = g - y
        val cb = b - y
        return kotlin.math.sqrt(cr * cr + cg * cg + cb * cb)
    }

    /* IRIS_26828_NATIVE_PROTECTED_CHROMA_PRIMARY
     * The exact 26728 capture math runs over the mapped RGBA16F carrier in JNI. Any native setup
     * failure falls back to the complete 26827 Kotlin implementation below. */
    private fun captureIris26728ProtectedChromaFloor(
        buffer: ByteBuffer,
        width: Int,
        height: Int,
    ): Iris26728ProtectedChromaFloor {
        val startNs = System.nanoTime()
        try {
            val native = MotionV2ProtectedChromaNative.capture(buffer, width, height)
            val protectedPixels = native.pixelIndices.size
            requireParity(native.floorCodes.size == protectedPixels,
                "26828 native protected-chroma capture array mismatch")
            val denominator = maxOf(protectedPixels, 1).toDouble()
            PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_PRE_VGN protectedPixels=$protectedPixels " +
                "meanMagnitude=${native.preVgnSum / denominator} source=physicalHdr26605 hueOwner=VGN_CLEANED")
            PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_POST_VGN protectedPixels=$protectedPixels " +
                "meanMagnitude=${native.postVgnSum / denominator} floorCarrier=RGBA16F_ALPHA directionOwner=VGN_CLEANED")
            PLog.i(TAG, "IRIS_26828_NATIVE_PROTECTED_CHROMA_CAPTURE entries=$protectedPixels " +
                "fullPixels=${width * height} elapsedMs=${(System.nanoTime() - startNs) / 1_000_000.0} fallback=false")
            buffer.position(0)
            return Iris26728ProtectedChromaFloor(native.pixelIndices, native.floorCodes, protectedPixels)
        } catch (error: Throwable) {
            PLog.w(TAG, "IRIS_26828_NATIVE_PROTECTED_CHROMA_CAPTURE_FALLBACK owner=26827_kotlin", error)
            return captureIris26728ProtectedChromaFloor26827Fallback(buffer, width, height)
        }
    }

    private fun captureIris26728ProtectedChromaFloor26827Fallback(
        buffer: ByteBuffer,
        width: Int,
        height: Int,
    ): Iris26728ProtectedChromaFloor {
        val startNs = System.nanoTime()
        val shorts = buffer.duplicate().order(ByteOrder.nativeOrder()).apply { position(0) }.asShortBuffer()
        val pixels = width * height
        requireParity(shorts.capacity() >= pixels * 4, "26728 protected chroma input buffer is short")
        /* IRIS_26827_SPARSE_PROTECTED_CHROMA_BOOKKEEPING
         * Only nonzero pre-VGN floors participate in the inherited post-denoise classifier. Keep
         * their ascending pixel order and exact Q8 codes, rather than allocating/scanning a full
         * frame byte map again after denoise. RGB math is unchanged. */
        var capacity = minOf(maxOf(1, 16 * 1024), maxOf(1, pixels))
        var pixelIndices = IntArray(capacity)
        var floorCodes = ByteArray(capacity)
        var protectedPixels = 0
        var preVgnSum = 0.0
        var postVgnSum = 0.0
        for (pixel in 0 until pixels) {
            val base = pixel * 4
            val preVgnRaw = Half.toFloat(shorts.get(base + 3))
            if (!preVgnRaw.isFinite()) continue
            val preVgnMagnitude = preVgnRaw.coerceIn(0f, 1f)
            if (preVgnMagnitude <= 0f) continue
            val rawR = Half.toFloat(shorts.get(base))
            val rawG = Half.toFloat(shorts.get(base + 1))
            val rawB = Half.toFloat(shorts.get(base + 2))
            if (!rawR.isFinite() || !rawG.isFinite() || !rawB.isFinite()) continue
            val r = rawR.coerceAtLeast(0f)
            val g = rawG.coerceAtLeast(0f)
            val b = rawB.coerceAtLeast(0f)
            val postVgnMagnitude = cameraChromaMagnitude26728(r, g, b)
            val protectedFloor = minOf(preVgnMagnitude, postVgnMagnitude).coerceIn(0f, 1f)
            if (protectedFloor <= 0f) continue
            if (protectedPixels == capacity) {
                val next = minOf(pixels, maxOf(capacity + 1, capacity * 2))
                pixelIndices = pixelIndices.copyOf(next)
                floorCodes = floorCodes.copyOf(next)
                capacity = next
            }
            val encoded = (kotlin.math.sqrt(protectedFloor) * 255f).toInt().coerceIn(1, 255)
            pixelIndices[protectedPixels] = pixel
            floorCodes[protectedPixels] = encoded.toByte()
            protectedPixels += 1
            preVgnSum += preVgnMagnitude.toDouble()
            postVgnSum += postVgnMagnitude.toDouble()
        }
        val denominator = maxOf(protectedPixels, 1).toDouble()
        PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_PRE_VGN protectedPixels=$protectedPixels " +
            "meanMagnitude=${preVgnSum / denominator} source=physicalHdr26605 hueOwner=VGN_CLEANED")
        PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_POST_VGN protectedPixels=$protectedPixels " +
            "meanMagnitude=${postVgnSum / denominator} floorCarrier=RGBA16F_ALPHA directionOwner=VGN_CLEANED")
        PLog.i(TAG, "IRIS_26827_SPARSE_PROTECTED_CHROMA_CAPTURE entries=$protectedPixels " +
            "fullPixels=$pixels elapsedMs=${(System.nanoTime() - startNs) / 1_000_000.0}")
        buffer.position(0)
        return Iris26728ProtectedChromaFloor(
            pixelIndices.copyOf(protectedPixels), floorCodes.copyOf(protectedPixels), protectedPixels)
    }

    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY
     * 26794 proved that absolute pre-presentation luma and self-surviving chroma are invalid
     * permissions for the visually-bright false-color class. 26795 keeps the successful 26793
     * Sabre/VGN/denoise owners intact and changes only the post-denoise protected-chroma decision.
     * A sparse histogram defines the current frame's upper luminance tail. Protected pixels on an
     * upper-tail/high-gradient boundary may restore (or keep) chroma only when same-hue evidence
     * extends away from the boundary along the dominant luminance-gradient normal. The candidate
     * pixel's own chroma is never support. Unsupported residual chroma is reduced toward the
     * externally-supported magnitude while preserving the pixel's denoised luminance. */
    private fun smoothstep26795(edge0: Float, edge1: Float, value: Float): Float {
        if (edge1 <= edge0) return if (value >= edge1) 1f else 0f
        val t = ((value - edge0) / (edge1 - edge0)).coerceIn(0f, 1f)
        return t * t * (3f - 2f * t)
    }


    private fun percentileLuma26795(histogram: IntArray, total: Int, quantile: Float): Float {
        if (total <= 0) return 0f
        val wanted = kotlin.math.ceil(total.toDouble() * quantile.coerceIn(0f, 1f)).toInt().coerceAtLeast(1)
        var cumulative = 0
        for (bin in histogram.indices) {
            cumulative += histogram[bin]
            if (cumulative >= wanted) return bin.toFloat() / (histogram.size - 1).toFloat()
        }
        return 1f
    }

    /* IRIS_26828_NATIVE_PROTECTED_CHROMA_PRIMARY
     * JNI preserves the exact 26795 classifier and no-raise semantics. Every argument, sparse
     * index, and JNI result carrier is acquired before the first RGB mutation; native failure can
     * therefore only occur pre-write, so the inherited 26827 Kotlin fallback is always safe. */
    private fun applyIris26728ProtectedChromaFloor(
        buffer: ByteBuffer,
        width: Int,
        height: Int,
        state: Iris26728ProtectedChromaFloor,
        residualDenoiseExecuted: Boolean,
    ) {
        val startNs = System.nanoTime()
        try {
            requireParity(state.pixelIndices.size == state.protectedPixels &&
                state.sqrtFloorQ8.size == state.protectedPixels,
                "26828 native protected-chroma state mismatch")
            val m = MotionV2ProtectedChromaNative.apply(
                buffer, width, height, state.pixelIndices, state.sqrtFloorQ8)
            val beforeSum=m[0]; val afterSum=m[1]; val measuredPixels=m[2].toInt()
            val floorCandidatePixels=m[3].toInt(); val legacyWouldRaisePixels=m[4].toInt()
            val raisedPixels=m[5].toInt(); val floorBlockedPixels=m[6].toInt()
            val residualReducedPixels=m[7].toInt(); val directionLostPixels=m[8].toInt()
            val sceneRiskCandidates=m[9].toInt(); val externallySupportedRiskCandidates=m[10].toInt()
            val suppressedFloorMagnitudeSum=m[11]; val suppressedResidualMagnitudeSum=m[12]
            val maxSuppressedFloorMagnitude=m[13]; val maxSuppressedResidualMagnitude=m[14]
            val histogramSamples=m[15].toInt(); val sceneP90=m[16]; val sceneP98=m[17]; val sceneP995=m[18]
            val upperTailStart=m[19]; val upperTailEnd=m[20]
            val denominator=maxOf(measuredPixels,1).toDouble()
            val floorDenominator=maxOf(legacyWouldRaisePixels,1).toDouble()
            val residualDenominator=maxOf(residualReducedPixels,1).toDouble()
            PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_POST_RESIDUAL_DENOISE protectedPixels=${state.protectedPixels} " +
                "measuredPixels=$measuredPixels residualDenoiseExecuted=$residualDenoiseExecuted " +
                "meanBeforeFloor=${beforeSum / denominator} meanAfterFloor=${afterSum / denominator} " +
                "raisedPixels=$raisedPixels directionLostPixels=$directionLostPixels hueOwner=DENOISED_VGN_DIRECTION")
            PLog.i(TAG, "IRIS_26828_NATIVE_PROTECTED_CHROMA_APPLY entries=${state.protectedPixels} " +
                "fullPixels=${width * height} elapsedMs=${(System.nanoTime() - startNs) / 1_000_000.0} " +
                "rgbClassifierOrder=ASCENDING_ORIGINAL_PROTECTED alphaNormalizedOnce=true fallback=false")
            PLog.i(TAG, "IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA histogramSamples=$histogramSamples " +
                "sceneP90=$sceneP90 sceneP98=$sceneP98 sceneP995=$sceneP995 upperTailStart=$upperTailStart upperTailEnd=$upperTailEnd " +
                "floorCandidatePixels=$floorCandidatePixels legacyWouldRaisePixels=$legacyWouldRaisePixels allowedRaisedPixels=$raisedPixels " +
                "sceneRiskCandidates=$sceneRiskCandidates externallySupportedRiskCandidates=$externallySupportedRiskCandidates " +
                "floorBlockedPixels=$floorBlockedPixels residualReducedPixels=$residualReducedPixels " +
                "meanSuppressedFloorMagnitude=${suppressedFloorMagnitudeSum / floorDenominator} maxSuppressedFloorMagnitude=$maxSuppressedFloorMagnitude " +
                "meanSuppressedResidualMagnitude=${suppressedResidualMagnitudeSum / residualDenominator} maxSuppressedResidualMagnitude=$maxSuppressedResidualMagnitude " +
                "grid=64x48 origin=GL_BOTTOM_LEFT")
            buffer.position(0)
            return
        } catch (error: Throwable) {
            PLog.w(TAG, "IRIS_26828_NATIVE_PROTECTED_CHROMA_APPLY_FALLBACK owner=26827_kotlin", error)
            applyIris26728ProtectedChromaFloor26827Fallback(
                buffer, width, height, state, residualDenoiseExecuted)
        }
    }

    private fun applyIris26728ProtectedChromaFloor26827Fallback(
        buffer: ByteBuffer,
        width: Int,
        height: Int,
        state: Iris26728ProtectedChromaFloor,
        residualDenoiseExecuted: Boolean,
    ) {
        val shorts = buffer.duplicate().order(ByteOrder.nativeOrder()).apply { position(0) }.asShortBuffer()
        val pixels = width * height
        requireParity(shorts.capacity() >= pixels * 4 &&
            state.sqrtFloorQ8.size == state.protectedPixels &&
            state.pixelIndices.size == state.protectedPixels,
            "26728 protected chroma floor buffer mismatch")
        val iris26827SparseApplyStartNs = System.nanoTime()

        /* Scene-relative authority. Keep this deterministic and cheap: a regular <=~50k-sample
         * grid reads the untouched post-denoise RGB carrier. No presentation gain, tone curve,
         * toggle, or semantic object knowledge is consumed here. */
        val histogram = IntArray(256)
        val sampleStepX = maxOf(width / 256, 1)
        val sampleStepY = maxOf(height / 192, 1)
        var histogramSamples = 0
        var sampleY = 0
        while (sampleY < height) {
            var sampleX = 0
            while (sampleX < width) {
                val base = (sampleY * width + sampleX) * 4
                val rr = Half.toFloat(shorts.get(base))
                val gg = Half.toFloat(shorts.get(base + 1))
                val bb = Half.toFloat(shorts.get(base + 2))
                if (rr.isFinite() && gg.isFinite() && bb.isFinite()) {
                    val luma = (0.25f * rr.coerceAtLeast(0f) +
                        0.50f * gg.coerceAtLeast(0f) +
                        0.25f * bb.coerceAtLeast(0f)).coerceIn(0f, 1f)
                    val bin = (luma * 255f).toInt().coerceIn(0, 255)
                    histogram[bin] += 1
                    histogramSamples += 1
                }
                sampleX += sampleStepX
            }
            sampleY += sampleStepY
        }
        val sceneP90 = percentileLuma26795(histogram, histogramSamples, 0.90f)
        val sceneP98 = percentileLuma26795(histogram, histogramSamples, 0.98f)
        val sceneP995 = percentileLuma26795(histogram, histogramSamples, 0.995f)
        val upperTailStart = maxOf(sceneP90, 0.01f)
        val upperTailEnd = maxOf(sceneP98, upperTailStart + 0.02f).coerceAtMost(1f)

        // Six 64x48 masks = 2304 bytes total, still tiny but 4x the cell resolution of 26794.
        val gridWidth = 64
        val gridHeight = 48
        /* IRIS_26816_RETIRE_26795_DIAGNOSTIC_MAPS
         * Spatial bitmaps were telemetry-only; grid dimensions remain for compact summary context. */

        var beforeSum = 0.0
        var afterSum = 0.0
        var measuredPixels = 0
        var floorCandidatePixels = 0
        var legacyWouldRaisePixels = 0
        var raisedPixels = 0
        var floorBlockedPixels = 0
        var residualReducedPixels = 0
        var directionLostPixels = 0
        var sceneRiskCandidates = 0
        var externallySupportedRiskCandidates = 0
        var suppressedFloorMagnitudeSum = 0.0
        var suppressedResidualMagnitudeSum = 0.0
        var maxSuppressedFloorMagnitude = 0f
        var maxSuppressedResidualMagnitude = 0f

        /* IRIS_26816_RETIRE_26795_TOP_RISK_BOOKKEEPING */

        /* First pass: classify from the untouched post-denoise carrier. state.sqrtFloorQ8 is reused
         * only after each pixel's original floor has been consumed; nonzero values become frozen
         * target magnitudes for the second pass. */
        for (entry in 0 until state.protectedPixels) {
            val pixel = state.pixelIndices[entry]
            val originalCode = state.sqrtFloorQ8[entry].toInt() and 0xFF
            if (originalCode == 0) continue
            val q = originalCode.toFloat() / 255f
            val floorMagnitude = q * q
            val base = pixel * 4
            val rawR = Half.toFloat(shorts.get(base))
            val rawG = Half.toFloat(shorts.get(base + 1))
            val rawB = Half.toFloat(shorts.get(base + 2))
            if (!rawR.isFinite() || !rawG.isFinite() || !rawB.isFinite()) {
                state.sqrtFloorQ8[entry] = 0
                continue
            }
            val r = rawR.coerceAtLeast(0f)
            val g = rawG.coerceAtLeast(0f)
            val b = rawB.coerceAtLeast(0f)
            val y = 0.25f * r + 0.50f * g + 0.25f * b
            val cr = r - y
            val cg = g - y
            val cb = b - y
            val currentMagnitude = kotlin.math.sqrt(cr * cr + cg * cg + cb * cb)
            beforeSum += currentMagnitude.toDouble()
            measuredPixels += 1

            val x = pixel % width
            val yy = pixel / width
            var legacyTarget = currentMagnitude
            var maximumMagnitude = Float.POSITIVE_INFINITY
            var dr = 0f
            var dg = 0f
            var db = 0f
            if (currentMagnitude > 1.0e-7f) {
                val inv = 1f / currentMagnitude
                dr = cr * inv
                dg = cg * inv
                db = cb * inv
                if (dr > 1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (1f - y) / dr)
                else if (dr < -1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (0f - y) / dr)
                if (dg > 1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (1f - y) / dg)
                else if (dg < -1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (0f - y) / dg)
                if (db > 1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (1f - y) / db)
                else if (db < -1.0e-7f) maximumMagnitude = minOf(maximumMagnitude, (0f - y) / db)
                legacyTarget = minOf(floorMagnitude, maximumMagnitude.coerceAtLeast(0f))
                if (legacyTarget > currentMagnitude + 1.0e-7f) {
                    floorCandidatePixels += 1
                    legacyWouldRaisePixels += 1
                } else {
                    legacyTarget = currentMagnitude
                }
            } else {
                directionLostPixels += 1
                state.sqrtFloorQ8[entry] = 0
                afterSum += currentMagnitude.toDouble()
                continue
            }

            var maxNeighborLuma = y
            var maxLumaDelta = 0f
            var leftLuma = y
            var rightLuma = y
            var upLuma = y
            var downLuma = y
            var leftProjection1 = 0f
            var leftProjection2 = 0f
            var rightProjection1 = 0f
            var rightProjection2 = 0f
            var upProjection1 = 0f
            var upProjection2 = 0f
            var downProjection1 = 0f
            var downProjection2 = 0f

            fun consumeNeighbor(np: Int, slot: Int) {
                val nbBase = np * 4
                val nRawR = Half.toFloat(shorts.get(nbBase))
                val nRawG = Half.toFloat(shorts.get(nbBase + 1))
                val nRawB = Half.toFloat(shorts.get(nbBase + 2))
                if (!nRawR.isFinite() || !nRawG.isFinite() || !nRawB.isFinite()) return
                val nrgbR = nRawR.coerceAtLeast(0f)
                val nrgbG = nRawG.coerceAtLeast(0f)
                val nrgbB = nRawB.coerceAtLeast(0f)
                val ny = 0.25f * nrgbR + 0.50f * nrgbG + 0.25f * nrgbB
                maxNeighborLuma = maxOf(maxNeighborLuma, ny)
                maxLumaDelta = maxOf(maxLumaDelta, kotlin.math.abs(ny - y))
                val nr = nrgbR - ny
                val ng = nrgbG - ny
                val nb = nrgbB - ny
                val projection = maxOf(nr * dr + ng * dg + nb * db, 0f)
                when (slot) {
                    0 -> { leftProjection1 = projection; leftLuma = ny }
                    1 -> leftProjection2 = projection
                    2 -> { rightProjection1 = projection; rightLuma = ny }
                    3 -> rightProjection2 = projection
                    4 -> { upProjection1 = projection; upLuma = ny }
                    5 -> upProjection2 = projection
                    6 -> { downProjection1 = projection; downLuma = ny }
                    7 -> downProjection2 = projection
                }
            }
            if (x > 0) consumeNeighbor(pixel - 1, 0)
            if (x > 1) consumeNeighbor(pixel - 2, 1)
            if (x + 1 < width) consumeNeighbor(pixel + 1, 2)
            if (x + 2 < width) consumeNeighbor(pixel + 2, 3)
            if (yy > 0) consumeNeighbor(pixel - width, 4)
            if (yy > 1) consumeNeighbor(pixel - 2 * width, 5)
            if (yy + 1 < height) consumeNeighbor(pixel + width, 6)
            if (yy + 2 < height) consumeNeighbor(pixel + 2 * width, 7)

            val horizontalGradient = kotlin.math.abs(rightLuma - leftLuma)
            val verticalGradient = kotlin.math.abs(downLuma - upLuma)
            fun sideDepth(p1: Float, p2: Float): Float = maxOf(minOf(p1, p2), 0.35f * p1)
            val externalMagnitude = if (horizontalGradient >= verticalGradient) {
                maxOf(sideDepth(leftProjection1, leftProjection2), sideDepth(rightProjection1, rightProjection2))
            } else {
                maxOf(sideDepth(upProjection1, upProjection2), sideDepth(downProjection1, downProjection2))
            }
            val supportReference = maxOf(floorMagnitude, currentMagnitude, 1.0e-7f)
            val externalSupportRatio = (externalMagnitude / supportReference).coerceIn(0f, 1f)
            val externalPermission = smoothstep26795(0.15f, 0.60f, externalSupportRatio)

            val localPeakLuma = maxOf(y, maxNeighborLuma)
            val relativeGradient = maxLumaDelta / maxOf(localPeakLuma, sceneP90, 0.02f)
            val upperTailScore = smoothstep26795(upperTailStart, upperTailEnd, localPeakLuma)
            val gradientScore = smoothstep26795(0.08f, 0.30f, relativeGradient)
            val sceneRisk = (upperTailScore * gradientScore).coerceIn(0f, 1f)
            val unsupported = 1f - externalPermission
            val correctionStrength = sceneRisk * unsupported

            if (sceneRisk >= 0.20f) {
                sceneRiskCandidates += 1
                if (externalPermission >= 0.50f) {
                    externallySupportedRiskCandidates += 1
                }
            }

            /* Unsupported bright-edge residuals are allowed to retain a small fraction of their
             * own magnitude to avoid a hard neutral seam. External same-hue depth may preserve more.
             * This is chroma-only; y is invariant. */
            val externallySupportedResidual = minOf(currentMagnitude,
                maxOf(externalMagnitude, currentMagnitude * 0.08f))
            val residualTarget = currentMagnitude +
                (externallySupportedResidual - currentMagnitude) * correctionStrength

            val floorPermission = (1f - correctionStrength).coerceIn(0f, 1f)
            var targetMagnitude = residualTarget
            if (legacyTarget > currentMagnitude + 1.0e-7f) {
                targetMagnitude = residualTarget +
                    (legacyTarget - residualTarget).coerceAtLeast(0f) * floorPermission
                if (targetMagnitude <= currentMagnitude + 1.0e-6f) {
                    floorBlockedPixels += 1
                }
                val suppressedFloor = (legacyTarget - maxOf(targetMagnitude, currentMagnitude)).coerceAtLeast(0f)
                if (suppressedFloor > 0f) {
                    suppressedFloorMagnitudeSum += suppressedFloor.toDouble()
                    maxSuppressedFloorMagnitude = maxOf(maxSuppressedFloorMagnitude, suppressedFloor)
                }
            }
            if (targetMagnitude + 1.0e-6f < currentMagnitude) {
                residualReducedPixels += 1
                val suppressedResidual = currentMagnitude - targetMagnitude
                suppressedResidualMagnitudeSum += suppressedResidual.toDouble()
                maxSuppressedResidualMagnitude = maxOf(maxSuppressedResidualMagnitude, suppressedResidual)
            }

            // IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER
            // The residual-denoise output is the chroma ceiling. Protected-chroma bookkeeping may
            // still reduce unsupported bright-edge chroma, but it may never restore/increase
            // chroma magnitude above the denoised result. Luma and hue direction remain unchanged.
            targetMagnitude = minOf(targetMagnitude, currentMagnitude)

            val riskForProof = sceneRisk * unsupported
            if (riskForProof >= 0.10f) {
            }

            if (targetMagnitude > currentMagnitude + 1.0e-6f) {
                val encodedTarget = (kotlin.math.sqrt(targetMagnitude.coerceIn(0f, 1f)) * 255f)
                    .toInt().coerceIn(1, 255)
                val encodedQ = encodedTarget.toFloat() / 255f
                val quantizedTarget = encodedQ * encodedQ
                if (quantizedTarget > currentMagnitude + 1.0e-7f) {
                    state.sqrtFloorQ8[entry] = encodedTarget.toByte()
                    targetMagnitude = quantizedTarget
                    raisedPixels += 1
                } else {
                    state.sqrtFloorQ8[entry] = 0
                    targetMagnitude = currentMagnitude
                }
            } else if (targetMagnitude + 1.0e-6f < currentMagnitude) {
                val encodedTarget = (kotlin.math.sqrt(targetMagnitude.coerceIn(0f, 1f)) * 255f)
                    .toInt().coerceIn(1, 255)
                val encodedQ = encodedTarget.toFloat() / 255f
                val quantizedTarget = encodedQ * encodedQ
                if (quantizedTarget + 1.0e-7f < currentMagnitude) {
                    state.sqrtFloorQ8[entry] = encodedTarget.toByte()
                    targetMagnitude = quantizedTarget
                } else {
                    state.sqrtFloorQ8[entry] = 0
                    targetMagnitude = currentMagnitude
                }
            } else {
                state.sqrtFloorQ8[entry] = 0
                targetMagnitude = currentMagnitude
            }
            afterSum += targetMagnitude.toDouble()
        }

        // Second pass: apply frozen up/down chroma targets; every classifier read above was untouched.
        for (entry in 0 until state.protectedPixels) {
            val pixel = state.pixelIndices[entry]
            val base = pixel * 4
            val code = state.sqrtFloorQ8[entry].toInt() and 0xFF
            if (code != 0) {
                val q = code.toFloat() / 255f
                val targetMagnitude = q * q
                val rawR = Half.toFloat(shorts.get(base))
                val rawG = Half.toFloat(shorts.get(base + 1))
                val rawB = Half.toFloat(shorts.get(base + 2))
                if (rawR.isFinite() && rawG.isFinite() && rawB.isFinite()) {
                    val r = rawR.coerceAtLeast(0f)
                    val g = rawG.coerceAtLeast(0f)
                    val b = rawB.coerceAtLeast(0f)
                    val y = 0.25f * r + 0.50f * g + 0.25f * b
                    var cr = r - y
                    var cg = g - y
                    var cb = b - y
                    val currentMagnitude = kotlin.math.sqrt(cr * cr + cg * cg + cb * cb)
                    if (currentMagnitude > 1.0e-7f && kotlin.math.abs(targetMagnitude - currentMagnitude) > 1.0e-7f) {
                        val scale = targetMagnitude / currentMagnitude
                        cr *= scale
                        cg *= scale
                        cb *= scale
                        shorts.put(base, Half.toHalf((y + cr).coerceIn(0f, 1f)))
                        shorts.put(base + 1, Half.toHalf((y + cg).coerceIn(0f, 1f)))
                        shorts.put(base + 2, Half.toHalf((y + cb).coerceIn(0f, 1f)))
                    }
                }
            }
        }
        // Alpha carried pre-VGN magnitude metadata; clear it exactly once after sparse RGB updates.
        for (pixel in 0 until pixels) shorts.put(pixel * 4 + 3, HALF_ONE)

        val denominator = maxOf(measuredPixels, 1).toDouble()
        val floorDenominator = maxOf(legacyWouldRaisePixels, 1).toDouble()
        val residualDenominator = maxOf(residualReducedPixels, 1).toDouble()
        PLog.i(TAG, "IRIS_26728_PROTECTED_CHROMA_POST_RESIDUAL_DENOISE protectedPixels=${state.protectedPixels} " +
            "measuredPixels=$measuredPixels residualDenoiseExecuted=$residualDenoiseExecuted " +
            "meanBeforeFloor=${beforeSum / denominator} meanAfterFloor=${afterSum / denominator} " +
            "raisedPixels=$raisedPixels directionLostPixels=$directionLostPixels hueOwner=DENOISED_VGN_DIRECTION")
        PLog.i(TAG, "IRIS_26827_SPARSE_PROTECTED_CHROMA_APPLY entries=${state.protectedPixels} " +
            "fullPixels=$pixels elapsedMs=${(System.nanoTime() - iris26827SparseApplyStartNs) / 1_000_000.0} " +
            "rgbClassifierOrder=ASCENDING_ORIGINAL_PROTECTED alphaNormalizedOnce=true")
        PLog.i(TAG, "IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA histogramSamples=$histogramSamples " +
            "sceneP90=$sceneP90 sceneP98=$sceneP98 sceneP995=$sceneP995 upperTailStart=$upperTailStart upperTailEnd=$upperTailEnd " +
            "floorCandidatePixels=$floorCandidatePixels legacyWouldRaisePixels=$legacyWouldRaisePixels allowedRaisedPixels=$raisedPixels " +
            "sceneRiskCandidates=$sceneRiskCandidates externallySupportedRiskCandidates=$externallySupportedRiskCandidates " +
            "floorBlockedPixels=$floorBlockedPixels residualReducedPixels=$residualReducedPixels " +
            "meanSuppressedFloorMagnitude=${suppressedFloorMagnitudeSum / floorDenominator} maxSuppressedFloorMagnitude=$maxSuppressedFloorMagnitude " +
            "meanSuppressedResidualMagnitude=${suppressedResidualMagnitudeSum / residualDenominator} maxSuppressedResidualMagnitude=$maxSuppressedResidualMagnitude " +
            "grid=${gridWidth}x${gridHeight} origin=GL_BOTTOM_LEFT")
        buffer.position(0)
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


    /* IRIS_26836_CLAUDE_WB_DOMAIN_CONTRACT
     * Mirrors GlesMgcRawSpatialStacker's calculationWhiteBalance exactly. Neutrality is defined
     * only after these gains; camera-RGB R=G=B is never treated as neutral. */
    private fun calculationWhiteBalance26836(wb: FloatArray): FloatArray {
        fun safeGain(channel: Int, fallback: Float): Float = wb.getOrElse(channel) { fallback }
            .takeIf { it.isFinite() && it > 0f } ?: fallback
        val greenEven = safeGain(1, 1f)
        val greenOdd = safeGain(2, greenEven)
        val greenBase = (0.5f * (greenEven + greenOdd)).takeIf { it.isFinite() && it > 0f } ?: 1f
        fun relative(v: Float) = (v / greenBase).coerceIn(1.0e-3f, 64f)
        return floatArrayOf(relative(safeGain(0, greenBase)), 1f, relative(safeGain(3, greenBase)))
    }

    private fun readR16f26836(texture: Int, width: Int, height: Int): ByteBuffer {
        val bytes = width.toLong() * height * 2L
        val output = LargeDirectBuffer.allocate(bytes, "IRIS26836 R16F clip mask")
            ?: invalid("unable to allocate 26836 R16F mask readback")
        val fbo = IntArray(1); GLES30.glGenFramebuffers(1, fbo, 0)
        requireParity(fbo[0] != 0, "26836 mask FBO allocation failed")
        try {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fbo[0])
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER, GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D, texture, 0)
            requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) == GLES30.GL_FRAMEBUFFER_COMPLETE,
                "26836 mask readback FBO incomplete")
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0); GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 2)
            output.position(0); GLES30.glReadPixels(0,0,width,height,GLES30.GL_RED,GLES30.GL_HALF_FLOAT,output)
            checkGl("read 26836 R16F mask"); output.position(0); return output
        } catch (t: Throwable) { LargeDirectBuffer.free(output); throw t }
        finally { GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1); GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0); GLES30.glDeleteFramebuffers(1,fbo,0) }
    }

    private data class Iris26837Programs(val products:Int,val gaussian:Int,val downsample:Int,val applyFragment:Int)

    private fun compileShader26836(type:Int, source:String, label:String):Int {
        val shader=GLES30.glCreateShader(type); GLES30.glShaderSource(shader,source); GLES30.glCompileShader(shader)
        val ok=IntArray(1); GLES30.glGetShaderiv(shader,GLES30.GL_COMPILE_STATUS,ok,0)
        if(ok[0]==0){val log=GLES30.glGetShaderInfoLog(shader);GLES30.glDeleteShader(shader);invalid("26836 $label compile failed: $log")}
        return shader
    }

    private fun linkFragment26836(fragment:String,label:String):Int {
        val vertex="""
            #version 300 es
            void main(){
                vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));
                gl_Position=vec4(p*2.0-1.0,0.0,1.0);
            }
        """.trimIndent()
        val vs=compileShader26836(GLES30.GL_VERTEX_SHADER,vertex,"$label vertex")
        val fs=compileShader26836(GLES30.GL_FRAGMENT_SHADER,fragment,"$label fragment")
        val p=GLES30.glCreateProgram(); GLES30.glAttachShader(p,vs);GLES30.glAttachShader(p,fs);GLES30.glLinkProgram(p)
        GLES30.glDeleteShader(vs);GLES30.glDeleteShader(fs);val ok=IntArray(1);GLES30.glGetProgramiv(p,GLES30.GL_LINK_STATUS,ok,0)
        if(ok[0]==0){val log=GLES30.glGetProgramInfoLog(p);GLES30.glDeleteProgram(p);invalid("26836 $label link failed: $log")};return p
    }

    private fun linkCompute26836(source:String,label:String):Int {
        val cs=compileShader26836(GLES31.GL_COMPUTE_SHADER,source,"$label compute")
        val p=GLES31.glCreateProgram();GLES31.glAttachShader(p,cs);GLES31.glLinkProgram(p);GLES31.glDeleteShader(cs)
        val ok=IntArray(1);GLES31.glGetProgramiv(p,GLES31.GL_LINK_STATUS,ok,0)
        if(ok[0]==0){val log=GLES31.glGetProgramInfoLog(p);GLES31.glDeleteProgram(p);invalid("26836 $label link failed: $log")};return p
    }

    private fun createTexture26837(width:Int,height:Int,internalFormat:Int,filter:Int):Int {
        val id=IntArray(1);GLES30.glGenTextures(1,id,0);requireParity(id[0]!=0,"26837 texture allocation failed")
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id[0]);GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,filter);GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,filter)
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE);GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE)
        /* IRIS_26837_PROVEN_IMMUTABLE_GL_STORAGE
         * Match GlesMgcRawSpatialStacker.allocateTexture/GLTexture: textures used by the final
         * chroma owner are immutable sized storage, never glTexImage2D mutable storage. */
        GLES30.glTexStorage2D(GLES30.GL_TEXTURE_2D,1,internalFormat,width,height);checkGl("26837 immutable texture init")
        return id[0]
    }

    private fun bindTexture26836(program:Int,name:String,unit:Int,texture:Int){GLES30.glActiveTexture(GLES30.GL_TEXTURE0+unit);GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,texture);GLES30.glUniform1i(GLES30.glGetUniformLocation(program,name),unit)}

    private fun draw26836(program:Int,target:Int,width:Int,height:Int,fbo:Int){
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo);GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,target,0)
        requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE,"26836 draw FBO incomplete")
        GLES30.glViewport(0,0,width,height);GLES30.glDisable(GLES30.GL_BLEND);GLES30.glUseProgram(program);GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3);checkGl("26836 draw")
    }

    private fun gaussianKernel26836(sigmaIn:Float):Pair<FloatArray,Int>{
        val sigma=sigmaIn.coerceIn(0.25f,20f);val radius=kotlin.math.ceil(3.0*sigma.toDouble()).toInt().coerceIn(1,30);val k=FloatArray(61);var sum=0.0
        for(i in -radius..radius){val v=kotlin.math.exp(-0.5*(i.toDouble()/sigma)*(i.toDouble()/sigma));k[i+30]=v.toFloat();sum+=v};for(i in k.indices)k[i]/=sum.toFloat();return k to radius
    }

    private fun gaussianPass26836(program:Int,source:Int,target:Int,width:Int,height:Int,sigma:Float,horizontal:Boolean,fbo:Int){
        val (k,r)=gaussianKernel26836(sigma);GLES30.glUseProgram(program);bindTexture26836(program,"uInput",0,source)
        GLES30.glUniform2i(GLES30.glGetUniformLocation(program,"uSize"),width,height);GLES30.glUniform2i(GLES30.glGetUniformLocation(program,"uDirection"),if(horizontal)1 else 0,if(horizontal)0 else 1)
        GLES30.glUniform1i(GLES30.glGetUniformLocation(program,"uRadius"),r);GLES30.glUniform1fv(GLES30.glGetUniformLocation(program,"uKernel"),61,k,0);GLES30.glUniform1f(GLES30.glGetUniformLocation(program,"uGain"),1f);GLES30.glUniform1i(GLES30.glGetUniformLocation(program,"uClamp01"),0)
        draw26836(program,target,width,height,fbo)
    }

    private fun applyIris26837FinalClipZoneChroma(buffer:ByteBuffer,width:Int,height:Int,maskTexture:Int,wb:FloatArray,t:IrisMotionSettings.EdgeFalseColorTunables.Snapshot){
        requireParity(wb.size==3&&wb.all{it.isFinite()&&it>0f},"26837 invalid calculation WB=${wb.contentToString()}")
        /* IRIS_26837_DEVICE_SAFE_FRAGMENT_BACKEND
         * Claude's WB-linear equations are byte-for-byte mirrored by clipZoneApplyFragment26837.
         * The active apply path uses the same GLES3 FBO draw machinery already proven by the
         * products/Gaussian passes. No glBindImageTexture/imageStore/SSBO capability is required. */
        val programs=Iris26837Programs(
            linkFragment26836(GlesMgcRawSabreShaders.clipZoneProducts26834,"products"),
            linkFragment26836(GlesMgcRawSabreShaders.clipZoneGaussian26834,"gaussian"),
            linkFragment26836(GlesMgcRawSabreShaders.clipZoneDownsample4Products26834,"downsample"),
            linkFragment26836(GlesMgcRawSabreShaders.clipZoneApplyFragment26840,"applyFragment"),
        )
        val textures=ArrayList<Int>();val fboA=IntArray(1);GLES30.glGenFramebuffers(1,fboA,0);val fbo=fboA[0]
        try{
            val source=createTexture26837(width,height,GLES30.GL_RGBA16F,GLES30.GL_NEAREST);textures+=source;GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,source);GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,8);buffer.position(0);GLES30.glTexSubImage2D(GLES30.GL_TEXTURE_2D,0,0,0,width,height,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,buffer);checkGl("26837 upload post-26728 carrier")
            val products=createTexture26837(width,height,GLES30.GL_RGBA16F,GLES30.GL_NEAREST);textures+=products;val scratch=createTexture26837(width,height,GLES30.GL_RGBA16F,GLES30.GL_NEAREST);textures+=scratch
            GLES30.glUseProgram(programs.products);bindTexture26836(programs.products,"uRgb",0,source);bindTexture26836(programs.products,"uMask",1,maskTexture);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.products,"uYFloor"),t.clipZoneYFloor);GLES30.glUniform3f(GLES30.glGetUniformLocation(programs.products,"uCalculationWb"),wb[0],wb[1],wb[2]);draw26836(programs.products,products,width,height,fbo)
            val qw=(width+3)/4;val qh=(height+3)/4;val big=createTexture26837(qw,qh,GLES30.GL_RGBA16F,GLES30.GL_LINEAR);textures+=big;val bigScratch=createTexture26837(qw,qh,GLES30.GL_RGBA16F,GLES30.GL_LINEAR);textures+=bigScratch
            GLES30.glUseProgram(programs.downsample);bindTexture26836(programs.downsample,"uInput",0,products);GLES30.glUniform2i(GLES30.glGetUniformLocation(programs.downsample,"uInputSize"),width,height);draw26836(programs.downsample,big,qw,qh,fbo)
            gaussianPass26836(programs.gaussian,big,bigScratch,qw,qh,t.clipZoneSigmaBig/4f,true,fbo);gaussianPass26836(programs.gaussian,bigScratch,big,qw,qh,t.clipZoneSigmaBig/4f,false,fbo)
            gaussianPass26836(programs.gaussian,products,scratch,width,height,t.clipZoneSigmaSmall,true,fbo);gaussianPass26836(programs.gaussian,scratch,products,width,height,t.clipZoneSigmaSmall,false,fbo)
            val output=createTexture26837(width,height,GLES30.GL_RGBA16F,GLES30.GL_NEAREST);textures+=output
            val copyFbos=IntArray(2);GLES30.glGenFramebuffers(2,copyFbos,0)
            try {
                GLES30.glBindFramebuffer(GLES30.GL_READ_FRAMEBUFFER,copyFbos[0]);GLES30.glFramebufferTexture2D(GLES30.GL_READ_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,source,0)
                GLES30.glBindFramebuffer(GLES30.GL_DRAW_FRAMEBUFFER,copyFbos[1]);GLES30.glFramebufferTexture2D(GLES30.GL_DRAW_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,output,0)
                requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_READ_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE&&GLES30.glCheckFramebufferStatus(GLES30.GL_DRAW_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE,"26837 bit-copy FBO incomplete")
                GLES30.glBlitFramebuffer(0,0,width,height,0,0,width,height,GLES30.GL_COLOR_BUFFER_BIT,GLES30.GL_NEAREST);checkGl("26837 M0 bit-copy")
            } finally { GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0);GLES30.glDeleteFramebuffers(2,copyFbos,0) }
            GLES30.glUseProgram(programs.applyFragment);bindTexture26836(programs.applyFragment,"uRgb",0,source);bindTexture26836(programs.applyFragment,"uMask",1,maskTexture);bindTexture26836(programs.applyFragment,"uSmall",2,products);bindTexture26836(programs.applyFragment,"uBigQuarter",3,big);GLES30.glUniform2i(GLES30.glGetUniformLocation(programs.applyFragment,"uSize"),width,height);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.applyFragment,"uYFloor"),t.clipZoneYFloor);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.applyFragment,"uAThreshold"),t.clipZoneAThreshold);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.applyFragment,"uNeutralRms"),t.clipZoneNeutralRms);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.applyFragment,"uCoherenceThreshold"),t.clipZoneCoherence);GLES30.glUniform1f(GLES30.glGetUniformLocation(programs.applyFragment,"uDirectionCosThreshold"),t.clipZoneDirectionCos);GLES30.glUniform3f(GLES30.glGetUniformLocation(programs.applyFragment,"uCalculationWb"),wb[0],wb[1],wb[2]);checkGl("26840 final fragment bindings")
            draw26836(programs.applyFragment,output,width,height,fbo);checkGl("26840 final fragment apply")
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo);GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,GLES30.GL_TEXTURE_2D,output,0);requireParity(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)==GLES30.GL_FRAMEBUFFER_COMPLETE,"26837 output readback FBO incomplete");GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0);GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,8);buffer.position(0);GLES30.glReadPixels(0,0,width,height,GLES30.GL_RGBA,GLES30.GL_HALF_FLOAT,buffer);checkGl("26837 final readback");buffer.position(0)
            PLog.i(TAG,"IRIS_26840_CLIP_ZONE_CHROMA backend=FBO_FRAGMENT_GLES300 inherited26837Backend=true inherited26839HueContract=true maskCoreLow=0.55 maskCoreHigh=0.95 maskRegularization=INWARD_3X3_TENT maskCanExpand=false maskTailExactNoop=true boundaryHueDirectionContinuous=true crossHueBoundaryBlend=false broadHueAuthority=false sourceHueDirectionOwner=true donorMagnitudeOnly=true hueRequiresSourceSmallBroadConsensus=true neutralWhiteFallback=false warmTerminalFallback=true warmTerminalDeepCoreOnly=true lumaPreserved=WB_LINEAR colorDomain=WB_LINEAR inverseWbRoundTrip=true insertion=POST_RESIDUAL_POST_26728_PRE_TONE dngUntouched=true longColorAuthority=false wb=${wb.contentToString()} sigmaSmall=${t.clipZoneSigmaSmall} sigmaBig=${t.clipZoneSigmaBig} aThreshold=${t.clipZoneAThreshold} neutralRms=${t.clipZoneNeutralRms} coherence=${t.clipZoneCoherence} directionCos=${t.clipZoneDirectionCos}")
        }finally{
            if(textures.isNotEmpty())GLES30.glDeleteTextures(textures.size,textures.toIntArray(),0);if(fbo!=0)GLES30.glDeleteFramebuffers(1,intArrayOf(fbo),0);GLES30.glDeleteProgram(programs.products);GLES30.glDeleteProgram(programs.gaussian);GLES30.glDeleteProgram(programs.downsample);GLES30.glDeleteProgram(programs.applyFragment);GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT,1);GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1);GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,0)
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
