#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D BlockFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int iterations;

float bilinear(sampler2D t,vec2 p) {
    vec2 mx=vec2(levelSize)-vec2(1.001);
    p=clamp(p,vec2(0.0),mx);
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(t,p0,0).r,texelFetch(t,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(t,ivec2(p0.x,p1.y),0).r,texelFetch(t,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float refAt(ivec2 p) {
    p=clamp(p,ivec2(0),levelSize-ivec2(1));
    return texelFetch(ReferenceGuide,p,0).r;
}

/* IRIS_26462_WRONSKI_INVERSE_COMPOSITIONAL_ALIGNMENT
 * Hessian from reference gradients; three additive IC updates.
 */
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 seed=texelFetch(BlockFlow,tile,0);
    vec2 flow=seed.xy;

    float H00=0.0,H01=0.0,H11=0.0;
    for(int yy=0;yy<64;yy++) {
        if(yy>=tileSize) continue;
        for(int xx=0;xx<64;xx++) {
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            if(any(greaterThanEqual(p,levelSize))) continue;
            float gx=0.5*(refAt(p+ivec2(1,0))-refAt(p-ivec2(1,0)));
            float gy=0.5*(refAt(p+ivec2(0,1))-refAt(p-ivec2(0,1)));
            H00+=gx*gx; H01+=gx*gy; H11+=gy*gy;
        }
    }
    float det=max(H00*H11-H01*H01,1e-8);

    for(int iter=0;iter<3;iter++) {
        if(iter>=iterations) break;
        float b0=0.0,b1=0.0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 p=tile*tileSize+ivec2(xx,yy);
                if(any(greaterThanEqual(p,levelSize))) continue;
                float gx=0.5*(refAt(p+ivec2(1,0))-refAt(p-ivec2(1,0)));
                float gy=0.5*(refAt(p+ivec2(0,1))-refAt(p-ivec2(0,1)));
                float residual=bilinear(MovingGuide,vec2(p)+flow)-refAt(p);
                b0 += -gx*residual;
                b1 += -gy*residual;
            }
        }
        vec2 d=vec2(
                ( H11*b0-H01*b1)/det,
                (-H01*b0+H00*b1)/det);
        d=clamp(d,vec2(-1.5),vec2(1.5));
        flow+=d;
    }
    imageStore(OutputFlow,tile,vec4(flow,seed.z,seed.w));
}