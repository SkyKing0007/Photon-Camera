#!/usr/bin/env python3
from pathlib import Path
import hashlib
import math
import re
import sys

MERGER = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java"
SHORT = "app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
PRE = {
    MERGER: "9519d52fed6c12a1ef707e9d47b9111dafe901e9ab7c3918998841935decc111",
    SHORT: "9c1cb82fc9c151eaaa7266d40eee63c0df193d3fdef9b911b193e89e9f454f65",
}
SHORT_POST_SHA256 = "66ee99202db50525a35284835f8552625fb228e6c0e68db5b07a2a1b65202726"

OLD_GAIN = "        float gain = Math.max(1.0f, candidateGain * adaptiveReduction);\n"
NEW_GAIN = """        /*
         * IRIS_26491_MIDTONE_OWNS_GLOBAL_DISPLAY_GAIN
         *
         * The p50/p90 scene body owns global display exposure. Highlight
         * occupancy and true-clip measurements remain diagnostic evidence only;
         * aligned short-frame recovery, physical-sensor RCD and extended-linear
         * rendering own local/saturated highlight handling.
         */
        float gain = Math.max(1.0f, candidateGain);
"""

SHORT_26491 = r"""#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

uniform highp sampler2D normalCfa;
uniform highp sampler2D shortCfa;
uniform highp sampler2D flowTexture;
layout(rgba32f,binding=0) uniform highp writeonly image2D outCfa;
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float shortToNormalScale;
uniform float physicalClipThreshold;
uniform float shortClipThreshold;
uniform float minimumFlowConfidence;

/* IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY */
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

vec4 shortSafeMask(vec4 v) {
    return vec4(
        v.r < shortClipThreshold ? 1.0 : 0.0,
        v.g < shortClipThreshold ? 1.0 : 0.0,
        v.b < shortClipThreshold ? 1.0 : 0.0,
        v.a < shortClipThreshold ? 1.0 : 0.0);
}

float sum4(vec4 v) {
    return dot(v, vec4(1.0));
}

/*
 * IRIS_26491_JOINT_SHORT_HDR_CHROMATICITY
 *
 * 26490 correctly aligned and radiometrically normalized the short RAW, but
 * its final decision was made independently for each CFA phase. Around a
 * saturated lamp/reflection that can extend R/G/B phases from different
 * evidence states and expose the 2x2 CFA geometry as orange/pink blocks.
 *
 * 26491 keeps the same physical samples and flow field, but makes one joint
 * decision for every phase that the normal observation says is clipped:
 *   1. Prefer the aligned center short CFA vector when every needed phase is
 *      physically unsaturated.
 *   2. If only part of that center vector is censored, a 3x3 packed-CFA
 *      search may transfer ONE coherent neighboring short vector, but only
 *      when at least two center phases provide matching unsaturated evidence.
 *   3. If coherent evidence cannot be proven, preserve the normal saturated
 *      lower bound. RCD remains the physical censor/opponent fallback owner.
 *
 * No channel is independently borrowed and nothing is clamped to 1.0.
 */
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, packedSize))) return;

    vec4 normal = texelFetch(normalCfa, p, 0);
    vec2 uv = (vec2(p) + vec2(0.5)) / vec2(packedSize);

    /* IRIS_26490_SHORT_FLOW_RELIABILITY_GATE -- preserved byte-for-math. */
    vec4 flowState = texture(flowTexture, uv);
    float variation = max(flowState.z, 0.0);
    float cancelled = step(0.5, flowState.w);
    float flowConfidence = (1.0 - cancelled) * exp(-80.0 * variation);
    float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);
    vec2 source = vec2(p) + vec2(0.5) + flowState.xy;
    if (source.x < 0.0 || source.y < 0.0 ||
        source.x >= float(packedSize.x) || source.y >= float(packedSize.y) ||
        flowConfidence < minimumFlowConfidence) {
        imageStore(outCfa, p, normal);
        return;
    }

    vec4 normalSensor = normal / max(referenceExposureScale, 1.0e-6);
    vec4 normalClip = smoothstep(
        vec4(physicalClipThreshold), vec4(1.0), normalSensor);
    vec4 needed = step(vec4(0.05), normalClip);
    if (sum4(needed) < 0.5) {
        imageStore(outCfa, p, normal);
        return;
    }

    vec4 centerShort = phaseSafeBilinear(source);
    vec4 centerSafe = shortSafeMask(centerShort);
    vec4 selectedShort = centerShort;
    float jointConfidence = 0.0;

    /* Fast path: one real center short vector contains every clipped phase. */
    if (sum4(needed * (vec4(1.0) - centerSafe)) < 0.5) {
        jointConfidence = 1.0;
    } else {
        /*
         * Partial-censor path. Search only one packed-CFA texel away, which
         * preserves CFA phase identity. A candidate must contain ALL needed
         * phases below short saturation and agree with at least two measurable
         * center phases after a bounded local brightness normalization.
         */
        float bestCost = 1.0e20;
        vec4 bestShort = centerShort;
        float bestConfidence = 0.0;

        for (int oy = -1; oy <= 1; ++oy) {
            for (int ox = -1; ox <= 1; ++ox) {
                if (ox == 0 && oy == 0) continue;
                vec2 q = source + vec2(float(ox), float(oy));
                if (q.x < 0.0 || q.y < 0.0 ||
                    q.x >= float(packedSize.x) || q.y >= float(packedSize.y)) {
                    continue;
                }

                vec4 candidate = phaseSafeBilinear(q);
                vec4 candidateSafe = shortSafeMask(candidate);
                if (sum4(needed * (vec4(1.0) - candidateSafe)) >= 0.5) {
                    continue;
                }

                vec4 common = centerSafe * candidateSafe;
                float commonCount = sum4(common);
                if (commonCount < 1.5) continue;

                float centerSum = dot(centerShort, common);
                float candidateSum = dot(candidate, common);
                float localScale = clamp(
                    centerSum / max(candidateSum, 1.0e-6), 0.67, 1.50);
                vec4 scaledCandidate = candidate * localScale;
                float centerMean = centerSum / max(commonCount, 1.0);
                float relativeError =
                    dot(abs(centerShort - scaledCandidate), common)
                    / (max(commonCount, 1.0) * max(centerMean, 0.02));

                float spatialPenalty =
                    0.018 * sqrt(float(ox * ox + oy * oy));
                float cost = relativeError + spatialPenalty;
                float coherence =
                    1.0 - smoothstep(0.060, 0.140, relativeError);

                if (coherence > 0.0 && cost < bestCost) {
                    bestCost = cost;
                    bestShort = scaledCandidate;
                    bestConfidence = 0.85 * coherence;
                }
            }
        }

        selectedShort = bestShort;
        jointConfidence = bestConfidence;
    }

    if (jointConfidence <= 0.0) {
        imageStore(outCfa, p, normal);
        return;
    }

    /* IRIS_26490_CENSORED_NORMAL_IS_LOWER_BOUND -- preserved physically. */
    vec4 recoveredEstimate =
        selectedShort * shortToNormalScale * referenceExposureScale;
    vec4 recovered = max(normal, recoveredEstimate);

    /*
     * One scalar confidence gates every clipped phase. normalClip still gives
     * the smooth physical transition into saturation, but shortSafe is no
     * longer multiplied per channel and therefore cannot draw CFA blocks.
     */
    vec4 useShort = normalClip * (flowGate * jointConfidence);
    imageStore(outCfa, p, mix(normal, recovered, useShort));
}
"""

