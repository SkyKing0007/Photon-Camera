#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
uniform sampler2D uExtractedBayer;
uniform highp usampler2D uRaw26790;
/* IRIS_26852_TEMPORAL_CFA_RECONSTRUCTION_INPUT
 * When enabled, scalar CFA comes from the completed shared-weight R/G1/G2/B carrier.
 * uRaw26790 remains bound only for inherited non-temporal callers (LONG/rollback). */
uniform int uTemporalCfaOwner26852;
uniform sampler2D uTemporalCfaSignals26852;
uniform sampler2D uTemporalCfaSupport26852;
uniform sampler2D uTemporalCfaValidity26852;
uniform sampler2D uFlow;
uniform sampler2D uCovariance;
uniform sampler2D uRejection;
uniform vec4 uFlowScaleOffset;
uniform ivec2 uExtractedSize;
uniform ivec2 uOutputSize;
uniform vec4 uFrameBorderPadded;
uniform int uCfaPattern;
uniform int uUseFrameWeight;
/* IRIS_26790_COMPILER_REPAIR_LONG_CHROMA_UNIFORMS
 * Compile-only repair after Actions exposed two host-bound uniforms used by merge but
 * omitted from the GLSL declaration block. No CFA/LCA/neutral/LONG math changes. */
uniform int uLongChromaGuard26790;
uniform sampler2D uNormalChromaConsensus26790;
/* IRIS_26792_CONTINUOUS_SCALAR_CFA_LCA_NEUTRAL_OWNER
 * One scalar CFA producer only: physical phase is selected from the nominal Sabre topology,
 * R/B receive the calibrated radial coordinate correction, and that corrected coordinate is
 * sampled continuously on the fixed 2-pixel same-phase lattice. There is no nearest-phase
 * snap and no edge-directed branch in the JPEG scalar producer; Sabre remains the sole
 * spatial CFA->RGB/demosaic owner. Physical two-green censor evidence is consumed here,
 * before RGB construction, as a continuous per-frame CFA neutral bound. */
uniform int uJpegLcaEnabled26790;
uniform vec2 uJpegLcaKrKb26790;
uniform vec4 uPhaseGains26790;
uniform vec4 uPhaseBlackTerms26790;
uniform vec4 uPhaseWhiteBalance26790;
uniform float uSourceWhiteNormalized26790;
uniform int uDngQuadHeadroom26790;
uniform int uDngEdgeDeAlias26790;
uniform int uJpegNeutralClamp26792;
/* IRIS_26720_REFERENCE_ROW_FLICKER_MERGE_CONFIDENCE
 * Reference NORMAL bypasses ordinary rejection, so only it needs this additional merge
 * reliability. Alternate NORMALs already carry row confidence in their rejection texture.
 * SHORT/LONG keep this disabled. */
uniform int uRowFlickerEnabled;
uniform int uRowFlickerHarmonic;
uniform vec2 uRowFlickerAB;
uniform float uRowFlickerStrength;
/* IRIS_26603_ONE_TUNNEL_SOURCE_CLIPPING
 * Every bracket observation, including the reference, reaches this same RBF accumulator.
 * Source headroom is one continuous scalar for the complete consumed 3x3 CFA footprint,
 * so no Bayer phase or RGB channel can become an independent bracket owner. Confidence
 * falls only in the final 0.75% of sensor-code headroom and reaches zero at true saturation;
 * the reference retains only its tiny deterministic same-source fallback at full loss.
 */
uniform int uSourceClipGuard;
uniform float uSourceClippingPoint;
uniform float uSourceClippedWeight;
uniform float uValidityWeightScale;
uniform vec4 uGains;
uniform vec4 uBlackLevelsTimesGains;
uniform vec4 uCovRangeRg;
uniform vec2 uCovRangeB;
layout(location = 0) out vec4 oColorAndRWeight;
layout(location = 1) out vec2 oWeightsGb;
/* IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_SIDECAR
 * Third MRT is read-only provenance for the later color owner. It accumulates kernel/frame
 * weight multiplied by the actual source-code headroom confidence of each CFA channel.
 * It never feeds temporal weights, color accumulation, Resolve, VGN, DNG or SR detail. */
layout(location = 2) out vec4 oValidWeights;
/* IRIS_26834_NORMAL_CLIP_ZONE_PROVENANCE
 * Fourth MRT is scalar NORMAL-only provenance. x=sum(w*headroomConfidence), y=sum(w).
 * It is read-only evidence and cannot feed merge weights, RGB, Resolve, VGN, DNG or SR. */
layout(location = 3) out vec2 oClipZoneProvenance26834;
uniform int uClipZoneEnabled26834;
uniform float uClipZoneClipStart26834;

vec2 mirrorUvs(vec2 sampleUv) {
    if (sampleUv.x <= uFrameBorderPadded.x) {
        sampleUv.x = 2.0 * uFrameBorderPadded.x - sampleUv.x;
    }
    if (sampleUv.y <= uFrameBorderPadded.y) {
        sampleUv.y = 2.0 * uFrameBorderPadded.y - sampleUv.y;
    }
    if (sampleUv.x > uFrameBorderPadded.z) {
        sampleUv.x = 2.0 * uFrameBorderPadded.z - sampleUv.x;
    }
    if (sampleUv.y > uFrameBorderPadded.w) {
        sampleUv.y = 2.0 * uFrameBorderPadded.w - sampleUv.y;
    }
    return sampleUv;
}

float iris26720MergeRowReliability(float rowUv) {
    if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 || uRowFlickerStrength <= 0.0) return 1.0;
    float phase = 6.283185307179586 * float(uRowFlickerHarmonic) * clamp(rowUv, 0.0, 1.0);
    float logModulation = uRowFlickerAB.x * cos(phase) + uRowFlickerAB.y * sin(phase);
    float amplitude = length(uRowFlickerAB);
    float darkMagnitude = max(-logModulation, 0.0);
    float darkBand = smoothstep(0.010, max(0.030, amplitude * 0.90), darkMagnitude);
    return mix(1.0, 0.08, clamp(darkBand * clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));
}

float kernelWeight(vec2 pixelOffset, vec3 covariance) {
    float kernelDistance =
        pixelOffset.x * pixelOffset.x * covariance.x +
        pixelOffset.y * pixelOffset.y * covariance.y +
        pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
    return exp2(-0.5 * kernelDistance) + 0.00005;
}

vec3 unpackCovariance(vec3 packedCovariance) {
    return vec3(
        packedCovariance.x * uCovRangeRg.y + uCovRangeRg.x,
        packedCovariance.y * uCovRangeRg.w + uCovRangeRg.z,
        packedCovariance.z * uCovRangeB.y + uCovRangeB.x
    );
}

mat3 get3x3FromExtractedBayer(ivec2 bayerPosition) {
    mat3 values = mat3(0.0);
    int type = (bayerPosition.y % 2) * 2 + (bayerPosition.x % 2);
    vec2 texturePosition = vec2(bayerPosition / 2);
    if (type == 0) texturePosition += vec2(-1.0, -1.0);
    else if (type == 1) texturePosition += vec2(0.0, -1.0);
    else if (type == 2) texturePosition += vec2(-1.0, 0.0);
    texturePosition += vec2(0.5);
    vec2 reciprocalSize = 1.0 / vec2(uExtractedSize);
    vec4 bayer0 = texture(uExtractedBayer, texturePosition * reciprocalSize);
    vec4 bayer1 = texture(
        uExtractedBayer,
        (texturePosition + vec2(1.0, 0.0)) * reciprocalSize
    );
    vec4 bayer2 = texture(
        uExtractedBayer,
        (texturePosition + vec2(0.0, 1.0)) * reciprocalSize
    );
    vec4 bayer3 = texture(
        uExtractedBayer,
        (texturePosition + vec2(1.0, 1.0)) * reciprocalSize
    );
    if (type == 0) {
        values[0][0] = bayer0.w; values[1][0] = bayer1.z; values[2][0] = bayer1.w;
        values[0][1] = bayer2.y; values[1][1] = bayer3.x; values[2][1] = bayer3.y;
        values[0][2] = bayer2.w; values[1][2] = bayer3.z; values[2][2] = bayer3.w;
    } else if (type == 1) {
        values[0][0] = bayer0.z; values[1][0] = bayer0.w; values[2][0] = bayer1.z;
        values[0][1] = bayer2.x; values[1][1] = bayer2.y; values[2][1] = bayer3.x;
        values[0][2] = bayer2.z; values[1][2] = bayer2.w; values[2][2] = bayer3.z;
    } else if (type == 2) {
        values[0][0] = bayer0.y; values[1][0] = bayer1.x; values[2][0] = bayer1.y;
        values[0][1] = bayer0.w; values[1][1] = bayer1.z; values[2][1] = bayer1.w;
        values[0][2] = bayer2.y; values[1][2] = bayer3.x; values[2][2] = bayer3.y;
    } else {
        values[0][0] = bayer0.x; values[1][0] = bayer0.y; values[2][0] = bayer1.x;
        values[0][1] = bayer0.z; values[1][1] = bayer0.w; values[2][1] = bayer1.z;
        values[0][2] = bayer2.x; values[1][2] = bayer2.y; values[2][2] = bayer3.x;
    }
    return values;
}


