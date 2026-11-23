// Experiment C-only Sabre RAW finishing. No A/B Spatial, user-adjustment,
// VGN, Iris residual map, or alternate denoising entry is callable here.
// The MGC static kernels are universal native math; JNI ownership is C-only.
// This does NOT by itself certify bjzhou's later low-frequency chroma parity.
package com.hinnka.mycamera.raw

import android.content.Context
import com.hinnka.mycamera.utils.PLog
import java.nio.ByteBuffer

/** Sabre-only, donor-tuned RAW full-resolution denoise boundary for Experiment C. */
internal object Iris26975CIndependentDenoise {
    private const val TAG = "Iris26975CIndependentDenoise"
    private const val SABRE_LUMA_TUNING_ASSET = "mgc_denoise/sabre_luma_denoise.binarypb"
    private const val CHROMA_TUNING_ASSET = "mgc_denoise/chroma_denoise.binarypb"

    data class Tuning(
        val strength: FloatArray,
        val revertFactor: FloatArray,
        val outlierDistance: FloatArray,
    )

    private data class TuningPoint(val snr: Float, val tuning: Tuning)

    @Volatile private var initialized = false
    @Volatile private var initializationFailed = false
    private var sabreLumaTuningPoints: List<TuningPoint> = emptyList()
    private var chromaTuningPoints: List<TuningPoint> = emptyList()

    @Synchronized
    fun ensureInitialized(context: Context): Boolean {
        if (initialized) return true
        if (initializationFailed) return false
        return runCatching {
            val assets = context.applicationContext.assets
            sabreLumaTuningPoints = assets.open(SABRE_LUMA_TUNING_ASSET)
                .use { parseTuning(it.readBytes()) }
            chromaTuningPoints = assets.open(CHROMA_TUNING_ASSET)
                .use { parseTuning(it.readBytes()) }
            check(sabreLumaTuningPoints.size >= 2 && chromaTuningPoints.size >= 2) {
                "Incomplete donor Sabre luma/chroma SNR protobuf tuning"
            }
            initialized = true
            PLog.i(TAG, "C Sabre denoise tuning initialized: " +
                "lumaSnr=${sabreLumaTuningPoints.map { it.snr }} " +
                "chromaSnr=${chromaTuningPoints.map { it.snr }}")
            true
        }.onFailure { error ->
            initializationFailed = true
            PLog.e(TAG, "Donor Sabre tuning initialization failed", error)
        }.getOrDefault(false)
    }

