#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;

uniform highp sampler2D normalCfa;
/* IRIS_26498_V13_REFERENCE_CFA_CORRESPONDENCE_AUTHORITY */
uniform highp sampler2D referenceCfa;
uniform highp sampler2D shortCfa;
uniform highp sampler2D flowTexture;
layout(rgba32f, binding = 0) uniform highp writeonly image2D outCfa;
layout(r32f, binding = 1) uniform highp writeonly image2D outProvenance;
layout(std430, binding = 2) buffer ShortDiagBuf {
    uint shortDiag[];
};
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float shortToNormalScale;
uniform float physicalClipThreshold;
uniform float shortClipThreshold;
uniform float minimumFlowConfidence;

const float PROVENANCE_NORMAL = 0.0;
const float PROVENANCE_CENSORED = 1.0;
const float PROVENANCE_SHORT_VALIDATED = 2.0;

const uint D_TOTAL_CLIPPED = 0u;
const uint D_SHORT_SAFE = 1u;
const uint D_SHORT_CLIPPED = 2u;
const uint D_FLOW_REJECT = 3u;
const uint D_CORR_REJECT = 4u;
const uint D_RADIOMETRY_REJECT = 5u;
const uint D_VALIDATED = 6u;
const uint D_STILL_CENSORED = 7u;
const uint D_BIN_LT50 = 8u;
const uint D_BIN_50_70 = 9u;
const uint D_BIN_70_85 = 10u;
const uint D_BIN_85_95 = 11u;
const uint D_BIN_95_CLIP = 12u;
const uint D_PHASE_TOTAL = 16u;
const uint D_PHASE_VALIDATED = 20u;
const uint D_PHASE_SHORT_CLIPPED = 24u;
const uint D_PHASE_FLOW_REJECT = 28u;
const uint D_PHASE_CORR_REJECT = 32u;
const uint D_PHASE_RADIOMETRY_REJECT = 36u;
const uint D_PHASE_STILL_CENSORED = 40u;

void addMask(uint totalIndex, uint phaseBase, vec4 mask) {
    for (int i = 0; i < 4; ++i) {
        if (mask[i] > 0.5) {
            atomicAdd(shortDiag[totalIndex], 1u);
            atomicAdd(shortDiag[phaseBase + uint(i)], 1u);
        }
    }
}
void addTotalOnly(uint index, vec4 mask) {
    for (int i = 0; i < 4; ++i) if (mask[i] > 0.5) atomicAdd(shortDiag[index], 1u);
}
void classifyShortSamples(vec4 shortCenter, vec4 clipMask) {
    for (int i = 0; i < 4; ++i) {
        if (clipMask[i] <= 0.5) continue;
        float v = shortCenter[i];
        if (v >= shortClipThreshold) continue;
        if (v < 0.50) atomicAdd(shortDiag[D_BIN_LT50], 1u);
        else if (v < 0.70) atomicAdd(shortDiag[D_BIN_50_70], 1u);
        else if (v < 0.85) atomicAdd(shortDiag[D_BIN_70_85], 1u);
        else if (v < 0.95) atomicAdd(shortDiag[D_BIN_85_95], 1u);
        else atomicAdd(shortDiag[D_BIN_95_CLIP], 1u);
    }
}

float sum4(vec4 v) { return dot(v, vec4(1.0)); }
float encodePhaseStates(vec4 s) { return dot(s, vec4(1.0, 3.0, 9.0, 27.0)); }

