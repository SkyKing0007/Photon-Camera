#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
precision highp isampler2D;
uniform highp isampler2D uInput;
uniform ivec2 uInputSize;
layout(location = 0) out highp int oGray;
int valueAt(ivec2 p) {
    return texelFetch(
        uInput, clamp(p, ivec2(0), uInputSize - ivec2(1)), 0
    ).r;
}
int firstStageAt(ivec2 p) {
    int sum = 0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            sum += valueAt(p + ivec2(x, y)) *
                (2 - abs(x)) * (2 - abs(y));
        }
    }
    return (sum + 8) >> 4;
}
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy) * 4;
    int sum = 0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            sum += firstStageAt(p + 2 * ivec2(x, y)) *
                (2 - abs(x)) * (2 - abs(y));
        }
    }
    oGray = (sum + 8) >> 4;
}
