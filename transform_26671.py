#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26671.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26671'
pre=root/'R1_26671_PREWRITE_SOURCE_HASHES.sha256'; exp=root/'R1_26671_EXPECTED_CHANGED_SOURCE_HASHES.sha256'; changedf=root/'R1_26671_RUNTIME_CHANGED_PATHS.txt'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for line in Path(p).read_text().splitlines():
  if line.strip(): h,r=line.split('  ',1); d[r]=h
 return d
changed=[x for x in changedf.read_text().splitlines() if x]
assert len(changed)==5 and len(set(changed))==5
pre_m=pm(pre); exp_m=pm(exp); assert set(pre_m)==set(exp_m)==set(changed)
for rel in changed:
 p=base/rel
 if not p.is_file() or sha(p)!=pre_m[rel]: raise SystemExit('FAIL prewrite authority hash: '+rel)
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in changed:
 src=payload/rel; dst=out/rel
 if not src.is_file(): raise SystemExit('FAIL missing 26671 payload: '+rel)
 if sha(src)!=exp_m[rel]: raise SystemExit('FAIL payload hash: '+rel)
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
for rel in changed:
 if sha(out/rel)!=exp_m[rel]: raise SystemExit('FAIL transformed candidate hash: '+rel)
print('TRANSFORM_26671_OK exact successful-26670 compiled authority -> frozen 5-path candidate (5 modified / 0 added / 0 deleted)')
