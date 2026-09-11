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
        /* IRIS_26606_MEASURABLE_NORMAL_REJECTION_OWNER
         * Ordinary Sabre rejection owns only the measurable-reference path. HIGHLIGHT_SHORT
         * clipped-reference rescue is applied later as one scalar frame weight after dilation,
         * so NORMAL-oriented photometric rejection/unblocker/dilation cannot silently veto
         * physically censored reference pixels. NORMAL and Night behavior remain unchanged.
         */
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
        /* IRIS_26610_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_OUTPUT
         * This is not a second approximation of NORMAL protection. It is emitted by the exact
         * ordinary Sabre rejection invocation from the same unblocker/flow decision that caps
         * NORMAL. HIGHLIGHT_SHORT may relax only reference-photometric agreement in a proven
         * censored core; this physical reverse weight remains mandatory. */
        layout(location = 2) out float oPhysicalReverseWeight;

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
            oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);
        }
    """.trimIndent()


    /* IRIS_26606_SHORT_BOUNDARY_ANCHOR
     * HIGHLIGHT_SHORT rescue has two independent geometry proofs. flow.w is the robust local
     * affine residual in RAW pixels; it rejects local discontinuity/bad-center alignment without
     * rejecting coherent rotation/perspective. Boundary radiometry then proves that the coherent
     * warp is absolutely registered where NORMAL is still measurable. The output contains only
     * confidence metadata: z=connected-region eligibility, w=measurable-boundary anchor.
     */
    val shortBoundaryAnchor26606 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform sampler2D uFlow;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uRegionFloor;
        uniform float uBoundaryCeiling;
        uniform float uShortHeadroomThreshold;
        uniform float uConsistencyLow;
        uniform float uConsistencyHigh;
        layout(location = 0) out vec4 oAnchor;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, (phase >> 1) & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float rawAt(highp usampler2D t, ivec2 p) {
            return float(texelFetch(t, clampRaw(p), 0).r);
        }
        float normalizedRaw(float raw, float black) {
            return max(raw - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        float normalizedAt(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = clampRaw(p);
            return normalizedRaw(rawAt(t, q), blackAt(blackByPhase, phaseAt(q)));
        }
        ivec2 phaseGridSize(int phase) {
            ivec2 off = phaseOffset(phase);
            return max((uRawSize - off + ivec2(1)) / 2, ivec2(1));
        }
        ivec2 phaseSamplePixel(int phase, ivec2 gridP) {
            ivec2 off = phaseOffset(phase);
            ivec2 size = phaseGridSize(phase);
            return 2 * clamp(gridP, ivec2(0), size - ivec2(1)) + off;
        }
        vec4 samePhaseSupport(highp usampler2D t, vec2 rawCenter, int phase, vec4 blackByPhase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 g = (rawCenter - origin) * 0.5;
            ivec2 g0 = ivec2(floor(g));
            ivec2 p00 = phaseSamplePixel(phase, g0);
            ivec2 p10 = phaseSamplePixel(phase, g0 + ivec2(1, 0));
            ivec2 p01 = phaseSamplePixel(phase, g0 + ivec2(0, 1));
            ivec2 p11 = phaseSamplePixel(phase, g0 + ivec2(1, 1));
            return vec4(
                normalizedRaw(rawAt(t, p00), blackAt(blackByPhase, phase)),
                normalizedRaw(rawAt(t, p10), blackAt(blackByPhase, phase)),
                normalizedRaw(rawAt(t, p01), blackAt(blackByPhase, phase)),
                normalizedRaw(rawAt(t, p11), blackAt(blackByPhase, phase))
            );
        }
        float bilinearSamePhase(vec4 v, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 f = fract((rawCenter - origin) * 0.5);
            return mix(mix(v.x, v.y, f.x), mix(v.z, v.w, f.x), f.y);
        }
        float samePhasePeak(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        float secondHighestReference(ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float first = 0.0;
            float second = 0.0;
            for (int y = 0; y < 2; ++y) {
                for (int x = 0; x < 2; ++x) {
                    float signal = normalizedAt(
                        uReferenceRaw, q + ivec2(x, y), uReferenceBlackByPhase);
                    if (signal >= first) { second = first; first = signal; }
                    else if (signal > second) { second = signal; }
                }
            }
            return second;
        }
        float shortQuadConfidence(ivec2 referenceQuad, vec2 flowRawPixels) {
            float confidence = 1.0;
            for (int phase = 0; phase < 4; ++phase) {
                ivec2 rp = referenceQuad + phaseOffset(phase);
                vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                float peak = samePhasePeak(samePhaseSupport(
                    uShortRaw, shortCenter, phase, uShortBlackByPhase));
                float phaseConfidence = 1.0 - smoothstep(
                    uShortHeadroomThreshold, 0.995, peak);
                confidence = min(confidence, phaseConfidence);
            }
            return clamp(confidence, 0.0, 1.0);
        }

        void main() {
            ivec2 tile = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uGridSize - ivec2(1));
            vec2 flowTextureUv = (vec2(tile) + vec2(0.5)) / vec2(uGridSize);
            vec2 referenceUv = (flowTextureUv - uFlowScaleOffset.zw) /
                max(uFlowScaleOffset.xy, vec2(1.0e-7));
            referenceUv = clamp(referenceUv, vec2(0.0), vec2(1.0));
            vec4 flow = texelFetch(uFlow, tile, 0);
            vec2 flowRawPixels = flow.xy * vec2(uRawSize);
            ivec2 referenceP = clampRaw(ivec2(floor(referenceUv * vec2(uRawSize))));
            ivec2 referenceQuad = (referenceP / 2) * 2;

            float residualConfidence = 1.0 - smoothstep(0.50, 2.00, max(flow.w, 0.0));
            float sourceConfidence = shortQuadConfidence(referenceQuad, flowRawPixels);
            float referenceSecond = secondHighestReference(referenceP);
            float brightRegionConfidence = smoothstep(uRegionFloor, uBoundaryCeiling, referenceSecond);
            float regionConfidence = min(
                residualConfidence, min(sourceConfidence, brightRegionConfidence));
            float anchorConfidence = 0.0;

            if (regionConfidence > 0.0 && referenceSecond < uBoundaryCeiling) {
                float errorSum = 0.0;
                int phaseEvidence = 0;
                int quadEvidence = 0;
                for (int qy = -1; qy <= 1; ++qy) {
                    for (int qx = -1; qx <= 1; ++qx) {
                        ivec2 rq = referenceQuad + ivec2(qx * 2, qy * 2);
                        int phasesThisQuad = 0;
                        for (int phase = 0; phase < 4; ++phase) {
                            ivec2 rp = clampRaw(rq + phaseOffset(phase));
                            float nr = normalizedAt(uReferenceRaw, rp, uReferenceBlackByPhase);
                            if (nr < 0.025 || nr >= uBoundaryCeiling) continue;
                            vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                            vec4 support = samePhaseSupport(
                                uShortRaw, shortCenter, phase, uShortBlackByPhase);
                            if (samePhasePeak(support) >= uShortHeadroomThreshold) continue;
                            float ns = bilinearSamePhase(support, shortCenter, phase) * uExposureRatio;
                            if (ns < 0.025) continue;
                            errorSum += abs(ns - nr) / max(max(nr, ns), 0.05);
                            phaseEvidence += 1;
                            phasesThisQuad += 1;
                        }
                        if (phasesThisQuad >= 2) quadEvidence += 1;
                    }
                }
                if (quadEvidence >= 3 && phaseEvidence >= 6) {
                    float meanError = errorSum / float(phaseEvidence);
                    float radiometricConfidence = 1.0 - smoothstep(
                        uConsistencyLow, uConsistencyHigh, meanError);
                    anchorConfidence = min(regionConfidence, radiometricConfidence);
                }
            }
            oAnchor = vec4(flow.xy, regionConfidence, anchorConfidence);
        }
    """.trimIndent()

    /* IRIS_26606_SHORT_BOUNDARY_BOTTLENECK_PROPAGATION
     * Boundary trust may enter a clipped core only through connected cells whose local affine
     * residual and SHORT source validity remain strong. Confidence is propagated with min/max
     * bottleneck operations, never repeated multiplication, so a valid large highlight core does
     * not decay toward zero while a low-confidence discontinuity remains a hard barrier.
     */
    val shortBoundaryPropagate26606 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAnchor;
        uniform sampler2D uCurrent;
        uniform ivec2 uGridSize;
        layout(location = 0) out float oTrust;

        float trustAt(ivec2 p) {
            return texelFetch(uCurrent, clamp(p, ivec2(0), uGridSize - ivec2(1)), 0).r;
        }
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uGridSize - ivec2(1));
            vec4 anchor = texelFetch(uAnchor, p, 0);
            float regionConfidence = clamp(anchor.z, 0.0, 1.0);
            float trust = clamp(anchor.w, 0.0, 1.0);
            if (regionConfidence >= 0.50) {
                trust = max(trust, min(regionConfidence, trustAt(p + ivec2(-1, 0))));
                trust = max(trust, min(regionConfidence, trustAt(p + ivec2( 1, 0))));
                trust = max(trust, min(regionConfidence, trustAt(p + ivec2( 0,-1))));
                trust = max(trust, min(regionConfidence, trustAt(p + ivec2( 0, 1))));
            }
            oTrust = trust;
        }
    """.trimIndent()

    /* IRIS_26606_SHORT_RESCUE_SINGLE_WEIGHT_OWNER
     * Ordinary post-dilation Sabre weight remains authoritative while NORMAL is measurable.
     * As the NORMAL source quad becomes physically censored, only boundary-anchored coherent
     * SHORT confidence may replace it. This texture is still a single scalar weight for the
     * complete RGB observation; the existing exact 3x3 source-CFA clipping guard remains the
     * final physical veto inside both coverage accounting and the common RBF merge.
     */
    val shortRescueWeight26606 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uOrdinaryWeight;
        uniform sampler2D uReferenceExtractedBayer;
        uniform sampler2D uShortExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uBoundaryTrust;
        uniform ivec2 uExtractedSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uFrameBorderPadded;
        uniform float uSourceClippingPoint;
        layout(location = 0) out float oWeight;
        layout(location = 1) out float oRescueOnlyWeight;

        vec2 mirrorUvs(vec2 sampleUv) {
            if (sampleUv.x <= uFrameBorderPadded.x) sampleUv.x =
                2.0 * uFrameBorderPadded.x - sampleUv.x;
            if (sampleUv.y <= uFrameBorderPadded.y) sampleUv.y =
                2.0 * uFrameBorderPadded.y - sampleUv.y;
            if (sampleUv.x > uFrameBorderPadded.z) sampleUv.x =
                2.0 * uFrameBorderPadded.z - sampleUv.x;
            if (sampleUv.y > uFrameBorderPadded.w) sampleUv.y =
                2.0 * uFrameBorderPadded.w - sampleUv.y;
            return sampleUv;
        }
        float max4(vec4 v) { return max(max(v.r, v.g), max(v.b, v.a)); }
        float sourceQuadHeadroomConfidence(sampler2D image, vec2 uv) {
            ivec2 p = clamp(
                ivec2(floor(uv * vec2(uExtractedSize))),
                ivec2(0), uExtractedSize - ivec2(1));
            float peak = max4(texelFetch(image, p, 0));
            float start = max(1.0, uSourceClippingPoint * 0.9925);
            return 1.0 - smoothstep(
                start, max(start + 1.0e-4, uSourceClippingPoint), peak);
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(textureSize(uOrdinaryWeight, 0));
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 warpedUv = mirrorUvs(referenceUv + flow.xy);
            float ordinaryWeight = texture(uOrdinaryWeight, referenceUv).r;
            float referenceHeadroom = sourceQuadHeadroomConfidence(
                uReferenceExtractedBayer, referenceUv);
            float shortHeadroom = sourceQuadHeadroomConfidence(
                uShortExtractedBayer, warpedUv);
            float referenceLoss = 1.0 - referenceHeadroom;
            float residualConfidence = 1.0 - smoothstep(0.50, 2.00, max(flow.w, 0.0));
            float boundaryTrust = texture(uBoundaryTrust, flowUv).r;
            float rescueConfidence = min(
                shortHeadroom, min(residualConfidence, boundaryTrust));
            oWeight = clamp(mix(ordinaryWeight, rescueConfidence, referenceLoss), 0.0, 1.0);
            oRescueOnlyWeight = clamp(rescueConfidence * referenceLoss, 0.0, 1.0);
        }
    """.trimIndent()


    /* IRIS_26607_UNIVERSAL_HIGHLIGHT_COMPONENT_ANCHOR
     * The 26606 device bulb proof showed the boundary test was spatially undersampled: one
     * ~66x67 RAW-pixel flow cell searched only ~6x6 RAW pixels around its center. 26607 samples
     * the actual flow-cell footprint and treats highlight loss as a physical RAW condition, not a
     * semantic scene class. The same rule therefore applies to bulbs, clouds, white fabric,
     * reflective metal, signage, windows, skin highlights, and any other recoverable highlight.
     *
     * flow.xy remains the exact production warp consumed by Sabre. flow.w remains diagnostic local
     * affine residual; it is used only as one geometry/coherence input and never as an absolute
     * registration-error proxy. Boundary radiometry validates the SAME production flow that the
     * common accumulator later consumes. Output z is connected highlight-component eligibility;
     * w is measurable-boundary anchor confidence. No private image/reconstruction is produced.
     */
    val shortComponentAnchor26607 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform sampler2D uFlow;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uSourceClippingPoint;
        uniform float uComponentFloor;
        uniform float uComponentFull;
        uniform float uBoundaryCeiling;
        uniform float uConsistencyLow;
        uniform float uConsistencyHigh;
        uniform float uFallbackAffineValid;
        uniform vec3 uFallbackFlowX;
        uniform vec3 uFallbackFlowY;
        layout(location = 0) out vec4 oAnchor;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        ivec2 clampGrid(ivec2 p) { return clamp(p, ivec2(0), uGridSize - ivec2(1)); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, (phase >> 1) & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float rawAt(highp usampler2D t, ivec2 p) {
            return float(texelFetch(t, clampRaw(p), 0).r);
        }
        float normalizedRaw(float rawCode, float black) {
            return max(rawCode - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        float normalizedAt(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = clampRaw(p);
            return normalizedRaw(rawAt(t, q), blackAt(blackByPhase, phaseAt(q)));
        }
        ivec2 phaseGridSize(int phase) {
            ivec2 off = phaseOffset(phase);
            return max((uRawSize - off + ivec2(1)) / 2, ivec2(1));
        }
        ivec2 phaseSamplePixel(int phase, ivec2 gridP) {
            ivec2 off = phaseOffset(phase);
            ivec2 size = phaseGridSize(phase);
            return 2 * clamp(gridP, ivec2(0), size - ivec2(1)) + off;
        }
        vec4 samePhaseRawSupport(highp usampler2D t, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 g = (rawCenter - origin) * 0.5;
            ivec2 g0 = ivec2(floor(g));
            return vec4(
                rawAt(t, phaseSamplePixel(phase, g0)),
                rawAt(t, phaseSamplePixel(phase, g0 + ivec2(1, 0))),
                rawAt(t, phaseSamplePixel(phase, g0 + ivec2(0, 1))),
                rawAt(t, phaseSamplePixel(phase, g0 + ivec2(1, 1)))
            );
        }
        float bilinearRaw(vec4 values, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 f = fract((rawCenter - origin) * 0.5);
            return mix(mix(values.x, values.y, f.x), mix(values.z, values.w, f.x), f.y);
        }
        float peak4(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        float secondHighest4(vec4 v) {
            float first = -1.0;
            float second = -1.0;
            for (int i = 0; i < 4; ++i) {
                float x = v[i];
                if (x >= first) { second = first; first = x; }
                else if (x > second) second = x;
            }
            return max(second, 0.0);
        }
        vec2 rawFlowAt(ivec2 p) {
            return texelFetch(uFlow, clampGrid(p), 0).xy * vec2(uRawSize);
        }
        float predictorConsensus(ivec2 tile) {
            if (tile.x <= 0 || tile.y <= 0 || tile.x + 1 >= uGridSize.x || tile.y + 1 >= uGridSize.y)
                return 0.0;
            vec2 p0 = 0.5 * (rawFlowAt(tile + ivec2(-1, 0)) + rawFlowAt(tile + ivec2(1, 0)));
            vec2 p1 = 0.5 * (rawFlowAt(tile + ivec2(0, -1)) + rawFlowAt(tile + ivec2(0, 1)));
            vec2 p2 = 0.5 * (rawFlowAt(tile + ivec2(-1, -1)) + rawFlowAt(tile + ivec2(1, 1)));
            vec2 p3 = 0.5 * (rawFlowAt(tile + ivec2(-1, 1)) + rawFlowAt(tile + ivec2(1, -1)));
            float s0 = length(p0-p1) + length(p0-p2) + length(p0-p3);
            float s1 = length(p1-p0) + length(p1-p2) + length(p1-p3);
            float s2 = length(p2-p0) + length(p2-p1) + length(p2-p3);
            float s3 = length(p3-p0) + length(p3-p1) + length(p3-p2);
            float spread = min(min(s0, s1), min(s2, s3)) / 3.0;
            return 1.0 - smoothstep(2.0, 8.0, spread);
        }
        float sourcePhaseConfidence(float peakRawCode) {
            float headroomStart = max(1.0, uSourceClippingPoint * 0.9925);
            return 1.0 - smoothstep(
                headroomStart,
                max(headroomStart + 1.0e-4, uSourceClippingPoint),
                peakRawCode);
        }
        vec4 referenceQuadNormalized(ivec2 referenceQuad) {
            vec4 v = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase)
                v[phase] = normalizedAt(
                    uReferenceRaw, referenceQuad + phaseOffset(phase), uReferenceBlackByPhase);
            return v;
        }
        bool shortQuadEvidence(
            ivec2 referenceQuad,
            vec2 flowRawPixels,
            out vec4 scaledShort,
            out vec4 phaseSourceConfidence
        ) {
            scaledShort = vec4(0.0);
            phaseSourceConfidence = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase) {
                ivec2 rp = referenceQuad + phaseOffset(phase);
                vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                vec4 supportRaw = samePhaseRawSupport(uShortRaw, shortCenter, phase);
                phaseSourceConfidence[phase] = sourcePhaseConfidence(peak4(supportRaw));
                float shortRawCode = bilinearRaw(supportRaw, shortCenter, phase);
                scaledShort[phase] = normalizedRaw(
                    shortRawCode, blackAt(uShortBlackByPhase, phase)) * uExposureRatio;
            }
            return min(min(phaseSourceConfidence.x, phaseSourceConfidence.y),
                min(phaseSourceConfidence.z, phaseSourceConfidence.w)) > 0.0;
        }
        float effectiveLossWeight(vec4 referenceNormalized, vec4 scaledShort) {
            vec4 phaseLoss = vec4(0.0);
            float severeSingle = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(scaledShort[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float signalGate = smoothstep(0.72, 0.92, predicted);
                phaseLoss[phase] = signalGate * smoothstep(0.05, 0.12, relativeLoss);
                severeSingle = max(severeSingle,
                    smoothstep(0.94, 0.98, reference) *
                    signalGate * smoothstep(0.12, 0.22, relativeLoss));
            }
            return max(secondHighest4(phaseLoss), severeSingle);
        }

        void main() {
            ivec2 tile = clampGrid(ivec2(gl_FragCoord.xy));
            vec2 flowTextureUv = (vec2(tile) + vec2(0.5)) / vec2(uGridSize);
            vec2 safeScale = max(abs(uFlowScaleOffset.xy), vec2(1.0e-7));
            vec2 referenceUv = (flowTextureUv - uFlowScaleOffset.zw) / safeScale;
            referenceUv = clamp(referenceUv, vec2(0.0), vec2(1.0));
            vec4 flow = texelFetch(uFlow, tile, 0);
            vec2 nativeFlowRawPixels = flow.xy * vec2(uRawSize);

            /* IRIS_26611_SAME_CFA_MEASURABLE_BOUNDARY_SEED
             * Device 26610 proved that 2..8 RAW-pixel residual confidence is unsafe at Bayer
             * highlight edges: p50=2.46 RAW px still received ~98% trust. A one-RAW-pixel
             * displacement can cross CFA phase, so only a sub-pixel local residual may seed a
             * clipped component. Same-phase radiometry below supplies the independent measurement
             * proof. Predictor coherence may strengthen a valid seed but can never manufacture it. */
            float strictBoundaryResidualConfidence =
                1.0 - smoothstep(0.35, 0.95, max(flow.w, 0.0));
            float neighborhoodPredictorConfidence = predictorConsensus(tile);
            float boundaryLocalFlowProof = strictBoundaryResidualConfidence * mix(
                0.85, 1.0, neighborhoodPredictorConfidence);

            /* IRIS_26625_ROBUST_AFFINE_FALLBACK_GEOMETRY
             * Never relax the successful 26611 local residual threshold. If the production center
             * is outside that threshold, a deterministic frame-global affine may only PROPOSE the
             * sampling geometry. The model came exclusively from <=0.95-RAW-pixel production-flow
             * inliers; the unchanged same-CFA 5x5 boundary radiometry below must still independently
             * authorize any seed. Thus geometry cannot manufacture SHORT ownership. */
            vec3 affineBasis = vec3(1.0, referenceUv.x, referenceUv.y);
            vec2 fallbackFlowRawPixels = vec2(
                dot(uFallbackFlowX, affineBasis), dot(uFallbackFlowY, affineBasis));
            bool useFallbackGeometry = strictBoundaryResidualConfidence <= 0.0 &&
                uFallbackAffineValid >= 0.5;
            vec2 flowRawPixels = useFallbackGeometry
                ? fallbackFlowRawPixels : nativeFlowRawPixels;
            float selectedGeometryProof = useFallbackGeometry
                ? 1.0 : boundaryLocalFlowProof;

            vec2 cellSpanRaw = vec2(uRawSize) / (vec2(uGridSize) * safeScale);
            vec2 cellCenterRaw = referenceUv * vec2(uRawSize);
            float componentBrightness = 0.0;
            float componentSourceConfidence = 0.0;
            float literalLossSeen = 0.0;
            float effectiveLossSeen = 0.0;
            float effectiveLossComponentConfidence = 0.0;
            float anchorConfidenceSum = 0.0;
            int anchorPhaseEvidence = 0;
            int anchorQuadEvidence = 0;

            /* Five-by-five probes span the full sparse-flow cell footprint at -50/-25/0/+25/+50%. */
            for (int py = -2; py <= 2; ++py) {
                for (int px = -2; px <= 2; ++px) {
                    vec2 probeRaw = cellCenterRaw +
                        vec2(float(px), float(py)) * (0.25 * cellSpanRaw);
                    ivec2 referenceP = clampRaw(ivec2(floor(probeRaw)));
                    ivec2 referenceQuad = (referenceP / 2) * 2;
                    vec4 referenceNormalized = referenceQuadNormalized(referenceQuad);
                    vec4 scaledShort = vec4(0.0);
                    vec4 phaseSourceConfidence = vec4(0.0);
                    bool hasShort = shortQuadEvidence(
                        referenceQuad, flowRawPixels, scaledShort, phaseSourceConfidence);
                    float probeSourceConfidence = min(
                        min(phaseSourceConfidence.x, phaseSourceConfidence.y),
                        min(phaseSourceConfidence.z, phaseSourceConfidence.w));
                    float referenceSecond = secondHighest4(referenceNormalized);
                    float shortSecond = secondHighest4(scaledShort);
                    float brightness = smoothstep(
                        uComponentFloor, uComponentFull, max(referenceSecond, shortSecond));
                    if (hasShort && brightness > 0.0) {
                        componentBrightness = max(componentBrightness, brightness);
                        componentSourceConfidence = max(
                            componentSourceConfidence, probeSourceConfidence);
                    }

                    int literalPhasesHere = 0;
                    for (int phase = 0; phase < 4; ++phase) {
                        if (rawAt(uReferenceRaw, referenceQuad + phaseOffset(phase)) >=
                                uSourceClippingPoint) literalPhasesHere += 1;
                    }
                    if (literalPhasesHere >= 2) literalLossSeen = 1.0;
                    if (hasShort) {
                        float probeEffectiveLoss = effectiveLossWeight(
                            referenceNormalized, scaledShort);
                        effectiveLossSeen = max(effectiveLossSeen, probeEffectiveLoss);
                        /* IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_MEMBERSHIP
                         * Near-saturated NORMAL may already have lost radiometry before literal
                         * two-phase sensor clipping. Bind that loss to SHORT headroom from the SAME
                         * probe so an unrelated good SHORT sample elsewhere in the flow cell cannot
                         * manufacture component membership. This is region membership only; geometry
                         * trust still requires the unchanged sub-pixel measurable boundary seed. */
                        effectiveLossComponentConfidence = max(
                            effectiveLossComponentConfidence,
                            min(probeSourceConfidence, probeEffectiveLoss));
                    }

                    int phasesThisQuad = 0;
                    if (hasShort) {
                        for (int phase = 0; phase < 4; ++phase) {
                            float nr = referenceNormalized[phase];
                            float ns = scaledShort[phase];
                            if (nr < 0.05 || nr >= uBoundaryCeiling || ns < 0.05) continue;
                            if (phaseSourceConfidence[phase] <= 0.0) continue;
                            float relativeError = abs(ns - nr) / max(max(nr, ns), 0.05);
                            anchorConfidenceSum += 1.0 - smoothstep(
                                uConsistencyLow, uConsistencyHigh, relativeError);
                            anchorPhaseEvidence += 1;
                            phasesThisQuad += 1;
                        }
                    }
                    if (phasesThisQuad >= 2) anchorQuadEvidence += 1;
                }
            }

            /* IRIS_26624_BOUNDARY_PROVEN_LITERAL_PLUS_EFFECTIVE_COMPONENT
             * z remains region membership only and still contains no geometry authority. Preserve
             * 26611 literal two-phase clipping exactly, but also admit exposure-normalized effective
             * loss when the SAME probe has valid SHORT headroom. This allows a proven boundary to
             * carry trust through broad clouds/ground/foliage whose NORMAL signal flattened before
             * literal clipping. Neither literal nor effective loss can self-seed: geometry enters
             * exclusively through unchanged w and the CFA-safe bottleneck propagation below. */
            float literalComponentConfidence = min(
                componentSourceConfidence, literalLossSeen);
            float componentConfidence = max(
                literalComponentConfidence, effectiveLossComponentConfidence);
            float anchorConfidence = 0.0;
            if (anchorQuadEvidence >= 4 && anchorPhaseEvidence >= 8
                    && selectedGeometryProof > 0.0) {
                float radiometricConfidence =
                    anchorConfidenceSum / float(anchorPhaseEvidence);
                anchorConfidence = min(
                    componentSourceConfidence,
                    min(selectedGeometryProof, radiometricConfidence));
            }
            oAnchor = vec4(flowRawPixels / vec2(uRawSize),
                clamp(componentConfidence, 0.0, 1.0),
                clamp(anchorConfidence, 0.0, 1.0));
        }
    """.trimIndent()

    /* IRIS_26607_CONNECTED_HIGHLIGHT_COMPONENT_PROPAGATION
     * Boundary trust is propagated across the physically bright/lost component with a bottleneck
     * min/max rule. Adjacent production-flow disagreement is a discontinuity barrier, not an
     * absolute registration metric. This prevents a validated bulb/cloud component from dying at
     * each interior cell while still failing closed across a strong local motion boundary.
     */
    val shortComponentPropagate26607 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAnchor;
        uniform sampler2D uCurrent;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        layout(location = 0) out float oTrust;

        ivec2 clampGrid(ivec2 p) { return clamp(p, ivec2(0), uGridSize - ivec2(1)); }
        float trustAt(ivec2 p) { return texelFetch(uCurrent, clampGrid(p), 0).r; }
        vec2 rawFlowAtAnchor(ivec2 p) {
            return texelFetch(uAnchor, clampGrid(p), 0).xy * vec2(uRawSize);
        }
        float compatibleFlow(ivec2 a, ivec2 b) {
            /* IRIS_26611_CFA_PHASE_SAFE_COMPONENT_PROPAGATION
             * Trust may cross only a smoothly registered physically clipped interior. A neighbor
             * flow jump approaching one RAW pixel can change CFA phase ownership and therefore
             * terminates propagation instead of painting SHORT chroma across a material edge. */
            float delta = length(rawFlowAtAnchor(a) - rawFlowAtAnchor(b));
            return 1.0 - smoothstep(0.50, 1.25, delta);
        }
        void main() {
            ivec2 p = clampGrid(ivec2(gl_FragCoord.xy));
            vec4 anchor = texelFetch(uAnchor, p, 0);
            float componentConfidence = clamp(anchor.z, 0.0, 1.0);
            float trust = clamp(anchor.w, 0.0, 1.0);
            if (componentConfidence > 0.0) {
                ivec2 n0 = p + ivec2(-1, 0);
                ivec2 n1 = p + ivec2( 1, 0);
                ivec2 n2 = p + ivec2( 0,-1);
                ivec2 n3 = p + ivec2( 0, 1);
                trust = max(trust, min(componentConfidence,
                    min(trustAt(n0), compatibleFlow(p, n0))));
                trust = max(trust, min(componentConfidence,
                    min(trustAt(n1), compatibleFlow(p, n1))));
                trust = max(trust, min(componentConfidence,
                    min(trustAt(n2), compatibleFlow(p, n2))));
                trust = max(trust, min(componentConfidence,
                    min(trustAt(n3), compatibleFlow(p, n3))));
            }
            oTrust = trust;
        }
    """.trimIndent()

    /* IRIS_26625_COMPONENT_EFFECTIVE_FLOW
     * The common Sabre merge must sample the exact geometry that boundary radiometry validated.
     * Outside boundary-proven component trust, preserve production flow byte-for-byte. Inside it,
     * use oAnchor.xy (native when 26611 was valid, robust affine only when native was invalid).
     * z/w remain production-flow metadata; no second merge or RGB path is created.
     */
    val shortComponentEffectiveFlow26625 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uFlow;
        uniform sampler2D uAnchor;
        uniform sampler2D uTrust;
        uniform ivec2 uGridSize;
        layout(location = 0) out vec4 oFlow;
        layout(location = 1) out float oFallbackUsed;
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uGridSize - ivec2(1));
            vec4 production = texelFetch(uFlow, p, 0);
            vec4 geometry = texelFetch(uAnchor, p, 0);
            float trust = clamp(texelFetch(uTrust, p, 0).r, 0.0, 1.0);
            bool componentOwned = trust > 0.0;
            bool fallbackUsed = componentOwned && production.w >= 0.95 &&
                length(geometry.xy - production.xy) > 1.0e-7;
            vec2 selected = componentOwned ? geometry.xy : production.xy;
            oFlow = vec4(selected, production.zw);
            oFallbackUsed = fallbackUsed ? 1.0 : 0.0;
        }
    """.trimIndent()

    /* IRIS_26607_UNIVERSAL_EFFECTIVE_HIGHLIGHT_LOSS_WEIGHT
     * Rescue is triggered by physical NORMAL information loss, not by semantic scene type and not
     * only by literal sensor code saturation. For each spatial CFA phase, exposure-normalized
     * SHORT is compared with NORMAL in the same RAW domain. A two-phase 5..12% deficit, or one
     * severe near-saturation phase, proves effective NORMAL censorship before literal white.
     *
     * Component trust owns geometry once boundary correspondence has been validated. No second
     * flow.w penalty is applied here. The exact common-RBF 3x3 source-clipping guard still runs
     * afterward and is the final physical veto before accumulator contribution.
     *
     * MRT outputs: final common-Sabre SHORT weight, target-domain rescue-only weight, and NORMAL
     * physical-loss candidate weight for semantic funnel telemetry.
     */
    val shortRescueWeight26607 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uOrdinaryWeight;
        uniform sampler2D uPhysicalWeight;
        uniform sampler2D uReferenceExtractedBayer;
        uniform sampler2D uShortExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uComponentTrust;
        uniform ivec2 uExtractedSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uFrameBorderPadded;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uSourceClippingPoint;
        layout(location = 0) out float oWeight;
        layout(location = 1) out float oRescueOnlyWeight;
        layout(location = 2) out float oLossCandidate;

        vec2 mirrorUvs(vec2 sampleUv) {
            if (sampleUv.x <= uFrameBorderPadded.x) sampleUv.x =
                2.0 * uFrameBorderPadded.x - sampleUv.x;
            if (sampleUv.y <= uFrameBorderPadded.y) sampleUv.y =
                2.0 * uFrameBorderPadded.y - sampleUv.y;
            if (sampleUv.x > uFrameBorderPadded.z) sampleUv.x =
                2.0 * uFrameBorderPadded.z - sampleUv.x;
            if (sampleUv.y > uFrameBorderPadded.w) sampleUv.y =
                2.0 * uFrameBorderPadded.w - sampleUv.y;
            return sampleUv;
        }
        float secondHighest4(vec4 v) {
            float first = -1.0;
            float second = -1.0;
            for (int i = 0; i < 4; ++i) {
                float x = v[i];
                if (x >= first) { second = first; first = x; }
                else if (x > second) second = x;
            }
            return max(second, 0.0);
        }
        vec4 normalizedQuad(vec4 rawQuad, vec4 blackByPhase) {
            vec4 denominator = max(vec4(uWhiteLevel) - blackByPhase, vec4(1.0));
            return max(rawQuad - blackByPhase, vec4(0.0)) / denominator;
        }
        ivec2 clampExtracted(ivec2 p) {
            return clamp(p, ivec2(0), uExtractedSize - ivec2(1));
        }
        void shortPhaseSupport(vec2 uv, out vec4 interpolatedRaw, out vec4 peakRaw) {
            vec2 position = uv * vec2(uExtractedSize) - vec2(0.5);
            ivec2 p0 = ivec2(floor(position));
            vec2 f = fract(position);
            vec4 q00 = texelFetch(uShortExtractedBayer, clampExtracted(p0), 0);
            vec4 q10 = texelFetch(uShortExtractedBayer, clampExtracted(p0 + ivec2(1, 0)), 0);
            vec4 q01 = texelFetch(uShortExtractedBayer, clampExtracted(p0 + ivec2(0, 1)), 0);
            vec4 q11 = texelFetch(uShortExtractedBayer, clampExtracted(p0 + ivec2(1, 1)), 0);
            interpolatedRaw = mix(mix(q00, q10, f.x), mix(q01, q11, f.x), f.y);
            peakRaw = max(max(q00, q10), max(q01, q11));
        }
        float wholeShortHeadroom(vec4 peakRaw) {
            float peak = max(max(peakRaw.x, peakRaw.y), max(peakRaw.z, peakRaw.w));
            float headroomStart = max(1.0, uSourceClippingPoint * 0.9925);
            return 1.0 - smoothstep(
                headroomStart,
                max(headroomStart + 1.0e-4, uSourceClippingPoint),
                peak);
        }
        float effectiveLossWeight(vec4 referenceNormalized, vec4 scaledShort) {
            vec4 phaseLoss = vec4(0.0);
            float severeSingle = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(scaledShort[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float signalGate = smoothstep(0.72, 0.92, predicted);
                phaseLoss[phase] = signalGate * smoothstep(0.05, 0.12, relativeLoss);
                severeSingle = max(severeSingle,
                    smoothstep(0.94, 0.98, reference) * signalGate *
                    smoothstep(0.12, 0.22, relativeLoss));
            }
            return max(secondHighest4(phaseLoss), severeSingle);
        }
        float literalLossWeight(
            vec4 referenceRaw,
            vec4 scaledShort,
            vec4 peakShortRaw
        ) {
            /* IRIS_26610_TWO_PHASE_PHYSICAL_CENSORSHIP_ONLY
             * Guides are already exposure-normalized before ordinary Sabre rejection. Therefore
             * ordinary photometric protection remains physically valid for SHORT unless NORMAL
             * has lost at least two CFA phases to literal RAW clipping. A one-phase or merely
             * effective/downstream highlight-risk signal may request/carry SHORT, but it may not
             * bypass ordinary NORMAL photometric rejection. */
            if (secondHighest4(referenceRaw) < uSourceClippingPoint) return 0.0;
            float explained = 1.0;
            for (int phase = 0; phase < 4; ++phase) {
                if (referenceRaw[phase] >= uSourceClippingPoint) {
                    float phaseHeadroom = peakShortRaw[phase] < uSourceClippingPoint ? 1.0 : 0.0;
                    float signalProof = smoothstep(0.85, 0.95, scaledShort[phase]);
                    explained = min(explained, phaseHeadroom * signalProof);
                }
            }
            return explained;
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(textureSize(uOrdinaryWeight, 0));
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 warpedUv = mirrorUvs(referenceUv + flow.xy);
            float ordinaryWeight = texture(uOrdinaryWeight, referenceUv).r;
            float physicalWeight = texture(uPhysicalWeight, referenceUv).r;

            ivec2 referenceP = clampExtracted(
                ivec2(floor(referenceUv * vec2(uExtractedSize))));
            vec4 referenceRaw = texelFetch(uReferenceExtractedBayer, referenceP, 0);
            vec4 shortRaw = vec4(0.0);
            vec4 shortPeakRaw = vec4(0.0);
            shortPhaseSupport(warpedUv, shortRaw, shortPeakRaw);
            vec4 referenceNormalized = normalizedQuad(referenceRaw, uReferenceBlackByPhase);
            vec4 scaledShort = normalizedQuad(shortRaw, uShortBlackByPhase) * uExposureRatio;

            float literalLoss = literalLossWeight(referenceRaw, scaledShort, shortPeakRaw);
            float effectiveLoss = effectiveLossWeight(referenceNormalized, scaledShort);
            float targetLoss = clamp(max(literalLoss, effectiveLoss), 0.0, 1.0);
            float shortHeadroom = wholeShortHeadroom(shortPeakRaw);
            float componentTrust = clamp(texture(uComponentTrust, flowUv).r, 0.0, 1.0);
            /* IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY
             * componentTrust can exist only if a sub-pixel, same-CFA, exposure-normalized
             * measurable boundary seed was proven and then propagated through the two-phase clipped
             * interior without a CFA-meaningful flow discontinuity. The old 2..8 RAW-pixel local
             * residual curve is deliberately absent here: it was the 26610 device-proven path that
             * treated a 2.46-pixel residual as ~98% trustworthy. */
            float rescueConfidence = min(shortHeadroom, componentTrust);

            /* IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP
             * Only NORMAL-reference photometry is relaxable in a proven censored core. The exact
             * ordinary-rejection physical/unblocker weight after the same dilation remains a hard
             * cap, and the common RBF 3x3 source-clipping guard still runs afterward. */
            float censoredCoreWeight = min(physicalWeight, rescueConfidence);
            /* IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_RESCUE
             * Preserve the complete 26611 literal-censoring path byte-for-byte in literalFinalWeight.
             * For pre-clipping/effective NORMAL loss, componentTrust is the geometry authority: only
             * boundary-proven trust may expose the already-validated SHORT sample, still capped by
             * SHORT headroom + ordinary physical rejection and followed by the common 3x3 source-clip
             * veto. effectiveRescueWeight is additive-only (max), so near-saturation recovery can
             * never reduce an ordinary valid SHORT weight or alter non-highlight behavior. */
            float physicalCensoring = clamp(literalLoss, 0.0, 1.0);
            float literalFinalWeight = mix(
                ordinaryWeight, censoredCoreWeight, physicalCensoring);
            float effectiveRescueWeight = censoredCoreWeight * clamp(effectiveLoss, 0.0, 1.0);
            float finalWeight = max(literalFinalWeight, effectiveRescueWeight);
            oWeight = clamp(finalWeight, 0.0, 1.0);
            oRescueOnlyWeight = clamp(max(finalWeight - ordinaryWeight, 0.0), 0.0, 1.0);
            oLossCandidate = targetLoss;
        }
    """.trimIndent()

    /* IRIS_26595_SUBPIXEL_PHASE_SHORT_HANDOFF
     * 26594 device proof exposed three independent false-closed conditions:
     *  - Sabre photometric rejection deliberately collapses when clipped NORMAL guide=10000;
     *  - integer RAW snapping discarded subpixel flow before the 5% radiometric proof;
     *  - a fixed flood radius could not be a universal owner for large clipped cores.
     *
     * 26595 keeps boundary radiometry only where NORMAL is still measurable, but samples SHORT at
     * the exact Sabre subpixel displacement on the SAME CFA phase lattice. Geometry is flow-only
     * (flow.w raw-pixel variation). SHORT headroom is checked only on the phase support actually
     * used by interpolation. No Sabre frameWeight/unblocker value is an HDR eligibility input.
     */
    val shortRegionSeed26595 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform sampler2D uFlow;
        uniform ivec2 uRawSize;
        uniform ivec2 uRegionSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uRegionFloor;
        uniform float uBoundaryCeiling;
        uniform float uShortHeadroomThreshold;
        uniform float uFlowVariationPixelsThreshold;
        uniform float uConsistencyThreshold;
        layout(location = 0) out float oSeed;
        layout(location = 1) out float oRegion;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        float rawAt(highp usampler2D t, ivec2 p) { return float(texelFetch(t, clampRaw(p), 0).r); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, (phase >> 1) & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float normalizedRaw(float raw, float black) {
            return max(raw - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        float normalizedAt(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = clampRaw(p);
            return normalizedRaw(rawAt(t, q), blackAt(blackByPhase, phaseAt(q)));
        }
        ivec2 phaseGridSize(int phase) {
            ivec2 off = phaseOffset(phase);
            return max((uRawSize - off + ivec2(1)) / 2, ivec2(1));
        }
        ivec2 phaseSamplePixel(int phase, ivec2 gridP) {
            ivec2 off = phaseOffset(phase);
            ivec2 size = phaseGridSize(phase);
            return 2 * clamp(gridP, ivec2(0), size - ivec2(1)) + off;
        }
        vec4 samePhaseSupport(highp usampler2D t, vec2 rawCenter, int phase, vec4 blackByPhase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 g = (rawCenter - origin) * 0.5;
            ivec2 g0 = ivec2(floor(g));
            vec2 f = fract(g);
            ivec2 p00 = phaseSamplePixel(phase, g0);
            ivec2 p10 = phaseSamplePixel(phase, g0 + ivec2(1, 0));
            ivec2 p01 = phaseSamplePixel(phase, g0 + ivec2(0, 1));
            ivec2 p11 = phaseSamplePixel(phase, g0 + ivec2(1, 1));
            float a = normalizedRaw(rawAt(t, p00), blackAt(blackByPhase, phase));
            float b = normalizedRaw(rawAt(t, p10), blackAt(blackByPhase, phase));
            float c = normalizedRaw(rawAt(t, p01), blackAt(blackByPhase, phase));
            float d = normalizedRaw(rawAt(t, p11), blackAt(blackByPhase, phase));
            return vec4(a, b, c, d);
        }
        float bilinearSamePhase(vec4 v, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 f = fract((rawCenter - origin) * 0.5);
            return mix(mix(v.x, v.y, f.x), mix(v.z, v.w, f.x), f.y);
        }
        float samePhasePeak(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        float secondHighestReference(ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float first = 0.0; float second = 0.0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                float signal = normalizedAt(uReferenceRaw, q + ivec2(x, y), uReferenceBlackByPhase);
                if (signal >= first) { second = first; first = signal; }
                else if (signal > second) second = signal;
            }
            return second;
        }
        /* IRIS_26599_PHASE_SCOPED_REGION_MEASURABILITY
         * Region connectivity needs the SHORT quad to remain physically measurable, not a full
         * 10% reserve in every unrelated CFA phase. Boundary seeds below still demand the strict
         * per-phase 0.90 reserve for every phase actually used by radiometric proof.
         */
        bool shortQuadPhysicallyMeasurable(ivec2 referenceQuad, vec2 flowRawPixels) {
            for (int phase = 0; phase < 4; ++phase) {
                ivec2 rp = referenceQuad + phaseOffset(phase);
                vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                if (samePhasePeak(samePhaseSupport(
                        uShortRaw, shortCenter, phase, uShortBlackByPhase)) >= 0.995) return false;
            }
            return true;
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uRegionSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 flowRawPixels = flow.xy * vec2(uRawSize);
            ivec2 referenceP = clampRaw(ivec2(floor(referenceUv * vec2(uRawSize))));
            ivec2 referenceQuad = (referenceP / 2) * 2;

            bool geometryTrusted = flow.w <= uFlowVariationPixelsThreshold &&
                shortQuadPhysicallyMeasurable(referenceQuad, flowRawPixels);
            float referenceSecond = secondHighestReference(referenceP);
            bool regionCandidate = geometryTrusted && referenceSecond >= uRegionFloor;
            oRegion = regionCandidate ? 1.0 : 0.0;
            if (!regionCandidate || referenceSecond >= uBoundaryCeiling) {
                oSeed = 0.0;
                return;
            }

            float errorSum = 0.0;
            int phaseEvidence = 0;
            int quadEvidence = 0;
            for (int qy = -1; qy <= 1; ++qy) {
                for (int qx = -1; qx <= 1; ++qx) {
                    ivec2 rq = referenceQuad + ivec2(qx * 2, qy * 2);
                    int phasesThisQuad = 0;
                    for (int phase = 0; phase < 4; ++phase) {
                        ivec2 rp = clampRaw(rq + phaseOffset(phase));
                        float nr = normalizedAt(uReferenceRaw, rp, uReferenceBlackByPhase);
                        if (nr < 0.025 || nr >= uBoundaryCeiling) continue;
                        vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                        vec4 support = samePhaseSupport(
                            uShortRaw, shortCenter, phase, uShortBlackByPhase);
                        if (samePhasePeak(support) >= uShortHeadroomThreshold) continue;
                        float ns = bilinearSamePhase(support, shortCenter, phase) * uExposureRatio;
                        if (ns < 0.025) continue;
                        errorSum += abs(ns - nr) / max(max(nr, ns), 0.05);
                        phaseEvidence += 1;
                        phasesThisQuad += 1;
                    }
                    if (phasesThisQuad >= 2) quadEvidence += 1;
                }
            }
            float meanError = phaseEvidence > 0 ? errorSum / float(phaseEvidence) : 1.0;
            oSeed = quadEvidence >= 3 && phaseEvidence >= 6 &&
                meanError < uConsistencyThreshold ? 1.0 : 0.0;
        }
    """.trimIndent()

    val shortRegionPropagate26594 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uSeed;
        uniform sampler2D uRegion;
        uniform sampler2D uCurrent;
        uniform ivec2 uSize;
        layout(location = 0) out float oTrust;

        float at(sampler2D t, ivec2 p) {
            return texelFetch(t, clamp(p, ivec2(0), uSize - ivec2(1)), 0).r;
        }
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uSize - ivec2(1));
            float seed = at(uSeed, p);
            if (seed >= 0.5) { oTrust = 1.0; return; }
            if (at(uRegion, p) < 0.5) { oTrust = 0.0; return; }
            float trust = 0.0;
            for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x)
                trust = max(trust, at(uCurrent, p + ivec2(x, y)));
            oTrust = trust >= 0.5 ? 1.0 : 0.0;
        }
    """.trimIndent()

    /* IRIS_26600_BOUNDARY_CONSENSUS_SHORT_GEOMETRY
     * 26599 device proof showed every bright candidate died at the old flow.w max-range gate.
     * flow.w is the maximum 3x3 sparse-LK range, so one textureless/clipped outlier can reject an
     * otherwise coherent alignment. 26600 builds a SHORT-only geometry authority on the existing
     * sparse Sabre grid instead: a strict majority cluster chooses the local flow, an ambiguous
     * second cluster rejects motion boundaries, and measurable NORMAL/SHORT boundary radiometry
     * marks where non-literal HDR ownership may originate. No threshold is relaxed: all flow
     * consensus uses the same 2 RAW-pixel tolerance that 26595 used as its fail-closed limit.
     * Output: xy normalized SHORT flow, z geometry trust, w radiometric-boundary seed.
     */
    val shortBoundaryGeometrySeed26600 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform sampler2D uFlow;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uRegionFloor;
        uniform float uBoundaryCeiling;
        uniform float uShortHeadroomThreshold;
        uniform float uConsensusPixels;
        uniform float uConsistencyThreshold;
        layout(location = 0) out vec4 oGeometry;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        ivec2 clampGrid(ivec2 p) { return clamp(p, ivec2(0), uGridSize - ivec2(1)); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, (phase >> 1) & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float rawAt(highp usampler2D t, ivec2 p) { return float(texelFetch(t, clampRaw(p), 0).r); }
        float normalizedRaw(float raw, float black) {
            return max(raw - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        float normalizedAt(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = clampRaw(p);
            return normalizedRaw(rawAt(t, q), blackAt(blackByPhase, phaseAt(q)));
        }
        ivec2 phaseGridSize(int phase) {
            ivec2 off = phaseOffset(phase);
            return max((uRawSize - off + ivec2(1)) / 2, ivec2(1));
        }
        ivec2 phaseSamplePixel(int phase, ivec2 gridP) {
            ivec2 off = phaseOffset(phase);
            ivec2 size = phaseGridSize(phase);
            return 2 * clamp(gridP, ivec2(0), size - ivec2(1)) + off;
        }
        vec4 samePhaseSupport(highp usampler2D t, vec2 rawCenter, int phase, vec4 blackByPhase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 g = (rawCenter - origin) * 0.5;
            ivec2 g0 = ivec2(floor(g));
            ivec2 p00 = phaseSamplePixel(phase, g0);
            ivec2 p10 = phaseSamplePixel(phase, g0 + ivec2(1, 0));
            ivec2 p01 = phaseSamplePixel(phase, g0 + ivec2(0, 1));
            ivec2 p11 = phaseSamplePixel(phase, g0 + ivec2(1, 1));
            float a = normalizedRaw(rawAt(t, p00), blackAt(blackByPhase, phase));
            float b = normalizedRaw(rawAt(t, p10), blackAt(blackByPhase, phase));
            float c = normalizedRaw(rawAt(t, p01), blackAt(blackByPhase, phase));
            float d = normalizedRaw(rawAt(t, p11), blackAt(blackByPhase, phase));
            return vec4(a, b, c, d);
        }
        float bilinearSamePhase(vec4 v, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 f = fract((rawCenter - origin) * 0.5);
            return mix(mix(v.x, v.y, f.x), mix(v.z, v.w, f.x), f.y);
        }
        float samePhasePeak(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        float secondHighestReference(ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float first = 0.0; float second = 0.0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                float signal = normalizedAt(uReferenceRaw, q + ivec2(x, y), uReferenceBlackByPhase);
                if (signal >= first) { second = first; first = signal; }
                else if (signal > second) second = signal;
            }
            return second;
        }
        vec2 rawFlowAt(ivec2 p) {
            return texelFetch(uFlow, clampGrid(p), 0).xy * vec2(uRawSize);
        }
        int supportCount(vec2 hypothesis) {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            int count = 0;
            for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x)
                count += length(rawFlowAt(tile + ivec2(x, y)) - hypothesis) <= uConsensusPixels ? 1 : 0;
            return count;
        }
        bool robustLocalFlow(out vec2 meanRawFlow) {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            int bestSupport = 0;
            vec2 best = vec2(0.0);
            for (int cy = -1; cy <= 1; ++cy) for (int cx = -1; cx <= 1; ++cx) {
                vec2 h = rawFlowAt(tile + ivec2(cx, cy));
                int support = supportCount(h);
                if (support > bestSupport) { bestSupport = support; best = h; }
            }
            if (bestSupport < 5) return false;
            int secondSupport = 0;
            for (int cy = -1; cy <= 1; ++cy) for (int cx = -1; cx <= 1; ++cx) {
                vec2 h = rawFlowAt(tile + ivec2(cx, cy));
                if (length(h - best) <= uConsensusPixels) continue;
                secondSupport = max(secondSupport, supportCount(h));
            }
            if (bestSupport - secondSupport < 2) return false;
            vec2 sum = vec2(0.0);
            int count = 0;
            for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                vec2 v = rawFlowAt(tile + ivec2(x, y));
                if (length(v - best) <= uConsensusPixels) { sum += v; count += 1; }
            }
            if (count < 5) return false;
            meanRawFlow = sum / float(count);
            float maximumDeviation = 0.0;
            for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                vec2 v = rawFlowAt(tile + ivec2(x, y));
                if (length(v - best) <= uConsensusPixels)
                    maximumDeviation = max(maximumDeviation, length(v - meanRawFlow));
            }
            return maximumDeviation <= uConsensusPixels;
        }
        bool boundaryRadiometryAt(vec2 referenceUv, vec2 flowRawPixels) {
            ivec2 referenceP = clampRaw(ivec2(floor(referenceUv * vec2(uRawSize))));
            ivec2 referenceQuad = (referenceP / 2) * 2;
            float referenceSecond = secondHighestReference(referenceP);
            if (referenceSecond < uRegionFloor || referenceSecond >= uBoundaryCeiling) return false;
            float errorSum = 0.0;
            int phaseEvidence = 0;
            int quadEvidence = 0;
            for (int qy = -1; qy <= 1; ++qy) {
                for (int qx = -1; qx <= 1; ++qx) {
                    ivec2 rq = referenceQuad + ivec2(qx * 2, qy * 2);
                    int phasesThisQuad = 0;
                    for (int phase = 0; phase < 4; ++phase) {
                        ivec2 rp = clampRaw(rq + phaseOffset(phase));
                        float nr = normalizedAt(uReferenceRaw, rp, uReferenceBlackByPhase);
                        if (nr < 0.025 || nr >= uBoundaryCeiling) continue;
                        vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                        vec4 support = samePhaseSupport(uShortRaw, shortCenter, phase, uShortBlackByPhase);
                        if (samePhasePeak(support) >= uShortHeadroomThreshold) continue;
                        float ns = bilinearSamePhase(support, shortCenter, phase) * uExposureRatio;
                        if (ns < 0.025) continue;
                        errorSum += abs(ns - nr) / max(max(nr, ns), 0.05);
                        phaseEvidence += 1;
                        phasesThisQuad += 1;
                    }
                    if (phasesThisQuad >= 2) quadEvidence += 1;
                }
            }
            float meanError = phaseEvidence > 0 ? errorSum / float(phaseEvidence) : 1.0;
            return quadEvidence >= 3 && phaseEvidence >= 6 && meanError < uConsistencyThreshold;
        }
        void main() {
            oGeometry = vec4(0.0);
            vec2 meanRawFlow = vec2(0.0);
            if (!robustLocalFlow(meanRawFlow)) return;
            ivec2 tile = ivec2(gl_FragCoord.xy);
            vec2 flowUv = (vec2(tile) + vec2(0.5)) / vec2(uGridSize);
            vec2 safeScale = max(abs(uFlowScaleOffset.xy), vec2(1.0e-6));
            vec2 referenceCenter = (flowUv - uFlowScaleOffset.zw) / safeScale;
            vec2 referenceStep = (vec2(1.0) / vec2(uGridSize)) / safeScale;
            float boundary = 0.0;
            for (int sy = -1; sy <= 1; ++sy) for (int sx = -1; sx <= 1; ++sx) {
                vec2 uv = clamp(referenceCenter + vec2(float(sx), float(sy)) * referenceStep * 0.33,
                    vec2(0.0), vec2(1.0));
                if (boundaryRadiometryAt(uv, meanRawFlow)) boundary = 1.0;
            }
            oGeometry = vec4(meanRawFlow / vec2(uRawSize), 1.0, boundary);
        }
    """.trimIndent()

    /* IRIS_26600_BOUNDARY_CONSENSUS_PROPAGATION
     * Grow only through highlight cells. Geometry holes require a coherent 8-neighbour flow
     * cluster; conflicting object/background motion therefore stays untrusted. Boundary proof is
     * carried only along the same coherent flow. Running gridWidth+gridHeight passes removes the
     * old fixed 32-quarter-resolution-cell radius without increasing native-resolution memory.
     */
    val shortBoundaryGeometryPropagate26600 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform sampler2D uCurrent;
        uniform highp usampler2D uReferenceRaw;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uRegionFloor;
        uniform float uConsensusPixels;
        layout(location = 0) out vec4 oGeometry;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        ivec2 clampGrid(ivec2 p) { return clamp(p, ivec2(0), uGridSize - ivec2(1)); }
        int phaseAt(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }
        float blackAt(vec4 b, int phase) { return b[phase]; }
        float rawAt(ivec2 p) { return float(texelFetch(uReferenceRaw, clampRaw(p), 0).r); }
        float normalizedAt(ivec2 p) {
            ivec2 q = clampRaw(p);
            float black = blackAt(uReferenceBlackByPhase, phaseAt(q));
            return max(rawAt(q) - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        vec2 topTwoAt(vec2 referenceUv) {
            ivec2 p = clampRaw(ivec2(floor(referenceUv * vec2(uRawSize))));
            ivec2 q = (p / 2) * 2;
            float first = 0.0; float second = 0.0;
            for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                float v = normalizedAt(q + ivec2(x, y));
                if (v >= first) { second = first; first = v; }
                else if (v > second) second = v;
            }
            return vec2(first, second);
        }
        bool highlightCell(ivec2 tile) {
            vec2 flowUv = (vec2(tile) + vec2(0.5)) / vec2(uGridSize);
            vec2 safeScale = max(abs(uFlowScaleOffset.xy), vec2(1.0e-6));
            vec2 referenceCenter = (flowUv - uFlowScaleOffset.zw) / safeScale;
            vec2 referenceStep = (vec2(1.0) / vec2(uGridSize)) / safeScale;
            for (int sy = -1; sy <= 1; ++sy) for (int sx = -1; sx <= 1; ++sx) {
                vec2 uv = clamp(referenceCenter + vec2(float(sx), float(sy)) * referenceStep * 0.33,
                    vec2(0.0), vec2(1.0));
                vec2 top = topTwoAt(uv);
                if (top.x >= 0.98 || top.y >= uRegionFloor) return true;
            }
            return false;
        }
        vec4 geometryAt(ivec2 p) { return texelFetch(uCurrent, clampGrid(p), 0); }
        vec2 rawFlow(vec4 g) { return g.xy * vec2(uRawSize); }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            vec4 current = geometryAt(tile);
            bool inHighlight = highlightCell(tile);
            vec2 resolvedFlow = rawFlow(current);
            float geometryTrust = current.z >= 0.5 ? 1.0 : 0.0;
            float boundaryTrust = current.w >= 0.5 ? 1.0 : 0.0;

            if (geometryTrust < 0.5 && inHighlight) {
                int bestSupport = 0;
                int secondSupport = 0;
                vec2 best = vec2(0.0);
                for (int hy = -1; hy <= 1; ++hy) for (int hx = -1; hx <= 1; ++hx) {
                    vec4 hGeom = geometryAt(tile + ivec2(hx, hy));
                    if (hGeom.z < 0.5) continue;
                    vec2 h = rawFlow(hGeom);
                    int support = 0;
                    for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                        vec4 g = geometryAt(tile + ivec2(x, y));
                        if (g.z >= 0.5 && length(rawFlow(g) - h) <= uConsensusPixels) support += 1;
                    }
                    if (support > bestSupport) { secondSupport = bestSupport; bestSupport = support; best = h; }
                    else if (support > secondSupport && length(h - best) > uConsensusPixels) secondSupport = support;
                }
                if (bestSupport >= 2 && bestSupport > secondSupport) {
                    vec2 sum = vec2(0.0);
                    int count = 0;
                    for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                        vec4 g = geometryAt(tile + ivec2(x, y));
                        if (g.z >= 0.5 && length(rawFlow(g) - best) <= uConsensusPixels) {
                            sum += rawFlow(g); count += 1;
                        }
                    }
                    if (count >= 2) {
                        vec2 meanFlow = sum / float(count);
                        float maxDeviation = 0.0;
                        for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                            vec4 g = geometryAt(tile + ivec2(x, y));
                            if (g.z >= 0.5 && length(rawFlow(g) - best) <= uConsensusPixels)
                                maxDeviation = max(maxDeviation, length(rawFlow(g) - meanFlow));
                        }
                        if (maxDeviation <= uConsensusPixels) {
                            resolvedFlow = meanFlow;
                            geometryTrust = 1.0;
                        }
                    }
                }
            }

            if (geometryTrust >= 0.5 && boundaryTrust < 0.5 && inHighlight) {
                int boundarySupport = 0;
                for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
                    vec4 g = geometryAt(tile + ivec2(x, y));
                    if (g.z >= 0.5 && g.w >= 0.5 &&
                            length(rawFlow(g) - resolvedFlow) <= uConsensusPixels) boundarySupport += 1;
                }
                if (boundarySupport >= 1) boundaryTrust = 1.0;
            }

            oGeometry = geometryTrust >= 0.5
                ? vec4(resolvedFlow / vec2(uRawSize), 1.0, boundaryTrust)
                : vec4(0.0);
        }
    """.trimIndent()

    val shortBoundaryGeometryProbe26600 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uGeometry;
        uniform ivec2 uSize;
        layout(location = 0) out float oGeometryTrust;
        layout(location = 1) out float oBoundaryTrust;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(uSize);
            vec4 g = texture(uGeometry, uv);
            oGeometryTrust = g.z >= 0.99 ? 1.0 : 0.0;
            oBoundaryTrust = g.w >= 0.99 ? 1.0 : 0.0;
        }
    """.trimIndent()

    /* IRIS_26599_EFFECTIVE_SENSOR_LOSS_SHORT_MASK
     * Preserve the exact 26596/26597 literal sensor-code clipping owner, but add a physically
     * grounded non-literal loss owner. RAW is linear: before NORMAL loses information, an aligned
     * SHORT sample scaled by the exact exposure ratio must agree with the same NORMAL CFA phase.
     * A material SHORT>NORMAL deficit therefore proves effective NORMAL highlight loss even when
     * the NORMAL code is a few counts below literal white. Whole-RGB replacement remains one
     * scalar mask. 26600 obtains geometry from a robust boundary-consensus field: the blown core
     * no longer has to pass the poisoned max-range metric, while conflicting motion remains
     * fail-closed. Non-literal recovery additionally requires boundary-radiometric connectivity.
     *
     * oGateStage is telemetry only and never feeds reconstruction. It stores terminal/cumulative
     * progress as stage/7: 1 bright candidate, 2 flow, 3 measurable SHORT, 4 loss detected,
     * 5 SHORT headroom/evidence, 6 region/direct radiometric trust, 7 non-zero final handoff.
     */
    val shortRestoreMask26596 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReferenceRaw;
        uniform highp usampler2D uShortRaw;
        uniform sampler2D uBoundaryGeometry;
        uniform ivec2 uRawSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uFlowScaleOffset;
        uniform vec4 uReferenceBlackByPhase;
        uniform vec4 uShortBlackByPhase;
        uniform float uWhiteLevel;
        uniform float uExposureRatio;
        uniform float uReferenceNearClipThreshold;
        uniform float uShortHeadroomThreshold;
        uniform float uEffectiveSignalFloor;
        uniform float uEffectiveLossStart;
        uniform float uEffectiveLossFull;
        uniform float uSevereSingleReferenceFloor;
        uniform float uSevereSingleLossStart;
        uniform float uSevereSingleLossFull;
        layout(location = 0) out float oMask;
        layout(location = 1) out float oGateStage;

        ivec2 clampRaw(ivec2 p) { return clamp(p, ivec2(0), uRawSize - ivec2(1)); }
        int phaseAt(ivec2 p) { return (p.x & 1) + 2 * (p.y & 1); }
        ivec2 phaseOffset(int phase) { return ivec2(phase & 1, (phase >> 1) & 1); }
        float blackAt(vec4 b, int phase) {
            if (phase == 0) return b.x;
            if (phase == 1) return b.y;
            if (phase == 2) return b.z;
            return b.w;
        }
        float rawAt(highp usampler2D t, ivec2 p) {
            return float(texelFetch(t, clampRaw(p), 0).r);
        }
        float normalizedRaw(float raw, float black) {
            return max(raw - black, 0.0) / max(uWhiteLevel - black, 1.0);
        }
        float normalizedAt(highp usampler2D t, ivec2 p, vec4 blackByPhase) {
            ivec2 q = clampRaw(p);
            return normalizedRaw(rawAt(t, q), blackAt(blackByPhase, phaseAt(q)));
        }
        ivec2 phaseGridSize(int phase) {
            ivec2 off = phaseOffset(phase);
            return max((uRawSize - off + ivec2(1)) / 2, ivec2(1));
        }
        ivec2 phaseSamplePixel(int phase, ivec2 gridP) {
            ivec2 off = phaseOffset(phase);
            ivec2 size = phaseGridSize(phase);
            return 2 * clamp(gridP, ivec2(0), size - ivec2(1)) + off;
        }
        vec4 samePhaseSupport(highp usampler2D t, vec2 rawCenter, int phase, vec4 blackByPhase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 g = (rawCenter - origin) * 0.5;
            ivec2 g0 = ivec2(floor(g));
            ivec2 p00 = phaseSamplePixel(phase, g0);
            ivec2 p10 = phaseSamplePixel(phase, g0 + ivec2(1, 0));
            ivec2 p01 = phaseSamplePixel(phase, g0 + ivec2(0, 1));
            ivec2 p11 = phaseSamplePixel(phase, g0 + ivec2(1, 1));
            float a = normalizedRaw(rawAt(t, p00), blackAt(blackByPhase, phase));
            float b = normalizedRaw(rawAt(t, p10), blackAt(blackByPhase, phase));
            float c = normalizedRaw(rawAt(t, p01), blackAt(blackByPhase, phase));
            float d = normalizedRaw(rawAt(t, p11), blackAt(blackByPhase, phase));
            return vec4(a, b, c, d);
        }
        float bilinearSamePhase(vec4 v, vec2 rawCenter, int phase) {
            vec2 origin = vec2(phaseOffset(phase)) + vec2(0.5);
            vec2 f = fract((rawCenter - origin) * 0.5);
            return mix(mix(v.x, v.y, f.x), mix(v.z, v.w, f.x), f.y);
        }
        float samePhasePeak(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        int sensorClippedPhaseCount(ivec2 p) {
            ivec2 q = (clampRaw(p) / 2) * 2;
            float clipCode = uWhiteLevel - 0.5;
            int count = 0;
            for (int phase = 0; phase < 4; ++phase)
                count += rawAt(uReferenceRaw, q + phaseOffset(phase)) >= clipCode ? 1 : 0;
            return count;
        }
        vec4 referenceQuadNormalized(ivec2 referenceQuad) {
            vec4 v = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase)
                v[phase] = normalizedAt(
                    uReferenceRaw, referenceQuad + phaseOffset(phase), uReferenceBlackByPhase);
            return v;
        }
        float highestVec4(vec4 v) { return max(max(v.x, v.y), max(v.z, v.w)); }
        float secondHighestVec4(vec4 v) {
            float first = 0.0; float second = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float signal = v[phase];
                if (signal >= first) { second = first; first = signal; }
                else if (signal > second) second = signal;
            }
            return second;
        }
        bool shortQuadEvidence(ivec2 referenceQuad, vec2 flowRawPixels,
                out vec4 shortNormalized, out vec4 shortSupportPeak) {
            shortNormalized = vec4(0.0);
            shortSupportPeak = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase) {
                ivec2 rp = referenceQuad + phaseOffset(phase);
                vec2 shortCenter = vec2(rp) + vec2(0.5) + flowRawPixels;
                vec4 support = samePhaseSupport(uShortRaw, shortCenter, phase, uShortBlackByPhase);
                float supportPeak = samePhasePeak(support);
                shortSupportPeak[phase] = supportPeak;
                if (supportPeak >= 0.995) return false;
                shortNormalized[phase] = bilinearSamePhase(support, shortCenter, phase) * uExposureRatio;
            }
            return true;
        }
        bool everyClippedReferencePhaseExplained(ivec2 referenceQuad, vec4 shortNormalized,
                vec4 shortSupportPeak) {
            float clipCode = uWhiteLevel - 0.5;
            int clipped = 0;
            for (int phase = 0; phase < 4; ++phase) {
                if (rawAt(uReferenceRaw, referenceQuad + phaseOffset(phase)) >= clipCode) {
                    clipped += 1;
                    if (shortSupportPeak[phase] >= uShortHeadroomThreshold) return false;
                    if (shortNormalized[phase] < 0.90) return false;
                }
            }
            return clipped >= 1;
        }
        vec4 effectiveLossByPhase(vec4 referenceNormalized, vec4 shortNormalized) {
            vec4 outLoss = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(shortNormalized[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float signalGate = smoothstep(uEffectiveSignalFloor, 0.92, predicted);
                outLoss[phase] = signalGate *
                    smoothstep(uEffectiveLossStart, uEffectiveLossFull, relativeLoss);
            }
            return outLoss;
        }
        vec4 phaseScopedHeadroom(vec4 evidence, vec4 shortSupportPeak) {
            vec4 result = vec4(0.0);
            for (int phase = 0; phase < 4; ++phase)
                result[phase] = shortSupportPeak[phase] < uShortHeadroomThreshold
                    ? evidence[phase] : 0.0;
            return result;
        }
        float severeSingleLossWeight(vec4 referenceNormalized, vec4 shortNormalized,
                vec4 shortSupportPeak) {
            float best = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(shortNormalized[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float referenceGate = smoothstep(
                    uSevereSingleReferenceFloor, uReferenceNearClipThreshold, reference);
                float signalGate = smoothstep(uEffectiveSignalFloor, 0.92, predicted);
                float lossGate = smoothstep(
                    uSevereSingleLossStart, uSevereSingleLossFull, relativeLoss);
                float headroom = shortSupportPeak[phase] < uShortHeadroomThreshold ? 1.0 : 0.0;
                best = max(best, referenceGate * signalGate * lossGate * headroom);
            }
            return best;
        }
        void stage(int value) { oGateStage = float(value) / 7.0; }
        void main() {
            oMask = 0.0;
            stage(0);
            vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
            ivec2 referenceP = clampRaw(ivec2(floor(referenceUv * vec2(uRawSize))));
            ivec2 referenceQuad = (clampRaw(referenceP) / 2) * 2;
            vec4 referenceNormalized = referenceQuadNormalized(referenceQuad);
            float referenceSecond = secondHighestVec4(referenceNormalized);
            bool actualSensorLoss = sensorClippedPhaseCount(referenceP) >= 1;
            if (!actualSensorLoss && referenceSecond < 0.70) return;
            stage(1);

            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 boundaryGeometry = texture(uBoundaryGeometry, flowUv);
            if (boundaryGeometry.z < 0.99) return;
            stage(2);
            vec2 flowRawPixels = boundaryGeometry.xy * vec2(uRawSize);
            vec4 shortNormalized = vec4(0.0);
            vec4 shortSupportPeak = vec4(0.0);
            if (!shortQuadEvidence(referenceQuad, flowRawPixels, shortNormalized, shortSupportPeak)) return;
            stage(3);

            if (actualSensorLoss) {
                stage(4);
                if (!everyClippedReferencePhaseExplained(
                        referenceQuad, shortNormalized, shortSupportPeak)) return;
                stage(5);
                stage(6); /* Literal sensor loss + same-phase SHORT proof is direct radiometry. */
                oMask = 1.0;
                stage(7);
                return;
            }

            vec4 rawLossEvidence = effectiveLossByPhase(referenceNormalized, shortNormalized);
            float twoPhaseRawLoss = secondHighestVec4(rawLossEvidence);
            float severeRawLoss = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(shortNormalized[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                severeRawLoss = max(severeRawLoss,
                    smoothstep(uSevereSingleReferenceFloor, uReferenceNearClipThreshold, reference) *
                    smoothstep(uEffectiveSignalFloor, 0.92, predicted) *
                    smoothstep(uSevereSingleLossStart, uSevereSingleLossFull, relativeLoss));
            }
            if (max(twoPhaseRawLoss, severeRawLoss) <= 0.0) return;
            stage(4);

            vec4 headroomLossEvidence = phaseScopedHeadroom(rawLossEvidence, shortSupportPeak);
            float twoPhaseHandoff = secondHighestVec4(headroomLossEvidence);
            float severeSingleHandoff = severeSingleLossWeight(
                referenceNormalized, shortNormalized, shortSupportPeak);
            float effectiveHandoff = max(twoPhaseHandoff, severeSingleHandoff);
            if (effectiveHandoff <= 0.0) return;
            stage(5);
            if (boundaryGeometry.w < 0.99) return;
            stage(6);
            oMask = clamp(effectiveHandoff, 0.0, 1.0);
            if (oMask > 0.0) stage(7);
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
    /* IRIS_26601_SHORT_COMMON_SABRE_VGN_OWNERSHIP
     * The 26600 device fix proved SHORT geometry, but late post-VGN RGB compositing exposed
     * independently reconstructed CFA/color edges at bright material boundaries. SHORT now enters
     * the same homogeneous Sabre accumulator domain as NORMAL/LONG before dehomogenize/Resolve/VGN.
     * uShortMask remains the exact 26600 fail-closed evidence authority. This is a binary evidence
     * ownership switch, never an RGB alpha blend: all three homogeneous color/weight channels move
     * together, while temporal coverage/noise and DNG remain NORMAL/LONG-owned elsewhere.
     */
    val shortAccumulatorOwnership26601 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uNormalColorAndRWeight;
        uniform sampler2D uNormalWeightsGb;
        uniform sampler2D uShortColorAndRWeight;
        uniform sampler2D uShortWeightsGb;
        uniform sampler2D uShortMask;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec2 oWeightsGb;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            vec4 normalColor = texelFetch(uNormalColorAndRWeight, p, 0);
            vec2 normalGb = texelFetch(uNormalWeightsGb, p, 0).rg;
            vec4 shortColor = texelFetch(uShortColorAndRWeight, p, 0);
            vec2 shortGb = texelFetch(uShortWeightsGb, p, 0).rg;
            float evidence = texelFetch(uShortMask, p, 0).r;
            float minimumShortWeight = min(shortColor.a, min(shortGb.r, shortGb.g));
            float shortOwner = (evidence > 0.0 && minimumShortWeight > 1.0e-7) ? 1.0 : 0.0;
            oColorAndRWeight = mix(normalColor, shortColor, shortOwner);
            oWeightsGb = mix(normalGb, shortGb, shortOwner);
        }
    """.trimIndent()

    /* IRIS_26602_SHORT_FULL_NORMAL_PROTECTION
     * SHORT must not merely arrive before Resolve/VGN; it must inherit the same Sabre
     * photometric/unblocker/dilated-frame-weight protection that NORMAL uses. The reference guide
     * cannot remain measurable inside a clipped core, so the measured NORMAL-equivalent protection
     * is seeded only on a radiometrically valid 26600 boundary and then propagated through that
     * already-proven motion-consensus geometry. A separate NORMAL-only temporal coverage map keeps
     * LONG support from validating SHORT.
     */
    val shortProtectionSeed26602 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uBoundaryGeometry;
        uniform sampler2D uFrameWeight;
        uniform sampler2D uNormalCoverage;
        uniform ivec2 uGridSize;
        layout(location = 0) out float oProtection;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(p, uGridSize))) { oProtection = 0.0; return; }
            vec2 uv = (vec2(p) + vec2(0.5)) / vec2(uGridSize);
            vec4 g = texelFetch(uBoundaryGeometry, p, 0);
            float measured = texture(uFrameWeight, uv).r;
            float normalSupport = texture(uNormalCoverage, uv).r;
            bool accepted = g.z >= 0.5 && g.w >= 0.5 &&
                measured > 0.08 && normalSupport > (0.5 / 255.0);
            oProtection = accepted ? measured : 0.0;
        }
    """.trimIndent()

    /* Protection never invents trust. It can only carry an already-measured NORMAL-equivalent
     * Sabre weight through the exact 26600 coherent-flow/boundary-connected region. Confidence is
     * non-increasing: propagation uses the weakest compatible supporting neighbour.
     */
    val shortProtectionPropagate26602 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uCurrent;
        uniform sampler2D uBoundaryGeometry;
        uniform ivec2 uGridSize;
        uniform ivec2 uRawSize;
        uniform float uConsensusPixels;
        layout(location = 0) out float oProtection;
        ivec2 clampGrid(ivec2 p) { return clamp(p, ivec2(0), uGridSize - ivec2(1)); }
        vec4 geom(ivec2 p) { return texelFetch(uBoundaryGeometry, clampGrid(p), 0); }
        float protect(ivec2 p) { return texelFetch(uCurrent, clampGrid(p), 0).r; }
        vec2 rawFlow(vec4 g) { return g.xy * vec2(uRawSize); }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(p, uGridSize))) { oProtection = 0.0; return; }
            float existing = protect(p);
            if (existing > 0.0) { oProtection = existing; return; }
            vec4 center = geom(p);
            if (center.z < 0.5 || center.w < 0.5) { oProtection = 0.0; return; }
            vec2 centerFlow = rawFlow(center);
            int support = 0;
            float weakest = 1.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    if (x == 0 && y == 0) continue;
                    ivec2 q = clampGrid(p + ivec2(x, y));
                    float w = protect(q);
                    vec4 g = geom(q);
                    if (w <= 0.0 || g.z < 0.5 || g.w < 0.5) continue;
                    if (length(rawFlow(g) - centerFlow) > uConsensusPixels) continue;
                    weakest = min(weakest, w);
                    support += 1;
                }
            }
            oProtection = support >= 1 ? weakest : 0.0;
        }
    """.trimIndent()

    /* IRIS_26602_BAYER_QUAD_COHERENT_SHORT_VALIDITY
     * All four positions of one physical Bayer quad receive one SHORT confidence. This prevents
     * neighbouring CFA phases from independently choosing bracket ownership at a material edge.
     * The candidate mask remains the exact 26600 sensor-loss/headroom authority; protection can
     * only reduce it.
     */
    val shortProtectedMask26602 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uCandidateMask;
        uniform sampler2D uProtection;
        uniform ivec2 uOutputSize;
        layout(location = 0) out float oMask;
        ivec2 clampOutput(ivec2 p) { return clamp(p, ivec2(0), uOutputSize - ivec2(1)); }
        float candidateAt(ivec2 p) { return texelFetch(uCandidateMask, clampOutput(p), 0).r; }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            ivec2 q = (clampOutput(p) / 2) * 2;
            float candidate = min(
                min(candidateAt(q), candidateAt(q + ivec2(1, 0))),
                min(candidateAt(q + ivec2(0, 1)), candidateAt(q + ivec2(1, 1)))
            );
            vec2 quadUv = (vec2(q) + vec2(1.0)) / vec2(uOutputSize);
            float protection = texture(uProtection, quadUv).r;
            float protectionGate = smoothstep(0.08, 0.16, protection);
            oMask = clamp(candidate * protectionGate, 0.0, 1.0);
        }
    """.trimIndent()

    /* IRIS_26602_PROTECTED_SHORT_COMMON_ACCUMULATOR
     * Fuse dehomogenized NORMAL/LONG and protected SHORT evidence before the one Resolve/VGN pass.
     * The same scalar confidence applies to R/G/B; NORMAL/LONG accumulated weights remain the
     * temporal/noise/support authority. This removes 26601's binary accumulator replacement while
     * retaining valid SHORT radiometry where NORMAL is censored.
     */
    val shortProtectedAccumulatorFuse26602 = """
        #version 300 es
        precision highp float;
        uniform sampler2D uNormalColorAndRWeight;
        uniform sampler2D uNormalWeightsGb;
        uniform sampler2D uShortColorAndRWeight;
        uniform sampler2D uShortWeightsGb;
        uniform sampler2D uProtectedMask;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec2 oWeightsGb;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            vec4 normalColor = texelFetch(uNormalColorAndRWeight, p, 0);
            vec2 normalGb = texelFetch(uNormalWeightsGb, p, 0).rg;
            vec4 shortColor = texelFetch(uShortColorAndRWeight, p, 0);
            vec2 shortGb = texelFetch(uShortWeightsGb, p, 0).rg;
            vec3 normalWeight = vec3(normalColor.a, normalGb);
            vec3 shortWeight = vec3(shortColor.a, shortGb);
            float minimumNormalWeight = min(normalWeight.r, min(normalWeight.g, normalWeight.b));
            float minimumShortWeight = min(shortWeight.r, min(shortWeight.g, shortWeight.b));
            float confidence = texelFetch(uProtectedMask, p, 0).r;
            if (minimumNormalWeight <= 1.0e-7 || minimumShortWeight <= 1.0e-7) confidence = 0.0;
            vec3 normalMean = normalColor.rgb / max(normalWeight, vec3(1.0e-7));
            vec3 shortMean = shortColor.rgb / max(shortWeight, vec3(1.0e-7));
            vec3 fusedMean = mix(normalMean, shortMean, clamp(confidence, 0.0, 1.0));
            oColorAndRWeight = vec4(fusedMean * normalWeight, normalColor.a);
            oWeightsGb = normalGb;
        }
    """.trimIndent()

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
            mat3 sourceValidity = mat3(1.0);
            float headroomStart=max(1.0,uSourceClippingPoint*0.9925);
            for (int sx=0;sx<3;++sx) {
                for (int sy=0;sy<3;++sy) {
                    float sampleConfidence=1.0-smoothstep(
                        headroomStart,max(headroomStart+1.0e-4,uSourceClippingPoint),
                        bayerValue[sx][sy]);
                    sourceValidity[sx][sy]=sampleConfidence;
                    sourceNeighborhoodConfidence=min(
                        sourceNeighborhoodConfidence,sampleConfidence);
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
            validAccumulatedWeights = vec3(
                validReorderedWeights.r,
                validReorderedWeights.g + validReorderedWeights.b,
                validReorderedWeights.a
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
            vec3 validAccumulatedWeight = vec3(0.0);
            float sourceNeighborhoodConfidence = 1.0;
            sampleNeighborhoodRbf(
                sampleUv,
                covariance,
                accumulatedColor,
                accumulatedWeight,
                sourceNeighborhoodConfidence,
                validAccumulatedWeight
            );
            float frameWeight = uUseFrameWeight != 0
                ? texture(uRejection, referenceUv).r
                : 1.0;
            if (uSourceClipGuard != 0) {
                frameWeight *= mix(
                    uSourceClippedWeight,1.0,
                    clamp(sourceNeighborhoodConfidence,0.0,1.0));
            }
            accumulatedColor *= frameWeight;
            accumulatedWeight *= frameWeight;
            validAccumulatedWeight *= frameWeight;
            oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);
            oWeightsGb = accumulatedWeight.gb;
            oValidWeights = vec4(
                validAccumulatedWeight / max(uValidityWeightScale, 1.0e-6), 0.0);
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
            vec2 flowRangeBayerQuads = maximumFlow - minimumFlow;
            vec2 normalizedRange =
                flowRangeBayerQuads /
                max(uFlowNormalizationSize, vec2(1.0));
            float localFlowVariation = length(normalizedRange);
            /* IRIS_26606_COHERENT_LOCAL_AFFINE_RESIDUAL
             * z remains Sabre's exact normalized 3x3 variation for ordinary rejection. w is no
             * longer that range expressed in RAW pixels. Four independent opposite-neighbor
             * averages predict the center of any first-order affine flow field exactly; the
             * second-smallest prediction residual is robust to one bad neighbor while still
             * rejecting an isolated bad center/discontinuity. Edge cells fail closed for SHORT.
             */
            float localAffineResidualRawPixels = 4.0;
            bool interior = tile.x > 0 && tile.y > 0 &&
                tile.x + 1 < uGridSize.x && tile.y + 1 < uGridSize.y;
            if (interior) {
                vec2 horizontalPrediction = 0.5 * (
                    flowAt(tile + ivec2(-1, 0)) + flowAt(tile + ivec2(1, 0)));
                vec2 verticalPrediction = 0.5 * (
                    flowAt(tile + ivec2(0, -1)) + flowAt(tile + ivec2(0, 1)));
                vec2 diagonalPredictionA = 0.5 * (
                    flowAt(tile + ivec2(-1, -1)) + flowAt(tile + ivec2(1, 1)));
                vec2 diagonalPredictionB = 0.5 * (
                    flowAt(tile + ivec2(-1, 1)) + flowAt(tile + ivec2(1, -1)));
                float r0 = length(flowPixels - horizontalPrediction);
                float r1 = length(flowPixels - verticalPrediction);
                float r2 = length(flowPixels - diagonalPredictionA);
                float r3 = length(flowPixels - diagonalPredictionB);
                float pairMin0 = min(r0, r1);
                float pairMax0 = max(r0, r1);
                float pairMin1 = min(r2, r3);
                float pairMax1 = max(r2, r3);
                float secondResidualBayerQuads = min(
                    max(pairMin0, pairMin1), min(pairMax0, pairMax1));
                localAffineResidualRawPixels = 2.0 * secondResidualBayerQuads;
            }
            oFlow = vec4(uvFlow, localFlowVariation, localAffineResidualRawPixels);
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
            float sourceNeighborhoodConfidence = 1.0;
            float headroomStart=max(1.0,uSourceClippingPoint*0.9925);
            for (int sx = 0; sx < 3; ++sx) {
                for (int sy = 0; sy < 3; ++sy) {
                    float sampleConfidence=1.0-smoothstep(
                        headroomStart,max(headroomStart+1.0e-4,uSourceClippingPoint),
                        bayerValue[sx][sy]);
                    sourceNeighborhoodConfidence=min(
                        sourceNeighborhoodConfidence,sampleConfidence);
                }
            }
            oAccumulatedWeight=texture(uRejection,referenceUv).r
                *clamp(sourceNeighborhoodConfidence,0.0,1.0)/uAccumulatedWeightScale;
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

    /* IRIS_26611_HDR_INDEPENDENT_VGN_COLOR_DIRECTION
     * Below white this is exactly the existing normalized camera RGB. Above white the physical
     * RGB vector is divided by one scalar max-RGB magnitude before RGBA16UI quantization. VGN thus
     * sees the true color direction without per-channel clipping, while the unclipped physical
     * magnitude remains in the separate RGBA16F carrier for scalar restoration after cleanup. */
    val outputTransformHdrDirectionUint16 = """
        #version 300 es
        $outputTransformBody
        layout(location = 0) out highp uvec4 oResolved;
        float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            vec3 physical = max(transformOutput(p), vec3(0.0));
            float magnitude = max(max3(physical), 1.0);
            vec3 directionDomain = clamp(physical / magnitude, 0.0, 1.0);
            oResolved = uvec4(uvec3(round(directionDomain * 65535.0)), 65535u);
        }
    """.trimIndent()


    /* IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE
     * VGN-cleaned RGB is the sole post-clean hue/chroma authority. The old physical RGB vector may
     * contribute exactly one scalar: its max-RGB HDR magnitude, which is also the source-domain
     * guide consumed by the validated 26610 rendition. Below white the output remains exactly VGN.
     * Above white, one scalar magnitude multiplies the cleaned direction; no pre-clean R/G/B excess
     * can cross the cleanup boundary independently, so dirty magenta/cyan cannot be resurrected. */
    val restoreExtendedHdrAfterVgn = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform sampler2D uPhysicalHdr;
        uniform highp usampler2D uVgnNormalized;
        uniform ivec2 uImageSize;
        layout(location = 0) out vec4 oHdr;
        float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uImageSize - ivec2(1));
            vec3 physical = max(texelFetch(uPhysicalHdr, p, 0).rgb, vec3(0.0));
            float physicalMagnitude = max3(physical);
            vec3 cleaned = max(vec3(texelFetch(uVgnNormalized, p, 0).rgb) / 65535.0, vec3(0.0));
            vec3 restored = cleaned;
            if (physicalMagnitude > 1.0) {
                float cleanedMagnitude = max3(cleaned);
                vec3 cleanedDirection = cleanedMagnitude > 1.0e-6 ?
                    cleaned / cleanedMagnitude : vec3(1.0);
                restored = cleanedDirection * physicalMagnitude;
            }
            oHdr = vec4(max(restored, vec3(0.0)), 1.0);
        }
    """.trimIndent()

    /* IRIS_26605_EXTENDED_HDR_TELEMETRY_PROBE
     * Sparse fixed-size readback only; never participates in reconstruction.
     */
    val extendedHdrTelemetryProbe = """
        #version 300 es
        precision highp float;
        uniform sampler2D uHdr;
        uniform ivec2 uProbeSize;
        layout(location = 0) out vec4 oSample;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(uProbeSize);
            oSample = vec4(texture(uHdr, clamp(uv, vec2(0.0), vec2(1.0))).rgb, 1.0);
        }
    """.trimIndent()
}
