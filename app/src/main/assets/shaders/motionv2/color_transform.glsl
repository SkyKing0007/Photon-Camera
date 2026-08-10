precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

/*
 * IRIS_26427_COHERENT_NEUTRAL_HIGHLIGHT_CLIP
 *
 * Extreme highlights are allowed to clip. The requirement is that they clip
 * coherently rather than exposing unequal R/G/B clipping as magenta/cyan
 * zipper structure.
 *
 * Camera2 WB gains and the timestamp-owned sensor -> linear-sRGB matrix remain
 * authoritative. No neighboring hue is imported.
 */

float max3(vec3 v) { return max(v.r,max(v.g,v.b)); }
float min3(vec3 v) { return min(v.r,min(v.g,v.b)); }

vec3 transformBalanced(vec3 balanced) {
    return vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));

    float sensorClip=max(sensorClipLevel,1.0e-6);
    vec3 sensorRelative=cameraRgb/sensorClip;

    /*
     * One confidence for the highlight, not three independent clipping
     * decisions. As any physical camera channel loses authority, confidence
     * falls continuously.
     */
    vec3 sensorReliable=vec3(1.0)-smoothstep(
            vec3(0.900),
            vec3(0.985),
            sensorRelative);
    float sensorLoss=1.0-min3(sensorReliable);

    /*
     * Apply the actual HAL color contract first. The legacy pre-transform
     * neighboring-hue reconstruction is intentionally absent.
     */
    vec3 balanced=cameraRgb*sensorGains;
    vec3 linearSrgb=max(transformBalanced(balanced),vec3(0.0));

    float outMax=max3(linearSrgb);
    float outMin=min3(linearSrgb);
    float y=max(dot(linearSrgb,vec3(0.2126,0.7152,0.0722)),0.0);

    /*
     * Protect ordinary saturated colors. Output-space neutralization requires
     * HIGH LUMINANCE, not merely one large RGB component. Therefore a vivid
     * red/blue object is not made white just because one channel is large.
     */
    float brightHighlight=smoothstep(0.62,0.90,y);

    /*
     * Catch WB/matrix expansion: a sensor sample may still be below physical
     * white while transformed linear RGB is already beyond display headroom.
     * Channel spread matters only inside a genuinely bright highlight.
     */
    float spread=(outMax-outMin)/max(outMax,1.0e-6);
    float overflow=smoothstep(0.94,1.10,outMax);
    float suspiciousSpread=smoothstep(0.08,0.30,spread);
    float transformedLoss=brightHighlight*overflow*suspiciousSpread;

    /*
     * Physical sensor saturation is also only allowed to neutralize a bright
     * highlight. This avoids changing a normally exposed saturated surface.
     */
    float physicalLoss=brightHighlight*sensorLoss;
    float colorAuthorityLoss=max(physicalLoss,transformedLoss);

    /*
     * Continuous authority transition:
     * valid color -> reduced chroma -> neutral highlight.
     */
    float neutralize=smoothstep(0.10,0.72,colorAuthorityLoss);

    /*
     * Preserve highlight energy. As color authority vanishes, converge toward
     * equal RGB at the brightest transformed channel. Render may then compress
     * or clip that value normally, but it cannot become magenta/cyan.
     */
    float neutralEnergy=max(outMax,y);
    vec3 coherentRgb=mix(linearSrgb,vec3(neutralEnergy),neutralize);

    /*
     * Terminal coherent clip. At this point highlight color is intentionally
     * considered unrecoverable.
     */
    float terminal=
            smoothstep(0.68,0.96,colorAuthorityLoss)
            * smoothstep(0.78,1.02,y);
    float terminalEnergy=max3(coherentRgb);
    coherentRgb=mix(coherent,vec3(terminalEnergy),terminal);

    Output=max(coherentRgb,vec3(0.0));
}
