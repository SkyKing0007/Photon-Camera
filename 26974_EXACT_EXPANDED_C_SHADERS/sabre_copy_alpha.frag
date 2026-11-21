#version 300 es
precision highp float;
precision highp sampler2D;
uniform sampler2D uSource;
layout(location = 0) out float oWeight;
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    oWeight = texelFetch(uSource, p, 0).a;
}
