package com.hinnka.mycamera.processor

import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CaptureRequest
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.media.Image
import android.media.ImageReader
import android.net.Uri
import android.util.Log
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.Executors
import kotlin.math.max

/**
 * Independent C-only Camera2 shutter callbacks. No A/B processing,
 * legacy JPEG owner, synthetic RAW or YUV fallback is used.
 *
 * A shutter may own exact timestamp/physical-result pairs transferred from the
 * existing bounded pre-shutter RAW ring. Their reference timestamp freezes
 * the donor burst; otherwise the first new C CaptureStarted is the reference.
 * Only exact real Camera2 image/result pairs are admitted.
 * Every unmatched queued preview RAW Image is promptly closed. Image/result
 * callbacks can arrive in either order and are joined by physical timestamp.
 * All failures produce a terminal callback; no partial/black gallery row.
 */
class Iris26972CCamera2ShutterSession @JvmOverloads constructor(
    context: Context,
    private val manager: CameraManager,
    private val logicalId: String,
    private val physicalId: String,
    private val frameCount: Int,
    private val night: Boolean,
    rawReader: ImageReader,
    private val orientationDegrees: Int,
    private val shutterMillis: Long,
    private val terminal: Terminal,
    private val preShutterImages: List<Image> = emptyList(),
    private val preShutterTotals: List<TotalCaptureResult> = emptyList(),
    private val outputGeometry: Iris26975COutputGeometry? = null,
    // Actual Iris-selected SS*ISO, before Camera2 HAL rounds the request.
    // Never substitute preview AE / a guessed desired product.
    private val desiredExposureProduct: Double = Double.NaN,
    private val previewTicket: com.particlesdevs.photoncamera.processing.experimentc.Iris26977CPreviewTicket,
    private val captureExposureCompensationEv: Float,
    private val donorGeometry: com.hinnka.mycamera.processor.experimentc.Iris26977CPhysicalGeometry.Frozen,
) : AutoCloseable {
    fun interface Terminal {
        fun onTerminal(uri: Uri?, error: String?)
    }

    private val displayName = com.particlesdevs.photoncamera.processing.ImagePath.generateNewFileName("IMG") + ".jpg"
    private val component = "26972 C independent Camera2 shutter"
    private val traceTag = "Iris26974C"
    private val applicationContext = context.applicationContext
    // Never share a scratch directory between live/closing C sessions. A previous
    // Camera2 GL worker may still be cancelling when a new camera opens.
    private val privateRoot = File(applicationContext.cacheDir, "iris26972c-private")
    private val privateDirectory = File(privateRoot, "session-${UUID.randomUUID()}")
    private val worker = Executors.newSingleThreadExecutor { task ->
        Thread(task, "Iris26972C-Camera2-GL").apply { isDaemon = true }
    }
    private val maxAttempts = frameCount * 3
    private val starts = LongArray(maxAttempts)
    private val startedFrameNumbers = LongArray(maxAttempts)
    private val uniqueStartedFrameNumbers = HashSet<Long>()
    private val results = BooleanArray(maxAttempts)
    private val captured = HashSet<Long>()
    private val rawTickets = com.particlesdevs.photoncamera.processing.experimentc.Iris26976CRawTicketJoin<Image>(
        frameCount, max(1, rawReader.maxImages - 2), { image ->
        try { image.close() } catch (_: Throwable) { /* best effort release; no foreign RAW admission */ }
    }, true)
    // Images arriving before their TotalCaptureResult are held only until the
    // exact physical pair has been checked; no rejected RAW is written to disk.
    private val pendingRaw = LinkedHashMap<Long, Image>()
    private val acceptedTimestamps = HashSet<Long>()
    private val rejectedTimestamps = HashSet<Long>()
    private val exactGroup = com.particlesdevs.photoncamera.processing.experimentc.Iris26980CExactExposureGroup(frameCount)
    private val pendingRawLimit = max(1, rawReader.maxImages - 3)
    private val icc: ByteArray
    private var nextStart = 0
    private var nextResult = 0
    private var nextTotalAttempt = 0
    private var shutter: Iris26972CContract.Plan? = null
    private var spool: Iris26972CPhysicalRawSpool? = null
    private var state = State.COLLECTING
    private var terminalSent = false
    // C may have a 100% pre-shutter burst. Never queue its worker before
    // CaptureController installs the independent terminal/sequence fence.
    private var activated = false
    @Volatile private var cancelled = false
    @Volatile private var processingDeadlineExpired = false

    private enum class State { COLLECTING, PROCESSING, FINISHED }

    init {
        require(frameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES && logicalId.isNotBlank() &&
            physicalId.isNotBlank() && rawReader.imageFormat == ImageFormat.RAW_SENSOR &&
            rawReader.width in 16..16384 && rawReader.height in 16..16384 &&
            orientationDegrees in listOf(0, 90, 180, 270) && shutterMillis > 0L &&
            desiredExposureProduct.isFinite() && desiredExposureProduct > 0.0 &&
            outputGeometry != null && outputGeometry.rawWidth == rawReader.width &&
            outputGeometry.rawHeight == rawReader.height &&
            outputGeometry.rotation == orientationDegrees) {
            "$component missing real RAW_SENSOR session or frozen capture parameters"
        }
        // Only the first C session in a process can reclaim abandoned scratch
        // from a previous *dead process*. Reclaiming on every session could
        // delete files still in use by an earlier cancelled GPU worker.
        reclaimPreviousProcessWorkspace(privateRoot)
        val required = frameCount.toLong() * rawReader.width * rawReader.height * 2L
        require(required in 1024L..MAX_PRIVATE_BYTES &&
            applicationContext.cacheDir.usableSpace >= required + FREE_SPACE_RESERVE) {
            "$component cannot guarantee entire RAW burst storage; cancel before exposure"
        }
        require(privateDirectory.mkdir() && privateDirectory.isDirectory &&
            privateDirectory.canWrite()) { "$component no writable isolated private spool" }
        icc = applicationContext.assets.open("iris26972c/sRGB.icc").use { it.readBytes() }
        require(icc.size == 588 && MessageDigest.getInstance("SHA-256")
            .digest(icc).joinToString("") { "%02x".format(it.toInt() and 255) } == ICC_SHA256) {
            "$component missing pinned sRGB ICC; no mislabelled JPEG"
        }
        // The pre-shutter list transfers REAL, already-paired RAW leases, not
        // a copy of Motion's capture logic. Every transferred Image must be
        // closed on this constructor's success AND failure paths.
        var consumed = 0
        try {
            require(preShutterImages.size == preShutterTotals.size &&
                preShutterImages.size <= frameCount) {
                "$component invalid pre-shutter RAW/TotalCaptureResult transfer"
            }
            for (index in preShutterImages.indices) {
                val image = preShutterImages[index]
                val total = preShutterTotals[index]
                // C must not accept a historical RAW merely because its
                // timestamp and physical lens match. Reject inherited A/B
                // preview requests with NR/EDGE not provably OFF. This mirrors
                // the controller's early ZSL filter, but makes this isolated
                // Camera2 session fail closed if another caller omits it.
                val cSourceRequest = total.request
                require(cSourceRequest != null &&
                    com.particlesdevs.photoncamera.processing.experimentc
                        .Iris26975COffModePolicy.acceptZslRequest(
                            cSourceRequest.get(CaptureRequest.NOISE_REDUCTION_MODE),
                            cSourceRequest.get(CaptureRequest.EDGE_MODE))) {
                    "$component ZSL RAW producer did not prove HAL NR/EDGE OFF"
                }
                val timestamp = total.get(CaptureResult.SENSOR_TIMESTAMP)
                require(timestamp != null && timestamp > 0L &&
                    timestamp == image.timestamp && total.frameNumber >= 0L &&
                    (index == 0 || timestamp > starts[index - 1])) {
                    "$component stale, unordered or mismatched ZSL RAW/result"
                }
                onStarted(index, timestamp, total.frameNumber)
                check(isCollecting()) { "$component pre-shutter start refused" }
                check(onTotal(index, total)) // physical metadata and lens IDs checked by spool
                check(isCollecting()) { "$component pre-shutter result refused" }
                consumed = index + 1
                onRaw(image)          // checksum + private copy + Image.close()
                check(isCollecting()) { "$component pre-shutter RAW refused" }
            }
            if (consumed > 0) Log.i(traceTag,
                "IRIS_26975_C_PRE_SHUTTER_ADMITTED pre=" + consumed + "/" + frameCount)
        } catch (failure: Throwable) {
            for (index in consumed until preShutterImages.size) {
                try { preShutterImages[index].close() } catch (close: Throwable) {
                    failure.addSuppressed(close)
                }
            }
            closeRawTickets()
            try { spool?.close() } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
            try { cleanSessionWorkspace() } catch (cleanup: Throwable) { failure.addSuppressed(cleanup) }
            worker.shutdown()
            throw failure
        }
    }

    /** Called only for a C-tagged request from this captureBurst, in submit order. */
    @Synchronized
    fun onStarted(index: Int, timestampNs: Long, frameNumber: Long) {
        if (state != State.COLLECTING) return
        try {
            require(index == nextStart && index in 0 until maxAttempts &&
                timestampNs > 0L && frameNumber >= 0L &&
                (index == 0 || (timestampNs > starts[index - 1] &&
                    frameNumber > startedFrameNumbers[index - 1])) &&
                captured.add(timestampNs) && uniqueStartedFrameNumbers.add(frameNumber)) {
                "$component duplicate/out-of-order started frame"
            }
            starts[index] = timestampNs
            startedFrameNumbers[index] = frameNumber
            nextStart++
            if (nextStart == 1 || nextStart == frameCount || nextStart % 5 == 0)
                Log.i(traceTag, "IRIS_26974_C_STARTED " + nextStart + "/" + frameCount)
            // Only a tagged start can promote a provisional Image into the spool.
            rawTickets.start(timestampNs)?.let { acceptOrHoldRaw(it) }
        } catch (error: Throwable) {
            fail("capture start: ${error.message}")
        }
    }

    /** Exact tagged TotalCaptureResult; do not borrow preview metadata. */
    @Synchronized
    fun onTotal(index: Int, total: TotalCaptureResult): Boolean {
        if (state != State.COLLECTING) return false
        try {
            val ts = total.get(CaptureResult.SENSOR_TIMESTAMP)
            require(index == nextTotalAttempt && index in 0 until nextStart && !results[index] &&
                ts != null && ts == starts[index] &&
                total.frameNumber == startedFrameNumbers[index]) {
                "$component duplicate/missing/wrong physical total-result timestamp/frame number"
            }
            val physical = if (physicalId == logicalId) total else total.physicalCameraResults[physicalId]
            val actualTime = physical?.get(CaptureResult.SENSOR_EXPOSURE_TIME)
            val actualIso = physical?.get(CaptureResult.SENSOR_SENSITIVITY)
            require(physical != null && actualTime != null && actualIso != null &&
                actualTime > 0 && actualIso > 0 && physical.get(CaptureResult.SENSOR_TIMESTAMP) == ts) {
                "$component missing exact physical exposure result"
            }
            results[index] = true
            nextTotalAttempt++
            if (!exactGroup.admit(actualTime, actualIso)) {
                rejectedTimestamps.add(ts)
                rawTickets.reject(ts)
                pendingRaw.remove(ts)?.close()
                Log.w(traceTag, "IRIS_26980_C_EXPOSURE_ATTEMPT_REJECT index=$index actual=$actualTime/$actualIso expected=${exactGroup.shutter()}/${exactGroup.iso()}")
                return false
            }
            if (exactGroup.accepted() == 1) {
                shutter = Iris26972CContract.freeze(physicalId, frameCount, night, ts)
                spool = Iris26972CPhysicalRawSpool.create(manager, logicalId, physicalId,
                    checkNotNull(shutter), privateDirectory, desiredExposureProduct, shutterMillis)
            }
            checkNotNull(spool).offerTotal(total)
            acceptedTimestamps.add(ts)
            nextResult++
            check(nextResult == exactGroup.accepted())
            pendingRaw.remove(ts)?.let { stageProvenRaw(it) }
            if (nextResult == 1 || nextResult == frameCount || nextResult % 5 == 0)
                Log.i(traceTag, "IRIS_26974_C_RESULTS " + nextResult + "/" + frameCount)
            maybeProcess()
            return true
        } catch (error: Throwable) {
            fail("exact physical result: ${error.message}")
            return false
        }
    }

    @Synchronized fun acceptedResultCount(): Int = nextResult
    @Synchronized fun remainingResultSlots(): Int = if(state==State.COLLECTING) frameCount-nextResult else 0
    @Synchronized fun attemptsRemaining(): Int = maxAttempts-nextStart

    /** Takes ownership of Image on every path, including unexpected preview RAWs. */
    @Synchronized
    fun onRaw(image: Image) {
        if (state != State.COLLECTING) {
            try { image.close() } catch (_: Throwable) { }
            return
        }
        val timestamp = try { image.timestamp } catch (error: Throwable) {
            try { image.close() } catch (_: Throwable) { }
            fail("RAW_SENSOR timestamp unavailable: ${error.message}")
            return
        }
        try {
            rawTickets.image(timestamp, image)?.let { acceptOrHoldRaw(it) }
            rawTickets.trimPending(max(0,pendingRawLimit-pendingRaw.size))
        } catch (error: Throwable) {
            fail("RAW_SENSOR ticket join: ${error.message}")
        }
    }

    private fun acceptOrHoldRaw(image: Image) {
        val ts=image.timestamp
        if (rejectedTimestamps.contains(ts)) { image.close(); return }
        if (acceptedTimestamps.contains(ts)) { stageProvenRaw(image); return }
        if (pendingRaw.size>=pendingRawLimit || pendingRaw.containsKey(ts)) {
            image.close()
            fail("C proved RAW awaiting physical result exceeded bounded leases")
            return
        }
        pendingRaw[ts]=image
        rawTickets.trimPending(max(0,pendingRawLimit-pendingRaw.size))
    }
    private fun closeRawTickets() {
        rawTickets.close()
        pendingRaw.values.forEach { try { it.close() } catch (_: Throwable) {} }
        pendingRaw.clear()
    }
    // No unknown, duplicate or late preview RAW can consume the exact frame budget.
    private fun stageProvenRaw(image: Image) {
        try {
            val sourceTimestamp = image.timestamp
            checkNotNull(spool).offerRaw(image) // always closes the Image
            Log.i(traceTag, "IRIS_26976_C_PROVEN_RAW_STAGED timestamp=" + sourceTimestamp)
            maybeProcess()
        } catch (error: Throwable) {
            fail("RAW_SENSOR Image delivery/storage: ${error.message}")
        }
    }

    @Synchronized
    fun onCaptureFailed(reason: String) = fail("Camera2 failure: $reason")

    /** This is a deliberate bounded callback deadline, not a silent no-image state. */
    @Synchronized
    fun timeout() {
        if (state == State.COLLECTING)
            fail("RAW/result timeout starts=$nextStart totals=$nextResult / $frameCount")
    }

    @Synchronized
    fun isCollecting(): Boolean = state == State.COLLECTING

    @Synchronized
    fun activate() {
        check(!activated && state != State.FINISHED) { "C owner activated twice or after failure" }
        activated = true
        maybeProcess()
    }

    @Synchronized
    private fun maybeProcess() {
        if (!activated || state != State.COLLECTING) return
        val active = spool ?: return
        if (nextResult != frameCount ||
            !active.hasCompletePhysicalBurst()) return
        closeRawTickets()
        state = State.PROCESSING
        Log.i(traceTag, "IRIS_26974_C_FULL_BURST_PROCESSING_START frames=" + frameCount)
        val processingWatchdog = Thread({
            try { Thread.sleep(PROCESSING_DEADLINE_MS) } catch (_: InterruptedException) { return@Thread }
            synchronized(this) {
                if (state == State.PROCESSING) {
                    processingDeadlineExpired = true
                    cancelled = true
                    // Do not release the GPU/spool or admit another C owner until the worker exits.
                    Log.e(traceTag,"IRIS_26975_C_PROCESSING_DEADLINE publicationCancelled=true ownerRetained=true")
                }
            }
        },"Iris26975C-ProcessingDeadline").apply { isDaemon = true }
        processingWatchdog.start()
        try {
            worker.execute {
                var uri: Uri? = null
                var reason: String? = null
                try {
                    // Nobody publishes without both independent production gates.
                    check(Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED) {
                        "$component production/device-compile gate is not enabled"
                    }
                    check(!cancelled) { "$component camera closed during C GPU dispatch" }
                    uri = run {
                        val frozen = checkNotNull(shutter)
                        val name = displayName
                        val finish = Iris26972CStreamingFinish.Plan(
                            File(privateDirectory, "iris26972c_${UUID.randomUUID()}.jpg"),
                            privateDirectory, physicalId, orientationDegrees, icc, 1.0f,
                            checkNotNull(outputGeometry),
                            Iris26975CDonorLutSelection.freeze())
                        Iris26972CCaptureToGallery.executeSpool(applicationContext,
                            active, frozen, finish, name, shutterMillis,
                            previewTicket.await(1500L), captureExposureCompensationEv, donorGeometry) { !cancelled }
                    }
                    check(uri != null) { "$component no authenticated JPEG-R MediaStore commit" }
                } catch (failure: Throwable) {
                    reason = "C RAW processing failed: ${failure.javaClass.simpleName}: ${failure.message}"
                    com.particlesdevs.photoncamera.util.Log.e(traceTag, reason, failure)
                } finally {
                    previewTicket.close()
                    try { active.close() } catch (cleanup: Throwable) {
                        reason = (reason ?: "C RAW cleanup failed") + "; ${cleanup.message}"
                        val committed = uri
                        if (committed != null) try {
                            com.particlesdevs.photoncamera.processing.experimentc
                                .Iris26972CMediaStorePublisher.revokeCommitted(applicationContext, committed)
                        } catch (revoke: Throwable) {
                            reason += "; C row revocation failed: ${revoke.message}"
                        }
                        uri = null
                    }
                    try { cleanSessionWorkspace() } catch (cleanup: Throwable) {
                        reason = (reason ?: "C private workspace cleanup failed") +
                            "; ${cleanup.message}"
                        // No successful photograph may be announced after a
                        // private source deletion failure. Revoke below.
                        if (uri != null) {
                            try {
                                com.particlesdevs.photoncamera.processing.experimentc
                                    .Iris26972CMediaStorePublisher.revokeCommitted(
                                        applicationContext, uri)
                            } catch (revoke: Throwable) {
                                reason += "; C row revocation failed: ${revoke.message}"
                            }
                            uri = null
                        }
                    }
                    Log.i(traceTag, "IRIS_26974_C_GPU_FINISH " +
                        "success=" + (uri != null) + " failure=" + (reason ?: "none"))
                    synchronized(this) {
                        // This lock serializes Camera2 close with the terminal
                        // commit. If close wins, the committed C-only row is
                        // revoked before any success notification is delivered.
                        if (cancelled) {
                            val row = uri
                            if (row != null) try {
                                com.particlesdevs.photoncamera.processing.experimentc
                                    .Iris26972CMediaStorePublisher.revokeCommitted(applicationContext,row)
                            } catch (revoke: Throwable) {
                                reason = "C cancelled row could not be revoked: ${revoke.message}"
                            }
                            uri = null
                            if (reason == null) reason = "$component camera closed during processing"
                        }
                        if (processingDeadlineExpired) reason = "$component donor processing deadline exceeded; no gallery commit"
                        state = State.FINISHED
                        processingWatchdog.interrupt()
                        deliver(uri, reason)
                    }
                    worker.shutdown()
                }
            }
        } catch (error: Throwable) {
            processingWatchdog.interrupt()
            state = State.COLLECTING // no worker owns the spool if execute() rejects
            fail("C GPU dispatch rejected: ${error.message}")
        }
    }

    @Synchronized
    private fun fail(reason: String) {
        if (state == State.FINISHED) return
        if (state == State.PROCESSING) {
            cancelled = true // worker owns spool; publication must now abort
            return
        }
        state = State.FINISHED
        previewTicket.close()
        closeRawTickets()
        Log.e(traceTag, "IRIS_26974_C_TERMINAL_FAILURE " + reason)
        var terminalReason = reason
        try { spool?.close() } catch (cleanup: Throwable) {
            terminalReason += "; C private RAW deletion failed: ${cleanup.message}"
        }
        try { cleanSessionWorkspace() } catch (cleanup: Throwable) {
            terminalReason += "; C private workspace deletion failed: ${cleanup.message}"
        }
        worker.shutdown()
        deliver(null, terminalReason)
    }

    @Synchronized
    private fun deliver(uri: Uri?, error: String?) {
        if (terminalSent) return
        terminalSent = true
        terminal.onTerminal(uri, error)
    }

    @Synchronized
    override fun close() {
        // Do not close the RAW spool while a GPU worker owns its mapped files.
        // Instead fence publication and let that worker release every resource.
        cancelled = true
        fail("camera/session closed before complete C image")
    }

    /** Delete only this session's exclusive scratch, never the shared root. */
    private fun cleanSessionWorkspace() {
        if (!privateDirectory.exists()) return
        require(!isSymbolicLink(privateDirectory) &&
            privateDirectory.parentFile?.canonicalFile == privateRoot.canonicalFile) {
            "$component unsafe private workspace location"
        }
        removeWithoutFollowingSymlinks(privateDirectory)
    }

    companion object {
        // One janitor pass per PROCESS. New sessions may overlap cancelled GL
        // workers, so never remove an earlier session directory in this process.
        private val reclaimLock = Any()
        private var reclaimedThisProcess = false
        private fun reclaimPreviousProcessWorkspace(root: File) = synchronized(reclaimLock) {
            if (reclaimedThisProcess) return@synchronized
            require((root.isDirectory || root.mkdir()) && !isSymbolicLink(root) &&
                root.isDirectory && root.canWrite()) {
                "26972 C invalid or symbolic private workspace root"
            }
            val entries = root.listFiles()
                ?: throw IllegalStateException("26972 C cannot inspect old RAW scratch")
            for (entry in entries) {
                // Older C checkpoints placed only these names directly in the
                // root. New checkpoints use session-UUID directories.
                val cOwned = entry.name.startsWith("session-") ||
                    entry.name.startsWith(".iris26972c_") ||
                    entry.name.startsWith("iris26972c_")
                require(cOwned) { "26972 C foreign file in private workspace; no deletion" }
                removeWithoutFollowingSymlinks(entry)
            }
            reclaimedThisProcess = true
        }
        /** java.io-only symlink detection; usable on every legacy Iris API. */
        private fun isSymbolicLink(file: File): Boolean {
            val parent = file.absoluteFile.parentFile?.canonicalFile
                ?: throw IllegalStateException("26972 C private workspace has no parent")
            val last = File(parent, file.name)
            return last.canonicalPath != last.absolutePath
        }
        private fun removeWithoutFollowingSymlinks(file: File) {
            // Do not recurse into a symlink even when it points at a directory;
            // Android's old API levels need no java.nio.file walker.
            if (!isSymbolicLink(file) && file.isDirectory) {
                val children = file.listFiles()
                    ?: throw IllegalStateException("26972 C cannot enumerate private scratch")
                for (child in children) removeWithoutFollowingSymlinks(child)
            }
            check(file.delete()) {
                "26972 C private scratch deletion refused: ${file.name}"
            }
        }
        private const val PROCESSING_DEADLINE_MS = 180_000L
        private const val MAX_PRIVATE_BYTES = 8L * 1024 * 1024 * 1024
        private const val FREE_SPACE_RESERVE = 128L * 1024 * 1024
        private const val ICC_SHA256 = "78e7ab7ab641965ccafce2b4fdd481c8b90ae15c8c4e9afef649aa9c7b1633c8"
    }
}
