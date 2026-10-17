#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uAccumulatedColor;
uniform sampler2D uAccumulatedWeightsGb;
layout(location = 0) out vec2 oChroma;
float luma26790(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec4 sums = texelFetch(uAccumulatedColor, p, 0);
    vec2 gbw = texelFetch(uAccumulatedWeightsGb, p, 0).rg;
    vec3 weights = max(vec3(sums.a, gbw), vec3(1.0e-7));
    vec3 mean = sums.rgb / weights;
    float y = max(luma26790(mean), 0.02);
    oChroma = clamp(vec2(mean.r - mean.g, mean.b - mean.g) / y, vec2(-4.0), vec2(4.0));
}
