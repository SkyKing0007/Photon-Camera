#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D physicalCfa;
layout(r32f,binding=0) uniform highp writeonly image2D outUnblocker;
uniform ivec2 rawHalf;
uniform ivec2 unblockerSize;
uniform int cfaPattern;
uniform float physicalExposureScale;
uniform float greenShot;
uniform float greenRead;
vec4 canon(vec4 v){if(cfaPattern==0)return v;if(cfaPattern==1)return vec4(v.g,v.r,v.a,v.b);if(cfaPattern==2)return vec4(v.b,v.a,v.r,v.g);return vec4(v.a,v.b,v.g,v.r);}
vec2 greensAt(ivec2 q){vec4 v=canon(max(texelFetch(physicalCfa,clamp(q,ivec2(0),rawHalf-ivec2(1)),0),vec4(0.0))/max(physicalExposureScale,1.0e-6));return v.gb;}
float averageGreen(ivec2 q){vec2 g=greensAt(q);return 0.5*(g.x+g.y);}
float blurredGreen(ivec2 q){float v=0.0;for(int y=-1;y<=1;y++){float wy=y==0?0.5:0.25;for(int x=-1;x<=1;x++){float wx=x==0?0.5:0.25;v+=averageGreen(q+ivec2(x,y))*wx*wy;}}return v;}
/* IRIS_26487_BJZHOU_UNBLOCKER_NATIVE_EQUATION
 * Exact recovered 128/9 variance ratio and 0.45 mapping, adapted only from
 * native integer RAW to normalized post-black physical CFA. The ratio is
 * scale invariant because Camera2 noise is in the same normalized domain.
 */
void main(){
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(tile,unblockerSize)))return;
    ivec2 origin=tile*8;float preSum=0.0,preSq=0.0,postSum=0.0,postSq=0.0;
    for(int y=0;y<8;y++)for(int x=0;x<8;x++){ivec2 q=origin+ivec2(x,y);vec2 g=greensAt(q);float b=blurredGreen(q);preSum+=g.x+g.y;preSq+=dot(g,g);postSum+=b;postSq+=b*b;}
    float preMean=preSum/128.0,postMean=postSum/64.0;
    float preVar=max(preSq/128.0-preMean*preMean,0.0),postVar=max(postSq/64.0-postMean*postMean,0.0);
    float predicted=max(greenShot*max(preMean,0.0)+greenRead,0.0);
    float corrected=max(preVar-4.0*predicted,0.0);float denom=postVar*(128.0/9.0);float ratio=denom>0.0?corrected/denom:0.0;
    float mapped=sqrt(max(ratio,0.0))-0.45;float q8=floor(clamp(mapped,0.0,1.0)*255.0)/255.0;
    imageStore(outUnblocker,tile,vec4(q8));
}
