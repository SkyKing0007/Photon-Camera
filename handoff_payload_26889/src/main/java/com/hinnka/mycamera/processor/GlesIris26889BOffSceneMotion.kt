package com.hinnka.mycamera.processor

import java.nio.ByteBuffer
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * IRIS_26889_B_OFF_SHUTTER_ADJACENT_REFERENCE_AND_LONG_POLICY
 * Capture-local, RAW-only static/motion confidence. No semantic object labels,
 * no A, Wronski B ON, Night, DNG or vendor producer participation.
 *
 * The camera may shake while the scene is static: fit local translations
 * BEFORE detecting independently moving structures. Ambiguous results never
 * grant a later whole-burst reference or a separate LONG exposure.
 */
internal object GlesIris26889BOffSceneMotion {
    internal data class Decision(
        val staticTrusted: Boolean,
        val shutterAdjacent: Set<Int>,
        val reliablePatches: Int,
        val movingPatches: Int,
        val unexplainedPatches: Int,
        val comparedFrames: Int,
    )

    private data class Match(val dx:Int, val dy:Int, val loss:Float, val atZero:Float, val structure:Float)

    private fun median(values:List<Int>):Int = values.sorted()[values.size/2]

    fun classify(frozen:GlesIris26864FrozenRawrIngress, cfa:Int, shutterIndex:Int):Decision {
        frozen.assertUsable()
        require(cfa in 0..3 && shutterIndex in frozen.buffers.indices)
        val t0=frozen.timestampsNs[shutterIndex]
        require(t0>0L && frozen.timestampsNs.toSet().size==frozen.buffers.size)
        // Processing order begins with the shutter frame; chronological order
        // must be reconstructed from sensor timestamps, never list position.
        val nearest=frozen.buffers.indices.sortedWith(compareBy<Int> {
            val dt=if(frozen.timestampsNs[it]>t0) frozen.timestampsNs[it]-t0
                   else t0-frozen.timestampsNs[it]
            dt
        }.thenBy { frozen.timestampsNs[it] })
        val adjacent=nearest.take(min(3,nearest.size)).toSet()
        if (frozen.width<128 || frozen.height<128 || frozen.buffers.size<3) {
            return Decision(false,adjacent,0,0,0,0)
        }
        // Restrict checks to the exposures closest to the shutter. Capture
        // geometry is constant and the physical lens has already been verified.
        val peers=nearest.filter { it!=shutterIndex }
        val referenceExposure=frozen.exposures[shutterIndex]
        if(!referenceExposure.isFinite() || referenceExposure<=0f) {
            return Decision(false,adjacent,0,0,0,0)
        }
        val greenX=if(cfa==0 || cfa==3) 1 else 0
        val centers=ArrayList<Pair<Int,Int>>(48)
        for (y in 1..6) for (x in 1..8) {
            val px=((frozen.width.toLong()*x/9).toInt() and -2)+greenX
            val py=((frozen.height.toLong()*y/7).toInt() and -2)
            if(px in 32 until frozen.width-32 && py in 32 until frozen.height-32) centers.add(px to py)
        }
        if(centers.size<20)return Decision(false,adjacent,0,0,0,0)
        val ref=frozen.buffers[shutterIndex]
        val refStride=frozen.stridesBytes[shutterIndex]
        val blackRef=frozen.blackByFrameByPhase[shutterIndex*4+greenX]
        val whiteRef=frozen.sensorWhiteByFrame[shutterIndex]
        if(!(whiteRef>blackRef+1f))return Decision(false,adjacent,0,0,0,0)
        fun read(b:ByteBuffer,stride:Int,x:Int,y:Int,black:Float,white:Float,expRatio:Float):Float {
            val raw=b.getShort(y*stride+x*2).toInt() and 0xffff
            return ((raw-black)/max(1f,white-black)*expRatio).coerceIn(0f,1.5f)
        }
        var good=0;var moving=0;var unexplained=0;var compared=0
        for(peer in peers) {
            val exposure=frozen.exposures[peer]
            if(!exposure.isFinite() || exposure<=0f || abs(exposure/referenceExposure-1f)>0.06f)
                return Decision(false,adjacent,good,moving,unexplained,compared)
            val other=frozen.buffers[peer]
            val stride=frozen.stridesBytes[peer]
            val black=frozen.blackByFrameByPhase[peer*4+greenX]
            val white=frozen.sensorWhiteByFrame[peer]
            val ratio=referenceExposure/exposure
            if(!(white>black+1f))return Decision(false,adjacent,good,moving,unexplained,compared)
            val matches=ArrayList<Match>(centers.size)
            for((cx,cy) in centers) {
                val src=FloatArray(25)
                var k=0;var low=Float.POSITIVE_INFINITY;var high=0f
                for(iy in -2..2) for(ix in -2..2){
                    val value=read(ref,refStride,cx+ix*4,cy+iy*4,blackRef,whiteRef,1f)
                    src[k++]=value
                    low=min(low,value);high=max(high,value)
                }
                val structure=high-low
                // Only structurally supported tiles can yield a motion vector.
                // Flat high-ISO noise must not be mistaken for a moving object.
                if (structure<0.08f || low<0.015f || high>0.96f) continue
                var bestLoss=Float.POSITIVE_INFINITY;var bestDx=0;var bestDy=0;var zeroLoss=0f
                for(dy in -12..12 step 2) for(dx in -12..12 step 2) {
                    var loss=0f;k=0
                    for(iy in -2..2) for(ix in -2..2) {
                        val v=read(other,stride,cx+ix*4+dx,cy+iy*4+dy,black,white,ratio)
                        loss+=abs(v-src[k++])
                    }
                    loss/=25f
                    if(dx==0 && dy==0)zeroLoss=loss
                    if(loss<bestLoss-0.000001f ||
                       (abs(loss-bestLoss)<=0.000001f && abs(dx)+abs(dy)<abs(bestDx)+abs(bestDy))) {
                        bestLoss=loss;bestDx=dx;bestDy=dy
                    }
                }
                matches.add(Match(bestDx,bestDy,bestLoss,zeroLoss,structure))
            }
            compared++
            val coherent=matches.filter { it.loss<0.13f && it.structure>0.10f }
            good+=coherent.size
            if (coherent.size<max(8,centers.size/4)) {
                return Decision(false,adjacent,good,moving,unexplained,compared)
            }
            val globalX=median(coherent.map { it.dx })
            val globalY=median(coherent.map { it.dy })
            if(abs(globalX)>=12 || abs(globalY)>=12) {
                // Insufficient support for large camera motion: never promote
                // LONG or a temporally distant sharpest frame.
                return Decision(false,adjacent,good,moving,unexplained,compared)
            }
            var localOutliers=0;var inconsistent=0
            for(m in matches) {
                if(m.structure<0.10f) continue
                val difference=abs(m.dx-globalX)+abs(m.dy-globalY)
                if(m.loss<0.12f && difference>=6 && m.atZero-m.loss>=0.025f)
                    localOutliers++
                // Structural changes that *no* 2D translation could match,
                // such as a changing TV image or a moving occlusion.
                if(m.loss>0.115f && m.loss>0.50f*m.structure)
                    inconsistent++
            }
            moving+=localOutliers
            unexplained+=inconsistent
            if(localOutliers>=max(3,centers.size/12) || inconsistent>=max(3,centers.size/10)) {
                return Decision(false,adjacent,good,moving,unexplained,compared)
            }
        }
        return Decision(compared>=2 && good>=24 && moving==0 && unexplained==0,
                        adjacent,good,moving,unexplained,compared)
    }
}