vec4 swizzleForType(vec4 value, int type) {
    if (type == 0) return value.rgba;
    if (type == 1) return value.grab;
    if (type == 2) return value.barg;
    return value.abgr;
}

void fillCorrectedCfaNeighborhood26792(
    ivec2 position,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    out mat3 bayerValue,
    out mat3 sourceValidity
);


/* IRIS_26793_SAME_LOCATION_CFA_COLOR_DIFFERENCE_OWNER
 * Sabre remains the sole CFA->RGB topology owner. 26793 changes only the color quantity
 * accumulated by that existing topology: R/B are represented as same-location R-G/B-G
 * differences, with G predicted from the immediate orthogonal green CFA evidence using
 * the already-owned Sabre covariance. Legacy per-frame Sabre luma is preserved exactly.
 * There is no RGB low-pass, post-RGB neutral mask, new edge detector, or temporal owner. */
int relativeCfaGroup26793(int sx, int sy) {
    if (sx == 1 && sy == 1) return 3;
    if (sx == 1) return 1;
    if (sy == 1) return 2;
    return 0;
}

float component26793(vec4 value, int groupIndex) {
    if (groupIndex == 0) return value.r;
    if (groupIndex == 1) return value.g;
    if (groupIndex == 2) return value.b;
    return value.a;
}

void buildCalculationCfa26793(
    mat3 bayerValue,
    vec4 reorderedGains,
    vec4 reorderedBlack,
    out mat3 calculationCfa
) {
    calculationCfa = mat3(0.0);
    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            int groupIndex = relativeCfaGroup26793(sx, sy);
            calculationCfa[sx][sy] =
                bayerValue[sx][sy] * component26793(reorderedGains, groupIndex) +
                component26793(reorderedBlack, groupIndex);
        }
    }
}

/* IRIS_26829_WEIGHTED_GREEN_CLIP_CALC_DOMAIN
 * The revised clipped-R/B gate is evaluated in the exact same calculation domain as
 * predictedGreen. Each orthogonal green phase therefore contributes its own clipped-code
 * value after that phase's gain and black term; the predictor applies the identical spatial
 * and physical-support weights to signal and clip reference. */
void buildCalculationClipCfa26793(
    vec4 reorderedGains,
    vec4 reorderedBlack,
    out mat3 calculationClipCfa
) {
    calculationClipCfa = mat3(0.0);
    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            int groupIndex = relativeCfaGroup26793(sx, sy);
            calculationClipCfa[sx][sy] =
                uSourceClippingPoint * component26793(reorderedGains, groupIndex) +
                component26793(reorderedBlack, groupIndex);
        }
    }
}

/* IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER
 * Preserve 26846 phase-validity ownership exactly, then address the remaining valid-but-cross-edge
 * failure class before R-G/B-G becomes RGB. The inherited predictor remains the baseline. Only when
 * both physical green phases are healthy AND the orthogonal green samples themselves prove a local
 * material boundary may Sabre's already-owned output RBF weights continuously favor the green samples
 * that geometrically belong to this output location. No phase value is substituted, no RGB hue is
 * borrowed, no chroma is neutralized after reconstruction, and flat/interior pixels are exact 26846. */
float predictSameLocationGreen26793(
    mat3 calculationCfa,
    mat3 calculationClipCfa,
    mat3 sampleWeights26847,
    mat3 greenSupport,
    ivec2 colorLocal,
    int type,
    float horizontalGreenWeight,
    float verticalGreenWeight,
    int useGreenSupport,
    out float greenConfidence,
    out float greenPhaseBalance26846,
    out float greenMaterialBoundary26847,
    out float predictedGreenClip
) {
    float numerator = 0.0;
    float clipNumerator = 0.0;
    float supportedWeight = 0.0;
    float fullWeight = 0.0;
    float horizontalSupportedWeight26846 = 0.0;
    float horizontalFullWeight26846 = 0.0;
    float verticalSupportedWeight26846 = 0.0;
    float verticalFullWeight26846 = 0.0;
    float ownedNumerator26847 = 0.0;
    float ownedClipNumerator26847 = 0.0;
    float ownedWeight26847 = 0.0;
    float greenMin26847 = 1.0e30;
    float greenMax26847 = -1.0e30;
    float greenEvidence26847 = 0.0;
    int redGroup = type;
    int blueGroup = 3 - type;
    for (int dx = -1; dx <= 1; ++dx) {
        for (int dy = -1; dy <= 1; ++dy) {
            if (abs(dx) + abs(dy) != 1) continue;
            ivec2 q = colorLocal + ivec2(dx, dy);
            if (q.x < 0 || q.x > 2 || q.y < 0 || q.y > 2) continue;
            int groupIndex = relativeCfaGroup26793(q.x, q.y);
            if (groupIndex == redGroup || groupIndex == blueGroup) continue;
            float spatialWeight = dx != 0
                ? horizontalGreenWeight : verticalGreenWeight;
            float physicalSupport = useGreenSupport != 0
                ? clamp(greenSupport[q.x][q.y], 0.0, 1.0)
                : 1.0;
            float supportedSpatialWeight = spatialWeight * physicalSupport;
            fullWeight += spatialWeight;
            supportedWeight += supportedSpatialWeight;
            if (dx != 0) {
                horizontalFullWeight26846 += spatialWeight;
                horizontalSupportedWeight26846 += supportedSpatialWeight;
            } else {
                verticalFullWeight26846 += spatialWeight;
                verticalSupportedWeight26846 += supportedSpatialWeight;
            }
            float greenSignal26847 = calculationCfa[q.x][q.y];
            float greenClip26847 = calculationClipCfa[q.x][q.y];
            numerator += greenSignal26847 * supportedSpatialWeight;
            clipNumerator += greenClip26847 * supportedSpatialWeight;

            /* Use the exact already-computed Sabre RBF weight only as a same-material selector.
             * It has zero effect until the signal-domain material-boundary gate below activates. */
            float outputOwnership26847 = max(sampleWeights26847[q.x][q.y], 0.00005);
            float ownedSupportedWeight26847 = supportedSpatialWeight * outputOwnership26847;
            ownedNumerator26847 += greenSignal26847 * ownedSupportedWeight26847;
            ownedClipNumerator26847 += greenClip26847 * ownedSupportedWeight26847;
            ownedWeight26847 += ownedSupportedWeight26847;
            if (physicalSupport >= 0.50) {
                greenMin26847 = min(greenMin26847, greenSignal26847);
                greenMax26847 = max(greenMax26847, greenSignal26847);
                greenEvidence26847 += 1.0;
            }
        }
    }
    greenConfidence = clamp(
        supportedWeight / max(fullWeight, 1.0e-7), 0.0, 1.0);
    float horizontalConfidence26846 = horizontalFullWeight26846 > 1.0e-7
        ? horizontalSupportedWeight26846 / horizontalFullWeight26846
        : greenConfidence;
    float verticalConfidence26846 = verticalFullWeight26846 > 1.0e-7
        ? verticalSupportedWeight26846 / verticalFullWeight26846
        : greenConfidence;
    greenPhaseBalance26846 = clamp(
        min(horizontalConfidence26846, verticalConfidence26846), 0.0, 1.0);
    if (supportedWeight <= 1.0e-7) {
        greenMaterialBoundary26847 = 0.0;
        predictedGreenClip = 0.0;
        return 0.0;
    }
    float inheritedGreen26847 = numerator / supportedWeight;
    float inheritedClip26847 = clipNumerator / supportedWeight;
    float ownedGreen26847 = ownedWeight26847 > 1.0e-7
        ? ownedNumerator26847 / ownedWeight26847 : inheritedGreen26847;
    float ownedClip26847 = ownedWeight26847 > 1.0e-7
        ? ownedClipNumerator26847 / ownedWeight26847 : inheritedClip26847;

    /* 26782 already established ~20% relative local guide separation as a real hard-edge class.
     * Re-express that principle in this exact calculation domain with a 3.5%-of-white floor so
     * dark shot noise cannot become a material boundary. Require both green phases to be healthy:
     * clipped/imbalanced evidence remains exclusively owned by 26846. */
    float greenRange26847 = greenEvidence26847 >= 2.0
        ? max(greenMax26847 - greenMin26847, 0.0) : 0.0;
    float greenScale26847 = max(
        max(abs(inheritedGreen26847), 0.035 * max(abs(inheritedClip26847), 1.0e-7)),
        1.0e-7);
    float relativeGreenRange26847 = greenRange26847 / greenScale26847;
    float balancedPhysicalSupport26847 = smoothstep(0.85, 1.00, greenPhaseBalance26846);
    greenMaterialBoundary26847 = smoothstep(
        0.18, 0.50, relativeGreenRange26847) * balancedPhysicalSupport26847;

    float materialBlend26847 = 0.85 * greenMaterialBoundary26847;
    predictedGreenClip = mix(inheritedClip26847, ownedClip26847, materialBlend26847);
    return mix(inheritedGreen26847, ownedGreen26847, materialBlend26847);
}

/* IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION
 * Failed Actions run 38999246441 proved GLSL ES requires the new 26849 helper and
 * six-argument CFA-neighborhood overload to be declared before sampleNeighborhoodRbf
 * calls them. Declarations only: implementations/math remain byte-identical. */
float peripheralLcaStrength26849(vec2 referenceUv);
float centralMaterialRegistrationGate26851(ivec2 position);
void fillCorrectedCfaNeighborhood26792(
    ivec2 position,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    float autoPeripheralLcaStrength26849,
    out mat3 bayerValue,
    out mat3 sourceValidity
);

/* IRIS_26829_GREEN_SUPPORT_HEADROOM_CLIPPED_RB_OWNER
 * Restore source-site validity as the normal chroma authority, but permit one-sided clipped
 * R/B hue evidence only when the orthogonal greens are nearly fully supported and their
 * predicted value is comfortably below the weighted per-phase green clip point. This
 * preserves saturated orange/red/blue material such as the Wegmans letters without giving a
 * clipped bright-edge R/B site full authority when its green prediction is biased low.
 * This owner is the true NORMAL/Sabre resolve used by Motion and Night. The separate
 * Motion NORMAL-master SHORT fusion already pre-applies source validity in validWeights and
 * remains byte-identical to successful 26828 to avoid double-gating that path. */
void sameLocationChroma26793(
    mat3 calculationCfa,
    mat3 calculationClipCfa,
    mat3 sampleWeights,
    mat3 greenSupport,
    int type,
    vec3 covariance,
    int useGreenSupport,
    vec3 legacyRgb,
    out float dR,
    out float dB
) {
    int redGroup = type;
    int blueGroup = 3 - type;
    float horizontalGreenWeight = kernelWeight(vec2(1.0, 0.0), covariance);
    float verticalGreenWeight = kernelWeight(vec2(0.0, 1.0), covariance);
    float redDifferenceSum = 0.0;
    float blueDifferenceSum = 0.0;
    float redDifferenceWeight = 0.0;
    float blueDifferenceWeight = 0.0;
    float redTotalWeight = 0.0;
    float blueTotalWeight = 0.0;
    /* IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER
     * 26847 proved that valid green evidence still needs output-side material ownership.
     * Apply the same already-owned Sabre RBF geometry to R/B contributors, but only when
     * 26847's green-only signal proof identifies a real material boundary. The strongest
     * same-channel output-side sample remains exact; weaker cross-edge samples are
     * continuously de-emphasized. This does not inspect R/B hue to decide validity, does
     * not shift CFA phases, and does not neutralize RGB after reconstruction. */
    float redMaxColorWeight26848 = 0.0;
    float blueMaxColorWeight26848 = 0.0;
    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            int groupIndex = relativeCfaGroup26793(sx, sy);
            if (groupIndex != redGroup && groupIndex != blueGroup) continue;
            float colorWeight = max(sampleWeights[sx][sy], 0.0);
            if (groupIndex == redGroup) {
                redMaxColorWeight26848 = max(redMaxColorWeight26848, colorWeight);
            } else {
                blueMaxColorWeight26848 = max(blueMaxColorWeight26848, colorWeight);
            }
        }
    }
    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            int groupIndex = relativeCfaGroup26793(sx, sy);
            if (groupIndex != redGroup && groupIndex != blueGroup) continue;
            float colorWeight = max(sampleWeights[sx][sy], 0.0);
            float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);
            float greenConfidence = 0.0;
            float greenPhaseBalance26846 = 0.0;
            float greenMaterialBoundary26847 = 0.0;
            float predictedGreenClip = 0.0;
            float predictedGreen = predictSameLocationGreen26793(
                calculationCfa, calculationClipCfa, sampleWeights, greenSupport,
                ivec2(sx, sy), type, horizontalGreenWeight, verticalGreenWeight,
                useGreenSupport, greenConfidence, greenPhaseBalance26846,
                greenMaterialBoundary26847, predictedGreenClip);
            /* IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY
             * 26829's aggregate green support remains exact when G1/G2 support is balanced.
             * Only an actual per-phase support imbalance transitions chroma authority toward
             * the weaker green phase. This avoids the failed broad-neutral/cross-phase class:
             * no whole observation is rejected, no phase value is replaced, and no RGB hue
             * is inferred after reconstruction. Saturated R/B rescue is likewise unchanged
             * when both green phases are healthy, preserving the validated real-color case. */
            float aggregateGreenSupport26846 = smoothstep(0.70, 1.00, greenConfidence);
            float balancedGreenSupport26846 = smoothstep(0.70, 1.00, greenPhaseBalance26846);
            float greenDirectionalRatio26846 = min(
                horizontalGreenWeight, verticalGreenWeight) /
                max(max(horizontalGreenWeight, verticalGreenWeight), 1.0e-7);
            /* Existing Sabre covariance remains the topology owner. If it has already made
             * one axis strongly directional at a hard edge, do not force the perpendicular
             * green phase back into ownership. The new balance gate acts only where both
             * orthogonal green phases are geometrically relevant yet their physical source
             * validity is unequal. */
            float bothGreenDirectionsRelevant26846 = smoothstep(
                0.25, 0.65, greenDirectionalRatio26846);
            float greenPhaseAsymmetry26846 = smoothstep(
                0.03, 0.18, max(greenConfidence - greenPhaseBalance26846, 0.0)) *
                bothGreenDirectionsRelevant26846;
            float gSupport = mix(
                aggregateGreenSupport26846,
                balancedGreenSupport26846,
                greenPhaseAsymmetry26846);
            float greenHeadroomRatio = predictedGreenClip > 1.0e-7
                ? predictedGreen / predictedGreenClip : 1.0;
            float gHead = 1.0 - smoothstep(0.55, 0.90, greenHeadroomRatio);
            float aggregateClippedRescue26846 =
                smoothstep(0.85, 1.00, greenConfidence) * gHead;
            float balancedClippedRescue26846 =
                smoothstep(0.85, 1.00, greenPhaseBalance26846) * gHead;
            float clippedSiteRescue = mix(
                aggregateClippedRescue26846,
                balancedClippedRescue26846,
                greenPhaseAsymmetry26846);
            float siteEff = siteValid + (1.0 - siteValid) * clippedSiteRescue;
            float channelMaxColorWeight26848 = groupIndex == redGroup
                ? redMaxColorWeight26848 : blueMaxColorWeight26848;
            float rbOutputOwnership26848 = clamp(
                colorWeight / max(channelMaxColorWeight26848, 1.0e-7), 0.0, 1.0);
            float rbMaterialBlend26848 = 0.85 * greenMaterialBoundary26847;
            float topologyColorWeight26848 = colorWeight * mix(
                1.0, rbOutputOwnership26848, rbMaterialBlend26848);
            if (groupIndex == redGroup) redTotalWeight += topologyColorWeight26848;
            else blueTotalWeight += topologyColorWeight26848;
            float differenceWeight = topologyColorWeight26848 * gSupport * siteEff;
            /* IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT
             * 26847's owned green predictor remains exact. 26848 changes only which valid
             * R/B contributors may influence its same-location chroma estimate at a proven
             * material boundary; luma preservation, temporal weight and downstream ownership
             * remain inherited. */
            float difference = calculationCfa[sx][sy] - predictedGreen;
            if (groupIndex == redGroup) {
                redDifferenceSum += difference * differenceWeight;
                redDifferenceWeight += differenceWeight;
            } else {
                blueDifferenceSum += difference * differenceWeight;
                blueDifferenceWeight += differenceWeight;
            }
        }
    }
    float measuredDR = redDifferenceWeight > 1.0e-7
        ? redDifferenceSum / redDifferenceWeight : 0.0;
    float measuredDB = blueDifferenceWeight > 1.0e-7
        ? blueDifferenceSum / blueDifferenceWeight : 0.0;
    float redPhysicalFraction = clamp(
        redDifferenceWeight / max(redTotalWeight, 1.0e-7), 0.0, 1.0);
    float bluePhysicalFraction = clamp(
        blueDifferenceWeight / max(blueTotalWeight, 1.0e-7), 0.0, 1.0);
    dR = measuredDR * redPhysicalFraction;
    dB = measuredDB * bluePhysicalFraction;
}

