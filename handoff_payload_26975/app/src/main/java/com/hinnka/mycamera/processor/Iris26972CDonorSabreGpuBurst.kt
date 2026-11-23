package com.hinnka.mycamera.processor
import com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreAlignmentOffset

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import android.opengl.EGL14
import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Completely isolated Experiment C donor-Sabre RAW burst composition, producing
 * linear camera RGB and feeding the separate C color and finishing owners.
 *
 * One NORMAL reference is retained, one NORMAL alternate is prepared, LK-aligned,
 * rejected, dilated and fused at a time. Actual donor R8 weights are blended immediately
 * into ONE persistent quarter-grid R8 coverage target; alternate masks are then freed.
 * No A/B optical flow, demosaic, fallback or synthetic alternate is possible.
 * C production routing stays deliberately disabled.
 *
 * This host-integrated operation has NOT been Android-GPU/GLSL/device validated.
 */
internal object Iris26972CDonorSabreGpuBurst {
    private const val COMPONENT = "26972 C isolated donor RAW Sabre burst"
    private val gl = Iris26972CDonorSabreGpuMerge
    internal enum class CaptureRole { NORMAL, SHORT, LONG }

    internal data class Frame(
        val role: CaptureRole,
        val physicalCameraId: String,
        val frameNumber: Long,
        val sensorTimestampNs: Long,
        /** Actual Camera2 exposureTimeNs * sensitivityIso for this RAW, not AE intent. */
        val exposureProduct: Double,
        val raw: Iris26975COriginalSabreGpuPreparedFrame.Plan,
        val sensorBlackLevels: FloatArray,
        val alignmentGain: Float,
        /** Donor RAW16 sensor-code-domain noise, NOT normalized QMC/WB variance. */
        val unblockerShotNoise: FloatArray,
        val unblockerReadNoise: FloatArray,
        /** Donor V25 post-Sabre noise model is normalized camera RGB, no calculation WB. */
        val cameraRgbShotNoise: FloatArray,
        val cameraRgbReadNoise: FloatArray,
    )
    internal data class Plan(
        val frozenFrames: List<Frame>,
        /** Frozen shutter reference RAW timestamp, never inferred from a re-sorted burst. */
        val frozenReferenceTimestampNs: Long,
        val resolve: Iris26972CDonorSabreGpuResolve.Plan,
        val referencePhysical: Iris26972CPhysicalRawMetadata.Frozen? = null,
        val measuredReferenceSignal: Float = Float.NaN,
    ) {
        val rawWidth: Int get() = frozenFrames.first().raw.raw.cropWidth
        val rawHeight: Int get() = frozenFrames.first().raw.raw.cropHeight
    }

