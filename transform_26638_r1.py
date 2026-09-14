#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26638_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26638_r1'
changed=[x for x in (root/'R1_26638_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added={x for x in (root/'R1_26638_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x}
def read_manifest(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip(): h,rel=line.split('  ',1); d[rel]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre=read_manifest(root/'R1_26638_PREWRITE_SOURCE_HASHES.sha256')
expected=read_manifest(root/'R1_26638_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if len(changed)!=10 or len(set(changed))!=10 or len(added)!=1: raise SystemExit('runtime allowlist/add count mismatch')
if set(changed)!=set(pre)|added or set(expected)!=set(changed) or set(pre)&added: raise SystemExit('changed/prewrite/add/expected path mismatch')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out,symlinks=True)
for rel in changed:
 p=base/rel; q=payload/rel; dst=out/rel
 if rel in added:
  if p.exists(): raise SystemExit(f'added path unexpectedly exists in authority: {rel}')
 else:
  if not p.is_file() or sha(p)!=pre[rel]: raise SystemExit(f'authority prewrite mismatch: {rel}')
 if not q.is_file() or sha(q)!=expected[rel]: raise SystemExit(f'sealed payload hash mismatch: {rel}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,dst)
 if sha(dst)!=expected[rel]: raise SystemExit(f'transformed hash mismatch: {rel}')
print('PASS 26638 deterministic candidate transform: exact 10-path delta / 1 added from successful 26637 compiled-candidate authority')
