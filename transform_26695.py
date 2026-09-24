#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26695.py BASE DEST')
base=Path(sys.argv[1]); dest=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent; payload=pkg/'handoff_payload_26695'
changed=[x.strip() for x in (pkg/'26695_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 out={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,r=line.split(None,1);out[r.strip()]=h
 return out
pre=load('26695_PREWRITE_SOURCE_HASHES.sha256'); post=load('26695_EXPECTED_CHANGED_SOURCE_HASHES.sha256'); assert sorted(pre)==sorted(changed)==sorted(post)
if dest.exists():shutil.rmtree(dest)
shutil.copytree(base,dest)
for rel in changed:
 src=payload/rel;dst=dest/rel;assert src.is_file() and dst.is_file();assert sha(dst)==pre[rel],rel;shutil.copy2(src,dst);assert sha(dst)==post[rel],rel
print('PASS 26695 deterministic transform: exact 4 modified paths, 0 additions/removals')
