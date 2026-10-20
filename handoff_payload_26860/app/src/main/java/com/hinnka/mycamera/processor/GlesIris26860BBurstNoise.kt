package com.hinnka.mycamera.processor

import android.graphics.ImageFormat
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * IRIS_26860_B_SENSOR_BURST_MEASURED_NOISE_OWNER.
 * Per-physical-phase sensor-linear temporal measurement, independent of Camera2's
 * shot/read coefficients. Never used by Experiment A, shared alignment/rejection,
 * DNG, LONG, Sabre or exposure/WB/LSC. Only reliable equal-exposure NORMAL bursts
 * can override B's denoiser noise coefficients. No RAW frame is discarded.
 */
internal object GlesIris26860BBurstNoise {
    internal data class Profile(
        val shot: FloatArray, val read: FloatArray, val measuredPhases: Int,
        val acceptedSites: IntArray, val mode: String,
    ) {
        init { require(shot.size == 4 && read.size == 4 && acceptedSites.size == 4) }
    }
    private const val BANDS = 4
    private const val STRIP = 32
    private const val STEP_X = 24
    private const val STEP_Y = 4
    private const val BINS = 12

    /**
     * Input coefficients are **physical TL/TR/BL/BR**, black and range are in RAW16
     * sensor units. Caller owns and keeps all NORMAL SafeImages alive through fitting.
     * Camera2 is a non-measured safety fallback, not the input used for fitted slope.
     */
    fun estimate(
        normals: List<RawStackFrame>, width: Int, height: Int,
        phaseBlackByFrame: List<FloatArray>, phaseRangeByFrame: List<FloatArray>,
        cameraShot: FloatArray, cameraRead: FloatArray,
    ): Profile {
        require(phaseBlackByFrame.size == normals.size && phaseRangeByFrame.size == normals.size &&
            phaseBlackByFrame.all { it.size == 4 } && phaseRangeByFrame.all { it.size == 4 } &&
            cameraShot.size == 4 && cameraRead.size == 4)
        fun fallback(reason: String) = Profile(cameraShot.copyOf(),cameraRead.copyOf(),0,
            IntArray(4),"CAMERA2_FALLBACK_$reason")
        if (normals.size < 6 || width < 192 || height < 256 || (width and 1) != 0 ||
            (height and 1) != 0 || phaseRangeByFrame.any { ranges ->
                ranges.any { !it.isFinite() || it <= 0f }
            }) return fallback("GEOMETRY")
        val first = normals.first()
        if (normals.any { it.rowFlickerHarmonic > 0 && it.rowFlickerStrength > 0.12f })
            return fallback("ACTIVE_FLICKER")
        if (normals.any { f -> f.role != RawBurstFrameRole.NORMAL ||
                f.image.format != ImageFormat.RAW_SENSOR || f.image.width != width || f.image.height != height ||
                f.image.pixelStrideBytes != 2 || f.image.rowStrideBytes < width*2 ||
                f.physicalCameraId != first.physicalCameraId ||
                f.sensitivityIso != first.sensitivityIso ||
                f.exposureTimeNs <= 0L || first.exposureTimeNs <= 0L ||
                abs(f.exposureTimeNs.toDouble()/first.exposureTimeNs.toDouble()-1.0)>0.012 }) {
            return fallback("MIXED_SOURCE")
        }
        // Fixed integer CFA sensor coordinates. Avoid resampled/correlated pixels
        // and spatial patch variance (which contains real texture/fixed-pattern noise).
        val tops=IntArray(BANDS) { i ->
            ((height*(2*i+1)/(2*BANDS)-STRIP/2).coerceIn(4,height-STRIP-4)) and -2
        }
        val xs=(8 until width-8 step STEP_X).toList()
        val sitesPerBand=xs.size*((STRIP-4)/STEP_Y)*4
        val total=sitesPerBand*BANDS
        val samples=FloatArray(total*normals.size) { Float.NaN }
        val flat=BooleanArray(total) { true }
        try {
            for ((fi, frame) in normals.withIndex()) {
                val image=frame.image
                val phaseBlack=phaseBlackByFrame[fi]
                val phaseRange=phaseRangeByFrame[fi]
                val mem=if (!image.isFileBacked) image.planes.singleOrNull()?.buffer
                    ?.duplicate()?.order(ByteOrder.nativeOrder()) else null
                if (!image.isFileBacked && mem == null) return fallback("MISSING_PLANE")
                if (mem != null && mem.limit() < image.rowStrideBytes*height) return fallback("PLANE_SIZE")
                for (band in 0 until BANDS) {
                    val region=if (image.isFileBacked)
                        image.readFileRegion(0,tops[band],width,STRIP) else null
                    try {
                        val bytes=(region?.buffer ?: mem!!).duplicate().order(ByteOrder.nativeOrder())
                        val rowStride=region?.rowStride ?: image.rowStrideBytes
                        val yBase=if (region!=null) 0 else tops[band]
                        fun at(x:Int, y:Int):Int {
                            val ofs=(yBase+y)*rowStride+x*2
                            return bytes.getShort(ofs).toInt() and 65535
                        }
                        for (yi in 0 until (STRIP-4)/STEP_Y) {
                            val y=2+yi*STEP_Y
                            for ((xi,x) in xs.withIndex()) {
                                for (phase in 0..3) {
                                    val px=(x and -2)+(phase and 1)
                                    val py=y+(phase shr 1)
                                    val index=band*sitesPerBand+((yi*xs.size+xi)*4+phase)
                                    val raw=at(px,py)
                                    val v=((raw.toFloat()-phaseBlack[phase])/phaseRange[phase])
                                    samples[fi*total+index]=v
                                    if (fi==0) {
                                        val neighborRaw=intArrayOf(at(px-2,py),at(px+2,py),
                                            at(px,py-2),at(px,py+2))
                                        // Flatness from *same phase* witnesses only; does not
                                        // interpret hair/denim/fiber as random sensor noise.
                                        val spread=neighborRaw.max()-neighborRaw.min()
                                        val maxSpread=max(0.016f,0.045f*v.coerceAtLeast(0f))*phaseRange[phase]
                                        flat[index]=v in 0.008f..0.965f && spread<=maxSpread
                                    }
                                }
                            }
                        }
                    } finally { region?.close() }
                }
            }
        } catch (_: Exception) { return fallback("UNAVAILABLE_RAW") }
        // Sites within the same bin represent independent sensor locations.
        // Temporal per-site variance removes fixed-pattern offsets and texture.
        val bins=Array(4){Array(BINS){ArrayList<Double>()}}
        val sums=Array(4){DoubleArray(BINS)}
        for (site in 0 until total) {
            if (!flat[site]) continue
            val phase=site and 3
            val values=ArrayList<Double>(normals.size)
            for (fi in normals.indices) {
                val value=samples[fi*total+site]
                if (value.isFinite() && value in 0.0f..0.970f) values+=value.toDouble()
            }
            if (values.size < max(6,(normals.size*4)/5)) continue
            values.sort()
            val mid=values[values.size/2]
            val absdev=values.map{abs(it-mid)}.sorted()
            val mad=absdev[absdev.size/2]
            val cap=max(0.015,6.0*mad*1.4826)
            val kept=values.filter{abs(it-mid)<=cap}
            if (kept.size < max(6,(normals.size*4)/5)) continue
            val mean=kept.average()
            if (mean !in 0.008..0.965) continue
            val var0=kept.sumOf{(it-mean)*(it-mean)}/(kept.size-1)
            if (!var0.isFinite() || var0<=0.0) continue
            val bin=min(BINS-1,(mean*BINS).toInt())
            bins[phase][bin]+=var0
            sums[phase][bin]+=mean
        }
        val shot=cameraShot.copyOf(); val read=cameraRead.copyOf()
        val accepted=IntArray(4)
        var measured=0
        var fitted=0
        for (phase in 0..3) {
            val data=ArrayList<Triple<Double,Double,Double>>()
            for (bin in 0 until BINS) {
                val v=bins[phase][bin]
                accepted[phase]+=v.size
                if (v.size < 35) continue
                v.sort()
                // Unbiased temporal variance with median across sensor locations
                // resists moving shadows, sensor defects and accidental texture.
                val variance=v[v.size/2]*1.07
                val level=sums[phase][bin]/v.size
                data+=Triple(level,variance,v.size.toDouble())
            }
            if (accepted[phase] < 350 || data.isEmpty()) continue
            var newShot=Double.NaN; var newRead=Double.NaN
            val dynamic=(data.maxOf{it.first}-data.minOf{it.first})
            if(data.size>=3 && dynamic>=0.10) {
                val w=data.sumOf{it.third};val mx=data.sumOf{it.first*it.third}/w
                val my=data.sumOf{it.second*it.third}/w
                val d=data.sumOf{it.third*(it.first-mx)*(it.first-mx)}
                if(d>1e-7){newShot=data.sumOf{it.third*(it.first-mx)*(it.second-my)}/d
                    newRead=my-newShot*mx}
                if(newShot>=0.0 && newRead>=0.0 && newShot.isFinite() && newRead.isFinite()) fitted++
                else {newShot=Double.NaN;newRead=Double.NaN}
            }
            if (!newShot.isFinite() || !newRead.isFinite()) {
                // Insufficient radiometric spread to identify two coefficients:
                // measure amplitude from temporal variance; retain Camera2 shape.
                val ratios=data.map { (level,variance,_) ->
                    variance/max(1e-9,cameraShot[phase].toDouble()*level+cameraRead[phase])
                }.sorted()
                val scale=ratios[ratios.size/2].coerceIn(0.25,4.0)
                newShot=cameraShot[phase].toDouble()*scale;newRead=cameraRead[phase].toDouble()*scale
            }
            // A physically implausible or motion-biased burst must not replace
            // the calibrated fallback. These broad bounds are safety rails,
            // not a forced Camera2 agreement for ordinary valid measurements.
            val oldVar=cameraShot[phase]*0.10+cameraRead[phase]
            val newVar=newShot*0.10+newRead
            val oldDark=cameraShot[phase]*0.02+cameraRead[phase]
            val newDark=newShot*0.02+newRead
            if(newShot>=0.0 && newRead>=0.0 && newShot<0.15 && newRead<0.025 &&
                newVar>=max(1e-9,oldVar*0.20) && newVar<=max(1e-8,oldVar*5.0) &&
                newDark>=max(1e-9,oldDark*0.20) && newDark<=max(1e-8,oldDark*5.0)) {
                shot[phase]=newShot.toFloat();read[phase]=newRead.toFloat();measured++
            }
        }
        return Profile(shot,read,measured,accepted,
            if(measured==4) "BURST_${if(fitted==4)"SHOT_READ" else "PARTIAL_FIT"}"
            else if(measured>0) "BURST_PHASE_PARTIAL" else "CAMERA2_FALLBACK_INSUFFICIENT_SUPPORT")
    }
}
