precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

/* IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_CLIP_AUTHORITY
 * The Wronski CFA path already enters a green-normalized calculation-WB domain
 * and mfsr_finalize removes those temporary gains. This stage therefore owns
 * only the one authoritative Camera2 WB + 3x3 color transform. No inferred
 * sensor clipping is attempted after CFA evidence has already been reconstructed.
 */
void main(){
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    vec3 balanced=cameraRgb*max(sensorGains,vec3(1.0e-6));
    vec3 linearSrgb=vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
    Output=max(linearSrgb,vec3(0.0));
}
