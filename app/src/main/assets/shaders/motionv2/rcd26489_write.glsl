#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
layout(std430, binding = 0) readonly buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 1) readonly buffer RedBuf {
    float red[];
};
layout(std430, binding = 2) readonly buffer GreenBuf {
    float green[];
};
layout(std430, binding = 3) readonly buffer BlueBuf {
    float blue[];
};
layout(rgba16f, binding = 9) writeonly uniform highp image2D OutputRgb;
uniform ivec2 rawSize;
uniform ivec2 bandSize;
uniform int bandOriginY;
uniform int coreLocalY;
uniform int coreRows;
uniform int cfaPattern;
uniform vec3 calculationWb;

/* IRIS_26490_BJZHOU_RCD_PHOTO_BORDER_MIRROR_1TO1
 * Preserve the virtual PPG coordinate. Each sample is reflected in full-photo coordinates,
 * then mapped back into this band's halo. Clamping the virtual center changes Bayer parity and
 * is not equivalent to the reference PPG border semantics.
 */
int mirrorIndex(int value,int size){
    if(size<=1)return 0;
    int period=2*(size-1);
    int wrapped=value%period;
    if(wrapped<0)wrapped+=period;
    return wrapped<size?wrapped:period-wrapped;
}
ivec2 mirrorLocal(ivec2 p){
    ivec2 gp=ivec2(p.x,bandOriginY+p.y);
    ivec2 safeGlobal=ivec2(mirrorIndex(gp.x,rawSize.x),mirrorIndex(gp.y,rawSize.y));
    return ivec2(safeGlobal.x,safeGlobal.y-bandOriginY);
}
int idxAt(ivec2 p){ivec2 safe=mirrorLocal(p);return safe.y*bandSize.x+safe.x;}
int phaseAtSafeLocal(ivec2 p){ivec2 gp=ivec2(p.x,bandOriginY+p.y);return (gp.x&1)|((gp.y&1)<<1);}
int colorAt(ivec2 p){ivec2 safe=mirrorLocal(p);int q=phaseAtSafeLocal(safe);if(cfaPattern==0)return q==0?0:(q==3?2:1);if(cfaPattern==1)return q==1?0:(q==2?2:1);if(cfaPattern==2)return q==2?0:(q==1?2:1);return q==3?0:(q==0?2:1);}
float raw(ivec2 p){return cfa[idxAt(p)];}
float ppgGreen(ivec2 p){
    if(colorAt(p)==1) return max(raw(p),0.0);
    float c=raw(p);
    float xm=raw(p+ivec2(-1,0)), xp=raw(p+ivec2(1,0));
    float xm2=raw(p+ivec2(-2,0)), xp2=raw(p+ivec2(2,0));
    float xm3=raw(p+ivec2(-3,0)), xp3=raw(p+ivec2(3,0));
    float ym=raw(p+ivec2(0,-1)), yp=raw(p+ivec2(0,1));
    float ym2=raw(p+ivec2(0,-2)), yp2=raw(p+ivec2(0,2));
    float ym3=raw(p+ivec2(0,-3)), yp3=raw(p+ivec2(0,3));
    float gx=2.0*(xm+c+xp)-xm2-xp2;
    float gy=2.0*(ym+c+yp)-ym2-yp2;
    float dx=3.0*(abs(xm2-c)+abs(xp2-c)+abs(xm-xp))
        +2.0*(abs(xp3-xp)+abs(xm3-xm));
    float dy=3.0*(abs(ym2-c)+abs(yp2-c)+abs(ym-yp))
        +2.0*(abs(yp3-yp)+abs(ym3-ym));
    float outg=dx>dy?clamp(0.25*gy,min(ym,yp),max(ym,yp))
                    :clamp(0.25*gx,min(xm,xp),max(xm,xp));
    return max(outg,0.0);
}
vec3 ppg(ivec2 p){
    int own=colorAt(p); float c=max(raw(p),0.0),gg=ppgGreen(p); vec3 outc=vec3(0.0,gg,0.0);
    if(own==0||own==2){
        if(own==0) outc.r=c; else outc.b=c;
        ivec2 a=ivec2(-1,-1),bb=ivec2(1,-1),cc=ivec2(-1,1),d=ivec2(1,1);
        float e1=abs(raw(p+a)-raw(p+d))+abs(ppgGreen(p+a)-gg)+abs(ppgGreen(p+d)-gg);
        float e2=abs(raw(p+bb)-raw(p+cc))+abs(ppgGreen(p+bb)-gg)+abs(ppgGreen(p+cc)-gg);
        float v1=0.5*(raw(p+a)+raw(p+d)+2.0*gg-ppgGreen(p+a)-ppgGreen(p+d));
        float v2=0.5*(raw(p+bb)+raw(p+cc)+2.0*gg-ppgGreen(p+bb)-ppgGreen(p+cc));
        float v=e1<e2?v1:(e2<e1?v2:0.5*(v1+v2)); if(own==0) outc.b=v; else outc.r=v;
    } else {
        outc.g=c; bool horizontalRed=colorAt(p+ivec2(1,0))==0;
        float h=0.5*(raw(p+ivec2(-1,0))+raw(p+ivec2(1,0))+2.0*c-ppgGreen(p+ivec2(-1,0))-ppgGreen(p+ivec2(1,0)));
        float v=0.5*(raw(p+ivec2(0,-1))+raw(p+ivec2(0,1))+2.0*c-ppgGreen(p+ivec2(0,-1))-ppgGreen(p+ivec2(0,1)));
        if(horizontalRed){outc.r=h;outc.b=v;}else{outc.r=v;outc.b=h;}
    }
    return max(outc,vec3(0.0));
}
void main(){
    ivec2 gid=ivec2(gl_GlobalInvocationID.xy);
    if(gid.x>=rawSize.x||gid.y>=coreRows) return;
    ivec2 lp=ivec2(gid.x,coreLocalY+gid.y);
    ivec2 gp=ivec2(gid.x,bandOriginY+lp.y);
    vec3 rgb;
    bool boundary=gp.x<9||gp.y<9||gp.x+9>=rawSize.x||gp.y+9>=rawSize.y;
    if(boundary) rgb=ppg(lp); else {int i=idxAt(lp);rgb=max(vec3(red[i],green[i],blue[i]),vec3(0.0));}
    rgb/=max(calculationWb,vec3(1.0e-6));
    imageStore(OutputRgb,gp,vec4(rgb,1.0));
}
