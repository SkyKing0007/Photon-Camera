package com.unspektrawesome.vulkan

import android.content.Context
import android.graphics.Bitmap
import android.hardware.HardwareBuffer
import android.view.Surface
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Iris shell for the original UnspektrAwesome 1.2.5 Vulkan renderer.
 *
 * The native library and JNI signatures are pinned to the user-supplied original 1.2.5 APK.
 */
class VulkanRenderer(context: Context) : AutoCloseable {
    private var handle: Long

    init {
        val root = File(context.cacheDir, "vulkan-pipelines").apply { mkdirs() }
        val rendering = File(root, "rendering").apply { mkdirs() }
        handle = nativeCreate(rendering.absolutePath).also {
            check(it != 0L) { "Native Vulkan renderer creation failed" }
        }
    }

    /**
     * Original UnspektrAwesome 1.2.5 DEX JNI frame-carrier contract.
     * Exact original DEX VulkanRenderer.m instructions 0x0077..0x009f
     * prove that the FIRST two trailing ints satisfy 0 <= a < b < 121,
     * NOT that they are Camera2 RAW pixel formats. The third int is in
     * [2,17); the supplied float must be finite and its absolute value <=1.
     * These are original Lou2 cadence and Lu14 video_recording values,
     * recovered from the original 1.2.5 application DEX.
     */
    class NativeFrame125(
        // Lnu2.a: actual first sensor timestamp of the camera cadence generation.
        val frameIdentity: Long,
        // Lf03.a: optional Android PerformanceHintManager session receipt (0 if unavailable).
        val sequenceIdentity: Long,
        // Lnu2.b/c: original Lou2 cadence index and allowed per-cycle sample count.
        val originalBoundedIndex: Int,
        val originalBoundedCount: Int,
        // Ldu2.a: actual Camera2 capture sensor timestamp.
        val originalTimeNs: Long,
        // Lu14.F/G: original video_recording temporal_strength / temporal_frames.
        val originalNormalizedValue: Float,
        val originalMode: Int,
        // Ldu2.a and original app identity-hash frame presentation ticket.
        val presentationTimestampNs: Long,
        val presentationSequence: Long,
    ) {
        init {
            // The original 1.2.5 DEX VulkanRenderer.m does NOT constrain
            // signedness of these opaque 64-bit identities. Its callers use
            // identityHashCode/31-multiplication, which can wrap the sign.
            // Requiring >= 0 here would reject valid original frames before
            // JNI and recreate a black preview on some frame generations.
            require(originalBoundedIndex >= 0 && originalBoundedIndex < originalBoundedCount && originalBoundedCount < 121) {
                "1.2.5 original bounded index/count are not Camera2 RAW format codes"
            }
            require(originalNormalizedValue.isFinite() && kotlin.math.abs(originalNormalizedValue) <= 1.0f)
            require(originalMode in 2..16)
        }
    }

    /**
     * The original 1.2.5 constructor owns nativeRawUploads(nativeCreate())
     * for all frames copied into the original RAW upload pool.
     */
    private var pool125: RawUploadPool? = null

    @Synchronized
    internal fun original125Uploads(): RawUploadPool = withHandle { current ->
        pool125 ?: RawUploadPool(nativeRawUploads(current)).also { pool125 = it }
    }

