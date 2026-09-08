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
uniform float iris26612SourceP99Final;
uniform float iris26612SourceP995Final;
uniform float iris26612SourceP998Final;
uniform float iris26612HdrP99Boost;
uniform float iris26612HdrP995Boost;
uniform float iris26612HdrP998Boost;
uniform float iris26612ToneStrength;
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
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}

float max3(vec3 v){return max(v.r,max(v.g,v.b));}
float iris26612MapHdrTarget(float hdrBase,float sourceFinal){
    float strength=clamp(iris26612ToneStrength,0.0,1.0);
    float a=iris26612SourceP99Final,c=iris26612SourceP995Final,b=iris26612SourceP998Final;
    if(strength<=0.0||hdrBase<=0.0||a<=0.42||c<=a||b<=c||b<=a+0.01)return hdrBase;
    float start=max(0.40,a*0.75);
    if(sourceFinal<=start)return hdrBase;
    float boost;
    if(sourceFinal<=a){float t=clamp((sourceFinal-start)/max(a-start,1.0e-6),0.0,1.0);boost=mix(1.0,iris26612HdrP99Boost,t);}
    else if(sourceFinal<=c){float t=clamp((sourceFinal-a)/max(c-a,1.0e-6),0.0,1.0);boost=mix(iris26612HdrP99Boost,iris26612HdrP995Boost,t);}
    else if(sourceFinal<=b){float t=clamp((sourceFinal-c)/max(b-c,1.0e-6),0.0,1.0);boost=mix(iris26612HdrP995Boost,iris26612HdrP998Boost,t);}
    else boost=iris26612HdrP998Boost;
    return hdrBase*mix(1.0,boost,strength);
}

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
    float hdrTargetScale=hdrExposureScale*(motionHdrHandoff!=0?max(displayGain,1.0e-6):1.0);
    vec3 hdrPositive=max(hdrRgb,vec3(0.0));
    float hdrBase=max(luminance(hdrPositive*hdrTargetScale),0.0);
    float sourceFinal=max3(hdrPositive)*hdrTargetScale;
    float hdr=motionHdrHandoff!=0?iris26612MapHdrTarget(hdrBase,sourceFinal):hdrBase;
    float sdr=max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
