package com.hinnka.mycamera.processor

/**
 * GLES stages for the MGC-compatible Spatial RAW pipeline.
 *
 * The guide, rejection, dilation and merge equations below retain the embedded GLSL equations and
 * constants. The original program first extracts RAW16 into a half-resolution Bayer texture.
 * Photon reads R16UI directly; the RGB branch reconstructs jointly from native CFA observations.
 */
internal object C26986GlesIris26521SpatialRgbShaders {
    /* IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_MATH
     * IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE
     * Same live c4ff transport ABI; independently authored edge/color reconstruction equations.
     */
    val guide = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uGuideSize;
        uniform int uCfaPattern;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform sampler2D uNoiseEstimates;
        uniform vec4 uNoiseTextureScaleBias;
        uniform float uGreenClippingPoint;
        uniform float uForceReferenceColorRgb;
        out vec4 oGuide;

        vec4 rawQuad(ivec2 quad) {
            ivec2 p = clamp(quad * 2, ivec2(0), uRawSize - ivec2(2));
            float p00 = float(texelFetch(uRaw, p, 0).r);
            float p10 = float(texelFetch(uRaw, p + ivec2(1, 0), 0).r);
            float p01 = float(texelFetch(uRaw, p + ivec2(0, 1), 0).r);
            float p11 = float(texelFetch(uRaw, p + ivec2(1, 1), 0).r);
            vec4 raw;
            if (uCfaPattern == 0) raw = vec4(p00, p10, p01, p11);
            else if (uCfaPattern == 1) raw = vec4(p10, p00, p11, p01);
            else if (uCfaPattern == 2) raw = vec4(p01, p11, p00, p10);
            else raw = vec4(p11, p01, p10, p00);
            return raw * uGains + uBlackLevelsTimesGains;
        }

        float luma(vec3 rgb) {
            return dot(rgb, vec3(0.25, 0.5, 0.25));
        }

        float kernelWeight(int offset) {
            return offset == 0 ? 0.5 : 0.25;
        }

