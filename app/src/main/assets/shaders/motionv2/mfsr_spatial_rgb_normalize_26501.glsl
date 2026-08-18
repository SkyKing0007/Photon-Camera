precision highp float;
precision highp int;

uniform highp sampler2D semanticAccumulator;
uniform highp sampler2D opponentWeightAccumulator;
uniform highp sampler2D fallbackCfa;
uniform highp sampler2D highlightProvenance;
uniform highp sampler2D lensShadingMap;
uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform vec3 cameraDomainScale;
uniform int useLensShading;
out vec4 Output;

/* IRIS_26502_STACK_AWARE_SEMANTIC_NORMALIZE
 * Keep V6 green/luma structure and one final normalization. Only R-G/B-G residuals
 * are locally regularized, using the actual semantic denominators accumulated by
 * the admitted Wronski/Short-A path. Packed highlight provenance remains a hard
 * safety/reliability hint; it no longer directly paints a visible neutral patch.
 */
const float SUPPORT_EPS=1.0e-7;
float phaseDivisor(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float packedCensoredFraction(ivec2 packedP){
    packedP=clamp(packedP,ivec2(0),packedSize-ivec2(1));
    float code=texelFetch(highlightProvenance,packedP,0).r;
    float count=0.0;
    for(int q=0;q<4;++q){
        float state=mod(floor(code/phaseDivisor(q)),3.0);
        count+=abs(state-1.0)<0.25?1.0:0.0;
    }
    return 0.25*count;
}
float smoothCensoredFraction(ivec2 rawP){
    vec2 packedPosition=0.5*vec2(rawP)-vec2(0.5);
    ivec2 lo=ivec2(floor(packedPosition));
    ivec2 hi=lo+ivec2(1);
    vec2 f=fract(packedPosition);
    float a=packedCensoredFraction(lo);
    float b=packedCensoredFraction(ivec2(hi.x,lo.y));
    float c=packedCensoredFraction(ivec2(lo.x,hi.y));
    float d=packedCensoredFraction(hi);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
float packedNeutralAt(ivec2 packedP){
    packedP=clamp(packedP,ivec2(0),packedSize-ivec2(1));
    vec4 v=max(texelFetch(fallbackCfa,packedP,0),vec4(0.0));
    return max(max(v.r,v.g),max(v.b,v.a));
}
float neutralFallback(ivec2 rawP){
    vec2 packedPosition=(vec2(rawP)+vec2(0.5))*0.5-vec2(0.25);
    vec2 p=packedPosition-vec2(0.5);
    ivec2 lo=ivec2(floor(p));
    vec2 f=fract(p);
    ivec2 hi=lo+ivec2(1);
    float a=packedNeutralAt(lo);
    float b=packedNeutralAt(ivec2(hi.x,lo.y));
    float c=packedNeutralAt(ivec2(lo.x,hi.y));
    float d=packedNeutralAt(hi);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
vec3 lensShadingRgb(ivec2 rawP){
    if(useLensShading==0)return vec3(1.0);
    vec2 uv=(vec2(rawP)+vec2(0.5))/vec2(rawSize);
    vec4 g=texture(lensShadingMap,clamp(uv,vec2(0.0),vec2(1.0)));
    return max(vec3(g.r,0.5*(g.g+g.b),g.a),vec3(0.0));
}
float opponentSupportQuality(float greenWeight,float opponentWeight){
    if(greenWeight<=SUPPORT_EPS||opponentWeight<=SUPPORT_EPS)return 0.0;
    /* Healthy 3x3 Bayer sampling supplies roughly >=0.3 opponent support per unit
     * green support. The ratio is frame-count invariant and exposes local dropouts. */
    return clamp(opponentWeight/max(0.30*greenWeight,SUPPORT_EPS),0.0,1.0);
}
void accumulateNeighborOpponent(
        ivec2 q,float centerGreen,float spatialWeight,
        inout vec2 opponentSums,inout vec2 neighborWeightSums){
    if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,rawSize)))return;
    vec4 neighborSemantic=texelFetch(semanticAccumulator,q,0);
    vec2 neighborOpponentWeight=texelFetch(opponentWeightAccumulator,q,0).rg;
    if(neighborSemantic.a<=SUPPORT_EPS)return;
    float neighborGreen=neighborSemantic.r/neighborSemantic.a;
    float sigma=max(0.004,0.035*max(centerGreen,0.02));
    float z=(neighborGreen-centerGreen)/sigma;
    float edgeWeight=exp(-0.5*z*z)*spatialWeight;
    if(neighborOpponentWeight.r>SUPPORT_EPS){
        float qualityR=opponentSupportQuality(neighborSemantic.a,neighborOpponentWeight.r);
        float wR=edgeWeight*qualityR;
        opponentSums.r+=(neighborSemantic.g/neighborOpponentWeight.r)*wR;
        neighborWeightSums.r+=wR;
    }
    if(neighborOpponentWeight.g>SUPPORT_EPS){
        float qualityB=opponentSupportQuality(neighborSemantic.a,neighborOpponentWeight.g);
        float wB=edgeWeight*qualityB;
        opponentSums.g+=(neighborSemantic.b/neighborOpponentWeight.g)*wB;
        neighborWeightSums.g+=wB;
    }
}
float opponentAgreement(float centerOpponent,float localOpponent,float green,float centerQuality){
    float threshold=max(0.010,0.25*max(green,0.02));
    float chromaEdge=smoothstep(threshold,2.5*threshold,abs(centerOpponent-localOpponent));
    /* Strong center evidence protects real equal-luma color edges. Weak evidence is
     * allowed to follow the local consensus because it is exactly the noisy case. */
    return 1.0-centerQuality*chromaEdge;
}
float localEvidenceQuality(float neighborWeightSum){
    return smoothstep(0.25,1.75,neighborWeightSum);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,rawSize))){Output=vec4(0.0);return;}
    vec4 semantic=texelFetch(semanticAccumulator,p,0);
    vec4 opponentWeights=texelFetch(opponentWeightAccumulator,p,0);
    float gWeight=semantic.a;
    float rWeight=opponentWeights.r;
    float bWeight=opponentWeights.g;
    float green=gWeight>SUPPORT_EPS?semantic.r/gWeight:0.0;
    bool centerRPresent=rWeight>SUPPORT_EPS;
    bool centerBPresent=bWeight>SUPPORT_EPS;
    float centerRg=centerRPresent?semantic.g/rWeight:0.0;
    float centerBg=centerBPresent?semantic.b/bWeight:0.0;
    float centerQr=opponentSupportQuality(gWeight,rWeight);
    float centerQb=opponentSupportQuality(gWeight,bWeight);

    /* IRIS_26502_NEIGHBOR_OPPONENT_REPAIR
     * Gather only already-admitted semantic evidence. No unaligned RAW fallback is
     * introduced here: unsafe auxiliary pixels never entered these accumulators. */
    vec2 opponentSums=vec2(0.0);
    vec2 neighborWeightSums=vec2(0.0);
    accumulateNeighborOpponent(p+ivec2(-1, 0),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1, 0),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 0,-1),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 0, 1),green,1.0,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2(-1,-1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1,-1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2(-1, 1),green,0.70710678,opponentSums,neighborWeightSums);
    accumulateNeighborOpponent(p+ivec2( 1, 1),green,0.70710678,opponentSums,neighborWeightSums);
    bool localRPresent=neighborWeightSums.r>SUPPORT_EPS;
    bool localBPresent=neighborWeightSums.g>SUPPORT_EPS;
    float localRg=localRPresent?opponentSums.r/neighborWeightSums.r:centerRg;
    float localBg=localBPresent?opponentSums.g/neighborWeightSums.g:centerBg;
    float localQr=localEvidenceQuality(neighborWeightSums.r);
    float localQb=localEvidenceQuality(neighborWeightSums.g);

    float censored=smoothCensoredFraction(p);
    float neutral=neutralFallback(p);
    float physicalHighlight=max(max(green,neutral),0.0);
    float darkGate=1.0-smoothstep(0.018,0.085,max(green,0.0));
    float highlightGate=smoothstep(0.55,0.96,physicalHighlight)
            *smoothstep(0.10,0.90,censored);

    /* IRIS_26502_OPPONENT_SUPPORT_REGULARIZATION
     * Suppress low-signal chroma clumps before the large display lift. Green is never
     * blurred. Strongly supported true color edges resist the local opponent average. */
    float rShadowBlend=darkGate*mix(0.70,0.38,centerQr)
            *opponentAgreement(centerRg,localRg,green,centerQr)*localQr;
    float bShadowBlend=darkGate*mix(0.70,0.38,centerQb)
            *opponentAgreement(centerBg,localBg,green,centerQb)*localQb;
    float rHighlightRepair=highlightGate*(1.0-centerQr)*localQr;
    float bHighlightRepair=highlightGate*(1.0-centerQb)*localQb;
    float rBlend=localRPresent?max(rShadowBlend,rHighlightRepair):0.0;
    float bBlend=localBPresent?max(bShadowBlend,bHighlightRepair):0.0;
    float rg=centerRPresent?mix(centerRg,localRg,clamp(rBlend,0.0,1.0))
            :(localRPresent?localRg:0.0);
    float bg=centerBPresent?mix(centerBg,localBg,clamp(bBlend,0.0,1.0))
            :(localBPresent?localBg:0.0);
    float finalQr=max(centerRPresent?centerQr:0.0,localRPresent?localQr:0.0);
    float finalQb=max(centerBPresent?centerQb:0.0,localBPresent?localQb:0.0);
    vec3 calculationRgb=max(vec3(green+rg,green,green+bg),vec3(0.0));

    /* IRIS_26502_CONTINUOUS_HIGHLIGHT_RELIABILITY
     * Packed censor state no longer directly controls visible neutralization. Preserve
     * supported wall/object hue and converge to neutral only when highlight color is
     * still unsupported or the helper brightness is genuinely at the sensor endpoint. */
    float colorQuality=min(finalQr,finalQb);
    float unresolvedColor=1.0-smoothstep(0.20,0.70,colorQuality);
    float neutralMix=highlightGate*unresolvedColor;
    float exhaustedGate=smoothstep(0.970,0.995,neutral)
            *smoothstep(0.70,0.98,censored);
    neutralMix=max(neutralMix,exhaustedGate);
    if(gWeight<=SUPPORT_EPS)neutralMix=1.0;
    if(neutralMix>0.0){
        calculationRgb=mix(
                calculationRgb,vec3(max(neutral,green)),clamp(neutralMix,0.0,1.0));
    }

    calculationRgb*=lensShadingRgb(p);
    vec3 cameraRgb=calculationRgb*cameraDomainScale;
    Output=vec4(max(cameraRgb,vec3(0.0)),min(gWeight,65504.0));
}
