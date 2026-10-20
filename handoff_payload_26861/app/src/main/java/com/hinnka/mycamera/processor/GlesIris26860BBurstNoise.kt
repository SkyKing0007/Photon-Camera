package com.hinnka.mycamera.processor

import android.graphics.ImageFormat
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * IRIS_26861_B_ONLY_EMPIRICAL_CFA_NOISE.
 * This owner never reads Camera2 SENSOR_NOISE_PROFILE or another noise model.
 * Four Bayer phases are fitted independently from consecutive NORMAL RAW-pair
 * differences after phase-preserving local integer registration. The search and
 * variance samples are disjoint to avoid fitting down the noise via min-SSD.
 * Observations in badly aligned, moving or clipped blocks are rejected; only
 * low-variance static quantiles per radiance bin enter the fit. Fractionally
 * shifted texture increases residuals and is rejected instead of pretending
 * correlated interpolated pixels are independent sensor observations.
 */
internal object GlesIris26860BBurstNoise {
    internal data class Profile(
        val shot: FloatArray, val read: FloatArray, val measuredPhases: Int,
        val acceptedSites: IntArray, val mode: String,
        val signalBins: IntArray, val samplePairs: Int,
    ) {
        init { require(shot.size == 4 && read.size == 4 && acceptedSites.size == 4 && signalBins.size == 4) }
        val fullyMeasured: Boolean get() = measuredPhases == 4
    }
    private const val STRIP_HEIGHT = 48
    private const val BANDS = 6
    private const val PATCH_STEP = 64
    private const val N_BINS = 12
    private const val MIN_BLOCKS_PER_BIN = 10
    private const val PAIR_MAX = 6
    private val shifts = intArrayOf(-4, -2, 0, 2, 4)
    private val pilot = intArrayOf(6, 14, 22, 30)
    private val evidence = intArrayOf(8, 16, 24, 32)

    /** Exposed to regression fixtures independent of the Android GL runtime. */
    internal data class BlockEvidence(val phase: Int, val level: Double, val variance: Double)

    internal fun fitBlocks(blocks: List<BlockEvidence>, samplePairs: Int): Profile {
        val shot = FloatArray(4)
        val read = FloatArray(4)
        val count = IntArray(4)
        val occupied = IntArray(4)
        var supported = 0
        var fullFit = 0
        for (phase in 0..3) {
            val bins = Array(N_BINS) { ArrayList<Double>() }
            val levels = Array(N_BINS) { ArrayList<Double>() }
            for (b in blocks) {
                if (b.phase != phase || !b.level.isFinite() || !b.variance.isFinite() ||
                    b.variance <= 0.0 || b.level < -0.005 || b.level >= 0.965) continue
                val k = (max(0.0, b.level) * N_BINS).toInt().coerceIn(0, N_BINS - 1)
                bins[k].add(b.variance)
                levels[k].add(b.level)
            }
            val points = ArrayList<Pair<Double, Double>>()
            for (bin in 0 until N_BINS) {
                val vals = bins[bin]
                count[phase] += vals.size
                if (vals.size < MIN_BLOCKS_PER_BIN) continue
                vals.sort()
                // Lower-tail rejects motion/edge variance; compensate the low
                // chi-square quantile's finite-block downward bias conservatively.
                val index = (0.25 * (vals.size - 1)).toInt()
                val variance = vals[index] / 0.78
                if (!variance.isFinite() || variance <= 0.0) continue
                val l = levels[bin].sorted()[levels[bin].size / 2]
                points.add(Pair(max(l, 0.0), variance))
            }
            occupied[phase] = points.size
            if (count[phase] < 100 || points.isEmpty()) continue
            var slope = Double.NaN
            var intercept = Double.NaN
            if (points.size >= 3 && points.last().first - points.first().first >= 0.10) {
                val weights = points.map { 1.0 / max(1.0e-16, it.second * it.second) }
                val sum = weights.sum()
                val mx = points.indices.sumOf { points[it].first * weights[it] } / sum
                val my = points.indices.sumOf { points[it].second * weights[it] } / sum
                val denom = points.indices.sumOf { weights[it] * (points[it].first-mx) * (points[it].first-mx) }
                if (denom > 1.0e-15) {
                    slope = points.indices.sumOf { weights[it] * (points[it].first-mx) * (points[it].second-my) } / denom
                    intercept = my - slope * mx
                }
                if (!slope.isFinite() || !intercept.isFinite() || slope < 0.0 || intercept < 0.0) {
                    slope = Double.NaN
                    intercept = Double.NaN
                }
            }
            if (slope.isFinite() && intercept.isFinite() && slope < 0.15 && intercept < 0.025) {
                shot[phase] = slope.toFloat()
                read[phase] = max(intercept, 1.0e-10).toFloat()
                fullFit++
                supported++
            } else {
                // Not a pretend shot/read fit: a measured constant-variance
                // profile, marked as such and only used as a conservative proxy
                // in the supported brightness range. No Camera2 shape enters.
                val v = points.map { it.second }.sorted()
                read[phase] = v[v.size / 2].coerceIn(1.0e-10, 0.025).toFloat()
                shot[phase] = 0f
                supported++
            }
        }
        val mode = when {
            supported == 0 -> "BURST_UNSUPPORTED_MOTION_ONLY"
            supported == 4 && fullFit == 4 -> "BURST_ALL_PHASE_SHOT_READ"
            supported == 4 -> "BURST_ALL_PHASE_MEASURED_BINS"
            else -> "BURST_PARTIAL_MEASURED_BINS"
        }
        return Profile(shot, read, supported, count, mode, occupied, samplePairs)
    }

