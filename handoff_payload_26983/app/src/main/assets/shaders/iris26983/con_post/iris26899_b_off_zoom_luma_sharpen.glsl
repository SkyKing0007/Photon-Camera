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
/* IRIS_26902_LENS_RELATIVE_SCALE_AWARE_RADIUS:
 * Actual per-active-optical-lens software zoom, never global display zoom. */
uniform float iris26902LensLocalZoomForRadius;
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

    /* Preserve the original 12-neighbor fetch count. Expand only the medium
     * detector's physical footprint: a high lens-relative digital zoom requires
     * a farther comparison than +/-2 output pixels to expose curvature.
     * Smooth source ramps remain unsharpened unless source evidence bends. */
    float lensLocalZoom=clamp(iris26902LensLocalZoomForRadius,1.0,30.0);
    int radius=int(clamp(floor(1.0+0.80*max(lensLocalZoom-1.0,0.0)+0.5),2.0,24.0));
    float farAxial = iris26899ReadY(p+ivec2(-radius, 0),hi) +
                     iris26899ReadY(p+ivec2( radius, 0),hi) +
                     iris26899ReadY(p+ivec2( 0,-radius),hi) +
                     iris26899ReadY(p+ivec2( 0, radius),hi);
    float diagonal = iris26899ReadY(p+ivec2(-radius,-radius),hi) +
                     iris26899ReadY(p+ivec2(-radius, radius),hi) +
                     iris26899ReadY(p+ivec2( radius,-radius),hi) +
                     iris26899ReadY(p+ivec2( radius, radius),hi);
    float mediumMean = (4.0*y + farAxial + diagonal) / 12.0;

    /* IRIS_26902_BICUBIC_COMPLEMENT_GAINS: preserve the 26900 removal of
     * arbitrary low-contrast/noise-evidence suppression. The new deliberate
     * user-specified +35..+150% curve is computed by the B-only Java owner.
     * Retain prior near-black/near-white safeguards and luminance bounds. */
    float mediumWeight=mix(0.26,0.50,smoothstep(3.0,12.0,lensLocalZoom));
    float detail=(1.0-mediumWeight)*(y-fineMean)+mediumWeight*(y-mediumMean);
    float shadowGate=smoothstep(0.006,0.018,y);
    float highlightGate=1.0-smoothstep(0.965,0.994,y);
    float gate=shadowGate*highlightGate;
    float relativeGain = 1.0 + clamp(iris26899AdditionalPct, 35.0, 150.0)/100.0;
    float boundedDelta = clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082);
    float sharpY = clamp(y + boundedDelta, 0.0, 1.0);
    /* Do not introduce independent R/G/B edge decisions or false chroma.
     * Uniform RGB scaling retains hue unless an extreme channel clips. */
    float ratio = clamp(sharpY / max(y, 1.0e-5), 0.55, 1.60);
    Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));
}
