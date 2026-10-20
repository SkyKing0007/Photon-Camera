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
    private val shifts = intArrayOf(-4, -2, 0, 2, 4)
    private val pilot = intArrayOf(6, 14, 22, 30)
    private val evidence = intArrayOf(8, 16, 24, 32)

    /** Exposed to regression fixtures independent of the Android GL runtime. */
    internal data class BlockEvidence(
        val phase: Int, val level: Double, val variance: Double,
        val temporal: Boolean = true,
    )

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
            // Use independent temporal evidence when identifiable. If one phase
            // cannot be measured temporally, use only that phase's RAW-derived
            // spatial bound (never substitute another phase or Camera2 profile).
            val temporalBlocks = blocks.filter { it.phase == phase && it.temporal }
            val temporalBinCount = IntArray(N_BINS)
            for (b in temporalBlocks) if (b.level.isFinite() && b.variance.isFinite() &&
                b.variance > 0.0 && b.level in -0.005..0.965) {
                temporalBinCount[(max(0.0, b.level) * N_BINS).toInt().coerceIn(0, N_BINS-1)]++
            }
            val usableTemporal = temporalBinCount.sum() >= 100 &&
                temporalBinCount.any { it >= MIN_BLOCKS_PER_BIN }
            val phaseBlocks = if (usableTemporal) temporalBlocks else
                blocks.filter { it.phase == phase && !it.temporal }
            for (b in phaseBlocks) {
                if (!b.level.isFinite() || !b.variance.isFinite() ||
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
            if (phaseBlocks.firstOrNull()?.temporal == true &&
                points.size >= 3 && points.last().first - points.first().first >= 0.10) {
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
            supported == 4 && blocks.any { !it.temporal } -> "BURST_ALL_PHASE_RAW_BOUNDED"
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
        // IRIS_26862_B_BURST_NOISE_INDEPENDENT_OF_CAPTURE_POLICY:
        // Capture owns flicker/EV/ISO admission. The estimator consumes the
        // accepted NORMAL RAW samples; none of those metadata values veto a
        // burst. Only unreadable/incompatible RAW byte geometry is fatal.
        if (normals.size < 2 || (width and 1) != 0 || (height and 1) != 0 ||
            width < 192 || height < 384 ||
            phaseBlackByFrame.size != normals.size || phaseRangeByFrame.size != normals.size ||
            phaseBlackByFrame.any { it.size != 4 || it.any { v -> !v.isFinite() } } ||
            phaseRangeByFrame.any { it.size != 4 || it.any { v -> !v.isFinite() || v <= 0f } })
            return unsupported("GEOMETRY")
        if (normals.any { it.role != RawBurstFrameRole.NORMAL ||
            it.image.format != ImageFormat.RAW_SENSOR || it.image.width != width ||
            it.image.height != height || it.image.pixelStrideBytes != 2 ||
            it.image.rowStrideBytes < width*2 }) return unsupported("RAW_GEOMETRY")
        val order = normals.indices.sortedWith(compareBy({ normals[it].sensorTimestampNs }, { it }))
        // Actual sensor exposure metadata is a radiometric conversion, not an
        // admission gate; non-positive/absent metadata retains RAW evidence.
        fun product(index: Int): Double {
            val f = normals[index]
            return if (f.exposureTimeNs > 0L && f.sensitivityIso > 0)
                f.exposureTimeNs.toDouble() * f.sensitivityIso.toDouble() else Double.NaN
        }
        val referenceProduct = product(0)
        fun gain(index: Int): Double {
            val v = product(index)
            val g = if (referenceProduct.isFinite() && v.isFinite() && v > 0.0)
                referenceProduct / v else 1.0
            return if (g.isFinite() && g > 0.0) g else 1.0
        }
        val samples=ArrayList<BlockEvidence>()
        var acceptedPairs=0
        // Chronological nonoverlapping pairs limit CPU time and cover every
        // accepted NORMAL. An odd final frame pairs with its nearest neighbor.
        val pairs = order.chunked(2).mapIndexed { index, group ->
            if (group.size == 2) Pair(group[0],group[1]) else
                Pair(order[max(0,index*2-1)],group[0])
        }
        try {
            for ((i, j) in pairs) {
                val f0=normals[i]
                val f1=normals[j]
                // Cross-physical-camera differences cannot estimate a single
                // sensor's noise. They do not veto other compatible pairs.
                if (f0.physicalCameraId != f1.physicalCameraId) continue
                val gain0 = gain(i)
                val gain1 = gain(j)
                var pairEvidence=0
                for (band in 0 until BANDS) {
                    val top=(((height-STRIP_HEIGHT)*(2*band+1)/(2*BANDS)) and -2)
                    val ref=readStrip(f0,width,top,STRIP_HEIGHT,phaseBlackByFrame[i],phaseRangeByFrame[i])
                    val nxt=readStrip(f1,width,top,STRIP_HEIGHT,phaseBlackByFrame[j],phaseRangeByFrame[j])
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
                                val a=at(ref,bx+x,y,phase)*gain0
                                val b=at(nxt,bx+x+bestDx,y+bestDy,phase)*gain1
                                if (a > 0.965 || b > 0.965 || !a.isFinite() || !b.isFinite()) clipped=true
                                differences[k++]=a-b
                                levelSum+=0.5*(a+b)
                            }
                            if (clipped) continue
                            // Mains row modulation is structured illumination,
                            // not sensor noise. Remove a separate residual mean
                            // per observed RAW row (four independent rows).
                            // The remaining 12 degrees of freedom prevent the
                            // detrend from spuriously lowering shot/read noise.
                            val side=evidence.size
                            val rowMeans=DoubleArray(side) { row ->
                                (0 until side).sumOf { col -> differences[row*side+col] } / side
                            }
                            val residuals=DoubleArray(differences.size) { index ->
                                differences[index]-rowMeans[index/side]
                            }
                            val variance=0.5*residuals.sumOf { it*it } /
                                (differences.size-side).toDouble()
                            if (!variance.isFinite() || variance <= 0.0) continue
                            // Motion-induced RAW structure is spatially correlated.
                            // White sensor noise is not; compare disjoint evidence
                            // residuals, never the pilot sites used for alignment.
                            var horizontal=0.0; var vertical=0.0
                            for (yy in evidence.indices) for (xx in evidence.indices) {
                                val v=residuals[yy*evidence.size+xx]
                                if (xx+1<evidence.size) horizontal+=v*residuals[yy*evidence.size+xx+1]
                                if (yy+1<evidence.size) vertical+=v*residuals[(yy+1)*evidence.size+xx]
                            }
                            val norm=(2.0*variance)*(evidence.size*(evidence.size-1)).toDouble()
                            if (abs(horizontal/norm)>0.50 || abs(vertical/norm)>0.50) continue
                            val signal=levelSum/differences.size
                            if (!signal.isFinite()) continue
                            samples.add(BlockEvidence(phase, signal, variance))
                            pairEvidence++
                        }
                    }
                }
                if (pairEvidence >= 64) acceptedPairs++
            }
        } catch (_: Exception) { return unsupported("RAW_UNAVAILABLE") }
        val fitted = fitBlocks(samples,acceptedPairs)
        if (fitted.measuredPhases == 4) return fitted
        // When temporal alignment/flicker removes enough independent samples,
        // measure conservative spatial same-CFA second differences directly
        // from the same accepted RAW burst. This is *not* a shot/read fit:
        // structural texture can only increase the variance floor. The spatial
        // data never enter another phase's model nor a Camera2 escape hatch.
        try {
            val needed = (0..3).filter { fitted.acceptedSites[it] < 100 || fitted.signalBins[it] == 0 }
            for (i in order) {
                for (band in 0 until BANDS) {
                    val top=(((height-STRIP_HEIGHT)*(2*band+1)/(2*BANDS)) and -2)
                    val raw=readStrip(normals[i],width,top,STRIP_HEIGHT,
                        phaseBlackByFrame[i],phaseRangeByFrame[i])
                    val g=gain(i)
                    for (bx in 16 until width-50 step PATCH_STEP) {
                        for (phase in needed) {
                            val q=DoubleArray(16)
                            var level=0.0
                            for (y in 0..3) for (x in 0..3) {
                                val cy=8+y*8+(phase shr 1)
                                val cx=bx+12+x*8+(phase and 1)
                                val at=raw[cy*width+cx].toDouble()*g
                                val left=raw[cy*width+cx-2].toDouble()*g
                                val right=raw[cy*width+cx+2].toDouble()*g
                                q[y*4+x]=at-0.5*(left+right)
                                level+=at
                            }
                            val mean=q.average()
                            val variance=q.sumOf { (it-mean)*(it-mean) } /
                                (15.0*1.5)
                            if (variance.isFinite() && variance > 0.0 &&
                                level/16.0 in 0.0..0.965) {
                                samples.add(BlockEvidence(phase,level/16.0,variance,false))
                            }
                        }
                    }
                }
            }
        } catch (_: Exception) { return unsupported("RAW_UNAVAILABLE") }
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
