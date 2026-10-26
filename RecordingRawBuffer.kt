package com.unspektrawesome.preview

import java.nio.ByteBuffer

/**
 * The original UnspektrAwesome 1.2.5 native recording-buffer JNI owner.
 * Unlike a Java DirectByteBuffer cache, this memory is allocated/freed by
 * the reference native implementation. Retain exact instance descriptors.
 * Never return a native allocation to arbitrary threads after close.
 */
internal class RecordingRawBuffer : AutoCloseable {
    private var owned: ByteBuffer? = null

    @Synchronized
    fun allocate(sizeBytes: Int): ByteBuffer {
        require(sizeBytes > 0) { "RAW recording allocation must be positive" }
        check(owned == null) { "RAW recording buffer is already allocated" }
        return requireNotNull(nativeAllocate(sizeBytes)) { "Native RAW recording allocation failed" }
            .also { check(it.isDirect); owned = it }
    }

    @Synchronized
    override fun close() {
        val bytes = owned ?: return
        owned = null
        nativeRelease(bytes)
    }

    // Exact DEX JNI signatures: (I)Ljava/nio/ByteBuffer; and (Ljava/nio/ByteBuffer;)V.
    private external fun nativeAllocate(sizeBytes: Int): ByteBuffer?
    private external fun nativeRelease(bytes: ByteBuffer)
}
