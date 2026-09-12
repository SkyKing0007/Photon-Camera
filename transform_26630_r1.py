#!/usr/bin/env python3
from pathlib import Path
import hashlib, os, shutil, subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26630_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); P=Path(__file__).resolve().parent
if not (base/'app').is_dir(): raise SystemExit('base app missing')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest,expected):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    if len(lines)!=expected: raise SystemExit(f'{manifest} count {len(lines)} != {expected}')
    for line in lines:
        sh,rel=line.split('  ',1); q=root/rel
        if not q.is_file() or h(q)!=sh: raise SystemExit(f'hash mismatch before/after transform: {rel}')
verify(base,'R1_26630_PREWRITE_SOURCE_HASHES.sha256',13)
added=[x.strip() for x in (P/'R1_26630_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
if added: raise SystemExit('26630 adds no runtime paths')
patch=P/'R1_26630_RUNTIME_DELTA_FROM_26629_R1.patch'
env=os.environ.copy(); env['GIT_CEILING_DIRECTORIES']=str(out.parent)
probe=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=out,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if probe.returncode==0: raise SystemExit('candidate transform unexpectedly discovered a parent Git worktree')
subprocess.run(['git','apply','--check',str(patch)],cwd=out,env=env,check=True)
subprocess.run(['git','apply',str(patch)],cwd=out,env=env,check=True)
verify(out,'R1_26630_EXPECTED_CHANGED_SOURCE_HASHES.sha256',13)
print('PASS 26630 deterministic candidate reconstruction from exact successful 26629 R1 + canonical full-index patch')
