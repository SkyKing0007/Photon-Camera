precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out float Output;

/* IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY
 * Android Ultra HDR permits a gain map at the same resolution as the primary.
 * Generate the standard logarithmic gain per primary pixel, so the decoder never
 * has to spatially resample a lower-resolution brightness edge over the sharp SDR
 * base. The SDR image remains the exact spatial/color primary; UHDR changes only
 * the per-pixel display gain.
 */
const float UHDR_OFFSET = 0.015625;
float luminance(vec3 c){return dot(c,vec3(0.2126,0.7152,0.0722));}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,gainMapSize))){Output=0.0;return;}
    float hdr=max(luminance(max(texelFetch(HdrBuffer,p,0).rgb,vec3(0.0))*hdrExposureScale),0.0);
    float sdr=max(luminance(srgbDecode(texelFetch(SdrBuffer,p,0).rgb)),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
