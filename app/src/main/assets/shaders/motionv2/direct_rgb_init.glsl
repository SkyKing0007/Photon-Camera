#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float clipForColor(int c){return c==0?clipR:(c==2?clipB:clipG);}
float sampleValidity(float v,int c){
    float clip=max(clipForColor(c),1e-6);
    return 1.0-smoothstep(0.985*clip,0.998*clip,v);
}
float cfaAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(referenceCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
mat2 covAt(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(referenceCov,p);
    return mat2(v.x,v.y,v.z,v.w);
}
mat2 interpolateCov(vec2 greyPos){
    vec2 gp=greyPos;
    ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));
    ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));
    vec2 f=fract(gp);
    mat2 c00=covAt(fl);
    mat2 c01=covAt(ivec2(ce.x,fl.y));
    mat2 c10=covAt(ivec2(fl.x,ce.y));
    mat2 c11=covAt(ce);
    return c00*((1.0-f.x)*(1.0-f.y))
         + c01*(f.x*(1.0-f.y))
         + c10*((1.0-f.x)*f.y)
         + c11*(f.x*f.y);
}
mat2 invertCov(mat2 m){
    float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];
    if(abs(d)<=1e-10) return mat2(1,0,0,1);
    return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;
}

/* IRIS_26463_WRONSKI_PUBLIC_REFERENCE_ACCUMULATION
 * Direct translation of merge_ref(): reference robustness=1, covariance
 * interpolated on Bayer-quad grid, 3x3 physical CFA gather, independent RGB
 * numerator/denominator. No per-frame normalization.
 */
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec2 coarse=vec2(outP); // public scale=1 coarse_ref_sub_pos
    vec2 greyPos=(coarse-vec2(0.5))/2.0;
    mat2 invCov=invertCov(interpolateCov(greyPos));
    ivec2 center=ivec2(round(coarse));
    vec3 num=vec3(0), den=vec3(0), validDen=vec3(0);

    for(int iy=-1;iy<=1;iy++) for(int ix=-1;ix<=1;ix++){
        ivec2 p=center+ivec2(ix,iy);
        if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize))) continue;
        int c=componentColor(componentIndex(p));
        vec2 d=vec2(p)-coarse;
        float z=max(dot(d,invCov*d),0.0);
        float w=exp(-0.5*z);
        float cfaSample=cfaAt(p);
        num[c]+=cfaSample*w;
        den[c]+=w;
        validDen[c]+=w*sampleValidity(cfaSample,c);
    }
    imageStore(outNumerator,outP,vec4(num,0));
    imageStore(outDenominator,outP,vec4(den,1));
    /* IRIS_26465_CFA_UNSATURATED_SUPPORT_CARRIER
     * R stores historical frame-equivalent support. G/B/A carry the
     * independent unsaturated Wronski denominator for R/G/B.
     */
    imageStore(outFrameSupport,outP,vec4(1,validDen));
}
