package com.hinnka.mycamera.processor

/**
 * Experiment C-owned, source-faithful MGC V25 classic Sabre post-merge noise model.
 * Pinned reference: bjzhou/PhotonCamera@0a8a11defe7d932d8c8a729120a4d5f159e9d677
 * processor/MgcSabreMergedNoiseModel.kt. The RGB inputs must be normalized,
 * un-white-balanced per-frame Camera2 S/O noise at the reference exposure.
 * The fusion weights do not substitute for these V25 model weights.
 */
internal object Iris26975CDonorSabreMergedNoiseModel {
    data class Frame(val read: FloatArray, val shot: FloatArray)
    data class Output(val read: FloatArray, val shot: FloatArray, val correlation: FloatArray)

    /** Backwards-compatible C-only API; the original pinned donor owns the algorithm. */
    fun merge(frames: List<Frame>, referenceSnr: Float, noiseSpectrumSeed: Float = 1f): Output {
        val donor = com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel.merge(
            frames.map { frame ->
                com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel.Frame(
                    frame.read, frame.shot)
            },
            referenceSnr, noiseSpectrumSeed)
        return Output(donor.read, donor.shot, donor.correlation)
    }

    /** Exact donor MgcSpatialMergeTuning.outputNoiseModelSnr normalized green model. */
    internal fun outputNoiseModelSnr(
        signal: Float,
        greenReadVariance: Float,
        greenShotNoiseFactor: Float,
    ): Float? {
        if (!signal.isFinite() || signal < 0f ||
            !greenReadVariance.isFinite() || greenReadVariance < 0f ||
            !greenShotNoiseFactor.isFinite() || greenShotNoiseFactor < 0f
        ) return null
        val variance = greenReadVariance + greenShotNoiseFactor * signal
        if (!variance.isFinite() || variance <= 0f) return null
        return (signal / kotlin.math.sqrt(variance)).takeIf {
            it.isFinite() && it >= 0f
        }
    }

    /** Delegate the V25 SNR variance correction to the original pinned donor. */
    internal fun snrCorrection(referenceSnr: Float): Float =
        com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel
            .snrCorrection(referenceSnr)
}
