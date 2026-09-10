precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D CoeffBuffer;
uniform ivec2 ltmGridSize;
out vec4 Output;

/*
 * IRIS_26619_GUIDED_BASE_DETAIL_LTM_BASE
 *
 * Reconstruct only the edge-aware broad log-guide base.  This pass deliberately
 * emits no exposure gain and modifies no image pixel.  MotionV2Render is the sole
 * consumer/appearance owner; the exact same base samples are exported to true-2x.
 */
const vec3 IRIS_LUMA = vec3(0.22897456, 0.69173852, 0.07928691);

float irisLogGuide(vec2 uv) {
    vec3 rgb = max(texture(InputBuffer, clamp(uv, vec2(0.0), vec2(1.0))).rgb, vec3(0.0));
    float y = max(dot(rgb, IRIS_LUMA), 0.0);
    float peak = max(rgb.r, max(rgb.g, rgb.b));
    return log2(max(max(y, peak), 0.000244140625));
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

    float logGuide = irisLogGuide(uv);
    float guidedBaseLog = meanAb.x * logGuide + meanAb.y;
    Output = vec4(guidedBaseLog, 0.0, 0.0, 1.0);
}
