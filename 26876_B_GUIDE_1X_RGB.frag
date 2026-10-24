#version 300 es
precision highp float;
precision highp int;
uniform highp sampler2D uWronski2xRgb;
layout(location=0) out vec4 oBOneX;
void main() {
ivec2 p=ivec2(gl_FragCoord.xy)*2;
vec4 a=texelFetch(uWronski2xRgb,p,0);
vec4 b=texelFetch(uWronski2xRgb,p+ivec2(1,0),0);
vec4 c=texelFetch(uWronski2xRgb,p+ivec2(0,1),0);
vec4 d=texelFetch(uWronski2xRgb,p+ivec2(1,1),0);
oBOneX=(a+b+c+d)*0.25;
}
