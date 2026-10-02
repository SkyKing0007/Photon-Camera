#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26746_authority.py ROOT BASE26745 CAND26746')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823,(len(B),len(C)); assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in B|C)
bm=load('26746_BASE_26745_FULL_APP.sha256'); cm=load('26746_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26746_EXACT_26745_CANDIDATE_AUTHORITY.sha256'); assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26746_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==2 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
assert not (pkg/'26746_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
pb=load('26746_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26746_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1821 and pb==pc
for stem,count in [('NATIVE_FULL',820),('NATIVE_PROTECTED',820),('VENDOR_PROTECTED',1),('DNG',6),('ASSET_SHADER_UNIVERSE',271)]:
 x=load(f'26746_{stem}_BASE.sha256'); y=load(f'26746_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
print('PASS 26746 authority/manifests: exact successful 26745 Actions candidate -> exact 2-file 26746 candidate; 1821 protected / 820 native-protected / 1 vendor / 6 DNG / 271 asset shaders invariant')
