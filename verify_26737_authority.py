#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26737_authority.py ROOT BASE26736 CAND26737')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26737_BASE_26736_FULL_APP.sha256'); cm=load('26737_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26737_EXACT_26736_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26737_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==4 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26737_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26737_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1819 and pb==pc
for stem,count in [('NATIVE_FULL',820),('NATIVE_PROTECTED',820),('VENDOR_PROTECTED',1),('DNG',6),('ASSET_SHADER_UNIVERSE',271)]:
 x=load(f'26737_{stem}_BASE.sha256'); y=load(f'26737_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
print('PASS 26737 authority/manifests: exact reconstructed 26736 candidate -> exact 4-file 26737 candidate; 1819 protected / 820 native / 1 vendor / 6 DNG invariant; 271 asset shaders invariant')
