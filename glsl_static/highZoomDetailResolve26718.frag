#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uTemporalLumaStats;
uniform sampler2D uPhaseOccupancy;
uniform sampler2D uNativeVgnGuide;
uniform ivec2 uOutputOrigin;
uniform ivec2 uOutputFullSize;
uniform ivec2 uGuideSize;
layout(location = 0) out vec4 oDetailAndDiagnostic;

float irisSmooth01(float x) {
    float t=clamp(x,0.0,1.0);
    return t*t*(3.0-2.0*t);
}
float irisLuma(vec3 v) { return 0.25*v.r+0.50*v.g+0.25*v.b; }
float irisGuideY(ivec2 globalP) {
    vec2 s=clamp((vec2(globalP)+vec2(0.5))*0.5-vec2(0.5),
                 vec2(0.0),vec2(uGuideSize-ivec2(1)));
    ivec2 p0=ivec2(floor(s));
    ivec2 p1=min(p0+ivec2(1),uGuideSize-ivec2(1));
    vec2 f=s-vec2(p0);
    float a=irisLuma(texelFetch(uNativeVgnGuide,p0,0).rgb);
    float b=irisLuma(texelFetch(uNativeVgnGuide,ivec2(p1.x,p0.y),0).rgb);
    float c=irisLuma(texelFetch(uNativeVgnGuide,ivec2(p0.x,p1.y),0).rgb);
    float d=irisLuma(texelFetch(uNativeVgnGuide,p1,0).rgb);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
int irisPhaseCount(ivec2 localP) {
    vec4 phases=texelFetch(uPhaseOccupancy,localP,0);
    return (phases.r>0.0?1:0)+(phases.g>0.0?1:0)+
           (phases.b>0.0?1:0)+(phases.a>0.0?1:0);
}
float irisMeanY(ivec2 localP) {
    vec4 m=texelFetch(uTemporalLumaStats,localP,0);
    return m.z>0.08 ? max(m.x/m.z,0.0) : 0.0;
}
float irisTemporalAgreement(ivec2 localP) {
    vec4 m=texelFetch(uTemporalLumaStats,localP,0);
    float sumW=max(m.z,0.0), sumW2=max(m.w,0.0);
    if(sumW<=0.08||sumW2<=1.0e-6)return 0.0;
    float meanY=m.x/sumW;
    float varianceY=max(m.y/sumW-meanY*meanY,0.0);
    float effectiveN=(sumW*sumW)/max(sumW2,1.0e-6);
    float supportGate=irisSmooth01((effectiveN-1.50)/1.50);
    float relativeSigma=sqrt(varianceY)/max(abs(meanY),0.030);
    float stabilityGate=1.0-irisSmooth01((relativeSigma-0.060)/0.120);
    return clamp(supportGate*stabilityGate,0.0,1.0);
}
void main() {
    ivec2 localP=ivec2(gl_FragCoord.xy);
    ivec2 globalP=uOutputOrigin+localP;
    ivec2 globalBlock=(globalP/2)*2;
    ivec2 block=globalBlock-uOutputOrigin;
    ivec2 q00=block;
    ivec2 q10=block+ivec2(1,0);
    ivec2 q01=block+ivec2(0,1);
    ivec2 q11=block+ivec2(1,1);
    ivec2 cell=globalP-globalBlock;

    float y00=irisMeanY(q00), y10=irisMeanY(q10);
    float y01=irisMeanY(q01), y11=irisMeanY(q11);
    float directY=cell.y==0 ? (cell.x==0?y00:y10) : (cell.x==0?y01:y11);
    float lowY=max(0.25*(y00+y10+y01+y11),0.0);
    float guideY=max(irisGuideY(globalP),0.0);
    float guideBlockY=max(irisGuideY(globalBlock),0.0);

    int p00=irisPhaseCount(q00), p10=irisPhaseCount(q10);
    int p01=irisPhaseCount(q01), p11=irisPhaseCount(q11);
    int phaseCount=cell.y==0 ? (cell.x==0?p00:p10) : (cell.x==0?p01:p11);
    int blockPhaseCount=min(min(p00,p10),min(p01,p11));
    float phaseGate=blockPhaseCount>=4?1.0:(blockPhaseCount==3?0.85:(blockPhaseCount==2?0.0:0.0));
    float temporalGate=min(min(irisTemporalAgreement(q00),irisTemporalAgreement(q10)),
                           min(irisTemporalAgreement(q01),irisTemporalAgreement(q11)));
    float signalGate=irisSmooth01((guideBlockY-0.015)/0.055);
    float agreement=abs(log2((lowY+0.01)/(guideBlockY+0.01)));
    float agreementGate=1.0-irisSmooth01((agreement-0.08)/0.27);

    float g00=irisGuideY(globalBlock);
    float g10=irisGuideY(globalBlock+ivec2(1,0));
    float g01=irisGuideY(globalBlock+ivec2(0,1));
    float g11=irisGuideY(globalBlock+ivec2(1,1));
    float guideMin=min(min(g00,g10),min(g01,g11));
    float guideMax=max(max(g00,g10),max(g01,g11));
    float guideRange=(guideMax-guideMin)/max(guideBlockY,0.015);
    float edgeConservatism=irisSmooth01((guideRange-0.10)/0.45);
    float detailBound=mix(0.30,0.14,edgeConservatism);

    float denom=max(lowY,0.015);
    float d00=(y00-lowY)/denom, d10=(y10-lowY)/denom;
    float d01=(y01-lowY)/denom, d11=(y11-lowY)/denom;
    float directDetail=cell.y==0 ? (cell.x==0?d00:d10) : (cell.x==0?d01:d11);
    float maxAbs=max(max(abs(d00),abs(d10)),max(abs(d01),abs(d11)));
    float shapeScale=maxAbs>1.0e-6 ? min(1.0,detailBound/maxAbs) : 0.0;

    /* IRIS_26758_ADAPTIVE_FUSION_REJECTION
     * Paper-inspired hybrid rule applied to same-lens RAW evidence: uncertain alignment,
     * unsupported alternating row/column/checker energy, and flattened highlights fade
     * continuously to the native Sabre/VGN base instead of being forced into the output.
     * This is a detail veto only; it never changes RGB/chroma/highlight ownership.
     */
    float guideGradX=0.5*(abs(g10-g00)+abs(g11-g01))/max(guideBlockY,0.015);
    float guideGradY=0.5*(abs(g01-g00)+abs(g11-g10))/max(guideBlockY,0.015);
    float rowAlternation=0.5*abs((d00+d10)-(d01+d11));
    float colAlternation=0.5*abs((d00+d01)-(d10+d11));
    float checkerAlternation=0.5*abs((d00+d11)-(d10+d01));
    float unsupportedRow=rowAlternation*(1.0-irisSmooth01((guideGradY-0.035)/0.18));
    float unsupportedCol=colAlternation*(1.0-irisSmooth01((guideGradX-0.035)/0.18));
    float unsupportedChecker=checkerAlternation*(1.0-edgeConservatism);
    float aliasMetric=max(unsupportedChecker,max(unsupportedRow,unsupportedCol));
    float aliasGate=1.0-irisSmooth01((aliasMetric-0.10)/0.22);
    float highlightGate=1.0-irisSmooth01((guideMax-0.72)/0.20);
    float confidence=clamp(phaseGate*temporalGate*signalGate*agreementGate*aliasGate*highlightGate,0.0,1.0);
    /* IRIS_26759_CONFIDENCE_GATED_ZOOM_DETAIL_REINFORCEMENT
     * Same policy as true-2x Super Res: only strongly supported luma microstructure receives
     * extra detail/microcontrast. Alias/alignment/highlight rejection stays authoritative,
     * and the combined gain is capped at 2x before the inherited +/-0.56 EV sidecar bound.
     */
    float structuralDetail=irisSmooth01((abs(directDetail)-0.020)/0.120);
    float provenStructure=structuralDetail*irisSmooth01((confidence-0.30)/0.55);
    float strongConfidence=irisSmooth01((confidence-0.58)/0.30);
    float detailReinforcement=1.0+provenStructure*strongConfidence;
    float microcontrastGain=1.0+0.36*provenStructure;
    float combinedDetailGain=min(2.0,detailReinforcement*microcontrastGain);
    float boundedDetail=directDetail*shapeScale*confidence*combinedDetailGain;
    float factor=max(1.0+boundedDetail,0.68);
    float logDetail=confidence>0.02 ? clamp(log2(factor),-0.56,0.56) : 0.0;

    int reasonClass=0;
    if(blockPhaseCount<3)reasonClass=6;
    else if(temporalGate<=0.02)reasonClass=3;
    else if(highlightGate<=0.001)reasonClass=4;
    else if(agreementGate<=0.02 || aliasGate<=0.02)reasonClass=5;
    else if(signalGate<=0.02)reasonClass=7;
    else if(confidence>=0.50)reasonClass=2;
    else if(confidence>0.02)reasonClass=1;
    oDetailAndDiagnostic=vec4(logDetail,float(phaseCount*8+reasonClass),guideY,1.0);
}
