#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D frameSupport;
uniform highp sampler2D denominator;
layout(rgba32f,binding=0) uniform highp writeonly image2D outSupportDiag;
layout(rgba32f,binding=1) uniform highp writeonly image2D outDenominatorDiag;
uniform ivec2 rawSize;
uniform ivec2 diagSize;
uniform float maximumAux;
/* IRIS_26488_TINY_RUNTIME_SUPPORT_AND_DENOMINATOR_DIAGNOSTICS */
void main() {
    ivec2 q = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(q, diagSize))) return;
    vec4 supportSum = vec4(0.0);
    vec4 denominatorSum = vec4(0.0);
    for (int y = 0; y < 4; ++y) {
        for (int x = 0; x < 4; ++x) {
            vec2 cell = (vec2(q) + (vec2(x, y) + vec2(0.5)) / 4.0) / vec2(diagSize);
            ivec2 p = clamp(ivec2(cell * vec2(rawSize)), ivec2(0), rawSize - ivec2(1));
            vec4 support = texelFetch(frameSupport, p, 0);
            vec4 den = texelFetch(denominator, p, 0);
            float oob = maximumAux > 0.0 ? clamp(support.a / maximumAux, 0.0, 1.0) : 0.0;
            supportSum += vec4(
                1.0 + max(support.r, 0.0),
                1.0 + max(support.g, 0.0),
                1.0 + max(support.b, 0.0),
                oob
            );
            float opponentRatio = min(max(den.g, 0.0), max(den.b, 0.0)) /
                max(max(den.r, 0.0), 1.0e-8);
            denominatorSum += vec4(max(den.r, 0.0), max(den.g, 0.0), max(den.b, 0.0), opponentRatio);
        }
    }
    imageStore(outSupportDiag, q, supportSum / 16.0);
    imageStore(outDenominatorDiag, q, denominatorSum / 16.0);
}
