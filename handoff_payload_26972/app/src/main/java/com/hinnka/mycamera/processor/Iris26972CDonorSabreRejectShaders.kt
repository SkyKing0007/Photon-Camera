package com.hinnka.mycamera.processor

/**
 * Experiment C only. Pinned bjzhou/PhotonCamera 1.29.0
 * GlesMgcRawSabreShaders.sampleBicubicAbsolute/baseFrameReferenceColor/rejection.
 * NOT a replacement for the guide, covariance, flow, unblocker, dilation or RAW stages.
 */
internal object Iris26972CDonorSabreRejectShaders {
    private val sampleBicubicAbsolute = """
        vec4 sampleBicubicAbsolute(sampler2D image, vec2 uv) {
            vec2 pixel = uv * vec2(uGuideSize) + 0.5;
            vec2 integerPixel = floor(pixel);
            vec2 a = fract(pixel);
            vec2 w0 = (1.0 / 6.0) * (a * (a * (-a + 3.0) - 3.0) + 1.0);
            vec2 w1 = (1.0 / 6.0) * (a * a * (3.0 * a - 6.0) + 4.0);
            vec2 w2 = (1.0 / 6.0) * (a * (a * (-3.0 * a + 3.0) + 3.0) + 1.0);
            vec2 w3 = (1.0 / 6.0) * (a * a * a);
            vec2 g0 = w0 + w1;
            vec2 g1 = w2 + w3;
            vec2 h0 = -1.0 + w1 / g0;
            vec2 h1 = 1.0 + w3 / g1;
            vec2 reciprocalSize = 1.0 / vec2(uGuideSize);
            vec2 p0 = (integerPixel + h0 - 0.5) * reciprocalSize;
            vec2 p1 = (integerPixel + h1 - 0.5) * reciprocalSize;
            // Take abs after each bilinear lookup, exactly as MGC does: guide alpha stores
            // the green-only flag in its sign, while RGB and variance share the same filter.
            return g0.y * (
                g0.x * abs(texture(image, vec2(p0.x, p0.y))) +
                g1.x * abs(texture(image, vec2(p1.x, p0.y)))
            ) + g1.y * (
                g0.x * abs(texture(image, vec2(p0.x, p1.y))) +
                g1.x * abs(texture(image, vec2(p1.x, p1.y)))
            );
        }
    """.trimIndent()

    val baseFrameReferenceColor = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        uniform sampler2D uBaseGuide;
        uniform ivec2 uGuideSize;
        layout(location = 0) out vec4 oReferenceColor;

        ${sampleBicubicAbsolute.prependIndent("        ")}

        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(uGuideSize);
            vec4 reference = sampleBicubicAbsolute(uBaseGuide, uv);
            if (texture(uBaseGuide, uv).w < 0.0) reference.w = -reference.w;
            oReferenceColor = reference;
        }
    """.trimIndent()

    val rejection = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
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

        ${sampleBicubicAbsolute.prependIndent("        ")}

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
            vec4 current = sampleBicubicAbsolute(uAltGuide, warpedUv);
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
            float filterVarianceScale = greenOnly ? 0.211665 : 0.0898866;
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
}
