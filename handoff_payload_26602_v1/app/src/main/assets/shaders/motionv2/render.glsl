precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float sceneWhite;
uniform float outputExposureScale;
uniform float irisOutputZoom;
uniform int iris26592MotionHdrHandoff;
uniform float iris26602MotionMasterToneStart;
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

float mapHeadroomLuminance(float y) {
    /* IRIS_26602_UHDR_MASTER_SDR_PARITY
     * Motion's UHDR target is the extended-linear pre-tone rendition at the same 0.80
     * presentation scale. Preserve that master rendition exactly through guide=1.0, so
     * SDR and UHDR have identical blacks/body/midtones/color/contrast. Only luminance that
     * actually needs HDR headroom enters the shoulder. Night retains its exact 0.50 start.
     */
    float start=iris26592MotionHdrHandoff!=0 ? iris26602MotionMasterToneStart : 0.50;
    if(y<=start) return y;

    float whitePoint=max(sceneWhite,start+0.05);

    /*
     * If there is little physical headroom, sensor white maps close to display
     * white. If Motion preserved several times display-white energy, spread it
     * across the remaining SDR range instead of crushing it into 0.93-1.00.
     */
    float u=max((y-start)/max(whitePoint-start,1.0e-6),0.0);

    /* IRIS_26592_UNBOUNDED_MONOTONIC_HIGHLIGHT_TAIL
     * Motion: sceneWhite is a scale, not an endpoint. No finite valid recovered value is clamped
     * into the same tone coordinate as a brighter value. The nested log+tanh function is strictly
     * monotonic and asymptotically approaches display white. Night keeps exact successful-26591.
     */
    const float logShape=3.0;
    float shaped;
    if(iris26592MotionHdrHandoff!=0) {
        /* IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE
         * Preserve the exact 26596 body exposure and tone start. 26596 used a concave
         * log+tanh allocation inside the recoverable highlight interval, spending too much
         * display range on its lower half and making bright roads/ground/foliage wash toward
         * white even when the source still contained structure. Allocate 0..sceneWhite
         * headroom linearly instead. At u=1 retain the exact 26596 scene-white output anchor
         * (tanh(1.2020679)), then continue with a C1-matched rational tail so values beyond
         * scene white remain strictly ordered and true speculars may still approach white.
         * Nothing at or below start changes. No scene/category threshold is introduced.
         */
        /* IRIS_26597_V1_1_ESSL_CONSTANT_INITIALIZER_FIX
         * ESSL 3.20 const initializers cannot call tanh()/max(). These literals are the IEEE-754
         * float results of the unchanged V1 equations, so the highlight mapping is unchanged.
         */
        const float sceneAnchor=0.834284246;
        const float tailSlope=5.03442907;
        if(u<=1.0) {
            shaped=sceneAnchor*max(u,0.0);
        } else {
            shaped=1.0-(1.0-sceneAnchor)/(1.0+tailSlope*(u-1.0));
        }
    } else {
        float x=clamp(u,0.0,1.0);
        shaped=log(1.0+logShape*x)/log(1.0+logShape);
    }

    /* IRIS_26501_WHITE_TARGET_AFTER_EXISTING_OUTPUT_EXPOSURE
     * The previous 1.0 pre-scale ceiling became only 0.80 after the proven output
     * exposure, structurally preventing clean white clipping. Map to the inverse
     * of that existing scale so the final SDR endpoint can actually reach 1.0.
     */
    float preScaleDisplayWhite=1.0/max(outputExposureScale,1.0e-6);
    return start+(preScaleDisplayWhite-start)*shaped;
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
    float mappedGuide=mapHeadroomLuminance(guide);
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
    linearSrgb=mapExtendedLinearHeadroom(linearSrgb);

    /*
     * The global exposure remains the tested 0.80 linear scale (~-0.322 EV).
     */
    linearSrgb*=outputExposureScale;
    linearSrgb=fitDisplayGamut(linearSrgb);

    Output=clamp(
            srgbEncode(linearSrgb),
            vec3(0.0),
            vec3(1.0));
}
