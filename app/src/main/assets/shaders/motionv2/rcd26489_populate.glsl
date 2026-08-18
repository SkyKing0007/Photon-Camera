#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp sampler2D;

uniform highp sampler2D InputBayer;
uniform highp sampler2D HighlightProvenance;
uniform highp sampler2D LensShadingMap;
layout(std430, binding = 0) buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 1) buffer RedBuf {
    float red[];
};
layout(std430, binding = 2) buffer GreenBuf {
    float green[];
};
layout(std430, binding = 3) buffer BlueBuf {
    float blue[];
};
uniform ivec2 rawSize;
uniform ivec2 bandSize;
uniform int bandOriginY;
uniform int cfaPattern;
uniform vec3 calculationWb;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform float highlightThreshold;
uniform float highlightCeiling;
uniform int useLensShading;

const float PROVENANCE_CENSORED = 1.0;

int phaseAt(ivec2 p) { return (p.x & 1) | ((p.y & 1) << 1); }
int colorAt(ivec2 p) {
    int q = phaseAt(p);
    if (cfaPattern == 0) return q == 0 ? 0 : (q == 3 ? 2 : 1);
    if (cfaPattern == 1) return q == 1 ? 0 : (q == 2 ? 2 : 1);
    if (cfaPattern == 2) return q == 2 ? 0 : (q == 1 ? 2 : 1);
    return q == 3 ? 0 : (q == 0 ? 2 : 1);
}
bool inRaw(ivec2 p) {
    return all(greaterThanEqual(p, ivec2(0))) && all(lessThan(p, rawSize));
}
ivec2 clampGlobal(ivec2 p) { return clamp(p, ivec2(0), rawSize - ivec2(1)); }
float phaseComponent(vec4 v, int q) {
    return q == 0 ? v.r : (q == 1 ? v.g : (q == 2 ? v.b : v.a));
}
float phaseDivisor(int q) {
    return q == 0 ? 1.0 : (q == 1 ? 3.0 : (q == 2 ? 9.0 : 27.0));
}
float provenanceAt(ivec2 p) {
    p = clampGlobal(p);
    float code = texelFetch(HighlightProvenance, p >> 1, 0).r;
    float digit = floor(code / phaseDivisor(phaseAt(p)));
    return mod(digit, 3.0);
}
bool isCensoredState(float state) { return abs(state - PROVENANCE_CENSORED) < 0.25; }
float fusedAt(ivec2 p) {
    p = clampGlobal(p);
    vec4 v = texelFetch(InputBayer, p >> 1, 0);
    return phaseComponent(v, phaseAt(p));
}
vec3 shadingRgb(ivec2 p) {
    if (useLensShading == 0) return vec3(1.0);
    vec2 uv = (vec2(clampGlobal(p)) + vec2(0.5)) / vec2(rawSize);
    vec4 g = texture(LensShadingMap, clamp(uv, vec2(0.0), vec2(1.0)));
    return max(vec3(g.r, 0.5 * (g.g + g.b), g.a), vec3(0.0));
}
float wbForColor(int col) { return col == 0 ? calculationWb.r : (col == 2 ? calculationWb.b : calculationWb.g); }
float gainForColor(int col) { return col == 0 ? sensorGains.r : (col == 2 ? sensorGains.b : sensorGains.g); }
float rawCalculationAt(ivec2 p) {
    p = clampGlobal(p);
    int col = colorAt(p);
    vec3 lsc = shadingRgb(p);
    return clamp(fusedAt(p) * lsc[col] * max(wbForColor(col), 1.0e-6), 0.0, highlightCeiling);
}
float rawBalancedAt(ivec2 p) {
    int col = colorAt(clampGlobal(p));
    return rawCalculationAt(p) * gainForColor(col) / max(wbForColor(col), 1.0e-6);
}

/* IRIS_26494_PHASE_LOCAL_CENSOR_LOWER_BOUND
 * Keep the proven neutral physical lower bound, but apply it only to an actually
 * unresolved clipped phase. Measured phases in the same 2x2 cell pass unchanged.
 */
float censoredNeutralBalanced(ivec2 p) {
    ivec2 origin = (clampGlobal(p) >> 1) << 1;
    float lowerBound = 0.0;
    for (int py = 0; py < 2; ++py) {
        for (int px = 0; px < 2; ++px) {
            ivec2 q = clampGlobal(origin + ivec2(px, py));
            lowerBound = max(lowerBound, rawBalancedAt(q));
        }
    }
    return lowerBound;
}
bool trustedSamePhaseBalanced(ivec2 p, out float value) {
    if (!inRaw(p)) { value = 0.0; return false; }
    if (isCensoredState(provenanceAt(p))) { value = 0.0; return false; }
    value = rawBalancedAt(p);
    return true;
}
float constrainedSamePhaseBalanced(ivec2 p, float neutralLowerBound) {
    float l, r, u, d;
    bool hl = trustedSamePhaseBalanced(p + ivec2(-2, 0), l) &&
              trustedSamePhaseBalanced(p + ivec2( 2, 0), r);
    bool hv = trustedSamePhaseBalanced(p + ivec2(0, -2), u) &&
              trustedSamePhaseBalanced(p + ivec2(0,  2), d);
    float best = neutralLowerBound;
    float bestCost = 1.0e20;
    if (hl) {
        float meanH = 0.5 * (l + r);
        float costH = abs(l - r) / max(meanH, 0.04);
        if (costH <= 0.18 && costH < bestCost) {
            best = max(neutralLowerBound, meanH);
            bestCost = costH;
        }
    }
    if (hv) {
        float meanV = 0.5 * (u + d);
        float costV = abs(u - d) / max(meanV, 0.04);
        if (costV <= 0.18 && costV < bestCost) {
            best = max(neutralLowerBound, meanV);
        }
    }
    return best;
}
float provenanceCalculationAt(ivec2 p) {
    int col = colorAt(clampGlobal(p));
    float measured = rawCalculationAt(p);
    if (!isCensoredState(provenanceAt(p))) return measured;
    float neutralBalanced = censoredNeutralBalanced(p);
    float reconstructedBalanced = constrainedSamePhaseBalanced(p, neutralBalanced);
    float reconstructedCalculation = reconstructedBalanced * wbForColor(col) /
            max(gainForColor(col), 1.0e-6);
    return min(max(reconstructedCalculation, 0.0), highlightCeiling);
}

/* IRIS_26494_RCD_PER_PHASE_PROVENANCE_CONSUMER
 * RCD remains a consumer, never a clip classifier. NORMAL and SHORT_VALIDATED
 * phases pass exactly; only the unresolved CENSORED physical phase is replaced
 * before the unchanged nine directional RCD passes.
 */
void main() {
    ivec2 lp = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(lp, bandSize))) return;
    ivec2 gp = ivec2(lp.x, bandOriginY + lp.y);
    int idx = lp.y * bandSize.x + lp.x;
    int col = colorAt(gp);
    float value = provenanceCalculationAt(gp);
    cfa[idx] = value;
    red[idx] = col == 0 ? value : 0.0;
    green[idx] = col == 1 ? value : 0.0;
    blue[idx] = col == 2 ? value : 0.0;
}
