#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uRgb;
uniform sampler2D uMask;
uniform sampler2D uSmall;
uniform sampler2D uBigQuarter;
uniform ivec2 uSize;
uniform float uYFloor;
uniform float uAThreshold;
uniform vec3 uCalculationWb;
layout(location=0) out vec4 oColor;
vec2 safeFill(vec4 v){ return v.b>1.0e-3 ? v.rg/v.b : vec2(0.0); }
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float m=texelFetch(uMask,p,0).r;
    if(m<=0.0) discard;
    vec4 src=texelFetch(uRgb,p,0); vec3 rgb=src.rgb*uCalculationWb;
    float y=(rgb.r+2.0*rgb.g+rgb.b)*0.25; float yc=max(y,uYFloor);
    vec2 c=vec2(rgb.r-rgb.g,rgb.b-rgb.g)/yc;
    vec4 sm=texelFetch(uSmall,p,0);
    vec2 uv=(vec2(p)+vec2(0.5))/vec2(uSize);
    vec4 bg=texture(uBigQuarter,uv);
    float a=clamp(sm.b/max(uAThreshold,1.0e-4),0.0,1.0);
    vec2 fill=mix(safeFill(bg),safeFill(sm),a);
    vec2 cp=mix(c,fill,m);
    float dR=cp.x*yc, dB=cp.y*yc;
    float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);
    vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));
    oColor=vec4(cameraDst,src.a);
}
