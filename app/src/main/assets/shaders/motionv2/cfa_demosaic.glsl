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

/*
 * IRIS_26460_CROSS_PHASE_PLATEAU_CHROMA
 *
 * The remaining magenta/cyan dot pattern is not limited to clipped highlights.
 * Offline reconstruction from the clean timestamp-owned DNG reproduced a
 * strong false-magenta trophy pixel at only ~11% of the sensor clip level.
 *
 * The old interpolation asks whether nearby samples of ONE target color agree
 * with one another. Two same-CFA-phase samples can agree while both are wrong:
 * a sub-pixel luminance edge can land on the target-color row/column and be
 * misread as chroma.
 *
 * New authority test:
 *   1. gather only physically measured sites of the requested R/B color;
 *   2. reject those sites as chroma references when their four adjacent
 *      measured GREEN photosites prove that the site lies directly on a steep
 *      luminance transition;
 *   3. estimate a local white-balanced target/green ratio from the remaining
 *      locally homogeneous ("plateau") evidence;
 *   4. only on a strong green/luma edge, and only when the normal demosaic
 *      ratio is a large outlier from that coherent plateau evidence, pull the
 *      target chroma toward the plateau ratio.
 *
 * Green/luma geometry is never filtered or replaced. This is not a generic
 * chroma blur, not highlight neutralization, not 26453 post-denoise, not the
 * 26454 measured-site same-phase consensus, and not the rejected direct-RGB
 * merge path.
 */
float plateauChromaRatio(
        ivec2 p,
        int targetColor,
        float greenCenter,
        out float support,
        out float ratioSpread) {
    float targetGain = gainForColor(targetColor);
    float greenGain = gainForColor(1);

    float sumRatio = 0.0;
    float sumRatioSq = 0.0;
    float sumW = 0.0;

    for (int oy = -2; oy <= 2; oy++) {
        for (int ox = -2; ox <= 2; ox++) {
            ivec2 q = safeFullPoint(p + ivec2(ox, oy));
            if (cfaColor(q) != targetColor) continue;

            float targetRaw = rawAt(q);
            float targetTrust = rawReliability(targetRaw);
            if (targetTrust <= 0.002) continue;

            float greenQ = greenAt(q);
            float greenTrust = rawReliability(greenQ);

            /*
             * At a physical R/B photosite, all four cardinal +/-1 neighbors are
             * physical GREEN photosites in a 2x2 Bayer mosaic. Their range is
             * therefore direct cross-phase evidence, not interpolated RGB.
             */
            float gl = rawAt(q + ivec2(-1, 0));
            float gr = rawAt(q + ivec2( 1, 0));
            float gu = rawAt(q + ivec2( 0,-1));
            float gd = rawAt(q + ivec2( 0, 1));
            float greenMin = min(min(gl, gr), min(gu, gd));
            float greenMax = max(max(gl, gr), max(gu, gd));
            float greenRangeBalanced =
                    (greenMax - greenMin) * greenGain;

            float greenBalanced = max(greenQ * greenGain, 0.0);
            float edgeScale =
                    0.025
                    + 0.18 * sqrt(greenBalanced)
                    + 0.015 * greenBalanced;

            /*
             * A target-color sample sitting directly on a steep luma edge is
             * poor chroma authority because CFA phase and scene position are
             * inseparable there. Plateau samples retain full authority.
             */
            float plateauTrust =
                    1.0 - smoothstep(
                            0.35,
                            1.25,
                            greenRangeBalanced
                                    / max(edgeScale, 1.0e-6));
            if (plateauTrust <= 0.001) continue;

            float targetBalanced =
                    max(targetRaw * targetGain, 0.0);
            float ratio =
                    clamp(
                            targetBalanced
                                    / max(greenBalanced, 0.008),
                            0.05,
                            4.0);

            float r2 = float(ox * ox + oy * oy);
            float spatial =
                    1.0 / (1.0 + 0.35 * r2);

            /*
             * Prefer plateau evidence on the same luma side of the edge as the
             * current physical green sample. This avoids borrowing a bright
             * object's color into a dark neighbor or vice versa.
             */
            float greenDelta =
                    abs(
                            greenBalanced
                                    - greenCenter * greenGain);
            float rangeWeight =
                    1.0 / (0.040 + greenDelta);

            float w =
                    spatial
                    * targetTrust
                    * mix(0.20, 1.0, greenTrust)
                    * plateauTrust
                    * rangeWeight;

            sumRatio += w * ratio;
            sumRatioSq += w * ratio * ratio;
            sumW += w;
        }
    }

    support = sumW;
    if (sumW <= 1.0e-6) {
        ratioSpread = 1.0;
        return 1.0;
    }

    float meanRatio = sumRatio / sumW;
    float variance =
            max(
                    sumRatioSq / sumW
                            - meanRatio * meanRatio,
                    0.0);
    ratioSpread = sqrt(variance);
    return meanRatio;
}

