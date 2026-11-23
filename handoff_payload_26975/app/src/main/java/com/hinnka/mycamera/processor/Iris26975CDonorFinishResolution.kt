package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.experimentc.original129.raw.MgcFinishResolution

/**
 * Experiment C-only ABI adapter. All MGC V25 FinishShot resolution policy is
 * executed by the EXACT pinned original bjzhou MgcFinishResolution, not a
 * reimplementation. Keep this adapter until the entire RAW engine owns C.
 * The separate original donor class is byte-verified after its package rename.
 */
internal class Iris26975CDonorFinishResolution private constructor(
    private val original: MgcFinishResolution,
) {
    val log2Downsample: Int get() = original.log2Downsample
    val downsampleFactor: Int get() = original.downsampleFactor
    val needsGuidedUpsample: Boolean get() = original.needsGuidedUpsample
    val processingPeriod: Int get() = original.processingPeriod
    internal fun originalPolicy(): MgcFinishResolution = original

    companion object {
        fun resolve(
            cropWidth: Int,
            cropHeight: Int,
            outputWidth: Int,
            outputHeight: Int,
            scaleOverride: Float = -1f,
            levelOverride: Int = -1,
        ): Iris26975CDonorFinishResolution = Iris26975CDonorFinishResolution(
            MgcFinishResolution.resolve(cropWidth, cropHeight, outputWidth, outputHeight,
                scaleOverride, levelOverride),
        )
    }
}
