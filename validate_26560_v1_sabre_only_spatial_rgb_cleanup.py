#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re

MODIFIED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/res/values/arrays.xml',
'app/src/main/res/values/strings.xml',
'app/src/main/res/xml/preferences.xml',
'app/version.properties',
}
DELETED={
'app/src/main/assets/shaders/motionv2/alignment_global_score.glsl',
'app/src/main/assets/shaders/motionv2/alignment_guide.glsl',
'app/src/main/assets/shaders/motionv2/alignment_local_flow.glsl',
'app/src/main/assets/shaders/motionv2/cfa_reconstruct_accumulate.glsl',
'app/src/main/assets/shaders/motionv2/cfa_reconstruct_init.glsl',
'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
'app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_26488_stage_diag.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_26489_bayer_diag_sample.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulator_clear.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bayer_normalize.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_mgc_reference_gray.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_pyramid_gaussian.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl',
'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
}
EXPECTED_CHANGED=MODIFIED|DELETED

PROTECTED=(
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
)
DELETED_CLASSES=(
'GlesIris26521SpatialRgbStacker','GlesMgc1271ReleasedSpatialStacker','GlesMgc1271ReleasedSpatialShaders',
'IrisNightMgc1271Bridge','MotionV2CfaReconstruction','MotionV2WronskiAlignment','MotionV2Alignment',
'MotionV2MgcSourceExposure','MotionV2HighlightChromaReliability',
)


