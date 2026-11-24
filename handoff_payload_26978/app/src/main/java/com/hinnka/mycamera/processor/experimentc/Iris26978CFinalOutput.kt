package com.hinnka.mycamera.processor.experimentc

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.ColorSpace
import android.graphics.Rect
import com.hinnka.mycamera.processor.experimentc.original129.hdr.RawGainmapMath
import com.hinnka.mycamera.processor.experimentc.original129.hdr.LuminanceGainMap
import com.hinnka.mycamera.processor.experimentc.original129.hdr.LuminanceGainMapEncoding

/** Neutral output boundary only. Donor no-look render clamps RGB to [0,1] in RGBA8.
 * Extended encoded sRGB has the same in-range transfer and primaries as sRGB.
 * Draw through Android's color-managed Canvas into an explicitly bounded sRGB
 * destination; never relabel the source or modify the linear HDR reference.
 */
internal object Iris26978CFinalOutput {
    fun prepareSdr(source: Bitmap): Bitmap {
        require(!source.isRecycled && source.width > 0 && source.height > 0)
        val srgb = ColorSpace.get(ColorSpace.Named.SRGB)
        val extended = ColorSpace.get(ColorSpace.Named.EXTENDED_SRGB)
        require(source.colorSpace?.id == srgb.id || source.colorSpace?.id == extended.id) {
            "C donor returned unexpected SDR color space: ${source.colorSpace}"
        }
        if (source.config == Bitmap.Config.ARGB_8888 && source.colorSpace?.isSrgb == true) return source
        val target = Bitmap.createBitmap(source.width, source.height, Bitmap.Config.ARGB_8888, false, srgb)
        try {
            // Explicit source/destination rectangles: no density scaling or geometry change.
            val bounds = Rect(0, 0, source.width, source.height)
            Canvas(target).drawBitmap(source, bounds, bounds, null)
            check(target.colorSpace?.isSrgb == true && target.config == Bitmap.Config.ARGB_8888)
            return target
        } catch (failure: Throwable) {
            target.recycle()
            throw failure
        }
    }

    fun validateHdrPair(sdr: Bitmap, hdr: Bitmap) {
        require(!sdr.isRecycled && !hdr.isRecycled && sdr.width > 0 && sdr.height > 0)
        require(sdr.config == Bitmap.Config.ARGB_8888 && sdr.colorSpace?.isSrgb == true)
        require(hdr.config == Bitmap.Config.RGBA_F16 && hdr.colorSpace?.id ==
            ColorSpace.get(ColorSpace.Named.LINEAR_EXTENDED_SRGB).id) {
            "C donor HDR reference must remain linear extended sRGB RGBA_F16"
        }
        require(sdr.width == hdr.width && sdr.height == hdr.height) { "C SDR/HDR geometry mismatch" }
    }

    fun validateSidecar(sdr: Bitmap, sidecar: LuminanceGainMap) {
        val d = RawGainmapMath.DOWNSAMPLE
        val b = sidecar.bitmap
        require(!b.isRecycled && sidecar.encoding == LuminanceGainMapEncoding.LINEAR_RATIO &&
            b.config == Bitmap.Config.RGBA_F16 && b.colorSpace?.id ==
            ColorSpace.get(ColorSpace.Named.LINEAR_EXTENDED_SRGB).id &&
            b.width == (sdr.width + d - 1) / d && b.height == (sdr.height + d - 1) / d) {
            "C donor RAW gainmap luminance sidecar contract failed"
        }
    }
}
