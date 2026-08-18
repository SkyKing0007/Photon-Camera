#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D InputCfa;
layout(r32f, binding=0) uniform highp writeonly image2D OutputGuide;
uniform int guideScale;
uniform float signalScale;

/*
 * IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE
 *
 * Wronski 2019 does not disclose the exact CFA->gray registration prefilter.
 * IPOL Sec. 2.1 explicitly identifies averaging each 2x2 Bayer quad as the
 * cheap/fast strategy likely used by the original mobile implementation and
 * says it is the option to use to be closer to Wronski's original method.
 *
 * InputCfa is already packed as one RGBA texel per physical 2x2 Bayer quad,
 * so this is the exact arithmetic mean of the four physical CFA samples.
 * No 26473 5x5 "FFT-equivalent" approximation remains.
 */
void main() {
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(q,os))) return;
    ivec2 is=textureSize(InputCfa,0);
    ivec2 p=clamp(q,ivec2(0),is-ivec2(1));
    vec4 v=max(texelFetch(InputCfa,p,0),vec4(0.0));
    float g=0.25*(v.r+v.g+v.b+v.a)/max(signalScale,1.0e-6);
    imageStore(OutputGuide,q,vec4(g,0.0,0.0,0.0));
}

