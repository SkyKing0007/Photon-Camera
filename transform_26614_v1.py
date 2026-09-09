#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26614_v1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); P=Path(__file__).resolve().parent
if not (base/'app').is_dir(): raise SystemExit('base app missing')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root, manifest):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    for line in lines:
        sha,rel=line.split('  ',1)
        q=root/rel
        if not q.is_file() or h(q)!=sha: raise SystemExit(f'hash mismatch before/after transform: {rel}')
    return len(lines)
# Candidate-first authority guard: only exact successful 26613 V1.1 changed-file bytes are writable.
if verify(base,'V1_26614_PREWRITE_SOURCE_HASHES.sha256')!=12: raise SystemExit('prewrite count')
patch=P/'V1_26614_RUNTIME_DELTA_FROM_26613_V1_1.patch'
subprocess.run(['git','apply','--check',str(patch)],cwd=out,check=True)
subprocess.run(['git','apply',str(patch)],cwd=out,check=True)
if verify(out,'V1_26614_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=12: raise SystemExit('candidate changed count')
print('PASS 26614 deterministic candidate reconstruction from exact successful 26613 V1.1 + canonical full-index patch')
