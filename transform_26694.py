#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26694.py BASE DEST')
base=Path(sys.argv[1]); dest=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent; payload=pkg/'handoff_payload_26694'
changed=[x.strip() for x in (pkg/'26694_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_manifest(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if not line.strip(): continue
  h,rel=line.split(None,1); out[rel.strip()]=h
 return out
pre=read_manifest('26694_PREWRITE_SOURCE_HASHES.sha256'); post=read_manifest('26694_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert sorted(pre)==sorted(changed)==sorted(post)
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest)
for rel in changed:
 src=payload/rel; dst=dest/rel
 assert src.is_file(),f'missing payload {rel}'
 assert dst.is_file(),f'base path absent {rel}'
 assert sha(dst)==pre[rel],f'base hash mismatch {rel}'
 shutil.copy2(src,dst)
 assert sha(dst)==post[rel],f'target hash mismatch {rel}'
print('PASS 26694 deterministic transform: exact 7 modified paths, 0 additions/removals')
