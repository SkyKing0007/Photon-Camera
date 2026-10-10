precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float outputExposureScale;
uniform float irisOutputZoom;
uniform float displayGain;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;

layout(std430, binding=1) buffer iris26799Stats {
    uint iris26799Counters[28];
};

out float Output;

/* IRIS_26800_HIGH_CHROMA_BRIGHT_FRINGE_CLASSIFIER
 * Extends the successful 26799 mask admission without changing propagation.
 * High-chroma false fringes may enter only on bright physical contours/plateaus when a
 * genuine 2-D interior patch does not support the center hue. The old 26799 low/moderate
 * classifier remains the fallback for ambiguous pixels.
 *
 * IRIS_26799_MULTI_PASS_FALSE_COLOR_CLASSIFIER
 * Classification only. No RGB is modified here. The input is the exact calibrated linear
 * Display-P3 MotionV2Render input after MotionV2ColorTransform/ACR3 and before presentation tone.
 * The mask encodes: 1.00 phase/opponent seed, 0.85 strict single-hue seed,
 * 0.55 ordinary weak contour candidate, 0.40 neutral highlight-plateau candidate, 0 otherwise.
 * Material validity is two-dimensional: both depth and tangent support are required on a side.
 */

float luminance(vec3 c){return dot(c,vec3(0.22897456,0.69173852,0.07928691));}
float max3(vec3 v){return max(v.r,max(v.g,v.b));}
vec3 sampleP3(vec2 p){
    vec2 sz=vec2(textureSize(InputBuffer,0));
    vec2 hi=max(sz-vec2(1.0),vec2(0.0));
    p=clamp(p,vec2(0.0),hi);
    return max(texture(InputBuffer,(p+vec2(0.5))/sz).rgb,vec3(0.0));
}
vec3 normalizedChroma(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    return (rgb-vec3(y))/max(guide,0.04);
}
float sameHue(vec3 rgb,vec3 dir){return max(dot(normalizedChroma(rgb),dir),0.0);}
float opponent(vec3 rgb,vec3 dir){return max(-dot(normalizedChroma(rgb),dir),0.0);}
float hueTurn(vec3 rgb,vec3 dir,float centerMag){
    vec3 c=normalizedChroma(rgb);
    float m=length(c);
    if(m<=1.0e-7)return 0.0;
    float alignment=dot(c/m,dir);
    float different=1.0-smoothstep(0.42,0.88,alignment);
    return different*smoothstep(0.10,0.42,m/max(centerMag,1.0e-6));
}
float lumaAt(vec2 p){return max(luminance(sampleP3(p)),0.0);}

/* Exact 26798 final-guide predictor subset. */
float iris26623HighlightPressure(){
    float broad=smoothstep(0.015,0.060,clamp(iris26623ToneBroadNearFraction,0.0,1.0));
    float hard=smoothstep(0.010,0.050,clamp(iris26623ToneHardFraction,0.0,1.0));
    float baseWhite=max(iris26623ToneBaseSceneWhite,1.0);
    float adaptiveWhite=max(iris26623ToneAdaptiveSceneWhite,baseWhite);
    float span=max(adaptiveWhite/baseWhite-1.0,0.0);
    float spanPressure=smoothstep(0.08,0.35,span);
    return clamp(max(0.70*broad+0.30*spanPressure,0.75*hard),0.0,1.0);
}
void iris26623LegacyBody(float x,float requested,out float value,out float derivative){
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    float oneMinus=1.0-x;
    float cubic=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    float rational=bodyGain*x/(1.0+ratio*x);
    float cubicDerivative=whiteAnchor+(bodyGain-whiteAnchor)*oneMinus*(1.0-3.0*x);
    float rationalDerivative=bodyGain/((1.0+ratio*x)*(1.0+ratio*x));
    value=0.5*(cubic+rational);
    derivative=0.5*(cubicDerivative+rationalDerivative);
}
float iris26623LegacyMap(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){float value=0.0;float derivative=0.0;iris26623LegacyBody(x,requested,value,derivative);return value;}
    float rationalSlopeAtWhite=bodyGain/((1.0+ratio)*(1.0+ratio));
    float bodySlopeAtWhite=0.5*(whiteAnchor+rationalSlopeAtWhite);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlopeAtWhite,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}
