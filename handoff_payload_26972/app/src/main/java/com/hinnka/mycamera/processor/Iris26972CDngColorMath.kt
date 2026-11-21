package com.hinnka.mycamera.processor

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Experiment C only: isolated, shutter-frozen DNG dual-illuminant color math.
 *
 * The forward matrices are camera-reference RGB -> XYZ D50. The complete DNG
 * transform below consumes unbalanced camera RGB; donor Sabre Resolve has
 * *already* multiplied its output by its actual three final gains. Undo precisely
 * those applied gains as part of the matrix, rather than applying AWB again.
 * Lens-shading correction is NOT undone here. Everything is row-major.
 *
 * Equations follow DNG ForwardMatrix/CalibrationMatrix mechanics used by the
 * successful 26971 Converter, but this is a new standalone C-only implementation;
 * no changes to A/B color classes, DNG writer, or global settings.
 */
internal object Iris26972CDngColorMath {
    private const val COMPONENT = "26972 C frozen dual-illuminant color"
    private val d50 = doubleArrayOf(0.9642, 1.0, 0.8249)
    private val xyzToProphoto = doubleArrayOf(
        1.345753, -0.255603, -0.051025,
        -0.544426, 1.508096, 0.020472,
        0.0, 0.0, 1.211968,
    )
    private val xyzToLinearSrgb = doubleArrayOf(
        3.1338561, -1.6168667, -0.4906146,
        -0.9787684, 1.9161415, 0.0334540,
        0.0719453, -0.2289914, 1.4052427,
    )
    private val prophotoToXyz = doubleArrayOf(
        0.797779, 0.135213, 0.031303,
        0.288000, 0.711900, 0.000100,
        0.000000, 0.000000, 0.825105,
    )

    /** All matrix buffers must originate from the *actual physical lens* characteristics. */
    internal class Inputs(
        val colorMatrix1: FloatArray,
        val colorMatrix2: FloatArray,
        val calibrationMatrix1: FloatArray,
        val calibrationMatrix2: FloatArray,
        val forwardMatrix1: FloatArray,
        val forwardMatrix2: FloatArray,
        val neutralCamera: FloatArray,
        /** Actual, shutter-frozen ResolveSabre uFinalGains, NOT requested AWB. */
        val appliedDonorRgbGains: FloatArray,
        val illuminant1Kelvin: Int,
        val illuminant2Kelvin: Int,
    )

    internal class Solved internal constructor(
        sensorToProfile: FloatArray,
        profileToLinearSrgb: FloatArray,
        val interpolation: Double,
    ) {
        private val sensorToProfileValue = sensorToProfile.copyOf()
        private val profileToSrgbValue = profileToLinearSrgb.copyOf()
        val sensorToProfile: FloatArray get() = sensorToProfileValue.copyOf()
        val profileToLinearSrgb: FloatArray get() = profileToSrgbValue.copyOf()
    }

    private fun checkedMatrix(values: FloatArray, label: String): DoubleArray {
        require(values.size == 9 && values.all { it.isFinite() && abs(it) <= 100f }) {
            "$COMPONENT invalid real $label matrix"
        }
        val d = DoubleArray(9) { values[it].toDouble() }
        invert(d)
        return d
    }

    private fun multiply(a: DoubleArray, b: DoubleArray): DoubleArray = DoubleArray(9) { idx ->
        val row = idx / 3
        val col = idx % 3
        a[row * 3] * b[col] + a[row * 3 + 1] * b[3 + col] +
            a[row * 3 + 2] * b[6 + col]
    }

    private fun map(a: DoubleArray, v: DoubleArray): DoubleArray = DoubleArray(3) { row ->
        a[row * 3] * v[0] + a[row * 3 + 1] * v[1] + a[row * 3 + 2] * v[2]
    }

    private fun mix(a: DoubleArray, b: DoubleArray, f: Double): DoubleArray =
        DoubleArray(9) { a[it] * (1.0 - f) + b[it] * f }

    private fun invert(m: DoubleArray): DoubleArray {
        val a = m[0]; val b = m[1]; val c = m[2]
        val d = m[3]; val e = m[4]; val f = m[5]
        val g = m[6]; val h = m[7]; val i = m[8]
        val adj = doubleArrayOf(e * i - f * h, c * h - b * i, b * f - c * e,
            f * g - d * i, a * i - c * g, c * d - a * f,
            d * h - e * g, b * g - a * h, a * e - b * d)
        val det = a * adj[0] + b * adj[3] + c * adj[6]
        require(det.isFinite() && abs(det) > 1e-9) { "$COMPONENT singular DNG matrix" }
        val out = DoubleArray(9) { adj[it] / det }
        require(out.all { it.isFinite() && abs(it) <= 1000.0 }) {
            "$COMPONENT ill-conditioned DNG matrix"
        }
        return out
    }

