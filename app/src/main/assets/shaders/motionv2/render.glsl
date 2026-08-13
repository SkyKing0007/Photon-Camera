precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float sceneWhite;
uniform float outputExposureScale;
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
    return dot(c,vec3(0.2126,0.7152,0.0722));
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

float mapHeadroomLuminance(float y) {
    const float start=0.50;
    if(y<=start) return y;

    float whitePoint=max(sceneWhite,start+0.05);

    /*
     * If there is little physical headroom, sensor white maps close to display
     * white. If Motion preserved several times display-white energy, spread it
     * across the remaining SDR range instead of crushing it into 0.93-1.00.
     */
    float x=clamp(
            (y-start)/max(whitePoint-start,1.0e-6),
            0.0,
            1.0);

    const float logShape=6.0;
    float shaped=
            log(1.0+logShape*x)
            /log(1.0+logShape);

    return start+(1.0-start)*shaped;
}

vec3 mapExtendedLinearHeadroom(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    if(y<=1.0e-7) return rgb;

    float mappedY=mapHeadroomLuminance(y);
    return rgb*(mappedY/y);
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
    return rgb/max(peak,1.0e-6);
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 linearSrgb=max(
            texelFetch(InputBuffer,xy,0).rgb,
            vec3(0.0));

    /*
     * Apply the same pre-tone local-contrast intent that the HDR target uses.
     * The existing headroom mapper and 0.80 exposure remain unchanged.
     */
    linearSrgb=applyReferenceSafeMicrocontrast(xy,linearSrgb);
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
