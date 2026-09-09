precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform float exposureEv;
uniform float shadowsControl;
uniform float contrastControl;
out vec4 Output;

float irisLuma(vec3 c) {
    return dot(max(c, vec3(0.0)), vec3(0.22897456, 0.69173852, 0.07928691));
}

vec3 scaleToLuma(vec3 rgb, float sourceY, float targetY) {
    if (sourceY <= 1.0e-7) return vec3(max(targetY, 0.0));
    return max(rgb, vec3(0.0)) * (max(targetY, 0.0) / sourceY);
}

vec3 applyShadows(vec3 rgb, float amount) {
    if (abs(amount) < 0.0001) return rgb;
    float y = irisLuma(rgb);
    float mask = 1.0 - smoothstep(0.08, 0.55, y);
    float targetY = y;
    if (amount < 0.0) {
        // User convention: negative opens shadows. Maximum lift is deliberately bounded.
        targetY = y + (-amount) * 0.08 * mask * (1.0 - clamp(y, 0.0, 1.0));
    } else {
        // Positive deepens shadows while leaving mid/high tones progressively untouched.
        targetY = y * (1.0 - 0.75 * amount * mask);
    }
    return scaleToLuma(rgb, y, targetY);
}

vec3 applyContrast(vec3 rgb, float amount) {
    if (abs(amount) < 0.0001) return rgb;
    float y = irisLuma(rgb);
    if (y <= 1.0e-7) return rgb;
    const float pivot = 0.18;
    float slope = 1.0 + 0.25 * amount;
    float targetY = pivot * exp2(log2(max(y / pivot, 1.0e-6)) * slope);
    return scaleToLuma(rgb, y, targetY);
}

void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec4 source = texelFetch(InputBuffer, xy, 0);
    vec3 rgb = max(source.rgb, vec3(0.0));
    /* IRIS_26615_MANUAL_POST_SPATIAL_PRESENTATION
     * Automatic viewfinder brightness has already been allocated by the single spatial appearance
     * owner. Manual controls operate directly on that canonical appearance and never recreate the
     * old global target multiplier. Alpha is immutable physical HDR provenance for UHDR.
     */
    rgb *= exp2(exposureEv);
    rgb = applyShadows(rgb, shadowsControl);
    rgb = applyContrast(rgb, contrastControl);
    Output = vec4(max(rgb, vec3(0.0)), source.a);
}
