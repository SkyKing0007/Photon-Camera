#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, re
from pathlib import Path

STACKER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
CURRENT_STACKER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
MATCHER='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
VERSION='app/version.properties'
CHANGED={STACKER}

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def load(path:Path):
    spec=importlib.util.spec_from_file_location('a26518',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def renamed_c4ff(relroot:Path)->str:
    p=relroot/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
    s=p.read_text().replace('\r\n','\n').replace('\r','\n')
    s=s.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker')
    s=s.replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--released-root',required=True,type=Path); ap.add_argument('--apply-script',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path); ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args(); base=ns.base.resolve(); cand=ns.candidate.resolve(); relroot=ns.released_root.resolve(); mod=load(ns.apply_script.resolve())
    bf,cf=files(base),files(cand)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==CHANGED, f'26518 runtime delta drift extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes(), 'version changed before guarded build block'

    # Re-prove 26517 released source is exact c4ff with only the documented symbol renames.
    exact=renamed_c4ff(relroot)
    base_stacker=bf[STACKER].read_text().replace('\r\n','\n').replace('\r','\n')
    assert base_stacker==exact, '26517 released owner is not exact c4ff + symbol rename before ABI adapter'
    expected=mod.expected_text(base_stacker)
    actual=cf[STACKER].read_text().replace('\r\n','\n').replace('\r','\n')
    assert actual==expected, '26518 released stacker transform drift'
    stripped=actual.replace(mod.REPLACEMENT,mod.ANCHOR,1)
    assert stripped==exact, 'removing ABI export does not recover exact c4ff owner'
    print('PASS: released Spatial math is exact c4ff after removing the narrow result-ABI export')

    for token in (
        'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE',
        'mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr',
        'mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr',
        'private val guideWidth = max(1, width / 4)',
    ): assert token in actual, token
    for forbidden in ('MgcSpatialMergeTuning','MgcSabreResolveTuning','mgcSharpenAttenuationScale ='):
        assert forbidden not in actual, 'forbidden post-Sabre tuning import: '+forbidden
    print('PASS: c4ff referenceSnr exported to newer ABI; no Sabre/post-Sabre tuning math imported')

    # Everything around the released stacker remains byte-identical to the successful 26517 source.
    for rel in (SHADERS,FUSION,CURRENT_STACKER,BRIDGE,MATCHER):
        assert rel in bf and rel in cf and bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen byte drift: '+rel
    fusion=cf[FUSION].read_text(); bridge=cf[BRIDGE].read_text(); matcher=cf[MATCHER].read_text()
    assert 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in fusion
    assert 'GlesMgc1271ReleasedSpatialStacker(' in fusion
    assert 'mergeMethod == MgcMergeMethod.SPATIAL_RGB' in fusion
    assert 'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER' in matcher
    assert 'mgcDenoiseTuningSnr' in bridge, 'bridge no longer consumes MGC tuning SNR'
    assert 'missing/malformed MGC tuning SNR' in bridge, 'observed 26517 parity failure anchor drifted'
    print('PASS: 26517 routing, viewfinder solver, and bridge parity consumer are frozen byte-for-byte')

    # Patch must be an audit artifact for exactly the one source owner.
    patch=ns.patch.resolve(); psha=ns.patch_sha.resolve(); assert patch.is_file() and psha.is_file()
    line=psha.read_text().strip().split(); assert len(line)>=2 and line[0]==sha(patch)
    pt=patch.read_text(); assert STACKER in pt and 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in pt
    assert 'PhotonMotionMgc1271Bridge.kt' not in pt and 'GlesMgcRawSpatialStacker.kt' not in pt
    print('PASS: pre-write rollback/audit patch covers only released owner ABI export')

if __name__=='__main__': main()
