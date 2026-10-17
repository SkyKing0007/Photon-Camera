#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uBayerAndWeight;
uniform ivec2 uOutputSize;
uniform float uOutputExposureScale;
uniform int uCfaPattern26786;
uniform int uNeutralClamp26786;
uniform vec3 uAsShotNeutral26786;
layout(location = 0) out highp uint oBayer16;
int redPhase26786() { return uCfaPattern26786; }
int bluePhase26786() { return 3 - uCfaPattern26786; }

/* IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER
 * Preserve Bayer CFA publication and the exact quad-average neutral radiance. For a proven
 * neutral thin/high-frequency structure, R/G1/G2/B are jointly pulled toward that quad's
 * neutral mean. This fixes both edge fringes and full-body pink/blue fill when a distant
 * white stripe occupies only a few CFA sites. Real colored fine structure is protected by
 * two-neighbor same-hue persistence; alignment, temporal weights, LCA and normalDngMerge
 * remain untouched. */
int iris26821PhaseAt(ivec2 p) { return ((p.y & 1) << 1) + (p.x & 1); }
ivec2 iris26821PhaseOffset(int phase) { return ivec2(phase & 1, phase >> 1); }
ivec2 iris26821ClampPixel(ivec2 p) { return clamp(p,ivec2(0),uOutputSize-ivec2(1)); }
ivec2 iris26821ClampQuad(ivec2 q) {
    ivec2 qmax=max((uOutputSize-ivec2(1))/2,ivec2(0));
    return clamp(q,ivec2(0),qmax);
}
float iris26821ResolvedRaw(ivec2 p) {
    p=iris26821ClampPixel(p);
    vec2 sw=texelFetch(uBayerAndWeight,p,0).rg;
    return sw.x/max(sw.y,1.0e-8)*uOutputExposureScale;
}
float iris26821NeutralScaleForPhase(int phase) {
    if(phase==redPhase26786())return max(uAsShotNeutral26786.x,1.0e-6);
    if(phase==bluePhase26786())return max(uAsShotNeutral26786.z,1.0e-6);
    return max(uAsShotNeutral26786.y,1.0e-6);
}
float iris26821NeutralAt(ivec2 p) {
    p=iris26821ClampPixel(p);
    return iris26821ResolvedRaw(p)/iris26821NeutralScaleForPhase(iris26821PhaseAt(p));
}
vec4 iris26821NeutralQuad(ivec2 q){
    q=iris26821ClampQuad(q);ivec2 origin=q*2;
    int rp=redPhase26786();int bp=bluePhase26786();int g0=-1;int g1=-1;
    for(int phase=0;phase<4;phase++){
        if(phase!=rp&&phase!=bp){if(g0<0)g0=phase;else g1=phase;}
    }
    return vec4(
        iris26821NeutralAt(origin+iris26821PhaseOffset(rp)),
        iris26821NeutralAt(origin+iris26821PhaseOffset(g0)),
        iris26821NeutralAt(origin+iris26821PhaseOffset(g1)),
        iris26821NeutralAt(origin+iris26821PhaseOffset(bp)));
}
vec3 iris26821PhaseResidual(vec4 q){
    float g=0.5*(q.y+q.z);
    return vec3(q.x-g,q.w-g,0.5*(q.y-q.z));
}
float iris26821QuadMean(vec4 q){return 0.25*(q.x+q.y+q.z+q.w);}
float iris26821HueSupport(vec4 center,vec4 neighbor){
    float cg=0.5*(center.y+center.z);float ng=0.5*(neighbor.y+neighbor.z);
    vec2 cc=vec2(center.x-cg,center.w-cg);vec2 nc=vec2(neighbor.x-ng,neighbor.w-ng);
    float cm=length(cc);float nm=length(nc);
    float cGuide=max(iris26821QuadMean(center),0.03);float nGuide=max(iris26821QuadMean(neighbor),0.03);
    if(cm/cGuide<0.035||nm/nGuide<0.035)return 0.0;
    float align=dot(cc/max(cm,1.0e-7),nc/max(nm,1.0e-7));
    float lumaMatch=1.0-smoothstep(0.12,0.38,abs(iris26821QuadMean(center)-iris26821QuadMean(neighbor))/cGuide);
    return smoothstep(0.68,0.90,align)*smoothstep(0.035,0.10,nm/nGuide)*lumaMatch;
}
float iris26821NeutralPhaseCorrected(ivec2 p,float normalized,int phase){
    if(p.x<4||p.y<4||p.x>=uOutputSize.x-4||p.y>=uOutputSize.y-4)return normalized;
    ivec2 q=p/2;vec4 center=iris26821NeutralQuad(q);
    float qMean=iris26821QuadMean(center);float guide=max(qMean,0.03);
    if(qMean<0.025)return normalized;
    vec3 centerResidual=iris26821PhaseResidual(center);
    float phaseSpread=(max(max(center.x,center.y),max(center.z,center.w))-min(min(center.x,center.y),min(center.z,center.w)))/guide;
    float greenMismatch=abs(center.y-center.z)/guide;
    float gMean=0.5*(center.y+center.z);
    float rbMismatch=max(abs(center.x-gMean),abs(center.w-gMean))/guide;

    vec4 material=vec4(0.0);
    material+=iris26821NeutralQuad(q);
    material+=iris26821NeutralQuad(q+ivec2(-2,0));material+=iris26821NeutralQuad(q+ivec2(2,0));
    material+=iris26821NeutralQuad(q+ivec2(0,-2));material+=iris26821NeutralQuad(q+ivec2(0,2));
    material+=iris26821NeutralQuad(q+ivec2(-2,-2));material+=iris26821NeutralQuad(q+ivec2(2,-2));
    material+=iris26821NeutralQuad(q+ivec2(-2,2));material+=iris26821NeutralQuad(q+ivec2(2,2));
    material/=9.0;
    float materialGuide=max(iris26821QuadMean(material),0.03);
    float materialResidual=length(iris26821PhaseResidual(material))/materialGuide;
    float neutralMaterial=1.0-smoothstep(0.07,0.18,materialResidual);

    float best1=0.0;float best2=0.0;
    for(int oy=-1;oy<=1;oy++){
        for(int ox=-1;ox<=1;ox++){
            if(ox==0&&oy==0)continue;
            float support=iris26821HueSupport(center,iris26821NeutralQuad(q+ivec2(ox,oy)));
            if(support>best1){best2=best1;best1=support;}else if(support>best2){best2=support;}
        }
    }
    float coherentColorProtect=smoothstep(0.45,0.78,min(best1,best2));
    float phaseAlias=max(
        smoothstep(0.055,0.18,greenMismatch),
        smoothstep(0.075,0.24,rbMismatch));
    phaseAlias*=smoothstep(0.075,0.24,phaseSpread);
    float greenAlias=smoothstep(0.10,0.30,greenMismatch);
    float aliasStrength=max(phaseAlias,greenAlias)*neutralMaterial*(1.0-coherentColorProtect);
    aliasStrength*=smoothstep(0.025,0.060,qMean);
    /* IRIS_26821_DNG_NONIDENTIFIABLE_GREEN_PHASE_OVERRIDE
     * At CFA Nyquist, extreme G1/G2 disagreement plus full quad phase spread is not
     * identifiable as trustworthy scene chroma. Periodic Bayer alias can repeat the
     * same false hue in neighboring quads, so material/hue persistence must not veto
     * this specific sensor-domain anti-alias case. Preserve the WB-neutral quad mean
     * exactly; band-limit only the unidentifiable sub-quad chroma. */
    float nonIdentifiablePhase=
        smoothstep(0.38,0.78,greenMismatch)*
        smoothstep(0.35,0.80,phaseSpread)*
        smoothstep(0.025,0.060,qMean);
    aliasStrength=max(aliasStrength,nonIdentifiablePhase);
    aliasStrength=clamp(aliasStrength,0.0,1.0);
    if(aliasStrength<=1.0e-6)return normalized;

    float phaseScale=iris26821NeutralScaleForPhase(phase);
    float centerNeutral=normalized/phaseScale;
    /* Every phase in this quad computes the same strength/target. Therefore the neutral
     * quad mean is exactly preserved while only phase-colored disagreement is removed. */
    return mix(centerNeutral,qMean,aliasStrength)*phaseScale;
}

