precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform float mpy;
uniform float whiteMax;
uniform float applyGammaMix;
uniform float indoorHdrStrength;
uniform float lowerMidLift;
uniform float highlightCompression;
uniform float backlitWindowStrength;
out vec4 Output;
vec3 reinhard_extended(vec3 v, float max_white){
    vec3 numerator = v * (vec3(1.0f) + (v / vec3(max_white * max_white)));
    return numerator / (vec3(1.0f) + v);
}
vec2 reinhard_extended(vec2 v, float max_white){
    vec2 numerator = v * (vec2(1.0f) + (v / vec2(max_white * max_white)));
    return numerator / (vec2(1.0f) + v);
}
float reinhard_extended(float v, float max_white){
    float numerator = v * (float(1.0f) + (v / float(max_white * max_white)));
    return numerator / (float(1.0f) + v);
}

vec3 tonemap(vec3 rgb, float gain) {
    float r = rgb.r;
    float g = rgb.g;
    float b = rgb.b;

    float min_val = min(r, min(g, b));
    float max_val = max(r, max(g, b));
    float mid_val = dot(rgb, vec3(1.0)) - min_val - max_val;

    vec2 minmax_in = vec2(min_val, max_val);
    vec2 minmax = vec2(reinhard_extended(minmax_in * gain, whiteMax));

    float new_min = minmax.x;
    float new_max = minmax.y;

    float denom = max_val - min_val;
    float yprog = (mid_val - min_val) / (denom + 1e-6);
    float new_mid = new_min + (new_max - new_min) * yprog;

    // Branchless assignment using nested mix for each channel
    float new_r = mix(mix(new_mid, new_max, float(r == max_val)), new_min, float(r == min_val));
    float new_g = mix(mix(new_mid, new_max, float(g == max_val)), new_min, float(g == min_val));
    float new_b = mix(mix(new_mid, new_max, float(b == max_val)), new_min, float(b == min_val));

    return vec3(new_r, new_g, new_b);
}
void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec4 inp = texelFetch(InputBuffer, xy, 0);
    //Output.rgb = reinhard_extended(inp.rgb * mpy, mpy);
    Output.rgb = tonemap(mix(inp.rgb,sqrt(inp.rgb), applyGammaMix), mpy);
    Output.rgb = mix(Output.rgb,Output.rgb * Output.rgb, applyGammaMix);

    float luma =
            dot(
                    Output.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    /*
     * Build 26252:
     * Independent tone strengths are supplied by Java. Shadow recovery is no
     * longer disabled by a zero highlight gate, and the shoulder is driven by
     * histogram bright-tail occupancy.
     *
     * Based on the earlier 26250 curve:
     * Earlier and broader toe expansion.
     *
     * 26249 began too late and tapered too early, so the lower percentiles
     * remained decisively darker than GCam. Start recovery closer to black,
     * keep it active longer through the lower midtones, and weight the boost
     * toward true shadow structure rather than upper-mid luminance.
     *
     * Highlight handling is still performed by the existing shoulder path;
     * its strength is increased from Java by the 26250 highlightCompression
     * change above.
     */
    /*
     * Build 26253:
     * Narrow the recovery to true shadows and early lower midtones.
     * Mathematical black remains protected, strongest recovery is centered
     * around approximately 0.01-0.06, and the gain approaches unity before
     * the middle of the tonal range.
     */
    float blackProtection =
            smoothstep(
                    0.0015,
                    0.014,
                    luma
            );

    float upperMidProtection =
            1.0
                    - smoothstep(
                            0.22,
                            0.46,
                            luma
                    );

    float lowerMidMask =
            blackProtection
                    * upperMidProtection;

    float deepShadowWeight =
            1.0
                    - smoothstep(
                            0.022,
                            0.11,
                            luma
                    );

    float midShadowWeight =
            smoothstep(
                    0.04,
                    0.14,
                    luma
            )
            * (
                    1.0
                            - smoothstep(
                                    0.16,
                                    0.30,
                                    luma
                            )
            );

    float shapedGain =
            1.0
                    + lowerMidLift
                    * lowerMidMask
                    * (
                            0.55
                                    + 1.70
                                    * deepShadowWeight
                                    + 0.25
                                    * midShadowWeight
                    );

    Output.rgb =
            clamp(
                    Output.rgb * shapedGain,
                    0.0,
                    1.0
            );

    luma =
            dot(
                    Output.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    /*
     * Build 26271:
     * Keep upper midtones distinct, then progressively compress the true
     * highlight shoulder. Preserve center chroma directly rather than trying
     * to reconstruct saturation after it has already been compressed.
     */
    float highlightMask =
            smoothstep(
                    0.62,
                    0.94,
                    luma
            );

    float strongHighlightMask =
            smoothstep(
                    0.80,
                    0.985,
                    luma
            );

    vec3 preHighlightColor =
            Output.rgb;

    float preHighlightLuma =
            luma;

    vec3 preHighlightChroma =
            preHighlightColor
                    - vec3(preHighlightLuma);

    float shoulderCoefficient =
            mix(
                    0.42,
                    0.68,
                    backlitWindowStrength
            );

    vec3 compressedHighlights =
            Output.rgb
                    / (
                            vec3(1.0)
                                    + shoulderCoefficient
                                    * Output.rgb
                    );

    float shoulderBlend =
            clamp(
                    highlightCompression
                            * (
                                    0.42
                                            * highlightMask
                                            + 0.58
                                            * strongHighlightMask
                              ),
                    0.0,
                    0.78
            );

    vec3 compressedOutput =
            mix(
                    Output.rgb,
                    compressedHighlights,
                    shoulderBlend
            );

    float compressedLuma =
            dot(
                    compressedOutput,
                    vec3(0.299, 0.587, 0.114)
            );

    /*
     * Direct center-chroma retention. This does not multiply saturation; it
     * prevents the shoulder from collapsing existing non-clipped color.
     */
    float nonClipProtection =
            1.0
                    - smoothstep(
                            0.94,
                            0.995,
                            max(
                                    preHighlightColor.r,
                                    max(
                                            preHighlightColor.g,
                                            preHighlightColor.b
                                    )
                            )
                    );

    float chromaRetention =
            clamp(
                    (
                            0.86
                                    + 0.10
                                    * backlitWindowStrength
                    )
                            * nonClipProtection,
                    0.0,
                    0.96
            );

    vec3 retainedColor =
            vec3(compressedLuma)
                    + preHighlightChroma
                            * mix(
                                    compressedLuma
                                            / max(preHighlightLuma, 0.0001),
                                    1.0,
                                    chromaRetention
                              );

    /*
     * Restore a small amount of local luminance separation in the bright
     * region. The detail signal comes from the pre-tone input and is clamped
     * tightly to avoid halos.
     */
    ivec2 size =
            textureSize(
                    InputBuffer,
                    0
            );

    ivec2 maxCoord =
            size - ivec2(1);

    float inputCenterLuma =
            dot(
                    inp.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    float inputNeighborAverage =
            0.25
                    * (
                            dot(
                                    texelFetch(
                                            InputBuffer,
                                            clamp(xy + ivec2(-2, 0), ivec2(0), maxCoord),
                                            0
                                    ).rgb,
                                    vec3(0.299, 0.587, 0.114)
                            )
                                    + dot(
                                            texelFetch(
                                                    InputBuffer,
                                                    clamp(xy + ivec2(2, 0), ivec2(0), maxCoord),
                                                    0
                                            ).rgb,
                                            vec3(0.299, 0.587, 0.114)
                                      )
                                    + dot(
                                            texelFetch(
                                                    InputBuffer,
                                                    clamp(xy + ivec2(0, -2), ivec2(0), maxCoord),
                                                    0
                                            ).rgb,
                                            vec3(0.299, 0.587, 0.114)
                                      )
                                    + dot(
                                            texelFetch(
                                                    InputBuffer,
                                                    clamp(xy + ivec2(0, 2), ivec2(0), maxCoord),
                                                    0
                                            ).rgb,
                                            vec3(0.299, 0.587, 0.114)
                                      )
                      );

    float localDetail =
            clamp(
                    inputCenterLuma
                            - inputNeighborAverage,
                    -0.025,
                    0.025
            );

    float detailStrength =
            0.32
                    * backlitWindowStrength
                    * highlightMask
                    * nonClipProtection;

    retainedColor +=
            vec3(
                    localDetail
                            * detailStrength
            );

    Output.rgb =
            mix(
                    compressedOutput,
                    retainedColor,
                    0.72
                            * nonClipProtection
            );

    Output.rgb =
            clamp(
                    Output.rgb,
                    0.0,
                    1.0
            );
}
