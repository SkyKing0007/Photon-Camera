#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputGuide;
layout(r32f,binding=0) uniform highp writeonly image2D OutputGuide;
uniform int factor;

/* IRIS_26462_WRONSKI_GAUSSIAN_PYRAMID
 * Separable-binomial equivalent 5x5 Gaussian sampling before decimation.
 */
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(p,os))) return;
    ivec2 isz=textureSize(InputGuide,0);
    ivec2 c=p*factor;
    const float k[5]=float[5](1.0,4.0,6.0,4.0,1.0);
    float sum=0.0,ws=0.0;
    for(int y=-2;y<=2;y++) for(int x=-2;x<=2;x++) {
        ivec2 q=clamp(c+ivec2(x,y),ivec2(0),isz-ivec2(1));
        float w=k[x+2]*k[y+2];
        sum+=w*texelFetch(InputGuide,q,0).r;
        ws+=w;
    }
    imageStore(OutputGuide,p,vec4(sum/max(ws,1e-8)));
}