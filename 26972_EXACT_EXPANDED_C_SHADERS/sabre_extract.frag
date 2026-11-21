#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp usampler2D;
uniform highp usampler2D uRaw;
uniform ivec2 uRawSize;
layout(location = 0) out vec4 oExtractedBayer;

float rawAt(ivec2 p) {
    return float(texelFetch(uRaw, clamp(p, ivec2(0), uRawSize - ivec2(1)), 0).r);
}

void main() {
    ivec2 q = ivec2(gl_FragCoord.xy);
    ivec2 p = q * 2;
    oExtractedBayer = vec4(
        rawAt(p),
        rawAt(p + ivec2(1, 0)),
        rawAt(p + ivec2(0, 1)),
        rawAt(p + ivec2(1, 1))
    ) + vec4(1.0e-4);
}
