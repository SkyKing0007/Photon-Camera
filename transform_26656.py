#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26656.py BASE DEST')
base=Path(sys.argv[1]).resolve(); dest=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
changed=[x for x in (root/'R1_26656_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26656_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==11 and len(added)==5 and set(added)<=set(changed)
pre=readm(root/'R1_26656_PREWRITE_SOURCE_HASHES.sha256'); assert len(pre)==6
for r,h in pre.items():
 p=base/r
 if not p.is_file() or sha(p)!=h: raise SystemExit(f'prewrite authority mismatch {r}')
for r in added:
 if (base/r).exists(): raise SystemExit(f'added path unexpectedly exists in 26655 authority {r}')
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest,copy_function=shutil.copy2)
payload=root/'handoff_payload_26656'; files=sorted(p for p in payload.rglob('*') if p.is_file())
if len(files)!=11: raise SystemExit(f'expected 11 payload files, got {len(files)}')
if {str(p.relative_to(payload)) for p in files}!=set(changed): raise SystemExit('payload path set != runtime allowlist')
for p in files:
 rel=p.relative_to(payload); out=dest/rel; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,out)
exp=readm(root/'R1_26656_EXPECTED_CANDIDATE_FULL_APP.sha256')
actual={str(p.relative_to(dest)):sha(p) for p in sorted((dest/'app').rglob('*')) if p.is_file()}
if actual!=exp: raise SystemExit('transformed candidate != sealed freeze2 expected candidate manifest')
print('PASS 26656 deterministic candidate transform: exact successful 26655 compiled authority + 11-path freeze2 payload (6 modified + 5 added) = 1726 files')
