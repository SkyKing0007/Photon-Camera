#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uRgb;
uniform sampler2D uMask;
uniform sampler2D uSmall;
uniform sampler2D uBigQuarter;
uniform ivec2 uSize;
uniform float uYFloor;
uniform float uAThreshold;
uniform float uNeutralRms;
uniform float uCoherenceThreshold;
uniform float uDirectionCosThreshold;
uniform vec3 uCalculationWb;
layout(location=0) out vec4 oColor;
vec2 safeFill(vec4 v){ return v.b>1.0e-3 ? v.rg/v.b : vec2(0.0); }
float dirCos(vec2 a,vec2 b){
    float na=length(a), nb=length(b);
    if(na<1.0e-6 || nb<1.0e-6) return 1.0;
    return dot(a,b)/(na*nb);
}
float maskAt(ivec2 q){
    ivec2 hi=max(uSize-ivec2(1),ivec2(0));
    return texelFetch(uMask,clamp(q,ivec2(0),hi),0).r;
}
float inwardRegularizedMask(ivec2 p,float center){
    float crossSum=maskAt(p+ivec2(-1,0))+maskAt(p+ivec2(1,0))+maskAt(p+ivec2(0,-1))+maskAt(p+ivec2(0,1));
    float cornerSum=maskAt(p+ivec2(-1,-1))+maskAt(p+ivec2(1,-1))+maskAt(p+ivec2(-1,1))+maskAt(p+ivec2(1,1));
    float tent=(4.0*center+2.0*crossSum+cornerSum)*(1.0/16.0);
    return min(center,tent);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float centerMask=texelFetch(uMask,p,0).r;
    float m=inwardRegularizedMask(p,centerMask);
    float own=smoothstep(0.55,0.95,m);
    if(own<=0.0) discard;
    vec4 src=texelFetch(uRgb,p,0); vec3 rgb=src.rgb*uCalculationWb;
    float y=(rgb.r+2.0*rgb.g+rgb.b)*0.25; float yc=max(y,uYFloor);
    vec2 c=vec2(rgb.r-rgb.g,rgb.b-rgb.g)/yc;
    vec4 sm=texelFetch(uSmall,p,0);
    vec2 uv=(vec2(p)+vec2(0.5))/vec2(uSize);
    vec4 bg=texture(uBigQuarter,uv);
    vec2 cs=safeFill(sm), cb=safeFill(bg);
    float smallSupport=clamp(sm.b/max(uAThreshold,1.0e-4),0.0,1.0);
    float broadSupport=clamp(bg.b/max(uAThreshold,1.0e-4),0.0,1.0);
    float support=min(smallSupport,broadSupport);
    float srcMag=length(c), smallMag=length(cs), broadMag=length(cb);
    float donorCos=dirCos(cs,cb);
    float sourceSmallCos=dirCos(c,cs);
    float sourceBroadCos=dirCos(c,cb);
    float magRatio=min(smallMag,broadMag)/max(max(smallMag,broadMag),1.0e-6);
    bool sourceHasHue=srcMag>uNeutralRms;
    bool donorCoherent=support>=0.999 && donorCos>=uDirectionCosThreshold && magRatio>=uCoherenceThreshold;
    bool sourceHueAgrees=sourceHasHue && sourceSmallCos>=uDirectionCosThreshold && sourceBroadCos>=uDirectionCosThreshold;
    bool preserveHue=donorCoherent && sourceHueAgrees;
    float agreedMag=max(uNeutralRms,min(smallMag,broadMag));
    float trustedMag=min(srcMag,agreedMag);
    float untrustedFloor=0.25*uNeutralRms;

    /* IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF
     * 26840 still had a binary confidence cliff: anything short of strict source+small+broad
     * consensus collapsed almost to neutral. That stripped genuine foliage, ground, rails
     * and painted material of color exactly where clipping confidence became uncertain.
     * Keep the successful 26839 source-hue ownership contract, but make magnitude confidence
     * continuous. The small neighborhood is the primary same-material evidence; broad/donor
     * evidence may raise saturation confidence but can never rotate hue. */
    float localHueTrust=sourceHasHue
            ? smallSupport*smoothstep(0.80,uDirectionCosThreshold,sourceSmallCos)
            : 0.0;
    float broadHueTrust=sourceHasHue
            ? broadSupport*smoothstep(0.72,uDirectionCosThreshold,sourceBroadCos)
            : 0.0;
    float donorMagnitudeTrust=
            smoothstep(0.72,uDirectionCosThreshold,donorCos)*
            smoothstep(0.65,uCoherenceThreshold,magRatio);
    float secondaryTrust=max(broadHueTrust,donorMagnitudeTrust);
    float partialTrust=clamp(localHueTrust*(0.48+0.52*secondaryTrust),0.0,1.0);
    float localMagnitude=max(untrustedFloor,min(srcMag,max(uNeutralRms,smallMag)));
    float partialTargetMag=mix(untrustedFloor,localMagnitude,partialTrust);
    float targetMag=preserveHue ? trustedMag : min(srcMag,partialTargetMag);
    float rolloffMag=mix(srcMag,targetMag,own);
    vec2 alongSource=(srcMag>1.0e-6) ? c*(rolloffMag/srcMag) : vec2(0.0);

    /* Never turn a still-colored clipped pixel gray/warm merely because broad confidence
     * is weak. The warm terminal is reserved for a truly hue-less deepest core only. */
    float sourceHueGone=1.0-smoothstep(0.65*uNeutralRms,1.35*uNeutralRms,srcMag);
    float terminal=smoothstep(0.94,0.999,m)*sourceHueGone;
    vec2 warmFallback=vec2(0.25,-0.65)*uNeutralRms;
    vec2 cp=mix(alongSource,warmFallback,terminal);
    float dR=cp.x*yc, dB=cp.y*yc;
    float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);
    vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));
    oColor=vec4(cameraDst,src.a);
}
