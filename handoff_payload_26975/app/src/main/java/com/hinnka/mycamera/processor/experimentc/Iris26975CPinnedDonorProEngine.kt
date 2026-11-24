package com.hinnka.mycamera.processor.experimentc

import android.content.Context
import android.graphics.Rect
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.net.Uri
import android.util.Size
import com.hinnka.mycamera.processor.Iris26972CCaptureToGallery
import com.hinnka.mycamera.processor.experimentc.original129.camera.CaptureInfo
import com.hinnka.mycamera.processor.experimentc.original129.gallery.Jpeg444ExportEncoder
import com.hinnka.mycamera.processor.experimentc.original129.hdr.GainmapSourceSet
import com.hinnka.mycamera.processor.experimentc.original129.hdr.HdrBuffer
import com.hinnka.mycamera.processor.experimentc.original129.hdr.HdrBufferEncoding
import com.hinnka.mycamera.processor.experimentc.original129.hdr.SourceKind
import com.hinnka.mycamera.processor.experimentc.original129.hdr.GpuReferenceGainmapProducer
import com.hinnka.mycamera.processor.experimentc.original129.hdr.HdrGainmapStrength
import com.hinnka.mycamera.processor.experimentc.original129.hdr.NoLookLutRawGainmapSidecar
import com.hinnka.mycamera.processor.experimentc.original129.processor.GpuLinearRgbStorage
import com.hinnka.mycamera.processor.experimentc.original129.processor.MultiFrameStacker
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawNoiseProfileSelection
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackFrame
import com.hinnka.mycamera.processor.experimentc.original129.raw.DngNoiseProfile
import com.hinnka.mycamera.processor.experimentc.original129.raw.MgcSpatialGpuDenoiseMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawAdaptiveExposureMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawCaptureProfileCoordinator
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDemosaicProcessor
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDngCaptureProfilePreparer
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDngProfilePreparationOptions
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawMetadata
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawNoiseProfileManager
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawRenderingEngine
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawSceneExposureMath
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawToneMappingParameters
import com.hinnka.mycamera.processor.experimentc.original129.utils.LargeDirectBuffer
import com.hinnka.mycamera.processor.experimentc.original129.utils.RawProcessor
import com.hinnka.mycamera.processor.experimentc.original129.utils.SuperResolutionDngWriter
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975CDonorMediaStorePublisher
import kotlinx.coroutines.runBlocking
import java.io.File

/**
 * Original Pro Mode pipeline, C-only. No alternative algorithms or A/B dispatch.
 * This is source-integrated, NOT build-proven; the externally controlled production
 * gate must remain FALSE until the original JNI/Java ABI and Actions assembly pass.
 */