    /** Pure capture-admission validation, before any GPU program or buffer allocation. */
    internal fun validate(plan: Plan, metadataOnly: Boolean = false) {
        val frames = plan.frozenFrames
        require(frames.size in 2..Iris26972CContract.MAX_NORMAL_FRAMES) { "$COMPONENT requires full frozen NORMAL RAW burst" }
        val first = frames.first()
        val physical = first.physicalCameraId
        val baseRaw = first.raw.raw
        val snr = first.raw.referenceSnr
        val baseCfa = first.raw.cfaPattern
        val baseExposure = first.exposureProduct
        require(plan.frozenReferenceTimestampNs > 0L &&
            plan.frozenReferenceTimestampNs == first.sensorTimestampNs &&
            baseExposure.isFinite() && baseExposure > 0.0) {
            "$COMPONENT reference timestamp/exposure does not match shutter-frozen RAW"
        }
        require(physical.isNotBlank() && first.sensorTimestampNs > 0L && first.frameNumber >= 0L) {
            "$COMPONENT missing real source camera/frame metadata"
        }
        require(plan.resolve.cfaPattern == baseCfa &&
            plan.resolve.frozenNormalFrameCount == frames.size &&
            plan.resolve.referenceSnr == snr) {
            "$COMPONENT resolve metadata diverges from shutter-frozen RAW burst"
        }
        Iris26972CDonorSabreGpuResolve.validate(plan.resolve,baseRaw.cropWidth,baseRaw.cropHeight,metadataOnly)
        require(first.raw.referenceShotNoise.contentEquals(first.raw.currentShotNoise) &&
            first.raw.referenceReadNoise.contentEquals(first.raw.currentReadNoise)) {
            "$COMPONENT base QMC noise must be reference/reference, not alternate"
        }
        val timestamps = HashSet<Long>()
        val frameNumbers = HashSet<Long>()
        frames.forEachIndexed { index, frame ->
            val prepared = frame.raw
            Iris26972CDonorSabreGpuRawIngress.validate(prepared.raw)
            val raw = prepared.raw
            require(frame.role == CaptureRole.NORMAL && frame.physicalCameraId == physical &&
                frame.sensorTimestampNs > 0L && frame.frameNumber >= 0L &&
                timestamps.add(frame.sensorTimestampNs) && frameNumbers.add(frame.frameNumber)) {
                "$COMPONENT duplicate, relabeled, LONG or cross-camera capture frame=$index"
            }
            require(prepared.cfaPattern == baseCfa && prepared.frozenFrameCount == frames.size &&
                prepared.referenceSnr == snr &&
                // PhotonFusionTuning.DEFAULT is -1f, even for the reference.
                prepared.mergeGradientThreshold == -1f &&
                raw.cropWidth == baseRaw.cropWidth && raw.cropHeight == baseRaw.cropHeight &&
                raw.cropLeft == baseRaw.cropLeft && raw.cropTop == baseRaw.cropTop &&
                prepared.referenceShotNoise.contentEquals(first.raw.referenceShotNoise) &&
                prepared.referenceReadNoise.contentEquals(first.raw.referenceReadNoise) &&
                frame.cameraRgbShotNoise.size == 3 &&
                frame.cameraRgbReadNoise.size == 3 &&
                frame.cameraRgbShotNoise.all { it.isFinite() && it >= 0f } &&
                frame.cameraRgbReadNoise.all { it.isFinite() && it >= 0f }) {
                "$COMPONENT inconsistent RAW reference/noise/crop/CFA frame=$index"
            }
            // The NORMAL label alone is not exposure proof: reject real Camera2
            // bracketed frames even when incorrectly relabeled NORMAL. Preserve the
            // donor's equal-exposure noise and frame-normalization assumptions.
            require(frame.exposureProduct.isFinite() && frame.exposureProduct > 0.0 &&
                kotlin.math.abs(frame.exposureProduct / baseExposure - 1.0) <= 0.01) {
                "$COMPONENT intentional/invalid RAW exposure bracket frame=$index"
            }
            require(frame.sensorBlackLevels.size == 4 &&
                frame.sensorBlackLevels.all { it.isFinite() && it in 0f..65535f } &&
                frame.alignmentGain.isFinite() && frame.alignmentGain > 0f &&
                frame.alignmentGain <= 64f &&
                frame.unblockerShotNoise.size == 4 && frame.unblockerReadNoise.size == 4 &&
                frame.unblockerShotNoise.all { it.isFinite() && it > 0f } &&
                frame.unblockerReadNoise.all { it.isFinite() && it >= 0f }) {
                "$COMPONENT missing sensor black/RAW alignment gain frame=$index"
            }
            Iris26972CDonorSabreLkPyramidPlan(raw.cropWidth,raw.cropHeight,
                MgcSabreAlignmentOffset.tileSupport(snr))
            // Each donor QMC constructor validates actual finite Camera2 noise, no defaults.
            Iris26975COriginalSabreGpuNoiseLut.validateNoiseCoefficients(
                prepared.referenceShotNoise,prepared.referenceReadNoise,
                prepared.currentShotNoise,prepared.currentReadNoise)
            // Validate untouched Camera2 calibration arrays before entering GL.
            require(prepared.gains.size == 4 && prepared.blackLevelsTimesGains.size == 4 &&
                prepared.gains.all { it.isFinite() && it > 0f } &&
                prepared.blackLevelsTimesGains.all { it.isFinite() } &&
                prepared.greenClippingPoint.isFinite() && prepared.greenClippingPoint > 0f) {
                "$COMPONENT invalid donor RAW guide calibration frame=$index"
            }
        }
    }

