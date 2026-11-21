package com.hinnka.mycamera.processor

/**
 * C-only original bjzhou 1.29.0 RAW Sabre Bayer guide/covariance shader.
 * Source: GlesMgcRawSabreShaders.kt, pinned Git blob
 * 78c52d3afaf1be05a34ca94078a101fa81af7edc.
 */
internal object Iris26972CDonorSabreGuideShaders {
    val guideAndCovariance = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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
        // Exact Sabre contract: x is a 0/1 switch; the remaining components are unused.
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
}
