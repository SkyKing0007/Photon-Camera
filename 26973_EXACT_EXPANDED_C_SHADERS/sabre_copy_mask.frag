#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uRejection;
uniform float uAccumulatedWeightScale;
layout(location = 0) out float oAccumulatedWeight;
void main() {
    vec2 uv = gl_FragCoord.xy / vec2(textureSize(uRejection, 0));
    oAccumulatedWeight = texture(uRejection, uv).r / uAccumulatedWeightScale;
}
