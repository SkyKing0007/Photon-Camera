package com.hinnka.mycamera.processor

/**
 * GLES translation of MGC's Sabre programs from sabre_programs.cc/sabre_merge.cc.
 *
 * Sabre works on an extracted 2x2 Bayer texture, builds its guide and covariance at one sample
 * per Bayer quad, accumulates camera RGB and three independent weights in a full-resolution MRT,
 * then dehomogenizes the result before the ResolveSabre stage.
 */
internal object GlesMgcRawSabreShaders {
    val extractBayer = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        layout(location = 0) out vec4 oExtractedBayer;

        float rawAt(ivec2 p) {
            return float(texelFetch(uRaw, clamp(p, ivec2(0), uRawSize - ivec2(1)), 0).r);
        }

        void main() {
            ivec2 q = ivec2(gl_FragCoord.xy);
            ivec2 p = q * 2;
            // GetFourPixelsFromPacked16 stores the spatial 2x2 order. The epsilon is present in
            // the embedded MGC source and prevents zero-valued half-float samples.
            oExtractedBayer = vec4(
                rawAt(p),
                rawAt(p + ivec2(1, 0)),
                rawAt(p + ivec2(0, 1)),
                rawAt(p + ivec2(1, 1))
            ) + vec4(1.0e-4);
        }
    """.trimIndent()

    val guideAndCovariance = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uNoiseEstimates;
        uniform ivec2 uGuideSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uNoiseTextureScaleBias;
        uniform vec4 uCovarianceParameters1;
        uniform vec4 uCovarianceParameters2;
        uniform vec4 uCovRangeRgFactors;
        uniform vec2 uCovRangeBFactor;
        uniform float uGreenClippingPoint;
        // IRIS_26545 current Sabre contract: x is a strict 0/1 switch.
        uniform vec4 uForceReferenceColorRgb;
        layout(location = 0) out vec4 oGuide;
        layout(location = 1) out vec4 oCovariance;

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

        vec4 canonicalQuad(vec2 uv) {
            vec4 spatial = vec4(uvec4(texture(uExtractedBayer, uv)));
            vec4 canonical;
            if (uCfaPattern == 0) canonical = spatial;
            else if (uCfaPattern == 1) canonical = spatial.yxwz;
            else if (uCfaPattern == 2) canonical = spatial.zwxy;
            else canonical = spatial.wzyx;
            return canonical * uGains + uBlackLevelsTimesGains;
        }

        float weight1d(int x) {
            return x == 0 ? 0.5 : 0.25;
        }

        void accumulateGradient(float dx, float dy, inout vec4 tensor) {
            tensor += vec4(dx * dx, dy * dy, dx * dy, 0.0);
        }

        vec4 structureTensor(float green0[9], float green1[9]) {
            vec4 tensor = vec4(0.0);
            for (int y = 0; y < 2; ++y) {
                for (int x = 0; x < 2; ++x) {
                    float g00 = green0[y * 3 + x];
                    float g01 = green0[y * 3 + x + 1];
                    float g10 = green1[y * 3 + x];
                    float g11 = green1[y * 3 + x + 1];
                    float g20 = green0[(y + 1) * 3 + x];
                    float g21 = green0[(y + 1) * 3 + x + 1];
                    float g30 = green1[(y + 1) * 3 + x];
                    float g31 = green1[(y + 1) * 3 + x + 1];
                    float bdx;
                    float bdy;
                    float rdx;
                    float rdy;
                    if (uCfaPattern == 1 || uCfaPattern == 2) {
                        bdx = 0.5 * ((g11 - g01) + (g21 - g10));
                        bdy = 0.5 * ((g01 - g10) + (g11 - g21));
                        rdx = 0.5 * ((g21 - g10) + (g30 - g20));
                        rdy = 0.5 * ((g21 - g30) + (g10 - g20));
                    } else {
                        bdx = 0.5 * ((g11 - g00) + (g20 - g10));
                        bdy = 0.5 * ((g00 - g10) + (g11 - g20));
                        rdx = 0.5 * ((g21 - g11) + (g31 - g20));
                        rdy = 0.5 * ((g21 - g31) + (g11 - g20));
                    }
                    accumulateGradient(bdx, bdy, tensor);
                    accumulateGradient(rdx, rdy, tensor);
                    accumulateGradient(0.5 * (g21 - g00), 0.5 * (g01 - g20), tensor);
                    accumulateGradient(0.5 * (g31 - g10), 0.5 * (g11 - g30), tensor);
                }
            }
            tensor /= 16.0;
            tensor.w = 0.75;
            float c0 = 0.5 * (tensor.x + tensor.y);
            float c1 = 0.5 * (tensor.y - tensor.x);
            return vec4(c0 + tensor.z, c0 - tensor.z, c1, tensor.w);
        }

        vec3 constructCovariance(vec4 tensor, float greenVariance, float greenNoise) {
            float trace = tensor.x + tensor.y;
            float difference = tensor.x - tensor.y;
            float discriminant = sqrt(max(
                difference * difference + 4.0 * tensor.z * tensor.z,
                0.0
            ));
            float eigenvalue1 = 0.5 * (trace + discriminant);
            float eigenvalue2 = 0.5 * (trace - discriminant);
            vec2 eigenvector1 = vec2(1.0, 0.0);
            if (abs(tensor.z) > 0.0001) {
                eigenvector1 = normalize(vec2(tensor.z, eigenvalue1 - tensor.x)) *
                    -sign(tensor.z);
            } else if (tensor.x < tensor.y) {
                eigenvector1 = vec2(0.0, 1.0);
            }
            vec2 eigenvector2 = vec2(-eigenvector1.y, eigenvector1.x);
            float singularValue1 = sqrt(eigenvalue1);
            float singularValue2 = sqrt(max(eigenvalue2, 0.0));
            float correction = tensor.w * greenNoise;
            eigenvalue1 *= eigenvalue1 / (eigenvalue1 + correction);
            float strength = sqrt(max(eigenvalue1, 0.0));
            float coherence = (singularValue1 - singularValue2) /
                (singularValue1 + singularValue2 + 1.0e-6);
            float greenStdDev = sqrt(
                greenVariance * greenVariance / (greenVariance + greenNoise)
            );
            float gradientBlurring = clamp(
                1.0 -
                    (max(strength, greenStdDev) - uCovarianceParameters1.z) *
                    uCovarianceParameters2.y,
                0.0,
                1.0
            );
            float anisotropicShrinking = mix(
                uCovarianceParameters1.w,
                uCovarianceParameters1.x,
                min(coherence, strength * 5.0)
            );
            float sigma1 = mix(
                anisotropicShrinking,
                uCovarianceParameters2.x,
                gradientBlurring
            );
            float sigma2 = mix(
                mix(uCovarianceParameters1.w, uCovarianceParameters1.y, coherence),
                uCovarianceParameters2.x,
                gradientBlurring
            );
            mat2 rotation = mat2(eigenvector1, eigenvector2);
            mat2 covariance = transpose(rotation) * mat2(
                sigma1 * sigma1, 0.0,
                0.0, sigma2 * sigma2
            ) * rotation;
            return vec3(covariance[0].x, covariance[1].y, covariance[0].y);
        }

        void main() {
            vec2 centerUv = mirrorUvs(gl_FragCoord.xy / vec2(uGuideSize));
            vec2 reciprocalSize = 1.0 / vec2(uGuideSize);
            float green0[9];
            float green1[9];
            vec3 rgbSum = vec3(0.0);
            vec3 rgbSquareSum = vec3(0.0);
            float greenSum = 0.0;
            float greenSquareSum = 0.0;
            vec3 averageRgb = vec3(0.0);
            float centerGreen = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    vec4 rggb = canonicalQuad(
                        centerUv + vec2(float(x), float(y)) * reciprocalSize
                    );
                    // MGC constructs Bayer Sabre programs with SQRT_COLOR_SPACE enabled. Guide
                    // color, local variance, and the structure tensor must all use this domain.
                    rggb = sqrt(max(vec4(0.0), rggb));
                    int index = (y + 1) * 3 + x + 1;
                    if (uCfaPattern == 2 || uCfaPattern == 3) {
                        green0[index] = rggb.z;
                        green1[index] = rggb.y;
                    } else {
                        green0[index] = rggb.y;
                        green1[index] = rggb.z;
                    }
                    vec3 rgb = vec3(rggb.x, 0.5 * (rggb.y + rggb.z), rggb.w);
                    averageRgb += rgb * weight1d(x) * weight1d(y);
                    rgbSum += rgb;
                    rgbSquareSum += rgb * rgb;
                    greenSum += rggb.y + rggb.z;
                    greenSquareSum += rggb.y * rggb.y + rggb.z * rggb.z;
                    if (x == 0 && y == 0) centerGreen = rgb.y;
                }
            }
            vec3 rgbMean = rgbSum / 9.0;
            vec3 rgbVariance = max(vec3(0.0), rgbSquareSum / 9.0 - rgbMean * rgbMean);
            float greenMean = greenSum / 18.0;
            float greenVariance = max(
                0.0,
                greenSquareSum / 18.0 - greenMean * greenMean
            );
            float averageLuma = dot(averageRgb, vec3(0.25, 0.5, 0.25));
            vec2 noiseUv = vec2(averageLuma, 1.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            float greenNoise = 2.0 * texture(uNoiseEstimates, noiseUv).y;

            vec3 referenceColor;
            float referenceVariance;
            if (greenVariance > 3.0 * greenNoise && uForceReferenceColorRgb.x == 0.0) {
                referenceColor = vec3(averageRgb.x, centerGreen, averageRgb.z);
                referenceVariance = -max(rgbVariance.y, greenVariance);
            } else {
                referenceColor = averageRgb;
                referenceVariance = dot(rgbVariance, vec3(1.0 / 3.0));
            }
            if (centerGreen >= uGreenClippingPoint) referenceColor = vec3(10000.0);
            oGuide = vec4(referenceColor, referenceVariance * 1024.0);

            vec3 covariance = constructCovariance(
                structureTensor(green0, green1),
                greenVariance,
                greenNoise
            );
            vec2 packedRg = clamp(
                covariance.xy * uCovRangeRgFactors.yw + uCovRangeRgFactors.xz,
                0.0,
                1.0
            );
            float packedB = clamp(
                covariance.z * uCovRangeBFactor.y + uCovRangeBFactor.x,
                0.0,
                1.0
            );
            oCovariance = vec4(packedRg, packedB, 0.0);
        }
    """.trimIndent()

