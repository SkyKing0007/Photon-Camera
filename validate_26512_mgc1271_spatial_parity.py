#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, re, sys
from pathlib import Path

ADAPTER_CHANGED={
'app/src/main/cpp/CMakeLists.txt',
'app/src/main/cpp/mgc1271_upstream/CMakeLists.txt',
'app/src/main/cpp/mgc1271_upstream/mgc1271_non_arm64_stub.cpp',
'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackRuntimeDebug.kt',
'app/src/main/java/com/hinnka/mycamera/raw/RawMetadata.kt',
'app/src/main/java/com/hinnka/mycamera/utils/LargeDirectBuffer.kt',
'app/src/main/java/com/hinnka/mycamera/utils/PLog.kt',
'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
}
PROTECTED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
]

def h(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(text:str,needle:str,label:str):
    if needle not in text: raise AssertionError(f'{label}: missing {needle!r}')
def forbid(text:str,needle:str,label:str):
    if needle in text: raise AssertionError(f'{label}: forbidden {needle!r}')
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}

def load_importer(path:Path):
    spec=importlib.util.spec_from_file_location('mgcimport',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def expected_import_targets(imp):
    out=set()
    for n in imp.PROCESSOR: out.add(f'app/src/main/java/com/hinnka/mycamera/processor/{n}')
    out.update(imp.OTHER); out.update(imp.ASSETS)
    # Entire upstream static dir copied beneath isolated owner.
    return out

def compare_upstream(cand:Path,up:Path,imp):
    head=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()
    assert head==imp.PINNED,(head,imp.PINNED)
    pairs=[]
    for n in imp.PROCESSOR:
        src=up/'app/src/main/java/com/hinnka/mycamera/processor'/n
        dst=cand/'app/src/main/java/com/hinnka/mycamera/processor'/n; pairs.append((src,dst))
    for rel in imp.OTHER+imp.ASSETS:
        pairs.append((up/rel,cand/rel))
    for src,dst in imp.MAPPED:
        pairs.append((up/src,cand/dst))
    pairs.append((up/'app/src/main/cpp/mgc_strength_map_scaler.cpp',cand/'app/src/main/cpp/mgc1271_upstream/mgc_strength_map_scaler.cpp'))
    srcdir=up/'app/src/main/cpp/mgc_denoise_static'; dstdir=cand/'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static'
    for src in sorted(srcdir.rglob('*')):
        if src.is_file(): pairs.append((src,dstdir/src.relative_to(srcdir)))
    for src,dst in pairs:
        assert src.is_file(),f'missing upstream {src}'
        assert dst.is_file(),f'missing imported {dst}'
        assert src.read_bytes()==dst.read_bytes(),f'upstream byte drift {dst.relative_to(cand)}'
    print(f'PASS: {len(pairs)} imported 1.27.1 files are byte-identical to pinned upstream')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',type=Path,required=True); ap.add_argument('--candidate',type=Path,required=True); ap.add_argument('--importer',type=Path,required=True); ap.add_argument('--upstream',type=Path)
    a=ap.parse_args(); base=a.base.resolve(); cand=a.candidate.resolve(); imp=load_importer(a.importer.resolve())
    bf,cf=files(base),files(cand)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or h(bf[r])!=h(cf[r])}
    imported=set()
    if a.upstream:
        compare_upstream(cand,a.upstream.resolve(),imp)
        for n in imp.PROCESSOR: imported.add(f'app/src/main/java/com/hinnka/mycamera/processor/{n}')
        imported.update(imp.OTHER); imported.update(imp.ASSETS)
        imported.update(dst for _,dst in imp.MAPPED)
        imported.add('app/src/main/cpp/mgc1271_upstream/mgc_strength_map_scaler.cpp')
        srcdir=a.upstream.resolve()/'app/src/main/cpp/mgc_denoise_static'
        imported.update('app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/'+p.relative_to(srcdir).as_posix() for p in srcdir.rglob('*') if p.is_file())
    expected=ADAPTER_CHANGED|imported
    assert changed==expected,'unexpected candidate delta:\n extra='+repr(sorted(changed-expected))+'\n missing='+repr(sorted(expected-changed))
    print(f'PASS: exact candidate delta = {len(ADAPTER_CHANGED)} adapter paths + {len(imported)} pinned-upstream paths')
    for r in PROTECTED:
        assert r in bf and r in cf and bf[r].read_bytes()==cf[r].read_bytes(),f'protected 26507 drift: {r}'
    print('PASS: Wronski/GLTexture/post/UHDR/JPEG protected files remain byte-identical to successful 26507')

    hdrx=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    img=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java').read_text()
    cm=(cand/'app/src/main/cpp/mgc1271_upstream/CMakeLists.txt').read_text()
    debug=(cand/'app/src/main/java/com/hinnka/mycamera/processor/RawStackRuntimeDebug.kt').read_text()
    need(hdrx,'PhotonMotionMgc1271Bridge.reconstruct(','Hdrx parity route')
    forbid(hdrx,'MotionV2CfaReconstruction.reconstruct(','Hdrx parity route')
    need(bridge,'GlesMgcRawFusion(','bridge exact fusion entry')
    forbid(bridge,'GlesMgcRawSpatialStacker(','bridge must not bypass fusion scheduler')
    need(bridge,'mergeMethod = MgcMergeMethod.SPATIAL_RGB','Spatial RGB lock')
    need(bridge,'MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT','default denoise lock')
    need(bridge,'lumaStrengthScale = 1.0f','exact default luma')
    need(bridge,'chromaStrengthScale = 1.0f','exact default chroma')
    need(bridge,'System.loadLibrary("my-native-lib")','native ABI contract')
    need(bridge,'Build.SUPPORTED_ABIS.any { it == "arm64-v8a" }','arm64 AOT gate')
    need(bridge,'val mgcBase = inputImages.first()','1.27.1 base scheduling')
    need(bridge,'reference.width,\n                reference.height,','26507 display-gain stride contract')
    forbid(bridge,'sortedBy','no Wronski order policy')
    need(bridge,'frame.motionV2NoiseProfileSource == "CAMERA2_BASE_FRAME"','Camera2 base noise semantics')
    need(bridge,'forceOpaqueHalfAlpha','retire Wronski alpha support')
    need(bridge,'MGC PARITY ARCHITECTURE INVALID','hard parity failure')
    forbid(bridge,'MotionV2CfaReconstruction','no hybrid reconstruction call')
    forbid(bridge,'MotionV2WronskiAlignment','no Wronski inside owner')
    need(debug,'val mgcSpatialDiagnosticMode: MgcSpatialDiagnosticMode\n        get() = MgcSpatialDiagnosticMode.NONE','production diagnostic hardlock')
    need(cap,'/* updateMotionV2ExposureAuthority(result); intentionally dormant */','AE dormancy')
    need(cap,'setMotionV2PlaneLayout(','RAW stride transport')
    need(img,'motionV2PlaneRowStrideBytes','RAW row stride field')
    need(img,'motionV2PlanePixelStrideBytes','RAW pixel stride field')
    print('PASS: active Motion route is pinned MGC Fusion -> Spatial RGB -> propagated SPATIAL_DEFAULT, with no hybrid fallback')

    need(cm,'add_library(my-native-lib SHARED','isolated native library')
    need(cm,'mgc_full_resolution_denoise_jni.cpp','full denoise JNI')
    need(cm,'mgc_spatial_strength_jni.cpp','strength JNI')
    need(cm,'3ee5c92d2b830448de6270ec0c71ac64a484885a6bd7440d1c53f8695afc55ec','denoise capsule hash')
    need(cm,'769d656725b445c356b9f3e44341e101806bb201fcd2e5681c0ab92173a68c9a','demoire capsule hash')
    need(cm,'if(NOT ANDROID_ABI STREQUAL "arm64-v8a")','non-arm64 isolation')
    print('PASS: isolated native owner contains exact arm64 MGC AOT hash gates and no Photon GLTexture dependency')

    runtime='\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
    for bad in ['IRIS_26509_','IRIS_26510_','IRIS_26511_']:
        forbid(runtime,bad,'rejected runtime exclusion')
    forbid(runtime,'mfsr_spatial_rgb_vgn_chroma_26510','rejected VGN exclusion')
    print('PASS: rejected 26509/26510/26511 runtime code is absent')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('VALIDATION FAILED:',e,file=sys.stderr); raise
