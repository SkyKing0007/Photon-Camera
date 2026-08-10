
precision highp float;
precision highp usampler2D;
precision mediump sampler2D;
uniform usampler2D InputBuffer;
uniform sampler2D GainMap;
uniform sampler2D Kodak;
uniform ivec2 RawSize;
uniform vec2 RawInvSize;
uniform vec4 blackLevel;
uniform vec3 whitePoint;
uniform int CfaPattern;
uniform uint whitelevel;
uniform float CanonicalExposureGain;
uniform int MinimalInd;
#ifndef IRIS_26403_MOTION_HIGHLIGHT_SHOULDER
#define IRIS_26403_MOTION_HIGHLIGHT_SHOULDER 0
#endif
#ifndef IRIS_26412_MOTION_V2_WIDE_LINEAR
#define IRIS_26412_MOTION_V2_WIDE_LINEAR 0
#endif
uniform int MotionHighlightShoulderEnable;
uniform float MotionHighlightShoulderStart;
uniform float MotionHighlightShoulderStrength;
#define BLR (0.0)
#define BLG (0.0)
#define BLB (0.0)
#define QUAD 0
#define RGBLAYOUT 0
#define TESTPATTERN 0
#define OFFSET 0,0
#define USEGAIN 1
#import interpolation
#if RGBLAYOUT == 1
out vec3 Output;
#else
out float Output;
#endif


void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy) - ivec2(OFFSET);
    ivec2 fact = (xy)%2;
    xy+=ivec2(CfaPattern%2,CfaPattern/2);
    #if QUAD == 1
        fact = (xy/2)%2;
        xy+=ivec2(CfaPattern%2,CfaPattern/2)*2;
    #endif
    float balance;
    #if USEGAIN == 1
    vec4 gains = texture(GainMap, vec2(xy)*vec2(RawInvSize));
    gains.rgb = vec3(gains.r,(gains.g+gains.b)/2.0,gains.a);
    gains.rgb /= dot(gains.rgb,vec3(1.0/3.0));
    #else
    vec3 gains = vec3(1.0);
    #endif
    //gains.rgb = vec3(1.f);
    vec3 level = vec3(blackLevel.r,(blackLevel.g+blackLevel.b)/2.0,blackLevel.a);
    #if RGBLAYOUT == 1
    //Output = vec3(texelFetch(InputBuffer, (xy+ivec2(0,0)), 0).rgb)/float(whitelevel);
    Output = vec3(texelFetch(InputBuffer, (xy), 0).rgb)/(float(whitelevel));
    Output = gains.rgb*(Output-level.rgb)/(vec3(1.0)-level.rgb);
    #else
    vec3 col = vec3(0.0);
    if(fact.x+fact.y == 1){
            col.g = 1.0;
            balance = whitePoint.g;
            Output = float(texelFetch(InputBuffer, (xy+ivec2(0,0)), 0).x)/float(whitelevel);
            Output = gains.g*(Output-level.g-BLG)/(1.0-level.g);
        } else {
            if(fact.x == 0){
                col.r = 1.0;
                balance = whitePoint.r;
                Output = float(texelFetch(InputBuffer, (xy), 0).x)/float(whitelevel);
                Output = gains.r*(Output-level.r-BLR)/(1.0-level.r);
            } else {
                col.b = 1.0;
                balance = whitePoint.b;
                Output = float(texelFetch(InputBuffer, (xy), 0).x)/float(whitelevel);
                Output = gains.b*(Output-level.b-BLB)/(1.0-level.b);
            }
        }
    // IRIS_26394_MOTION_CANONICAL_RAW_EXPOSURE
    // Global linear exposure only. No ADRC/local curve.
    Output *= CanonicalExposureGain;

    /*
     * IRIS_26403_MOTION_HIGHLIGHT_PRESERVATION
     *
     * 26402 proved that hard-clamping here can erase highlight ordering before
     * demosaic/LTM. Keep the downstream 0..1 contract, but replace the Motion
     * hard ceiling with a C1-continuous rational shoulder:
     *
     *   x <= 0.84 : exactly unchanged
     *   x >  0.84 : progressively compressed toward 1.0
     *
     * At x=1.0 the output is 0.92. Values above 1 remain ordered rather than
     * collapsing to one flat plateau. Photo/Night retain the exact old clamp.
     */
    float iris26403Linear = max(Output/balance, 0.0);
#if IRIS_26412_MOTION_V2_WIDE_LINEAR == 1
    // IRIS_26412: keep HDR headroom through demosaic/reconstruction.
    Output = max(iris26403Linear, 0.0);
#elif IRIS_26403_MOTION_HIGHLIGHT_SHOULDER == 1
    /*
     * IRIS_26404_MOTION_IQ_LAB
     * Strength 0 reproduces the pre-26403 hard-clamp result.
     * Strength 1 reproduces the 26403 rational shoulder.
     */
    float iris26404ShoulderStart =
            clamp(MotionHighlightShoulderStart, 0.75, 0.98);
    float iris26404ShoulderSpan =
            max(1.0 - iris26404ShoulderStart, 0.001);
    float iris26404Excess =
            max(iris26403Linear - iris26404ShoulderStart, 0.0);
    float iris26404Compressed =
            iris26404ShoulderStart
            + iris26404Excess
              / (1.0 + iris26404Excess / iris26404ShoulderSpan);
    float iris26404Shouldered =
            iris26403Linear <= iris26404ShoulderStart
                    ? iris26403Linear
                    : iris26404Compressed;
    float iris26404Strength =
            MotionHighlightShoulderEnable == 1
                    ? clamp(MotionHighlightShoulderStrength, 0.0, 1.0)
                    : 0.0;
    Output = clamp(
            mix(iris26403Linear, iris26404Shouldered, iris26404Strength),
            0.0,
            1.0);
#else
    Output = clamp(iris26403Linear,0.0,1.0);
#endif
    #endif
    #if TESTPATTERN == 1
        ivec2 diag = ivec2(xy.x+xy.y,xy.x-xy.y);
        //Output = balance*float((xy.x+xy.y)%64)/64.0;
        //checkerboard pattern
        //Output = balance*float((diag.x/31+diag.y/31)%2);
        //colored checkerboard pattern
        /*vec3 col2;
        float main = 0.1;
        float sec = 1.0;
        if (diag.x/31%2 == 0){
            if (diag.y/31%2 == 0){
                col2 = vec3(main,sec,sec);
            } else {
                col2 = vec3(sec,main,sec);
            }
        } else {
            if (diag.y/32%2 == 0){
                col2 = vec3(sec,sec,main);
            } else {
                col2 = vec3(main,main,sec);
            }
        }*/
        //Output *= length(col*col2);
        // round dots pattern
        //ivec2 center = (xy/31) * 31 + 16;
        //float rad = min(length(vec2(center-xy)),16.0);
        //Output = (col.r+col.b)*balance*float(int(rad) < 16)*0.1;
        //Output += balance*float(int(rad) < 10)*0.8;
        ivec2 ksize = textureSize(Kodak,0);
        vec3 col2 = texelFetch(Kodak, xy%ksize, 0).rgb;
        Output = length(col*col2*col2)*balance;
    #endif
}
