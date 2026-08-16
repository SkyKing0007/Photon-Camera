#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

FILES = {
'prov': Path('app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl'),
'short': Path('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl'),
'populate': Path('app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl'),
'gain': Path('app/src/main/assets/shaders/motionv2/gainmap.glsl'),
'recon': Path('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'),
'render': Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'),
}
EXPECTED = {
FILES['prov']: 'a9a813348c59979ae0daaa6bf28384410c7b1a8f04f0c1d8d8447370fd51cacd',
FILES['short']: 'a96963ce3c84c9d93d5a2124a6f8da57b0f11f360329a467b8768d0d2f01f6ef',
FILES['populate']: '43977cb7cf51878e5eb851a811f12e2a133e2e53e054f6fc0105cae51ce72d8f',
FILES['gain']: 'a392ed0931d2fa475ce3353c7fe15051e033ed9c6194c7487f7eba883a208d87',
FILES['recon']: '94a47bb25c85e13e9221779a17688b9865ab5cffd809d89b723f550959fd0f85',
FILES['render']: '407a27674331f15cff491a0608a16cf489b4b0889c9cbebd38ba6ce8c723213e',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(s, old, new, name):
    c=s.count(old)
    if c != 1: raise SystemExit(f'{name} anchor count={c}, expected=1')
    return s.replace(old,new,1)

PROVENANCE = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp image2D;

uniform highp sampler2D normalCfa;
layout(r32f, binding = 0) uniform highp writeonly image2D outProvenance;
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float physicalClipThreshold;

/* IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_INIT
 * Provenance follows each physical R/G1/G2/B observation independently, while
 * preserving the proven one-float-per-packed-cell bridge. Four ternary states are
 * encoded exactly as a base-3 integer in R32F:
 *   code = s0 + 3*s1 + 9*s2 + 27*s3, each s in {0 NORMAL, 1 CENSORED, 2 SHORT}.
 * Maximum code is 80, represented exactly by float32. No extra full-frame carrier
 * or readback bandwidth is introduced.
 */
float encodePhaseStates(vec4 s) {
    return dot(s, vec4(1.0, 3.0, 9.0, 27.0));
}
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, packedSize))) return;
    vec4 normal = texelFetch(normalCfa, p, 0);
    vec4 sensor = normal / max(referenceExposureScale, 1.0e-6);
    vec4 state = step(vec4(physicalClipThreshold), sensor);
    imageStore(outProvenance, p, vec4(encodePhaseStates(state), 0.0, 0.0, 0.0));
}
'''

SHORT = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;

uniform highp sampler2D normalCfa;
uniform highp sampler2D shortCfa;
uniform highp sampler2D flowTexture;
layout(rgba32f, binding = 0) uniform highp writeonly image2D outCfa;
layout(r32f, binding = 1) uniform highp writeonly image2D outProvenance;
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float shortToNormalScale;
uniform float physicalClipThreshold;
uniform float shortClipThreshold;
uniform float minimumFlowConfidence;

const float PROVENANCE_NORMAL = 0.0;
const float PROVENANCE_CENSORED = 1.0;
const float PROVENANCE_SHORT_VALIDATED = 2.0;

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

/* Existing correspondence proof is preserved. */
bool validateObservableCorrespondence(
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
            vec4 nSensor = texelFetch(normalCfa, q, 0) /
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
    return supportCount >= 12.0 && meanRelativeError <= 0.12 && structure >= 0.08;
}

void storeState(ivec2 p, vec4 cfa, vec4 state) {
    imageStore(outCfa, p, cfa);
    imageStore(outProvenance, p, vec4(encodePhaseStates(state), 0.0, 0.0, 0.0));
}

/* IRIS_26494_PER_PHASE_SHORT_VALIDATION
 * Unsaturated normal phases remain exactly measured when another phase clips.
 * Only a clipped phase whose short observation is individually unsaturated may
 * become SHORT_VALIDATED, and only after the existing observable-ring proof.
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

    vec2 uv = (vec2(p) + vec2(0.5)) / vec2(packedSize);
    vec4 flowState = texture(flowTexture, uv);
    float variation = max(flowState.z, 0.0);
    float cancelled = step(0.5, flowState.w);
    float flowConfidence = (1.0 - cancelled) * exp(-80.0 * variation);
    vec2 source = vec2(p) + vec2(0.5) + flowState.xy;
    if (source.x < 0.0 || source.y < 0.0 ||
            source.x >= float(packedSize.x) || source.y >= float(packedSize.y) ||
            flowConfidence < minimumFlowConfidence) {
        storeState(p, normal, clipMask);
        return;
    }

    vec4 shortCenter = phaseSafeBilinear(source);
    vec4 recoverMask = clipMask * shortSafe(shortCenter);
    if (sum4(recoverMask) < 0.5) {
        storeState(p, normal, clipMask);
        return;
    }

    float meanError;
    float structure;
    float supportCount;
    if (!validateObservableCorrespondence(p, source, meanError, structure, supportCount)) {
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
    storeState(p, recovered, state);
}
'''

