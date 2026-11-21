package com.hinnka.mycamera.processor

/**
 * 26972 C-owned GPU Sabre merge stages transcribed from the pinned bjzhou
 * PhotonCamera 1.29.0 `GlesMgcRawSabreShaders.kt` (Git blob
 * 78c52d3afaf1be05a34ca94078a101fa81af7edc), commit
 * 0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * This object is NOT linked to the historical Iris GPU engine and no shader
 * here is a functional fallback. It supplies the real donor GLSL source for
 * C's implemented private streaming GL merge driver; C remains
 * production-disabled until Android compilation and device testing.
 */
internal object Iris26972CDonorSabreMergeShaders {
    val extractBayer = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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
            oExtractedBayer = vec4(
                rawAt(p),
                rawAt(p + ivec2(1, 0)),
                rawAt(p + ivec2(0, 1)),
                rawAt(p + ivec2(1, 1))
            ) + vec4(1.0e-4);
        }
    """.trimIndent()

    /** Native MGC Sabre 3-channel RBF accumulator and independent R/G/B weights. */
    val merge = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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

        // The donor uses `packed` here, a reserved GLSL identifier. Rename the
        // local argument only; the arithmetic and donor merge contract are identical.
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

    val copyMask = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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
        precision highp sampler2D;
        uniform sampler2D uSource;
        layout(location = 0) out float oWeight;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            oWeight = texelFetch(uSource, p, 0).a;
        }
    """.trimIndent()

    val dehomogenize = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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
}
