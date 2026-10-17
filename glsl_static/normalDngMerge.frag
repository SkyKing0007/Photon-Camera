#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
uniform highp usampler2D uRaw;
uniform sampler2D uFlow;
uniform sampler2D uCovariance;
uniform sampler2D uRejection;
uniform vec4 uFlowScaleOffset;
uniform ivec2 uRawSize;
uniform vec4 uFrameBorderPadded;
uniform int uCfaPattern;
uniform int uUseFrameWeight;
uniform vec4 uPhaseGains;
uniform vec4 uPhaseBlackTerms;
/* IRIS_26782_DNG_SOURCE_HEADROOM_OWNER
 * Physical sensor white expressed in this frame's black-subtracted normalized domain.
 * For NORMAL exposure normalization this equals the frame exposure scale; using it keeps
 * source clipping detection independent of exposure normalization. */
uniform float uSourceWhiteNormalized;
/* IRIS_26786_DNG_COMBINED_AB_OPTIONS */
uniform int uDngLcaEnabled26786;
uniform vec2 uDngLcaKrKb26786;
uniform int uDngQuadHeadroom26786;
uniform int uDngEdgeDeAlias26786;
uniform vec4 uCovRangeRg;
uniform vec2 uCovRangeB;
layout(location = 0) out vec2 oSignalAndWeight;

vec2 mirrorUvs(vec2 sampleUv) {
    if (sampleUv.x <= uFrameBorderPadded.x) sampleUv.x = 2.0 * uFrameBorderPadded.x - sampleUv.x;
    if (sampleUv.y <= uFrameBorderPadded.y) sampleUv.y = 2.0 * uFrameBorderPadded.y - sampleUv.y;
    if (sampleUv.x > uFrameBorderPadded.z) sampleUv.x = 2.0 * uFrameBorderPadded.z - sampleUv.x;
    if (sampleUv.y > uFrameBorderPadded.w) sampleUv.y = 2.0 * uFrameBorderPadded.w - sampleUv.y;
    return sampleUv;
}

int phaseAt(ivec2 p) {
    return ((p.y & 1) << 1) + (p.x & 1);
}

ivec2 phaseOffset(int phaseIndex) {
    return ivec2(phaseIndex & 1, (phaseIndex >> 1) & 1);
}

ivec2 clampPhaseLattice(ivec2 q, int phaseIndex) {
    ivec2 offset = phaseOffset(phaseIndex);
    ivec2 maximum = max((uRawSize - ivec2(1) - offset) / 2, ivec2(0));
    return clamp(q, ivec2(0), maximum);
}

ivec2 pixelForPhaseLattice(ivec2 q, int phaseIndex) {
    return clampPhaseLattice(q, phaseIndex) * 2 + phaseOffset(phaseIndex);
}

float normalizedRaw(ivec2 p) {
    p = clamp(p, ivec2(0), uRawSize - ivec2(1));
    int phaseIndex = phaseAt(p);
    return float(texelFetch(uRaw, p, 0).r) * uPhaseGains[phaseIndex] + uPhaseBlackTerms[phaseIndex];
}

float kernelWeight(vec2 pixelOffset, vec3 covariance) {
    float kernelDistance =
        pixelOffset.x * pixelOffset.x * covariance.x +
        pixelOffset.y * pixelOffset.y * covariance.y +
        pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
    return exp2(-0.5 * kernelDistance) + 0.00005;
}

vec3 unpackCovariance(vec3 packed) {
    return vec3(
        packed.x * uCovRangeRg.y + uCovRangeRg.x,
        packed.y * uCovRangeRg.w + uCovRangeRg.z,
        packed.z * uCovRangeB.y + uCovRangeB.x
    );
}

