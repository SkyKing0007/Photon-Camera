#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D referenceGuide;
uniform highp sampler2D currentGuide;
uniform highp sampler2D flowTexture;
uniform highp sampler2D unblockerTexture;
layout(r32f,binding=0) uniform highp writeonly image2D outReverseWeight;
layout(r32f,binding=1) uniform highp writeonly image2D outPixelDifference;
uniform ivec2 rawHalf;
uniform ivec2 guideSize;
uniform vec3 referenceNoiseShot;
uniform vec3 referenceNoiseRead;
uniform vec3 currentNoiseShot;
uniform vec3 currentNoiseRead;
const float FLOW_VARIATION_THRESHOLD=9.88235261e-5;
vec2 mirrorUv(vec2 uv){uv=mod(uv,2.0);return mix(uv,2.0-uv,greaterThan(uv,vec2(1.0)));}
vec4 sampleBiquadraticAbsolute(sampler2D image,vec2 uv){vec2 ts=1.0/vec2(guideSize);vec2 f=fract(uv*vec2(guideSize));vec2 c=f*f-f+0.5;vec2 w0=uv-c*ts,w1=uv+c*ts;vec4 s=abs(texture(image,vec2(w0.x,w0.y)))+abs(texture(image,vec2(w0.x,w1.y)))+abs(texture(image,vec2(w1.x,w1.y)))+abs(texture(image,vec2(w1.x,w0.y)));s.w/=1024.0;return 0.25*s;}
vec3 nvar(vec3 shot,vec3 read,float signal){return max(shot*max(signal,0.0)+read,vec3(1.0e-10));}
float q8(float v){return round(255.0*clamp(v,0.0,1.0))/255.0;}
/* IRIS_26487_BJZHOU_REJECTION_EXACT_EQUATION */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawHalf)))return;
    vec2 uv=(vec2(p)+0.5)/vec2(rawHalf);vec4 flow=texture(flowTexture,uv);vec2 warped=mirrorUv(uv+flow.xy/vec2(rawHalf));
    float unblocker=texture(unblockerTexture,uv).r;if(flow.z<FLOW_VARIATION_THRESHOLD)unblocker=0.0;bool motionPrior=flow.z>FLOW_VARIATION_THRESHOLD;
    vec4 reference=texture(referenceGuide,uv);bool greenOnly=reference.w<0.0;reference.w=abs(reference.w)/1024.0;
    vec4 current=sampleBiquadraticAbsolute(currentGuide,warped);
    float luma=clamp(greenOnly?reference.g:dot(reference.rgb,vec3(1.0/3.0)),0.0,1.0);
    vec3 refNoise=nvar(referenceNoiseShot,referenceNoiseRead,luma);vec3 curNoise=nvar(currentNoiseShot,currentNoiseRead,luma);
    float scale=greenOnly?0.25:0.0976597;refNoise*=scale;curNoise*=scale;reference.w*=scale;current.w*=scale;
    float pixelVariance=min(reference.w,current.w);float minimumVariance=greenOnly?refNoise.g:dot(refNoise,vec3(1.0/3.0));float boost=1.0;
    if(reference.w>25.0*minimumVariance&&motionPrior)boost=6.0;pixelVariance*=2.0;
    vec3 combined=max(refNoise+curNoise,vec3(1.0e-8));vec3 diff=current.rgb-reference.rgb;vec3 diffSq=max(diff*diff-combined,vec3(0.0));vec3 variance=max(vec3(pixelVariance),combined);
    vec3 pixelDistanceSq=diffSq/combined;diffSq/=variance;
    float distance=greenOnly?0.35*diffSq.g:0.07*dot(diffSq,vec3(1.0/3.0));
    float pixelDistance=greenOnly?0.35*pixelDistanceSq.g:0.07*dot(pixelDistanceSq,vec3(1.0/3.0));
    float pixelDifference=exp2(min(-pixelDistance,0.0));distance*=boost;float frameWeight=exp2(min(-distance,0.0));float weight=min(1.0-unblocker,frameWeight);
    imageStore(outReverseWeight,p,vec4(q8(1.0-weight)));imageStore(outPixelDifference,p,vec4(q8(pixelDifference)));
}
