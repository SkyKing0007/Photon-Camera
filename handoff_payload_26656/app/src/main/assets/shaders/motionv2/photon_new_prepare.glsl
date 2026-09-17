precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D GainMap;
uniform float irisSaturation;
out vec4 Output;

const vec3 PHOTON_LUMA=vec3(0.299,0.587,0.114);
const vec3 IRIS_P3_LUMA=vec3(0.22897456,0.69173852,0.07928691);
float photonLuma(vec3 c){return dot(c,PHOTON_LUMA);}
float irisLuma(vec3 c){return dot(c,IRIS_P3_LUMA);}
float gammaEncode0(float x){return x<=0.0031308?x*12.92:1.055*pow(max(x,0.0),1.0/2.4)-0.055;}
vec3 gammaEncode0(vec3 x){return vec3(gammaEncode0(x.r),gammaEncode0(x.g),gammaEncode0(x.b));}
vec3 irisSaturate(vec3 rgb,float sat){float y=irisLuma(rgb);return max(mix(vec3(y),rgb,sat),vec3(0.0));}
float reinhardExtended(float v,float maxWhite){return v*(1.0+v/(maxWhite*maxWhite))/(1.0+v);}
vec4 cubic(float x){float x2=x*x,x3=x2*x;return vec4(-x3+3.0*x2-3.0*x+1.0,3.0*x3-6.0*x2+4.0,-3.0*x3+3.0*x2+3.0*x+1.0,x3)/6.0;}
vec4 textureBicubicHardware(sampler2D sampler,vec2 texCoords){
    vec2 texSize=vec2(textureSize(sampler,0)),invTexSize=1.0/texSize;
    texCoords=texCoords*texSize-0.5;vec2 fxy=fract(texCoords);texCoords-=fxy;
    vec4 xcubic=cubic(fxy.x),ycubic=cubic(fxy.y);
    vec4 c=texCoords.xxyy+vec2(-0.5,+1.5).xyxy;
    vec4 s=vec4(xcubic.xz+xcubic.yw,ycubic.xz+ycubic.yw);
    vec4 offset=c+vec4(xcubic.yw,ycubic.yw)/s;offset*=invTexSize.xxyy;
    vec4 sample0=texture(sampler,offset.xz),sample1=texture(sampler,offset.yz);
    vec4 sample2=texture(sampler,offset.xw),sample3=texture(sampler,offset.yw);
    float sx=s.x/(s.x+s.y),sy=s.z/(s.z+s.w);
    return mix(mix(sample3,sample2,sx),mix(sample1,sample0,sx),sy);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec3 rgb=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
    /* Photon exposure scalar already ran pre-color; Iris color is now frozen in this RGB. */

    /* ModernInitial local white point from the Camera2 lens gain map. Reproduce Photon's
       bicubic gain sampling and gainsVal exactly, but apply its Reinhard result to luminance
       as a common scalar so Iris's proven pink/green/magenta chroma protection remains intact. */
    vec2 uv=(gl_FragCoord.xy-vec2(0.5))/vec2(textureSize(InputBuffer,0));
    vec4 gains=textureBicubicHardware(GainMap,uv);
    vec3 gainRgb=vec3(gains.r,(gains.g+gains.b)*0.5,gains.a);
    float gainsVal=max(dot(gainRgb,vec3(1.0/3.0)),1.0);
    float pk=max(rgb.r,max(rgb.g,rgb.b));
    if(pk>1.0)rgb/=pk; // common-axis equivalent of ModernInitial's pre-Reinhard clamp
    float y=max(irisLuma(rgb),0.0);
    if(y>1.0e-8){float ty=clamp(reinhardExtended(y*gainsVal,gainsVal),0.0,1.0);rgb*=ty/y;}
    float pkTone=max(rgb.r,max(rgb.g,rgb.b));if(pkTone>1.0)rgb/=pkTone;

    rgb=gammaEncode0(clamp(rgb,vec3(0.0),vec3(1.0)));
    /* Photon New default BASECONTRAST=0 and user contrast/shadow are intentionally not imported;
       Iris's color preference is retained solely as its frozen per-lens saturation. */
    rgb=irisSaturate(rgb,clamp(irisSaturation,0.0,2.0));
    float pk2=max(rgb.r,max(rgb.g,rgb.b));if(pk2>1.0)rgb/=pk2;
    Output=vec4(clamp(rgb,vec3(0.0),vec3(1.0)),1.0);
}
