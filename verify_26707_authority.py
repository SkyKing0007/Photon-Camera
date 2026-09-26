#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit("usage: verify_26707_authority.py ROOT BASE26706 CANDIDATE")
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def actual(r):return {'app/'+str(p.relative_to(r/'app')):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1823
assert B==load('26707_BASE_26706_FULL_APP.sha256');assert C==load('26707_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26707_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(changed)==5
assert {k for k in set(B)|set(C) if B.get(k)!=C.get(k)}==set(changed)
for a,d,n in [('26707_PROTECTED_UNCHANGED_BASE.sha256','26707_PROTECTED_UNCHANGED_CANDIDATE.sha256',1818),('26707_NATIVE_PROTECTED_BASE.sha256','26707_NATIVE_PROTECTED_CANDIDATE.sha256',819),('26707_VENDOR_PROTECTED_BASE.sha256','26707_VENDOR_PROTECTED_CANDIDATE.sha256',778),('26707_DNG_BASE.sha256','26707_DNG_CANDIDATE.sha256',7),('26707_ASSET_SHADER_UNIVERSE_BASE.sha256','26707_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271)]:
 A=load(a);D=load(d);assert len(A)==len(D)==n,(a,len(A),len(D));assert A==D,a
 for rel,h in A.items():assert B[rel]==h and C[rel]==h,(a,rel)
NFb=load('26707_NATIVE_FULL_BASE.sha256');NFc=load('26707_NATIVE_FULL_CANDIDATE.sha256');assert len(NFb)==len(NFc)==819 and NFb==NFc
print('PASS 26707 authority/manifests revised: 1823 base + candidate; 5 changed; 1818 protected; all 819 native, 778 vendor, 7 DNG and 271 asset shaders invariant')
