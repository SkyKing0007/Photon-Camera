#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D normalRgb;
uniform highp sampler2D flowTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D shortCfa;
layout(rgba32f,binding=2) uniform highp writeonly image2D outRgb;
uniform ivec2 rawSize;uniform ivec2 rawHalf;uniform int cfaPattern;
uniform float shortToNormalScale;uniform float physicalClipThreshold;uniform float referenceExposureScale;uniform float highlightCeiling;uniform float minimumFlowConfidence;
int ci(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}int cc(int c){if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}if(c==3)return 0;if(c==0)return 2;return 1;}
float at(ivec2 p,bool sh){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=sh?imageLoad(shortCfa,p>>1):imageLoad(referenceCfa,p>>1);int c=ci(p);float x=c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));return max(sh?x:x/max(referenceExposureScale,1e-6),0.0);}
float clipFraction(ivec2 center,int color){float s=0.0,n=0.0;for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){ivec2 q=center+ivec2(x,y);if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,rawSize))||cc(ci(q))!=color)continue;s+=at(q,false)>=physicalClipThreshold?1.0:0.0;n+=1.0;}return s/max(n,1.0);}
vec2 shortMeasurement(ivec2 center,int color){float bestD=1e9;ivec2 best=center;for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){ivec2 q=center+ivec2(x,y);if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,rawSize))||cc(ci(q))!=color)continue;float d=float(x*x+y*y);if(d<bestD){bestD=d;best=q;}}float sensor=at(best,true);float valid=sensor<physicalClipThreshold?1.0:0.0;return vec2(min(sensor*shortToNormalScale,highlightCeiling),valid);}
/* IRIS_26487_SHORT_SAME_PHYSICAL_CLIP_AUTHORITY
 * Short replacement is allowed only where the normal sensor channel is physically
 * clipped and the short channel is physically uncensored under the same 250/255
 * authority used by the temporal/opponent merge. No 0.94-vs-0.985 ownership gap.
 */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawSize)))return;vec4 normal=texelFetch(normalRgb,p,0);vec4 f=texture(flowTexture,(vec2(p)+0.5)/vec2(rawSize));float variation=max(f.z,0.0);float cancelled=step(0.5,f.w);float flowConfidence=(1.0-cancelled)*exp(-80.0*variation);vec2 sp=vec2(p)+0.5+2.0*f.xy;if(sp.x<0.0||sp.y<0.0||sp.x>=float(rawSize.x)||sp.y>=float(rawSize.y)||flowConfidence<minimumFlowConfidence){imageStore(outRgb,p,normal);return;}ivec2 sc=ivec2(sp);vec3 outc=normal.rgb;float flowGate=smoothstep(minimumFlowConfidence,0.80,flowConfidence);for(int c=0;c<3;c++){float clipped=clipFraction(p,c);if(clipped<=0.0)continue;vec2 m=shortMeasurement(sc,c);float use=smoothstep(0.08,0.75,clipped)*m.y*flowGate;outc[c]=mix(normal[c],m.x,use);}imageStore(outRgb,p,vec4(max(outc,vec3(0.0)),normal.a));}