void sampleNeighborhoodRbf(
    vec2 sampleUv,
    vec2 referenceUv26791,
    vec3 covariance,
    out vec3 accumulatedIntensities,
    out vec3 accumulatedWeights,
    out float sourceNeighborhoodConfidence,
    out vec3 validAccumulatedWeights
) {
    accumulatedIntensities = vec3(0.0);
    accumulatedWeights = vec3(0.0);
    validAccumulatedWeights = vec3(0.0);
    sourceNeighborhoodConfidence = 1.0;
    vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
    ivec2 position = ivec2(coordinateScaled);
    mat3 bayerValue = mat3(0.0);
    mat3 sourceValidity = mat3(1.0);
    float autoPeripheralLcaStrength26849 = uJpegLcaEnabled26790 == 0
        ? peripheralLcaStrength26849(referenceUv26791) : 0.0;
    /* IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER
     * Preserve successful 26850 exactly wherever its peripheral search was active. Only
     * inside the former 26849/26850 central dead zone may the established green-only
     * material-range thresholds and healthy two-green headroom open the same 26850
     * same-phase search. This is not global LCA: zero shift remains the default and the
     * 26850 score/improvement gates remain the sole authority for accepting a shift. */
    float autoRegistrationSearchGate26851 = autoPeripheralLcaStrength26849;
    if (uJpegLcaEnabled26790 == 0 && autoPeripheralLcaStrength26849 <= 1.0e-7) {
        autoRegistrationSearchGate26851 = centralMaterialRegistrationGate26851(position);
    }
    if (uTemporalCfaOwner26852 != 0 || uJpegLcaEnabled26790 != 0 ||
        uJpegNeutralClamp26792 != 0 || autoRegistrationSearchGate26851 > 1.0e-7) {
        /* IRIS_26792_ONE_RGB_TOPOLOGY
         * LCA and neutral censorship may alter only scalar CFA evidence beneath the one
         * inherited Sabre topology. Position/type and CFA->RGB ownership never change. */
        vec2 sharedTranslationPixels26791 =
            (sampleUv - referenceUv26791) * vec2(uOutputSize);
        fillCorrectedCfaNeighborhood26792(
            position,
            sharedTranslationPixels26791,
            covariance,
            autoRegistrationSearchGate26851,
            bayerValue,
            sourceValidity
        );
        for (int sx = 0; sx < 3; ++sx) {
            for (int sy = 0; sy < 3; ++sy) {
                sourceNeighborhoodConfidence = min(
                    sourceNeighborhoodConfidence, sourceValidity[sx][sy]);
            }
        }
    } else {
        /* Exact inherited no-LCA signal/headroom path. */
        bayerValue = get3x3FromExtractedBayer(position);
        mat3 validityBayerValue26789 = bayerValue;
        float headroomStart = max(1.0, uSourceClippingPoint * 0.9925);
        for (int sx = 0; sx < 3; ++sx) {
            for (int sy = 0; sy < 3; ++sy) {
                float sampleConfidence = 1.0 - smoothstep(
                    headroomStart,
                    max(headroomStart + 1.0e-4, uSourceClippingPoint),
                    validityBayerValue26789[sx][sy]
                );
                sourceValidity[sx][sy] = sampleConfidence;
                sourceNeighborhoodConfidence = min(
                    sourceNeighborhoodConfidence, sampleConfidence);
            }
        }
    }
    mat3 weights = mat3(0.0);
    vec2 subpixelOffset = floor(coordinateScaled) + 0.5 - coordinateScaled;
    for (int i = -1; i <= 1; ++i) {
        for (int j = -1; j <= 1; ++j) {
            weights[i + 1][j + 1] = kernelWeight(
                subpixelOffset + vec2(ivec2(i, j)),
                covariance
            );
        }
    }
    mat3 validWeights = mat3(0.0);
    for (int sx=0;sx<3;++sx) {
        for (int sy=0;sy<3;++sy) {
            validWeights[sx][sy]=weights[sx][sy]*sourceValidity[sx][sy];
        }
    }
    ivec2 bayerOffset = ivec2(0);
    if (uCfaPattern == 0) bayerOffset = ivec2(1, 1);
    else if (uCfaPattern == 1) bayerOffset = ivec2(0, 1);
    else if (uCfaPattern == 2) bayerOffset = ivec2(1, 0);
    int type = (((position.y + bayerOffset.y) & 1) << 1) +
        ((position.x + bayerOffset.x) & 1);
    vec4 cornerWeights = vec4(
        weights[0][0], weights[0][2], weights[2][0], weights[2][2]
    );
    vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);
    vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);
    vec4 validCornerWeights = vec4(
        validWeights[0][0], validWeights[0][2], validWeights[2][0], validWeights[2][2]
    );
    vec2 validUpDownWeights = vec2(validWeights[1][0], validWeights[1][2]);
    vec2 validLeftRightWeights = vec2(validWeights[0][1], validWeights[2][1]);
    vec4 value1 = vec4(
        bayerValue[0][0], bayerValue[0][2], bayerValue[2][0], bayerValue[2][2]
    );
    vec2 value2 = vec2(bayerValue[1][0], bayerValue[1][2]);
    vec2 value3 = vec2(bayerValue[0][1], bayerValue[2][1]);
    vec4 reorderedGains = swizzleForType(uGains, type);
    vec4 reorderedBlack = swizzleForType(uBlackLevelsTimesGains, type);
    vec4 intensities = vec4(
        dot(value1 * reorderedGains.r + reorderedBlack.r, cornerWeights),
        dot(value2 * reorderedGains.g + reorderedBlack.g, upDownWeights),
        dot(value3 * reorderedGains.b + reorderedBlack.b, leftRightWeights),
        (bayerValue[1][1] * reorderedGains.a + reorderedBlack.a) * weights[1][1]
    );
    vec4 reorderedWeights = vec4(
        dot(cornerWeights, vec4(1.0)),
        dot(upDownWeights, vec2(1.0)),
        dot(leftRightWeights, vec2(1.0)),
        weights[1][1]
    );
    vec4 validReorderedWeights = vec4(
        dot(validCornerWeights, vec4(1.0)),
        dot(validUpDownWeights, vec2(1.0)),
        dot(validLeftRightWeights, vec2(1.0)),
        validWeights[1][1]
    );
    intensities = swizzleForType(intensities, type);
    reorderedWeights = swizzleForType(reorderedWeights, type);
    validReorderedWeights = swizzleForType(validReorderedWeights, type);
    accumulatedWeights = vec3(
        reorderedWeights.r,
        reorderedWeights.g + reorderedWeights.b,
        reorderedWeights.a
    );
    vec3 legacyRgb26793 = vec3(
        intensities.r,
        intensities.g + intensities.b,
        intensities.a
    ) / max(accumulatedWeights, vec3(1.0e-7));
    mat3 calculationCfa26793 = mat3(0.0);
    mat3 calculationClipCfa26793 = mat3(0.0);
    buildCalculationCfa26793(
        bayerValue, reorderedGains, reorderedBlack, calculationCfa26793);
    buildCalculationClipCfa26793(
        reorderedGains, reorderedBlack, calculationClipCfa26793);
    float dR26793 = 0.0;
    float dB26793 = 0.0;
    sameLocationChroma26793(
        calculationCfa26793, calculationClipCfa26793, weights, sourceValidity,
        type, covariance, 1, legacyRgb26793, dR26793, dB26793);
    float legacyLuma26793 = dot(legacyRgb26793, vec3(0.25, 0.50, 0.25));
    float correctedG26793 = legacyLuma26793 - 0.25 * (dR26793 + dB26793);
    vec3 correctedRgb26793 = vec3(
        correctedG26793 + dR26793,
        correctedG26793,
        correctedG26793 + dB26793);
    accumulatedIntensities = correctedRgb26793 * accumulatedWeights;
    validAccumulatedWeights = vec3(
        validReorderedWeights.r,
        validReorderedWeights.g + validReorderedWeights.b,
        validReorderedWeights.a
    );
}


