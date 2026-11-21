package com.hinnka.mycamera.processor

import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.media.Image
import android.media.ImageReader
import android.net.Uri
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.Executors
import kotlin.math.max

/**
 * Independent C-only Camera2 shutter callbacks. No A/B frame, ImageSaver,
 * legacy callback, ZSL ring, JPEG owner or YUV fallback is used.
 *
 * A real first CaptureStarted timestamp freezes the donor reference; only
 * images named by that exact request's onCaptureStarted event are admitted.
 * Every unmatched queued preview RAW Image is promptly closed. Image/result
 * callbacks can arrive in either order and are joined by physical timestamp.
 * All failures produce a terminal callback; no partial/black gallery row.
 */
class Iris26972CCamera2ShutterSession(
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
) : AutoCloseable {
    fun interface Terminal {
        fun onTerminal(uri: Uri?, error: String?)
    }

    private val component = "26972 C independent Camera2 shutter"
    private val applicationContext = context.applicationContext
    // Never share a scratch directory between live/closing C sessions. A previous
    // Camera2 GL worker may still be cancelling when a new camera opens.
    private val privateRoot = File(applicationContext.cacheDir, "iris26972c-private")
    private val privateDirectory = File(privateRoot, "session-${UUID.randomUUID()}")
    private val worker = Executors.newSingleThreadExecutor { task ->
        Thread(task, "Iris26972C-Camera2-GL").apply { isDaemon = true }
    }
    private val starts = LongArray(frameCount)
    private val startedFrameNumbers = LongArray(frameCount)
    private val uniqueStartedFrameNumbers = HashSet<Long>()
    private val results = BooleanArray(frameCount)
    private val captured = HashSet<Long>()
    private val icc: ByteArray
    private var nextStart = 0
    private var nextResult = 0
    private var shutter: Iris26972CContract.Plan? = null
    private var spool: Iris26972CPhysicalRawSpool? = null
    private var state = State.COLLECTING
    private var terminalSent = false
    @Volatile private var cancelled = false

    private enum class State { COLLECTING, PROCESSING, FINISHED }

    init {
        require(frameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES && logicalId.isNotBlank() &&
            physicalId.isNotBlank() && rawReader.imageFormat == ImageFormat.RAW_SENSOR &&
            rawReader.width in 16..16384 && rawReader.height in 16..16384 &&
            orientationDegrees in listOf(0, 90, 180, 270) && shutterMillis > 0L) {
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
    }

    /** Called only for a C-tagged request from this captureBurst, in submit order. */
    @Synchronized
    fun onStarted(index: Int, timestampNs: Long, frameNumber: Long) {
        if (state != State.COLLECTING) return
        try {
            require(index == nextStart && index in 0 until frameCount &&
                timestampNs > 0L && frameNumber >= 0L &&
                (index == 0 || (timestampNs > starts[index - 1] &&
                    frameNumber > startedFrameNumbers[index - 1])) &&
                captured.add(timestampNs) && uniqueStartedFrameNumbers.add(frameNumber)) {
                "$component duplicate/out-of-order started frame"
            }
            if (index == 0) {
                shutter = Iris26972CContract.freeze(physicalId, frameCount, night, timestampNs)
                spool = Iris26972CPhysicalRawSpool.create(manager, logicalId, physicalId,
                    checkNotNull(shutter), privateDirectory)
            }
            check(spool != null) { "$component physical reference was not started first" }
            starts[index] = timestampNs
            startedFrameNumbers[index] = frameNumber
            nextStart++
        } catch (error: Throwable) {
            fail("capture start: ${error.message}")
        }
    }

    /** Exact tagged TotalCaptureResult; do not borrow preview metadata. */
    @Synchronized
    fun onTotal(index: Int, total: TotalCaptureResult) {
        if (state != State.COLLECTING) return
        try {
            val ts = total.get(CaptureResult.SENSOR_TIMESTAMP)
            require(index in 0 until nextStart && !results[index] &&
                ts != null && ts == starts[index] &&
                total.frameNumber == startedFrameNumbers[index]) {
                "$component duplicate/missing/wrong physical total-result timestamp/frame number"
            }
            checkNotNull(spool).offerTotal(total)
            results[index] = true
            nextResult++
            maybeProcess()
        } catch (error: Throwable) {
            fail("exact physical result: ${error.message}")
        }
    }

    /** Takes ownership of Image on every path, including unexpected preview RAWs. */
    @Synchronized
    fun onRaw(image: Image) {
        // ImageReader may coalesce several queued RAW Images in one callback.
        // A later C frame can consequently be dequeued before its own
        // onCaptureStarted callback runs on the same Handler. Stage *only* a
        // strictly future sensor timestamp while more tagged C starts remain;
        // the private spool will accept it only if an exact tagged started and
        // TotalCaptureResult arrive. Otherwise the whole burst fails closed.
        // Do not invent a reference from an unknown RAW, admit old preview
        // frames, or hold Image/HAL buffers across callbacks.
        val fromStarted = image.timestamp in captured
        val boundedFuture = nextStart in 1 until frameCount &&
            image.timestamp > starts[nextStart - 1] && spool != null
        if (state != State.COLLECTING || (!fromStarted && !boundedFuture)) {
            try { image.close() } catch (_: Throwable) { /* no leaked RAW lease */ }
            return
        }
        try {
            checkNotNull(spool).offerRaw(image) // always closes the Image
            maybeProcess()
        } catch (error: Throwable) {
            // offerRaw has already closed the Image, including the failing path.
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
    private fun maybeProcess() {
        val active = spool ?: return
        if (nextStart != frameCount || nextResult != frameCount ||
            !active.hasCompletePhysicalBurst()) return
        state = State.PROCESSING
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
                    uri = Iris26972CEglProcessingOwner.withNewContext {
                        val frozen = checkNotNull(shutter)
                        val name = "IRIS_C_${shutterMillis}_${UUID.randomUUID()}.jpg"
                        val finish = Iris26972CStreamingFinish.Plan(
                            File(privateDirectory, "iris26972c_${UUID.randomUUID()}.jpg"),
                            privateDirectory, physicalId, orientationDegrees, icc, 1.0f)
                        Iris26972CCaptureToGallery.executeSpool(applicationContext,
                            active, frozen, finish, name, shutterMillis) { !cancelled }
                    }
                    check(uri != null) { "$component no authenticated JPEG-R MediaStore commit" }
                } catch (failure: Throwable) {
                    reason = "C RAW processing failed: ${failure.javaClass.simpleName}: ${failure.message}"
                } finally {
                    try { active.close() } catch (cleanup: Throwable) {
                        reason = (reason ?: "C RAW cleanup failed") + "; ${cleanup.message}"
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
                        state = State.FINISHED
                        deliver(uri, reason)
                    }
                    worker.shutdown()
                }
            }
        } catch (error: Throwable) {
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
        private const val MAX_PRIVATE_BYTES = 8L * 1024 * 1024 * 1024
        private const val FREE_SPACE_RESERVE = 128L * 1024 * 1024
        private const val ICC_SHA256 = "78e7ab7ab641965ccafce2b4fdd481c8b90ae15c8c4e9afef649aa9c7b1633c8"
    }
}
