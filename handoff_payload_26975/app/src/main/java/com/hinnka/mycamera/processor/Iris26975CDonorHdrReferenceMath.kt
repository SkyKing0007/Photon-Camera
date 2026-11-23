package com.hinnka.mycamera.processor

import kotlin.math.ceil
import kotlin.math.max

/**
 * Experiment C-owned port of bjzhou's RawHdrReferenceMath neutral-response solve.
 * Pinned donor: bjzhou/PhotonCamera@0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 * The no-DCP, AdobeCurve path is deliberate: an actual DCP requires a separate
 * measured profile plan, never a guessed table. A/B rendering is not consulted.
 */
internal object Iris26975CDonorHdrReferenceMath {
    const val SAMPLES = 1024
    const val SEARCH_START = 20_000f / 65_535f
    private const val WHITE = 1f
    private const val MULTIPLIER = 1.41421356237f
    private const val MIN_INTERVAL = 1e-4f

    internal data class Extension(
        val joinInput: Float,
        val joinOutput: Float,
        val joinSlope: Float,
        val quadratic: Float,
        val whiteOutput: Float,
        val whiteSlope: Float,
        val extendsBase: Boolean,
    ) {
        fun evaluate(x: Float, base: FloatArray): Float {
            val value = if (x.isFinite()) x.coerceAtLeast(0f) else 0f
            if (value <= joinInput) return sample(base, value)
            if (value <= WHITE) {
                val d = value - joinInput
                return if (extendsBase) sample(base, value) + quadratic * d * d
                else joinOutput + joinSlope * d + quadratic * d * d
            }
            return whiteOutput + whiteSlope * (value - WHITE)
        }
    }

    /** Host reference for donor's Adobe/no-DCP neutral samples. Runtime uses a
     * measured RGBA16F GPU neutral pass, never this approximate CPU oracle. */
    fun neutralAdobeCurve(
        profileToLinearSrgbRows: FloatArray,
        profileExposure: Iris26975CDonorProfileExposure.Frozen,
    ): FloatArray {
        require(profileToLinearSrgbRows.size == 9 &&
            profileToLinearSrgbRows.all { it.isFinite() })
        val lumaRows = floatArrayOf(0.2126f, 0.7152f, 0.0722f)
        val neutralLumaScale = (0..2).sumOf { row ->
            (lumaRows[row] * (0..2).sumOf { col ->
                profileToLinearSrgbRows[row * 3 + col].toDouble()
            }.toFloat()).toDouble()
        }.toFloat()
        require(neutralLumaScale.isFinite() && neutralLumaScale > 0f)
        val acr3 = Iris26972CAdobeAcr3.samples()
        require(acr3.size == 1025)
        val tone = { input: Float ->
            if (!profileExposure.toneEnabled) input
            else if (input <= .25f) input * profileExposure.toneSlope
            else (profileExposure.toneA * input + profileExposure.toneB) * input +
                profileExposure.toneC
        }
        return FloatArray(SAMPLES) { i ->
            val x = tone(i.toFloat() / (SAMPLES - 1))
            val pos = x.coerceIn(0f, 1f) * (acr3.size - 1)
            val low = pos.toInt().coerceIn(0, acr3.lastIndex - 1)
            val alpha = pos - low
            // Donor RawEngineTonePass renders the neutral response into an
            // RGBA16F FBO BEFORE RawHdrReferenceMath.solve sees the samples.
            // Match that rounding, not the unrounded CPU ACR3 interpolation.
            quantizeHalfPositive(((acr3[low] + (acr3[low + 1] - acr3[low]) * alpha) *
                neutralLumaScale).coerceAtLeast(0f))
        }
    }

