package com.hinnka.mycamera.processor.experimentc

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Gainmap
import android.util.Log
import java.nio.ByteBuffer
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.roundToInt

/** C OFF publication only. No RAW, tone, sharpening, HDR-reference or encoder changes. */
internal object Iris26994COffWatermark {
    private const val ASSET_WIDTH = 2048
    private const val ASSET_HEIGHT = 1312
    internal data class Geometry(val width: Int, val height: Int) {
        val wmWidth = width * 0.115f
        val wmHeight = wmWidth * (ASSET_HEIGHT.toFloat() / ASSET_WIDTH)
        val margin = maxOf(2f, minOf(width, height) * 0.025f)
        val left = width - margin - wmWidth
        val top = height - margin - wmHeight
        val x0 = ceil(left - 0.5f).toInt().coerceIn(0, width - 1)
        val y0 = ceil(top - 0.5f).toInt().coerceIn(0, height - 1)
        val x1 = (floor(left + wmWidth - 0.5f).toInt() + 1).coerceIn(x0 + 1, width)
        val y1 = (floor(top + wmHeight - 0.5f).toInt() + 1).coerceIn(y0 + 1, height)
        val w = x1 - x0
        val h = y1 - y0
    }

    // Exact C ON encoder's five rounded output sample positions, encoded luma and threshold.
    internal fun useDark(g: Geometry, pixel: (Int, Int) -> Int): Boolean {
        val samples = arrayOf(0.2f to 0.2f, 0.8f to 0.2f, 0.5f to 0.5f, 0.2f to 0.8f, 0.8f to 0.8f)
        var luma = 0f
        for ((u,v) in samples) {
            val c = pixel((g.left + g.wmWidth*u).roundToInt().coerceIn(0,g.width-1),
                (g.top + g.wmHeight*v).roundToInt().coerceIn(0,g.height-1))
            luma += 0.2126f*((c ushr 16 and 255)/255f) + 0.7152f*((c ushr 8 and 255)/255f) + 0.0722f*((c and 255)/255f)
        }
        return luma/5f >= 0.55f
    }

    /** Bilinear sampling in premultiplied encoded sRGB, followed by source-over on
     * the existing encoded SDR raster. Never apply alpha twice (dark fringe).
     * Return alpha at this output pixel for the corresponding local HDR gain support. */
    internal fun composite(g: Geometry, logo: IntArray, pixels: IntArray): ByteArray {
        require(logo.size == ASSET_WIDTH*ASSET_HEIGHT && pixels.size == g.w*g.h)
        val mask = ByteArray(pixels.size)
        for (y in 0 until g.h) for (x in 0 until g.w) {
            val sx = ((g.x0+x+0.5f-g.left)/g.wmWidth*ASSET_WIDTH - 0.5f).coerceIn(0f,ASSET_WIDTH-1f)
            val sy = ((g.y0+y+0.5f-g.top)/g.wmHeight*ASSET_HEIGHT - 0.5f).coerceIn(0f,ASSET_HEIGHT-1f)
            val ix = sx.toInt(); val iy = sy.toInt()
            val nx = minOf(ix+1,ASSET_WIDTH-1); val ny = minOf(iy+1,ASSET_HEIGHT-1)
            val fx = sx-ix; val fy = sy-iy
            val p0 = logo[iy*ASSET_WIDTH+ix]; val p1 = logo[iy*ASSET_WIDTH+nx]
            val p2 = logo[ny*ASSET_WIDTH+ix]; val p3 = logo[ny*ASSET_WIDTH+nx]
            val w0 = (1f-fx)*(1f-fy)*(p0 ushr 24)/255f
            val w1 = fx*(1f-fy)*(p1 ushr 24)/255f
            val w2 = (1f-fx)*fy*(p2 ushr 24)/255f
            val w3 = fx*fy*(p3 ushr 24)/255f
            val a = (w0+w1+w2+w3).coerceIn(0f,1f)
            val i = y*g.w+x
            val coverage = (a*255f).roundToInt()
            if (coverage == 0) continue
            mask[i] = coverage.toByte()
            val old = pixels[i]
            fun blend(shift: Int): Int = ((old ushr shift and 255)*(1f-a) +
                (p0 ushr shift and 255)*w0 + (p1 ushr shift and 255)*w1 +
                (p2 ushr shift and 255)*w2 + (p3 ushr shift and 255)*w3).roundToInt().coerceIn(0,255)
            pixels[i] = (old and 0xff000000.toInt()) or (blend(16) shl 16) or (blend(8) shl 8) or blend(0)
        }
        return mask
    }

