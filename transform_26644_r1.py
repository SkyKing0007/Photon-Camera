#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26644_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26644_r1'
changed=[x for x in (root/'R1_26644_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre=readm(root/'R1_26644_PREWRITE_SOURCE_HASHES.sha256'); expected=readm(root/'R1_26644_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if len(changed)!=6 or len(set(changed))!=6: raise SystemExit('runtime allowlist count mismatch')
if set(changed)!=set(expected) or set(pre)!=set(changed): raise SystemExit('changed/prewrite/expected path mismatch')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out,symlinks=True)
for rel in changed:
 bp=base/rel; q=payload/rel; dst=out/rel
 if not bp.is_file() or sha(bp)!=pre[rel]: raise SystemExit(f'authority prewrite mismatch: {rel}')
 if not q.is_file() or sha(q)!=expected[rel]: raise SystemExit(f'sealed payload hash mismatch: {rel}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,dst)
 if sha(dst)!=expected[rel]: raise SystemExit(f'transformed hash mismatch: {rel}')
print('PASS 26644 deterministic candidate transform: exact 6-path/0-added delta from successful 26643 compiled-candidate authority')