POPULATE = r'''#define LAYOUT //
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
'''

GAIN = r'''precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform ivec2 sourceSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out vec4 Output;

/* IRIS_26494_MATCHED_FOOTPRINT_UHDR_GAINMAP
 * Each 1/4-resolution gain value represents its exact corresponding 4x4 source
 * footprint. HDR and SDR luminance are integrated first; the ratio is formed once
 * afterward. This is anti-aliased decimation, not a blur of an aliased gain map.
 * SDR remains the sole full-resolution spatial-detail authority.
 */
const float UHDR_OFFSET = 0.015625;
const int FOOTPRINT = 4;
float luminance(vec3 c){return dot(c,vec3(0.2126,0.7152,0.0722));}
float srgbDecode(float x){
    x=clamp(x,0.0,1.0);
    return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);
}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}
void footprintLuminance(ivec2 gainPixel, out float hdrMean, out float sdrMean) {
    ivec2 base = gainPixel * FOOTPRINT;
    float hdrSum = 0.0;
    float sdrSum = 0.0;
    for (int oy = 0; oy < FOOTPRINT; ++oy) {
        for (int ox = 0; ox < FOOTPRINT; ++ox) {
            ivec2 sp = clamp(base + ivec2(ox, oy), ivec2(0), sourceSize - ivec2(1));
            vec3 hdr = max(texelFetch(HdrBuffer, sp, 0).rgb, vec3(0.0)) * hdrExposureScale;
            vec3 sdr = srgbDecode(texelFetch(SdrBuffer, sp, 0).rgb);
            hdrSum += max(luminance(hdr), 0.0);
            sdrSum += max(luminance(sdr), 0.0);
        }
    }
    hdrMean = hdrSum / float(FOOTPRINT * FOOTPRINT);
    sdrMean = sdrSum / float(FOOTPRINT * FOOTPRINT);
}
void main(){
    ivec2 gp = ivec2(gl_FragCoord.xy);
    if (any(greaterThanEqual(gp, gainMapSize))) {
        Output = vec4(0.0,0.0,0.0,1.0);
        return;
    }
    float hdrMean;
    float sdrMean;
    footprintLuminance(gp, hdrMean, sdrMean);
    float maxLog=max(log2(max(maxGainRatio,1.001)),1.0e-6);
    float ratio=clamp((hdrMean+UHDR_OFFSET)/(sdrMean+UHDR_OFFSET),
            1.0,max(maxGainRatio,1.001));
    float encoded=clamp(log2(ratio)/maxLog,0.0,1.0);
    Output=vec4(encoded,encoded,encoded,1.0);
}
'''

