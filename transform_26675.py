#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26675.py BASE OUT')
root=Path(__file__).resolve().parent; base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in Path(p).read_text().splitlines():
  if line.strip(): h,r=line.split('  ',1); d[r]=h
 return d
changed=[x for x in (root/'R1_26675_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
pre=manifest(root/'R1_26675_PREWRITE_SOURCE_HASHES.sha256'); expected=manifest(root/'R1_26675_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert len(changed)==8 and set(changed)==set(pre)==set(expected)
for p in changed:
 q=base/p
 if not q.is_file() or sha(q)!=pre[p]: raise SystemExit(f'FAIL 26675 prior source authority {p}')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
payload=root/'handoff_payload_26675'
for p in changed:
 src=payload/p; dst=out/p
 if not src.is_file(): raise SystemExit(f'FAIL missing sealed payload {p}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 if sha(dst)!=expected[p]: raise SystemExit(f'FAIL transformed hash {p}')
print('PASS 26675 deterministic candidate transform: 8 modifications / 0 additions / 0 deletions')
