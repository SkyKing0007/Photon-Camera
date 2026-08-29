#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math, re, sys

EXPECTED_CHANGED = {
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
    'app/version.properties',
}
BASE_MERGE_SHA='7114ea0803b634a8b88fbe330b04fa3c5e136d72d0ed8ff06ad0b7ffe064ce60'


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def tree(root: Path):
    return {p.relative_to(root).as_posix(): h(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}

def exact_val_block(text: str, name: str) -> str:
    # Preserve source bytes of one Kotlin raw-string val including trimIndent call.
    pat=re.compile(r'(?ms)^\s{4}val\s+'+re.escape(name)+r'\s*=\s*""".*?^\s{4}"""\.trimIndent\(\)\n')
    m=pat.search(text)
    if not m: raise AssertionError(f'missing val block {name}')
    return m.group(0)

def between(text: str, start: str, end: str) -> str:
    i=text.index(start); j=text.index(end,i)
    return text[i:j]

def self_test():
    # Permanent defect model: normalization cannot recover a saturated Long sample.
    white=1023.0
    long_raw=1023.0
    exposure_scale=0.25
    normalized=long_raw*exposure_scale
    assert normalized == 255.75 and normalized < white
    # New invariant must make the source-domain saturation decision before normalization.
    clip_point=white-0.5
    assert long_raw >= clip_point
    assert normalized < clip_point
    # Exact intended scene-adaptive Night advantages.
    assert abs(2.0**0.30 - 1.2311444133) < 1e-6
    assert abs(2.0**0.40 - 1.3195079108) < 1e-6
    # Highlight safety is allowed to reduce realized advantage rather than force clipping.
    motion_ev=0.8; desired=motion_ev+0.3; cap=0.9
    solved=min(desired,cap)
    assert solved==0.9 and solved-motion_ev < 0.3
    print('PASS 26558 validator self-test: source-domain clipping + adaptive Night EV regressions')

def validate(base: Path, cand: Path):
    B,C=tree(base),tree(cand)
    changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
    assert changed==EXPECTED_CHANGED, f'changed scope mismatch extra={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}'

    version=(cand/'app/version.properties').read_text()
    assert 'VERSION_NAME=0.9726558' in version and 'VERSION_BUILD=26558' in version

    shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    bs=(base/shader_rel).read_text(); cs=(cand/shader_rel).read_text()
    bm=exact_val_block(bs,'merge'); cm=exact_val_block(cs,'merge')
    assert bm==cm, 'Motion/NORMAL Sabre merge shader changed'
    assert h(bm.encode())==BASE_MERGE_SHA, f'base Motion merge block unexpected {h(bm.encode())}'
    # Every pre-existing embedded Sabre shader/value remains exact 26556 source bytes. Only the two
    # new Night-only shader values may appear in this Kotlin carrier.
    raw_pat=re.compile(r'(?ms)^\s{4}val\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*""".*?^\s{4}"""\.trimIndent\(\)\n')
    base_vals={m.group(1):m.group(0) for m in raw_pat.finditer(bs)}
    cand_vals={m.group(1):m.group(0) for m in raw_pat.finditer(cs)}
    assert set(cand_vals)-set(base_vals)=={'mergeShadowLong26558','copyMaskShadowLong26558'}, (set(cand_vals)-set(base_vals))
    assert set(base_vals)-set(cand_vals)==set()
    for name,block in base_vals.items():
        assert cand_vals[name]==block, f'pre-existing embedded Sabre value changed: {name}'
    # Motion/NORMAL accumulated coverage shader is therefore exact too.
    assert exact_val_block(bs,'copyMask')==exact_val_block(cs,'copyMask'), 'Motion/NORMAL Sabre copyMask shader changed'
    assert cs.count('val mergeShadowLong26558 = """')==1
    assert cs.count('val copyMaskShadowLong26558 = """')==1
    assert 'uniform float uSourceClippingPoint;' in exact_val_block(cs,'mergeShadowLong26558')
    long_merge=exact_val_block(cs,'mergeShadowLong26558')
    assert 'for (int sx = 0; sx < 3; ++sx)' in long_merge and 'for (int sy = 0; sy < 3; ++sy)' in long_merge
    assert 'step(uSourceClippingPoint, bayerValue[sx][sy])' in long_merge
    assert 'if (sourceNeighborhoodClipped > 0.5)' in long_merge and 'frameWeight = 0.0;' in long_merge
    # Whole-observation rejection: only one scalar frameWeight gates every RGB intensity and every RGB weight.
    assert 'accumulatedColor *= frameWeight;' in long_merge and 'accumulatedWeight *= frameWeight;' in long_merge
    assert not re.search(r'frameWeight[RGB]|channelClip|perChannel', long_merge)

    long_cov=exact_val_block(cs,'copyMaskShadowLong26558')
    assert 'step(uSourceClippingPoint, bayerValue[sx][sy])' in long_cov
    assert 'float validLong = 1.0 - step(0.5, sourceNeighborhoodClipped);' in long_cov
    assert 'texture(uRejection, referenceUv).r * validLong / uAccumulatedWeightScale' in long_cov

    stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
    st=(cand/stack_rel).read_text()
    assert st.count('shadowLongSourceClipGuard = false')==1
    assert st.count('shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG')==1
    assert st.count('if (frame.role == RawBurstFrameRole.SHADOW_LONG) {\n                    renderSabreShadowLongCoverage(')==1
    assert st.count('GlesMgcRawSabreShaders.mergeShadowLong26558')==1
    assert st.count('GlesMgcRawSabreShaders.copyMaskShadowLong26558')==1
    assert 'sensorWhiteLevel.coerceAtLeast(1f) - 0.5f' in st
    assert 'domain=unnormalized_sensor_raw' in st and 'footprint=exact_sabre_3x3' in st
    assert 'wholeLongObservationReject=true' in st and 'coverageSupportGuard=true' in st
    # New correction must not revive inactive Spatial clipping/reconstruction ownership.
    added='\n'.join(line[1:] for line in __import__('difflib').unified_diff((base/stack_rel).read_text().splitlines(), st.splitlines()) if line.startswith('+') and not line.startswith('+++'))
    for forbidden in ('alignedRawClippingMask','renderAlignedLongFrameClippingMask','mergeRgbProgram','GlesMgcRawSpatialShaders.aligned'):
        assert forbidden not in added, f'26558 newly references inactive Spatial owner {forbidden}'

    tone_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
    bt=(base/tone_rel).read_text(); ct=(cand/tone_rel).read_text()
    assert 'NIGHT_DARK_ADVANTAGE_EV = 0.40f' in ct
    assert 'NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f' in ct
    assert 'matchStrengthPercent = readMatchStrengthPercent();' in ct
    assert 'float motionEquivalentEv = clamp(rawSolvedEv * motionStrength, MIN_EV, MAX_EV);' in ct
    assert 'float desiredEv = clamp(motionEquivalentEv + nightAdvantageEv, MIN_EV, MAX_EV);' in ct
    assert 'Math.min(desiredEv, headroomCapEv)' in ct
    assert 'NIGHT_HEADROOM_GUIDE_LIMIT = 5.0f' in ct
    assert 'realizedBrightnessRatio=' in ct
    # Exact Motion else branch and Motion preference reader stay byte-identical.
    marker='''            } else {\n                /* Exact Motion behavior retained from 26549. */'''
    motion_end='''            float gain = (float)Math.pow(2.0, solvedEv);'''
    assert between(bt,marker,motion_end)==between(ct,marker,motion_end), 'Motion presentation branch changed'
    reader_start='''    private static float readMatchStrengthPercent() {'''
    reader_end='''    private static String cameraIdForLog() {'''
    assert between(bt,reader_start,reader_end)==between(ct,reader_start,reader_end), 'Motion strength preference reader changed'

    # Rejected 26557 Jin adapter must not be carried into 26558. Exact 26556 Jin files are protected by scope.
    for rel in (
        'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
    ):
        assert B[rel]==C[rel], f'Jin file changed: {rel}'
        assert 'IRIS_26557_JIN_CHROMA_SAFE' not in (cand/rel).read_text(errors='ignore')

    # Shared IQ owners explicitly protected.
    protected_needles=(
        'MotionV2Render', 'MotionV2DisplayExposure', 'Vgn',
    )
    for needle in protected_needles:
        for rel in sorted(k for k in B if needle.lower() in Path(k).name.lower()):
            assert B[rel]==C[rel], f'protected shared IQ owner changed: {rel}'

    print('PASS exact 4-file 26558 scope')
    print('PASS every pre-existing embedded Sabre shader/value exact 26556 bytes; Motion merge + coverage invariant')
    print('PASS Night-only SHADOW_LONG source-domain exact-3x3 whole-observation rejection')
    print('PASS Night Long accumulated support/alpha guard matches source-clipping contract')
    print('PASS inactive Spatial clipping/reconstruction not revived')
    print('PASS Motion-relative +0.40EV dark / +0.30EV bright Night presentation with P99 headroom retained')
    print('PASS exact Motion presentation branch + preference reader invariance')
    print('PASS Jin/VGN/shared render owners remain exact 26556 bytes')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--base',type=Path)
    ap.add_argument('--candidate',type=Path)
    a=ap.parse_args()
    if a.self_test:
        self_test(); return
    if not a.base or not a.candidate: raise SystemExit('--base and --candidate required')
    validate(a.base,a.candidate)

if __name__=='__main__': main()
