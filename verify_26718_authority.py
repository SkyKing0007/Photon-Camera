#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: verify_26718_authority.py ROOT BASE26717 CAND26718')
pkg=Path(sys.argv[1]);b=Path(sys.argv[2]);c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c);assert len(B)==len(C)==1823,(len(B),len(C))
base_manifest=load('26718_BASE_26717_FULL_APP.sha256');success=load('26718_SUCCESSFUL_26717_CANDIDATE_AUTHORITY.sha256');expected=load('26718_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(base_manifest)==len(success)==len(expected)==1823
assert B==base_manifest==success;assert C==expected
changed=set((pkg/'26718_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert len(changed)==12
assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26718_PROTECTED_UNCHANGED_BASE.sha256');pc=load('26718_PROTECTED_UNCHANGED_CANDIDATE.sha256');assert len(pb)==len(pc)==1811 and pb==pc
for stem,count in [('NATIVE_PROTECTED',820),('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26718_{stem}_BASE.sha256');y=load(f'26718_{stem}_CANDIDATE.sha256');assert len(x)==len(y)==count,(stem,len(x),len(y));assert x==y,stem
sb=load('26718_ASSET_SHADER_UNIVERSE_BASE.sha256');sc=load('26718_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==271
assert {p for p in sb if sb[p]!=sc[p]}=={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'}
print('PASS 26718 authority/manifests: exact successful 26717 compiled candidate -> exact 12-file 26718 candidate; 1811 protected / 820 native / 1 vendor / 6 DNG invariant; shader universe 271 with exact 2-asset delta')
