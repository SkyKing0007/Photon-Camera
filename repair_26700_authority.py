#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: repair_26700_authority.py ROOT BASE26699 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(root):return {'app/'+str(p.relative_to(root/'app')):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1823
assert B==load('26700_BASE_26699_FULL_APP.sha256');assert C==load('26700_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26700_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(changed)==5;assert {k for k in B if B[k]!=C[k]}==set(changed)
pairs=[('26700_PROTECTED_UNCHANGED_BASE.sha256','26700_PROTECTED_UNCHANGED_CANDIDATE.sha256',1818),('26700_NATIVE_PROTECTED_BASE.sha256','26700_NATIVE_PROTECTED_CANDIDATE.sha256',819),('26700_NATIVE_FULL_BASE.sha256','26700_NATIVE_FULL_CANDIDATE.sha256',819),('26700_VENDOR_PROTECTED_BASE.sha256','26700_VENDOR_PROTECTED_CANDIDATE.sha256',778),('26700_DNG_BASE.sha256','26700_DNG_CANDIDATE.sha256',7),('26700_ASSET_SHADER_UNIVERSE_BASE.sha256','26700_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271)]
for a,bb,n in pairs:
 A=load(a);D=load(bb);assert len(A)==len(D)==n,(a,len(A),len(D));assert A==D,a
 for rel,hh in A.items():assert B[rel]==hh and C[rel]==hh,(a,rel)
print('PASS 26700 authority/manifests: 1823 base + 1823 candidate; 1818 protected; 819 native; 778 vendor; 7 DNG; 271 shaders')