float iris26623MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float legacy=iris26623LegacyMap(x);
    float adaptiveEnable=smoothstep(1.05,1.25,requested);
    const float upperStart=0.65;
    if(adaptiveEnable<=1.0e-7||x<=upperStart)return legacy;
    float pressure=iris26623HighlightPressure();
    float targetWhite=mix(0.945,0.895,pressure);
    float targetSlope=mix(0.360,0.620,pressure);
    float startValue=0.0;float startSlope=0.0;
    iris26623LegacyBody(upperStart,requested,startValue,startSlope);
    float width=1.0-upperStart;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return legacy;
    float m0=max(startSlope,0.0);float m1=max(targetSlope,0.0);
    float a=m0/secant;float b=m1/secant;float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-upperStart)/width,0.0,1.0);float t2=t*t;float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue+(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite+(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);float tailScale=reserve/max(m1,1.0e-6);
        float excess=x-1.0;candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(legacy,candidate,adaptiveEnable);
}
float iris26653MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float off=iris26623MapMotionSdrFinalGuide(x);
    if(iris26653HighlightCompressionEnabled==0||x<=0.65)return off;
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float enable=smoothstep(1.05,1.25,requested);
    if(enable<=1.0e-7)return off;
    float scenePressure=iris26623HighlightPressure();
    float kneePressure=clamp((0.90-iris26653HighlightKnee)/(0.90-0.55),0.0,1.0);
    float pressure=max(scenePressure,kneePressure);
    float targetWhite=mix(0.915,0.890,pressure);float targetSlope=mix(0.090,0.055,pressure);
    const float startX=0.65;float startValue=0.0;float startSlope=0.0;
    iris26623LegacyBody(startX,requested,startValue,startSlope);
    float width=1.0-startX;float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return off;
    float m0=max(startSlope,0.0);float m1=max(targetSlope,0.0);float a=m0/secant;float b=m1/secant;
    float norm2=a*a+b*b;if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-startX)/width,0.0,1.0);float t2=t*t;float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue+(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite+(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);float whiteSpan=max(1.0,sqrt(max(iris26653AdaptiveWhitePoint,1.0)));
        float tailScale=reserve/max(m1,1.0e-6)*whiteSpan;float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(off,candidate,enable);
}

vec2 sourcePixelForOutput(vec2 outputPixel){
    vec2 sourceSize=vec2(textureSize(InputBuffer,0));
    float zoom=max(irisOutputZoom,1.0);
    if(zoom<=1.00001)return clamp(outputPixel,vec2(0.0),sourceSize-vec2(1.0));
    vec2 center=(sourceSize-vec2(1.0))*0.5;
    return clamp(center+(outputPixel-center)/zoom,vec2(0.0),sourceSize-vec2(1.0));
}

float patchSameHue(vec2 p,vec2 n,vec2 t,float side,float depth,vec3 dir){
    vec2 c=p+n*(side*depth);
    return (sameHue(sampleP3(c-t*1.5),dir)+sameHue(sampleP3(c),dir)+sameHue(sampleP3(c+t*1.5),dir))/3.0;
}
float patchChroma(vec2 p,vec2 n,vec2 t,float side,float depth){
    vec2 c=p+n*(side*depth);
    return (length(normalizedChroma(sampleP3(c-t*1.5)))+length(normalizedChroma(sampleP3(c)))
            +length(normalizedChroma(sampleP3(c+t*1.5))))/3.0;
}
float patchLuma(vec2 p,vec2 n,vec2 t,float side,float depth){
    vec2 c=p+n*(side*depth);
    return (lumaAt(c-t*1.5)+lumaAt(c)+lumaAt(c+t*1.5))/3.0;
}

/* IRIS_26800_TRUE_2D_MATERIAL_PATCH
 * A real material hue must occupy area, not merely survive on one depth/tangent line.
 * The 3x3 patch spans normal depths 4..6 around depth 5 and three tangent positions.
 */
float patchSameHueArea(vec2 p,vec2 n,vec2 t,float side,vec3 dir){
    float sum=0.0;
    for(int dn=-1;dn<=1;dn++){
        for(int dt=-1;dt<=1;dt++){
            vec2 q=p+n*(side*(5.0+float(dn)))+t*(1.5*float(dt));
            sum+=sameHue(sampleP3(q),dir);
        }
    }
    return sum/9.0;
}
float patchChromaArea(vec2 p,vec2 n,vec2 t,float side){
    float sum=0.0;
    for(int dn=-1;dn<=1;dn++){
        for(int dt=-1;dt<=1;dt++){
            vec2 q=p+n*(side*(5.0+float(dn)))+t*(1.5*float(dt));
            sum+=length(normalizedChroma(sampleP3(q)));
        }
    }
    return sum/9.0;
}

