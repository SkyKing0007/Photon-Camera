#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26659.py BASE CANDIDATE')
base=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26659';changed=[x for x in (root/'R1_26659_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(changed)==4 and not (root/'R1_26659_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
pre=readm(root/'R1_26659_PREWRITE_SOURCE_HASHES.sha256');exp=readm(root/'R1_26659_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert set(pre)==set(exp)==set(changed)
for r in changed:
 p=base/r
 if not p.is_file() or sha(p)!=pre[r]:raise SystemExit(f'FAIL 26659 prewrite authority {r}')
 q=payload/r
 if not q.is_file() or sha(q)!=exp[r]:raise SystemExit(f'FAIL 26659 sealed payload {r}')
if out.exists():shutil.rmtree(out)
shutil.copytree(base,out)
for r in changed:
 dst=out/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/r,dst)
for r in changed:
 if sha(out/r)!=exp[r]:raise SystemExit(f'FAIL 26659 transformed hash {r}')
print('PASS 26659 deterministic candidate transform: 4 exact replacements / 0 additions from successful 26658 compiled candidate')
