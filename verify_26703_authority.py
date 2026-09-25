#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: verify_26703_authority.py ROOT BASE26702 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(root):return {'app/'+str(p.relative_to(root/'app')):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1823,(len(B),len(C))
assert B==load('26703_BASE_26702_FULL_APP.sha256');assert C==load('26703_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26703_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(changed)==3
assert {k for k in set(B)|set(C) if B.get(k)!=C.get(k)}==set(changed)
for a,d,n in [('26703_PROTECTED_UNCHANGED_BASE.sha256','26703_PROTECTED_UNCHANGED_CANDIDATE.sha256',1820),('26703_NATIVE_PROTECTED_BASE.sha256','26703_NATIVE_PROTECTED_CANDIDATE.sha256',819),('26703_VENDOR_PROTECTED_BASE.sha256','26703_VENDOR_PROTECTED_CANDIDATE.sha256',778),('26703_DNG_BASE.sha256','26703_DNG_CANDIDATE.sha256',7),('26703_ASSET_SHADER_UNIVERSE_BASE.sha256','26703_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271)]:
 A=load(a);D=load(d);assert len(A)==len(D)==n,(a,len(A),len(D));assert A==D,a
 for rel,hh in A.items():assert B[rel]==hh and C[rel]==hh,(a,rel)
NFb=load('26703_NATIVE_FULL_BASE.sha256');NFc=load('26703_NATIVE_FULL_CANDIDATE.sha256');assert len(NFb)==len(NFc)==819 and NFb==NFc
print('PASS 26703 authority/manifests: 1823 base + 1823 candidate; 3 changed; 1820 protected; all 819 native, 778 vendor, 7 DNG and 271 asset shaders invariant')