    /**
     * Isolated C chain through genuine camera2-profile color, preserving both
     * native sRGB for MGC sharpening and pre-Adobe, extended-linear sRGB for HDR gainmap.
     * The isolated Camera2/gallery source owner calls this C-only chain, but
     * Android execution and device output are unproven; the production gate is disabled.
     */
    internal fun processColor(
        burst: Plan,
        color: Iris26972CColorDeveloper.Plan,
        context: android.content.Context,
        scratch: java.io.File,
        shading: Iris26972CPhysicalLensShading.Frozen,
    ): Iris26972CColorDeveloper.Result {
        validate(burst)
        Iris26972CColorDeveloper.validate(color)
        require(color.physicalCameraId == burst.frozenFrames.first().physicalCameraId &&
            color.width == burst.rawWidth && color.height == burst.rawHeight) {
            "$COMPONENT color profile must belong to the same frozen physical RAW lens"
        }
        val fused = process(burst)
        return try {
            val physical=checkNotNull(burst.referencePhysical) {
                "$COMPONENT donor RAW denoise requires actual physical Camera2 noise"
            }
            check(physical.physicalCameraId == color.physicalCameraId &&
                physical.sensorTimestampNs == burst.frozenReferenceTimestampNs) {
                "$COMPONENT donor RAW noise must share the shutter reference"
            }
            require(burst.measuredReferenceSignal.isFinite() &&
                burst.measuredReferenceSignal >= 0f) {
                "$COMPONENT requires actual reference RAW green signal for merged SNR"
            }
            // Preserve bjzhou's full-res order: Sabre Resolve -> native
            // denoising -> original full-resolution RAW linear calibration ->
            // original Adobe HDR reference. Final guided SDR sharpening follows.
            // HDR must use the same denoised camera-RGB source as the SDR prepass,
            // never the earlier provisional C custom color developer.
            val params = com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreResolveTuning.build(
                burst.resolve.referenceSnr,burst.resolve.desiredExposureProduct,
                burst.resolve.actualExposureProduct)
            // The donor constructs merged read/shot/correlation from the actual
            // admitted Camera2 RAW frames; do not infer it from output residuals.
            val mergedNoise =
                com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel.merge(
                    burst.frozenFrames.map { frame ->
                        com.hinnka.mycamera.processor.experimentc.bjzhou.processor.MgcSabreMergedNoiseModel.Frame(
                            frame.cameraRgbReadNoise, frame.cameraRgbShotNoise)
                    },
                    burst.frozenFrames.first().raw.referenceSnr,
                    noiseSpectrumSeed = 1f, // pinned PhotonDenoiseTuning.DEFAULT_SPECTRUM_SEED
                )
            Iris26975CDonorNativeDenoise.apply(context,scratch,physical,fused,
                burst.measuredReferenceSignal,shading,mergedNoise)
            // The original RawHdrReferencePass creates a measured, scalar HDR
            // ratio from the now-denoised full-resolution profile-domain source.
            // Both full-resolution F16 outputs are reused by guided SDR and the
            // HDR sidecar. The C temporary color-developer GLSL is not executed.
            val result = Iris26975COriginalHdrAfterDenoise.develop(color, fused,
                burst.frozenFrames.first().raw.referenceSnr,params.demosaicSharpness)
            var guidedComplete = false
            try {
                // MGC V25 1x: the real denoised donor camera RGB supplies the
                // full-resolution guide. Adobe tone runs on its 4x BOX color,
                // before ridge-fit GuidedUpsample reconstructs native output.
                // Render IN PLACE over the temporary ProPhoto reference input;
                // no additional 50MP GPU surface is allocated or leaked.
                val resolution = Iris26975CDonorFinishResolution.resolve(
                    burst.rawWidth,burst.rawHeight,burst.rawWidth,burst.rawHeight)
                check(resolution.log2Downsample == 2) {
                    "$COMPONENT 1x MGC V25 finishing must select 4x low tone"
                }
                Iris26975CDonorGuidedV25Gpu().use { guided ->
                    guided.prepare(fused.extendedCameraRgbTexture,burst.rawWidth,
                        burst.rawHeight,physical.copyCanonicalWbForAudit(),resolution)
                    guided.renderAdobeLowTone(color)
                    guided.render(result.encodedSrgbTexture,
                        burst.frozenFrames.first().raw.referenceSnr,
                        Iris26975CDonorMgcSharpenCurves.strength(
                            com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract.SHARPENING)
                            * params.demosaicSharpness)
                }
                result.markDonorGuidedSdrComplete()
                guidedComplete = true
                result
            } finally {
                if (!guidedComplete) result.close()
            }
        } finally {
            fused.close()
        }
    }

