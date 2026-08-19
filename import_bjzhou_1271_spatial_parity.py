#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, os, shutil, subprocess, sys
from pathlib import Path

PINNED='09c76e57e8f01a5a8fc536ab41fc80ba642d4042'
PROCESSOR=[
'BentoFallbackTopology.kt',
'CalibratedRawNoiseProfile.kt',
'DenoiseStrength.kt',
'GlesComputeWorkGroup.kt',
'GlesGpuCompletion.kt',
'GlesGpuScheduler.kt',
'GlesGraphicsShader.kt',
'GlesMgcRawFusion.kt',
'GlesMgcRawSabreProcessor.kt',
'GlesMgcRawSabreShaders.kt',
'GlesMgcRawSpatialShaders.kt',
'GlesMgcRawSpatialStacker.kt',
'GlesPixelBufferTransfer.kt',
'MgcAlignmentInputScale.kt',
'MgcSabreKernelTuning.kt',
'MgcSabreNoiseEstimatesLut.kt',
'MgcSabreRejectionTuning.kt',
'MgcSabreResolveTuning.kt',
'MgcSabreResolver.kt',
'MgcSpatialDenoiseModel.kt',
'MgcSpatialDiagnosticGeometry.kt',
'MgcSpatialMergeTuning.kt',
'MgcSpatialOutputExposure.kt',
'MgcSpatialRgbTilePlanner.kt',
'MgcSpatialStrengthAtlasLayout.kt',
'MgcSpatialStrengthMapGenerator.kt',
'MgcSpatialStrengthMapScaler.kt',
'MgcStrengthReadbackShaders.kt',
'RawNoiseModel.kt',
'RawNoiseProfileSelection.kt',
]
OTHER=[
'app/src/main/java/com/hinnka/mycamera/camera/MultiFrameConfig.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcSpatialStrengthMap.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
]
MAPPED=[('LICENSE','app/src/main/assets/licenses/bjzhou_photoncamera_APACHE_2_0.txt')]
ASSETS=[
'app/src/main/assets/mgc_denoise/luma_denoise_default.binarypb',
'app/src/main/assets/mgc_denoise/sabre_luma_denoise.binarypb',
'app/src/main/assets/mgc_denoise/chroma_denoise.binarypb',
]
NATIVE_ROOT='app/src/main/cpp/mgc_denoise_static'
NATIVE_SINGLE=['app/src/main/cpp/mgc_strength_map_scaler.cpp']
NATIVE_CLOSURE_CAPSULES={
'mgc_sabre_resolve_capsule.bin':'725c5ac2c2de63e7f17c8fb3516fe176d2387c6eed579da25e35df12588e0e69',
'mgc_sharpen_capsule.bin':'733065cfec32ac752cc2088ea284b44a55b24a6171e5829f6971dcb098b1d7ce',
}
NATIVE_CLOSURE_REQUIRED=[
'mgc_sabre_resolve_static.S.in',
'mgc_sabre_resolve_jni.cpp',
'mgc_sharpen_static.S.in',
'mgc_sharpen_jni.cpp',
]

def run(*args:str,cwd:Path|None=None)->str:
    return subprocess.check_output(args,cwd=cwd,text=True).strip()

def copy_exact(src:Path,dst:Path):
    if not src.is_file(): raise SystemExit(f'missing upstream file: {src}')
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    if src.read_bytes()!=dst.read_bytes(): raise SystemExit(f'copy drift: {dst}')

def replace_once(text:str,old:str,new:str,label:str)->str:
    if text.count(old)!=1: raise SystemExit(f'{label}: expected exactly one transform anchor, found {text.count(old)}')
    return text.replace(old,new,1)

