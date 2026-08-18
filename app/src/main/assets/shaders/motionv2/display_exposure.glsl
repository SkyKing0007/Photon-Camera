precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
out vec3 Output;

/* IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY */
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));
    Output = c * max(displayGain, 1.0);
}
