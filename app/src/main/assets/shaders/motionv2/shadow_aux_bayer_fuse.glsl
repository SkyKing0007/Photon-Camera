#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;

uniform highp sampler2D mergedCfa;
uniform highp sampler2D referenceCfa;
uniform highp sampler2D shadowCfa;
uniform highp sampler2D flowTexture;
uniform highp sampler2D frameSupport;
layout(rgba32f, binding = 0) uniform highp writeonly image2D outCfa;
layout(rgba32f, binding = 1) uniform highp writeonly image2D outSemanticWeight;
layout(std430, binding = 3) buffer ShadowDiagBuf {
    uint shadowDiag[];
};
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float shadowToNormalScale;
uniform float shadowExposureRatio;
uniform float shadowClipThreshold;
uniform float minimumFlowConfidence;
uniform float deepShadowThreshold;
uniform float deepShadowPackCeiling;
uniform float minimumShadowSignal;
uniform float requiredExposureSupportRatio;
uniform float maxShadowBlend;

/* IRIS_26498_V13_BOUNDED_PRE_SHUTTER_SHADOW_AUX
 * Exactly one already-buffered brighter RAW can contribute. The merged normal CFA
 * remains base/detail authority; the immutable Wronski reference owns geometry and
 * correspondence. No generic Photon noiseS/noiseO is consumed here. A phase is
 * eligible only when actual exposure-energy gain beats its local temporal support,
 * so the auxiliary is used only where it predicts a physical shadow-SNR benefit.
 */
