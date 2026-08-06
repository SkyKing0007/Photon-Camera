precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform float mpy;
uniform float whiteMax;
uniform float applyGammaMix;
uniform float irisHdrIndoorBacklitStrength;
uniform float irisHdrOutdoorBroadStrength;
uniform float irisHdrHighlightCompression;
uniform float irisHdrLowerMidLift;
uniform float irisHdrShadowChromaProtection;
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
    /*
     * Iris 26335: progressive highlight shoulder followed by selective
     * lower-midtone lift. The operations are performed in luminance and then
     * recombined with bounded chroma to reduce colored highlight halos.
     *
     * IRIS_26335_PROGRESSIVE_HDR_TONE
     */
    float irisHdrLuma =
            dot(Output.rgb, vec3(0.299, 0.587, 0.114));

    float irisHdrShoulderStart =
            mix(
                    0.72,
                    0.64,
                    irisHdrIndoorBacklitStrength
            );

    float irisHdrHighlightMask =
            smoothstep(
                    irisHdrShoulderStart,
                    0.98,
                    irisHdrLuma
            );

    float irisHdrStrongHighlightMask =
            smoothstep(
                    0.84,
                    1.04,
                    irisHdrLuma
            );

    float irisHdrShoulderCoefficient =
            mix(
                    1.55,
                    2.65,
                    max(
                            irisHdrIndoorBacklitStrength,
                            irisHdrOutdoorBroadStrength
                    )
            );

    float irisHdrHighlightExcess =
            max(
                    irisHdrLuma - irisHdrShoulderStart,
                    0.0
            );

    float irisHdrCompressedLuma =
            irisHdrShoulderStart
                    + irisHdrHighlightExcess
                            / (
                                    1.0
                                            + irisHdrShoulderCoefficient
                                                    * irisHdrHighlightExcess
                              );

    float irisHdrShoulderBlend =
            clamp(
                    irisHdrHighlightCompression
                            * (
                                    0.18 * irisHdrHighlightMask
                                            + 0.82
                                                    * irisHdrStrongHighlightMask
                              ),
                    0.0,
                    0.90
            );

    float irisHdrToneLuma =
            mix(
                    irisHdrLuma,
                    irisHdrCompressedLuma,
                    irisHdrShoulderBlend
            );

    float irisHdrBlackProtection =
            smoothstep(
                    0.035,
                    0.13,
                    irisHdrToneLuma
            );

    float irisHdrUpperMidProtection =
            1.0
                    - smoothstep(
                            0.46,
                            0.76,
                            irisHdrToneLuma
                      );

    float irisHdrLowerMidMask =
            irisHdrBlackProtection
                    * irisHdrUpperMidProtection;

    float irisHdrLiftAmount =
            irisHdrLowerMidLift
                    * irisHdrLowerMidMask
                    * (1.0 - irisHdrToneLuma);

    float irisHdrOutputLuma =
            clamp(
                    irisHdrToneLuma + irisHdrLiftAmount,
                    0.0,
                    1.0
            );

    vec3 irisHdrChroma =
            Output.rgb - vec3(irisHdrLuma);

    float irisHdrPositiveHeadroom =
            min(
                    irisHdrChroma.r > 0.0
                            ? (1.0 - irisHdrOutputLuma)
                                    / max(irisHdrChroma.r, 0.000001)
                            : 1.0,
                    min(
                            irisHdrChroma.g > 0.0
                                    ? (1.0 - irisHdrOutputLuma)
                                            / max(irisHdrChroma.g, 0.000001)
                                    : 1.0,
                            irisHdrChroma.b > 0.0
                                    ? (1.0 - irisHdrOutputLuma)
                                            / max(irisHdrChroma.b, 0.000001)
                                    : 1.0
                    )
            );

    float irisHdrNegativeHeadroom =
            min(
                    irisHdrChroma.r < 0.0
                            ? irisHdrOutputLuma
                                    / max(-irisHdrChroma.r, 0.000001)
                            : 1.0,
                    min(
                            irisHdrChroma.g < 0.0
                                    ? irisHdrOutputLuma
                                            / max(-irisHdrChroma.g, 0.000001)
                                    : 1.0,
                            irisHdrChroma.b < 0.0
                                    ? irisHdrOutputLuma
                                            / max(-irisHdrChroma.b, 0.000001)
                                    : 1.0
                    )
            );

    float irisHdrSafeChromaScale =
            clamp(
                    min(
                            irisHdrPositiveHeadroom,
                            irisHdrNegativeHeadroom
                    ),
                    0.0,
                    1.0
            );

    /* IRIS_26347_HDR_SHADOW_CHROMA_SAFETY
     * Preserve lifted luminance; fade only unreliable chroma close to black.
     */
    float iris26347NearBlack = 1.0 - smoothstep(0.035, 0.28, irisHdrOutputLuma);
    float iris26347ChromaRetention = mix(
            1.0,
            0.18,
            clamp(iris26347NearBlack * irisHdrShadowChromaProtection, 0.0, 1.0));
    irisHdrSafeChromaScale *= iris26347ChromaRetention;

    Output.rgb =
            clamp(
                    vec3(irisHdrOutputLuma)
                            + irisHdrChroma
                                    * irisHdrSafeChromaScale,
                    0.0,
                    1.0
            );
}
