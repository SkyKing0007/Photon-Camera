#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGradient;
layout(rgba32f,binding=0) uniform highp writeonly image2D OutputInverseHessian;
uniform ivec2 levelSize;
uniform int tileSize;

/*
 * IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE
 * IPOL computation details separate a fixed reference initialization cost
 * (reference gradients + ICA Hessians) from linear per-auxiliary work.
 */
void main(){
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputInverseHessian);
    if(any(greaterThanEqual(tile,grid))) return;

    float H00=0.0,H01=0.0,H11=0.0;
    for(int yy=0;yy<64;yy++){
        if(yy>=tileSize) continue;
        for(int xx=0;xx<64;xx++){
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            if(any(greaterThanEqual(p,levelSize))) continue;
            vec2 g=texelFetch(ReferenceGradient,p,0).rg;
            H00+=g.x*g.x;
            H01+=g.x*g.y;
            H11+=g.y*g.y;
        }
    }
    float det=H00*H11-H01*H01;
    if(abs(det)<1.0e-10){
        imageStore(OutputInverseHessian,tile,vec4(0.0));
        return;
    }
    float invDet=1.0/det;
    imageStore(OutputInverseHessian,tile,
        vec4(H11*invDet,-H01*invDet,-H01*invDet,H00*invDet));
}

