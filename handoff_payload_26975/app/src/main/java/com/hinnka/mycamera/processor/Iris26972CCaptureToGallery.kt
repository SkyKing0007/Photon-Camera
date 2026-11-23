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
    ) {
        fun validate() {
            rawBurst.validateAgainst(shutter)
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
                shutterTimeMillis > 0) { "$COMPONENT output/shutter/physical-lens mismatch" }
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
        stillLive: () -> Boolean = { true },
    ): Uri? {
        var committed: Uri? = null
        var primary: Throwable? = null
        try {
            committed = spool.withOriginalDonorRawBurst { rawBurst ->
                executeOriginal(
                    context,
                    OriginalTransaction(
                        shutter, rawBurst, OriginalOutput.fromIrisShell(finish),
                        displayName, shutterTimeMillis,
                    ),
                    stillLive,
                )
            }
            return committed
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            try {
                spool.close()
            } catch (cleanup: Throwable) {
                if (committed != null) try {
                    com.particlesdevs.photoncamera.processing.experimentc
                        .Iris26972CMediaStorePublisher.revokeCommitted(context, committed)
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
