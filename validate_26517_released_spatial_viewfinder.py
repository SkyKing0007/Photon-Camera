#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--released-root',required=True,type=Path); ap.add_argument('--apply-script',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path); ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args(); b=ns.base.resolve(); c=ns.candidate.resolve(); rr=ns.released_root.resolve()
    spec=importlib.util.spec_from_file_location('iris26517apply',ns.apply_script)
    mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)
    released=mod.released_owner_texts(rr)
    # Patch integrity.
    line=ns.patch_sha.read_text().strip(); expected,name=line.split(None,1); name=name.strip()
    assert Path(name).name==ns.patch.name
    assert sha(ns.patch)==expected
    assert ns.patch.stat().st_size>0
    # Exact deterministic delta, including exact renamed released-source owners.
    all_rel=set()
    for root in (b/'app/src/main',c/'app/src/main'):
        all_rel |= {str(p.relative_to(root.parent.parent.parent)).replace('\\\\','/') for p in root.rglob('*') if p.is_file()}
    changed=[]
    for rel in sorted(all_rel):
        bp=b/rel; cp=c/rel
        bs=bp.read_bytes() if bp.is_file() else None; cs=cp.read_bytes() if cp.is_file() else None
        if bs!=cs: changed.append(rel)
    assert set(changed)==set(mod.CHANGED), f'unexpected runtime delta: {changed}'
    for rel in mod.CHANGED:
        bp=b/rel; old=bp.read_text() if bp.is_file() else ''
        assert (c/rel).read_text()==mod.expected_text(rel,old,released), rel
    for rel,text in released.items():
        assert (c/rel).read_text()==text, rel+' is not exact released owner transform'
    # Prove the released owner is actually pre-Sabre 1.27.1 Spatial geometry.
    rs=(c/mod.NEW_STACKER_PATH).read_text(); rg=(c/mod.NEW_SHADERS_PATH).read_text()
    assert 'private val guideWidth = max(1, width / 4)' in rs
    assert 'private val guideHeight = max(1, height / 4)' in rs
    assert 'MgcRawProcessorPipeline' not in rs and 'MgcSabreRejectionTuning' not in rs
    assert 'FLOW_VARIATION_THRESHOLD = 9.88235261e-5f' in rs
    assert 'GlesMgc1271ReleasedSpatialShaders' in rs
    assert 'internal object GlesMgc1271ReleasedSpatialShaders' in rg
    # Current post-Sabre/Sabre owners stay byte-for-byte frozen beside the released copy.
    frozen=(
      'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreProcessor.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialDiagnosticGeometry.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialOutputExposure.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
      'app/src/main/assets/shaders/motionv2/color_transform.glsl',
      'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    )
    for rel in frozen:
        assert (b/rel).is_file() and (c/rel).is_file(), rel
        assert sha(b/rel)==sha(c/rel), 'frozen owner drifted: '+rel
    fusion=(c/mod.FUSION_PATH).read_text()
    assert fusion.count('IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER')==2
    assert 'if (mergeMethod == MgcMergeMethod.SPATIAL_RGB)' in fusion
    assert 'return GlesMgc1271ReleasedSpatialStacker(' in fusion
    assert fusion.count('return GlesMgcRawSpatialStacker(')==1
    matcher=(c/mod.MATCHER_PATH).read_text()
    assert 'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER' in matcher
    assert 'METER_BLACK = 0.003f' in matcher and 'METER_WHITE = 0.98f' in matcher
    assert matcher.count('eligibleDisplayedLuma(y)')==2
    assert 'y > 0.025f && y < 0.975f' not in matcher
    assert 'y > 1.0e-4f && y < 8.0f' not in matcher
    assert 'midtoneVotes=P35,P50,P65' in matcher
    assert 'private static final float MIN_EV = -4.0f;' in matcher
    assert 'private static final float MAX_EV = 4.0f;' in matcher
    # Version must remain the tested 26516 value until the builder's guarded version/build block.
    assert (c/'app/version.properties').read_text()==(b/'app/version.properties').read_text()
    print('PASS: exact 26517 runtime delta = Fusion route + released c4ff Spatial owner pair + matcher only')
    print('PASS: current 09c Spatial/Sabre, MGC metadata/noise/denoise, Short/Long, profile, render and UHDR owners frozen')
    print('PASS: released Spatial geometry and symmetric viewfinder population invariants proven')
    print('PRE-BUILD 26517 RELEASED-SPATIAL/VIEWFINDER NO-REGRESSION PROOF PASSED')
if __name__=='__main__': main()