REQUIRED_MERGER_26490 = (
    "IRIS_26490_EXPLICIT_DISPLAY_DOMAIN",
    "float p50 = quantile(hist, samples, 0.50f);",
    "float p90 = quantile(hist, samples, 0.90f);",
    "final float targetP50 = 0.050f;",
    "final float targetP90 = 0.18f;",
    "float candidateGain = Math.max(1.0f, sceneGain);",
    "float predictedShoulderFraction = fractionAbove(hist, samples, 0.82f / candidateGain);",
    "float predictedWhiteFraction = fractionAbove(hist, samples, 1.00f / candidateGain);",
    "float predictedHighFraction = fractionAbove(hist, samples, 1.50f / candidateGain);",
    "float trueRawClipFraction = fractionAbove(hist, samples, 0.995f);",
    "float adaptiveReduction = 1.0f /",
    "gain = Math.min(gain, 16.0f);",
)

REQUIRED_SHORT_26490 = (
    "IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY",
    "IRIS_26490_SHORT_FLOW_RELIABILITY_GATE",
    "IRIS_26490_CENSORED_NORMAL_IS_LOWER_BOUND",
    "float flowConfidence = (1.0 - cancelled) * exp(-80.0 * variation);",
    "float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);",
    "vec4 useShort = normalClip * shortSafe * flowGate;",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str):
    raise SystemExit("26491 FAIL: " + msg)


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def smoothstep(a: float, b: float, x: float) -> float:
    t = clamp01((x-a)/max(b-a,1e-12))
    return t*t*(3.0-2.0*t)