    /**
     * Original RAW-upload pool is borrowed throughout the synchronous native call.
     * The Camera2 callback and the RawUpload owner must both outlive this method.
     */
    @Synchronized
    internal fun renderOriginal125(
        hardwareBuffer: HardwareBuffer?, packedRawBytes: ByteBuffer?,
        rawParameters: ByteBuffer, rawColorParameters: ByteBuffer,
        geometryParameters: ByteBuffer, spektraFilmParameters: ByteBuffer,
        lensShadingMap: ByteBuffer?, processingWidth: Int, processingHeight: Int,
        previewTimingOutput: ByteBuffer?, exposureMeterCarrier: ByteBuffer?,
        nativeUpload: RawUpload?, frame: NativeFrame125,
    ): Boolean = withHandle { current ->
        require(hardwareBuffer != null || packedRawBytes != null || nativeUpload != null) {
            "Original 1.2.5 renderer needs an acquired RAW frame"
        }
        require(processingWidth > 0 && processingHeight > 0)
        // These four exact minima are literal diagnostics embedded in the
        // user's 1.2.5 libunspektrawesome_vulkan.so, not 1.1.2 guesses.
        require(rawParameters.isDirect && rawParameters.capacity() >= 64)
        require(rawColorParameters.isDirect && rawColorParameters.capacity() >= 144)
        require(geometryParameters.isDirect && geometryParameters.capacity() >= 64)
        require(spektraFilmParameters.isDirect && spektraFilmParameters.capacity() >= 648)
        require(packedRawBytes == null || packedRawBytes.isDirect)
        require(lensShadingMap == null || lensShadingMap.isDirect)
        require(previewTimingOutput == null || (previewTimingOutput.isDirect && previewTimingOutput.capacity() >= 8))
        require(exposureMeterCarrier == null ||
            (exposureMeterCarrier.isDirect && exposureMeterCarrier.capacity() >= EXPOSURE_METER_BYTES)) {
            "Exposure-meter carrier must be a direct $EXPOSURE_METER_BYTES-byte buffer"
        }
        // All ten additional fields are supplied explicitly. No legacy
        // 1.1.2 overload, guessed native upload pointer or silent fallback.
        val callNative: (Long) -> Boolean = { uploadHandle -> nativeRender(
            current, hardwareBuffer, packedRawBytes,
            rawParameters, rawColorParameters, geometryParameters,
            spektraFilmParameters, lensShadingMap,
            processingWidth, processingHeight, previewTimingOutput,
            exposureMeterCarrier,
            frame.frameIdentity,
            uploadHandle,
            frame.sequenceIdentity,
            frame.originalBoundedIndex,
            frame.originalBoundedCount,
            frame.originalTimeNs,
            frame.originalNormalizedValue,
            frame.originalMode,
            frame.presentationTimestampNs,
            frame.presentationSequence,
        ) }
        // Keep RawUpload's monitor throughout the native call, just as the
        // original 1.2.5 readNow route brackets begin/end native access.
        if (nativeUpload != null) nativeUpload.withNativeHandle(callNative)
        else callNative(0L) // Exact original DEX's absent-RawUpload native handle
    }

    /** Actual original 1.2.5 native presentation counter, not render submission.
     * A renderer returning true does not prove any Surface image was shown. */
    @Synchronized
    internal fun presentedFrames125(): Long = withHandle { current ->
        nativePresentedFrames(current)
    }

    @Synchronized
    fun setSurface(surface: Surface?): Boolean = withHandle { current ->
        nativeSetSurface(current, surface)
    }

    /**
     * Original 1.2.5 RCD synchronous mutable ARGB_8888 bitmap capture.
     * Native descriptor is identical to the 1.1.2 version, verified in original APK.
     */
    @Synchronized
    fun captureRcd(
        hardwareBuffer: HardwareBuffer?,
        packedRawBytes: ByteBuffer?,
        rawParameters: ByteBuffer,
        rawColorParameters: ByteBuffer,
        geometryParameters: ByteBuffer,
        spektraFilmParameters: ByteBuffer,
        lensShadingMap: ByteBuffer?,
        output: Bitmap,
        spektraTimeSeconds: Double,
    ): Boolean = withHandle { current ->
        require(hardwareBuffer != null || packedRawBytes != null) { "RAW input is unavailable" }
        require(packedRawBytes == null || packedRawBytes.isDirect) { "Packed RAW bytes must be direct" }
        require(rawParameters.isDirect) { "RAW parameters must be direct" }
        require(rawColorParameters.isDirect) { "RAW color parameters must be direct" }
        require(geometryParameters.isDirect) { "Geometry parameters must be direct" }
        require(spektraFilmParameters.isDirect) { "SpektraFilm parameters must be direct" }
        require(lensShadingMap == null || lensShadingMap.isDirect) { "Lens-shading parameters must be direct" }
        require(output.isMutable && output.config == Bitmap.Config.ARGB_8888) {
            "RCD output must be a mutable ARGB_8888 Bitmap"
        }
        val nativeHardwareBuffer = if (packedRawBytes == null) hardwareBuffer else null
        nativeCaptureRcd(
            current,
            nativeHardwareBuffer,
            packedRawBytes,
            rawParameters,
            rawColorParameters,
            geometryParameters,
            spektraFilmParameters,
            lensShadingMap,
            output,
            spektraTimeSeconds,
            false,
            true,
            true,
            0,
        )
    }

