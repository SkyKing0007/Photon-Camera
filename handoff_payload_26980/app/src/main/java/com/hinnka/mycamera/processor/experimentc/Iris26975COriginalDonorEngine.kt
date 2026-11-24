package com.hinnka.mycamera.processor.experimentc

import android.content.Context
import android.net.Uri
import com.hinnka.mycamera.processor.Iris26972CCaptureToGallery
import com.hinnka.mycamera.processor.experimentc.original129.processor.RawStackFrame
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract

/**
 * The single Experiment C processing boundary. Iris owns capture and final gallery
 * entry; the original pinned bjzhou engine must own EVERYTHING between them.
 *
 * No Iris A/B, Spektra, DNG saver, reconstructed Sabre, custom color-developer,
 * or old C UHDR writer is a permitted implementation of this port. The exact
 * physical RAW16 and Camera2 source reaches this gateway without prototype
 * C Sabre GPU planning or custom color calibration.
 *
 * The original processing chain is now SOURCE-WIRED, but remains unavailable at
 * runtime until GitHub Actions compiles Android Kotlin/Java/shaders/NDK and proves
 * the donor JNI/Exif ABI. This fails CLOSED, never to an A/B fallback.
 */
internal object Iris26975COriginalDonorEngine {
    const val PINNED_REVISION = "0a8a11defe7d932d8c8a729120a4d5f159e9d677"
    const val DONOR_VERSION = "bjzhou/PhotonCamera:1.29.0"
    const val DEFAULT_LUMA = 0.00f
    const val DEFAULT_CHROMA = 0.50f
    const val DEFAULT_SHARPENING = 0.20f
    const val DEFAULT_JPEG_QUALITY = 95

    /**
     * No global mutable engine registration: Camera2 transactions and GL state
     * must be strictly owned by their one shutter session, not borrowed from A/B.
     */
    internal interface Engine {
        fun process(
            context: Context,
            transaction: Iris26972CCaptureToGallery.OriginalTransaction,
            frames: List<RawStackFrame>,
            proSabre1x: Iris26975CProSabre1xSelection,
            stillLive: () -> Boolean,
        ): Uri?
    }

    /** Source-connected only; production gate stays closed until full Actions proof. */
    private val originalEngine: Engine? = Iris26975CPinnedDonorProEngine

    fun processFrozen(
        context: Context,
        transaction: Iris26972CCaptureToGallery.OriginalTransaction,
        stillLive: () -> Boolean,
    ): Uri? {
        // The proven 26974 Iris shutter already has a separate controlled-device-trial
        // admission gate. Keep PRODUCTION_READY false until Actions and real image parity,
        // but do not dead-end every admitted C trial at this mandatory source boundary.
        // Any original JNI/GL/RAW/JPEG failure still throws: there is NO A/B fallback.
        check(Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED) {
            "C original bjzhou controlled trial is disabled; no alternate processing"
        }
        check(Iris26972CContract.LUMA_DENOISE == DEFAULT_LUMA &&
            Iris26972CContract.CHROMA_DENOISE == DEFAULT_CHROMA &&
            Iris26972CContract.SHARPENING == DEFAULT_SHARPENING &&
            Iris26972CContract.JPEG_QUALITY == DEFAULT_JPEG_QUALITY &&
            Iris26972CContract.JPEG_444 &&
            Iris26972CContract.ULTRA_HDR_ENABLED &&
            !Iris26972CContract.HEIC_ENABLED &&
            Iris26972CContract.INTERNAL_RAISR_SCALE == 1 &&
            Iris26972CContract.FINAL_OUTPUT_SCALE == 1) {
            "C donor settings differ from the original screenshot acceptance"
        }
        val engine = checkNotNull(originalEngine) {
            "C original donor engine not installed; fail closed"
        }
        if (!stillLive()) return null
        val proSabre1x = Iris26975CProSabre1xSelection.forFrozen(transaction)
        return Iris26975CDonorStackFrameAdapter.withOriginalDonorFrames(transaction.rawBurst) { frames ->
            check(frames.size == proSabre1x.normalFrameCount) {
                "C must pass the entire shutter-frozen 2..30 RAW burst to original Pro Sabre"
            }
            engine.process(context, transaction, frames, proSabre1x, stillLive)
        }
    }
}
