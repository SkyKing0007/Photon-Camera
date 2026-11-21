package com.hinnka.mycamera.processor

import android.content.Context
import android.net.Uri
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract

/**
 * Isolated end-to-end C ownership boundary, from one fully frozen NORMAL RAW
 * burst to ONE visible gallery JPEG/R. No A/B Camera2 callbacks, fallback
 * reconstructor, synthetic physical metadata, or parallel JPEG writer.
 *
 * An isolated shutter source dispatcher calls C; production stays
 * disabled until the original guarded Android build and real-device tests.
 */
internal object Iris26972CCaptureToGallery {
    private const val COMPONENT = "26972 C frozen RAW-to-gallery transaction"

    internal class FrozenTransaction(
        val shutter: Iris26972CContract.Plan,
        val burst: Iris26972CDonorSabreGpuBurst.Plan,
        val calibration: Iris26972CCamera2Calibration.Frozen,
        val lensShading: Iris26972CPhysicalLensShading.Frozen,
        val finish: Iris26972CStreamingFinish.Plan,
        val displayName: String,
        val shutterTimeMillis: Long,
    )

    /** Must reject inconsistent provenance BEFORE allocating a single GPU pixel. */
    internal fun validate(tx: FrozenTransaction) {
        Iris26972CDonorSabreGpuBurst.validate(tx.burst, metadataOnly = true)
        val first = tx.burst.frozenFrames.first()
        require(tx.shutter.frameCount == tx.burst.frozenFrames.size &&
            tx.shutter.physicalLensId == first.physicalCameraId &&
            tx.shutter.referenceTimestampNs == tx.burst.frozenReferenceTimestampNs &&
            tx.finish.physicalCameraId == first.physicalCameraId &&
            tx.shutterTimeMillis > 0L &&
            tx.displayName.length in 1..95 &&
            tx.displayName.matches(Regex("[A-Za-z0-9][A-Za-z0-9_.-]*\\.jpg")) &&
            !tx.displayName.contains("..")) {
            "$COMPONENT shutter/RAW/color/publisher identity mismatch"
        }
        // The shutter freeze and Sabre GPU model MUST agree on role and every
        // actual exposure; relabeling an auxiliary bracket as NORMAL cannot pass.
        Iris26972CContract.validateBurst(tx.shutter,
            tx.burst.frozenFrames.map { Iris26972CContract.Role.valueOf(it.role.name) },
            tx.burst.frozenFrames.map { it.sensorTimestampNs },
            tx.burst.frozenFrames.map { it.exposureProduct })
        tx.calibration.colorPlan(tx.burst.rawWidth, tx.burst.rawHeight, tx.burst)
        tx.lensShading.requireMatches(first.physicalCameraId, tx.burst.frozenReferenceTimestampNs)
        Iris26972CStreamingFinish.validate(tx.finish, tx.burst.rawWidth, tx.burst.rawHeight)
    }

    /**
     * Independent C-only streaming owner: the shutter's RAW Images were each
     * closed as soon as copied; no ImageReader allocation survives this call.
     * The spool verifies all exact Camera2 timestamps and SHA-256 payloads
     * before constructing the same frozen transaction as the live Image owner.
     *
     * The caller provides a real EGL owner on this thread. This is NOT a
     * shortcut around the disabled production gate or Android verification.
     */
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
            committed = spool.withFrozenBurst { burst, calibration, lensShading ->
                execute(context, FrozenTransaction(shutter, burst, calibration,
                    lensShading, finish, displayName, shutterTimeMillis), stillLive)
            }
            return committed
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            try {
                spool.close()
            } catch (cleanup: Throwable) {
                // A successful JPEG/R commit cannot silently survive if its
                // source RAW cleanup subsequently fails. Revoke the C row.
                val row = committed
                if (row != null) try {
                    com.particlesdevs.photoncamera.processing.experimentc
                        .Iris26972CMediaStorePublisher.revokeCommitted(context, row)
                } catch (revoke: Throwable) { cleanup.addSuppressed(revoke) }
                if (primary != null) primary.addSuppressed(cleanup) else throw cleanup
            }
        }
    }

    /**
     * Only C's private 1x 4:4:4 JPEG/R can become visible. The color GPU result
     * is released on the original EGL thread after pending-row commit/rollback.
     * The disabled production gate cannot be bypassed by calling this directly.
     */
    internal fun execute(context: Context, tx: FrozenTransaction,
        stillLive: () -> Boolean = { true }): Uri? {
        validate(tx)
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED || !stillLive()) return null
        // No synthetic texture ID may masquerade as real physical lens shading.
        // GLES ownership begins only after pure metadata has passed and ends
        // even when RAW fusion, JPEG/R or provider publication throws.
        return tx.lensShading.allocate().use { shading ->
            val renderBurst=tx.burst.copy(resolve=
                tx.burst.resolve.copy(lensShadingTexture=shading.id))
            Iris26972CDonorSabreGpuBurst.processWithFrozenCamera2Color(
                renderBurst, tx.calibration).use { color ->
                Iris26972CStreamingFinish.publishToMediaStore(tx.finish, color,
                    context, tx.displayName, tx.shutterTimeMillis, stillLive)
            }
        }
    }
}
