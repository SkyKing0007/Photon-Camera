#!/usr/bin/env python3
from pathlib import Path
import hashlib, os, shutil, subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26621_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); P=Path(__file__).resolve().parent
if not (base/'app').is_dir(): raise SystemExit('base app missing')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root, manifest):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    for line in lines:
        sha,rel=line.split('  ',1); q=root/rel
        if not q.is_file() or h(q)!=sha: raise SystemExit(f'hash mismatch before/after transform: {rel}')
    return len(lines)
if verify(base,'R1_26621_PREWRITE_SOURCE_HASHES.sha256')!=12: raise SystemExit('prewrite count')
added=[x.strip() for x in (P/'R1_26621_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
if len(added)!=5: raise SystemExit('added path count')
for rel in added:
    if (base/rel).exists(): raise SystemExit(f'26621 added path unexpectedly exists in 26620 authority: {rel}')
patch=P/'R1_26621_RUNTIME_DELTA_FROM_26620_R1.patch'
# Exact successful 26620 nested-worktree isolation: the isolated candidate must not discover
# the checked-out carrier repository while git validates/applies the canonical patch.
env=os.environ.copy(); env['GIT_CEILING_DIRECTORIES']=str(out.parent)
probe=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=out,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if probe.returncode==0: raise SystemExit('candidate transform unexpectedly discovered a parent Git worktree')
subprocess.run(['git','apply','--check',str(patch)],cwd=out,env=env,check=True)
subprocess.run(['git','apply',str(patch)],cwd=out,env=env,check=True)
if verify(out,'R1_26621_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=14: raise SystemExit('candidate surviving changed count')
for rel in [
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl']:
    if (out/rel).exists(): raise SystemExit(f'stale 26620 local-tone shader survived: {rel}')
print('PASS 26621 deterministic candidate reconstruction from exact successful 26620 R1 + canonical full-index patch')
