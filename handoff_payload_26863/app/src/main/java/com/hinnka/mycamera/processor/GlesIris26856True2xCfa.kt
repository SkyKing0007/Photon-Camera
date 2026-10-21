package com.hinnka.mycamera.processor

/**
 * IRIS_26856_B_2X_PHYSICAL_CFA_SINGLE_OWNER
 *
 * A native 2x Bayer lattice reconstructed directly from independently aligned
 * NORMAL RAW observations. It never samples, rescales, or adopts 26850/Sabre
 * RGB or VGN chroma. The accepted source is the full immutable NORMAL burst,
 * existing per-frame alignment/covariance/rejection evidence, and frozen
 * sensor-neutral black/exposure normalization.
 *
 * This file defines the GPU reconstruction ABI only. In particular, a lone
 * unshifted frame is NOT permission to upsample: the resolve shader requires
 * multiple measurements and independent fractional flow phases per CFA site.
 * The producer must prove those conditions and install a tile-streamed AMaZE
 * consumer before enabling the 2x B/A+B capture route.
 */
internal object GlesIris26856True2xCfa {
    const val owner = "IRIS_26856_B_2X_PHYSICAL_CFA_SINGLE_OWNER"
    const val haloPixels = 32
    const val minimumNormalFrames = 2

    fun validate(rawWidth: Int, rawHeight: Int, pattern: Int,
                 normalFrames: Int, tileX: Int, tileY: Int,
                 tileWidth: Int, tileHeight: Int) {
        require(rawWidth >= 32 && rawHeight >= 32 && rawWidth % 2 == 0 && rawHeight % 2 == 0)
        require(rawWidth <= Int.MAX_VALUE / 2 && rawHeight <= Int.MAX_VALUE / 2)
        require(pattern in 0..3 && normalFrames >= minimumNormalFrames)
        require(tileX >= 0 && tileY >= 0 && tileWidth >= 32 && tileHeight >= 32)
        require((tileX or tileY or tileWidth or tileHeight) and 1 == 0)
        require(tileX.toLong() + tileWidth <= rawWidth.toLong() * 2L)
        require(tileY.toLong() + tileHeight <= rawHeight.toLong() * 2L)
    }

    /**
     * IRIS_26856_B_2X_RAWR_SEAM_SAFE_STREAMING_GEOMETRY
     *
     * The doubled CFA lattice is a *sensor mosaic*, not RGB. Run the existing
     * per-frame accumulate/resolve/pack shaders only over these bounded
     * expanded tiles, feed each packed region into the exact pinned RAWR
     * AMaZE host, and publish only the non-overlapping core rectangle.
     * A 32-output-pixel minimum apron is larger than the host's 16-pixel
     * AMaZE tiling margin. Extra source support includes measured frame flow.
     * All coordinates remain in the 2x mosaic's global (even) Bayer lattice.
     * No consumer may treat adjacent overlapping tiles as extra RAW frames.
     */
    data class StreamingTile(
        val outputLeft: Int, val outputTop: Int,
        val outputWidth: Int, val outputHeight: Int,
        val expandedLeft: Int, val expandedTop: Int,
        val expandedWidth: Int, val expandedHeight: Int,
        val cropLeft: Int, val cropTop: Int,
        val packedWidth: Int, val packedHeight: Int,
        val tileSlots: Int,
        val estimatedGpuBytes: Long,
    ) {
        init {
            require(outputLeft >= 0 && outputTop >= 0 && outputWidth >= 32 && outputHeight >= 32)
            require((outputLeft or outputTop or outputWidth or outputHeight or
                expandedLeft or expandedTop or expandedWidth or expandedHeight or
                cropLeft or cropTop) and 1 == 0) {
                "26856 2x streaming geometry cannot change Bayer phase at a seam"
            }
            require(cropLeft == outputLeft - expandedLeft && cropTop == outputTop - expandedTop)
            require(cropLeft >= 0 && cropTop >= 0)
            require(cropLeft + outputWidth <= expandedWidth && cropTop + outputHeight <= expandedHeight)
            require(packedWidth * 2L == expandedWidth.toLong() &&
                packedHeight * 2L == expandedHeight.toLong())
            require(tileSlots == 16 && estimatedGpuBytes > 0)
        }
    }

