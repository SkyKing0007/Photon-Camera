#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp usampler2D;
uniform highp usampler2D uRaw;
uniform ivec2 uRawSize;
uniform ivec2 uGraySize;
uniform int uCfaPattern;
uniform vec4 uBlackLevels;
uniform float uGain;
layout(location = 0) out highp int oGray;
uint quadSum(ivec2 q) {
    q = clamp(q, ivec2(0), uGraySize - ivec2(1));
    ivec2 p = clamp(q * 2, ivec2(0), uRawSize - ivec2(2));
    return texelFetch(uRaw, p, 0).r +
        texelFetch(uRaw, p + ivec2(1, 0), 0).r +
        texelFetch(uRaw, p + ivec2(0, 1), 0).r +
        texelFetch(uRaw, p + ivec2(1, 1), 0).r;
}
uint hadd(uint a, uint b) { return (a + b) >> 1; }
uint rhadd(uint a, uint b) { return (a + b + 1u) >> 1; }
uint verticalAt(ivec2 q) {
    return rhadd(
        hadd(quadSum(q + ivec2(0, -1)), quadSum(q + ivec2(0, 1))),
        quadSum(q)
    );
}
void main() {
    ivec2 q = ivec2(gl_FragCoord.xy);
    uint filtered = hadd(
        rhadd(verticalAt(q + ivec2(-1, 0)), verticalAt(q + ivec2(1, 0))),
        verticalAt(q)
    );
    float scale = uGain * 0.25;
    float blackSum = ((uBlackLevels.x + uBlackLevels.y) +
        uBlackLevels.z) + uBlackLevels.w;
    float offset = 0.5 - scale * blackSum;
    float value = offset + scale * float(filtered);
    oGray = int(clamp(value, -16383.0, 16383.0));
}
