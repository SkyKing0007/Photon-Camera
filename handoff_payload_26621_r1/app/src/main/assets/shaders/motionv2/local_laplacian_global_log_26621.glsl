precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float outputExposureScale;
out float Output;

const vec3 IRIS_LUMA = vec3(0.22897456,0.69173852,0.07928691);
const float IRIS_LOG_FLOOR = 0.000244140625; /* 2^-12 */

float irisMax3(vec3 v){return max(v.r,max(v.g,v.b));}
float irisGuide(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    return max(dot(rgb,IRIS_LUMA),irisMax3(rgb));
}

/* IRIS_26621_NEW_SIMPLIFIED_GLOBAL_TONE
 * motionV2DisplayGain remains the single brightness request and outputExposureScale
 * is consumed once. The old 26614 cubic and this rational map share the same black
 * slope and source-white anchor; a constant 50/50 blend keeps proven body brightness
 * while enforcing useful positive slope through the upper body. The >1 branch is C1
 * and asymptotically reserves the final SDR code range for genuine HDR headroom. */
float iris26621GlobalTone(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor){
        bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    }
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float oneMinus=1.0-x;
        float oldBody=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
        float rationalBody=bodyGain*x/(1.0+ratio*x);
        return 0.5*(oldBody+rationalBody);
    }
    float rationalSlopeAtWhite=bodyGain/((1.0+ratio)*(1.0+ratio));
    float bodySlopeAtWhite=0.5*(whiteAnchor+rationalSlopeAtWhite);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlopeAtWhite,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}

void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float mapped=iris26621GlobalTone(irisGuide(texelFetch(InputBuffer,p,0).rgb));
    Output=log2(max(mapped,IRIS_LOG_FLOOR));
}
