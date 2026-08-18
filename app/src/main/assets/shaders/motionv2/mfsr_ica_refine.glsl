#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D BlockFlow;
uniform highp sampler2D ReferenceGradient;
uniform highp sampler2D InverseHessian;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;

float movingAt(vec2 p) {
    if(p.x<0.0||p.y<0.0||p.x>float(levelSize.x-1)||p.y>float(levelSize.y-1))
        return 0.0;
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(MovingGuide,p0,0).r,
                texelFetch(MovingGuide,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(MovingGuide,ivec2(p0.x,p1.y),0).r,
                texelFetch(MovingGuide,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float refCircular(ivec2 p) {
    ivec2 q=ivec2((p.x%levelSize.x+levelSize.x)%levelSize.x,
                  (p.y%levelSize.y+levelSize.y)%levelSize.y);
    return texelFetch(ReferenceGuide,q,0).r;
}

/*
 * IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS
 * IPOL Algorithm 2: multi-scale BM first, then exactly three ICA iterations
 * on the final fine tiles. Wronski states exactly three LK refinements after
 * block matching; whether LK was repeated at each pyramid stage is unspecified.
 */
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 seed=texelFetch(BlockFlow,tile,0);
    vec4 ih=texelFetch(InverseHessian,tile,0);
    if(dot(abs(ih),vec4(1.0))<=1.0e-12){
        imageStore(OutputFlow,tile,seed);
        return;
    }

    vec2 flow=seed.xy;
    for(int iter=0;iter<3;iter++){
        float b0=0.0,b1=0.0;
        for(int yy=0;yy<64;yy++){
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++){
                if(xx>=tileSize) continue;
                ivec2 p=tile*tileSize+ivec2(xx,yy);
                if(any(greaterThanEqual(p,levelSize))) continue;
                vec2 g=texelFetch(ReferenceGradient,p,0).rg;
                float residual=movingAt(vec2(p)+flow)-refCircular(p);
                b0 += -g.x*residual;
                b1 += -g.y*residual;
            }
        }
        vec2 d=vec2(
            ih.r*b0 + ih.g*b1,
            ih.b*b0 + ih.a*b1);
        flow+=d;
    }
    imageStore(OutputFlow,tile,vec4(flow,seed.zw));
}

