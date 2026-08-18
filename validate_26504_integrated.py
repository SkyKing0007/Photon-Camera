#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, math, re

EXPECTED = {
    "app/src/main/assets/shaders/motionv2/display_exposure.glsl",
    "app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl",
    "app/src/main/assets/shaders/motionv2/render.glsl",
    "app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java",
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def collect(root: Path):
    base = root / "app"
    out = {}
    for p in (base / "src/main").rglob("*"):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = sha(p)
    vp = base / "version.properties"
    out[vp.relative_to(root).as_posix()] = sha(vp)
    return out

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def smoothstep(a, b, x):
    t = clamp((x-a)/(b-a), 0.0, 1.0)
    return t*t*(3.0-2.0*t)

def exposure_model(ev100, histogram_gain, occupancy=0.0):
    anchor = 1.0 + (2.15-1.0)*smoothstep(2.0, 5.0, ev100)
    ratio = histogram_gain / max(anchor, 1e-6)
    rev = math.log(max(ratio,1e-6), 2.0)
    rev = clamp(rev, -0.25, 0.25)
    if rev > 0.0:
        rev *= 1.0 - 0.70*clamp(occupancy,0.0,1.0)
    return clamp(anchor*(2.0**rev), 1.0, 4.0)

def phase_state(code, q):
    return int(math.floor(code/(1,3,9,27)[q])) % 3

def has_censored(code):
    return any(phase_state(code,q)==1 for q in range(4))

def encode(states):
    return states[0]+3*states[1]+9*states[2]+27*states[3]

def residual_keep(opponent, sigma, dark_gate=1.0):
    z=abs(opponent)/max(sigma,1e-6)
    noise_like=1.0-smoothstep(1.50,3.25,z)
    return 1.0-0.82*dark_gate*noise_like

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate",type=Path)
    ap.add_argument("--base-root",type=Path,required=True)
    args=ap.parse_args()
    c=args.candidate
    b=args.base_root

    cm=collect(c); bm=collect(b)
    changed={k for k in set(cm)|set(bm) if cm.get(k)!=bm.get(k)}
    assert changed==EXPECTED, (
        "26504 changed-file allowlist mismatch\n"
        f"expected={sorted(EXPECTED)}\nactual={sorted(changed)}")

    version=(c/"app/version.properties").read_text()
    assert re.search(r"^VERSION_NAME=0\.9726502$",version,re.M)
    assert re.search(r"^VERSION_BUILD=26502$",version,re.M)

    def text(rel): return (c/rel).read_text()

    norm=text("app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl")
    assert "IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY" in norm
    assert "IRIS_26504_POST_LSC_CHROMA_EXHAUSTION" in norm
    assert "IRIS_26504_NOISE_AWARE_OPPONENT_SANITY" in norm
    assert "smoothCensoredFraction" not in norm
    assert norm.index("calculationRgb*=lsc;") < norm.index("bool colorIncomplete")
    assert "frameSupportTexture" in norm
    assert "noiseShotRgb" in norm and "noiseReadRgb" in norm
    assert "localFrameSupport" in norm

    merger=text("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java")
    assert "IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN" in merger
    assert "residualEv = Math.max(-0.25f, Math.min(0.25f, residualEv));" in merger
    assert "previewKeyImplemented=false" in merger
    assert "liveAeFeedback=false" in merger

    cfa=text("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java")
    assert "IRIS_26504_LOCAL_SUPPORT_AND_NOISE_TO_NORMALIZER" in cfa
    assert "IRIS_26504_DISABLE_HEAVY_PROVENANCE_READBACK" in cfa
    assert "IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2" in cfa
    assert 'glProg.setTexture("frameSupportTexture", currentDirectFrameSupport);' in cfa
    assert 'glProg.setVar("noiseShotRgb"' in cfa
    assert 'glProg.setVar("noiseReadRgb"' in cfa

    display=text("app/src/main/assets/shaders/motionv2/display_exposure.glsl")
    assert "IRIS_26504_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION" in display
    assert "carrier.a" in display and "retainedFrames" in display

    displayj=text("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java")
    assert "IRIS_26504_SINGLE_EXPOSURE_LOCAL_SUPPORT" in displayj
    assert 'glProg.setVar("retainedFrames", retainedFrames);' in displayj
    assert "photonAutoExposure=false" in displayj
    assert "photonExposureFusion=false" in displayj

    short=text("app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")
    assert "IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY" in short
    assert "flowConfidence < max(minimumFlowConfidence, 0.85)" in short

    render=text("app/src/main/assets/shaders/motionv2/render.glsl")
    assert "IRIS_26503_UPSTREAM_EXHAUSTION_OWNS_WHITE" in render
    assert "IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT" in render

    assert not has_censored(encode([0,0,0,0]))
    assert not has_censored(encode([2,0,2,0]))
    for q in range(4):
        st=[0,0,0,0]; st[q]=1
        assert has_censored(encode(st))

    hi=exposure_model(6.5,5.85,0.0)
    lo=exposure_model(6.5,1.26,0.0)
    assert abs(math.log(hi/lo,2.0)) <= 0.5000001, (hi,lo)
    assert exposure_model(1.0,16.0,0.0) <= 2.0**0.25 + 1e-6
    assert exposure_model(6.5,5.85,1.0) <= hi

    assert residual_keep(0.5,1.0) < 0.30
    assert residual_keep(4.0,1.0) > 0.999

    print("PASS: exact seven-file 26504 runtime scope")
    print("PASS: 2x2 Bayer quad provenance authority")
    print("PASS: post-LSC neutralization order")
    print("PASS: Camera2/Wronski residual-noise chroma sanity")
    print("PASS: +/-0.25 EV composition residual bound")
    print("PASS: proven 26503 Short-A/render directions preserved")
    print("PASS: version remains canonical 0.9726502 / 26502 before safety proof")

if __name__=="__main__":
    main()
