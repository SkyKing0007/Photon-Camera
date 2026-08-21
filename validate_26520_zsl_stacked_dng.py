#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
CFA='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
SHADER='app/src/main/assets/shaders/motionv2/dng_cfa_to_raw16_26520.glsl'
VERSION='app/version.properties'
CHANGED={CAPTURE,SAVER,HDRX,CFA,MERGER,SHADER}
FROZEN=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/res/xml/preferences.xml',
]
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def load(path:Path):
    spec=importlib.util.spec_from_file_location('a26520',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply-script',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args()
    base=ns.base.resolve(); cand=ns.candidate.resolve(); mod=load(ns.apply_script.resolve())
    bf,cf=files(base),files(cand)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==CHANGED, f'26520 runtime delta drift extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes()
    assert 'VERSION_NAME=0.9726519' in bf[VERSION].read_text()
    assert 'VERSION_BUILD=26519' in bf[VERSION].read_text()

    expected=mod.expected_map(base)
    for rel,new in expected.items():
        actual=cf[rel].read_text().replace('\r\n','\n').replace('\r','\n')
        assert actual==new, 'transform drift '+rel
    print('PASS: candidate exactly matches semantic six-path 26520 transform')

    for rel in FROZEN:
        assert rel in bf and rel in cf, 'missing frozen '+rel
        assert bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen drift '+rel
    matcher=cf[FROZEN[4]].read_text(); prefs=cf[FROZEN[-1]].read_text()
    stack=cf[FROZEN[0]].read_text(); fusion=cf[FROZEN[2]].read_text()
    assert 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' in matcher
    assert 'pref_motion_viewfinder_match_strength' in prefs
    assert 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in stack
    assert 'mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr' in stack
    assert 'mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr' in stack
    assert 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in fusion
    print('PASS: c4ff/SNR ABI/26519 matcher+slider frozen byte-for-byte')

    cap=cf[CAPTURE].read_text()
    assert 'mMotionTopUpMinimumFrames = Math.min(mMotionTopUpTargetFrames, 2);' in cap
    assert 'if (iris26486ReadyNow < 2)' not in cap
    assert 'if (actualCount < 2)' not in cap
    assert 'iris26486ReadyNow < mMotionTopUpMinimumFrames' in cap
    assert 'actualCount < mMotionTopUpMinimumFrames' in cap
    assert 'MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L' in cap
    assert 'postShutterNormalAdmission=false' in cap
    assert 'neighborFallback=false' in cap
    saver=cf[SAVER].read_text()
    assert 'batch.frames.isEmpty()' in saver
    assert 'requires at least two normal RAW frames' not in saver
    print('PASS: one normal is explicit-valid; >=2 requests retain two-normal minimum; grace is metadata-only')

    shader=cf[SHADER].read_text()
    for tok in ('IRIS_26520_DNG_RAW16_CODE_DOMAIN','r = (0,0), g = (1,0), b = (0,1), a = (1,1)',
                'layout(r16ui, binding = 0)','normalized * span + black'):
        assert tok in shader, tok
    cfa=cf[CFA].read_text()
    assert cfa.index('IRIS_26520_DNG_FUSED_BAYER_QUEUED') < cfa.index('IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_OWNER')
    assert 'mfsr_bayer_normalize' in cfa
    assert 'stackedDngRaw16Output' in cfa
    assert 'shortLongExcluded=true' in cfa
    hdrx=cf[HDRX].read_text()
    assert 'IRIS_26520_SHARED_NORMAL_BATCH_DNG' in hdrx
    assert 'sameNormalBatch=true' in hdrx
    assert 'shortLongExcludedFromDng=true' in hdrx
    assert 'secondAlignmentPass=false' in hdrx
    assert 'pyramidMergeForDng=false' in hdrx
    assert 'Motion V2 reference DNG buffer is null' not in hdrx
    assert 'IRIS_26480_DEFERRED_DNG_CAPTURED bytes=' not in hdrx
    assert 'iris26409V2.dngStackFrames != iris26409V2.inputFrames' in hdrx
    merger=cf[MERGER].read_text()
    assert 'stackedDngRaw16' in merger and 'dngStackFrames' in merger
    print('PASS: same admitted normal population feeds JPEG candidate and normal-only fused-Bayer DNG; no second alignment')

    patch=ns.patch.resolve(); psha=ns.patch_sha.resolve()
    assert patch.is_file() and psha.is_file()
    words=psha.read_text().strip().split()
    assert len(words)>=2 and words[0]==sha(patch)
    pt=patch.read_text()
    for rel in CHANGED: assert rel in pt, 'patch missing '+rel
    for rel in FROZEN: assert rel not in pt, 'frozen file leaked into patch '+rel
    print('PASS: rollback/audit patch covers exactly six approved runtime paths')

if __name__=='__main__':
    main()
