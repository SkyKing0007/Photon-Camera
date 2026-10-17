#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uSource;
uniform sampler2D uValidWeights;
uniform float uZeroValidityThreshold26787;
layout(location = 0) out vec4 oColor;
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec4 source = texelFetch(uSource, p, 0);
    float measuredGreenValidity = texelFetch(uValidWeights, p, 0).g;
    if (measuredGreenValidity <= uZeroValidityThreshold26787) {
        source.r = min(source.r, 1.0);
        source.b = min(source.b, 1.0);
    }
    oColor = source;
}
