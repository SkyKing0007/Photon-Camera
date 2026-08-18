#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D noiseCurve;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D alterCfa;
layout(r32f,binding=2) uniform highp writeonly image2D outRobustness;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform int tileSizePacked;
uniform float wbR;
uniform float wbG;
uniform float wbB;

int colorOf(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
vec3 guideReference(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));vec4 v=imageLoad(referenceCfa,q);float s[4]=float[4](v.r,v.g,v.b,v.a);vec3 o=vec3(0.0);float ng=0.0;
    for(int i=0;i<4;i++){int c=colorOf(i);float g=c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6));float x=s[i]/g;if(c==0)o.r=x;else if(c==2)o.b=x;else{o.g+=x;ng+=1.0;}}o.g/=max(ng,1.0);return o;
}
vec3 guideAlter(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));vec4 v=imageLoad(alterCfa,q);float s[4]=float[4](v.r,v.g,v.b,v.a);vec3 o=vec3(0.0);float ng=0.0;
    for(int i=0;i<4;i++){int c=colorOf(i);float g=c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6));float x=s[i]/g;if(c==0)o.r=x;else if(c==2)o.b=x;else{o.g+=x;ng+=1.0;}}o.g/=max(ng,1.0);return o;
}
void localStatsRef(ivec2 q,out vec3 mu,out vec3 var){
    vec3 s=vec3(0),ss=vec3(0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec3 v=guideReference(q+ivec2(x,y));s+=v;ss+=v*v;}
    mu=s/9.0;var=max(ss/9.0-mu*mu,vec3(0));
}
vec3 localMeanAlt(ivec2 q){vec3 s=vec3(0);for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)s+=guideAlter(q+ivec2(x,y));return s/9.0;}
float dogson(float x){float a=abs(x);if(a<=0.5)return -2.0*a*a+1.0;if(a<=1.5)return a*a-2.5*a+1.5;return 0.0;}
void dogsonRef(vec2 p,out vec3 mu,out vec3 var){ivec2 c=ivec2(round(p));vec3 sm=vec3(0),sv=vec3(0);float sw=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(c+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));float w=dogson(float(q.x)-p.x)*dogson(float(q.y)-p.y);vec3 m,v;localStatsRef(q,m,v);sm+=m*w;sv+=v*w;sw+=w;}mu=sm/max(sw,1e-8);var=sv/max(sw,1e-8);}
vec3 dogsonAlt(vec2 p){ivec2 c=ivec2(round(p));vec3 sm=vec3(0);float sw=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(c+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));float w=dogson(float(q.x)-p.x)*dogson(float(q.y)-p.y);sm+=localMeanAlt(q)*w;sw+=w;}return sm/max(sw,1e-8);}
vec2 ipolNoise(float b){int idx=clamp(int(round(1000.0*clamp(b,0.0,1.0))),0,1000);return texelFetch(noiseCurve,ivec2(idx,0),0).rg;}

/* IRIS_26484_BJZHOU_FLOW_VARIATION_REJECTION_CORE
 * Flow variation from the safe spatial reconstruction becomes an explicit motion prior;
 * photometric residual is normalized by the per-frame physical noise curve before admission.
 * Existing 5x5 conservative erosion remains the final spatial rejection expansion.
 *
 * IRIS_26483_HALF_RES_ROBUSTNESS_ON_BAYER_QUADS
 * Robustness evidence is intrinsically built from packed Bayer-quad statistics.
 * Evaluate it once per Bayer quad instead of four times per physical RAW pixel.
 */
void main(){
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(q,rawHalf)))return;
    vec4 flowState=texelFetch(flowTexture,q,0);vec2 flow=flowState.xy;
    vec2 alt=vec2(q)+flow;
    if(alt.x<0.0||alt.y<0.0||alt.x>=float(rawHalf.x)||alt.y>=float(rawHalf.y)){imageStore(outRobustness,q,vec4(0));return;}
    vec3 refMu,refVar;dogsonRef(vec2(q),refMu,refVar);vec3 altMu=dogsonAlt(alt);vec3 dp=abs(refMu-altMu);
    float d2=0.0,sigma2=0.0;
    for(int c=0;c<3;c++){vec2 curve=ipolNoise(refMu[c]);float sigmaT=max(curve.x,1e-8),dT=max(curve.y,1e-8);float dp2=dp[c]*dp[c];float shrink=dp2/max(dp2+dT*dT,1e-12);d2+=dp2*shrink*shrink;sigma2+=max(refVar[c],sigmaT*sigmaT);}
    vec2 mn=vec2(3.402823e38),mx=vec2(-3.402823e38);int ts=max(tileSizePacked,1);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 qq=clamp(q+ivec2(x,y)*ts,ivec2(0),rawHalf-ivec2(1));vec2 f=texelFetch(flowTexture,qq,0).xy;mn=min(mn,f);mx=max(mx,f);}
    vec2 span=mx-mn;float motionPrior=max(flowState.z,length(span)/max(length(vec2(rawHalf)),1.0));float robustnessBoost=motionPrior>9.88235261e-5?6.0:1.0;float photometric=exp2(min(-0.07*d2/max(sigma2,1e-12),0.0));float unblocker=clamp(motionPrior*32.0,0.0,0.95);float R=min(1.0-unblocker,photometric);R=pow(clamp(R,0.0,1.0),robustnessBoost>1.0?1.15:1.0);imageStore(outRobustness,q,vec4(R));
}