void main(){
    vec2 outputPixel=vec2(gl_FragCoord.xy)-vec2(0.5);
    vec2 p=sourcePixelForOutput(outputPixel);
    vec3 rgb=sampleP3(p);
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    vec3 frac=normalizedChroma(rgb);
    float mag=length(frac);
    float chromaPresence=smoothstep(0.010,0.034,mag);
    if(guide<=1.0e-6||chromaPresence<=1.0e-5){Output=0.0;return;}

    float projected=iris26653MapMotionSdrFinalGuide(guide);
    float brightRisk=smoothstep(0.64,0.82,projected);
    if(brightRisk<=1.0e-5){Output=0.0;return;}
    atomicAdd(iris26799Counters[0],1u);

    float legacyChromaRisk=chromaPresence*(1.0-smoothstep(0.28,0.44,mag));
    float highChroma=smoothstep(0.26,0.38,mag);
    bool highChromaRelevant=highChroma>1.0e-5;
    if(highChromaRelevant)atomicAdd(iris26799Counters[20],1u);

    vec3 dir=frac/max(mag,1.0e-7);
    vec2 gx=vec2(lumaAt(p+vec2(1.0,0.0))-lumaAt(p-vec2(1.0,0.0)),
                  lumaAt(p+vec2(0.0,1.0))-lumaAt(p-vec2(0.0,1.0)));
    vec2 cg=vec2(length(normalizedChroma(sampleP3(p+vec2(1.0,0.0))))-length(normalizedChroma(sampleP3(p-vec2(1.0,0.0)))),
                 length(normalizedChroma(sampleP3(p+vec2(0.0,1.0))))-length(normalizedChroma(sampleP3(p-vec2(0.0,1.0)))));
    vec2 axis=length(gx)>1.0e-6?gx:(length(cg)>1.0e-6?cg:vec2(1.0,0.0));
    vec2 n=normalize(axis);vec2 t=vec2(-n.y,n.x);

    float pos3=patchSameHue(p,n,t,1.0,3.0,dir);float pos5=patchSameHue(p,n,t,1.0,5.0,dir);
    float neg3=patchSameHue(p,n,t,-1.0,3.0,dir);float neg5=patchSameHue(p,n,t,-1.0,5.0,dir);
    float posDepthSupport=min(pos3,pos5);float negDepthSupport=min(neg3,neg5);
    float posAreaSupport=patchSameHueArea(p,n,t,1.0,dir);
    float negAreaSupport=patchSameHueArea(p,n,t,-1.0,dir);
    float posRobust=min(posDepthSupport,posAreaSupport);
    float negRobust=min(negDepthSupport,negAreaSupport);
    float robustMaterialRatio=max(posRobust,negRobust)/max(mag,1.0e-6);
    float materialSupport=smoothstep(0.28,0.60,robustMaterialRatio);
    float unsupported=1.0-materialSupport;

    float posAreaChroma=patchChromaArea(p,n,t,1.0);
    float negAreaChroma=patchChromaArea(p,n,t,-1.0);
    float neutralInterior=1.0-smoothstep(0.055,0.17,min(posAreaChroma,negAreaChroma));

    /* IRIS_26800_STRICT_MATERIAL_PROOF
     * A high-chroma center is protected only when the same hue fills a real 2-D interior patch.
     * A narrow CFA lobe cannot authenticate itself through one depth/tangent line.
     */
    if(materialSupport>0.72){
        atomicAdd(iris26799Counters[5],1u);
        atomicAdd(iris26799Counters[23],1u);
        Output=0.0;
        return;
    }

    float p1=lumaAt(p+n);float n1=lumaAt(p-n);
    float p2=lumaAt(p+n*2.0);float n2=lumaAt(p-n*2.0);
    float p3=lumaAt(p+n*3.0);float n3=lumaAt(p-n*3.0);
    float edgeBand=max(abs(p1-n1)*0.5,max(abs(p2-n2)*0.25,abs(p3-n3)/6.0));
    float edgeRisk=smoothstep(0.026,0.105,edgeBand*max(irisOutputZoom,1.0)/max(guide,0.03));

    float posL=0.5*(patchLuma(p,n,t,1.0,3.0)+patchLuma(p,n,t,1.0,5.0));
    float negL=0.5*(patchLuma(p,n,t,-1.0,3.0)+patchLuma(p,n,t,-1.0,5.0));
    float rangeLo=min(posL,negL);float rangeHi=max(posL,negL);
    float outside=max(max(rangeLo-y,y-rangeHi),0.0)/max(guide,0.03);
    float withinMaterial=1.0-smoothstep(0.06,0.24,outside);
    float materialSpan=abs(posL-negL)/max(guide,0.03);
    float ordinarySpan=smoothstep(0.030,0.14,materialSpan);

    /* Exact 26799 low/moderate-chroma fallback admission. */
    float weakStrength=brightRisk*legacyChromaRisk*unsupported*edgeRisk*withinMaterial*ordinarySpan;
    float weak=smoothstep(0.07,0.24,weakStrength);
    if(weak>1.0e-5)atomicAdd(iris26799Counters[3],1u);

    float plateauFlat=1.0-smoothstep(0.030,0.105,materialSpan);
    float plateauBright=smoothstep(0.86,0.95,projected);
    float plateauStrength=plateauBright*legacyChromaRisk*unsupported*neutralInterior*plateauFlat;
    float plateau=smoothstep(0.08,0.28,plateauStrength);
    if(plateau>1.0e-5)atomicAdd(iris26799Counters[4],1u);

    /* IRIS_26800_HIGH_CHROMA_BRIGHT_ADMISSION
     * The 26799 0.28..0.44 ceiling hid the strongest false pixels. Admit them only where spatial
     * evidence is restrictive: very bright contour/plateau, unsupported 2-D material hue, and a
     * narrow edge/plateau topology. This is hue-agnostic (green/pink/magenta/violet/blue/cyan).
     */
    float highBright=smoothstep(0.80,0.93,projected);
    float highTopology=max(edgeRisk,plateauBright*plateauFlat);
    float highStrength=highChroma*highBright*unsupported*neutralInterior*withinMaterial*highTopology;
    float highWeak=smoothstep(0.10,0.34,highStrength);
    if(highWeak>1.0e-5)atomicAdd(iris26799Counters[24],1u);

    vec3 q1=sampleP3(p+n);vec3 q2=sampleP3(p+n*2.0);vec3 q3=sampleP3(p+n*3.0);
    vec3 r1=sampleP3(p-n);vec3 r2=sampleP3(p-n*2.0);vec3 r3=sampleP3(p-n*3.0);
    float opp=max(max(opponent(q1,dir),opponent(r1,dir)),max(max(opponent(q2,dir),opponent(r2,dir)),max(opponent(q3,dir),opponent(r3,dir))));
    float wideOpponent=smoothstep(0.08,0.34,opp/max(mag,1.0e-6));
    float turn=max(max(hueTurn(q1,dir,mag),hueTurn(r1,dir,mag)),max(max(hueTurn(q2,dir,mag),hueTurn(r2,dir,mag)),max(hueTurn(q3,dir,mag),hueTurn(r3,dir,mag))));
    float phaseEvidence=max(wideOpponent,turn);

    float candidate=max(max(weak,plateau),highWeak);
    float phaseSeed=smoothstep(0.16,0.40,candidate*phaseEvidence);
    if(phaseSeed>1.0e-5)atomicAdd(iris26799Counters[1],1u);

    float lowPhase=1.0-smoothstep(0.12,0.30,phaseEvidence);
    float singleHueBright=smoothstep(0.80,0.92,projected);
    float moderateChroma=1.0-smoothstep(0.18,0.30,mag);
    float regularSingleHueStrength=max(weak,plateau)*singleHueBright*neutralInterior
            *withinMaterial*lowPhase*moderateChroma;
    float regularSingleHueSeed=smoothstep(0.18,0.42,regularSingleHueStrength);

    float highSingleHueStrength=highWeak*singleHueBright*lowPhase;
    float highSingleHueSeed=smoothstep(0.14,0.36,highSingleHueStrength);
    if(highSingleHueSeed>1.0e-5)atomicAdd(iris26799Counters[22],1u);

    float highPlateauStrength=highWeak*plateauBright*plateauFlat;
    float highPlateauSeed=smoothstep(0.12,0.34,highPlateauStrength);
    if(highPlateauSeed>1.0e-5)atomicAdd(iris26799Counters[21],1u);

    float singleHueSeed=max(regularSingleHueSeed,highSingleHueSeed);
    if(singleHueSeed>1.0e-5)atomicAdd(iris26799Counters[2],1u);

    if(phaseSeed>1.0e-5||highPlateauSeed>1.0e-5){Output=1.0;return;}
    if(singleHueSeed>1.0e-5){Output=0.85;return;}
    if(max(weak,highWeak)>1.0e-5){Output=0.55;return;}
    if(plateau>1.0e-5){Output=0.40;return;}
    if(highChromaRelevant)atomicAdd(iris26799Counters[27],1u);
    Output=0.0;
}
