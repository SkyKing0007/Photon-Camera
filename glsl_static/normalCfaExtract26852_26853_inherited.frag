#version 300 es
precision highp float;
uniform sampler2D uPhaseSignal;
uniform sampler2D uSharedSupport;
uniform ivec2 uQuadSize;
uniform vec4 uReferencePhaseGains;
uniform vec4 uReferencePhaseBlackTerms;
layout(location = 0) out vec4 oExtractedBayer;
void main() {
    ivec2 q = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uQuadSize - ivec2(1));
    vec4 signal = texelFetch(uPhaseSignal, q, 0);
    float w = max(texelFetch(uSharedSupport, q, 0).x, 1.0e-8);
    vec4 normalized = signal / w;
    vec4 rawCode = (normalized - uReferencePhaseBlackTerms) /
        max(uReferencePhaseGains, vec4(1.0e-12));
    oExtractedBayer = max(rawCode, vec4(0.0)) + vec4(1.0e-4);
}