vec4 phaseSafeBilinear(vec2 packedCenter) {
    vec2 p = packedCenter - vec2(0.5);
    ivec2 lo = ivec2(floor(p));
    vec2 f = fract(p);
    ivec2 maxP = packedSize - ivec2(1);
    ivec2 p00 = clamp(lo, ivec2(0), maxP);
    ivec2 p10 = clamp(lo + ivec2(1,0), ivec2(0), maxP);
    ivec2 p01 = clamp(lo + ivec2(0,1), ivec2(0), maxP);
    ivec2 p11 = clamp(lo + ivec2(1,1), ivec2(0), maxP);
    vec4 a = texelFetch(shortCfa, p00, 0);
    vec4 b = texelFetch(shortCfa, p10, 0);
    vec4 c = texelFetch(shortCfa, p01, 0);
    vec4 d = texelFetch(shortCfa, p11, 0);
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
vec4 shortSafe(vec4 v) { return vec4(1.0) - step(vec4(shortClipThreshold), v); }
vec4 normalSafe(vec4 v) { return vec4(1.0) - step(vec4(0.90), v); }

/* IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT
 * mfsr_flow_expand.w means interpolation was cancelled and the whole base tile
 * vector was preserved. It does NOT mean the base vector is invalid. 26496
 * incorrectly converted that safe fallback into zero highlight evidence.
 *
 * For clipped sites, refine the predicted short-frame correspondence locally on
 * unsaturated physical CFA evidence. Structured regions require a unique best
 * match. Smooth regions may be accepted only with tighter radiometric agreement,
 * where a subpixel ambiguity cannot create an edge/color displacement.
 */
void evaluateCorrespondence(
        ivec2 p, vec2 source, out float meanRelativeError,
        out float structure, out float supportCount) {
    float errorSum = 0.0;
    supportCount = 0.0;
    float lumaMin = 1.0e20;
    float lumaMax = 0.0;
    float lumaSum = 0.0;
    float lumaCount = 0.0;
    ivec2 maxP = packedSize - ivec2(1);
    for (int oy = -2; oy <= 2; ++oy) {
        for (int ox = -2; ox <= 2; ++ox) {
            if (max(abs(ox), abs(oy)) != 2) continue;
            ivec2 q = p + ivec2(ox, oy);
            if (any(lessThan(q, ivec2(0))) || any(greaterThan(q, maxP))) continue;
            vec2 qs = source + vec2(float(ox), float(oy));
            if (qs.x < 0.0 || qs.y < 0.0 ||
                    qs.x >= float(packedSize.x) || qs.y >= float(packedSize.y)) continue;
            vec4 nSensor = texelFetch(referenceCfa, q, 0) /
                    max(referenceExposureScale, 1.0e-6);
            vec4 sRaw = phaseSafeBilinear(qs);
            vec4 mask = normalSafe(nSensor) * shortSafe(sRaw) *
                    step(vec4(0.010001), nSensor);
            float count = sum4(mask);
            if (count < 1.5) continue;
            vec4 sEquivalent = sRaw * shortToNormalScale;
            vec4 rel = abs(nSensor - sEquivalent) / max(nSensor, vec4(0.04));
            errorSum += dot(rel, mask);
            supportCount += count;
            float luma = dot(nSensor, vec4(0.25));
            lumaMin = min(lumaMin, luma);
            lumaMax = max(lumaMax, luma);
            lumaSum += luma;
            lumaCount += 1.0;
        }
    }
    meanRelativeError = supportCount > 0.0 ? errorSum / supportCount : 1.0e20;
    float lumaMean = lumaCount > 0.0 ? lumaSum / lumaCount : 0.0;
    structure = lumaCount >= 4.0
            ? (lumaMax - lumaMin) / max(lumaMean, 0.03)
            : 0.0;
}

bool refineObservableCorrespondence(
        ivec2 p, vec2 predicted, out vec2 refined,
        out float bestError, out float structure, out float supportCount) {
    bestError = 1.0e20;
    float secondError = 1.0e20;
    refined = predicted;
    structure = 0.0;
    supportCount = 0.0;
    bool found = false;
    for (int sy = -1; sy <= 1; ++sy) {
        for (int sx = -1; sx <= 1; ++sx) {
            vec2 candidate = predicted + 0.5 * vec2(float(sx), float(sy));
            if (candidate.x < 0.0 || candidate.y < 0.0 ||
                    candidate.x >= float(packedSize.x) ||
                    candidate.y >= float(packedSize.y)) continue;
            float e, s, n;
            evaluateCorrespondence(p, candidate, e, s, n);
            if (n < 12.0) continue;
            found = true;
            if (e < bestError) {
                secondError = bestError;
                bestError = e;
                refined = candidate;
                structure = s;
                supportCount = n;
            } else if (e < secondError) {
                secondError = e;
            }
        }
    }
    if (!found) return false;

    if (structure >= 0.08) {
        float margin = secondError - bestError;
        bool exceptionallyGood = bestError <= 0.055;
        return bestError <= 0.12 && (exceptionallyGood || margin >= 0.010);
    }
    return supportCount >= 16.0 && bestError <= 0.060;
}

void storeState(ivec2 p, vec4 cfa, vec4 state) {
    imageStore(outCfa, p, cfa);
    imageStore(outProvenance, p, vec4(encodePhaseStates(state), 0.0, 0.0, 0.0));
}

/* IRIS_26497_PHYSICAL_SHORT_VALIDATION
 * NORMAL remains measured. SHORT_VALIDATED is granted only after unsaturated
 * short evidence survives corrected flow semantics, local correspondence
 * refinement, and the existing physical radiometry check. CENSORED remains
 * explicitly unknown rather than being promoted by downstream color heuristics.
 */
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, packedSize))) return;
    vec4 normal = texelFetch(normalCfa, p, 0);
    vec4 normalSensor = normal / max(referenceExposureScale, 1.0e-6);
    vec4 clipMask = step(vec4(physicalClipThreshold), normalSensor);
    if (sum4(clipMask) < 0.5) {
        storeState(p, normal, vec4(PROVENANCE_NORMAL));
        return;
    }
    addMask(D_TOTAL_CLIPPED, D_PHASE_TOTAL, clipMask);

    vec2 uv = (vec2(p) + vec2(0.5)) / vec2(packedSize);
    vec4 flowState = texture(flowTexture, uv);
    float variation = max(flowState.z, 0.0);
    /* flowState.w is interpolation-cancel/base-vector-preserved, not invalid. */
    float flowConfidence = exp(-80.0 * variation);
    vec2 predicted = vec2(p) + vec2(0.5) + flowState.xy;
    if (flowConfidence < minimumFlowConfidence) {
        addMask(D_FLOW_REJECT, D_PHASE_FLOW_REJECT, clipMask);
        addMask(D_STILL_CENSORED, D_PHASE_STILL_CENSORED, clipMask);
        storeState(p, normal, clipMask);
        return;
    }

    vec2 source;
    float meanError;
    float structure;
    float supportCount;
    if (!refineObservableCorrespondence(
            p, predicted, source, meanError, structure, supportCount)) {
        addMask(D_CORR_REJECT, D_PHASE_CORR_REJECT, clipMask);
        addMask(D_STILL_CENSORED, D_PHASE_STILL_CENSORED, clipMask);
        storeState(p, normal, clipMask);
        return;
    }

    vec4 shortCenter = phaseSafeBilinear(source);
    vec4 recoverMask = clipMask * shortSafe(shortCenter);
    vec4 shortClippedMask = clipMask - recoverMask;
    addTotalOnly(D_SHORT_SAFE, recoverMask);
    addMask(D_SHORT_CLIPPED, D_PHASE_SHORT_CLIPPED, shortClippedMask);
    classifyShortSamples(shortCenter, clipMask);
    if (sum4(recoverMask) < 0.5) {
        addMask(D_STILL_CENSORED, D_PHASE_STILL_CENSORED, clipMask);
        storeState(p, normal, clipMask);
        return;
    }

    vec4 shortEquivalent = shortCenter * shortToNormalScale * referenceExposureScale;
    float requiredScale = 1.0;
    for (int i = 0; i < 4; ++i) {
        if (recoverMask[i] > 0.5) {
            requiredScale = max(requiredScale,
                    normal[i] / max(shortEquivalent[i], 1.0e-6));
        }
    }
    if (requiredScale > 1.25) {
        addMask(D_RADIOMETRY_REJECT, D_PHASE_RADIOMETRY_REJECT, recoverMask);
        addMask(D_STILL_CENSORED, D_PHASE_STILL_CENSORED, clipMask);
        storeState(p, normal, clipMask);
        return;
    }
    shortEquivalent *= requiredScale;

    vec4 recovered = normal;
    vec4 state = clipMask;
    for (int i = 0; i < 4; ++i) {
        if (recoverMask[i] > 0.5) {
            float blend = smoothstep(physicalClipThreshold, 1.0, normalSensor[i]);
            recovered[i] = mix(normal[i], shortEquivalent[i], blend);
            state[i] = PROVENANCE_SHORT_VALIDATED;
        }
    }
    addMask(D_VALIDATED, D_PHASE_VALIDATED, recoverMask);
    if (sum4(shortClippedMask) > 0.5) {
        addMask(D_STILL_CENSORED, D_PHASE_STILL_CENSORED, shortClippedMask);
    }
    storeState(p, recovered, state);
}
