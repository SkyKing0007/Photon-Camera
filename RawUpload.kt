package com.unspektrawesome.vulkan

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Native RAW copy owned by UnspektrAwesome 1.2.5 RawUploadPool.
 *
 * The original APK's nativeBeginRead/nativeEndRead pair brackets EVERY native view.
 * Never publish that transient ByteBuffer outside this synchronous read scope;
 * it becomes invalid as soon as nativeEndRead executes.
 */
class RawUpload internal constructor(
    initialHandle: Long,
    private val onReleased: ((RawUpload) -> Unit)? = null,
) : AutoCloseable {
    private var handle = initialHandle.also { require(it != 0L) }

    /** Invoked only while the renderer owns this upload and it has not been released. */
    /**
     * A borrowed native handle must never escape its synchronized lifetime.
     * Native render is synchronous and has to finish before another thread
     * may close/release the upload. Returning the raw Long was racy.
     */
    @Synchronized
    internal fun <R> withNativeHandle(block: (Long) -> R): R {
        check(handle != 0L) { "Native RAW upload was released" }
        return block(handle)
    }

    @Synchronized
    fun readNow(consumer: (ByteBuffer) -> Unit): Boolean {
        val current = handle
        check(current != 0L) { "Native RAW upload was released" }
        val bytes = nativeBeginRead(current) ?: return false
        try {
            consumer(bytes.order(ByteOrder.nativeOrder()))
        } finally {
            nativeEndRead(current)
        }
        return true
    }

    override fun close() {
        // withNativeHandle/readNow both hold this monitor for the entire
        // native borrow. Native release cannot begin until that call exits.
        // Invoke the pool callback OUTSIDE this monitor: a pool.close() may
        // already be waiting for us while another thread closes an upload.
        var released = false
        try {
            synchronized(this) {
                val current = handle
                if (current != 0L) {
                    handle = 0L
                    released = true
                    nativeRelease(current)
                }
            }
        } finally {
            if (released) onReleased?.invoke(this)
        }
    }

    // Descriptors copied from original 1.2.5 DEX; no old Iris JNI methods.
    private external fun nativeBeginRead(handle: Long): ByteBuffer?
    private external fun nativeEndRead(handle: Long)
    private external fun nativeRelease(handle: Long)
}
