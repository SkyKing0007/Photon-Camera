#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uSource;
uniform ivec2 uExtractedSize;
uniform ivec2 uRawSize;
uniform int uCfaPattern;
uniform vec2 uKrKb26788;
layout(location = 0) out vec4 oExtractedBayer;

ivec2 phaseOffset26788(int phaseIndex) {
    return ivec2(phaseIndex & 1, (phaseIndex >> 1) & 1);
}
float phaseK26788(int phaseIndex) {
    if (phaseIndex == uCfaPattern) return uKrKb26788.x;
    if (phaseIndex == 3 - uCfaPattern) return uKrKb26788.y;
    return 0.0;
}
float component26788(vec4 v, int phaseIndex) {
    if (phaseIndex == 0) return v.r;
    if (phaseIndex == 1) return v.g;
    if (phaseIndex == 2) return v.b;
    return v.a;
}
float samePhaseBilinear26788(vec2 rawPixelCenter, int phaseIndex) {
    ivec2 offset = phaseOffset26788(phaseIndex);
    vec2 lattice = 0.5 * (rawPixelCenter - (vec2(offset) + vec2(0.5)));
    vec2 maximum = vec2(max(uExtractedSize - ivec2(1), ivec2(0)));
    lattice = clamp(lattice, vec2(0.0), maximum);
    ivec2 q0 = ivec2(floor(lattice));
    ivec2 q1 = min(q0 + ivec2(1), uExtractedSize - ivec2(1));
    vec2 f = fract(lattice);
    float c00 = component26788(texelFetch(uSource, q0, 0), phaseIndex);
    float c10 = component26788(texelFetch(uSource, ivec2(q1.x, q0.y), 0), phaseIndex);
    float c01 = component26788(texelFetch(uSource, ivec2(q0.x, q1.y), 0), phaseIndex);
    float c11 = component26788(texelFetch(uSource, q1, 0), phaseIndex);
    return mix(mix(c00, c10, f.x), mix(c01, c11, f.x), f.y);
}
void main() {
    ivec2 q = ivec2(gl_FragCoord.xy);
    vec4 center = texelFetch(uSource, q, 0);
    vec4 corrected = center;
    vec2 opticalCenter = 0.5 * vec2(uRawSize);
    for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
        float k = phaseK26788(phaseIndex);
        if (abs(k) < 1.0e-12) continue; // both green phases remain exact source values
        ivec2 offset = phaseOffset26788(phaseIndex);
        vec2 targetCenter = vec2(q * 2 + offset) + vec2(0.5);
        vec2 correctedCenter = opticalCenter +
            (targetCenter - opticalCenter) * (1.0 - k);
        corrected[phaseIndex] = samePhaseBilinear26788(correctedCenter, phaseIndex);
    }
    oExtractedBayer = corrected;
}
