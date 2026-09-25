package com.unspektrawesome.preview

import android.content.Context
import android.graphics.Bitmap
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.params.MeteringRectangle
import android.hardware.camera2.CameraManager
import android.net.Uri
import android.os.SystemClock
import android.view.Surface
import android.view.WindowManager
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import com.unspektrawesome.camera.CameraDescriptor
import com.unspektrawesome.camera.LensFacing
import com.unspektrawesome.camera.RawFormat
import com.unspektrawesome.camera.RawPreviewPolicy
import com.unspektrawesome.camera.Size2d
import com.unspektrawesome.camera.session.Camera2RawSession
import com.unspektrawesome.camera.session.RawHardwareFrame
import com.unspektrawesome.camera.session.RawStillCaptureCallback
import com.unspektrawesome.capture.CaptureGeometry
import com.unspektrawesome.capture.CaptureTransform
import com.unspektrawesome.capture.CaptureMetadata
import com.unspektrawesome.capture.FrameGeometrySnapshot
import com.unspektrawesome.capture.JpegMediaStoreWriter
import com.unspektrawesome.settings.CameraPreferences
import com.unspektrawesome.spektra.SpektraCaptureSnapshot
import com.unspektrawesome.spektra.SpektraFilmParams
import com.unspektrawesome.spektra.SpektraState
import com.unspektrawesome.spektra.SpektraStateRepository
import com.unspektrawesome.vulkan.VulkanRenderer
import com.unspektrawesome.vulkan.params.FrameSeedSnapshot
import com.unspektrawesome.vulkan.params.GeometryShaderParameters
import com.unspektrawesome.vulkan.params.LensShadingMapParameters
import com.unspektrawesome.vulkan.params.RawShaderParameters
import com.unspektrawesome.vulkan.params.RawColorShaderParameters
import com.unspektrawesome.vulkan.params.VulkanCaptureSnapshot
import com.unspektrawesome.vulkan.params.WhiteBalanceGains
import com.particlesdevs.photoncamera.spektra.SpektraExposureController
import com.particlesdevs.photoncamera.processing.ultrahdr.MotionV2Jpeg444Encoder
import com.particlesdevs.photoncamera.app.PhotonCamera
import com.particlesdevs.photoncamera.settings.PreferenceKeys
import com.particlesdevs.photoncamera.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.LinkedHashMap
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

enum class RawPreviewPhase {
    IDLE, PAUSED, WAITING_FOR_SURFACE, OPENING, STREAMING, ERROR, CLOSED,
}

data class RawPreviewStatus(
    val phase: RawPreviewPhase = RawPreviewPhase.IDLE,
    val message: String = "RAW preview is idle",
    val rendererDiagnostic: String = "Renderer has not attached a surface",
    val renderedFrames: Long = 0,
    val skippedFrames: Long = 0,
    val droppedCameraFrames: Long = 0,
    val spektraRevision: Long? = null,
)

enum class RawCapturePhase {
    IDLE, CAPTURING, SAVING, SUCCEEDED, ERROR,
}

data class RawCaptureStatus(
    val phase: RawCapturePhase = RawCapturePhase.IDLE,
    val message: String = "Ready to capture",
    val revisionId: Long? = null,
    val lastUri: Uri? = null,
)

