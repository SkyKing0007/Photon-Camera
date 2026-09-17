precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float outputExposureScale;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;
out float Output;

const vec3 IRIS_LUMA = vec3(0.22897456,0.69173852,0.07928691);
const float IRIS_LOG_FLOOR = 0.000244140625; /* 2^-12 */

float irisMax3(vec3 v){return max(v.r,max(v.g,v.b));}
float irisGuide(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    return max(dot(rgb,IRIS_LUMA),irisMax3(rgb));
}

/* IRIS_26632_SMOOTHER_UPPER_TONE
 * 26632 preserves the same pointwise/global owner and 0.65 entry but reserves more ordered SDR
 * range through source white. No spatial mask, edge boost, or local-protection change.
 *
 * IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE
 * 26622 proved that the image-formation and Local-Laplacian architecture are sound, but two
 * very different scenes still crowded real HDR separation into the last few SDR code values.
 * Preserve the exact 26621/26622 mapping through source guide 0.65. Above that point, derive one
 * scene-wide highlight pressure from already-solved broad/hard ceiling occupancy plus the robust
 * adaptive/base scene-white ratio. This is not scene recognition: no sky/window/lamp semantics.
 * The upper body is a monotone C1 Hermite continuation and the >1 tail is a C1 rational shoulder.
 * Sparse highlights keep a high white anchor; broad HDR fields reserve more SDR range. */
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
    if(requested>whiteAnchor) bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
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
    if(requested>whiteAnchor) bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float value=0.0;
        float derivative=0.0;
        iris26623LegacyBody(x,requested,value,derivative);
        return value;
    }
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
    if(adaptiveEnable<=1.0e-7 || x<=upperStart) return legacy;

    float pressure=iris26623HighlightPressure();
    float targetWhite=mix(0.945,0.925,pressure);
    float targetSlope=mix(0.360,0.300,pressure);
    float startValue=0.0;
    float startSlope=0.0;
    iris26623LegacyBody(upperStart,requested,startValue,startSlope);
    float width=1.0-upperStart;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6) return legacy;

    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant;
    float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){
        float limiter=3.0/sqrt(norm2);
        m0*=limiter;
        m1*=limiter;
    }

    float candidate;
    if(x<=1.0){
        float t=clamp((x-upperStart)/width,0.0,1.0);
        float t2=t*t;
        float t3=t2*t;
        float h00=2.0*t3-3.0*t2+1.0;
        float h10=t3-2.0*t2+t;
        float h01=-2.0*t3+3.0*t2;
        float h11=t3-t2;
        candidate=h00*startValue+h10*width*m0+h01*targetWhite+h11*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float tailScale=reserve/max(m1,1.0e-6);
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(legacy,candidate,adaptiveEnable);
}

/* IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE
 * OFF is exact 26652. ON is applied only after brightnessTargetGain/displayGain is frozen.
 * Below source guide 0.65 the map is exactly OFF; above it one C1 monotone curve preserves
 * visible spacing of the real extended-linear >1.0 HDR master. */
float iris26653MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float off=iris26623MapMotionSdrFinalGuide(x);
    if(iris26653HighlightCompressionEnabled==0 || x<=0.65)return off;
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float enable=smoothstep(1.05,1.25,requested);
    if(enable<=1.0e-7)return off;
    float scenePressure=iris26623HighlightPressure();
    float kneePressure=clamp((0.90-iris26653HighlightKnee)/(0.90-0.55),0.0,1.0);
    float pressure=max(scenePressure,kneePressure);
    float targetWhite=mix(0.915,0.890,pressure);
    float targetSlope=mix(0.090,0.055,pressure);
    const float startX=0.65;
    float startValue=0.0; float startSlope=0.0;
    iris26623LegacyBody(startX,requested,startValue,startSlope);
    float width=1.0-startX;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return off;
    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-startX)/width,0.0,1.0);
        float t2=t*t; float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue
            +(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite
            +(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float whiteSpan=max(1.0,sqrt(max(iris26653AdaptiveWhitePoint,1.0)));
        float tailScale=reserve/max(m1,1.0e-6)*whiteSpan;
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(off,candidate,enable);
}

void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float mapped=iris26653MapMotionSdrFinalGuide(irisGuide(texelFetch(InputBuffer,p,0).rgb));
    Output=log2(max(mapped,IRIS_LOG_FLOOR));
}
