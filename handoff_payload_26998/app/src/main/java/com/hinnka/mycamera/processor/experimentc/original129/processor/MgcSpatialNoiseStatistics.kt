package com.hinnka.mycamera.processor.experimentc.original129.processor

import com.hinnka.mycamera.processor.experimentc.original129.raw.MgcSpatialStrengthMap

/**
 * Noise model of the merged Spatial image before output-exposure normalization.
 * The read, shot and Savannah diagnostic tuples use camera RGB channel order.
 */
internal data class MgcSpatialNoiseStatistics(
    val strengthMap: MgcSpatialStrengthMap,
    val outputReadNoise: FloatArray,
    val outputShotNoise: FloatArray,
    val outputWeightsSumTotalDiag0: FloatArray,
    val outputWeightsSumTotalDiag1: FloatArray,
)
