precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuidedBaseBuffer;
uniform int iris26619GuidedBaseEnabled;
uniform float sceneWhite;
uniform float outputExposureScale;
uniform float irisOutputZoom;
uniform int iris26592MotionHdrHandoff;
uniform float displayGain;
uniform float iris26604MotionSdrKneeFinal;
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

/* IRIS_26614_CANONICAL_SOURCE_DOMAIN_SDR_APPEARANCE
 * One C1 monotonic source-domain appearance map. Low source values retain the solved viewfinder
 * body slope. Extra display gain fades continuously toward nominal source white instead of moving
 * the highlight boundary downward as displayGain rises. Source white maps to 0.95 and >1 clean
 * HDR occupies the final 5% asymptotically. No histogram percentile or scene-dependent knot. */
float iris26614MapMotionSdrFinalGuide(float sourceGuide) {
    float x=max(sourceGuide,0.0);
    float requestedFinalGain=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float whiteAnchor=min(0.95,requestedFinalGain);
    float bodyGain=requestedFinalGain;
    if(requestedFinalGain>whiteAnchor){
        bodyGain=min(requestedFinalGain,4.0*whiteAnchor-1.0e-4);
    }
    if(x<=1.0){
        float oneMinus=1.0-x;
        return whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    }
    float reserve=1.0-whiteAnchor;
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(whiteAnchor,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}

/* IRIS_26619_MONOTONIC_GUIDED_BASE_MAP
 * The viewfinder target remains the low-guide slope.  Broad source white is reserved below final
 * white so measured local detail and compact highlights have display range above the illumination
 * field.  The rational branch is strictly increasing; the >1 tail matches its derivative at
 * source white, making the complete broad-base map C1 and strictly monotonic.
 */
const float IRIS_26619_BROAD_BASE_WHITE = 0.86;
const float IRIS_26619_DETAIL_LIMIT_STOPS = 2.0;

float iris26619MapMotionBroadBase(float sourceBase) {
    float x=max(sourceBase,0.0);
    float requestedFinalGain=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float globalMapped=iris26614MapMotionSdrFinalGuide(x);
    /* Fade the spatial allocation in as a GLOBAL capture-level condition.  This is not a
     * source-luminance threshold, so it cannot draw a ring across a smooth spatial gradient. */
    float spatialStrength=smoothstep(1.05,1.80,requestedFinalGain);
    if(spatialStrength<=0.0)return globalMapped;
    float broadWhite=min(IRIS_26619_BROAD_BASE_WHITE,requestedFinalGain);
    float bodyGain=min(requestedFinalGain,4.0*broadWhite-1.0e-4);
    float spatialMapped;
    if(bodyGain<=broadWhite+1.0e-6) {
        spatialMapped=bodyGain*x;
    } else if(x<=1.0) {
        float c=bodyGain/max(broadWhite,1.0e-6)-1.0;
        spatialMapped=bodyGain*x/(1.0+c*x);
    } else {
        float leftSlope=broadWhite*broadWhite/bodyGain;
        float reserve=max(1.0-broadWhite,1.0e-6);
        float tailScale=reserve/max(leftSlope,1.0e-6);
        float excess=x-1.0;
        spatialMapped=broadWhite+reserve*excess/(excess+tailScale);
    }
    return mix(globalMapped,spatialMapped,spatialStrength);
}

float iris26619GuidedBaseLogAt(vec2 sourcePixel, ivec2 sourceSize) {
    vec2 denom=max(vec2(sourceSize),vec2(1.0));
    vec2 uv=(sourcePixel+vec2(0.5))/denom;
    return texture(GuidedBaseBuffer,clamp(uv,vec2(0.0),vec2(1.0))).r;
}

float mapFinalSdrGuide(float sourceGuide) {
    if(iris26592MotionHdrHandoff!=0) {
        return iris26614MapMotionSdrFinalGuide(sourceGuide);
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

vec3 mapExtendedLinearHeadroom(vec3 rgb, vec2 sourcePixel, ivec2 sourceSize) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    float peak=max3(rgb);
    float guide=max(y,peak);
    if(guide<=1.0e-7) return rgb;

    float mappedGuide=mapFinalSdrGuide(guide);
    if(iris26592MotionHdrHandoff!=0 && iris26619GuidedBaseEnabled!=0) {
        /* IRIS_26619_TRUE_BASE_DETAIL_RECOMBINATION
         * 26618 multiplied linear RGB by a rapidly varying pre-tone gain and then passed that
         * result through the nonlinear 26614 map.  The composition became non-monotonic and its
         * separate 0.95->1.05 release created the observed smooth-gradient contour failure.
         *
         * 26619 instead maps only the edge-aware broad tone-guide base with a C1 monotonic curve,
         * then restores the measured local log-guide residual.  Detail strength is exactly 1.0; the +/-2-stop guard is only a pathological
         * halo/numerical bound and never increases the measured residual.
         */
        float baseLog=iris26619GuidedBaseLogAt(sourcePixel,sourceSize);
        float baseGuide=exp2(baseLog);
        float detailStops=clamp(log2(max(guide,0.000244140625))-baseLog,
                                -IRIS_26619_DETAIL_LIMIT_STOPS,
                                 IRIS_26619_DETAIL_LIMIT_STOPS);
        float mappedBase=iris26619MapMotionBroadBase(baseGuide);
        mappedGuide=max(mappedBase*exp2(detailStops),0.0);
    }
    return rgb*(mappedGuide/guide);
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

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sourceSize=textureSize(InputBuffer,0);
    ivec2 sourceXY=xy;
    vec3 linearSrgb;
    float zoom=max(irisOutputZoom,1.0);
    if(zoom<=1.00001) {
        /* IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL
         * Exact tested 26523 1x path remains unchanged.
         */
        if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;
        linearSrgb=max(texelFetch(InputBuffer,sourceXY,0).rgb,vec3(0.0));
    } else {
        vec2 center=(vec2(sourceSize)-vec2(1.0))*0.5;
        vec2 sourcePixel=center+(vec2(xy)-center)/zoom;
        linearSrgb=max(iris26524BilinearInput(sourcePixel),vec3(0.0));
        sourceXY=ivec2(clamp(floor(sourcePixel+vec2(0.5)),
                            vec2(0.0),vec2(sourceSize-ivec2(1))));
    }

    /* IRIS_26559_REMOVE_SHARED_MICROCONTRAST_HALO
     * Do not apply the legacy 5x5 local-luma contrast multiplier here. Sabre remains
     * the detail authority; headroom mapping, exposure, gamut fit and zoom are unchanged.
     */
    linearSrgb=mapExtendedLinearHeadroom(linearSrgb,vec2(sourceXY),sourceSize);

    /* IRIS_26604_FINAL_DOMAIN_TONE
     * outputExposureScale and Motion brightness target are already consumed by mapFinalSdrGuide;
     * there is no second image multiplier after the canonical tone owner.
     */
    linearSrgb=fitDisplayGamut(linearSrgb);

    Output=clamp(
            srgbEncode(linearSrgb),
            vec3(0.0),
            vec3(1.0));
}