    /**
     * Only the frozen PHYSICAL Camera2/DNG reference may authorize C RAW color.
     * The built-in color and MGC finishing paths have no implicit sensor-neutral,
     * logical-camera, white-balance or A/B renderer fallback.
     */
    internal fun processWithFrozenCamera2Color(
        burst: Plan,
        calibration: Iris26972CCamera2Calibration.Frozen,
        context: android.content.Context,
        scratch: java.io.File,
        shading: Iris26972CPhysicalLensShading.Frozen,
    ): Iris26972CColorDeveloper.Result {
        validate(burst)
        val colorPlan = calibration.colorPlan(burst.rawWidth, burst.rawHeight, burst)
        return processColor(burst, colorPlan,context,scratch,shading)
    }

    /** Original donor's 1x1 zero-flow and identity R16F weight, reference frame ONLY. */
    private class ReferenceIdentity(
        val zeroFlow: Int, val oneWeight: Int,
        private val context: android.opengl.EGLContext,
    ) : AutoCloseable {
        override fun close() {
            check(context != EGL14.EGL_NO_CONTEXT &&
                context == EGL14.eglGetCurrentContext()) { "$COMPONENT wrong identity owner" }
            GLES30.glDeleteTextures(2,intArrayOf(zeroFlow,oneWeight),0)
        }
    }

