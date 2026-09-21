#define LAYOUT //
LAYOUT
precision highp float;precision highp int;
layout(std430,binding=0)readonly buffer CfaBuf{
float cfa[];
};
layout(std430,binding=2)buffer GreenBuf{
float green[];
};
layout(std430,binding=4)readonly buffer VhBuf{
float vh[];
};
layout(std430,binding=5)readonly buffer LpfBuf{
float lpf[];
};
layout(std430,binding=9)readonly buffer TrustBuf{
float trust[];
};
uniform ivec2 bandSize;uniform int bandOriginY;uniform int cfaPattern;
int idxAt(ivec2 p){p=clamp(p,ivec2(0),bandSize-ivec2(1));return p.y*bandSize.x+p.x;}float raw(ivec2 p){return cfa[idxAt(p)];}float low(ivec2 p){return lpf[idxAt(p)];}float tr(ivec2 p){return trust[idxAt(p)];}
int phaseAt(ivec2 p){ivec2 gp=ivec2(p.x,bandOriginY+p.y);return(gp.x&1)|((gp.y&1)<<1);}int colorAt(ivec2 p){int q=phaseAt(p);if(cfaPattern==0)return q==0?0:(q==3?2:1);if(cfaPattern==1)return q==1?0:(q==2?2:1);if(cfaPattern==2)return q==2?0:(q==1?2:1);return q==3?0:(q==0?2:1);}
float safePair(ivec2 a,ivec2 b,out bool ok){ok=tr(a)>0.5&&tr(b)>0.5;return ok?0.5*(raw(a)+raw(b)):0.0;}
float safeGreenCross(ivec2 p){bool hv,vv;float h=safePair(p+ivec2(-1,0),p+ivec2(1,0),hv);float v=safePair(p+ivec2(0,-1),p+ivec2(0,1),vv);if(hv&&vv){float hd=abs(raw(p+ivec2(-1,0))-raw(p+ivec2(1,0)));float vd=abs(raw(p+ivec2(0,-1))-raw(p+ivec2(0,1)));return hd<vd?h:(vd<hd?v:0.5*(h+v));}if(hv)return h;if(vv)return v;float s=0.0,w=0.0;ivec2 d[4]=ivec2[4](ivec2(-1,0),ivec2(1,0),ivec2(0,-1),ivec2(0,1));for(int k=0;k<4;++k){float t=tr(p+d[k]);s+=t*raw(p+d[k]);w+=t;}return w>0.5?s/w:max(raw(p),0.0);}
float safeSameGreen(ivec2 p){bool h,v;float hm=safePair(p+ivec2(-2,0),p+ivec2(2,0),h);float vm=safePair(p+ivec2(0,-2),p+ivec2(0,2),v);if(h&&v)return 0.5*(hm+vm);if(h)return hm;if(v)return vm;return safeGreenCross(p);}
bool originalNeighborhoodTrusted(ivec2 p){for(int k=-4;k<=4;++k){if(tr(p+ivec2(k,0))<0.5||tr(p+ivec2(0,k))<0.5)return false;}return true;}
/* IRIS_26498_RCD_GREEN_NEVER_USES_CENSORED_AS_DIRECTIONAL_MEASUREMENT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,bandSize)))return;int i=idxAt(p);int ccol=colorAt(p);
 if(ccol==1){green[i]=tr(p)>0.5?raw(p):safeSameGreen(p);return;}
 if(p.x<5||p.y<5||p.x+5>=bandSize.x||p.y+5>=bandSize.y||tr(p)<0.5||!originalNeighborhoodTrusted(p)){green[i]=safeGreenCross(p);return;}
 const float e=1.0e-5;float c=raw(p);float ng=e+abs(raw(p+ivec2(0,-1))-raw(p+ivec2(0,1)))+abs(c-raw(p+ivec2(0,-2)))+abs(raw(p+ivec2(0,-1))-raw(p+ivec2(0,-3)))+abs(raw(p+ivec2(0,-2))-raw(p+ivec2(0,-4)));float sg=e+abs(raw(p+ivec2(0,1))-raw(p+ivec2(0,-1)))+abs(c-raw(p+ivec2(0,2)))+abs(raw(p+ivec2(0,1))-raw(p+ivec2(0,3)))+abs(raw(p+ivec2(0,2))-raw(p+ivec2(0,4)));float wg=e+abs(raw(p+ivec2(-1,0))-raw(p+ivec2(1,0)))+abs(c-raw(p+ivec2(-2,0)))+abs(raw(p+ivec2(-1,0))-raw(p+ivec2(-3,0)))+abs(raw(p+ivec2(-2,0))-raw(p+ivec2(-4,0)));float eg=e+abs(raw(p+ivec2(1,0))-raw(p+ivec2(-1,0)))+abs(c-raw(p+ivec2(2,0)))+abs(raw(p+ivec2(1,0))-raw(p+ivec2(3,0)))+abs(raw(p+ivec2(2,0))-raw(p+ivec2(4,0)));float lc=low(p);float n=raw(p+ivec2(0,-1))*(2.0*lc)/(e+lc+low(p+ivec2(0,-1)));float s=raw(p+ivec2(0,1))*(2.0*lc)/(e+lc+low(p+ivec2(0,1)));float w=raw(p+ivec2(-1,0))*(2.0*lc)/(e+lc+low(p+ivec2(-1,0)));float ee=raw(p+ivec2(1,0))*(2.0*lc)/(e+lc+low(p+ivec2(1,0)));float v=(sg*n+ng*s)/(ng+sg);float h=(wg*ee+eg*w)/(eg+wg);green[i]=mix(v,h,clamp(vh[i],0.0,1.0));}
