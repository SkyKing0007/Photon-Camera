#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputRobustness;
layout(r32f,binding=0) uniform highp writeonly image2D OutputRobustness;

/* IRIS_26462_WRONSKI_5X5_ROBUSTNESS_MIN - published local minimum. */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(OutputRobustness);
    if(any(greaterThanEqual(p,sz)))return;
    float r=3.402823e38;
    for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){
        ivec2 q=clamp(p+ivec2(x,y),ivec2(0),sz-ivec2(1));
        r=min(r,texelFetch(InputRobustness,q,0).r);
    }
    imageStore(OutputRobustness,p,vec4(r));
}