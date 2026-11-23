package com.hinnka.mycamera.processor.experimentc.original129.processor

/** GLES pixel-buffer operations missing from Android's Java GLES bindings. */
internal object GlesPixelBufferTransfer {
    init {
        com.hinnka.mycamera.processor.experimentc.Iris26975COriginalNative.ensureLoaded()
    }

    /** Queues an RGBA16F upload from PBO offset zero into an existing 2D texture. */
    external fun uploadRgba16fPboToTexture(
        pixelBufferObject: Int,
        textureId: Int,
        width: Int,
        height: Int,
    ): Boolean
}
