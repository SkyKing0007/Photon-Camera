#define LAYOUT //
LAYOUT
precision highp float;precision highp int;
layout(std430,binding=1)buffer RedBuf{
float red[];
};
layout(std430,binding=2)readonly buffer GreenBuf{
float green[];
};
layout(std430,binding=3)buffer BlueBuf{
float blue[];
};
layout(std430,binding=4)readonly buffer VhBuf{
float vh[];
};
layout(std430,binding=9)readonly buffer TrustBuf{
float trust[];
};
uniform ivec2 bandSize;uniform int bandOriginY;uniform int cfaPattern;
int idxAt(ivec2 p){p=clamp(p,ivec2(0),bandSize-ivec2(1));return p.y*bandSize.x+p.x;}int phaseAt(ivec2 p){ivec2 gp=ivec2(p.x,bandOriginY+p.y);return(gp.x&1)|((gp.y&1)<<1);}int colorAt(ivec2 p){int q=phaseAt(p);if(cfaPattern==0)return q==0?0:(q==3?2:1);if(cfaPattern==1)return q==1?0:(q==2?2:1);if(cfaPattern==2)return q==2?0:(q==1?2:1);return q==3?0:(q==0?2:1);}float g(ivec2 p){return green[idxAt(p)];}float r(ivec2 p){return red[idxAt(p)];}float b(ivec2 p){return blue[idxAt(p)];}float tr(ivec2 p){return trust[idxAt(p)];}
bool fullTrusted(ivec2 p,bool wantRed){bool horizontal=colorAt(p+ivec2(1,0))==(wantRed?0:2);ivec2 a=horizontal?ivec2(-1,0):ivec2(0,-1);ivec2 z=horizontal?ivec2(1,0):ivec2(0,1);ivec2 a3=3*a,z3=3*z;return tr(p)>0.5&&tr(p+a)>0.5&&tr(p+z)>0.5&&tr(p+a3)>0.5&&tr(p+z3)>0.5;}
float safeAxis(ivec2 p,bool wantRed){float gc=g(p);bool horizontal=colorAt(p+ivec2(1,0))==(wantRed?0:2);ivec2 a=horizontal?ivec2(-1,0):ivec2(0,-1);ivec2 z=horizontal?ivec2(1,0):ivec2(0,1);if(tr(p+a)<0.5||tr(p+z)<0.5)return gc;float ca=(wantRed?r(p+a):b(p+a))-g(p+a);float cz=(wantRed?r(p+z):b(p+z))-g(p+z);float mean=0.5*(ca+cz);float rel=abs(ca-cz)/max(abs(mean),0.045);float conf=1.0-smoothstep(0.22,0.42,rel);return max(0.0,gc+mean*conf);}
float originalEstimate(ivec2 p,bool wantRed){const float e=1.0e-5;float gc=g(p);float n2=e+abs(gc-g(p+ivec2(0,-2)));float s2=e+abs(gc-g(p+ivec2(0,2)));float w2=e+abs(gc-g(p+ivec2(-2,0)));float e2=e+abs(gc-g(p+ivec2(2,0)));float n=wantRed?r(p+ivec2(0,-1)):b(p+ivec2(0,-1));float s=wantRed?r(p+ivec2(0,1)):b(p+ivec2(0,1));float w=wantRed?r(p+ivec2(-1,0)):b(p+ivec2(-1,0));float ee=wantRed?r(p+ivec2(1,0)):b(p+ivec2(1,0));float n3=wantRed?r(p+ivec2(0,-3)):b(p+ivec2(0,-3));float s3=wantRed?r(p+ivec2(0,3)):b(p+ivec2(0,3));float w3=wantRed?r(p+ivec2(-3,0)):b(p+ivec2(-3,0));float e3=wantRed?r(p+ivec2(3,0)):b(p+ivec2(3,0));float commonV=abs(n-s),commonH=abs(w-ee);float gradN=n2+commonV+abs(n-n3);float gradS=s2+commonV+abs(s-s3);float gradW=w2+commonH+abs(w-w3);float gradE=e2+commonH+abs(ee-e3);float dn=n-g(p+ivec2(0,-1));float ds=s-g(p+ivec2(0,1));float dw=w-g(p+ivec2(-1,0));float de=ee-g(p+ivec2(1,0));float vertical=(gradN*ds+gradS*dn)/(gradN+gradS);float horizontal=(gradE*dw+gradW*de)/(gradE+gradW);return max(0.0,gc+mix(vertical,horizontal,clamp(vh[idxAt(p)],0.0,1.0)));}
/* IRIS_26498_RCD_GREEN_SITE_CHROMA_REQUIRES_TWO_SIDED_PHYSICAL_EVIDENCE */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,bandSize)))return;if(colorAt(p)!=1)return;red[idxAt(p)]=fullTrusted(p,true)?originalEstimate(p,true):safeAxis(p,true);blue[idxAt(p)]=fullTrusted(p,false)?originalEstimate(p,false):safeAxis(p,false);}
