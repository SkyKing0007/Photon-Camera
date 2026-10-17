#version 300 es
precision highp float;
precision highp int;
// IRIS_26845_SHADOW_LONG_LOW_FREQUENCY_LUMA_AUTHORITY
uniform sampler2D uNormalMean;
uniform sampler2D uLongLumaAccumulator;
uniform ivec2 uOutputSize;
uniform float uLongFrameCount;
layout(location = 0) out vec2 oGainTrust;
float luma26845(vec3 v) { return dot(v, vec3(0.25, 0.50, 0.25)); }
float normalY26845(ivec2 p) {
    return max(luma26845(texelFetch(uNormalMean, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rgb), 0.0);
}
vec2 longYS26845(ivec2 p) {
    return max(texelFetch(uLongLumaAccumulator, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rg, vec2(0.0));
}
float tentW26845(int d) { return d == 0 ? 2.0 : 1.0; }
void main() {
    ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uOutputSize - ivec2(1));
    float normalSum = 0.0;
    float longWeightedSum = 0.0;
    float supportWeightedSum = 0.0;
    float wsum = 0.0;
    float minNormal = 1.0e20;
    float maxNormal = 0.0;
    float normalCenter = normalY26845(p);
    vec2 longCenterAccum = longYS26845(p);
    float longCenter = longCenterAccum.g > 1.0e-7 ? longCenterAccum.r / longCenterAccum.g : 0.0;
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            float w = tentW26845(x) * tentW26845(y);
            ivec2 q = p + ivec2(x, y);
            float ny = normalY26845(q);
            vec2 ls = longYS26845(q);
            normalSum += ny * w;
            longWeightedSum += ls.r * w;
            supportWeightedSum += ls.g * w;
            wsum += w;
            minNormal = min(minNormal, ny);
            maxNormal = max(maxNormal, ny);
        }
    }
    float normalLow = normalSum / max(wsum, 1.0e-7);
    float supportLow = supportWeightedSum / max(wsum, 1.0e-7);
    float longLow = supportWeightedSum > 1.0e-7 ? longWeightedSum / supportWeightedSum : 0.0;
    float meanSupport = supportLow / max(uLongFrameCount, 1.0);
    float supportGate = smoothstep(0.08, 0.55, meanSupport);
    float shadowGate = 1.0 - smoothstep(0.20, 0.46, normalLow);
    float localRange = maxNormal - minNormal;
    /* Dark shot noise naturally increases relative range.  The 0.06 floor prevents that
     * random range from being misclassified as texture while still rejecting real edges. */
    float relativeRange = localRange / max(normalLow, 0.060);
    float flatGate = 1.0 - smoothstep(0.20, 0.46, relativeRange);
    float consistency = min(normalLow + 0.006, longLow + 0.006) /
        max(normalLow + 0.006, longLow + 0.006);
    float consistencyGate = smoothstep(0.70, 0.91, consistency);
    float trust = clamp(supportGate * shadowGate * flatGate * consistencyGate, 0.0, 1.0);

    /* Real sub-neighborhood detail should appear with the same sign in both exposures after
     * radiometric normalization.  Protect that coherent detail even inside dark regions;
     * uncorrelated NORMAL-only residual is the noise-like component eligible for cleanup. */
    float longToNormal = longLow > 0.006 ? normalLow / longLow : 1.0;
    float normalHigh = normalCenter - normalLow;
    float longHigh = longCenter * longToNormal - normalLow;
    float highMax = max(abs(normalHigh), abs(longHigh));
    float highMin = min(abs(normalHigh), abs(longHigh));
    float signAgreement = step(0.0, normalHigh * longHigh);
    float amplitudeAgreement = highMax > 0.002 ? highMin / highMax : 0.0;
    float relativeDetail = highMax / max(normalLow, 0.060);
    float coherentDetail = signAgreement * smoothstep(0.45, 0.82, amplitudeAgreement) *
        smoothstep(0.055, 0.14, relativeDetail);
    float cleanupTrust = trust * (1.0 - coherentDetail);

    /* LONG is allowed to set the smooth shadow luminance ratio strongly when every safety
     * gate agrees.  Ratio remains bounded so stale/misaligned LONG can never dominate. */
    float desiredRatio = normalLow > 0.006 ? longLow / normalLow : 1.0;
    float adaptiveLong = 0.88 * trust;
    float gain = mix(1.0, clamp(desiredRatio, 0.78, 1.42), adaptiveLong);
    oGainTrust = vec2(gain, cleanupTrust);
}
