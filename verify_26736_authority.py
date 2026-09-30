#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26736_authority.py ROOT BASE26735 CAND26736')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26736_BASE_26735_FULL_APP.sha256'); cm=load('26736_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26736_SUCCESSFUL_26735_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26736_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==3 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26736_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26736_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1820 and pb==pc
for stem,count in [('NATIVE_FULL',820),('NATIVE_PROTECTED',820),('VENDOR_PROTECTED',1),('DNG',6),('ASSET_SHADER_UNIVERSE',271)]:
 x=load(f'26736_{stem}_BASE.sha256'); y=load(f'26736_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
print('PASS 26736 authority/manifests: exact successful 26735 compiled candidate -> exact 3-file 26736 candidate; 1820 protected / 820 native / 1 vendor / 6 DNG invariant; 271 asset shaders invariant')
