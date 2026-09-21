#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp sampler2D;
uniform highp sampler2D InputBayer;
uniform highp sampler2D LensShadingMap;
layout(std430,binding=0) buffer CfaBuf { float cfa[]; };
layout(std430,binding=1) buffer RedBuf { float red[]; };
layout(std430,binding=2) buffer GreenBuf { float green[]; };
layout(std430,binding=3) buffer BlueBuf { float blue[]; };
layout(std430,binding=9) buffer TrustBuf { float trust[]; };
uniform ivec2 rawSize;
uniform ivec2 bandSize;
uniform ivec2 bandOrigin;
uniform int cfaPattern;
uniform int useLensShading;
uniform float highlightCeiling;
int mirrorIndex(int v,int size){if(size<=1)return 0;int period=2*(size-1);int w=v%period;if(w<0)w+=period;return w<size?w:period-w;}
ivec2 physicalAt(ivec2 lp){ivec2 g=bandOrigin+lp;return ivec2(mirrorIndex(g.x,rawSize.x),mirrorIndex(g.y,rawSize.y));}
int phaseAt(ivec2 p){return (p.x&1)|((p.y&1)<<1);}
int colorAt(ivec2 p){int q=phaseAt(p);if(cfaPattern==0)return q==0?0:(q==3?2:1);if(cfaPattern==1)return q==1?0:(q==2?2:1);if(cfaPattern==2)return q==2?0:(q==1?2:1);return q==3?0:(q==0?2:1);}
float phaseComponent(vec4 v,int q){return q==0?v.r:(q==1?v.g:(q==2?v.b:v.a));}
float samplePhysical(ivec2 p){return phaseComponent(texelFetch(InputBayer,p>>1,0),phaseAt(p));}
vec3 shadingRgb(ivec2 p){if(useLensShading==0)return vec3(1.0);vec2 uv=(vec2(p)+vec2(0.5))/vec2(rawSize);vec4 g=texture(LensShadingMap,clamp(uv,vec2(0.0),vec2(1.0)));return max(vec3(g.r,0.5*(g.g+g.b),g.a),vec3(0.0));}
/* IRIS_26681_SPEKTRA_SINGLE_PHYSICAL_RAW_RCD
 * Every lattice sample comes from the one timestamp-matched physical RAW. There is no
 * Motion/SHORT provenance and therefore no synthetic placeholder authority. Trust=1
 * is a statement about observation ownership, not about highlight validity.
 */
void main(){ivec2 lp=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(lp,bandSize)))return;ivec2 pp=physicalAt(lp);int i=lp.y*bandSize.x+lp.x;int col=colorAt(pp);vec3 lsc=shadingRgb(pp);float v=clamp(samplePhysical(pp)*lsc[col],0.0,highlightCeiling);cfa[i]=v;red[i]=col==0?v:0.0;green[i]=col==1?v:0.0;blue[i]=col==2?v:0.0;trust[i]=1.0;}
