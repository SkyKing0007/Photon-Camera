#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3:raise SystemExit("usage: transform_26707.py BASE26706 DEST")
base=Path(sys.argv[1]);dest=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent;payload=pkg/"handoff_payload_26707"
changed=[x.strip() for x in (pkg/"26707_RUNTIME_CHANGED_PATHS.txt").read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
pre=load("26707_PREWRITE_26706_SOURCE_HASHES.sha256");exp=load("26707_EXPECTED_CHANGED_SOURCE_HASHES.sha256")
assert set(pre)==set(exp)==set(changed) and len(changed)==5
for rel in changed:
 p=base/rel;q=payload/rel
 if not p.is_file() or sha(p)!=pre[rel]:raise SystemExit("FAIL prior source hash "+rel)
 if not q.is_file() or sha(q)!=exp[rel]:raise SystemExit("FAIL payload source hash "+rel)
if dest.exists():shutil.rmtree(dest)
shutil.copytree(base,dest)
for rel in changed:
 q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/rel,q)
print("PASS transform 26707 revised: overlaid 5 exact runtime files onto successful 26706 authority")
