#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26700.py BASE26699 DEST')
base=Path(sys.argv[1]);dest=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent;payload=pkg/'handoff_payload_26700'
changed=[x.strip() for x in (pkg/'26700_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
added=[x.strip() for x in (pkg/'26700_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
pre=load('26700_PREWRITE_26699_SOURCE_HASHES.sha256');exp=load('26700_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if set(pre)!=set(changed) or set(exp)!=set(changed):raise SystemExit('FAIL changed hash manifest key mismatch')
for rel in changed:
 p=base/rel
 if not p.is_file() or sha(p)!=pre[rel]:raise SystemExit(f'FAIL prior source hash {rel}')
 q=payload/rel
 if not q.is_file() or sha(q)!=exp[rel]:raise SystemExit(f'FAIL payload source hash {rel}')
for rel in added:
 if (base/rel).exists():raise SystemExit(f'FAIL added path unexpectedly exists in authority {rel}')
if dest.exists():shutil.rmtree(dest)
shutil.copytree(base,dest)
for rel in changed:
 q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/rel,q)
print(f'PASS transform 26700: overlaid {len(changed)} exact runtime files onto successful 26699 authority')