/* IRIS_26785_PHASE_SCOPED_HIGHLIGHT_VALIDITY_OWNER
 * Preserve 26782 shared Bayer-quad geometry exactly: R/G1/G2/B keep independent same-phase
 * 2-pixel lattices while one quad flow/covariance/rejection owner remains shared by all four.
 * Radiometric saturation validity is phase-scoped: a valid reference phase remains exact
 * identity, but a clipped/near-clipped reference phase is censored so aligned valid samples
 * of that SAME CFA phase may dominate it. Alternate source headroom is likewise evaluated
 * only for the target phase (and, for fractional interpolation, every same-phase sample in
 * the consumed 2x2 lattice footprint). The 26782 hard-edge/material veto remains unchanged.
 * A tiny deterministic reference fallback prevents holes if no alternate phase measurement
 * survives; it cannot dominate any normally weighted valid alternate. No G1/G2 pooling,
 * cross-phase hue synthesis, WB, demosaic, tone, or JPEG/VGN ownership is introduced. */
float quadGuide(ivec2 quadIndex) {
    ivec2 q = max(quadIndex, ivec2(0));
    ivec2 origin = q * 2;
    ivec2 maxOrigin = max(uRawSize - ivec2(2), ivec2(0));
    origin = clamp(origin, ivec2(0), maxOrigin);
    return 0.25 * (
        normalizedRaw(origin) +
        normalizedRaw(origin + ivec2(1, 0)) +
        normalizedRaw(origin + ivec2(0, 1)) +
        normalizedRaw(origin + ivec2(1, 1))
    );
}

float phaseHeadroomConfidence(ivec2 quadIndex, int phaseIndex) {
    ivec2 p = pixelForPhaseLattice(quadIndex, phaseIndex);
    float value = normalizedRaw(p);
    float whitePoint = max(uSourceWhiteNormalized, 1.0e-5);
    float headroomStart = whitePoint * 0.9925;
    return 1.0 - smoothstep(
        headroomStart, max(headroomStart + 1.0e-5, whitePoint), value);
}

float quadHeadroomConfidence(ivec2 quadIndex) {
    float confidence = 1.0;
    for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
        confidence = min(confidence, phaseHeadroomConfidence(quadIndex, phaseIndex));
    }
    return confidence;
}

int redPhase26786() { return uCfaPattern; }
int bluePhase26786() { return 3 - uCfaPattern; }
float phaseLcaK26786(int phaseIndex) {
    if (phaseIndex == redPhase26786()) return uDngLcaKrKb26786.x;
    if (phaseIndex == bluePhase26786()) return uDngLcaKrKb26786.y;
    return 0.0;
}
float selectedHeadroom26786(ivec2 q, int phaseIndex) {
    return uDngQuadHeadroom26786 != 0
        ? quadHeadroomConfidence(q) : phaseHeadroomConfidence(q, phaseIndex);
}

