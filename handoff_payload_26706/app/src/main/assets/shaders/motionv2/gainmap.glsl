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
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;
/* IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY */
out float Output;

/* IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY_SUPERSEDED_26641
 * 26641 intentionally replaces the former one-gain-sample-per-primary-pixel geometry with a
 * half-linear-resolution Motion gain map. HDR and SDR intents are filtered in linear light at the
 * same source center before their quotient is formed; the completed gain field is never blurred
 * or dilated. The SDR image remains the exact spatial/color primary.
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
    /* IRIS_26706_VISUAL_HIGHLIGHT_SPACING
     * 26705 proved that broad visually flattened highlights can cluster at nominal source white
     * even when hard sensor clipping is not the deciding condition. Preserve the exact mapping
     * through source guide 0.65, but for broad highlight pressure reserve more SDR code space above
     * nominal white and increase (rather than decrease) the C1 source-white slope. This remains one
     * global pointwise monotone scalar: no spatial mask, no semantic scene class, no SHORT ownership
     * change, and no channel-dependent operation. */
    float targetWhite=mix(0.945,0.895,pressure);
    float targetSlope=mix(0.360,0.620,pressure);
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

/* IRIS_26653_UHDR_SHARED_FINAL_SDR_TONE
 * Gain-map intent must model the exact same completed SDR global tone as MotionV2Render. */
float iris26653MapMotionSdrGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float off=iris26640MapMotionSdrGuide(x);
    if(iris26653HighlightCompressionEnabled==0 || x<=0.65)return off;
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float enable=iris26640Smoothstep(1.05,1.25,requested);
    if(enable<=1.0e-7)return off;
    float scenePressure=iris26640HighlightPressure();
    float kneePressure=clamp((0.90-iris26653HighlightKnee)/(0.90-0.55),0.0,1.0);
    float pressure=max(scenePressure,kneePressure);
    float targetWhite=mix(0.915,0.890,pressure);
    float targetSlope=mix(0.090,0.055,pressure);
    const float startX=0.65;
    float startValue=0.0; float startSlope=0.0;
    iris26640LegacyBody(startX,requested,startValue,startSlope);
    float width=1.0-startX;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return off;
    float m0=max(startSlope,0.0); float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant; float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-startX)/width,0.0,1.0); float t2=t*t; float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue
            +(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite
            +(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float whiteSpan=max(1.0,sqrt(max(iris26653AdaptiveWhitePoint,1.0)));
        float tailScale=reserve/max(m1,1.0e-6)*whiteSpan;
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(off,candidate,enable);
}
/* IRIS_26660_OBJECT_COLOR_GAMMA
 * IRIS_26671_UPPER_GAMMA_RELEASE
 * Exact SDR mirror of MotionV2Render. No spatial sampling/threshold is introduced here.
 * The corrected SDR denominator is gamma-shaped while the HDR numerator below remains on the
 * exact successful-26658 local-structure target, preserving the existing UHDR brightness pop. */
float iris26660ObjectColorGamma(float mappedGuide){
    float y=max(mappedGuide,0.0);
    if(motionHdrHandoff==0 || iris26653HighlightCompressionEnabled==0) return y;
    const float gammaValue=2.50;
    const float influencePower=6.0;
    const float whiteScale=0.90;
    float gammaOwned;
    if(y<=1.0){
        float w=pow(clamp(y,0.0,1.0),influencePower);
        float gammaMapped=whiteScale*pow(max(y,1.0e-8),gammaValue);
        gammaOwned=mix(y,gammaMapped,w);
    }else{
        const float endSlope=influencePower*(whiteScale-1.0)+whiteScale*gammaValue;
        gammaOwned=whiteScale+(y-1.0)*endSlope;
    }

    /* IRIS_26671_SINGLE_HIGHLIGHT_LUMINANCE_OWNER
     * 26670 proved that SHORT recovers real extended-linear highlight separation, while the
     * completed 26653 highlight tone and the later 26660 object-color gamma both compressed the
     * same upper display range. Preserve exact 26670 behavior through mapped linear guide 0.78.
     * Above that true-highlight boundary, release only the second gamma compression with a C1
     * smoothstep until mapped white, leaving the already-completed 26653 tone as the sole upper
     * luminance owner. No spatial sample, local mask, semantic scene class, or channel-dependent
     * operation is introduced; RGB remains uniformly scaled by the caller and hue stays unchanged.
     */
    const float releaseStart=0.78;
    if(y<=releaseStart) return gammaOwned;
    if(y>=1.0) return y;
    float t=clamp((y-releaseStart)/(1.0-releaseStart),0.0,1.0);
    float release=t*t*(3.0-2.0*t);
    return mix(gammaOwned,y,release);
}

float iris26640SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){
    float globalMapped=iris26653MapMotionSdrGuide(sourceGuide);
    if(iris26621LocalToneEnabled==0)return globalMapped;
    vec2 toneSize=vec2(textureSize(iris26621LocalToneLog,0));
    vec2 uv=(masterSourcePixel+vec2(0.5))/max(toneSize,vec2(1.0));
    vec2 halfTexel=vec2(0.5)/max(toneSize,vec2(1.0));
    float localLog=texture(iris26621LocalToneLog,clamp(uv,halfTexel,vec2(1.0)-halfTexel)).r;
    float localMapped=exp2(clamp(localLog,-12.0,0.0));
    float localStrength=smoothstep(0.030,0.100,globalMapped);
    return mix(globalMapped,localMapped,localStrength);
}
float iris26660SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){
    return iris26660ObjectColorGamma(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel));
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
 * Motion and Night may request detached lower-resolution gain maps. Map every gain pixel back to
 * the corresponding full-resolution SDR/HDR pixel center instead of accidentally reading only a
 * top-left fraction of the image. Motion adds 26641 linear-light matched pre-divide filtering.
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
/* IRIS_26641_LINEAR_LIGHT_SDR_PREDIVIDE_DOWNSAMPLE
 * Motion's half-resolution gain map averages decoded SDR radiance before dividing by the matched
 * HDR intent. At an exact 2x reduction the bilinear center sample is a 2x2 linear-light box.
 * Night deliberately keeps the pre-26641 encoded-bilinear/decode behavior. */
