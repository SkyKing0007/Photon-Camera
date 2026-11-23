package com.hinnka.mycamera.processor.experimentc.original129.hdr

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.ColorSpace

/**
 * Experiment C ingress adapter for the original RAW GPU gainmap producer.
 * No creative/look LUT is selected, so its required after/before luminance
 * ratio sidecar is exactly one (identity). Donor GpuReferenceGainmapProducer
 * still computes the physical HDR/SDR gain from original-rendered pixels.
 */
internal object NoLookLutRawGainmapSidecar {
    fun create(sdrBase: Bitmap): LuminanceGainMap {
        require(!sdrBase.isRecycled && sdrBase.width > 0 && sdrBase.height > 0)
        val downsample = RawGainmapMath.DOWNSAMPLE
        val width = ((sdrBase.width + downsample - 1) / downsample).coerceAtLeast(1)
        val height = ((sdrBase.height + downsample - 1) / downsample).coerceAtLeast(1)
        val contents = Bitmap.createBitmap(
            width, height, Bitmap.Config.RGBA_F16, false,
            ColorSpace.get(ColorSpace.Named.LINEAR_EXTENDED_SRGB),
        )
        contents.eraseColor(Color.WHITE)
        return LuminanceGainMap(contents, LuminanceGainMapEncoding.LINEAR_RATIO)
    }
}
