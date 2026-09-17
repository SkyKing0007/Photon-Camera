#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26654.py BASE DEST')
base=Path(sys.argv[1]).resolve(); dest=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
changed=[x for x in (root/'R1_26654_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26654_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==8 and len(added)==0
pre=readm(root/'R1_26654_PREWRITE_SOURCE_HASHES.sha256'); assert len(pre)==8
for r,h in pre.items():
 p=base/r
 if not p.is_file() or sha(p)!=h: raise SystemExit(f'prewrite authority mismatch {r}')
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest,copy_function=shutil.copy2)
payload=root/'handoff_payload_26654'; files=sorted(p for p in payload.rglob('*') if p.is_file())
if len(files)!=8: raise SystemExit(f'expected 8 payload files, got {len(files)}')
for p in files:
 rel=p.relative_to(payload); out=dest/rel; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,out)
exp=readm(root/'R1_26654_EXPECTED_CANDIDATE_FULL_APP.sha256')
actual={str(p.relative_to(dest)):sha(p) for p in sorted((dest/'app').rglob('*')) if p.is_file()}
if actual!=exp: raise SystemExit('transformed candidate != sealed expected candidate manifest')
print('PASS 26654 deterministic candidate transform: exact successful 26653 compiled authority + 8-path payload = 1721 files')
