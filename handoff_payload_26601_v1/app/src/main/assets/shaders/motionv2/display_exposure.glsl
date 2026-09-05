precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
out vec3 Output;

/* IRIS_26516_SIGNED_PRESENTATION_EV_SCALAR
 * This shader is a pure positive linear scalar. Source restoration normally uses >=1x, while
 * viewfinder-matched presentation may legitimately be below 1x. No Camera2 authority lives here.
 */
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));
    Output = c * max(displayGain, 1.0e-6);
}
