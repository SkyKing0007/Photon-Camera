precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float presentationLinearAnchor;
uniform float presentationKnee;
uniform int motionToneNormalization;
out vec3 Output;

/* IRIS_26599_SHARED_HDR_PRESENTATION_NORMALIZATION
 * Motion keeps the solved display gain exactly through the linear body anchor, then smoothly
 * reduces only the additional positive gain. A single scalar derived from max(luma, peak) scales
 * whole RGB, so hue and neutrals are invariant. Night and non-positive Motion gains retain the
 * exact successful-26598 scalar behavior. This node remains presentation-only: no Camera2 write.
 */
float irisGuide(vec3 c) {
    float y = dot(c, vec3(0.2126, 0.7152, 0.0722));
    return max(y, max(c.r, max(c.g, c.b)));
}
float irisMappedGuide(float guide, float gain) {
    float g = max(guide, 0.0);
    float dg = max(gain, 1.0e-6);
    if (motionToneNormalization == 0 || dg <= 1.0 || g <= presentationLinearAnchor)
        return g * dg;
    float x = g - presentationLinearAnchor;
    float knee = max(presentationKnee, 1.0e-6);
    return presentationLinearAnchor * dg + x
        + (dg - 1.0) * knee * log(1.0 + x / knee);
}
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));
    float guide = irisGuide(c);
    if (guide <= 1.0e-7) {
        Output = c * max(displayGain, 1.0e-6);
        return;
    }
    float mapped = irisMappedGuide(guide, displayGain);
    Output = c * (mapped / guide);
}