int phaseAt26790(ivec2 p) {
    return ((p.y & 1) << 1) + (p.x & 1);
}
ivec2 phaseOffset26790(int phaseIndex) {
    return ivec2(phaseIndex & 1, (phaseIndex >> 1) & 1);
}
ivec2 clampPhaseLattice26790(ivec2 q, int phaseIndex) {
    ivec2 offset = phaseOffset26790(phaseIndex);
    ivec2 maximum = max((uOutputSize - ivec2(1) - offset) / 2, ivec2(0));
    return clamp(q, ivec2(0), maximum);
}
ivec2 pixelForPhaseLattice26790(ivec2 q, int phaseIndex) {
    return clampPhaseLattice26790(q, phaseIndex) * 2 + phaseOffset26790(phaseIndex);
}
float temporalNormalized26852(ivec2 p);
float normalizedRaw26790(ivec2 p) {
    p = clamp(p, ivec2(0), uOutputSize - ivec2(1));
    if (uTemporalCfaOwner26852 != 0) return temporalNormalized26852(p);
    int phaseIndex = phaseAt26790(p);
    return float(texelFetch(uRaw26790, p, 0).r) * uPhaseGains26790[phaseIndex] +
        uPhaseBlackTerms26790[phaseIndex];
}
float quadGuide26790(ivec2 quadIndex) {
    ivec2 q = max(quadIndex, ivec2(0));
    ivec2 origin = q * 2;
    ivec2 maxOrigin = max(uOutputSize - ivec2(2), ivec2(0));
    origin = clamp(origin, ivec2(0), maxOrigin);
    return 0.25 * (
        normalizedRaw26790(origin) +
        normalizedRaw26790(origin + ivec2(1, 0)) +
        normalizedRaw26790(origin + ivec2(0, 1)) +
        normalizedRaw26790(origin + ivec2(1, 1))
    );
}
float phaseHeadroomConfidence26790(ivec2 quadIndex, int phaseIndex) {
    ivec2 q = max(quadIndex, ivec2(0));
    if (uTemporalCfaOwner26852 != 0) {
        float sharedSupport26852 = max(
            texelFetch(uTemporalCfaSupport26852, q, 0).x, 1.0e-8);
        vec4 valid = texelFetch(uTemporalCfaValidity26852, q, 0);
        return clamp(valid[phaseIndex] / sharedSupport26852, 0.0, 1.0);
    }
    ivec2 p = pixelForPhaseLattice26790(q, phaseIndex);
    float value = normalizedRaw26790(p);
    float whitePoint = max(uSourceWhiteNormalized26790, 1.0e-5);
    float headroomStart = whitePoint * 0.9925;
    return 1.0 - smoothstep(
        headroomStart, max(headroomStart + 1.0e-5, whitePoint), value);
}
float quadHeadroomConfidence26790(ivec2 quadIndex) {
    float confidence = 1.0;
    for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
        confidence = min(confidence, phaseHeadroomConfidence26790(quadIndex, phaseIndex));
    }
    return confidence;
}
int redPhase26790() { return uCfaPattern; }
int bluePhase26790() { return 3 - uCfaPattern; }
float phaseLcaK26790(int phaseIndex) {
    if (uJpegLcaEnabled26790 == 0) return 0.0;
    if (phaseIndex == redPhase26790()) return uJpegLcaKrKb26790.x;
    if (phaseIndex == bluePhase26790()) return uJpegLcaKrKb26790.y;
    return 0.0;
}

/* IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER
 * 26848 removes valid-but-cross-edge CFA chroma without moving phases. The remaining
 * star/door/shutter residual is a thin peripheral R/B-vs-G positional displacement, while
 * the older global LCA helped those edges but made central chandelier shadows greener.
 * Preserve the legacy user-enabled LCA equation exactly. With the legacy toggle OFF, use
 * the same calibrated same-phase coefficients only outside a protected inner field, with a
 * smooth sensor-normalized ramp. The inner field therefore remains byte-equation-identical
 * to 26848; green is never shifted; no RGB/post-demosaic correction is introduced. */
float calibratedPhaseLcaK26849(int phaseIndex) {
    if (phaseIndex == redPhase26790()) return uJpegLcaKrKb26790.x;
    if (phaseIndex == bluePhase26790()) return uJpegLcaKrKb26790.y;
    return 0.0;
}
float peripheralLcaStrength26849(vec2 referenceUv) {
    vec2 normalizedFromCenter = abs(referenceUv * 2.0 - vec2(1.0));
    float peripheralDistance = max(normalizedFromCenter.x, normalizedFromCenter.y);
    return smoothstep(0.40, 0.58, peripheralDistance);
}
float selectedHeadroom26790(ivec2 q, int phaseIndex) {
    return uDngQuadHeadroom26790 != 0
        ? quadHeadroomConfidence26790(q) : phaseHeadroomConfidence26790(q, phaseIndex);
}

float temporalNormalized26852(ivec2 p) {
    p = clamp(p, ivec2(0), uOutputSize - ivec2(1));
    ivec2 q = p / 2;
    int phaseIndex = ((p.y & 1) << 1) + (p.x & 1);
    vec4 signal = texelFetch(uTemporalCfaSignals26852, q, 0);
    float w = max(texelFetch(uTemporalCfaSupport26852, q, 0).x, 1.0e-8);
    return signal[phaseIndex] / w;
}
float rawCode26791(ivec2 p) {
    p = clamp(p, ivec2(0), uOutputSize - ivec2(1));
    if (uTemporalCfaOwner26852 != 0) {
        int phaseIndex = ((p.y & 1) << 1) + (p.x & 1);
        return (temporalNormalized26852(p) - uPhaseBlackTerms26790[phaseIndex]) /
            max(uPhaseGains26790[phaseIndex], 1.0e-12) + 1.0e-4;
    }
    return float(texelFetch(uRaw26790, p, 0).r) + 1.0e-4;
}