    /**
     * Consumes ONLY Sabre's per-frame-merged normalized camera-RGB read/shot
     * model and 128-bin spectrum. No fallback profiles, Spatial residual,
     * fabricated Q8 strength map, or alternate processing mode is admitted.
     * Native C bridge signature remains private to Experiment C.
     */
    fun denoise(
        rgba16f: ByteBuffer,
        width: Int,
        height: Int,
        globalOriginX: Int,
        globalOriginY: Int,
        fullWidth: Int,
        fullHeight: Int,
        metadata: com.hinnka.mycamera.processor.experimentc.Iris26975CSabreDenoiseMetadata,
        tuningSnr: Float,
        lumaStrengthScale: Float,
        chromaStrengthScale: Float,
    ): Boolean {
        // Fixed user-approved 26975 settings. A future adjustable UI must use
        // an explicit new C contract, not silently fall into an Iris branch.
        if (lumaStrengthScale != 0f || chromaStrengthScale != 1f ||
            !initialized || !rgba16f.isDirect || width <= 0 || height <= 0 ||
            fullWidth != width || fullHeight != height ||
            globalOriginX != 0 || globalOriginY != 0 ||
            width.toLong() * height.toLong() * 8L > rgba16f.capacity().toLong() ||
            !tuningSnr.isFinite() || tuningSnr < 0f) {
            PLog.e(TAG, "Rejected non-Sabre/non-native-grid denoise or invalid settings")
            return false
        }
        val rgbRead = metadata.mgcDenoiseReadNoise?.copyOf()
        val rgbShot = metadata.mgcDenoiseShotNoise?.copyOf()
        val correlation = metadata.mgcDenoiseCorrelation?.copyOf()
        if (!validRgbNoise(rgbRead) || !validRgbNoise(rgbShot) ||
            (rgbRead!!.none { it > 0f } && rgbShot!!.none { it > 0f }) ||
            !validCorrelation(correlation)) {
            PLog.e(TAG, "Missing/invalid donor Sabre merged noise or forbidden Iris noise inputs")
            return false
        }
        val lensShading = metadata.lensShadingMap
        if (lensShading != null && !hasValidLensShadingMap(metadata)) {
            PLog.e(TAG, "Invalid optional physical-lens shading map")
            return false
        }
        val rgbWhiteBalance = normalizedRgbWhiteBalance(metadata.whiteBalanceGains)
        val lumaTuning = interpolateTuning(tuningSnr, sabreLumaTuningPoints)
        val chromaTuning = interpolateTuning(tuningSnr, chromaTuningPoints)
        val moire = metadata.cfaPattern in 0..3
        rgba16f.clear()
        val result = nativeDenoiseRgba16f(
            rgbaBuffer = rgba16f,
            width = width,
            height = height,
            globalOriginX = 0,
            globalOriginY = 0,
            fullWidth = width,
            fullHeight = height,
            inputIsBayer = false,
            cfaPattern = metadata.cfaPattern,
            measureMoireEnabled = moire,
            applyLensShadingInBayerAot = false,
            lensShading = lensShading,
            lensWidth = if (lensShading == null) 0 else metadata.lensShadingMapWidth,
            lensHeight = if (lensShading == null) 0 else metadata.lensShadingMapHeight,
            normalizedRgbShot = rgbShot!!,
            normalizedRgbRead = rgbRead!!,
            normalizedRgbWhiteBalance = rgbWhiteBalance,
            preparedNormalizedYuvRead = null,
            preparedNormalizedLumaShot = 0f,
            preparedNormalizedLumaQuadratic = 0f,
            preparedNormalizedChromaShot = 0f,
            preparedNormalizedChromaQuadratic = 0f,
            lumaCorrelation = correlation,
            chromaCorrelation = correlation,
            spatialStrengthQ8 = null,
            spatialStrengthWidth = 0,
            spatialStrengthHeight = 0,
            lumaEnabled = false,
            chromaEnabled = true,
            lumaStrength = FloatArray(5) { 0f },
            lumaOutlierDistance = lumaTuning.outlierDistance,
            lumaRevertFactor = lumaTuning.revertFactor,
            chromaStrength = chromaTuning.strength,
            chromaOutlierThreshold = chromaTuning.outlierDistance,
            diagnosticsEnabled = false,
        )
        rgba16f.position(0)
        if (result != 0) {
            PLog.e(TAG, "Donor Sabre chroma-only native kernel failed: code=$result")
            return false
        }
        PLog.d(TAG, "C Sabre native full-resolution chroma=1 luma=0 " +
            "snr=$tuningSnr size=${width}x$height " +
            "lensShading=${lensShading != null} mergedSpectrum=128")
        return true
    }

    private fun validRgbNoise(values: FloatArray?): Boolean =
        values?.let { it.size == 3 && it.all { x -> x.isFinite() && x >= 0f } } == true

    private fun validCorrelation(values: FloatArray?): Boolean =
        values?.let { it.size == 128 && it.all { x -> x.isFinite() && x >= 0f } } == true

    private fun hasValidLensShadingMap(metadata: com.hinnka.mycamera.processor.experimentc.Iris26975CSabreDenoiseMetadata): Boolean {
        val map = metadata.lensShadingMap ?: return false
        val expectedSize = metadata.lensShadingMapWidth.toLong() *
            metadata.lensShadingMapHeight.toLong() * 4L
        return metadata.lensShadingMapWidth > 0 && metadata.lensShadingMapHeight > 0 &&
            expectedSize in 1L..Int.MAX_VALUE.toLong() && map.size == expectedSize.toInt() &&
            map.all { it.isFinite() && it > 0f }
    }

