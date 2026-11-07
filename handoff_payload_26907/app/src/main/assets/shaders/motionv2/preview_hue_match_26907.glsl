precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D HueDeltas;
out vec3 Output;

/* IRIS_26907_HUE_ONLY_PREVIEW_REFERENCE
 * Accepts only independently measured, spatially aligned shutter-preview hue residuals.
 * Input and output are linear Display-P3. Keep Display-P3 luminance EXACT and preserve the
 * perceptual chroma magnitude. Do not alter tone, exposure, white point, or saturation policy.
 * Unmatched scenes never invoke this shader. No static hue direction or offset is hardcoded.
 */
const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;
const vec3 P3_Y = vec3(0.22897456,0.69173852,0.07928691);

vec3 p3ToLinearSrgb(vec3 c) {
    return vec3(1.22494018*c.r-0.22494018*c.g,
                -0.04205695*c.r+1.04205695*c.g,
                -0.01963755*c.r-0.07863605*c.g+1.09827360*c.b);
}
vec3 linearSrgbToP3(vec3 c) {
    return vec3(0.8224621*c.r+0.1775379*c.g,
                0.0331941*c.r+0.9668059*c.g,
                0.0170827*c.r+0.0723974*c.g+0.9105199*c.b);
}
vec3 rgbToOklab(vec3 c) {
    vec3 lms=vec3(dot(c,vec3(0.4122214708,0.5363325363,0.0514459929)),
                  dot(c,vec3(0.2119034982,0.6806995451,0.1073969566)),
                  dot(c,vec3(0.0883024619,0.2817188376,0.6299787005)));
    lms=pow(max(lms,vec3(0.0)),vec3(1.0/3.0));
    return vec3(dot(lms,vec3(0.2104542553,0.7936177850,-0.0040720468)),
                dot(lms,vec3(1.9779984951,-2.4285922050,0.4505937099)),
                dot(lms,vec3(0.0259040371,0.7827717662,-0.8086757660)));
}
vec3 oklabToRgb(vec3 c) {
    vec3 lms=vec3(c.x+0.3963377774*c.y+0.2158037573*c.z,
                  c.x-0.1055613458*c.y-0.0638541728*c.z,
                  c.x-0.0894841775*c.y-1.2914855480*c.z);
    lms=lms*lms*lms;
    return vec3(dot(lms,vec3(4.0767416621,-3.3077115913,0.2309699292)),
                dot(lms,vec3(-1.2684380046,2.6097574011,-0.3413193965)),
                dot(lms,vec3(-0.0041960863,-0.7034186147,1.7076147010)));
}
float measuredDelta(float hue) {
    const int N=48;
    float position=fract((hue+TAU)/TAU)*float(N)-0.5;
    float lower=floor(position);
    int i0=(int(lower)+N)%N;
    int i1=(i0+1)%N;
    return mix(texelFetch(HueDeltas,ivec2(i0,0),0).r,
               texelFetch(HueDeltas,ivec2(i1,0),0).r,
               fract(position));
}
vec3 rotateHueWithoutTone(vec3 p3,vec3 lab,float delta) {
    float angle=atan(lab.z,lab.y)+delta;
    float chroma=length(lab.yz);
    vec3 target=oklabToRgb(vec3(lab.x,chroma*cos(angle),chroma*sin(angle)));
    vec3 outP3=linearSrgbToP3(target);
    float oldY=dot(p3,P3_Y);
    float newY=dot(outP3,P3_Y);
    if(newY<=1.0e-8)return p3;
    outP3*=oldY/newY;
    return outP3;
}
void main(){
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 src=texelFetch(InputBuffer,xy,0).rgb;
    Output=src;
    if(any(lessThan(src,vec3(0.0)))||any(isnan(src))||any(isinf(src)))return;
    vec3 rgb=p3ToLinearSrgb(src);
    vec3 lab=rgbToOklab(rgb);
    if(length(lab.yz)<0.045||lab.x<0.10||lab.x>0.95)return;
    float delta=measuredDelta(atan(lab.z,lab.y));
    if(abs(delta)<0.0001)return;
    vec3 result=rotateHueWithoutTone(src,lab,delta);
    if(any(lessThan(result,vec3(-0.000005)))||any(isnan(result))||any(isinf(result))){
        result=rotateHueWithoutTone(src,lab,0.5*delta);
        if(any(lessThan(result,vec3(-0.000005)))||any(isnan(result))||any(isinf(result)))return;
    }
    Output=max(result,vec3(0.0));
}