def wire_complete_native_closure(cand:Path):
    native=cand/'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static'
    for name,expected in NATIVE_CLOSURE_CAPSULES.items():
        path=native/name
        if not path.is_file(): raise SystemExit(f'missing pinned native closure capsule: {path}')
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected: raise SystemExit(f'pinned native closure capsule hash drift: {name} {actual} != {expected}')
    for name in NATIVE_CLOSURE_REQUIRED:
        path=native/name
        if not path.is_file(): raise SystemExit(f'missing pinned native closure source: {path}')

    cmake=cand/'app/src/main/cpp/mgc1271_upstream/CMakeLists.txt'
    text=cmake.read_text()
    marker='# IRIS_26512_MGC1271_COMPLETE_PINNED_NATIVE_CLOSURE'
    if marker in text: raise SystemExit('complete native closure marker unexpectedly pre-exists before pinned import')
    sabre_sharpen='''# IRIS_26512_MGC1271_COMPLETE_PINNED_NATIVE_CLOSURE
set(MGC_SABRE_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sabre_resolve_capsule.bin")
set(MGC_SABRE_CAPSULE_SHA256
    "725c5ac2c2de63e7f17c8fb3516fe176d2387c6eed579da25e35df12588e0e69")
file(SHA256 "${MGC_SABRE_CAPSULE}" MGC_SABRE_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_SABRE_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_SABRE_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 Sabre Resolve capsule hash mismatch")
endif()
set(MGC_SABRE_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_sabre_resolve_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sabre_resolve_static.S.in"
    "${MGC_SABRE_ASM}" @ONLY)
set_source_files_properties("${MGC_SABRE_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_SABRE_CAPSULE}")

set(MGC_SHARPEN_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sharpen_capsule.bin")
set(MGC_SHARPEN_CAPSULE_SHA256
    "733065cfec32ac752cc2088ea284b44a55b24a6171e5829f6971dcb098b1d7ce")
file(SHA256 "${MGC_SHARPEN_CAPSULE}" MGC_SHARPEN_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_SHARPEN_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_SHARPEN_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 SharpenTo16Bit capsule hash mismatch")
endif()
set(MGC_SHARPEN_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_sharpen_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sharpen_static.S.in"
    "${MGC_SHARPEN_ASM}" @ONLY)
set_source_files_properties("${MGC_SHARPEN_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_SHARPEN_CAPSULE}")

'''
    text=replace_once(text,'add_library(my-native-lib SHARED\n',sabre_sharpen+'add_library(my-native-lib SHARED\n','native closure CMake insertion')
    old_sources='''    mgc_denoise_static/mgc_full_resolution_denoise_jni.cpp
    mgc_denoise_static/mgc_spatial_strength_jni.cpp
    "${MGC_DENOISE_ASM}"
    "${MGC_DEMOIRE_ASM}")'''
    new_sources='''    mgc_denoise_static/mgc_full_resolution_denoise_jni.cpp
    mgc_denoise_static/mgc_sabre_resolve_jni.cpp
    mgc_denoise_static/mgc_sharpen_jni.cpp
    mgc_denoise_static/mgc_spatial_strength_jni.cpp
    "${MGC_DENOISE_ASM}"
    "${MGC_DEMOIRE_ASM}"
    "${MGC_SABRE_ASM}"
    "${MGC_SHARPEN_ASM}")'''
    text=replace_once(text,old_sources,new_sources,'native closure source list')
    old_flags='''set_source_files_properties(mgc_denoise_static/mgc_denoise_static.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
target_compile_options(my-native-lib PRIVATE -O3 -w ${OpenMP_CXX_FLAGS})'''
    new_flags='''set_source_files_properties(mgc_denoise_static/mgc_denoise_static.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
set_source_files_properties(mgc_denoise_static/mgc_sharpen_jni.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
target_compile_options(my-native-lib PRIVATE -O3 -w ${OpenMP_CXX_FLAGS})'''
    text=replace_once(text,old_flags,new_flags,'SharpenTo16Bit scalar boundary flags')
    cmake.write_text(text)
    required=(
        marker,
        'mgc_denoise_static/mgc_sabre_resolve_jni.cpp',
        'mgc_denoise_static/mgc_sharpen_jni.cpp',
        '"${MGC_SABRE_ASM}"',
        '"${MGC_SHARPEN_ASM}"',
        '725c5ac2c2de63e7f17c8fb3516fe176d2387c6eed579da25e35df12588e0e69',
        '733065cfec32ac752cc2088ea284b44a55b24a6171e5829f6971dcb098b1d7ce',
    )
    for token in required:
        if token not in text: raise SystemExit(f'complete native closure proof failed: missing {token!r}')
    if text.count(marker)!=1: raise SystemExit(f'complete native closure marker count drift: {text.count(marker)}')
    print('PASS: complete pinned MGC native closure wired: denoise + demoire + Sabre Resolve + SharpenTo16Bit')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--manifest',required=True,type=Path)
    ns=ap.parse_args(); up=ns.upstream.resolve(); cand=ns.candidate.resolve()
    head=run('git','rev-parse','HEAD',cwd=up)
    if head!=PINNED: raise SystemExit(f'wrong bjzhou commit {head}, expected {PINNED}')
    procroot=up/'app/src/main/java/com/hinnka/mycamera/processor'
    copied=[]
    for name in PROCESSOR:
        rel=Path('app/src/main/java/com/hinnka/mycamera/processor')/name
        copy_exact(procroot/name,cand/rel); copied.append(rel)
    for rels in OTHER+ASSETS:
        rel=Path(rels); copy_exact(up/rel,cand/rel); copied.append(rel)
    for srcs,dsts in MAPPED:
        src=Path(srcs); dst=Path(dsts); copy_exact(up/src,cand/dst); copied.append(dst)
    src_native=up/NATIVE_ROOT; dst_native=cand/'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static'
    if dst_native.exists(): shutil.rmtree(dst_native)
    shutil.copytree(src_native,dst_native)
    for p in sorted(dst_native.rglob('*')):
        if p.is_file():
            src=src_native/p.relative_to(dst_native)
            if p.read_bytes()!=src.read_bytes(): raise SystemExit(f'native copy drift: {p}')
            copied.append(p.relative_to(cand))
    # Place scaler beside the isolated CMakeLists; do not leave a duplicate at cpp root.
    scaler_src=up/'app/src/main/cpp/mgc_strength_map_scaler.cpp'
    scaler_dst=cand/'app/src/main/cpp/mgc1271_upstream/mgc_strength_map_scaler.cpp'
    copy_exact(scaler_src,scaler_dst); copied.append(scaler_dst.relative_to(cand))
    stray=cand/'app/src/main/cpp/mgc_strength_map_scaler.cpp'
    if stray.exists(): stray.unlink()
    # Complete the isolated native owner with the exact pinned 1.27.1 Sabre/Sharpen AOT closure.
    # This changes only the existing Photon adapter CMake path; copied upstream bytes remain untouched.
    wire_complete_native_closure(cand)
    # Exact upstream byte equivalence proof for all copied source/assets/native inputs.
    rows=[]
    for rel in sorted(set(copied),key=lambda x:str(x)):
        p=cand/rel
        rows.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}')
    ns.manifest.parent.mkdir(parents=True,exist_ok=True)
    ns.manifest.write_text('\n'.join(rows)+'\n')
    print(f'PASS: imported {len(rows)} exact bjzhou 1.27.1 Spatial parity files from {PINNED}')

if __name__=='__main__': main()
