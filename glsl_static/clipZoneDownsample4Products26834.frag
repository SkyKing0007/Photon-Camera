#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uInput;
uniform ivec2 uInputSize;
out vec4 oValue;
void main(){
    ivec2 q=ivec2(gl_FragCoord.xy); ivec2 base=q*4; vec4 s=vec4(0.0);
    for(int y=0;y<4;++y) for(int x=0;x<4;++x)
        s+=texelFetch(uInput,clamp(base+ivec2(x,y),ivec2(0),uInputSize-ivec2(1)),0);
    oValue=s*(1.0/16.0);
}
