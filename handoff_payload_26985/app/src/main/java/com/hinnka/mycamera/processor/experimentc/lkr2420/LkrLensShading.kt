// SPDX-FileCopyrightText: 2026 RawLens contributors
// SPDX-License-Identifier: GPL-3.0-or-later
package com.hinnka.mycamera.processor.experimentc.lkr2420

internal object LkrLensShading {
    /** Merge's raw clip level (lkrl SolveParams::clip): its highlight neutralise starts at 0.85 of it. */
    private const val HIGHLIGHT_CLIP = 0.98f

    /**
     * Shading gains for one interleaved pixel. With [wb] (LK-R), blown highlights stay white: the merge
     * neutralised them at G = 1, but shading gains above 1 push G over the DNG's [0, 1] clamp, which cuts
     * G and leaves R / B -> pink (also bright unblown pixels pushed over 1 by the gain). Same rule as
     * lkrl FinishLook: smoothstep(0.85, 1) of the brightest channel (before shading against the raw clip,
     * after it against the file's 1.0), blend to neutral at the wb-space luma, capped at min(wb) so the
     * clamped file stays neutral. [white] = the clip level of an HDR merge (all levels scale with it).
     */
    private fun shadePixel(rgb: java.nio.FloatBuffer, i: Int, gR: Float, gG: Float, gB: Float, wb: FloatArray?, white: Float = 1f) {
        val r0 = rgb.get(i); val g0 = rgb.get(i + 1); val b0 = rgb.get(i + 2)
        var r = r0 * gR; var g = g0 * gG; var b = b0 * gB
        if (wb != null) {
            val v = maxOf(maxOf(r0, g0, b0) / HIGHLIGHT_CLIP, maxOf(r, g, b)) / white
            var m = ((v - 0.85f) / 0.15f).coerceIn(0f, 1f)
            m = m * m * (3f - 2f * m)
            if (m > 0f) {
                val lum = minOf(0.25f * wb[0] * r + 0.5f * wb[1] * g + 0.25f * wb[2] * b, minOf(wb[0], wb[1], wb[2]) * white)
                r += m * (lum / wb[0] - r); g += m * (lum / wb[1] - g); b += m * (lum / wb[2] - b)
            }
        }
        rgb.put(i, r); rgb.put(i + 1, g); rgb.put(i + 2, b)
    }

    /**
     * Lens shading for a merge of a sensor sub-region (LK-R zoom): output
     * pixel (x, y) sits at sensor (x0 + (x + 0.5) * sx, y0 + (y + 0.5) * sy).
     */
    internal fun applyShadingMapped(
        rgb: java.nio.FloatBuffer, w: Int, h: Int, model: LensShadingModel,
        x0: Int, y0: Int, sx: Float, sy: Float, highlightWb: FloatArray? = null, white: Float = 1f
    ) {
        if (model.alreadyApplied) return
        ShardWorkers.forEachShard(h) { ya, yb ->
            for (y in ya until yb) {
                val syy = (y0 + (y + 0.5f) * sy).toInt()
                for (x in 0 until w) {
                    val sxx = (x0 + (x + 0.5f) * sx).toInt()
                    val i = 3 * (y * w + x)
                    val gG = 0.5f * (model.gainAt(sxx, syy, CfaColor.GREEN, 0) + model.gainAt(sxx, syy, CfaColor.GREEN, 1))
                    shadePixel(rgb, i, model.gainAt(sxx, syy, CfaColor.RED), gG, model.gainAt(sxx, syy, CfaColor.BLUE), highlightWb, white)
                }
            }
        }
    }

}
