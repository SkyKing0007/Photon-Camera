#version 300 es
precision highp float;
uniform sampler2D uLongMean;
uniform sampler2D uLongWeightR;
uniform sampler2D uLongWeightsGb;
layout(location = 0) out vec2 oWeightedLumaSupport;
float luma26833(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
void main() {
    vec2 uv = gl_FragCoord.xy / vec2(textureSize(uLongMean, 0));
    vec3 rgb = max(texture(uLongMean, uv).rgb, vec3(0.0));
    vec3 support = vec3(
        max(texture(uLongWeightR, uv).r, 0.0),
        max(texture(uLongWeightsGb, uv).r, 0.0),
        max(texture(uLongWeightsGb, uv).g, 0.0));
    float scalarSupport = min(support.r, min(support.g, support.b));
    oWeightedLumaSupport = vec2(max(luma26833(rgb), 0.0) * scalarSupport, scalarSupport);
}
