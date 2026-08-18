#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430,binding=0)readonly buffer CfaBuf{
float cfa[];
};
layout(std430,binding=5)buffer LpfBuf{
float lpf[];
};
layout(std430,binding=9)readonly buffer TrustBuf{
float trust[];
};
uniform ivec2 bandSize;
int idxAt(ivec2 p){p=clamp(p,ivec2(0),bandSize-ivec2(1));return p.y*bandSize.x+p.x;}
float raw(ivec2 p){return cfa[idxAt(p)];}float tr(ivec2 p){return trust[idxAt(p)];}
void addTerm(inout float s,inout float w,ivec2 p,float k){float t=tr(p);s+=k*t*raw(p);w+=k*t;}
/* IRIS_26498_RCD_LPF_NORMALIZED_MISSING_DATA */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,bandSize)))return;
 float all=tr(p)*tr(p+ivec2(-1,0))*tr(p+ivec2(1,0))*tr(p+ivec2(0,-1))*tr(p+ivec2(0,1))*tr(p+ivec2(-1,-1))*tr(p+ivec2(1,-1))*tr(p+ivec2(-1,1))*tr(p+ivec2(1,1));
 if(all>0.5){float v=raw(p)+0.5*(raw(p+ivec2(-1,0))+raw(p+ivec2(1,0))+raw(p+ivec2(0,-1))+raw(p+ivec2(0,1)))+0.25*(raw(p+ivec2(-1,-1))+raw(p+ivec2(1,-1))+raw(p+ivec2(-1,1))+raw(p+ivec2(1,1)));lpf[idxAt(p)]=v;return;}
 float s=0.0,w=0.0;addTerm(s,w,p,1.0);addTerm(s,w,p+ivec2(-1,0),0.5);addTerm(s,w,p+ivec2(1,0),0.5);addTerm(s,w,p+ivec2(0,-1),0.5);addTerm(s,w,p+ivec2(0,1),0.5);addTerm(s,w,p+ivec2(-1,-1),0.25);addTerm(s,w,p+ivec2(1,-1),0.25);addTerm(s,w,p+ivec2(-1,1),0.25);addTerm(s,w,p+ivec2(1,1),0.25);
 lpf[idxAt(p)]=w>1.0e-6?(s/w)*4.0:4.0*max(raw(p),0.0);
}
