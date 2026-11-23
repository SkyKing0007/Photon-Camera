package com.hinnka.mycamera.processor.experimentc

import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.RawNoiseModel

/** Camera2 physical Bayer ordering adapter; the donor owns all noise sanitization and mapping. */
internal object Iris26975CDonorCamera2Noise {
    internal data class Canonical(val shot: FloatArray, val read: FloatArray) {
        fun copyShot(): FloatArray = shot.copyOf()
        fun copyRead(): FloatArray = read.copyOf()
    }

    fun normalize(
        cfaPattern: Int,
        canonicalShot: FloatArray,
        canonicalRead: FloatArray,
    ): Canonical {
        require(cfaPattern in 0..3 && canonicalShot.size == 4 && canonicalRead.size == 4) {
            "C donor needs four actual physical Camera2 channel-pairs and Bayer CFA"
        }
        val phaseToCanonical = when (cfaPattern) {
            0 -> intArrayOf(0, 1, 2, 3)
            1 -> intArrayOf(1, 0, 3, 2)
            2 -> intArrayOf(2, 3, 0, 1)
            else -> intArrayOf(3, 2, 1, 0)
        }
        // Camera2 SENSOR_NOISE_PROFILE is in physical phase order, never sorted R/G/B.
        val phasePairs = FloatArray(8) { i ->
            val color = phaseToCanonical[i / 2]
            if (i % 2 == 0) canonicalShot[color] else canonicalRead[color]
        }
        val model = RawNoiseModel.fromCamera2NoiseProfile(phasePairs)
        require(model.hasValidCamera2Profile) {
            "C donor Camera2 noise model is unavailable: no invented profile fallback"
        }
        return Canonical(
            model.normalizedShotNoiseForShader(cfaPattern),
            model.normalizedReadNoiseForShader(cfaPattern),
        )
    }
}
