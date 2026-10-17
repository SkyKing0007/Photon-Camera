#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uNormalMean;
uniform sampler2D uNormalWeightR;
uniform sampler2D uNormalWeightsGb;
uniform sampler2D uNormalValidWeights;
uniform sampler2D uShortExtractedBayer;
uniform sampler2D uShortExtractedBayerValidity;
uniform sampler2D uShortFlow;
uniform sampler2D uShortCovariance;
uniform sampler2D uShortPhysicalReverseWeight;
uniform vec4 uFlowScaleOffset;
uniform ivec2 uExtractedSize;
uniform ivec2 uOutputSize;
uniform vec4 uFrameBorderPadded;
uniform int uCfaPattern;
uniform float uSourceClippingPoint;
uniform float uValidityWeightScale;
uniform vec4 uGains;
uniform vec4 uBlackLevelsTimesGains;
uniform vec4 uCovRangeRg;
uniform vec2 uCovRangeB;
uniform vec3 uShortShotNoiseRgb;
uniform vec3 uShortReadNoiseRgb;
uniform vec3 uNormalShotNoiseRgb;
uniform vec3 uNormalReadNoiseRgb;
uniform float uNormalFrameCount;
uniform float uReferenceProtectionEv;
layout(location = 0) out vec4 oFusedExtendedLinear;
layout(location = 1) out float oDecision;
layout(location = 2) out float oShortColorValidity;

bool shortWarpUvValid(vec2 sampleUv) {
    return sampleUv.x > uFrameBorderPadded.x && sampleUv.y > uFrameBorderPadded.y &&
        sampleUv.x < uFrameBorderPadded.z && sampleUv.y < uFrameBorderPadded.w;
}
float minimum3(vec3 v) { return min(v.r, min(v.g, v.b)); }
float secondHighest3(vec3 v) {
    return max(min(v.r, v.g), max(min(v.r, v.b), min(v.g, v.b)));
}
float luma(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
float shortGuide(vec2 uv) {
    vec4 q = texture(uShortExtractedBayerValidity, clamp(uv, vec2(0.0), vec2(1.0)));
    return dot(max(q, vec4(0.0)), vec4(0.25));
}
float normalFineStructureProtection() {
    /* IRIS_26653_FULL_RES_FINE_STRUCTURE_SHORT_RADIANCE_GUARD
     * The packed SHORT guide cannot prove one-pixel/two-pixel ridge phase. Detect such
     * structure directly in the full-resolution NORMAL master. On coherent fine detail,
     * an interpolated SHORT> NORMAL brightness difference is not sufficient evidence of
     * radiometric loss; measured NORMAL source-validity loss is still allowed to recover.
     * This is semantic-independent: lamp ribs, hair, fabric, needles, text and wires use
     * the same second-derivative proof. */
    ivec2 c = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uOutputSize - ivec2(1));
    ivec2 lP = clamp(c + ivec2(-1, 0), ivec2(0), uOutputSize - ivec2(1));
    ivec2 rP = clamp(c + ivec2( 1, 0), ivec2(0), uOutputSize - ivec2(1));
    ivec2 dP = clamp(c + ivec2( 0,-1), ivec2(0), uOutputSize - ivec2(1));
    ivec2 uP = clamp(c + ivec2( 0, 1), ivec2(0), uOutputSize - ivec2(1));
    float cc = luma(max(texelFetch(uNormalMean, c, 0).rgb, vec3(0.0)));
    float ll = luma(max(texelFetch(uNormalMean, lP, 0).rgb, vec3(0.0)));
    float rr = luma(max(texelFetch(uNormalMean, rP, 0).rgb, vec3(0.0)));
    float dd = luma(max(texelFetch(uNormalMean, dP, 0).rgb, vec3(0.0)));
    float uu = luma(max(texelFetch(uNormalMean, uP, 0).rgb, vec3(0.0)));
    float scale = max(max(cc, 0.25 * (ll + rr + dd + uu)), 0.035);
    float lap = abs((ll + rr + dd + uu) - 4.0 * cc) / (4.0 * scale);
    float ridgeX = abs(ll - 2.0 * cc + rr) / (2.0 * scale);
    float ridgeY = abs(dd - 2.0 * cc + uu) / (2.0 * scale);
    return smoothstep(0.035, 0.120, max(lap, max(ridgeX, ridgeY)));
}

