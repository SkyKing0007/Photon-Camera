precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float displayGain;
uniform int motionHdrHandoff;
uniform float maxGainRatio;
uniform float irisOutputZoom;
uniform sampler2D iris26621LocalToneLog;
uniform int iris26621LocalToneEnabled;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
/* IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY */
out float Output;

/* IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY
 * Android Ultra HDR permits a gain map at the same resolution as the primary.
 * Generate the standard logarithmic gain per primary pixel, so the decoder never
 * has to spatially resample a lower-resolution brightness edge over the sharp SDR
 * base. The SDR image remains the exact spatial/color primary; UHDR changes only
 * the per-pixel display gain.
 */
const float UHDR_OFFSET = 0.015625;
float luminance(vec3 c){return dot(c,vec3(0.22897456,0.69173852,0.07928691));}
float max3(vec3 c){return max(c.r,max(c.g,c.b));}
float iris26640Smoothstep(float a,float b,float x){
    float t=clamp((x-a)/max(b-a,1.0e-6),0.0,1.0);
    return t*t*(3.0-2.0*t);
}
float iris26640HighlightPressure(){
    float broad=iris26640Smoothstep(0.015,0.060,clamp(iris26623ToneBroadNearFraction,0.0,1.0));
    float hard=iris26640Smoothstep(0.010,0.050,clamp(iris26623ToneHardFraction,0.0,1.0));
    float baseWhite=max(iris26623ToneBaseSceneWhite,1.0);
    float adaptiveWhite=max(iris26623ToneAdaptiveSceneWhite,baseWhite);
    float span=max(adaptiveWhite/baseWhite-1.0,0.0);
    float spanPressure=iris26640Smoothstep(0.08,0.35,span);
    return clamp(max(0.70*broad+0.30*spanPressure,0.75*hard),0.0,1.0);
}
void iris26640LegacyBody(float x,float requested,out float value,out float derivative){
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float shoulderRatio=max(bodyGain/safeWhite-1.0,0.0);
    float oneMinus=1.0-x;
    float cubic=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    float rational=bodyGain*x/(1.0+shoulderRatio*x);
    float cubicDerivative=whiteAnchor+(bodyGain-whiteAnchor)*oneMinus*(1.0-3.0*x);
    float rationalDerivative=bodyGain/((1.0+shoulderRatio*x)*(1.0+shoulderRatio*x));
    value=0.5*(cubic+rational);
    derivative=0.5*(cubicDerivative+rationalDerivative);
}
float iris26640LegacyMap(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float shoulderRatio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float value=0.0; float derivative=0.0;
        iris26640LegacyBody(x,requested,value,derivative);
        return value;
    }
    float rationalSlope=bodyGain/((1.0+shoulderRatio)*(1.0+shoulderRatio));
    float bodySlope=0.5*(whiteAnchor+rationalSlope);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlope,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}
float iris26640MapMotionSdrGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float legacy=iris26640LegacyMap(x);
    float adaptiveEnable=iris26640Smoothstep(1.05,1.25,requested);
    const float upperStart=0.65;
    if(adaptiveEnable<=1.0e-7 || x<=upperStart)return legacy;
    float pressure=iris26640HighlightPressure();
    float targetWhite=mix(0.945,0.925,pressure);
    float targetSlope=mix(0.360,0.300,pressure);
    float startValue=0.0; float startSlope=0.0;
    iris26640LegacyBody(upperStart,requested,startValue,startSlope);
    float width=1.0-upperStart;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return legacy;
    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-upperStart)/width,0.0,1.0);
        float t2=t*t; float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue
            +(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite
            +(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float tailScale=reserve/max(m1,1.0e-6);
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(legacy,candidate,adaptiveEnable);
}
float iris26640SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){
    float globalMapped=iris26640MapMotionSdrGuide(sourceGuide);
    if(iris26621LocalToneEnabled==0)return globalMapped;
    vec2 toneSize=vec2(textureSize(iris26621LocalToneLog,0));
    vec2 uv=(masterSourcePixel+vec2(0.5))/max(toneSize,vec2(1.0));
    vec2 halfTexel=vec2(0.5)/max(toneSize,vec2(1.0));
    float localLog=texture(iris26621LocalToneLog,clamp(uv,halfTexel,vec2(1.0)-halfTexel)).r;
    float localMapped=exp2(clamp(localLog,-12.0,0.0));
    float localStrength=smoothstep(0.030,0.100,globalMapped);
    return mix(globalMapped,localMapped,localStrength);
}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}