    private fun createReferenceIdentity(): ReferenceIdentity {
        gl.requireCurrentContext()
        val state = Iris26972CDonorSabreGpuMerge.GlState.capture()
        val pbo = gl.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val align = gl.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val rowLength = gl.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        val ids=IntArray(2)
        var success=false
        try {
            GLES30.glGenTextures(2,ids,0)
            check(ids.all { it>0 } && ids[0]!=ids[1]) {
                "$COMPONENT donor reference identity texture failure"
            }
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,0)
            for (index in 0..1) {
                GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
                GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,ids[index])
                for (param in intArrayOf(GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_TEXTURE_MAG_FILTER))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,param,GLES30.GL_NEAREST)
                for (param in intArrayOf(GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_TEXTURE_WRAP_T))
                    GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,param,GLES30.GL_CLAMP_TO_EDGE)
                val data=ByteBuffer.allocateDirect(if(index==0)8 else 2)
                    .order(ByteOrder.nativeOrder())
                if (index==0) repeat(4){data.putShort(0)} else data.putShort(0x3c00.toShort())
                data.flip()
                GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,
                    if(index==0)GLES30.GL_RGBA16F else GLES30.GL_R16F,
                    1,1,0,if(index==0)GLES30.GL_RGBA else GLES30.GL_RED,
                    GLES30.GL_HALF_FLOAT,data)
                gl.checkGl("donor reference ${if(index==0) "zero flow" else "unity weight"}")
            }
            success=true
            return ReferenceIdentity(ids[0],ids[1],EGL14.eglGetCurrentContext())
        } finally {
            if(!success && ids.any { it>0 })
                GLES30.glDeleteTextures(ids.count{it>0},ids.filter{it>0}.toIntArray(),0)
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER,pbo)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,align)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH,rowLength)
            state.restore()
        }
    }

    /** Returns only genuine donor fused RGBA16UI linear RGB (still NOT processed photo). */
    internal fun process(plan: Plan): Iris26972CDonorSabreGpuResolve.Result {
        validate(plan)
        gl.requireCurrentContext()
        gl.checkGl("before C donor NORMAL burst")
        // Stack owns all intermediates; closing in reverse order keeps reference guide
        // and gray LK pyramid alive until the final alternate has been merged.
        val owned = ArrayList<AutoCloseable>()
        fun <T: AutoCloseable> own(value:T):T {owned.add(value);return value}
        fun release(value:AutoCloseable) {
            check(owned.remove(value)) { "$COMPONENT double release of owned input" }
            value.close()
        }
        var primaryFailure: Throwable? = null
        try {
            val frames = plan.frozenFrames
            val reference = frames.first()
            val normalCount = frames.size
            val physical=checkNotNull(plan.referencePhysical) {
                "$COMPONENT authentic donor hot-pixel detection requires physical Camera2 reference"
            }
            check(physical.physicalCameraId == reference.physicalCameraId &&
                physical.sensorTimestampNs == reference.sensorTimestampNs &&
                physical.frameNumber == reference.frameNumber) {
                "$COMPONENT donor hot-pixel mask cannot mix physical RAW generations"
            }
            val hotPixels=own(Iris26975COriginalSabreHotPixel.begin(
                plan.rawWidth,plan.rawHeight,reference.raw.cfaPattern,physical,normalCount))
            val preparedReference=own(Iris26975COriginalSabreGpuPreparedFrame.prepare(
                reference.raw,hotPixels,isShutterReference=true))
            // Original GlesMgcRawSpatialStacker builds this once, outside
            // the alternate-frame loop. The original GPU base filter stays
            // immutable until all rejected NORMAL alternates are merged.
            val referenceColor = own(Iris26975COriginalSabreGpuRejection.prepareReferenceColor(
                plan.rawWidth,plan.rawHeight,preparedReference.guideTexture))
            val referenceGray=own(Iris26972CDonorSabreGpuGrayPyramid.build(
                Iris26972CDonorSabreGpuGrayPyramid.Plan(plan.rawWidth,plan.rawHeight,
                    preparedReference.raw16Texture,reference.raw.cfaPattern,
                    reference.sensorBlackLevels,reference.alignmentGain,
                    MgcSabreAlignmentOffset.tileSupport(reference.raw.referenceSnr))))
            val alignmentProducts=own(
                Iris26975COriginalSabreGpuLkAlignment.prepareReferenceProducts(referenceGray))
            val stream=own(Iris26972CDonorSabreGpuMerge.beginStream(
                plan.rawWidth,plan.rawHeight,reference.raw.cfaPattern,normalCount))
            val coverage=own(Iris26972CDonorSabreGpuNormalize.CoverageStream.begin(
                plan.rawWidth,plan.rawHeight,normalCount))
            val identity=own(createReferenceIdentity())
            stream.append(Iris26972CDonorSabreGpuMerge.Frame(
                preparedReference.extractedBayerTexture,identity.zeroFlow,
                preparedReference.covarianceTexture,identity.oneWeight,
                floatArrayOf(1f,1f,0f,0f),reference.raw.gains,
                reference.raw.blackLevelsTimesGains,true))
            coverage.appendReference(identity.oneWeight)
            // Identity textures are needed only during reference draw.
            release(identity)
            for (i in 1 until frames.size) {
                val frame=frames[i]
                val prepared=own(Iris26975COriginalSabreGpuPreparedFrame.prepare(
                    frame.raw,hotPixels,isShutterReference=false))
                val gray=own(Iris26972CDonorSabreGpuGrayPyramid.build(
                    Iris26972CDonorSabreGpuGrayPyramid.Plan(plan.rawWidth,plan.rawHeight,
                        prepared.raw16Texture,frame.raw.cfaPattern,
                        frame.sensorBlackLevels,frame.alignmentGain,
                        MgcSabreAlignmentOffset.tileSupport(reference.raw.referenceSnr))))
                val flow=own(Iris26975COriginalSabreGpuLkAlignment.solveAndConvert(
                    Iris26975COriginalSabreGpuLkAlignment.Plan(
                        referenceGray,gray,i,reference.raw.referenceSnr),alignmentProducts))
                // Upstream 1.29.0 uses RAW16 DN-domain noise here. The QMC
                // sqrt-domain reference/current arrays above include WB/exposure
                // gains and must NEVER be substituted for sensor-code noise.
                prepared.computeUnblocker(frame.raw.cfaPattern,frame.sensorBlackLevels,
                    frame.unblockerShotNoise,frame.unblockerReadNoise)
                val reverse=own(Iris26975COriginalSabreGpuRejection.process(
                    Iris26975COriginalSabreGpuRejection.Plan(plan.rawWidth,plan.rawHeight,
                        preparedReference.guideTexture, listOf(
                            Iris26975COriginalSabreGpuRejection.Alternative(
                                prepared.guideTexture,flow.flowTexture,
                                prepared.unblockerTexture,prepared.qmcNoiseTexture,
                                flow.flowScaleOffset))),referenceColor))
                val forward=own(Iris26975COriginalSabreGpuDilation.process(reverse))
                check(forward.mergeWeights.size==1){"$COMPONENT not one measured mask per alternate"}
                stream.append(Iris26972CDonorSabreGpuMerge.Frame(
                    prepared.extractedBayerTexture,flow.flowTexture,
                    prepared.covarianceTexture,forward.mergeWeights[0],
                    flow.flowScaleOffset,frame.raw.gains,
                    frame.raw.blackLevelsTimesGains,false))
                // Same donor mask ID goes into both merge and coverage, before release.
                // Quarter-res R8 target stays live; NO per-frame full-res mask retention.
                coverage.appendAlternate(forward.mergeWeights[0])
                release(forward);release(reverse);release(flow);release(gray);release(prepared)
            }
            hotPixels.requireComplete()
            check(stream.mergedCount == normalCount && coverage.consumed == normalCount)
            val realMasks=stream.actualMaskIds()
            val merged=own(stream.finish())
            release(stream)
            // The reference's identity R16F mask was consumed by the base draw and
            // deliberately destroyed; only alternate masks are sampled by normalize.
            Iris26972CDonorSabreGpuNormalize.normalizeAccumulatedStream(
                plan.rawWidth,plan.rawHeight,realMasks,merged,coverage)
            val measuredResidual=coverage.readMeasuredResidual()
            release(coverage)
            release(alignmentProducts);release(referenceGray)
            release(referenceColor);release(preparedReference)
            val resolved=Iris26972CDonorSabreGpuResolve.resolve(plan.resolve,merged)
            resolved.attachMeasuredResidual(measuredResidual)
            release(merged)
            return resolved
        } catch (cause:Throwable) {
            primaryFailure=cause
            throw cause
        } finally {
            // Keep the first actual GPU failure authoritative: EGL cleanup
            // can fail too, but must be attached as a suppressed cause, not
            // replace the shutter's real processing failure.
            var cleanupFailure:Throwable? = null
            for (obj in owned.asReversed()) {
                try { obj.close() } catch (error:Throwable) {
                    if(cleanupFailure==null) cleanupFailure=error
                    else cleanupFailure.addSuppressed(error)
                }
            }
            owned.clear()
            if(cleanupFailure!=null) {
                if(primaryFailure!=null) primaryFailure.addSuppressed(cleanupFailure)
                else throw cleanupFailure
            }
        }
    }
}
