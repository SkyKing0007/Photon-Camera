#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D frameSupport;
uniform highp sampler2D denominator;
layout(rgba32f,binding=0) uniform highp writeonly image2D outSupportDiag;
layout(rgba32f,binding=1) uniform highp writeonly image2D outDenominatorDiag;
uniform ivec2 packedSize;
uniform ivec2 diagSize;

/*
 * IRIS_26489_TINY_BAYER_SUPPORT_DENOMINATOR_DIAGNOSTIC
 * IRIS_26489_V3_RAW_SIZED_R32F_PHASE_DIAGNOSTIC
 */
vec4 loadPackedPhases(sampler2D tex, ivec2 packedP) {
    ivec2 base = packedP * 2;
    return vec4(
        texelFetch(tex, base + ivec2(0, 0), 0).r,
        texelFetch(tex, base + ivec2(1, 0), 0).r,
        texelFetch(tex, base + ivec2(0, 1), 0).r,
        texelFetch(tex, base + ivec2(1, 1), 0).r);
}

void main() {
    ivec2 q = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(q, diagSize))) return;
    vec4 supportSum = vec4(0.0);
    vec4 denominatorSum = vec4(0.0);
    for (int y = 0; y < 4; ++y) {
        for (int x = 0; x < 4; ++x) {
            vec2 cell = (vec2(q) + (vec2(x,y)+vec2(0.5))/4.0) / vec2(diagSize);
            ivec2 p = clamp(ivec2(cell * vec2(packedSize)), ivec2(0), packedSize-ivec2(1));
            vec4 support = loadPackedPhases(frameSupport, p);
            vec4 den = loadPackedPhases(denominator, p);
            float meanSupport = dot(support,vec4(0.25));
            float minSupport = min(min(support.r,support.g),min(support.b,support.a));
            float maxSupport = max(max(support.r,support.g),max(support.b,support.a));
            supportSum += vec4(meanSupport,minSupport,maxSupport,0.0);
            denominatorSum += max(den,vec4(0.0));
        }
    }
    imageStore(outSupportDiag,q,supportSum/16.0);
    imageStore(outDenominatorDiag,q,denominatorSum/16.0);
}