    private const val maximumCoreWidth = 512
    private const val maximumCoreHeight = 256
    private const val minimumCorePixels = 32
    // Conservative budget for B's temporary CFA, moments, and packed output
    // plus the 16 pinned RAWR 160x160 / 34-channel scratch slots. Excludes the
    // already-owned NORMAL frames and the independent JPEG output file.
    private const val maximumTemporaryGpuBytes = 96L * 1024 * 1024
    private const val bytesPerExpandedPixel = 66L // 26863 B packed noise attachment
    private const val rawrScratchBytes = 16L * 34 * 160 * 160 * 4

    private fun evenCeiling(v: Double): Int {
        require(v.isFinite() && v >= 0.0 && v < 1_000_000.0) {
            "26856 B measured flow cannot be represented by bounded CFA tiling"
        }
        return ((kotlin.math.ceil(v).toInt() + 1) and -2)
    }

    private fun coreExtent(remaining: Int, ceiling: Int): Int {
        require(remaining >= minimumCorePixels && (remaining and 1) == 0)
        var n = minOf(remaining, ceiling)
        val after = remaining - n
        if (after in 2 until minimumCorePixels) n -= minimumCorePixels - after
        require(n >= minimumCorePixels && (n and 1) == 0)
        return n
    }

    /**
     * An ordered lazy tile iterator. The consumer must release each tile's
     * GLES/Vulkan resources and fence before advancing to the next tile.
     * `maxFlowRawX/Y` are measured absolute motions over the admitted NORMAL
     * burst, not invented geometry or uncalibrated gyro displacements.
     */
    fun streamingTiles(
        rawWidth: Int, rawHeight: Int, bayerPattern: Int, normalFrames: Int,
        maxGlTexture: Int, maxFlowRawX: Float, maxFlowRawY: Float,
    ): Sequence<StreamingTile> {
        require(rawWidth in 32..(Int.MAX_VALUE / 2) &&
            rawHeight in 32..(Int.MAX_VALUE / 2)) {
            "26856 B doubled CFA geometry overflow"
        }
        validate(rawWidth, rawHeight, bayerPattern, normalFrames,
            0, 0, rawWidth * 2, rawHeight * 2)
        require(maxGlTexture >= 128)
        require(maxFlowRawX.isFinite() && maxFlowRawY.isFinite() &&
            maxFlowRawX >= 0f && maxFlowRawY >= 0f)
        // Account for RBF 3x3 same-phase taps and AMaZE's internal boundary.
        val haloX = haloPixels + evenCeiling(2.0 * (maxFlowRawX + 3.0))
        val haloY = haloPixels + evenCeiling(2.0 * (maxFlowRawY + 3.0))
        val width = rawWidth * 2
        val height = rawHeight * 2
        require(maxGlTexture > 2 * maxOf(haloX, haloY) + minimumCorePixels) {
            "26856 B unsupported GLES texture size / measured flow for seam-safe AMaZE"
        }
        val coreWidthLimit = minOf(maximumCoreWidth, (maxGlTexture - 2 * haloX) and -2)
        val coreHeightLimit = minOf(maximumCoreHeight, (maxGlTexture - 2 * haloY) and -2)
        require(coreWidthLimit >= minimumCorePixels &&
            coreHeightLimit >= minimumCorePixels)
        // No full-output image, accumulated 2x mosaic or RGB texture allocated.
        return sequence {
            var y = 0
            while (y < height) {
                val coreH = coreExtent(height - y, coreHeightLimit)
                var x = 0
                while (x < width) {
                    val coreW = coreExtent(width - x, coreWidthLimit)
                    val lx = maxOf(0, x - haloX)
                    val ty = maxOf(0, y - haloY)
                    val rx = minOf(width, x + coreW + haloX)
                    val by = minOf(height, y + coreH + haloY)
                    val expandedW = rx - lx
                    val expandedH = by - ty
                    val estimate = expandedW.toLong() * expandedH * bytesPerExpandedPixel + rawrScratchBytes
                    require(estimate <= maximumTemporaryGpuBytes) {
                        "26856 B 2x tile exceeds conservative temporary GPU memory budget"
                    }
                    yield(StreamingTile(x, y, coreW, coreH, lx, ty, expandedW, expandedH,
                        x - lx, y - ty, expandedW / 2, expandedH / 2, 16, estimate))
                    x += coreW
                }
                y += coreH
            }
        }
    }

