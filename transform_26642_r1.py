#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26642_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26642_r1'
changed=[x for x in (root/'R1_26642_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added={x for x in (root/'R1_26642_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x}
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre=readm(root/'R1_26642_PREWRITE_SOURCE_HASHES.sha256'); expected=readm(root/'R1_26642_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if len(changed)!=14 or len(set(changed))!=14 or len(added)!=2: raise SystemExit('runtime allowlist/add count mismatch')
if set(changed)!=set(expected) or set(pre)!=(set(changed)-added): raise SystemExit('changed/prewrite/expected path mismatch')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out,symlinks=True)
for rel in changed:
 q=payload/rel; dst=out/rel
 if rel in added:
  if (base/rel).exists(): raise SystemExit(f'added path unexpectedly exists in authority: {rel}')
 else:
  bp=base/rel
  if not bp.is_file() or sha(bp)!=pre[rel]: raise SystemExit(f'authority prewrite mismatch: {rel}')
 if not q.is_file() or sha(q)!=expected[rel]: raise SystemExit(f'sealed payload hash mismatch: {rel}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(q,dst)
 if sha(dst)!=expected[rel]: raise SystemExit(f'transformed hash mismatch: {rel}')
print('PASS 26642 deterministic candidate transform: exact 14-path delta / 2 added from successful 26641 compiled-candidate authority')
