package com.hinnka.mycamera.processor

import android.graphics.ImageFormat
import android.hardware.camera2.CameraManager
import android.hardware.camera2.TotalCaptureResult
import android.media.Image
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import java.io.File
import java.io.FileOutputStream
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import java.security.MessageDigest
import kotlin.math.max

/**
 * C-only bounded Camera2 RAW_SENSOR rendezvous. Each Image is copied into a
 * private RAW16 file and CLOSED within the availability callback; the matching
 * TotalCaptureResult can arrive before OR after the Image. The complete
 * reference-first immutable burst is validated before allocating any GL work.
 *
 * This code does not modify A/B readers and is source-wired to an isolated Camera2
 * listener; actual Android hardware execution is not yet proven. Large memory maps are virtual reservations, NOT copied Java heap;
 * real 50MP device storage, I/O timing and page-cache use remain unverified.
 */
internal class Iris26972CPhysicalRawSpool private constructor(
    private val cameraManager: CameraManager,
    private val logicalCameraId: String,
    private val physicalCameraId: String,
    private val shutter: Iris26972CContract.Plan,
    private val scratch: File,
    private val maxBytes: Long,
    private val frozenDesiredExposureProduct: Double,
    private val shutterTimeMillis: Long,
) : AutoCloseable {
    private val name = "26972 C private RAW16 Camera2 rendezvous"
    private data class Raw(
        val timestamp: Long,
        val path: File,
        val width: Int,
        val height: Int,
        // The file stores a tightly packed crop. Preserve its original sensor
        // geometry so a shifted Bayer or lens-shading domain never silently
        // enters a different frame's reference pyramid.
        val sensorWidth: Int,
        val sensorHeight: Int,
        val sensorCropLeft: Int,
        val sensorCropTop: Int,
        val byteLength: Long,
        val sha256: ByteArray,
    )
    private data class Completed(
        val metadata: Iris26972CPhysicalRawMetadata.Frozen,
        val total: TotalCaptureResult,
    )
    private val raws = LinkedHashMap<Long, Raw>()
    private val results = LinkedHashMap<Long, Completed>()
    private val frameNumbers = HashSet<Long>()
    private var usedBytes = 0L
    private var closed = false
    private var processedOnce = false
    private var poisoned = false

    @Synchronized
    internal fun hasCompletePhysicalBurst(): Boolean = !closed && !processedOnce &&
        !poisoned && raws.size == shutter.frameCount &&
        results.size == shutter.frameCount && raws.keys == results.keys

    /**
     * Camera2 ImageReader entry. Releases Image on EVERY path, including if
     * the TotalCaptureResult is not yet available. No Image, Plane, HAL buffer
     * or mutable ByteBuffer escapes into a cross-callback queue.
     */
    @Synchronized
    internal fun offerRaw(image: Image) {
        var partial: File? = null
        var finished: File? = null
        var primary: Throwable? = null
        try {
            check(!closed && !processedOnce && !poisoned && raws.size < shutter.frameCount) {
                "$name image after frame budget/completion"
            }
            require(image.format == ImageFormat.RAW_SENSOR && image.planes.size == 1 &&
                image.timestamp > 0L && !raws.containsKey(image.timestamp)) {
                "$name requires unique real RAW_SENSOR Image"
            }
            val src = image.planes.single()
            val crop = image.cropRect
            val input = Iris26972CDonorSabreGpuRawIngress.Plane(
                src.buffer,image.width,image.height,src.rowStride,src.pixelStride,
                crop.left,crop.top,crop.width(),crop.height())
            Iris26972CDonorSabreGpuRawIngress.validate(input)
            val width = crop.width()
            val height = crop.height()
            val referenceShape = raws.values.firstOrNull()
            require(referenceShape == null ||
                (referenceShape.width == width && referenceShape.height == height &&
                    referenceShape.sensorWidth == image.width &&
                    referenceShape.sensorHeight == image.height &&
                    referenceShape.sensorCropLeft == crop.left &&
                    referenceShape.sensorCropTop == crop.top)) {
                "$name inconsistent RAW16 sensor crop or Bayer origin"
            }
            val byteCount = width.toLong() * height * 2L
            require(byteCount in 512L..Int.MAX_VALUE.toLong() &&
                byteCount <= maxBytes - usedBytes &&
                scratch.usableSpace > byteCount + MIN_FREE_BYTES) {
                "$name insufficient private storage for frozen RAW"
            }
            partial = File.createTempFile(".iris26972c_raw_", ".part", scratch)
            val digest = MessageDigest.getInstance("SHA-256")
            val staging = ByteArray(minOf(width*2,256*1024))
            val buffer = src.buffer.duplicate().order(ByteOrder.nativeOrder())
            val start = src.buffer.position().toLong() +
                crop.top.toLong()*src.rowStride + crop.left.toLong()*2L
            FileOutputStream(partial).use { stream ->
                for (y in 0 until height) {
                    var position = start + y.toLong()*src.rowStride
                    var remaining = width*2
                    while (remaining > 0) {
                        val n = minOf(remaining,staging.size)
                        buffer.position(position.toInt())
                        buffer.get(staging,0,n)
                        stream.write(staging,0,n)
                        digest.update(staging,0,n)
                        position += n
                        remaining -= n
                    }
                }
                stream.fd.sync()
            }
            require(partial.length() == byteCount) { "$name truncated staging write" }
            finished = File(scratch,partial.name.removeSuffix(".part")+".raw16")
            check(!finished.exists() && partial.renameTo(finished)) {
                "$name failed atomic RAW staging"
            }
            partial = null
            raws[image.timestamp] = Raw(image.timestamp,finished,width,height,
                image.width,image.height,crop.left,crop.top,
                byteCount,digest.digest())
            finished = null
            usedBytes += byteCount
        } catch (failure: Throwable) {
            poisoned = true
            primary = failure
            throw failure
        } finally {
            // A failed Camera2 Image.close cannot mask an earlier RAW error.
            // Treat either error as terminal for this shutter's provenance.
            try { image.close() } catch (failure: Throwable) {
                poisoned = true
                if (primary != null) primary.addSuppressed(failure) else throw failure
            } finally {
                partial?.delete()
                finished?.delete()
            }
        }
    }

    /**
     * CameraCaptureSession.CaptureCallback entry: actual per-physical result,
     * never a synthetic or preview-derived result. May arrive before RAW.
     */
    @Synchronized
    internal fun offerTotal(total: TotalCaptureResult) {
        try {
            check(!closed && !processedOnce && !poisoned && results.size < shutter.frameCount) {
                "$name Camera2 result after frame budget/completion"
            }
            val metadata = Iris26972CPhysicalRawMetadata.freezeFromTotal(
                cameraManager,logicalCameraId,physicalCameraId,total)
            require(!results.containsKey(metadata.sensorTimestampNs) &&
                !frameNumbers.contains(metadata.frameNumber)) {
                "$name repeated actual Camera2 sensor timestamp/frame number"
            }
            frameNumbers.add(metadata.frameNumber)
            results[metadata.sensorTimestampNs] = Completed(metadata,total)
        } catch (failure: Throwable) {
            poisoned = true
            throw failure
        }
    }

    /** Synchronous convenience, with both Camera2 owners already paired. */
    internal fun append(image: Image,total: TotalCaptureResult) {
        val metadata = try {
            Iris26972CPhysicalRawMetadata.freezeFromTotal(
                cameraManager,logicalCameraId,physicalCameraId,total)
        } catch(failure:Throwable) {
            poisoned = true
            try { image.close() } catch(closeError: Throwable) { failure.addSuppressed(closeError) }
            throw failure
        }
        if(metadata.sensorTimestampNs != image.timestamp) {
            poisoned = true
            val failure = IllegalArgumentException("$name Image/TotalCaptureResult timestamp mismatch")
            try { image.close() } catch(closeError: Throwable) { failure.addSuppressed(closeError) }
            throw failure
        }
        offerRaw(image)
        offerTotal(total)
    }

    /**
     * Full preflight before EGL: verify every staged file SHA against the
     * original Image, exact TotalCaptureResult correspondence, reference-first
     * frame-number order, same physical CFA/crop/exposure and noise validity.
     */
    @Synchronized
    internal fun <T> withFrozenBurst(block: (
        Iris26972CDonorSabreGpuBurst.Plan,
        Iris26972CCamera2Calibration.Frozen,
        Iris26972CPhysicalLensShading.Frozen,
        Iris26975CDonorExif.Frozen,
    ) -> T): T {
        check(hasCompletePhysicalBurst()) {
            "$name incomplete/ambiguous physical RAW/result rendezvous"
        }
        processedOnce = true
        val ordered = results.values.sortedBy { it.metadata.frameNumber }
        val base = ordered.first().metadata
        require(base.sensorTimestampNs == shutter.referenceTimestampNs &&
            ordered.all { it.metadata.cfaPattern == base.cfaPattern &&
                it.metadata.sensorWhiteLevel == base.sensorWhiteLevel &&
                kotlin.math.abs(it.metadata.exposureProduct/base.exposureProduct-1.0)<=0.01 }) {
            "$name reference must be FIRST frame, normal-only same sensor/exposure"
        }
        val planes = ArrayList<Iris26972CDonorSabreGpuRawIngress.Plane>(ordered.size)
        val referenceRaw = checkNotNull(raws[base.sensorTimestampNs])
        for (frame in ordered) {
            val raw = checkNotNull(raws[frame.metadata.sensorTimestampNs])
            require(raw.width == referenceRaw.width && raw.height == referenceRaw.height &&
                raw.sensorWidth == referenceRaw.sensorWidth &&
                raw.sensorHeight == referenceRaw.sensorHeight &&
                raw.sensorCropLeft == referenceRaw.sensorCropLeft &&
                raw.sensorCropTop == referenceRaw.sensorCropTop) {
                "$name physical RAW sensor crop moved across shutter burst"
            }
            val digest = MessageDigest.getInstance("SHA-256")
            val staging = ByteArray(256*1024)
            FileInputStream(raw.path).use { input ->
                while (true) {
                    val n = input.read(staging)
                    if (n < 0) break
                    if (n > 0) digest.update(staging,0,n)
                }
            }
            require(raw.path.length()==raw.byteLength &&
                raw.sha256.contentEquals(digest.digest())) {
                "$name RAW source changed after Camera2 HAL was released"
            }
            val mapping=FileInputStream(raw.path).channel.use { channel ->
                channel.map(FileChannel.MapMode.READ_ONLY,0L,raw.byteLength)
            }
            planes += Iris26972CDonorSabreGpuRawIngress.Plane(mapping,
                raw.width,raw.height,raw.width*2,2,0,0,raw.width,raw.height)
        }
        val measured=Iris26972CMeasuredRawSnr.measure(base,planes.first())
        val snr=measured.referenceSnr
        val frames=ordered.indices.map { i ->
            ordered[i].metadata.toBurstFrame(base,planes[i],snr,ordered.size)
        }
        val wb=base.copyCanonicalWbForAudit()
        val scale=max((16384f/(base.sensorWhiteLevel+1f)).toInt(),1)
        val white=base.sensorWhiteLevel.toLong()*scale
        require(white in 1..32767) { "$name MGC Resolve white overflow" }
        val burst=Iris26972CDonorSabreGpuBurst.Plan(frames,
            shutter.referenceTimestampNs,Iris26972CDonorSabreGpuResolve.Plan(
                base.cfaPattern,frames.size,snr,frozenDesiredExposureProduct,
                base.exposureProduct,
                white.toInt(),floatArrayOf(1f/wb[0],1f,1f/wb[3]),0),
            referencePhysical=base, measuredReferenceSignal=measured.referenceSignal)
        Iris26972CDonorSabreGpuBurst.validate(burst,metadataOnly=true)
        Iris26972CContract.validateBurst(shutter,
            frames.map {Iris26972CContract.Role.valueOf(it.role.name)},
            frames.map {it.sensorTimestampNs},frames.map {it.exposureProduct})
        val firstTotal=ordered.first().total
        val color=Iris26972CCamera2Calibration.freezeFromTotalCaptureResult(
            cameraManager,logicalCameraId,physicalCameraId,firstTotal,
            shutter.referenceTimestampNs,floatArrayOf(1f/wb[0],1f,1f/wb[3]))
        val lens=Iris26972CPhysicalLensShading.freezeFromTotal(logicalCameraId,
            physicalCameraId,firstTotal,shutter.referenceTimestampNs)
        color.colorPlan(burst.rawWidth,burst.rawHeight,burst)
        lens.requireMatches(physicalCameraId,shutter.referenceTimestampNs)
        val exif = Iris26975CDonorExif.freeze(cameraManager,logicalCameraId,
            physicalCameraId,firstTotal,base,shutterTimeMillis)
        return block(burst,color,lens,exif)
    }

    /**
     * ORIGINAL bjzhou RAW ingress. This intentionally bypasses the custom
     * Iris26972CDonorSabreGpuBurst.Plan and its custom RAW color/develop path.
     * The donor gets untouched RAW16 plus original per-frame Camera2 metadata.
     * No A/B image-processing class is referenced by this handoff.
     */
    @Synchronized
    internal fun <T> withOriginalDonorRawBurst(
        block: (com.hinnka.mycamera.processor.experimentc.Iris26975COriginalRawBurst) -> T,
    ): T {
        check(hasCompletePhysicalBurst()) {
            "$name incomplete/ambiguous original donor RAW/result rendezvous"
        }
        processedOnce = true
        val ordered = results.values.sortedBy { it.metadata.frameNumber }
        val reference = ordered.first().metadata
        require(reference.sensorTimestampNs == shutter.referenceTimestampNs &&
            ordered.size == shutter.frameCount &&
            ordered.all { it.metadata.physicalCameraId == physicalCameraId &&
                it.metadata.cfaPattern == reference.cfaPattern &&
                it.metadata.sensorWhiteLevel == reference.sensorWhiteLevel &&
                kotlin.math.abs(it.metadata.exposureProduct / reference.exposureProduct - 1.0) <= 0.01 }) {
            "$name original donor reference/sensor/exposure differs"
        }
        val firstRaw = checkNotNull(raws[reference.sensorTimestampNs])
        val rawFrames = ordered.map { capture ->
            val raw = checkNotNull(raws[capture.metadata.sensorTimestampNs])
            require(raw.sensorWidth == firstRaw.sensorWidth &&
                raw.sensorHeight == firstRaw.sensorHeight &&
                raw.width == firstRaw.width && raw.height == firstRaw.height &&
                raw.sensorCropLeft == firstRaw.sensorCropLeft &&
                raw.sensorCropTop == firstRaw.sensorCropTop) {
                "$name donor raw geometry changed after shutter"
            }
            // No donor frame may be constructed from an unchecked mmap, and
            // no Camera2 Image survives acquisition. Re-read source SHA here.
            val digest = MessageDigest.getInstance("SHA-256")
            val buf = ByteArray(256 * 1024)
            FileInputStream(raw.path).use { input ->
                while (true) {
                    val count = input.read(buf)
                    if (count < 0) break
                    if (count > 0) digest.update(buf, 0, count)
                }
            }
            require(raw.path.length() == raw.byteLength &&
                raw.sha256.contentEquals(digest.digest())) {
                "$name donor raw16 SHA changed after acquisition"
            }
            val source = FileInputStream(raw.path).channel.use { channel ->
                channel.map(FileChannel.MapMode.READ_ONLY, 0L, raw.byteLength)
            }
            com.hinnka.mycamera.processor.experimentc.Iris26975COriginalRawBurst.Frame(
                metadata = capture.metadata,
                totalCaptureResult = capture.total,
                physicalCaptureResult = if (logicalCameraId == physicalCameraId) capture.total else
                    checkNotNull(capture.total.physicalCameraResults[physicalCameraId]) {
                        "$name missing exact physical donor capture result"
                    },
                sensorWidth = raw.sensorWidth,
                sensorHeight = raw.sensorHeight,
                cropLeft = raw.sensorCropLeft,
                cropTop = raw.sensorCropTop,
                rawWidth = raw.width,
                rawHeight = raw.height,
                raw16 = source,
            )
        }
        val burst = com.hinnka.mycamera.processor.experimentc
            .Iris26975COriginalRawBurst.create(physicalCameraId, shutter.referenceTimestampNs, rawFrames)
        burst.validateAgainst(shutter)
        return block(burst)
    }

    @Synchronized
    override fun close() {
        if(closed) return
        closed=true
        var cause:Throwable?=null
        for(raw in raws.values) {
            try { check(raw.path.delete()) { "$name failed secure private-file deletion" } }
            catch(failure:Throwable) {
                if(cause==null) cause=failure else cause.addSuppressed(failure)
            }
        }
        raws.clear()
        results.clear()
        frameNumbers.clear()
        if(cause!=null)throw cause
    }

    internal companion object {
        private const val MIN_FREE_BYTES=128L*1024L*1024L
        private const val MAX_BURST_BYTES=8L*1024L*1024L*1024L
        fun create(manager:CameraManager,logicalCameraId:String,
            physicalCameraId:String,shutter:Iris26972CContract.Plan,
            scratchDirectory:File,desiredExposureProduct:Double,
            shutterTimeMillis:Long,
            diskLimitBytes:Long=MAX_BURST_BYTES):
                Iris26972CPhysicalRawSpool {
            require(logicalCameraId.isNotBlank() && physicalCameraId.isNotBlank() &&
                shutter.physicalLensId==physicalCameraId &&
                desiredExposureProduct.isFinite() && desiredExposureProduct > 0.0 &&
                shutterTimeMillis > 0L &&
                shutter.frameCount in 2..Iris26972CContract.MAX_NORMAL_FRAMES && scratchDirectory.isDirectory &&
                scratchDirectory.canWrite() &&
                diskLimitBytes in 1024L..MAX_BURST_BYTES) {
                "26972 C invalid frozen shutter, camera or scratch directory"
            }
            return Iris26972CPhysicalRawSpool(manager,logicalCameraId,
                physicalCameraId,shutter,scratchDirectory,diskLimitBytes,
                desiredExposureProduct,shutterTimeMillis)
        }
    }
}
