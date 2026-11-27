package com.hinnka.mycamera.processor

import android.content.Context
import android.net.Uri
import com.hinnka.mycamera.processor.experimentc.Iris26975COriginalDonorEngine
import com.hinnka.mycamera.processor.experimentc.Iris26975COriginalRawBurst
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.io.File

/**
 * Iris shell -> authentic bjzhou 1.29.0 Experiment C engine.
 *
 * The incoming burst is untouched sensor RAW16 paired with its original
 * physical Camera2 TotalCaptureResults. No prototype Iris C Sabre/ColorDeveloper,
 * A/B processing, Spektra, DNG saver, or custom JPEG writer is called here.
 * The original engine owns every image-processing operation after acquisition.
 */
internal object Iris26972CCaptureToGallery {
    private const val COMPONENT = "26975 C original donor frozen RAW/gallery handoff"

    internal class OriginalOutput(
        val destination: File,
        val scratchDirectory: File,
        val physicalCameraId: String,
        val rotationDegrees: Int,
        val finalWidth: Int,
        val finalHeight: Int,
        val geometry: com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry,
        val sRgbIcc: ByteArray,
        val gainmapStrength: Float,
    ) {
        companion object {
            fun fromIrisShell(plan: Iris26972CStreamingFinish.Plan): OriginalOutput {
                require(plan.lutSelection.isNoLut) { "$COMPONENT original No LUT donor policy" }
                return OriginalOutput(
                    plan.output, plan.scratchDirectory, plan.physicalCameraId,
                    plan.displayOrientationDegrees,
                    plan.geometry.outputWidth, plan.geometry.outputHeight,
                    plan.geometry,
                    plan.sRgbIcc.copyOf(), plan.gainmapStrength,
                )
            }
        }
    }

    internal class OriginalTransaction(
        val shutter: Iris26972CContract.Plan,
        val rawBurst: Iris26975COriginalRawBurst,
        val output: OriginalOutput,
        val displayName: String,
        val shutterTimeMillis: Long,
        val previewThumbnail: android.graphics.Bitmap,
        val captureExposureCompensationEv: Float,
        val donorGeometry: com.hinnka.mycamera.processor.experimentc.Iris26977CPhysicalGeometry.Frozen,
        val sharpenBands: com.hinnka.mycamera.processor.experimentc.original129.processor.PhotonSharpenBands,
        val watermarkEnabled: Boolean,
        val denoise1291: com.particlesdevs.photoncamera.settings.Iris26998CDenoiseSettings.Frozen?,
    ) {
        fun validate() {
            rawBurst.validateAgainst(shutter)
            require((denoise1291 != null) == !shutter.night) { "26998 Photo-only settings ownership" }
            require(output.physicalCameraId == rawBurst.physicalCameraId &&
                output.rotationDegrees in listOf(0, 90, 180, 270) &&
                output.finalWidth > 0 && output.finalHeight > 0 &&
                output.finalWidth <= 16384 && output.finalHeight <= 16384 &&
                output.geometry.outputWidth == output.finalWidth &&
                output.geometry.outputHeight == output.finalHeight &&
                output.geometry.rotation == output.rotationDegrees &&
                output.sRgbIcc.size in 32..4_194_304 &&
                output.gainmapStrength.isFinite() &&
                output.gainmapStrength >= 0f &&
                output.destination.parentFile?.isDirectory == true &&
                output.scratchDirectory.isDirectory && !output.destination.exists() &&
                displayName.matches(Regex("[A-Za-z0-9][A-Za-z0-9_.-]*\\.jpg")) &&
                displayName.length in 1..95 && !displayName.contains("..") &&
                shutterTimeMillis > 0 && !previewThumbnail.isRecycled &&
                previewThumbnail.width > 0 && previewThumbnail.height > 0 &&
                captureExposureCompensationEv.isFinite() && donorGeometry.geometry === output.geometry &&
                sharpenBands.toList().all { it.isFinite() && it in 0f..2f }) { "$COMPONENT output/shutter/physical-lens mismatch" }
        }
    }

