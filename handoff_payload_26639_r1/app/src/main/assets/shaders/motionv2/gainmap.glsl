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
float iris26639BaseGlobalSdrGuide(float sourceGuide){
    const float outputScale=0.80;
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*outputScale;
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float shoulderRatio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float oneMinus=1.0-x;
        float cubic=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
        float rational=bodyGain*x/(1.0+shoulderRatio*x);
        return 0.5*(cubic+rational);
    }
    float rationalSlope=bodyGain/((1.0+shoulderRatio)*(1.0+shoulderRatio));
    float bodySlope=0.5*(whiteAnchor+rationalSlope);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlope,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
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
    vec3 hdrRgb;
    if(zoom<=1.00001){
        hdrRgb=iris26524BilinearHdr(sourcePixel);
    }else{
        ivec2 hdrSize=textureSize(HdrBuffer,0);
        vec2 center=(vec2(hdrSize)-vec2(1.0))*0.5;
        vec2 zoomedSource=center+(sourcePixel-center)/zoom;
        hdrRgb=iris26524BilinearHdr(zoomedSource);
    }
    vec3 hdrPositive=max(hdrRgb,vec3(0.0));
    float sdr=max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio;
    if(motionHdrHandoff!=0){
        /* IRIS_26639_SELECTIVE_RECOVERABLE_HEADROOM_UHDR
         * Ordinary SDR body is exact unity. Eligibility is pointwise/source-aligned and is never
         * spatially dilated, so a chandelier cannot lend gain to a darker neighbor. Desired gain is
         * derived from the same pre-tone max-channel/luma guide and the frozen 0.80 brightness target.
         * The actual SDR sample is used only as a one-sided ceiling: local tone/detail can REDUCE gain
         * to prevent an overshoot rim, but can never create extra gain or an HDR island. */
        const float hdrEntry=0.65;
        const float hdrFullEntry=0.85;
        float sourceY=max(luminance(hdrPositive),0.0);
        float sourceGuide=max(sourceY,max3(hdrPositive));
        float eligibility=smoothstep(hdrEntry,hdrFullEntry,sourceGuide);
        if(sourceGuide<=hdrEntry || eligibility<=1.0e-7){
            ratio=1.0;
        }else{
            float globalSdr=max(iris26639BaseGlobalSdrGuide(sourceGuide),0.0);
            float requested=max(displayGain,1.0e-6)*hdrExposureScale;
            float recoverable=max(globalSdr,sourceY*requested);
            float desired=clamp((recoverable+UHDR_OFFSET)/(globalSdr+UHDR_OFFSET),1.0,safeMax);
            float pixelCeiling=clamp((recoverable+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
            float eligibleRatio=min(desired,pixelCeiling);
            ratio=clamp(exp2(log2(max(eligibleRatio,1.0))*eligibility),1.0,safeMax);
        }
    }else{
        float hdrTargetScale=hdrExposureScale;
        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);
        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    }
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
