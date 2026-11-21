package com.hinnka.mycamera.processor

import java.nio.ByteOrder
import kotlin.math.max
import kotlin.math.sqrt

/**
 * C-only measurement of the actual shutter-reference green RAW, not an assumed
 * 0.18/average scene or ISO proxy. The sampling, 1024-linear-bin histogram
 * quantization and variance-stabilized mean follow pinned bjzhou 1.29.0
 * `GlesMgcRawSpatialStacker.estimateReferenceGreenSignal`.
 *
 * No Android-device quality claims. Caller must keep the Image/plane open.
 */
internal object Iris26972CMeasuredRawSnr {
    private const val LINEAR_BINS=1024
    private const val ROW_STEP=8
    private const val COMPONENT="26972 C shutter RAW reference measured SNR"

    internal data class Measurement(val referenceSignal:Float,val referenceSnr:Float,
        val samples:Int,val phase:Int)

    internal fun measure(
        physical:Iris26972CPhysicalRawMetadata.Frozen,
        plane:Iris26972CDonorSabreGpuRawIngress.Plane,
    ):Measurement {
        Iris26972CDonorSabreGpuRawIngress.validate(plane)
        val white=physical.sensorWhiteLevel
        val black=physical.copyCanonicalBlackForAudit()
        val (shot,read)=physical.copyCanonicalNoiseForAudit()
        val greenPhase=if(physical.cfaPattern==0 || physical.cfaPattern==3)1 else 0
        val greenChannel=when(physical.cfaPattern) {
            0->1; 1->1; 2->2; 3->2
            else->error("$COMPONENT impossible Bayer phase")
        }
        val blackGreen=black[greenChannel]
        val range=white.toFloat()-blackGreen
        require(range>0 && range.isFinite() && shot[greenChannel]>0 &&
            read[greenChannel]>=0 && read[greenChannel].isFinite()) {
            "$COMPONENT physical reference noise unavailable"
        }
        val w=plane.cropWidth
        val h=plane.cropHeight
        val left=(w/8) and -4
        val right=(w*7/8) and -4
        val top=(h/8) and -2
        val bottom=(h*7/8) and -2
        require(right>left && bottom>top) {"$COMPONENT empty real RAW sampling support"}
        val tail=white-LINEAR_BINS
        val shift=if(tail<LINEAR_BINS)0 else
            32-Integer.numberOfLeadingZeros(tail ushr 10)
        require(shift in 0..6) {"$COMPONENT unexpected true RAW histogram quantization"}
        val quantWidth=1 shl shift
        val quantHalf=quantWidth/2
        val buffer=plane.data.duplicate().order(ByteOrder.nativeOrder())
        val offsetStart=buffer.position()+plane.cropTop*plane.rowStrideBytes+plane.cropLeft*2
        var count=0
        var sumSqrt=0.0
        var y=top
        while(y<bottom) {
            var x=left+(greenPhase and 1)
            while(x<right) {
                val offset=offsetStart+y*plane.rowStrideBytes+x*2
                require(offset>=0 && offset+2<=buffer.limit()) {"$COMPONENT stale RAW plane"}
                val raw=buffer.getShort(offset).toInt() and 0xffff
                val bin=if(shift==0||raw<LINEAR_BINS)raw else
                    LINEAR_BINS+(((raw-LINEAR_BINS) shr shift) shl shift)+quantHalf
                val signal=max(bin.toFloat()-blackGreen,0f)
                sumSqrt+=sqrt(signal.toDouble())
                count++
                x+=2
            }
            y+=ROW_STEP
        }
        require(count>0) {"$COMPONENT no actual reference RAW samples"}
        val meanSqrt=sumSqrt/count
        val normalizedSignal=(meanSqrt*meanSqrt/range.toDouble()).toFloat()
        // Pinned donor's `noiseVarianceAtSignal` averages BOTH green-phase
        // Camera2 S/O coefficients, even though mean RAW is sampled from the
        // first-row green phase. A single-phase variance biases SNR when the
        // sensor's Gr/Gb noise differs.
        val greenShot=0.5f*(shot[1]+shot[2])
        val greenRead=0.5f*(read[1]+read[2])
        val variance=greenShot*normalizedSignal+greenRead
        val snr=if(variance>1e-12f) normalizedSignal/sqrt(variance) else 0f
        require(normalizedSignal.isFinite() && normalizedSignal>=0f &&
            snr.isFinite()&&snr>=0f) {"$COMPONENT actual RAW signal SNR invalid"}
        return Measurement(normalizedSignal,snr,count,greenPhase)
    }
}
