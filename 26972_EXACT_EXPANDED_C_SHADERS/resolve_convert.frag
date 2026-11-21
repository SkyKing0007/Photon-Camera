#version 310 es
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp isampler2D;
precision highp usampler2D;
uniform highp sampler2D uAccumulated;
uniform ivec2 uImageSize;
uniform ivec2 uRedSite;
uniform float uQuantizationScale;
layout(location = 0) out highp ivec4 oConverted;

void main() {
    ivec2 virtualSite = ivec2(gl_FragCoord.xy) - ivec2(4);
    ivec2 source = clamp(virtualSite + uRedSite, ivec2(0), uImageSize - ivec2(1));
    vec4 color = texelFetch(uAccumulated, source, 0);
    int cfaColor = (virtualSite.x & 1) + (virtualSite.y & 1);
    float sampleValue = cfaColor == 0 ? color.r : (cfaColor == 1 ? color.g : color.b);
    float scaled = sampleValue * uQuantizationScale;
    oConverted = ivec4(int(clamp(roundEven(scaled), -32768.0, 32767.0)), 0, 0, 0);
}
