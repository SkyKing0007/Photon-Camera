precision highp float;
precision mediump sampler2D;

uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out vec4 Output;

/* IRIS_26438_MATCHED_FOOTPRINT_STANDARD_GAINMAP */
const float UHDR_OFFSET = 0.015625;
float luminance(vec3 c){return dot(c,vec3(0.2126,0.7152,0.0722));}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}
float hdrLocalLogLumaMean(vec2 uv){
 vec2 texel=1.0/vec2(textureSize(HdrBuffer,0));float sum=0.0;float wsum=0.0;
 for(int oy=-2;oy<=2;oy++)for(int ox=-2;ox<=2;ox++){float r2=float(ox*ox+oy*oy);float w=exp(-0.55*r2);vec3 c=max(texture(HdrBuffer,clamp(uv+vec2(float(ox),float(oy))*texel,vec2(0.0),vec2(1.0))).rgb,vec3(0.0));sum+=w*log(1.0e-4+max(luminance(c),0.0));wsum+=w;}return sum/max(wsum,1.0e-6);
}
vec3 applyHdrMicrocontrast(vec2 uv,vec3 rgb){rgb=max(rgb,vec3(0.0));float y=max(luminance(rgb),0.0);if(y<=1.0e-7)return rgb;float detail=log(1.0e-4+y)-hdrLocalLogLumaMean(uv);detail=clamp(detail,-0.20,0.20);float gate=smoothstep(0.025,0.12,y)*(1.0-smoothstep(0.55,0.92,y));return rgb*exp(0.42*gate*detail);}
vec3 matchedHdrFootprint(vec2 uv){vec2 texel=1.0/vec2(textureSize(HdrBuffer,0));vec3 sum=vec3(0.0);for(int oy=0;oy<4;oy++)for(int ox=0;ox<4;ox++){vec2 d=(vec2(float(ox),float(oy))-vec2(1.5))*texel;vec2 suv=clamp(uv+d,vec2(0.0),vec2(1.0));vec3 c=max(texture(HdrBuffer,suv).rgb,vec3(0.0));sum+=applyHdrMicrocontrast(suv,c);}return sum*(1.0/16.0);}
vec3 matchedSdrFootprint(vec2 uv){vec2 texel=1.0/vec2(textureSize(SdrBuffer,0));vec3 sum=vec3(0.0);for(int oy=0;oy<4;oy++)for(int ox=0;ox<4;ox++){vec2 d=(vec2(float(ox),float(oy))-vec2(1.5))*texel;vec3 c=texture(SdrBuffer,clamp(uv+d,vec2(0.0),vec2(1.0))).rgb;sum+=srgbDecode(c);}return sum*(1.0/16.0);}
void main(){vec2 uv=gl_FragCoord.xy/vec2(max(gainMapSize,ivec2(1)));vec3 hdr=matchedHdrFootprint(uv)*hdrExposureScale;vec3 sdr=matchedSdrFootprint(uv);float hdrY=max(luminance(hdr),0.0);float sdrY=max(luminance(sdr),0.0);float ratio=clamp((hdrY+UHDR_OFFSET)/(sdrY+UHDR_OFFSET),1.0,max(maxGainRatio,1.001));float encoded=log2(ratio)/max(log2(max(maxGainRatio,1.001)),1.0e-6);encoded=clamp(encoded,0.0,1.0);Output=vec4(encoded,encoded,encoded,1.0);}