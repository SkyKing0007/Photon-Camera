#version 300 es
precision highp float;
precision highp int;
uniform sampler2D uProvenance;
uniform ivec2 uSize;
uniform int uRadius;
out float oMask;
float z0(ivec2 p) {
    vec2 q=texelFetch(uProvenance,clamp(p,ivec2(0),uSize-ivec2(1)),0).rg;
    return q.y>1.0e-7 ? clamp(1.0-q.x/q.y,0.0,1.0) : 0.0;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy); float m=0.0;
    for(int y=-4;y<=4;++y) for(int x=-4;x<=4;++x)
        if(abs(x)<=uRadius && abs(y)<=uRadius) m=max(m,z0(p+ivec2(x,y)));
    oMask=m;
}
