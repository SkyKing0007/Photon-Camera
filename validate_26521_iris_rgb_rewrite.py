#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

VERSION='app/version.properties'
CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
CFA='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
DNG_SHADER='app/src/main/assets/shaders/motionv2/dng_cfa_to_raw16_26520.glsl'
IRIS_SHADER='app/src/main/assets/shaders/motionv2/iris_fused_bayer_rgb_26521.glsl'

EXPECTED_RUNTIME_DELTA={
    CAPTURE,SAVER,HDRX,CFA,MERGER,DNG_SHADER,IRIS_SHADER
}
IDENTICAL_TO_26520={
    CAPTURE,SAVER,HDRX,MERGER,DNG_SHADER
}

FROZEN=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/res/xml/preferences.xml',
]

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def files(root:Path):
    return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}

def load(path:Path):
    spec=importlib.util.spec_from_file_location('apply26520',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply26520',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args()

    base=ns.base.resolve()
    cand=ns.candidate.resolve()
    bf,cf=files(base),files(cand)

    assert 'VERSION_NAME=0.9726519' in bf[VERSION].read_text()
    assert 'VERSION_BUILD=26519' in bf[VERSION].read_text()
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes(), \
        'version changed before guarded build block'

    changed={
        r for r in set(bf)|set(cf)
        if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])
    }
    assert changed==EXPECTED_RUNTIME_DELTA, \
        f'26521 runtime delta drift extra={sorted(changed-EXPECTED_RUNTIME_DELTA)} missing={sorted(EXPECTED_RUNTIME_DELTA-changed)}'
    print('PASS: 26521 runtime delta is exactly seven approved paths')

    # Build exact in-memory 26520 sibling from the same 26519 base.
    mod20=load(ns.apply26520.resolve())
    expected20=mod20.expected_map(base)
    for rel in IDENTICAL_TO_26520:
        actual=cf[rel].read_text().replace('\r\n','\n').replace('\r','\n')
        assert actual==expected20[rel], \
            '26521 diverged from 26520 capture/DNG semantics: '+rel
    print('PASS: one-frame/capture/DNG paths are byte-identical to the 26520 sibling transform')

    cap=cf[CAPTURE].read_text()
    hdr=cf[HDRX].read_text()
    cfa=cf[CFA].read_text()
    assert 'IRIS_26520_FROZEN_METADATA_GRACE' in cap
    assert 'iris26486ReadyNow < mMotionTopUpMinimumFrames' in cap
    assert 'actualCount < mMotionTopUpMinimumFrames' in cap
    assert 'postShutterNormalAdmission=false' in cap
    assert 'neighborFallback=false' in cap
    assert 'IRIS_26520_SHARED_NORMAL_BATCH_DNG' in hdr
    assert 'sameNormalBatch=true' in hdr
    assert 'shortLongExcludedFromDng=true' in hdr
    assert 'secondAlignmentPass=false' in hdr
    assert 'IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG' in cfa
    print('PASS: explicit one-normal + exact metadata grace + same-normal stacked DNG preserved')

    for rel in FROZEN:
        assert rel in bf and rel in cf, 'missing frozen owner '+rel
        assert bf[rel].read_bytes()==cf[rel].read_bytes(), \
            'unrelated/frozen owner drift '+rel
    matcher=cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'].read_text()
    prefs=cf['app/src/main/res/xml/preferences.xml'].read_text()
    stack=cf['app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'].read_text()
    fusion=cf['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'].read_text()
    assert 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' in matcher
    assert 'pref_motion_viewfinder_match_strength' in prefs
    assert 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in stack
    assert 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in fusion
    print('PASS: Wronski, dormant c4ff source, SNR ABI, PostPipeline, color/tone and 26519 viewfinder owner are frozen byte-for-byte')

    run=cfa.index('    public void Run() {')
    active=cfa[run:]
    for token in (
        'iris26501ContributeRgbFrame(',
        'iris26501RenderChromaGuide(',
        'iris26501RenderRgbCovariance(',
        'mfsr_spatial_rgb_normalize_26501',
        'IRIS_26501_SPATIAL_RGB_CONTRIBUTION_INVARIANT',
    ):
        assert token not in active, 'old Spatial RGB active token survived: '+token

    for token in (
        'IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER',
        'iris_fused_bayer_rgb_26521',
        'directC4ffSpatialAccumulator=false',
        'wronskiAlignmentPreserved=true',
        'wronskiBayerAccumulatorPreserved=true',
        'dngBranchAlreadyFrozenBeforeRgb=true',
    ):
        assert token in active, 'new Iris RGB owner missing '+token

    shader=cf[IRIS_SHADER].read_text()
    for token in (
        'IRIS_26521_INDEPENDENT_FUSED_BAYER_RGB',
        'edge-directed color-difference',
        'float greenAt',
        'float reconstructColor',
        'Extended-linear values above 1.0 are preserved',
    ):
        assert token in shader, token
    for forbidden in (
        'chromaEdgeNoiseSigmas',
        'chromaEdgeSigmaFloor',
        'opponentWeightAccumulator',
        'semanticAccumulator',
        'mfsr_spatial_rgb',
        'GlesMgc',
    ):
        assert forbidden not in shader, \
            'old Spatial RGB token in new Iris shader: '+forbidden
    print('PASS: only intended A/B variable is active RGB reconstruction owner')

    words=ns.patch_sha.read_text().strip().split()
    assert words and words[0]==sha(ns.patch), 'patch hash mismatch'
    patch=ns.patch.read_text()
    for rel in EXPECTED_RUNTIME_DELTA:
        assert rel in patch, 'rollback patch missing '+rel
    for rel in FROZEN:
        assert rel not in patch, 'frozen file leaked into rollback patch '+rel
    print('PASS: rollback/audit patch covers exactly the seven approved 26521 runtime paths')

if __name__=='__main__':
    main()
