precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float sceneWhite;
uniform float outputExposureScale;
uniform float irisOutputZoom;
uniform int iris26592MotionHdrHandoff;
uniform float displayGain;
uniform sampler2D iris26621LocalToneLog;
uniform int iris26621LocalToneEnabled;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform float iris26630MotionSaturation;
/* IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER */
out vec3 Output;

/*
 * IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV
 *
 * Retires IRIS_26420's fixed 0.70 asymptotic shoulder.
 *
 * Values below 0.50 linear are untouched.
 * Above that, the available display range is allocated according to the
 * Motion-owned physical headroom (sceneWhite), derived from the canonical RAW
 * exposure gain. This preserves substantially more window/sky separation.
 */

float max3(vec3 v) {
    return max(v.r,max(v.g,v.b));
}

float luminance(vec3 c) {
    return dot(c,vec3(0.22897456,0.69173852,0.07928691));
}

/*
 * IRIS_26438_REFERENCE_SAFE_MICROCONTRAST
 *
 * Lightroom showed that much of the apparent haze is surviving detail with
 * insufficient local tonal separation. Restore only a bounded log-luma
 * residual, and fade it out in deep shadows and highlights to avoid noise,
 * halos and highlight-edge exaggeration.
 */
float localLogLumaMean(ivec2 xy) {
    ivec2 sz=textureSize(InputBuffer,0);
    float sum=0.0;
    float wsum=0.0;
    for(int oy=-2;oy<=2;oy++) {
        for(int ox=-2;ox<=2;ox++) {
            ivec2 p=clamp(xy+ivec2(ox,oy),ivec2(0),sz-ivec2(1));
            float y=max(luminance(max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0))),0.0);
            float r2=float(ox*ox+oy*oy);
            float w=exp(-0.55*r2);
            sum+=w*log(1.0e-4+y);
            wsum+=w;
        }
    }
    return sum/max(wsum,1.0e-6);
}
vec3 applyReferenceSafeMicrocontrast(ivec2 xy, vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    if(y<=1.0e-7) return rgb;
    float detail=log(1.0e-4+y)-localLogLumaMean(xy);
    detail=clamp(detail,-0.20,0.20);
    float shadowGate=smoothstep(0.025,0.12,y);
    float highlightGate=1.0-smoothstep(0.55,0.92,y);
    float gate=shadowGate*highlightGate;
    float scale=exp(0.42*gate*detail);
    return rgb*scale;
}

float srgbEncode(float x) {
    x=max(x,0.0);
    return x<=0.0031308
            ? 12.92*x
            : 1.055*pow(x,1.0/2.4)-0.055;
}

vec3 srgbEncode(vec3 x) {
    return vec3(
            srgbEncode(x.r),
            srgbEncode(x.g),
            srgbEncode(x.b));
}

vec3 iris26524BilinearInput(vec2 sourcePixel) {
    ivec2 sz = textureSize(InputBuffer,0);
    vec2 hi = max(vec2(sz) - vec2(1.0), vec2(0.0));
    vec2 p = clamp(sourcePixel, vec2(0.0), hi);
    ivec2 p0 = ivec2(floor(p));
    ivec2 p1 = min(p0 + ivec2(1), sz - ivec2(1));
    vec2 f = fract(p);
    vec3 a = mix(texelFetch(InputBuffer, ivec2(p0.x,p0.y),0).rgb,
                 texelFetch(InputBuffer, ivec2(p1.x,p0.y),0).rgb, f.x);
    vec3 b = mix(texelFetch(InputBuffer, ivec2(p0.x,p1.y),0).rgb,
                 texelFetch(InputBuffer, ivec2(p1.x,p1.y),0).rgb, f.x);
    return mix(a,b,f.y);
}

/* IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE
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
    float targetWhite=mix(0.925,0.885,pressure);
    float targetSlope=mix(0.270,0.200,pressure);
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


float mapFinalSdrGuide(float sourceGuide) {
    if(iris26592MotionHdrHandoff!=0) {
        return iris26623MapMotionSdrFinalGuide(sourceGuide);
    }

    float start=0.50;
    float mappedPre=sourceGuide;
    if(sourceGuide>start){
        float whitePoint=max(sceneWhite,start+0.05);
        float u=max((sourceGuide-start)/max(whitePoint-start,1.0e-6),0.0);
        float x=clamp(u,0.0,1.0);
        float shaped=log(1.0+6.0*x)/log(7.0);
        float preScaleDisplayWhite=1.0/max(outputExposureScale,1.0e-6);
        mappedPre=start+(preScaleDisplayWhite-start)*shaped;
    }
    return mappedPre*outputExposureScale;
}

vec3 mapExtendedLinearHeadroom(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float peak=max3(rgb);
    float guide=max(y,peak);
    if(guide<=1.0e-7) return rgb;

    /* IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2
     * Saturated channels participate in the shoulder decision directly.
     * Uniform scaling preserves hue/channel ratios.
     */
    /* IRIS_26491_EXTENDED_LINEAR_CHROMA_PRESERVING_HIGHLIGHT_COMPRESSION
     * Scene exposure arrived in extended-linear RGB from MotionV2DisplayExposure.
     * Compression is one scalar derived from the max-RGB/luma guide, so values
     * keep channel ratios until the final display-gamut fit. No per-channel 1.0
     * clamp is introduced here.
     */
    float mappedGuide=mapFinalSdrGuide(guide);
    vec3 mapped=rgb*(mappedGuide/guide);

    /* IRIS_26503_UPSTREAM_EXHAUSTION_OWNS_WHITE
     * 26502 already knows whether physical Bayer/Short-A evidence is genuinely
     * exhausted.  Do not create a second visible white-convergence decision from
     * render headroom position.  Uniform scalar compression preserves the hue of
     * recoverable warm walls/lamps; truly exhausted upstream-neutral pixels remain
     * neutral because equal channels stay equal under the same scalar.
     */
    return mapped;
}

/*
 * JPEG/sRGB cannot encode a channel above 1.0. If tone-mapped luminance is
 * valid but one saturated channel still exceeds the display gamut, shrink
 * chroma around the luminance axis instead of independently clipping R/G/B.
 */
vec3 fitDisplayGamut(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float peak=max3(rgb);
    if(peak<=1.0) return rgb;

    /*
     * IRIS_26438_HUE_PRESERVING_HIGHLIGHT_GAMUT
     *
     * The previous luminance-axis fit reduced chroma as bright colored
     * foliage approached display white. Uniform RGB scaling preserves channel
     * ratios/hue and trades only highlight luminance for display gamut.
     */
    /* IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT
     * Final display-gamut fit is one uniform RGB scale.  No independent channel
     * clipping and no overflow-driven white mix are allowed here.
     */
    return rgb/max(peak,1.0e-6);
}

/* IRIS_26630_ADAPTIVE_COLOR_V5
 * One final Display-P3 luminance/chroma authority for Motion presentation.  Luminance stays fixed;
 * only the pixel's own neutral-axis chroma vector is scaled.  Default per-lens saturation 1.0
 * enables at most +22% automatic recovery in reliable weak/moderate chroma. Deep black, near-neutral,
 * strong color and highlights taper to unity.  User saturation is also gated away from black/highlight
 * instability and is gamut-limited with one shared RGB chroma scale; no channel-wise clipping or
 * neighbor hue borrowing is introduced. Night receives saturation=1.0 from Java and therefore never
 * inherits the Motion per-lens saturation setting.
 */
float iris26630ChromaGainLimit(float y,float c){
    if(c>1.0e-8) return max(1.0,(1.0-y)/c);
    if(c<(-1.0e-8)) return max(1.0,y/(-c));
    return 1.0e6;
}