/** Owns Camera2 RAW streaming and synchronous borrowed-buffer Vulkan rendering. */
class RawVulkanPreviewController(
    context: Context,
    private val spektraRepository: SpektraStateRepository,
) : DefaultLifecycleObserver, AutoCloseable {
    fun interface HistogramListener {
        fun onHistogramPixels(pixels: IntArray)
    }

    interface CaptureListener {
        fun onCaptureAccepted(revisionId: Long)
        fun onProcessingStarted(revisionId: Long)
        fun onCaptureSucceeded(revisionId: Long, uri: Uri)
        fun onCaptureFailed(revisionId: Long?, message: String)
    }

    private val lock = Any()
    private val cameraManager = context.applicationContext
        .getSystemService(CameraManager::class.java)
    private val renderer = VulkanRenderer(context.applicationContext)
    private val jpegWriter = JpegMediaStoreWriter(context.applicationContext.contentResolver)
    private val captureWriter = Executors.newSingleThreadExecutor { task ->
        Thread(task, "UnspektrawesomeJpegWriter")
    }
    // IRIS_26696_UNSPEKTRA_AE_POLL_OWNER: 1.1.2 drains pending native meter generations on a
    // 4 ms scheduled loop. It never blocks the render/camera/UI threads waiting for a fence.
    private val exposureMeterPoller: ScheduledExecutorService =
        Executors.newSingleThreadScheduledExecutor { task ->
            Thread(task, "UnspektrawesomeExposureMeter")
        }
    private val windowManager = context.getSystemService(WindowManager::class.java)
    private val mutableStatus = MutableStateFlow(RawPreviewStatus())
    private val mutableCaptureStatus = MutableStateFlow(RawCaptureStatus())
    private val mutableRawImportCapabilities =
        MutableStateFlow<Map<RawImportStreamKey, RawImportCapability>>(emptyMap())

    private var configuredCamera: CameraDescriptor? = null
    private var configuredPreferences = CameraPreferences()
    private var active: ActiveSession? = null
    private var attachedSurface: Surface? = null
    private var viewportSize: Size2d? = null
    private var resumed = false
    private var closed = false
    private var blockedConfiguration: ConfigurationKey? = null
    private var latestWhiteBalance: WhiteBalanceGains? = null
    private var latestLensShadingMap: LensShadingMapParameters? = null
    private var pendingCapture: PendingCapture? = null
    private var renderedFrames = 0L
    private var skippedFrames = 0L
    private val rawParameterBuffer = directBuffer(RawShaderParameters.SIZE_BYTES)
    private val rawColorParameterBuffer = directBuffer(RawColorShaderParameters.SIZE_BYTES)
    private val geometryParameterBuffer = directBuffer(GeometryShaderParameters.SIZE_BYTES)
    private val previewSpektraParameterBuffer = directBuffer(SpektraFilmParams.STRUCT_SIZE)
    private var previewSpektraRevision = Long.MIN_VALUE
    private var lensShadingBuffer: ByteBuffer? = null
    private var lastSuccessPublishAtMs = 0L
    // IRIS_26693_STANDALONE_HISTOGRAM_LIFECYCLE_OWNER
    // Acquisition lives with the Unspektrawesome preview owner, never in an Iris worker/poller.
    private var histogramListener: HistogramListener? = null
    private var captureListener: CaptureListener? = null
    private var lastHistogramPublishAtMs = 0L
    private var lastExposureMeterLogAtMs = 0L
    // IRIS_26694_STANDALONE_AE_METER_INPUT: the carrier is bidirectional. Configure the
    // standalone default center-weighted point before the first native render.
    private val exposureMeterBuffer = directBuffer(VulkanRenderer.EXPOSURE_METER_BYTES).also {
        renderer.configureCenterWeightedExposureMeter(it)
    }
    private val previewTimingBuffer = directBuffer(8)
    private var nextExposureMeterGeneration = 1L
    private val pendingExposureMeters = LinkedHashMap<Long, PendingExposureMeter>()
    private var exposureMeterPollEpoch = 0L
    private var exposureMeterPollScheduled = false
    private var manualIso: Int? = null
    private var manualExposureNs: Long? = null
    private var manualEvSteps: Int = 0
    private var manualFocusDistance: Float? = null

    val status: StateFlow<RawPreviewStatus> = mutableStatus.asStateFlow()
    val captureStatus: StateFlow<RawCaptureStatus> = mutableCaptureStatus.asStateFlow()
    val rawImportCapabilities: StateFlow<Map<RawImportStreamKey, RawImportCapability>> =
        mutableRawImportCapabilities.asStateFlow()

    fun isStreaming(): Boolean = synchronized(lock) {
        !closed && resumed && active?.session?.state() == Camera2RawSession.State.STREAMING &&
            mutableStatus.value.phase == RawPreviewPhase.STREAMING
    }

    fun isCaptureReady(): Boolean = synchronized(lock) {
        isStreaming() && pendingCapture == null && mutableCaptureStatus.value.phase !in BUSY_CAPTURE_PHASES
    }

    fun debugStatus(): String = synchronized(lock) {
        val preview = mutableStatus.value
        val capture = mutableCaptureStatus.value
        "preview=${preview.phase} capture=${capture.phase} frames=${preview.renderedFrames} " +
            "skipped=${preview.skippedFrames} camera=${configuredCamera?.route?.routeId ?: "none"} " +
            "renderer=${renderer.diagnostics()}"
    }

    fun setManualControls(iso: Int?, exposureNs: Long?, evSteps: Int) = synchronized(lock) {
        manualIso = iso
        manualExposureNs = exposureNs
        manualEvSteps = evSteps
        active?.let { owner ->
            applyStoredManualControls(owner)
        }
    }

    fun setManualFocus(focusDistance: Float?) = synchronized(lock) {
        require(focusDistance == null || (focusDistance.isFinite() && focusDistance >= 0f)) {
            "Manual focus distance must be finite and non-negative"
        }
        manualFocusDistance = focusDistance
        active?.session?.setManualFocus(focusDistance)
    }

    fun touchFocus(normalizedX: Float, normalizedY: Float, lockFocus: Boolean) = synchronized(lock) {
        val owner = active ?: return@synchronized
        val activeArray = owner.camera.sensorMetadata.activeArray(false) ?: return@synchronized
        val x = normalizedX.coerceIn(0f, 1f)
        val y = normalizedY.coerceIn(0f, 1f)
        val cx = activeArray.left + (activeArray.width() * x).toInt()
        val cy = activeArray.top + (activeArray.height() * y).toInt()
        val halfW = maxOf(16, activeArray.width() / 20)
        val halfH = maxOf(16, activeArray.height() / 20)
        val left = (cx - halfW).coerceIn(activeArray.left, activeArray.right - 1)
        val top = (cy - halfH).coerceIn(activeArray.top, activeArray.bottom - 1)
        val right = (cx + halfW).coerceIn(left + 1, activeArray.right)
        val bottom = (cy + halfH).coerceIn(top + 1, activeArray.bottom)
        owner.session.touchFocus(
            MeteringRectangle(left, top, right - left, bottom - top, MeteringRectangle.METERING_WEIGHT_MAX),
            lockFocus,
        )
    }

    fun unlockFocus() = synchronized(lock) {
        active?.session?.unlockFocus()
    }

    fun captureStill(): Boolean = synchronized(lock) {
        if (closed || !resumed) {
            publishCaptureErrorLocked("RAW preview is not active")
            return@synchronized false
        }
        if (pendingCapture != null || mutableCaptureStatus.value.phase in BUSY_CAPTURE_PHASES) {
            return@synchronized false
        }
        val owner = active
        if (owner == null || owner.session.state() != Camera2RawSession.State.STREAMING) {
            publishCaptureErrorLocked("RAW preview is not ready for capture")
            return@synchronized false
        }
        val request = runCatching {
            val snapshot = spektraRepository.captureSnapshot()
            /* IRIS_26702_SPEKTRA_ACTIVE_MOTION_ORIENTATION_PARITY
             * Saved stills must use physical device orientation, exactly like Motion. CameraActivity
             * is portrait-locked, so the window/display rotation is not a saved-photo authority. */
            val sensorOrientation = owner.camera.sensorMetadata.orientationDegrees
            val motionCameraRotation = PhotonCamera.getGravity().getCameraRotation(sensorOrientation)
            val transform = CaptureTransform(
                orientationDegrees = motionCameraRotation,
                mirrorHorizontal = owner.camera.facing == LensFacing.FRONT,
            )
            Log.i(
                TAG,
                "IRIS_26702_SPEKTRA_ACTIVE_CAPTURE_ORIENTATION " +
                    "sensor=$sensorOrientation physicalGravity=${PhotonCamera.getGravity().rotation} " +
                    "rotation=$motionCameraRotation mirror=${transform.mirrorHorizontal} " +
                    "source=PhotonCamera.Gravity activeOwner=RawVulkanPreviewController",
            )
            val captureOutput = RawPreviewPolicy.selectCaptureOutput(
                owner.camera.rawOutputs,
                VulkanRawImportPolicy.candidateFormats,
            )
            val geometry = FrameGeometrySnapshot.create(
                owner.camera.sensorMetadata,
                captureOutput,
                transform,
                requireNotNull(viewportSize) { "Viewfinder dimensions are unavailable" },
            )
            PendingCapture(
                owner,
                snapshot,
                captureOutput,
                geometry,
                latestLensShadingMap,
                snapshot.params.toByteBuffer(),
                System.nanoTime() * NANOSECONDS_TO_SECONDS,
                System.currentTimeMillis(),
                PreferenceKeys.isShowWatermarkOn(),
            )
        }.getOrElse { error ->
            publishCaptureErrorLocked(
                "Full-resolution RAW capture is unavailable: ${error.message ?: error.javaClass.simpleName}",
            )
            return@synchronized false
        }
        pendingCapture = request
        clearHistogramLocked()
        Log.i(
            TAG,
            "IRIS_26691_SPEKTRA_CAPTURE_ACCEPT route=${request.owner.camera.route.routeId} " +
                "previewLsc=${lensShadingSummary(request.lensShadingMap)} stage=STILL_CONFIGURING",
        )
        mutableCaptureStatus.value = RawCaptureStatus(
            phase = RawCapturePhase.CAPTURING,
            message = "Configuring full-resolution RAW capture",
            revisionId = request.snapshot.revisionId,
            lastUri = mutableCaptureStatus.value.lastUri,
        )
        notifyCaptureAcceptedLocked(request.snapshot.revisionId)
        runCatching {
            owner.session.captureStill(
                owner.camera.rawOutputs,
                VulkanRawImportPolicy.candidateFormats,
                stillCallback(request),
            )
        }.onFailure { error ->
            pendingCapture = null
            publishCaptureErrorLocked(
                "Full-resolution RAW request failed: ${error.message ?: error.javaClass.simpleName}",
                request.snapshot.revisionId,
            )
        }.isSuccess
    }

    fun configure(camera: CameraDescriptor?, preferences: CameraPreferences) = synchronized(lock) {
        check(!closed) { "Preview controller is closed" }
        val changed = configuredCamera?.route?.routeId != camera?.route?.routeId ||
            configuredPreferences.previewQuality != preferences.previewQuality ||
            configuredPreferences.rawPreviewStreams != preferences.rawPreviewStreams
        configuredCamera = camera
        configuredPreferences = preferences
        if (changed) {
            blockedConfiguration = null
            latestWhiteBalance = null
            latestLensShadingMap = null
        }
        reconcileLocked()
    }

    fun attachSurface(surface: Surface) = synchronized(lock) {
        check(!closed) { "Preview controller is closed" }
        if (!surface.isValid) {
            publishLocked(RawPreviewPhase.WAITING_FOR_SURFACE, "Viewfinder surface is not valid")
            return@synchronized
        }
        if (attachedSurface === surface) return@synchronized
        stopActiveLocked()
        attachedSurface = surface
        blockedConfiguration = null
        if (!renderer.setSurface(surface)) {
            attachedSurface = null
            publishLocked(RawPreviewPhase.ERROR, "Vulkan rejected the viewfinder surface")
            return@synchronized
        }
        reconcileLocked()
    }

    fun updateViewport(width: Int, height: Int) = synchronized(lock) {
        if (closed || width <= 0 || height <= 0) return@synchronized
        viewportSize = Size2d(width, height)
    }
    fun detachSurface(surface: Surface? = null) = synchronized(lock) {
        if (closed || (surface != null && attachedSurface !== surface)) return@synchronized
        stopActiveLocked()
        attachedSurface = null
        renderer.setSurface(null)
        publishLocked(RawPreviewPhase.WAITING_FOR_SURFACE, "Waiting for viewfinder surface")
    }

    override fun onResume(owner: LifecycleOwner) = synchronized(lock) {
        if (closed) return@synchronized
        resumed = true
        blockedConfiguration = null
        reconcileLocked()
    }

    override fun onPause(owner: LifecycleOwner) = synchronized(lock) {
        if (closed) return@synchronized
        resumed = false
        stopActiveLocked()
        publishLocked(RawPreviewPhase.PAUSED, "RAW preview is paused")
    }

    override fun onDestroy(owner: LifecycleOwner) {
        close()
    }

    override fun close() = synchronized(lock) {
        if (closed) return@synchronized
        closed = true
        resumed = false
        active?.session?.close()
        active = null
        attachedSurface = null
        pendingCapture = null
        resetExposureMeterStateLocked()
        clearHistogramLocked()
        histogramListener = null
        captureListener = null
        renderer.close()
        exposureMeterPoller.shutdownNow()
        captureWriter.shutdownNow()
        publishLocked(RawPreviewPhase.CLOSED, "RAW preview is closed")
    }

    /** Non-blocking mode handoff. Completion means CameraDevice.onClosed actually fired. */
    fun retireForModeHandoff(onReleased: Runnable) {
        val current = synchronized(lock) {
            configuredCamera = null
            blockedConfiguration = null
            resetExposureMeterStateLocked()
            clearHistogramLocked()
            val owner = active
            if (owner != null && pendingCapture?.owner === owner) {
                val revision = pendingCapture?.snapshot?.revisionId
                pendingCapture = null
                publishCaptureErrorLocked("RAW capture was canceled by mode handoff", revision)
            }
            active = null
            owner
        }
        if (current == null) {
            onReleased.run()
            return
        }
        current.session.closeWhenCameraReleased {
            synchronized(lock) {
                if (!closed) publishLocked(RawPreviewPhase.IDLE, "Spektra camera released for mode handoff")
            }
            Log.i(TAG, "IRIS_26696_SPEKTRA_CAMERA_RELEASED route=${current.camera.route.routeId}")
            onReleased.run()
        }
    }

    private fun stillCallback(request: PendingCapture) = object : RawStillCaptureCallback {
        override fun onStillFrame(frame: RawHardwareFrame) {
            processStillFrame(request, frame)
        }

        override fun onPreviewResumed() = Unit

        override fun onStillCaptureError(error: Camera2RawSession.SessionError) = synchronized(lock) {
            if (pendingCapture !== request) return@synchronized
            pendingCapture = null
            publishCaptureErrorLocked(
                "${error.code}: ${error.message}",
                request.snapshot.revisionId,
            )
            resumePreviewAfterStillLocked(request.owner)
        }
    }

    private fun processStillFrame(request: PendingCapture, frame: RawHardwareFrame) = synchronized(lock) {
        if (closed || pendingCapture !== request || active !== request.owner) {
            pendingCapture = null
            return@synchronized
        }
        notifyProcessingStartedLocked(request.snapshot.revisionId)
        val processed = runCatching {
            runCatching { WhiteBalanceGains.fromRawCaptureMetadata(frame.metadata) }
                .getOrNull()?.also { latestWhiteBalance = it }
            check(frame.output == request.captureOutput) {
                "Still RAW output does not match the shutter geometry snapshot"
            }
            val whiteBalance = WhiteBalanceGains.fromRawCaptureMetadata(frame.metadata)
                .also { latestWhiteBalance = it }
            val stillLensShading = runCatching {
                LensShadingMapParameters.fromRawCaptureMetadataOrNull(frame.metadata)
            }.getOrNull()
            val captureLensShading = stillLensShading ?: request.lensShadingMap
            captureLensShading?.also { latestLensShadingMap = it }
            val lensShadingSource = when {
                stillLensShading != null -> "STILL"
                request.lensShadingMap != null -> "PREVIEW"
                else -> "NONE"
            }
            Log.i(
                TAG,
                "IRIS_26691_SPEKTRA_STILL_RAW route=${request.owner.camera.route.routeId} " +
                    "lscSource=$lensShadingSource lsc=${lensShadingSummary(captureLensShading)} " +
                    "raw=${frame.output.format}:${frame.output.size.width}x${frame.output.size.height} " +
                    "carrier=${if (frame.packedRawBytes != null) "ROW_STRIDE_BUFFER" else "HARDWARE_BUFFER"}",
            )
            val captureSnapshot = VulkanCaptureSnapshot.from(request.snapshot, frame.metadata)
            val raw = RawShaderParameters.forCapture(
                frame.output,
                request.owner.camera.sensorMetadata,
                frame.metadata,
                frame.rowStrideBytes,
                captureSnapshot,
            )
            val rawColor = RawColorShaderParameters.fromCaptureSnapshot(
                captureSnapshot,
                request.owner.camera.sensorMetadata,
                whiteBalance,
                captureLensShading,
            )
            val outputSize = request.geometry.outputSize
            val bitmap = Bitmap.createBitmap(outputSize.width, outputSize.height, Bitmap.Config.ARGB_8888)
            val rendered = renderer.captureRcd(
                frame.hardwareBuffer,
                frame.packedRawBytes,
                raw.writeTo(rawParameterBuffer),
                rawColor.writeTo(rawColorParameterBuffer),
                GeometryShaderParameters.from(request.geometry).writeTo(geometryParameterBuffer),
                request.spektraParameters,
                lensShadingByteBuffer(captureLensShading),
                bitmap,
                request.spektraTimeSeconds,
            )
            if (!rendered) {
                bitmap.recycle()
                error(renderer.diagnostics())
            }
            Log.i(
                TAG,
                "IRIS_26691_SPEKTRA_RCD_OK output=${outputSize.width}x${outputSize.height} " +
                    "lsc=${lensShadingSummary(captureLensShading)}",
            )
            bitmap
        }

        resumePreviewAfterStillLocked(request.owner)
        processed.onSuccess { image ->
            mutableCaptureStatus.value = RawCaptureStatus(
                phase = RawCapturePhase.SAVING,
                message = "Saving full-resolution RCD capture",
                revisionId = request.snapshot.revisionId,
                lastUri = mutableCaptureStatus.value.lastUri,
            )
            saveCapture(request, frame, image)
        }.onFailure { error ->
            pendingCapture = null
            publishCaptureErrorLocked(
                "Vulkan RCD capture failed: ${error.message ?: error.javaClass.simpleName}",
                request.snapshot.revisionId,
            )
        }
    }

    private fun saveCapture(
        request: PendingCapture,
        frame: RawHardwareFrame,
        image: Bitmap,
    ) {
        val metadata = CaptureMetadata(
            sensorTimestampNs = frame.metadata.sensorTimestampNs,
            exposureTimeNs = frame.metadata.exposureTimeNs,
            sensitivityIso = frame.metadata.sensitivityIso,
            focalLengthMm = request.owner.camera.focalLengthMm,
            lensModel = request.owner.camera.displayName(),
        )
        captureWriter.execute {
            val result = try {
                runCatching {
                    if (request.watermarkEnabled) {
                        check(MotionV2Jpeg444Encoder.applyFinalRasterWatermark(image)) {
                            "Spektra Motion-parity watermark application failed"
                        }
                        Log.i(TAG, "IRIS_26700_SPEKTRA_WATERMARK_PARITY applied=true " +
                            "revision=${request.snapshot.revisionId} finalRaster=${image.width}x${image.height}")
                    } else {
                        Log.i(TAG, "IRIS_26700_SPEKTRA_WATERMARK_PARITY applied=false " +
                            "revision=${request.snapshot.revisionId} toggleFrozen=false")
                    }
                    jpegWriter.write(
                        image,
                        metadata,
                        capturedAtMillis = request.capturedAtMillis,
                    )
                }
            } finally {
                image.recycle()
            }
            synchronized(lock) {
                if (pendingCapture !== request) return@synchronized
                pendingCapture = null
                result.onSuccess { uri ->
                    Log.i(TAG, "IRIS_26691_SPEKTRA_JPEG_SAVED uri=$uri revision=${request.snapshot.revisionId}")
                    mutableCaptureStatus.value = RawCaptureStatus(
                        phase = RawCapturePhase.SUCCEEDED,
                        message = "Saved full-resolution RCD capture",
                        revisionId = request.snapshot.revisionId,
                        lastUri = uri,
                    )
                    notifyCaptureSucceededLocked(request.snapshot.revisionId, uri)
                }.onFailure { error ->
                    publishCaptureErrorLocked(
                        "JPEG save failed: ${error.message ?: error.javaClass.simpleName}",
                        request.snapshot.revisionId,
                    )
                }
            }
        }
    }

    private fun resumePreviewAfterStillLocked(owner: ActiveSession) {
        if (closed || active !== owner) return
        runCatching { owner.session.resumePreview() }.onFailure { error ->
            publishCaptureErrorLocked(
                "RAW preview resume failed: ${error.message ?: error.javaClass.simpleName}",
                pendingCapture?.snapshot?.revisionId,
            )
        }
    }

    private fun publishCaptureErrorLocked(message: String, revisionId: Long? = null) {
        Log.e(TAG, "IRIS_26691_SPEKTRA_CAPTURE_ERROR revision=$revisionId message=$message")
        mutableCaptureStatus.value = RawCaptureStatus(
            phase = RawCapturePhase.ERROR,
            message = message,
            revisionId = revisionId,
            lastUri = mutableCaptureStatus.value.lastUri,
        )
        notifyCaptureFailedLocked(revisionId, message)
    }

    fun setCaptureListener(listener: CaptureListener?) = synchronized(lock) {
        captureListener = listener
    }

    private fun notifyCaptureAcceptedLocked(revisionId: Long) {
        runCatching { captureListener?.onCaptureAccepted(revisionId) }.onFailure { error ->
            Log.e(TAG, "IRIS_26694_SPEKTRA_CAPTURE_UI_CALLBACK_FAILED phase=ACCEPTED " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    private fun notifyProcessingStartedLocked(revisionId: Long) {
        runCatching { captureListener?.onProcessingStarted(revisionId) }.onFailure { error ->
            Log.e(TAG, "IRIS_26694_SPEKTRA_CAPTURE_UI_CALLBACK_FAILED phase=PROCESSING " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    private fun notifyCaptureSucceededLocked(revisionId: Long, uri: Uri) {
        runCatching { captureListener?.onCaptureSucceeded(revisionId, uri) }.onFailure { error ->
            Log.e(TAG, "IRIS_26694_SPEKTRA_CAPTURE_UI_CALLBACK_FAILED phase=SUCCEEDED " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    private fun notifyCaptureFailedLocked(revisionId: Long?, message: String) {
        runCatching { captureListener?.onCaptureFailed(revisionId, message) }.onFailure { error ->
            Log.e(TAG, "IRIS_26694_SPEKTRA_CAPTURE_UI_CALLBACK_FAILED phase=ERROR " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    fun setHistogramListener(listener: HistogramListener?) = synchronized(lock) {
        histogramListener = listener
        lastHistogramPublishAtMs = 0L
        if (listener != null && (closed || !resumed ||
            active?.session?.state() != Camera2RawSession.State.STREAMING ||
            mutableStatus.value.phase != RawPreviewPhase.STREAMING
        )) {
            runCatching { listener.onHistogramPixels(IntArray(0)) }
        }
    }

    private fun publishHistogramFromRenderedFrameLocked(owner: ActiveSession, nowMs: Long) {
        val listener = histogramListener ?: return
        if (closed || !resumed || active !== owner ||
            owner.session.state() != Camera2RawSession.State.STREAMING
        ) return
        if (nowMs - lastHistogramPublishAtMs < HISTOGRAM_MIN_INTERVAL_MS) return
        lastHistogramPublishAtMs = nowMs
        val pixels = runCatching { renderer.histogramPixels(1.0f) }.getOrElse { IntArray(0) }
        runCatching { listener.onHistogramPixels(pixels) }.onFailure { error ->
            Log.w(TAG, "IRIS_26693_SPEKTRA_HISTOGRAM_PRESENTATION_FAILURE " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    private fun clearHistogramLocked() {
        lastHistogramPublishAtMs = 0L
        val listener = histogramListener ?: return
        runCatching { listener.onHistogramPixels(IntArray(0)) }.onFailure { error ->
            Log.w(TAG, "IRIS_26693_SPEKTRA_HISTOGRAM_CLEAR_FAILURE " +
                (error.message ?: error.javaClass.simpleName))
        }
    }

    private fun lensShadingSummary(map: LensShadingMapParameters?): String =
        map?.let { "${it.width}x${it.height}" } ?: "none"

    @Suppress("DEPRECATION")
    private fun displayRotationDegrees(): Int = when (windowManager.defaultDisplay.rotation) {
        Surface.ROTATION_0 -> 0
        Surface.ROTATION_90 -> 90
        Surface.ROTATION_180 -> 180
        Surface.ROTATION_270 -> 270
        else -> 0
    }

    private fun reconcileLocked() {
        if (closed) return
        val camera = configuredCamera
        val surface = attachedSurface
        if (!resumed) {
            stopActiveLocked()
            publishLocked(RawPreviewPhase.PAUSED, "RAW preview is paused")
            return
        }
        if (surface == null || !surface.isValid) {
            stopActiveLocked()
            publishLocked(RawPreviewPhase.WAITING_FOR_SURFACE, "Waiting for viewfinder surface")
            return
        }
        if (camera == null) {
            stopActiveLocked()
            publishLocked(RawPreviewPhase.IDLE, "Select a RAW camera")
            return
        }

        val plan = runCatching {
            RawPreviewPlanSelector.select(
                camera,
                configuredPreferences,
                importCapabilities = mutableRawImportCapabilities.value,
            )
        }.getOrElse { error ->
            stopActiveLocked()
            publishLocked(
                RawPreviewPhase.ERROR,
                "RAW preview selection failed: ${error.message ?: error.javaClass.simpleName}",
            )
            return
        }
        val key = ConfigurationKey(camera.route.routeId, plan)
        if (blockedConfiguration == key) return
        val current = active
        if (current != null) {
            if (current.key == key && current.session.state() !in TERMINAL_SESSION_STATES) return
            stopActiveLocked()
            return
        }
        startLocked(camera, plan, key)
    }

    private fun startLocked(
        camera: CameraDescriptor,
        plan: RawPreviewPolicy.Plan,
        key: ConfigurationKey,
    ) {
        val characteristics = cameraManager.getCameraCharacteristics(camera.route.characteristicsCameraId)
        val exposure = SpektraExposureController(
            characteristics, camera.equivalentFocalLengthMm,
        ).also { it.reset(System.nanoTime()) }
        val session = Camera2RawSession(cameraManager)
        val owner = ActiveSession(session, camera, plan, key, characteristics, exposure)
        applyStoredManualControls(owner)
        session.setManualFocus(manualFocusDistance)
        resetExposureMeterStateLocked()
        active = owner
        publishLocked(
            RawPreviewPhase.OPENING,
            "Opening ${camera.displayName()} at ${plan.processingSize}",
        )
        session.start(
            camera.route,
            plan.acquisitionOutput,
            plan.aeTargetRange,
            { frame -> renderFrame(owner, frame) },
            object : com.unspektrawesome.camera.session.RawSessionListener {
                override fun onStateChanged(state: Camera2RawSession.State) {
                    handleSessionState(owner, state)
                }

                override fun onError(error: Camera2RawSession.SessionError) {
                    handleSessionError(owner, error)
                }
            },
        )
    }

    private fun stopActiveLocked() {
        clearHistogramLocked()
        resetExposureMeterStateLocked()
        val current = active ?: return
        if (pendingCapture?.owner === current &&
            mutableCaptureStatus.value.phase == RawCapturePhase.CAPTURING
        ) {
            val revision = pendingCapture?.snapshot?.revisionId
            pendingCapture = null
            publishCaptureErrorLocked("RAW capture was canceled", revision)
        }
        current.session.close()
        if (current.session.state() in TERMINAL_SESSION_STATES) active = null
    }

    private fun handleSessionState(owner: ActiveSession, state: Camera2RawSession.State) =
        synchronized(lock) {
            if (closed || active !== owner) return@synchronized
            when (state) {
                Camera2RawSession.State.OPENING, Camera2RawSession.State.CONFIGURING ->
                    publishLocked(RawPreviewPhase.OPENING, "Configuring RAW-only Camera2 session")
                Camera2RawSession.State.STREAMING ->
                    publishLocked(RawPreviewPhase.STREAMING, "RAW Vulkan preview streaming")
                Camera2RawSession.State.CLOSED -> {
                    active = null
                    reconcileLocked()
                }
                Camera2RawSession.State.UNSUPPORTED, Camera2RawSession.State.ERROR -> {
                    if (pendingCapture?.owner === owner) {
                        val revision = pendingCapture?.snapshot?.revisionId
                        pendingCapture = null
                        publishCaptureErrorLocked("RAW session ended during capture", revision)
                    }
                    active = null
                    blockedConfiguration = owner.key
                }
                else -> Unit
            }
        }

    private fun handleSessionError(
        owner: ActiveSession,
        error: Camera2RawSession.SessionError,
    ) = synchronized(lock) {
        if (closed || active !== owner) return@synchronized
        if (error.fatal) {
            blockedConfiguration = owner.key
            if (error.code == Camera2RawSession.ErrorCode.BUFFER) {
                val reason = buildString {
                    append("${error.code}: ${error.message}")
                    error.cause?.message?.takeIf(String::isNotBlank)?.let {
                        append(": $it")
                    }
                }
                recordRawImportCapability(
                    owner,
                    RawImportCapability(RawImportCapabilityState.INCOMPATIBLE, reason),
                )
            }
        }
        publishLocked(
            RawPreviewPhase.ERROR,
            "${error.code}: ${error.message}",
            owner,
        )
    }

    private fun renderFrame(owner: ActiveSession, frame: RawHardwareFrame) = synchronized(lock) {
        if (closed || !resumed || attachedSurface == null || active !== owner) {
            skippedFrames++
            return@synchronized
        }
        var meterGeneration = 0L
        runCatching {
            runCatching { WhiteBalanceGains.fromRawCaptureMetadata(frame.metadata) }
                .getOrNull()?.let { latestWhiteBalance = it }
            runCatching { LensShadingMapParameters.fromRawCaptureMetadataOrNull(frame.metadata) }
                .getOrNull()?.let { latestLensShadingMap = it }

            val whiteBalance = latestWhiteBalance ?: run {
                skippedFrames++
                publishLocked(
                    RawPreviewPhase.OPENING,
                    "Waiting for valid RAW white-balance metadata: " +
                        (frame.metadata.neutralColorPoint()?.contentToString() ?: "missing"),
                    owner,
                )
                return@synchronized
            }
            val state = spektraRepository.captureSnapshot()
            val capture = VulkanCaptureSnapshot.from(state, frame.metadata)
            val geometry = FrameGeometrySnapshot.create(
                owner.camera.sensorMetadata,
                frame.output,
                CaptureGeometry.transform(
                    owner.camera.sensorMetadata.orientationDegrees,
                    displayRotationDegrees(),
                    owner.camera.facing,
                ),
                requireNotNull(viewportSize) { "Viewfinder dimensions are unavailable" },
                owner.plan.processingSize,
            )
            val raw = RawShaderParameters.forPreview(
                frame.output,
                owner.camera.sensorMetadata,
                frame.metadata,
                frame.rowStrideBytes,
                geometry.outputSize,
                FrameSeedSnapshot.fromFrameNumber(frame.metadata.frameNumber),
            )
            val rawColor = RawColorShaderParameters.fromCaptureSnapshot(
                capture,
                owner.camera.sensorMetadata,
                whiteBalance,
                latestLensShadingMap,
            )
            meterGeneration = prepareExposureMeterForFrameLocked(owner, frame)
            val rendered = renderer.render(
                frame.hardwareBuffer,
                frame.packedRawBytes,
                raw.writeTo(rawParameterBuffer),
                rawColor.writeTo(rawColorParameterBuffer),
                GeometryShaderParameters.from(geometry).writeTo(geometryParameterBuffer),
                previewSpektraParameters(state.state),
                lensShadingByteBuffer(),
                geometry.outputSize.width,
                geometry.outputSize.height,
                previewTimingBuffer,
                exposureMeterBuffer,
            )
            if (rendered) {
                consumeExposureMeterCarrierLocked(owner, "render")
                scheduleExposureMeterPollLocked()
                recordRawImportCapability(
                    owner,
                    RawImportCapability(
                        RawImportCapabilityState.COMPATIBLE,
                        if (frame.packedRawBytes != null)
                            "Actual Camera2 ${frame.output.format} row-stride plane uploaded to the native Vulkan RAW buffer"
                        else
                            "Actual Camera2 ${frame.output.format} HardwareBuffer imported by Vulkan",
                    ),
                )
                renderedFrames++
                val now = SystemClock.elapsedRealtime()
                publishHistogramFromRenderedFrameLocked(owner, now)
                val previous = mutableStatus.value
                if (previous.phase != RawPreviewPhase.STREAMING ||
                    previous.spektraRevision != state.revisionId ||
                    now - lastSuccessPublishAtMs >= STATUS_PUBLISH_INTERVAL_MS
                ) {
                    lastSuccessPublishAtMs = now
                    publishLocked(
                        RawPreviewPhase.STREAMING,
                        "RAW Vulkan preview streaming",
                        owner,
                        state.revisionId,
                    )
                }
            } else {
                if (meterGeneration > 0L) pendingExposureMeters.remove(meterGeneration)
                skippedFrames++
                val diagnostic = renderer.diagnostics()
                val importRejection =
                    RawImportDiagnosticClassifier.importRejectionReason(diagnostic)
                if (importRejection != null) {
                    recordRawImportCapability(
                        owner,
                        RawImportCapability(
                            RawImportCapabilityState.INCOMPATIBLE,
                            importRejection,
                        ),
                    )
                    blockedConfiguration = owner.key
                    publishLocked(
                        RawPreviewPhase.ERROR,
                        "${frame.output.format} ${frame.output.size.width} x " +
                            "${frame.output.size.height} cannot use Vulkan zero-copy import: " +
                            importRejection,
                        owner,
                    )
                    owner.session.close()
                } else {
                    publishLocked(
                        RawPreviewPhase.ERROR,
                        "Vulkan RAW error: $diagnostic",
                        owner,
                    )
                }
            }
        }.onFailure { error ->
            if (meterGeneration > 0L) pendingExposureMeters.remove(meterGeneration)
            skippedFrames++
            publishLocked(
                RawPreviewPhase.ERROR,
                "RAW frame render failed: ${error.message ?: error.javaClass.simpleName}",
                owner,
            )
        }
    }

    private fun applyStoredManualControls(owner: ActiveSession) {
        val mode = when {
            manualIso == null && manualExposureNs == null -> SpektraExposureController.Mode.AUTO
            manualIso != null && manualExposureNs == null -> SpektraExposureController.Mode.ISO_PRIORITY
            manualIso == null -> SpektraExposureController.Mode.SHUTTER_PRIORITY
            else -> SpektraExposureController.Mode.MANUAL
        }
        val step = owner.characteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP)
        val ev = if (step != null && step.denominator != 0) manualEvSteps * step.toDouble() else 0.0
        owner.exposure.setMode(mode, manualIso, manualExposureNs)
        owner.exposure.setExposureCompensationEv(ev)
        val initial = owner.exposure.initialSolution()
        owner.session.setSensorExposure(
            initial.iso, initial.exposureNs, owner.exposure.exposureGeneration,
        )
    }

    // IRIS_26696_UNSPEKTRA_AE_GENERATION_CONTRACT
    // 1.1.2 tags every render, clears output slots, consumes an immediate result after render,
    // then polls every 4 ms until all pending generations have drained.
    private fun prepareExposureMeterForFrameLocked(owner: ActiveSession, frame: RawHardwareFrame): Long {
        val actualIso = frame.metadata.sensitivityIso ?: return 0L
        val actualExposureNs = frame.metadata.exposureTimeNs ?: return 0L
        val requestedIso = frame.metadata.requestedSensitivityIso ?: return 0L
        val exposureGeneration = frame.metadata.exposureGeneration
        if (actualIso <= 0 || actualExposureNs <= 0L || requestedIso <= 0 ||
            exposureGeneration != owner.exposure.exposureGeneration) return 0L
        var generation = nextExposureMeterGeneration++
        if (generation <= 0L) {
            nextExposureMeterGeneration = 2L
            generation = 1L
        }
        pendingExposureMeters[generation] = PendingExposureMeter(
            owner,
            frame.metadata.sensorTimestampNs,
            exposureGeneration,
            requestedIso,
            actualIso,
            actualExposureNs,
        )
        while (pendingExposureMeters.size > MAX_PENDING_EXPOSURE_METERS) {
            val oldest = pendingExposureMeters.entries.iterator().next()
            pendingExposureMeters.remove(oldest.key)
        }
        renderer.configureCenterWeightedExposureMeter(exposureMeterBuffer)
        exposureMeterBuffer.putLong(EXPOSURE_METER_GENERATION_OFFSET, generation)
        exposureMeterBuffer.putLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET, 0L)
        exposureMeterBuffer.putDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET, Double.NaN)
        exposureMeterBuffer.position(0)
        return generation
    }

    private fun consumeExposureMeterCarrierLocked(owner: ActiveSession, source: String): Boolean {
        val sequence = exposureMeterBuffer.getLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET)
        val meter = exposureMeterBuffer.getDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET)
        // IRIS_26697_SIGNED_NATIVE_METER_EV: negative, zero and positive EV are all valid.
        if (sequence <= 0L || !meter.isFinite()) return false
        exposureMeterBuffer.putLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET, 0L)
        exposureMeterBuffer.putDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET, Double.NaN)
        val pending = pendingExposureMeters.remove(sequence) ?: return false
        if (pending.owner !== owner || active !== owner) return false
        val solution = owner.exposure.update(
            pending.sensorTimestampNs,
            meter,
            pending.actualIso,
            pending.actualExposureNs,
            pending.exposureGeneration,
            pending.requestedIso,
        )
        val changed = solution != null
        if (solution != null) {
            owner.session.setSensorExposure(
                solution.iso, solution.exposureNs, owner.exposure.exposureGeneration,
            )
        }
        val logNowMs = SystemClock.elapsedRealtime()
        if (lastExposureMeterLogAtMs == 0L || logNowMs - lastExposureMeterLogAtMs >= AE_METER_LOG_INTERVAL_MS) {
            lastExposureMeterLogAtMs = logNowMs
            Log.i(
                TAG,
                "IRIS_26697_UNSPEKTRA_AE source=$source generation=$sequence " +
                    "sensorTimestampNs=${pending.sensorTimestampNs} meterEv=$meter " +
                    "frameAeGeneration=${pending.exposureGeneration} " +
                    "controllerAeGeneration=${owner.exposure.exposureGeneration} " +
                    "requestedIso=${pending.requestedIso} actualIso=${pending.actualIso} " +
                    "actualExposureNs=${pending.actualExposureNs} " +
                    "nextIso=${solution?.iso ?: owner.exposure.currentIso} " +
                    "nextExposureNs=${solution?.exposureNs ?: owner.exposure.currentExposureNs} " +
                    "changed=$changed",
            )
        }
        return true
    }

    private fun scheduleExposureMeterPollLocked() {
        if (closed || pendingExposureMeters.isEmpty() || exposureMeterPollScheduled) return
        val epoch = exposureMeterPollEpoch
        exposureMeterPollScheduled = true
        exposureMeterPoller.schedule({
            synchronized(lock) {
                exposureMeterPollScheduled = false
                if (closed || epoch != exposureMeterPollEpoch) return@synchronized
                val owner = active ?: return@synchronized
                val polled = runCatching { renderer.pollExposureMeter(exposureMeterBuffer) }
                    .getOrElse { error ->
                        Log.e(TAG, "IRIS_26696_UNSPEKTRA_AE_POLL_FAILED", error)
                        false
                    }
                if (polled) consumeExposureMeterCarrierLocked(owner, "poll")
                if (pendingExposureMeters.isNotEmpty()) scheduleExposureMeterPollLocked()
            }
        }, EXPOSURE_METER_POLL_MS, TimeUnit.MILLISECONDS)
    }

    private fun resetExposureMeterStateLocked() {
        exposureMeterPollEpoch++
        exposureMeterPollScheduled = false
        pendingExposureMeters.clear()
        exposureMeterBuffer.putLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET, 0L)
        exposureMeterBuffer.putDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET, Double.NaN)
    }

    private fun lensShadingByteBuffer(
        map: LensShadingMapParameters? = latestLensShadingMap,
    ): ByteBuffer? {
        map ?: return null
        val current = lensShadingBuffer
        val target = if (current == null || current.capacity() < map.sizeBytes) {
            directBuffer(map.sizeBytes).also { lensShadingBuffer = it }
        } else {
            current
        }
        return map.writeTo(target)
    }

    private fun previewSpektraParameters(state: SpektraState): ByteBuffer {
        if (previewSpektraRevision != state.revisionId) {
            state.params.writeTo(previewSpektraParameterBuffer)
            previewSpektraRevision = state.revisionId
        } else {
            previewSpektraParameterBuffer.position(0)
            previewSpektraParameterBuffer.limit(SpektraFilmParams.STRUCT_SIZE)
        }
        return previewSpektraParameterBuffer
    }

    private fun recordRawImportCapability(
        owner: ActiveSession,
        capability: RawImportCapability,
    ) {
        val key = RawImportStreamKey.from(
            owner.camera.route.routeId,
            owner.plan.acquisitionOutput,
        )
        if (mutableRawImportCapabilities.value[key] == capability) return
        mutableRawImportCapabilities.value =
            mutableRawImportCapabilities.value + (key to capability)
    }

    private fun publishLocked(
        phase: RawPreviewPhase,
        message: String,
        owner: ActiveSession? = active,
        revision: Long? = mutableStatus.value.spektraRevision,
    ) {
        mutableStatus.value = RawPreviewStatus(
            phase = phase,
            message = message,
            rendererDiagnostic = renderer.diagnostics(),
            renderedFrames = renderedFrames,
            skippedFrames = skippedFrames,
            droppedCameraFrames = owner?.session?.droppedPendingFrames() ?: 0L,
            spektraRevision = revision,
        )
    }

    private data class ConfigurationKey(
        val routeId: String,
        val acquisitionOutput: com.unspektrawesome.camera.RawOutput,
        val processingWidth: Int,
        val processingHeight: Int,
        val framesPerSecond: Int,
    ) {
        constructor(routeId: String, plan: RawPreviewPolicy.Plan) : this(
            routeId,
            plan.acquisitionOutput,
            plan.processingSize.width,
            plan.processingSize.height,
            plan.framesPerSecond,
        )
    }

    private data class PendingExposureMeter(
        val owner: ActiveSession,
        val sensorTimestampNs: Long,
        val exposureGeneration: Long,
        val requestedIso: Int?,
        val actualIso: Int,
        val actualExposureNs: Long,
    )

    private data class ActiveSession(
        val session: Camera2RawSession,
        val camera: CameraDescriptor,
        val plan: RawPreviewPolicy.Plan,
        val key: ConfigurationKey,
        val characteristics: CameraCharacteristics,
        val exposure: SpektraExposureController,
    )

    private data class PendingCapture(
        val owner: ActiveSession,
        val snapshot: SpektraCaptureSnapshot,
        val captureOutput: com.unspektrawesome.camera.RawOutput,
        val geometry: FrameGeometrySnapshot,
        val lensShadingMap: LensShadingMapParameters?,
        val spektraParameters: ByteBuffer,
        val spektraTimeSeconds: Double,
        val capturedAtMillis: Long,
        val watermarkEnabled: Boolean,
    )

    private companion object {
        const val TAG = "UnspekRawPreview"
        const val STATUS_PUBLISH_INTERVAL_MS = 1_000L
        const val HISTOGRAM_MIN_INTERVAL_MS = 50L
        const val AE_METER_LOG_INTERVAL_MS = 500L
        private const val EXPOSURE_METER_GENERATION_OFFSET = 0
        const val EXPOSURE_METER_POLL_MS = 4L
        const val MAX_PENDING_EXPOSURE_METERS = 8
        const val NANOSECONDS_TO_SECONDS = 1e-9

        val BUSY_CAPTURE_PHASES = setOf(RawCapturePhase.CAPTURING, RawCapturePhase.SAVING)

        fun directBuffer(size: Int): ByteBuffer = ByteBuffer.allocateDirect(size)
            .order(ByteOrder.nativeOrder())

        val TERMINAL_SESSION_STATES = setOf(
            Camera2RawSession.State.CLOSED,
            Camera2RawSession.State.UNSUPPORTED,
            Camera2RawSession.State.ERROR,
        )
    }
}
