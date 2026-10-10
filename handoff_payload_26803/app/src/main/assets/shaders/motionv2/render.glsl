precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float sceneWhite;
uniform float outputExposureScale;
uniform float irisOutputZoom;
/* IRIS_26718_FINAL_SAMPLE_HIGH_ZOOM_DETAIL */
uniform sampler2D iris26718HighZoomDetail;
uniform int iris26718HighZoomDetailEnabled;
uniform vec2 iris26752PlanBDetailScale;
uniform vec2 iris26752PlanBDetailOrigin;
uniform int iris26592MotionHdrHandoff;
uniform float displayGain;
uniform sampler2D iris26621LocalToneLog;
uniform int iris26621LocalToneEnabled;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;
uniform float iris26630MotionSaturation;
uniform float iris26704BodyToneStrength;
/* IRIS_26799_CONNECTED_MASK_CORRECTION_INPUTS */
uniform sampler2D iris26799ConnectedMask;
uniform int iris26799ConnectedEnabled;
layout(std430, binding=1) buffer iris26799Stats {
    uint iris26799Counters[28];
};
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
    /* IRIS_26706_VISUAL_HIGHLIGHT_SPACING
     * 26705 proved that broad visually flattened highlights can cluster at nominal source white
     * even when hard sensor clipping is not the deciding condition. Preserve the exact mapping
     * through source guide 0.65, but for broad highlight pressure reserve more SDR code space above
     * nominal white and increase (rather than decrease) the C1 source-white slope. This remains one
     * global pointwise monotone scalar: no spatial mask, no semantic scene class, no SHORT ownership
     * change, and no channel-dependent operation. */
    float targetWhite=mix(0.945,0.895,pressure);
    float targetSlope=mix(0.360,0.620,pressure);
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

/* IRIS_26660_OBJECT_COLOR_GAMMA
 * IRIS_26671_UPPER_GAMMA_RELEASE
 * Visual authority: 26659 recovered some upper-range separation but its band-limited Hermite +
 * source-domain fade produced unnatural ground/foliage gamma patches and a visible contour.
 * Replace it with one analytic gamma family over the completed SDR guide. There is no spatial
 * sampling, no local threshold and no source-domain fade. A high-order luminance weight leaves
 * body tones nearly identity while progressively applying gamma to bright material tones. RGB is
 * still rescaled by one scalar below, so source chromaticity/hue is preserved (green foliage stays
 * green, grey cement stays neutral) instead of inventing color from neighboring pixels.
 * The same function is mirrored in gainmap.glsl; the HDR target remains exact successful-26658. */
float iris26660ObjectColorGamma(float mappedGuide){
    float y=max(mappedGuide,0.0);
    if(iris26592MotionHdrHandoff==0 || iris26653HighlightCompressionEnabled==0) return y;
    const float gammaValue=2.50;
    const float influencePower=6.0;
    const float whiteScale=0.90;
    float gammaOwned;
    if(y<=1.0){
        float w=pow(clamp(y,0.0,1.0),influencePower);
        float gammaMapped=whiteScale*pow(max(y,1.0e-8),gammaValue);
        gammaOwned=mix(y,gammaMapped,w);
    }else{
        const float endSlope=influencePower*(whiteScale-1.0)+whiteScale*gammaValue;
        gammaOwned=whiteScale+(y-1.0)*endSlope;
    }

    /* IRIS_26671_SINGLE_HIGHLIGHT_LUMINANCE_OWNER
     * 26670 proved that SHORT recovers real extended-linear highlight separation, while the
     * completed 26653 highlight tone and the later 26660 object-color gamma both compressed the
     * same upper display range. Preserve exact 26670 behavior through mapped linear guide 0.78.
     * Above that true-highlight boundary, release only the second gamma compression with a C1
     * smoothstep until mapped white, leaving the already-completed 26653 tone as the sole upper
     * luminance owner. No spatial sample, local mask, semantic scene class, or channel-dependent
     * operation is introduced; RGB remains uniformly scaled by the caller and hue stays unchanged.
     */
    const float releaseStart=0.78;
    if(y<=releaseStart) return gammaOwned;
    if(y>=1.0) return y;
    float t=clamp((y-releaseStart)/(1.0-releaseStart),0.0,1.0);
    float release=t*t*(3.0-2.0*t);
    return mix(gammaOwned,y,release);
}

/* IRIS_26704_RANGE_SEPARATED_BODY_TONE
 * Global pointwise toe lift only. True/near black remains protected, dark body/midtones can rise,
 * and mapped guide >=0.35 is exact identity so the existing recovered highlight owner is untouched.
 * One scalar is applied to RGB by the caller; no local/spatial/chroma synthesis occurs. */
float iris26704BodyToneGuide(float mappedGuide){
    float y=max(mappedGuide,0.0);
    float strength=clamp(iris26704BodyToneStrength,0.0,1.0);
    const float anchorGuide=0.35;
    if(strength<=1.0e-7 || y<=0.0 || y>=anchorGuide)return y;
    float gamma=1.0-0.28*strength;
    float toe=anchorGuide*pow(clamp(y/anchorGuide,0.0,1.0),gamma);
    float blackGate=smoothstep(0.004,0.018,y);
    return mix(y,toe,blackGate);
}

uniform float iris26792SdrBodyContrast;

/* IRIS_26770_MIDTONE_PRESENTATION_TRIM
 * 25% blend toward a darker quadratic midpoint curve. This is luminance-only: callers rescale RGB
 * by one scalar, so hue/channel ratios are unchanged. Deep shadows <=0.08 and upper/highlight
 * presentation >=0.78 are exact identity; no spatial sample or saturation control is involved. */
/* IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE
 * Strengthen only the finished SDR body's pointwise luminance separation. Exact black/deep-shadow
 * identity extends through 0.10 and upper/highlight identity remains from 0.78. The gain-map shader
 * carries this exact same function, so the decoded UHDR target remains owned by the frozen matched
 * HDR intent while the SDR denominator changes. */
float iris26770MidtonePresentationTrim(float mappedGuide){
    float y=max(mappedGuide,0.0);
    float low=smoothstep(0.10,0.24,y);
    float high=1.0-smoothstep(0.50,0.78,y);
    float w=clamp(low*high,0.0,1.0);
    return mix(y,y*y,clamp(iris26792SdrBodyContrast,0.0,0.35)*w);
}

