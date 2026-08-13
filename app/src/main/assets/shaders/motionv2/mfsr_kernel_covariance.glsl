#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;
layout(rgba32f,binding=1) uniform highp writeonly image2D outputCov;
uniform ivec2 rawHalf;
uniform float noiseS;
uniform float noiseO;
uniform float kDetail;
uniform float kDenoise;
uniform float Dth;
uniform float Dtr;
uniform float kStretch;
uniform float kShrink;

float vst(float x){
    float a=max(noiseS,1e-7);
    float b=max(noiseO,0.0);
    float q=max(a*x+0.375*a*a+b,0.0);
    return 2.0/a*sqrt(q);
}
float greyVst(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(inputCfa,p);
    return 0.25*(vst(v.r)+vst(v.g)+vst(v.b)+vst(v.a));
}
vec2 publicGrad(ivec2 p){
    /* Exact algebra of public kernels.py:
       horizontal [-.5,.5] / average [.5,.5], followed by
       vertical average [.5,.5] / difference [-.5,.5]. */
    float g00=greyVst(p);
    float g01=greyVst(p+ivec2(1,0));
    float g10=greyVst(p+ivec2(0,1));
    float g11=greyVst(p+ivec2(1,1));
    return vec2(
        0.25*(-g00+g01-g10+g11),
        0.25*(-g00-g01+g10+g11));
}

/* IRIS_26463_WRONSKI_PUBLIC_PER_FRAME_KERNEL_COVARIANCE
 * Direct translation of public kernels.py: GAT -> Bayer-quad mean ->
 * published gradients -> 2x2 structure tensor -> eigen law -> covariance.
 * One covariance per Bayer quad, recomputed independently for each frame.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawHalf))) return;

    float jxx=0.0,jxy=0.0,jyy=0.0;
    for(int iy=0;iy<2;iy++) for(int ix=0;ix<2;ix++){
        ivec2 q=p-ivec2(1)+ivec2(ix,iy);
        if(q.x<0||q.y<0||q.x>=rawHalf.x-1||q.y>=rawHalf.y-1) continue;
        vec2 g=publicGrad(q);
        jxx+=g.x*g.x;
        jxy+=g.x*g.y;
        jyy+=g.y*g.y;
    }

    float tr=jxx+jyy;
    float disc=sqrt(max((jxx-jyy)*(jxx-jyy)+4.0*jxy*jxy,0.0));
    float l1=max(0.5*(tr+disc),0.0);
    float l2=max(0.5*(tr-disc),0.0);

    vec2 e1;
    if(abs(jxy)<1e-12 && abs(jxx-jyy)<1e-12) e1=vec2(1.0,0.0);
    else {
        e1=vec2(jxx+jxy-l2,jxy+jyy-l2);
        if(dot(e1,e1)<1e-16) e1=jxx>=jyy?vec2(1,0):vec2(0,1);
        else e1=normalize(e1);
    }
    vec2 e2=vec2(-e1.y,e1.x);

    float A=1.0+sqrt(max((l1-l2)/max(l1+l2,1e-20),0.0));
    float D=clamp(1.0-sqrt(max(l1,0.0))/max(Dtr,1e-8)+Dth,0.0,1.0);
    float sk1=1.0+0.5*A*(1.0/kShrink-1.0);
    float sk2=1.0+0.5*A*(kStretch-1.0);
    float k1=kDetail*((1.0-D)*sk1+D*kDenoise);
    float k2=kDetail*((1.0-D)*sk2+D*kDenoise);
    float k1s=k1*k1, k2s=k2*k2;

    float xx=k1s*e1.x*e1.x+k2s*e2.x*e2.x;
    float xy=k1s*e1.x*e1.y+k2s*e2.x*e2.y;
    float yy=k1s*e1.y*e1.y+k2s*e2.y*e2.y;
    imageStore(outputCov,p,vec4(xx,xy,xy,yy));
}
