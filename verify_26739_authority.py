#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26739_authority.py ROOT BASE26738 CAND26739')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26739_BASE_26738_FULL_APP.sha256'); cm=load('26739_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26739_EXACT_26738_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26739_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==5 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26739_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26739_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1818 and pb==pc
for stem,count in [('NATIVE_FULL',820),('NATIVE_PROTECTED',820),('VENDOR_PROTECTED',1),('DNG',6),('ASSET_SHADER_UNIVERSE',271)]:
 x=load(f'26739_{stem}_BASE.sha256'); y=load(f'26739_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
print('PASS 26739 authority/manifests: exact reconstructed 26738 candidate -> exact 5-file 26739 candidate; 1818 protected / 820 native / 1 vendor / 6 DNG / 271 asset shaders invariant')
