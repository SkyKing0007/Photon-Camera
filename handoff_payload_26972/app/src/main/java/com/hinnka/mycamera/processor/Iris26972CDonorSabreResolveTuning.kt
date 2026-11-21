package com.hinnka.mycamera.processor

/**
 * Experiment C-owned port of bjzhou/PhotonCamera tag 1.29.0 MgcSabreResolveTuning.
 * Pinned donor blob SHA-1: 96e9cf198d3a8245ef1d4cf72b55fda562661823.
 * Source: app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolveTuning.kt
 *
 * IMPORTANT: This is the DONOR's Gr/Gb imbalance retention parameter, not
 * the older Iris MgcSabreResolveTuning.outputWhiteLevel even though their
 * SNR interpolation numbers look similar. A/B code remains unchanged.
 * The donor GL ResolveSabre consumer must be ported before production C can use it.
 */
internal object Iris26972CDonorSabreResolveTuning {
    data class Parameters(
        val greenImbalanceRetention: Float,
        val demosaicSharpness: Float,
    )

    fun build(
        referenceSnr: Float,
        desiredExposureProduct: Double?,
        actualExposureProduct: Double,
    ): Parameters = Parameters(
        greenImbalanceRetention = greenImbalanceRetention(referenceSnr),
        demosaicSharpness = demosaicSharpness(desiredExposureProduct, actualExposureProduct),
    )

    /** Donor V25 Gr/Gb retention: {{5,0}, {20,0.5}, {40,1}}, endpoint clamped. */
    internal fun greenImbalanceRetention(referenceSnr: Float): Float {
        val snr = referenceSnr.takeIf { it.isFinite() } ?: GREEN_IMBALANCE_SNR_LOW
        return when {
            snr <= GREEN_IMBALANCE_SNR_LOW -> GREEN_IMBALANCE_LOW
            snr < GREEN_IMBALANCE_SNR_MID -> interpolate(
                snr, GREEN_IMBALANCE_SNR_LOW, GREEN_IMBALANCE_LOW,
                GREEN_IMBALANCE_SNR_MID, GREEN_IMBALANCE_MID,
            )
            snr < GREEN_IMBALANCE_SNR_HIGH -> interpolate(
                snr, GREEN_IMBALANCE_SNR_MID, GREEN_IMBALANCE_MID,
                GREEN_IMBALANCE_SNR_HIGH, GREEN_IMBALANCE_HIGH,
            )
            else -> GREEN_IMBALANCE_HIGH
        }
    }

    /** MGC min(FinalTet / actual TET, 1) in equivalent Camera2 exposure-product units. */
    internal fun demosaicSharpness(
        desiredExposureProduct: Double?,
        actualExposureProduct: Double,
    ): Float {
        val desired = desiredExposureProduct
            ?.takeIf { it.isFinite() && it > 0.0 }
            ?: return DEFAULT_DEMOSAIC_SHARPNESS
        val actual = actualExposureProduct
            .takeIf { it.isFinite() && it > 0.0 }
            ?: return DEFAULT_DEMOSAIC_SHARPNESS
        return (desired / actual).coerceAtMost(1.0).toFloat()
    }

    private fun interpolate(
        value: Float, lowerX: Float, lowerY: Float, upperX: Float, upperY: Float,
    ): Float {
        val amount = (value - lowerX) / (upperX - lowerX)
        return upperY * amount + lowerY * (1f - amount)
    }

    private const val GREEN_IMBALANCE_SNR_LOW = 5f
    private const val GREEN_IMBALANCE_SNR_MID = 20f
    private const val GREEN_IMBALANCE_SNR_HIGH = 40f
    private const val GREEN_IMBALANCE_LOW = 0f
    private const val GREEN_IMBALANCE_MID = 0.5f
    private const val GREEN_IMBALANCE_HIGH = 1f
    private const val DEFAULT_DEMOSAIC_SHARPNESS = 1f
}