    val rejection = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBaseGuide;
        uniform sampler2D uAltGuide;
        uniform sampler2D uFlow;
        uniform sampler2D uUnblocker;
        uniform sampler2D uNoiseEstimates;
        uniform ivec2 uGuideSize;
        uniform ivec2 uRejectionSize;
        uniform vec4 uFrameBorderPadded;
        uniform vec4 uFlowScaleOffset;
        uniform vec2 uUnblockerScale;
        uniform vec4 uNoiseTextureScaleBias;
        uniform vec2 uColorDifferenceMultiplier;
        uniform float uUnblockerReductionThreshold;
        uniform float uExtraMotionRobustnessBoost;
        uniform float uMotionRobustnessBoostVarianceThreshold;
        uniform float uExtraMotionRobustnessMotionThreshold;
        layout(location = 0) out float oReverseWeight;
        layout(location = 1) out float oPixelDifference;

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

        vec4 sampleBiquadraticAbsolute(sampler2D image, vec2 uv) {
            vec2 fractionalOffset = fract(uv * vec2(uGuideSize));
            vec2 c = fractionalOffset * fractionalOffset - fractionalOffset + 0.5;
            vec2 reciprocalSize = 1.0 / vec2(uGuideSize);
            vec2 w0 = uv - c * reciprocalSize;
            vec2 w1 = uv + c * reciprocalSize;
            return 0.25 * (
                abs(texture(image, vec2(w0.x, w0.y))) +
                abs(texture(image, vec2(w0.x, w1.y))) +
                abs(texture(image, vec2(w1.x, w1.y))) +
                abs(texture(image, vec2(w1.x, w0.y)))
            );
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uRejectionSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 warpedUv = mirrorUvs(referenceUv + flow.xy);
            float unblocker = texture(uUnblocker, referenceUv * uUnblockerScale).r;
            float localFlowVariation = flow.z;
            if (localFlowVariation < uUnblockerReductionThreshold) {
                unblocker = 0.0;
            }
            bool motionPrior =
                localFlowVariation > uExtraMotionRobustnessMotionThreshold;

            vec4 reference = texture(uBaseGuide, referenceUv);
            bool greenOnly = reference.w < 0.0;
            reference.w = abs(reference.w) / 1024.0;
            vec4 current = sampleBiquadraticAbsolute(uAltGuide, warpedUv);
            current.w /= 1024.0;
            float referenceLuma = greenOnly
                ? reference.y
                : dot(reference.rgb, vec3(1.0 / 3.0));
            vec2 referenceNoiseUv =
                vec2(referenceLuma, 0.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            vec2 currentNoiseUv =
                vec2(referenceLuma, 1.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            vec3 referenceNoise = texture(uNoiseEstimates, referenceNoiseUv).xyz;
            vec3 currentNoise = texture(uNoiseEstimates, currentNoiseUv).xyz;
            float filterVarianceScale = greenOnly ? 0.25 : 0.0976597;
            referenceNoise *= filterVarianceScale;
            currentNoise *= filterVarianceScale;
            reference.w *= filterVarianceScale;
            current.w *= filterVarianceScale;
            float pixelVariance = min(reference.w, current.w);
            float minimumVariance = greenOnly
                ? referenceNoise.y
                : dot(referenceNoise, vec3(1.0 / 3.0));
            float robustnessBoost = 1.0;
            if (reference.w >
                    uMotionRobustnessBoostVarianceThreshold * minimumVariance &&
                motionPrior) {
                robustnessBoost = uExtraMotionRobustnessBoost;
            }
            pixelVariance *= 2.0;
            vec3 combinedNoise = referenceNoise + currentNoise;
            vec3 difference = current.rgb - reference.rgb;
            vec3 differenceSquared = max(
                difference * difference - combinedNoise,
                vec3(0.0)
            );
            vec3 variance = max(vec3(pixelVariance), combinedNoise);
            vec3 pixelDistanceSquared = differenceSquared / combinedNoise;
            differenceSquared /= variance;
            float distance = greenOnly
                ? uColorDifferenceMultiplier.y * differenceSquared.y
                : uColorDifferenceMultiplier.x *
                    dot(differenceSquared, vec3(1.0 / 3.0));
            float pixelDistance = greenOnly
                ? uColorDifferenceMultiplier.y * pixelDistanceSquared.y
                : uColorDifferenceMultiplier.x *
                    dot(pixelDistanceSquared, vec3(1.0 / 3.0));
            float pixelDifference = exp2(min(-pixelDistance, 0.0));
            distance *= robustnessBoost;
            float frameWeight = exp2(min(-distance, 0.0));
            float weight = min(1.0 - unblocker, frameWeight);
            oReverseWeight = 1.0 - weight;
            oPixelDifference = pixelDifference;
        }
    """.trimIndent()


    /* IRIS_26592_TRUST_GATED_RADIOMETRIC_SHORT_HANDOFF
     * Separate two concepts that 26590/26591 incorrectly conflated: Sabre evidence decides only
     * whether aligned SHORT is trustworthy, while NORMAL sensor saturation decides how much SHORT
     * should replace NORMAL. Below 0.90 second-highest CFA signal the output is exact NORMAL; from
     * 0.90 to 0.98 it transitions monotonically; at >=0.98 a trusted SHORT is 100% authoritative.
     * This prevents clipped NORMAL from contaminating a valid SHORT merely because alignment trust
     * was fractional. Existing flow/covariance/rejection/coverage/unblocker/radiometric gates stay
     * fail-closed and there is still no second correspondence search or per-channel substitution.
     */
    val shortRestoreMask26587 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform sampler2D uFlow;
        uniform sampler2D uShortWeight;
        uniform sampler2D uNormalCoverage;
        uniform sampler2D uUnblocker;
        uniform ivec2 uRawSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uReferenceNearClipThreshold;
        uniform float uShortHeadroomThreshold;
        uniform float uNormalCoverageThreshold;
        uniform float uFlowVariationThreshold;
        uniform float uShortWeightThreshold;
        uniform float uUnblockerThreshold;
        uniform float uConsistencyThreshold;
        layout(location = 0) out float oMask;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        float rawAt(highp usampler2D t, ivec2 p) { return float(texelFetch(t, clampRaw(p), 0).r); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float normalizedRaw(float raw, float black) {
            return max(raw - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        int sensorClippedQuad(highp usampler2D t, ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float clipCode = uWhiteLevel - 0.5;
            int count = 0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x)
                count += rawAt(t, q + ivec2(x, y)) >= clipCode ? 1 : 0;
            return count;
        }
        float referenceSecondHighestSignal(ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float first = 0.0;
            float second = 0.0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                ivec2 s = q + ivec2(x, y);
                float signal = normalizedRaw(
                    rawAt(uReferenceRaw, s),
                    blackAt(uReferenceBlackByPhase, phaseAt(s))
                );
                if (signal >= first) { second = first; first = signal; }
                else if (signal > second) { second = signal; }
            }
            return second;
        }
        bool shortNeighborhoodHasHeadroom(ivec2 p) {
            for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                ivec2 s = clampRaw(p + ivec2(x, y));
                float signal = normalizedRaw(
                    rawAt(uShortRaw, s),
                    blackAt(uShortBlackByPhase, phaseAt(s))
                );
                if (signal >= uShortHeadroomThreshold) return false;
            }
            return true;
        }
        float quadMean(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float sum = 0.0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                ivec2 s = q + ivec2(x, y);
                sum += normalizedRaw(rawAt(t, s), blackAt(blackByPhase, phaseAt(s)));
            }
            return 0.25 * sum;
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uRawSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 shortUv = clamp(referenceUv + flow.xy, vec2(0.0), vec2(1.0));
            ivec2 referenceP = ivec2(gl_FragCoord.xy);
            ivec2 shortP = clampRaw(ivec2(floor(shortUv * vec2(uRawSize))));

            const float handoffStart = 0.90;
            const float trustGate = 0.60;
            float referenceSecond = referenceSecondHighestSignal(referenceP);
            if (referenceSecond < handoffStart || !shortNeighborhoodHasHeadroom(shortP)) {
                oMask = 0.0; return;
            }
            float shortWeight = texture(uShortWeight, referenceUv).r;
            float coverage = texture(uNormalCoverage, referenceUv).r;
            float unblocker = texture(uUnblocker, referenceUv).r;
            if (shortWeight < uShortWeightThreshold || coverage < uNormalCoverageThreshold ||
                flow.z > uFlowVariationThreshold || unblocker > uUnblockerThreshold) {
                oMask = 0.0; return;
            }

            float errorSum = 0.0;
            int evidence = 0;
            ivec2 referenceQuad = (referenceP / 2) * 2;
            ivec2 shortQuad = (shortP / 2) * 2;
            for (int qy = -1; qy <= 1; ++qy) {
                for (int qx = -1; qx <= 1; ++qx) {
                    ivec2 rp = referenceQuad + ivec2(qx * 2, qy * 2);
                    ivec2 sp = shortQuad + ivec2(qx * 2, qy * 2);
                    if (sensorClippedQuad(uReferenceRaw, rp) != 0 || sensorClippedQuad(uShortRaw, sp) != 0) continue;
                    float nr = quadMean(uReferenceRaw, rp, uReferenceBlackByPhase);
                    float ns = quadMean(uShortRaw, sp, uShortBlackByPhase) * uExposureRatio;
                    if (nr < 0.025 || ns < 0.025) continue;
                    errorSum += abs(ns - nr) / max(max(nr, ns), 0.05);
                    evidence += 1;
                }
            }
            if (evidence < 3) { oMask = 0.0; return; }
            float meanError = errorSum / float(evidence);
            if (meanError >= uConsistencyThreshold) { oMask = 0.0; return; }

            float weightConfidence = smoothstep(uShortWeightThreshold, 0.95, shortWeight);
            float supportConfidence = smoothstep(uNormalCoverageThreshold, min(1.0, uNormalCoverageThreshold + 0.20), coverage);
            float flowConfidence = 1.0 - smoothstep(0.5 * uFlowVariationThreshold, uFlowVariationThreshold, flow.z);
            float unblockerConfidence = 1.0 - smoothstep(0.25 * uUnblockerThreshold, uUnblockerThreshold, unblocker);
            float consistencyConfidence = 1.0 - smoothstep(0.5 * uConsistencyThreshold, uConsistencyThreshold, meanError);
            float trustConfidence = clamp(min(weightConfidence, min(supportConfidence, min(flowConfidence,
                min(unblockerConfidence, consistencyConfidence)))), 0.0, 1.0);
            if (trustConfidence < trustGate) { oMask = 0.0; return; }

            /* Trust is a gate, never blend opacity. Sensor reliability alone owns the handoff. */
            oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);
        }
    """.trimIndent()

    /* IRIS_26590_SHORT_MASK_EFFECT_PROBE
     * Read-only sparse diagnostic. Downsample the already-finalized native-resolution mask to a
     * tiny probe texture so device logs can distinguish an empty mask from real SHORT admission
     * without a full-frame CPU readback. This shader never feeds reconstruction or rendering.
     */
    val shortRestoreMaskProbe26590 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uMask;
        uniform ivec2 uProbeSize;
        layout(location = 0) out float oMask;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(uProbeSize);
            oMask = texture(uMask, uv).r;
        }
    """.trimIndent()

    /* IRIS_26592_RGBA16F_WHOLE_RGB_RADIOMETRIC_SHORT_HANDOFF
     * SHORT remains native-exposure through reconstruction/VGN. The exposure ratio is applied only
     * here, in RGBA16F. uMask is now the sensor-saturation handoff weight produced only after all
     * Sabre trust gates pass: exact NORMAL below the handoff, exact SHORT at >=0.98, one RGB scalar
     * throughout the transition. Alpha stays NORMAL-owned.
     */
    val shortRestoreRgba16f26587 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uNormalRgb;
        uniform sampler2D uShortRgb;
        uniform sampler2D uMask;
        uniform float uExposureRatio;
        layout(location = 0) out vec4 oColor;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(textureSize(uNormalRgb, 0));
            vec4 normalRgb = texture(uNormalRgb, uv);
            vec3 restoredShort = texture(uShortRgb, uv).rgb * uExposureRatio;
            float confidence = clamp(texture(uMask, uv).r, 0.0, 1.0);
            oColor = vec4(mix(normalRgb.rgb, restoredShort, confidence), normalRgb.a);
        }
    """.trimIndent()

    val merge = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uCovariance;
        uniform sampler2D uRejection;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uExtractedSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec2 oWeightsGb;

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

        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float kernelDistance =
                pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
            return exp2(-0.5 * kernelDistance) + 0.00005;
        }