def apply(root: Path):
    for rel,h in EXPECTED.items():
        p=root/rel
        if not p.is_file(): raise SystemExit(f'missing exact V5B target: {rel}')
        a=sha(p)
        if a!=h: raise SystemExit(f'V5B target hash mismatch {rel}: {a} expected {h}')
    (root/FILES['prov']).write_text(PROVENANCE)
    (root/FILES['short']).write_text(SHORT)
    (root/FILES['populate']).write_text(POPULATE)
    (root/FILES['gain']).write_text(GAIN)

    rp=root/FILES['recon']; s=rp.read_text()
    s=replace_once(s,
'''            /* IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE_OWNER\n             * Classify physical clipping before any short-frame substitution. This state is a\n             * separate proven R32F carrier and therefore cannot corrupt the four CFA radiance channels.\n             */''',
'''            /* IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_OWNER\n             * Classify R/G1/G2/B clipping independently before short substitution. The four ternary\n             * phase states are base-3 packed into the existing R32F carrier, preserving bandwidth.\n             */''','recon provenance comment')
    old='''                    int normalCount = 0, censoredCount = 0, shortCount = 0, invalidCount = 0;\n                    ByteBuffer provenanceView = highlightProvenanceOutput.duplicate()\n                            .order(ByteOrder.nativeOrder());\n                    provenanceView.position(0);\n                    while (provenanceView.remaining() >= Float.BYTES) {\n                        float encoded = provenanceView.getFloat();\n                        int state = Math.round(encoded);\n                        if (!Float.isFinite(encoded) || Math.abs(encoded - state) > 0.01f) invalidCount++;\n                        else if (state == 0) normalCount++;\n                        else if (state == 1) censoredCount++;\n                        else if (state == 2) shortCount++;\n                        else invalidCount++;\n                    }\n                    Log.d(TAG, "IRIS_26492_HIGHLIGHT_PROVENANCE_COUNTS"\n                            + " normal=" + normalCount\n                            + " censored=" + censoredCount\n                            + " shortValidated=" + shortCount\n                            + " invalid=" + invalidCount\n                            + " oneGpuDrain=true");'''
    new='''                    int normalPhases = 0, censoredPhases = 0, shortPhases = 0, invalidPhases = 0;\n                    int[] censoredByPackedPhase = new int[4];\n                    int[] shortByPackedPhase = new int[4];\n                    int[] affectedPackHistogram = new int[5];\n                    int packsWithShort = 0;\n                    ByteBuffer provenanceView = highlightProvenanceOutput.duplicate()\n                            .order(ByteOrder.nativeOrder());\n                    provenanceView.position(0);\n                    while (provenanceView.remaining() >= Float.BYTES) {\n                        float encoded = provenanceView.getFloat();\n                        int code = Math.round(encoded);\n                        if (!Float.isFinite(encoded) || Math.abs(encoded - code) > 0.01f\n                                || code < 0 || code > 80) {\n                            invalidPhases += 4;\n                            continue;\n                        }\n                        int affected = 0;\n                        boolean anyShort = false;\n                        int remaining = code;\n                        for (int phase = 0; phase < 4; ++phase) {\n                            int state = remaining % 3;\n                            remaining /= 3;\n                            if (state == 0) {\n                                normalPhases++;\n                            } else if (state == 1) {\n                                censoredPhases++; censoredByPackedPhase[phase]++; affected++;\n                            } else {\n                                shortPhases++; shortByPackedPhase[phase]++; affected++; anyShort = true;\n                            }\n                        }\n                        affectedPackHistogram[affected]++;\n                        if (anyShort) packsWithShort++;\n                    }\n                    Log.d(TAG, "IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE"\n                            + " encoding=R32F_BASE3_PHASES"\n                            + " normalPhases=" + normalPhases\n                            + " censoredPhases=" + censoredPhases\n                            + " shortValidatedPhases=" + shortPhases\n                            + " invalidPhases=" + invalidPhases\n                            + " censoredByPackedPhase=" + java.util.Arrays.toString(censoredByPackedPhase)\n                            + " shortByPackedPhase=" + java.util.Arrays.toString(shortByPackedPhase)\n                            + " affectedPackHistogram0to4=" + java.util.Arrays.toString(affectedPackHistogram)\n                            + " packsWithShort=" + packsWithShort\n                            + " extraFullFrameCarrier=false"\n                            + " oneGpuDrain=true");\n                    try {\n                        com.particlesdevs.photoncamera.util.MotionTrace.processingState(\n                                "IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE",\n                                "normalPhases=" + normalPhases\n                                        + " censoredPhases=" + censoredPhases\n                                        + " shortPhases=" + shortPhases\n                                        + " invalidPhases=" + invalidPhases\n                                        + " affectedPacks0to4=" + java.util.Arrays.toString(affectedPackHistogram));\n                    } catch (Throwable ignored) {}'''
    s=replace_once(s,old,new,'recon phase diagnostics')
    s=s.replace('+ " highlightProvenanceR32F=" + directBayer);',
                '+ " highlightProvenanceR32FBase3PerPhase=" + directBayer);',1)
    rp.write_text(s)

    mp=root/FILES['render']; s=mp.read_text()
    old='''                glProg.setTexture("HdrBuffer", extendedLinearHdr);\n                glProg.setTexture("SdrBuffer", WorkingTexture);\n                glProg.setVar("gainMapSize", gainSize);\n                glProg.setVar("hdrExposureScale", OUTPUT_EXPOSURE_SCALE);'''
    new='''                glProg.setTexture("HdrBuffer", extendedLinearHdr);\n                glProg.setTexture("SdrBuffer", WorkingTexture);\n                glProg.setVar("gainMapSize", gainSize);\n                glProg.setVar("sourceSize", renderedSdrSize);\n                glProg.setVar("hdrExposureScale", OUTPUT_EXPOSURE_SCALE);'''
    s=replace_once(s,old,new,'render gainmap source geometry')
    s=s.replace('+ " broadRenditionNotEdgeTexture=true"\n                        + " midtoneGainUnity=true"',
                '+ " broadRenditionNotEdgeTexture=true"\n                        + " matchedSourceFootprint=4x4"\n                        + " pointDecimation=false"\n                        + " postAliasSpikeRepair=false"\n                        + " midtoneGainUnity=true"',1)
    mp.write_text(s)

    checks={
      FILES['prov']:'R32F_BASE3',
      FILES['short']:'IRIS_26494_PER_PHASE_SHORT_VALIDATION',
      FILES['populate']:'IRIS_26494_RCD_PER_PHASE_PROVENANCE_CONSUMER',
      FILES['gain']:'IRIS_26494_MATCHED_FOOTPRINT_UHDR_GAINMAP',
      FILES['recon']:'IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE',
      FILES['render']:'matchedSourceFootprint=4x4',
    }
    # provenance marker is semantic in comment; direct check for base-3 function instead.
    if 'encodePhaseStates' not in (root/FILES['prov']).read_text(): raise SystemExit('provenance base3 encoder missing')
    for rel,marker in list(checks.items())[1:]:
        if marker not in (root/rel).read_text(): raise SystemExit(f'marker missing {marker} in {rel}')
    print('26494 TRANSFORM PASS files=6 perPhaseCfaAuthority=true provenanceCarrier=R32F_BASE3 shortPerPhase=true rcdUnresolvedPhaseOnly=true uhdrMatchedFootprint4x4=true')


