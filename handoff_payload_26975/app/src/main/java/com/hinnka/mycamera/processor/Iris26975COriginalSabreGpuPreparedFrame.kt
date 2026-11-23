package com.hinnka.mycamera.processor

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract

/**
 * Experiment C-only real Camera2 RAW16 upload -> donor 2x2 Bayer extraction ->
 * reference/current sqrt-domain 64-QMC noise LUT -> donor Sabre guide/covariance.
 * All stages run synchronously on one caller-owned EGL context. This result
 * deliberately does NOT contain alignment, rejection or a completed RGB image.
 */
internal object Iris26975COriginalSabreGpuPreparedFrame {
    private const val COMPONENT = "26972 C donor Sabre RAW preparation"

    internal data class Plan(
        val raw: Iris26972CDonorSabreGpuRawIngress.Plane,
        val cfaPattern: Int,
        val referenceSnr: Float,
        val frozenFrameCount: Int,
        val referenceShotNoise: FloatArray,
        val referenceReadNoise: FloatArray,
        val currentShotNoise: FloatArray,
        val currentReadNoise: FloatArray,
        val gains: FloatArray,
        val blackLevelsTimesGains: FloatArray,
        val greenClippingPoint: Float,
        /** The pinned donor PhotonFusionTuning.DEFAULT uses -1f, never adaptive null. */
        val mergeGradientThreshold: Float = -1f,
    )

    internal class Result private constructor(
        private val raw: Iris26975COriginalSabreGpuRawIngress.Result,
        private val noise: Iris26975COriginalSabreGpuNoiseLut.Result,
        private val guide: Iris26975COriginalSabreGpuGuide.Result,
    ) : AutoCloseable {
        val rawWidth: Int get() = raw.rawWidth
        val rawHeight: Int get() = raw.rawHeight
        val extractedBayerTexture: Int get() { requireOwner(); return raw.extractedBayerTexture }
        val raw16Texture: Int get() { requireOwner(); return raw.raw16Texture }
        private var unblocker: Iris26972CDonorSabreGpuUnblocker.Result? = null
        /** Consumes only this frame's retained original R16UI RAW samples. */
        val unblockerTexture: Int get() {
            requireOwner()
            return checkNotNull(unblocker) { "$COMPONENT unblocker not computed" }.texture
        }
        internal fun computeUnblocker(
            cfaPattern: Int,
            blackLevels: FloatArray,
            shotNoise: FloatArray,
            readNoise: FloatArray,
        ) {
            requireOwner()
            check(unblocker == null) { "$COMPONENT unblocker already computed" }
            val plan=Iris26972CDonorSabreGpuUnblocker.Plan(
                rawWidth,rawHeight,raw16Texture,cfaPattern,blackLevels,shotNoise,readNoise)
            Iris26972CDonorSabreGpuUnblocker.validate(plan)
            unblocker=Iris26972CDonorSabreGpuUnblocker.compute(plan)
        }
        val qmcNoiseTexture: Int get() { requireOwner(); return noise.texture }
        val guideTexture: Int get() { requireOwner(); return guide.guideTexture }
        val covarianceTexture: Int get() { requireOwner(); return guide.covarianceTexture }
        private var closed = false
        internal fun requireOwner() {
            check(!closed) { "$COMPONENT already released" }
            raw.requireOwner(); noise.checkOwner(); guide.requireOwner()
        }
        override fun close() {
            requireOwner()
            // RAW16, Bayer, noise, guide, covariance, optional unblocker are owned.
            unblocker?.close()
            guide.close()
            noise.close()
            raw.close()
            closed = true
        }
        internal companion object {
            fun owned(raw: Iris26975COriginalSabreGpuRawIngress.Result,
                noise: Iris26975COriginalSabreGpuNoiseLut.Result,
                guide: Iris26975COriginalSabreGpuGuide.Result) = Result(raw,noise,guide)
        }
    }

    /** Never substitute missing or invalid Camera2 noise metadata with guesses. */
    internal fun prepare(plan: Plan, hotPixels: Iris26975COriginalSabreHotPixel? = null,
        isShutterReference: Boolean = false): Result {
        Iris26972CDonorSabreGpuRawIngress.validate(plan.raw)
        require(plan.cfaPattern in 0..3 && plan.frozenFrameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
            plan.referenceSnr.isFinite() && plan.referenceSnr >= 0f) {
            "$COMPONENT invalid frozen RAW burst metadata"
        }
        // Pure CPU validation before any GPU side effects.
        Iris26975COriginalSabreGpuNoiseLut.validateNoiseCoefficients(
            plan.referenceShotNoise,plan.referenceReadNoise,
            plan.currentShotNoise,plan.currentReadNoise)
        val guidePlan=Iris26975COriginalSabreGpuGuide.Plan(
            rawWidth=plan.raw.cropWidth,rawHeight=plan.raw.cropHeight,
            cfaPattern=plan.cfaPattern,referenceSnr=plan.referenceSnr,
            frozenFrameCount=plan.frozenFrameCount,
            frame=Iris26975COriginalSabreGpuGuide.Frame(
                extractedBayerTexture=1,qmcNoiseTexture=2,
                gains=plan.gains,blackLevelsTimesGains=plan.blackLevelsTimesGains,
                greenClippingPoint=plan.greenClippingPoint),
            mergeGradientThreshold=plan.mergeGradientThreshold)
        Iris26975COriginalSabreGpuGuide.validate(guidePlan)
        var noise: Iris26975COriginalSabreGpuNoiseLut.Result? = null
        var raw: Iris26975COriginalSabreGpuRawIngress.Result? = null
        var guide: Iris26975COriginalSabreGpuGuide.Result? = null
        try {
            noise=Iris26975COriginalSabreGpuNoiseLut.create(
                plan.referenceShotNoise,plan.referenceReadNoise,
                plan.currentShotNoise,plan.currentReadNoise)
            raw=Iris26975COriginalSabreGpuRawIngress.extract(plan.raw,hotPixels,isShutterReference)
            guide=Iris26975COriginalSabreGpuGuide.process(guidePlan.copy(
                frame=guidePlan.frame.copy(
                    extractedBayerTexture=raw.extractedBayerTexture,
                    qmcNoiseTexture=noise.texture)))
            check(guide.rawWidth==raw.rawWidth && guide.rawHeight==raw.rawHeight) {
                "$COMPONENT RAW and donor guide dimensions diverged"
            }
            return Result.owned(raw,noise,guide)
        } catch (cause: Throwable) {
            // Try to release all independently owned textures, preserving original failure.
            try { guide?.close() } catch (cleanup: Throwable) { cause.addSuppressed(cleanup) }
            try { raw?.close() } catch (cleanup: Throwable) { cause.addSuppressed(cleanup) }
            try { noise?.close() } catch (cleanup: Throwable) { cause.addSuppressed(cleanup) }
            throw cause
        }
    }
}
