#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
layout(r32f,binding=0) uniform highp writeonly image2D outputGreen;
uniform ivec2 rawSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
uniform float highlightClipThreshold;
uniform float highlightCeiling;
int phaseIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int colorFromPhase(int phase){if(cfaPattern==0){if(phase==0)return 0;if(phase==3)return 2;return 1;}if(cfaPattern==1){if(phase==1)return 0;if(phase==2)return 2;return 1;}if(cfaPattern==2){if(phase==2)return 0;if(phase==1)return 2;return 1;}if(phase==3)return 0;if(phase==0)return 2;return 1;}
float wbForColor(int color){return color==0?wbR:(color==2?wbB:1.0);}
int clampPhase(int value,int extent){int phase=value&1;if(phase>=extent)return extent-1;int last=phase+2*((extent-1-phase)/2);return clamp(value,phase,last);}
ivec2 phaseClamp(ivec2 p){return ivec2(clampPhase(p.x,rawSize.x),clampPhase(p.y,rawSize.y));}
float sensorNormalizedAt(ivec2 p){p=phaseClamp(p);int phase=phaseIndex(p);float rawValue=float(texelFetch(rawTexture,p,0).r);float black=blackLevel[phase];return max(rawValue-black,0.0)/max(whiteLevel-black,1.0);}
float cameraSampleAt(ivec2 p){return sensorNormalizedAt(p)*exposureScale;}
float nativeCalculationSample(ivec2 p){p=phaseClamp(p);return cameraSampleAt(p)*wbForColor(colorFromPhase(phaseIndex(p)));}
float highlightCalculationSample(ivec2 p){
 p=phaseClamp(p);int targetColor=colorFromPhase(phaseIndex(p));float targetWb=max(wbForColor(targetColor),1e-6);float sensor=sensorNormalizedAt(p);float cameraFallback=cameraSampleAt(p);float clipMask=smoothstep(highlightClipThreshold,1.0,sensor);if(clipMask<=0.0)return cameraFallback*targetWb;
 float sumR=0.0,sumG=0.0,sumB=0.0,countR=0.0,countG=0.0,countB=0.0;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){ivec2 q=phaseClamp(p+ivec2(dx,dy));int c=colorFromPhase(phaseIndex(q));float v=nativeCalculationSample(q);if(c==0){sumR+=v;countR+=1.0;}else if(c==1){sumG+=v;countG+=1.0;}else{sumB+=v;countB+=1.0;}}
 const float power=3.0;float rootR=pow(max(sumR/max(countR,1.0),0.0),1.0/power),rootG=pow(max(sumG/max(countG,1.0),0.0),1.0/power),rootB=pow(max(sumB/max(countB,1.0),0.0),1.0/power);float opposed=targetColor==0?.5*(rootG+rootB):(targetColor==1?.5*(rootR+rootB):.5*(rootR+rootG));float calculationFallback=cameraFallback*targetWb;float reconstructed=pow(max(opposed,0.0),power);reconstructed=min(max(reconstructed,calculationFallback),highlightCeiling);return mix(calculationFallback,reconstructed,clipMask);
}
float edgeGreen(ivec2 p,float center){float gL=highlightCalculationSample(p+ivec2(-1,0)),gR=highlightCalculationSample(p+ivec2(1,0)),gU=highlightCalculationSample(p+ivec2(0,-1)),gD=highlightCalculationSample(p+ivec2(0,1));float cL2=highlightCalculationSample(p+ivec2(-2,0)),cR2=highlightCalculationSample(p+ivec2(2,0)),cU2=highlightCalculationSample(p+ivec2(0,-2)),cD2=highlightCalculationSample(p+ivec2(0,2));float hLin=.5*(gL+gR),vLin=.5*(gU+gD);float hCorr=clamp(.25*(2.0*center-cL2-cR2),-.5*abs(gL-gR),.5*abs(gL-gR));float vCorr=clamp(.25*(2.0*center-cU2-cD2),-.5*abs(gU-gD),.5*abs(gU-gD));float h=hLin+hCorr,v=vLin+vCorr;float gh=abs(gL-gR)+abs(2.0*center-cL2-cR2),gv=abs(gU-gD)+abs(2.0*center-cU2-cD2);float blendH=gv/max(gh+gv,1e-7);float green=mix(v,h,blendH);return clamp(green,min(min(gL,gR),min(gU,gD)),max(max(gL,gR),max(gU,gD)));}
/* IRIS_26488_BJZHOU_NATIVE_RAW_EDGE_DIRECTED_CHROMA_GUIDE */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawSize)))return;float center=highlightCalculationSample(p);float green=colorFromPhase(phaseIndex(p))==1?center:edgeGreen(p,center);imageStore(outputGreen,p,vec4(green));}
