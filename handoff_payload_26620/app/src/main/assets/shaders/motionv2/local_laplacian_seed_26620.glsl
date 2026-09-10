precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float outputExposureScale;
out vec2 Output;

/* IRIS_26620_LOCAL_LAPLACIAN_SEED
 * First Gaussian level at half resolution. R stores log2(source guide), G stores
 * log2(the exact 26614 globally mapped guide). The centered 5x5 binomial kernel
 * is a standard Gaussian-pyramid reduce filter; there is no tile or coarse-map owner. */
const vec3 LUMA = vec3(0.22897456,0.69173852,0.07928691);
const float LOG_FLOOR = 0.000244140625; /* 2^-12 */

float lumaOf(vec3 c){return dot(c,LUMA);}
float max3(vec3 c){return max(c.r,max(c.g,c.b));}
float guideOf(vec3 c){c=max(c,vec3(0.0));return max(lumaOf(c),max3(c));}

float iris26614MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requestedFinalGain=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float whiteAnchor=min(0.95,requestedFinalGain);
    float bodyGain=requestedFinalGain;
    if(requestedFinalGain>whiteAnchor){
        bodyGain=min(requestedFinalGain,4.0*whiteAnchor-1.0e-4);
    }
    if(x<=1.0){
        float oneMinus=1.0-x;
        return whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    }
    float reserve=1.0-whiteAnchor;
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(whiteAnchor,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}

vec2 logPairAt(ivec2 p){
    ivec2 sz=textureSize(InputBuffer,0);
    p=clamp(p,ivec2(0),sz-ivec2(1));
    float sourceGuide=guideOf(texelFetch(InputBuffer,p,0).rgb);
    float mappedGuide=iris26614MapMotionSdrFinalGuide(sourceGuide);
    return vec2(log2(max(sourceGuide,LOG_FLOOR)),
                log2(max(mappedGuide,LOG_FLOOR)));
}

float kernel5(int o){
    int a=abs(o);
    if(a==0)return 6.0;
    if(a==1)return 4.0;
    return 1.0;
}

void main(){
    ivec2 q=ivec2(gl_FragCoord.xy);
    ivec2 center=q*2;
    vec2 sum=vec2(0.0);
    for(int oy=-2;oy<=2;oy++){
        float wy=kernel5(oy);
        for(int ox=-2;ox<=2;ox++){
            float wx=kernel5(ox);
            sum+=logPairAt(center+ivec2(ox,oy))*(wx*wy);
        }
    }
    Output=sum*(1.0/256.0);
}
