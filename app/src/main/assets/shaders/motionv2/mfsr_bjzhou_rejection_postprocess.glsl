#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D originalRejection;
uniform highp sampler2D filteredRejection;
uniform highp sampler2D pixelDifference;
layout(r32f,binding=0) uniform highp writeonly image2D outRejection;
uniform ivec2 fullSize;
uniform ivec2 smallSize;
float sampleSmall(vec2 uv){vec2 s=uv*vec2(smallSize)-vec2(0.5);ivec2 p0=ivec2(floor(s));vec2 f=fract(s);ivec2 mx=smallSize-ivec2(1);float a=texelFetch(filteredRejection,clamp(p0,ivec2(0),mx),0).r,b=texelFetch(filteredRejection,clamp(p0+ivec2(1,0),ivec2(0),mx),0).r,c=texelFetch(filteredRejection,clamp(p0+ivec2(0,1),ivec2(0),mx),0).r,d=texelFetch(filteredRejection,clamp(p0+ivec2(1),ivec2(0),mx),0).r;return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}
/* IRIS_26487_BJZHOU_REJECTION_POSTPROCESS_EXACT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,fullSize)))return;float original=texelFetch(originalRejection,p,0).r;float pd=texelFetch(pixelDifference,p,0).r;vec2 uv=(vec2(p)+0.5)/vec2(fullSize);float filtered=sampleSmall(uv);float post=filtered;if(filtered>original){float w=pd<150.0/255.0?0.0:pd;post=original+w*(filtered-original);}if(original<=3.0/255.0&&pd<=150.0/255.0)post=original;post=round(255.0*clamp(post,0.0,1.0))/255.0;imageStore(outRejection,p,vec4(post));}
