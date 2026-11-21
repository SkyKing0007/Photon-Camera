#version 300 es
precision highp float;
precision highp sampler2D;
precision highp int;
uniform sampler2D uBaseGuide;
uniform ivec2 uGuideSize;
layout(location = 0) out vec4 oReferenceColor;

        vec4 sampleBicubicAbsolute(sampler2D image, vec2 uv) {
    vec2 pixel = uv * vec2(uGuideSize) + 0.5;
    vec2 integerPixel = floor(pixel);
    vec2 a = fract(pixel);
    vec2 w0 = (1.0 / 6.0) * (a * (a * (-a + 3.0) - 3.0) + 1.0);
    vec2 w1 = (1.0 / 6.0) * (a * a * (3.0 * a - 6.0) + 4.0);
    vec2 w2 = (1.0 / 6.0) * (a * (a * (-3.0 * a + 3.0) + 3.0) + 1.0);
    vec2 w3 = (1.0 / 6.0) * (a * a * a);
    vec2 g0 = w0 + w1;
    vec2 g1 = w2 + w3;
    vec2 h0 = -1.0 + w1 / g0;
    vec2 h1 = 1.0 + w3 / g1;
    vec2 reciprocalSize = 1.0 / vec2(uGuideSize);
    vec2 p0 = (integerPixel + h0 - 0.5) * reciprocalSize;
    vec2 p1 = (integerPixel + h1 - 0.5) * reciprocalSize;
    // Take abs after each bilinear lookup, exactly as MGC does: guide alpha stores
    // the green-only flag in its sign, while RGB and variance share the same filter.
    return g0.y * (
        g0.x * abs(texture(image, vec2(p0.x, p0.y))) +
        g1.x * abs(texture(image, vec2(p1.x, p0.y)))
    ) + g1.y * (
        g0.x * abs(texture(image, vec2(p0.x, p1.y))) +
        g1.x * abs(texture(image, vec2(p1.x, p1.y)))
    );
}

void main() {
    vec2 uv = gl_FragCoord.xy / vec2(uGuideSize);
    vec4 reference = sampleBicubicAbsolute(uBaseGuide, uv);
    if (texture(uBaseGuide, uv).w < 0.0) reference.w = -reference.w;
    oReferenceColor = reference;
}