    private fun normalizedRgbWhiteBalance(gains: FloatArray): FloatArray {
        fun safeGain(index: Int, fallback: Float): Float {
            val value = gains.getOrElse(index) { fallback }
            return value.takeIf { it.isFinite() && it > 0f } ?: fallback
        }
        val greenEven = safeGain(1, 1f)
        val greenOdd = safeGain(2, greenEven)
        val green = (0.5f * (greenEven + greenOdd))
            .takeIf { it.isFinite() && it > 0f }
            ?: 1f
        return floatArrayOf(
            (safeGain(0, green) / green).coerceIn(1e-3f, 64f),
            1f,
            (safeGain(3, green) / green).coerceIn(1e-3f, 64f),
        )
    }

    /**
     * Mechanically retained from pinned bjzhou MgcFullResolutionDenoise.interpolateTuning
     * (Git blob c39feafd3fcb1759f49ba43d9f02eedd1068b4a0).
     * V25 selects the STRICTLY GREATER upper node, then multiplies both source
     * nodes before adding.  The previous Iris delta-formula had different binary32
     * rounding and different exact-node tie handling. Native MGC consumes these
     * coefficients directly, so do not algebraically simplify this expression.
     */
    private fun interpolateTuning(
        snr: Float,
        points: List<TuningPoint>,
    ): Tuning {
        val finiteSnr = snr.takeIf { it.isFinite() && it >= 0f }
            ?: points.first().snr
        val upperIndex = points.indexOfFirst { it.snr > finiteSnr }
        if (upperIndex < 0) return points.last().tuning.copyArrays()
        if (upperIndex == 0) return points.first().tuning.copyArrays()
        val lower = points[upperIndex - 1]
        val upper = points[upperIndex]
        val amount = (
            (finiteSnr - lower.snr) /
                (upper.snr - lower.snr)
            ).coerceIn(0f, 1f)
        val lowerAmount = 1f - amount
        fun interpolate(
            first: FloatArray,
            second: FloatArray,
        ): FloatArray = FloatArray(5) { index ->
            // libgcastartup 0x54b3794..0x54b37ac: two FMULs, then FADD (not FMADD).
            lowerAmount * first[index] + second[index] * amount
        }
        return Tuning(
            strength = interpolate(
                lower.tuning.strength,
                upper.tuning.strength,
            ),
            revertFactor = interpolate(
                lower.tuning.revertFactor,
                upper.tuning.revertFactor,
            ),
            outlierDistance = interpolate(
                lower.tuning.outlierDistance,
                upper.tuning.outlierDistance,
            ),
        )
    }

    private fun Tuning.copyArrays(): Tuning = Tuning(
        strength.copyOf(),
        revertFactor.copyOf(),
        outlierDistance.copyOf(),
    )

    private class ProtoReader(
        private val bytes: ByteArray,
        private var position: Int = 0,
        private val limit: Int = bytes.size,
    ) {
        fun hasRemaining(): Boolean = position < limit

        fun readTag(): Pair<Int, Int> {
            val tag = readVarint().toInt()
            return (tag ushr 3) to (tag and 7)
        }

        fun readMessage(): ProtoReader {
            val length = readVarint().toInt()
            require(length >= 0 && position + length <= limit)
            val child = ProtoReader(bytes, position, position + length)
            position += length
            return child
        }

        fun readFixed32Float(): Float {
            require(position + 4 <= limit)
            val bits =
                (bytes[position].toInt() and 0xff) or
                    ((bytes[position + 1].toInt() and 0xff) shl 8) or
                    ((bytes[position + 2].toInt() and 0xff) shl 16) or
                    ((bytes[position + 3].toInt() and 0xff) shl 24)
            position += 4
            return Float.fromBits(bits)
        }

        fun skip(wireType: Int) {
            when (wireType) {
                0 -> readVarint()
                1 -> position += 8
                2 -> position += readVarint().toInt()
                5 -> position += 4
                else -> error("Unsupported protobuf wire type $wireType")
            }
            require(position <= limit)
        }

        private fun readVarint(): Long {
            var result = 0L
            var shift = 0
            while (shift < 64) {
                require(position < limit)
                val value = bytes[position++].toInt() and 0xff
                result = result or ((value and 0x7f).toLong() shl shift)
                if (value and 0x80 == 0) return result
                shift += 7
            }
            error("Malformed protobuf varint")
        }
    }

