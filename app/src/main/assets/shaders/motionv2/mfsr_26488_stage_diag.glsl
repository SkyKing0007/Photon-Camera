#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D unblockerTexture;
uniform highp sampler2D reverseWeightTexture;
uniform highp sampler2D pixelDifferenceTexture;
uniform highp sampler2D postRejectionTexture;
uniform highp sampler2D finalWeightTexture;
uniform highp usampler2D rawTexture;
layout(rgba32f,binding=0) uniform highp writeonly image2D outStageA;
layout(rgba32f,binding=1) uniform highp writeonly image2D outStageB;
layout(rgba32f,binding=2) uniform highp writeonly image2D outStageC;
uniform ivec2 rawSize;
uniform ivec2 diagSize;
uniform int frameSlot;
uniform int cfaPattern;
uniform vec4 blackLevel;
uniform float whiteLevel;
uniform float clipThreshold;

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

float sensorNormalizedAt(ivec2 p) {
    p = clamp(p, ivec2(0), rawSize - ivec2(1));
    int phase = phaseIndex(p);
    float rawValue = float(texelFetch(rawTexture, p, 0).r);
    float black = blackLevel[phase];
    return max(rawValue - black, 0.0) / max(whiteLevel - black, 1.0);
}

float quadAnyClip(ivec2 p) {
    ivec2 q = clamp(p >> 1, ivec2(0), (rawSize >> 1) - ivec2(1));
    ivec2 base = q << 1;
    float maximum = 0.0;
    maximum = max(maximum, sensorNormalizedAt(base));
    maximum = max(maximum, sensorNormalizedAt(base + ivec2(1, 0)));
    maximum = max(maximum, sensorNormalizedAt(base + ivec2(0, 1)));
    maximum = max(maximum, sensorNormalizedAt(base + ivec2(1, 1)));
    return maximum >= clipThreshold ? 1.0 : 0.0;
}

/* IRIS_26488_SMALL_PER_FRAME_REJECTION_CONTRACT_ATLAS */
void main() {
    ivec2 q = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(q, diagSize))) return;

    vec4 stageA = vec4(0.0);
    vec4 stageB = vec4(0.0);
    vec3 clipCount = vec3(0.0);
    vec3 channelCount = vec3(0.0);
    float anyClip = 0.0;
    for (int y = 0; y < 4; ++y) {
        for (int x = 0; x < 4; ++x) {
            vec2 uv = (vec2(q) + (vec2(x, y) + vec2(0.5)) / 4.0) / vec2(diagSize);
            vec4 flow = texture(flowTexture, uv);
            float unblocker = texture(unblockerTexture, uv).r;
            float reverseWeight = texture(reverseWeightTexture, uv).r;
            float pixelDifference = texture(pixelDifferenceTexture, uv).r;
            float postRejection = texture(postRejectionTexture, uv).r;
            float finalWeight = texture(finalWeightTexture, uv).r;
            stageA += vec4(flow.z, flow.w > 0.5 ? 1.0 : 0.0, unblocker, reverseWeight);
            stageB += vec4(pixelDifference, postRejection, finalWeight, 1.0 - reverseWeight);

            ivec2 rawP = clamp(ivec2(uv * vec2(rawSize)), ivec2(0), rawSize - ivec2(1));
            int color = colorFromPhase(phaseIndex(rawP));
            float clipped = sensorNormalizedAt(rawP) >= clipThreshold ? 1.0 : 0.0;
            clipCount[color] += clipped;
            channelCount[color] += 1.0;
            anyClip += quadAnyClip(rawP);
        }
    }

    vec3 clipFraction = clipCount / max(channelCount, vec3(1.0));
    ivec2 outP = ivec2(q.x, frameSlot * diagSize.y + q.y);
    imageStore(outStageA, outP, stageA / 16.0);
    imageStore(outStageB, outP, stageB / 16.0);
    imageStore(outStageC, outP, vec4(clipFraction, anyClip / 16.0));
}
