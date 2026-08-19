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

def run(*args:str,cwd:Path|None=None)->str:
    return subprocess.check_output(args,cwd=cwd,text=True).strip()

def copy_exact(src:Path,dst:Path):
    if not src.is_file(): raise SystemExit(f'missing upstream file: {src}')
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    if src.read_bytes()!=dst.read_bytes(): raise SystemExit(f'copy drift: {dst}')

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
    # Exact upstream byte equivalence proof for all copied source/assets/native inputs.
    rows=[]
    for rel in sorted(set(copied),key=lambda x:str(x)):
        p=cand/rel
        rows.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}')
    ns.manifest.parent.mkdir(parents=True,exist_ok=True)
    ns.manifest.write_text('\n'.join(rows)+'\n')
    print(f'PASS: imported {len(rows)} exact bjzhou 1.27.1 Spatial parity files from {PINNED}')

if __name__=='__main__': main()
