#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uInput;
uniform ivec2 uSize;
uniform ivec2 uDirection;
uniform int uRadius;
uniform float uKernel[61];
uniform float uGain;
uniform int uClamp01;
out vec4 oFiltered;
vec4 at(ivec2 p){return texelFetch(uInput,clamp(p,ivec2(0),uSize-ivec2(1)),0);}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy); vec4 v=vec4(0.0);
    for(int i=-30;i<=30;++i) if(abs(i)<=uRadius) v+=uKernel[i+30]*at(p+uDirection*i);
    v*=uGain; if(uClamp01!=0) v=clamp(v,vec4(0.0),vec4(1.0)); oFiltered=v;
}
