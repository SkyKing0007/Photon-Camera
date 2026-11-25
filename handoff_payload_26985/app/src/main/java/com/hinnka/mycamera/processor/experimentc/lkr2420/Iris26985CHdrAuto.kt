// SPDX-License-Identifier: GPL-3.0-or-later
package com.hinnka.mycamera.processor.experimentc.lkr2420

import java.nio.ByteBuffer
import kotlin.math.pow

// The exact donor meter reads only these RAW view properties.
internal data class RawImageView(val width:Int,val height:Int,val buffer:ByteBuffer?,val rowStride:Int,val pixelStride:Int)
enum class LkrHdrMode { OFF, AUTO, ON }

/** The donor's measurement/decision, with Iris frozen physical exposure limits. */
object Iris26985CHdrAuto {
    const val LONG_CAP_NS = 125_000_000L
    @JvmStatic fun plan(raw:ByteBuffer, width:Int,height:Int,rowStride:Int,pixelStride:Int,
        black:FloatArray,white:Float,tile:Int,baseNs:Long,minNs:Long,maxNs:Long,total:Int):FloatArray {
        if(total<3 || width<4 || height<4 || tile<=0 || baseNs<=0 || minNs<=0 || maxNs<minNs ||
            black.size!=4 || !white.isFinite() || black.any{!it.isFinite()||it<0f||it>=white} ||
            pixelStride!=2 || rowStride<width*2 || rowStride%2!=0 ||
            raw.remaining().toLong()<(height-1L)*rowStride+width*2L) return FloatArray(0)
        val stats=LkrHdrDecision.measure(RawImageView(width,height,raw.slice(),rowStride,pixelStride),black,white)
        val fraction=tile.toDouble()*tile/(width.toDouble()*height)
        val longNs=shutterNs(baseNs,LkrHdrDecision.LONG_EV)
        val plan=LkrHdrDecision.decide(LkrHdrMode.AUTO,stats,fraction,longNs<=minOf(maxNs,LONG_CAP_NS),total)
        return plan.evs.filter{shutterNs(baseNs,it) in minNs..maxNs}.toFloatArray()
    }
    @JvmStatic fun shutterNs(baseNs:Long,ev:Float):Long = kotlin.math.round(baseNs*2.0.pow(ev.toDouble())).toLong()
}
