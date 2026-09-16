#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26649.py BASE DEST')
base=Path(sys.argv[1]).resolve(); dest=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26649_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
if len(changed)!=5 or len(set(changed))!=5: raise SystemExit(f'expected 5 unique changed paths, got {len(changed)}')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip(): h,r=line.split('  ',1); d[r]=h
 return d
pre=readm(root/'R1_26649_PREWRITE_SOURCE_HASHES.sha256'); post=readm(root/'R1_26649_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if set(pre)!=set(changed) or set(post)!=set(changed): raise SystemExit('changed hash manifest scope mismatch')
for rel in changed:
 p=base/rel
 if not p.is_file() or sha(p)!=pre[rel]: raise SystemExit(f'base authority mismatch: {rel}')
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest,copy_function=shutil.copy2)
payload=root/'handoff_payload_26649'
for rel in changed:
 src=payload/rel; out=dest/rel
 if not src.is_file() or sha(src)!=post[rel]: raise SystemExit(f'sealed payload mismatch: {rel}')
 out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,out)
 if sha(out)!=post[rel]: raise SystemExit(f'candidate write mismatch: {rel}')
files=[p for p in (dest/'app').rglob('*') if p.is_file()]
if len(files)!=1720: raise SystemExit(f'candidate file count {len(files)} != 1720')
print('PASS 26649 deterministic payload transform: exact successful 26648 R1.2 authority -> 1720-file candidate, 5 changed / 0 added')