float crossPhaseSafeColor(
        ivec2 p,
        int targetColor,
        float greenCenter,
        float baseColor) {
    float greenGain = gainForColor(1);
    float targetGain = gainForColor(targetColor);
    float centerBalanced =
            max(greenCenter * greenGain, 0.0);

    /*
     * Detect only a genuine high-frequency green/luma transition. This leaves
     * flat walls, broad colors, fabric, foliage interiors and normal low-light
     * chroma on the existing 26452/26453 path.
     */
    float gl = greenAt(p + ivec2(-1, 0)) * greenGain;
    float gr = greenAt(p + ivec2( 1, 0)) * greenGain;
    float gu = greenAt(p + ivec2( 0,-1)) * greenGain;
    float gd = greenAt(p + ivec2( 0, 1)) * greenGain;
    float greenMin =
            min(centerBalanced, min(min(gl, gr), min(gu, gd)));
    float greenMax =
            max(centerBalanced, max(max(gl, gr), max(gu, gd)));
    float greenRange = greenMax - greenMin;

    float edgeScale =
            0.025
            + 0.18 * sqrt(centerBalanced)
            + 0.015 * centerBalanced;
    float edgeEvidence =
            smoothstep(
                    0.45,
                    1.35,
                    greenRange / max(edgeScale, 1.0e-6));

    if (edgeEvidence <= 0.0) {
        return baseColor;
    }

    float plateauSupport;
    float plateauSpread;
    float plateauRatio =
            plateauChromaRatio(
                    p,
                    targetColor,
                    greenCenter,
                    plateauSupport,
                    plateauSpread);

    float supportConfidence =
            smoothstep(0.18, 0.80, plateauSupport);
    float consensusConfidence =
            1.0 - smoothstep(
                    0.28,
                    0.85,
                    plateauSpread);

    float baseRatio =
            max(baseColor * targetGain, 0.0)
                    / max(centerBalanced, 0.008);
    float ratioMismatch =
            abs(baseRatio - plateauRatio);

    /*
     * Small ratio differences are ordinary demosaic/color detail and remain
     * untouched. The correction begins only when the normal result becomes a
     * large cross-phase outlier on a proven luma edge.
     */
    float mismatchEvidence =
            smoothstep(
                    0.22,
                    0.80,
                    ratioMismatch);

    float correction = clamp(
            edgeEvidence
                    * supportConfidence
                    * consensusConfidence
                    * mismatchEvidence,
            0.0,
            0.88);

    float safeRatio =
            mix(
                    baseRatio,
                    plateauRatio,
                    correction);

    return max(
            safeRatio
                    * centerBalanced
                    / targetGain,
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

    /*
     * Preserve the proven 26452/26453 reconstruction as the base estimate.
     * The 26460 cross-phase gate may alter only R/B chroma authority at a
     * proven high-frequency green/luma edge. Green itself is untouched.
     */
    float redBase = reconstructColor(p, 0, green);
    float blueBase = reconstructColor(p, 2, green);

    float red =
            crossPhaseSafeColor(
                    p,
                    0,
                    green,
                    redBase);
    float blue =
            crossPhaseSafeColor(
                    p,
                    2,
                    green,
                    blueBase);

    /*
     * No upper clamp. Canonical highlight headroom is retained for the
     * dedicated MotionV2ColorTransform + MotionV2Render stages.
     */
    Output = max(vec3(red, green, blue), vec3(0.0));
}