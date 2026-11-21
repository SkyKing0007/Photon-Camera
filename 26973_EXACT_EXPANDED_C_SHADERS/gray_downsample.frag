#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp isampler2D;
uniform highp isampler2D uInput;
uniform ivec2 uInputSize;
layout(location = 0) out highp int oGray;
float valueAt(ivec2 p) {
    return float(texelFetch(
        uInput, clamp(p, ivec2(0), uInputSize - ivec2(1)), 0
    ).r);
}
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy) * 2;
    float value = 0.0;
    for (int y = -1; y <= 1; ++y) {
        float wy = y == 0 ? 0.5 : 0.25;
        for (int x = -1; x <= 1; ++x) {
            float wx = x == 0 ? 0.5 : 0.25;
            value += valueAt(p + ivec2(x, y)) * wx * wy;
        }
    }
    oGray = int(clamp(floor(value + 0.5), -32768.0, 32767.0));
}
