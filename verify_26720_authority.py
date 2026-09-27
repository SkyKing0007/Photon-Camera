#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26720_authority.py ROOT BASE26719 CAND26720')
pkg=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
bm=load('26720_BASE_26719_FULL_APP.sha256'); cm=load('26720_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26720_SUCCESSFUL_26719_CANDIDATE_AUTHORITY.sha256'); assert len(bm)==len(cm)==len(am)==1823 and B==bm==am and C==cm
changed=set((pkg/'26720_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==14 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
pb=load('26720_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26720_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1809 and pb==pc
for stem,count in [('NATIVE_PROTECTED',820),('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26720_{stem}_BASE.sha256'); y=load(f'26720_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count,(stem,len(x),len(y)); assert x==y,stem
sb=load('26720_ASSET_SHADER_UNIVERSE_BASE.sha256'); sc=load('26720_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(sb)==len(sc)==271
shader_delta={k for k in sb|sc if sb.get(k)!=sc.get(k)}; assert shader_delta=={'app/src/main/assets/shaders/motionv2/color_transform.glsl'},shader_delta
print('PASS 26720 authority/manifests: exact successful 26719 compiled candidate -> exact 14-file 26720 candidate; 1809 protected / 820 native / 1 vendor / 6 DNG invariant; shader universe 271 with exact color_transform delta')
