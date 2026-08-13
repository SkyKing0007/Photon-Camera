#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=1) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=2) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=3) uniform highp writeonly image2D outRgb;
uniform float wbR;
uniform float wbG;
uniform float wbB;

/* IRIS_26463_WRONSKI_PUBLIC_DIVIDE_ONCE_FINALIZER
 * Public super_resolution.py divides num/den only once after every frame.
 * Wronski was run in its WB signal domain; divide those gains here only to
 * return completed RGB to Photon's proven sensor-linear Camera2 color stage.
 */
/* IRIS_26465_FULLY_CLIPPED_NEUTRAL_HIGHLIGHT_RECOVERY
 * If all three CFA colors have lost unsaturated support, chroma is no longer
 * physically observed. Preserve balanced-domain highlight luminance and
 * collapse only that unsupported chroma toward neutral. If any channel still
 * has substantial unsaturated support, preserve the Wronski color unchanged.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,imageSize(outRgb)))) return;
    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/den;
    vec4 support=imageLoad(currentFrameSupport,p);
    vec3 validDen=max(support.gba,vec3(0.0));
    vec3 validRatio=clamp(validDen/den,vec3(0.0),vec3(1.0));
    float strongestValid=max(validRatio.r,max(validRatio.g,validRatio.b));
    float unsupportedAll=1.0-smoothstep(0.08,0.35,strongestValid);
    float highlightLevel=max(wbRgb.r,max(wbRgb.g,wbRgb.b));
    vec3 neutralWb=vec3(highlightLevel);
    wbRgb=mix(wbRgb,neutralWb,unsupportedAll);
    vec3 sensorRgb=wbRgb/vec3(max(wbR,1e-6),max(wbG,1e-6),max(wbB,1e-6));
    float fs=max(support.r,1.0);
    imageStore(outRgb,p,vec4(max(sensorRgb,vec3(0)),fs));
}
