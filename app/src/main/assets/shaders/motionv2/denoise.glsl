precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float effectiveSupport;
out vec3 Output;

/*
 * IRIS_26430_LIGHT_SUPPORT_OWNED_RESIDUAL_CLEANUP
 *
 * The 26429 temporal reconstruction is the primary denoiser.
 *
 * This stage:
 * - consumes no Photon noiseS/noiseO/noiseRstr state;
 * - uses a 3x3 edge-aware neighborhood instead of the old 5x5 cleanup;
 * - applies only small luma/chroma residual correction;
 * - protects detail and bright highlights;
 * - performs no sharpening.
 */

float luminance(vec3 c) {
    return dot(c,vec3(0.2126,0.7152,0.0722));
}

void main() {
    ivec2 p=ivec2(gl_FragCoord.xy);
    ivec2 sz=textureSize(InputBuffer,0);
    vec3 c=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
    float y0=max(luminance(c),0.0);

    float supportConfidence=
            clamp((effectiveSupport-2.0)/8.0,0.0,1.0);

    float yMin=y0;
    float yMax=y0;
    float sumW=0.0;
    float sumG=0.0;
    float sumRG=0.0;
    float sumBG=0.0;

    /*
     * 3x3 only. Neighbor rejection is driven by already-transformed luminance,
     * not by generic Photon noise tuning.
     */
    float edgeScale=0.018+0.070*sqrt(max(y0,0.0));

    for(int oy=-1;oy<=1;oy++) {
        for(int ox=-1;ox<=1;ox++) {
            ivec2 q=clamp(
                    p+ivec2(ox,oy),
                    ivec2(0),
                    sz-ivec2(1));
            vec3 s=max(texelFetch(InputBuffer,q,0).rgb,vec3(0.0));
            float ys=max(luminance(s),0.0);

            yMin=min(yMin,ys);
            yMax=max(yMax,ys);

            float dy=abs(ys-y0);
            float edgeWeight=exp(
                    -0.5*dy*dy/
                    max(edgeScale*edgeScale,1.0e-6));
            float spatial=
                    (ox==0 && oy==0) ? 1.0 :
                    ((ox==0 || oy==0) ? 0.72 : 0.50);
            float w=edgeWeight*spatial;

            sumW+=w;
            sumG+=w*s.g;
            sumRG+=w*(s.r-s.g);
            sumBG+=w*(s.b-s.g);
        }
    }

    float invW=1.0/max(sumW,1.0e-6);
    float filteredG=sumG*invW;
    float filteredRG=sumRG*invW;
    float filteredBG=sumBG*invW;

    float localRange=max(yMax-yMin,0.0);
    float detailThreshold=0.010+0.075*y0;
    float detailEvidence=smoothstep(
            detailThreshold,
            3.0*detailThreshold+0.002,
            localRange);

    /*
     * At strong temporal support:
     *   flat luma <= ~1.5%, detailed luma <= ~0.3%
     *   flat chroma <= ~5%,   detailed chroma <= ~1.5%
     *
     * At weak support the residual cleanup rises gently, but never approaches
     * the old 26411/26423 30-90% chroma filtering.
     */
    /*
     * IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP
     *
     * 26436 remained visibly soft. The owned reference-edge anchor now protects
     * real high-frequency geometry upstream, so this residual cleanup becomes
     * still lighter. This is preservation, not an unsharp-mask/sharpen pass.
     */
    float flatLuma=mix(0.028,0.008,supportConfidence);
    float detailLuma=mix(0.006,0.001,supportConfidence);
    float lumaStrength=mix(
            flatLuma,
            detailLuma,
            detailEvidence);

    float flatChroma=mix(0.12,0.035,supportConfidence);
    float detailChroma=mix(0.040,0.008,supportConfidence);
    float chromaStrength=mix(
            flatChroma,
            detailChroma,
            detailEvidence);

    /*
     * IRIS_26453_STRUCTURAL_EDGE_CHROMA_PROTECTION
     *
     * 26452 live audit proved that this residual stage spatially averages
     * opponent chroma (R-G / B-G) over a 3x3 neighborhood. That is desirable
     * in smooth low-detail regions, but on thin white text, reflective metal
     * and high-contrast edges it can widen a small upstream CFA/demosaic color
     * disagreement into a more visible cyan/magenta footprint.
     *
     * Do not increase chroma denoise. Instead fade this residual chroma mixing
     * toward zero as the already-computed local luminance range proves that the
     * pixel belongs to structural detail. Luma cleanup remains unchanged.
     *
     * At a strong edge:
     *   weak-support detail chroma 4.0% -> as low as 0.32%
     *   strong-support detail chroma 0.8% -> as low as 0.064%
     *
     * Flat-region chroma cleanup is unchanged.
     */
    float structuralEdgeProtect=smoothstep(
            0.55*detailThreshold,
            1.70*detailThreshold+0.001,
            localRange);
    chromaStrength*=1.0-0.92*structuralEdgeProtect;

    /*
     * Never smear color back across bright clipping boundaries.
     */
    float highlightProtect=smoothstep(0.65,0.95,y0);
    lumaStrength*=1.0-0.92*highlightProtect;
    chromaStrength*=1.0-0.96*highlightProtect;

    float outG=mix(c.g,filteredG,lumaStrength);
    float rg=mix(c.r-c.g,filteredRG,chromaStrength);
    float bg=mix(c.b-c.g,filteredBG,chromaStrength);

    Output=max(
            vec3(outG+rg,outG,outG+bg),
            vec3(0.0));
}