def display_gain(p50,p90,shoulder,white,high,clip):
    eps=1e-6
    gain50=0.050/max(p50,eps)
    gain90=0.180/max(p90,eps)
    scene=math.sqrt(max(1.0,gain50)*max(1.0,gain90))
    candidate=max(1.0,scene)
    occupancy=clamp01(0.45*smoothstep(0.06,0.32,shoulder)
                      +0.35*smoothstep(0.02,0.18,white)
                      +0.20*smoothstep(0.005,0.08,high))
    true_clip=smoothstep(0.002,0.035,clip)
    reduction=1.0/(1.0+0.55*occupancy+1.35*true_clip)
    old=max(1.0,min(16.0,candidate*reduction))
    new=max(1.0,min(16.0,candidate))
    if old<1.02: old=1.0
    if new<1.02: new=1.0
    return old,new,candidate,reduction


def validate_math():
    _,bright,_,_=display_gain(0.080,0.320,0.30,0.20,0.10,0.05)
    if abs(bright-1.0)>1e-7: fail(f"bright room must remain unity, got {bright}")
    _,a,_,_=display_gain(0.005,0.030,0.01,0.002,0.001,0.0005)
    _,b,_,_=display_gain(0.005,0.030,0.45,0.25,0.12,0.05)
    if abs(a-b)>1e-7 or a<=1.0: fail(f"highlight tail still owns global gain {a} {b}")
    _,dark,_,_=display_gain(0.010,0.050,0,0,0,0)
    _,broad,_,_=display_gain(0.010,0.250,0,0,0,0)
    if not broad<dark: fail("p90 broad-scene restraint missing")
    print("26491 DISPLAY EXPOSURE MATH PASS midtoneOwner=true highlightTailDiagnosticOnly=true")


def validate_joint_policy_model():
    # Needed phases are the phases whose normal observations are clipped.
    # Partial short availability must never produce independent channel writes.
    def joint(needed,safe):
        return all((not n) or s for n,s in zip(needed,safe))
    if not joint((1,1,0,0),(1,1,1,1)): fail("joint fully-safe case rejected")
    if joint((1,1,0,0),(1,0,1,1)): fail("partial per-phase short case was accepted")
    if not joint((0,1,0,0),(0,1,0,0)): fail("single needed safe phase rejected")
    print("26491 JOINT SHORT MODEL PASS partialPhaseSubstitution=false")


def transform_merger(text: str) -> str:
    for n in REQUIRED_MERGER_26490:
        if n not in text: fail("missing exact 26490 merger contract: "+n)
    if text.count(OLD_GAIN)!=1: fail(f"26490 gain assignment count={text.count(OLD_GAIN)} expected=1")
    if "IRIS_26491_MIDTONE_OWNS_GLOBAL_DISPLAY_GAIN" in text: fail("26491 merger marker already present")
    out=text.replace(OLD_GAIN,NEW_GAIN,1)
    validate_merger(out)
    return out


