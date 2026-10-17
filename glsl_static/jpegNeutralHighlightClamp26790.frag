#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uSource;
uniform sampler2D uNormalDngAccumulator26790;
uniform ivec2 uOutputSize;
uniform int uCfaPattern26790;
layout(location = 0) out vec4 oColor;
int redPhase26790() { return uCfaPattern26790; }
int bluePhase26790() { return 3 - uCfaPattern26790; }
void main() {
    ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uOutputSize - ivec2(1));
    vec4 source = texelFetch(uSource, p, 0);
    int rPhase = redPhase26790();
    int bPhase = bluePhase26790();
    ivec2 q = (p / 2) * 2;
    int g0 = -1; int g1 = -1;
    for (int phase = 0; phase < 4; ++phase) {
        if (phase != rPhase && phase != bPhase) {
            if (g0 < 0) g0 = phase; else g1 = phase;
        }
    }
    ivec2 gp0 = min(q + ivec2(g0 & 1, g0 >> 1), uOutputSize - ivec2(1));
    ivec2 gp1 = min(q + ivec2(g1 & 1, g1 >> 1), uOutputSize - ivec2(1));
    float gw0 = texelFetch(uNormalDngAccumulator26790, gp0, 0).g;
    float gw1 = texelFetch(uNormalDngAccumulator26790, gp1, 0).g;
    bool bothGreensFullyCensored26790 = gw0 <= 0.000051 && gw1 <= 0.000051;
    if (bothGreensFullyCensored26790) {
        source.rgb = min(source.rgb, vec3(1.0));
    }
    oColor = source;
}
