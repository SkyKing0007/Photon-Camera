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
ch=[x for x in (root/'R1_26678_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
adds=[x for x in (root/'R1_26678_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
dels=[x for x in (root/'R1_26678_DELETED_PATHS_MUST_EXIST.txt').read_text().splitlines() if x]
pre=m(root/'R1_26678_PREWRITE_SOURCE_HASHES.sha256'); exp=m(root/'R1_26678_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert len(ch)==10 and len(adds)==2 and len(dels)==1 and len(pre)==8 and len(exp)==9
assert set(ch)==set(pre)|set(exp) and set(adds)==set(exp)-set(pre) and set(dels)==set(pre)-set(exp)
for p,x in pre.items(): assert (base/p).is_file() and h(base/p)==x,p
for p in adds: assert not (base/p).exists(),p
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out); payload=root/'handoff_payload_26678'
for p in dels:
 q=out/p; assert q.is_file(),p; q.unlink()
for p,x in exp.items():
 q=out/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/p,q);assert h(q)==x,p
assert sum(1 for p in (out/'app').rglob('*') if p.is_file())==1727
print('PASS 26678 deterministic candidate transform: 7 modifications / 2 additions / 1 deletion; 1727 files')
