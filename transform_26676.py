#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26676.py BASE OUT')
root=Path(__file__).resolve().parent; base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in Path(p).read_text().splitlines():
  if line.strip(): h,r=line.split('  ',1); d[r]=h
 return d
changed=[x for x in (root/'R1_26676_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26676_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
deleted=[x for x in (root/'R1_26676_DELETED_PATHS_MUST_EXIST.txt').read_text().splitlines() if x]
pre=manifest(root/'R1_26676_PREWRITE_SOURCE_HASHES.sha256'); expected=manifest(root/'R1_26676_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert len(changed)==9 and len(added)==1 and len(deleted)==1
assert set(pre)==set(changed)-set(added) and set(expected)==set(changed)-set(deleted)
for p,h in pre.items():
 q=base/p
 if not q.is_file() or sha(q)!=h: raise SystemExit(f'FAIL 26676 prior source authority {p}')
for p in added:
 if (base/p).exists(): raise SystemExit(f'FAIL 26676 added path already exists in authority {p}')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for p in deleted:
 q=out/p
 if not q.is_file(): raise SystemExit(f'FAIL 26676 deletion authority missing {p}')
 q.unlink()
payload=root/'handoff_payload_26676'
for p in sorted(set(changed)-set(deleted)):
 src=payload/p; dst=out/p
 if not src.is_file(): raise SystemExit(f'FAIL missing sealed payload {p}')
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 if sha(dst)!=expected[p]: raise SystemExit(f'FAIL transformed hash {p}')
for p in deleted:
 if (out/p).exists(): raise SystemExit(f'FAIL deleted path survived {p}')
count=sum(1 for p in (out/'app').rglob('*') if p.is_file())
assert count==1726,count
print('PASS 26676 deterministic candidate transform: 7 modifications / 1 addition / 1 deletion; 1726 files')