void main() {
    ivec2 p = clamp(
        ivec2(gl_FragCoord.xy),
        ivec2(0),
        uOutputSize - ivec2(1)
    );
    vec2 valueAndWeight = texelFetch(uBayerAndWeight, p, 0).rg;
    float normalized =
        valueAndWeight.x / max(valueAndWeight.y, 1.0e-8) *
        uOutputExposureScale;
    int phase26786 = ((p.y & 1) << 1) + (p.x & 1);
    normalized=iris26821NeutralPhaseCorrected(p,normalized,phase26786);
    if (uNeutralClamp26786 != 0) {
        int rPhase26786 = redPhase26786();
        int bPhase26786 = bluePhase26786();
        if (phase26786 == rPhase26786 || phase26786 == bPhase26786) {
            ivec2 q26786 = (p / 2) * 2;
            int g0 = -1; int g1 = -1;
            for (int phase = 0; phase < 4; ++phase) {
                if (phase != rPhase26786 && phase != bPhase26786) {
                    if (g0 < 0) g0 = phase; else g1 = phase;
                }
            }
            ivec2 gp0 = min(q26786 + ivec2(g0 & 1, g0 >> 1), uOutputSize - ivec2(1));
            ivec2 gp1 = min(q26786 + ivec2(g1 & 1, g1 >> 1), uOutputSize - ivec2(1));
            float gw0 = texelFetch(uBayerAndWeight, gp0, 0).g;
            float gw1 = texelFetch(uBayerAndWeight, gp1, 0).g;
            bool bothGreensFullyCensored26786 = gw0 <= 0.000051 && gw1 <= 0.000051;
            if (bothGreensFullyCensored26786) {
                float neutralLimit = phase26786 == rPhase26786
                    ? uAsShotNeutral26786.x / max(uAsShotNeutral26786.y, 1.0e-6)
                    : uAsShotNeutral26786.z / max(uAsShotNeutral26786.y, 1.0e-6);
                normalized = min(normalized, neutralLimit);
            }
        }
    }
    oBayer16 = uint(round(clamp(normalized, 0.0, 1.0) * 65535.0));
}
