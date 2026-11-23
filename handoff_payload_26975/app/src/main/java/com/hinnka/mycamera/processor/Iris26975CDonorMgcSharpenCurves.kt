package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.PhotonSharpenTuning
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.MgcSharpenCurveBuilder
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawSharpeningDefaults

/**
 * Experiment C selection adapter. No independently transcribed tuning nodes or
 * interpolation kernels: both source authorities are original pinned bjzhou.
 * The full MGC sharpen shader still needs numerical/device parity validation.
 */
internal object Iris26975CDonorMgcSharpenCurves {
    fun build(referenceSnr: Float): FloatArray =
        MgcSharpenCurveBuilder.build(referenceSnr, PhotonSharpenTuning.DEFAULT).points

    fun strength(slider: Float): Float = RawSharpeningDefaults.toMgcStrength(slider)
}
