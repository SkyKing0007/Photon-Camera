#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
layout(rgba32f,binding=0) uniform highp writeonly image2D outputGuide;
uniform ivec2 rawSize;
uniform ivec2 guideSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
uniform vec3 noiseShot;
uniform vec3 noiseRead;

int phaseIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int colorFromPhase(int phase){if(cfaPattern==0){if(phase==0)return 0;if(phase==3)return 2;return 1;}if(cfaPattern==1){if(phase==1)return 0;if(phase==2)return 2;return 1;}if(cfaPattern==2){if(phase==2)return 0;if(phase==1)return 2;return 1;}if(phase==3)return 0;if(phase==0)return 2;return 1;}
float wbForColor(int color){return color==0?wbR:(color==2?wbB:1.0);}
ivec2 clampCoord(ivec2 p){return clamp(p,ivec2(0),rawSize-ivec2(1));}
float sensorNormalizedAt(ivec2 p){p=clampCoord(p);int phase=phaseIndex(p);float rawValue=float(texelFetch(rawTexture,p,0).r);float black=blackLevel[phase];return max(rawValue-black,0.0)/max(whiteLevel-black,1.0);}
float calculationAt(ivec2 p){p=clampCoord(p);return sensorNormalizedAt(p)*exposureScale*wbForColor(colorFromPhase(phaseIndex(p)));}
vec4 physicalQuad(ivec2 q){ivec2 p=clamp(q*2,ivec2(0),rawSize-ivec2(2));return vec4(sensorNormalizedAt(p),sensorNormalizedAt(p+ivec2(1,0)),sensorNormalizedAt(p+ivec2(0,1)),sensorNormalizedAt(p+ivec2(1,1)));}
vec4 calculationQuad(ivec2 q){ivec2 p=clamp(q*2,ivec2(0),rawSize-ivec2(2));return vec4(calculationAt(p),calculationAt(p+ivec2(1,0)),calculationAt(p+ivec2(0,1)),calculationAt(p+ivec2(1,1)));}
vec4 canon(vec4 v){if(cfaPattern==0)return v;if(cfaPattern==1)return vec4(v.g,v.r,v.a,v.b);if(cfaPattern==2)return vec4(v.b,v.a,v.r,v.g);return vec4(v.a,v.b,v.g,v.r);}
float kw(int o){return o==0?0.5:0.25;}
float noiseVariance(int c,float signal){return max(noiseShot[c]*max(signal,0.0)+noiseRead[c],1e-10);}
/* IRIS_26488_BJZHOU_NATIVE_RAW_GUIDE_EXACT_STRUCTURE
 * Native R16UI -> post-black/exposure/WB calculation domain, matching the recovered MGC guide.
 * Hard saturation sentinel remains separate from the 0.985 soft color-only highlight repair.
 */
void main(){
 ivec2 center=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(center,guideSize)))return;
 vec3 m0=vec3(0.0),m1=vec3(0.0),avg=vec3(0.0);float mg0=0.0,mg1=0.0,centerGreen=0.0;ivec2 base=center*2;
 for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec4 rggb=canon(calculationQuad(base+ivec2(x,y)));vec3 rgb=vec3(rggb.r,.5*(rggb.g+rggb.b),rggb.a);avg+=rgb*kw(x)*kw(y);if(x==0&&y==0)centerGreen=rgb.g;m0+=rgb;m1+=rgb*rgb;mg0+=rggb.g+rggb.b;mg1+=rggb.g*rggb.g+rggb.b*rggb.b;}
 m0/=9.0;m1/=9.0;vec3 rgbVar=max(m1-m0*m0,vec3(0.0));mg0/=18.0;mg1/=18.0;float greenVar=max(mg1-mg0*mg0,0.0);float averageLuma=clamp(dot(avg,vec3(.25,.5,.25)),0.0,1.0);float greenNoise=2.0*noiseVariance(1,averageLuma);vec3 refColor;float refVar;if(greenVar>3.0*greenNoise){refColor=vec3(avg.r,centerGreen,avg.b);refVar=-max(rgbVar.g,greenVar);}else{refColor=avg;refVar=dot(rgbVar,vec3(1.0/3.0));}
 vec4 physical=canon(physicalQuad(base));float centerGreenSensor=.5*(physical.g+physical.b);if(centerGreenSensor>=1.0)refColor=vec3(10000.0);imageStore(outputGuide,center,vec4(refColor,refVar*1024.0));
}
