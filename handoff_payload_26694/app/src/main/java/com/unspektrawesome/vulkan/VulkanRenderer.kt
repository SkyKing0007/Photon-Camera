package com.unspektrawesome.vulkan

import android.content.Context
import android.graphics.Bitmap
import android.hardware.HardwareBuffer
import android.view.Surface
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Iris host wrapper for the exact Unspektrawesome 1.1.2 native renderer.
 *
 * The JNI class/package and native descriptors intentionally match the audited 1.1.2 APK so the
 * original libunspektrawesome_vulkan.so can remain byte-identical.
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

    @Synchronized
    fun setSurface(surface: Surface?): Boolean = withHandle { current ->
        nativeSetSurface(current, surface)
    }

    /**
     * Preview path. Packed RAW follows the 1.1.2 ByteBuffer route; RAW_SENSOR may use the borrowed
     * HardwareBuffer. The final 40-byte buffer is the exact 1.1.2 exposure-meter carrier.
     */
    @Synchronized
    fun render(
        hardwareBuffer: HardwareBuffer?,
        packedRawBytes: ByteBuffer?,
        rawParameters: ByteBuffer,
        rawColorParameters: ByteBuffer,
        geometryParameters: ByteBuffer,
        spektraFilmParameters: ByteBuffer,
        lensShadingMap: ByteBuffer?,
        processingWidth: Int,
        processingHeight: Int,
        previewTimingOutput: ByteBuffer? = null,
        exposureMeterCarrier: ByteBuffer? = null,
    ): Boolean = withHandle { current ->
        require(hardwareBuffer != null || packedRawBytes != null) { "RAW input is unavailable" }
        require(packedRawBytes == null || packedRawBytes.isDirect) { "Packed RAW bytes must be direct" }
        require(rawParameters.isDirect) { "RAW parameters must be direct" }
        require(rawColorParameters.isDirect) { "RAW color parameters must be direct" }
        require(geometryParameters.isDirect) { "Geometry parameters must be direct" }
        require(spektraFilmParameters.isDirect) { "SpektraFilm parameters must be direct" }
        require(lensShadingMap == null || lensShadingMap.isDirect) { "Lens-shading parameters must be direct" }
        require(previewTimingOutput == null || (previewTimingOutput.isDirect && previewTimingOutput.capacity() >= 8)) {
            "Preview timing output must be a direct ByteBuffer of at least 8 bytes"
        }
        require(exposureMeterCarrier == null ||
            (exposureMeterCarrier.isDirect && exposureMeterCarrier.capacity() >= EXPOSURE_METER_BYTES)) {
            "Exposure-meter carrier must be a direct ByteBuffer of at least $EXPOSURE_METER_BYTES bytes"
        }
        val nativeHardwareBuffer = if (packedRawBytes == null) hardwareBuffer else null
        nativeRender(
            current,
            nativeHardwareBuffer,
            packedRawBytes,
            rawParameters,
            rawColorParameters,
            geometryParameters,
            spektraFilmParameters,
            lensShadingMap,
            processingWidth,
            processingHeight,
            previewTimingOutput,
            exposureMeterCarrier,
        )
    }

    /**
     * Full-resolution saved path. 1.1.2 writes directly into a mutable ARGB_8888 Bitmap and the
     * production Process-now call uses trailing controls false/true/true/0.
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

    /** Optional non-blocking warmup primitive; 26689 never gates camera opening on warmup. */
    @Synchronized
    fun warmUp(preview: Boolean, step: Int): Boolean = withHandle { current ->
        nativeWarmUp(current, preview, step)
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
        nativeRelease(current)
    }

    private inline fun <T> withHandle(block: (Long) -> T): T {
        check(handle != 0L) { "Renderer is released" }
        return block(handle)
    }

    private external fun nativeCreate(cachePath: String): Long
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
    ): Boolean
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
    private external fun nativeWarmUp(handle: Long, preview: Boolean, step: Int): Boolean
    private external fun nativePollExposureMeter(handle: Long, target: ByteBuffer): Boolean
    private external fun nativeHistogramPixels(handle: Long, scale: Float): IntArray?
    private external fun nativeBeginLensSwitchBlur(handle: Long): Boolean
    private external fun nativeRelease(handle: Long)

    companion object {
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
