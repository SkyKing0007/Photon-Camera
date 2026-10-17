#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uDirectRgb;
uniform sampler2D uPhaseOccupancy;
uniform sampler2D uTemporalLumaStats;
uniform sampler2D uNativeVgnGuide;
uniform ivec2 uOutputOrigin;
uniform ivec2 uOutputFullSize;
uniform ivec2 uGuideSize;
uniform float uChromaDenoiseStrength26762;
layout(location = 0) out vec4 oRenderRgb;

/* IRIS_26573_CROSS_FRAME_TRUE_DETAIL_LUMA_OWNER
 * Native Sabre/VGN remains the sole RGB/chroma/highlight and low-frequency identity owner.
 * Direct-CFA true2x contributes only temporally-proven zero-mean 2x2 intra-cell luminance structure. The
 * direct residual is zero-DC inside each 2x2 cell before the final per-pixel safety bound;
 * there is no broad sharpening kernel and no
 * direct-CFA chroma transfer. Unsafe block evidence produces the exact guide RGB.
 */
float irisSmooth01(float x) {
    float t = clamp(x, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}
float irisLuma(vec3 v) { return 0.25 * v.r + 0.50 * v.g + 0.25 * v.b; }
float irisPeak(vec3 v) { return max(v.r, max(v.g, v.b)); }
vec3 irisChroma(vec3 v) { return v / max(v.r + v.g + v.b, 1.0e-5); }
vec3 irisGuide(ivec2 globalP) {
    vec2 s = clamp((vec2(globalP) + vec2(0.5)) * 0.5 - vec2(0.5),
                   vec2(0.0), vec2(uGuideSize - ivec2(1)));
    ivec2 p0 = ivec2(floor(s));
    ivec2 p1 = min(p0 + ivec2(1), uGuideSize - ivec2(1));
    vec2 f = s - vec2(p0);
    vec3 a = texelFetch(uNativeVgnGuide, p0, 0).rgb;
    vec3 b = texelFetch(uNativeVgnGuide, ivec2(p1.x, p0.y), 0).rgb;
    vec3 c = texelFetch(uNativeVgnGuide, ivec2(p0.x, p1.y), 0).rgb;
    vec3 d = texelFetch(uNativeVgnGuide, p1, 0).rgb;
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}
/* IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE
 * Native Sabre/VGN remains the only chroma authority. Replace cross-edge bilinear chroma
 * mixing with a positive-weight same-material reconstruction while preserving the exact
 * bilinear guide luminance. The nearest native sample supplies a stable material side;
 * temporally-proven direct-CFA luma may refine that side only in proportion to SR confidence.
 * No direct-CFA chroma enters, no hue is invented, and the reconstructed chroma magnitude is
 * capped by the strongest of the four actually-supported native VGN samples.
 */
vec3 irisTopologyGuide(ivec2 globalP, vec3 bilinearGuide, float directY, float confidence,
                      out float materialBoundary) {
    vec2 s = clamp((vec2(globalP) + vec2(0.5)) * 0.5 - vec2(0.5),
                   vec2(0.0), vec2(uGuideSize - ivec2(1)));
    ivec2 p0 = ivec2(floor(s));
    ivec2 p1 = min(p0 + ivec2(1), uGuideSize - ivec2(1));
    vec2 f = s - vec2(p0);
    vec3 samples[4] = vec3[4](
        texelFetch(uNativeVgnGuide, p0, 0).rgb,
        texelFetch(uNativeVgnGuide, ivec2(p1.x, p0.y), 0).rgb,
        texelFetch(uNativeVgnGuide, ivec2(p0.x, p1.y), 0).rgb,
        texelFetch(uNativeVgnGuide, p1, 0).rgb);
    float spatial[4] = float[4](
        (1.0 - f.x) * (1.0 - f.y), f.x * (1.0 - f.y),
        (1.0 - f.x) * f.y, f.x * f.y);
    int nearestIndex = 0;
    for (int i = 1; i < 4; ++i) if (spatial[i] > spatial[nearestIndex]) nearestIndex = i;
    float sampleY[4];
    vec3 sampleChroma[4];
    float sampleChromaMagnitude[4];
    float maxYDelta = 0.0;
    float maxChromaMagnitude = 0.0;
    for (int i = 0; i < 4; ++i) {
        sampleY[i] = irisLuma(samples[i]);
        sampleChroma[i] = samples[i] - vec3(sampleY[i]);
        sampleChromaMagnitude[i] = length(sampleChroma[i]);
        maxChromaMagnitude = max(maxChromaMagnitude, sampleChromaMagnitude[i]);
    }
    for (int i = 0; i < 4; ++i) for (int j = i + 1; j < 4; ++j)
        maxYDelta = max(maxYDelta, abs(sampleY[i] - sampleY[j]));
    float bilinearY = max(irisLuma(bilinearGuide), 0.0);
    /* IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP
     * Direct-CFA remains luma-only. Its temporally proven 2x luma is used only to choose
     * which native VGN material side owns this output pixel. Cross-edge samples receive no
     * meaningful floor weight, preventing a colored native edge pixel from painting the
     * neighboring neutral glyph/background side. */
    float selectorY = mix(sampleY[nearestIndex], directY, 0.60 * confidence);
    vec3 topologyChroma = vec3(0.0);
    float weight = 0.0;
    float crossSideSpatial = 0.0;
    float localChromaOccupancy = 0.0;
    float neutralVotes = 0.0;
    int anchorIndex = nearestIndex;
    float anchorScore = -1.0;
    for (int i = 0; i < 4; ++i) {
        float relativeY = abs(sampleY[i] - selectorY) /
            max(max(abs(sampleY[i]), abs(selectorY)), 0.035);
        float sameMaterial = 1.0 - irisSmooth01((relativeY - 0.08) / 0.32);
        float materialWeight = sameMaterial * sameMaterial;
        float w = spatial[i] * (0.002 + 0.998 * materialWeight);
        topologyChroma += sampleChroma[i] * w;
        weight += w;
        crossSideSpatial += spatial[i] * (1.0 - sameMaterial);
        localChromaOccupancy += spatial[i] *
            irisSmooth01((sampleChromaMagnitude[i] - 0.020) / 0.055);
        neutralVotes += 1.0 - irisSmooth01((sampleChromaMagnitude[i] - 0.010) / 0.050);
        float score = spatial[i] * (0.15 + 0.85 * sameMaterial);
        if (score > anchorScore) { anchorScore = score; anchorIndex = i; }
    }
    topologyChroma /= max(weight, 1.0e-6);
    float topologyMagnitude = length(topologyChroma);
    if (topologyMagnitude > maxChromaMagnitude && topologyMagnitude > 1.0e-7)
        topologyChroma *= maxChromaMagnitude / topologyMagnitude;
    vec3 bilinearChroma = bilinearGuide - vec3(bilinearY);
    float edgeGate = irisSmooth01((maxYDelta - 0.018) / 0.095);
    float crossEdgeEvidence = irisSmooth01((crossSideSpatial - 0.06) / 0.30);
    /* IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO
     * At an unambiguous material boundary, do not retain a bilinear cross-edge chroma
     * bridge. Ambiguous/low-contrast regions keep the proven 26580 soft transition. */
    float decisiveBoundary = irisSmooth01((maxYDelta - 0.050) / 0.075) *
        irisSmooth01((crossSideSpatial - 0.10) / 0.24);
    float topologyGate = max(edgeGate * mix(0.70, 1.0, crossEdgeEvidence),
        decisiveBoundary);
    materialBoundary = max(decisiveBoundary, edgeGate * crossEdgeEvidence);
    vec3 selectedChroma = mix(bilinearChroma, topologyChroma, topologyGate);

    /* IRIS_26580_NEUTRAL_GLYPH_OUTSIDE_EDGE_EXCLUSION
     * Do not identify text semantically. When at least three of the four native guide
     * samples are neutral and the high-resolution luma-selected owner is also neutral, any
     * chroma arriving mainly from the opposite material side is unsupported. Pull only
     * toward that already-existing neutral owner chroma. A nearby tiny colored print is
     * protected whenever its spatially owned chroma occupancy is strong. */
    vec3 anchorChroma = sampleChroma[anchorIndex];
    float anchorNeutral = 1.0 -
        irisSmooth01((sampleChromaMagnitude[anchorIndex] - 0.012) / 0.050);
    float neutralNeighborhood = irisSmooth01((neutralVotes - 2.55) / 0.90);
    float localColorProtection = irisSmooth01((localChromaOccupancy - 0.20) / 0.40);
    float neutralSideOwnership = edgeGate * crossEdgeEvidence * anchorNeutral *
        neutralNeighborhood * (1.0 - localColorProtection);
    selectedChroma = mix(selectedChroma, anchorChroma, 0.92 * neutralSideOwnership);
    /* IRIS_26760_SUPER_RES_CHROMA_DENOISE_50
     * Super-Res-only chroma cleanup, intentionally inside the true-2x guide resolver.
     * Luminance and direct-CFA detail are untouched. Build a 3x3 native-VGN same-material
     * chroma consensus around the selected owner, blend at Lightroom-like 0.50 strength in
     * stable material interiors, and retreat sharply at material boundaries. Near-neutral
     * regions may shed incoherent color speckle; coherent saturated colors retain at least
     * 90% of the already-supported selected chroma magnitude. No direct-CFA chroma enters. */
    ivec2 anchorP26760 = anchorIndex == 0 ? p0 :
        (anchorIndex == 1 ? ivec2(p1.x, p0.y) :
         (anchorIndex == 2 ? ivec2(p0.x, p1.y) : p1));
    float anchorY26760 = sampleY[anchorIndex];
    float anchorMag26760 = length(anchorChroma);
    float centerColor26760 = irisSmooth01((anchorMag26760 - 0.018) / 0.070);
    vec3 chromaSum26760 = anchorChroma * 1.60;
    float chromaWeight26760 = 1.60;
    float coherentHueWeight26760 = 0.0;
    for (int oy26760 = -1; oy26760 <= 1; ++oy26760) {
        for (int ox26760 = -1; ox26760 <= 1; ++ox26760) {
            if (ox26760 == 0 && oy26760 == 0) continue;
            ivec2 np26760 = clamp(anchorP26760 + ivec2(ox26760, oy26760),
                ivec2(0), uGuideSize - ivec2(1));
            vec3 nrgb26760 = texelFetch(uNativeVgnGuide, np26760, 0).rgb;
            float ny26760 = irisLuma(nrgb26760);
            vec3 nc26760 = nrgb26760 - vec3(ny26760);
            float nmag26760 = length(nc26760);
            float relY26760 = abs(ny26760 - anchorY26760) /
                max(max(abs(ny26760), abs(anchorY26760)), 0.035);
            float lumaCompat26760 = 1.0 -
                irisSmooth01((relY26760 - 0.045) / 0.200);
            float neighborColor26760 = irisSmooth01((nmag26760 - 0.012) / 0.055);
            float neutralCompat26760 = 1.0 - neighborColor26760;
            float hueCos26760 = dot(anchorChroma, nc26760) /
                max(anchorMag26760 * nmag26760, 1.0e-6);
            float hueCompat26760 =
                irisSmooth01((hueCos26760 - 0.55) / 0.38) * neighborColor26760;
            float materialCompat26760 = mix(
                neutralCompat26760, hueCompat26760, centerColor26760);
            float spatial26760 = (abs(ox26760) + abs(oy26760) == 2) ? 0.70 : 1.0;
            float w26760 = lumaCompat26760 * materialCompat26760 * spatial26760;
            chromaSum26760 += nc26760 * w26760;
            chromaWeight26760 += w26760;
            coherentHueWeight26760 += hueCompat26760 * w26760;
        }
    }
    vec3 denoisedChroma26760 = chromaSum26760 / max(chromaWeight26760, 1.0e-6);
    float denoisedMag26760 = length(denoisedChroma26760);
    float selectedMag26760 = length(selectedChroma);
    float coherentHue26760 = irisSmooth01(
        (coherentHueWeight26760 / max(chromaWeight26760, 1.0e-6) - 0.18) / 0.42);
    float colorRetention26760 = centerColor26760 * coherentHue26760;
    float retainedMag26760 = mix(denoisedMag26760,
        max(denoisedMag26760, 0.90 * selectedMag26760),
        0.75 * colorRetention26760);
    retainedMag26760 = min(retainedMag26760, max(maxChromaMagnitude, selectedMag26760));
    if (denoisedMag26760 > 1.0e-7)
        denoisedChroma26760 *= retainedMag26760 / denoisedMag26760;
    else
        denoisedChroma26760 = selectedChroma;
    /* IRIS_26762_SUPER_RES_BOUNDED_ADAPTIVE_CHROMA_BLEND
     * 0.5..1.0 preserves the proven 26760/26761 same-material consensus blend. Values
     * above 1.0 never extrapolate mix(): first reach the bounded consensus, then apply a
     * second bounded near-neutral cleanup only inside stable material. Coherent saturated
     * color is protected by colorRetention26760 and material boundaries veto the excess. */
    float adaptive26762 = clamp(uChromaDenoiseStrength26762, 0.50, 2.00);
    float materialGate26762 = 1.0 - 0.75 * materialBoundary;
    float baseBlend26762 = min(adaptive26762, 1.0) * materialGate26762;
    selectedChroma = mix(selectedChroma, denoisedChroma26760, baseBlend26762);
    float excess26762 = max(adaptive26762 - 1.0, 0.0);
    float neutralCleanup26762 = excess26762 * materialGate26762 * materialGate26762 *
        (1.0 - colorRetention26760);
    vec3 strongerTarget26762 = denoisedChroma26760 *
        (1.0 - 0.35 * neutralCleanup26762);
    selectedChroma = mix(selectedChroma, strongerTarget26762,
        clamp(neutralCleanup26762, 0.0, 1.0));

    /* Preserve exact bilinear guide luminance without clipping a negative RGB component:
     * if a supported chroma vector would cross zero at this luminance, reduce only chroma. */
    float nonNegativeScale = 1.0;
    if (selectedChroma.r < 0.0) nonNegativeScale = min(nonNegativeScale,
        bilinearY / max(-selectedChroma.r, 1.0e-7));
    if (selectedChroma.g < 0.0) nonNegativeScale = min(nonNegativeScale,
        bilinearY / max(-selectedChroma.g, 1.0e-7));
    if (selectedChroma.b < 0.0) nonNegativeScale = min(nonNegativeScale,
        bilinearY / max(-selectedChroma.b, 1.0e-7));
    return vec3(bilinearY) + selectedChroma * clamp(nonNegativeScale, 0.0, 1.0);
}
int irisPhaseCount(ivec2 localP) {
    vec4 phases = texelFetch(uPhaseOccupancy, localP, 0);
    return (phases.r > 0.0 ? 1 : 0) + (phases.g > 0.0 ? 1 : 0) +
           (phases.b > 0.0 ? 1 : 0) + (phases.a > 0.0 ? 1 : 0);
}
float irisTemporalAgreement(ivec2 localP) {
    vec4 moments = texelFetch(uTemporalLumaStats, localP, 0);
    float sumW = max(moments.z, 0.0);
    float sumW2 = max(moments.w, 0.0);
    if (sumW <= 0.08 || sumW2 <= 1.0e-6) return 0.0;
    float meanY = moments.x / sumW;
    float varianceY = max(moments.y / sumW - meanY * meanY, 0.0);
    float effectiveN = (sumW * sumW) / max(sumW2, 1.0e-6);
    float supportGate = irisSmooth01((effectiveN - 1.50) / 1.50);
    float relativeSigma = sqrt(varianceY) / max(abs(meanY), 0.030);
    float stabilityGate = 1.0 - irisSmooth01((relativeSigma - 0.060) / 0.120);
    return clamp(supportGate * stabilityGate, 0.0, 1.0);
}
/* IRIS_26853_SUPER_RES_LOCAL_NOISE_GATE
 * The 2x direct-CFA detail owner uses its own already-accumulated local temporal moments.
 * This is not global effectiveSupport and does not change frame admission. Noisy flat
 * shadow detail returns toward the cleaned native CFA/VGN guide; stable structure survives. */
float irisResidualNoiseGate26853(ivec2 localP) {
    vec4 moments = texelFetch(uTemporalLumaStats, localP, 0);
    float sumW = max(moments.z, 0.0);
    float sumW2 = max(moments.w, 0.0);
    if (sumW <= 0.08 || sumW2 <= 1.0e-6) return 0.0;
    float meanY = moments.x / sumW;
    float varianceY = max(moments.y / sumW - meanY * meanY, 0.0);
    float effectiveN = max((sumW * sumW) / sumW2, 1.0);
    float residualRelativeSigma = sqrt(varianceY / effectiveN) / max(abs(meanY), 0.030);
    return 1.0 - irisSmooth01((residualRelativeSigma - 0.025) / 0.105);
}
void main() {
    ivec2 localP = ivec2(gl_FragCoord.xy);
    ivec2 globalP = uOutputOrigin + localP;
    ivec2 globalBlock = (globalP / 2) * 2;
    ivec2 block = globalBlock - uOutputOrigin;
    ivec2 q00 = block;
    ivec2 q10 = block + ivec2(1, 0);
    ivec2 q01 = block + ivec2(0, 1);
    ivec2 q11 = block + ivec2(1, 1);

    vec3 b00 = texelFetch(uDirectRgb, q00, 0).rgb;
    vec3 b10 = texelFetch(uDirectRgb, q10, 0).rgb;
    vec3 b01 = texelFetch(uDirectRgb, q01, 0).rgb;
    vec3 b11 = texelFetch(uDirectRgb, q11, 0).rgb;
    ivec2 cell = globalP - globalBlock;
    vec3 directRgb = cell.y == 0 ? (cell.x == 0 ? b00 : b10) : (cell.x == 0 ? b01 : b11);
    vec3 bilinearGuideRgb = irisGuide(globalP);
    ivec2 nativeBlock = clamp(globalBlock / 2, ivec2(0), uGuideSize - ivec2(1));
    vec3 guideBlockRgb = texelFetch(uNativeVgnGuide, nativeBlock, 0).rgb;

    float y00 = max(irisLuma(b00), 0.0);
    float y10 = max(irisLuma(b10), 0.0);
    float y01 = max(irisLuma(b01), 0.0);
    float y11 = max(irisLuma(b11), 0.0);
    float directY = max(irisLuma(directRgb), 0.0);
    float lowY = max(0.25 * (y00 + y10 + y01 + y11), 0.0);
    float guideY = max(irisLuma(bilinearGuideRgb), 0.0);
    float guideBlockY = max(irisLuma(guideBlockRgb), 0.0);

    int p00 = irisPhaseCount(q00);
    int p10 = irisPhaseCount(q10);
    int p01 = irisPhaseCount(q01);
    int p11 = irisPhaseCount(q11);
    int phaseCount = cell.y == 0 ? (cell.x == 0 ? p00 : p10) : (cell.x == 0 ? p01 : p11);
    int blockPhaseCount = min(min(p00, p10), min(p01, p11));
    float phaseGate = blockPhaseCount >= 4 ? 1.0 : (blockPhaseCount == 3 ? 0.85 : (blockPhaseCount == 2 ? 0.50 : 0.0));
    float t00 = irisTemporalAgreement(q00);
    float t10 = irisTemporalAgreement(q10);
    float t01 = irisTemporalAgreement(q01);
    float t11 = irisTemporalAgreement(q11);
    float n00_26853 = irisResidualNoiseGate26853(q00);
    float n10_26853 = irisResidualNoiseGate26853(q10);
    float n01_26853 = irisResidualNoiseGate26853(q01);
    float n11_26853 = irisResidualNoiseGate26853(q11);
    /* IRIS_26573_BLOCK_WIDE_TEMPORAL_PROOF
     * One unstable subpixel invalidates the whole zero-DC 2x2 residual. This prevents a
     * single phase/alignment outlier from being converted into wire/stem/edge zippering.
     */
    float temporalGate = min(min(t00, t10), min(t01, t11));
    float signalGate = irisSmooth01((guideBlockY - 0.015) / 0.055);
    float blockPeak = max(max(max(irisPeak(b00), irisPeak(b10)), max(irisPeak(b01), irisPeak(b11))), irisPeak(guideBlockRgb));
    float highlightGate = 1.0 - irisSmooth01((blockPeak - 0.72) / 0.20);
    vec3 directBlockRgb = 0.25 * (b00 + b10 + b01 + b11);
    float chromaDistance = length(irisChroma(directBlockRgb) - irisChroma(guideBlockRgb));
    float chromaGate = 1.0 - irisSmooth01((chromaDistance - 0.015) / 0.055);
    float agreement = abs(log2((lowY + 0.01) / (guideBlockY + 0.01)));
    float agreementGate = 1.0 - irisSmooth01((agreement - 0.08) / 0.27);
    float safetyGate = min(signalGate, min(highlightGate, min(chromaGate, agreementGate)));

    /* IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION
     * Keep true-2x measurement-driven while rejecting the historical failure signatures:
     * alternating row/column/checker residual unsupported by the native VGN structure.
     * The continuous gate is analogous to hybrid fusion uncertainty masking: unsafe SR
     * detail returns to the exact Sabre/VGN guide rather than creating zipper/line aliasing.
     */
    float aliasDenom=max(lowY,0.015);
    float rowAlternation=0.5*abs((y00+y10)-(y01+y11))/aliasDenom;
    float colAlternation=0.5*abs((y00+y01)-(y10+y11))/aliasDenom;
    float checkerAlternation=0.5*abs((y00+y11)-(y10+y01))/aliasDenom;
    float gg00=max(irisLuma(irisGuide(globalBlock)),0.0);
    float gg10=max(irisLuma(irisGuide(globalBlock+ivec2(1,0))),0.0);
    float gg01=max(irisLuma(irisGuide(globalBlock+ivec2(0,1))),0.0);
    float gg11=max(irisLuma(irisGuide(globalBlock+ivec2(1,1))),0.0);
    float guideGradX=0.5*(abs(gg10-gg00)+abs(gg11-gg01))/max(guideBlockY,0.015);
    float guideGradY=0.5*(abs(gg01-gg00)+abs(gg11-gg10))/max(guideBlockY,0.015);
    float guideRange26758=(max(max(gg00,gg10),max(gg01,gg11))-min(min(gg00,gg10),min(gg01,gg11)))/max(guideBlockY,0.015);
    float supportedEdge26758=irisSmooth01((guideRange26758-0.10)/0.45);
    float unsupportedRow=rowAlternation*(1.0-irisSmooth01((guideGradY-0.035)/0.18));
    float unsupportedCol=colAlternation*(1.0-irisSmooth01((guideGradX-0.035)/0.18));
    float unsupportedChecker=checkerAlternation*(1.0-supportedEdge26758);
    float aliasMetric=max(unsupportedChecker,max(unsupportedRow,unsupportedCol));
    float aliasGate=1.0-irisSmooth01((aliasMetric-0.10)/0.22);
    float confidence = clamp(phaseGate * temporalGate * safetyGate * aliasGate, 0.0, 1.0);

    /* Zero-mean direct-CFA microstructure inside this exact 2x2 cell.  Scaling all four
     * deviations by one block scalar preserves their zero DC while allowing materially
     * more real subpixel structure than the old +/-0.25-EV exponent residual.
     */
    /* IRIS_26581_MATERIAL_SEPARATED_SR_DETAIL_ENVELOPE
     * Zero-DC over a mixed leaf/sky 2x2 block can create a compensating dark/bright pair
     * across the material edge. Preserve the exact old zero-DC residual in uniform cells,
     * but at a proven boundary center the direct-CFA residual only on the current material
     * side. A side represented by only one trustworthy subpixel does not fabricate detail. */
    float materialBoundary = 0.0;
    vec3 guideRgb = irisTopologyGuide(globalP, bilinearGuideRgb, directY, confidence,
        materialBoundary);
    float denom = max(lowY, 0.015);
    float d00 = (y00 - lowY) / denom;
    float d10 = (y10 - lowY) / denom;
    float d01 = (y01 - lowY) / denom;
    float d11 = (y11 - lowY) / denom;
    float maxAbsDetail = max(max(abs(d00), abs(d10)), max(abs(d01), abs(d11)));
    float shapeScale = maxAbsDetail > 1.0e-6 ? min(1.0, 0.42 / maxAbsDetail) : 0.0;
    float blockDetail = ((directY - lowY) / denom) * shapeScale;

    float rel00 = abs(y00 - directY) / max(max(y00, directY), 0.030);
    float rel10 = abs(y10 - directY) / max(max(y10, directY), 0.030);
    float rel01 = abs(y01 - directY) / max(max(y01, directY), 0.030);
    float rel11 = abs(y11 - directY) / max(max(y11, directY), 0.030);
    float mw00 = 1.0 - irisSmooth01((rel00 - 0.10) / 0.34);
    float mw10 = 1.0 - irisSmooth01((rel10 - 0.10) / 0.34);
    float mw01 = 1.0 - irisSmooth01((rel01 - 0.10) / 0.34);
    float mw11 = 1.0 - irisSmooth01((rel11 - 0.10) / 0.34);
    float materialWeight = mw00 + mw10 + mw01 + mw11;
    float materialMean = (y00 * mw00 + y10 * mw10 + y01 * mw01 + y11 * mw11) /
        max(materialWeight, 1.0e-6);
    float materialDenom = max(materialMean, 0.015);
    float md00 = (y00 - materialMean) / materialDenom;
    float md10 = (y10 - materialMean) / materialDenom;
    float md01 = (y01 - materialMean) / materialDenom;
    float md11 = (y11 - materialMean) / materialDenom;
    float materialMaxAbs = max(max(abs(md00) * step(0.20, mw00),
                                   abs(md10) * step(0.20, mw10)),
                               max(abs(md01) * step(0.20, mw01),
                                   abs(md11) * step(0.20, mw11)));
    float materialShapeScale = materialMaxAbs > 1.0e-6 ?
        min(1.0, 0.42 / materialMaxAbs) : 0.0;
    float materialDetail = ((directY - materialMean) / materialDenom) *
        materialShapeScale;
    float materialSupportGate = irisSmooth01((materialWeight - 1.15) / 1.10);
    float directDetail = mix(blockDetail, materialDetail, materialBoundary);
    float detailConfidence = confidence * mix(1.0, materialSupportGate, materialBoundary);
    float localNoiseGate26853 = min(min(n00_26853, n10_26853), min(n01_26853, n11_26853));
    float flatShadow26853 = (1.0 - supportedEdge26758) *
        (1.0 - irisSmooth01((guideBlockY - 0.18) / 0.42));
    detailConfidence *= mix(1.0, localNoiseGate26853, 0.85 * flatShadow26853);
    float detailScaleY = mix(guideBlockY, guideY, materialBoundary);
    /* IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT
     * Strengthen only direct-CFA luma microstructure already proven by phase, temporal,
     * signal, highlight, chroma/agreement and alias rejection. This is not RGB sharpening.
     * The structural/microcontrast gain rises continuously with confidence and is capped
     * at 2x before the inherited material envelope and 0.68..1.47 luminance-factor bound.
     */
    float structuralDetail=irisSmooth01((abs(directDetail)-0.020)/0.120);
    float provenStructure=structuralDetail*irisSmooth01((detailConfidence-0.30)/0.55);
    float strongConfidence=irisSmooth01((detailConfidence-0.58)/0.30);
    float detailReinforcement=1.0+provenStructure*strongConfidence;
    float microcontrastGain=1.0+0.36*provenStructure;
    float combinedDetailGain=min(2.0,detailReinforcement*microcontrastGain);
    float targetY = max(guideY + detailScaleY * directDetail * detailConfidence * combinedDetailGain, 0.0);
    float factor = guideY > 1.0e-5 ? clamp(targetY / guideY, 0.68, 1.47) : 1.0;

    /* Boundary-only luminance envelope: the amount of permitted SR excursion is derived
     * from variation already observed on the selected material side. Uniform sky therefore
     * cannot acquire a bright halo simply to compensate a dark leaf residual, while textured
     * foliage keeps substantially more true subpixel modulation. */
    float materialMinY = directY;
    float materialMaxY = directY;
    if (mw00 > 0.35) { materialMinY = min(materialMinY, y00); materialMaxY = max(materialMaxY, y00); }
    if (mw10 > 0.35) { materialMinY = min(materialMinY, y10); materialMaxY = max(materialMaxY, y10); }
    if (mw01 > 0.35) { materialMinY = min(materialMinY, y01); materialMaxY = max(materialMaxY, y01); }
    if (mw11 > 0.35) { materialMinY = min(materialMinY, y11); materialMaxY = max(materialMaxY, y11); }
    float materialRelativeRange = (materialMaxY - materialMinY) / max(materialMean, 0.015);
    float edgeExcursion = clamp(0.045 + 0.70 * materialRelativeRange, 0.060, 0.30);
    float envelopeFactor = clamp(factor, 1.0 - edgeExcursion, 1.0 + edgeExcursion);
    factor = mix(factor, envelopeFactor, materialBoundary);

    /* IRIS_26573_REQUIRED_SR_PROOF_DIAGNOSTIC
     * Alpha is diagnostic-only and never published. Encode phaseCount*8 + reasonClass as
     * an exact integer in binary16 so the already-required 50MP readback can produce hard
     * per-shot SR statistics with no second readback. reasonClass: 0=fallback-other,
     * 1=active, 2=strong, 3=temporal-reject, 4=highlight-reject, 5=material/agreement-reject,
     * 6=phase-reject, 7=signal-reject.
     */
    int reasonClass = 0;
    if (blockPhaseCount < 2) reasonClass = 6;
    else if (temporalGate <= 0.02) reasonClass = 3;
    else if (highlightGate <= 0.001) reasonClass = 4;
    else if (chromaGate <= 0.001 || agreementGate <= 0.001 || aliasGate <= 0.02) reasonClass = 5;
    else if (signalGate <= 0.001) reasonClass = 7;
    else if (confidence >= 0.50) reasonClass = 2;
    else if (confidence > 0.02) reasonClass = 1;
    oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount * 8 + reasonClass));
}
