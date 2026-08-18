#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D inputLuma;
uniform highp sampler2D inputRejection;
layout(r32f,binding=0) uniform highp writeonly image2D outFiltered;
uniform ivec2 smallSize;
float at(sampler2D t,ivec2 p){return texelFetch(t,clamp(p,ivec2(0),smallSize-ivec2(1)),0).r;}
float bilateralWeight(float residual,float sigma){float w2=sigma*sigma*5.0;float d2=residual*residual;float d=1.0-d2/w2;return d2<=w2?d*d:0.0;}
float spatialWeight(float r){return exp(-(r*r)/(2.0*4.0*4.0));}
/* IRIS_26487_BJZHOU_REJECTION_BILATERAL_EXACT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,smallSize)))return;float cl=at(inputLuma,p),cr=at(inputRejection,p);float wr=0.0,ws=0.0;for(int dy=-3;dy<=3;dy++){float sy=spatialWeight(float(dy));for(int dx=-3;dx<=3;dx++){ivec2 q=p+ivec2(dx,dy);float dl=at(inputLuma,q),dr=at(inputRejection,q);float sigma=cr<dr-1.0/255.0?0.00005:0.025;float w=bilateralWeight(abs(dl-cl),sigma)*spatialWeight(float(dx))*sy;float v=min(dr,cr);wr+=w*v;ws+=w;}}float outv=ws>0.0?wr/ws:cr;outv=round(255.0*clamp(outv,0.0,1.0))/255.0;imageStore(outFiltered,p,vec4(outv));}