    @Synchronized
    fun pollExposureMeter(target: ByteBuffer): Boolean = withHandle { current ->
        require(target.isDirect && target.capacity() >= EXPOSURE_METER_BYTES) {
            "Exposure-meter output must be a direct ByteBuffer of at least $EXPOSURE_METER_BYTES bytes"
        }
        nativePollExposureMeter(current, target)
    }

    /**
     * IRIS_26694_STANDALONE_CENTER_WEIGHTED_METER_CONTRACT
     * The first 24 bytes of the exact 1.1.2 40-byte carrier are input configuration. The native
     * renderer preserves them while publishing sequence/value at +24/+32. A freshly allocated
     * zero buffer therefore means CenterWeighted at (0,0), not the standalone default center.
     */
    fun configureCenterWeightedExposureMeter(target: ByteBuffer) {
        require(target.isDirect && target.capacity() >= EXPOSURE_METER_BYTES) {
            "Exposure-meter carrier must be a direct ByteBuffer of at least $EXPOSURE_METER_BYTES bytes"
        }
        target.order(ByteOrder.nativeOrder())
        target.putInt(EXPOSURE_METER_METHOD_OFFSET, EXPOSURE_METER_METHOD_CENTER_WEIGHTED)
        target.putFloat(EXPOSURE_METER_CENTER_X_OFFSET, EXPOSURE_METER_DEFAULT_CENTER)
        target.putFloat(EXPOSURE_METER_CENTER_Y_OFFSET, EXPOSURE_METER_DEFAULT_CENTER)
        target.position(0)
    }

    @Synchronized
    fun histogramPixels(scale: Float): IntArray = withHandle { current ->
        // IRIS_26693_NATIVE_HISTOGRAM_NULL_CONTRACT: JNI may transiently report no frame as null.
        nativeHistogramPixels(current, scale) ?: IntArray(0)
    }

    @Synchronized
    fun beginLensSwitchBlur(): Boolean = withHandle { current -> nativeBeginLensSwitchBlur(current) }

    /** Original 1.2.5 native shader warmup is hierarchical: step, then part. */
    fun warmUpStepCount(preview: Boolean): Int = nativeWarmupStepCount(preview).also {
        require(it >= 0) { "Invalid original Vulkan warmup step count" }
    }

    fun warmUpPartCount(preview: Boolean, step: Int): Int {
        require(step in 0 until warmUpStepCount(preview))
        return nativeWarmupPartCount(preview, step).also {
            require(it >= 0) { "Invalid original Vulkan warmup part count" }
        }
    }

    @Synchronized
    fun warmUp(preview: Boolean, step: Int, part: Int): Boolean = withHandle { current ->
        require(step in 0 until warmUpStepCount(preview))
        require(part in 0 until warmUpPartCount(preview, step))
        nativeWarmUp(current, preview, step, part)
    }

    @Synchronized
    fun diagnostics(): String = if (handle == 0L) {
        "Renderer is released"
    } else {
        nativeGetDiagnosticString(handle)
    }

    @Synchronized
    override fun close() {
        val current = handle
        if (current == 0L) return
        handle = 0L
        try {
            pool125?.close()
        } finally {
            pool125 = null
            nativeRelease(current)
        }
    }

    private inline fun <T> withHandle(block: (Long) -> T): T {
        check(handle != 0L) { "Renderer is released" }
        return block(handle)
    }