    /**
     * A write-only weighted sample for ONE aligned RAW frame. Output is added
     * to RGBA16F by GL_ONE/GL_ONE, separately for each admitted NORMAL frame.
     * A phase occupancy image records independent subpixel flow bins.
     *
     * Every contributing RAW sample must be of the same physical CFA color
     * (including separate Gr/Gb) as the requested 2x Bayer site.
     */
    val accumulate = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRawRegion;
        uniform sampler2D uFlow;
        uniform sampler2D uCovarianceRegion;
        uniform sampler2D uRejectionRegion;
        uniform ivec2 uRawOrigin;
        uniform ivec2 uRawRegionSize;
        uniform ivec2 uRawFullSize;
        uniform ivec2 uCovarianceOrigin;
        uniform ivec2 uCovarianceRegionSize;
        uniform ivec2 uCovarianceFullSize;
        uniform ivec2 uRejectionOrigin;
        uniform ivec2 uRejectionRegionSize;
        uniform ivec2 uRejectionFullSize;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputFullSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uPhaseGains;
        uniform vec4 uPhaseBlackTerms;
        uniform vec4 uPhaseNoiseShot26863;
        uniform vec4 uPhaseNoiseRead26863;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        uniform float uRawClipThreshold;
        uniform int uUseFrameWeight;
        // Inherit 26720's evidence-only row-flicker reliability weighting.
        // No new capture timing or row-gain correction is introduced.
        uniform int uRowFlickerEnabled;
        uniform int uRowFlickerHarmonic;
        uniform vec2 uRowFlickerAB;
        uniform float uRowFlickerStrength;
        uniform int uCfaPattern;
        layout(location=0) out vec4 oSignalWeight;
        layout(location=1) out vec4 oPhaseBins;
        // Distinguish a real 2D fractional motion spread from bin-edge noise.
        layout(location=2) out vec4 oPhaseCircularMoments;

