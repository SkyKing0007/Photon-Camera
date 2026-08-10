#define LAYOUT //
LAYOUT
precision highp float;
precision highp usampler2D;
precision highp image2D;

uniform highp usampler2D inTexture;
layout(rgba16f, binding = 0) uniform highp writeonly image2D outTexture;

uniform float whiteLevel;
uniform vec4 blackLevel;
uniform float exposure;

/*
 * IRIS_26416_MOTION_V2_OWNED_RAW_TO_CFA
 *
 * Motion V2 owns this conversion. No legacy merge shader participates.
 *
 * One half-resolution output texel stores the physical 2x2 sensor block:
 *   .r = raw(2x+0, 2y+0)
 *   .g = raw(2x+1, 2y+0)
 *   .b = raw(2x+0, 2y+1)
 *   .a = raw(2x+1, 2y+1)
 *
 * Per-site black subtraction is retained. There is deliberately NO upper
 * clamp: extended-linear values above 1.0 remain representable.
 */

float readRaw(ivec2 p) {
    return float(texelFetch(inTexture, p, 0).r);
}

void main() {
    ivec2 q = ivec2(gl_GlobalInvocationID.xy);
    ivec2 base = q * 2;

    vec4 raw = vec4(
            readRaw(base + ivec2(0, 0)),
            readRaw(base + ivec2(1, 0)),
            readRaw(base + ivec2(0, 1)),
            readRaw(base + ivec2(1, 1)));

    vec4 denominator =
            max(vec4(whiteLevel) - blackLevel, vec4(1.0));

    vec4 normalized =
            max((raw - blackLevel) / denominator, vec4(0.0));

    imageStore(outTexture, q, normalized * vec4(exposure));
}