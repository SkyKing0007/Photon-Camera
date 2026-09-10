precision highp float;
precision mediump sampler2D;

uniform sampler2D Pyramid0;
uniform sampler2D Pyramid1;
uniform sampler2D Pyramid2;
uniform sampler2D Pyramid3;
uniform sampler2D Pyramid4;
uniform sampler2D Pyramid5;
uniform sampler2D Pyramid6;
uniform sampler2D Pyramid7;
out float Output;

/* IRIS_26620_MULTISCALE_LOCAL_LAPLACIAN_PRESENTATION
 * Work only in the scalar log-intensity guide. The coarsest illumination base
 * remains the exact 26614 global-tone result. Finer Laplacian bands may move
 * continuously toward their source contrast only when the global map compressed
 * them, only while their amplitude is in the detail/medium-structure regime,
 * and never beyond source contrast. This mirrors the Local-Laplacian principle
 * alpha=1 (detail preservation) while leaving large edges to the global tone map.
 * There is no semantic classifier, tile atlas, fine-structure amplification, or
 * per-channel color operation. */
const float IRIS_SIGMA_DETAIL_EV = 1.32192809489; /* log2(2.5), paper-style range scale */

vec2 levelSampleAligned(sampler2D tex,vec2 level0Coord,float scale){
    vec2 sz=vec2(textureSize(tex,0));
    vec2 coord=level0Coord*scale;
    vec2 uv=(coord+vec2(0.5))/max(sz,vec2(1.0));
    vec2 lo=vec2(0.5)/max(sz,vec2(1.0));
    return texture(tex,clamp(uv,lo,vec2(1.0)-lo)).rg;
}

float preserveCompressedBand(float mappedBand,float sourceBand,float scaleWeight){
    float am=abs(mappedBand);
    float as=abs(sourceBand);
    float compression=max(as-am,0.0);
    float denom=max(am*as,1.0e-6);
    float signAgreement=(mappedBand*sourceBand)/denom;
    float signGate=smoothstep(0.75,0.98,signAgreement);
    float compressionGate=smoothstep(0.02,0.15,compression);
    float detailGate=1.0-smoothstep(0.75*IRIS_SIGMA_DETAIL_EV,
                                    1.25*IRIS_SIGMA_DETAIL_EV,as);
    float blend=clamp(scaleWeight*signGate*compressionGate*detailGate,0.0,1.0);
    return mix(mappedBand,sourceBand,blend);
}

float softLimit(float x,float limitValue){
    float a=abs(x);
    return x/(1.0+a/max(limitValue,1.0e-6));
}

void main(){
    /* Every reduce pass is phase-anchored at input index 2*q. Reconstruct all
     * coarser levels at that same level-0 sample location; using one normalized
     * UV for unequal/ceil-sized levels would introduce a half-pixel pyramid drift. */
    vec2 level0Coord=gl_FragCoord.xy-vec2(0.5);
    vec2 p0=levelSampleAligned(Pyramid0,level0Coord,1.0);
    vec2 p1=levelSampleAligned(Pyramid1,level0Coord,0.5);
    vec2 p2=levelSampleAligned(Pyramid2,level0Coord,0.25);
    vec2 p3=levelSampleAligned(Pyramid3,level0Coord,0.125);
    vec2 p4=levelSampleAligned(Pyramid4,level0Coord,0.0625);
    vec2 p5=levelSampleAligned(Pyramid5,level0Coord,0.03125);
    vec2 p6=levelSampleAligned(Pyramid6,level0Coord,0.015625);
    vec2 p7=levelSampleAligned(Pyramid7,level0Coord,0.0078125);

    float source0=p0.r;
    float mapped0=p0.g;
    float outLog=p7.g;

    /* Approximate source-pixel bands: 128-256, 64-128, 32-64, 16-32,
     * 8-16, 4-8 and 2-4. The finest band stays exactly global-tone mapped;
     * the coarsest >~256 px illumination remains the global exposure anchor. */
    outLog+=preserveCompressedBand(p6.g-p7.g,p6.r-p7.r,0.84);
    outLog+=preserveCompressedBand(p5.g-p6.g,p5.r-p6.r,0.78);
    outLog+=preserveCompressedBand(p4.g-p5.g,p4.r-p5.r,0.68);
    outLog+=preserveCompressedBand(p3.g-p4.g,p3.r-p4.r,0.54);
    outLog+=preserveCompressedBand(p2.g-p3.g,p2.r-p3.r,0.38);
    outLog+=preserveCompressedBand(p1.g-p2.g,p1.r-p2.r,0.18);
    outLog+=preserveCompressedBand(p0.g-p1.g,p0.r-p1.r,0.00);

    float correctionEv=outLog-mapped0;
    /* Deep shadows remain on the exact 26614 global map. The transition is
     * smooth in rendered luminance and introduces no black offset. */
    float mappedGuide=exp2(mapped0);
    float shadowPreserve=smoothstep(0.020,0.080,mappedGuide);
    correctionEv*=shadowPreserve;
    /* IRIS_26620_BLACK_CRUSH_PROTECTION
     * Negative local contrast restoration is introduced more conservatively through
     * the lower rendered body so the multiscale stage cannot deepen 26614 shadows
     * abruptly. Positive recovery keeps the original symmetric floor gate. */
    if(correctionEv<0.0){
        correctionEv*=smoothstep(0.080,0.200,mappedGuide);
    }
    /* Symmetric smooth bound; zero stays exactly zero and no hard threshold
     * exists in source brightness or highlight position. */
    correctionEv=softLimit(correctionEv,0.55);
    if(!isnan(source0) && !isinf(source0) && !isnan(correctionEv) && !isinf(correctionEv)){
        Output=correctionEv;
    }else{
        Output=0.0;
    }
}
