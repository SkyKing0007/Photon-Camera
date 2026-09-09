precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
out vec4 Output;
#ifndef CALIBRATED_PROFILE
#define CALIBRATED_PROFILE 0
#endif

/* IRIS_26616_PRE_LTM_COLOR_ONLY
 * Motion colorfulness correction before Wronski LTM. This shader is strictly luminance-preserving
 * and contains no displayGain, shoulder, white anchor, output scale, histogram, or tone predictor.
 * It may alter only the center pixel's chroma vector around its own linear Display-P3 luminance.
 */
const vec3 LUMA_WEIGHTS=vec3(0.22897456,0.69173852,0.07928691);
float lum(vec3 c){return dot(c,LUMA_WEIGHTS);}
float pk(vec3 c){return max(c.r,max(c.g,c.b));}
ivec2 safeP(ivec2 p,ivec2 sz){return clamp(p,ivec2(0),sz-ivec2(1));}
vec3 at(ivec2 p,ivec2 sz){return max(texelFetch(InputBuffer,safeP(p,sz),0).rgb,vec3(0.0));}
float floorGainLimit(float y,float c){return c<-1.0e-7?max(1.0,(0.0-y)/c):4.0;}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);ivec2 sz=textureSize(InputBuffer,0);vec3 center=at(p,sz);
    /* IRIS_26616_PRE_APPEARANCE_PHYSICAL_GUIDE_ALPHA
     * Alpha is derived before any adaptive colorfulness change.  It is physical provenance only,
     * never an LTM/tone signal, and must survive unchanged through Wronski for UHDR. */
    float y=lum(center);float physicalGuide=max(y,pk(center));
#if CALIBRATED_PROFILE == 1
    Output=vec4(center,max(physicalGuide,0.0));return;
#endif
    vec3 chroma=center-vec3(y);float cm=length(chroma);float relative=cm/max(y,0.08);
    const ivec2 off[4]=ivec2[4](ivec2(-1,0),ivec2(1,0),ivec2(0,-1),ivec2(0,1));
    vec3 sum=chroma;float magSum=cm,maxYDelta=0.0;
    for(int i=0;i<4;i++){vec3 n=at(p+off[i],sz);float ny=lum(n);vec3 nc=n-vec3(ny);sum+=nc;magSum+=length(nc);maxYDelta=max(maxYDelta,abs(ny-y));}
    vec3 mean=sum/5.0;float meanMag=magSum/5.0;float coherence=length(mean)/max(meanMag,1.0e-6);float disagreement=length(chroma-mean);
    float neutral=smoothstep(0.0035,0.018,cm);float rolloff=1.0-smoothstep(0.08,0.45,relative);
    float shadow=smoothstep(0.015,0.075,y);float highlight=1.0-smoothstep(0.72,0.98,pk(center));
    float coh=smoothstep(0.45,0.82,coherence);float agree=1.0-smoothstep(0.018,0.085,disagreement);float edge=1.0-smoothstep(0.025,0.11,maxYDelta);
    float requested=1.0+0.32*neutral*rolloff*shadow*highlight*coh*agree*edge;
    float floorLimit=min(4.0,min(floorGainLimit(y,chroma.r),min(floorGainLimit(y,chroma.g),floorGainLimit(y,chroma.b))));
    float gain=clamp(min(requested,floorLimit),1.0,1.32);
    vec3 appearanceRgb=gain<=1.000001?center:vec3(y)+chroma*gain;
    Output=vec4(appearanceRgb,max(physicalGuide,0.0));
}