        void main() {
            ivec2 center = ivec2(gl_FragCoord.xy);
            vec3 m0Rgb = vec3(0.0);
            vec3 m1Rgb = vec3(0.0);
            float m0Green = 0.0;
            float m1Green = 0.0;
            vec3 averageRgb = vec3(0.0);
            float centerGreen = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    vec4 rggb = rawQuad(center * 2 + ivec2(x, y));
                    vec3 rgb = vec3(rggb.x, 0.5 * (rggb.y + rggb.z), rggb.w);
                    averageRgb += rgb * kernelWeight(x) * kernelWeight(y);
                    if (x == 0 && y == 0) centerGreen = rgb.y;
                    m0Rgb += rgb;
                    m1Rgb += rgb * rgb;
                    m0Green += rggb.y + rggb.z;
                    m1Green += rggb.y * rggb.y + rggb.z * rggb.z;
                }
            }
            m0Rgb /= 9.0;
            m1Rgb /= 9.0;
            vec3 rgbVariance = max(vec3(0.0), m1Rgb - m0Rgb * m0Rgb);
            m0Green /= 18.0;
            m1Green /= 18.0;
            float greenVariance = max(0.0, m1Green - m0Green * m0Green);
            float averageLuma = luma(averageRgb);
            vec2 noiseUv =
                vec2(averageLuma, 1.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            float greenVarianceNoise =
                2.0 * texture(uNoiseEstimates, noiseUv).y;
            vec3 referenceColor;
            float referenceVariance;
            if (greenVariance > 3.0 * greenVarianceNoise &&
                uForceReferenceColorRgb == 0.0) {
                referenceColor = vec3(averageRgb.x, centerGreen, averageRgb.z);
                referenceVariance = -max(rgbVariance.y, greenVariance);
            } else {
                referenceColor = averageRgb;
                referenceVariance = dot(rgbVariance, vec3(1.0 / 3.0));
            }
            if (centerGreen >= uGreenClippingPoint) {
                referenceColor = vec3(10000.0);
            }
            oGuide = vec4(referenceColor, referenceVariance * 1024.0);
        }
    """.trimIndent()

    /**
     * Precomputes the edge-directed green value at native R/B sites for one RAW tile region.
     * MergeRgb consumes this compact guide instead of repeating eight neighboring RAW fetches
     * for every chroma observation at every super-resolution output sample.
     */
    val rgbChromaGuide = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uRawTextureOrigin;
        uniform ivec2 uRegionOrigin;
        uniform ivec2 uRegionSize;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform int uCfaPattern;
        out float oGreen;

        int canonicalChannel(ivec2 p) {
            int phase = ((p.y & 1) << 1) + (p.x & 1);
            if (uCfaPattern == 0) return phase;
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
            if (phase == 0) return 3;
            if (phase == 1) return 2;
            if (phase == 2) return 1;
            return 0;
        }

        int clampRawCoordinateToPhase(int coordinate, int extent) {
            int phase = coordinate & 1;
            if (phase >= extent) return extent - 1;
            int last = phase + 2 * ((extent - 1 - phase) / 2);
            return clamp(coordinate, phase, last);
        }

        ivec2 clampRawPixelToPhase(ivec2 p) {
            return ivec2(
                clampRawCoordinateToPhase(p.x, uRawSize.x),
                clampRawCoordinateToPhase(p.y, uRawSize.y)
            );
        }

        float gainedRaw(ivec2 globalPixel) {
            int channel = canonicalChannel(globalPixel);
            globalPixel = clampRawPixelToPhase(globalPixel);
            return float(texelFetch(uRaw, globalPixel - uRawTextureOrigin, 0).r) *
                uGains[channel] +
                uBlackLevelsTimesGains[channel];
        }

        /* IRIS_26521_V4_DIRECTIONAL_GREEN */
        float greenAtNonGreen(ivec2 p, float center) {
            float gL = gainedRaw(p + ivec2(-1, 0));
            float gR = gainedRaw(p + ivec2(1, 0));
            float gU = gainedRaw(p + ivec2(0, -1));
            float gD = gainedRaw(p + ivec2(0, 1));
            float cL2 = gainedRaw(p + ivec2(-2, 0));
            float cR2 = gainedRaw(p + ivec2(2, 0));
            float cU2 = gainedRaw(p + ivec2(0, -2));
            float cD2 = gainedRaw(p + ivec2(0, 2));
            float horizontalLinear = 0.5 * (gL + gR);
            float verticalLinear = 0.5 * (gU + gD);
            float horizontalCurvature = 2.0 * center - cL2 - cR2;
            float verticalCurvature = 2.0 * center - cU2 - cD2;
            float horizontalCorrection = clamp(
                0.25 * horizontalCurvature,
                -0.5 * abs(gL - gR),
                0.5 * abs(gL - gR)
            );
            float verticalCorrection = clamp(
                0.25 * verticalCurvature,
                -0.5 * abs(gU - gD),
                0.5 * abs(gU - gD)
            );
            float horizontal = horizontalLinear + horizontalCorrection;
            float vertical = verticalLinear + verticalCorrection;
            float gradientH = abs(gL - gR) + abs(horizontalCurvature);
            float gradientV = abs(gU - gD) + abs(verticalCurvature);
            float gradientSum = max(gradientH + gradientV, 1.0e-7);
            float softHorizontal = gradientV / gradientSum;
            float softEstimate = mix(vertical, horizontal, softHorizontal);
            float directionalEstimate = gradientH <= gradientV ? horizontal : vertical;
            float directionalConfidence = abs(gradientH - gradientV) / gradientSum;
            float directionalMix = smoothstep(0.20, 0.75, directionalConfidence);
            float green = mix(softEstimate, directionalEstimate, directionalMix);
            float nativeMinimum = min(min(gL, gR), min(gU, gD));
            float nativeMaximum = max(max(gL, gR), max(gU, gD));
            return clamp(green, nativeMinimum, nativeMaximum);
        }

        void main() {
            ivec2 local = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(local, uRegionSize))) {
                oGreen = 0.0;
                return;
            }
            ivec2 globalPixel = local + uRegionOrigin;
            float center = gainedRaw(globalPixel);
            int channel = canonicalChannel(globalPixel);
            oGreen = channel == 1 || channel == 2
                ? center
                : greenAtNonGreen(globalPixel, center);
        }
    """.trimIndent()

    /**
     * Structure-adaptive Spatial RGB precision matrix recovered with MergeRgbRaw.
     *
     * MGC originally emitted this beside the guide. It is kept as an independent draw here so the
     * corrected Bayer guide/rejection transport remains byte-for-byte isolated from RGB output.
     */
    val covariance = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uRawTextureOrigin;
        uniform ivec2 uRawTextureSize;
        uniform ivec2 uCovarianceSize;
        uniform ivec2 uCovarianceOrigin;
        uniform ivec2 uCovarianceTextureSize;
        uniform vec4 uBayerPhaseGains;
        uniform vec4 uBayerPhaseBlackTerms;
        uniform vec2 uFigure7Noise;
        uniform float uKDetail;
        uniform float uKDenoise;
        uniform float uDth;
        uniform float uDtr;
        uniform float uKStretch;
        uniform float uKShrink;
        out vec4 oCovariance;

        /* IRIS_26543_ACTIVE_IPOL_FIGURE7_COVARIANCE
         * This is the production GlesIris26521SpatialRgbStacker owner, not the dormant MotionV2
         * asset path. It follows IPOL Alg. 5: GAT -> Bayer-quad grey (RAW/2) -> public 2x2
         * gradients -> 2x2 structure tensor -> linear A/D selection with stretch=4/shrink=2.
         * IPOL produces covariance. Spatial-RGB consumes precision, so invert once here and store
         * direct Pxx/Pyy/Pxy in RGBA16F without the released MGC RGB10_A2 packing/clipping.
         */
        int phaseIndex(ivec2 p) { return ((p.y & 1) << 1) | (p.x & 1); }

        float sensorSample(ivec2 p) {
            p = clamp(p, ivec2(0), uRawSize - ivec2(1));
            int phase = phaseIndex(p);
            ivec2 local = p - uRawTextureOrigin;
            local = clamp(local, ivec2(0), uRawTextureSize - ivec2(1));
            return max(
                float(texelFetch(uRaw, local, 0).r) * uBayerPhaseGains[phase] +
                    uBayerPhaseBlackTerms[phase],
                0.0
            );
        }

        float vst(float x) {
            float alpha = max(uFigure7Noise.x, 1.0e-8);
            float beta = max(uFigure7Noise.y, 0.0);
            float stabilized = max(alpha * x + 0.375 * alpha * alpha + beta, 0.0);
            return 2.0 / alpha * sqrt(stabilized);
        }

        float greyVst(ivec2 q) {
            q = clamp(q, ivec2(0), uCovarianceSize - ivec2(1));
            ivec2 p = q * 2;
            return 0.25 * (
                vst(sensorSample(p)) +
                vst(sensorSample(p + ivec2(1, 0))) +
                vst(sensorSample(p + ivec2(0, 1))) +
                vst(sensorSample(p + ivec2(1, 1)))
            );
        }

        vec2 publicGrad(ivec2 q) {
            float g00 = greyVst(q);
            float g01 = greyVst(q + ivec2(1, 0));
            float g10 = greyVst(q + ivec2(0, 1));
            float g11 = greyVst(q + ivec2(1, 1));
            return vec2(
                0.25 * (-g00 + g01 - g10 + g11),
                0.25 * (-g00 - g01 + g10 + g11)
            );
        }

        void main() {
            ivec2 localP = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(localP, uCovarianceTextureSize))) {
                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);
                return;
            }
            ivec2 p = localP + uCovarianceOrigin;
            if (any(greaterThanEqual(p, uCovarianceSize))) {
                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);
                return;
            }
            float jxx = 0.0, jxy = 0.0, jyy = 0.0;
            for (int iy = 0; iy < 2; ++iy) {
                for (int ix = 0; ix < 2; ++ix) {
                    ivec2 q = p - ivec2(1) + ivec2(ix, iy);
                    if (q.x < 0 || q.y < 0 ||
                        q.x >= uCovarianceSize.x - 1 || q.y >= uCovarianceSize.y - 1) continue;
                    vec2 g = publicGrad(q);
                    jxx += g.x * g.x;
                    jxy += g.x * g.y;
                    jyy += g.y * g.y;
                }
            }

            float trace = jxx + jyy;
            float disc = sqrt(max((jxx-jyy)*(jxx-jyy) + 4.0*jxy*jxy, 0.0));
            float l1 = max(0.5 * (trace + disc), 0.0);
            float l2 = max(0.5 * (trace - disc), 0.0);
            vec2 va = vec2(jxy, l1 - jxx);
            vec2 vb = vec2(l1 - jyy, jxy);
            float na = dot(va, va), nb = dot(vb, vb);
            vec2 e1;
            if (max(na, nb) > 1.0e-20) e1 = normalize(na >= nb ? va : vb);
            else e1 = jxx >= jyy ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
            vec2 e2 = vec2(-e1.y, e1.x);

            float A = 1.0 + sqrt(max((l1-l2) / max(l1+l2, 1.0e-20), 0.0));
            float D = clamp(1.0 - sqrt(max(l1, 0.0)) / max(uDtr, 1.0e-8) + uDth, 0.0, 1.0);
            float selected1 = 1.0 + 0.5 * A * (1.0 / max(uKShrink, 1.0e-8) - 1.0);
            float selected2 = 1.0 + 0.5 * A * (uKStretch - 1.0);
            float k1 = max(uKDetail * ((1.0-D) * selected1 + D * uKDenoise), 1.0e-5);
            float k2 = max(uKDetail * ((1.0-D) * selected2 + D * uKDenoise), 1.0e-5);
            float k1s = k1*k1, k2s = k2*k2;
            float xx = k1s*e1.x*e1.x + k2s*e2.x*e2.x;
            float xy = k1s*e1.x*e1.y + k2s*e2.x*e2.y;
            float yy = k1s*e1.y*e1.y + k2s*e2.y*e2.y;
            float det = xx*yy - xy*xy;
            if (abs(det) <= 1.0e-12) {
                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);
            } else {
                oCovariance = vec4(yy/det, xx/det, -xy/det, 1.0);
            }
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

        vec2 mirrorUv(vec2 uv) {
            uv = mod(uv, 2.0);
            return mix(uv, 2.0 - uv, greaterThan(uv, vec2(1.0)));
        }

        vec4 sampleBiquadraticAbsolute(sampler2D image, vec2 uv) {
            vec2 texelSize = 1.0 / vec2(uGuideSize);
            vec2 fractionalOffset = fract(uv * vec2(uGuideSize));
            vec2 c = fractionalOffset * fractionalOffset -
                fractionalOffset + 0.5;
            vec2 w0 = uv - c * texelSize;
            vec2 w1 = uv + c * texelSize;
            vec4 samples =
                abs(texture(image, vec2(w0.x, w0.y))) +
                abs(texture(image, vec2(w0.x, w1.y))) +
                abs(texture(image, vec2(w1.x, w1.y))) +
                abs(texture(image, vec2(w1.x, w0.y)));
            samples.w /= 1024.0;
            return samples * 0.25;
        }

        void main() {
            // V25 requires GenerateRejectionTexture and GuideImage to share the RAW/4 domain.
            vec2 uv = gl_FragCoord.xy / vec2(uRejectionSize);
            vec2 flowUv = uv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec4 flow = texture(uFlow, flowUv);
            vec2 warpedUv = mirrorUv(uv + flow.xy);
            float unblocker = texture(uUnblocker, uv * uUnblockerScale).r;
            if (flow.z < uUnblockerReductionThreshold) unblocker = 0.0;
            bool motionPrior = flow.z > uExtraMotionRobustnessMotionThreshold;
            vec4 reference = texture(uBaseGuide, uv);
            bool greenOnly = reference.w < 0.0;
            reference.w = abs(reference.w) / 1024.0;
            vec4 current = sampleBiquadraticAbsolute(uAltGuide, warpedUv);
            float luma = greenOnly
                ? reference.y
                : dot(reference.rgb, vec3(1.0 / 3.0));
            vec2 referenceNoiseUv =
                vec2(luma, 0.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            vec2 currentNoiseUv =
                vec2(luma, 1.0) * uNoiseTextureScaleBias.xy +
                uNoiseTextureScaleBias.zw;
            vec3 referenceNoise =
                texture(uNoiseEstimates, referenceNoiseUv).xyz;
            vec3 currentNoise =
                texture(uNoiseEstimates, currentNoiseUv).xyz;
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
            // Noise estimates are transported through RGBA16F and can quantize to zero at the
            // dark end. Keep the recovered equations defined without changing any positive
            // estimate.
            vec3 combinedNoise = max(
                referenceNoise + currentNoise,
                vec3(1.0e-8)
            );
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

    /**
     * IRIS_26527_FINAL_MGC_REJECTION_ALIGNMENT_PARITY
     * Rejection::Downsample2x. MGC applies this to pixel difference immediately after
     * DilateMask moves the rejection result onto the RAW/4 merge-weight grid.
     */
    val rejectionPixelDifferenceDownsample = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uInput;
        uniform ivec2 uInputSize;
        out float oPixelDifference;
        float valueAt(ivec2 p) {
            return texelFetch(
                uInput,
                clamp(p, ivec2(0), uInputSize - ivec2(1)),
                0
            ).r;
        }
        void main() {
            ivec2 source = ivec2(gl_FragCoord.xy) * 2;
            oPixelDifference = 0.25 * (
                valueAt(source) +
                valueAt(source + ivec2(1, 0)) +
                valueAt(source + ivec2(0, 1)) +
                valueAt(source + ivec2(1, 1))
            );
        }
    """.trimIndent()

    /**
     * ClippedGaussianBlurHalide (0x387cd28), recovered from the AOT workers and verified against
     * the original function with constant, impulse, step and asymmetric synthetic inputs.
     *
     * filtered_a_x = min(input, GaussianX(input))
     * output = min(filtered_a_x, GaussianY(filtered_a_x))
     *
     * MGC keeps the horizontal intermediate in Float32 and quantizes only the final result to U8.
     */
    val clippedGaussianHorizontal = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uInput;
        uniform ivec2 uSize;
        uniform float uKernel[20];
        out float oFiltered;
        float valueAt(ivec2 p) {
            return texelFetch(
                uInput,
                clamp(p, ivec2(0), uSize - ivec2(1)),
                0
            ).r;
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float filtered = 0.0;
            for (int tap = 0; tap < 20; ++tap) {
                filtered += uKernel[tap] *
                    valueAt(p + ivec2(tap - 9, 0));
            }
            oFiltered = min(valueAt(p), filtered);
        }
    """.trimIndent()

    val clippedGaussianVertical = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uInput;
        uniform ivec2 uSize;
        uniform float uKernel[20];
        out float oFiltered;
        float valueAt(ivec2 p) {
            return texelFetch(
                uInput,
                clamp(p, ivec2(0), uSize - ivec2(1)),
                0
            ).r;
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float filtered = 0.0;
            for (int tap = 0; tap < 20; ++tap) {
                filtered += uKernel[tap] *
                    valueAt(p + ivec2(0, tap - 9));
            }
            oFiltered = round(
                255.0 * clamp(min(valueAt(p), filtered), 0.0, 1.0)
            ) / 255.0;
        }
    """.trimIndent()

    /**
     * Read4xDownSample and the input preparation for
     * Downsample4xAndFilterRejectionMap from the embedded rejection.cl. These inputs are already
     * on DilateMask's RAW/4 merge-weight grid; this pass produces the RAW/16 filter grid.
     */
    val rejectionFilterDownsample = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uBaseLuma;
        uniform sampler2D uWeight;
        uniform ivec2 uInputSize;
        layout(location = 0) out float oLuma;
        layout(location = 1) out float oRejection;

        float lumaLinearAt(vec2 coordinate) {
            vec2 shifted = coordinate - vec2(0.5);
            ivec2 p0 = ivec2(floor(shifted));
            vec2 fraction = fract(shifted);
            ivec2 maximum = uInputSize - ivec2(1);
            float v00 = float(texelFetch(
                uBaseLuma, clamp(p0, ivec2(0), maximum), 0
            ).r);
            float v10 = float(texelFetch(
                uBaseLuma, clamp(p0 + ivec2(1, 0), ivec2(0), maximum), 0
            ).r);
            float v01 = float(texelFetch(
                uBaseLuma, clamp(p0 + ivec2(0, 1), ivec2(0), maximum), 0
            ).r);
            float v11 = float(texelFetch(
                uBaseLuma, clamp(p0 + ivec2(1), ivec2(0), maximum), 0
            ).r);
            return mix(
                mix(v00, v10, fraction.x),
                mix(v01, v11, fraction.x),
                fraction.y
            );
        }

        float weightLinearAt(vec2 coordinate) {
            return texture(
                uWeight,
                coordinate / vec2(uInputSize)
            ).r;
        }

        void main() {
            vec2 center = 4.0 * floor(gl_FragCoord.xy) + vec2(2.0);
            center = clamp(
                center,
                vec2(2.0),
                vec2(uInputSize) - vec2(2.0)
            );
            float luma = 0.0;
            float weight = 0.0;
            for (int y = -1; y <= 1; y += 2) {
                for (int x = -1; x <= 1; x += 2) {
                    vec2 coordinate = center + vec2(x, y);
                    luma += lumaLinearAt(coordinate);
                    weight += weightLinearAt(coordinate);
                }
            }
            // The source reads CL_SNORM_INT16 and multiplies by 32767 / 16383.
            oLuma = 0.25 * luma / 16383.0;
            oRejection = 0.25 * weight;
        }
    """.trimIndent()

    /**
     * Downsample4xAndFilterRejectionMap from the embedded rejection.cl. The input textures contain
     * the exact Read4xDownSample results, so the 7x7 loop is algebraically identical to the fused
     * OpenCL kernel while avoiding repeated 4x4 source reads.
     */
    val rejectionFilter = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uLuma;
        uniform sampler2D uRejection;
        uniform ivec2 uSize;
        uniform int uRadius;
        uniform float uSigmaSpatial;
        uniform float uColorSigma;
        uniform float uColorSigmaBoost;
        uniform int uClipRejection;
        out float oFilteredRejection;

        float bilateralWeight(float residual, float sigma) {
            float widthSquared = sigma * sigma * 5.0;
            float squaredDistance = residual * residual;
            float distance = 1.0 - squaredDistance / widthSquared;
            return squaredDistance <= widthSquared
                ? distance * distance
                : 0.0;
        }

        float spatialWeight(float radius) {
            return exp(
                -(radius * radius) /
                    (2.0 * uSigmaSpatial * uSigmaSpatial)
            );
        }

        float valueAt(sampler2D image, ivec2 p) {
            return texelFetch(
                image,
                clamp(p, ivec2(0), uSize - ivec2(1)),
                0
            ).r;
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float centerLuma = valueAt(uLuma, p);
            float centerWeight = valueAt(uRejection, p);
            int spatialRadius = min(uRadius, 3 * int(uSigmaSpatial));
            float weightedRejection = 0.0;
            float weightSum = 0.0;
            for (int dy = -3; dy <= 3; ++dy) {
                if (abs(dy) > spatialRadius) continue;
                float spatialWeightY = spatialWeight(float(dy));
                for (int dx = -3; dx <= 3; ++dx) {
                    if (abs(dx) > spatialRadius) continue;
                    ivec2 q = p + ivec2(dx, dy);
                    float deltaLuma = valueAt(uLuma, q);
                    float deltaWeight = valueAt(uRejection, q);
                    float sigma = centerWeight <
                            deltaWeight - 1.0 / 255.0
                        ? uColorSigma
                        : uColorSigma * (
                            uClipRejection != 0 ? uColorSigmaBoost : 1.0
                        );
                    float weight = bilateralWeight(
                        abs(deltaLuma - centerLuma),
                        sigma
                    );
                    weight *= spatialWeight(float(dx)) * spatialWeightY;
                    // DilateMask has inverted rejection into acceptance weight. Filtering may
                    // restore support, but clip-rejection must never lower the center acceptance.
                    float value = uClipRejection != 0
                        ? max(deltaWeight, centerWeight)
                        : deltaWeight;
                    weightedRejection += weight * value;
                    weightSum += weight;
                }
            }
            oFilteredRejection = weightSum > 0.0
                ? weightedRejection / weightSum
                : centerWeight;
        }
    """.trimIndent()

    /**
     * Upsample4xAndPostProcess from the embedded rejection.cl. A separate output texture avoids
     * undefined framebuffer feedback while preserving the source equation.
     */
    val rejectionPostprocess = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uOriginalWeight;
        uniform sampler2D uFilteredWeight;
        uniform sampler2D uPixelDifference;
        uniform ivec2 uSize;
        uniform float uPixelDifferenceThreshold;
        uniform float uClippedThreshold;
        out float oRejection;
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float original = texelFetch(uOriginalWeight, p, 0).r;
            float pixelDifference = texelFetch(uPixelDifference, p, 0).r;
            vec2 uv = (vec2(p) + vec2(0.5)) / vec2(uSize);
            float filtered = texture(uFilteredWeight, uv).r;
            float postprocessed = filtered;
            if (filtered > original) {
                float weight = pixelDifference < uPixelDifferenceThreshold
                    ? 0.0
                    : pixelDifference;
                postprocessed =
                    original + weight * (filtered - original);
            }
            if (uClippedThreshold > 0.0 &&
                original <= uClippedThreshold &&
                pixelDifference <= uPixelDifferenceThreshold) {
                postprocessed = original;
            }
            oRejection = postprocessed;
        }
    """.trimIndent()

    val dilateRejection = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uRejection;
        uniform ivec2 uInputSize;
        out float oWeight;
        float rejectionAt(vec2 p) {
            return texture(uRejection, p / vec2(uInputSize)).r;
        }
        void main() {
            // Exact DilateMask mapping from the full Bayer-quad rejection domain to
            // MergeBayer's half-sized rejection texture. The nine bilinear reads and
            // coefficients are the factored form of a 5x5 box sum.
            vec2 texCoord =
                2.0 * floor(gl_FragCoord.xy - vec2(0.5)) + vec2(1.5);
            float rejection =
                4.0 * rejectionAt(texCoord + vec2(-1.5, -1.5)) +
                4.0 * rejectionAt(texCoord + vec2( 0.5, -1.5)) +
                2.0 * rejectionAt(texCoord + vec2( 2.0, -1.5)) +
                4.0 * rejectionAt(texCoord + vec2(-1.5,  0.5)) +
                4.0 * rejectionAt(texCoord + vec2( 0.5,  0.5)) +
                2.0 * rejectionAt(texCoord + vec2( 2.0,  0.5)) +
                2.0 * rejectionAt(texCoord + vec2(-1.5,  2.0)) +
                2.0 * rejectionAt(texCoord + vec2( 0.5,  2.0)) +
                      rejectionAt(texCoord + vec2( 2.0,  2.0));
            rejection = (rejection - 0.2) * 0.5;
            oWeight = 1.0 - rejection;
        }
    """.trimIndent()

    /**
     * Bento UpdateLinearKernelMaskHalide. MGC invokes this once on the rejection-buffer slice
     * selected by the accepted ultrashort index. It is not a temporal union of normal-frame
     * rejection maps.
     */
    val updateLinearKernelMask = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uRejection;
        uniform ivec2 uSize;
        out float oLinearKernelMask;
        float rejectionAt(ivec2 p) {
            return texelFetch(
                uRejection,
                clamp(p, ivec2(0), uSize - ivec2(1)),
                0
            ).r;
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float localMinimum = 1.0;
            float localMaximum = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    float rejection = rejectionAt(p + ivec2(x, y));
                    localMinimum = min(localMinimum, rejection);
                    localMaximum = max(localMaximum, rejection);
                }
            }
            // UpdateLinearKernelMaskHalide emits a strict binary mask: any non-uniform
            // 3x3 rejection neighbourhood selects the linear kernel, independently of
            // the rejection-value amplitude.
            oLinearKernelMask = localMaximum != localMinimum ? 1.0 : 0.0;
        }
    """.trimIndent()

    /**
     * First FindBlockTiles pass. Each output texel represents one 16x16 RAW tile
     * (8x8 Bayer quads); RGBA stores the phase-preserving alignment residual on
     * the left, right, top, and bottom tile edges.
     */
    val findBlockTilesGatherEdges = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;

        uniform usampler2D uBaseRaw;
        uniform usampler2D uAltRaw;
        uniform sampler2D uFlow;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uRawSize;
        uniform ivec2 uBayerSize;
        uniform ivec2 uTileGridSize;
        uniform int uCfaPattern;
        uniform vec4 uBasePhaseGains;
        uniform vec4 uBasePhaseBlackTerms;
        uniform vec4 uAltPhaseGains;
        uniform vec4 uAltPhaseBlackTerms;

        layout(location = 0) out vec4 oEdges;

        const int TILE_SIZE = 8;
        const float SIGNAL_FLOOR = 0.015625;
        const float INTERIOR_REJECTION = 0.82;

        float normalizedPhase(
            usampler2D rawTexture,
            ivec2 bayer,
            int phase,
            vec4 gains,
            vec4 blackTerms
        ) {
            ivec2 raw = bayer * 2 + ivec2(phase & 1, phase >> 1);
            raw = clamp(raw, ivec2(0), uRawSize - ivec2(1));
            return clamp(float(texelFetch(rawTexture, raw, 0).r) * gains[phase] + blackTerms[phase], 0.0, 1.0);
        }

        float greenAt(
            usampler2D rawTexture,
            ivec2 bayer,
            vec4 gains,
            vec4 blackTerms
        ) {
            // RGGB/BGGR have their greens at phases 1/2; GRBG/GBRG at 0/3.
            int phase0 = (uCfaPattern == 0 || uCfaPattern == 3) ? 1 : 0;
            int phase1 = (uCfaPattern == 0 || uCfaPattern == 3) ? 2 : 3;
            return 0.5 * (
                normalizedPhase(rawTexture, bayer, phase0, gains, blackTerms) +
                normalizedPhase(rawTexture, bayer, phase1, gains, blackTerms)
            );
        }

        float alignedAltGreen(vec2 bayer) {
            vec2 clamped = clamp(bayer, vec2(0.0), vec2(uBayerSize - ivec2(1)));
            ivec2 p0 = ivec2(floor(clamped));
            ivec2 p1 = min(p0 + ivec2(1), uBayerSize - ivec2(1));
            vec2 f = fract(clamped);
            float v00 = greenAt(uAltRaw, p0, uAltPhaseGains, uAltPhaseBlackTerms);
            float v10 = greenAt(uAltRaw, ivec2(p1.x, p0.y), uAltPhaseGains, uAltPhaseBlackTerms);
            float v01 = greenAt(uAltRaw, ivec2(p0.x, p1.y), uAltPhaseGains, uAltPhaseBlackTerms);
            float v11 = greenAt(uAltRaw, p1, uAltPhaseGains, uAltPhaseBlackTerms);
            return mix(mix(v00, v10, f.x), mix(v01, v11, f.x), f.y);
        }

        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(tile, uTileGridSize))) {
                oEdges = vec4(0.0);
                return;
            }

            ivec2 tileOrigin = tile * TILE_SIZE;
            vec4 edgeSum = vec4(0.0);
            vec4 edgeCount = vec4(0.0);
            float tileSum = 0.0;
            float tileCount = 0.0;

            for (int y = 0; y < TILE_SIZE; ++y) {
                for (int x = 0; x < TILE_SIZE; ++x) {
                    ivec2 bayer = tileOrigin + ivec2(x, y);
                    if (any(greaterThanEqual(bayer, uBayerSize))) {
                        continue;
                    }

                    vec2 referenceUv = (vec2(bayer) + vec2(0.5)) / vec2(uBayerSize);
                    vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
                    vec2 flow = texture(uFlow, flowUv).xy * vec2(uBayerSize);
                    float baseGreen = greenAt(uBaseRaw, bayer, uBasePhaseGains, uBasePhaseBlackTerms);
                    float altGreen = alignedAltGreen(vec2(bayer) + flow);
                    float signal = max(0.5 * (baseGreen + altGreen), SIGNAL_FLOOR);
                    float residual = abs(baseGreen - altGreen) / sqrt(signal);

                    tileSum += residual;
                    tileCount += 1.0;
                    if (x < 2) {
                        edgeSum.x += residual;
                        edgeCount.x += 1.0;
                    }
                    if (x >= TILE_SIZE - 2) {
                        edgeSum.y += residual;
                        edgeCount.y += 1.0;
                    }
                    if (y < 2) {
                        edgeSum.z += residual;
                        edgeCount.z += 1.0;
                    }
                    if (y >= TILE_SIZE - 2) {
                        edgeSum.w += residual;
                        edgeCount.w += 1.0;
                    }
                }
            }

            vec4 edgeMean = edgeSum / max(edgeCount, vec4(1.0));
            float interiorMean = tileSum / max(tileCount, 1.0);
            oEdges = clamp(edgeMean - vec4(INTERIOR_REJECTION * interiorMean), 0.0, 1.0);
        }
    """.trimIndent()

    /** Pair the two observations of every shared tile edge and convert them to a soft mask. */
    val findBlockTilesFilterIntermediate = """
        #version 300 es
        precision highp float;
        precision highp int;

        uniform sampler2D uGatheredEdges;
        uniform ivec2 uSize;

        layout(location = 0) out float oFiltered;

        vec4 edgesAt(ivec2 p) {
            return texelFetch(uGatheredEdges, clamp(p, ivec2(0), uSize - ivec2(1)), 0);
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(p, uSize))) {
                oFiltered = 0.0;
                return;
            }

            vec4 center = edgesAt(p);
            float left = p.x > 0 ? min(center.x, edgesAt(p + ivec2(-1, 0)).y) : 0.0;
            float right = p.x + 1 < uSize.x ? min(center.y, edgesAt(p + ivec2(1, 0)).x) : 0.0;
            float top = p.y > 0 ? min(center.z, edgesAt(p + ivec2(0, -1)).w) : 0.0;
            float bottom = p.y + 1 < uSize.y ? min(center.w, edgesAt(p + ivec2(0, 1)).z) : 0.0;
            float pairedEdge = max(max(left, right), max(top, bottom));
            oFiltered = smoothstep(0.020, 0.080, pairedEdge);
        }
    """.trimIndent()

    /** Final binary tile mask. Isolated responses are removed before CPU component analysis. */
    val findBlockTilesOutput = """
        #version 300 es
        precision highp float;
        precision highp int;

        uniform sampler2D uFiltered;
        uniform ivec2 uSize;

        layout(location = 0) out float oMask;

        float valueAt(ivec2 p) {
            if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, uSize))) {
                return 0.0;
            }
            return texelFetch(uFiltered, p, 0).r;
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(p, uSize)) || p.x == 0 || p.y == 0 || p.x == uSize.x - 1 || p.y == uSize.y - 1) {
                oMask = 0.0;
                return;
            }

            float center = valueAt(p);
            float axialSupport = valueAt(p + ivec2(-1, 0)) + valueAt(p + ivec2(1, 0)) +
                valueAt(p + ivec2(0, -1)) + valueAt(p + ivec2(0, 1));
            oMask = center >= 0.5 && center + axialSupport >= 1.5 ? 1.0 : 0.0;
        }
    """.trimIndent()

    // Embedded OpenCL source: Mask_GenerateHighlightMask.
    val bentoGenerateHighlightMask = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBaseFrame;
        uniform ivec2 uSize;
        uniform float uMaxRgbClippingThreshold;
        out float oHighlightMask;
        void main() {
            ivec2 p = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                uSize - ivec2(1)
            );
            vec3 rgb = round(
                65535.0 * clamp(texelFetch(uBaseFrame, p, 0).rgb, 0.0, 1.0)
            ) / 65535.0;
            float maxIntensity = max(rgb.r, max(rgb.g, rgb.b));
            float clippedRatio =
                (maxIntensity - uMaxRgbClippingThreshold) /
                (1.0 - uMaxRgbClippingThreshold);
            oHighlightMask = clamp(clippedRatio, 0.0, 1.0);
        }
    """.trimIndent()

    /**
     * Counts non-zero R8 highlight-mask pixels without materializing the full mask on the CPU.
     * One atomic update is issued per 8x8 work group rather than per active pixel.
     */
    val bentoCountHighlightMask = """
        #version 310 es
        precision highp float;
        precision highp int;
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        uniform highp sampler2D uMask;
        uniform ivec2 uSize;
        layout(std430, binding = 0) buffer ActiveCountBuffer {
            uint activeCount;
        };
        shared uint localCounts[64];

        void main() {
            uint lane = gl_LocalInvocationIndex;
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            localCounts[lane] =
                all(lessThan(p, uSize)) && texelFetch(uMask, p, 0).r > 0.0
                    ? 1u
                    : 0u;
            barrier();
            for (uint stride = 32u; stride > 0u; stride >>= 1u) {
                if (lane < stride) {
                    localCounts[lane] += localCounts[lane + stride];
                }
                barrier();
            }
            if (lane == 0u && localCounts[0] != 0u) {
                atomicAdd(activeCount, localCounts[0]);
            }
        }
    """.trimIndent()

    // Embedded OpenCL sources: GainUp and
    // Mask_AdjustHighlightMaskAndGenerateInpaintingMask. The third output is the aligned
    // ultrashort clipping mask consumed by Bento's high-overlap fallback predicate.
    val bentoAdjustHighlightMask = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBaseFrame;
        uniform sampler2D uUltrashortFrame;
        uniform sampler2D uHighlightMask;
        uniform sampler2D uFlow;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uSize;
        uniform float uExposureRatio;
        uniform float uMinNormalizedIntensityError;
        uniform float uMaxRgbClippingThreshold;
        uniform float uMinRgbForInpainting;
        layout(location = 0) out float oAdjustedHighlightMask;
        layout(location = 1) out float oInpaintingMask;
        layout(location = 2) out float oUltrashortClippingMask;

        void main() {
            ivec2 p = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                uSize - ivec2(1)
            );
            vec2 uv = gl_FragCoord.xy / vec2(uSize);
            vec2 flowUv = uv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec2 flow = texture(uFlow, flowUv).xy;
            vec2 ultrashortUv = uv + flow;
            bool physicalUltrashort = all(greaterThanEqual(ultrashortUv, vec2(0.0))) &&
                all(lessThanEqual(ultrashortUv, vec2(1.0)));
            vec3 base = round(
                65535.0 * clamp(texelFetch(uBaseFrame, p, 0).rgb, 0.0, 1.0)
            ) / 65535.0;
            if (!physicalUltrashort) {
                /* IRIS_26532_BENTO_REAL_SENSOR_SUPPORT: absent Short evidence is zero evidence. */
                oAdjustedHighlightMask = 0.0;
                oInpaintingMask = 0.0;
                oUltrashortClippingMask = 0.0;
                return;
            }
            vec3 ultrashort = clamp(
                texture(uUltrashortFrame, ultrashortUv).rgb,
                0.0,
                1.0
            );
            vec3 gainedUltrashort = floor(
                65535.0 * clamp(ultrashort * uExposureRatio, 0.0, 1.0)
            ) / 65535.0;
            vec3 difference = min(gainedUltrashort - base, vec3(0.0));
            float normalizedIntensityError = length(difference);
            float fallback = normalizedIntensityError >=
                    uMinNormalizedIntensityError
                ? floor(normalizedIntensityError * 255.0) / 255.0
                : 0.0;
            float highlight = texelFetch(uHighlightMask, p, 0).r;
            fallback = highlight > 0.0 ? fallback : 0.0;
            oAdjustedHighlightMask = floor(
                (1.0 - fallback) * highlight * 255.0
            ) / 255.0;

            vec3 base8 = round(clamp(base, 0.0, 1.0) * 255.0) / 255.0;
            float smallest = min(base8.r, min(base8.g, base8.b));
            float largest = max(base8.r, max(base8.g, base8.b));
            float middle = base8.r + base8.g + base8.b - smallest - largest;
            oInpaintingMask =
                fallback > 0.0 &&
                smallest >= uMinRgbForInpainting &&
                middle >= uMaxRgbClippingThreshold
                    ? 1.0
                    : 0.0;

            float ultrashortMax = max(
                ultrashort.r,
                max(ultrashort.g, ultrashort.b)
            );
            oUltrashortClippingMask = clamp(
                (ultrashortMax - uMaxRgbClippingThreshold) /
                    (1.0 - uMaxRgbClippingThreshold),
                0.0,
                1.0
            );
        }
    """.trimIndent()

    // Embedded OpenCL source: MaskRejectionWithClippedHighlights.
    val bentoRewriteWeight = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExistingWeight;
        uniform sampler2D uBentoMask;
        uniform ivec2 uSize;
        uniform int uHasExistingWeight;
        out float oWeight;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(uSize);
            float existingWeight = uHasExistingWeight != 0
                ? texture(uExistingWeight, uv).r
                : 1.0;
            float maskWeight = texture(uBentoMask, uv).r;
            oWeight = existingWeight * (1.0 - maskWeight);
        }
    """.trimIndent()

    /**
     * RAW-domain joint demosaic and super-resolution merge.
     *
     * No per-frame RGB image exists. Every output location gathers native CFA observations in the
     * continuously warped sensor domain. Native greens form the high-resolution edge lattice;
     * native red/blue sites contribute R-G/B-G observations against an edge-directed local green.
     * This couples all output channels to one SR edge geometry instead of reproducing the historical
     * independent-RGB support that produced purple/green fringes on high-contrast edges.
     */
    val mergeRgb = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform sampler2D uChromaGuideRegion;
        uniform sampler2D uAlignment;
        uniform sampler2D uFrameWeight;
        uniform sampler2D uCovariance;
        uniform ivec2 uRawSize;
        uniform ivec2 uCovarianceOrigin;
        uniform ivec2 uCovarianceTextureSize;
        uniform ivec2 uRawTextureOrigin;
        uniform ivec2 uRawRegionOrigin;
        uniform ivec2 uRawRegionSize;
        uniform ivec2 uOutputSize;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uAccumulatorOrigin;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec2 uGreenNoise;
        uniform float uChromaEdgeNoiseSigmas;
        uniform float uChromaEdgeSigmaFloor;
        uniform float uInterpolationFlowTolerance;
        uniform float uGlobalFrameWeight;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        layout(location = 0) out vec4 oColorAndRWeight;
        layout(location = 1) out vec4 oGbWeights;

        int canonicalChannel(ivec2 p) {
            int phase = ((p.y & 1) << 1) + (p.x & 1);
            if (uCfaPattern == 0) return phase;
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
            if (phase == 0) return 3;
            if (phase == 1) return 2;
            if (phase == 2) return 1;
            return 0;
        }

        int clampRawCoordinateToPhase(int coordinate, int extent) {
            int phase = coordinate & 1;
            if (phase >= extent) return extent - 1;
            int last = phase + 2 * ((extent - 1 - phase) / 2);
            return clamp(coordinate, phase, last);
        }

        ivec2 clampRawPixelToPhase(ivec2 p) {
            return ivec2(
                clampRawCoordinateToPhase(p.x, uRawSize.x),
                clampRawCoordinateToPhase(p.y, uRawSize.y)
            );
        }

        float gainedRaw(ivec2 globalPixel) {
            int channel = canonicalChannel(globalPixel);
            globalPixel = clampRawPixelToPhase(globalPixel);
            return float(texelFetch(uRaw, globalPixel - uRawTextureOrigin, 0).r) *
                uGains[channel] +
                uBlackLevelsTimesGains[channel];
        }

        float chromaGuideAt(ivec2 globalPixel) {
            ivec2 local = clamp(
                globalPixel - uRawRegionOrigin,
                ivec2(0),
                uRawRegionSize - ivec2(1)
            );
            return texelFetch(uChromaGuideRegion, local, 0).r;
        }

        vec2 alignmentAt(ivec2 tile) {
            ivec2 size = max(textureSize(uAlignment, 0), ivec2(1));
            return texelFetch(uAlignment, clamp(tile, ivec2(0), size - ivec2(1)), 0).xy;
        }

        vec2 interpolatedAlignment(vec2 quadPosition) {
            ivec2 tile = ivec2(floor(quadPosition / 8.0));
            vec2 baseFlow = alignmentAt(tile);
            if (uInterpolationFlowTolerance <= 0.0) return baseFlow;
            vec2 offsetWithinTile = quadPosition - vec2(tile * 8);
            bool leftHalf = offsetWithinTile.x <= 4.0;
            bool topHalf = offsetWithinTile.y <= 4.0;
            int tx0 = leftHalf ? tile.x - 1 : tile.x;
            int ty0 = topHalf ? tile.y - 1 : tile.y;
            ivec2 tile00 = ivec2(tx0, ty0);
            vec2 flow00 = alignmentAt(tile00);
            vec2 flow10 = alignmentAt(tile00 + ivec2(1, 0));
            vec2 flow01 = alignmentAt(tile00 + ivec2(0, 1));
            vec2 flow11 = alignmentAt(tile00 + ivec2(1, 1));
            float threshold = 8.0 * uInterpolationFlowTolerance;
            bool cancelInterpolation =
                any(greaterThanEqual(abs(flow00 - baseFlow), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow10 - baseFlow), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow01 - baseFlow), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow11 - baseFlow), vec2(threshold)));
            if (cancelInterpolation) return baseFlow;
            float ux = quadPosition.x / 8.0 - (float(tx0) + 0.5);
            float uy = quadPosition.y / 8.0 - (float(ty0) + 0.5);
            return mix(mix(flow00, flow10, ux), mix(flow01, flow11, ux), uy);
        }

        vec2 mirrorUv(vec2 uv) {
            uv = mod(uv, 2.0);
            return mix(uv, 2.0 - uv, greaterThan(uv, vec2(1.0)));
        }

        float kernelWeight(vec2 pixelOffset, vec3 precisionCoeffs) {
            float distance = pixelOffset.x * pixelOffset.x * precisionCoeffs.x +
                pixelOffset.y * pixelOffset.y * precisionCoeffs.y +
                2.0 * pixelOffset.x * pixelOffset.y * precisionCoeffs.z;
            return exp(-0.5 * max(distance, 0.0));
        }

        float chromaGuideWeight(float sampleGreen, float targetGreen) {
            float signal = max(max(sampleGreen, targetGreen), 0.0);
            float variance = max(uGreenNoise.x * signal + uGreenNoise.y, 0.0);
            float sigma = max(
                uChromaEdgeNoiseSigmas * sqrt(variance),
                uChromaEdgeSigmaFloor
            );
            float normalizedDifference = (sampleGreen - targetGreen) / sigma;
            return exp(-0.5 * normalizedDifference * normalizedDifference);
        }

        vec2 greenDirectionMoment(ivec2 center, float signal) {
            float gx = chromaGuideAt(center + ivec2(1, 0)) -
                chromaGuideAt(center - ivec2(1, 0));
            float gy = chromaGuideAt(center + ivec2(0, 1)) -
                chromaGuideAt(center - ivec2(0, 1));
            float energy = gx * gx + gy * gy;
            float variance = max(uGreenNoise.x * max(signal, 0.0) + uGreenNoise.y, 0.0);
            float varianceFloor = uChromaEdgeSigmaFloor * uChromaEdgeSigmaFloor;
            float noiseEnergy = 4.0 * max(variance, varianceFloor);
            float confidence = clamp(
                (energy - noiseEnergy) / max(energy + noiseEnergy, 1.0e-12),
                0.0,
                1.0
            );
            vec2 doubledAngle = vec2(gx * gx - gy * gy, 2.0 * gx * gy) /
                max(energy, 1.0e-12);
            return doubledAngle * confidence;
        }

        void main() {
            ivec2 localOutput = ivec2(gl_FragCoord.xy) - uAccumulatorOrigin;
            ivec2 outputPixel = localOutput + uOutputOrigin;
            vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *
                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);
            vec2 sourceRaw = referenceRaw + 2.0 * interpolatedAlignment(referenceRaw * 0.5);
            /* IPOL Bayer covariance coordinate is (sourceCenter/2 - 0.5). Our sourceRaw is
             * integer-pixel-center coordinates, so sourceCenter=sourceRaw+0.5. Converting that
             * texel-index coordinate to GL normalized coordinates for a possibly band-local
             * covariance texture gives ((sourceRaw+0.5)/2-origin)/localSize. Full-frame origin=0
             * reduces exactly to the previously audited (sourceRaw+0.5)/rawSize mapping. */
            vec2 mirroredRawCenter = mirrorUv(
                (sourceRaw + vec2(0.5)) / vec2(uRawSize)
            ) * vec2(uRawSize);
            vec2 covarianceUv = (
                mirroredRawCenter * 0.5 - vec2(uCovarianceOrigin)
            ) / vec2(uCovarianceTextureSize);
            vec3 covariance = texture(
                uCovariance,
                clamp(covarianceUv, vec2(0.0), vec2(1.0))
            ).xyz;
            vec2 samplePosition = sourceRaw + vec2(0.5);
            ivec2 anchor = ivec2(floor(samplePosition));
            vec2 subpixelOffset = vec2(anchor) + vec2(0.5) - samplePosition;
            float greenSum = 0.0;
            float greenWeight = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    ivec2 p = anchor + ivec2(x, y);
                    int channel = canonicalChannel(p);
                    if (channel != 1 && channel != 2) continue;
                    float spatialWeight = kernelWeight(
                        subpixelOffset + vec2(x, y),
                        covariance
                    );
                    greenSum += gainedRaw(p) * spatialWeight;
                    greenWeight += spatialWeight;
                }
            }
            float targetGreen = greenSum / max(greenWeight, 1.0e-8);
            vec3 semanticSums = vec3(greenSum, 0.0, 0.0);
            vec3 weights = vec3(greenWeight, 0.0, 0.0);
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    ivec2 p = anchor + ivec2(x, y);
                    int channel = canonicalChannel(p);
                    if (channel == 1 || channel == 2) continue;
                    float spatialWeight = kernelWeight(
                        subpixelOffset + vec2(x, y),
                        covariance
                    );
                    float nativeValue = gainedRaw(p);
                    float localGreen = chromaGuideAt(p);
                    float jointWeight = spatialWeight *
                        chromaGuideWeight(localGreen, targetGreen);
                    int opponent = channel == 0 ? 1 : 2;
                    semanticSums[opponent] += (nativeValue - localGreen) * jointWeight;
                    weights[opponent] += jointWeight;
                }
            }
            vec2 weightUv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);
            float frameWeight = uUseFrameWeight != 0 ?
                texture(uFrameWeight, clamp(weightUv, vec2(0.0), vec2(1.0))).r : 1.0;
            frameWeight = clamp(frameWeight, 0.0, 1.0);
            frameWeight *= uGlobalFrameWeight;
            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);
            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);
            oGbWeights = vec4(
                weights.gb * frameWeight,
                directionMoment * weights.r * frameWeight
            );
        }
    """.trimIndent()

    /* IRIS_26530_MOTION_SAFE_RAW_SUPERRES
     * High-zoom-only derivative of the proven 26529 joint CFA shader. The legacy mergeRgb
     * string above is untouched and remains the <8x path. Spatial reconstruction maps the
     * requested crop directly into the original output grid; one shared green-driven geometry
     * remains authoritative for G/R-G/B-G so red/blue can never invent independent edge motion.
     * Luma temporal scaling applies only to green semantic/value support. Chroma opponents keep
     * the full rejection/global-frame weights for strong color-noise suppression.
     */
    val mergeRgbSuperRes = mergeRgb
        .replace(
            "uniform ivec2 uOutputSize;",
            "uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;",
        )
        .replace(
            "    vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);",
            "    vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n    vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n    vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);",
        )
        .replace(
            "    frameWeight *= uGlobalFrameWeight;\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * frameWeight\n    );",
            "    frameWeight *= uGlobalFrameWeight;\n    float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(\n        semanticSums.r * lumaFrameWeight,\n        semanticSums.g * frameWeight,\n        semanticSums.b * frameWeight,\n        weights.r * lumaFrameWeight\n    );\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * lumaFrameWeight\n    );",
        ).also { shader ->
            check(shader.contains("uReconstructionZoom"))
            check(shader.contains("uLumaTemporalScale"))
            check(shader.contains("lumaFrameWeight"))
            check(shader.contains("rawCenter"))
            check(shader.contains("referenceRaw = rawCenter"))
            check(!shader.contains("flowAndConfidence"))
            check(shader.contains("cancelInterpolation"))
        }

    val normalizeRgb16 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uColorAndRWeight;
        uniform sampler2D uGbWeights;
        uniform sampler2D uLensShading;
        uniform ivec2 uAccumulatorSize;
        uniform ivec2 uTargetOrigin;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputSize;
        uniform vec3 uCameraDomainScale;
        uniform float uOutputExposureScale;
        uniform int uUseLensShading;
        layout(location = 0) out highp uvec4 oRgb16;

        uint encodeSnorm8(float value) {
            int encoded = int(round(clamp(value, -1.0, 1.0) * 127.0));
            return uint(encoded & 0xFF);
        }

        uint packDirectionMoment(vec2 moment) {
            return encodeSnorm8(moment.x) | (encodeSnorm8(moment.y) << 8u);
        }

        void main() {
            ivec2 local = ivec2(gl_FragCoord.xy) - uTargetOrigin;
            if (any(lessThan(local, ivec2(0))) || any(greaterThanEqual(local, uAccumulatorSize))) {
                oRgb16 = uvec4(0u, 0u, 0u, 65535u);
                return;
            }
            vec4 colorAndR = texelFetch(uColorAndRWeight, local, 0);
            vec4 gbWeightsAndDirection = texelFetch(uGbWeights, local, 0);
            vec3 semantic = colorAndR.rgb / max(
                vec3(colorAndR.a, gbWeightsAndDirection.x, gbWeightsAndDirection.y),
                vec3(1.0e-8)
            );
            vec2 directionMoment = gbWeightsAndDirection.ba / max(colorAndR.a, 1.0e-8);
            vec3 rgb = vec3(
                semantic.r + semantic.g,
                semantic.r,
                semantic.r + semantic.b
            );
            ivec2 outputPixel = local + uOutputOrigin;
            if (uUseLensShading != 0) {
                vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);
                vec4 shading = texture(uLensShading, clamp(uv, vec2(0.0), vec2(1.0)));
                rgb *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
            }
            rgb = max(rgb * uCameraDomainScale * uOutputExposureScale, vec3(0.0));
            oRgb16 = uvec4(
                uvec3(round(clamp(rgb, vec3(0.0), vec3(1.0)) * 65535.0)),
                packDirectionMoment(directionMoment)
            );
        }
    """.trimIndent()

    /* IRIS_26530_SUPERRES_LSC_SENSOR_COORDINATE
     * Crop-aware SR must sample lens shading at the reconstructed sensor coordinate, not at the
     * post-crop output coordinate. This avoids radial R/G/B gain errors and pink/green edges.
     */
    val normalizeRgb16SuperRes = normalizeRgb16
        .replace(
            "uniform ivec2 uOutputSize;",
            "uniform ivec2 uOutputSize;\nuniform ivec2 uRawSize;\nuniform float uReconstructionZoom;",
        )
        .replace(
            "vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);",
            "vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) * vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n                vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n                vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);\n                vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);",
        )



    /* IRIS_26532_STREAMED_2X_TO_NATIVE_CHROMA
     * The high-resolution normalized Spatial band is the SR evidence. Downsample only the
     * base RGB carrier to the native grid before the existing Iris chroma/tone chain. Direction
     * moments are decoded, averaged and repacked rather than averaging packed alpha integers.
     */
    val downsampleRgb16SuperRes2x = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uHighResBand;
        uniform ivec2 uTargetOrigin;
        layout(location = 0) out highp uvec4 oRgb16;

        float decodeSnorm8(uint x) {
            int v = int(x & 255u);
            if (v > 127) v -= 256;
            return clamp(float(v) / 127.0, -1.0, 1.0);
        }
        uint encodeSnorm8(float value) {
            int encoded = int(round(clamp(value, -1.0, 1.0) * 127.0));
            return uint(encoded & 0xFF);
        }
        vec2 decodeMoment(uint irisPackedBits26986) {
            return vec2(decodeSnorm8(irisPackedBits26986), decodeSnorm8(irisPackedBits26986 >> 8u));
        }
        uint encodeMoment(vec2 moment) {
            return encodeSnorm8(moment.x) | (encodeSnorm8(moment.y) << 8u);
        }
        void main() {
            ivec2 nativeLocal = ivec2(gl_FragCoord.xy) - uTargetOrigin;
            ivec2 q = nativeLocal * 2;
            uvec4 a = texelFetch(uHighResBand, q, 0);
            uvec4 b = texelFetch(uHighResBand, q + ivec2(1, 0), 0);
            uvec4 c = texelFetch(uHighResBand, q + ivec2(0, 1), 0);
            uvec4 d = texelFetch(uHighResBand, q + ivec2(1, 1), 0);
            uvec3 rgb = (a.rgb + b.rgb + c.rgb + d.rgb + uvec3(2u)) / 4u;
            vec2 moment = 0.25 * (
                decodeMoment(a.a) + decodeMoment(b.a) +
                decodeMoment(c.a) + decodeMoment(d.a)
            );
            oRgb16 = uvec4(rgb, encodeMoment(moment));
        }
    """.trimIndent()

    /** Float variant used only for the direct CPU black-box boundary. */
    val normalizeRgbFloat = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uColorAndRWeight;
        uniform sampler2D uGbWeights;
        uniform sampler2D uLensShading;
        uniform ivec2 uAccumulatorSize;
        uniform ivec2 uTargetOrigin;
        uniform ivec2 uOutputOrigin;
        uniform ivec2 uOutputSize;
        uniform vec3 uCameraDomainScale;
        uniform float uOutputExposureScale;
        uniform int uUseLensShading;
        layout(location = 0) out highp vec4 oRgb16f;

        void main() {
            ivec2 local = ivec2(gl_FragCoord.xy) - uTargetOrigin;
            if (any(lessThan(local, ivec2(0))) || any(greaterThanEqual(local, uAccumulatorSize))) {
                oRgb16f = vec4(0.0, 0.0, 0.0, 1.0);
                return;
            }
            vec4 colorAndR = texelFetch(uColorAndRWeight, local, 0);
            vec2 gbWeights = texelFetch(uGbWeights, local, 0).rg;
            vec3 semantic = colorAndR.rgb / max(
                vec3(colorAndR.a, gbWeights.x, gbWeights.y),
                vec3(1.0e-8)
            );
            vec3 rgb = vec3(
                semantic.r + semantic.g,
                semantic.r,
                semantic.r + semantic.b
            );
            ivec2 outputPixel = local + uOutputOrigin;
            if (uUseLensShading != 0) {
                vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);
                vec4 shading = texture(uLensShading, clamp(uv, vec2(0.0), vec2(1.0)));
                rgb *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
            }
            vec3 normalized = clamp(
                rgb * uCameraDomainScale * uOutputExposureScale,
                vec3(0.0),
                vec3(1.0)
            );
            // Preserve the former RGBA16UI contract before storing the transient half-float.
            normalized = round(normalized * 65535.0) / 65535.0;
            oRgb16f = vec4(normalized, 1.0);
        }
    """.trimIndent()

    /**
     * Detect source-frame sensor clipping after transporting the long-frame RAW into reference
     * coordinates. Detection stays in the unnormalized sensor domain so exposure scaling cannot
     * make a clipped long-frame sample appear valid.
     */
    val alignedRawClippingMask = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;

        uniform highp usampler2D uRaw;
        uniform sampler2D uFlow;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uRawSize;
        uniform ivec2 uBayerSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uPhaseClippingLevels;

        out float oClippingMask;

        bool quadIsNearClipping(ivec2 quad) {
            quad = clamp(quad, ivec2(0), uBayerSize - ivec2(1));
            ivec2 rawOrigin = quad * 2;
            for (int phase = 0; phase < 4; ++phase) {
                ivec2 phaseOffset = ivec2(phase & 1, phase >> 1);
                ivec2 rawPixel = min(rawOrigin + phaseOffset, uRawSize - ivec2(1));
                float rawValue = float(texelFetch(uRaw, rawPixel, 0).r);
                if (rawValue >= uPhaseClippingLevels[phase]) {
                    return true;
                }
            }
            return false;
        }

        void main() {
            ivec2 outputPixel = ivec2(gl_FragCoord.xy);
            if (any(greaterThanEqual(outputPixel, uOutputSize))) {
                oClippingMask = 1.0;
                return;
            }

            // V25 merge weight is RAW/8: one texel covers 4x4 Bayer quads. Use its center in
            // reference coordinates, then inspect the 3x3 source neighborhood consumed by merge.
            ivec2 referenceQuad = min(outputPixel * 4 + ivec2(2), uBayerSize - ivec2(1));
            vec2 referenceUv = (vec2(referenceQuad) + vec2(0.5)) / vec2(uBayerSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec2 sourceFlow = texture(uFlow, flowUv).xy * vec2(uBayerSize);
            ivec2 sourceAnchor = ivec2(roundEven(vec2(referenceQuad) + sourceFlow));

            bool clipped = false;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    clipped = clipped || quadIsNearClipping(sourceAnchor + ivec2(x, y));
                }
            }
            oClippingMask = clipped ? 1.0 : 0.0;
        }
    """.trimIndent()

    /**
     * MergeBayerRaw transport recovered from the Halide AOT contract. IRIS_26527 consumes the final AlignAlt merge-grid directly.
     *
     * Alignment and the spatial kernel operate on Bayer quads, and every output sample is
     * reconstructed only from the same CFA phase in neighboring quads.
     */
    val mergeBayer = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform sampler2D uAlignment;
        uniform sampler2D uFrameWeight;
        uniform sampler2D uLinearKernelMask;
        uniform ivec2 uRawSize;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform float uKernelSigma;
        uniform float uInterpolationFlowTolerance;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        out vec4 oBayerAndWeight;

        int phaseIndex(ivec2 phase) {
            return (phase.y << 1) + phase.x;
        }

        int mirrorCoordinate(int coordinate, int extent) {
            if (extent <= 1) return 0;
            if (coordinate < 0) coordinate = -coordinate - 1;
            if (coordinate >= extent) coordinate = 2 * extent - coordinate - 1;
            return clamp(coordinate, 0, extent - 1);
        }

        ivec2 mirrorQuad(ivec2 quad, ivec2 extent) {
            return ivec2(
                mirrorCoordinate(quad.x, extent.x),
                mirrorCoordinate(quad.y, extent.y)
            );
        }

        float kernelWeight(vec2 pixelOffset, float kernelSigmaSquared) {
            return exp(
                -0.5 * dot(pixelOffset * pixelOffset, vec2(kernelSigmaSquared))
            );
        }

        float linearKernelWeight(vec2 pixelOffset) {
            return max(1.0 - length(pixelOffset) * 0.4, 0.0);
        }

        vec4 alignmentAt(ivec2 tile, ivec2 alignmentSize) {
            return texelFetch(
                uAlignment,
                clamp(tile, ivec2(0), alignmentSize - ivec2(1)),
                0
            );
        }

        /**
         * Exact GLES translation of MGC's interpolate_flow.cl/GetInterpolatedFlow.
         *
         * Flow samples live at 8x8 Bayer-quad tile centres. Interpolation is cancelled for
         * the whole pixel when any of the four candidates differs from the current tile by
         * at least the configured per-axis threshold, so motion boundaries stay discontinuous.
         */
        vec4 interpolatedAlignment(
            ivec2 tileId,
            ivec2 offsetWithinTile,
            ivec2 alignmentSize
        ) {
            vec4 baseFlow = alignmentAt(tileId, alignmentSize);
            if (uInterpolationFlowTolerance <= 0.0) {
                return baseFlow;
            }

            bool leftHalf = offsetWithinTile.x <= 4;
            bool topHalf = offsetWithinTile.y <= 4;
            int tx0 = leftHalf ? tileId.x - 1 : tileId.x;
            int ty0 = topHalf ? tileId.y - 1 : tileId.y;
            ivec2 tile00 = ivec2(tx0, ty0);
            ivec2 tile10 = tile00 + ivec2(1, 0);
            ivec2 tile01 = tile00 + ivec2(0, 1);
            ivec2 tile11 = tile00 + ivec2(1, 1);
            vec2 flow00 = alignmentAt(tile00, alignmentSize).xy;
            vec2 flow10 = alignmentAt(tile10, alignmentSize).xy;
            vec2 flow01 = alignmentAt(tile01, alignmentSize).xy;
            vec2 flow11 = alignmentAt(tile11, alignmentSize).xy;

            float threshold = 8.0 * uInterpolationFlowTolerance;
            bool cancelInterpolation =
                any(greaterThanEqual(abs(flow00 - baseFlow.xy), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow10 - baseFlow.xy), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow01 - baseFlow.xy), vec2(threshold))) ||
                any(greaterThanEqual(abs(flow11 - baseFlow.xy), vec2(threshold)));
            if (cancelInterpolation) {
                return baseFlow;
            }

            ivec2 pixelPosition = tileId * 8 + offsetWithinTile;
            float ux = float(pixelPosition.x) / 8.0 - (float(tx0) + 0.5);
            float uy = float(pixelPosition.y) / 8.0 - (float(ty0) + 0.5);
            vec2 flow = mix(
                mix(flow00, flow10, ux),
                mix(flow01, flow11, ux),
                uy
            );
            return vec4(flow, baseFlow.zw);
        }

        void main() {
            ivec2 outputPixel = ivec2(gl_FragCoord.xy);
            ivec2 phase = outputPixel & ivec2(1);
            int phaseChannel = phaseIndex(phase);
            ivec2 outputQuad = outputPixel / 2;
            // MergeBayerRaw16 addresses the converted alignment as one texel per
            // 8x8 Bayer-quad tile. X/Y are displacements in Bayer-quad units.
            // There is no normalized-UV conversion or filtering at this stage.
            ivec2 tileId = outputQuad / 8;
            ivec2 offsetWithinTile = outputQuad - tileId * 8;
            ivec2 alignmentSize = max(textureSize(uAlignment, 0), ivec2(1));
            vec2 alignmentQuadOffset = interpolatedAlignment(
                tileId,
                offsetWithinTile,
                alignmentSize
            ).xy;
            vec2 tilePosition =
                vec2(tileId * 8) + alignmentQuadOffset;
            ivec2 alignedTileQuad = ivec2(roundEven(tilePosition));
            vec2 subquadPixelOffset =
                2.0 * (vec2(alignedTileQuad) - tilePosition);
            ivec2 anchor = alignedTileQuad + offsetWithinTile;
            // MGC samples the quarter-resolution rejection image separately for all four
            // Bayer phases. In normalized GLES coordinates this is exactly the RAW-pixel
            // center, so adjacent phases retain their own linearly interpolated confidence
            // instead of sharing one nearest 4x4 RAW block.
            vec2 rawPixelUv =
                (vec2(outputPixel) + vec2(0.5)) / vec2(uRawSize);
            float frameWeight = uUseFrameWeight != 0
                ? texture(uFrameWeight, rawPixelUv).r
                : 1.0;
            // UpdateLinearKernelMask is sampled once at the center of each Bayer quad.
            vec2 quadCenterUv =
                (2.0 * vec2(outputQuad) + vec2(1.0)) / vec2(uRawSize);
            float linearKernelMix = texture(
                uLinearKernelMask,
                quadCenterUv
            ).r;
            ivec2 quadExtent = max(uRawSize / 2, ivec2(1));
            float kernelSigmaSquared = uKernelSigma * uKernelSigma;
            float intensity = 0.0;
            float accumulatedWeight = 0.0;
            float accumulatedWeightSquared = 0.0;
            for (int y = -1; y <= 1; ++y) {
                float sampleOffsetY =
                    subquadPixelOffset.y + 2.0 * float(y);
                if (abs(sampleOffsetY) > 2.5) continue;
                for (int x = -1; x <= 1; ++x) {
                    vec2 sampleOffset =
                        subquadPixelOffset + 2.0 * vec2(x, y);
                    ivec2 quad = mirrorQuad(
                        anchor + ivec2(x, y),
                        quadExtent
                    );
                    ivec2 rawPixel = quad * 2 + phase;
                    if (
                        abs(sampleOffset.x) <= 1.5 &&
                        abs(sampleOffset.y) <= 1.5
                    ) {
                        float rawValue = float(
                            texelFetch(uRaw, rawPixel, 0).r
                        );
                        float normalized =
                            rawValue * uGains[phaseChannel] +
                            uBlackLevelsTimesGains[phaseChannel];
                        float weight = mix(
                            kernelWeight(
                                sampleOffset,
                                kernelSigmaSquared
                            ),
                            linearKernelWeight(sampleOffset),
                            linearKernelMix
                        );
                        intensity += normalized * weight;
                        accumulatedWeight += weight;
                        accumulatedWeightSquared += weight * weight;
                    }

                    bool diagonalGreenPair =
                        (uCfaPattern == 0 || uCfaPattern == 3) &&
                        (phaseChannel == 1 || phaseChannel == 2);
                    bool cornerGreenPair =
                        (uCfaPattern == 1 || uCfaPattern == 2) &&
                        (phaseChannel == 0 || phaseChannel == 3);
                    // SampleNeighborhoodDualKernel always merges the two green lattices.
                    // The linear-kernel mask only selects the kernel shape; it does not enable
                    // or disable this cross-phase green support.
                    if (
                        (diagonalGreenPair || cornerGreenPair)
                    ) {
                        int otherPhase = phaseChannel;
                        vec2 diagonalOffset = vec2(0.0);
                        if (diagonalGreenPair) {
                            if (phaseChannel == 1) {
                                otherPhase = 2;
                                diagonalOffset = vec2(-1.0, 1.0);
                            } else {
                                otherPhase = 1;
                                diagonalOffset = vec2(1.0, -1.0);
                            }
                        } else if (phaseChannel == 0) {
                            otherPhase = 3;
                            diagonalOffset = vec2(1.0);
                        } else {
                            otherPhase = 0;
                            diagonalOffset = vec2(-1.0);
                        }
                        vec2 otherPixelOffset =
                            sampleOffset + diagonalOffset;
                        if (
                            abs(otherPixelOffset.x) <= 1.5 &&
                            abs(otherPixelOffset.y) <= 1.5
                        ) {
                            ivec2 otherPhaseCoordinate = ivec2(
                                otherPhase & 1,
                                otherPhase >> 1
                            );
                            ivec2 otherRawPixel =
                                quad * 2 + otherPhaseCoordinate;
                            float otherRawValue = float(
                                texelFetch(uRaw, otherRawPixel, 0).r
                            );
                            float otherNormalized =
                                otherRawValue * uGains[otherPhase] +
                                uBlackLevelsTimesGains[otherPhase];
                            float otherWeight = mix(
                                kernelWeight(
                                    otherPixelOffset,
                                    kernelSigmaSquared
                                ),
                                linearKernelWeight(otherPixelOffset),
                                linearKernelMix
                            );
                            intensity += otherNormalized * otherWeight;
                            accumulatedWeight += otherWeight;
                            accumulatedWeightSquared += otherWeight * otherWeight;
                        }
                    }
                }
            }
            /* IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS
             * Preserve the tested 26522 Bayer signal and normalization channels exactly:
             *   r = weighted signal, g = sum of Spatial sample weights * temporal robustness.
             *
             * b accumulates the variance weight sum over INDIVIDUAL same-CFA observations:
             *   sum(frameWeight^2 * sum(kernelWeight_i^2)).
             * a stores the reference frame's own normalized Spatial-kernel variance once.
             * Together these yield frame-equivalent noise support relative to the reference
             * frame's own reconstruction kernel, without confusing kernel geometry with temporal
             * rejection as 26522 did.
             */
            float contributionWeight = accumulatedWeight * frameWeight;
            float contributionVarianceWeight =
                accumulatedWeightSquared * frameWeight * frameWeight;
            float referenceNormalizedKernelVariance = uUseFrameWeight == 0
                ? accumulatedWeightSquared /
                    max(accumulatedWeight * accumulatedWeight, 1.0e-12)
                : 0.0;
            oBayerAndWeight = vec4(
                intensity * frameWeight,
                contributionWeight,
                contributionVarianceWeight,
                referenceNormalizedKernelVariance
            );
        }
    """.trimIndent()

    /* IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8 */
    val normalDngSupportQ8 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBayerAndWeight;
        uniform ivec2 uSourceSize;
        uniform ivec2 uOutputSize;
        uniform float uMaximumFrames;
        layout(location = 0) out highp uint oSupportQ8;
        void main() {
            ivec2 q = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                uOutputSize - ivec2(1)
            );
            vec2 uv = (vec2(q) + vec2(0.5)) / vec2(uOutputSize);
            ivec2 p = clamp(
                ivec2(floor(uv * vec2(uSourceSize))),
                ivec2(0),
                uSourceSize - ivec2(1)
            );
            vec4 accumulated = texelFetch(uBayerAndWeight, p, 0);
            float sumW = max(accumulated.g, 0.0);
            float sumIndividualW2 = max(accumulated.b, 0.0);
            float referenceNormalizedVariance = max(accumulated.a, 0.0);
            float effective = 1.0;
            if (sumW > 1.0e-8 && sumIndividualW2 > 1.0e-12 &&
                referenceNormalizedVariance > 1.0e-12) {
                effective = referenceNormalizedVariance * sumW * sumW / sumIndividualW2;
            }
            effective = clamp(effective, 1.0, max(uMaximumFrames, 1.0));
            oSupportQ8 = uint(round(effective * 256.0));
        }
    """.trimIndent()


    /** IRIS_26529_C317_RGB16UI_TO_RGBA16F */
    val copyRgb16ToFloat = """
        #version 310 es
        precision highp float;
        precision highp int;
        precision highp uimage2D;
        precision highp image2D;
        layout(local_size_x = 8, local_size_y = 8) in;
        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uRgb16;
        layout(rgba16f, binding = 1) writeonly uniform highp image2D uRgb16f;
        uniform ivec2 uImageSize;

        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, uImageSize))) return;
            uvec3 encoded = imageLoad(uRgb16, p).rgb;
            imageStore(uRgb16f, p, vec4(vec3(encoded) * (1.0 / 65535.0), 1.0));
        }
    """.trimIndent()

    val normalizeBayer = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBayerAndWeight;
        uniform ivec2 uOutputSize;
        uniform float uOutputExposureScale;
        layout(location = 0) out highp uint oBayer16;
        void main() {
            ivec2 p = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                uOutputSize - ivec2(1)
            );
            vec2 valueAndWeight = texelFetch(uBayerAndWeight, p, 0).rg;
            float normalized =
                valueAndWeight.x / max(valueAndWeight.y, 1.0e-8) *
                uOutputExposureScale;
            oBayer16 = uint(round(clamp(normalized, 0.0, 1.0) * 65535.0));
        }
    """.trimIndent()

    /**
     * Packs the full-resolution normalized Bayer mosaic into MGC Fixed16.
     *
     * DownsampleRawF16ToFloatTileSize16 does not consume IEEE FP16. Its F16
     * input is signed Q14 and has Halide dimensions [quadX, quadY, phase].
     * The four phase planes are stacked vertically so the readback has the
     * same conventional planar strides requested by the Halide bounds query:
     *
     *   address = quadX + quadY * quadWidth
     *       + phase * quadWidth * quadHeight
     */
    val packBayerFixed16 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBayerAndWeight;
        uniform ivec2 uSourceSize;
        uniform ivec2 uQuadSize;
        layout(location = 0) out highp int oBayerFixed16;
        void main() {
            ivec2 irisPackedBits26986 = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                ivec2(uQuadSize.x - 1, uQuadSize.y * 4 - 1)
            );
            int phase = irisPackedBits26986.y / uQuadSize.y;
            ivec2 quad = ivec2(irisPackedBits26986.x, irisPackedBits26986.y - phase * uQuadSize.y);
            ivec2 phaseOffset = ivec2(phase & 1, phase >> 1);
            ivec2 source = min(quad * 2 + phaseOffset, uSourceSize - ivec2(1));
            vec2 valueAndWeight = texelFetch(uBayerAndWeight, source, 0).rg;
            float normalized = max(
                valueAndWeight.x / max(valueAndWeight.y, 1.0e-8),
                0.0
            );
            oBayerFixed16 = int(round(clamp(normalized * 16384.0, 0.0, 32767.0)));
        }
    """.trimIndent()

    /**
     * Raw16ToGrayHalide (0x3bbaf98): one value per Bayer quad, phase black
     * subtraction, scalar gain, equal RGGB average and separable 1:2:1 filtering.
     */
    val rawToGray = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uGraySize;
        uniform int uCfaPattern;
        uniform vec4 uBlackLevels;
        uniform float uGain;
        layout(location = 0) out highp uint oGray;

        vec4 canonicalQuad(ivec2 q) {
            ivec2 p = clamp(q * 2, ivec2(0), uRawSize - ivec2(2));
            float p00 = float(texelFetch(uRaw, p, 0).r);
            float p10 = float(texelFetch(uRaw, p + ivec2(1, 0), 0).r);
            float p01 = float(texelFetch(uRaw, p + ivec2(0, 1), 0).r);
            float p11 = float(texelFetch(uRaw, p + ivec2(1, 1), 0).r);
            vec4 v;
            if (uCfaPattern == 0) v = vec4(p00, p10, p01, p11);
            else if (uCfaPattern == 1) v = vec4(p10, p00, p11, p01);
            else if (uCfaPattern == 2) v = vec4(p01, p11, p00, p10);
            else v = vec4(p11, p01, p10, p00);
            return max(v - uBlackLevels, vec4(0.0)) * uGain;
        }

        float grayAt(ivec2 q) {
            return dot(canonicalQuad(q), vec4(0.25));
        }

        void main() {
            ivec2 q = ivec2(gl_FragCoord.xy);
            float value = 0.0;
            for (int y = -1; y <= 1; ++y) {
                float wy = y == 0 ? 0.5 : 0.25;
                for (int x = -1; x <= 1; ++x) {
                    float wx = x == 0 ? 0.5 : 0.25;
                    value += grayAt(q + ivec2(x, y)) * wx * wy;
                }
            }
            // DownsampleRawToGrayHalide hands AlignPyramid an S16 buffer.
            oGray = uint(clamp(round(value), 0.0, 32767.0));
        }
    """.trimIndent()

    val grayDownsample = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uInput;
        uniform ivec2 uInputSize;
        layout(location = 0) out highp uint oGray;
        float valueAt(ivec2 p) {
            return float(texelFetch(
                uInput,
                clamp(p, ivec2(0), uInputSize - ivec2(1)),
                0
            ).r);
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) * 2;
            float value = 0.0;
            for (int y = -1; y <= 1; ++y) {
                float wy = y == 0 ? 0.5 : 0.25;
                for (int x = -1; x <= 1; ++x) {
                    float wx = x == 0 ? 0.5 : 0.25;
                    value += valueAt(p + ivec2(x, y)) * wx * wy;
                }
            }
            oGray = uint(clamp(round(value), 0.0, 32767.0));
        }
    """.trimIndent()

    /**
     * GradientAndGradientProductsHalide (0x3ba9244). The generated kernel stores central
     * differences as saturated S16 and five per-tile Float32 products in this order:
     * xx, yy, xy, base*x and base*y.
     */
    val alignmentGradientProducts = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReference;
        uniform ivec2 uImageSize;
        uniform int uTileStride;
        uniform int uTileSize;
        uniform int uNormalize;
        layout(location = 0) out vec4 oProducts0;
        layout(location = 1) out float oProducts1;

        float valueAt(ivec2 p) {
            return min(
                float(texelFetch(
                    uReference,
                    clamp(p, ivec2(0), uImageSize - ivec2(1)),
                    0
                ).r),
                32767.0
            );
        }
        vec2 gradientAt(ivec2 p) {
            return clamp(
                vec2(
                    valueAt(p + ivec2(1, 0)) - valueAt(p - ivec2(1, 0)),
                    valueAt(p + ivec2(0, 1)) - valueAt(p - ivec2(0, 1))
                ),
                vec2(-32768.0),
                vec2(32767.0)
            );
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            // Halide's LK buffers have min=(1,1); the texture stores only that
            // interior extent, so local texel zero is logical tile (1,1).
            ivec2 origin = (tile + ivec2(1)) * uTileStride;
            float count = float(uTileSize * uTileSize);
            float meanBase = 0.0;
            if (uNormalize != 0) {
                for (int y = 0; y < 64; ++y) {
                    if (y >= uTileSize) break;
                    for (int x = 0; x < 64; ++x) {
                        if (x >= uTileSize) break;
                        meanBase += valueAt(origin + ivec2(x, y));
                    }
                }
                meanBase /= count;
            }

            float xx = 0.0;
            float yy = 0.0;
            float xy = 0.0;
            float baseX = 0.0;
            float baseY = 0.0;
            for (int y = 0; y < 64; ++y) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 64; ++x) {
                    if (x >= uTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    vec2 gradient = gradientAt(p);
                    float base = valueAt(p) - meanBase;
                    xx += gradient.x * gradient.x;
                    yy += gradient.y * gradient.y;
                    xy += gradient.x * gradient.y;
                    baseX += base * gradient.x;
                    baseY += base * gradient.y;
                }
            }
            float inverseCount = 1.0 / count;
            oProducts0 = vec4(
                0.25 * xx * inverseCount,
                0.25 * yy * inverseCount,
                0.25 * xy * inverseCount,
                0.5 * baseX * inverseCount
            );
            oProducts1 = 0.5 * baseY * inverseCount;
        }
    """.trimIndent()

    /**
     * UpsampleAlignmentI16Halide (0x3be8da0, three-candidate worker 0x3be8048).
     * Tile centers, rather than tile origins, determine the nearest coarse flow and
     * the next-nearest flow on each axis. The three whole candidates are evaluated
     * against the target-level S16 images, avoiding a synthesized motion vector
     * across an alignment discontinuity.
     */
    val upsampleAlignment = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReference;
        uniform highp usampler2D uCurrent;
        uniform sampler2D uInitialAlignment;
        uniform ivec2 uImageSize;
        uniform ivec2 uInitialGridSize;
        uniform int uInitialGridMin;
        uniform int uTargetGridMin;
        uniform int uInitialTileStride;
        uniform int uTargetTileStride;
        uniform int uTargetTileSize;
        uniform float uInitialScale;
        out vec4 oAlignment;

        float valueAt(highp usampler2D image, ivec2 p) {
            return min(
                float(texelFetch(
                    image,
                    clamp(p, ivec2(0), uImageSize - ivec2(1)),
                    0
                ).r),
                32767.0
            );
        }
        ivec2 boundedInitialTile(ivec2 p) {
            return clamp(p, ivec2(0), uInitialGridSize - ivec2(1));
        }
        vec2 candidateFlow(ivec2 p) {
            return texelFetch(
                uInitialAlignment,
                boundedInitialTile(p),
                0
            ).xy * uInitialScale;
        }
        float candidateCost(ivec2 origin, vec2 flow) {
            // The AArch64 worker rounds each candidate to an integer S16-image
            // displacement for the block L1 comparison.
            ivec2 displacement = ivec2(roundEven(flow));
            float cost = 0.0;
            for (int y = 0; y < 64; ++y) {
                if (y >= uTargetTileSize) break;
                for (int x = 0; x < 64; ++x) {
                    if (x >= uTargetTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    cost += abs(
                        valueAt(uReference, p) -
                        valueAt(uCurrent, p + displacement)
                    );
                }
            }
            return cost / float(uTargetTileSize * uTargetTileSize);
        }
        void main() {
            ivec2 targetTile = ivec2(gl_FragCoord.xy);
            ivec2 targetLogicalTile =
                targetTile + ivec2(uTargetGridMin);
            // Express the target tile center in the initial alignment grid. Using
            // the tile origin here changes the nearest coarse tile at a regular
            // half-grid cadence and produces block-shaped alignment discontinuities.
            vec2 targetCenter =
                (vec2(targetLogicalTile) + vec2(0.5)) *
                float(uTargetTileStride);
            vec2 initialGrid =
                targetCenter /
                (uInitialScale * float(uInitialTileStride)) -
                vec2(float(uInitialGridMin) + 0.5);

            vec2 nearestPosition = roundEven(initialGrid);
            ivec2 nearest = ivec2(nearestPosition);
            ivec2 nextX = nearest + ivec2(
                initialGrid.x < nearestPosition.x ? -1 : 1,
                0
            );
            ivec2 nextY = nearest + ivec2(
                0,
                initialGrid.y < nearestPosition.y ? -1 : 1
            );
            nearest = boundedInitialTile(nearest);
            nextX = boundedInitialTile(nextX);
            nextY = boundedInitialTile(nextY);

            ivec2 origin = targetLogicalTile * uTargetTileStride;
            vec2 bestFlow = candidateFlow(nearest);
            float bestCost = candidateCost(origin, bestFlow);
            float candidateIndex = 0.0;

            vec2 flowX = candidateFlow(nextX);
            float costX = candidateCost(origin, flowX);
            if (costX < bestCost) {
                bestFlow = flowX;
                bestCost = costX;
                candidateIndex = 1.0;
            }

            vec2 flowY = candidateFlow(nextY);
            float costY = candidateCost(origin, flowY);
            if (costY < bestCost) {
                bestFlow = flowY;
                bestCost = costY;
                candidateIndex = 2.0;
            }
            oAlignment = vec4(bestFlow, bestCost, candidateIndex);
        }
    """.trimIndent()

    /**
     * BlockLucasKanadeHalide (0x3b9be68, workers 0x3b9cb5c/0x3b9e72c). One draw is
     * one generated-kernel iteration. Its input has already been expanded onto this LK
     * grid by UpsampleAlignment. Bilinear weights below are the image-warp S16 Q15
     * conversion and saturating rounded shift used by the AArch64 worker.
     */
    val blockLucasKanade = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReference;
        uniform highp usampler2D uCurrent;
        uniform sampler2D uProducts0;
        uniform sampler2D uProducts1;
        uniform sampler2D uInitialAlignment;
        uniform ivec2 uImageSize;
        uniform ivec2 uGridSize;
        uniform int uTileStride;
        uniform int uTileSize;
        uniform int uNormalize;
        uniform int uHasInitialAlignment;
        out vec4 oAlignment;

        float referenceAt(ivec2 p) {
            return min(
                float(texelFetch(
                    uReference,
                    clamp(p, ivec2(0), uImageSize - ivec2(1)),
                    0
                ).r),
                32767.0
            );
        }
        vec2 gradientAt(ivec2 p) {
            return clamp(
                vec2(
                    referenceAt(p + ivec2(1, 0)) -
                        referenceAt(p - ivec2(1, 0)),
                    referenceAt(p + ivec2(0, 1)) -
                        referenceAt(p - ivec2(0, 1))
                ),
                vec2(-32768.0),
                vec2(32767.0)
            );
        }
        float currentAt(ivec2 p) {
            return min(
                float(texelFetch(
                    uCurrent,
                    clamp(p, ivec2(0), uImageSize - ivec2(1)),
                    0
                ).r),
                32767.0
            );
        }
        float q15Weight(float value) {
            return clamp(floor(value * 32768.0), 0.0, 32767.0);
        }
        float warpedCurrentAt(vec2 p) {
            vec2 bounded = clamp(
                p,
                vec2(0.0),
                vec2(uImageSize - ivec2(1))
            );
            ivec2 p0 = ivec2(floor(bounded));
            vec2 fraction = fract(bounded);
            float w00 = q15Weight((1.0 - fraction.x) * (1.0 - fraction.y));
            float w10 = q15Weight(fraction.x * (1.0 - fraction.y));
            float w01 = q15Weight((1.0 - fraction.x) * fraction.y);
            float w11 = q15Weight(fraction.x * fraction.y);
            float weighted =
                currentAt(p0) * w00 +
                currentAt(p0 + ivec2(1, 0)) * w10 +
                currentAt(p0 + ivec2(0, 1)) * w01 +
                currentAt(p0 + ivec2(1, 1)) * w11;
            return clamp(
                floor((weighted + 16384.0) / 32768.0),
                -32768.0,
                32767.0
            );
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            vec2 flow = uHasInitialAlignment != 0
                ? texelFetch(
                    uInitialAlignment,
                    clamp(tile, ivec2(0), uGridSize - ivec2(1)),
                    0
                ).xy
                : vec2(0.0);
            ivec2 origin = (tile + ivec2(1)) * uTileStride;
            float count = float(uTileSize * uTileSize);
            float meanCurrent = 0.0;
            if (uNormalize != 0) {
                for (int y = 0; y < 64; ++y) {
                    if (y >= uTileSize) break;
                    for (int x = 0; x < 64; ++x) {
                        if (x >= uTileSize) break;
                        meanCurrent += warpedCurrentAt(
                            vec2(origin + ivec2(x, y)) + flow
                        );
                    }
                }
                meanCurrent /= count;
            }

            float targetX = 0.0;
            float targetY = 0.0;
            for (int y = 0; y < 64; ++y) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 64; ++x) {
                    if (x >= uTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    float current = warpedCurrentAt(vec2(p) + flow) - meanCurrent;
                    vec2 gradient = gradientAt(p);
                    targetX += current * gradient.x;
                    targetY += current * gradient.y;
                }
            }
            vec4 products0 = texelFetch(uProducts0, tile, 0);
            float products1 = texelFetch(uProducts1, tile, 0).r;
            float bx = 0.5 * targetX / count - products0.w;
            float by = 0.5 * targetY / count - products1;
            float inverseDeterminant = 1.0 / (
                1.0 +
                products0.x * products0.y -
                products0.z * products0.z
            );
            vec2 delta = inverseDeterminant * vec2(
                products0.z * by - products0.y * bx,
                products0.z * bx - products0.x * by
            );
            flow += clamp(delta, vec2(-1.0), vec2(1.0));
            oAlignment = vec4(flow, 0.0, 0.0);
        }
    """.trimIndent()

    /**
     * AlignL1Halide UInt16 path (0x3be3c58). Candidate ties retain the first
     * candidate. The quadratic correction is exactly
     * .5*(Eminus-Eplus)/(Eminus+Eplus-2*Ecenter).
     */
    val alignL1 = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uReference;
        uniform highp usampler2D uCurrent;
        uniform sampler2D uInitialAlignment;
        uniform ivec2 uImageSize;
        uniform ivec2 uGridSize;
        uniform ivec2 uInitialGridSize;
        uniform int uTileStride;
        uniform int uTileSize;
        uniform int uSearchRadius;
        uniform float uInitialScale;
        uniform int uHasInitialAlignment;
        out vec4 oAlignment;

        float valueAt(highp usampler2D image, ivec2 p) {
            return float(texelFetch(
                image,
                clamp(p, ivec2(0), uImageSize - ivec2(1)),
                0
            ).r);
        }
        float sadAt(ivec2 origin, ivec2 displacement) {
            float sad = 0.0;
            for (int y = 0; y < 16; ++y) {
                if (y >= uTileSize) break;
                for (int x = 0; x < 16; ++x) {
                    if (x >= uTileSize) break;
                    ivec2 p = origin + ivec2(x, y);
                    sad += abs(
                        valueAt(uReference, p) -
                        valueAt(uCurrent, p + displacement)
                    );
                }
            }
            return sad / float(uTileSize * uTileSize);
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            ivec2 initialTile = clamp(
                ivec2(
                    floor(
                        (vec2(tile) + 0.5) *
                        vec2(uInitialGridSize) / vec2(uGridSize)
                    )
                ),
                ivec2(0),
                uInitialGridSize - ivec2(1)
            );
            vec2 initial = uHasInitialAlignment != 0
                ? texelFetch(uInitialAlignment, initialTile, 0).xy * uInitialScale
                : vec2(0.0);
            ivec2 center = ivec2(round(initial));
            ivec2 origin = tile * uTileStride;
            ivec2 best = center;
            float bestCost = sadAt(origin, center);
            for (int y = -3; y <= 3; ++y) {
                for (int x = -3; x <= 3; ++x) {
                    if (abs(x) > uSearchRadius || abs(y) > uSearchRadius) continue;
                    if (x == 0 && y == 0) continue;
                    ivec2 candidate = center + ivec2(x, y);
                    float cost = sadAt(origin, candidate);
                    if (cost < bestCost) {
                        bestCost = cost;
                        best = candidate;
                    }
                }
            }
            float minusX = sadAt(origin, best - ivec2(1, 0));
            float plusX = sadAt(origin, best + ivec2(1, 0));
            float minusY = sadAt(origin, best - ivec2(0, 1));
            float plusY = sadAt(origin, best + ivec2(0, 1));
            float denomX = minusX + plusX - 2.0 * bestCost;
            float denomY = minusY + plusY - 2.0 * bestCost;
            float subX = abs(denomX) > 1.0e-12
                ? 0.5 * (minusX - plusX) / denomX
                : 0.0;
            float subY = abs(denomY) > 1.0e-12
                ? 0.5 * (minusY - plusY) / denomY
                : 0.0;
            oAlignment = vec4(vec2(best) + clamp(vec2(subX, subY), -0.5, 0.5),
                bestCost, 0.0);
        }
    """.trimIndent()

    /** Component-wise 3x3 median used by the alignment graph. */
    val medianAlignment = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAlignment;
        uniform ivec2 uGridSize;
        out vec4 oAlignment;
        float median9(float v[9]) {
            for (int i = 1; i < 9; ++i) {
                float x = v[i];
                int j = i - 1;
                while (j >= 0 && v[j] > x) {
                    v[j + 1] = v[j];
                    --j;
                }
                v[j + 1] = x;
            }
            return v[4];
        }
        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy);
            float x[9];
            float y[9];
            float z[9];
            int i = 0;
            for (int oy = -1; oy <= 1; ++oy) {
                for (int ox = -1; ox <= 1; ++ox) {
                    vec3 v = texelFetch(
                        uAlignment,
                        clamp(p + ivec2(ox, oy), ivec2(0), uGridSize - ivec2(1)),
                        0
                    ).xyz;
                    x[i] = v.x;
                    y[i] = v.y;
                    z[i] = v.z;
                    ++i;
                }
            }
            oAlignment = vec4(median9(x), median9(y), median9(z), 0.0);
        }
    """.trimIndent()

    /**
     * ConvertAlignment (0x35cf3ec): evaluate the same edge-aware tile-centre interpolation as
     * MergeBayerRaw, convert it to normalized UV displacement, and store the pre-interpolation
     * local 3x3 range in B.
     */
    /**
     * ConvertAlignmentHalide: preserve the sparse alignment grid while converting Bayer-quad
     * displacements to normalized UV and storing the local 3x3 flow range in B. Current MGC
     * performs guarded interpolation only in the merge shader, never in this transport stage.
     */
    val convertAlignment = """
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
     * IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT
     *
     * Spatial-only backport of bjzhou 1b84bf86 after the b0d4c692 alignment correction.
     * Resamples the finest LK grid continuously onto MergeBayerRaw16's one-sample-per-8x8-
     * Bayer-quad alignment contract. The discontinuity gate intentionally remains only in the
     * actual merge-domain consumer (mergeBayer/mergeRgb), where it cannot quantize motion at the
     * coarser finest-LK cadence into 64-RAW-pixel constant-flow blocks.
     */
    val strengthAlignment = """
        #version 300 es
        precision highp float;
        precision highp int;
        /* IRIS_26530_V1_3_FINAL_BAYER_ALIGNMENT_AUTHORITY */
        uniform sampler2D uAlignment;
        uniform ivec2 uOutputSize;
        uniform ivec2 uOutputOrigin;
        uniform int uComponent;
        out float oAlignment;
        void main() {
            vec2 local = gl_FragCoord.xy - vec2(uOutputOrigin);
            vec2 uv = local / vec2(uOutputSize);
            oAlignment = texture(uAlignment, uv)[uComponent];
        }
    """.trimIndent()

    val strengthRejection = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uWeight;
        uniform ivec2 uOutputSize;
        uniform ivec2 uOutputOrigin;
        uniform int uIdentityWeight;
        out float oRejection;
        void main() {
            vec2 local = gl_FragCoord.xy - vec2(uOutputOrigin);
            vec2 uv = local / vec2(uOutputSize);
            oRejection = uIdentityWeight != 0 ? 1.0 : texture(uWeight, uv).r;
        }
    """.trimIndent()

    /**
     * UnblockerRaw10Halide (0x35dd50c), operating on unpacked native RAW values.
     *
     * The original receives fullres_tile_size=8, scale=1 and offset=0.45. Each output cell
     * therefore covers an 8x8 Bayer-quad / 16x16 full-resolution region. The 128/9 variance
     * factor, four-noise subtraction, sqrt, offset/scale mapping and byte-domain truncation are
     * retained.
     */
    val unblocker = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uRaw;
        uniform ivec2 uRawSize;
        uniform ivec2 uGridSize;
        uniform int uCfaPattern;
        uniform float uBlackLevelGreen;
        uniform float uNoiseQuadratic;
        uniform float uNoiseScale;
        uniform float uNoiseOffset;
        uniform float uOutputScale;
        uniform float uOutputOffset;
        out float oUnblocker;

        vec2 greensAt(ivec2 q) {
            ivec2 p = clamp(q * 2, ivec2(0), uRawSize - ivec2(2));
            float p00 = float(texelFetch(uRaw, p, 0).r);
            float p10 = float(texelFetch(uRaw, p + ivec2(1, 0), 0).r);
            float p01 = float(texelFetch(uRaw, p + ivec2(0, 1), 0).r);
            float p11 = float(texelFetch(uRaw, p + ivec2(1), 0).r);
            vec4 v;
            if (uCfaPattern == 0) v = vec4(p00, p10, p01, p11);
            else if (uCfaPattern == 1) v = vec4(p10, p00, p11, p01);
            else if (uCfaPattern == 2) v = vec4(p01, p11, p00, p10);
            else v = vec4(p11, p01, p10, p00);
            return v.yz;
        }
        float averageGreen(ivec2 q) {
            q = clamp(q, ivec2(0), (uRawSize / 2) - ivec2(1));
            vec2 g = greensAt(q);
            return 0.5 * (g.x + g.y);
        }
        float blurredGreen(ivec2 q) {
            float value = 0.0;
            for (int y = -1; y <= 1; ++y) {
                float wy = y == 0 ? 0.5 : 0.25;
                for (int x = -1; x <= 1; ++x) {
                    float wx = x == 0 ? 0.5 : 0.25;
                    value += averageGreen(q + ivec2(x, y)) * wx * wy;
                }
            }
            return value;
        }
        void main() {
            ivec2 tile = ivec2(gl_FragCoord.xy);
            ivec2 origin = tile * 8;
            float preSum = 0.0;
            float preSquareSum = 0.0;
            float postSum = 0.0;
            float postSquareSum = 0.0;
            for (int y = 0; y < 8; ++y) {
                for (int x = 0; x < 8; ++x) {
                    ivec2 q = origin + ivec2(x, y);
                    vec2 g = greensAt(clamp(
                        q, ivec2(0), (uRawSize / 2) - ivec2(1)
                    ));
                    float b = blurredGreen(q);
                    preSum += g.x + g.y;
                    preSquareSum += dot(g, g);
                    postSum += b;
                    postSquareSum += b * b;
                }
            }
            float preCount = 128.0;
            float postCount = 64.0;
            float preMean = preSum / preCount;
            float postMean = postSum / postCount;
            float preVariance = max(
                preSquareSum / preCount - preMean * preMean,
                0.0
            );
            float postVariance = max(
                postSquareSum / postCount - postMean * postMean,
                0.0
            );
            float signal = max(preMean - uBlackLevelGreen, 0.0);
            float predictedNoise =
                (uNoiseQuadratic * signal + uNoiseScale) * signal +
                uNoiseOffset;
            float correctedVariance = max(
                preVariance - 4.0 * predictedNoise,
                0.0
            );
            float denominator = postVariance * (128.0 / 9.0);
            float ratio = denominator > 0.0
                ? correctedVariance / denominator
                : 0.0;
            float mapped = uOutputScale * (
                sqrt(max(ratio, 0.0)) - uOutputOffset
            );
            // The AOT converts with fcvtzs before storing U8. Quantize explicitly so the
            // normalized GL_R8 conversion cannot round a boundary upward.
            oUnblocker = floor(clamp(mapped, 0.0, 1.0) * 255.0) / 255.0;
        }
    """.trimIndent()

}
