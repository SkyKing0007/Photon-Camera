#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26734_authority.py ROOT BASE26733 CAND26734')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26734_BASE_26733_FULL_APP.sha256'); cm=load('26734_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26734_SUCCESSFUL_26733_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26734_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==8 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26734_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26734_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1815 and pb==pc
for stem,count,equal in [('NATIVE_FULL',820,False),('NATIVE_PROTECTED',819,True),('VENDOR_PROTECTED',1,True),('DNG',6,True)]:
 x=load(f'26734_{stem}_BASE.sha256'); y=load(f'26734_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y));
 if equal: assert x==y,stem
 else:
  delta={k for k in x|y if x.get(k)!=y.get(k)}; assert delta=={'app/src/main/cpp/motionv2_jpeg444_jni.cpp'},delta
sb=load('26734_ASSET_SHADER_UNIVERSE_BASE.sha256'); sc=load('26734_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(sb)==len(sc)==271 and sb==sc
print('PASS 26734 authority/manifests: exact successful 26733 compiled candidate -> exact 8-file 26734 candidate; 1815 protected / 819 native-protected / 1 vendor / 6 DNG invariant; one intentional native source change; shader asset universe 271 byte-identical')
