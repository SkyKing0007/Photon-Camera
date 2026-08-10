#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp uimage2D;

layout(rgba16f, binding = 0) uniform highp readonly image2D inTexture;
layout(r16ui, binding = 1) uniform highp writeonly uimage2D outTexture;

uniform float whiteLevel;
uniform vec4 blackLevel;

/* IRIS_26413_V2_PACK_RECONSTRUCTED_CFA */
void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    ivec2 outSize = imageSize(outTexture);
    if (any(greaterThanEqual(xy, outSize))) return;

    ivec2 q = xy / 2;
    vec4 packed = imageLoad(inTexture, q);
    int component = (xy.y & 1) * 2 + (xy.x & 1);

    float normalizedValue = max(packed[component], 0.0);
    float black = blackLevel[component];
    float sensorValue =
            normalizedValue * max(whiteLevel - black, 1.0)
                    + black;
    uint encoded = uint(clamp(
            floor(sensorValue + 0.5),
            0.0,
            65535.0));

    imageStore(outTexture, xy, uvec4(encoded, 0u, 0u, 0u));
}