    /** 26993 gain code is log2(ratio), with unity=0. Only samples whose bilinear
     * footprint actually touches the logo may change. Use max coverage across
     * their supporting pixels so opaque logo pixels cannot receive HDR boost.
     * No rectangular blackout, no global gain change, no new gainmap metadata. */
    internal fun neutralize(g: Geometry, mask: ByteArray, gain: ByteArray,
                            gw: Int, gh: Int, stride: Int): Int {
        require(mask.size == g.w*g.h && gw == (g.width+1)/2 && gh == (g.height+1)/2 &&
            stride >= gw && gain.size == stride*gh)
        val coverage = ByteArray(gain.size)
        for (y in 0 until g.h) for (x in 0 until g.w) {
            val a = mask[y*g.w+x].toInt() and 255
            if (a == 0) continue
            val sx = ((g.x0+x+0.5)*gw/g.width-0.5).coerceIn(0.0,gw-1.0)
            val sy = ((g.y0+y+0.5)*gh/g.height-0.5).coerceIn(0.0,gh-1.0)
            val ix = sx.toInt(); val iy = sy.toInt()
            val nx = ceil(sx).toInt(); val ny = ceil(sy).toInt()
            fun cover(i: Int) { if (a > (coverage[i].toInt() and 255)) coverage[i] = a.toByte() }
            cover(iy*stride+ix); cover(iy*stride+nx); cover(ny*stride+ix); cover(ny*stride+nx)
        }
        var changed = 0
        for (i in gain.indices) {
            val a = coverage[i].toInt() and 255
            if (a == 0) continue
            val old = gain[i].toInt() and 255
            val code = (old*(255-a)+127)/255
            if (code != old) { gain[i] = code.toByte(); changed++ }
        }
        return changed
    }

    fun apply(context: Context, source: Bitmap, gainmap: Gainmap): Bitmap {
        require(!source.isRecycled && source.config == Bitmap.Config.ARGB_8888 && source.colorSpace?.isSrgb == true &&
            source.width >= 16 && source.height >= 16)
        val g = Geometry(source.width, source.height)
        val useDark = useDark(g, source::getPixel)
        val asset = if (useDark) "watermark/iris_camera_watermark_dark.png" else "watermark/iris_camera_watermark_white.png"
        val logo = context.assets.open(asset).use {
            checkNotNull(BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply {
                inScaled = false; inPreferredConfig = Bitmap.Config.ARGB_8888
            }))
        }
        val colors = try {
            require(logo.width == ASSET_WIDTH && logo.height == ASSET_HEIGHT && logo.config == Bitmap.Config.ARGB_8888)
            IntArray(ASSET_WIDTH*ASSET_HEIGHT).also { logo.getPixels(it,0,ASSET_WIDTH,0,0,ASSET_WIDTH,ASSET_HEIGHT) }
        } finally { logo.recycle() }
        val pixels = IntArray(g.w*g.h)
        source.getPixels(pixels,0,g.w,g.x0,g.y0,g.w,g.h)
        val mask = composite(g,colors,pixels)
        check(mask.any { it.toInt() != 0 }) { "C OFF watermark has no coverage" }
        val gm = gainmap.gainmapContents
        require(!gm.isRecycled && gm.isMutable && gm.config == Bitmap.Config.ALPHA_8 &&
            gainmap.ratioMin.all { it == 1f } && gainmap.gamma.all { it == 1f } &&
            gainmap.epsilonSdr.contentEquals(gainmap.epsilonHdr)) { "Unexpected C OFF gainmap contract" }
        val codes = ByteArray(gm.byteCount)
        gm.copyPixelsToBuffer(ByteBuffer.wrap(codes))
        val changed = neutralize(g,mask,codes,gm.width,gm.height,gm.rowBytes)
        val target = if (source.isMutable) source else checkNotNull(source.copy(Bitmap.Config.ARGB_8888,true))
        try {
            // Only write nontransparent spans. Every untouched SDR pixel is bit-identical.
            for (y in 0 until g.h) {
                var x = 0
                while (x < g.w) {
                    while (x < g.w && mask[y*g.w+x].toInt() == 0) x++
                    val start = x
                    while (x < g.w && mask[y*g.w+x].toInt() != 0) x++
                    if (x > start) target.setPixels(pixels,y*g.w+start,g.w,g.x0+start,g.y0+y,x-start,1)
                }
            }
            if (changed != 0) gm.copyPixelsFromBuffer(ByteBuffer.wrap(codes))
            Log.i("COffWatermark", "IRIS_26994_C_OFF_WATERMARK variant=${if (useDark) "DARK_ON_BRIGHT" else "WHITE_ON_DARK"} final=${g.width}x${g.height} gainSamples=$changed")
            return target
        } catch (failure: Throwable) {
            if (target !== source) target.recycle()
            throw failure
        }
    }
}
