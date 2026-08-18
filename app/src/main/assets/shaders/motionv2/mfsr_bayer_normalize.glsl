#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(r32f,binding=0) uniform highp readonly image2D accumulatorNumerator;
layout(r32f,binding=1) uniform highp readonly image2D accumulatorDenominator;
layout(rgba32f,binding=2) uniform highp writeonly image2D outCfa;
uniform ivec2 packedSize;

/* IRIS_26489_BJZHOU_BAYER_NORMALIZE_ONCE */
/* IRIS_26489_V3_RAW_SIZED_R32F_ACCUMULATOR_TO_RGBA32F_FUSED_BAYER */
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, packedSize))) return;
    vec4 numerator = vec4(0.0);
    vec4 denominator = vec4(0.0);
    for (int phase = 0; phase < 4; ++phase) {
        ivec2 a = p * 2 + ivec2(phase & 1, (phase >> 1) & 1);
        numerator[phase] = imageLoad(accumulatorNumerator, a).r;
        denominator[phase] = imageLoad(accumulatorDenominator, a).r;
    }
    vec4 normalized = numerator / max(denominator, vec4(1.0e-8));
    imageStore(outCfa, p, max(normalized, vec4(0.0)));
}