vec3 iris26641BilinearSdrLinear(vec2 sourcePixel){
    ivec2 sz=textureSize(SdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(srgbDecode(texelFetch(SdrBuffer,ivec2(p0.x,p0.y),0).rgb),
               srgbDecode(texelFetch(SdrBuffer,ivec2(p1.x,p0.y),0).rgb),f.x);
    vec3 b=mix(srgbDecode(texelFetch(SdrBuffer,ivec2(p0.x,p1.y),0).rgb),
               srgbDecode(texelFetch(SdrBuffer,ivec2(p1.x,p1.y),0).rgb),f.x);
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
    float sdr=motionHdrHandoff!=0
        ? max(luminance(iris26641BilinearSdrLinear(sourcePixel)),0.0)
        : max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio;
    if(motionHdrHandoff!=0){
        /* IRIS_26641_TRUE_MATCHED_SDR_HDR_INTENT_QUOTIENT
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
            float globalSdrGuide=max(iris26653MapMotionSdrGuide(sourceGuide),0.0);
            float sharedSdrGuide26658=max(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel),0.0);
            float sharedSdrGuide=max(iris26660SharedSdrGuide(sourceGuide,masterSourcePixel),0.0);
            /* IRIS_26660_UHDR_POP_TARGET_FROZEN_TO_26658
             * Preserve the exact 26658 HDR target/local-structure scale. Only the SDR denominator
             * uses the smooth object-color gamma, so the decoded HDR brightness target stays 26658. */
            float localStructureScale=globalSdrGuide>1.0e-7
                ? sharedSdrGuide26658/globalSdrGuide : 1.0;
            float requested=max(displayGain,1.0e-6)*hdrExposureScale;
            float sdrModelY=sourceY*(sharedSdrGuide/sourceGuide);
            float linearTargetY=sourceY*requested*max(localStructureScale,0.0);
            /* IRIS_26641_TRUE_MATCHED_INTENT_DELTA
             * The HDR rendition differs from the completed SDR rendition by the full luminance
             * that the matched SDR model compressed away. 26640 multiplied this delta by the
             * compression fraction a second time, effectively squaring moderate compression and
             * under-restoring scenes such as the plant shelf. Keep the actual completed SDR as
             * the spatial/color base and restore the full matched-intent delta exactly once. */
            float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);
            float hdrIntentY=sdr+matchedIntentDelta;
            ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
        }
    }else{
        float hdrTargetScale=hdrExposureScale;
        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);
        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    }
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
