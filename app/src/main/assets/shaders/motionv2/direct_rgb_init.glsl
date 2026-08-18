#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

/* IRIS_26478_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR_NO_SATURATION_SIDECHANNEL */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawSize))) return;
    imageStore(outNumerator,p,vec4(0.0));
    imageStore(outDenominator,p,vec4(0.0));
    imageStore(outFrameSupport,p,vec4(0.0));
}
