#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

MATCHER='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
PREFS='app/src/main/res/xml/preferences.xml'
STACKER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
DISPLAY='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java'
COLOR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'
VERSION='app/version.properties'
CHANGED={MATCHER,PREFS}

ABI_BLOCK = '''                /* IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE
                 * Released c4ff already computes bayerKernelTuning.referenceSnr and uses it for
                 * its Spatial kernel selection. Its historical RawStackResult predates the later
                 * process-local tuning-SNR fields. Export that same c4ff value into the newer ABI
                 * only; do not import post-Sabre Spatial tuning or Sabre TET attenuation math.
                 */
                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,
'''

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def load(path:Path):
    spec=importlib.util.spec_from_file_location('a26519',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--released-root',required=True,type=Path)
    ap.add_argument('--matcher-reference-script',required=True,type=Path)
    ap.add_argument('--apply-script',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args()
    base=ns.base.resolve(); cand=ns.candidate.resolve(); relroot=ns.released_root.resolve()
    mod=load(ns.apply_script.resolve())
    bf,cf=files(base),files(cand)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==CHANGED, f'26519 runtime delta drift extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes(), 'version changed before guarded build block'

    # Base must be the successful 26518 behavior.
    bm=bf[MATCHER].read_text()
    assert 'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER' in bm
    assert 'reason=distribution_mismatch' in bm
    assert 'MAX_QUANTILE_SPREAD_EV' in bm
    bs=bf[STACKER].read_text()
    for token in (
        'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE',
        'mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr',
        'mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr',
        'private val guideWidth = max(1, width / 4)',
    ): assert token in bs, '26518/c4ff base invariant missing: '+token

    # Prove c4ff owner is still exact released source + symbol rename + only the documented ABI block.
    upstream=(relroot/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text().replace('\r\n','\n').replace('\r','\n')
    upstream=upstream.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker').replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
    stripped=bs.replace('\r\n','\n').replace('\r','\n').replace(ABI_BLOCK,'',1)
    assert stripped==upstream, 'successful 26518 stacker is not exact c4ff + documented ABI block'
    print('PASS: 26518 pink-artifact-fixed c4ff owner remains exact and frozen')

    # Exact matcher generation from the historical 26516 solver reference.
    ref=mod.load_26516_reference(ns.matcher_reference_script.resolve())
    expected=mod.expected_matcher_from_26516(ref)
    actual=cf[MATCHER].read_text().replace('\r\n','\n').replace('\r','\n')
    assert actual==expected, '26519 matcher is not exact 26516 relationship + response calibration'
    for token in (
        'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE',
        'rawSolvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);',
        'solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);',
        'DEFAULT_MATCH_STRENGTH_PERCENT = 65.0f',
        'return trimMiddle(luma, 0.25f, 0.50f);',
        'candidateMidtoneBand=P25-P50',
    ): assert token in actual, token
    for forbidden in ('MAX_QUANTILE_SPREAD_EV','reason=distribution_mismatch','IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER'):
        assert forbidden not in actual, '26517 hard-rejection behavior survived: '+forbidden
    print('PASS: 26516 scene-adaptive solver restored; 65% scales +1.764EV reference to ~+1.147EV without fixed EV clamp')

    # Slider must be exactly one normal preference, eligible for existing per-lens JSON save/restore.
    prefs=cf[PREFS].read_text()
    assert prefs.count('pref_motion_viewfinder_match_strength')==1
    assert 'ns0:defaultValue="65"' in prefs
    assert 'ns1:maxValue="100"' in prefs and 'ns1:minValue="0"' in prefs
    assert 'Motion viewfinder match strength' in prefs
    assert not mod.KEY.startswith('pref_motion_iq_') and not mod.KEY.startswith('pref_tunable_')
    print('PASS: 0-100% slider is a normal setting and therefore participates in existing Save per lens settings behavior')

    # All IQ/capture/render owners except matcher are byte-frozen from successful 26518.
    for rel in (STACKER,SHADERS,FUSION,BRIDGE,DISPLAY,COLOR):
        assert rel in bf and rel in cf and bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen owner drift: '+rel
    print('PASS: c4ff, SNR ABI, bridge, color, display, and capture-adjacent owners frozen byte-for-byte')

    patch=ns.patch.resolve(); psha=ns.patch_sha.resolve()
    assert patch.is_file() and psha.is_file()
    words=psha.read_text().strip().split()
    assert len(words)>=2 and words[0]==sha(patch)
    pt=patch.read_text()
    assert MATCHER in pt and PREFS in pt
    assert 'GlesMgc1271ReleasedSpatialStacker.kt' not in pt
    assert 'PhotonMotionMgc1271Bridge.kt' not in pt
    print('PASS: rollback/audit patch covers only matcher + settings slider')

if __name__=='__main__':
    main()
