#define LAYOUT //
LAYOUT
precision highp float;
precision highp uimage2D;
precision highp usampler2D;
uniform highp usampler2D rawTexture;
layout(r32ui,binding=0) uniform highp writeonly uimage2D outGray;
uniform ivec2 rawSize;
uniform ivec2 graySize;
uniform vec4 blackLevel;
uniform float gain;

vec4 phaseQuad(ivec2 q) {
    ivec2 p = clamp(q * 2, ivec2(0), rawSize - ivec2(2));
    vec4 values = vec4(
        float(texelFetch(rawTexture, p, 0).r),
        float(texelFetch(rawTexture, p + ivec2(1, 0), 0).r),
        float(texelFetch(rawTexture, p + ivec2(0, 1), 0).r),
        float(texelFetch(rawTexture, p + ivec2(1, 1), 0).r)
    );
    return max(values - blackLevel, vec4(0.0)) * gain;
}

float grayAt(ivec2 q) {
    return dot(phaseQuad(q), vec4(0.25));
}

/* IRIS_26488_BJZHOU_RAW16_TO_GRAY_HALIDE_CONTRACT */
void main() {
    ivec2 q = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(q, graySize))) return;
    float value = 0.0;
    for (int y = -1; y <= 1; ++y) {
        float wy = y == 0 ? 0.5 : 0.25;
        for (int x = -1; x <= 1; ++x) {
            float wx = x == 0 ? 0.5 : 0.25;
            value += grayAt(q + ivec2(x, y)) * wx * wy;
        }
    }
    imageStore(outGray, q, uvec4(uint(clamp(round(value), 0.0, 32767.0))));
}
