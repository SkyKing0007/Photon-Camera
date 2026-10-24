#version 300 es
precision highp float;
precision highp int;
uniform highp sampler2D uWronski2xClip;
layout(location=0) out float oBOneXClip;
void main() {
ivec2 p=ivec2(gl_FragCoord.xy)*2;
float a=texelFetch(uWronski2xClip,p,0).r;
float b=texelFetch(uWronski2xClip,p+ivec2(1,0),0).r;
float c=texelFetch(uWronski2xClip,p+ivec2(0,1),0).r;
float d=texelFetch(uWronski2xClip,p+ivec2(1,1),0).r;
oBOneXClip=max(max(a,b),max(c,d));
}
