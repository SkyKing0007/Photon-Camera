package com.hinnka.mycamera.processor.experimentc.original129.hdr

import kotlin.math.ln
import kotlin.math.pow
import kotlin.math.abs

internal object RawGainmapMath {
    const val DOWNSAMPLE = 2
    const val MIN_GAIN_RATIO = 1.0f
    const val MAX_GAIN_RATIO = 2.0f
    const val OFFSET = 1e-4f

    private const val LUMA_R = 0.2126f
    private const val LUMA_G = 0.7152f
    private const val LUMA_B = 0.0722f

    fun srgbToLinear(value: Float): Float {
        val magnitude = abs(value)
        val linearMagnitude = if (magnitude <= 0.04045f) {
            magnitude / 12.92f
        } else {
            ((magnitude + 0.055f) / 1.055f).pow(2.4f)
        }
        return if (value < 0f) -linearMagnitude else linearMagnitude
    }

    fun encode(
        sdrEncoded: Float,
        hdrLinear: Float,
        strength: Float = HdrGainmapStrength.DEFAULT,
        minGainRatio: Float = MIN_GAIN_RATIO,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET,
    ): Float {
        val sdrLinear = srgbToLinear(sdrEncoded)
        val strengthRatio = highlightGainRatio(sdrLinear, hdrLinear, strength, maxGainRatio, offset)
        return ((ln(strengthRatio) - ln(minGainRatio)) / (ln(maxGainRatio) - ln(minGainRatio)))
            .coerceIn(0f, 1f)
    }

    fun encodeLuminance(
        sdrEncodedRgb: FloatArray,
        hdrLinearRgb: FloatArray,
        lutLuminanceGain: Float? = null,
        strength: Float = HdrGainmapStrength.DEFAULT,
        minGainRatio: Float = MIN_GAIN_RATIO,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET,
    ): Float {
        require(sdrEncodedRgb.size >= 3 && hdrLinearRgb.size >= 3) {
            "SDR and HDR RGB inputs must contain at least three channels"
        }
        val sdrLuma = linearLuma(
            srgbToLinear(sdrEncodedRgb[0]),
            srgbToLinear(sdrEncodedRgb[1]),
            srgbToLinear(sdrEncodedRgb[2]),
        )
        val hdrLuma = linearLuma(
            hdrLinearRgb[0].coerceAtLeast(0f),
            hdrLinearRgb[1].coerceAtLeast(0f),
            hdrLinearRgb[2].coerceAtLeast(0f),
        )
        val targetHdrLuma = lutLuminanceGain?.let { gain ->
            applyLutLuminanceGain(gain, hdrLuma, offset)
        } ?: hdrLuma
        val strengthRatio = highlightGainRatio(sdrLuma, targetHdrLuma, strength, maxGainRatio, offset)
        return ((ln(strengthRatio) - ln(minGainRatio)) /
            (ln(maxGainRatio) - ln(minGainRatio))).coerceIn(0f, 1f)
    }

    // C OFF only: preserve the encoded SDR base, and consume only genuine
    // linear HDR headroom above reference white. Match the GPU shader exactly.
    private fun smoothStep(low: Float, high: Float, value: Float): Float {
        val t = ((value - low) / (high - low)).coerceIn(0f, 1f)
        return t * t * (3f - 2f * t)
    }

    internal fun highlightGainRatio(
        sdrLuma: Float,
        targetHdrLuma: Float,
        strength: Float,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET,
    ): Float {
        val safeSdr = sdrLuma.coerceAtLeast(0f)
        val excess = (targetHdrLuma - 1f).coerceAtLeast(0f)
        val highlightWeight = smoothStep(0.40f, 0.80f, safeSdr)
        val headroomWeight = smoothStep(0f, 0.50f, excess)
        val normalizedStrength = HdrGainmapStrength.coerce(strength)
        val capacity = maxGainRatio - 1f
        val weightedExcess = excess / (safeSdr + offset) * normalizedStrength
        // A rational soft ceiling, not a hard threshold/plateau. The boost
        // never exceeds either the measured excess or the advertised capacity.
        val boundedBoost = capacity * weightedExcess /
            (capacity * (1f + normalizedStrength) + weightedExcess)
        return 1f + highlightWeight * headroomWeight * boundedBoost
    }

    fun linearLuma(r: Float, g: Float, b: Float): Float =
        LUMA_R * r + LUMA_G * g + LUMA_B * b

    fun computeLutLuminanceGain(
        sdrBeforeLutLuma: Float,
        sdrAfterLutLuma: Float,
        offset: Float = OFFSET,
    ): Float {
        val safeBeforeLut = sdrBeforeLutLuma.coerceAtLeast(0f)
        val safeAfterLut = sdrAfterLutLuma.coerceAtLeast(0f)
        return (safeAfterLut + offset) / (safeBeforeLut + offset)
    }

    fun applyLutLuminanceGain(
        lutLuminanceGain: Float,
        hdrReferenceLuma: Float,
        offset: Float = OFFSET,
    ): Float {
        val safeHdr = hdrReferenceLuma.coerceAtLeast(0f)
        val lutGain = lutLuminanceGain.coerceAtLeast(0f)
        // The sidecar is (SDR_after + offset) / (SDR_before + offset).
        // Applying it to the complete reference preserves the RAW HDR/SDR ratio.
        // Splitting at absolute white changes that ratio according to the LUT gain
        // and can make a darker branch brighter than the surrounding sky.
        return ((safeHdr + offset) * lutGain - offset).coerceAtLeast(0f)
    }

    fun reconstructLinear(
        sdrEncoded: Float,
        encodedGain: Float,
        minGainRatio: Float = MIN_GAIN_RATIO,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET,
    ): Float {
        val logGain = ln(minGainRatio) +
            (ln(maxGainRatio) - ln(minGainRatio)) * encodedGain.coerceIn(0f, 1f)
        return (srgbToLinear(sdrEncoded) + offset) * kotlin.math.exp(logGain) - offset
    }

}
