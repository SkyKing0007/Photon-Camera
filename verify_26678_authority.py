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
b,c=amap(base),amap(cand);assert len(b)==1726 and len(c)==1727
assert b==m(root/'R1_26678_BASE_26677_FULL_APP.sha256');assert c==m(root/'R1_26678_EXPECTED_CANDIDATE_FULL_APP.sha256')
for f,n in [('PROTECTED_UNCHANGED',1718),('NATIVE_PROTECTED',805),('VENDOR_PROTECTED',778),('DNG',7)]:
 x=m(root/f'R1_26678_{f}_BASE.sha256');y=m(root/f'R1_26678_{f}_CANDIDATE.sha256');assert len(x)==len(y)==n and x==y
print('PASS 26678 authority: exact successful-26677 1726-file authority; candidate 1727 files; 7 modified / 2 added / 1 deleted; protected invariance PASS')