internal object Iris26975CPinnedDonorProEngine : Iris26975COriginalDonorEngine.Engine {
    // Reuse the donor GPU context/worker across C captures; do not spawn one per JPEG.
    private val rawGpuGainmapProducer = GpuReferenceGainmapProducer()
    override fun process(
        context: Context,
        transaction: Iris26972CCaptureToGallery.OriginalTransaction,
        frames: List<RawStackFrame>,
        proSabre1x: Iris26975CProSabre1xSelection,
        stillLive: () -> Boolean,
    ): Uri? = runBlocking {
        transaction.validate()
        require(frames.size == proSabre1x.normalFrameCount && frames.size in 2..30)
        val burst = transaction.rawBurst
        val reference = burst.reference
        val rawFrame = reference.metadata
        val output = transaction.output
        val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        val characteristics = cameraManager.getCameraCharacteristics(burst.physicalCameraId)
        val cameraResult: CaptureResult = reference.physicalCaptureResult
        val metadata = RawMetadata.create(
            width = reference.rawWidth, height = reference.rawHeight,
            characteristics = characteristics, captureResult = cameraResult,
        )
        check(metadata.cfaPattern == rawFrame.cfaPattern &&
            metadata.whiteLevel.toInt() == rawFrame.sensorWhiteLevel &&
            metadata.whiteBalanceGains.size == 4 &&
            metadata.cameraWhite.size >= 3) {
            "Pinned donor/physical Camera2 metadata mismatch; cannot substitute Iris A/B"
        }
        // The spool's RAW16 already represents this exact even-origin physical crop.
        // Never reinterpret cropped pixels as another lens or a synthetic CFA texture.
        val bounds = Rect(0, 0, reference.rawWidth, reference.rawHeight)
        val shutterGrid = output.geometry
        require(shutterGrid.rawWidth == reference.rawWidth &&
            shutterGrid.rawHeight == reference.rawHeight &&
            shutterGrid.outputWidth == output.finalWidth &&
            shutterGrid.outputHeight == output.finalHeight &&
            shutterGrid.rotation == output.rotationDegrees) {
            "Donor 1x output must honor shutter-frozen physical RAW geometry"
        }
        // Donor DNG HDR-source rendering treats DefaultCrop as authoritative;
        // passing a legacy cropRegion would be silently ignored. Carry this
        // even-origin sensor crop into both original PGTM preparation and SDR/HDR
        // output, without modifying the donor algorithm or any A/B processor.
        val shutterCrop = Rect(shutterGrid.cropLeft, shutterGrid.cropTop,
            shutterGrid.cropRight, shutterGrid.cropBottom)
        val noiseSelection: RawNoiseProfileSelection =
            RawNoiseProfileManager(context).resolveSelection(null, metadata)
        check(stillLive()) { "C original Pro Sabre shutter session closed" }
        val renderer = RawDemosaicProcessor.getInstance()
        var stackResult: com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackResult? = null
        var denoisedSource: com.hinnka.mycamera.processor.experimentc.original129.processor.GpuLinearRgbSource? = null
        var sdr: android.graphics.Bitmap? = null
        var hdr: android.graphics.Bitmap? = null
        var neutralLookLuma: com.hinnka.mycamera.processor.experimentc.original129.hdr.LuminanceGainMap? = null
        val temporary = File(output.scratchDirectory, "original129_sabre_${transaction.shutterTimeMillis}.jpg")
        require(!temporary.exists()) { "C scratch name collision" }
        try {
            stackResult = renderer.runStackingOnGlContext {
                MultiFrameStacker.processBurstRaw(
                    frames = frames, cfaPattern = metadata.cfaPattern,
                    outputMode = proSabre1x.stackOutputMode,
                    mergeMethod = proSabre1x.mergeMethod,
                    masterBlackLevel = metadata.blackLevel.copyOf(),
                    whiteLevel = rawFrame.sensorWhiteLevel,
                    whiteBalanceGains = metadata.whiteBalanceGains.copyOf(),
                    cameraWhite = metadata.cameraWhite.copyOf(),
                    noiseProfileSelection = noiseSelection,
                    lensShading = metadata.lensShadingMap,
                    lensShadingWidth = metadata.lensShadingMapWidth,
                    lensShadingHeight = metadata.lensShadingMapHeight,
                    applyLensShadingCorrection = true,
                    sourceBounds = bounds,
                    useCurrentGlContext = true,
                    exportGpuLinearRgbSource = true,
                    gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
                )
            } ?: error("Original bjzhou Pro Sabre GPU merge failed")
            val merged = checkNotNull(stackResult)
            check(merged.mergedFrameCount == frames.size && merged.isNormalizedSensorData &&
                merged.mgcDenoiseCorrelation?.size == 128 &&
                merged.mgcDenoiseReadNoise?.size == 3 &&
                merged.mgcDenoiseShotNoise?.size == 3) {
                "Original Sabre did not return a complete admitted-burst/noise solution"
            }
            check(merged.width == shutterGrid.rawWidth &&
                merged.height == shutterGrid.rawHeight) {
                "Original Pro Sabre must preserve native physical 1x RAW dimensions"
            }
            val samples = merged.inputColStepSamples ?: 3
            check(samples == 3 && merged.width > 0 && merged.height > 0)
            val rowSamples = merged.inputRowStepSamples ?: merged.width * samples
            val mergeMetadata = metadata.copy(
                width = merged.width, height = merged.height,
                blackLevel = merged.blackLevel.copyOf(), whiteLevel = 65535f,
                frameCount = merged.mergedFrameCount,
                mgcDenoiseCorrelation = merged.mgcDenoiseCorrelation,
                mgcDenoiseReadNoise = merged.mgcDenoiseReadNoise,
                mgcDenoiseShotNoise = merged.mgcDenoiseShotNoise,
                mgcSpatialStrengthMap = merged.mgcSpatialStrengthMap,
                mgcDenoiseTuningSnr = merged.mgcDenoiseTuningSnr,
                mgcSharpenTuningSnr = merged.mgcSharpenTuningSnr,
                mgcSharpenAttenuationScale = merged.mgcSharpenAttenuationScale,
            )
            val denoised = renderer.processMgcSpatialGpuLinearRgb(
                context = context, rawData = merged.fusedBayerBuffer,
                width = merged.width, height = merged.height,
                rowStride = rowSamples * Short.SIZE_BYTES,
                samplesPerPixel = samples,
                gpuLinearRgbSource = merged.gpuLinearRgbSource,
                gpuBayerSource = merged.gpuBayerSource,
                metadata = mergeMetadata,
                sourcePixelsIncludeLensShadingCorrection = merged.lensShadingCorrectionApplied,
                applyLensShadingCorrection = true,
                mode = MgcSpatialGpuDenoiseMode.SABRE_DEFAULT,
                lumaStrengthScale = Iris26975COriginalDonorEngine.DEFAULT_LUMA,
                chromaStrengthScale = Iris26975COriginalDonorEngine.DEFAULT_CHROMA,
            ) ?: error("Original Sabre full-resolution chroma denoise failed")
            denoisedSource = denoised.gpuLinearRgbSource
            val stackedMetadata = mergeMetadata.copy(
                blackLevel = FloatArray(4), whiteLevel = 65535f, frameCount = 1,
                mgcDenoiseCorrelation = null, mgcDenoiseReadNoise = null,
                mgcDenoiseShotNoise = null, mgcSpatialStrengthMap = null,
                mgcDenoiseTuningSnr = null,
            )
            val preparationOptions = RawDngProfilePreparationOptions(
                generatePhotonPgtm = RawToneMappingParameters.DEFAULT.usePhotonHdr,
                captureProfilePreparer = RawDngCaptureProfilePreparer { input ->
                    RawCaptureProfileCoordinator.prepareCaptureProfile(
                        renderer = renderer, context = context, input = input,
                        mode = RawAdaptiveExposureMode.resolve(
                            usePhotonHdr = RawToneMappingParameters.DEFAULT.usePhotonHdr,
                            useLegacyAutoExposure = false,
                        ),
                        aspectRatio = null, cropRegion = null,
                        rotation = output.rotationDegrees,
                        capturePreviewThumbnail = null, capturePortraitMask = null,
                        viewfinderMirroredHorizontally = characteristics.get(
                            CameraCharacteristics.LENS_FACING
                        ) == CameraCharacteristics.LENS_FACING_FRONT,
                        viewfinderPreviewToCaptureRotationDegrees = 0,
                        statsBounds = null,
                        rawNoiseProfileId = noiseSelection.id,
                        maxHdrRatio = RawSceneExposureMath.FAST_MOMENTS_MAX_HDR_RATIO,
                    )
                },
            )
            val mergedNoise = DngNoiseProfile.fromMergedModel(
                read = merged.mgcDenoiseReadNoise, shot = merged.mgcDenoiseShotNoise,
            )
            val preparation = RawProcessor.prepareRawDngProfile(
                rawBuffer = null, gpuLinearRgbSource = denoisedSource,
                fastMomentsRawStats = merged.fastMomentsRawStats,
                width = merged.width, height = merged.height,
                characteristics = characteristics, captureResult = cameraResult,
                cfaPattern = metadata.cfaPattern,
                blackLevel = FloatArray(4), whiteLevel = 65535,
                valueDomain = RawProcessor.RawBufferValueDomain.NORMALIZED_SENSOR_RANGE,
                baselineExposureEv = merged.baselineExposureEv,
                imageLayout = SuperResolutionDngWriter.ImageLayout.LINEAR_RAW_RGB,
                inputRowStepSamples = rowSamples, inputColStepSamples = 3,
                pixelsIncludeLensShadingCorrection = denoised.pixelsIncludeLensShadingCorrection,
                options = preparationOptions,
                defaultCrop = Rect(shutterCrop),
                noiseProfile = mergedNoise,
            ) ?: error("Original DNG/Adobe/Photon PGTM profile construction failed")
            if (RawToneMappingParameters.DEFAULT.usePhotonHdr) {
                check(preparation.profileGainTableMap != null) {
                    "Original Photon HDR PGTM required; never render a substitute"
                }
            }
            val renderMetadata = RawProcessor.buildLinearDngRenderMetadata(
                width = merged.width, height = merged.height,
                characteristics = characteristics, captureResult = cameraResult,
                baseMetadata = stackedMetadata,
                defaultCrop = Rect(shutterCrop),
                rotation = output.rotationDegrees,
                profilePreparation = preparation,
                noiseProfile = mergedNoise,
            )
            val embeddedPlan = SuperResolutionDngWriter.resolveEmbeddedRenderPlan(
                characteristics = characteristics,
                metadata = renderMetadata,
                imageLayout = SuperResolutionDngWriter.ImageLayout.LINEAR_RAW_RGB,
                profileGainTableMap = renderMetadata.profileGainTableMap,
                profileToneCurve = null,
            ) ?: error("Original Adobe DNG embedded color profile unavailable")
            check(embeddedPlan.lookTable == null && embeddedPlan.hueSatMap == null &&
                embeddedPlan.toneCurveLut == null) {
                "Experiment C original Pro Sabre must never apply a film/look/profile LUT"
            }
            val rendered = renderer.processDngBufferForHdrSources(
                context = context, rawData = null,
                width = merged.width, height = merged.height,
                rowStride = rowSamples * Short.SIZE_BYTES,
                samplesPerPixel = 3, gpuLinearRgbSource = denoisedSource,
                metadata = renderMetadata,
                aspectRatio = null, cropRegion = null,
                rotation = output.rotationDegrees,
                sharpeningValue = Iris26975COriginalDonorEngine.DEFAULT_SHARPENING,
                denoiseValue = 0f, chromaDenoiseValue = 1f,
                rawNoiseProfileId = noiseSelection.id,
                embeddedDngRenderPlan = embeddedPlan,
                rawRenderingEngine = RawRenderingEngine.AdobeCurve,
                rawToneMappingParameters = RawToneMappingParameters.DEFAULT,
                rawOutputScale = 1f,
                rawOutputUpscaleMode = proSabre1x.outputUpscaleMode,
                // Donor RawOutputGeometry swaps the reference internally for
                // 90/270 rotation. Passing the already-rotated dimensions here
                // transposes portrait JPEGs and breaks their output size.
                rawPhysicalOutputSize = Size(shutterGrid.rawWidth, shutterGrid.rawHeight),
                // C has exactly one output mode: original SDR base + original HDR reference.
                includeHdrReference = true,
                photonHdrRatio = preparation.hdrRatio,
                photonSourceToShortGain = preparation.finalShortGain,
                photonHdrNetPostExposureEv = preparation.hdrNetPostExposureEv,
                photonHdrNetInputExposureEv = preparation.hdrNetInputExposureEv,
            ) ?: error("Original Adobe SDR/linear-HDR renderer failed")
            sdr = rendered.sdrBitmap
            hdr = rendered.hdrReferenceBitmap
            check(sdr?.width == output.finalWidth && sdr?.height == output.finalHeight) {
                "Original 1x Lanczos-3 physical output does not match frozen Iris geometry"
            }
            val hdrBitmap = checkNotNull(hdr) {
                "Original HDR reference missing; no estimated SDR fallback allowed"
            }
            check(stillLive()) { "C session closed before rendered pixel validation" }
            validateNonBlackBase(checkNotNull(sdr), reference, shutterGrid)
            // The original GPU RAW gainmap needs an explicit LUT-ratio input.
            // No film/look LUT is applied: an exact identity sidecar leaves the
            // HDR-to-SDR gain computed solely by donor RAW HDR/SDR pixels.
            neutralLookLuma = NoLookLutRawGainmapSidecar.create(checkNotNull(sdr))
            val gainmap = rawGpuGainmapProducer.build(
                GainmapSourceSet(
                    sdrBase = checkNotNull(sdr),
                    lutLuminanceGainMap = neutralLookLuma,
                    hdrReference = HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB),
                    sourceKind = SourceKind.RAW,
                ),
                HdrGainmapStrength.DEFAULT,
            ) ?: error("Original JPEG/R gainmap unavailable")
            check(stillLive()) { "C session closed before original JPEG/R encoding" }
            val info = CaptureInfo(
                exposureTime = rawFrame.exposureTimeNs,
                iso = rawFrame.sensitivityIso,
                orientation = output.rotationDegrees,
                imageWidth = checkNotNull(sdr).width,
                imageHeight = checkNotNull(sdr).height,
                captureTime = transaction.shutterTimeMillis,
            )
            check(Jpeg444ExportEncoder.write(
                checkNotNull(sdr), temporary,
                Iris26975COriginalDonorEngine.DEFAULT_JPEG_QUALITY,
                gainmapResult = gainmap,
                captureInfo = info,
            ) && Jpeg444ExportEncoder.isJpegR(temporary)) {
                "Original bjzhou native JPEG 4:4:4/Q95 + JPEG/R packaging failed"
            }
            check(stillLive()) { "C shutter session closed before gallery publication" }
            // Donor rendered bitmap has the requested physical rotation. EXIF is NORMAL.
            Iris26975CDonorMediaStorePublisher.publish(
                context, temporary, transaction.displayName,
                transaction.shutterTimeMillis, 0,
            ) { stillLive() }
        } finally {
            temporary.delete()
            sdr?.recycle()
            hdr?.recycle()
            neutralLookLuma?.bitmap?.recycle()
            // All original GL texture owners, even failed jobs, return to their renderer.
            val fused = stackResult
            val final = denoisedSource
            if (final != null) renderer.releaseGpuLinearRgbSource(final)
            if (fused != null) {
                if (fused.gpuLinearRgbSource?.textureId != final?.textureId) {
                    renderer.releaseGpuLinearRgbSource(fused.gpuLinearRgbSource)
                }
                renderer.releaseGpuBayerSource(fused.gpuBayerSource)
                if (fused.fusedBayerUsesNativeAllocator) {
                    LargeDirectBuffer.free(fused.fusedBayerBuffer)
                }
                fused.fusedBayerBuffer = null
            }
        }
    }

    /** Reject an exactly black SDR base only when the actual same-crop RAW has
     * meaningful signal. No exposure rescue, color change or substitution.
     * A sparse positive probe avoids a full scan for normal photos; a suspected
     * black image is confirmed across every row before rejection. */
    private fun validateNonBlackBase(bitmap: android.graphics.Bitmap,
            reference: Iris26975COriginalRawBurst.Frame,
            geometry: com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry) {
        if (bitmap.isRecycled) error("C donor returned a recycled SDR bitmap")
        for (iy in 0 until 8) for (ix in 0 until 8) {
            val x = (ix * 2 + 1) * bitmap.width / 16
            val y = (iy * 2 + 1) * bitmap.height / 16
            if (bitmap.getPixel(x,y) and 0x00ffffff != 0) return
        }
        val phase = when(reference.metadata.cfaPattern) {
            0 -> intArrayOf(0,1,2,3); 1 -> intArrayOf(1,0,3,2)
            2 -> intArrayOf(2,3,0,1); 3 -> intArrayOf(3,2,1,0)
            else -> error("C unknown CFA in rendered-pixel guard")
        }
        val canonical = reference.metadata.copyCanonicalBlackForAudit()
        val raw = com.particlesdevs.photoncamera.processing.experimentc.Iris26975CRawHighlightMeter.measure(
            reference.raw16(), reference.rawWidth * 2, 2,
            geometry.cropLeft,geometry.cropTop,geometry.cropRight,geometry.cropBottom,
            reference.metadata.sensorWhiteLevel,FloatArray(4) { canonical[phase[it]] })
        // Preserve genuinely dark photographs. This is deliberately not a general IQ metric.
        if (raw.mean < 0.08f) return
        val row = IntArray(bitmap.width)
        for (y in 0 until bitmap.height) {
            bitmap.getPixels(row,0,bitmap.width,0,y,bitmap.width,1)
            if (row.any { (it and 0x00ffffff) != 0 }) return
        }
        error("C original donor SDR was exactly black despite substantial physical RAW signal")
    }
}
