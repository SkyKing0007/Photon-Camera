package com.hinnka.mycamera.processor.experimentc

import android.content.Context
import android.graphics.Rect
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawHdrRenderResult
import kotlin.math.abs
import kotlin.math.roundToInt
import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.SystemClock
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.net.Uri
import com.hinnka.mycamera.processor.experimentc.original129.camera.associateMetadataCameraId
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
import com.hinnka.mycamera.processor.experimentc.original129.processor.PhotonSharpenTuning
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawNoiseProfileSelection
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackFrame
import com.hinnka.mycamera.processor.experimentc.original129.raw.DngNoiseProfile
import com.hinnka.mycamera.processor.experimentc.original129.raw.MgcSpatialGpuDenoiseMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawAdaptiveExposureMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawCaptureProfileCoordinator
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDemosaicProcessor
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDngCaptureProfilePreparer
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDngProfilePreparationOptions
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawMgcTuningSnr
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawMetadata
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawNoiseProfileManager
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawRenderingEngine
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawSceneExposureMath
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawToneMappingParameters
import com.hinnka.mycamera.processor.experimentc.original129.utils.PLog
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
        val photo1291 = !transaction.shutter.night
        val denoise1291 = transaction.denoise1291
        check(photo1291 == (denoise1291 != null))
        val photoCalibration1291 = if (photo1291) {
            characteristics.associateMetadataCameraId(burst.physicalCameraId)
            com.hinnka.mycamera.processor.experimentc.original129.raw.Iris26998RawColorCalibrationPolicy
                .fromCapture(characteristics, cameraResult, logDecision = true)
        } else null
        val renderer = RawDemosaicProcessor.getInstance()
        val physicalCrop = transaction.donorGeometry.physicalCrop
        val shutterGrid = output.geometry
        require(shutterGrid.rawWidth == reference.rawWidth && shutterGrid.rawHeight == reference.rawHeight &&
            shutterGrid.outputWidth == output.finalWidth && shutterGrid.outputHeight == output.finalHeight &&
            shutterGrid.rotation == output.rotationDegrees && physicalCrop.sourceWidth == reference.sensorWidth &&
            physicalCrop.sourceHeight == reference.sensorHeight) { "C donor frozen physical RAW dimensions mismatch" }
        val bounds = Rect(physicalCrop.sourceBounds).apply { offset(-reference.cropLeft, -reference.cropTop) }
        require(Rect(0, 0, reference.rawWidth, reference.rawHeight).contains(bounds)) {
            "C packed RAW does not cover donor physical crop"
        }
        // Match original GalleryManager: donor color space, rebased physical LSC, requested
        // AE compensation, and the same selected profile applied to capture metadata.
        val captureMetadata = physicalCrop.rebase(RawMetadata.create(
            width = reference.sensorWidth, height = reference.sensorHeight,
            characteristics = characteristics, captureResult = cameraResult,
            captureExposureCompensationEv = transaction.captureExposureCompensationEv,
            colorSpace = renderer.getRawColorSpace(RawRenderingEngine.AdobeCurve),
            photo1291 = photo1291,
        )).copy(exposureCompensation = transaction.captureExposureCompensationEv)
        check(captureMetadata.cfaPattern == rawFrame.cfaPattern &&
            captureMetadata.whiteLevel.toInt() == rawFrame.sensorWhiteLevel &&
            captureMetadata.whiteBalanceGains.size == 4 && captureMetadata.cameraWhite.size >= 3) {
            "Pinned donor/physical Camera2 metadata mismatch; cannot substitute Iris A/B"
        }
        val noiseSelection: RawNoiseProfileSelection =
            RawNoiseProfileManager(context).resolveSelection(null, captureMetadata)
        val metadata = captureMetadata.withNoiseProfileSelection(noiseSelection)
        val shutterCrop = physicalCrop.outputBounds
        val previewRotation = Math.floorMod(output.rotationDegrees -
            (characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION) ?: 0), 360)
        // Original CameraViewModel rotates the already display-oriented preview by this delta;
        // the original matcher receives the identical delta and the physical front-lens mirror flag.
        val originalPreview = transaction.previewThumbnail
        val tag = "CProSabre"
        var stageMs = SystemClock.elapsedRealtime()
        fun stage(name: String) {
            val now = SystemClock.elapsedRealtime()
            PLog.i(tag, "IRIS_26977_C_STAGE $name elapsedMs=${now - stageMs}")
            stageMs = now
        }
        check(stillLive()) { "C original Pro Sabre shutter session closed" }
        var stackResult: com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackResult? = null
        var mergedRgbReleased = false
        var mergedBayerReleased = false
        var mergedBufferReleased = false
        var denoisedSource: com.hinnka.mycamera.processor.experimentc.original129.processor.GpuLinearRgbSource? = null
        var sdr: android.graphics.Bitmap? = null
        var hdr: android.graphics.Bitmap? = null
        var gainmapContents: Bitmap? = null
        var neutralLookLuma: com.hinnka.mycamera.processor.experimentc.original129.hdr.LuminanceGainMap? = null
        val temporary = File(output.scratchDirectory, "original129_sabre_${transaction.shutterTimeMillis}.jpg")
        require(!temporary.exists()) { "C scratch name collision" }
        var capturePreview = originalPreview
        try {
            capturePreview = if (previewRotation == 0) originalPreview else Bitmap.createBitmap(
            originalPreview, 0, 0, originalPreview.width, originalPreview.height,
            Matrix().apply { postRotate(previewRotation.toFloat()) }, true,
        )
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
                    enableHdrFusion = false, // C owns a NORMAL-only same-exposure group.
                    photo1291 = photo1291,
                )
            } ?: error("Original bjzhou Pro Sabre GPU merge failed")
            val merged = checkNotNull(stackResult)
            check(merged.mergedFrameCount == frames.size && merged.isNormalizedSensorData &&
                merged.mgcDenoiseCorrelation?.size == 128 &&
                merged.mgcDenoiseReadNoise?.size == 3 &&
                merged.mgcDenoiseShotNoise?.size == 3) {
                "Original Sabre did not return a complete admitted-burst/noise solution"
            }
            stage("Sabre merge")
            check(merged.width == physicalCrop.width && merged.height == physicalCrop.height) {
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
                lumaStrengthScale = denoise1291?.luma ?: Iris26975COriginalDonorEngine.DEFAULT_LUMA,
                chromaStrengthScale = denoise1291?.chroma ?: Iris26975COriginalDonorEngine.DEFAULT_CHROMA,
                photo1291 = photo1291,
                lumaBands1291 = denoise1291?.lumaBands() ?: FloatArray(5) { 1f },
                chromaBands1291 = denoise1291?.chromaBands() ?: FloatArray(5) { 1f },
            ) ?: error("Original Sabre full-resolution chroma denoise failed")
            denoisedSource = denoised.gpuLinearRgbSource
            // Exact original GalleryManager ownership: release consumed fusion buffers before
            // profile/model/render work, retaining only the default-denoised GPU RGB lease.
            if (merged.gpuLinearRgbSource?.textureId != denoisedSource.textureId) {
                mergedRgbReleased = true
                renderer.releaseGpuLinearRgbSource(merged.gpuLinearRgbSource)
            }
            mergedBayerReleased = true
            renderer.releaseGpuBayerSource(merged.gpuBayerSource)
            mergedBufferReleased = true
            if (merged.fusedBayerUsesNativeAllocator) LargeDirectBuffer.free(merged.fusedBayerBuffer)
            merged.fusedBayerBuffer = null
            stage("full-resolution denoise")
            val tuningSnr = requireNotNull(RawMgcTuningSnr.read(RawMgcTuningSnr.write(
                emptyMap(), sharpen = merged.mgcSharpenTuningSnr, denoise = merged.mgcDenoiseTuningSnr,
            ))) { "Original merged capture tuning SNR unavailable" }
            PLog.i(tag, "IRIS_26977_C_NOISE selection=${noiseSelection.id} sharpenSnr=${tuningSnr.sharpen} " +
                "denoiseSnr=${tuningSnr.denoise} read=${merged.mgcDenoiseReadNoise?.contentToString()} " +
                "shot=${merged.mgcDenoiseShotNoise?.contentToString()}")
            val stackedMetadata = mergeMetadata.copy(
                blackLevel = FloatArray(4), whiteLevel = 65535f, frameCount = 1,
                mgcDenoiseCorrelation = null, mgcDenoiseReadNoise = null,
                mgcDenoiseShotNoise = null, mgcSpatialStrengthMap = null,
                mgcDenoiseTuningSnr = null,
            )
            val preparationOptions = RawDngProfilePreparationOptions(
                generatePhotonPgtm = RawToneMappingParameters.DEFAULT.usePhotonHdr,
                statsBounds = Rect(shutterCrop), // donor physical crop is the full merged native grid
                captureProfilePreparer = RawDngCaptureProfilePreparer { input ->
                    RawCaptureProfileCoordinator.prepareCaptureProfile(
                        renderer = renderer, context = context, input = input,
                        mode = RawAdaptiveExposureMode.resolve(
                            usePhotonHdr = RawToneMappingParameters.DEFAULT.usePhotonHdr,
                            useLegacyAutoExposure = false,
                        ),
                        aspectRatio = null, cropRegion = null,
                        rotation = output.rotationDegrees,
                        capturePreviewThumbnail = capturePreview, capturePortraitMask = null,
                        viewfinderMirroredHorizontally = characteristics.get(
                            CameraCharacteristics.LENS_FACING
                        ) == CameraCharacteristics.LENS_FACING_FRONT,
                        viewfinderPreviewToCaptureRotationDegrees = previewRotation,
                        statsBounds = Rect(shutterCrop),
                        rawNoiseProfileId = noiseSelection.id,
                        maxHdrRatio = RawSceneExposureMath.FAST_MOMENTS_MAX_HDR_RATIO,
                        useLensSensitivity = photo1291,
                    )
                },
            )
            val mergedNoise = requireNotNull(DngNoiseProfile.fromMergedModel(
                read = merged.mgcDenoiseReadNoise, shot = merged.mgcDenoiseShotNoise,
            )) { "Original merged DNG noise profile missing" }
            val preparation = RawProcessor.prepareRawDngProfile(
                rawBuffer = null, gpuLinearRgbSource = denoisedSource,
                fastMomentsRawStats = merged.fastMomentsRawStats,
                width = merged.width, height = merged.height,
                characteristics = characteristics, captureResult = cameraResult,
                captureExposureCompensationEv = transaction.captureExposureCompensationEv,
                cfaPattern = metadata.cfaPattern,
                blackLevel = FloatArray(4), whiteLevel = 65535,
                valueDomain = RawProcessor.RawBufferValueDomain.NORMALIZED_SENSOR_RANGE,
                baselineExposureEv = merged.baselineExposureEv,
                imageLayout = SuperResolutionDngWriter.ImageLayout.LINEAR_RAW_RGB,
                inputRowStepSamples = rowSamples, inputColStepSamples = 3,
                pixelsIncludeLensShadingCorrection = denoised.pixelsIncludeLensShadingCorrection,
                options = preparationOptions,
                defaultCrop = Rect(shutterCrop),
                physicalRawCrop = physicalCrop,
                noiseProfile = mergedNoise,
                photoCalibration1291 = photoCalibration1291,
            ) ?: error("Original DNG/Adobe/Photon PGTM profile construction failed")
            if (RawToneMappingParameters.DEFAULT.usePhotonHdr) {
                check(preparation.profileGainTableMap != null) {
                    "Original Photon HDR PGTM required; never render a substitute"
                }
            }
            stage("original Adobe HDRNet PGTM")
            val renderMetadata = RawProcessor.buildLinearDngRenderMetadata(
                width = merged.width, height = merged.height,
                characteristics = characteristics, captureResult = cameraResult,
                baseMetadata = stackedMetadata,
                defaultCrop = Rect(shutterCrop),
                rotation = output.rotationDegrees,
                profilePreparation = preparation,
                noiseProfile = mergedNoise,
                photoCalibration1291 = photoCalibration1291,
            )
            val embeddedPlan = SuperResolutionDngWriter.resolveEmbeddedRenderPlan(
                characteristics = characteristics,
                metadata = renderMetadata,
                imageLayout = SuperResolutionDngWriter.ImageLayout.LINEAR_RAW_RGB,
                profileGainTableMap = renderMetadata.profileGainTableMap,
                profileToneCurve = null,
                photoCalibration1291 = photoCalibration1291,
            ) ?: error("Original Adobe DNG embedded color profile unavailable")
            check(embeddedPlan.lookTable == null && embeddedPlan.hueSatMap == null &&
                embeddedPlan.toneCurveLut == null) {
                "Experiment C original Pro Sabre must never apply a film/look/profile LUT"
            }
            val sharpenTuning = PhotonSharpenTuning.DEFAULT.copy(amount = transaction.sharpenBands)
            PLog.i(tag, "IRIS_26982_C_MGC_SHARPEN physical=${burst.physicalCameraId} " +
                "band0=${transaction.sharpenBands.band0} band1=${transaction.sharpenBands.band1} " +
                "band2=${transaction.sharpenBands.band2} master=0.20")
            val rendered = renderer.processDngBufferForHdrSources(
                context = context, rawData = null,
                width = merged.width, height = merged.height,
                rowStride = rowSamples * Short.SIZE_BYTES,
                samplesPerPixel = 3, gpuLinearRgbSource = denoisedSource,
                metadata = renderMetadata,
                aspectRatio = null, cropRegion = null,
                rotation = output.rotationDegrees,
                sharpeningValue = Iris26975COriginalDonorEngine.DEFAULT_SHARPENING,
                photonSharpenTuning = sharpenTuning,
                denoiseValue = Iris26975COriginalDonorEngine.DEFAULT_LUMA,
                chromaDenoiseValue = Iris26975COriginalDonorEngine.DEFAULT_CHROMA,
                rawNoiseProfileId = noiseSelection.id,
                mgcTuningSnr = tuningSnr,
                embeddedDngRenderPlan = embeddedPlan,
                rawRenderingEngine = RawRenderingEngine.AdobeCurve,
                iris26993COffShadowLift = true,
                rawToneMappingParameters = RawToneMappingParameters.DEFAULT,
                rawOutputScale = 1f,
                rawOutputUpscaleMode = proSabre1x.outputUpscaleMode,
                // Donor RawOutputGeometry swaps the reference internally for
                // 90/270 rotation. Passing the already-rotated dimensions here
                // transposes portrait JPEGs and breaks their output size.
                rawPhysicalOutputSize = transaction.donorGeometry.nativeOutputSize,
                // C has exactly one output mode: original SDR base + original HDR reference.
                includeHdrReference = true,
                photonHdrRatio = preparation.hdrRatio,
                photonSourceToShortGain = preparation.finalShortGain,
                photonHdrNetPostExposureEv = preparation.hdrNetPostExposureEv,
                photonHdrNetInputExposureEv = preparation.hdrNetInputExposureEv,
            ) ?: error("Original Adobe SDR/linear-HDR renderer failed")
            stage("original Adobe SDR/HDR rendering and Lanczos-3")
            sdr = rendered.sdrBitmap
            hdr = rendered.hdrReferenceBitmap
            val originalSdr = checkNotNull(sdr)
            val finalSdr = Iris26978CFinalOutput.prepareSdr(originalSdr)
            sdr = finalSdr
            if (finalSdr !== originalSdr) originalSdr.recycle()
            stage("neutral encoded sRGB JPEG base preparation")
            check(sdr?.width == output.finalWidth && sdr?.height == output.finalHeight) {
                "Original 1x Lanczos-3 physical output does not match frozen Iris geometry"
            }
            val sourceHdr = checkNotNull(hdr) { "Original HDR reference missing; no estimated SDR fallback allowed" }
            val hdrBitmap = checkNotNull(normalizeRawHdrReferenceForGainmap(rendered, checkNotNull(sdr), sourceHdr))
            if (hdrBitmap !== sourceHdr && !sourceHdr.isRecycled) sourceHdr.recycle()
            hdr = hdrBitmap
            Iris26978CFinalOutput.validateHdrPair(checkNotNull(sdr), hdrBitmap)
            check(stillLive()) { "C session closed before rendered pixel validation" }
            validateNonBlackBase(checkNotNull(sdr), reference, shutterGrid)
            // The original GPU RAW gainmap needs an explicit LUT-ratio input.
            // No film/look LUT is applied: an exact identity sidecar leaves the
            // HDR-to-SDR gain computed solely by donor RAW HDR/SDR pixels.
            neutralLookLuma = NoLookLutRawGainmapSidecar.create(checkNotNull(sdr))
            Iris26978CFinalOutput.validateSidecar(checkNotNull(sdr), checkNotNull(neutralLookLuma))
            check(Jpeg444ExportEncoder.isSupported) { "Original native JPEG/R encoder unavailable" }
            val gainmap = rawGpuGainmapProducer.build(
                GainmapSourceSet(
                    sdrBase = checkNotNull(sdr),
                    lutLuminanceGainMap = neutralLookLuma,
                    hdrReference = HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB),
                    sourceKind = SourceKind.RAW,
                    confidence = 0.8f,
                ),
                HdrGainmapStrength.DEFAULT,
            ) ?: error("Original JPEG/R gainmap unavailable")
            gainmapContents = gainmap.gainmap.gainmapContents
            check(!checkNotNull(gainmapContents).isRecycled &&
                checkNotNull(gainmapContents).width == checkNotNull(neutralLookLuma).bitmap.width &&
                checkNotNull(gainmapContents).height == checkNotNull(neutralLookLuma).bitmap.height) {
                "Original gainmap result geometry invalid"
            }
            stage("original GPU gainmap")
            check(stillLive()) { "C session closed before original JPEG/R encoding" }
            // All donor processing and gain generation are complete. Only the final
            // publication raster and the corresponding local gain samples may change.
            if (transaction.watermarkEnabled) {
                val beforeOverlay = checkNotNull(sdr)
                sdr = Iris26994COffWatermark.apply(context, beforeOverlay, gainmap.gainmap)
                if (sdr !== beforeOverlay) beforeOverlay.recycle()
                stage("C OFF adaptive final watermark")
            }
            val info = CaptureInfo(
                exposureTime = rawFrame.exposureTimeNs,
                iso = rawFrame.sensitivityIso,
                aperture = cameraResult.get(CaptureResult.LENS_APERTURE),
                focalLength = cameraResult.get(CaptureResult.LENS_FOCAL_LENGTH),
                exposureBias = transaction.captureExposureCompensationEv,
                exposureCompensation = transaction.captureExposureCompensationEv,
                orientation = 0,
                imageWidth = checkNotNull(sdr).width,
                imageHeight = checkNotNull(sdr).height,
                captureTime = transaction.shutterTimeMillis,
            )
            check(Jpeg444ExportEncoder.write(
                checkNotNull(sdr), temporary,
                Iris26975COriginalDonorEngine.DEFAULT_JPEG_QUALITY,
                gainmapResult = gainmap,
                captureInfo = info,
                baseExifWriter = { base -> Iris26979CExif.write(base, info) },
            ) && Jpeg444ExportEncoder.isJpegR(temporary) && Iris26979CExif.verify(temporary, info)) {
                "Original bjzhou native JPEG 4:4:4/Q95 + JPEG/R packaging failed"
            }
            stage("original JPEG/R encoding")
            check(stillLive()) { "C shutter session closed before gallery publication" }
            // Donor rendered bitmap has the requested physical rotation. EXIF is NORMAL.
            Iris26975CDonorMediaStorePublisher.publish(
                context, temporary, transaction.displayName,
                transaction.shutterTimeMillis, 0,
            ) { stillLive() }.also { stage("MediaStore publication") }
        } finally {
            if (capturePreview !== originalPreview) capturePreview.recycle()
            temporary.delete()
            sdr?.recycle()
            hdr?.recycle()
            neutralLookLuma?.bitmap?.recycle()
            gainmapContents?.recycle()
            // All original GL texture owners, even failed jobs, return to their renderer.
            val fused = stackResult
            val final = denoisedSource
            if (final != null) renderer.releaseGpuLinearRgbSource(final)
            if (fused != null) {
                if (!mergedRgbReleased && fused.gpuLinearRgbSource?.textureId != final?.textureId) {
                    renderer.releaseGpuLinearRgbSource(fused.gpuLinearRgbSource)
                }
                if (!mergedBayerReleased) renderer.releaseGpuBayerSource(fused.gpuBayerSource)
                if (!mergedBufferReleased && fused.fusedBayerUsesNativeAllocator) {
                    LargeDirectBuffer.free(fused.fusedBayerBuffer)
                }
                fused.fusedBayerBuffer = null
            }
        }
    }

    private fun normalizeRawHdrReferenceForGainmap(
        rawResult: RawHdrRenderResult,
        sdrBitmap: Bitmap,
        hdrReferenceBitmap: Bitmap?,
    ): Bitmap? {
        val hdr = hdrReferenceBitmap ?: return null
        if (hdr.width == sdrBitmap.width && hdr.height == sdrBitmap.height) {
            return hdr
        }

        val cropped = cropFullRawHdrReferenceToOutput(rawResult, hdr)
        val aligned = cropped?.let { candidate ->
            alignHdrReferenceSizeToSdr(sdrBitmap, candidate, "raw_output_bounds").also { aligned ->
                if (aligned !== candidate && candidate !== hdr && !candidate.isRecycled) {
                    candidate.recycle()
                }
            }
        } ?: alignHdrReferenceSizeToSdr(sdrBitmap, hdr, "raw_size_fallback")

        PLog.w(
            "PhotoProcessor",
            "RAW HDR reference size normalized for gainmap: " +
                "sdr=${sdrBitmap.width}x${sdrBitmap.height}, " +
                "hdr=${hdr.width}x${hdr.height}, " +
                "raw=${rawResult.rawInputWidth}x${rawResult.rawInputHeight}, " +
                "bounds=${rawResult.outputSourceBounds}, " +
                "effectiveDefaultCrop=${rawResult.effectiveDefaultCrop}, " +
                "result=${aligned.width}x${aligned.height}"
        )
        return aligned
    }

    private fun cropFullRawHdrReferenceToOutput(
        rawResult: RawHdrRenderResult,
        hdrReferenceBitmap: Bitmap,
    ): Bitmap? {
        val rawWidth = rawResult.rawInputWidth.takeIf { it > 0 } ?: return null
        val rawHeight = rawResult.rawInputHeight.takeIf { it > 0 } ?: return null
        if (hdrReferenceBitmap.width != rawWidth || hdrReferenceBitmap.height != rawHeight) {
            return null
        }
        val sourceBounds = rawResult.outputSourceBounds ?: return null
        val safeBounds = Rect(sourceBounds)
        if (!safeBounds.intersect(Rect(0, 0, rawWidth, rawHeight)) || safeBounds.isEmpty) {
            return null
        }
        val cropped = Bitmap.createBitmap(
            hdrReferenceBitmap,
            safeBounds.left,
            safeBounds.top,
            safeBounds.width(),
            safeBounds.height()
        )
        val rotated = rotateBitmapForRawOutput(cropped, rawResult.outputRotation)
        if (rotated !== cropped && !cropped.isRecycled) {
            cropped.recycle()
        }
        return rotated
    }

    private fun rotateBitmapForRawOutput(input: Bitmap, rotation: Int): Bitmap {
        val normalized = ((rotation % 360) + 360) % 360
        if (normalized == 0) return input
        val matrix = Matrix().apply { postRotate(normalized.toFloat()) }
        return Bitmap.createBitmap(input, 0, 0, input.width, input.height, matrix, true)
    }

    private fun alignHdrReferenceSizeToSdr(
        sdrBitmap: Bitmap,
        hdrReferenceBitmap: Bitmap,
        label: String,
    ): Bitmap {
        val aspectAligned = cropHdrReferenceToSdrAspect(sdrBitmap, hdrReferenceBitmap, label)
        if (aspectAligned.width == sdrBitmap.width && aspectAligned.height == sdrBitmap.height) {
            return aspectAligned
        }
        PLog.w(
            "PhotoProcessor",
            "Scaling RAW HDR reference for gainmap ($label): " +
                "hdr=${aspectAligned.width}x${aspectAligned.height}, " +
                "sdr=${sdrBitmap.width}x${sdrBitmap.height}"
        )
        val scaled = Bitmap.createScaledBitmap(aspectAligned, sdrBitmap.width, sdrBitmap.height, true)
        if (aspectAligned !== hdrReferenceBitmap && !aspectAligned.isRecycled) {
            aspectAligned.recycle()
        }
        return scaled
    }

    private fun cropHdrReferenceToSdrAspect(
        sdrBitmap: Bitmap,
        hdrReferenceBitmap: Bitmap,
        label: String,
    ): Bitmap {
        if (sdrBitmap.width <= 0 || sdrBitmap.height <= 0 ||
            hdrReferenceBitmap.width <= 0 || hdrReferenceBitmap.height <= 0
        ) {
            return hdrReferenceBitmap
        }

        val targetAspect = sdrBitmap.width.toFloat() / sdrBitmap.height.toFloat()
        val sourceAspect = hdrReferenceBitmap.width.toFloat() / hdrReferenceBitmap.height.toFloat()
        val aspectError = abs(sourceAspect - targetAspect) / targetAspect
        if (aspectError <= 0.0015f) {
            return hdrReferenceBitmap
        }

        val cropWidth: Int
        val cropHeight: Int
        if (sourceAspect > targetAspect) {
            cropHeight = hdrReferenceBitmap.height
            cropWidth = (cropHeight * targetAspect).roundToInt()
                .coerceIn(1, hdrReferenceBitmap.width)
        } else {
            cropWidth = hdrReferenceBitmap.width
            cropHeight = (cropWidth / targetAspect).roundToInt()
                .coerceIn(1, hdrReferenceBitmap.height)
        }

        if (cropWidth == hdrReferenceBitmap.width && cropHeight == hdrReferenceBitmap.height) {
            return hdrReferenceBitmap
        }

        val left = (hdrReferenceBitmap.width - cropWidth).coerceAtLeast(0) / 2
        val top = (hdrReferenceBitmap.height - cropHeight).coerceAtLeast(0) / 2
        PLog.w(
            "PhotoProcessor",
            "Cropping RAW HDR reference to SDR aspect ($label): " +
                "hdr=${hdrReferenceBitmap.width}x${hdrReferenceBitmap.height}, " +
                "sdr=${sdrBitmap.width}x${sdrBitmap.height}, " +
                "crop=${left},${top},${cropWidth}x${cropHeight}"
        )
        return Bitmap.createBitmap(hdrReferenceBitmap, left, top, cropWidth, cropHeight)
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
