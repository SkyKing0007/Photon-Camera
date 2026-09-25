#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26706_authority.py ROOT BASE26705 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def actual(r):return {'app/'+str(p.relative_to(r/'app')):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1823
assert B==load('26706_BASE_26705_FULL_APP.sha256');assert C==load('26706_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26706_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(changed)==6
assert {k for k in set(B)|set(C) if B.get(k)!=C.get(k)}==set(changed)
for a,d,n,same in [
 ('26706_PROTECTED_UNCHANGED_BASE.sha256','26706_PROTECTED_UNCHANGED_CANDIDATE.sha256',1817,True),
 ('26706_NATIVE_PROTECTED_BASE.sha256','26706_NATIVE_PROTECTED_CANDIDATE.sha256',819,True),
 ('26706_VENDOR_PROTECTED_BASE.sha256','26706_VENDOR_PROTECTED_CANDIDATE.sha256',778,True),
 ('26706_DNG_BASE.sha256','26706_DNG_CANDIDATE.sha256',7,True),
 ('26706_ASSET_SHADER_UNIVERSE_BASE.sha256','26706_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271,False)]:
 A=load(a);D=load(d);assert len(A)==len(D)==n,(a,len(A),len(D))
 if same: assert A==D,a
 for rel,h in A.items(): assert B[rel]==h,(a,rel)
 for rel,h in D.items(): assert C[rel]==h,(d,rel)
NFb=load('26706_NATIVE_FULL_BASE.sha256');NFc=load('26706_NATIVE_FULL_CANDIDATE.sha256');assert len(NFb)==len(NFc)==819 and NFb==NFc
assetB=load('26706_ASSET_SHADER_UNIVERSE_BASE.sha256');assetC=load('26706_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')
assetChanged={r for r in assetB if assetB[r]!=assetC[r]}
assert assetChanged=={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'},assetChanged
print('PASS 26706 authority/manifests: 1823 base + candidate; 6 changed; 1817 protected; all 819 native, 778 vendor, 7 DNG invariant; exactly 2/271 asset shaders changed')
