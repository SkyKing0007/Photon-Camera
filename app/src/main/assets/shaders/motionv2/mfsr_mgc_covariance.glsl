#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
layout(rgba32f,binding=0) uniform highp writeonly image2D outputCov;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform ivec2 guideSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
uniform float noiseS;
uniform float noiseO;

int phaseIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int colorFromPhase(int phase){if(cfaPattern==0){if(phase==0)return 0;if(phase==3)return 2;return 1;}if(cfaPattern==1){if(phase==1)return 0;if(phase==2)return 2;return 1;}if(cfaPattern==2){if(phase==2)return 0;if(phase==1)return 2;return 1;}if(phase==3)return 0;if(phase==0)return 2;return 1;}
float wbForColor(int color){return color==0?wbR:(color==2?wbB:1.0);}
int clampPhase(int value,int extent){int phase=value&1;if(phase>=extent)return extent-1;int last=phase+2*((extent-1-phase)/2);return clamp(value,phase,last);}
ivec2 phaseClamp(ivec2 p){return ivec2(clampPhase(p.x,rawSize.x),clampPhase(p.y,rawSize.y));}
float nativeCalculationSample(ivec2 p){p=phaseClamp(p);int phase=phaseIndex(p);float rawValue=float(texelFetch(rawTexture,p,0).r);float black=blackLevel[phase];float sensor=max(rawValue-black,0.0)/max(whiteLevel-black,1.0);return sensor*exposureScale*wbForColor(colorFromPhase(phase));}
vec4 qAt(ivec2 q){ivec2 p=clamp(q*2,ivec2(0),rawSize-ivec2(2));return vec4(nativeCalculationSample(p),nativeCalculationSample(p+ivec2(1,0)),nativeCalculationSample(p+ivec2(0,1)),nativeCalculationSample(p+ivec2(1,1)));}
vec4 canon(vec4 v){if(cfaPattern==0)return v;if(cfaPattern==1)return vec4(v.g,v.r,v.a,v.b);if(cfaPattern==2)return vec4(v.b,v.a,v.r,v.g);return vec4(v.a,v.b,v.g,v.r);}
void grad(float dx,float dy,inout vec4 t){t+=vec4(dx*dx,dy*dy,dx*dy,0.0);}
vec4 structureTensor(float g0[9],float g1[9]){
    vec4 t=vec4(0.0);
    for(int y=0;y<2;y++)for(int x=0;x<2;x++){
        float g00=g0[y*3+x],g01=g0[y*3+x+1],g10=g1[y*3+x],g11=g1[y*3+x+1];
        float g20=g0[(y+1)*3+x],g21=g0[(y+1)*3+x+1],g30=g1[(y+1)*3+x],g31=g1[(y+1)*3+x+1];
        float bdx,bdy,rdx,rdy;
        if(cfaPattern==1||cfaPattern==2){
            bdx=.5*((g11-g01)+(g21-g10)); bdy=.5*((g01-g10)+(g11-g21));
            rdx=.5*((g21-g10)+(g30-g20)); rdy=.5*((g21-g30)+(g10-g20));
        }else{
            bdx=.5*((g11-g00)+(g20-g10)); bdy=.5*((g00-g10)+(g11-g20));
            rdx=.5*((g21-g11)+(g31-g20)); rdy=.5*((g21-g31)+(g11-g20));
        }
        grad(bdx,bdy,t);grad(rdx,rdy,t);grad(.5*(g21-g00),.5*(g01-g20),t);grad(.5*(g31-g10),.5*(g11-g30),t);
    }
    t/=16.0;t.w=.75;float c0=.5*(t.x+t.y);float c1=.5*(t.y-t.x);return vec4(c0+t.z,c0-t.z,c1,t.w);
}
mat2 precisionFrom(vec4 t,float greenVar,float greenNoise){
    float trace=t.x+t.y,difference=t.x-t.y,disc=sqrt(max(difference*difference+4.0*t.z*t.z,0.0));
    float l1=.5*(trace+disc),l2=.5*(trace-disc);vec2 e1=vec2(1.0,0.0);
    if(abs(t.z)>.0001)e1=normalize(vec2(t.z,l1-t.x))*-sign(t.z);else if(t.x<t.y)e1=vec2(0.0,1.0);
    vec2 e2=vec2(-e1.y,e1.x);float s1=sqrt(max(l1,0.0)),s2=sqrt(max(l2,0.0));
    float correction=t.w*greenNoise;l1*=l1/max(l1+correction,1e-8);float strength=sqrt(max(l1,0.0));
    float coherence=(s1-s2)/(s1+s2+1e-6);float correctedGreenStd=sqrt(greenVar*greenVar/max(greenVar+greenNoise,1e-8));
    float dominant=max(strength,correctedGreenStd)-.001;float blur=clamp(1.0-dominant*142.857142857,0.0,1.0);
    float anisotropic=mix(4.0,6.0,min(coherence,strength*5.0));float p1=mix(anisotropic,1.0,blur);float p2=mix(mix(4.0,1.3333333333,coherence),1.0,blur);
    mat2 R=mat2(e1,e2);return transpose(R)*mat2(p1*p1,0.0,0.0,p2*p2)*R;
}
/* IRIS_26488_BJZHOU_NATIVE_RAW_COVARIANCE_EXACT_GEOMETRY
 * Exact recovered structure-tensor equations at one sample per RAW/4 guide texel.
 * The resulting precision matrix is stored directly (not inverted) for MergeRgb.
 */
void main(){
    ivec2 center=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(center,guideSize)))return;
    float g0[9],g1[9];float gs=0.0,gs2=0.0;vec3 avg=vec3(0.0);ivec2 base=center*2;
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        vec4 rggb=canon(qAt(base+ivec2(x,y)));int idx=(y+1)*3+x+1;
        if(cfaPattern==2||cfaPattern==3){g0[idx]=rggb.b;g1[idx]=rggb.g;}else{g0[idx]=rggb.g;g1[idx]=rggb.b;}
        float wx=x==0?.5:.25,wy=y==0?.5:.25;avg+=vec3(rggb.r,.5*(rggb.g+rggb.b),rggb.a)*wx*wy;
        gs+=rggb.g+rggb.b;gs2+=rggb.g*rggb.g+rggb.b*rggb.b;
    }
    float gm=gs/18.0,gv=max(gs2/18.0-gm*gm,0.0);float averageLuma=clamp(dot(avg,vec3(0.25,0.5,0.25)),0.0,1.0);
    float greenNoise=2.0*max(noiseS*max(averageLuma,0.0)+noiseO,1e-10);
    mat2 P=precisionFrom(structureTensor(g0,g1),gv,greenNoise);
    imageStore(outputCov,center,vec4(P[0][0],P[0][1],P[1][0],P[1][1]));
}
