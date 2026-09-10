precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform ivec2 ltmGridSize;
out vec4 Output;

/*
 * IRIS_26619_GUIDED_BASE_DETAIL_LTM_COEFFICIENTS
 *
 * Self-guided filter coefficients in log2 final-tone guide.  The guide is the exact
 * max(luma,maxRGB) scalar consumed by MotionV2Render, so the spatial decomposition
 * cannot disagree with final highlight ownership.  No RGB component is mixed with
 * a neighbour and no chroma quantity is modified.  A 7x7 support on the deliberately low-resolution
 * coefficient grid captures broad illumination while the guided variance term
 * keeps material/geometry edges out of that broad base.
 */
const vec3 IRIS_LUMA = vec3(0.22897456, 0.69173852, 0.07928691);
const float IRIS_GUIDED_EPSILON_STOPS2 = 0.0625; // (0.25 stop)^2

float irisLogGuide(vec2 uv) {
    vec3 rgb = max(texture(InputBuffer, clamp(uv, vec2(0.0), vec2(1.0))).rgb, vec3(0.0));
    float y = max(dot(rgb, IRIS_LUMA), 0.0);
    float peak = max(rgb.r, max(rgb.g, rgb.b));
    return log2(max(max(y, peak), 0.000244140625)); // 2^-12
}

void main() {
    vec2 gridSize = vec2(max(ltmGridSize, ivec2(1)));
    vec2 uv = gl_FragCoord.xy / gridSize;
    vec2 stepUv = 1.0 / gridSize;

    float sum = 0.0;
    float sum2 = 0.0;
    for (int j = -3; j <= 3; ++j) {
        for (int i = -3; i <= 3; ++i) {
            float v = irisLogGuide(uv + vec2(float(i), float(j)) * stepUv);
            sum += v;
            sum2 += v * v;
        }
    }
    const float invN = 1.0 / 49.0;
    float mean = sum * invN;
    float variance = max(sum2 * invN - mean * mean, 0.0);
    float a = variance / (variance + IRIS_GUIDED_EPSILON_STOPS2);
    float b = mean * (1.0 - a);
    Output = vec4(a, b, 0.0, 1.0);
}
