#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26743_authority.py ROOT BASE26742 CAND26743')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823,(len(B),len(C))
bm=load('26743_BASE_26742_FULL_APP.sha256'); cm=load('26743_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26743_EXACT_26742_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26743_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==5 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26743_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26743_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1818 and pb==pc
for stem,count,same in [('NATIVE_FULL',820,False),('NATIVE_PROTECTED',819,True),('VENDOR_PROTECTED',1,True),('DNG',6,True),('ASSET_SHADER_UNIVERSE',271,True)]:
 x=load(f'26743_{stem}_BASE.sha256'); y=load(f'26743_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y))
 if same: assert x==y,stem
nb=load('26743_NATIVE_FULL_BASE.sha256'); nc=load('26743_NATIVE_FULL_CANDIDATE.sha256'); nd={k for k in nb|nc if nb.get(k)!=nc.get(k)}
assert nd=={'app/src/main/cpp/motionv2_jpeg444_jni.cpp'},nd
print('PASS 26743 authority/manifests: exact successful 26742 Actions candidate -> exact 5-file 26743 candidate; 1818 protected / 819 native-protected / 1 vendor / 6 DNG / 271 asset shaders invariant')
