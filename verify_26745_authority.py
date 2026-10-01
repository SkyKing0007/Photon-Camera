#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26745_authority.py ROOT BASE26743 CAND26745')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823,(len(B),len(C))
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in B|C)
bm=load('26745_BASE_26743_FULL_APP.sha256'); cm=load('26745_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26745_EXACT_26743_CANDIDATE_AUTHORITY.sha256')
assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26745_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==4 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
assert not (pkg/'26745_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
pb=load('26745_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26745_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1819 and pb==pc
for stem,count in [('NATIVE_FULL',820),('NATIVE_PROTECTED',819),('VENDOR_PROTECTED',1),('DNG',6),('ASSET_SHADER_UNIVERSE',271)]:
 x=load(f'26745_{stem}_BASE.sha256'); y=load(f'26745_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y))
 if stem not in ('NATIVE_FULL','ASSET_SHADER_UNIVERSE'): assert x==y,stem
nb=load('26745_NATIVE_FULL_BASE.sha256'); nc=load('26745_NATIVE_FULL_CANDIDATE.sha256'); assert {k for k in nb|nc if nb.get(k)!=nc.get(k)}=={'app/src/main/cpp/motionv2_jpeg444_jni.cpp'}
sb=load('26745_ASSET_SHADER_UNIVERSE_BASE.sha256'); sc=load('26745_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert {k for k in sb|sc if sb.get(k)!=sc.get(k)}=={'app/src/main/assets/shaders/motionv2/color_transform.glsl'}
print('PASS 26745 authority/manifests: exact successful 26743 Actions candidate -> exact 4-file 26745 candidate; 1819 protected / 819 native-protected / 1 vendor / 6 DNG invariant; one intended asset shader changed')