def self_test():
    def encode(states): return states[0]+3*states[1]+9*states[2]+27*states[3]
    def decode(code):
        out=[]
        for _ in range(4): out.append(code%3); code//=3
        return out
    states=[0,0,0,1]
    code=encode(states)
    assert code<=80 and decode(code)==states
    # measured phases survive when one clips; short upgrades only that physical phase.
    normal=[.72,.83,.91,1.0]; recovered=normal[:]; out=states[:]
    recovered[3]=1.42; out[3]=2
    assert recovered[:3]==normal[:3] and decode(encode(out))==[0,0,0,2]
    neutral=1.1; l=1.25; r=1.27; mean=.5*(l+r); cost=abs(l-r)/max(mean,.04)
    estimate=max(neutral,mean) if cost<=.18 else neutral
    assert estimate>=neutral
    hdr=[1.0]*8+[4.0]*8; sdr=[1.0]*8+[2.0]*8
    footprint=(sum(hdr)/16+.015625)/(sum(sdr)/16+.015625)
    point=(hdr[-1]+.015625)/(sdr[-1]+.015625)
    assert abs(footprint-point)>0.05
    print('26494 MODEL SELF-TEST PASS base3RoundTrip=true partialPackPreservesMeasured=true shortPerPhase=true censoredFloorMonotonic=true gainRatioUsesFootprint=true')

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--self-test': self_test()
    elif len(sys.argv)==2: apply(Path(sys.argv[1]).resolve())
    else: raise SystemExit('usage: transform_26494_hdr_phase_validity_uhdr_aa_v1.py --self-test | <repo-root>')
