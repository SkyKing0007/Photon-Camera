#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D InitialFlow;
uniform highp sampler2D ReferenceGradient;
uniform highp sampler2D InverseHessian;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int hasInitial;
uniform float initialToCurrentScale;
uniform int iterations;

float movingAt(vec2 p){
    if(p.x<0.0||p.y<0.0||p.x>float(levelSize.x-1)||p.y>float(levelSize.y-1)) return 0.0;
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(MovingGuide,p0,0).r,texelFetch(MovingGuide,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(MovingGuide,ivec2(p0.x,p1.y),0).r,texelFetch(MovingGuide,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float referenceAt(ivec2 p){
    return texelFetch(ReferenceGuide,clamp(p,ivec2(0),levelSize-ivec2(1)),0).r;
}
vec2 initialFlow(ivec2 tile,ivec2 grid){
    if(hasInitial==0) return vec2(0.0);
    vec2 uv=(vec2(tile)+0.5)/vec2(grid);
    return texture(InitialFlow,clamp(uv,vec2(0.0),vec2(1.0))).xy*initialToCurrentScale;
}

/* IRIS_26484_BJZHOU_CLAMPED_LEVELWISE_LK
 * No circular frame-edge addressing: reference/current samples clamp to the valid image.
 *
 * IRIS_26483_BJZHOU_LEVELWISE_REFERENCE_PRODUCT_LK
 * Adapt the current RAWmax/MGC alignment execution principle: immutable reference
 * gradient/Hessian products are prepared once per pyramid level, then every auxiliary
 * performs only level-local LK updates. Coarse-to-fine flow remains reference-owned.
 */
void main(){
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 ih=texelFetch(InverseHessian,tile,0);
    vec2 flow=initialFlow(tile,grid);
    if(dot(abs(ih),vec4(1.0))>1.0e-12){
        for(int iter=0;iter<3;iter++){
            if(iter>=iterations) continue;
            float b0=0.0,b1=0.0;
            for(int yy=0;yy<32;yy++){
                if(yy>=tileSize) continue;
                for(int xx=0;xx<32;xx++){
                    if(xx>=tileSize) continue;
                    ivec2 p=tile*tileSize+ivec2(xx,yy);
                    if(any(greaterThanEqual(p,levelSize))) continue;
                    vec2 g=texelFetch(ReferenceGradient,p,0).rg;
                    float residual=movingAt(vec2(p)+flow)-referenceAt(p);
                    b0+=-g.x*residual;
                    b1+=-g.y*residual;
                }
            }
            vec2 d=vec2(ih.r*b0+ih.g*b1,ih.b*b0+ih.a*b1);
            // Match RAWmax/MGC bounded level-wise LK behavior: one pyramid pixel per iteration.
            flow+=clamp(d,vec2(-1.0),vec2(1.0));
        }
    }

    float residualSum=0.0;
    int n=0;
    for(int yy=0;yy<32;yy+=2){
        if(yy>=tileSize) continue;
        for(int xx=0;xx<32;xx+=2){
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            if(any(greaterThanEqual(p,levelSize))) continue;
            residualSum+=abs(movingAt(vec2(p)+flow)-referenceAt(p));
            n++;
        }
    }
    float meanResidual=residualSum/float(max(n,1));
    float confidence=exp(-meanResidual/max(0.02,1.0e-5));
    imageStore(OutputFlow,tile,vec4(flow,clamp(confidence,0.0,1.0),meanResidual));
}
