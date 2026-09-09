precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
out vec4 Output;
void main(){
    ivec2 outP=ivec2(gl_FragCoord.xy);ivec2 sz=textureSize(InputBuffer,0);ivec2 p=outP*2;
    vec4 a=texelFetch(InputBuffer,clamp(p,ivec2(0),sz-ivec2(1)),0);
    vec4 b=texelFetch(InputBuffer,clamp(p+ivec2(1,0),ivec2(0),sz-ivec2(1)),0);
    vec4 c=texelFetch(InputBuffer,clamp(p+ivec2(0,1),ivec2(0),sz-ivec2(1)),0);
    vec4 d=texelFetch(InputBuffer,clamp(p+ivec2(1,1),ivec2(0),sz-ivec2(1)),0);
    Output=(a+b+c+d)*0.25;
}
