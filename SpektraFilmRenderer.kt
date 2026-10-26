package com.unspektrawesome.spektra

import java.nio.ByteBuffer

/** The original 1.2.5 independent native SpektraFilm rendering owner.
 * Its class is NOT Iris's com.particlesdevs.photoncamera.spektra renderer.
 * This is an ABI carrier only until the coherent 1.2.5 app/JNI migration.
 */
internal class SpektraFilmRenderer {
    // Original application DEX declares all five as private instance natives.
    private external fun nativeSpektraDestroy()
    private external fun nativeSpektraIsAvailable(): Boolean
    private external fun nativeSpektraLastDiagnosticsJson(): String
    private external fun nativeSpektraRelease()
    private external fun nativeSpektraRenderRgba16f(
        input: ByteBuffer, output: ByteBuffer,
        width: Int, height: Int, parameters: ByteBuffer, timeSeconds: Double,
    ): Boolean
}