    private external fun nativeCreate(cachePath: String): Long
    private external fun nativeRawUploads(handle: Long): Long
    private external fun nativeSetSurface(handle: Long, surface: Surface?): Boolean
    private external fun nativeRender(
        handle: Long,
        hardwareBuffer: HardwareBuffer?,
        packedRawBytes: ByteBuffer?,
        rawParameters: ByteBuffer,
        rawColorParameters: ByteBuffer,
        geometryParameters: ByteBuffer,
        spektraFilmParameters: ByteBuffer,
        lensShadingMap: ByteBuffer?,
        processingWidth: Int,
        processingHeight: Int,
        previewTimingOutput: ByteBuffer?,
        exposureMeterCarrier: ByteBuffer?,
        originalFrameTimestampNs: Long,
        originalNativeRawUpload: Long,
        originalFrameGeneration: Long,
        originalStreamIndex: Int,
        originalPresentationFlags: Int,
        originalExposureTimeNs: Long,
        originalExposureCompensation: Float,
        originalPresentationMode: Int,
        originalPresentationTimestampNs: Long,
        originalPresentationSequence: Long,
    ): Boolean
    private external fun nativePresentedFrames(handle: Long): Long
    private external fun nativePreviewSnapshot(handle: Long, output: Bitmap): Long
    private external fun nativeLoadedPipelineCache(handle: Long): Boolean
    private external fun nativePipelineCreationStats(handle: Long): LongArray?
    private external fun nativePreparationIdentity(handle: Long): String
    private external fun nativeSetGpuPerformanceActive(handle: Long, active: Boolean)
    private external fun nativeSetVideoSurface(
        handle: Long, surface: Surface?, width: Int, height: Int, useHdr: Boolean,
    ): Boolean
    private external fun nativeVideoFrames(handle: Long): Long
    private external fun nativeHistogramBins(handle: Long, scale: Float, generation: Long): IntArray?
    private external fun nativeWarmUp(handle: Long, preview: Boolean, step: Int, mode: Int): Boolean
    private external fun nativeCaptureRcd(
        handle: Long,
        hardwareBuffer: HardwareBuffer?,
        packedRawBytes: ByteBuffer?,
        rawParameters: ByteBuffer,
        rawColorParameters: ByteBuffer,
        geometryParameters: ByteBuffer,
        spektraFilmParameters: ByteBuffer,
        lensShadingMap: ByteBuffer?,
        output: Any,
        spektraTimeSeconds: Double,
        flag0: Boolean,
        flag1: Boolean,
        flag2: Boolean,
        exportControl: Int,
    ): Boolean
    private external fun nativeGetDiagnosticString(handle: Long): String
    private external fun nativePollExposureMeter(handle: Long, target: ByteBuffer): Boolean
    private external fun nativeHistogramPixels(handle: Long, scale: Float): IntArray?
    private external fun nativeBeginLensSwitchBlur(handle: Long): Boolean
    private external fun nativeRelease(handle: Long)

    companion object {
        // In original APK DEX these three natives carry ACC_STATIC. @JvmStatic
        // on the companion external creates native methods on VulkanRenderer
        // itself (confirmed by javap), not on its synthetic Companion class.
        @JvmStatic private external fun nativeWarmupPartCount(preview: Boolean, mode: Int): Int
        @JvmStatic private external fun nativeWarmupStepCount(preview: Boolean): Int
        @JvmStatic private external fun nativeSetVideoColorSpace(surface: Surface?, useHdr: Boolean): Boolean
        const val EXPOSURE_METER_BYTES = 40
        const val EXPOSURE_METER_METHOD_OFFSET = 8
        const val EXPOSURE_METER_CENTER_X_OFFSET = 12
        const val EXPOSURE_METER_CENTER_Y_OFFSET = 16
        const val EXPOSURE_METER_METHOD_CENTER_WEIGHTED = 0
        const val EXPOSURE_METER_DEFAULT_CENTER = 0.5f
        const val EXPOSURE_METER_SEQUENCE_OFFSET = 24
        const val EXPOSURE_METER_VALUE_OFFSET = 32

        init {
            System.loadLibrary("unspektrawesome_vulkan")
        }
    }
}
