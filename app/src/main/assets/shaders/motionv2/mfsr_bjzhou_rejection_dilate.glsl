#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D inputRejection;
layout(r32f,binding=0) uniform highp writeonly image2D outWeight;
uniform ivec2 inputSize;
uniform ivec2 outputSize;
float sampleCoord(vec2 coordinate){vec2 s=coordinate-vec2(0.5);ivec2 p0=ivec2(floor(s));vec2 f=fract(s);ivec2 mx=inputSize-ivec2(1);float a=texelFetch(inputRejection,clamp(p0,ivec2(0),mx),0).r,b=texelFetch(inputRejection,clamp(p0+ivec2(1,0),ivec2(0),mx),0).r,c=texelFetch(inputRejection,clamp(p0+ivec2(0,1),ivec2(0),mx),0).r,d=texelFetch(inputRejection,clamp(p0+ivec2(1),ivec2(0),mx),0).r;return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}
/* IRIS_26487_BJZHOU_DILATE_MASK_EXACT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,outputSize)))return;vec2 t=2.0*vec2(p)+vec2(1.5);float r=4.0*sampleCoord(t+vec2(-1.5,-1.5))+4.0*sampleCoord(t+vec2(0.5,-1.5))+2.0*sampleCoord(t+vec2(2.0,-1.5))+4.0*sampleCoord(t+vec2(-1.5,0.5))+4.0*sampleCoord(t+vec2(0.5,0.5))+2.0*sampleCoord(t+vec2(2.0,0.5))+2.0*sampleCoord(t+vec2(-1.5,2.0))+2.0*sampleCoord(t+vec2(0.5,2.0))+sampleCoord(t+vec2(2.0,2.0));r=(r-0.2)*0.5;imageStore(outWeight,p,vec4(clamp(1.0-r,0.0,1.0)));}