float sum4(vec4 v){return dot(v,vec4(1.0));}
float max4(vec4 v){return max(max(v.x,v.y),max(v.z,v.w));}
vec4 shadowSafe(vec4 v){return vec4(1.0)-step(vec4(shadowClipThreshold),v);}
vec4 phaseSafeShadow(vec2 packedCenter){
    vec2 p=packedCenter-vec2(0.5); ivec2 lo=ivec2(floor(p)); vec2 f=fract(p);
    ivec2 hi=packedSize-ivec2(1);
    ivec2 p00=clamp(lo,ivec2(0),hi),p10=clamp(lo+ivec2(1,0),ivec2(0),hi);
    ivec2 p01=clamp(lo+ivec2(0,1),ivec2(0),hi),p11=clamp(lo+ivec2(1,1),ivec2(0),hi);
    vec4 a=texelFetch(shadowCfa,p00,0),b=texelFetch(shadowCfa,p10,0);
    vec4 c=texelFetch(shadowCfa,p01,0),d=texelFetch(shadowCfa,p11,0);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
bool validateReferenceOwnedCorrespondence(ivec2 p,vec2 source,out float meanErr,out float support){
    float err=0.0; support=0.0; ivec2 hi=packedSize-ivec2(1);
    for(int oy=-2;oy<=2;++oy)for(int ox=-2;ox<=2;++ox){
        if(max(abs(ox),abs(oy))!=2)continue;
        ivec2 q=p+ivec2(ox,oy); if(any(lessThan(q,ivec2(0)))||any(greaterThan(q,hi)))continue;
        vec2 qs=source+vec2(float(ox),float(oy));
        if(qs.x<0.0||qs.y<0.0||qs.x>=float(packedSize.x)||qs.y>=float(packedSize.y))continue;
        vec4 refSensor=texelFetch(referenceCfa,q,0)/max(referenceExposureScale,1.0e-6);
        vec4 sh=phaseSafeShadow(qs); vec4 shEq=sh*shadowToNormalScale;
        vec4 mask=(vec4(1.0)-step(vec4(0.85),refSensor))*shadowSafe(sh)*step(vec4(minimumShadowSignal),refSensor);
        float n=sum4(mask); if(n<1.5)continue;
        vec4 rel=abs(refSensor-shEq)/max(refSensor,vec4(0.025));
        err+=dot(rel,mask); support+=n;
    }
    meanErr=support>0.0?err/support:1.0e20;
    return support>=12.0&&meanErr<=0.10;
}
float phaseSupport(ivec2 p,int phase){
    ivec2 rawP=p*2+ivec2(phase&1,(phase>>1)&1);
    return max(texelFetch(frameSupport,rawP,0).r,1.0);
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,packedSize)))return;
    vec4 merged=texelFetch(mergedCfa,p,0), ref=texelFetch(referenceCfa,p,0);
    vec4 mergedSensor=merged/max(referenceExposureScale,1.0e-6);
    vec4 refSensor=ref/max(referenceExposureScale,1.0e-6);
    if(max4(mergedSensor)>=deepShadowPackCeiling||max4(refSensor)>=deepShadowPackCeiling){
        imageStore(outCfa,p,merged);
        imageStore(outSemanticWeight,p,vec4(0.0));
        return;
    }
    vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize); vec4 fs=texture(flowTexture,uv);
    float cancelled=step(0.5,fs.w);
    float flowConfidence=(1.0-cancelled)*exp(-80.0*max(fs.z,0.0));
    vec2 source=vec2(p)+vec2(0.5)+fs.xy;
    if(source.x<0.0||source.y<0.0||source.x>=float(packedSize.x)||source.y>=float(packedSize.y)){
        atomicAdd(shadowDiag[6],1u); imageStore(outCfa,p,merged);
        imageStore(outSemanticWeight,p,vec4(0.0)); return;
    }
    if(flowConfidence<minimumFlowConfidence){
        atomicAdd(shadowDiag[3],1u); imageStore(outCfa,p,merged);
        imageStore(outSemanticWeight,p,vec4(0.0)); return;
    }
    float corrErr,corrSupport;
    if(!validateReferenceOwnedCorrespondence(p,source,corrErr,corrSupport)){
        atomicAdd(shadowDiag[7],1u); imageStore(outCfa,p,merged);
        imageStore(outSemanticWeight,p,vec4(0.0)); return;
    }
    atomicAdd(shadowDiag[2],1u);
    vec4 sh=phaseSafeShadow(source); vec4 shEqSensor=sh*shadowToNormalScale;
    vec4 shEq=shEqSensor*referenceExposureScale; vec4 outv=merged; bool any=false;
    vec4 semanticPhaseWeight=vec4(0.0);
    float corrConf=1.0-smoothstep(0.06,0.10,corrErr);
    for(int phase=0;phase<4;++phase){
        if(mergedSensor[phase]>=deepShadowThreshold||refSensor[phase]>=deepShadowPackCeiling)continue;
        atomicAdd(shadowDiag[0],1u);
        if(mergedSensor[phase]<minimumShadowSignal||refSensor[phase]<minimumShadowSignal||shEqSensor[phase]<minimumShadowSignal)continue;
        atomicAdd(shadowDiag[1],1u);
        if(sh[phase]>=shadowClipThreshold){atomicAdd(shadowDiag[4],1u);continue;}
        float radiometric=abs(refSensor[phase]-shEqSensor[phase])/max(refSensor[phase],0.020);
        if(radiometric>0.22){atomicAdd(shadowDiag[8],1u);continue;}
        float sup=phaseSupport(p,phase);
        if(sup<=1.25)atomicAdd(shadowDiag[10],1u);else if(sup<=4.5)atomicAdd(shadowDiag[11],1u);else atomicAdd(shadowDiag[12],1u);
        float requiredRatio=max(1.50,requiredExposureSupportRatio*sup);
        if(shadowExposureRatio<requiredRatio){atomicAdd(shadowDiag[9],1u);continue;}
        float benefit=smoothstep(requiredRatio,min(4.0,requiredRatio+0.75),shadowExposureRatio);
        float blend=maxShadowBlend*corrConf*max(benefit,0.25);
        blend=clamp(blend,0.0,maxShadowBlend);
        outv[phase]=mix(merged[phase],shEq[phase],blend);
        semanticPhaseWeight[phase]=blend;
        atomicAdd(shadowDiag[5],1u); atomicAdd(shadowDiag[16+phase],1u); any=true;
    }
    if(any)atomicAdd(shadowDiag[13],1u);
    imageStore(outCfa,p,max(outv,vec4(0.0)));
    /* IRIS_26501_SHADOW_VALIDATED_SEMANTIC_WEIGHT
     * Reuse the exact reference-owned correspondence/SNR decision phase by phase as
     * the native shadow RAW semantic authority. One accepted phase never authorizes another.
     * The helper CFA is never color input. */
    imageStore(outSemanticWeight,p,semanticPhaseWeight);
}
