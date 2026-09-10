precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float sceneWhite;
uniform float outputExposureScale;
uniform float irisOutputZoom;
uniform int iris26592MotionHdrHandoff;
uniform float displayGain;
uniform float iris26604MotionSdrKneeFinal;
uniform sampler2D iris26620LocalLaplacianCorrection;
uniform int iris26620LocalLaplacianEnabled;
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
    linearSrgb=mapExtendedLinearHeadroom(linearSrgb);

    /* IRIS_26620_MULTISCALE_LOCAL_LAPLACIAN_FINAL_OWNER
     * The exact 26614 global tone map above consumes motionV2DisplayGain/outputExposureScale once.
     * A half-resolution correction field reconstructed from seven Gaussian/Laplacian scales then
     * restores only contrast that the global map compressed. Apply one RGB scalar after global
     * mapping so hue/channel ratios are unchanged and no second exposure owner is introduced. */
    if(iris26620LocalLaplacianEnabled!=0){
        vec2 correctionSize=vec2(textureSize(iris26620LocalLaplacianCorrection,0));
        /* Pyramid0 is decimated at source index 2*q, so sample in that exact
         * phase instead of mapping by normalized source dimensions. */
        vec2 correctionCoord=sourcePixel*0.5;
        vec2 uv=(correctionCoord+vec2(0.5))/max(correctionSize,vec2(1.0));
        vec2 halfTexel=vec2(0.5)/max(correctionSize,vec2(1.0));
        uv=clamp(uv,halfTexel,vec2(1.0)-halfTexel);
        float correctionEv=clamp(texture(iris26620LocalLaplacianCorrection,uv).r,-0.55,0.55);
        /* Local presentation may restore compressed contrast, but it may not
         * create a new display-gamut clip that was absent after the 26614 map. */
        float mappedPeak=max3(linearSrgb);
        if(correctionEv>0.0){
            float availableUpEv=mappedPeak>1.0e-7 ? max(log2(1.0/mappedPeak),0.0) : 0.0;
            correctionEv=min(correctionEv,availableUpEv);
        }
        linearSrgb*=exp2(correctionEv);
    }

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