/* IRIS_26792_DNG_DERIVED_CONTINUOUS_SCALAR_CFA_PRODUCER
 * Input: one nominal physical CFA location plus Sabre's already-owned shared translation.
 * Output: one corrected scalar CFA sample plus continuous physical headroom. The optical
 * coordinate equation is the DNG equation; interpolation is continuous bilinear sampling
 * on the fixed same-phase lattice. No hard-edge snap, phase change, RGB or rejection owner. */
float neutralBoundedRawCode26792(float rawCode, ivec2 q, int phaseIndex) {
    if (uJpegNeutralClamp26792 == 0) return rawCode;
    int rPhase = redPhase26790();
    int bPhase = bluePhase26790();
    if (phaseIndex != rPhase && phaseIndex != bPhase) return rawCode;
    int g0 = -1;
    int g1 = -1;
    for (int phase = 0; phase < 4; ++phase) {
        if (phase != rPhase && phase != bPhase) {
            if (g0 < 0) g0 = phase; else g1 = phase;
        }
    }
    float gh0 = phaseHeadroomConfidence26790(q, g0);
    float gh1 = phaseHeadroomConfidence26790(q, g1);
    /* One censored green is insufficient. As both greens lose recoverable evidence the
     * CFA bound approaches the exact DNG AsShotNeutral ceiling continuously. */
    float bothGreenCensor = clamp(1.0 - max(gh0, gh1), 0.0, 1.0);
    if (bothGreenCensor <= 1.0e-7) return rawCode;
    float phaseGain = max(uPhaseGains26790[phaseIndex], 1.0e-12);
    float normalizedSensor = rawCode * phaseGain + uPhaseBlackTerms26790[phaseIndex];
    float neutralLimit = 1.0 / max(uPhaseWhiteBalance26790[phaseIndex], 1.0e-6);
    float boundedSensor = min(normalizedSensor, neutralLimit);
    float correctedSensor = mix(normalizedSensor, boundedSensor, bothGreenCensor);
    return (correctedSensor - uPhaseBlackTerms26790[phaseIndex]) / phaseGain;
}

/* IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER
 * 26849 proved that a fixed radial coefficient is insufficient for the remaining star/door/shutter
 * fringe. Keep 26848 as the exact fallback and keep legacy user-enabled LCA byte-equation-identical.
 * With legacy LCA OFF, only a strong peripheral green edge may open a bounded same-phase R/B search.
 * Candidate shifts never change CFA phase and are scored only by local edge-shape agreement with the
 * two-green guide, not by RGB neutrality or hue. Zero shift wins unless a nonzero candidate produces
 * a strong, material edge-aligned improvement. Flat/interior pixels and rejected searches return the
 * exact inherited 26848 scalar/headroom path. */
float phaseNormalizedAtCenter26850(vec2 sourceCenter, int phaseIndex) {
    ivec2 offset = phaseOffset26790(phaseIndex);
    vec2 latticeCoordinate = 0.5 *
        (sourceCenter - (vec2(offset) + vec2(0.5)));
    ivec2 q00 = ivec2(floor(latticeCoordinate));
    vec2 frac = clamp(latticeCoordinate - vec2(q00), vec2(0.0), vec2(1.0));
    ivec2 q10 = q00 + ivec2(1, 0);
    ivec2 q01 = q00 + ivec2(0, 1);
    ivec2 q11 = q00 + ivec2(1, 1);
    q00 = clampPhaseLattice26790(q00, phaseIndex);
    q10 = clampPhaseLattice26790(q10, phaseIndex);
    q01 = clampPhaseLattice26790(q01, phaseIndex);
    q11 = clampPhaseLattice26790(q11, phaseIndex);
    float w00 = (1.0 - frac.x) * (1.0 - frac.y);
    float w10 = frac.x * (1.0 - frac.y);
    float w01 = (1.0 - frac.x) * frac.y;
    float w11 = frac.x * frac.y;
    float rawValue =
        rawCode26791(pixelForPhaseLattice26790(q00, phaseIndex)) * w00 +
        rawCode26791(pixelForPhaseLattice26790(q10, phaseIndex)) * w10 +
        rawCode26791(pixelForPhaseLattice26790(q01, phaseIndex)) * w01 +
        rawCode26791(pixelForPhaseLattice26790(q11, phaseIndex)) * w11;
    return rawValue * uPhaseGains26790[phaseIndex] +
        uPhaseBlackTerms26790[phaseIndex];
}

float greenGuideAtCenter26850(vec2 sourceCenter) {
    int rPhase = redPhase26790();
    int bPhase = bluePhase26790();
    float sum = 0.0;
    float count = 0.0;
    for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
        if (phaseIndex == rPhase || phaseIndex == bPhase) continue;
        sum += phaseNormalizedAtCenter26850(sourceCenter, phaseIndex);
        count += 1.0;
    }
    return sum / max(count, 1.0);
}

/* IRIS_26851_CENTRAL_GREEN_MATERIAL_PROOF
 * This mirrors 26847's signal-domain material proof without inspecting R/B hue: use the
 * two physical green phases, require both to retain near-full headroom, apply the same
 * 3.5%-of-white dark-noise floor and 0.18..0.50 relative-range ramp, then hand only that
 * scalar gate to the byte-identical 26850 registration search. */
float centralMaterialRegistrationGate26851(ivec2 position) {
    int rPhase = redPhase26790();
    int bPhase = bluePhase26790();
    int g0 = -1;
    int g1 = -1;
    for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
        if (phaseIndex == rPhase || phaseIndex == bPhase) continue;
        if (g0 < 0) g0 = phaseIndex; else g1 = phaseIndex;
    }
    ivec2 q = max(position / 2, ivec2(0));
    float g0Headroom = selectedHeadroom26790(q, g0);
    float g1Headroom = selectedHeadroom26790(q, g1);
    float balancedPhysicalSupport26851 = smoothstep(
        0.85, 1.00, min(g0Headroom, g1Headroom));
    if (balancedPhysicalSupport26851 <= 1.0e-7) return 0.0;

    vec2 center = vec2(position) + vec2(0.5);
    float greenCenter = greenGuideAtCenter26850(center);
    float greenLeft = greenGuideAtCenter26850(center - vec2(1.0, 0.0));
    float greenRight = greenGuideAtCenter26850(center + vec2(1.0, 0.0));
    float greenUp = greenGuideAtCenter26850(center - vec2(0.0, 1.0));
    float greenDown = greenGuideAtCenter26850(center + vec2(0.0, 1.0));
    float greenMin = min(greenCenter, min(min(greenLeft, greenRight), min(greenUp, greenDown)));
    float greenMax = max(greenCenter, max(max(greenLeft, greenRight), max(greenUp, greenDown)));
    float greenRange = max(greenMax - greenMin, 0.0);
    float greenScale = max(
        max(abs(greenCenter), 0.035 * max(uSourceWhiteNormalized26790, 1.0e-5)),
        1.0e-5);
    float relativeGreenRange = greenRange / greenScale;
    return smoothstep(0.18, 0.50, relativeGreenRange) * balancedPhysicalSupport26851;
}

float phaseShapeScore26850(
    vec2 sourceCenter,
    vec2 radialUnit,
    int phaseIndex,
    vec2 greenShape
) {
    float colorMinus = phaseNormalizedAtCenter26850(
        sourceCenter - radialUnit, phaseIndex);
    float colorCenter = phaseNormalizedAtCenter26850(
        sourceCenter, phaseIndex);
    float colorPlus = phaseNormalizedAtCenter26850(
        sourceCenter + radialUnit, phaseIndex);
    vec2 colorShape = vec2(
        colorCenter - colorMinus,
        colorPlus - colorCenter
    );
    float greenNorm = length(greenShape);
    float colorNorm = length(colorShape);
    if (greenNorm <= 1.0e-7 || colorNorm <= 1.0e-7) return -1.0;
    float correlation = clamp(
        dot(greenShape, colorShape) / (greenNorm * colorNorm), -1.0, 1.0);
    float greenBalance =
        (abs(greenShape.x) - abs(greenShape.y)) /
        (abs(greenShape.x) + abs(greenShape.y) + 1.0e-7);
    float colorBalance =
        (abs(colorShape.x) - abs(colorShape.y)) /
        (abs(colorShape.x) + abs(colorShape.y) + 1.0e-7);
    float balanceAgreement = 1.0 - 0.5 * abs(greenBalance - colorBalance);
    return correlation * clamp(balanceAgreement, 0.0, 1.0);
}

