#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
assert B==load('26710_BASE_26709_FULL_APP.sha256'); assert C==load('26710_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=set((pkg/'26710_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==2
assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26710_PROTECTED_UNCHANGED_BASE.sha256');pc=load('26710_PROTECTED_UNCHANGED_CANDIDATE.sha256');assert len(pb)==len(pc)==1821 and pb==pc
for stem,count in [('NATIVE_PROTECTED',820),('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26710_{stem}_BASE.sha256');y=load(f'26710_{stem}_CANDIDATE.sha256');assert len(x)==len(y)==count,(stem,len(x),len(y));assert x==y,stem
sb=load('26710_ASSET_SHADER_UNIVERSE_BASE.sha256');sc=load('26710_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==271 and sb==sc
print('PASS 26710 authority/manifests: exact successful 26709 compiled candidate -> exact 2-file 26710 candidate; 1821 protected / 820 native / 1 vendor / 6 DNG / 271 shaders invariant')