        vec3 unpackCovariance(vec3 packed) {
            return vec3(
                packed.x * uCovRangeRg.y + uCovRangeRg.x,
                packed.y * uCovRangeRg.w + uCovRangeRg.z,
                packed.z * uCovRangeB.y + uCovRangeB.x
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

        void sampleNeighborhoodRbf(
            vec2 sampleUv,
            vec3 covariance,
            out vec3 accumulatedIntensities,
            out vec3 accumulatedWeights
        ) {
            accumulatedIntensities = vec3(0.0);
            accumulatedWeights = vec3(0.0);
            vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
            ivec2 position = ivec2(coordinateScaled);
            mat3 bayerValue = get3x3FromExtractedBayer(position);
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
            intensities = swizzleForType(intensities, type);
            reorderedWeights = swizzleForType(reorderedWeights, type);
            accumulatedIntensities = vec3(
                intensities.r,
                intensities.g + intensities.b,
                intensities.a
            );
            accumulatedWeights = vec3(
                reorderedWeights.r,
                reorderedWeights.g + reorderedWeights.b,
                reorderedWeights.a
            );
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
            vec2 flowUv =
                referenceUv * uFlowScaleOffset.xy +
                uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 sampleUv = mirrorUvs(referenceUv + flow.xy);
            vec3 covariance = unpackCovariance(texture(uCovariance, sampleUv).xyz);
            vec3 accumulatedColor = vec3(0.0);
            vec3 accumulatedWeight = vec3(0.0);
            sampleNeighborhoodRbf(
                sampleUv,
                covariance,
                accumulatedColor,
                accumulatedWeight
            );
            float frameWeight = uUseFrameWeight != 0
                ? texture(uRejection, referenceUv).r
                : 1.0;
            accumulatedColor *= frameWeight;
            accumulatedWeight *= frameWeight;
            oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);
            oWeightsGb = accumulatedWeight.gb;
        }
    """.trimIndent()

    /* IRIS_26558_SABRE_SHADOW_LONG_SOURCE_CLIP_GUARD
     * Night-only Sabre merge. The proven Motion/NORMAL merge shader above remains byte-for-byte
     * unchanged. For SHADOW_LONG only, reject the whole Long observation at an output pixel if
     * any of the exact 3x3 unnormalized source-CFA samples consumed by Sabre has reached sensor
     * saturation. This prevents exposure normalization from making lost/clipped channel evidence
     * look valid and preserves SHORT as highlight authority.
     */
    val mergeShadowLong26558 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uCovariance;
        uniform sampler2D uRejection;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uExtractedSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform float uSourceClippingPoint;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec2 oWeightsGb;

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

        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float kernelDistance =
                pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
            return exp2(-0.5 * kernelDistance) + 0.00005;
        }

        vec3 unpackCovariance(vec3 packed) {
            return vec3(
                packed.x * uCovRangeRg.y + uCovRangeRg.x,
                packed.y * uCovRangeRg.w + uCovRangeRg.z,
                packed.z * uCovRangeB.y + uCovRangeB.x
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

        void sampleNeighborhoodRbf(
            vec2 sampleUv,
            vec3 covariance,
            out vec3 accumulatedIntensities,
            out vec3 accumulatedWeights,
            out float sourceNeighborhoodClipped
        ) {
            accumulatedIntensities = vec3(0.0);
            accumulatedWeights = vec3(0.0);
            sourceNeighborhoodClipped = 0.0;
            vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
            ivec2 position = ivec2(coordinateScaled);
            mat3 bayerValue = get3x3FromExtractedBayer(position);
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) {
                    sourceNeighborhoodClipped = max(
                        sourceNeighborhoodClipped,
                        step(uSourceClippingPoint, bayerValue[sx][sy])
                    );
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
            intensities = swizzleForType(intensities, type);
            reorderedWeights = swizzleForType(reorderedWeights, type);
            accumulatedIntensities = vec3(
                intensities.r,
                intensities.g + intensities.b,
                intensities.a
            );
            accumulatedWeights = vec3(
                reorderedWeights.r,
                reorderedWeights.g + reorderedWeights.b,
                reorderedWeights.a
            );
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
            vec2 flowUv =
                referenceUv * uFlowScaleOffset.xy +
                uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 sampleUv = mirrorUvs(referenceUv + flow.xy);
            vec3 covariance = unpackCovariance(texture(uCovariance, sampleUv).xyz);
            vec3 accumulatedColor = vec3(0.0);
            vec3 accumulatedWeight = vec3(0.0);
            float sourceNeighborhoodClipped = 0.0;
            sampleNeighborhoodRbf(
                sampleUv,
                covariance,
                accumulatedColor,
                accumulatedWeight,
                sourceNeighborhoodClipped
            );
            float frameWeight = uUseFrameWeight != 0
                ? texture(uRejection, referenceUv).r
                : 1.0;
            if (sourceNeighborhoodClipped > 0.5) {
                frameWeight = 0.0;
            }
            accumulatedColor *= frameWeight;
            accumulatedWeight *= frameWeight;
            oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);
            oWeightsGb = accumulatedWeight.gb;
        }
    """.trimIndent()

    /* IRIS_26561_SABRE_NATIVE_2X_DETAIL
     * Iris Super Res extension after the current-MGC Sabre alignment/rejection contract.
     * The 1x Sabre merge/Resolve/VGN sources above remain unchanged. This shader reuses the
     * same sparse flow, covariance RBF and rejection decision at a 2x sample grid, but stores
     * only weighted luma + accepted-frame support. It is therefore not a second color owner.
     */
    val superResDetailMerge26561 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uCovariance;
        uniform sampler2D uRejection;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uExtractedSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        layout(location = 0) out vec2 oLumaAndSupport;

        vec2 mirrorUvs(vec2 sampleUv) {
            if (sampleUv.x <= uFrameBorderPadded.x)
                sampleUv.x = 2.0 * uFrameBorderPadded.x - sampleUv.x;
            if (sampleUv.y <= uFrameBorderPadded.y)
                sampleUv.y = 2.0 * uFrameBorderPadded.y - sampleUv.y;
            if (sampleUv.x > uFrameBorderPadded.z)
                sampleUv.x = 2.0 * uFrameBorderPadded.z - sampleUv.x;
            if (sampleUv.y > uFrameBorderPadded.w)
                sampleUv.y = 2.0 * uFrameBorderPadded.w - sampleUv.y;
            return sampleUv;
        }

        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float kernelDistance =
                pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
            return exp2(-0.5 * kernelDistance) + 0.00005;
        }