vec3 iris26524BilinearHdr(vec2 sourcePixel){
    ivec2 sz=textureSize(HdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(texelFetch(HdrBuffer,ivec2(p0.x,p0.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p0.y),0).rgb,f.x);
    vec3 b=mix(texelFetch(HdrBuffer,ivec2(p0.x,p1.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p1.y),0).rgb,f.x);
    return mix(a,b,f.y);
}
/* IRIS_26550_GAINMAP_GENERAL_GEOMETRY
 * Motion remains 1:1 so sourcePixel==p exactly. Night may request a smaller detached gain map;
 * sample the full rendered SDR/HDR at the corresponding pixel center instead of accidentally
 * reading only the top-left quarter of the image.
 */
vec3 iris26550BilinearSdr(vec2 sourcePixel){
    ivec2 sz=textureSize(SdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(texelFetch(SdrBuffer,ivec2(p0.x,p0.y),0).rgb,
               texelFetch(SdrBuffer,ivec2(p1.x,p0.y),0).rgb,f.x);
    vec3 b=mix(texelFetch(SdrBuffer,ivec2(p0.x,p1.y),0).rgb,
               texelFetch(SdrBuffer,ivec2(p1.x,p1.y),0).rgb,f.x);
    return mix(a,b,f.y);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,gainMapSize))){Output=0.0;return;}
    float zoom=max(irisOutputZoom,1.0);
    ivec2 sdrSize=textureSize(SdrBuffer,0);
    vec2 sourcePixel=(vec2(p)+vec2(0.5))*vec2(sdrSize)/vec2(gainMapSize)-vec2(0.5);
    vec2 masterSourcePixel=sourcePixel;
    vec3 hdrRgb;
    if(zoom<=1.00001){
        hdrRgb=iris26524BilinearHdr(masterSourcePixel);
    }else{
        ivec2 hdrSize=textureSize(HdrBuffer,0);
        vec2 center=(vec2(hdrSize)-vec2(1.0))*0.5;
        masterSourcePixel=center+(sourcePixel-center)/zoom;
        hdrRgb=iris26524BilinearHdr(masterSourcePixel);
    }
    vec3 hdrPositive=max(hdrRgb,vec3(0.0));
    float sdr=max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio;
    if(motionHdrHandoff!=0){
        /* IRIS_26640_MATCHED_SDR_HDR_INTENT_QUOTIENT
         * Both intents come from the same canonical extended-linear Motion master, same source
         * sample, same 26623 global tone prerequisites, and the same Local-Laplacian structure.
         * There is no luma eligibility threshold and no spatial gain dilation. The HDR intent
         * departs from SDR only by the amount that the SDR rendition is actually compressing the
         * shared linear-light target; weak body compression therefore collapses naturally to unity
         * while broad real highlight compression participates coherently. */
        float sourceY=max(luminance(hdrPositive),0.0);
        float sourceGuide=max(sourceY,max3(hdrPositive));
        if(sourceGuide<=1.0e-7 || sourceY<=1.0e-9){
            ratio=1.0;
        }else{
            float globalSdrGuide=max(iris26640MapMotionSdrGuide(sourceGuide),0.0);
            float sharedSdrGuide=max(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel),0.0);
            float localStructureScale=globalSdrGuide>1.0e-7
                ? sharedSdrGuide/globalSdrGuide : 1.0;
            float requested=max(displayGain,1.0e-6)*hdrExposureScale;
            float sdrModelY=sourceY*(sharedSdrGuide/sourceGuide);
            float linearTargetY=sourceY*requested*max(localStructureScale,0.0);
            float compressedDelta=max(linearTargetY-sdrModelY,0.0);
            float compressionFraction=linearTargetY>1.0e-7
                ? clamp(compressedDelta/linearTargetY,0.0,1.0) : 0.0;
            float hdrIntentY=sdr+compressedDelta*compressionFraction;
            ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
        }
    }else{
        float hdrTargetScale=hdrExposureScale;
        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);
        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    }
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
