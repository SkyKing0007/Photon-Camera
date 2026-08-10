precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
out vec3 Output;

#ifndef CFAPATTERN
#define CFAPATTERN 0
#endif

/*
 * IRIS_26415_V2_PACKED_CFA_DOMAIN
 * IRIS_26422_SENSOR_NEUTRAL_HIGHLIGHT_DEMOSAIC
 *
 * InputBuffer stores one physical 2x2 Bayer block in each RGBA texel.
 *
 * Critical 26422 rule:
 * Demosaic is still in camera RGB, before white balance. Therefore equal RAW
 * R/G/B values are NOT a neutral color. Chroma differences are reconstructed
 * in the white-balanced domain and converted back to camera RGB. When clipped
 * samples cease to be trustworthy, the fallback is the sensor-neutral RAW
 * ratio implied by the actual HAL gains rather than R=G=B.
 */

ivec2 fullSize() {
    return textureSize(InputBuffer, 0) * 2;
}

ivec2 safeFullPoint(ivec2 p) {
    return clamp(p, ivec2(0), fullSize() - ivec2(1));
}

float rawAt(ivec2 p) {
    ivec2 s = safeFullPoint(p);
    ivec2 q = s >> 1;
    vec4 packed = texelFetch(InputBuffer, q, 0);
    int component = ((s.y & 1) << 1) | (s.x & 1);
    if (component == 0) return packed.r;
    if (component == 1) return packed.g;
    if (component == 2) return packed.b;
    return packed.a;
}

int cfaColor(ivec2 p) {
    ivec2 s = safeFullPoint(p);
    int index = ((s.y & 1) << 1) | (s.x & 1);
#if CFAPATTERN == 0
    if (index == 0) return 0;
    if (index == 3) return 2;
    return 1;
#elif CFAPATTERN == 1
    if (index == 1) return 0;
    if (index == 2) return 2;
    return 1;
#elif CFAPATTERN == 2
    if (index == 2) return 0;
    if (index == 1) return 2;
    return 1;
#else
    if (index == 3) return 0;
    if (index == 0) return 2;
    return 1;
#endif
}

float clipLevel() {
    return max(sensorClipLevel, 1.0e-6);
}

float rawReliability(float rawValue) {
    /*
     * CFA values above ~94% of physical sensor white stop being reliable
     * chromatic measurements. Keep a smooth transition to avoid a contour.
     */
    float relative = rawValue / clipLevel();
    return 1.0 - smoothstep(0.940, 0.992, relative);
}

float greenAt(ivec2 p) {
    p = safeFullPoint(p);
    if (cfaColor(p) == 1) return rawAt(p);

    float l = rawAt(p + ivec2(-1, 0));
    float r = rawAt(p + ivec2( 1, 0));
    float u = rawAt(p + ivec2( 0,-1));
    float d = rawAt(p + ivec2( 0, 1));

    float ll = rawAt(p + ivec2(-2, 0));
    float rr = rawAt(p + ivec2( 2, 0));
    float uu = rawAt(p + ivec2( 0,-2));
    float dd = rawAt(p + ivec2( 0, 2));
    float center = rawAt(p);

    float gradientH =
            abs(l - r)
                    + 0.5 * abs(ll - 2.0 * center + rr);
    float gradientV =
            abs(u - d)
                    + 0.5 * abs(uu - 2.0 * center + dd);

    float horizontal = 0.5 * (l + r);
    float vertical = 0.5 * (u + d);

    float reliabilityH =
            sqrt(max(rawReliability(l) * rawReliability(r), 0.0));
    float reliabilityV =
            sqrt(max(rawReliability(u) * rawReliability(d), 0.0));

    float wh = reliabilityH / (gradientH + 1.0e-5);
    float wv = reliabilityV / (gradientV + 1.0e-5);
    float sumW = wh + wv;

    if (sumW <= 1.0e-6) {
        /*
         * Luma itself is clipped. Preserve the measured local ceiling; do not
         * invent colored geometry here.
         */
        return max(max(l, r), max(u, d));
    }
    return (horizontal * wh + vertical * wv) / sumW;
}