    private fun parseTuning(bytes: ByteArray): List<TuningPoint> {
        val result = ArrayList<TuningPoint>()
        val root = ProtoReader(bytes)
        while (root.hasRemaining()) {
            val (field, wire) = root.readTag()
            if (field != 1 || wire != 2) {
                root.skip(wire)
                continue
            }
            val point = root.readMessage()
            val strength = ArrayList<Float>(5)
            val revert = ArrayList<Float>(5)
            val outlier = ArrayList<Float>(5)
            var snr: Float? = null
            while (point.hasRemaining()) {
                val (pointField, pointWire) = point.readTag()
                when {
                    pointField == 1 && pointWire == 2 -> {
                        val level = point.readMessage()
                        var levelStrength = 0f
                        var levelRevert = 0f
                        var levelOutlier = 0f
                        while (level.hasRemaining()) {
                            val (levelField, levelWire) = level.readTag()
                            if (levelWire != 5) {
                                level.skip(levelWire)
                                continue
                            }
                            when (levelField) {
                                1 -> levelStrength = level.readFixed32Float()
                                2 -> levelRevert = level.readFixed32Float()
                                3 -> levelOutlier = level.readFixed32Float()
                                else -> level.skip(levelWire)
                            }
                        }
                        strength += levelStrength
                        revert += levelRevert
                        outlier += levelOutlier
                    }

                    pointField == 2 && pointWire == 2 -> {
                        val snrMessage = point.readMessage()
                        while (snrMessage.hasRemaining()) {
                            val (snrField, snrWire) = snrMessage.readTag()
                            if (snrField == 1 && snrWire == 5) {
                                snr = snrMessage.readFixed32Float()
                            } else {
                                snrMessage.skip(snrWire)
                            }
                        }
                    }

                    else -> point.skip(pointWire)
                }
            }
            require(strength.size == 5 && revert.size == 5 && outlier.size == 5)
            val pointSnr = requireNotNull(snr)
            result += TuningPoint(
                snr = pointSnr,
                tuning = Tuning(
                    strength.toFloatArray(),
                    revert.toFloatArray(),
                    outlier.toFloatArray(),
                ),
            )
        }
        return result.sortedBy(TuningPoint::snr)
    }

    private external fun nativeDenoiseRgba16f(
        rgbaBuffer: ByteBuffer,
        width: Int,
        height: Int,
        globalOriginX: Int,
        globalOriginY: Int,
        fullWidth: Int,
        fullHeight: Int,
        inputIsBayer: Boolean,
        cfaPattern: Int,
        measureMoireEnabled: Boolean,
        applyLensShadingInBayerAot: Boolean,
        lensShading: FloatArray?,
        lensWidth: Int,
        lensHeight: Int,
        normalizedRgbShot: FloatArray,
        normalizedRgbRead: FloatArray,
        normalizedRgbWhiteBalance: FloatArray,
        preparedNormalizedYuvRead: FloatArray?,
        preparedNormalizedLumaShot: Float,
        preparedNormalizedLumaQuadratic: Float,
        preparedNormalizedChromaShot: Float,
        preparedNormalizedChromaQuadratic: Float,
        lumaCorrelation: FloatArray?,
        chromaCorrelation: FloatArray?,
        spatialStrengthQ8: ShortArray?,
        spatialStrengthWidth: Int,
        spatialStrengthHeight: Int,
        lumaEnabled: Boolean,
        chromaEnabled: Boolean,
        lumaStrength: FloatArray,
        lumaOutlierDistance: FloatArray,
        lumaRevertFactor: FloatArray,
        chromaStrength: FloatArray,
        chromaOutlierThreshold: FloatArray,
        diagnosticsEnabled: Boolean,
    ): Int
}
