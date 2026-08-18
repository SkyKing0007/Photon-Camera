#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp image2D;

uniform highp sampler2D normalCfa;
layout(r32f, binding = 0) uniform highp writeonly image2D outProvenance;
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float physicalClipThreshold;

/* IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_INIT
 * Provenance follows each physical R/G1/G2/B observation independently, while
 * preserving the proven one-float-per-packed-cell bridge. Four ternary states are
 * encoded exactly as a base-3 integer in R32F:
 *   code = s0 + 3*s1 + 9*s2 + 27*s3, each s in {0 NORMAL, 1 CENSORED, 2 SHORT}.
 * Maximum code is 80, represented exactly by float32. No extra full-frame carrier
 * or readback bandwidth is introduced.
 */
float encodePhaseStates(vec4 s) {
    return dot(s, vec4(1.0, 3.0, 9.0, 27.0));
}
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, packedSize))) return;
    vec4 normal = texelFetch(normalCfa, p, 0);
    vec4 sensor = normal / max(referenceExposureScale, 1.0e-6);
    vec4 state = step(vec4(physicalClipThreshold), sensor);
    imageStore(outProvenance, p, vec4(encodePhaseStates(state), 0.0, 0.0, 0.0));
}
