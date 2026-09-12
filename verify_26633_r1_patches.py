#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26633_r1_patches.py BASE CAND FORWARD ROLLBACK')
B=Path(sys.argv[1]).resolve(); C=Path(sys.argv[2]).resolve(); F=Path(sys.argv[3]).resolve(); R=Path(sys.argv[4]).resolve(); P=Path(__file__).resolve().parent
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
BH,CH=H(B),H(C)
if len(BH)!=1713 or len(CH)!=1713: raise SystemExit('FAIL patch universe count')
expected=sorted(x.strip() for x in (P/'R1_26633_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
actual=sorted(k for k in set(BH)|set(CH) if BH.get(k)!=CH.get(k))
if actual!=expected or len(expected)!=5: raise SystemExit(f'FAIL patch allowlist mismatch {actual}')
for p in (F,R):
 text=p.read_text(errors='replace')
 indexes=[line for line in text.splitlines() if line.startswith('index ')]
 if len(indexes)!=5: raise SystemExit(f'FAIL patch index count {p.name} {len(indexes)}')
 for line in indexes:
  pair=line.split()[1]
  if '..' not in pair: raise SystemExit(f'FAIL malformed index {line}')
  a,b=pair.split('..',1)
  if len(a)!=40 or len(b)!=40: raise SystemExit(f'FAIL non-full index line in {p.name}: {line}')
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26633_patch_{abbrev}_') as td:
  root=Path(td); shutil.copytree(B/'app',root/'app')
  subprocess.run(['git','init','-q'],cwd=root,check=True); subprocess.run(['git','config','user.email','iris@example.invalid'],cwd=root,check=True); subprocess.run(['git','config','user.name','Iris Proof'],cwd=root,check=True); subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=root,check=True)
  subprocess.run(['git','add','-A'],cwd=root,check=True); subprocess.run(['git','commit','-qm','base'],cwd=root,check=True)
  subprocess.run(['git','apply','--check','--index',str(F)],cwd=root,check=True); subprocess.run(['git','apply','--index',str(F)],cwd=root,check=True)
  if H(root)!=CH: raise SystemExit(f'FAIL forward patch bytes core.abbrev={abbrev}')
  subprocess.run(['git','diff','--cached','--check'],cwd=root,check=True); subprocess.run(['git','commit','-qm','candidate'],cwd=root,check=True)
  subprocess.run(['git','apply','--check','--index',str(R)],cwd=root,check=True); subprocess.run(['git','apply','--index',str(R)],cwd=root,check=True)
  if H(root)!=BH: raise SystemExit(f'FAIL rollback patch bytes core.abbrev={abbrev}')
  subprocess.run(['git','diff','--cached','--check'],cwd=root,check=True)
print('PASS 26633 deterministic full-index patches core.abbrev=7/12/40; --index exact preimage; diff --check clean; exact forward/rollback')
