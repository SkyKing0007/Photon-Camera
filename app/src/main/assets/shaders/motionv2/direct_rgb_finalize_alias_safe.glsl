#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(rgba16f, binding = 0) uniform highp readonly image2D currentRgb;
layout(rgba16f, binding = 1) uniform highp readonly image2D currentFrameSupport;
layout(rgba16f, binding = 2) uniform highp writeonly image2D outRgb;

/*
 * IRIS_26450_ALIAS_AWARE_CHROMA_FINALIZER
 *
 * Preserve center green exactly. Only constrain R-G / B-G bandwidth when
 * one-pixel green structure is strong, two-pixel structure returns toward the
 * center (near-Nyquist periodicity), and chroma itself oscillates abnormally.
 */

ivec2 clampPos(ivec2 p, ivec2 sz) {
    return clamp(p,ivec2(0),sz-ivec2(1));
}

vec3 loadRgb(ivec2 p, ivec2 sz) {
    return max(imageLoad(currentRgb,clampPos(p,sz)).rgb,vec3(0.0));
}

vec2 chromaRG_BG(vec3 v) {
    return vec2(v.r-v.g,v.b-v.g);
}

void main() {
    ivec2 xy=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(outRgb);
    if(any(greaterThanEqual(xy,sz))) return;

    vec3 center=loadRgb(xy,sz);
    float g0=center.g;
    vec2 c0=chromaRG_BG(center);

    ivec2 d1[4]=ivec2[4](
            ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
    ivec2 d2[4]=ivec2[4](
            ivec2(2,0),ivec2(-2,0),ivec2(0,2),ivec2(0,-2));

    float firstStep=0.0;
    float secondStep=0.0;
    vec2 chromaSum=vec2(0.0);
    float chromaWeight=0.0;

    for(int i=0;i<4;i++) {
        vec3 n1=loadRgb(xy+d1[i],sz);
        vec3 n2=loadRgb(xy+d2[i],sz);

        firstStep += abs(n1.g-g0);
        secondStep += abs(n2.g-g0);

        float guideScale=0.020+0.16*max(g0,n1.g);
        float guideResidual=abs(n1.g-g0)/max(guideScale,1.0e-5);
        float w=exp(-1.35*guideResidual);
        chromaSum += chromaRG_BG(n1)*w;
        chromaWeight += w;
    }

    firstStep *= 0.25;
    secondStep *= 0.25;

    vec2 localChroma =
            chromaWeight > 1.0e-4
                    ? chromaSum/chromaWeight
                    : c0;

    float signalScale=0.018+0.18*max(g0,0.05);
    float hf1=firstStep/max(signalScale,1.0e-5);
    float hf2=secondStep/max(signalScale,1.0e-5);

    float onePixelEnergy=smoothstep(0.70,2.20,hf1);
    float twoPixelReturn=1.0-smoothstep(0.55,1.90,hf2);
    float periodicRisk=onePixelEnergy*twoPixelReturn;

    float chromaScale =
            0.012
            + 0.10*max(g0,0.04)
            + 0.30*length(localChroma);
    float chromaResidual =
            length(c0-localChroma)/max(chromaScale,1.0e-5);
    float chromaOscillation=smoothstep(0.55,1.75,chromaResidual);

    float aliasRisk=clamp(periodicRisk*chromaOscillation,0.0,1.0);
    float chromaBlend=0.82*aliasRisk;
    vec2 safeChroma=mix(c0,localChroma,chromaBlend);

    vec3 safeRgb=vec3(
            max(g0+safeChroma.x,0.0),
            g0,
            max(g0+safeChroma.y,0.0));

    float frameSupport=max(imageLoad(currentFrameSupport,xy).r,1.0);
    imageStore(outRgb,xy,vec4(safeRgb,frameSupport));
}