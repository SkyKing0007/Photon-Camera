#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 0) readonly buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 4) buffer VhBuf {
    float vh[];
};
layout(std430, binding = 9) readonly buffer TrustBuf {
    float trust[];
};
uniform ivec2 bandSize;
int idxAt(ivec2 p){p=clamp(p,ivec2(0),bandSize-ivec2(1));return p.y*bandSize.x+p.x;}
float raw(ivec2 p){return cfa[idxAt(p)];}
float tr(ivec2 p){return trust[idxAt(p)];}
float sq(float v){return v*v;}
float axisResidual(ivec2 p,ivec2 d){return sq(raw(p-3*d)-raw(p-d)-raw(p+d)+raw(p+3*d)-3.0*(raw(p-2*d)+raw(p+2*d))+6.0*raw(p));}
bool axisTrusted(ivec2 p,ivec2 d){for(int k=-4;k<=4;++k)if(tr(p+k*d)<0.5)return false;return true;}
/* IRIS_26498_RCD_DIRECTION_USES_MEASURED_EVIDENCE_ONLY */
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,bandSize)))return;int i=idxAt(p);
 if(p.x<4||p.y<4||p.x+4>=bandSize.x||p.y+4>=bandSize.y){vh[i]=0.5;return;}
 bool vOk=axisTrusted(p,ivec2(0,1));bool hOk=axisTrusted(p,ivec2(1,0));
 if(!vOk&&!hOk){vh[i]=0.5;return;} if(vOk&&!hOk){vh[i]=0.0;return;} if(!vOk&&hOk){vh[i]=1.0;return;}
 float vertical=axisResidual(p+ivec2(0,-1),ivec2(0,1))+axisResidual(p,ivec2(0,1))+axisResidual(p+ivec2(0,1),ivec2(0,1));
 float horizontal=axisResidual(p+ivec2(-1,0),ivec2(1,0))+axisResidual(p,ivec2(1,0))+axisResidual(p+ivec2(1,0),ivec2(1,0));
 vertical=max(vertical,1.0e-10);horizontal=max(horizontal,1.0e-10);vh[i]=vertical/(vertical+horizontal);
}