        // Canonical R/G1/G2/B, never merged green or Bayer-agnostic RGB.
        int canonicalAtPhase(int physicalPhase) {
            if (uCfaPattern == 0) return physicalPhase;
            if (uCfaPattern == 1) return physicalPhase == 0 ? 1 :
                (physicalPhase == 1 ? 0 : (physicalPhase == 2 ? 3 : 2));
            if (uCfaPattern == 2) return physicalPhase == 0 ? 2 :
                (physicalPhase == 1 ? 3 : (physicalPhase == 2 ? 0 : 1));
            return 3 - physicalPhase;
        }
        int phaseForCanonical(int channel) {
            for (int p=0;p<4;++p) if (canonicalAtPhase(p)==channel) return p;
            return -1;
        }
        float channelAt(vec4 v,int channel) {
            return channel==0?v.x:channel==1?v.y:channel==2?v.z:v.w;
        }
        bool rawInside(ivec2 q) {
            return all(greaterThanEqual(q,ivec2(0))) && all(lessThan(uvec2(q),uvec2(uRawFullSize)));
        }
        float rawAt(ivec2 q) {
            ivec2 local=q-uRawOrigin;
            return float(texelFetch(uRawRegion,local,0).r);
        }
        vec3 covarianceAt(vec2 uv) {
            vec2 pixel=clamp(uv*vec2(uCovarianceFullSize)-0.5,
                vec2(0.0),vec2(uCovarianceFullSize-ivec2(1)));
            vec2 l=clamp(pixel-vec2(uCovarianceOrigin),vec2(0.0),
                vec2(uCovarianceRegionSize-ivec2(1)));
            ivec2 a=ivec2(floor(l));
            ivec2 b=min(a+ivec2(1),uCovarianceRegionSize-ivec2(1));
            vec2 f=fract(l);
            vec3 v=mix(mix(texelFetch(uCovarianceRegion,a,0).rgb,
                texelFetch(uCovarianceRegion,ivec2(b.x,a.y),0).rgb,f.x),
                mix(texelFetch(uCovarianceRegion,ivec2(a.x,b.y),0).rgb,
                texelFetch(uCovarianceRegion,b,0).rgb,f.x),f.y);
            return vec3(v.x*uCovRangeRg.y+uCovRangeRg.x,
                v.y*uCovRangeRg.w+uCovRangeRg.z,
                v.z*uCovRangeB.y+uCovRangeB.x);
        }
        float rowReliability(float rowUv) {
            if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 ||
                uRowFlickerStrength <= 0.0) return 1.0;
            float phase = 6.283185307179586 * float(uRowFlickerHarmonic) *
                clamp(rowUv, 0.0, 1.0);
            float modulation = dot(uRowFlickerAB, vec2(cos(phase), sin(phase)));
            float amplitude = length(uRowFlickerAB);
            float dark = max(-modulation, 0.0);
            float band = smoothstep(0.010, max(0.030, amplitude * 0.90), dark);
            return mix(1.0, 0.08, clamp(band *
                clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));
        }
        float rejectionAt(vec2 uv) {
            if(uUseFrameWeight==0) return 1.0;
            vec2 p=clamp(uv*vec2(uRejectionFullSize)-0.5,
                vec2(0.0),vec2(uRejectionFullSize-ivec2(1)));
            vec2 local=clamp(p-vec2(uRejectionOrigin),vec2(0.0),
                vec2(uRejectionRegionSize-ivec2(1)));
            ivec2 a=ivec2(floor(local));
            ivec2 b=min(a+ivec2(1),uRejectionRegionSize-ivec2(1));
            vec2 f=fract(local);
            return mix(mix(texelFetch(uRejectionRegion,a,0).r,
                texelFetch(uRejectionRegion,ivec2(b.x,a.y),0).r,f.x),
                mix(texelFetch(uRejectionRegion,ivec2(a.x,b.y),0).r,
                texelFetch(uRejectionRegion,b,0).r,f.x),f.y);
        }
        void main() {
            ivec2 outP=uOutputOrigin+ivec2(gl_FragCoord.xy);
            vec2 referenceUv=(vec2(outP)+0.5)/vec2(uOutputFullSize);
            vec4 flow=texture(uFlow,referenceUv*uFlowScaleOffset.xy+uFlowScaleOffset.zw);
            vec2 sampleUv=referenceUv+flow.xy;
            // The support ROI and sensor border are deliberate hard rejection,
            // not an invalid-border clamp that fabricates detail.
            if(any(lessThan(sampleUv,vec2(0.0))) ||
               any(greaterThanEqual(sampleUv,vec2(1.0)))) {
                oSignalWeight=vec4(0.0);oPhaseBins=vec4(0.0);oPhaseCircularMoments=vec4(0.0);return;
            }
            float admission=rejectionAt(referenceUv)*rowReliability(sampleUv.y);
            if(admission<=0.08) {
                oSignalWeight=vec4(0.0);oPhaseBins=vec4(0.0);oPhaseCircularMoments=vec4(0.0);return;
            }
            int targetCanonical=canonicalAtPhase((outP.x&1)+2*(outP.y&1));
            int sensorPhase=phaseForCanonical(targetCanonical);
            ivec2 rawParity=ivec2(sensorPhase&1,(sensorPhase>>1)&1);
            vec2 sensor=sampleUv*vec2(uRawFullSize);
            ivec2 base=(ivec2(floor(sensor)) & ~ivec2(1))+rawParity;
            vec3 cov=covarianceAt(sampleUv);
            float gain=channelAt(uPhaseGains,sensorPhase);
            float black=channelAt(uPhaseBlackTerms,sensorPhase);
            float numerator=0.0,weight=0.0,weightSquared=0.0;
            for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx) {
                ivec2 p=base+ivec2(dx*2,dy*2);
                ivec2 local=p-uRawOrigin;
                if(!rawInside(p)||any(lessThan(local,ivec2(0)))||
                   any(greaterThanEqual(local,uRawRegionSize))) continue;
                float raw=rawAt(p);
                if(raw>=uRawClipThreshold) continue;
                vec2 d=(vec2(p)+0.5)-sensor;
                float dist=cov.x*d.x*d.x+cov.y*d.y*d.y+2.0*cov.z*d.x*d.y;
                float k=exp2(-0.5*max(dist,0.0));
                numerator+=k*max(raw*gain+black,0.0);
                weight+=k;
                weightSquared+=k*k;
            }
            float vote=weight>1e-5 ? admission : 0.0;
            float normalized=weight>1e-5?numerator/weight:0.0;
            // Pixel value is one observation per frame, never nine independent
            // temporal measurements from the same RAW frame.
            // A frame's nine local same-CFA samples are not nine temporal frames.
            // Preserve their spatial kernel-square variance within one vote.
            float perFrameVariance=(max(uPhaseNoiseShot26863[targetCanonical],0.0)*
                max(normalized,0.0)+max(uPhaseNoiseRead26863[targetCanonical],0.0)) *
                (weight>1.0e-5?weightSquared/(weight*weight):0.0);
            oSignalWeight=vec4(normalized*vote,vote,vote*vote,256.0*vote*vote*perFrameVariance);
            vec2 phase=fract(flow.xy*vec2(uRawFullSize));
            int bin=(phase.x>=0.5?1:0)+(phase.y>=0.5?2:0);
            oPhaseBins=bin==0?vec4(vote,0,0,0):
                bin==1?vec4(0,vote,0,0):
                bin==2?vec4(0,0,vote,0):vec4(0,0,0,vote);
            const float tau=6.28318530718;
            oPhaseCircularMoments=vote*vec4(cos(tau*phase.x),sin(tau*phase.x),
                cos(tau*phase.y),sin(tau*phase.y));
        }
    """.trimIndent()

    /** B's Bayer site resolver, with no reference-image or Sabre-RGB fallback. */
    val resolve = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAccumulated;
        uniform sampler2D uPhaseBins;
        uniform sampler2D uPhaseMoments;
        uniform float uMinimumWeight;
        layout(location=0) out vec4 oCfaSupport;
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy);
            vec4 a=texelFetch(uAccumulated,p,0);
            vec4 bins=texelFetch(uPhaseBins,p,0);
            float effectiveN=a.g*a.g/max(a.b,1e-6);
            int distinct=int(bins.r>0.10)+int(bins.g>0.10)+
                         int(bins.b>0.10)+int(bins.a>0.10);
            vec4 moment=texelFetch(uPhaseMoments,p,0);
            float invSupport=1.0/max(a.g,1e-6);
            // Circular variance handles 0/1 phase wrap, unlike linear moments.
            // A barely crossed 0.5 phase bin is NOT credible independent detail.
            // Real B 2x requires meaningful fractional diversity in BOTH axes.
            float varianceX=clamp(1.0-length(moment.xy)*invSupport,0.0,1.0);
            float varianceY=clamp(1.0-length(moment.zw)*invSupport,0.0,1.0);
            bool proven=a.g>=uMinimumWeight && effectiveN>=1.90 &&
                distinct>=2 && varianceX>=0.14 && varianceY>=0.14;
            // Output .x is a sensor-neutral CFA site. .y is weighted support,
            // .z effective independent frame count, .w a strict validity bit.
            oCfaSupport=proven?vec4(a.r/max(a.g,1e-6),a.g,effectiveN,1.0):vec4(0.0);
        }
    """.trimIndent()

    /** Pack the resolved doubled Bayer lattice for pinned RAWR PackedCfaImageView.
     * Any unsupported quadrant invalidates the entire cell; caller must tally
     * invalid cells and fail before invoking AMaZE. */
    val pack = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uResolved;
        uniform sampler2D uAccumulatedNoise26863;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oPackedCanonical;
        layout(location=1) out vec4 oSupport;
        layout(location=2) out vec4 oBNoiseVariance26863;
        float siteVariance(ivec2 q){
            vec4 a=texelFetch(uAccumulatedNoise26863,q,0);
            return a.g>1.0e-6?(max(a.a,0.0)/256.0)/max(a.g*a.g,1.0e-12):0.0;
        }
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy)*2;
            vec4 tl=texelFetch(uResolved,p,0);
            vec4 tr=texelFetch(uResolved,p+ivec2(1,0),0);
            vec4 bl=texelFetch(uResolved,p+ivec2(0,1),0);
            vec4 br=texelFetch(uResolved,p+ivec2(1,1),0);
            vec4 physical=vec4(tl.r,tr.r,bl.r,br.r);
            vec4 canonical=physical;
            if(uBayerPattern==1) canonical=physical.yxwz;
            else if(uBayerPattern==2) canonical=physical.zwxy;
            else if(uBayerPattern==3) canonical=physical.wzyx;
            float valid=tl.a*tr.a*bl.a*br.a;
            oPackedCanonical=valid>0.5?canonical:vec4(0.0);
            oSupport=vec4(min(min(tl.b,tr.b),min(bl.b,br.b)),valid,
                          min(min(tl.z,tr.z),min(bl.z,br.z)),0.0);
            vec4 vPhysical=vec4(siteVariance(p),siteVariance(p+ivec2(1,0)),
                siteVariance(p+ivec2(0,1)),siteVariance(p+ivec2(1,1)));
            vec4 vCanonical=vPhysical;
            if(uBayerPattern==1)vCanonical=vPhysical.yxwz;
            else if(uBayerPattern==2)vCanonical=vPhysical.zwxy;
            else if(uBayerPattern==3)vCanonical=vPhysical.wzyx;
            oBNoiseVariance26863=valid>0.5?vCanonical:vec4(0.0);
        }
    """.trimIndent()
}
