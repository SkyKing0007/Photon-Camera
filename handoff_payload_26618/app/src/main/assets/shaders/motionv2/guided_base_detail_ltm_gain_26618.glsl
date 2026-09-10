precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D CoeffBuffer;
uniform float displayGain;
uniform ivec2 ltmGridSize;
out vec4 Output;

/*
 * IRIS_26618_GUIDED_BASE_DETAIL_LTM_GAIN
 *
 * Reconstruct the low-frequency guided log-luminance base from smoothed (a,b)
 * coefficients, then allocate only the already-requested 26614 presentation lift.
 * Dark broad regions retain the full global target; broad regions that would be
 * driven near display white receive a bounded pre-tone attenuation.  Because the
 * scalar depends on the guided base rather than the local detail residual, the
 * original log-luminance detail is recombined unchanged.
 */
const vec3 IRIS_LUMA = vec3(0.22897456, 0.69173852, 0.07928691);
const float IRIS_OUTPUT_EXPOSURE_SCALE = 0.80;

float irisLogLuma(vec2 uv) {
    vec3 rgb = max(texture(InputBuffer, clamp(uv, vec2(0.0), vec2(1.0))).rgb, vec3(0.0));
    return log2(max(dot(rgb, IRIS_LUMA), 0.000244140625));
}

void main() {
    vec2 gridSize = vec2(max(ltmGridSize, ivec2(1)));
    vec2 uv = gl_FragCoord.xy / gridSize;
    ivec2 coeffSize = textureSize(CoeffBuffer, 0);
    vec2 coeffStep = 1.0 / vec2(max(coeffSize, ivec2(1)));

    vec2 meanAb = vec2(0.0);
    for (int j = -1; j <= 1; ++j) {
        for (int i = -1; i <= 1; ++i) {
            meanAb += texture(CoeffBuffer,
                    clamp(uv + vec2(float(i), float(j)) * coeffStep,
                          vec2(0.0), vec2(1.0))).rg;
        }
    }
    meanAb *= 1.0 / 9.0;

    float logY = irisLogLuma(uv);
    float guidedBaseLog = meanAb.x * logY + meanAb.y;
    float guidedBase = exp2(guidedBaseLog);

    float requestedFinalGain = max(displayGain * IRIS_OUTPUT_EXPOSURE_SCALE, 1.0e-6);
    float requestedEv = max(log2(requestedFinalGain), 0.0);
    float projectedBase = guidedBase * requestedFinalGain;

    /* Universal, non-semantic allocation.  The operator is deliberately inactive
     * for small/no presentation lifts, then smoothly reserves up to half of the
     * requested EV in broad regions whose projected base approaches nominal white. */
    float requestPressure = smoothstep(0.35, 1.50, requestedEv);
    float brightBasePressure = smoothstep(0.42, 0.95, projectedBase);
    float protectEv = min(1.0, 0.50 * requestedEv)
            * requestPressure * brightBasePressure;
    float gain = exp2(-protectEv);

    /* Bound the scalar so this stage cannot become a replacement global tone curve. */
    gain = clamp(gain, 0.50, 1.0);
    Output = vec4(gain, guidedBaseLog, requestedEv, 1.0);
}
