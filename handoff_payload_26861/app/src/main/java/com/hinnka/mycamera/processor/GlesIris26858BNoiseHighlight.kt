package com.hinnka.mycamera.processor

/**
 * IRIS_26858_B_INDEPENDENT_COLOR_NOISE_AND_SENSOR_CLIP_PROVENANCE.
 * Only the AMaZE B stacker links these shaders. A's 26850 reconstruction, VGN,
 * CFA denoising, and Camera2/RAW-DNG output are never consumers of this object.
 * Clip evidence is collected on original pre-LSC/pre-WB unsigned sensor RAWs,
 * not from temporary WB camera RGB, gamma, AMaZE or an SDR RGB heuristic.
 */
internal object GlesIris26858BNoiseHighlight {
    /* IRIS_26861_B_MOTION_ONLY_WHEN_UNMEASURED.
     * This is not a noise-profile substitute and does not perform denoising:
     * estimate exposure-normalized alignment agreement in B's own RAW guide,
     * bound every companion's share and reject motion borders. */
    val bMotionOnlyWeight26861 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uReferenceGuide;
        uniform sampler2D uCurrentGuide;
        uniform sampler2D uFlow;
        uniform ivec2 uCoverageSize;
        uniform vec4 uFlowScaleOffset;
        layout(location=0) out float oConfidence;
        void main(){
            vec2 uv=gl_FragCoord.xy/vec2(uCoverageSize);
            vec4 f=texture(uFlow,uv*uFlowScaleOffset.xy+uFlowScaleOffset.zw);
            vec2 target=uv+f.xy;
            float inBounds=float(all(greaterThan(target,vec2(0.01))) &&
                all(lessThan(target,vec2(0.99))));
            vec3 a=abs(texture(uReferenceGuide,uv).rgb);
            vec3 b=abs(texture(uCurrentGuide,clamp(target,vec2(0.0),vec2(1.0))).rgb);
            float ref=dot(a,vec3(0.3333333333));
            float cur=dot(b,vec3(0.3333333333));
            float residual=abs(ref-cur)/max(max(ref,cur),0.06);
            float photometric=1.0-smoothstep(0.065,0.19,residual);
            float flowGuard=1.0-smoothstep(0.028,0.11,max(f.z,0.0));
            oConfidence=0.20*photometric*flowGuard*inBounds;
        }
    """.trimIndent()

    /* IRIS_26861_B_WEIGHTED_CFA_IDENTITY. No spatial denoising is allowed
     * between the fully admitted temporal sensor CFA and AMaZE. */
    val bWeightedCfaIdentity26861 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uWeightedPhases;
        uniform ivec2 uSize;
        layout(location=0) out vec4 oWeighted;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            oWeighted=texelFetch(uWeightedPhases,p,0);
        }
    """.trimIndent()



