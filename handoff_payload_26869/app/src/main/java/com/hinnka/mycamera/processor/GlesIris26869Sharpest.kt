package com.hinnka.mycamera.processor

import java.nio.ByteBuffer
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/** IRIS_26869_B_FROZEN_NORMAL_SHARPEST_REFERENCE
 * An immutable RAW16 green-phase spatial-coherence ranker. Scores only
 * shutter-frozen NORMAL planes. This is CPU sampling, NOT upstream RAWR's
 * Vulkan sharpness kernel. No additional frame, RAW rewrite, or exposure
 * policy changes. All output metadata is selected by index in native HDRq.
 */
internal object GlesIris26869Sharpest {
    private fun value(buf: ByteBuffer, stride: Int, x: Int, y: Int): Int =
        buf.getShort(y * stride + x * 2).toInt() and 0xffff

    fun select(
        frozen: GlesIris26864FrozenRawrIngress,
        cfa: Int,
        shutterIndex: Int,
    ): Int {
        frozen.assertUsable()
        require(cfa in 0..3 && shutterIndex in frozen.buffers.indices)
        val w=frozen.width
        val h=frozen.height
        if(w<64||h<64) return shutterIndex
        val scores=DoubleArray(frozen.buffers.size)
        val samples=IntArray(frozen.buffers.size)
        val shutterExposure=frozen.exposures[shutterIndex].toDouble()
        for(i in frozen.buffers.indices) {
            val e=frozen.exposures[i].toDouble()
            if(!e.isFinite()||e<=0.0||abs(e/shutterExposure-1.0)>0.20) continue
            val buf=frozen.buffers[i]
            val row=frozen.stridesBytes[i]
            val white=frozen.sensorWhiteByFrame[i].toDouble()
            var score=0.0
            var usable=0
            // Both physical green phases, every twelve sensor pixels.
            // Same-phase neighbors are displaced TWO physical pixels.
            for(phase in 0..1) {
                val yParity=phase
                val greenX=if(cfa==0||cfa==3) 1-yParity else yParity
                val black=frozen.blackByFrameByPhase[i*4+yParity*2+greenX].toDouble()
                val span=white-black
                if(span<=32.0) continue
                for(y in (h/12).coerceAtLeast(4) until (h-h/12).coerceAtMost(h-4) step 12) {
                    val py=(y and -2)+yParity
                    if(py<2||py>=h-2) continue
                    for(x in (w/12).coerceAtLeast(4) until (w-w/12).coerceAtMost(w-4) step 12) {
                        val px=(x and -2)+greenX
                        if(px<2||px>=w-2) continue
                        val c=(value(buf,row,px,py)-black)/span
                        val left=(value(buf,row,px-2,py)-black)/span
                        val right=(value(buf,row,px+2,py)-black)/span
                        val up=(value(buf,row,px,py-2)-black)/span
                        val down=(value(buf,row,px,py+2)-black)/span
                        // Bright clipping, near-black read noise and defective sites
                        // are not evidence of actual scene sharpness.
                        if(min(min(left,right),min(up,down))<0.045 ||
                           max(max(left,right),max(up,down))>0.94 ||
                           c<0.045 || c>0.94) continue
                        val gx=abs(right-left)
                        val gy=abs(down-up)
                        val lap=abs(4*c-left-right-up-down)
                        // Reward coherent edges, not isolated hot-pixel spikes.
                        val coherence=(gx+gy).coerceIn(0.0,0.5)
                        if(coherence<0.007) continue
                        score += min(lap,0.25)*coherence
                        usable++
                    }
                }
            }
            // Never nominate a sparse high-contrast light as the base.
            if(usable>=160) {scores[i]=score/usable;samples[i]=usable}
        }
        val baseline=scores[shutterIndex]
        val best=scores.indices.maxByOrNull { scores[it] } ?: shutterIndex
        val peak=scores[best]
        // No structure, marginal improvements, or unreliable scoring ->
        // preserve the true shutter-time reference and its metadata.
        if(peak<0.00008 || samples[best]<160) return shutterIndex
        if(baseline>0.0 && peak<baseline*1.08) return shutterIndex
        // Favor nearer timestamps for statistically equivalent sharpness.
        val shutterTime=frozen.timestampsNs[shutterIndex]
        val near=scores.indices.filter { samples[it]>=160 && scores[it]>=peak*0.98 }
        return near.minByOrNull { abs(frozen.timestampsNs[it]-shutterTime) } ?: best
    }
}