    fun solve(baseCurve: FloatArray): Extension {
        require(baseCurve.size >= 4 && baseCurve.all { it.isFinite() })
        var previous = 0f
        val curve = FloatArray(baseCurve.size) { i ->
            baseCurve[i].coerceAtLeast(previous).coerceAtLeast(0f)
                .also { previous = it }
        }
        val last = curve.lastIndex
        val baseWhite = curve[last].coerceAtLeast(1e-4f)
        val start = ceil(SEARCH_START * last).toInt().coerceIn(1, last - 1)
        val span = max(1, ((20f / 65_535f) * last).toInt())
        var join = -1
        var slopeAtJoin = 0f
        for (i in start until last) {
            val lower = (i - span).coerceAtLeast(0)
            val x = i.toFloat() / last
            val lowerX = lower.toFloat() / last
            val spacing = max(x - lowerX, MIN_INTERVAL)
            val slope = (curve[i] - curve[lower]) / spacing
            val conservativeSlope = (curve[i] - curve[lower] -
                halfFloatRoundingError(curve[i]) - halfFloatRoundingError(curve[lower])) / spacing
            val tangentAtWhite = curve[i] - halfFloatRoundingError(curve[i]) +
                conservativeSlope * (WHITE - x)
            val interval = WHITE - x
            val quadratic = (baseWhite * MULTIPLIER - curve[i] - slope * interval) /
                max(interval * interval, MIN_INTERVAL * MIN_INTERVAL)
            val whiteSlope = slope + 2f * quadratic * interval
            if (slope.isFinite() && slope >= 0f && tangentAtWhite >= baseWhite &&
                whiteSlope.isFinite() && whiteSlope >= 0f) {
                join = i
                slopeAtJoin = slope
                break
            }
        }
        if (join < 0) {
            val x = start.toFloat() / last
            val d = WHITE - x
            val q = (baseWhite * MULTIPLIER - curve[last]) / (d * d)
            return Extension(x, curve[start],
                (curve[start] - curve[start - 1]) * last, q,
                baseWhite * MULTIPLIER,
                (curve[last] - curve[last - 1]) * last + 2f * q * d, true)
        }
        val x = join.toFloat() / last
        val d = (WHITE - x).coerceAtLeast(MIN_INTERVAL)
        val whiteOutput = baseWhite * MULTIPLIER
        val q = (whiteOutput - curve[join] - slopeAtJoin * d) / (d * d)
        val whiteSlope = slopeAtJoin + 2f * q * d
        require(q.isFinite() && whiteSlope.isFinite() && whiteSlope >= 0f)
        return Extension(x, curve[join], slopeAtJoin, q, whiteOutput, whiteSlope, false)
    }

    fun sample(curve: FloatArray, x: Float): Float {
        require(curve.isNotEmpty())
        if (curve.size == 1) return curve[0].coerceAtLeast(0f)
        val position = (if (x.isFinite()) x else 0f).coerceIn(0f, 1f) * curve.lastIndex
        val index = position.toInt().coerceAtMost(curve.lastIndex - 1)
        return curve[index] + (curve[index + 1] - curve[index]) * (position - index)
    }

    /** IEEE-754 binary16 round-to-nearest-even, positive finite scene values. */
    internal fun quantizeHalfPositive(value: Float): Float {
        require(value.isFinite() && value >= 0f)
        val bits = java.lang.Float.floatToRawIntBits(value)
        val exponent = ((bits ushr 23) and 255) - 127 + 15
        val mantissa = bits and 0x7fffff
        val half = when {
            exponent >= 31 -> 0x7bff // largest finite half; source would overflow F16
            exponent <= -10 -> 0
            exponent <= 0 -> {
                val shifted = mantissa or 0x800000
                val amount = 14 - exponent
                val truncated = shifted ushr amount
                val remainder = shifted and ((1 shl amount) - 1)
                val tie = 1 shl (amount - 1)
                truncated + if (remainder > tie ||
                    (remainder == tie && (truncated and 1) != 0)) 1 else 0
            }
            else -> {
                val rounded = mantissa + 0xfff + ((mantissa ushr 13) and 1)
                (exponent shl 10) + (rounded ushr 13)
            }
        }
        val e = (half ushr 10) and 31
        val fraction = half and 1023
        return when(e) {
            0 -> Math.scalb(fraction.toFloat(),-24)
            31 -> 65504f
            else -> Math.scalb(1f + fraction / 1024f,e-15)
        }
    }

    private fun halfFloatRoundingError(v: Float): Float =
        max(Math.ulp(v) * 4096f, 1f / 33_554_432f)
}
