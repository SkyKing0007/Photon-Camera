package com.hinnka.mycamera.processor.experimentc.original129.hdr
import kotlin.math.*
fun main() {
    var count = 0
    val strengths = listOf(0.25f, 1f, 2f)
    for (strength in strengths) {
        for (si in 0..1000) {
            val s = si / 1000f
            var last = 1f
            for (hi in 0..400) {
                val h = hi / 50f
                val g = RawGainmapMath.highlightGainRatio(s, h, strength)
                check(g.isFinite() && g >= 1f && g <= 2f)
                check(g + 1e-6f >= last)
                if (s <= 0.40f || h <= 1f) check(g == 1f)
                check(g <= 1f + (h - 1f).coerceAtLeast(0f)/(s+RawGainmapMath.OFFSET) + 1e-6f)
                last = g
                count++
            }
        }
    }
    for (si in 0..255) {
        val s=si/255f
        for (hi in 0..128) {
            val h=hi/16f
            val a=RawGainmapMath.encode(s,h)
            val b=RawGainmapMath.encodeLuminance(floatArrayOf(s,s,s),floatArrayOf(h,h,h),1f)
            check(abs(a-b)<2e-6f)
            val decoded=RawGainmapMath.reconstructLinear(s,a)
            check(decoded + 1e-6f >= RawGainmapMath.srgbToLinear(s))
            count += 2
        }
    }
    // Smooth lighting gradients: no derivative discontinuity at either knee.
    val d=0.0001f
    for (s in listOf(0.4f,0.8f)) {
        val f = { x:Float -> RawGainmapMath.highlightGainRatio(x,2f,1f) }
        check(abs((f(s+d)-f(s))/d-(f(s)-f(s-d))/d)<0.02f)
    }
    for (h in listOf(1f,1.5f)) {
        val f = { x:Float -> RawGainmapMath.highlightGainRatio(0.9f,x,1f) }
        check(abs((f(h+d)-f(h))/d-(f(h)-f(h-d))/d)<0.02f)
    }
    println("PASS Kotlin physical policy $count cases; unity/no darkening/bounds/monotonic HDR headroom/CPU luma parity/continuity")
    // Exact encoded CPU reference for the GPU rendering test, 64 x 64.
    for (y in 0..63) for (x in 0..63) {
        val s=(x*255/63)/255f
        val h=y/8f
        val g=RawGainmapMath.encodeLuminance(floatArrayOf(s,s,s),floatArrayOf(h,h,h),1f)
        println(g)
    }
}
