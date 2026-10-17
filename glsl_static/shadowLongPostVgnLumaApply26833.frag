#version 300 es
precision highp float;
precision highp int;
// IRIS_26845_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY
uniform sampler2D uPostVgnRgb;
uniform sampler2D uLongLumaGain;
layout(location = 0) out vec4 oColor;
float luma26845(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
float tentW26845(int d) { return d == 0 ? 2.0 : 1.0; }
void main() {
    ivec2 size = textureSize(uPostVgnRgb, 0);
    ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), size - ivec2(1));
    vec4 source = texelFetch(uPostVgnRgb, p, 0);
    vec2 gt = max(texelFetch(uLongLumaGain, p, 0).rg, vec2(0.0));
    float gain = gt.r;
    float trust = clamp(gt.g, 0.0, 1.0);

    float lowSum = 0.0;
    float wsum = 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            float w = tentW26845(x) * tentW26845(y);
            ivec2 q = clamp(p + ivec2(x, y), ivec2(0), size - ivec2(1));
            lowSum += max(luma26845(texelFetch(uPostVgnRgb, q, 0).rgb), 0.0) * w;
            wsum += w;
        }
    }
    float sourceY = max(luma26845(source.rgb), 0.0);
    float lowY = lowSum / max(wsum, 1.0e-7);
    /* Deep trusted flat shadows can suppress up to 78% of NORMAL-only residual luma
     * variation.  Coherent NORMAL/LONG detail was removed from trust upstream, so the
     * original NORMAL pixel remains the sole structure owner. */
    float cleanup = 0.78 * trust;
    float cleanedY = mix(sourceY, lowY, cleanup);
    float targetY = cleanedY * gain;
    float scale = sourceY > 1.0e-6 ? targetY / sourceY : gain;
    oColor = vec4(source.rgb * scale, source.a);
}