float gainForColor(int color) {
    if (color == 0) return max(sensorGains.r, 1.0e-6);
    if (color == 2) return max(sensorGains.b, 1.0e-6);
    return max(sensorGains.g, 1.0e-6);
}

float sensorNeutralFromGreen(float greenRaw, int targetColor) {
    float greenGain = gainForColor(1);
    float targetGain = gainForColor(targetColor);
    return greenRaw * greenGain / targetGain;
}

float reconstructColor(
        ivec2 p,
        int targetColor,
        float greenCenter) {
    p = safeFullPoint(p);

    float measured = rawAt(p);
    if (cfaColor(p) == targetColor
            && rawReliability(measured) > 0.35) {
        return measured;
    }

    float targetGain = gainForColor(targetColor);
    float greenGain = gainForColor(1);

    float sum = 0.0;
    float weightSum = 0.0;
    float sumSq = 0.0;
    float localGradient = 0.0;
    float reliableEvidence = 0.0;

    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            if (x == 0 && y == 0) continue;

            ivec2 q = safeFullPoint(p + ivec2(x, y));
            if (cfaColor(q) != targetColor) continue;

            float rawQ = rawAt(q);
            float targetReliability = rawReliability(rawQ);
            if (targetReliability <= 0.002) continue;

            float greenQ = greenAt(q);
            float greenReliability = rawReliability(greenQ);

            float targetBalanced = rawQ * targetGain;
            float greenBalanced = greenQ * greenGain;
            float differenceBalanced = targetBalanced - greenBalanced;
            float greenDelta =
                    abs(greenBalanced - greenCenter * greenGain);

            float spatial =
                    (abs(x) + abs(y) == 2)
                            ? 0.70710678
                            : 1.0;

            float saturationTrust =
                    targetReliability
                    * mix(0.12, 1.0, greenReliability);

            float weight =
                    spatial
                    * saturationTrust
                    / (0.006 + greenDelta);

            sum += differenceBalanced * weight;
            sumSq += differenceBalanced
                    * differenceBalanced
                    * weight;
            weightSum += weight;
            reliableEvidence += saturationTrust;
            localGradient = max(localGradient, greenDelta);
        }
    }

    float neutralRaw =
            sensorNeutralFromGreen(greenCenter, targetColor);

    if (weightSum <= 1.0e-6 || reliableEvidence < 0.05) {
        return neutralRaw;
    }

    float meanDifference = sum / weightSum;
    float variance =
            max(
                    sumSq / weightSum
                            - meanDifference * meanDifference,
                    0.0);
    float disagreement = sqrt(variance);

    float chromaConfidence =
            1.0 - smoothstep(
                    0.020 + 0.18 * localGradient,
                    0.085 + 0.55 * localGradient,
                    disagreement);

    /*
     * As green approaches sensor white, chroma evidence becomes increasingly
     * underdetermined even when a neighboring R/B sample has not clipped yet.
     * Fade only the interpolated color difference, never the structural green.
     */
    float highlightChromaTrust =
            1.0 - smoothstep(
                    0.900,
                    0.992,
                    greenCenter / clipLevel());

    chromaConfidence *=
            mix(0.10, 1.0, highlightChromaTrust);
    chromaConfidence = clamp(chromaConfidence, 0.0, 1.0);

    float balancedNeutral = greenCenter * greenGain;
    float reconstructedBalanced =
            balancedNeutral
                    + meanDifference * chromaConfidence;

    return max(
            reconstructedBalanced / targetGain,
            0.0);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 size = fullSize();
    if (any(greaterThanEqual(p, size))) {
        Output = vec3(0.0);
        return;
    }

    float green = greenAt(p);
    float red = reconstructColor(p, 0, green);
    float blue = reconstructColor(p, 2, green);

    /*
     * No upper clamp. Canonical highlight headroom is retained for the
     * dedicated MotionV2ColorTransform + MotionV2Render stages.
     */
    Output = max(vec3(red, green, blue), vec3(0.0));
}