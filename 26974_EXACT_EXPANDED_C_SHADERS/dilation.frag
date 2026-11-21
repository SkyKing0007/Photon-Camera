#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
uniform sampler2D uRejection;
uniform ivec2 uInputSize;
layout(location = 0) out float oWeight;
float rejectionAt(vec2 p) {
    return texture(uRejection, p / vec2(uInputSize)).r;
}
void main() {
    // Exact DilateMask mapping from guide-sized RAW/2 rejection to the half-sized
    // RAW/4 merge-weight texture. The nine bilinear reads and
    // coefficients are the factored form of a 5x5 box sum.
    vec2 texCoord =
        2.0 * floor(gl_FragCoord.xy - vec2(0.5)) + vec2(1.5);
    float rejection =
        4.0 * rejectionAt(texCoord + vec2(-1.5, -1.5)) +
        4.0 * rejectionAt(texCoord + vec2( 0.5, -1.5)) +
        2.0 * rejectionAt(texCoord + vec2( 2.0, -1.5)) +
        4.0 * rejectionAt(texCoord + vec2(-1.5,  0.5)) +
        4.0 * rejectionAt(texCoord + vec2( 0.5,  0.5)) +
        2.0 * rejectionAt(texCoord + vec2( 2.0,  0.5)) +
        2.0 * rejectionAt(texCoord + vec2(-1.5,  2.0)) +
        2.0 * rejectionAt(texCoord + vec2( 0.5,  2.0)) +
              rejectionAt(texCoord + vec2( 2.0,  2.0));
    rejection = (rejection - 0.2) * 0.5;
    oWeight = 1.0 - rejection;
}
