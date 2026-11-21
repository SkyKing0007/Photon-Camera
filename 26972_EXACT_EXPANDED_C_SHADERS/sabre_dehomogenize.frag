#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uSourceWeightR;
uniform sampler2D uSourceWeightGb;
uniform sampler2D uSourceAlpha;
uniform float uAlphaScale;
uniform float uAlphaBias;
layout(location = 0) out vec4 oColor;
void main() {
    vec2 uv = gl_FragCoord.xy / vec2(textureSize(uSourceWeightR, 0));
    vec3 weights = vec3(
        texture(uSourceWeightR, uv).r,
        texture(uSourceWeightGb, uv).rg
    );
    float targetAlpha = texture(uSourceAlpha, uv).r * uAlphaScale + uAlphaBias;
    oColor = vec4(vec3(1.0) / max(weights, vec3(1.0e-7)), targetAlpha);
}