float adaptivePhaseK26850(
    ivec2 position,
    vec2 sharedTranslationPixels,
    int phaseIndex,
    float peripheralGate
) {
    float baseK = calibratedPhaseLcaK26849(phaseIndex);
    peripheralGate = clamp(peripheralGate, 0.0, 1.0);
    if (abs(baseK) < 1.0e-12 || peripheralGate <= 1.0e-7) return 0.0;

    ivec2 nominalPhasePixel = pixelForPhaseLattice26790(position / 2, phaseIndex);
    vec2 nominalSourceCenter = vec2(nominalPhasePixel) + vec2(0.5);
    vec2 nominalTargetCenter = nominalSourceCenter - sharedTranslationPixels;
    vec2 opticalCenter = 0.5 * vec2(uOutputSize);
    vec2 radial = nominalTargetCenter - opticalCenter;
    float radialLength = length(radial);
    if (radialLength < 2.0) return 0.0;
    vec2 radialUnit = radial / radialLength;

    float greenMinus = greenGuideAtCenter26850(nominalSourceCenter - radialUnit);
    float greenCenter = greenGuideAtCenter26850(nominalSourceCenter);
    float greenPlus = greenGuideAtCenter26850(nominalSourceCenter + radialUnit);
    vec2 greenShape = vec2(
        greenCenter - greenMinus,
        greenPlus - greenCenter
    );
    float greenEnergy = abs(greenShape.x) + abs(greenShape.y);
    float greenScale = max(
        max(abs(greenCenter), 0.035 * max(uSourceWhiteNormalized26790, 1.0e-5)),
        1.0e-5);
    float relativeGreenEdge = greenEnergy / greenScale;
    float edgeGate = smoothstep(0.10, 0.30, relativeGreenEdge) * peripheralGate;
    if (edgeGate <= 0.15) return 0.0;

    float bestScore = phaseShapeScore26850(
        nominalSourceCenter, radialUnit, phaseIndex, greenShape);
    float bestK = 0.0;
    if (bestScore >= 0.96) return 0.0;

    for (int candidateIndex = 0; candidateIndex < 3; ++candidateIndex) {
        float candidateScale = candidateIndex == 0
            ? 2.0 : (candidateIndex == 1 ? 4.0 : 6.0);
        float candidateK = baseK * candidateScale * edgeGate;
        vec2 correctedTargetCenter = opticalCenter +
            (nominalTargetCenter - opticalCenter) * (1.0 - candidateK);
        vec2 correctedSourceCenter = correctedTargetCenter + sharedTranslationPixels;
        float candidateScore = phaseShapeScore26850(
            correctedSourceCenter, radialUnit, phaseIndex, greenShape);
        if (candidateScore >= 0.82 && candidateScore > bestScore + 0.08) {
            bestScore = candidateScore;
            bestK = candidateK;
        }
    }
    return bestK;
}

void correctedCfaScalar26792(
    ivec2 nominalSourcePixel,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    vec2 autoKrKb26850,
    out float rawValue,
    out float sourceHeadroomConfidence
) {
    nominalSourcePixel = clamp(
        nominalSourcePixel, ivec2(0), uOutputSize - ivec2(1));
    int phaseIndex = phaseAt26790(nominalSourcePixel);
    ivec2 nominalQ = nominalSourcePixel / 2;
    float legacyK26790 = phaseLcaK26790(phaseIndex);
    float autoK26850 = phaseIndex == redPhase26790()
        ? autoKrKb26850.x
        : (phaseIndex == bluePhase26790() ? autoKrKb26850.y : 0.0);
    float k = uJpegLcaEnabled26790 != 0 ? legacyK26790 : autoK26850;
    if (abs(k) < 1.0e-12) {
        rawValue = neutralBoundedRawCode26792(
            rawCode26791(nominalSourcePixel), nominalQ, phaseIndex);
        sourceHeadroomConfidence = selectedHeadroom26790(nominalQ, phaseIndex);
        return;
    }

    vec2 opticalCenter = 0.5 * vec2(uOutputSize);
    vec2 nominalSourceCenter = vec2(nominalSourcePixel) + vec2(0.5);
    vec2 nominalTargetCenter = nominalSourceCenter - sharedTranslationPixels;
    vec2 correctedTargetCenter = opticalCenter +
        (nominalTargetCenter - opticalCenter) * (1.0 - k);
    vec2 correctedSourceCenter = correctedTargetCenter + sharedTranslationPixels;

    ivec2 offset = phaseOffset26790(phaseIndex);
    vec2 latticeCoordinate = 0.5 *
        (correctedSourceCenter - (vec2(offset) + vec2(0.5)));
    ivec2 q00 = ivec2(floor(latticeCoordinate));
    vec2 frac = clamp(latticeCoordinate - vec2(q00), vec2(0.0), vec2(1.0));
    ivec2 q10 = q00 + ivec2(1, 0);
    ivec2 q01 = q00 + ivec2(0, 1);
    ivec2 q11 = q00 + ivec2(1, 1);
    q00 = clampPhaseLattice26790(q00, phaseIndex);
    q10 = clampPhaseLattice26790(q10, phaseIndex);
    q01 = clampPhaseLattice26790(q01, phaseIndex);
    q11 = clampPhaseLattice26790(q11, phaseIndex);

    float w00 = (1.0 - frac.x) * (1.0 - frac.y);
    float w10 = frac.x * (1.0 - frac.y);
    float w01 = (1.0 - frac.x) * frac.y;
    float w11 = frac.x * frac.y;
    float s00 = neutralBoundedRawCode26792(
        rawCode26791(pixelForPhaseLattice26790(q00, phaseIndex)), q00, phaseIndex);
    float s10 = neutralBoundedRawCode26792(
        rawCode26791(pixelForPhaseLattice26790(q10, phaseIndex)), q10, phaseIndex);
    float s01 = neutralBoundedRawCode26792(
        rawCode26791(pixelForPhaseLattice26790(q01, phaseIndex)), q01, phaseIndex);
    float s11 = neutralBoundedRawCode26792(
        rawCode26791(pixelForPhaseLattice26790(q11, phaseIndex)), q11, phaseIndex);
    rawValue = s00 * w00 + s10 * w10 + s01 * w01 + s11 * w11;
    sourceHeadroomConfidence =
        selectedHeadroom26790(q00, phaseIndex) * w00 +
        selectedHeadroom26790(q10, phaseIndex) * w10 +
        selectedHeadroom26790(q01, phaseIndex) * w01 +
        selectedHeadroom26790(q11, phaseIndex) * w11;
}

