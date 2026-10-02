#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26752_authority.py ROOT BASE26733 CAND26752')
pkg,b,c=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823; assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in B|C)
bm=load('26752_BASE_26733_FULL_APP.sha256'); cm=load('26752_EXPECTED_CANDIDATE_FULL_APP.sha256'); am=load('26752_EXACT_26733_CANDIDATE_AUTHORITY.sha256'); assert B==bm==am and C==cm and len(bm)==len(cm)==1823
changed=set((pkg/'26752_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==11 and {k for k in B|C if B.get(k)!=C.get(k)}==changed
assert not (pkg/'26752_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
pb=load('26752_PROTECTED_UNCHANGED_BASE.sha256'); pc=load('26752_PROTECTED_UNCHANGED_CANDIDATE.sha256'); assert len(pb)==len(pc)==1812 and pb==pc
# Native full domain intentionally changes only the one allowed JNI file; protected native remains exact.
nb=load('26752_NATIVE_FULL_BASE.sha256'); nc=load('26752_NATIVE_FULL_CANDIDATE.sha256'); assert len(nb)==len(nc)==819
native_changed={k for k in nb|nc if nb.get(k)!=nc.get(k)}; assert native_changed=={'app/src/main/cpp/motionv2_jpeg444_jni.cpp'},native_changed
npb=load('26752_NATIVE_PROTECTED_BASE.sha256'); npc=load('26752_NATIVE_PROTECTED_CANDIDATE.sha256'); assert len(npb)==len(npc)==818 and npb==npc
for stem,count in [('VENDOR_PROTECTED',1),('DNG',6)]:
 x=load(f'26752_{stem}_BASE.sha256'); y=load(f'26752_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y,stem
ab=load('26752_ASSET_SHADER_UNIVERSE_BASE.sha256'); ac=load('26752_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(ab)==len(ac)==271
ash={k for k in ab|ac if ab.get(k)!=ac.get(k)}; assert ash=={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'},ash
print('PASS 26752 authority/manifests: exact successful 26733 candidate -> exact 11-file 26752 candidate; 1812 protected / 818 protected-native / 1 vendor / 6 named-DNG invariant; asset shader universe 271 with exactly 2 intended shader changes')
