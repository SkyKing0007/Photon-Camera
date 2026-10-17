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
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float m=texelFetch(uMask,p,0).r;
    float own=smoothstep(0.55,0.85,m);
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
    float safeMag=min(srcMag,agreedMag);
    vec2 preserved=(srcMag>1.0e-6) ? c*(safeMag/srcMag) : vec2(0.0);
    /* Mild warm terminal axis: never white, cyan, teal, neon green, or arbitrary donor hue. */
    vec2 warmFallback=vec2(0.25,-0.65)*uNeutralRms;
    vec2 target=preserveHue ? preserved : warmFallback;
    vec2 cp=mix(c,target,own);
    float dR=cp.x*yc, dB=cp.y*yc;
    float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);
    vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));
    oColor=vec4(cameraDst,src.a);
}