float edgeCorrespondence(vec2 referenceUv, vec2 sampleUv) {
    /* IRIS_26651_MEASURABLE_EDGE_CORRESPONDENCE
     * Compare edge direction at the exact production warp on the 2x2-CFA-quad scale.
     * SHORT exposure magnitude is irrelevant because each gradient is normalized locally.
     * This is an absolute image correspondence check; flow.w remains only a local-affine
     * coherence input and is never interpreted as absolute registration error. */
    vec2 stepUv = 1.0 / vec2(uExtractedSize);
    float nL = luma(max(texture(uNormalMean, clamp(referenceUv - vec2(stepUv.x, 0.0), vec2(0.0), vec2(1.0))).rgb, vec3(0.0)));
    float nR = luma(max(texture(uNormalMean, clamp(referenceUv + vec2(stepUv.x, 0.0), vec2(0.0), vec2(1.0))).rgb, vec3(0.0)));
    float nD = luma(max(texture(uNormalMean, clamp(referenceUv - vec2(0.0, stepUv.y), vec2(0.0), vec2(1.0))).rgb, vec3(0.0)));
    float nU = luma(max(texture(uNormalMean, clamp(referenceUv + vec2(0.0, stepUv.y), vec2(0.0), vec2(1.0))).rgb, vec3(0.0)));
    float sL = shortGuide(sampleUv - vec2(stepUv.x, 0.0));
    float sR = shortGuide(sampleUv + vec2(stepUv.x, 0.0));
    float sD = shortGuide(sampleUv - vec2(0.0, stepUv.y));
    float sU = shortGuide(sampleUv + vec2(0.0, stepUv.y));
    vec2 ng = vec2(nR - nL, nU - nD);
    vec2 sg = vec2(sR - sL, sU - sD);
    float nScale = max(0.25 * (nL + nR + nD + nU), 0.03);
    float sScale = max(0.25 * (sL + sR + sD + sU), 1.0);
    float nStrength = length(ng) / nScale;
    float sStrength = length(sg) / sScale;
    float structure = smoothstep(0.05, 0.16, nStrength);
    float direction = dot(ng, sg) / max(length(ng) * length(sg), 1.0e-8);
    float directionTrust = smoothstep(0.15, 0.80, direction);
    float strengthRatio = min(nStrength, sStrength) / max(max(nStrength, sStrength), 1.0e-5);
    float edgeTrust = directionTrust * smoothstep(0.12, 0.55, strengthRatio);
    return mix(1.0, edgeTrust, structure);
}

/* IRIS_26652_LOCAL_CHROMA_CONSENSUS
 * Color recovery is a neighborhood-consensus problem, never a per-pixel SHORT repaint.
 * Reliable NORMAL neighbors on the same luminance surface define chromaticity. This is
 * semantic-independent: leaves, hair, wires, fabric, text and lamps use identical proof. */
