#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26663.py BASE CANDIDATE')
base,out=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26663';changed=[x for x in (root/'R1_26663_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(changed)==7 and not (root/'R1_26663_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
pre=readm(root/'R1_26663_PREWRITE_SOURCE_HASHES.sha256');exp=readm(root/'R1_26663_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if set(pre)!=set(changed) or set(exp)!=set(changed):raise SystemExit('FAIL 26663 hash allowlist')
for r in changed:
 p=base/r;q=payload/r
 if not p.is_file() or sha(p)!=pre[r]:raise SystemExit(f'FAIL 26663 prewrite authority {r}')
 if not q.is_file() or sha(q)!=exp[r]:raise SystemExit(f'FAIL 26663 sealed payload {r}')
if out.exists():shutil.rmtree(out)
shutil.copytree(base,out)
for r in changed:
 q=out/r;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/r,q)
 if sha(q)!=exp[r]:raise SystemExit(f'FAIL 26663 transformed hash {r}')
print('PASS 26663 deterministic candidate transform: 7 exact replacements / 0 additions from successful 26662 compiled candidate')
