package com.unspektrawesome.spektra

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Exact Unspektrawesome 1.1.2 default SpektraFilm parameter block.
 *
 * 26689 intentionally treats the audited 648-byte APK snapshot as runtime authority instead of
 * inheriting the older public-source parameter defaults. The Iris shell does not mutate this
 * processing state in the first embedded-mode build.
 */
class SpektraFilmParams private constructor(
    private val serialized: ByteArray,
) {
    init { require(serialized.size == STRUCT_SIZE) }

    fun toByteBuffer(): ByteBuffer = writeTo(
        ByteBuffer.allocateDirect(STRUCT_SIZE).order(ByteOrder.nativeOrder()),
    )

    fun writeTo(target: ByteBuffer): ByteBuffer {
        require(target.isDirect && target.capacity() >= STRUCT_SIZE) {
            "SpektraFilm parameter target must be a direct buffer of at least $STRUCT_SIZE bytes"
        }
        target.order(ByteOrder.nativeOrder()).clear()
        target.put(serialized)
        target.flip()
        return target
    }

    override fun equals(other: Any?): Boolean =
        other is SpektraFilmParams && serialized.contentEquals(other.serialized)

    override fun hashCode(): Int = serialized.contentHashCode()

    companion object {
        const val STRUCT_SIZE = 648
        private val EXACT_1_1_2_DEFAULT = byteArrayOf(1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 15, 0, 0, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 75, 67, 0, 0, 122, 68, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -51, 67, 0, 0, 0, 0, 0, -64, 40, 68, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -96, 65, 0, 0, 72, 67, -113, -62, 117, 61, 0, 0, -128, 63, 0, 0, -128, 63, 49, 8, -84, 62, -8, 83, -93, 62, -88, -58, -117, 62, 106, -68, -76, 62, -66, -97, -102, 62, 45, -78, 29, 62, 106, -68, -76, 62, 49, 8, 44, 62, -117, 108, 103, 62, 0, 0, 0, 0, 1, 0, 0, 0, 4, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 1, 0, 0, 0, 1, 0, 0, 0, -51, -52, -52, 61, -102, -103, -103, 63, 0, 0, -128, 63, 0, 0, 32, 64, 0, 0, -64, 64, 0, 0, -128, 63, -51, -52, -52, 62, 10, -41, 35, 61, -51, -52, 76, 61, -113, -62, 117, 61, -92, 112, 125, 63, -20, 81, 120, 63, 72, -31, 122, 63, -51, -52, 60, 65, 0, 0, -128, 63, -51, -52, 76, 62, 0, 0, -16, 65, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, -128, 0, 0, 0, 0, 0, -128, 62, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 119, -66, 127, 63, 23, -73, -47, 56, 32, 0, 0, 0, -102, -103, -103, 63, 0, 0, -128, 63, 0, 0, 32, 64, 0, 0, -64, 64, 0, 0, -128, 63, -51, -52, -52, 62, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, -51, -52, 76, 61, -113, -62, 117, 60, 0, 0, 0, 0, 0, 0, -126, 66, 0, 0, -126, 66, 0, 0, -126, 66, 0, 0, 0, 0, -102, -103, -103, 62, 0, 0, -128, 64, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 63, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 63, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, -128, 63, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 72, -31, 122, 63, 10, -41, 35, 60, -113, -62, -11, 60, 51, 51, 51, 63, 0, 0, 0, 63, 0, 0, 112, 66, 0, 0, -96, 64, 51, 51, 51, 63, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)
        fun exact112Default(): SpektraFilmParams = SpektraFilmParams(EXACT_1_1_2_DEFAULT.copyOf())
    }
}