void fillCorrectedCfaNeighborhood26792(
    ivec2 position,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    float autoPeripheralLcaStrength26849,
    out mat3 bayerValue,
    out mat3 sourceValidity
) {
    bayerValue = mat3(0.0);
    sourceValidity = mat3(1.0);
    vec2 autoKrKb26850 = vec2(0.0);
    if (uJpegLcaEnabled26790 == 0 && autoPeripheralLcaStrength26849 > 1.0e-7) {
        autoKrKb26850.x = adaptivePhaseK26850(
            position, sharedTranslationPixels, redPhase26790(),
            autoPeripheralLcaStrength26849);
        autoKrKb26850.y = adaptivePhaseK26850(
            position, sharedTranslationPixels, bluePhase26790(),
            autoPeripheralLcaStrength26849);
    }

    /* Exact 26848 fallback when neither legacy LCA, neutral clamp nor adaptive registration
     * owns this output. This deliberately reproduces the inherited extracted-Bayer and
     * final-0.75%-headroom equations instead of merely approximating them through k=0. */
    if (uJpegLcaEnabled26790 == 0 && uJpegNeutralClamp26792 == 0 &&
            max(abs(autoKrKb26850.x), abs(autoKrKb26850.y)) < 1.0e-12) {
        bayerValue = get3x3FromExtractedBayer(position);
        if (uTemporalCfaOwner26852 != 0) {
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) {
                    ivec2 physicalPixel = clamp(
                        position + ivec2(sx - 1, sy - 1),
                        ivec2(0), uOutputSize - ivec2(1));
                    int phaseIndex = phaseAt26790(physicalPixel);
                    sourceValidity[sx][sy] = phaseHeadroomConfidence26790(
                        physicalPixel / 2, phaseIndex);
                }
            }
        } else {
            mat3 validityBayerValue26850 = bayerValue;
            float headroomStart26850 = max(1.0, uSourceClippingPoint * 0.9925);
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) {
                    sourceValidity[sx][sy] = 1.0 - smoothstep(
                        headroomStart26850,
                        max(headroomStart26850 + 1.0e-4, uSourceClippingPoint),
                        validityBayerValue26850[sx][sy]
                    );
                }
            }
        }
        return;
    }

    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            ivec2 physicalPixel = position + ivec2(sx - 1, sy - 1);
            float rawValue;
            float headroom;
            correctedCfaScalar26792(
                physicalPixel,
                sharedTranslationPixels,
                covariance,
                autoKrKb26850,
                rawValue,
                headroom
            );
            bayerValue[sx][sy] = rawValue;
            sourceValidity[sx][sy] = headroom;
        }
    }
}

float dngQuadRejection26790(ivec2 outputPixel) {
    if (uUseFrameWeight == 0) return 1.0;
    ivec2 quadOrigin = (outputPixel / 2) * 2;
    ivec2 maxPixel = uOutputSize - ivec2(1);
    vec2 invRawSize = 1.0 / vec2(uOutputSize);
    ivec2 p00 = clamp(quadOrigin, ivec2(0), maxPixel);
    ivec2 p10 = clamp(quadOrigin + ivec2(1, 0), ivec2(0), maxPixel);
    ivec2 p01 = clamp(quadOrigin + ivec2(0, 1), ivec2(0), maxPixel);
    ivec2 p11 = clamp(quadOrigin + ivec2(1, 1), ivec2(0), maxPixel);
    float w00 = texture(uRejection, (vec2(p00) + vec2(0.5)) * invRawSize).r;
    float w10 = texture(uRejection, (vec2(p10) + vec2(0.5)) * invRawSize).r;
    float w01 = texture(uRejection, (vec2(p01) + vec2(0.5)) * invRawSize).r;
    float w11 = texture(uRejection, (vec2(p11) + vec2(0.5)) * invRawSize).r;
    return min(min(w00, w10), min(w01, w11));
}

float luma26790(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
vec2 chroma26790(vec3 v) {
    float y = max(luma26790(v), 0.02);
    return vec2(v.r - v.g, v.b - v.g) / y;
}
vec3 rgbAtLumaFromChroma26790(float y, vec2 c) {
    return max(y * vec3(
        1.0 + 0.75 * c.x - 0.25 * c.y,
        1.0 - 0.25 * c.x - 0.25 * c.y,
        1.0 - 0.25 * c.x + 0.75 * c.y), vec3(0.0));
}

void main() {
    ivec2 outputPixel26790 = ivec2(gl_FragCoord.xy);
    vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
    vec3 accumulatedColor = vec3(0.0);
    vec3 accumulatedWeight = vec3(0.0);
    vec3 validAccumulatedWeight = vec3(0.0);
    float sourceNeighborhoodConfidence = 1.0;
    vec2 rowReliabilitySampleUv26790 = referenceUv;

    /* IRIS_26791_SABRE_SOLE_RGB_OWNER
     * One flow/covariance/topology invocation for LCA ON and OFF. When LCA is ON only the
     * scalar CFA producer beneath sampleNeighborhoodRbf changes; RGB topology never does. */
    vec2 flowUv26791 = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
    vec4 flow26791 = texture(uFlow, flowUv26791);
    vec2 sampleUv26791 = mirrorUvs(referenceUv + flow26791.xy);
    vec3 covariance26791 = unpackCovariance(texture(uCovariance, sampleUv26791).xyz);
    sampleNeighborhoodRbf(
        sampleUv26791,
        referenceUv,
        covariance26791,
        accumulatedColor,
        accumulatedWeight,
        sourceNeighborhoodConfidence,
        validAccumulatedWeight
    );
    rowReliabilitySampleUv26790 = sampleUv26791;

    /* IRIS_26790_LONG_CHROMA_NO_REINTRODUCTION
     * Completed NORMAL consensus is the sole chroma anchor. A LONG-only chroma departure
     * is sufficient to trigger the guard even when luma agrees; strong disagreement is
     * fully replaced at the same LONG luminance. */
    if (uLongChromaGuard26790 != 0 &&
            min(accumulatedWeight.r, min(accumulatedWeight.g, accumulatedWeight.b)) > 1.0e-7) {
        vec3 longMean = accumulatedColor / max(accumulatedWeight, vec3(1.0e-7));
        vec2 normalChroma = texelFetch(uNormalChromaConsensus26790, outputPixel26790, 0).rg;
        vec2 longChroma = chroma26790(longMean);
        float chromaMismatch = length(longChroma - normalChroma);
        float guard = smoothstep(0.035, 0.12, chromaMismatch);
        float longY = luma26790(longMean);
        vec3 normalAtLongLuma = rgbAtLumaFromChroma26790(longY, normalChroma);
        vec3 guardedLongMean = mix(longMean, normalAtLongLuma, guard);
        accumulatedColor = guardedLongMean * accumulatedWeight;
    }

    float frameWeight = uUseFrameWeight != 0
        ? texture(uRejection, referenceUv).r
        : 1.0;
    frameWeight *= iris26720MergeRowReliability(rowReliabilitySampleUv26790.y);
    /* IRIS_26852_TEMPORAL_CFA_SUPPORT_HANDOFF
     * The temporal carrier already owns NORMAL frame admission and source-headroom gating as one
     * scalar per Bayer quad. The one-time 26851 reconstruction consumes that support without
     * re-selecting R/G/B frames. Clip-zone provenance receives the separately accumulated
     * pre-headroom denominator and tunable numerator from the same carrier. */
    float spatialSupport26852 = dot(accumulatedWeight, vec3(0.25, 0.50, 0.25));
    if (uTemporalCfaOwner26852 != 0) {
        ivec2 supportQ26852 = outputPixel26790 / 2;
        vec4 temporalSupport26852 = texelFetch(uTemporalCfaSupport26852, supportQ26852, 0);
        frameWeight *= max(temporalSupport26852.x, 0.0);
        oClipZoneProvenance26834 = uClipZoneEnabled26834 != 0
            ? spatialSupport26852 * vec2(max(temporalSupport26852.z, 0.0),
                                         max(temporalSupport26852.y, 0.0))
            : vec2(0.0);
    } else {
        /* IRIS_26834_NORMAL_CLIP_ZONE_PROVENANCE */
        float scalarSupport26834 = spatialSupport26852 * frameWeight;
        float desiredWidth26834 = max(1.0 - clamp(uClipZoneClipStart26834, 0.97, 0.999), 1.0e-4);
        float remapExponent26834 = desiredWidth26834 / 0.0075;
        float clipConfidence26834 = pow(clamp(sourceNeighborhoodConfidence, 0.0, 1.0), remapExponent26834);
        oClipZoneProvenance26834 = uClipZoneEnabled26834 != 0
            ? vec2(scalarSupport26834 * clipConfidence26834, scalarSupport26834)
            : vec2(0.0);
        if (uSourceClipGuard != 0) {
            frameWeight *= mix(
                uSourceClippedWeight, 1.0,
                clamp(sourceNeighborhoodConfidence, 0.0, 1.0));
        }
    }
    accumulatedColor *= frameWeight;
    accumulatedWeight *= frameWeight;
    validAccumulatedWeight *= frameWeight;
    oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);
    oWeightsGb = accumulatedWeight.gb;
    oValidWeights = vec4(
        validAccumulatedWeight / max(uValidityWeightScale, 1.0e-6), 0.0);
}
