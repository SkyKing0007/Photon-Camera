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
            color *= frameWeight;
            weights *= frameWeight;
            oColorAndRWeight = vec4(color, weights.r);
            oWeightsGb = weights.gb;

            oPhaseOccupancy = vec4(0.0);
            if (frameWeight > 0.08 && sourceRawPeak < uRawClipThreshold) {
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
        uniform sampler2D uNativeVgnGuide;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputFullSize;
        uniform ivec2 uGuideSize;
        layout(location = 0) out vec4 oRenderRgb;

        /* IRIS_26568_FUSED_SABRE_GUIDED_TRUE2X_RENDER
         * This is the exact 26567 CPU publication contract moved to the GPU while all evidence is
         * resident. Direct-CFA RGB may influence only one scalar detail factor; native Sabre/VGN
         * remains the RGB/chroma/highlight owner. The +/-0.25 EV cap and all confidence thresholds
         * are intentionally unchanged.
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
        void main() {
            ivec2 localP = ivec2(gl_FragCoord.xy);
            ivec2 globalP = uOutputOrigin + localP;
            vec3 directRgb = texelFetch(uDirectRgb, localP, 0).rgb;
            vec3 guideRgb = irisGuide(globalP);
            ivec2 globalBlock = (globalP / 2) * 2;
            ivec2 block = globalBlock - uOutputOrigin;
            vec3 b00 = texelFetch(uDirectRgb, block, 0).rgb;
            vec3 b10 = texelFetch(uDirectRgb, block + ivec2(1, 0), 0).rgb;
            vec3 b01 = texelFetch(uDirectRgb, block + ivec2(0, 1), 0).rgb;
            vec3 b11 = texelFetch(uDirectRgb, block + ivec2(1, 1), 0).rgb;
            float directY = max(irisLuma(directRgb), 0.0);
            float lowY = max(0.25 * (irisLuma(b00) + irisLuma(b10) + irisLuma(b01) + irisLuma(b11)), 0.0);
            float guideY = max(irisLuma(guideRgb), 0.0);
            vec4 phases = texelFetch(uPhaseOccupancy, localP, 0);
            int phaseCount = (phases.r > 0.0 ? 1 : 0) + (phases.g > 0.0 ? 1 : 0) +
                             (phases.b > 0.0 ? 1 : 0) + (phases.a > 0.0 ? 1 : 0);
            float phaseGate = phaseCount >= 4 ? 1.0 : (phaseCount == 3 ? 0.68 : (phaseCount == 2 ? 0.32 : 0.0));
            float signalGate = irisSmooth01((guideY - 0.020) / 0.080);
            float highlightGate = 1.0 - irisSmooth01((max(irisPeak(directRgb), irisPeak(guideRgb)) - 0.72) / 0.20);
            vec3 dc = irisChroma(directRgb);
            vec3 gc = irisChroma(guideRgb);
            float chromaDistance = length(dc - gc);
            float chromaGate = 1.0 - irisSmooth01((chromaDistance - 0.015) / 0.055);
            float agreement = abs(log2((lowY + 0.01) / (guideY + 0.01)));
            float agreementGate = 1.0 - irisSmooth01((agreement - 0.08) / 0.27);
            float confidence = clamp(phaseGate * signalGate * highlightGate * chromaGate * agreementGate, 0.0, 1.0);
            float rawLog = clamp(log2((directY + 0.004) / (lowY + 0.004)), -0.25, 0.25);
            float factor = exp2(rawLog * confidence);
            /* Alpha is diagnostic-only phase count. RGB publication remains exactly guide*factor.
             * The host harvests this alpha from the already-required RGBA16F render readback,
             * eliminating the old second full-resolution RGBA8 phase readback.
             */
            oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount));
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
