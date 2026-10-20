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

    /** Per-frame independent B clip votes. Physical x/y are original sensor sites.
     * Quad-wide motion admission is unchanged; all four phases receive the SAME
     * rejection/flow scalar, and all clipped values are measured from the RAW
     * code BEFORE calculation-WB, lens shading, AMaZE, RGB/tone or LONG.
     * RGBA = weighted R/G1/G2/B clipped votes indexed TL/TR/BL/BR.
     */
    val bClipAccumulate = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform sampler2D uFlow;
        uniform sampler2D uReject;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uRawSize;
        uniform ivec2 uCellSize;
        uniform vec4 uFlowBorder;
        uniform float uWhite;
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
                ivec2 off=ivec2(phase&1,phase>>1);
                ivec2 p=quad+off;
                vec2 c=vec2(p)+vec2(0.5)+d;
                vec2 lattice=(c-vec2(off)-vec2(0.5))*0.5;
                ivec2 nearest=ivec2(floor(lattice+vec2(0.5)));
                ivec2 maximum=max((uRawSize-ivec2(1)-off)/2,ivec2(0));
                ivec2 pixel=clamp(nearest,ivec2(0),maximum)*2+off;
                float code=float(texelFetch(uRaw,pixel,0).r);
                // Same pre-WB sensor 0.9925-white headroom transition as the
                // inherited CFA temporal owner, never post-RGB thresholds.
                float nearWhite = smoothstep(uWhite*0.9925,uWhite,code);
                clipped[phase]=nearWhite*w;
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
                    float affinity=(1.0-smoothstep(1.2,3.5,length(dc)/max(2.0*noise,0.002)))*
                        (1.0-smoothstep(1.2,3.0,gd/max(2.0*noise,0.002)));
                    acc+=affinity*vec2(z.r-z.g,z.b-z.g);aw+=affinity;
                }
            }
            float safe=(1.0-smoothstep(1.8,4.0,structure/max(noise,0.002)))*
                (1.0-smoothstep(0.10,0.50,green))*(1.0-smoothstep(0.0,0.30,sensorClipped));
            float need=smoothstep(0.025,0.13,noise/max(green,0.02));
            float weak=1.0-smoothstep(3.0,10.0,n);
            float a=clamp(0.30*need*(0.4+0.6*weak)*safe,0.0,0.30);
            vec2 dc=vec2(v.r-v.g,v.b-v.g);
            vec2 cleaned=mix(dc,acc/max(aw,0.001),a);
            oRgb=vec4(v.g+cleaned.x,v.g,v.g+cleaned.y,v.a);
        }
    """.trimIndent()

    /** JFA-compatible low-resolution guide: seeded ONLY on wholly unclipped
     * genuine camera color near the highlight. No sensor-clipped pixel can seed. */
    val bGuideSeed = """
        #version 300 es
        precision highp float;
        uniform sampler2D uWbRgb;
        uniform sampler2D uClip;
        uniform ivec2 uSize;
        uniform ivec2 uRgbSize;
        uniform ivec2 uCellSize;
        uniform int uBayerPattern;
        uniform ivec2 uOrigin;
        uniform int uExpandedScale;
        layout(location=0) out vec4 oGuide;
        vec3 clipRgb(ivec2 p){
            ivec2 global=uOrigin+p;
            ivec2 q=clamp(global/(2*uExpandedScale),ivec2(0),uCellSize-ivec2(1));
            vec4 ph=texelFetch(uClip,q,0);
            if(uBayerPattern==0)return vec3(ph.r,max(ph.g,ph.b),ph.a);
            if(uBayerPattern==1)return vec3(ph.g,max(ph.r,ph.a),ph.b);
            if(uBayerPattern==2)return vec3(ph.b,max(ph.r,ph.a),ph.g);
            return vec3(ph.a,max(ph.g,ph.b),ph.r);
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            ivec2 rgb=clamp(p*4+ivec2(2),ivec2(0),uRgbSize-ivec2(1));
            vec3 v=max(texelFetch(uWbRgb,rgb,0).rgb,vec3(0.0));
            vec3 clip=clipRgb(rgb);
            float signal=max(max(v.r,v.g),v.b);
            float clear=1.0-smoothstep(0.05,0.25,max(max(clip.r,clip.g),clip.b));
            float bright=smoothstep(0.18,0.32,signal);
            float good=clear*bright;
            float scale=max(v.r+v.g+v.b,1.0e-5);
            oGuide=vec4(v/scale,good);
        }
    """.trimIndent()

    val bGuideSpread = """
        #version 300 es
        precision highp float;
        uniform sampler2D uPrior;
        uniform sampler2D uWbRgb;
        uniform ivec2 uSize;
        uniform ivec2 uRgbSize;
        uniform int uStride;
        layout(location=0) out vec4 oGuide;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 best=texelFetch(uPrior,p,0);
            vec3 here=texelFetch(uWbRgb,clamp(p*4+ivec2(2),ivec2(0),uRgbSize-ivec2(1)),0).rgb;
            float luma=max(dot(max(here,vec3(0.0)),vec3(0.25,0.5,0.25)),0.0);
            float score=best.a;
            for(int y=-1;y<=1;++y){
                for(int x=-1;x<=1;++x){
                    if(x==0&&y==0)continue;
                    ivec2 q=clamp(p+ivec2(x,y)*uStride,ivec2(0),uSize-ivec2(1));
                    vec4 g=texelFetch(uPrior,q,0);
                    vec3 c=texelFetch(uWbRgb,clamp(q*4+ivec2(2),ivec2(0),uRgbSize-ivec2(1)),0).rgb;
                    float nearby=max(dot(max(c,vec3(0.0)),vec3(0.25,0.5,0.25)),0.0);
                    float match=1.0-smoothstep(0.08,0.75,abs(luma-nearby));
                    float candidate=g.a*match*0.96;
                    if(candidate>score){score=candidate;best=vec4(g.rgb,candidate);}
                }
            }
            oGuide=best;
        }
    """.trimIndent()

    /** Apply per-channel ratio from locally propagated unclipped color; no
     * global neutral clamp and NO changes when all sensor sites are valid. */
    val bHighlightRecover = """
        #version 300 es
        precision highp float;
        uniform sampler2D uWbRgb;
        uniform sampler2D uClip;
        uniform sampler2D uGuide;
        uniform ivec2 uSize;
        uniform ivec2 uCellSize;
        uniform int uBayerPattern;
        uniform ivec2 uOrigin;
        uniform int uExpandedScale;
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
            vec3 frac=clipRgb(p);
            vec3 bad=smoothstep(vec3(0.65),vec3(0.94),frac);
            if(max(max(bad.r,bad.g),bad.b)<0.001){oRgb=original;return;}
            vec4 guide=texelFetch(uGuide,p/4,0);
            vec3 c=max(original.rgb,vec3(0.0));
            vec3 recovered=c;
            float surviving=dot(vec3(1.0)-bad,guide.rgb);
            float sumActual=dot(vec3(1.0)-bad,c);
            if(guide.a>0.22&&surviving>0.015){
                float intensity=sumActual/surviving;
                // Confidence and channel-selectivity prevent projecting unrelated
                // surrounding material colors into physically saturated lamps.
                vec3 target=guide.rgb*min(intensity,8.0);
                vec3 trust=bad*clamp(guide.a,0.0,1.0);
                recovered=mix(c,target,trust);
            } else if(min(min(bad.r,bad.g),bad.b)>0.98){
                // Only a genuinely ALL-channel clipped core, with no trustworthy
                // guide, can move gently toward neutral. Never flatten its luma.
                float y=dot(c,vec3(0.25,0.5,0.25));
                recovered=mix(c,vec3(y),0.10);
            }
            oRgb=vec4(recovered,original.a);
        }
    """.trimIndent()
}
