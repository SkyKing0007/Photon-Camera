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
layout(std430, binding = 9) buffer TrustBuf {
    float trust[];
};
uniform ivec2 rawSize;
uniform ivec2 bandSize;
uniform ivec2 bandOrigin;
uniform int cfaPattern;
uniform vec3 calculationWb;
uniform vec3 sensorGains;
uniform float highlightCeiling;
uniform int useLensShading;

const float PROVENANCE_CENSORED = 1.0;

int mirrorIndex(int value, int size) {
    if (size <= 1) return 0;
    int period = 2 * (size - 1);
    int wrapped = value % period;
    if (wrapped < 0) wrapped += period;
    return wrapped < size ? wrapped : period - wrapped;
}
ivec2 physicalAt(ivec2 lp) {
    ivec2 virtualGlobal = bandOrigin + lp;
    return ivec2(mirrorIndex(virtualGlobal.x, rawSize.x),
                 mirrorIndex(virtualGlobal.y, rawSize.y));
}
int phaseAtPhysical(ivec2 p) { return (p.x & 1) | ((p.y & 1) << 1); }
int colorAtPhysical(ivec2 p) {
    int q = phaseAtPhysical(p);
    if (cfaPattern == 0) return q == 0 ? 0 : (q == 3 ? 2 : 1);
    if (cfaPattern == 1) return q == 1 ? 0 : (q == 2 ? 2 : 1);
    if (cfaPattern == 2) return q == 2 ? 0 : (q == 1 ? 2 : 1);
    return q == 3 ? 0 : (q == 0 ? 2 : 1);
}
float phaseComponent(vec4 v, int q) {
    return q == 0 ? v.r : (q == 1 ? v.g : (q == 2 ? v.b : v.a));
}
float phaseDivisor(int q) {
    return q == 0 ? 1.0 : (q == 1 ? 3.0 : (q == 2 ? 9.0 : 27.0));
}
float provenanceAtPhysical(ivec2 p) {
    float code = texelFetch(HighlightProvenance, p >> 1, 0).r;
    float digit = floor(code / phaseDivisor(phaseAtPhysical(p)));
    return mod(digit, 3.0);
}
bool isCensoredPhysical(ivec2 p) {
    return abs(provenanceAtPhysical(p) - PROVENANCE_CENSORED) < 0.25;
}
float fusedAtPhysical(ivec2 p) {
    vec4 v = texelFetch(InputBayer, p >> 1, 0);
    return phaseComponent(v, phaseAtPhysical(p));
}
vec3 shadingRgbPhysical(ivec2 p) {
    if (useLensShading == 0) return vec3(1.0);
    vec2 uv = (vec2(p) + vec2(0.5)) / vec2(rawSize);
    vec4 g = texture(LensShadingMap, clamp(uv, vec2(0.0), vec2(1.0)));
    return max(vec3(g.r, 0.5 * (g.g + g.b), g.a), vec3(0.0));
}
float wbForColor(int col) { return col == 0 ? calculationWb.r : (col == 2 ? calculationWb.b : calculationWb.g); }
float gainForColor(int col) { return col == 0 ? sensorGains.r : (col == 2 ? sensorGains.b : sensorGains.g); }
float calculationPhysical(ivec2 p) {
    int col = colorAtPhysical(p);
    vec3 lsc = shadingRgbPhysical(p);
    return clamp(fusedAtPhysical(p) * lsc[col] * max(wbForColor(col), 1.0e-6),
                 0.0, highlightCeiling);
}
float balancedPhysical(ivec2 p) {
    int col = colorAtPhysical(p);
    return calculationPhysical(p) * gainForColor(col) / max(wbForColor(col), 1.0e-6);
}
bool trustedSamePhasePhysical(ivec2 p, out float value) {
    p = ivec2(mirrorIndex(p.x, rawSize.x), mirrorIndex(p.y, rawSize.y));
    if (isCensoredPhysical(p)) { value = 0.0; return false; }
    value = balancedPhysical(p);
    return true;
}
float censoredNeutralBalanced(ivec2 p) {
    ivec2 origin = (p >> 1) << 1;
    float lowerBound = 0.0;
    for (int py = 0; py < 2; ++py) {
        for (int px = 0; px < 2; ++px) {
            ivec2 q = ivec2(mirrorIndex(origin.x + px, rawSize.x),
                            mirrorIndex(origin.y + py, rawSize.y));
            lowerBound = max(lowerBound, balancedPhysical(q));
        }
    }
    return lowerBound;
}
float constrainedSamePhaseBalanced(ivec2 p, float neutralLowerBound) {
    float l, r, u, d;
    bool hl = trustedSamePhasePhysical(p + ivec2(-2, 0), l) &&
              trustedSamePhasePhysical(p + ivec2( 2, 0), r);
    bool hv = trustedSamePhasePhysical(p + ivec2(0, -2), u) &&
              trustedSamePhasePhysical(p + ivec2(0,  2), d);
    float best = neutralLowerBound;
    float bestCost = 1.0e20;
    if (hl) {
        float meanH = 0.5 * (l + r);
        float costH = abs(l - r) / max(meanH, 0.04);
        if (costH <= 0.18 && costH < bestCost) { best = max(neutralLowerBound, meanH); bestCost = costH; }
    }
    if (hv) {
        float meanV = 0.5 * (u + d);
        float costV = abs(u - d) / max(meanV, 0.04);
        if (costV <= 0.18 && costV < bestCost) best = max(neutralLowerBound, meanV);
    }
    return best;
}

/* IRIS_26498_RCD_PROVENANCE_SEED_AUTHORITY
 * A CENSORED phase receives a brightness-safe placeholder so the numerical RCD
 * lattice remains finite, but TrustBuf=0 preserves the fact that the placeholder
 * is not a sensor measurement. Every later directional/color pass must respect
 * that trust bit. Virtual mirrored halo samples provide full-photo boundary
 * conditions without changing Bayer parity.
 */
void main() {
    ivec2 lp = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(lp, bandSize))) return;
    ivec2 pp = physicalAt(lp);
    int idx = lp.y * bandSize.x + lp.x;
    int col = colorAtPhysical(pp);
    bool measured = !isCensoredPhysical(pp);
    float value = calculationPhysical(pp);
    if (!measured) {
        float neutralBalanced = censoredNeutralBalanced(pp);
        float reconstructedBalanced = constrainedSamePhaseBalanced(pp, neutralBalanced);
        value = reconstructedBalanced * wbForColor(col) / max(gainForColor(col), 1.0e-6);
        value = min(max(value, 0.0), highlightCeiling);
    }
    cfa[idx] = value;
    red[idx] = col == 0 ? value : 0.0;
    green[idx] = col == 1 ? value : 0.0;
    blue[idx] = col == 2 ? value : 0.0;
    trust[idx] = measured ? 1.0 : 0.0;
}