vec3 normalValidityAt(ivec2 p) {
    ivec2 q = clamp(p, ivec2(0), uOutputSize - ivec2(1));
    vec3 total = vec3(
        max(texelFetch(uNormalWeightR, q, 0).r, 0.0),
        max(texelFetch(uNormalWeightsGb, q, 0).r, 0.0),
        max(texelFetch(uNormalWeightsGb, q, 0).g, 0.0));
    vec3 valid = max(texelFetch(uNormalValidWeights, q, 0).rgb, vec3(0.0)) *
        max(uValidityWeightScale, 1.0);
    return clamp(valid / max(total, vec3(1.0e-6)), vec3(0.0), vec3(1.0));
}
vec3 chromaticityAtLuma(vec3 rgb) {
    vec3 safe = max(rgb, vec3(0.0));
    return safe / max(luma(safe), 1.0e-5);
}
void localNormalChromaConsensus(
    ivec2 centerPixel, float targetY,
    out vec3 consensusChromaticity, out float consensusConfidence,
    out float consensusSupport, out float consensusSpread
) {
    vec3 sumC = vec3(0.0);
    vec3 sumC2 = vec3(0.0);
    float sumW = 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            if (abs(x) + abs(y) != 1) continue; // four-neighbor cross: bounded mobile-GPU cost
            ivec2 q = clamp(centerPixel + ivec2(x, y), ivec2(0), uOutputSize - ivec2(1));
            vec3 rgb = max(texelFetch(uNormalMean, q, 0).rgb, vec3(0.0));
            float yq = luma(rgb);
            float relativeLumaDelta = abs(yq - targetY) /
                max(max(yq, targetY), 0.04);
            float sameSurface = 1.0 - smoothstep(0.20, 0.58, relativeLumaDelta);
            float valid = minimum3(normalValidityAt(q));
            float measured = smoothstep(0.82, 0.98, valid);
            float w = sameSurface * measured;
            vec3 c = chromaticityAtLuma(rgb);
            sumC += c * w;
            sumC2 += c * c * w;
            sumW += w;
        }
    }
    consensusSupport = sumW;
    consensusChromaticity = sumW > 1.0e-5 ? sumC / sumW : vec3(1.0);
    vec3 variance = sumW > 1.0e-5
        ? max(sumC2 / sumW - consensusChromaticity * consensusChromaticity, vec3(0.0))
        : vec3(1.0);
    consensusSpread = sqrt(max(dot(variance, vec3(1.0 / 3.0)), 0.0));
    float supportConfidence = smoothstep(0.75, 1.80, sumW);
    float uniformityConfidence = 1.0 - smoothstep(0.025, 0.10, consensusSpread);
    consensusConfidence = supportConfidence * uniformityConfidence;
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
    vec4 bayer0 = texture(uShortExtractedBayer, texturePosition * reciprocalSize);
    vec4 bayer1 = texture(
        uShortExtractedBayer,
        (texturePosition + vec2(1.0, 0.0)) * reciprocalSize
    );
    vec4 bayer2 = texture(
        uShortExtractedBayer,
        (texturePosition + vec2(0.0, 1.0)) * reciprocalSize
    );
    vec4 bayer3 = texture(
        uShortExtractedBayer,
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

mat3 get3x3FromExtractedBayerValidity(ivec2 bayerPosition) {
    mat3 values = mat3(0.0);
    int type = (bayerPosition.y % 2) * 2 + (bayerPosition.x % 2);
    vec2 texturePosition = vec2(bayerPosition / 2);
    if (type == 0) texturePosition += vec2(-1.0, -1.0);
    else if (type == 1) texturePosition += vec2(0.0, -1.0);
    else if (type == 2) texturePosition += vec2(-1.0, 0.0);
    texturePosition += vec2(0.5);
    vec2 reciprocalSize = 1.0 / vec2(uExtractedSize);
    vec4 bayer0 = texture(uShortExtractedBayerValidity, texturePosition * reciprocalSize);
    vec4 bayer1 = texture(
        uShortExtractedBayerValidity,
        (texturePosition + vec2(1.0, 0.0)) * reciprocalSize
    );
    vec4 bayer2 = texture(
        uShortExtractedBayerValidity,
        (texturePosition + vec2(0.0, 1.0)) * reciprocalSize
    );
    vec4 bayer3 = texture(
        uShortExtractedBayerValidity,
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

float predictSameLocationGreen26793(
    mat3 calculationCfa,
    mat3 greenSupport,
    ivec2 colorLocal,
    int type,
    float horizontalGreenWeight,
    float verticalGreenWeight,
    int useGreenSupport,
    out float greenConfidence
) {
    float numerator = 0.0;
    float supportedWeight = 0.0;
    float fullWeight = 0.0;
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
            fullWeight += spatialWeight;
            supportedWeight += spatialWeight * physicalSupport;
            numerator += calculationCfa[q.x][q.y] * spatialWeight * physicalSupport;
        }
    }
    greenConfidence = clamp(
        supportedWeight / max(fullWeight, 1.0e-7), 0.0, 1.0);
    if (supportedWeight <= 1.0e-7) return 0.0;
    return numerator / supportedWeight;
}

void sameLocationChroma26793(
    mat3 calculationCfa,
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
    for (int sx = 0; sx < 3; ++sx) {
        for (int sy = 0; sy < 3; ++sy) {
            int groupIndex = relativeCfaGroup26793(sx, sy);
            if (groupIndex != redGroup && groupIndex != blueGroup) continue;
            float colorWeight = max(sampleWeights[sx][sy], 0.0);
            if (groupIndex == redGroup) redTotalWeight += colorWeight;
            else blueTotalWeight += colorWeight;
            float greenConfidence = 0.0;
            float predictedGreen = predictSameLocationGreen26793(
                calculationCfa, greenSupport, ivec2(sx, sy), type,
                horizontalGreenWeight, verticalGreenWeight,
                useGreenSupport, greenConfidence);
            float differenceWeight = colorWeight * greenConfidence;
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
    float legacyDR = legacyRgb.r - legacyRgb.g;
    float legacyDB = legacyRgb.b - legacyRgb.g;
    float measuredDR = redDifferenceWeight > 1.0e-7
        ? redDifferenceSum / redDifferenceWeight : legacyDR;
    float measuredDB = blueDifferenceWeight > 1.0e-7
        ? blueDifferenceSum / blueDifferenceWeight : legacyDB;
    float redPhysicalFraction = clamp(
        redDifferenceWeight / max(redTotalWeight, 1.0e-7), 0.0, 1.0);
    float bluePhysicalFraction = clamp(
        blueDifferenceWeight / max(blueTotalWeight, 1.0e-7), 0.0, 1.0);
    dR = mix(legacyDR, measuredDR, redPhysicalFraction);
    dB = mix(legacyDB, measuredDB, bluePhysicalFraction);
}

void sampleNeighborhoodRbf(
    vec2 sampleUv,
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
    mat3 bayerValue = get3x3FromExtractedBayer(position);
    mat3 validityBayerValue26788 = get3x3FromExtractedBayerValidity(position);
    mat3 sourceValidity = mat3(1.0);
    float headroomStart=max(1.0,uSourceClippingPoint*0.9925);
    for (int sx=0;sx<3;++sx) {
        for (int sy=0;sy<3;++sy) {
            /* IRIS_26648_SAMPLE_LEVEL_SHORT_VALIDITY
             * Saturated SHORT CFA samples receive zero radiometric authority individually.
             * One bad sample must not veto other valid same-color evidence in the 3x3 RBF. */
            sourceValidity[sx][sy]=1.0-smoothstep(
                headroomStart,max(headroomStart+1.0e-4,uSourceClippingPoint),
                validityBayerValue26788[sx][sy]);
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
        dot(value1 * reorderedGains.r + reorderedBlack.r, validCornerWeights),
        dot(value2 * reorderedGains.g + reorderedBlack.g, validUpDownWeights),
        dot(value3 * reorderedGains.b + reorderedBlack.b, validLeftRightWeights),
        (bayerValue[1][1] * reorderedGains.a + reorderedBlack.a) * validWeights[1][1]
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
    vec3 fullAccumulatedWeights = vec3(
        reorderedWeights.r,
        reorderedWeights.g + reorderedWeights.b,
        reorderedWeights.a
    );
    validAccumulatedWeights = vec3(
        validReorderedWeights.r,
        validReorderedWeights.g + validReorderedWeights.b,
        validReorderedWeights.a
    );
    /* RGB is reconstructed only from physically valid SHORT samples. Confidence is the
     * weakest color's retained RBF support fraction, not the weakest individual sample. */
    accumulatedWeights = validAccumulatedWeights;
    vec3 legacyRgb26793 = vec3(
        intensities.r,
        intensities.g + intensities.b,
        intensities.a
    ) / max(accumulatedWeights, vec3(1.0e-7));
    mat3 calculationCfa26793 = mat3(0.0);
    buildCalculationCfa26793(
        bayerValue, reorderedGains, reorderedBlack, calculationCfa26793);
    float dR26793 = 0.0;
    float dB26793 = 0.0;
    sameLocationChroma26793(
        calculationCfa26793, validWeights, sourceValidity, type, covariance, 1,
        legacyRgb26793, dR26793, dB26793);
    float legacyLuma26793 = dot(legacyRgb26793, vec3(0.25, 0.50, 0.25));
    float correctedG26793 = legacyLuma26793 - 0.25 * (dR26793 + dB26793);
    vec3 correctedRgb26793 = vec3(
        correctedG26793 + dR26793,
        correctedG26793,
        correctedG26793 + dB26793);
    accumulatedIntensities = correctedRgb26793 * accumulatedWeights;
    sourceNeighborhoodConfidence = minimum3(clamp(
        validAccumulatedWeights / max(fullAccumulatedWeights, vec3(1.0e-6)),
        vec3(0.0), vec3(1.0)));
}

void main() {
    vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
    vec4 normalMean = texture(uNormalMean, referenceUv);
    vec3 totalWeight = vec3(
        max(texture(uNormalWeightR, referenceUv).r, 0.0),
        max(texture(uNormalWeightsGb, referenceUv).r, 0.0),
        max(texture(uNormalWeightsGb, referenceUv).g, 0.0));
    vec3 validWeight = max(texture(uNormalValidWeights, referenceUv).rgb, vec3(0.0)) *
        max(uValidityWeightScale, 1.0);
    vec3 normalValidity = clamp(validWeight / max(totalWeight, vec3(1.0e-6)), 0.0, 1.0);
    float normalSourceConfidence = minimum3(normalValidity);
    float normalTemporalConfidence = clamp(normalMean.a, 0.0, 1.0);
    vec3 normalVariance = max(
        uNormalShotNoiseRgb * max(normalMean.rgb, vec3(0.0)) + uNormalReadNoiseRgb,
        vec3(1.0e-8)) / max(1.0, uNormalFrameCount * max(normalTemporalConfidence, 0.10));
    float normalSnr = luma(max(normalMean.rgb, vec3(0.0))) /
        sqrt(max(luma(normalVariance), 1.0e-8));
    float normalSnrConfidence = smoothstep(3.0, 8.0, normalSnr);

    vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
    vec4 flow = texture(uShortFlow, flowUv);
    vec2 sampleUv = referenceUv + flow.xy;
    /* Use the exact undilated ordinary Sabre physical blocker. Rejection dilation is deliberately
     * not an HDR fusion mask: it could widen exposure transitions and create edge halos. */
    ivec2 physicalCell = clamp(ivec2(referenceUv * vec2(uExtractedSize)),
        ivec2(0), uExtractedSize - ivec2(1));
    float physicalWeight = 1.0 - clamp(
        texelFetch(uShortPhysicalReverseWeight, physicalCell, 0).r, 0.0, 1.0);
    /* IRIS_26651_SHORT_LOCAL_AFFINE_COHERENCE_INPUT
     * flow.w is a local affine residual, not absolute registration error. It is retained
     * only as one coherence input; measurable image-edge correspondence below proves that
     * the exact production warp is spatially compatible before SHORT can alter radiance. */
    float alignmentConfidence = 1.0 - smoothstep(0.50, 2.00, max(flow.w, 0.0));
    if (physicalWeight <= 0.001 || alignmentConfidence <= 0.001 ||
        !shortWarpUvValid(sampleUv)) {
        oFusedExtendedLinear = normalMean;
        oDecision = 204.0 / 255.0;
        oShortColorValidity = 0.0; // physical geometry/support rejection
        return;
    }
    vec3 covariance = unpackCovariance(texture(uShortCovariance, sampleUv).xyz);
    vec3 shortColorSum = vec3(0.0);
    vec3 shortWeights = vec3(0.0);
    vec3 shortValidWeights = vec3(0.0);
    float shortSourceConfidence = 1.0;
    sampleNeighborhoodRbf(sampleUv, covariance, shortColorSum, shortWeights,
        shortSourceConfidence, shortValidWeights);
    if (shortSourceConfidence <= 0.001 || minimum3(shortWeights) <= 1.0e-6) {
        oFusedExtendedLinear = normalMean;
        oDecision = 224.0 / 255.0;
        oShortColorValidity = 0.0; // SHORT source clipped/incomplete
        return;
    }
    vec3 shortRgb = shortColorSum / max(shortWeights, vec3(1.0e-6));
    vec3 shortVariance = max(
        uShortShotNoiseRgb * max(shortRgb, vec3(0.0)) + uShortReadNoiseRgb,
        vec3(1.0e-8));
    float shortSnr = luma(max(shortRgb, vec3(0.0))) /
        sqrt(max(luma(shortVariance), 1.0e-8));
    float shortSnrConfidence = smoothstep(3.0, 8.0, shortSnr);
    if (shortSnrConfidence <= 0.001) {
        oFusedExtendedLinear = normalMean;
        oDecision = 240.0 / 255.0;
        oShortColorValidity = 0.0; // SHORT signal/SNR rejection
        return;
    }

    /* IRIS_26651_PHYSICAL_LOSS_SPLIT
     * Radiometric loss may prove that NORMAL lost luminance before literal clipping, but
     * it does not prove NORMAL lost chromaticity. Therefore partial loss is scalar-only.
     * The separate color gate below is derived strictly from measured NORMAL CFA validity
     * and requires physical loss in all three color supports. */
    vec3 relativeLoss = max(shortRgb - normalMean.rgb, vec3(0.0)) /
        max(shortRgb, vec3(0.05));
    vec3 radiometricLossByChannel = smoothstep(vec3(0.05), vec3(0.12), relativeLoss) *
        smoothstep(vec3(0.55), vec3(0.90), max(shortRgb, vec3(0.0)));
    float effectiveRadiometricLoss = secondHighest3(radiometricLossByChannel);
    float physicalNormalLoss = clamp(1.0 - normalSourceConfidence, 0.0, 1.0);
    float fineStructure = normalFineStructureProtection();
    float fineStructurePhysicalSupport = smoothstep(0.20, 0.70, physicalNormalLoss);
    float inferredRadiometricLoss = effectiveRadiometricLoss *
        mix(1.0, fineStructurePhysicalSupport, fineStructure);
    /* IRIS_26704_FAIL_CLOSED_INFERRED_SHORT_RADIANCE
     * A brighter warped SHORT sample does not prove highlight loss when NORMAL itself is
     * a dark foreground structure against a bright background. Require two-channel NORMAL
     * highlight context before non-physical inferred loss can contribute. Literal/measured
     * CFA loss remains independent below, so genuine clipped highlight recovery survives. */
    float normalRadiometricGuide = secondHighest3(max(normalMean.rgb, vec3(0.0)));
    float inferredHighlightContext = smoothstep(0.22, 0.50, normalRadiometricGuide);
    inferredRadiometricLoss *= inferredHighlightContext;
    /* IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION
     * Once 26674 has deliberately protected the NORMAL reference, a brighter normalized
     * SHORT sample is no longer sufficient evidence of NORMAL radiometric loss: amplifying
     * the ~2.5 EV SHORT can otherwise inject neutral/chroma speckle into valid smooth bright
     * surfaces. In that protected state SHORT may alter radiance only where the existing
     * per-CFA NORMAL validity proves actual source loss. Unprotected NORMAL retains the
     * exact 26674 inferred-loss path, preserving prior highlight behavior. */
    float protectedNormalActive = step(0.25, uReferenceProtectionEv);
    inferredRadiometricLoss *= (1.0 - protectedNormalActive);
    /* IRIS_26705_SHORT_RADIANCE_HIGHLIGHT_DOMAIN_ONLY
     * Even literal NORMAL validity loss does not grant SHORT ownership in shadows/body.
     * SHORT is a highlight radiance donor only; dark structures, blacks, text, foliage gaps
     * and other body content remain NORMAL-owned regardless of local validity weakness. */
    float shortRadiometricGuide = secondHighest3(max(shortRgb, vec3(0.0)));
    float physicalHighlightContext = smoothstep(
        0.38, 0.62, max(normalRadiometricGuide, shortRadiometricGuide));
    float measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss) *
        physicalHighlightContext;
    float edgeTrust = edgeCorrespondence(referenceUv, sampleUv);
    float shortConfidence = physicalWeight * alignmentConfidence * edgeTrust *
        shortSourceConfidence * shortSnrConfidence;
    /* IRIS_26704_LOW_NORMAL_CONFIDENCE_NEVER_BOOSTS_SHORT
     * Low local NORMAL support may attenuate an otherwise-proven SHORT rescue, but it must
     * never increase SHORT authority. Keep the inherited conservative 0.82 floor to avoid
     * weakening genuine physical highlight recovery while correcting the directionality. */
    float transitionSupport = mix(0.82, 1.0,
        min(normalTemporalConfidence, normalSnrConfidence));
    float radianceAuthority = clamp(
        shortConfidence * measuredNormalLoss * transitionSupport,
        0.0, 1.0);

    float normalY = luma(max(normalMean.rgb, vec3(0.0)));
    float shortY = luma(max(shortRgb, vec3(0.0)));
    float targetY = mix(normalY, shortY, radianceAuthority);
    vec3 normalChromaCarrier = max(normalMean.rgb, vec3(0.0)) *
        (targetY / max(normalY, 1.0e-5));
    vec3 shortChromaCarrier = max(shortRgb, vec3(0.0)) *
        (targetY / max(shortY, 1.0e-5));

    vec3 measuredNormalPhysicalLoss = clamp(vec3(1.0) - normalValidity, 0.0, 1.0);
    float allColorSupportLost = smoothstep(
        0.55, 0.90, minimum3(measuredNormalPhysicalLoss));

    /* IRIS_26652_TRUSTED_SHORT_CHROMA_CONSENSUS
     * All-three NORMAL loss makes color recovery eligible, not automatically trustworthy.
     * The recovered luminance remains the already-proven scalar targetY. Color comes from
     * uniform, same-surface, measured NORMAL neighbors. SHORT chromaticity may reinforce
     * that consensus only when it agrees; an isolated pink/cyan/blue SHORT outlier cannot
     * repaint a tiny object. If no trustworthy color survives, fail closed to NORMAL
     * chromaticity at the recovered luminance rather than inventing hue. */
    ivec2 centerPixel = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uOutputSize - ivec2(1));
    vec3 consensusChromaticity;
    float consensusConfidence;
    float consensusSupport;
    float consensusSpread;
    localNormalChromaConsensus(
        centerPixel, targetY, consensusChromaticity, consensusConfidence,
        consensusSupport, consensusSpread);
    vec3 shortChromaticity = chromaticityAtLuma(shortRgb);
    float shortConsensusDistance = length(shortChromaticity - consensusChromaticity);
    float shortConsensusAgreement = 1.0 - smoothstep(0.08, 0.22, shortConsensusDistance);
    vec3 consensusCarrier = consensusChromaticity * targetY;
    vec3 consensusWithShort = mix(
        consensusCarrier, shortChromaCarrier, 0.35 * shortConsensusAgreement);

    /* IRIS_26704_VALID_NORMAL_CHROMA_IMMUTABLE
     * Neighborhood color is reconstruction evidence only after measured CFA validity proves
     * that all three NORMAL color supports are physically lost. A more colorful neighbor
     * must never independently declare a valid neutral/different-colored center "washed
     * out"; this protects sign lettering, foliage/sky boundaries and tiny sky holes. */
    float colorRecoveryNeed = allColorSupportLost;
    float colorEligibility = clamp(radianceAuthority * colorRecoveryNeed, 0.0, 1.0);

    /* No trustworthy local color means no invented camera-domain neutral. Preserve the
     * NORMAL chromaticity at the recovered targetY. When consensus is trustworthy it
     * dominates, with agreeing SHORT color allowed only as bounded supporting evidence. */
    vec3 trustedRecoveredColor = mix(
        normalChromaCarrier, consensusWithShort, consensusConfidence);
    vec3 fused = mix(normalChromaCarrier, trustedRecoveredColor, colorEligibility);
    oFusedExtendedLinear = vec4(fused, normalMean.a); // SHORT never inflates temporal support

    /* Pack color-provenance state into the existing R8 decision telemetry without adding a
     * fourth attachment/readback. 48 quantized radiance levels preserve scalar telemetry.
     * 0=not color-eligible, 1=eligible/no trustworthy consensus (NORMAL-chroma fallback),
     * 2=consensus trusted but center SHORT chroma rejected as outlier, 3=SHORT agrees. */
    float colorState = 0.0;
    if (colorEligibility > 0.005) {
        if (consensusConfidence <= 0.20) colorState = 1.0;
        else if (shortConsensusAgreement < 0.50) colorState = 2.0;
        else colorState = 3.0;
    }
    float radianceCode = floor(clamp(radianceAuthority, 0.0, 1.0) * 47.0 + 0.5);
    oDecision = (colorState * 48.0 + radianceCode) / 255.0;

    /* IRIS_26652_CONTINUOUS_COLOR_VALIDITY
     * Publish only confidence that can raise the weakest measured validity toward 0.970.
     * This intentionally stays below the downstream 0.985 measured-color-protection knee,
     * preventing a hard validity seam from disabling false-color cleanup on one side. */
    float trustedColorConfidence = colorEligibility * consensusConfidence;
    float validityRoom = max(0.970 - normalSourceConfidence, 0.0);
    oShortColorValidity = validityRoom * trustedColorConfidence;
}