def h(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def tree(root:Path):
    return {p.relative_to(root).as_posix():h(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}

def self_test():
    assert len(MODIFIED)==13 and len(DELETED)==45 and len(EXPECTED_CHANGED)==58
    assert 'app/src/main/assets/shaders/motionv2/render.glsl' not in EXPECTED_CHANGED
    assert all('super_res' not in p.lower() for p in DELETED), 'Super Res UI/state must not be deleted'
    assert all(p.startswith('app/') for p in EXPECTED_CHANGED)
    print('PASS 26560 self-test: exact 13 modified + 45 deleted allowlist; Super Res UI/state excluded')

def validate(base:Path,cand:Path):
    B,C=tree(base),tree(cand)
    changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
    assert changed==EXPECTED_CHANGED, f'changed scope mismatch extra={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}'
    for rel in DELETED:
        assert rel in B and rel not in C, f'deletion mismatch {rel}'
    for rel in MODIFIED:
        assert rel in B and rel in C and B[rel]!=C[rel], f'modification mismatch {rel}'
    for rel in PROTECTED:
        assert rel in B and rel in C and B[rel]==C[rel], f'protected Sabre/shared owner changed: {rel}'

    version=(cand/'app/version.properties').read_text()
    assert 'VERSION_NAME=0.9726560' in version and 'VERSION_BUILD=26560' in version
    assert 'VERSION_NAME=0.9726559' not in version and 'VERSION_BUILD=26559' not in version

    fusion=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
    assert fusion.count('GlesIris26545SabreProcessor(')==1
    assert 'GlesIris26521SpatialRgbStacker' not in fusion
    assert 'MgcMergeMethod' not in fusion and 'MgcSpatialOutputMode' not in fusion
    assert 'allowShadowLong = allowSabreShadowLong' in fusion

    settings=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
    assert 'KEY_RECONSTRUCTION' not in settings and 'enum Reconstruction' not in settings
    assert 'spatial_rgb' not in settings.lower()

    bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    for forbidden in ('IrisMotionSettings.Reconstruction','MOTION_V2_RECONSTRUCTION_SPATIAL_RGB',
                      'MgcMergeMethod.SPATIAL_RGB','publishSpatialReliability','gateSuperResDetailByNativeReliability'):
        assert forbidden not in bridge, forbidden
    assert 'parameters.motionV2ReconstructionOwner = Parameters.MOTION_V2_RECONSTRUCTION_SABRE' in bridge
    assert 'allowSabreShadowLong = parameters.irisNightActive' in bridge
    assert 'parameters.motionV2SuperResOutputScale = 1f' in bridge
    assert 'superResRequested=${parameters.motionV2SuperResOutputEnabled}' in bridge
    assert 'futureBackend=SABRE_SR' in bridge
    assert 'result.sabreSelected = true' in bridge
    assert 'MgcFullResolutionDenoise.Pass.SABRE_DEFAULT' in bridge
    assert 'parameters.motionV2MgcSourceExposureGain = 1.0f' in bridge

    post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
    assert 'MOTION_V2_RECONSTRUCTION_SPATIAL_RGB' not in post
    assert 'new MotionV2MgcSourceExposure()' not in post
    assert 'new MotionV2HighlightChromaReliability()' not in post
    assert post.count('owner=SABRE carrier=RESOLVE_SABRE_LINEAR_RGB')==2
    assert 'NIGHT_SPATIAL_RGB_POST_ENTRY' not in post

    hdrx=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    assert 'MOTION_V2_RECONSTRUCTION_SPATIAL_RGB' not in hdrx
    assert 'MGC_SPATIAL_RGB_RGBA32F' not in hdrx
    assert '26560 Sabre-only Motion returned a non-Sabre reconstruction result' in hdrx

    params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
    assert 'MOTION_V2_RECONSTRUCTION_SPATIAL_RGB' not in params
    assert 'MOTION_V2_RECONSTRUCTION_SABRE = 2' in params, 'preserve proven Sabre owner numeric value'
    assert 'motionV2SpatialReliability' not in params

    pref=(cand/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
    assert 'setInitial(SCOPE_GLOBAL, "pref_iris_motion_reconstruction"' not in pref
    assert 'map.putIfAbsent("pref_iris_motion_reconstruction"' not in pref
    assert 'LEGACY_IRIS_RECONSTRUCTION_KEY' in pref and 'continue;' in pref
    assert 'COMMON_KEYS.add(Key.KEY_IRIS_SUPER_RES.mValue);' in pref
    assert 'setInitial(SCOPE_GLOBAL, Key.KEY_IRIS_SUPER_RES, false);' in pref
    assert 'public static boolean isIrisSuperResOn()' in pref and 'public static void setIrisSuperRes(boolean value)' in pref

    xml=(cand/'app/src/main/res/xml/preferences.xml').read_text()
    arrays=(cand/'app/src/main/res/values/arrays.xml').read_text()
    strings=(cand/'app/src/main/res/values/strings.xml').read_text()
    assert 'pref_iris_motion_reconstruction' not in xml
    assert 'iris_motion_reconstruction_entries' not in arrays and 'iris_motion_reconstruction_entryvalues' not in arrays
    assert 'iris_motion_reconstruction' not in strings
    assert '<string name="super_res">Super Res</string>' in strings
    assert '<string name="pref_iris_super_res_key">pref_iris_super_res</string>' in strings

    # Prove deleted shader assets have no remaining literal loaders/imports by filename.
    textual=[]
    for p in (cand/'app').rglob('*'):
        if p.is_file() and p.suffix in {'.java','.kt','.glsl','.xml','.cpp','.c','.h','.gradle','.kts','.cmake','.txt'}:
            try:textual.append((p,p.read_text(errors='ignore')))
            except Exception:pass
    for rel in DELETED:
        if '/assets/shaders/' in rel:
            name=Path(rel).name
            assert not any(name in text for _,text in textual), f'deleted shader still referenced: {name}'
    # Deleted class names may remain only in untouched historical comments in protected shared files.
    live_mod_text='\n'.join((cand/r).read_text(errors='ignore') for r in MODIFIED if (cand/r).suffix in {'.java','.kt'})
    for name in DELETED_CLASSES:
        assert name not in live_mod_text, f'deleted class still referenced by modified live owner: {name}'

    # Permanent javac regression from V1.3: exact ByteBuffer qualification must remain.
    cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    assert 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' in cc

    print('PASS exact 58-file 26560 scope (13 modified / 45 deleted / 0 added)')
    print('PASS Motion + Night top-level reconstruction is Sabre-only')
    print('PASS Spatial-RGB selector/global/per-lens authority removed')
    print('PASS obsolete Spatial-RGB/Wronski-hybrid classes and shaders removed with zero live modified-owner references')
    print('PASS Super Res switch/UI/state retained; 26560 backend pinned to Sabre native-grid 1x')
    print('PASS protected Sabre/VGN/Resolve/Jin/render/Night owners byte-identical to 26559')
    print('PASS 26558 Night Long admission gate preserved; Motion Long admission remains off')
    print('PASS permanent ByteBuffer javac regression preserved')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--base',type=Path); ap.add_argument('--candidate',type=Path); a=ap.parse_args()
    if a.self_test:self_test();return
    if not a.base or not a.candidate:raise SystemExit('--base and --candidate required')
    validate(a.base,a.candidate)
if __name__=='__main__': main()
