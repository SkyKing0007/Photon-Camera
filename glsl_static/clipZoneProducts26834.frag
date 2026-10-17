#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uRgb;
uniform sampler2D uMask;
uniform float uYFloor;
uniform vec3 uCalculationWb;
out vec4 oProducts;
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy); vec3 cameraRgb=texelFetch(uRgb,p,0).rgb;
    vec3 rgb=cameraRgb*uCalculationWb;
    float m=texelFetch(uMask,p,0).r; float y=(rgb.r+2.0*rgb.g+rgb.b)*0.25;
    float yc=max(y,uYFloor); vec2 c=vec2(rgb.r-rgb.g,rgb.b-rgb.g)/yc;
    float w=(1.0-m)*(1.0-m); oProducts=vec4(w*c,w,0.0);
}