        vec3 unpackCovariance(vec3 packed) {
            return vec3(
                packed.x * uCovRangeRg.y + uCovRangeRg.x,
                packed.y * uCovRangeRg.w + uCovRangeRg.z,
                packed.z * uCovRangeB.y + uCovRangeB.x
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
            vec4 bayer1 = texture(uExtractedBayer, (texturePosition + vec2(1.0, 0.0)) * reciprocalSize);
            vec4 bayer2 = texture(uExtractedBayer, (texturePosition + vec2(0.0, 1.0)) * reciprocalSize);
            vec4 bayer3 = texture(uExtractedBayer, (texturePosition + vec2(1.0, 1.0)) * reciprocalSize);
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

        void sampleNeighborhoodRbf(
            vec2 sampleUv,
            vec3 covariance,
            out vec3 accumulatedIntensities,
            out vec3 accumulatedWeights
        ) {
            accumulatedIntensities = vec3(0.0);
            accumulatedWeights = vec3(0.0);
            vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
            ivec2 position = ivec2(coordinateScaled);
            mat3 bayerValue = get3x3FromExtractedBayer(position);
            mat3 weights = mat3(0.0);
            vec2 subpixelOffset = floor(coordinateScaled) + 0.5 - coordinateScaled;
            for (int i = -1; i <= 1; ++i) {
                for (int j = -1; j <= 1; ++j) {
                    weights[i + 1][j + 1] = kernelWeight(subpixelOffset + vec2(ivec2(i, j)), covariance);
                }
            }
            ivec2 bayerOffset = ivec2(0);
            if (uCfaPattern == 0) bayerOffset = ivec2(1, 1);
            else if (uCfaPattern == 1) bayerOffset = ivec2(0, 1);
            else if (uCfaPattern == 2) bayerOffset = ivec2(1, 0);
            int type = (((position.y + bayerOffset.y) & 1) << 1) + ((position.x + bayerOffset.x) & 1);
            vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);
            vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);
            vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);
            vec4 value1 = vec4(bayerValue[0][0], bayerValue[0][2], bayerValue[2][0], bayerValue[2][2]);
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
            intensities = swizzleForType(intensities, type);
            reorderedWeights = swizzleForType(reorderedWeights, type);
            accumulatedIntensities = vec3(intensities.r, intensities.g + intensities.b, intensities.a);
            accumulatedWeights = vec3(reorderedWeights.r, reorderedWeights.g + reorderedWeights.b, reorderedWeights.a);
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec2 flow = texture(uFlow, flowUv).xy;
            vec2 sampleUv = mirrorUvs(referenceUv + flow);
            vec3 covariance = unpackCovariance(texture(uCovariance, sampleUv).xyz);
            vec3 accumulatedColor = vec3(0.0);
            vec3 accumulatedWeight = vec3(0.0);
            sampleNeighborhoodRbf(sampleUv, covariance, accumulatedColor, accumulatedWeight);
            vec3 frameRgb = accumulatedColor / max(accumulatedWeight, vec3(1.0e-6));
            float frameLuma = dot(frameRgb, vec3(0.25, 0.50, 0.25));
            float frameWeight = uUseFrameWeight != 0 ? texture(uRejection, referenceUv).r : 1.0;
            oLumaAndSupport = vec2(frameLuma * frameWeight, frameWeight);
        }
    """.trimIndent()

    /* Convert the 2x luma/support carrier to the existing 26532 Q8 signed-log-detail contract.
     * A reference-only pixel has support 1 and intentionally resolves to neutral detail. Multiple
     * accepted NORMAL observations progressively unlock real subpixel detail. Deep-black signal is
     * also neutral, preventing SR from magnifying unsupported shadow noise.
     */
    val superResDetailResolve26561 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAccumulatedDetail;
        uniform ivec2 uOutputSize;
        uniform int uBandTop;
        uniform float uExpectedNormalFrames;
        layout(location = 0) out float oDetailCode;

        vec2 lumaAndSupportAt(ivec2 p) {
            return texelFetch(uAccumulatedDetail, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rg;
        }

        float resolvedLuma(vec2 packedValue) {
            return packedValue.x / max(packedValue.y, 1.0e-6);
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) + ivec2(0, uBandTop);
            ivec2 blockOrigin = (p / 2) * 2;
            vec2 packed0 = lumaAndSupportAt(blockOrigin);
            vec2 packed1 = lumaAndSupportAt(blockOrigin + ivec2(1, 0));
            vec2 packed2 = lumaAndSupportAt(blockOrigin + ivec2(0, 1));
            vec2 packed3 = lumaAndSupportAt(blockOrigin + ivec2(1, 1));
            float luma0 = resolvedLuma(packed0);
            float luma1 = resolvedLuma(packed1);
            float luma2 = resolvedLuma(packed2);
            float luma3 = resolvedLuma(packed3);
            float blockMean = max((luma0 + luma1 + luma2 + luma3) * 0.25, 1.0e-6);
            float currentLuma = resolvedLuma(lumaAndSupportAt(p));
            float minimumSupport = min(min(packed0.y, packed1.y), min(packed2.y, packed3.y));
            float supportEnd = min(max(uExpectedNormalFrames, 2.0), 3.0);
            float supportGate = smoothstep(1.0, supportEnd, minimumSupport);
            float signalGate = smoothstep(0.002, 0.020, blockMean);
            float logDetail = clamp(log2(max(currentLuma, 1.0e-6) / blockMean), -0.75, 0.75);
            float trustedLogDetail = logDetail * supportGate * signalGate;
            oDetailCode = clamp((trustedLogDetail / 0.75) * 0.5 + 0.5, 0.0, 1.0);
        }
    """.trimIndent()

    /* IRIS_26562_SABRE_SUPER_RES_LINEAR_RAW
     * Build a truthful 3-channel 2x LinearRaw stream from the current native Sabre camera-RGB
     * base plus the exact 26561 NORMAL-only signed-log detail carrier. The base already includes
     * Sabre Resolve black removal and lens shading. Night SHADOW_LONG may influence that native
     * base, but it never enters uAccumulatedDetail. No Spatial/Wronski reconstruction is used.
     */
    val superResLinearRaw26562 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uNativeRgb;
        uniform sampler2D uAccumulatedDetail;
        uniform ivec2 uNativeSize;
        uniform ivec2 uOutputSize;
        uniform int uBandTop;
        uniform float uExpectedNormalFrames;
        layout(location = 0) out highp uvec4 oLinearRaw;

        vec2 lumaAndSupportAt(ivec2 p) {
            return texelFetch(uAccumulatedDetail, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rg;
        }

        float resolvedLuma(vec2 packedValue) {
            return packedValue.x / max(packedValue.y, 1.0e-6);
        }

        vec3 nativeRgbTexel(ivec2 p) {
            uvec3 encoded = texelFetch(uNativeRgb, clamp(p, ivec2(0), uNativeSize - ivec2(1)), 0).rgb;
            return vec3(encoded) / 65535.0;
        }

        vec3 nativeRgbAt(vec2 sourceCoordinate) {
            ivec2 p0 = ivec2(floor(sourceCoordinate));
            vec2 fraction = fract(sourceCoordinate);
            vec3 row0 = mix(nativeRgbTexel(p0), nativeRgbTexel(p0 + ivec2(1, 0)), fraction.x);
            vec3 row1 = mix(nativeRgbTexel(p0 + ivec2(0, 1)), nativeRgbTexel(p0 + ivec2(1, 1)), fraction.x);
            return mix(row0, row1, fraction.y);
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) + ivec2(0, uBandTop);
            ivec2 blockOrigin = (p / 2) * 2;
            vec2 packed0 = lumaAndSupportAt(blockOrigin);
            vec2 packed1 = lumaAndSupportAt(blockOrigin + ivec2(1, 0));
            vec2 packed2 = lumaAndSupportAt(blockOrigin + ivec2(0, 1));
            vec2 packed3 = lumaAndSupportAt(blockOrigin + ivec2(1, 1));
            float luma0 = resolvedLuma(packed0);
            float luma1 = resolvedLuma(packed1);
            float luma2 = resolvedLuma(packed2);
            float luma3 = resolvedLuma(packed3);
            float blockMean = max((luma0 + luma1 + luma2 + luma3) * 0.25, 1.0e-6);
            float currentLuma = resolvedLuma(lumaAndSupportAt(p));
            float minimumSupport = min(min(packed0.y, packed1.y), min(packed2.y, packed3.y));
            float supportEnd = min(max(uExpectedNormalFrames, 2.0), 3.0);
            float supportGate = smoothstep(1.0, supportEnd, minimumSupport);
            float signalGate = smoothstep(0.002, 0.020, blockMean);
            float logDetail = clamp(log2(max(currentLuma, 1.0e-6) / blockMean), -0.75, 0.75);
            float trustedLogDetail = logDetail * supportGate * signalGate;
            float detailFactor = exp2(trustedLogDetail);
            vec2 sourceCoordinate = (vec2(p) + vec2(0.5)) * 0.5 - vec2(0.5);
            vec3 linearRgb = clamp(nativeRgbAt(sourceCoordinate) * detailFactor, 0.0, 1.0);
            oLinearRaw = uvec4(uvec3(round(linearRgb * 65535.0)), 65535u);
        }
    """.trimIndent()

    /**
     * IRIS_26545_SABRE_SPARSE_FLOW_CONTRACT
     * Sabre-only reproduction of MGC ConvertAlignmentHalide. Keep the LK grid sparse; each
     * consumer interpolates it with an explicit reference-UV scale/offset instead of first
     * materializing a dense flow image.
     */
    val convertAlignmentSparse = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAlignment;
        uniform ivec2 uGridSize;
        uniform float uAlignmentScale;
        uniform vec2 uFlowNormalizationSize;
        out vec4 oFlow;
        vec2 flowAt(ivec2 p) {
            return texelFetch(
                uAlignment,
                clamp(p, ivec2(0), uGridSize - ivec2(1)),
                0
            ).xy * uAlignmentScale;
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            vec2 flowPixels = flowAt(tile);
            vec2 minimumFlow = vec2(1.0e20);
            vec2 maximumFlow = vec2(-1.0e20);
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    vec2 v = flowAt(tile + ivec2(x, y));
                    minimumFlow = min(minimumFlow, v);
                    maximumFlow = max(maximumFlow, v);
                }
            }
            vec2 uvFlow = flowPixels / uFlowNormalizationSize;
            vec2 normalizedRange =
                (maximumFlow - minimumFlow) /
                max(uFlowNormalizationSize, vec2(1.0));
            float localFlowVariation = length(normalizedRange);
            oFlow = vec4(uvFlow, localFlowVariation, 0.0);
        }
    """.trimIndent()

    /* IRIS_26574_TRUE2X_LOCAL_FLOW_REFINEMENT
     * SR-only one-step inverse-compositional LK refinement. The proven Sabre sparse flow remains
     * immutable and is the fallback. This shader only runs for frames already retained by the
     * unchanged 26568 top-two-per-phase JPEG reservoir. It works on Bayer-quad luma so subpixel
     * residual estimation never interpolates different CFA colours. Accepted delta is bounded to
     * +/-0.25 Bayer quad (= +/-0.5 RAW pixel) per axis.
     */
    val true2xFlowRefine26574 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uCurrentRaw;
        uniform sampler2D uSparseFlow;
        uniform ivec2 uRawSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uSparseFlowScaleOffset;
        uniform vec4 uReferencePhaseGains;
        uniform vec4 uReferencePhaseBlackTerms;
        uniform vec4 uCurrentPhaseGains;
        uniform vec4 uCurrentPhaseBlackTerms;
        out vec4 oFlow;

        float phaseValue(highp usampler2D rawTex, ivec2 rawP, vec4 gains, vec4 blackTerms) {
            rawP=clamp(rawP,ivec2(0),uRawSize-ivec2(1));
            int phase=((rawP.y&1)<<1)+(rawP.x&1);
            return max(float(texelFetch(rawTex,rawP,0).r)*gains[phase]+blackTerms[phase],0.0);
        }
        float quadValue(highp usampler2D rawTex, ivec2 q, vec4 gains, vec4 blackTerms) {
            ivec2 maxQ=max((uRawSize-ivec2(1))/2,ivec2(0));
            q=clamp(q,ivec2(0),maxQ);
            ivec2 p=q*2;
            return 0.25*(phaseValue(rawTex,p,gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(1,0),gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(0,1),gains,blackTerms)+
                phaseValue(rawTex,p+ivec2(1,1),gains,blackTerms));
        }
        float currentAt(vec2 q) {
            ivec2 q0=ivec2(floor(q));
            vec2 f=fract(q);
            float a=mix(quadValue(uCurrentRaw,q0,uCurrentPhaseGains,uCurrentPhaseBlackTerms),
                quadValue(uCurrentRaw,q0+ivec2(1,0),uCurrentPhaseGains,uCurrentPhaseBlackTerms),f.x);
            float b=mix(quadValue(uCurrentRaw,q0+ivec2(0,1),uCurrentPhaseGains,uCurrentPhaseBlackTerms),
                quadValue(uCurrentRaw,q0+ivec2(1,1),uCurrentPhaseGains,uCurrentPhaseBlackTerms),f.x);
            return mix(a,b,f.y);
        }
        vec4 sparseFlowAt(vec2 referenceUv) {
            vec2 uv=referenceUv*uSparseFlowScaleOffset.xy+uSparseFlowScaleOffset.zw;
            ivec2 size=textureSize(uSparseFlow,0);
            vec2 c=clamp(uv*vec2(size)-vec2(0.5),vec2(0.0),vec2(size-ivec2(1)));
            ivec2 p0=ivec2(floor(c));
            ivec2 p1=min(p0+ivec2(1),size-ivec2(1));
            vec2 f=fract(c);
            vec4 v00=texelFetch(uSparseFlow,p0,0);
            vec4 v10=texelFetch(uSparseFlow,ivec2(p1.x,p0.y),0);
            vec4 v01=texelFetch(uSparseFlow,ivec2(p0.x,p1.y),0);
            vec4 v11=texelFetch(uSparseFlow,p1,0);
            ivec2 nearest=ivec2(floor(c+vec2(0.5)));
            vec4 base=texelFetch(uSparseFlow,clamp(nearest,ivec2(0),size-ivec2(1)),0);
            vec2 rawSize=vec2(uRawSize);
            float maximumDifference=0.0;
            maximumDifference=max(maximumDifference,max(abs((v00.x-base.x)*rawSize.x),abs((v00.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v10.x-base.x)*rawSize.x),abs((v10.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v01.x-base.x)*rawSize.x),abs((v01.y-base.y)*rawSize.y)));
            maximumDifference=max(maximumDifference,max(abs((v11.x-base.x)*rawSize.x),abs((v11.y-base.y)*rawSize.y)));
            if(maximumDifference>=1.0)return vec4(base.xy,max(base.z,maximumDifference/max(rawSize.x,rawSize.y)),0.0);
            vec4 a=mix(v00,v10,f.x),b=mix(v01,v11,f.x);
            vec4 linear=mix(a,b,f.y);
            linear.z=max(linear.z,maximumDifference/max(rawSize.x,rawSize.y));
            return linear;
        }
        float referenceAt(ivec2 q){return quadValue(uReferenceRaw,q,uReferencePhaseGains,uReferencePhaseBlackTerms);}
        float residualCost(ivec2 centerQ,vec2 currentCenterQ){
            const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
            float cost=0.0;
            for(int i=0;i<5;++i){float r=currentAt(currentCenterQ+vec2(d[i]))-referenceAt(centerQ+d[i]);cost+=r*r;}
            return cost;
        }
        void main(){
            vec2 referenceUv=gl_FragCoord.xy/vec2(uOutputSize);
            vec4 base=sparseFlowAt(referenceUv);
            vec2 rawFlow=base.xy*vec2(uRawSize);
            vec2 quadFlow=rawFlow*0.5;
            ivec2 centerQ=ivec2(floor(referenceUv*vec2(uRawSize)*0.5));
            const ivec2 d[5]=ivec2[5](ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1));
            float hxx=0.0,hxy=0.0,hyy=0.0,bx=0.0,by=0.0,baseCost=0.0;
            for(int i=0;i<5;++i){
                ivec2 q=centerQ+d[i];
                float ref=referenceAt(q);
                float gx=0.5*(referenceAt(q+ivec2(1,0))-referenceAt(q-ivec2(1,0)));
                float gy=0.5*(referenceAt(q+ivec2(0,1))-referenceAt(q-ivec2(0,1)));
                float residual=currentAt(vec2(q)+quadFlow)-ref;
                hxx+=gx*gx;hxy+=gx*gy;hyy+=gy*gy;bx+=gx*residual;by+=gy*residual;baseCost+=residual*residual;
            }
            float trace=hxx+hyy;
            float determinant=hxx*hyy-hxy*hxy;
            float conditioning=determinant/max(trace*trace,1.0e-12);
            vec2 delta=vec2(0.0);
            if(determinant>1.0e-10)delta=-vec2(hyy*bx-hxy*by,-hxy*bx+hxx*by)/determinant;
            bool bounded=all(lessThanEqual(abs(delta),vec2(0.25)));
            float newCost=baseCost;
            float oppositeCost=baseCost;
            if(bounded&&conditioning>0.012&&baseCost>1.0e-10){
                newCost=residualCost(centerQ,vec2(centerQ)+quadFlow+delta);
                oppositeCost=residualCost(centerQ,vec2(centerQ)+quadFlow-delta);
            }
            float improvement=(baseCost-newCost)/max(baseCost,1.0e-10);
            float uniqueness=(oppositeCost-newCost)/max(baseCost,1.0e-10);
            float variationRaw=base.z*length(vec2(uRawSize));
            bool accept=bounded&&conditioning>0.012&&improvement>0.08&&uniqueness>0.04&&variationRaw<2.0;
            vec2 refinedRaw=rawFlow+(accept?delta*2.0:vec2(0.0));
            oFlow=vec4(refinedRaw/vec2(uRawSize),base.z,accept?1.0:0.0);
        }
    """.trimIndent()

    /**
     * IRIS_26545_SABRE_NORMALIZED16_DNG
     * RAW-only companion to Sabre merge. It consumes the exact Sabre sparse flow, covariance
     * and temporal rejection, but accumulates only the reference-CFA color in black-subtracted
     * normalized sensor units. No ResolveSabre/demosaic, WB, lens shading, denoise, tone or
     * sharpening is present in this sidecar path.
     */
    val normalDngMerge = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform sampler2D uFlow;
        uniform sampler2D uCovariance;
        uniform sampler2D uRejection;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uRawSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform vec4 uPhaseGains;
        uniform vec4 uPhaseBlackTerms;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        layout(location = 0) out vec2 oSignalAndWeight;

        vec2 mirrorUvs(vec2 sampleUv) {
            if (sampleUv.x <= uFrameBorderPadded.x)
                sampleUv.x = 2.0 * uFrameBorderPadded.x - sampleUv.x;
            if (sampleUv.y <= uFrameBorderPadded.y)
                sampleUv.y = 2.0 * uFrameBorderPadded.y - sampleUv.y;
            if (sampleUv.x > uFrameBorderPadded.z)
                sampleUv.x = 2.0 * uFrameBorderPadded.z - sampleUv.x;
            if (sampleUv.y > uFrameBorderPadded.w)
                sampleUv.y = 2.0 * uFrameBorderPadded.w - sampleUv.y;
            return sampleUv;
        }

        int mirrorCoordinate(int coordinate, int extent) {
            if (extent <= 1) return 0;
            if (coordinate < 0) coordinate = -coordinate - 1;
            if (coordinate >= extent) coordinate = 2 * extent - coordinate - 1;
            return clamp(coordinate, 0, extent - 1);
        }

        ivec2 mirrorPixel(ivec2 p) {
            return ivec2(
                mirrorCoordinate(p.x, uRawSize.x),
                mirrorCoordinate(p.y, uRawSize.y)
            );
        }

        int phaseAt(ivec2 p) {
            return ((p.y & 1) << 1) + (p.x & 1);
        }

        int canonicalChannelForPhase(int phase) {
            if (uCfaPattern == 1) {
                if (phase == 0) return 1;
                if (phase == 1) return 0;
                if (phase == 2) return 3;
                return 2;
            }
            if (uCfaPattern == 2) {
                if (phase == 0) return 2;
                if (phase == 1) return 3;
                if (phase == 2) return 0;
                return 1;
            }
            if (uCfaPattern == 3) {
                if (phase == 0) return 3;
                if (phase == 1) return 2;
                if (phase == 2) return 1;
                return 0;
            }
            return phase;
        }

        bool sameCfaColor(int targetCanonical, int sampleCanonical) {
            bool targetGreen = targetCanonical == 1 || targetCanonical == 2;
            bool sampleGreen = sampleCanonical == 1 || sampleCanonical == 2;
            return targetGreen ? sampleGreen : targetCanonical == sampleCanonical;
        }

        float normalizedRaw(ivec2 p) {
            p = mirrorPixel(p);
            int phase = phaseAt(p);
            return float(texelFetch(uRaw, p, 0).r) * uPhaseGains[phase] +
                uPhaseBlackTerms[phase];
        }

        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float kernelDistance =
                pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
            return exp2(-0.5 * kernelDistance) + 0.00005;
        }

        vec3 unpackCovariance(vec3 packed) {
            return vec3(
                packed.x * uCovRangeRg.y + uCovRangeRg.x,
                packed.y * uCovRangeRg.w + uCovRangeRg.z,
                packed.z * uCovRangeB.y + uCovRangeB.x
            );
        }

        void main() {
            ivec2 outputPixel = ivec2(gl_FragCoord.xy);
            vec2 referenceUv = gl_FragCoord.xy / vec2(uRawSize);
            vec2 flowUv =
                referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec2 flow = texture(uFlow, flowUv).xy;
            vec2 sampleUv = mirrorUvs(referenceUv + flow);
            vec3 covariance = unpackCovariance(texture(uCovariance, sampleUv).xyz);
            vec2 sourcePixel = sampleUv * vec2(uRawSize);
            ivec2 anchor = ivec2(floor(sourcePixel));
            vec2 subpixelOffset = vec2(anchor) + vec2(0.5) - sourcePixel;
            int targetCanonical = canonicalChannelForPhase(phaseAt(outputPixel));
            float intensity = 0.0;
            float accumulatedWeight = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    ivec2 samplePixel = anchor + ivec2(x, y);
                    ivec2 mirrored = mirrorPixel(samplePixel);
                    int sampleCanonical = canonicalChannelForPhase(phaseAt(mirrored));
                    if (!sameCfaColor(targetCanonical, sampleCanonical)) continue;
                    float w = kernelWeight(subpixelOffset + vec2(x, y), covariance);
                    intensity += normalizedRaw(samplePixel) * w;
                    accumulatedWeight += w;
                }
            }
            float frameWeight = uUseFrameWeight != 0
                ? texture(uRejection, referenceUv).r
                : 1.0;
            oSignalAndWeight = vec2(
                intensity * frameWeight,
                accumulatedWeight * frameWeight
            );
        }
    """.trimIndent()


    /* IRIS_26558_SABRE_SHADOW_LONG_SOURCE_CLIP_COVERAGE
     * Night-only companion for Sabre accumulated alpha/support. Motion/NORMAL keeps the proven
     * copyMask shader. On the quarter-resolution coverage grid, do not count a SHADOW_LONG
     * observation when its aligned exact Sabre 3x3 source-CFA footprint reaches sensor saturation.
     */
    val copyMaskShadowLong26558 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uRejection;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uFlow;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uExtractedSize;
        uniform vec4 uFrameBorderPadded;
        uniform float uAccumulatedWeightScale;
        uniform float uSourceClippingPoint;
        layout(location = 0) out float oAccumulatedWeight;

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

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(textureSize(uRejection, 0));
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 sampleUv = mirrorUvs(referenceUv + flow.xy);
            vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
            mat3 bayerValue = get3x3FromExtractedBayer(ivec2(coordinateScaled));
            float sourceNeighborhoodClipped = 0.0;
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) {
                    sourceNeighborhoodClipped = max(
                        sourceNeighborhoodClipped,
                        step(uSourceClippingPoint, bayerValue[sx][sy])
                    );
                }
            }
            float validLong = 1.0 - step(0.5, sourceNeighborhoodClipped);
            oAccumulatedWeight =
                texture(uRejection, referenceUv).r * validLong / uAccumulatedWeightScale;
        }
    """.trimIndent()

    val copyMask = """
        #version 300 es
        precision highp float;
        uniform sampler2D uRejection;
        uniform float uAccumulatedWeightScale;
        layout(location = 0) out float oAccumulatedWeight;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(textureSize(uRejection, 0));
            oAccumulatedWeight = texture(uRejection, uv).r / uAccumulatedWeightScale;
        }
    """.trimIndent()

    val copyAlpha = """
        #version 300 es
        precision highp float;
        uniform sampler2D uSource;
        layout(location = 0) out float oWeight;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            oWeight = texelFetch(uSource, p, 0).a;
        }
    """.trimIndent()

    /**
     * IRIS_26545_SABRE_MEASURED_SUPPORT
     * Current Sabre Q8 average-merge-factor diagnostic. Four-by-four reduction keeps readback
     * small while preserving the global mean of 256 / accumulated green weight.
     */
    val reciprocalGreenWeight4x4 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAccumulatedWeightsGb;
        uniform ivec2 uInputSize;
        layout(location = 0) out vec2 oReciprocalSumAndCount;
        void main() {
            ivec2 base = ivec2(gl_FragCoord.xy) * 4;
            float reciprocalSum = 0.0;
            float sampleCount = 0.0;
            for (int y = 0; y < 4; ++y) {
                for (int x = 0; x < 4; ++x) {
                    ivec2 p = base + ivec2(x, y);
                    if (p.x >= uInputSize.x || p.y >= uInputSize.y) {
                        continue;
                    }
                    float weight = texelFetch(uAccumulatedWeightsGb, p, 0).r;
                    float weightQ8 = max(floor(weight * 256.0 + 0.5), 1.0);
                    reciprocalSum += 256.0 / weightQ8;
                    sampleCount += 1.0;
                }
            }
            oReciprocalSumAndCount = vec2(reciprocalSum, sampleCount);
        }
    """.trimIndent()

    val dehomogenize = """
        #version 300 es
        precision highp float;
        uniform sampler2D uSourceWeightR;
        uniform sampler2D uSourceWeightGb;
        uniform sampler2D uSourceAlpha;
        uniform float uAlphaScale;
        uniform float uAlphaBias;
        layout(location = 0) out vec4 oColor;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(textureSize(uSourceWeightR, 0));
            vec3 weights = vec3(
                texture(uSourceWeightR, uv).r,
                texture(uSourceWeightGb, uv).rg
            );
            float targetAlpha = texture(uSourceAlpha, uv).r * uAlphaScale + uAlphaBias;
            oColor = vec4(vec3(1.0) / max(weights, vec3(1.0e-7)), targetAlpha);
        }
    """.trimIndent()


    /* IRIS_26564_TRUE_2X_GPU_ACCELERATOR
     * Tile-local GLES implementation of the same direct-CFA/RBF estimator as IrisTrue2xSrNative.
     * It consumes persisted Sabre evidence; no alignment or manufacturer policy lives here.
     */
    val true2xMerge26564 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRawRegion;
        uniform sampler2D uFlow;
        uniform sampler2D uCovarianceRegion;
        uniform sampler2D uRejectionRegion;
        uniform ivec2 uRawOrigin;
        uniform ivec2 uRawRegionSize;
        uniform ivec2 uRawFullSize;
        uniform ivec2 uCovarianceOrigin;
        uniform ivec2 uCovarianceRegionSize;
        uniform ivec2 uCovarianceFullSize;
        uniform ivec2 uRejectionOrigin;
        uniform ivec2 uRejectionRegionSize;
        uniform ivec2 uRejectionFullSize;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputFullSize;
        uniform vec4 uFlowScaleOffset;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        uniform float uRawClipThreshold;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec2 oWeightsGb;
        layout(location = 2) out vec4 oPhaseOccupancy;
        layout(location = 3) out vec4 oTemporalLumaStats;

        vec2 mirrorUvs(vec2 uv) {
            vec2 border = vec2(1.5) / vec2(uRawFullSize);
            if (uv.x <= border.x) uv.x = 2.0 * border.x - uv.x;
            if (uv.y <= border.y) uv.y = 2.0 * border.y - uv.y;
            if (uv.x > 1.0 - border.x) uv.x = 2.0 * (1.0 - border.x) - uv.x;
            if (uv.y > 1.0 - border.y) uv.y = 2.0 * (1.0 - border.y) - uv.y;
            return clamp(uv, vec2(0.0), vec2(1.0));
        }

        float rawAt(ivec2 globalP) {
            globalP = clamp(globalP, ivec2(0), uRawFullSize - ivec2(1));
            ivec2 localP = clamp(globalP - uRawOrigin, ivec2(0), uRawRegionSize - ivec2(1));
            return float(texelFetch(uRawRegion, localP, 0).r);
        }

        vec3 covarianceAt(ivec2 p) {
            p = clamp(p, ivec2(0), uCovarianceRegionSize - ivec2(1));
            return texelFetch(uCovarianceRegion, p, 0).rgb;
        }

        vec3 sampleCovariancePacked(vec2 uv) {
            vec2 globalCoordinate = clamp(
                uv * vec2(uCovarianceFullSize) - vec2(0.5),
                vec2(0.0), vec2(uCovarianceFullSize - ivec2(1)));
            vec2 localCoordinate = clamp(
                globalCoordinate - vec2(uCovarianceOrigin),
                vec2(0.0), vec2(uCovarianceRegionSize - ivec2(1)));
            ivec2 p0 = ivec2(floor(localCoordinate));
            ivec2 p1 = min(p0 + ivec2(1), uCovarianceRegionSize - ivec2(1));
            vec2 f = fract(localCoordinate);
            vec3 a = mix(covarianceAt(p0), covarianceAt(ivec2(p1.x, p0.y)), f.x);
            vec3 b = mix(covarianceAt(ivec2(p0.x, p1.y)), covarianceAt(p1), f.x);
            return mix(a, b, f.y);
        }

        float rejectionAt(ivec2 p) {
            p = clamp(p, ivec2(0), uRejectionRegionSize - ivec2(1));
            return texelFetch(uRejectionRegion, p, 0).r;
        }

        float sampleRejection(vec2 uv) {
            if (uUseFrameWeight == 0) return 1.0;
            vec2 globalCoordinate = clamp(
                uv * vec2(uRejectionFullSize) - vec2(0.5),
                vec2(0.0), vec2(uRejectionFullSize - ivec2(1)));
            vec2 localCoordinate = clamp(
                globalCoordinate - vec2(uRejectionOrigin),
                vec2(0.0), vec2(uRejectionRegionSize - ivec2(1)));
            ivec2 p0 = ivec2(floor(localCoordinate));
            ivec2 p1 = min(p0 + ivec2(1), uRejectionRegionSize - ivec2(1));
            vec2 f = fract(localCoordinate);
            float a = mix(rejectionAt(p0), rejectionAt(ivec2(p1.x, p0.y)), f.x);
            float b = mix(rejectionAt(ivec2(p0.x, p1.y)), rejectionAt(p1), f.x);
            return mix(a, b, f.y);
        }

        float kernelWeight(vec2 offset, vec3 covariance) {
            float d = offset.x * offset.x * covariance.x +
                offset.y * offset.y * covariance.y +
                offset.x * offset.y * covariance.z * 2.0;
            return exp2(-0.5 * d) + 0.00005;
        }

        vec4 swizzleForType(vec4 value, int type) {
            if (type == 0) return value.rgba;
            if (type == 1) return value.grab;
            if (type == 2) return value.barg;
            return value.abgr;
        }

        void sampleRbf(vec2 sensorCoordinate, vec3 covariance,
                       out vec3 accumulatedColor, out vec3 accumulatedWeight,
                       out float sourceRawPeak) {
            ivec2 position = ivec2(floor(sensorCoordinate));
            mat3 bayerValue = mat3(0.0);
            mat3 weights = mat3(0.0);
            vec2 subpixelOffset = floor(sensorCoordinate) + vec2(0.5) - sensorCoordinate;
            for (int x = -1; x <= 1; ++x) {
                for (int y = -1; y <= 1; ++y) {
                    bayerValue[x + 1][y + 1] = rawAt(position + ivec2(x, y));
                    weights[x + 1][y + 1] = kernelWeight(
                        subpixelOffset + vec2(float(x), float(y)), covariance);
                }
            }
            ivec2 bayerOffset = ivec2(0);
            if (uCfaPattern == 0) bayerOffset = ivec2(1, 1);
            else if (uCfaPattern == 1) bayerOffset = ivec2(0, 1);
            else if (uCfaPattern == 2) bayerOffset = ivec2(1, 0);
            int type = (((position.y + bayerOffset.y) & 1) << 1) +
                ((position.x + bayerOffset.x) & 1);
            sourceRawPeak = 0.0;
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) sourceRawPeak = max(sourceRawPeak, bayerValue[sx][sy]);
            }
            vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);
            vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);
            vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);
            vec4 cornerValues = vec4(bayerValue[0][0], bayerValue[0][2], bayerValue[2][0], bayerValue[2][2]);
            vec2 upDownValues = vec2(bayerValue[1][0], bayerValue[1][2]);
            vec2 leftRightValues = vec2(bayerValue[0][1], bayerValue[2][1]);
            vec4 gains = swizzleForType(uGains, type);
            vec4 black = swizzleForType(uBlackLevelsTimesGains, type);
            vec4 intensity = vec4(
                dot(cornerValues * gains.r + black.r, cornerWeights),
                dot(upDownValues * gains.g + black.g, upDownWeights),
                dot(leftRightValues * gains.b + black.b, leftRightWeights),
                (bayerValue[1][1] * gains.a + black.a) * weights[1][1]);
            vec4 channelWeight = vec4(
                dot(cornerWeights, vec4(1.0)),
                dot(upDownWeights, vec2(1.0)),
                dot(leftRightWeights, vec2(1.0)),
                weights[1][1]);
            intensity = swizzleForType(intensity, type);
            channelWeight = swizzleForType(channelWeight, type);
            accumulatedColor = vec3(intensity.r, intensity.g + intensity.b, intensity.a);
            accumulatedWeight = vec3(channelWeight.r, channelWeight.g + channelWeight.b, channelWeight.a);
        }

        void main() {
            ivec2 globalP = uOutputOrigin + ivec2(gl_FragCoord.xy);
            vec2 referenceUv = (vec2(globalP) + vec2(0.5)) / vec2(uOutputFullSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 sampleUv = mirrorUvs(referenceUv + flow.xy);
            vec3 packedCovariance = sampleCovariancePacked(sampleUv);
            vec3 covariance = vec3(
                packedCovariance.x * uCovRangeRg.y + uCovRangeRg.x,
                packedCovariance.y * uCovRangeRg.w + uCovRangeRg.z,
                packedCovariance.z * uCovRangeB.y + uCovRangeB.x);
            vec3 color;
            vec3 weights;
            float sourceRawPeak;
            sampleRbf(sampleUv * vec2(uRawFullSize), covariance, color, weights, sourceRawPeak);
            float frameWeight = sampleRejection(referenceUv);
            vec3 frameRgb = color / max(weights, vec3(1.0e-7));
            float frameY = clamp(0.25 * frameRgb.r + 0.50 * frameRgb.g + 0.25 * frameRgb.b, 0.0, 4.0);
            float temporalWeight = (frameWeight > 0.08 && sourceRawPeak < uRawClipThreshold) ? frameWeight : 0.0;
            /* IRIS_26573_CROSS_FRAME_LUMA_MOMENTS
             * Weighted first/second luminance moments plus sum(w),sum(w^2).  These are accumulated
             * across independently aligned RAW observations and are used only to prove that a
             * candidate 2x sample is temporally repeatable; they never become an RGB/chroma owner.
             */
            oTemporalLumaStats = vec4(
                frameY * temporalWeight,
                frameY * frameY * temporalWeight,
                temporalWeight,
                temporalWeight * temporalWeight);
            color *= frameWeight;
            weights *= frameWeight;
            oColorAndRWeight = vec4(color, weights.r);
            oWeightsGb = weights.gb;

            oPhaseOccupancy = vec4(0.0);
            if (temporalWeight > 0.0) {
                vec2 flowPixels = flow.xy * vec2(uRawFullSize);
                vec2 phase = fract(flowPixels);
                int bin = (phase.x >= 0.5 ? 1 : 0) + (phase.y >= 0.5 ? 2 : 0);
                if (bin == 0) oPhaseOccupancy.r = 1.0;
                else if (bin == 1) oPhaseOccupancy.g = 1.0;
                else if (bin == 2) oPhaseOccupancy.b = 1.0;
                else oPhaseOccupancy.a = 1.0;
            }
        }
    """.trimIndent()

    val true2xResolve26564 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAccumulatedColor;
        uniform sampler2D uAccumulatedWeightsGb;
        uniform sampler2D uLensShading;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputFullSize;
        uniform vec3 uCameraDomainScale;
        uniform int uUseLensShading;
        layout(location = 0) out vec4 oCameraRgb;
        void main() {
            ivec2 localP = ivec2(gl_FragCoord.xy);
            vec4 colorAndR = texelFetch(uAccumulatedColor, localP, 0);
            vec2 gb = texelFetch(uAccumulatedWeightsGb, localP, 0).rg;
            vec3 rgb = colorAndR.rgb / max(vec3(colorAndR.a, gb), vec3(1.0e-7));
            rgb = max(rgb * uCameraDomainScale, vec3(0.0));
            if (uUseLensShading != 0) {
                ivec2 globalP = uOutputOrigin + localP;
                vec2 uv = (vec2(globalP) + vec2(0.5)) / vec2(uOutputFullSize);
                vec4 shading = texture(uLensShading, uv);
                rgb *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
            }
            // Match native Sabre FLOAT output: reject negative camera values but retain >1.0
            // extended-linear headroom after lens shading/output scaling for highlight rendering.
            oCameraRgb = vec4(max(rgb, vec3(0.0)), 1.0);
        }
    """.trimIndent()

    val true2xGuideRender26568 = """
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
            float confidence = clamp(phaseGate * temporalGate * safetyGate, 0.0, 1.0);

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
            float detailScaleY = mix(guideBlockY, guideY, materialBoundary);
            float targetY = max(guideY + detailScaleY * directDetail * detailConfidence, 0.0);
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
            else if (chromaGate <= 0.001 || agreementGate <= 0.001) reasonClass = 5;
            else if (signalGate <= 0.001) reasonClass = 7;
            else if (confidence >= 0.50) reasonClass = 2;
            else if (confidence > 0.02) reasonClass = 1;
            oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount * 8 + reasonClass));
        }
    """.trimIndent()

    private val outputTransformBody = """
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uResolvedR;
        uniform highp usampler2D uResolvedG;
        uniform highp usampler2D uResolvedB;
        uniform sampler2D uLensShading;
        uniform ivec2 uOutputSize;
        uniform int uUseLensShading;
        uniform vec3 uFinalBlackLevel;
        uniform float uDemosaicWhiteLevel;
        uniform float uOutputExposureScale;

        vec3 transformOutput(ivec2 p) {
            uvec3 encoded = uvec3(
                texelFetch(uResolvedR, p, 0).r,
                texelFetch(uResolvedG, p, 0).r,
                texelFetch(uResolvedB, p, 0).r
            );
            // ResolveSabre emits camera RGB in its RAW14 domain and deliberately retains the
            // per-channel final black level. Convert that native result to the black-free,
            // normalized camera domain expected by Photon's linear-RGB pipeline.
            vec3 resolved = max(vec3(encoded) - uFinalBlackLevel, vec3(0.0)) /
                max(vec3(uDemosaicWhiteLevel) - uFinalBlackLevel, vec3(1.0));
            if (uUseLensShading != 0) {
                vec2 uv = (vec2(p) + vec2(0.5)) / vec2(uOutputSize);
                vec4 shading = texture(uLensShading, uv);
                resolved *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
            }
            return max(
                resolved * uOutputExposureScale,
                vec3(0.0)
            );
        }
    """.trimIndent()

    val outputTransformUint16 = """
        #version 300 es
        $outputTransformBody
        layout(location = 0) out highp uvec4 oResolved;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            vec3 resolved = clamp(transformOutput(p), 0.0, 1.0);
            oResolved = uvec4(uvec3(round(resolved * 65535.0)), 65535u);
        }
    """.trimIndent()

    val outputTransformFloat = """
        #version 300 es
        $outputTransformBody
        layout(location = 0) out vec4 oResolved;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            oResolved = vec4(transformOutput(p), 1.0);
        }
    """.trimIndent()
}
