#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26627_r1_patches.py BASE CAND FORWARD ROLLBACK')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); F=Path(sys.argv[3]); R=Path(sys.argv[4])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
BH,CH=H(B),H(C)
if len(BH)!=1713 or len(CH)!=1713: raise SystemExit('FAIL patch universe count')
for p in (F,R):
    text=p.read_text(errors='replace')
    for line in text.splitlines():
        if line.startswith('index '):
            ids=line.split()[1].split('..')
            if len(ids)!=2 or any(len(x)!=40 for x in ids): raise SystemExit(f'FAIL non-full index line in {p.name}: {line}')
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26627_patch_{abbrev}_') as td:
        root=Path(td); shutil.copytree(B/'app',root/'app')
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        subprocess.run(['git','config','user.email','iris@example.invalid'],cwd=root,check=True)
        subprocess.run(['git','config','user.name','Iris Proof'],cwd=root,check=True)
        subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=root,check=True)
        subprocess.run(['git','add','-A'],cwd=root,check=True); subprocess.run(['git','commit','-qm','base'],cwd=root,check=True)
        subprocess.run(['git','apply','--check','--index',str(F)],cwd=root,check=True)
        subprocess.run(['git','apply','--index',str(F)],cwd=root,check=True)
        if H(root)!=CH: raise SystemExit(f'FAIL forward patch bytes core.abbrev={abbrev}')
        subprocess.run(['git','diff','--cached','--check'],cwd=root,check=True); subprocess.run(['git','commit','-qm','candidate'],cwd=root,check=True)
        subprocess.run(['git','apply','--check','--index',str(R)],cwd=root,check=True)
        subprocess.run(['git','apply','--index',str(R)],cwd=root,check=True)
        if H(root)!=BH: raise SystemExit(f'FAIL rollback patch bytes core.abbrev={abbrev}')
        subprocess.run(['git','diff','--cached','--check'],cwd=root,check=True)
print('PASS 26627 deterministic full-index patches core.abbrev=7/12/40; --index exact preimage; diff --check clean; exact forward/rollback')
