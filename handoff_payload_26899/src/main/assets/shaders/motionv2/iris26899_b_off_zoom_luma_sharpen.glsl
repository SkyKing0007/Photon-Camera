precision highp float;
precision mediump sampler2D;

/* IRIS_26899_SHUTTER_FROZEN_B_SR_OFF_HIGH_ZOOM_ONLY
 * This shader is invoked only after the existing SDR renderer has completed;
 * no changes to original Sabre/VGN, RAW, Bayer, DNG, color or UHDR math.
 * Luma weights operate in the final encoded SDR display domain. A bounded
 * scalar applied uniformly to RGB preserves local channel proportions.
 */
uniform sampler2D InputBuffer;
uniform float iris26899AdditionalPct;
out vec3 Output;

float iris26899Luma(vec3 rgb) {
    return dot(rgb, vec3(0.2126, 0.7152, 0.0722));
}
float iris26899ReadY(ivec2 p, ivec2 hi) {
    return iris26899Luma(clamp(texelFetch(InputBuffer, clamp(p, ivec2(0), hi), 0).rgb,
                                 vec3(0.0), vec3(1.0)));
}

void main() {
    ivec2 sz = textureSize(InputBuffer, 0);
    ivec2 hi = max(sz - ivec2(1), ivec2(0));
    ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), hi);
    vec3 rgb = clamp(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0), vec3(1.0));
    float y = iris26899Luma(rgb);
    if (y < 0.006 || y > 0.994) { Output = rgb; return; }

    float l = iris26899ReadY(p + ivec2(-1, 0), hi);
    float r = iris26899ReadY(p + ivec2( 1, 0), hi);
    float u = iris26899ReadY(p + ivec2( 0,-1), hi);
    float d = iris26899ReadY(p + ivec2( 0, 1), hi);
    float fineMean = (4.0*y + l+r+u+d) * 0.125;

    float farAxial = iris26899ReadY(p+ivec2(-2, 0),hi) +
                     iris26899ReadY(p+ivec2( 2, 0),hi) +
                     iris26899ReadY(p+ivec2( 0,-2),hi) +
                     iris26899ReadY(p+ivec2( 0, 2),hi);
    float diagonal = iris26899ReadY(p+ivec2(-2,-2),hi) +
                     iris26899ReadY(p+ivec2(-2, 2),hi) +
                     iris26899ReadY(p+ivec2( 2,-2),hi) +
                     iris26899ReadY(p+ivec2( 2, 2),hi);
    float mediumMean = (4.0*y + farAxial + diagonal) / 12.0;

    /* A conservative low-contrast gate protects flat skies and shadow grain;
     * a bounded edge amplitude prevents white/dark overshoot at high zoom.
     * Double the nominal baseline at 1.10..10x; 2.5x at 20x; 3x >=30x.
     */
    float detail = 0.74*(y-fineMean) + 0.26*(y-mediumMean);
    float contrastEvidence = max(abs(y-fineMean), 0.65*abs(y-mediumMean));
    float evidence = smoothstep(0.0025, 0.012, contrastEvidence);
    float shadowGate = smoothstep(0.012, 0.08, y);
    float highlightGate = 1.0 - smoothstep(0.88, 0.992, y);
    float gate = evidence * shadowGate * highlightGate;
    float relativeGain = 1.0 + clamp(iris26899AdditionalPct, 100.0, 200.0)/100.0;
    float boundedDelta = clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082);
    float sharpY = clamp(y + boundedDelta, 0.0, 1.0);
    /* Do not introduce independent R/G/B edge decisions or false chroma.
     * Uniform RGB scaling retains hue unless an extreme channel clips. */
    float ratio = clamp(sharpY / max(y, 1.0e-5), 0.55, 1.60);
    Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));
}
