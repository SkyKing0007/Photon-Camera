#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
root,base,cand=map(Path,sys.argv[1:4])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def m(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip():a,b=l.split('  ',1);d[b]=a
 return d
def amap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b,c=amap(base),amap(cand);assert len(b)==len(c)==1727
assert b==m(root/'R2_26679_BASE_26678_FULL_APP.sha256');assert c==m(root/'R2_26679_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x for x in (root/'R2_26679_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
actual=sorted(p for p in b if b[p]!=c[p]);assert actual==sorted(changed) and len(actual)==5,(actual,changed)
for f,n in [('PROTECTED_UNCHANGED',1722),('NATIVE_PROTECTED',805),('VENDOR_PROTECTED',778),('DNG',7)]:
 x=m(root/f'R2_26679_{f}_BASE.sha256');y=m(root/f'R2_26679_{f}_CANDIDATE.sha256');assert len(x)==len(y)==n and x==y
print('PASS 26679 authority: exact successful-26678 1727-file authority; candidate 1727 files; exactly 5 modified / 0 added / 0 deleted; 1722 protected invariance PASS')