    /** Both committed rows remain owned until shutter terminal succeeds. */
    internal class Publication(val jpeg: Uri?, val dng: Uri?) {
        val primary: Uri = requireNotNull(jpeg ?: dng)
        fun revoke(context: Context) {
            var failure: Throwable? = null
            for (row in listOfNotNull(jpeg, dng)) try {
                com.particlesdevs.photoncamera.processing.experimentc.Iris26972CMediaStorePublisher
                    .revokeCommitted(context, row)
            } catch (t: Throwable) {
                if (failure == null) failure = t else failure.addSuppressed(t)
            }
            failure?.let { throw it }
        }
    }

    /** No Image or HAL plane escapes this call; spool deletes all RAW scratch files. */
    internal fun executeSpool(
        context: Context,
        spool: Iris26972CPhysicalRawSpool,
        shutter: Iris26972CContract.Plan,
        finish: Iris26972CStreamingFinish.Plan,
        displayName: String,
        shutterTimeMillis: Long,
        previewThumbnail: android.graphics.Bitmap?,
        captureExposureCompensationEv: Float,
        donorGeometry: com.hinnka.mycamera.processor.experimentc.Iris26977CPhysicalGeometry.Frozen,
        sharpenBands: FloatArray,
        offDng: Iris26986COffDng.Frozen?,
        rawSaver: Int,
        watermarkEnabled: Boolean,
        denoise1291: com.particlesdevs.photoncamera.settings.Iris26998CDenoiseSettings.Frozen?,
        stillLive: () -> Boolean = { true },
    ): Publication? {
        require(rawSaver in 0..2 && (offDng != null) == (rawSaver != 0))
        var jpeg: Uri? = null
        var dng: Uri? = null
        var primary: Throwable? = null
        try {
            spool.withOriginalDonorRawBurst { rawBurst ->
                rawBurst.validateAgainst(shutter)
                check(stillLive())
                if (rawSaver != 0) dng = Iris26986COffDng.save(context, requireNotNull(offDng),
                    rawBurst, finish.geometry, donorGeometry, displayName, shutterTimeMillis, stillLive)
                if (rawSaver != 2) jpeg = requireNotNull(executeOriginal(
                    context,
                    OriginalTransaction(
                        shutter, rawBurst, OriginalOutput.fromIrisShell(finish),
                        displayName, shutterTimeMillis, requireNotNull(previewThumbnail), captureExposureCompensationEv, donorGeometry,
                        com.hinnka.mycamera.processor.experimentc.original129.processor.PhotonSharpenBands(
                            sharpenBands[0], sharpenBands[1], sharpenBands[2]),
                        watermarkEnabled, denoise1291,
                    ), stillLive,
                )) { "$COMPONENT requested JPEG failed" }
                check(stillLive())
            }
            return Publication(jpeg, dng)
        } catch (failure: Throwable) {
            primary = failure
            if (jpeg != null || dng != null) try { Publication(jpeg, dng).revoke(context) }
                catch (revoke: Throwable) { failure.addSuppressed(revoke) }
            throw failure
        } finally {
            try { spool.close() } catch (cleanup: Throwable) {
                if (primary == null && (jpeg != null || dng != null)) try {
                    Publication(jpeg, dng).revoke(context)
                } catch (revoke: Throwable) { cleanup.addSuppressed(revoke) }
                if (primary != null) primary.addSuppressed(cleanup) else throw cleanup
            }
        }
    }

    internal fun executeOriginal(
        context: Context,
        tx: OriginalTransaction,
        stillLive: () -> Boolean = { true },
    ): Uri? {
        tx.validate() // real Camera2/raw provenance checked before GL
        if (!stillLive()) return null
        return Iris26975COriginalDonorEngine.processFrozen(context, tx, stillLive)
    }
}
