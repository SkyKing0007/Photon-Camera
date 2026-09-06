precision highp float;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform float exposureEv;
uniform float shadowsControl;
uniform float contrastControl;
uniform float brightnessTargetGain;
out vec3 Output;

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
    vec3 rgb = max(texelFetch(InputBuffer, xy, 0).rgb, vec3(0.0));
    /* IRIS_26604_MANUAL_VIRTUAL_PRESENTATION_DOMAIN
     * Preserve 26603 manual Exposure/Shadows/Contrast semantics even though automatic displayGain
     * is no longer a texture multiplier. Evaluate manual masks in the same virtually presented
     * domain, then return to source domain for the one final tone owner.
     */
    float targetGain=max(brightnessTargetGain,1.0e-6);
    vec3 virtualRgb=rgb*targetGain;
    virtualRgb *= exp2(exposureEv);
    virtualRgb = applyShadows(virtualRgb, shadowsControl);
    virtualRgb = applyContrast(virtualRgb, contrastControl);
    Output = max(virtualRgb/targetGain, vec3(0.0));
}