void main() {
    ivec2 outputPixel = ivec2(gl_FragCoord.xy);
    int targetPhase = phaseAt(outputPixel);

    /* IRIS_26786_LCA_REFERENCE_COMPATIBILITY
     * OFF is byte-equation-identical to 26785. With LCA ON, green still keeps exact
     * reference identity (k=0), while R/B continue through the same-phase kernel below so
     * the reference observation receives the same radial correction as every alternate. */
    if (uUseFrameWeight == 0 &&
            (uDngLcaEnabled26786 == 0 || abs(phaseLcaK26786(targetPhase)) < 1.0e-12)) {
        ivec2 referenceQuad = outputPixel / 2;
        float referenceHeadroom = selectedHeadroom26786(referenceQuad, targetPhase);
        /* IRIS_26785_CENSORED_REFERENCE_PHASE */
        const float referenceFallbackWeight26785 = 0.00005;
        float referenceWeight = max(referenceHeadroom, referenceFallbackWeight26785);
        oSignalAndWeight = vec2(
            normalizedRaw(outputPixel) * referenceWeight,
            referenceWeight);
        return;
    }

    ivec2 quadOrigin = (outputPixel / 2) * 2;
    vec2 rawSize = vec2(uRawSize);
    vec2 quadReferenceUv = (vec2(quadOrigin) + vec2(1.0)) / rawSize;
    vec2 sampleReferenceUv26786 = quadReferenceUv;
    vec2 targetOutputCenter26786 = vec2(outputPixel) + vec2(0.5);
    if (uDngLcaEnabled26786 != 0) {
        vec2 opticalCenter26786 = 0.5 * rawSize;
        float k26786 = phaseLcaK26786(targetPhase);
        vec2 correctedQuadCenter26786 = opticalCenter26786 +
            ((vec2(quadOrigin) + vec2(1.0)) - opticalCenter26786) * (1.0 - k26786);
        sampleReferenceUv26786 = correctedQuadCenter26786 / rawSize;
        targetOutputCenter26786 = opticalCenter26786 +
            (targetOutputCenter26786 - opticalCenter26786) * (1.0 - k26786);
    }
    vec2 flowUv = sampleReferenceUv26786 * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
    vec2 flow = texture(uFlow, flowUv).xy;
    vec2 quadSourceUv = mirrorUvs(sampleReferenceUv26786 + flow);
    vec2 sharedTranslationPixels = (quadSourceUv - sampleReferenceUv26786) * rawSize;
    vec3 covariance = unpackCovariance(texture(uCovariance, quadSourceUv).xyz);

    vec2 sourcePixel = targetOutputCenter26786 + sharedTranslationPixels;
    ivec2 offset = phaseOffset(targetPhase);
    vec2 latticeCoordinate = 0.5 * (sourcePixel - (vec2(offset) + vec2(0.5)));
    ivec2 nearestLattice = ivec2(floor(latticeCoordinate + vec2(0.5)));
    vec2 nearestDelta = latticeCoordinate - vec2(nearestLattice);

    float intensity = 0.0;
    float accumulatedWeight = 0.0;
    float sourceHeadroomConfidence = 1.0;
    float fractionalHardEdgeWeight = 1.0;
    bool exactSamePhaseSample = max(abs(nearestDelta.x), abs(nearestDelta.y)) < 1.0e-5;
    if (exactSamePhaseSample) {
        ivec2 q = clampPhaseLattice(nearestLattice, targetPhase);
        ivec2 source = pixelForPhaseLattice(q, targetPhase);
        intensity = normalizedRaw(source);
        accumulatedWeight = 1.0;
        // Preserve exact whole-2px sampling; saturation validity belongs only to targetPhase.
        sourceHeadroomConfidence = selectedHeadroom26786(q, targetPhase);
    } else {
        ivec2 latticeBase = ivec2(floor(latticeCoordinate));
        float guideMin = 1.0e9;
        float guideMax = 0.0;
        float guides26786[4];
        float samples26786[4];
        float weights26786[4];
        float headrooms26786[4];
        for (int ly = 0; ly <= 1; ++ly) {
            for (int lx = 0; lx <= 1; ++lx) {
                int i26786 = ly * 2 + lx;
                ivec2 q = clampPhaseLattice(latticeBase + ivec2(lx, ly), targetPhase);
                ivec2 source = q * 2 + offset;
                vec2 sampleCenter = vec2(source) + vec2(0.5);
                float w = kernelWeight(sampleCenter - sourcePixel, covariance);
                float sampleValue = normalizedRaw(source);
                float guide = quadGuide(q);
                float hr = selectedHeadroom26786(q, targetPhase);
                guides26786[i26786] = guide;
                samples26786[i26786] = sampleValue;
                weights26786[i26786] = w;
                headrooms26786[i26786] = hr;
                intensity += sampleValue * w;
                accumulatedWeight += w;
                guideMin = min(guideMin, guide);
                guideMax = max(guideMax, guide);
                sourceHeadroomConfidence = min(sourceHeadroomConfidence, hr);
            }
        }
        /* IRIS_26782_FRACTIONAL_HARD_EDGE_VETO + IRIS_26786_ONE_SIDED_DEALIAS
         * OFF preserves 26785 exactly. ON keeps the same phase lattice but, on a hard edge,
         * chooses only the nearest row/column pair along the lower-guide-gradient direction.
         * The selected pair must itself be same-side coherent; otherwise the old veto wins. */
        float guideRange = max(guideMax - guideMin, 0.0);
        float relativeGuideRange = guideRange / max(guideMax, 0.03);
        bool hardEdge = guideMax > 0.08 && guideRange > 0.055 && relativeGuideRange > 0.20;
        if (!hardEdge) {
            fractionalHardEdgeWeight = 1.0;
        } else if (uUseFrameWeight == 0 && uDngLcaEnabled26786 != 0 &&
                abs(phaseLcaK26786(targetPhase)) >= 1.0e-12) {
            /* LCA is a calibrated subpixel coordinate correction of the reference itself,
             * not an alternate temporal observation. Do not let the 26782 alternate-frame
             * veto cancel the default-on radial R/B correction. */
            fractionalHardEdgeWeight = 1.0;
        } else if (uDngEdgeDeAlias26786 == 0) {
            fractionalHardEdgeWeight = 0.0;
        } else {
            float acrossX = abs(guides26786[1] - guides26786[0]) + abs(guides26786[3] - guides26786[2]);
            float acrossY = abs(guides26786[2] - guides26786[0]) + abs(guides26786[3] - guides26786[1]);
            int i0; int i1;
            vec2 frac26786 = latticeCoordinate - floor(latticeCoordinate);
            if (acrossX > acrossY) {
                bool right = frac26786.x >= 0.5;
                i0 = right ? 1 : 0; i1 = right ? 3 : 2;
            } else {
                bool bottom = frac26786.y >= 0.5;
                i0 = bottom ? 2 : 0; i1 = bottom ? 3 : 1;
            }
            float pairMax = max(guides26786[i0], guides26786[i1]);
            float pairRange = abs(guides26786[i0] - guides26786[i1]);
            bool sameSide = pairRange <= max(0.035, 0.12 * max(pairMax, 0.03));
            if (sameSide) {
                intensity = samples26786[i0] * weights26786[i0] + samples26786[i1] * weights26786[i1];
                accumulatedWeight = weights26786[i0] + weights26786[i1];
                sourceHeadroomConfidence = min(headrooms26786[i0], headrooms26786[i1]);
                fractionalHardEdgeWeight = 1.0;
            } else {
                fractionalHardEdgeWeight = 0.0;
            }
        }
    }

    vec2 invRawSize = 1.0 / rawSize;
    ivec2 maxPixel = uRawSize - ivec2(1);
    ivec2 p00 = clamp(quadOrigin, ivec2(0), maxPixel);
    ivec2 p10 = clamp(quadOrigin + ivec2(1, 0), ivec2(0), maxPixel);
    ivec2 p01 = clamp(quadOrigin + ivec2(0, 1), ivec2(0), maxPixel);
    ivec2 p11 = clamp(quadOrigin + ivec2(1, 1), ivec2(0), maxPixel);
    float w00 = texture(uRejection, (vec2(p00) + vec2(0.5)) * invRawSize).r;
    float w10 = texture(uRejection, (vec2(p10) + vec2(0.5)) * invRawSize).r;
    float w01 = texture(uRejection, (vec2(p01) + vec2(0.5)) * invRawSize).r;
    float w11 = texture(uRejection, (vec2(p11) + vec2(0.5)) * invRawSize).r;
    float frameWeight = min(min(w00, w10), min(w01, w11));
    /* IRIS_26785_TARGET_PHASE_DNG_HEADROOM
     * Shared geometry/rejection remains quad-owned, but saturation is a property of the
     * consumed target-phase measurement. Do not discard usable R/G1/G2/B evidence merely
     * because a different phase in the same source quad clipped. */
    float radiometricWeight26786 = clamp(sourceHeadroomConfidence, 0.0, 1.0);
    if (uUseFrameWeight == 0) {
        // Preserve 26785's deterministic censored-reference fallback for LCA-resampled R/B.
        radiometricWeight26786 = max(radiometricWeight26786, 0.00005);
    }
    frameWeight *= radiometricWeight26786;
    frameWeight *= fractionalHardEdgeWeight;
    float reconstructed = intensity / max(accumulatedWeight, 1.0e-8);
    oSignalAndWeight = vec2(reconstructed * frameWeight, frameWeight);
}