    /** IRIS_26859_B_EXACT_FRACTIONAL_CFA_CLIP_FOOTPRINT
     * The clip carrier follows the 26858 normalized/guarded RAW phase samples:
     * exact lattice hit => one site, fractional flow => all four same-phase
     * corners. Any clipped contributor is flagged, as temporal CFA's minimum
     * headroom does, BEFORE LSC/temporary WB and before HDR/LONG color routing.
     */
    val bClipAccumulate = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform sampler2D uFlow;
        uniform sampler2D uReject;
        uniform sampler2D uVerifiedHotPixelMask26855;
        uniform int uVerifiedHotPixelMapEnabled26855;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uRawSize;
        uniform ivec2 uCellSize;
        uniform vec4 uFlowBorder;
        uniform vec4 uPhaseGains;
        uniform vec4 uPhaseBlackTerms;
        uniform vec4 uPhaseNoiseShot26855;
        uniform vec4 uPhaseNoiseRead26855;
        uniform float uSourceWhiteNormalized;
        uniform int uHasReject;
        uniform int uFlickerHarmonic;
        uniform vec2 uFlickerAB;
        uniform float uFlickerStrength;
        layout(location=0) out vec4 oClipVotes;
        vec2 mirrorUv(vec2 a){
            if(a.x<=uFlowBorder.x)a.x=2.0*uFlowBorder.x-a.x;
            if(a.y<=uFlowBorder.y)a.y=2.0*uFlowBorder.y-a.y;
            if(a.x>uFlowBorder.z)a.x=2.0*uFlowBorder.z-a.x;
            if(a.y>uFlowBorder.w)a.y=2.0*uFlowBorder.w-a.y;
            return a;
        }
        float flicker(float y){
            if(uFlickerHarmonic<=0||uFlickerStrength<=0.0)return 1.0;
            float a=6.28318530718*float(uFlickerHarmonic)*clamp(y,0.0,1.0);
            float v=uFlickerAB.x*cos(a)+uFlickerAB.y*sin(a);
            float dark=smoothstep(0.010,max(0.030,length(uFlickerAB)*0.90),max(-v,0.0));
            return mix(1.0,0.08,clamp(dark*uFlickerStrength,0.0,1.0));
        }
        float frameWeight(ivec2 p){
            if(uHasReject==0)return 1.0;
            vec2 inv=1.0/vec2(uRawSize);
            float r=1.0;
            for(int y=0;y<2;++y)for(int x=0;x<2;++x){
                r=min(r,texture(uReject,(vec2(p+ivec2(x,y))+vec2(0.5))*inv).r);
            }
            return r;
        }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) + (p.x & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, phase >> 1); }
        ivec2 clampPhaseLattice(ivec2 q, int phase) {
            ivec2 off = phaseOffset(phase);
            ivec2 maximum = max((uRawSize - ivec2(1) - off) / 2, ivec2(0));
            return clamp(q, ivec2(0), maximum);
        }
        ivec2 pixelForPhaseLattice(ivec2 q, int phase) {
            return clampPhaseLattice(q, phase) * 2 + phaseOffset(phase);
        }
        float normalizedRaw(ivec2 p) {
            p = clamp(p, ivec2(0), uRawSize - ivec2(1));
            int phase = phaseAt(p);
            return float(texelFetch(uRaw, p, 0).r) * uPhaseGains[phase] + uPhaseBlackTerms[phase];
        }
        /* IRIS_26855_RAW_CFA_IMPULSE_REPAIR_OWNER
         * Repair only an extreme, isolated positive SAME-PHASE raw spike before it
         * reaches the temporal CFA sum. This is not a broad spatial denoiser.
         * The raw pixel is never replaced merely for chromatic disagreement.
         * All 14 frames remain eligible; existing Sabre shared-motion admission
         * and all other CFA/SHORT/LONG/DNG ownership remain unchanged. */
        float guardedRaw26855(ivec2 p) {
            float center = normalizedRaw(p);
            if (p.x < 2 || p.y < 2 || p.x >= uRawSize.x-2 || p.y >= uRawSize.y-2)
                return center;
            int phase = phaseAt(p);
            /* Verified sparse Camera2 defects are corrected independent of
             * the scene's noise threshold, without filtering adjacent texture.
             * Coordinates originate in the sensor pixel-array domain and are
             * used only after exact RAW geometry translation is established. */
            bool sensorDefect = uVerifiedHotPixelMapEnabled26855 != 0 &&
                texelFetch(uVerifiedHotPixelMask26855,p,0).r > 0.5;
            float a = normalizedRaw(p + ivec2(-2,0));
            float b = normalizedRaw(p + ivec2( 2,0));
            float c = normalizedRaw(p + ivec2(0,-2));
            float d = normalizedRaw(p + ivec2(0, 2));
            if (sensorDefect) {
                float lowAB=min(a,b), highAB=max(a,b);
                float lowCD=min(c,d), highCD=max(c,d);
                return 0.5*(max(lowAB,lowCD)+min(highAB,highCD));
            }
            float cardinalMax = max(max(a,b),max(c,d));
            float cardinalMin = min(min(a,b),min(c,d));
            float meanCardinal = 0.25*(a+b+c+d);
            float shot = max(uPhaseNoiseShot26855[phase],0.0);
            float read = max(uPhaseNoiseRead26855[phase],0.0);
            float sigma = sqrt(max(shot*max(meanCardinal,0.0)+read,1.0e-9));
            /* An ordinary fabric strand, colored stitch, or subpixel detail must
             * never trigger the sparse impulse owner from a single noisy neighbor. */
            if (center <= cardinalMax + max(9.0*sigma,0.055) ||
                cardinalMax-cardinalMin > max(3.5*sigma,0.025)) return center;
            float e = normalizedRaw(p + ivec2(-2,-2));
            float f = normalizedRaw(p + ivec2( 2,-2));
            float g = normalizedRaw(p + ivec2(-2, 2));
            float h = normalizedRaw(p + ivec2( 2, 2));
            float diagonalMax = max(max(e,f),max(g,h));
            float diagonalMin = min(min(e,f),min(g,h));
            float ringMax = max(cardinalMax,diagonalMax);
            float ringMin = min(cardinalMin,diagonalMin);
            if (ringMax-ringMin > max(4.0*sigma,0.030) ||
                center <= ringMax + max(9.0*sigma,0.055)) return center;
            /* No hue/saturation/green substitution: return only same-phase RAW
             * evidence when eight local witnesses establish a single-pixel spike. */
            return 0.125*(a+b+c+d+e+f+g+h);
        }

        float actualClip(ivec2 p){
            float v=guardedRaw26855(p);
            float end=max(uSourceWhiteNormalized,1.0e-5);
            float start=end*0.9925;
            return smoothstep(start,max(start+1.0e-5,end),v);
        }
        float sameFootprintClip(vec2 sourceCenter,int phase){
            ivec2 off=phaseOffset(phase);
            vec2 lattice=0.5*(sourceCenter-(vec2(off)+vec2(0.5)));
            ivec2 nearest=ivec2(floor(lattice+vec2(0.5)));
            if(max(abs(lattice.x-float(nearest.x)),abs(lattice.y-float(nearest.y)))<1.0e-5){
                return actualClip(pixelForPhaseLattice(nearest,phase));
            }
            ivec2 base=ivec2(floor(lattice));
            float clipped=0.0;
            for(int y=0;y<=1;++y)for(int x=0;x<=1;++x){
                clipped=max(clipped,actualClip(pixelForPhaseLattice(base+ivec2(x,y),phase)));
            }
            return clipped;
        }
        void main(){
            ivec2 q=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uCellSize-ivec2(1));
            ivec2 quad=q*2;
            vec2 raw=vec2(uRawSize);
            vec2 ref=(vec2(quad)+vec2(1.0))/raw;
            vec2 flowUv=ref*uFlowScaleOffset.xy+uFlowScaleOffset.zw;
            vec2 src=mirrorUv(ref+texture(uFlow,flowUv).xy);
            vec2 d=(src-ref)*raw;
            float w=frameWeight(quad)*flicker(src.y);
            vec4 clipped=vec4(0.0);
            for(int phase=0;phase<4;++phase){
                ivec2 off=phaseOffset(phase);
                vec2 c=vec2(quad+off)+vec2(0.5)+d;
                clipped[phase]=sameFootprintClip(c,phase)*w;
            }
            oClipVotes=clipped;
        }
    """.trimIndent()

    val bClipNormalize = """
        #version 300 es
        precision highp float;
        uniform sampler2D uVotes;
        uniform sampler2D uTotal;
        uniform ivec2 uSize;
        layout(location=0) out vec4 oClippedFraction;
        void main(){
            ivec2 q=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            float sum=texelFetch(uTotal,q,0).y;
            // No admission => no trustworthy clipping provenance, not "fully clipped".
            oClippedFraction=sum>1.0e-6 ?
                clamp(texelFetch(uVotes,q,0)/sum,0.0,1.0) : vec4(0.0);
        }
    """.trimIndent()

    /** Camera RGB remains SENSOR-NEUTRAL here, no WB or CCM. RGB luma/detail
     * stays bit-identical by preserving green and the green-scaled chroma sum. */


    /** IRIS_26859_B_SENSOR_PROVEN_SMOOTH_WHITE
     * Temporary post-WB camera-linear RGB. Sensor-proven clipping only;
     * no nearby hue guides or color donation. Unclipped RGB is bit-exact.
     * The shared WB-dependent channel limit is only a brightness floor for
     * UNKNOWN clipped radiance, NEVER a clamp on reliable real RGB or HDR.
     */
    val bHighlightRecover = """
        #version 300 es
        precision highp float;
        uniform sampler2D uWbRgb;
        uniform sampler2D uClip;
        uniform ivec2 uSize;
        uniform ivec2 uCellSize;
        uniform int uBayerPattern;
        uniform ivec2 uOrigin;
        uniform int uExpandedScale;
        uniform vec3 uAmazeWb;
        layout(location=0) out vec4 oRgb;
        vec3 clipRgb(ivec2 p){
            ivec2 q=clamp((uOrigin+p)/(2*uExpandedScale),ivec2(0),uCellSize-ivec2(1));
            vec4 ph=texelFetch(uClip,q,0);
            if(uBayerPattern==0)return vec3(ph.r,max(ph.g,ph.b),ph.a);
            if(uBayerPattern==1)return vec3(ph.g,max(ph.r,ph.a),ph.b);
            if(uBayerPattern==2)return vec3(ph.b,max(ph.r,ph.a),ph.g);
            return vec3(ph.a,max(ph.g,ph.b),ph.r);
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 original=texelFetch(uWbRgb,p,0);
            vec3 clip=clipRgb(p);
            float unreliable=clamp(max(max(clip.r,clip.g),clip.b),0.0,1.0);
            if(unreliable<=0.0){oRgb=original;return;}
            // Smooth endpoints guarantee no abrupt nonzero correction just as
            // a channel enters the physically evidenced near-white interval.
            float fade=smoothstep(0.0,1.0,unreliable);
            vec3 rgb=max(original.rgb,vec3(0.0));
            float sharedSafeWhite=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));
            // Never reduce a sensor-reconstructed channel, clip HDR >1, or
            // compress the highlight radiance into an artificial grey shoulder.
            float neutral=max(max(max(rgb.r,rgb.g),rgb.b),sharedSafeWhite);
            vec3 white=vec3(neutral);
            oRgb=vec4(mix(original.rgb,white,fade),original.a);
        }
    """.trimIndent()

    /** IRIS_26859_B_PHYSICAL_LENS_LSC_ONCE
     * Sensor-linear RGB after pinned AMaZE; original clip evidence was already
     * committed pre-LSC. The same Camera2 RGGB map/origin as Sabre A is used,
     * but this code is entered ONLY on B. Physical pixel geometry includes
     * tile origin and 2x output scale, never display crop or zoom guessing.
     */
    val bLensShade = """
        #version 300 es
        precision highp float;
        uniform sampler2D uSensorRgb;
        uniform sampler2D uLensShading;
        uniform ivec2 uSize;
        uniform ivec2 uOrigin;
        uniform ivec2 uNativeSize;
        uniform int uExpandedScale;
        layout(location=0) out vec4 oRgb;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 rgba=texelFetch(uSensorRgb,p,0);
            vec2 nativeUv=(vec2(uOrigin+p)+vec2(0.5))/
                (vec2(uNativeSize)*float(uExpandedScale));
            vec4 gains=texture(uLensShading,nativeUv);
            vec3 physical=vec3(gains.r,0.5*(gains.g+gains.b),gains.a);
            oRgb=vec4(rgba.rgb*physical,rgba.a);
        }
    """.trimIndent()
}