float mapFinalSdrGuide(float sourceGuide) {
    if(iris26592MotionHdrHandoff!=0) {
        return iris26653MapMotionSdrFinalGuide(sourceGuide);
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
    mappedGuide=iris26704BodyToneGuide(mappedGuide);
    mappedGuide=iris26660ObjectColorGamma(mappedGuide);
    mappedGuide=iris26770MidtonePresentationTrim(mappedGuide);
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

/* IRIS_26638_TRUE_SHADOW_FLOOR_GUARD
 * Replace the broad 0..0.18 post-match darkener with a narrow true-shadow/noise-floor guard.
 * Exact black remains exact black and the original 0.72 deepest-floor protection is retained,
 * but signal-bearing body/shadow values are identity by 0.05 linear guide. Motion only. */
float iris26638ShadowFloorGuide(float guide){
    const float floorEnd=0.050;
    const float deepScale=0.72;
    float x=max(guide,0.0);
    if(x>=floorEnd) return x;
    float t=clamp(x/floorEnd,0.0,1.0);
    float smoothFactor=t*t*(3.0-2.0*t);
    return x*mix(deepScale,1.0,smoothFactor);
}
vec3 iris26638ApplyShadowFloorGuard(vec3 rgb){
    if(iris26592MotionHdrHandoff==0) return rgb;
    rgb=max(rgb,vec3(0.0));
    float guide=max(luminance(rgb),max3(rgb));
    if(guide<=1.0e-7) return rgb;
    float mapped=iris26638ShadowFloorGuide(guide);
    return rgb*(mapped/guide);
}

/* IRIS_26638_USER_SATURATION_ONLY
 * ACR3 is the automatic photographic color owner. Saturation 1.0 is exact identity here.
 * Only an explicit user deviation changes neutral-axis chroma, with the proven black/highlight
 * safety gates and shared gamut limit retained. No automatic +22% recovery or strong-color taper. */
float iris26638ChromaGainLimit(float y,float c){
    if(c>1.0e-8) return max(1.0,(1.0-y)/c);
    if(c<(-1.0e-8)) return max(1.0,y/(-c));
    return 1.0e6;
}
vec3 iris26638UserSaturation(vec3 rgb,float userSaturation){
    rgb=clamp(rgb,vec3(0.0),vec3(1.0));
    float sat=clamp(userSaturation,0.0,2.0);
    if(abs(sat-1.0)<=1.0e-7) return rgb;
    const vec3 displayP3Luma=vec3(0.22897456,0.69173852,0.07928691);
    float y=clamp(dot(rgb,displayP3Luma),0.0,1.0);
    vec3 chroma=rgb-vec3(y);
    float blackGate=smoothstep(0.018,0.050,y);
    float highlightGate=1.0-smoothstep(0.78,0.95,y);
    float requestedGain=max(1.0+blackGate*highlightGate*(sat-1.0),0.0);
    float limit=1.0e6;
    limit=min(limit,iris26638ChromaGainLimit(y,chroma.r));
    limit=min(limit,iris26638ChromaGainLimit(y,chroma.g));
    limit=min(limit,iris26638ChromaGainLimit(y,chroma.b));
    return clamp(vec3(y)+chroma*min(requestedGain,limit),vec3(0.0),vec3(1.0));
}

/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY
 * Motion-only, calibrated linear Display-P3, before presentation gain/tone.
 *
 * 26795 proved that bright-edge risk can be detected but also proved that an edge-following
 * false-color ribbon can validate itself when neighboring ribbon pixels are treated as material
 * support. 26796 moves the definitive decision after MotionV2ColorTransform/ACR3, where the
 * neutral axis is truly equal-channel Display-P3, and requires independent support several source
 * pixels INTO a material along the luminance-gradient normal. Tangent continuity never grants
 * permission. A correction additionally requires bipolar/opponent evidence across the normal;
 * therefore a genuine thin colored line with neutral surroundings is not desaturated merely for
 * being thin. The operation changes only neutral-axis chroma magnitude and preserves Display-P3
 * luminance exactly. All later default Motion owners are scalar/identity with respect to chroma.
 */
vec3 iris26796SampleCalibratedP3(vec2 sourcePixel){
    vec2 sz=vec2(textureSize(InputBuffer,0));
    vec2 hi=max(sz-vec2(1.0),vec2(0.0));
    vec2 p=clamp(sourcePixel,vec2(0.0),hi);
    return max(texture(InputBuffer,(p+vec2(0.5))/sz).rgb,vec3(0.0));
}
vec3 iris26796NormalizedChroma(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    return (rgb-vec3(y))/max(guide,0.04);
}
float iris26796SameHueProjection(vec3 rgb,vec3 dir){
    return max(dot(iris26796NormalizedChroma(rgb),dir),0.0);
}
float iris26796OpponentProjection(vec3 rgb,vec3 dir){
    return max(-dot(iris26796NormalizedChroma(rgb),dir),0.0);
}
vec3 iris26796CalibratedBrightContour(vec2 sourcePixel,vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    if(guide<=1.0e-6)return rgb;

    /* Derivatives must be evaluated before any data-dependent return so all fragments in a quad
     * participate in the gradient operation. */
    vec2 grad=vec2(dFdx(y),dFdy(y));
    float gradMag=length(grad);

    vec3 centerFrac=iris26796NormalizedChroma(rgb);
    float centerMagnitude=length(centerFrac);
    /* The observed chandelier/bulb defect is a low/moderate chroma reconstruction fringe. Strong
     * saturated material remains outside this automatic correction domain. */
    float chromaPresent=smoothstep(0.012,0.045,centerMagnitude);
    float strongMaterialProtect=1.0-smoothstep(0.30,0.48,centerMagnitude);
    float chromaRisk=chromaPresent*strongMaterialProtect;
    if(chromaRisk<=1.0e-5)return rgb;

    /* dFdx/dFdy are in output-pixel units. Compensate only the residual render zoom so this gate
     * measures the same source-space contour steepness when the final crop is enlarged. */
    float relativeGradient=(gradMag*max(irisOutputZoom,1.0))/max(guide,0.03);
    float edgeRisk=smoothstep(0.045,0.18,relativeGradient);
    if(edgeRisk<=1.0e-5)return rgb;

    /* Use the exact Motion final-tone predictor so a source value that will become visually bright
     * under a 3x-6x presentation request is classified as bright BEFORE that gain is rendered.
     * This more expensive predictor runs only after cheap chroma/edge rejection. */
    float projectedGuide=iris26653MapMotionSdrFinalGuide(guide);
    float brightRisk=smoothstep(0.70,0.88,projectedGuide);
    if(brightRisk<=1.0e-5)return rgb;

    vec2 normal=grad/max(gradMag,1.0e-7);
    vec3 dir=centerFrac/max(centerMagnitude,1.0e-7);

    /* Immediate samples can expose the complementary lobe of a CFA/reconstruction fringe. */
    vec3 nearPos=iris26796SampleCalibratedP3(sourcePixel+normal);
    vec3 nearNeg=iris26796SampleCalibratedP3(sourcePixel-normal);
    float opponent=max(iris26796OpponentProjection(nearPos,dir),
                       iris26796OpponentProjection(nearNeg,dir));
    float opponentRatio=opponent/max(centerMagnitude,1.0e-6);
    float bipolarEvidence=smoothstep(0.14,0.52,opponentRatio);
    if(bipolarEvidence<=1.0e-5)return rgb;

    /* Independent material evidence must survive at both 3- and 5-pixel depths on one side.
     * A one/two-pixel fringe therefore cannot authenticate itself. This samples only the edge
     * normal; tangent/contour continuity is intentionally excluded from permission. */
    vec3 pos3=iris26796SampleCalibratedP3(sourcePixel+normal*3.0);
    vec3 pos5=iris26796SampleCalibratedP3(sourcePixel+normal*5.0);
    vec3 neg3=iris26796SampleCalibratedP3(sourcePixel-normal*3.0);
    vec3 neg5=iris26796SampleCalibratedP3(sourcePixel-normal*5.0);
    float posDepth=min(iris26796SameHueProjection(pos3,dir),
                       iris26796SameHueProjection(pos5,dir));
    float negDepth=min(iris26796SameHueProjection(neg3,dir),
                       iris26796SameHueProjection(neg5,dir));
    float materialMagnitude=max(posDepth,negDepth);
    float materialRatio=materialMagnitude/max(centerMagnitude,1.0e-6);
    float materialSupport=smoothstep(0.24,0.68,materialRatio);
    float unsupported=1.0-materialSupport;

    float correction=clamp(brightRisk*edgeRisk*chromaRisk*bipolarEvidence*unsupported,0.0,1.0);
    if(correction<=1.0e-5)return rgb;

    /* Keep at least independently supported same-hue material chroma. At full-confidence bipolar
     * false color, unsupported residue is limited to 8% rather than hard-zeroed, avoiding a seam. */
    float supportedMagnitude=max(materialMagnitude,centerMagnitude*0.08);
    float targetMagnitude=mix(centerMagnitude,min(centerMagnitude,supportedMagnitude),correction);
    float scale=targetMagnitude/max(centerMagnitude,1.0e-7);
    vec3 corrected=vec3(y)+(rgb-vec3(y))*scale;
    /* Weighted Display-P3 luminance is algebraically invariant because rgb-y has zero weighted Y. */
    return max(corrected,vec3(0.0));
}

/* IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY
 * Motion-only high-confidence refinement of the successful 26796 calibrated-domain owner.
 *
 * 26796 remains the conservative fallback for every ambiguous pixel. 26797 adds a strong tier for
 * the residual defect proven by the 26796 chandelier/bulb comparison: a one-to-three-source-pixel
 * zipper/zig-zag chroma ribbon whose hue may step among magenta/violet/blue/cyan/green/yellow while
 * following an otherwise ordinary very-bright luminance contour. The strong tier never keys on a
 * named hue. It requires absent same-hue material support at depths 3/5 plus either wider opponent/
 * hue-turn evidence across +/-3 pixels of the edge normal or an edge-only neutral-material ribbon
 * whose tangent hue is not coherently stable. Tangent continuity is protection only; it can never
 * create correction permission. The target comes from independently sampled material interiors,
 * not from the artifact pixel, and weighted Display-P3 luminance remains invariant.
 */
float iris26797ChromaMagnitude(vec3 rgb){
    return length(iris26796NormalizedChroma(rgb));
}
float iris26797HueTurnEvidence(vec3 rgb,vec3 dir,float centerMagnitude){
    vec3 c=iris26796NormalizedChroma(rgb);
    float m=length(c);
    if(m<=1.0e-7)return 0.0;
    float relevance=smoothstep(0.16,0.44,m/max(centerMagnitude,1.0e-6));
    float alignment=clamp(dot(c/m,dir),-1.0,1.0);
    return relevance*smoothstep(0.08,0.46,1.0-alignment);
}
vec3 iris26797MaterialTargetChroma(vec3 negMaterial,vec3 posMaterial,float centerY,float centerGuide,float centerMagnitude){
    float yn=max(luminance(negMaterial),0.0);
    float yp=max(luminance(posMaterial),0.0);
    float t=0.5;
    if(abs(yp-yn)>1.0e-6)t=clamp((centerY-yn)/(yp-yn),0.0,1.0);
    vec3 predicted=mix(negMaterial,posMaterial,t);
    float predictedY=max(luminance(predicted),0.0);
    vec3 target=predicted-vec3(predictedY);
    float normalizedMagnitude=length(target)/max(centerGuide,0.04);
    if(normalizedMagnitude>centerMagnitude && normalizedMagnitude>1.0e-7){
        target*=centerMagnitude/normalizedMagnitude;
    }
    /* Preserve center luminance and prevent the material target from driving any channel negative.
     * There is intentionally no upper-one clamp in extended-linear Display-P3. */
    float lowerScale=1.0;
    if(target.r<(-1.0e-7))lowerScale=min(lowerScale,centerY/(-target.r));
    if(target.g<(-1.0e-7))lowerScale=min(lowerScale,centerY/(-target.g));
    if(target.b<(-1.0e-7))lowerScale=min(lowerScale,centerY/(-target.b));
    return target*clamp(lowerScale,0.0,1.0);
}
vec3 iris26797CalibratedZipperContour(vec2 sourcePixel,vec3 rgb){
    /* Always evaluate the proven 26796 fallback uniformly before any 26797 divergence so its
     * derivative operation remains legal on every fragment quad. */
    vec3 fallback26796=iris26796CalibratedBrightContour(sourcePixel,rgb);
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    if(guide<=1.0e-6)return fallback26796;

    vec2 grad=vec2(dFdx(y),dFdy(y));
    float gradMag=length(grad);
    vec3 centerFrac=iris26796NormalizedChroma(rgb);
    float centerMagnitude=length(centerFrac);
    float chromaPresent=smoothstep(0.010,0.036,centerMagnitude);
    float strongMaterialProtect=1.0-smoothstep(0.30,0.48,centerMagnitude);
    float chromaRisk=chromaPresent*strongMaterialProtect;
    if(chromaRisk<=1.0e-5 || gradMag<=1.0e-7)return fallback26796;

    float relativeGradient=(gradMag*max(irisOutputZoom,1.0))/max(guide,0.03);
    float edgeRisk=smoothstep(0.040,0.15,relativeGradient);
    if(edgeRisk<=1.0e-5)return fallback26796;
    float projectedGuide=iris26653MapMotionSdrFinalGuide(guide);
    float brightRisk=smoothstep(0.68,0.86,projectedGuide);
    if(brightRisk<=1.0e-5)return fallback26796;

    vec2 normal=grad/gradMag;
    vec2 tangent=vec2(-normal.y,normal.x);
    vec3 dir=centerFrac/max(centerMagnitude,1.0e-7);

    vec3 pos1=iris26796SampleCalibratedP3(sourcePixel+normal);
    vec3 pos2=iris26796SampleCalibratedP3(sourcePixel+normal*2.0);
    vec3 pos3=iris26796SampleCalibratedP3(sourcePixel+normal*3.0);
    vec3 pos5=iris26796SampleCalibratedP3(sourcePixel+normal*5.0);
    vec3 neg1=iris26796SampleCalibratedP3(sourcePixel-normal);
    vec3 neg2=iris26796SampleCalibratedP3(sourcePixel-normal*2.0);
    vec3 neg3=iris26796SampleCalibratedP3(sourcePixel-normal*3.0);
    vec3 neg5=iris26796SampleCalibratedP3(sourcePixel-normal*5.0);

    /* Real material color must survive at both depth 3 and depth 5 on at least one side. */
    float posDepth=min(iris26796SameHueProjection(pos3,dir),iris26796SameHueProjection(pos5,dir));
    float negDepth=min(iris26796SameHueProjection(neg3,dir),iris26796SameHueProjection(neg5,dir));
    float materialMagnitude=max(posDepth,negDepth);
    float materialRatio=materialMagnitude/max(centerMagnitude,1.0e-6);
    float materialSupport=smoothstep(0.20,0.60,materialRatio);
    float unsupported=1.0-materialSupport;
    if(unsupported<=0.10)return fallback26796;

    /* Wider normal-band evidence catches the observed magenta/violet/blue zipper even when the
     * complementary lobe is displaced by two or three pixels instead of immediately adjacent. */
    float opponent=max(max(iris26796OpponentProjection(pos1,dir),iris26796OpponentProjection(neg1,dir)),
                       max(max(iris26796OpponentProjection(pos2,dir),iris26796OpponentProjection(neg2,dir)),
                           max(iris26796OpponentProjection(pos3,dir),iris26796OpponentProjection(neg3,dir))));
    float opponentRatio=opponent/max(centerMagnitude,1.0e-6);
    float wideOpponent=smoothstep(0.08,0.34,opponentRatio);
    float hueTurn=max(max(iris26797HueTurnEvidence(pos1,dir,centerMagnitude),iris26797HueTurnEvidence(neg1,dir,centerMagnitude)),
                      max(max(iris26797HueTurnEvidence(pos2,dir,centerMagnitude),iris26797HueTurnEvidence(neg2,dir,centerMagnitude)),
                          max(iris26797HueTurnEvidence(pos3,dir,centerMagnitude),iris26797HueTurnEvidence(neg3,dir,centerMagnitude))));
    float normalPhaseEvidence=max(wideOpponent,hueTurn);

    /* The second proven residual is neutral -> colored -> neutral along a monotonic bright edge.
     * It has no immediate opponent. Protect a genuinely thin colored structure when the same hue
     * remains coherent along the tangent; zipper/phase color instead loses that coherence. */
    vec3 tanPos2=iris26796SampleCalibratedP3(sourcePixel+tangent*2.0);
    vec3 tanNeg2=iris26796SampleCalibratedP3(sourcePixel-tangent*2.0);
    float tangentSame=min(iris26796SameHueProjection(tanPos2,dir),iris26796SameHueProjection(tanNeg2,dir));
    float tangentRatio=tangentSame/max(centerMagnitude,1.0e-6);
    float tangentCoherent=smoothstep(0.52,0.82,tangentRatio);
    float tangentHueTurn=max(iris26797HueTurnEvidence(tanPos2,dir,centerMagnitude),
                             iris26797HueTurnEvidence(tanNeg2,dir,centerMagnitude));
    float phaseEvidence=max(normalPhaseEvidence,tangentHueTurn);

    vec3 posMaterial=0.5*(pos3+pos5);
    vec3 negMaterial=0.5*(neg3+neg5);
    float materialSame=max(iris26796SameHueProjection(posMaterial,dir),iris26796SameHueProjection(negMaterial,dir));
    float materialSameRatio=materialSame/max(centerMagnitude,1.0e-6);
    float interiorHueAbsent=1.0-smoothstep(0.16,0.48,materialSameRatio);

    float yPos3=max(luminance(pos3),0.0);
    float yNeg3=max(luminance(neg3),0.0);
    float rangeLo=min(yPos3,yNeg3);
    float rangeHi=max(yPos3,yNeg3);
    float outside=max(max(rangeLo-y,y-rangeHi),0.0)/max(guide,0.03);
    float withinMaterialEdge=1.0-smoothstep(0.07,0.30,outside);
    float materialLumaSpan=abs(yPos3-yNeg3)/max(guide,0.03);
    float realEdgeSpan=smoothstep(0.045,0.16,materialLumaSpan);
    float ribbonEvidence=interiorHueAbsent*withinMaterialEdge*realEdgeSpan*(1.0-tangentCoherent);

    /* Strong tier accepts either displaced multi-hue/opponent phase evidence or the one-sided
     * neutral-material ribbon topology. No named hue is privileged. */
    float topologyEvidence=max(phaseEvidence,ribbonEvidence);
    float baseConfidence=min(brightRisk,min(edgeRisk,chromaRisk));
    float confidence=min(baseConfidence,min(unsupported,topologyEvidence));
    float strongCorrection=smoothstep(0.22,0.50,confidence);
    if(strongCorrection<=1.0e-5)return fallback26796;

    vec3 targetChroma=iris26797MaterialTargetChroma(negMaterial,posMaterial,y,guide,centerMagnitude);
    vec3 strongCorrected=vec3(y)+targetChroma;
    /* Both fallback26796 and strongCorrected have exactly the original weighted Display-P3 Y. */
    return mix(fallback26796,strongCorrected,strongCorrection);
}

/* IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_VALIDITY
 * Motion-only refinement of the successful 26797 calibrated-domain owner.
 *
 * The 26797 residual audit proved two classifier failures on the real chandelier pixels:
 * (1) a false CFA/reconstruction fringe can be >0.82 tangent-coherent even when both material
 * interiors are neutral, so tangent coherence cannot be an unconditional real-color veto; and
 * (2) the chroma lobe can sit one-to-three source pixels away from the strongest luminance-gradient
 * pixel, so requiring every artifact pixel to independently satisfy the peak edge gate leaves
 * disconnected holes. 26798 keeps 26797 byte-identical as the conservative fallback, uses its
 * phase/opponent topology as STRONG SEEDS, expands edge membership to the local normal band, and
 * promotes only weak unsupported candidates connected along the same contour to a nearby seed.
 * A genuinely thin colored structure with no false-color seed remains protected. The correction
 * remains after ColorTransform/ACR3 and before presentation/tone, is hue-agnostic, and preserves
 * calibrated Display-P3 luminance exactly.
 */
layout(std430, binding=0) buffer iris26798Stats {
    uint iris26798Counters[12];
};

float iris26798LumaAt(vec2 p){
    return max(luminance(iris26796SampleCalibratedP3(p)),0.0);
}
float iris26798BandEdgeRisk(vec2 p,vec2 normal,float guide,float centerRelativeGradient){
    float p1=iris26798LumaAt(p+normal);
    float n1=iris26798LumaAt(p-normal);
    float p2=iris26798LumaAt(p+normal*2.0);
    float n2=iris26798LumaAt(p-normal*2.0);
    float p3=iris26798LumaAt(p+normal*3.0);
    float n3=iris26798LumaAt(p-normal*3.0);
    float z=max(irisOutputZoom,1.0);
    float bandGradient=max(abs(p1-n1)*0.5,
                       max(abs(p2-n2)*0.25,abs(p3-n3)/6.0))*z/max(guide,0.03);
    float centerRisk=smoothstep(0.040,0.15,centerRelativeGradient);
    float bandRisk=smoothstep(0.032,0.115,bandGradient);
    return max(centerRisk,bandRisk);
}
float iris26798SeedConfidenceAt(vec2 p,vec2 normal){
    vec3 c=iris26796SampleCalibratedP3(p);
    float y=max(luminance(c),0.0);
    float guide=max(y,max3(c));
    if(guide<=1.0e-6)return 0.0;
    vec3 frac=iris26796NormalizedChroma(c);
    float mag=length(frac);
    float chromaRisk=smoothstep(0.010,0.036,mag)*(1.0-smoothstep(0.30,0.48,mag));
    if(chromaRisk<=1.0e-5)return 0.0;
    float projected=iris26653MapMotionSdrFinalGuide(guide);
    float brightRisk=smoothstep(0.68,0.86,projected);
    if(brightRisk<=1.0e-5)return 0.0;
    vec3 dir=frac/max(mag,1.0e-7);
    vec3 pos1=iris26796SampleCalibratedP3(p+normal);
    vec3 pos2=iris26796SampleCalibratedP3(p+normal*2.0);
    vec3 pos3=iris26796SampleCalibratedP3(p+normal*3.0);
    vec3 pos5=iris26796SampleCalibratedP3(p+normal*5.0);
    vec3 neg1=iris26796SampleCalibratedP3(p-normal);
    vec3 neg2=iris26796SampleCalibratedP3(p-normal*2.0);
    vec3 neg3=iris26796SampleCalibratedP3(p-normal*3.0);
    vec3 neg5=iris26796SampleCalibratedP3(p-normal*5.0);
    float edgeBand=max(abs(luminance(pos1)-luminance(neg1))*0.5,
                   max(abs(luminance(pos2)-luminance(neg2))*0.25,
                       abs(luminance(pos3)-luminance(neg3))/6.0));
    float edgeRisk=smoothstep(0.032,0.115,
            edgeBand*max(irisOutputZoom,1.0)/max(guide,0.03));
    if(edgeRisk<=1.0e-5)return 0.0;
    float posDepth=min(iris26796SameHueProjection(pos3,dir),iris26796SameHueProjection(pos5,dir));
    float negDepth=min(iris26796SameHueProjection(neg3,dir),iris26796SameHueProjection(neg5,dir));
    float materialRatio=max(posDepth,negDepth)/max(mag,1.0e-6);
    float unsupported=1.0-smoothstep(0.20,0.60,materialRatio);
    if(unsupported<=0.10)return 0.0;
    float opponent=max(max(iris26796OpponentProjection(pos1,dir),iris26796OpponentProjection(neg1,dir)),
                       max(max(iris26796OpponentProjection(pos2,dir),iris26796OpponentProjection(neg2,dir)),
                           max(iris26796OpponentProjection(pos3,dir),iris26796OpponentProjection(neg3,dir))));
    float wideOpponent=smoothstep(0.08,0.34,opponent/max(mag,1.0e-6));
    float hueTurn=max(max(iris26797HueTurnEvidence(pos1,dir,mag),iris26797HueTurnEvidence(neg1,dir,mag)),
                      max(max(iris26797HueTurnEvidence(pos2,dir,mag),iris26797HueTurnEvidence(neg2,dir,mag)),
                          max(iris26797HueTurnEvidence(pos3,dir,mag),iris26797HueTurnEvidence(neg3,dir,mag))));
    float phaseEvidence=max(wideOpponent,hueTurn);
    return min(brightRisk,min(edgeRisk,min(chromaRisk,min(unsupported,phaseEvidence))));
}
void iris26798TelemetryMagnitude(uint preIndex,uint postIndex,uint maxPreIndex,uint maxPostIndex,
                                float preMagnitude,float postMagnitude){
    uint preQ=uint(clamp(preMagnitude,0.0,4.0)*4096.0+0.5);
    uint postQ=uint(clamp(postMagnitude,0.0,4.0)*4096.0+0.5);
    uint preMaxQ=uint(clamp(preMagnitude,0.0,4.0)*16384.0+0.5);
    uint postMaxQ=uint(clamp(postMagnitude,0.0,4.0)*16384.0+0.5);
    atomicAdd(iris26798Counters[preIndex],preQ);
    atomicAdd(iris26798Counters[postIndex],postQ);
    atomicMax(iris26798Counters[maxPreIndex],preMaxQ);
    atomicMax(iris26798Counters[maxPostIndex],postMaxQ);
}
vec3 iris26798CalibratedConnectedZipper(vec2 sourcePixel,vec3 rgb){
    /* Keep the successful 26797 owner as an exact conservative fallback. Its derivative path must
     * execute uniformly before 26798 starts any data-dependent divergence. */
    vec3 fallback26797=iris26797CalibratedZipperContour(sourcePixel,rgb);
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float guide=max(y,max3(rgb));
    vec2 grad=vec2(dFdx(y),dFdy(y));
    float gradMag=length(grad);
    if(guide<=1.0e-6 || gradMag<=1.0e-7)return fallback26797;

    vec3 centerFrac=iris26796NormalizedChroma(rgb);
    float centerMagnitude=length(centerFrac);
    float chromaRisk=smoothstep(0.010,0.036,centerMagnitude)
                    *(1.0-smoothstep(0.30,0.48,centerMagnitude));
    if(chromaRisk<=1.0e-5)return fallback26797;
    float projectedGuide=iris26653MapMotionSdrFinalGuide(guide);
    float brightRisk=smoothstep(0.68,0.86,projectedGuide);
    if(brightRisk<=1.0e-5)return fallback26797;

    vec2 normal=grad/gradMag;
    vec2 tangent=vec2(-normal.y,normal.x);
    float relativeGradient=(gradMag*max(irisOutputZoom,1.0))/max(guide,0.03);
    float edgeBandRisk=iris26798BandEdgeRisk(sourcePixel,normal,guide,relativeGradient);
    if(edgeBandRisk<=1.0e-5){
        atomicAdd(iris26798Counters[6],1u);
        return fallback26797;
    }
    atomicAdd(iris26798Counters[0],1u);

    vec3 dir=centerFrac/max(centerMagnitude,1.0e-7);
    vec3 pos1=iris26796SampleCalibratedP3(sourcePixel+normal);
    vec3 pos2=iris26796SampleCalibratedP3(sourcePixel+normal*2.0);
    vec3 pos3=iris26796SampleCalibratedP3(sourcePixel+normal*3.0);
    vec3 pos5=iris26796SampleCalibratedP3(sourcePixel+normal*5.0);
    vec3 neg1=iris26796SampleCalibratedP3(sourcePixel-normal);
    vec3 neg2=iris26796SampleCalibratedP3(sourcePixel-normal*2.0);
    vec3 neg3=iris26796SampleCalibratedP3(sourcePixel-normal*3.0);
    vec3 neg5=iris26796SampleCalibratedP3(sourcePixel-normal*5.0);

    float posDepth=min(iris26796SameHueProjection(pos3,dir),iris26796SameHueProjection(pos5,dir));
    float negDepth=min(iris26796SameHueProjection(neg3,dir),iris26796SameHueProjection(neg5,dir));
    float materialMagnitude=max(posDepth,negDepth);
    float materialRatio=materialMagnitude/max(centerMagnitude,1.0e-6);
    float materialSupport=smoothstep(0.20,0.60,materialRatio);
    float unsupported=1.0-materialSupport;
    if(unsupported<=0.10){
        atomicAdd(iris26798Counters[4],1u);
        return fallback26797;
    }

    vec3 posMaterial=0.5*(pos3+pos5);
    vec3 negMaterial=0.5*(neg3+neg5);
    float materialSame=max(iris26796SameHueProjection(posMaterial,dir),iris26796SameHueProjection(negMaterial,dir));
    float interiorHueAbsent=1.0-smoothstep(0.16,0.48,materialSame/max(centerMagnitude,1.0e-6));
    float yPos3=max(luminance(pos3),0.0);
    float yNeg3=max(luminance(neg3),0.0);
    float rangeLo=min(yPos3,yNeg3);
    float rangeHi=max(yPos3,yNeg3);
    float outside=max(max(rangeLo-y,y-rangeHi),0.0)/max(guide,0.03);
    float withinMaterialEdge=1.0-smoothstep(0.07,0.30,outside);
    float materialLumaSpan=abs(yPos3-yNeg3)/max(guide,0.03);
    float realEdgeSpan=smoothstep(0.045,0.16,materialLumaSpan);
    float ribbonEvidence=interiorHueAbsent*withinMaterialEdge*realEdgeSpan;
    float weakConfidence=min(brightRisk,min(edgeBandRisk,min(chromaRisk,min(unsupported,ribbonEvidence))));
    float weakCandidate=smoothstep(0.10,0.30,weakConfidence);
    if(weakCandidate<=1.0e-5)return fallback26797;
    atomicAdd(iris26798Counters[2],1u);

    /* 26797 phase/opponent topology becomes the strong seed. Tangent coherence is deliberately
     * absent here: the real residual proved that a false fringe can be tangent-coherent. */
    float centerSeedConfidence=iris26798SeedConfidenceAt(sourcePixel,normal);
    float centerSeed=smoothstep(0.18,0.42,centerSeedConfidence);
    if(centerSeed>1.0e-5)atomicAdd(iris26798Counters[1],1u);

    float neighborSeed=0.0;
    if(centerSeed<0.999){
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel+tangent,normal)));
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel-tangent,normal)));
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel+tangent*2.0,normal)));
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel-tangent*2.0,normal)));
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel+tangent*3.0,normal)));
        neighborSeed=max(neighborSeed,smoothstep(0.18,0.42,
                iris26798SeedConfidenceAt(sourcePixel-tangent*3.0,normal)));
    }
    float connectedSeed=max(centerSeed,neighborSeed);
    if(connectedSeed<=1.0e-5){
        vec3 tanPos2=iris26796SampleCalibratedP3(sourcePixel+tangent*2.0);
        vec3 tanNeg2=iris26796SampleCalibratedP3(sourcePixel-tangent*2.0);
        float tangentSame=min(iris26796SameHueProjection(tanPos2,dir),
                              iris26796SameHueProjection(tanNeg2,dir));
        float tangentCoherent=smoothstep(0.52,0.82,tangentSame/max(centerMagnitude,1.0e-6));
        if(tangentCoherent>0.5)atomicAdd(iris26798Counters[5],1u);
        return fallback26797;
    }

    float promoted=min(weakCandidate,connectedSeed);
    float hysteresisCorrection=max(centerSeed,smoothstep(0.06,0.24,promoted));
    hysteresisCorrection=clamp(hysteresisCorrection,0.0,1.0);
    if(hysteresisCorrection<=1.0e-5)return fallback26797;
    if(centerSeed<=1.0e-5 && neighborSeed>1.0e-5)atomicAdd(iris26798Counters[3],1u);

    vec3 targetChroma=iris26797MaterialTargetChroma(negMaterial,posMaterial,y,guide,centerMagnitude);
    vec3 strongCorrected=vec3(y)+targetChroma;
    vec3 corrected=mix(fallback26797,strongCorrected,hysteresisCorrection);
    float postMagnitude=length(corrected-vec3(y))/max(guide,0.04);
    atomicAdd(iris26798Counters[7],1u);
    iris26798TelemetryMagnitude(8u,9u,10u,11u,centerMagnitude,postMagnitude);
    return corrected;
}

/* IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_CORRECTION
 * Classification and recursive connectivity are produced in separate R8 passes. This final stage
 * changes only pixels in the proven connected mask. The target is a robust two-dimensional outer
 * material estimate; same-hue self-residue is capped so a false ribbon cannot validate itself.
 * Every accumulated sample chroma is defined around its own Display-P3 luminance, therefore the
 * target chroma and the corrected result preserve weighted Display-P3 luminance exactly.
 */
void iris26799AccumulateMaterial(vec2 p,float centerY,float guide,inout vec3 sum,inout float wsum){
    vec3 s=iris26796SampleCalibratedP3(p);
    float sy=max(luminance(s),0.0);
    vec3 c=s-vec3(sy);
    float sg=max(sy,max3(s));
    float cm=length(c)/max(sg,0.04);
    float lumaDelta=abs(sy-centerY)/max(guide,0.03);
    float lumaWeight=1.0-smoothstep(0.08,0.34,lumaDelta);
    float chromaWeight=0.18+0.82*(1.0-smoothstep(0.08,0.30,cm));
    float w=lumaWeight*chromaWeight;
    sum+=c*w;wsum+=w;
}
vec3 iris26799RobustMaterialTarget(vec2 p,float centerY,float guide,vec3 centerChroma){
    vec3 sum=vec3(0.0);float wsum=0.0;
    iris26799AccumulateMaterial(p+vec2(3.0,0.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(-3.0,0.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(0.0,3.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(0.0,-3.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(4.0,0.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(-4.0,0.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(0.0,4.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(0.0,-4.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(3.0,3.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(-3.0,3.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(3.0,-3.0),centerY,guide,sum,wsum);
    iris26799AccumulateMaterial(p+vec2(-3.0,-3.0),centerY,guide,sum,wsum);
    vec3 target=wsum>1.0e-6?sum/wsum:vec3(0.0);
    float centerMag=length(centerChroma);
    if(centerMag>1.0e-7){
        vec3 dir=centerChroma/centerMag;
        float same=max(dot(target,dir),0.0);
        float sameLimit=centerMag*0.20;
        if(same>sameLimit)target-=dir*(same-sameLimit);
        float tm=length(target);
        if(tm>centerMag)target*=centerMag/max(tm,1.0e-7);
    }
    float scale=1.0;
    if(target.r<0.0)scale=min(scale,centerY/max(-target.r,1.0e-7));
    if(target.g<0.0)scale=min(scale,centerY/max(-target.g,1.0e-7));
    if(target.b<0.0)scale=min(scale,centerY/max(-target.b,1.0e-7));
    return target*clamp(scale,0.0,1.0);
}
/* IRIS_26803_NEUTRAL_PARENT_CORRECTION_TARGET
 * Direct 0.92 seeds were admitted only from a strong far achromatic-parent proof. Reconstruct the
 * same finite-difference normal here and take the 4..6 px two-dimensional patch on the brighter
 * side. This target is intentionally separate from the legacy isotropic 26799 material target.
 * It preserves Display-P3 luminance exactly and cannot add the center false hue back into chrome.
 */
void iris26803ParentPatch(vec2 p,vec2 n,vec2 t,float side,
        out float meanLuma,out vec3 meanNormChroma){
    float lsum=0.0;vec3 csum=vec3(0.0);
    for(int dn=-1;dn<=1;dn++){
        for(int dt=-1;dt<=1;dt++){
            vec2 q=p+n*(side*(5.0+float(dn)))+t*(1.5*float(dt));
            vec3 s=iris26796SampleCalibratedP3(q);
            lsum+=max(luminance(s),0.0);
            csum+=iris26796NormalizedChroma(s);
        }
    }
    meanLuma=lsum/9.0;meanNormChroma=csum/9.0;
}
vec3 iris26803NeutralParentTarget(vec2 p,float centerY,float guide,vec3 centerChroma){
    vec2 lg=vec2(iris26798LumaAt(p+vec2(1.0,0.0))-iris26798LumaAt(p-vec2(1.0,0.0)),
                 iris26798LumaAt(p+vec2(0.0,1.0))-iris26798LumaAt(p-vec2(0.0,1.0)));
    vec2 cg=vec2(length(iris26796NormalizedChroma(iris26796SampleCalibratedP3(p+vec2(1.0,0.0))))
                    -length(iris26796NormalizedChroma(iris26796SampleCalibratedP3(p-vec2(1.0,0.0)))),
                 length(iris26796NormalizedChroma(iris26796SampleCalibratedP3(p+vec2(0.0,1.0))))
                    -length(iris26796NormalizedChroma(iris26796SampleCalibratedP3(p-vec2(0.0,1.0)))));
    vec2 axis=length(lg)>1.0e-6?lg:(length(cg)>1.0e-6?cg:vec2(1.0,0.0));
    vec2 n=normalize(axis);vec2 t=vec2(-n.y,n.x);
    float posL=0.0;float negL=0.0;vec3 posC=vec3(0.0);vec3 negC=vec3(0.0);
    iris26803ParentPatch(p,n,t,1.0,posL,posC);
    iris26803ParentPatch(p,n,t,-1.0,negL,negC);
    vec3 parentNorm=posL>=negL?posC:negC;
    float pm=length(parentNorm);
    if(pm<0.022){parentNorm=vec3(0.0);pm=0.0;}
    else if(pm>0.045){parentNorm*=0.045/max(pm,1.0e-7);pm=0.045;}
    float centerMag=length(centerChroma);
    if(centerMag>1.0e-7&&pm>1.0e-7){
        vec3 dir=centerChroma/centerMag;
        float same=max(dot(parentNorm,dir),0.0);
        float centerNormMag=centerMag/max(guide,0.04);
        float sameLimit=min(0.010,centerNormMag*0.04);
        if(same>sameLimit)parentNorm-=dir*(same-sameLimit);
    }
    vec3 target=parentNorm*max(guide,0.04);
    float scale=1.0;
    if(target.r<0.0)scale=min(scale,centerY/max(-target.r,1.0e-7));
    if(target.g<0.0)scale=min(scale,centerY/max(-target.g,1.0e-7));
    if(target.b<0.0)scale=min(scale,centerY/max(-target.b,1.0e-7));
    return target*clamp(scale,0.0,1.0);
}

void iris26799TelemetryMagnitude(float preMag,float postMag){
    uint preQ=uint(clamp(preMag,0.0,4.0)*4096.0+0.5);
    uint postQ=uint(clamp(postMag,0.0,4.0)*4096.0+0.5);
    uint preMaxQ=uint(clamp(preMag,0.0,4.0)*16384.0+0.5);
    uint postMaxQ=uint(clamp(postMag,0.0,4.0)*16384.0+0.5);
    atomicAdd(iris26799Counters[15],preQ);atomicAdd(iris26799Counters[16],postQ);
    atomicMax(iris26799Counters[17],preMaxQ);atomicMax(iris26799Counters[18],postMaxQ);
}
vec3 iris26799ApplyConnectedCorrection(ivec2 outputXY,vec2 sourcePixel,vec3 rgb){
    if(iris26799ConnectedEnabled==0)return rgb;
    ivec2 msz=textureSize(iris26799ConnectedMask,0);
    ivec2 mp=clamp(outputXY,ivec2(0),msz-ivec2(1));
    float connected=texelFetch(iris26799ConnectedMask,mp,0).r;
    if(connected<0.75)return rgb;
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);float guide=max(y,max3(rgb));
    vec3 centerChroma=rgb-vec3(y);
    float preMag=length(centerChroma)/max(guide,0.04);
    if(preMag<=1.0e-7)return rgb;
    bool iris26803NeutralParentDirect=connected>=0.90&&connected<=0.94;
    vec3 target=iris26803NeutralParentDirect
            ?iris26803NeutralParentTarget(sourcePixel,y,guide,centerChroma)
            :iris26799RobustMaterialTarget(sourcePixel,y,guide,centerChroma);
    vec3 corrected=vec3(y)+target;
    float postGuide=max(y,max3(corrected));
    float postMag=length(target)/max(postGuide,0.04);
    atomicAdd(iris26799Counters[14],1u);
    if(preMag>=0.26){
        atomicAdd(iris26799Counters[25],1u);
        atomicMax(iris26799Counters[26],uint(clamp(postMag,0.0,4.0)*16384.0+0.5));
    }
    iris26799TelemetryMagnitude(preMag,postMag);
    return corrected;
}

/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE
 * The sidecar is a centered subset of the global true-2x sensor lattice. It carries only signed
 * log2 luminance detail; zero and out-of-bounds are exact no-ops.
 */
float iris26718HighZoomLogDetail(vec2 sourcePixel){
    if(iris26718HighZoomDetailEnabled==0)return 0.0;
    /* IRIS_26752_IPOL_PLAN_B_NONINTEGER_SAMPLE
     * Preserve the paper's arbitrary continuous output lattice instead of snapping Plan B to
     * the retired fixed true-2x direct-CFA lattice. */
    vec2 local=sourcePixel*iris26752PlanBDetailScale-iris26752PlanBDetailOrigin;
    ivec2 sz=textureSize(iris26718HighZoomDetail,0);
    if(any(lessThan(local,vec2(0.0)))||any(greaterThan(local,vec2(sz)-vec2(1.0))))return 0.0;
    vec2 uv=(local+vec2(0.5))/vec2(sz);
    return clamp(texture(iris26718HighZoomDetail,uv).r,-0.56,0.56);
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
    if(iris26592MotionHdrHandoff!=0){
        /* 26798 keeps successful 26797 as fallback, then promotes weak unsupported chroma only
         * when it is contour-connected to a strong false-color seed before presentation/tone. */
        linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);
        /* 26799 consumes a true multi-pass connected mask after preserving 26798 as fallback. */
        linearSrgb=iris26799ApplyConnectedCorrection(xy,sourcePixel,linearSrgb);
    }
    if(iris26718HighZoomDetailEnabled!=0){
        linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail(sourcePixel)),vec3(0.0));
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
            float globalMapped=iris26653MapMotionSdrFinalGuide(sourceGuide);
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
            mappedGuide=iris26660ObjectColorGamma(mappedGuide);
            mappedGuide=iris26770MidtonePresentationTrim(mappedGuide);
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
    linearSrgb=iris26638ApplyShadowFloorGuard(linearSrgb);
    linearSrgb=fitDisplayGamut(linearSrgb);
    linearSrgb=iris26638UserSaturation(linearSrgb,iris26630MotionSaturation);

    Output=clamp(
            srgbEncode(linearSrgb),
            vec3(0.0),
            vec3(1.0));
}