def validate_merger(text: str):
    if text.count("IRIS_26491_MIDTONE_OWNS_GLOBAL_DISPLAY_GAIN")!=1: fail("26491 merger marker count invalid")
    if OLD_GAIN.strip() in text: fail("26490 highlight-pressure gain assignment survived")
    if text.count("float gain = Math.max(1.0f, candidateGain);")!=1: fail("candidateGain owner count invalid")
    for n in REQUIRED_MERGER_26490:
        if n not in text: fail("inherited merger contract removed: "+n)
    for line in text.splitlines():
        if re.search(r"\bgain\s*=.*adaptiveReduction",line):
            fail("highlight pressure still drives global gain: "+line.strip())
    if 'adaptiveReduction=' not in text: fail("highlight telemetry removed")


def validate_short_pre(text: str):
    for n in REQUIRED_SHORT_26490:
        if n not in text: fail("missing exact 26490 short contract: "+n)


def validate_short_post(text: str):
    for n in (
        "IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY",
        "IRIS_26490_SHORT_FLOW_RELIABILITY_GATE",
        "IRIS_26490_CENSORED_NORMAL_IS_LOWER_BOUND",
        "IRIS_26491_JOINT_SHORT_HDR_CHROMATICITY",
        "float flowConfidence = (1.0 - cancelled) * exp(-80.0 * variation);",
        "float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);",
        "selectedShort * shortToNormalScale * referenceExposureScale",
        "vec4 recovered = max(normal, recoveredEstimate);",
        "vec4 useShort = normalClip * (flowGate * jointConfidence);",
        "commonCount < 1.5",
        "localScale = clamp(",
    ):
        if n not in text: fail("26491 short contract missing: "+n)
    for forbidden in (
        "vec4 useShort = normalClip * shortSafe * flowGate;",
        "normalClip * shortSafe",
        "clamp(recovered",
        "min(normal, recoveredEstimate)",
    ):
        if forbidden in text: fail("unsafe/old short behavior survived: "+forbidden)
    if text.count("imageStore(outCfa")<4: fail("reference fallback paths unexpectedly removed")
    if text.count("{")!=text.count("}") or text.count("(")!=text.count(")"):
        fail("short shader delimiter imbalance")


def self_test():
    validate_math(); validate_joint_policy_model()
    if sha(SHORT_26491.encode("utf-8")) != SHORT_POST_SHA256:
        fail("embedded 26491 short shader hash mismatch")
    validate_short_post(SHORT_26491)
    fixture="\n".join(REQUIRED_MERGER_26490)+"\n"+OLD_GAIN+'                + " adaptiveReduction=" + adaptiveReduction\n'
    transform_merger(fixture)
    print(f"26491 TRANSFORM SELF-TEST PASS shortPostSha={SHORT_POST_SHA256}")


def apply(root: Path):
    for rel,expected in PRE.items():
        p=root/rel
        if not p.is_file(): fail("missing target "+rel)
        got=sha(p.read_bytes())
        if got!=expected: fail(f"exact 26490 pre-hash mismatch {rel} actual={got} expected={expected}")

    merger_path=root/MERGER; short_path=root/SHORT
    merger=merger_path.read_text(encoding="utf-8")
    short=short_path.read_text(encoding="utf-8")
    validate_short_pre(short)
    merger_new=transform_merger(merger)
    short_new=SHORT_26491
    validate_short_post(short_new)

    merger_path.write_text(merger_new,encoding="utf-8",newline="\n")
    short_path.write_text(short_new,encoding="utf-8",newline="\n")
    if sha(short_path.read_bytes())!=SHORT_POST_SHA256: fail("written short shader hash mismatch")
    validate_merger(merger_path.read_text(encoding="utf-8"))
    validate_short_post(short_path.read_text(encoding="utf-8"))
    print("26491 TRANSFORM PASS files=2 exposureOwner=p50_p90 shortHdr=joint_coherent_cfa")


if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1]=="--self-test": self_test()
    elif len(sys.argv)==2: validate_math(); validate_joint_policy_model(); apply(Path(sys.argv[1]))
    else: raise SystemExit("usage: transform_26491_adaptive_exposure_highlight_reconstruction_v2.py <repo-root> | --self-test")
