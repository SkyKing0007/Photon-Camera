#version 310 es
#line 1
precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
out vec3 Output;

/*
 * IRIS_26419_MOTION_V2_SHADOW_UNIFORMITY
 *
 * Input: extended-linear sRGB after MotionV2Denoise.
 *
 * Goal under severe +EV inspection:
 *   - no obvious CFA/grid-shaped chroma structure;
 *   - chroma approaches fine, spatially uniform residual noise;
 *   - luma retains substantially more high-frequency structure than chroma;
 *   - bright/mid-tone texture is essentially untouched.
 *
 * The filter is bilateral in luminance. Chroma is filtered substantially more
 * strongly than luma in low-signal regions. No sharpening and no upper clamp.
 */

float luminance(vec3 c) {
    return dot(c,vec3(0.2126,0.7152,0.0722));
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 size=textureSize(InputBuffer,0);
    vec3 center=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    float yc=max(luminance(center),0.0);

    /*
     * Strong only below roughly 10% linear luminance. The photographed
     * problematic corner lives far below this before display tone.
     */
    float lowSignal=1.0-smoothstep(0.018,0.115,yc);

    float wsum=0.0;
    float ysum=0.0;
    vec2 csum=vec2(0.0);
    float yMin=yc;
    float yMax=yc;

    for(int j=-2;j<=2;j++){
        for(int i=-2;i<=2;i++){
            ivec2 q=clamp(xy+ivec2(i,j),ivec2(0),size-ivec2(1));
            vec3 v=max(texelFetch(InputBuffer,q,0).rgb,vec3(0.0));
            float y=max(luminance(v),0.0);
            yMin=min(yMin,y);
            yMax=max(yMax,y);

            /*
             * Opponent chroma around luminance. This avoids letting a noisy
             * R/B excursion redefine local structure.
             */
            vec2 ch=vec2(v.r-y,v.b-y);

            float dy=abs(y-yc);
            float rangeScale=0.006+0.12*yc;
            float rangeW=1.0/(1.0+dy/max(rangeScale,1.0e-5));

            float d2=float(i*i+j*j);
            float spatialW=1.0/(1.0+0.42*d2);
            float w=rangeW*spatialW;

            wsum+=w;
            ysum+=w*y;
            csum+=w*ch;
        }
    }

    float meanY=ysum/max(wsum,1.0e-6);
    vec2 meanCh=csum/max(wsum,1.0e-6);

    float localDifference=abs(yc-meanY);
    float flatConfidence=1.0-smoothstep(
            0.003+0.025*yc,
            0.014+0.10*yc,
            localDifference);

    /*
     * Chroma receives the strongest cleanup even when luma contains some
     * texture. Luma cleanup is restrained and requires local flatness.
     */
    float chromaMix=clamp(lowSignal*(0.62+0.30*flatConfidence),0.0,0.92);
    float lumaMix=clamp(lowSignal*flatConfidence*0.38,0.0,0.38);

    /* IRIS_26842_TRUE_FLAT_MOTTLING_CLEANUP
     * The car-body sample shows low-frequency chroma/luma clouding on genuinely smooth dark paint.
     * Do not raise denoise globally. Require the entire 5x5 luminance neighborhood to remain flat,
     * then add only a small cleanup reserve. Foliage, text, rails, seams and coherent microstructure
     * lose this gate as soon as their local range becomes material. */
    float localRange=max(yMax-yMin,0.0);
    float wholeNeighborhoodFlat=1.0-smoothstep(
            0.010+0.055*yc,
            0.030+0.145*yc,
            localRange);
    float mottleConfidence=lowSignal*flatConfidence*wholeNeighborhoodFlat;
    chromaMix=clamp(chromaMix+0.07*mottleConfidence,0.0,0.94);
    lumaMix=clamp(lumaMix+0.09*mottleConfidence,0.0,0.47);

    float outY=mix(yc,meanY,lumaMix);
    vec2 centerCh=vec2(center.r-yc,center.b-yc);
    vec2 outCh=mix(centerCh,meanCh,chromaMix);

    /*
     * Reconstruct RGB while preserving green as the luma anchor. The two
     * opponent channels are intentionally the heavily-cleaned components.
     */
    float outR=outY+outCh.x;
    float outB=outY+outCh.y;
    float outG=(outY-0.2126*outR-0.0722*outB)/0.7152;

    Output=max(vec3(outR,outG,outB),vec3(0.0));
}