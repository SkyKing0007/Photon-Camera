#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 1) buffer RedBuf {
    float red[];
};
layout(std430, binding = 2) readonly buffer GreenBuf {
    float green[];
};
layout(std430, binding = 3) buffer BlueBuf {
    float blue[];
};
layout(std430, binding = 8) readonly buffer PqBuf {
    float pq[];
};
uniform ivec2 bandSize;
uniform int bandOriginY;
uniform int cfaPattern;
int idxAt(ivec2 p) {
    p=clamp(p,ivec2(0),bandSize-ivec2(1));
    return p.y*bandSize.x+p.x;
}
int phaseAt(ivec2 p) {
    ivec2 gp=ivec2(p.x,bandOriginY+p.y);
    return (gp.x&1)|((gp.y&1)<<1);
}
int colorAt(ivec2 p) {
    int q=phaseAt(p);
    if(cfaPattern==0) return q==0?0:(q==3?2:1);
    if(cfaPattern==1) return q==1?0:(q==2?2:1);
    if(cfaPattern==2) return q==2?0:(q==1?2:1);
    return q==3?0:(q==0?2:1);
}
float g(ivec2 p){return green[idxAt(p)];}
float r(ivec2 p){return red[idxAt(p)];}
float b(ivec2 p){return blue[idxAt(p)];}
float dir(ivec2 p){return pq[idxAt(p)];}
float interpolateOpposite(ivec2 p, bool wantRed) {
    const float e=1.0e-5;
    float gc=g(p);
    float nw=wantRed?r(p+ivec2(-1,-1)):b(p+ivec2(-1,-1));
    float ne=wantRed?r(p+ivec2(1,-1)):b(p+ivec2(1,-1));
    float sw=wantRed?r(p+ivec2(-1,1)):b(p+ivec2(-1,1));
    float se=wantRed?r(p+ivec2(1,1)):b(p+ivec2(1,1));
    float gradNw=e+abs(nw-se)
        +abs(nw-(wantRed?r(p+ivec2(-3,-3)):b(p+ivec2(-3,-3))))
        +abs(gc-g(p+ivec2(-2,-2)));
    float gradNe=e+abs(ne-sw)
        +abs(ne-(wantRed?r(p+ivec2(3,-3)):b(p+ivec2(3,-3))))
        +abs(gc-g(p+ivec2(2,-2)));
    float gradSw=e+abs(ne-sw)
        +abs(sw-(wantRed?r(p+ivec2(-3,3)):b(p+ivec2(-3,3))))
        +abs(gc-g(p+ivec2(-2,2)));
    float gradSe=e+abs(nw-se)
        +abs(se-(wantRed?r(p+ivec2(3,3)):b(p+ivec2(3,3))))
        +abs(gc-g(p+ivec2(2,2)));
    float dnW=nw-g(p+ivec2(-1,-1));
    float dnE=ne-g(p+ivec2(1,-1));
    float dsW=sw-g(p+ivec2(-1,1));
    float dsE=se-g(p+ivec2(1,1));
    float alongP=(gradNw*dsE+gradSe*dnW)/(gradNw+gradSe);
    float alongQ=(gradNe*dsW+gradSw*dnE)/(gradNe+gradSw);
    return max(0.0,gc+mix(alongP,alongQ,clamp(dir(p),0.0,1.0)));
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,bandSize))) return;
    int c=colorAt(p);
    if(c==0) blue[idxAt(p)]=interpolateOpposite(p,false);
    else if(c==2) red[idxAt(p)]=interpolateOpposite(p,true);
}
