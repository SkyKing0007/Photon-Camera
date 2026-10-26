package com.unspektrawesome.vulkan

import java.nio.ByteBuffer
import java.util.Collections
import java.util.IdentityHashMap

/** Native 1.2.5 RAW byte upload pool, not a replacement host-side ByteBuffer cache. */
class RawUploadPool internal constructor(initialHandle: Long) : AutoCloseable {
    private var handle = initialHandle.also { require(it != 0L) }
    // The native upload may retain pool-allocated storage even after
    // nativeCopy returns. Releasing the pool before outstanding upload views
    // and renders complete risks use-after-free in the original 1.2.5 JNI.
    private val liveUploads = Collections.newSetFromMap(IdentityHashMap<RawUpload, Boolean>())

    /**
     * Copy packed Camera2 RAW with its original capture timestamp.
     * The native object owns the returned bytes; callers must close each RawUpload.
     */
    @Synchronized
    fun copy(captureTimestampNs: Long, rawBytes: ByteBuffer): RawUpload? {
        require(rawBytes.isDirect) { "Packed RAW bytes must be direct" }
        val current = handle
        check(current != 0L) { "Native RAW upload pool was released" }
        val uploaded = nativeCopy(current, rawBytes, captureTimestampNs)
        if (uploaded == 0L) return null
        return RawUpload(uploaded) { finished ->
            synchronized(this) { liveUploads.remove(finished) }
        }.also { liveUploads.add(it) }
    }

    override fun close() {
        // Retire children first, AFTER closing the admission gate. Do not
        // hold the pool monitor while waiting for a child native render:
        // its onReleased callback also acquires that monitor.
        val retired: Pair<Long, List<RawUpload>> = synchronized(this) {
            val current = handle
            if (current == 0L) return
            handle = 0L
            val pending = liveUploads.toList()
            liveUploads.clear()
            current to pending
        }
        var firstFailure: Throwable? = null
        for (upload in retired.second) {
            try {
                upload.close()
            } catch (error: Throwable) {
                if (firstFailure == null) firstFailure = error
                else firstFailure!!.addSuppressed(error)
            }
        }
        try {
            nativeRelease(retired.first)
        } catch (error: Throwable) {
            if (firstFailure == null) firstFailure = error
            else firstFailure!!.addSuppressed(error)
        }
        firstFailure?.let { throw it }
    }

    // Exact JNI descriptors: (JLjava/nio/ByteBuffer;J)J and (J)V.
    private external fun nativeCopy(pool: Long, bytes: ByteBuffer, captureTimestampNs: Long): Long
    private external fun nativeRelease(pool: Long)
}