    fun estimate(
        normals: List<RawStackFrame>, width: Int, height: Int,
        phaseBlackByFrame: List<FloatArray>, phaseRangeByFrame: List<FloatArray>,
    ): Profile {
        fun unsupported(why: String) = Profile(FloatArray(4), FloatArray(4), 0,
            IntArray(4), "BURST_UNSUPPORTED_${why}", IntArray(4), 0)
        if (normals.size < 6 || (width and 1) != 0 || (height and 1) != 0 ||
            width < 192 || height < 384 ||
            phaseBlackByFrame.size != normals.size || phaseRangeByFrame.size != normals.size ||
            phaseBlackByFrame.any { it.size != 4 || it.any { v -> !v.isFinite() } } ||
            phaseRangeByFrame.any { it.size != 4 || it.any { v -> !v.isFinite() || v <= 0f } })
            return unsupported("GEOMETRY")
        val first = normals.first()
        if (normals.any { it.role != RawBurstFrameRole.NORMAL ||
            it.image.format != ImageFormat.RAW_SENSOR || it.image.width != width ||
            it.image.height != height || it.image.pixelStrideBytes != 2 ||
            it.image.rowStrideBytes < width*2 || it.physicalCameraId != first.physicalCameraId ||
            it.sensitivityIso != first.sensitivityIso || it.exposureTimeNs <= 0L ||
            abs(it.exposureTimeNs.toDouble()/first.exposureTimeNs.toDouble()-1.0)>0.012 })
            return unsupported("MIXED_FRAME")
        if (normals.any { it.rowFlickerHarmonic > 0 && it.rowFlickerStrength > 0.12f })
            return unsupported("ROW_FLICKER")
        val samples=ArrayList<BlockEvidence>()
        var acceptedPairs=0
        val pairStep=max(1,(normals.size - 1)/PAIR_MAX)
        val pairs=(0 until normals.size-1 step pairStep).take(PAIR_MAX)
        try {
            for (i in pairs) {
                val f0=normals[i]
                val f1=normals[i+1]
                var pairEvidence=0
                for (band in 0 until BANDS) {
                    val top=(((height-STRIP_HEIGHT)*(2*band+1)/(2*BANDS)) and -2)
                    val ref=readStrip(f0,width,top,STRIP_HEIGHT,phaseBlackByFrame[i],phaseRangeByFrame[i])
                    val nxt=readStrip(f1,width,top,STRIP_HEIGHT,phaseBlackByFrame[i+1],phaseRangeByFrame[i+1])
                    fun at(data:FloatArray,x:Int,y:Int,phase:Int):Double =
                        data[(y+(phase shr 1))*width+x+(phase and 1)].toDouble()
                    for (bx in 16 until width-50 step PATCH_STEP) {
                        // Candidate translation is common to all CFA phases;
                        // preserve 2x2 Bayer phase and test separate pixel sites.
                        var best=Double.POSITIVE_INFINITY
                        var bestDx=0;var bestDy=0
                        for (dy in shifts) for (dx in shifts) {
                            var loss=0.0
                            for (y in pilot) for (x in pilot) {
                                val r=bx+x
                                for (phase in 0..3) {
                                    val a=at(ref,r,y,phase)
                                    val b=at(nxt,r+dx,y+dy,phase)
                                    val e=abs(a-b)
                                    loss += min(e,0.2)
                                }
                            }
                            if (loss < best) { best=loss; bestDx=dx; bestDy=dy }
                        }
                        val averageMismatch=best/(pilot.size*pilot.size*4.0)
                        // Reject noninteger residual motion/scene changes rather
                        // than blur images to force a false sensor-noise fit.
                        if (averageMismatch>0.014) continue
                        for (phase in 0..3) {
                            val differences=DoubleArray(evidence.size*evidence.size)
                            var k=0;var levelSum=0.0;var clipped=false
                            for (y in evidence) for (x in evidence) {
                                val a=at(ref,bx+x,y,phase)
                                val b=at(nxt,bx+x+bestDx,y+bestDy,phase)
                                if (a > 0.965 || b > 0.965 || !a.isFinite() || !b.isFinite()) clipped=true
                                differences[k++]=a-b
                                levelSum+=0.5*(a+b)
                            }
                            if (clipped) continue
                            val mean=differences.average()
                            val variance=0.5*differences.sumOf { (it-mean)*(it-mean) } /(differences.size-1)
                            if (!variance.isFinite() || variance <= 0.0) continue
                            // Motion-induced RAW structure is spatially correlated.
                            // White sensor noise is not; compare disjoint evidence
                            // residuals, never the pilot sites used for alignment.
                            var horizontal=0.0; var vertical=0.0
                            for (yy in evidence.indices) for (xx in evidence.indices) {
                                val v=differences[yy*evidence.size+xx]-mean
                                if (xx+1<evidence.size) horizontal+=v*(differences[yy*evidence.size+xx+1]-mean)
                                if (yy+1<evidence.size) vertical+=v*(differences[(yy+1)*evidence.size+xx]-mean)
                            }
                            val norm=(2.0*variance)*(evidence.size*(evidence.size-1)).toDouble()
                            if (abs(horizontal/norm)>0.35 || abs(vertical/norm)>0.35) continue
                            val signal=levelSum/differences.size
                            samples.add(BlockEvidence(phase, signal, variance))
                            pairEvidence++
                        }
                    }
                }
                if (pairEvidence >= 64) acceptedPairs++
            }
        } catch (_: Exception) { return unsupported("RAW_UNAVAILABLE") }
        if (acceptedPairs<2) return unsupported("MOTION_INSUFFICIENT")
        return fitBlocks(samples,acceptedPairs)
    }

    private fun readStrip(
        frame: RawStackFrame, width:Int, top:Int, rows:Int, black:FloatArray, range:FloatArray,
    ):FloatArray {
        val image=frame.image
        val region=if (image.isFileBacked) image.readFileRegion(0,top,width,rows) else null
        try {
            val memory=(region?.buffer ?: image.planes.single().buffer).duplicate().order(ByteOrder.nativeOrder())
            val stride=region?.rowStride ?: image.rowStrideBytes
            val origin=if(region==null)top else 0
            require(memory.limit() >= (origin+rows-1)*stride+width*2)
            return FloatArray(width*rows) { index ->
                val y=index/width
                val x=index%width
                val phase=((top+y and 1) shl 1) + (x and 1)
                val sensor=memory.getShort((origin+y)*stride+x*2).toInt() and 65535
                (sensor.toFloat()-black[phase])/range[phase]
            }
        } finally { region?.close() }
    }
}
