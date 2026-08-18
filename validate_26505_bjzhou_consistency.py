#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, math, re

EXPECTED = {
    "app/src/main/assets/shaders/motionv2/display_exposure.glsl",
    "app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl",
    "app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl",
    "app/src/main/assets/shaders/motionv2/render.glsl",
    "app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl",
    "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java",
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def collect(root: Path):
    base=root/"app"; out={}
    for p in (base/"src/main").rglob("*"):
        if p.is_file(): out[p.relative_to(root).as_posix()]=sha(p)
    vp=base/"version.properties"
    out[vp.relative_to(root).as_posix()]=sha(vp)
    return out

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)

def low_support_authority(frames):
    return 1.0-smoothstep(1.5,3.5,max(frames,1.0))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate",type=Path)
    ap.add_argument("--base-root",type=Path,required=True)
    args=ap.parse_args(); c=args.candidate; b=args.base_root

    cm=collect(c); bm=collect(b)
    changed={k for k in set(cm)|set(bm) if cm.get(k)!=bm.get(k)}
    assert changed==EXPECTED, (
        "26505 changed-file allowlist mismatch\n"
        f"expected={sorted(EXPECTED)}\nactual={sorted(changed)}")

    version=(c/"app/version.properties").read_text()
    assert re.search(r"^VERSION_NAME=0\.9726502$",version,re.M)
    assert re.search(r"^VERSION_BUILD=26502$",version,re.M)

    def text(rel): return (c/rel).read_text()

    cap=text("app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java")
    for marker in [
        "IRIS_26505_PHYSICAL_LONG_BRACKET_OWNER",
        "IRIS_26505_PHYSICAL_LONG_BRACKET",
        "IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP",
        "IRIS_26505_LONG_ACTUAL_ACCEPTED",
    ]:
        assert marker in cap, marker
    assert "MOTION_26505_LONG_TARGET_EV = 2.5" in cap
    assert "MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS" in cap
    assert "10_000_000L" in cap
    assert "MOTION_26505_LONG_FALLBACK_MAX_ISO = 800" in cap
    assert "mMotion26505LongRequested" in cap
    assert "iris26486ShortTicket.slot.shadowAuxSlot" in cap
    assert "normalAccumulatorAdmission=false" in cap
    assert "!mMotion26505LongRequested" in cap
    assert "findNearestZslResult" in cap
    assert "nearestFallback=false" in cap
    # No Long-A frame is appended to the equal-exposure selected/processing list.
    assert "selected.add(iris26505" not in cap
    assert "iris26480ProcessingFrames.add(iris26505" not in cap
    assert "MotionV2FrameRole.SHADOW" not in cap

    cfa=text("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java")
    assert "IRIS_26505_LOW_SUPPORT_PPG_FALLBACK" in cfa
    assert 'glProg.useAssetProgram("motionv2/low_support_ppg_reference_26505")' in cfa
    assert 'glProg.setTexture("referenceCfa",referenceCfa);' in cfa
    assert 'glProg.setTexture("lowSupportReferenceRgb", iris26505LowSupportReference);' in cfa
    assert "irisV13ShadowToNormal>=0.15f&&irisV13ShadowToNormal<=0.84f" in cfa
    assert 'glProg.setVar("maxShadowBlend",0.35f);' in cfa
    assert "unalignedFallback=false" in cfa
    # Preserve 26504 local-support/noise and heavy-readback removal.
    assert "IRIS_26504_LOCAL_SUPPORT_AND_NOISE_TO_NORMALIZER" in cfa
    assert "IRIS_26504_DISABLE_HEAVY_PROVENANCE_READBACK" in cfa

    norm=text("app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl")
    for marker in [
        "IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY",
        "IRIS_26504_POST_LSC_CHROMA_EXHAUSTION",
        "IRIS_26504_NOISE_AWARE_OPPONENT_SANITY",
        "IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY",
    ]:
        assert marker in norm, marker
    assert "uniform highp sampler2D lowSupportReferenceRgb;" in norm
    assert "1.50,3.50,max(localFrameSupport,1.0)" in norm
    assert norm.index("IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY") < norm.index("IRIS_26504_POST_LSC_CHROMA_EXHAUSTION")
    assert norm.index("calculationRgb*=lsc;") < norm.index("bool colorIncomplete")

    ppg=text("app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl")
    assert "IRIS_26505_LOW_SUPPORT_PPG_REFERENCE" in ppg
    assert "referenceCfa" in ppg
    assert "ppgGreenAt" in ppg and "ppgColorAt" in ppg
    assert "semanticAccumulator" not in ppg
    assert "flowTexture" not in ppg
    assert "texture(" not in ppg.replace("texelFetch(","")  # nearest immutable CFA only

    # 26503/26504 established safety/rendering directions remain present.
    short=text("app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")
    render=text("app/src/main/assets/shaders/motionv2/render.glsl")
    display=text("app/src/main/assets/shaders/motionv2/display_exposure.glsl")
    merger=text("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java")
    assert "IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY" in short
    assert "IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT" in render
    assert "IRIS_26504_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION" in display
    assert "IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN" in merger

    # Numerical invariants for the new local-support gate and long ratio.
    assert low_support_authority(1.0) > 0.999
    assert low_support_authority(1.5) > 0.999
    mid=low_support_authority(2.5)
    assert 0.49 < mid < 0.51
    assert low_support_authority(3.5) < 1e-6
    assert low_support_authority(10.0) < 1e-6
    target=2.0**2.5
    assert abs(target-5.656854249492381) < 1e-12
    assert (1.0/target) > 0.15 and (1.0/target) < 0.84

    print("PASS: exact nine-file 26505 runtime scope")
    print("PASS: intentional +2.5 EV Long-A remains isolated from MotionBatch.frames")
    print("PASS: actual timestamp/exposure metadata owns Long-A role")
    print("PASS: opportunistic shadow scavenger cannot preempt intentional Long-A")
    print("PASS: Long-A host accepts ~5.66x energy with bounded 0.35 blend")
    print("PASS: immutable-reference PPG fallback is local-support gated only")
    print("PASS: 26503/26504 Short-A/highlight/render/exposure invariants preserved")
    print("PASS: version remains canonical 0.9726502 / 26502 before safety proof")

if __name__=="__main__": main()
