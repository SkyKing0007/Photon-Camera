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
uniform float irisHdrAbsoluteBlackPreserve;
uniform float irisHdrDeepShadowStart;
uniform float irisHdrFullShadowPoint;
uniform float irisHdrDeepShadowStrength;
uniform float irisHdrUpperMidProtectStart;
uniform float irisHdrUpperMidProtectEnd;
uniform float irisHdrDeepShadowSafety;
uniform float irisHdrChromaPreservationStrength;
uniform float irisHdrMinimumShadowColorRetention;
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
     * IRIS_26353_BRIGHTNESS_PRESERVING_SHOULDER
     */
    float irisHdrLuma =
            dot(Output.rgb, vec3(0.299, 0.587, 0.114));

    float irisHdrShoulderStart =
            mix(
                    0.80,
                    0.72,
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
                                    0.05 * irisHdrHighlightMask
                                            + 0.95
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


    /*
     * IRIS_26355_CONTEXT_AWARE_HDR_TONE_CURVE
     */
    float iris26355AbsoluteBlackGate =
            smoothstep(irisHdrAbsoluteBlackPreserve,
                    irisHdrDeepShadowStart,
                    irisHdrToneLuma);

    float iris26355FullShadowGate =
            smoothstep(irisHdrDeepShadowStart,
                    irisHdrFullShadowPoint,
                    irisHdrToneLuma);

    float iris26355DeepShadowEligibility =
            irisHdrDeepShadowStrength * irisHdrDeepShadowSafety;

    float irisHdrBlackProtection =
            iris26355AbsoluteBlackGate
                    * mix(iris26355DeepShadowEligibility,
                            1.0,
                            iris26355FullShadowGate);

    /*
     * IRIS_26368_DEEP_SHADOW_LATITUDE
     *
     * Gate deepest-toe latitude with the existing 26366 lower-mid need.
     * Good 163039 control (~0.1465) and closet low-light controls
     * (~0.066-0.074) remain excluded; crushed direct-bright case
     * (~0.181) is fully eligible.
     */
    float iris26368LatitudeNeed =
            smoothstep(
                    0.150,
                    0.180,
                    irisHdrLowerMidLift);

    float iris26368ToeSignal =
            smoothstep(
                    0.0015,
                    max(irisHdrDeepShadowStart, 0.0030),
                    irisHdrToneLuma);

    float iris26368ToeOnly =
            1.0 - iris26355FullShadowGate;

    float iris26368ToeLatitude =
            iris26368LatitudeNeed
                    * iris26368ToeSignal
                    * iris26368ToeOnly
                    * (0.18 * irisHdrDeepShadowSafety);

    irisHdrBlackProtection =
            max(
                    irisHdrBlackProtection,
                    iris26368ToeLatitude);

    float irisHdrUpperMidProtection =
            1.0 - smoothstep(irisHdrUpperMidProtectStart,
                    irisHdrUpperMidProtectEnd,
                    irisHdrToneLuma);

    float irisHdrLowerMidMask =
            clamp(irisHdrBlackProtection * irisHdrUpperMidProtection,
                    0.0,
                    1.0);

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

    /*
     * IRIS_26369_HDR_SATURATION_PRESERVATION
     *
     * 26358 kept absolute chroma fixed while adaptive HDR changed luminance.
     * That can make strongly lifted dark colors look washed out and can leave
     * differently-tonemapped colors looking too strong.
     *
     * Preserve chroma relative to the HDR luminance movement instead:
     * - luminance lift may increase chroma modestly;
     * - luminance compression may reduce chroma modestly;
     * - correction is bounded and partial, never a global saturation boost;
     * - very dark/noisy signal fades back to the proven 26358 behavior;
     * - the existing gamut and near-black chroma safety below still applies.
     */
    float iris26369SourceLuma =
            max(irisHdrLuma, 0.0005);

    float iris26369LumaRatio =
            irisHdrOutputLuma / iris26369SourceLuma;

    /*
     * Full saturation preservation would use the complete luma ratio.
     * Limit the requested chroma response to avoid foliage/skin overshoot.
     */
    float iris26369BoundedRatio =
            clamp(
                    iris26369LumaRatio,
                    0.78,
                    1.32);

    float iris26369ToneDelta =
            abs(irisHdrOutputLuma - irisHdrLuma);

    float iris26369ToneActivity =
            smoothstep(
                    0.008,
                    0.12,
                    iris26369ToneDelta);

    /*
     * Do not amplify chroma from values that are effectively black/noisy.
     * Above normal shadow levels the correction becomes fully eligible.
     */
    /*
     * IRIS_26376_COLOR_SAFE_HDR_PRESERVATION
     *
     * Strong real source chroma is never itself a reason to reduce color.
     *
     * Keep the improved lower-signal eligibility introduced during 26375,
     * but restore the bounded 26369 preservation strength so saturated
     * figurine prints, plaid, clothing, foliage, and other real colors do
     * not get muted simply because they are strongly colored.
     */
    float iris26369SignalSafety =
            smoothstep(
                    0.010,
                    0.060,
                    irisHdrLuma);

    float iris26369HdrActivity =
            clamp(
                    max(
                            irisHdrLowerMidLift / 0.30,
                            irisHdrHighlightCompression),
                    0.0,
                    1.0);

    float iris26369PreservationStrength =
            0.72
                    * iris26369ToneActivity
                    * iris26369SignalSafety
                    * iris26369HdrActivity;

    float iris26369ChromaScale =
            mix(
                    1.0,
                    iris26369BoundedRatio,
                    iris26369PreservationStrength);

    vec3 iris26356PreservedChroma =
            irisHdrChroma * iris26369ChromaScale;

    float irisHdrPositiveHeadroom =
            min(
                    iris26356PreservedChroma.r > 0.0
                            ? (1.0 - irisHdrOutputLuma)
                                    / max(iris26356PreservedChroma.r, 0.000001)
                            : 1.0,
                    min(
                            iris26356PreservedChroma.g > 0.0
                                    ? (1.0 - irisHdrOutputLuma)
                                            / max(iris26356PreservedChroma.g, 0.000001)
                                    : 1.0,
                            iris26356PreservedChroma.b > 0.0
                                    ? (1.0 - irisHdrOutputLuma)
                                            / max(iris26356PreservedChroma.b, 0.000001)
                                    : 1.0
                    )
            );

    float irisHdrNegativeHeadroom =
            min(
                    iris26356PreservedChroma.r < 0.0
                            ? irisHdrOutputLuma
                                    / max(-iris26356PreservedChroma.r, 0.000001)
                            : 1.0,
                    min(
                            iris26356PreservedChroma.g < 0.0
                                    ? irisHdrOutputLuma
                                            / max(-iris26356PreservedChroma.g, 0.000001)
                                    : 1.0,
                            iris26356PreservedChroma.b < 0.0
                                    ? irisHdrOutputLuma
                                            / max(-iris26356PreservedChroma.b, 0.000001)
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
            irisHdrMinimumShadowColorRetention,
            clamp(iris26347NearBlack * irisHdrShadowChromaProtection, 0.0, 1.0));
    irisHdrSafeChromaScale *= iris26347ChromaRetention;

    Output.rgb =
            clamp(
                    vec3(irisHdrOutputLuma)
                            + iris26356PreservedChroma * irisHdrSafeChromaScale,
                    0.0,
                    1.0
            );
}
