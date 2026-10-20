package com.hinnka.mycamera.processor

/**
 * IRIS_26858_B_INDEPENDENT_COLOR_NOISE_AND_SENSOR_CLIP_PROVENANCE.
 * Only the AMaZE B stacker links these shaders. A's 26850 reconstruction, VGN,
 * CFA denoising, and Camera2/RAW-DNG output are never consumers of this object.
 * Clip evidence is collected on original pre-LSC/pre-WB unsigned sensor RAWs,
 * not from temporary WB camera RGB, gamma, AMaZE or an SDR RGB heuristic.
 */
internal object GlesIris26858BNoiseHighlight {
    val bCfaNoise = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uPhaseSignal;
        uniform sampler2D uSupport;
        uniform sampler2D uValidity;
        uniform sampler2D uMoments;
        uniform ivec2 uSize;
        uniform vec4 uShot;
        uniform vec4 uRead;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oCfaWeighted;
        ivec2 bound(ivec2 p) { return clamp(p,ivec2(0),uSize-ivec2(1)); }
        float weight(ivec2 p) { return texelFetch(uSupport,bound(p),0).x; }
        vec4 mean(ivec2 p) {
            p=bound(p); float w=weight(p);
            return w>1.0e-7 ? texelFetch(uPhaseSignal,p,0)/w : vec4(0.0);
        }
        float neff(ivec2 p) {
            p=bound(p);
            float w=weight(p);
            float ss=texelFetch(uMoments,p,0).x;
            return ss>1.0e-7 ? clamp(w*w/ss,1.0,32.0) : 1.0;
        }
        vec4 sigmaAt(ivec2 p,vec4 v){
            p=bound(p);
            // Actual B per-NORMAL Camera2 variance, weighted by the exact
            // 26852 shared admission: sum(w_i^2 * var_i)/(sum w_i)^2.
            float w=weight(p);
            float measured=max(texelFetch(uMoments,p,0).y,0.0)/max(w*w,1.0e-10);
            vec4 phaseVar=max(uShot*max(v,vec4(0.0))+uRead,vec4(1.0e-9));
            float phaseMean=max(dot(phaseVar,vec4(0.25)),1.0e-9);
            return sqrt(max(measured*phaseVar/phaseMean,vec4(1.0e-9)));
        }
        void main() {
            ivec2 p=bound(ivec2(gl_FragCoord.xy));
            float w=weight(p);
            if(w<1.0e-7){oCfaWeighted=vec4(0.0);return;}
            vec4 center=mean(p);
            float n=neff(p);
            vec4 noise=sigmaAt(p,center);
            vec4 admitted=clamp(texelFetch(uValidity,p,0)/max(w,1.0e-7),0.0,1.0);
            // Physical site order TL/TR/BL/BR, never assume RGGB globally.
            // Canonical phase mapping must exactly match the pinned 26856 CFA pack.
            int ri = (uBayerPattern==0 ? 0 : uBayerPattern==1 ? 1 : uBayerPattern==2 ? 2 : 3);
            int bi = (uBayerPattern==0 ? 3 : uBayerPattern==1 ? 2 : uBayerPattern==2 ? 1 : 0);
            int g1 = (uBayerPattern==0 ? 1 : uBayerPattern==1 ? 0 : uBayerPattern==2 ? 3 : 2);
            int g2 = (uBayerPattern==0 ? 2 : uBayerPattern==1 ? 3 : uBayerPattern==2 ? 0 : 1);
            float green=0.5*(center[g1]+center[g2]);
            float greenNoise=0.5*(noise[g1]+noise[g2]);
            float highFreq=0.0;
            float lumaEdge=0.0;
            vec2 sum=2.0*vec2(center[ri],center[bi]);
            vec2 sumW=vec2(2.0);
            float chromaR=center[ri]-green;
            float chromaB=center[bi]-green;
            float chromaNoiseR=sqrt(noise[ri]*noise[ri]+greenNoise*greenNoise);
            float chromaNoiseB=sqrt(noise[bi]*noise[bi]+greenNoise*greenNoise);
            float coherentChroma=0.0;
            // Genuine local three-bin N_eff histogram from the temporally
            // admitted aligned NORMAL burst, never the old 1/mergeFactor.
            vec3 supportHistogram=vec3(0.0);
            for(int dy=-1;dy<=1;++dy){
                for(int dx=-1;dx<=1;++dx){
                    if(dx==0&&dy==0)continue;
                    ivec2 q=bound(p+ivec2(dx,dy));
                    float nq=neff(q);
                    supportHistogram+=vec3(float(nq<3.0),
                        float(nq>=3.0&&nq<8.0),float(nq>=8.0));
                    vec4 v=mean(q);
                    vec4 vn=sigmaAt(q,v);
                    float g=0.5*(v[g1]+v[g2]);
                    highFreq=max(highFreq,abs(g-green));
                    float sigmaG=sqrt(greenNoise*greenNoise+
                        0.25*(vn[g1]+vn[g2])*(vn[g1]+vn[g2]));
                    float material=1.0-smoothstep(2.0,4.2,abs(g-green)/max(sigmaG,0.001));
                    vec2 dd=abs(vec2(v[ri]-g,v[bi]-g)-vec2(chromaR,chromaB));
                    vec2 sn=vec2(chromaNoiseR,chromaNoiseB)+
                        vec2(sqrt(vn[ri]*vn[ri]+sigmaG*sigmaG),sqrt(vn[bi]*vn[bi]+sigmaG*sigmaG));
                    coherentChroma=max(coherentChroma,max((dd.x-3.5*sn.x)/max(sn.x,0.001),
                        (dd.y-3.5*sn.y)/max(sn.y,0.001)));
                    vec2 chromaAffinity=1.0-smoothstep(vec2(1.2),vec2(3.4),dd/max(sn,vec2(0.001)));
                    float spatial=(abs(dx)+abs(dy)==2)?0.75:1.0;
                    vec2 a=chromaAffinity*(material*spatial);
                    sum+=a*vec2(v[ri],v[bi]);
                    sumW+=a;
                    lumaEdge=max(lumaEdge,max(abs(v[g1]-center[g1]),abs(v[g2]-center[g2])));
                }
            }
            float flatEvidence=1.0-smoothstep(2.0,4.0,
                highFreq/max(greenNoise*1.414,0.001));
            float structure=1.0-smoothstep(2.3,4.5,
                lumaEdge/max(greenNoise*1.414,0.001));
            float colorStructure=1.0-smoothstep(0.0,2.0,coherentChroma);
            float shadow=1.0-smoothstep(0.12,0.55,green);
            float need=smoothstep(0.014,0.10,greenNoise/max(green,0.018));
            float supportNeed=1.0-smoothstep(3.0,9.0,n);
            // Local support histogram prevents aggressive denoise where most
            // adjacent sites have strong genuine burst support.
            float supportDistributionGuard=1.0-0.6*smoothstep(3.0,7.0,
                supportHistogram.z);
            float phaseValid=min(min(admitted.r,admitted.g),min(admitted.b,admitted.a));
            float validity=smoothstep(0.55,0.95,phaseValid);
            // Independent B pre-AMaZE chroma denoising. Preserve BOTH green phases
            // and therefore all luminance/high-frequency structure exactly.
            float alpha=clamp(0.86*need*(0.5+0.5*shadow)*
                (0.4+0.6*supportNeed)*supportDistributionGuard*
                flatEvidence*structure*colorStructure*validity,0.0,0.86);
            vec4 outC=center;
            outC[ri]=mix(center[ri],sum.x/max(sumW.x,1.0e-6),alpha);
            outC[bi]=mix(center[bi],sum.y/max(sumW.y,1.0e-6),alpha);
            oCfaWeighted=outC*w;
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
    val bResidualChroma = """
        #version 300 es
        precision highp float;
        uniform sampler2D uRgb;
        uniform sampler2D uSupport;
        uniform sampler2D uMoments;
        uniform sampler2D uClip;
        uniform sampler2D uLensShading;
        uniform int uUseLensShading;
        uniform ivec2 uNativeSize;
        uniform ivec2 uSize;
        uniform ivec2 uClipCellSize;
        uniform ivec2 uOrigin;
        uniform int uExpandedScale;
        uniform vec4 uNoiseShot;
        uniform vec4 uNoiseRead;
        layout(location=0) out vec4 oRgb;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 v=texelFetch(uRgb,p,0);
            ivec2 c=clamp((uOrigin+p)/(2*uExpandedScale),
                ivec2(0),uClipCellSize-ivec2(1));
            vec4 clip=texelFetch(uClip,c,0);
            float sensorClipped=max(max(clip.r,clip.g),max(clip.b,clip.a));
            float w=texelFetch(uSupport,c,0).x;
            float ss=texelFetch(uMoments,c,0).x;
            float n=ss>1.0e-7?clamp(w*w/ss,1.0,32.0):1.0;
            float green=max(v.g,0.0);
            float noise=sqrt(max(texelFetch(uMoments,c,0).y,1.0e-9)) /
                max(w,1.0e-6);
            // 26859: per-physical-channel gain squares variance exactly once
            // AFTER the B-only sensor-linear lens-map pass. No scalar denoise
            // coefficient is increased; pre-LSC CFA denoise is unchanged.
            vec3 gainRgb=vec3(1.0);
            if(uUseLensShading!=0){
                vec2 uv=(vec2(uOrigin+p)+vec2(0.5))/
                    (vec2(uNativeSize)*float(uExpandedScale));
                vec4 gains=texture(uLensShading,uv);
                gainRgb=vec3(gains.r,0.5*(gains.g+gains.b),gains.a);
            }
            vec3 phaseSigma=noise*gainRgb;
            vec2 chromaSigma=sqrt(max(vec2(
                0.5*(phaseSigma.r*phaseSigma.r+phaseSigma.g*phaseSigma.g),
                0.5*(phaseSigma.b*phaseSigma.b+phaseSigma.g*phaseSigma.g)),
                vec2(1.0e-9)));
            float greenSigma=phaseSigma.g;
            float noiseForNeed=max(chromaSigma.x,chromaSigma.y);
            vec2 acc=vec2(0.0);float aw=0.0;
            float structure=0.0;
            for(int yy=-1;yy<=1;++yy){
                for(int xx=-1;xx<=1;++xx){
                    if(xx==0&&yy==0)continue;
                    ivec2 q=clamp(p+ivec2(xx,yy),ivec2(0),uSize-ivec2(1));
                    vec3 z=texelFetch(uRgb,q,0).rgb;
                    float gd=abs(z.g-v.g);
                    structure=max(structure,gd);
                    vec2 dc=vec2(z.r-z.g,z.b-z.g)-vec2(v.r-v.g,v.b-v.g);
                    float affinity=(1.0-smoothstep(1.2,3.5,length(dc/max(2.0*chromaSigma,vec2(0.002)))))*
                        (1.0-smoothstep(1.2,3.0,gd/max(2.0*greenSigma,0.002)));
                    acc+=affinity*vec2(z.r-z.g,z.b-z.g);aw+=affinity;
                }
            }
            float safe=(1.0-smoothstep(1.8,4.0,structure/max(greenSigma,0.002)))*
                (1.0-smoothstep(0.10,0.50,green))*(1.0-smoothstep(0.0,0.30,sensorClipped));
            float need=smoothstep(0.025,0.13,noiseForNeed/max(green,0.02));
            float weak=1.0-smoothstep(3.0,10.0,n);
            float a=clamp(0.30*need*(0.4+0.6*weak)*safe,0.0,0.30);
            vec2 dc=vec2(v.r-v.g,v.b-v.g);
            vec2 cleaned=mix(dc,acc/max(aw,0.001),a);
            oRgb=vec4(v.g+cleaned.x,v.g,v.g+cleaned.y,v.a);
        }
    """.trimIndent()

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
