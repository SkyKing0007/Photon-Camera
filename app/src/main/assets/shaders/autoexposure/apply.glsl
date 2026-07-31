precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform float mpy;
uniform float whiteMax;
uniform float applyGammaMix;
uniform float indoorHdrStrength;
uniform float lowerMidLift;
uniform float highlightCompression;
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

    float lowerMidMask =
            smoothstep(
                    0.08,
                    0.22,
                    luma
            )
            * (
                    1.0
                            - smoothstep(
                                    0.52,
                                    0.72,
                                    luma
                            )
            );

    Output.rgb *=
            1.0
                    + lowerMidLift
                    * lowerMidMask;

    luma =
            dot(
                    Output.rgb,
                    vec3(0.299, 0.587, 0.114)
            );

    float highlightMask =
            smoothstep(
                    0.52,
                    0.92,
                    luma
            );

    vec3 compressedHighlights =
            Output.rgb
                    / (
                            vec3(1.0)
                                    + 0.55
                                    * Output.rgb
                    );

    Output.rgb =
            mix(
                    Output.rgb,
                    compressedHighlights,
                    highlightCompression
                            * highlightMask
            );

    Output.rgb =
            clamp(
                    Output.rgb,
                    0.0,
                    1.0
            );
}
