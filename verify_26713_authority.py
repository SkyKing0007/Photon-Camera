#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1);d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c);assert len(B)==len(C)==1823
assert B==load('26713_BASE_26712_FULL_APP.sha256');assert C==load('26713_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=set((pkg/'26713_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert len(changed)==4
assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26713_PROTECTED_UNCHANGED_BASE.sha256');pc=load('26713_PROTECTED_UNCHANGED_CANDIDATE.sha256');assert len(pb)==len(pc)==1819 and pb==pc
for stem,count in [('NATIVE_PROTECTED',820),('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26713_{stem}_BASE.sha256');y=load(f'26713_{stem}_CANDIDATE.sha256');assert len(x)==len(y)==count,(stem,len(x),len(y));assert x==y,stem
sb=load('26713_ASSET_SHADER_UNIVERSE_BASE.sha256');sc=load('26713_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==271
shader_changed={k for k in sb|sc if sb.get(k)!=sc.get(k)};assert shader_changed=={'app/src/main/assets/shaders/preview/main_fs.glsl'},shader_changed
print('PASS 26713 authority/manifests: exact successful 26712 compiled candidate -> exact 4-file 26713 candidate; 1819 protected / 820 native / 1 vendor / 6 DNG invariant; exactly one preview shader changed')
