#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D inputEvidence;
layout(r32f,binding=0) uniform highp writeonly image2D outEvidence;
uniform ivec2 size;
const float K[20]=float[20](0.049995250135,0.049996950002,0.049998449933,0.049999749910,0.050000849916,0.050001749940,0.050002449969,0.050002949996,0.050003250015,0.050003350021,0.050003250015,0.050002949996,0.050002449969,0.050001749940,0.050000849916,0.049999749910,0.049998449933,0.049996950002,0.049995250135,0.049993350351);
float at(ivec2 p){return texelFetch(inputEvidence,clamp(p,ivec2(0),size-ivec2(1)),0).r;}
/* IRIS_26487_BJZHOU_CLIPPED_GAUSSIAN_V_EXACT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,size)))return;float f=0.0;for(int t=0;t<20;t++)f+=K[t]*at(p+ivec2(0,t-9));float v=round(255.0*clamp(min(at(p),f),0.0,1.0))/255.0;imageStore(outEvidence,p,vec4(v));}
