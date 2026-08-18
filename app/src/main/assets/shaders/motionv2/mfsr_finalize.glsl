#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=1) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=2) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=3) uniform highp writeonly image2D outRgb;
uniform float wbR;uniform float wbG;uniform float wbB;uniform sampler2D lensShadingMap;uniform int useLensShading;
/* IRIS_26488_BJZHOU_RGB_NORMALIZE_LSC_CAMERA_DOMAIN
 * Camera2 lens shading is applied exactly once in the normalized calculation-RGB chain, using
 * R, mean(Gr/Gb), B as in bjzhou MGC RGB normalization.
 *
 * IRIS_26487_OPPONENT_NORMALIZE_ONCE_NO_SUPPORT_HUE_FADE
 * Each semantic channel is divided only by its own true valid denominator.
 * Missing clipped opponent evidence becomes neutral only when that denominator
 * is actually zero; no arbitrary support-ratio fade can create a colored halo.
 */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,imageSize(outRgb))))return;vec3 num=imageLoad(currentNumerator,p).rgb,den=imageLoad(currentDenominator,p).rgb;float g=num.x/max(den.x,1e-12);float rg=den.y>1e-10?num.y/den.y:0.0;float bg=den.z>1e-10?num.z/den.z:0.0;vec3 wbRgb=vec3(g+rg,g,g+bg);if(useLensShading!=0){vec2 uv=(vec2(p)+vec2(0.5))/vec2(imageSize(outRgb));vec4 shading=texture(lensShadingMap,clamp(uv,vec2(0.0),vec2(1.0)));wbRgb*=vec3(shading.r,0.5*(shading.g+shading.b),shading.a);}vec3 sensor=wbRgb/vec3(max(wbR,1e-6),max(wbG,1e-6),max(wbB,1e-6));float support=1.0+max(imageLoad(currentFrameSupport,p).r,0.0);imageStore(outRgb,p,vec4(max(sensor,vec3(0.0)),support));}
