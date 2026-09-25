#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: verify_26704_authority.py ROOT BASE26703 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(root):return {'app/'+str(p.relative_to(root/'app')):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1823,(len(B),len(C))
assert B==load('26704_BASE_26703_FULL_APP.sha256');assert C==load('26704_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26704_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(changed)==11
assert {k for k in set(B)|set(C) if B.get(k)!=C.get(k)}==set(changed)
for a,d,n in [('26704_PROTECTED_UNCHANGED_BASE.sha256','26704_PROTECTED_UNCHANGED_CANDIDATE.sha256',1812),('26704_NATIVE_PROTECTED_BASE.sha256','26704_NATIVE_PROTECTED_CANDIDATE.sha256',818),('26704_VENDOR_PROTECTED_BASE.sha256','26704_VENDOR_PROTECTED_CANDIDATE.sha256',778),('26704_DNG_BASE.sha256','26704_DNG_CANDIDATE.sha256',7)]:
 A=load(a);D=load(d);assert len(A)==len(D)==n,(a,len(A),len(D));assert A==D,a
 for rel,hh in A.items():assert B[rel]==hh and C[rel]==hh,(a,rel)
NFb=load('26704_NATIVE_FULL_BASE.sha256');NFc=load('26704_NATIVE_FULL_CANDIDATE.sha256');assert len(NFb)==len(NFc)==819
assert {k for k in NFb if NFb[k]!=NFc[k]}=={'app/src/main/cpp/motionv2_jpeg444_jni.cpp'}
SB=load('26704_ASSET_SHADER_UNIVERSE_BASE.sha256');SC=load('26704_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(SB)==len(SC)==271
assert {k for k in SB if SB[k]!=SC[k]}=={'app/src/main/assets/shaders/motionv2/render.glsl'}
print('PASS 26704 authority/manifests: 1823 base + candidate; 11 changed; 1812 protected; 818 native-protected/819 native-full one delta; 778 vendor; 7 DNG; 271 asset shaders one delta')
