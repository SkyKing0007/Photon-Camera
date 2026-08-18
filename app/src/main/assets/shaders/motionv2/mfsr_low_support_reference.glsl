#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
uniform highp sampler2D chromaGuide;
layout(rgba32f,binding=0) uniform highp readonly image2D referenceCov;
uniform highp sampler2D currentNumerator;
uniform highp sampler2D currentDenominator;
uniform highp sampler2D currentFrameSupport;
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
    return max(rawValue - black, 0.0) / max(whiteLevel - black, 1.0);
}

float cameraSampleAt(ivec2 p) {
    return sensorNormalizedAt(p) * exposureScale;
}

float calculationSampleAt(ivec2 p) {
    p = clampCoord(p);
    return cameraSampleAt(p) * wbForColor(colorFromPhase(phaseIndex(p)));
}

float highlightCalculationSampleAt(ivec2 p) {
    p = clampCoord(p);
    int targetColor = colorFromPhase(phaseIndex(p));
    float targetWb = max(wbForColor(targetColor), 1.0e-6);
    float sensor = sensorNormalizedAt(p);
    float cameraFallback = cameraSampleAt(p);
    float clipMask = smoothstep(highlightClipThreshold, 1.0, sensor);
    if (clipMask <= 0.0) return cameraFallback * targetWb;

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
    float opposedRoot = targetColor == 0
        ? 0.5 * (rootGreen + rootBlue)
        : (targetColor == 1
            ? 0.5 * (rootRed + rootBlue)
            : 0.5 * (rootRed + rootGreen));
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
    vec4 v = imageLoad(referenceCov, p);
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
    return exp2(-0.5 * max(dot(pixelOffset, precisionMatrix * pixelOffset), 0.0)) + 0.00005;
}

/* IRIS_26488_REFERENCE_NATIVE_RAW_MERGERGB_IDENTITY_WEIGHT */
void main() {
    ivec2 outP = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(outP, rawSize))) return;

    vec4 oldNum = texelFetch(currentNumerator, outP, 0);
    vec4 oldDen = texelFetch(currentDenominator, outP, 0);
    vec4 support = texelFetch(currentFrameSupport, outP, 0);
    vec2 target = vec2(outP);
    mat2 precisionMatrix = interpolatePrecision(
        (target + vec2(0.5)) * vec2(guideSize) / vec2(rawSize) - vec2(0.5)
    );
    ivec2 center = ivec2(round(target));

    float greenSum = 0.0;
    float greenWeight = 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            ivec2 p = center + ivec2(x, y);
            if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, rawSize))) continue;
            if (colorFromPhase(phaseIndex(p)) != 1) continue;
            float weight = kernelWeight(vec2(p) - target, precisionMatrix);
            greenSum += highlightCalculationSampleAt(p) * weight;
            greenWeight += weight;
        }
    }
    float targetGreen = greenSum / max(greenWeight, 1.0e-8);

    vec3 semanticSums = vec3(greenSum, 0.0, 0.0);
    vec3 semanticWeights = vec3(greenWeight, 0.0, 0.0);
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            ivec2 p = center + ivec2(x, y);
            if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, rawSize))) continue;
            int sampleColor = colorFromPhase(phaseIndex(p));
            if (sampleColor == 1) continue;
            float spatialWeight = kernelWeight(vec2(p) - target, precisionMatrix);
            float localGreen = greenAt(p);
            float jointWeight = spatialWeight * chromaWeight(localGreen, targetGreen);
            float opponent = highlightCalculationSampleAt(p) - localGreen;
            if (sampleColor == 0) {
                semanticSums.y += opponent * jointWeight;
                semanticWeights.y += jointWeight;
            } else {
                semanticSums.z += opponent * jointWeight;
                semanticWeights.z += jointWeight;
            }
        }
    }

    imageStore(outNumerator, outP, vec4(oldNum.rgb + semanticSums, 0.0));
    imageStore(outDenominator, outP, vec4(oldDen.rgb + semanticWeights, 1.0));
    imageStore(outFrameSupport, outP, support);
}