    private fun normalizedForward(source: DoubleArray): DoubleArray {
        val white = map(source, doubleArrayOf(1.0, 1.0, 1.0))
        require(white.all { it.isFinite() && it > 1e-6 }) {
            "$COMPONENT invalid white axis in ForwardMatrix"
        }
        return DoubleArray(9) { idx ->
            source[idx] * d50[idx / 3] / white[idx / 3]
        }
    }

    private fun chromaticTemperature(xyz: DoubleArray): Double {
        val sum = xyz.sum()
        require(sum.isFinite() && sum > 1e-8) { "$COMPONENT invalid illuminant XYZ" }
        val x = xyz[0] / sum
        val y = xyz[1] / sum
        val denominator = y - 0.1858
        require(abs(denominator) > 1e-6) { "$COMPONENT invalid chromaticity" }
        val n = (x - 0.332) / denominator
        val kelvin = -449.0 * n * n * n + 3525.0 * n * n - 6823.3 * n + 5520.33
        require(kelvin.isFinite() && kelvin > 500.0 && kelvin < 100_000.0) {
            "$COMPONENT invalid interpolated white point"
        }
        return kelvin
    }

    internal fun solve(input: Inputs): Solved {
        val color1 = normalizedForward(checkedMatrix(input.colorMatrix1, "ColorMatrix1"))
        val color2 = normalizedForward(checkedMatrix(input.colorMatrix2, "ColorMatrix2"))
        val cal1 = checkedMatrix(input.calibrationMatrix1, "CalibrationMatrix1")
        val cal2 = checkedMatrix(input.calibrationMatrix2, "CalibrationMatrix2")
        val forward1 = normalizedForward(checkedMatrix(input.forwardMatrix1, "ForwardMatrix1"))
        val forward2 = normalizedForward(checkedMatrix(input.forwardMatrix2, "ForwardMatrix2"))
        require(input.neutralCamera.size == 3 &&
            input.neutralCamera.all { it.isFinite() && it > 1e-5f && it < 100f }) {
            "$COMPONENT missing actual SENSOR_NEUTRAL_COLOR_POINT"
        }
        require(input.appliedDonorRgbGains.size == 3 &&
            input.appliedDonorRgbGains.all { it.isFinite() && it > 0.001f && it < 128f }) {
            "$COMPONENT missing actual ResolveSabre final WB gains"
        }
        val t1 = input.illuminant1Kelvin
        val t2 = input.illuminant2Kelvin
        require(t1 in 1800..10000 && t2 in 1800..10000) {
            "$COMPONENT unavailable dual DNG illuminant"
        }
        val neutral = DoubleArray(3) { input.neutralCamera[it].toDouble() }
        val xyzToCamera1 = multiply(cal1, color1)
        val xyzToCamera2 = multiply(cal2, color2)
        var factor = 0.5
        if (t1 != t2) {
            val low = min(t1, t2).toDouble()
            val high = max(t1, t2).toDouble()
            repeat(30) {
                val xyz = map(invert(mix(xyzToCamera1, xyzToCamera2, factor)), neutral)
                val kelvin = chromaticTemperature(xyz)
                val target = when {
                    kelvin <= low -> 1.0
                    kelvin >= high -> 0.0
                    else -> (1.0 / kelvin - 1.0 / high) / (1.0 / low - 1.0 / high)
                }
                val ordered = if (t1 == low.toInt()) 1.0 - target else target
                factor = (factor + ordered) * 0.5
            }
        }
        require(factor.isFinite() && factor in 0.0..1.0)
        val invCalibration = invert(mix(cal1, cal2, factor))
        val referenceNeutral = map(invCalibration, neutral)
        require(referenceNeutral.all { it.isFinite() && it > 1e-8 }) {
            "$COMPONENT nonpositive DNG calibrated neutral"
        }
        val maximum = referenceNeutral.maxOrNull()!!
        val diagonal = DoubleArray(9)
        for (channel in 0..2) diagonal[channel * 3 + channel] =
            maximum / referenceNeutral[channel]
        val cameraToXyzD50 = multiply(mix(forward1, forward2, factor),
            multiply(diagonal, invCalibration))
        // The donor's pre-clamp Resolve *already* multiplies cameraRGB by
        // uFinalGains. Undo that exact multiplication to avoid second WB.
        val undoDonorGains = DoubleArray(9)
        for (channel in 0..2) undoDonorGains[channel * 3 + channel] =
            1.0 / input.appliedDonorRgbGains[channel].toDouble()
        val toProphoto = multiply(xyzToProphoto, multiply(cameraToXyzD50, undoDonorGains))
        val toSrgb = multiply(xyzToLinearSrgb, prophotoToXyz)
        require(toProphoto.all { it.isFinite() && abs(it) <= 100.0 } &&
            toSrgb.all { it.isFinite() }) { "$COMPONENT unstable rendered calibration" }
        return Solved(FloatArray(9) { toProphoto[it].toFloat() },
            FloatArray(9) { toSrgb[it].toFloat() }, factor)
    }
}
