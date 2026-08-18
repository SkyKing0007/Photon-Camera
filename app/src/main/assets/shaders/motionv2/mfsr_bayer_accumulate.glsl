#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;

uniform highp usampler2D rawTexture;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
layout(rgba32f,binding=0) uniform highp readonly image2D alterCov;
layout(r32f,binding=1) uniform highp image2D accumulatorNumerator;
layout(r32f,binding=2) uniform highp image2D accumulatorDenominator;
layout(r32f,binding=3) uniform highp image2D accumulatorFrameSupport;

uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform ivec2 guideSize;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float exposureScale;
uniform int referenceFrame;

/*
 * IRIS_26489_BJZHOU_PERSISTENT_BAYER_ACCUMULATOR_OWNER
 * IRIS_26489_V3_GLES_LEGAL_R32F_READWRITE_ACCUMULATOR
 *
 * One persistent numerator/denominator/support triple survives the entire burst.
 * Frame 0 and every admitted auxiliary execute this same shader. Each logical packed Bayer
 * cell still owns four independent CFA phase scalars, but the four scalars are stored at the
 * corresponding 2x2 Bayer positions in a raw-sized R32F image. R32F is the GLES 3.1 image
 * format that legally supports
 * read/write image access without readonly/writeonly; this preserves the prior FLOAT32 math and
 * memory footprint while removing the illegal read/write RGBA32F image declaration.
 *
 * No RGB, white balance, opponent colour, demosaic or highlight synthesis is allowed here.
 */

ivec2 clampRaw(ivec2 p) {
    return clamp(p, ivec2(0), rawSize - ivec2(1));
}

float sensorNormalizedAt(ivec2 rawP, int phase) {
    rawP = clampRaw(rawP);
    float rawValue = float(texelFetch(rawTexture, rawP, 0).r);
    float black = blackLevel[phase];
    return max(rawValue - black, 0.0) / max(whiteLevel - black, 1.0);
}

mat2 precisionAt(ivec2 p) {
    p = clamp(p, ivec2(0), guideSize - ivec2(1));
    vec4 v = imageLoad(alterCov, p);
    return mat2(v.x, v.y, v.z, v.w);
}

mat2 interpolatePrecision(vec2 guidePosition) {
    ivec2 lo = clamp(ivec2(floor(guidePosition)), ivec2(0), guideSize - ivec2(1));
    ivec2 hi = min(lo + ivec2(1), guideSize - ivec2(1));
    vec2 f = fract(guidePosition);
    mat2 a = precisionAt(lo);
    mat2 b = precisionAt(ivec2(hi.x, lo.y));
    mat2 c = precisionAt(ivec2(lo.x, hi.y));
    mat2 d = precisionAt(hi);
    return a * ((1.0-f.x)*(1.0-f.y)) + b * (f.x*(1.0-f.y))
        + c * ((1.0-f.x)*f.y) + d * (f.x*f.y);
}

float kernelWeight(vec2 rawOffset, mat2 precisionMatrix) {
    float distance = max(dot(rawOffset, precisionMatrix * rawOffset), 0.0);
    return exp2(-0.5 * distance) + 0.00005;
}

ivec2 phaseOffset(int phase) {
    return ivec2(phase & 1, (phase >> 1) & 1);
}

ivec2 accumulatorCoord(ivec2 packedP, int phase) {
    return packedP * 2 + phaseOffset(phase);
}

void main() {
    ivec2 outP = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(outP, packedSize))) return;

    float numerator[4];
    float denominator[4];
    float support[4];
    for (int phase = 0; phase < 4; ++phase) {
        ivec2 a = accumulatorCoord(outP, phase);
        numerator[phase] = imageLoad(accumulatorNumerator, a).r;
        denominator[phase] = imageLoad(accumulatorDenominator, a).r;
        support[phase] = imageLoad(accumulatorFrameSupport, a).r;
    }

    if (referenceFrame != 0) {
        ivec2 rawBase = outP * 2;
        for (int phase = 0; phase < 4; ++phase) {
            float v = sensorNormalizedAt(rawBase + phaseOffset(phase), phase) * exposureScale;
            numerator[phase] += v;
            denominator[phase] += 1.0;
            support[phase] += 1.0;
        }
        for (int phase = 0; phase < 4; ++phase) {
            ivec2 a = accumulatorCoord(outP, phase);
            imageStore(accumulatorNumerator, a, vec4(numerator[phase], 0.0, 0.0, 0.0));
            imageStore(accumulatorDenominator, a, vec4(denominator[phase], 0.0, 0.0, 0.0));
            imageStore(accumulatorFrameSupport, a, vec4(support[phase], 0.0, 0.0, 0.0));
        }
        return;
    }

    vec2 uv = (vec2(outP) + vec2(0.5)) / vec2(packedSize);
    vec2 packedFlow = texture(flowTexture, uv).xy;
    vec2 sourcePacked = vec2(outP) + vec2(0.5) + packedFlow;
    if (sourcePacked.x < 0.0 || sourcePacked.y < 0.0 ||
        sourcePacked.x >= float(packedSize.x) || sourcePacked.y >= float(packedSize.y)) {
        return;
    }

    float frameWeight = clamp(texture(robustnessTexture, uv).r, 0.0, 1.0);
    if (frameWeight <= 0.0) return;

    vec2 sourceRawCenter = 2.0 * sourcePacked;
    mat2 precisionMatrix = interpolatePrecision(
        sourceRawCenter * vec2(guideSize) / vec2(rawSize) - vec2(0.5));
    ivec2 packedCenter = ivec2(floor(sourcePacked));

    for (int phase = 0; phase < 4; ++phase) {
        vec2 rawTarget = 2.0 * sourcePacked + vec2(phaseOffset(phase)) - vec2(1.0);
        float sum = 0.0;
        float weight = 0.0;
        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                ivec2 packedSample = packedCenter + ivec2(dx, dy);
                if (any(lessThan(packedSample, ivec2(0))) ||
                    any(greaterThanEqual(packedSample, packedSize))) continue;
                ivec2 rawSample = packedSample * 2 + phaseOffset(phase);
                float spatial = kernelWeight(vec2(rawSample) - rawTarget, precisionMatrix);
                float joint = spatial * frameWeight;
                sum += sensorNormalizedAt(rawSample, phase) * exposureScale * joint;
                weight += joint;
            }
        }
        if (weight > 1.0e-8) {
            numerator[phase] += sum;
            denominator[phase] += weight;
            support[phase] += frameWeight;
        }
    }

    for (int phase = 0; phase < 4; ++phase) {
        ivec2 a = accumulatorCoord(outP, phase);
        imageStore(accumulatorNumerator, a, vec4(numerator[phase], 0.0, 0.0, 0.0));
        imageStore(accumulatorDenominator, a, vec4(denominator[phase], 0.0, 0.0, 0.0));
        imageStore(accumulatorFrameSupport, a, vec4(support[phase], 0.0, 0.0, 0.0));
    }
}