vec3 iris26630AdaptiveColorV5(vec3 rgb,float userSaturation){
    rgb=clamp(rgb,vec3(0.0),vec3(1.0));
    const vec3 displayP3Luma=vec3(0.22897456,0.69173852,0.07928691);
    float y=clamp(dot(rgb,displayP3Luma),0.0,1.0);
    vec3 chroma=rgb-vec3(y);
    float relativeChroma=length(chroma)/(y+0.05);

    float blackGate=smoothstep(0.018,0.050,y);
    float userHighlightGate=1.0-smoothstep(0.78,0.95,y);
    float autoHighlightGate=1.0-smoothstep(0.42,0.72,y);
    float neutralGate=smoothstep(0.030,0.090,relativeChroma);
    float strongColorTaper=1.0-smoothstep(0.30,0.70,relativeChroma);
    float autoGate=blackGate*autoHighlightGate*neutralGate*strongColorTaper;
    float userGate=blackGate*userHighlightGate;

    float sat=clamp(userSaturation,0.0,2.0);
    float requestedGain=1.0 + userGate*(sat-1.0)
            + 0.22*autoGate*min(sat,1.0);
    requestedGain=max(requestedGain,0.0);

    float limit=1.0e6;
    limit=min(limit,iris26630ChromaGainLimit(y,chroma.r));
    limit=min(limit,iris26630ChromaGainLimit(y,chroma.g));
    limit=min(limit,iris26630ChromaGainLimit(y,chroma.b));
    float appliedGain=min(requestedGain,limit);
    return clamp(vec3(y)+chroma*appliedGain,vec3(0.0),vec3(1.0));
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sourceSize=textureSize(InputBuffer,0);
    ivec2 sourceXY=xy;
    vec2 sourcePixel=vec2(sourceXY);
    vec3 linearSrgb;
    float zoom=max(irisOutputZoom,1.0);
    if(zoom<=1.00001) {
        /* IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL
         * Exact tested 26523 1x path remains unchanged.
         */
        if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;
        sourcePixel=vec2(sourceXY);
        linearSrgb=max(texelFetch(InputBuffer,sourceXY,0).rgb,vec3(0.0));
    } else {
        vec2 center=(vec2(sourceSize)-vec2(1.0))*0.5;
        sourcePixel=center+(vec2(xy)-center)/zoom;
        linearSrgb=max(iris26524BilinearInput(sourcePixel),vec3(0.0));
        sourceXY=ivec2(clamp(floor(sourcePixel+vec2(0.5)),
                            vec2(0.0),vec2(sourceSize-ivec2(1))));
    }

    /* IRIS_26559_REMOVE_SHARED_MICROCONTRAST_HALO
     * Do not apply the legacy 5x5 local-luma contrast multiplier here. Sabre remains
     * the detail authority; headroom mapping, exposure, gamut fit and zoom are unchanged.
     */
    if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0){
        vec3 sourceRgb=max(linearSrgb,vec3(0.0));
        float sourceY=max(luminance(sourceRgb),0.0);
        float sourcePeak=max3(sourceRgb);
        float sourceGuide=max(sourceY,sourcePeak);
        if(sourceGuide>1.0e-7){
            float globalMapped=iris26623MapMotionSdrFinalGuide(sourceGuide);
            vec2 toneSize=vec2(textureSize(iris26621LocalToneLog,0));
            vec2 uv=(sourcePixel+vec2(0.5))/max(toneSize,vec2(1.0));
            vec2 halfTexel=vec2(0.5)/max(toneSize,vec2(1.0));
            float localLog=texture(iris26621LocalToneLog,clamp(uv,halfTexel,vec2(1.0)-halfTexel)).r;
            float localMapped=exp2(clamp(localLog,-12.0,0.0));
            /* IRIS_26621_BLACK_FLOOR_GLOBAL_AUTHORITY
             * Exact black and deep shadows stay on the global curve; Local Laplacian fades in
             * only after rendered body separation is safely established. */
            float localStrength=smoothstep(0.030,0.100,globalMapped);
            float mappedGuide=mix(globalMapped,localMapped,localStrength);
            linearSrgb=sourceRgb*(mappedGuide/sourceGuide);
        }else{
            linearSrgb=sourceRgb;
        }
    }else{
        linearSrgb=mapExtendedLinearHeadroom(linearSrgb);
    }

    /* IRIS_26621_FINAL_DOMAIN_SINGLE_PRESENTATION
     * motionV2DisplayGain/outputExposureScale are consumed only by the shared global tone seed.
     * Local Laplacian supplies an absolute mapped luminance target, never a second exposure gain.
     */
    linearSrgb=fitDisplayGamut(linearSrgb);
    linearSrgb=iris26630AdaptiveColorV5(linearSrgb,iris26630MotionSaturation);

    Output=clamp(
            srgbEncode(linearSrgb),
            vec3(0.0),
            vec3(1.0));
}
