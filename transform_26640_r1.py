#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26640_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26640_r1'
changed=[x for x in (root/'R1_26640_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added={x for x in (root/'R1_26640_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x}
def manifest(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre=manifest(root/'R1_26640_PREWRITE_SOURCE_HASHES.sha256')
expected=manifest(root/'R1_26640_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if len(changed)!=5 or len(set(changed))!=5 or added: raise SystemExit('runtime allowlist/add count mismatch')
if set(changed)!=set(pre) or set(expected)!=set(changed): raise SystemExit('changed/prewrite/expected path mismatch')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out,symlinks=True)
for rel in changed:
 p=base/rel; q=payload/rel; dst=out/rel
 if not p.is_file() or sha(p)!=pre[rel]: raise SystemExit(f'authority prewrite mismatch: {rel}')
 if not q.is_file() or sha(q)!=expected[rel]: raise SystemExit(f'sealed payload hash mismatch: {rel}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,dst)
 if sha(dst)!=expected[rel]: raise SystemExit(f'transformed hash mismatch: {rel}')
print('PASS 26640 deterministic candidate transform: exact 5-path delta / 0 added from successful 26639 compiled-candidate authority')
