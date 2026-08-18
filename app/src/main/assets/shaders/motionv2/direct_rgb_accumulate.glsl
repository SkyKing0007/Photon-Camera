#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
uniform highp sampler2D previousNumerator;
uniform highp sampler2D previousDenominator;
uniform highp sampler2D previousFrameSupport;
uniform highp sampler2D chromaGuide;
layout(rgba32f,binding=0) uniform highp readonly image2D alterCov;
layout(rgba32f,binding=1) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=2) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 guideSize;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform float wbR;
uniform float wbB;
uniform float highlightClipThreshold;
uniform float highlightCeiling;
uniform float maximumSupport;
uniform float greenNoiseS;
uniform float greenNoiseO;

int phaseIndex(ivec2 p) {
    return ((p.y & 1) << 1) | (p.x & 1);
}

int colorFromPhase(int phase) {
    if (cfaPattern == 0) {
        if (phase == 0) return 0;
        if (phase == 3) return 2;
        return 1;
    }
    if (cfaPattern == 1) {
        if (phase == 1) return 0;
        if (phase == 2) return 2;
        return 1;
    }
    if (cfaPattern == 2) {
        if (phase == 2) return 0;
        if (phase == 1) return 2;
        return 1;
    }
    if (phase == 3) return 0;
    if (phase == 0) return 2;
    return 1;
}

float wbForColor(int color) {
    if (color == 0) return wbR;
    if (color == 2) return wbB;
    return 1.0;
}

ivec2 clampCoord(ivec2 p) {
    return clamp(p, ivec2(0), rawSize - ivec2(1));
}

float sensorNormalizedAt(ivec2 p) {
    p = clampCoord(p);
    int phase = phaseIndex(p);
    float rawValue = float(texelFetch(rawTexture, p, 0).r);
    float black = blackLevel[phase];
    float span = max(whiteLevel - black, 1.0);
    return max(rawValue - black, 0.0) / span;
}

float cameraSampleAt(ivec2 p) {
    return sensorNormalizedAt(p) * exposureScale;
}

float calculationSampleAt(ivec2 p) {
    p = clampCoord(p);
    int color = colorFromPhase(phaseIndex(p));
    return cameraSampleAt(p) * wbForColor(color);
}

/*
 * IRIS_26488_BJZHOU_HIGHLIGHT_CALCULATION_DOMAIN_CAMERA_FINALIZE_ONCE
 * The clipped-site estimate and ordinary interpolation stay in one white-balanced calculation
 * domain, matching bjzhou's current RCD contract. Camera-domain ownership is restored exactly
 * once by mfsr_finalize after semantic normalization. This repair does NOT change temporal
 * validity or frame rejection.
 */
float highlightCalculationSampleAt(ivec2 p) {
    p = clampCoord(p);
    int targetPhase = phaseIndex(p);
    int targetColor = colorFromPhase(targetPhase);
    float targetWb = max(wbForColor(targetColor), 1.0e-6);
    float sensor = sensorNormalizedAt(p);
    float cameraFallback = cameraSampleAt(p);
    float clipMask = smoothstep(highlightClipThreshold, 1.0, sensor);
    if (clipMask <= 0.0) {
        return cameraFallback * targetWb;
    }

    float sumRed = 0.0;
    float sumGreen = 0.0;
    float sumBlue = 0.0;
    float countRed = 0.0;
    float countGreen = 0.0;
    float countBlue = 0.0;
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            ivec2 q = clampCoord(p + ivec2(dx, dy));
            int sampleColor = colorFromPhase(phaseIndex(q));
            float balanced = calculationSampleAt(q);
            if (sampleColor == 0) {
                sumRed += balanced;
                countRed += 1.0;
            } else if (sampleColor == 1) {
                sumGreen += balanced;
                countGreen += 1.0;
            } else {
                sumBlue += balanced;
                countBlue += 1.0;
            }
        }
    }

    const float power = 3.0;
    float rootRed = pow(max(sumRed / max(countRed, 1.0), 0.0), 1.0 / power);
    float rootGreen = pow(max(sumGreen / max(countGreen, 1.0), 0.0), 1.0 / power);
    float rootBlue = pow(max(sumBlue / max(countBlue, 1.0), 0.0), 1.0 / power);
    float opposedRoot;
    if (targetColor == 0) {
        opposedRoot = 0.5 * (rootGreen + rootBlue);
    } else if (targetColor == 1) {
        opposedRoot = 0.5 * (rootRed + rootBlue);
    } else {
        opposedRoot = 0.5 * (rootRed + rootGreen);
    }
    float calculationFallback = cameraFallback * targetWb;
    float reconstructed = pow(max(opposedRoot, 0.0), power);
    reconstructed = min(max(reconstructed, calculationFallback), highlightCeiling);
    return mix(calculationFallback, reconstructed, clipMask);
}

float greenAt(ivec2 p) {
    return texelFetch(chromaGuide, clampCoord(p), 0).r;
}

float chromaWeight(float sampleGreen, float targetGreen) {
    float signal = max(max(sampleGreen, targetGreen), 0.0);
    float variance = max(greenNoiseS * signal + greenNoiseO, 0.0);
    float sigma = max(2.5 * sqrt(variance), 1.0 / 160.0);
    float d = (sampleGreen - targetGreen) / sigma;
    return exp(-0.5 * d * d);
}

