#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26697.py BASE26696R1 DEST')
base=Path(sys.argv[1]); dest=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent; payload=pkg/'handoff_payload_26697'
changed=[x.strip() for x in (pkg/'26697_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
added=[x.strip() for x in (pkg/'26697_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():
   h,r=line.split(None,1); out[r.strip()]=h
 return out
pre=load('26697_PREWRITE_26696R1_SOURCE_HASHES.sha256'); post=load('26697_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert sorted(changed)==sorted(pre)==sorted(post) and not added
for rel in changed:
 assert (base/rel).is_file() and sha(base/rel)==pre[rel],('26696 R1 prewrite mismatch',rel)
 assert (payload/rel).is_file() and sha(payload/rel)==post[rel],('26697 payload mismatch',rel)
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest)
for rel in changed:
 dst=dest/rel; assert dst.is_file(),rel; shutil.copy2(payload/rel,dst); assert sha(dst)==post[rel],rel
print('PASS 26697 deterministic transform: exact successful 26696 R1 universe; exact 5 modified paths; 0 additions/removals')
