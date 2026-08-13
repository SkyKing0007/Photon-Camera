#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
/*
 * IRIS_26464_GLES31_WRONSKI_PING_PONG_FLOAT32
 *
 * GLSL ES requires non-r32 image formats such as rgba32f to be qualified
 * readonly and/or writeonly. Persistent Wronski accumulation is therefore
 * expressed as previous sampler textures -> writeonly next images.
 * The math remains exactly num_next = num_prev + addNum and
 * den_next = den_prev + addDen, with one divide only after the full burst.
 */
uniform highp sampler2D previousNumerator;
uniform highp sampler2D previousDenominator;
uniform highp sampler2D previousFrameSupport;
layout(rgba16f,binding=0) uniform highp readonly image2D alterCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D alterCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float maximumSupport;
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
    vec4 v=imageLoad(alterCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
mat2 covAt(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(alterCov,p);
    return mat2(v.x,v.y,v.z,v.w);
}
mat2 interpolateCov(vec2 gp){
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

/* IRIS_26463_WRONSKI_PUBLIC_AUX_ACCUMULATION
 * Public merge() coordinate contract at scale=1:
 * lr = output+0.5; lr_mov=lr+flow; center=int(lr_mov);
 * distance uses lr_mov-0.5; covariance position=lr_mov/2-0.5.
 * Num/den remain FLOAT32 running accumulators and are divided only once.
 */
/* IRIS_26465_WRONSKI_CFA_SATURATION_PROVENANCE
 * The published Wronski num/den recurrence is untouched. G/B/A in the
 * existing frame-support carrier accumulate unsaturated R/G/B kernel support
 * using the same sample positions, covariance and robustness weights.
 */
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec2 uv=(vec2(outP)+0.5)/vec2(rawSize);
    vec2 rawFlow=2.0*texture(flowTexture,uv).xy;
    vec2 lr=vec2(outP)+0.5;
    vec2 lrMov=lr+rawFlow;
    if(lrMov.x<0.0||lrMov.y<0.0||lrMov.x>=float(rawSize.x)||lrMov.y>=float(rawSize.y)) return;

    ivec2 robustP=clamp(ivec2(lr),ivec2(0),rawSize-ivec2(1));
    float R=clamp(texelFetch(robustnessTexture,robustP,0).r,0.0,1.0);
    vec2 kmap=lrMov/2.0-0.5;
    mat2 invCov=invertCov(interpolateCov(kmap));

    ivec2 center=ivec2(lrMov);
    vec2 movTarget=lrMov-0.5;
    vec3 addNum=vec3(0),addDen=vec3(0),addValidDen=vec3(0);
    for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){
        ivec2 p=center+ivec2(ix,iy);
        if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize))) continue;
        int c=componentColor(componentIndex(p));
        vec2 d=vec2(p)-movTarget;
        float z=max(dot(d,invCov*d),0.0);
        float w=exp(-0.5*z)*R;
        float cfaSample=cfaAt(p);
        addNum[c]+=w*cfaSample;
        addDen[c]+=w;
        addValidDen[c]+=w*sampleValidity(cfaSample,c);
    }
    vec4 n=texelFetch(previousNumerator,outP,0);
    n.rgb+=addNum;
    imageStore(outNumerator,outP,n);

    vec4 d=texelFetch(previousDenominator,outP,0);
    d.rgb+=addDen;
    imageStore(outDenominator,outP,d);

    vec4 fs=texelFetch(previousFrameSupport,outP,0);
    fs.r=min(max(maximumSupport,1.0),max(fs.r,1.0)+R);
    fs.gba+=addValidDen;
    imageStore(outFrameSupport,outP,fs);
}
