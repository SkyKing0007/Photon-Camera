#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26637_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26637_r1'
changed=[x for x in (root/'R1_26637_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added={x for x in (root/'R1_26637_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x}
def read_manifest(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip(): h,rel=line.split('  ',1); d[rel]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre=read_manifest(root/'R1_26637_PREWRITE_SOURCE_HASHES.sha256')
expected=read_manifest(root/'R1_26637_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if len(changed)!=3 or len(set(changed))!=3: raise SystemExit('runtime allowlist count/uniqueness mismatch')
if added or set(changed)!=set(pre) or set(expected)!=set(changed): raise SystemExit('changed/prewrite/add/expected path mismatch')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out,symlinks=True)
for rel in changed:
 p=base/rel; q=payload/rel; dst=out/rel
 if not p.is_file() or sha(p)!=pre[rel]: raise SystemExit(f'authority prewrite mismatch: {rel}')
 if not q.is_file() or sha(q)!=expected[rel]: raise SystemExit(f'sealed payload hash mismatch: {rel}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,dst)
 if sha(dst)!=expected[rel]: raise SystemExit(f'transformed hash mismatch: {rel}')
print('PASS 26637 deterministic candidate transform: exact 3-path replacement from successful 26636 authority')
