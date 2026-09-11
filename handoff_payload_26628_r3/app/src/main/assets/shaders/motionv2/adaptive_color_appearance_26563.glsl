precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float presentationChromaScale;
out vec3 Output;

/* IRIS_26628_RESTRAINED_COLOR_PRESENTATION
 * The 26626-style restrained look is now a presentation choice, not a color-correction heuristic.
 * Scale only the pixel's own Display-P3 chroma vector around its luminance.  A scale <=1 cannot
 * enlarge a pink/cyan edge, exact neutrals remain neutral, and no neighbor can donate hue.
 */
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec3 rgb=texelFetch(InputBuffer,p,0).rgb;
    float negativeFloor=min(rgb.r,min(rgb.g,rgb.b));
    if(negativeFloor<0.0)rgb-=vec3(negativeFloor);
    const vec3 displayP3Luma=vec3(0.22897456,0.69173852,0.07928691);
    float y=dot(rgb,displayP3Luma);
    vec3 chroma=rgb-vec3(y);
    float scale=clamp(presentationChromaScale,0.0,1.0);
    Output=vec3(y)+chroma*scale;
}
