package com.hinnka.mycamera.processor

import kotlin.math.abs
import kotlin.math.ln
import kotlin.math.exp
import kotlin.math.pow

/**
 * Independent C-only numerical port of bjzhou/hdr/RawGainmapMath and the
 * GpuReferenceGainmapProducer RAW luminance-residual transfer.
 * Pinned: bjzhou/PhotonCamera@0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * The sidecar is MANDATORY for the donor's RAW GPU producer. A missing LUT
 * luminance sidecar is an error, never an implicit gain of 1.0. The runtime
 * renderer and JPEG/R boundary MUST source that sidecar from the actual
 * before/after donor LUT stack, not fabricate one from already-clipped SDR.
 * This file defines/test-drives the math; it does not yet wire the producer.
 */
internal object Iris26975CDonorGainmapMath {
    const val DOWNSAMPLE = 2
    const val MIN_GAIN_RATIO = .25f
    const val MAX_GAIN_RATIO = 4f
    const val OFFSET = 1e-4f
    const val MIN_STRENGTH = .25f
    const val MAX_STRENGTH = 2f
    private const val LUMA_R = .2126f
    private const val LUMA_G = .7152f
    private const val LUMA_B = .0722f

    fun srgbToLinear(value: Float): Float {
        val magnitude = abs(value)
        val linearMagnitude = if (magnitude <= .04045f) magnitude / 12.92f
            else ((magnitude + .055f) / 1.055f).pow(2.4f)
        return if (value < 0f) -linearMagnitude else linearMagnitude
    }

    fun linearLuma(r: Float, g: Float, b: Float): Float =
        LUMA_R * r + LUMA_G * g + LUMA_B * b

    fun computeLutLuminanceGain(sdrBeforeLutLuma: Float, sdrAfterLutLuma: Float,
        offset: Float = OFFSET): Float {
        val safeBefore = sdrBeforeLutLuma.coerceAtLeast(0f)
        val safeAfter = sdrAfterLutLuma.coerceAtLeast(0f)
        return (safeAfter + offset) / (safeBefore + offset)
    }

    fun applyLutLuminanceGain(lutLuminanceGain: Float, hdrReferenceLuma: Float,
        offset: Float = OFFSET): Float {
        val safeHdr = hdrReferenceLuma.coerceAtLeast(0f)
        val safeGain = lutLuminanceGain.coerceAtLeast(0f)
        return ((safeHdr + offset) * safeGain - offset).coerceAtLeast(0f)
    }

    /** Return the donor's 0..1 encoded alpha for an RGBA_F16 RAW HDR reference. */
    fun encodeLuminance(sdrEncodedRgb: FloatArray, hdrLinearRgb: FloatArray,
        lutLuminanceGain: Float, strength: Float = 1f,
        minGainRatio: Float = MIN_GAIN_RATIO,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET): Float {
        require(sdrEncodedRgb.size >= 3 && hdrLinearRgb.size >= 3)
        require(lutLuminanceGain.isFinite() && lutLuminanceGain >= 0f)
        require(strength.isFinite() && strength in MIN_STRENGTH..MAX_STRENGTH)
        require(minGainRatio.isFinite() && minGainRatio > 0f &&
            maxGainRatio.isFinite() && maxGainRatio > minGainRatio &&
            offset.isFinite() && offset > 0f)
        val sdrLuma = linearLuma(srgbToLinear(sdrEncodedRgb[0]),
            srgbToLinear(sdrEncodedRgb[1]), srgbToLinear(sdrEncodedRgb[2]))
        val hdrLuma = linearLuma(hdrLinearRgb[0].coerceAtLeast(0f),
            hdrLinearRgb[1].coerceAtLeast(0f), hdrLinearRgb[2].coerceAtLeast(0f))
        val targetHdrLuma = applyLutLuminanceGain(lutLuminanceGain,hdrLuma,offset)
        val candidateRatio = ((targetHdrLuma + offset) / (sdrLuma + offset))
            .coerceIn(minGainRatio, maxGainRatio)
        val strengthRatio = (1f + (candidateRatio - 1f)*strength)
            .coerceIn(minGainRatio,maxGainRatio)
        return ((ln(strengthRatio) - ln(minGainRatio)) /
            (ln(maxGainRatio) - ln(minGainRatio))).coerceIn(0f,1f)
    }

    fun reconstructLinear(sdrEncoded: Float, encodedGain: Float,
        minGainRatio: Float = MIN_GAIN_RATIO,
        maxGainRatio: Float = MAX_GAIN_RATIO,
        offset: Float = OFFSET): Float {
        val logGain = ln(minGainRatio) +
            (ln(maxGainRatio) - ln(minGainRatio)) * encodedGain.coerceIn(0f,1f)
        return (srgbToLinear(sdrEncoded) + offset) * exp(logGain) - offset
    }
}