mat2 precisionAt(ivec2 p) {
    p = clamp(p, ivec2(0), guideSize - ivec2(1));
    vec4 v = imageLoad(alterCov, p);
    return mat2(v.x, v.y, v.z, v.w);
}

mat2 interpolatePrecision(vec2 guidePosition) {
    ivec2 lower = clamp(ivec2(floor(guidePosition)), ivec2(0), guideSize - ivec2(1));
    ivec2 upper = min(lower + ivec2(1), guideSize - ivec2(1));
    vec2 f = fract(guidePosition);
    mat2 a = precisionAt(lower);
    mat2 b = precisionAt(ivec2(upper.x, lower.y));
    mat2 c = precisionAt(ivec2(lower.x, upper.y));
    mat2 d = precisionAt(upper);
    return a * ((1.0 - f.x) * (1.0 - f.y)) +
        b * (f.x * (1.0 - f.y)) +
        c * ((1.0 - f.x) * f.y) +
        d * (f.x * f.y);
}

float kernelWeight(vec2 pixelOffset, mat2 precisionMatrix) {
    float distance = max(dot(pixelOffset, precisionMatrix * pixelOffset), 0.0);
    return exp2(-0.5 * distance) + 0.00005;
}

void preserve(ivec2 p, float oob) {
    vec4 numerator = texelFetch(previousNumerator, p, 0);
    vec4 denominator = texelFetch(previousDenominator, p, 0);
    vec4 support = texelFetch(previousFrameSupport, p, 0);
    support.a += oob;
    imageStore(outNumerator, p, numerator);
    imageStore(outDenominator, p, denominator);
    imageStore(outFrameSupport, p, support);
}

/* IRIS_26488_BJZHOU_NATIVE_RAW_MERGERGB_NO_BLANKET_CENSOR */
void main() {
    ivec2 outP = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(outP, rawSize))) return;

    vec2 uv = (vec2(outP) + vec2(0.5)) / vec2(rawSize);
    vec2 rawFlow = 2.0 * texture(flowTexture, uv).xy;
    vec2 source = vec2(outP) + vec2(0.5) + rawFlow;
    if (source.x < 0.0 || source.y < 0.0 ||
        source.x >= float(rawSize.x) || source.y >= float(rawSize.y)) {
        preserve(outP, 1.0);
        return;
    }

    float frameWeight = clamp(texture(robustnessTexture, uv).r, 0.0, 1.0);
    mat2 precisionMatrix = interpolatePrecision(
        source * vec2(guideSize) / vec2(rawSize) - vec2(0.5)
    );
    ivec2 center = ivec2(floor(source));
    vec2 target = source - vec2(0.5);

    float greenSum = 0.0;
    float greenWeight = 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            ivec2 p = center + ivec2(x, y);
            if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, rawSize))) continue;
            if (colorFromPhase(phaseIndex(p)) != 1) continue;
            float spatialWeight = kernelWeight(vec2(p) - target, precisionMatrix);
            float jointWeight = spatialWeight * frameWeight;
            greenSum += highlightCalculationSampleAt(p) * jointWeight;
            greenWeight += jointWeight;
        }
    }
    float targetGreen = greenSum / max(greenWeight, 1.0e-8);

    vec3 semanticSums = vec3(greenSum, 0.0, 0.0);
    vec3 semanticWeights = vec3(greenWeight, 0.0, 0.0);
    float redFrameEvidence = 0.0;
    float blueFrameEvidence = 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            ivec2 p = center + ivec2(x, y);
            if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, rawSize))) continue;
            int sampleColor = colorFromPhase(phaseIndex(p));
            if (sampleColor == 1) continue;
            float spatialWeight = kernelWeight(vec2(p) - target, precisionMatrix);
            float localGreen = greenAt(p);
            float jointWeight = spatialWeight *
                chromaWeight(localGreen, targetGreen) * frameWeight;
            float opponent = highlightCalculationSampleAt(p) - localGreen;
            if (sampleColor == 0) {
                semanticSums.y += opponent * jointWeight;
                semanticWeights.y += jointWeight;
                redFrameEvidence += jointWeight;
            } else {
                semanticSums.z += opponent * jointWeight;
                semanticWeights.z += jointWeight;
                blueFrameEvidence += jointWeight;
            }
        }
    }

    vec4 numerator = texelFetch(previousNumerator, outP, 0);
    numerator.rgb += semanticSums;
    imageStore(outNumerator, outP, numerator);

    vec4 denominator = texelFetch(previousDenominator, outP, 0);
    denominator.rgb += semanticWeights;
    imageStore(outDenominator, outP, denominator);

    vec4 support = texelFetch(previousFrameSupport, outP, 0);
    support.r = min(
        max(maximumSupport - 1.0, 0.0),
        max(support.r, 0.0) + frameWeight
    );
    support.g += redFrameEvidence > 1.0e-8 ? frameWeight : 0.0;
    support.b += blueFrameEvidence > 1.0e-8 ? frameWeight : 0.0;
    imageStore(outFrameSupport, outP, support);
}
