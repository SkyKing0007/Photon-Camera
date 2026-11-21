package com.hinnka.mycamera.processor

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Experiment C-only copy of pinned bjzhou v1.29.0 Sabre sqrt-domain QMC LUT.
 * Original MgcSabreNoiseEstimatesLut.kt blob 9060357f8f0d4ec2165558c78abbaddff34ae1b8.
 */
internal object Iris26972CDonorSabreNoiseEstimatesLut {
    const val WIDTH = 10
    const val ROWS = 2
    const val CHANNELS = 4

    private const val QMC_SAMPLE_COUNT = 64
    private const val QMC_PAIR_COUNT = QMC_SAMPLE_COUNT / 2
    private const val UINT32_RANGE = 4_294_967_296.0
    private const val TWO_PI = 2.0 * PI

    private val qmcNormalSamples: FloatArray = createQmcNormalSamples()

    fun create(
        referenceShotNoise: FloatArray,
        referenceReadNoise: FloatArray,
        currentShotNoise: FloatArray,
        currentReadNoise: FloatArray,
    ): FloatArray {
        require(referenceShotNoise.size >= CHANNELS)
        require(referenceReadNoise.size >= CHANNELS)
        require(currentShotNoise.size >= CHANNELS)
        require(currentReadNoise.size >= CHANNELS)
        // C rejects invalid Camera2 noise metadata; never invent a quiet noise model.
        for (input in arrayOf(referenceShotNoise,referenceReadNoise,currentShotNoise,currentReadNoise)) {
            require(input.take(CHANNELS).all { it.isFinite() && it >= 0f }) {
                "26972 C needs genuine finite nonnegative Camera2 shot/read noise coefficients"
            }
        }
        val values = FloatArray(WIDTH * ROWS * CHANNELS)
        writeRow(values, 0, referenceShotNoise, referenceReadNoise)
        writeRow(values, 1, currentShotNoise, currentReadNoise)
        require(values.all { it.isFinite() && it >= 0f }) {
            "26972 C donor QMC LUT is invalid"
        }
        return values
    }

    private fun writeRow(destination: FloatArray, row: Int, shotNoise: FloatArray, readNoise: FloatArray) {
        for (x in 0 until WIDTH) {
            val sqrtSignal = x.toFloat() / (WIDTH - 1).toFloat()
            val offset = (row * WIDTH + x) * CHANNELS
            destination[offset] = sqrtDomainVariance(sqrtSignal,shotNoise[0],readNoise[0])
            val greenVarianceSum =
                sqrtDomainVariance(sqrtSignal,shotNoise[1],readNoise[1]) +
                    sqrtDomainVariance(sqrtSignal,shotNoise[2],readNoise[2])
            destination[offset + 1] = 0.25f * greenVarianceSum
            destination[offset + 2] = sqrtDomainVariance(sqrtSignal,shotNoise[3],readNoise[3])
            destination[offset + 3] = 0f
        }
    }

    internal fun sqrtDomainVariance(sqrtSignal: Float,shotNoise: Float,readNoise: Float): Float {
        require(sqrtSignal.isFinite() && sqrtSignal in 0f..1f)
        require(shotNoise.isFinite() && readNoise.isFinite())
        val linearSignal = sqrtSignal * sqrtSignal
        val linearVariance = max(readNoise + shotNoise * linearSignal, 0f)
        val linearStandardDeviation = sqrt(linearVariance)
        var squaredErrorSum = 0f
        for (normalSample in qmcNormalSamples) {
            val noisyLinearSignal = linearSignal + linearStandardDeviation * normalSample
            val transformedSample = sqrt(max(noisyLinearSignal, 0f))
            val error = transformedSample - sqrtSignal
            squaredErrorSum += error * error
        }
        return squaredErrorSum / QMC_SAMPLE_COUNT.toFloat()
    }

    internal fun qmcAngleBits(index: Int): UInt {
        require(index >= 0)
        var remaining = index
        var mask = 0x80000000u
        var bits = 0u
        while (remaining != 0) {
            if ((remaining and 1) != 0) bits = bits xor mask
            mask = mask or (mask shr 1)
            remaining = remaining ushr 1
        }
        return bits
    }

    private fun createQmcNormalSamples(): FloatArray {
        val samples = FloatArray(QMC_SAMPLE_COUNT)
        for (index in 0 until QMC_PAIR_COUNT) {
            val radialInput = (index.toFloat() + 0.5f) / QMC_PAIR_COUNT.toFloat()
            val radius = sqrt((-2f * ln(radialInput.toDouble()).toFloat()).toDouble()).toFloat()
            val phase = (qmcAngleBits(index).toLong().toDouble() / UINT32_RANGE).toFloat()
            val angle = (phase.toDouble() * TWO_PI).toFloat()
            samples[index * 2] = radius * sin(angle.toDouble()).toFloat()
            samples[index * 2 + 1] = radius * cos(angle.toDouble()).toFloat()
        }
        return samples
    }
}
