#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D PreviousFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int searchRadius;
uniform int distanceMetric;
uniform int hasPrevious;
uniform float previousToCurrentScale;

/* IRIS_26473_IPOL_ALIGNMENT_BOUNDARY_SEMANTICS */
float sampleReference(ivec2 p) {
    ivec2 s=levelSize;
    ivec2 q=ivec2((p.x%s.x+s.x)%s.x,(p.y%s.y+s.y)%s.y);
    return texelFetch(ReferenceGuide,q,0).r;
}
float sampleMoving(ivec2 p) {
    if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,levelSize)))
        return 0.0;
    return texelFetch(MovingGuide,p,0).r;
}
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec2 pred=vec2(0.0);
    if(hasPrevious!=0) {
        vec2 uv=(vec2(tile)+0.5)/vec2(grid);
        pred=texture(PreviousFlow,clamp(uv,vec2(0.0),vec2(1.0))).xy
                *previousToCurrentScale;
    }
    ivec2 ipred=ivec2(round(pred));
    float best=3.402823e38;
    ivec2 bestShift=ipred;

    for(int sy=-4;sy<=4;sy++) for(int sx=-4;sx<=4;sx++) {
        if(abs(sx)>searchRadius || abs(sy)>searchRadius) continue;
        ivec2 sh=ipred+ivec2(sx,sy);
        float e=0.0;
        int n=0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 rp=tile*tileSize+ivec2(xx,yy);
                float a=sampleReference(rp);
                float b=sampleMoving(rp+sh);
                float d=a-b;
                e += distanceMetric==0 ? abs(d) : d*d;
                n++;
            }
        }
        e/=float(max(n,1));
        if(e<best) { best=e; bestShift=sh; }
    }
    float confidence=exp(-best/max(1e-5,0.02+best));
    imageStore(OutputFlow,tile,vec4(vec2(bestShift),confidence,best));
}
