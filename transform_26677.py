#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
root=Path(__file__).resolve().parent;base=Path(sys.argv[1]);out=Path(sys.argv[2])
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def m(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): a,b=l.split('  ',1);d[b]=a
 return d
ch=[x for x in (root/'R1_26677_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; pre=m(root/'R1_26677_PREWRITE_SOURCE_HASHES.sha256'); exp=m(root/'R1_26677_EXPECTED_CHANGED_SOURCE_HASHES.sha256'); assert len(ch)==4 and set(ch)==set(pre)==set(exp)
for p,x in pre.items(): assert (base/p).is_file() and h(base/p)==x,p
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out); payload=root/'handoff_payload_26677'
for p in ch:
 q=out/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/p,q);assert h(q)==exp[p]
assert sum(1 for p in (out/'app').rglob('*') if p.is_file())==1726
print('PASS 26677 deterministic candidate transform: 4 modifications; 1726 files')
