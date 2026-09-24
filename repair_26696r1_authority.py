#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=5:raise SystemExit('usage: repair_26696r1_authority.py ROOT BASE26695 ROLLBACK26694 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);r94=Path(sys.argv[3]);c=Path(sys.argv[4])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 out={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(x):return {'app/'+str(p.relative_to(x/'app')):sha(p) for p in sorted((x/'app').rglob('*')) if p.is_file()}
B=actual(b);R=actual(r94);C=actual(c);assert len(B)==1822 and len(R)==1822 and len(C)==1823
assert B==load('26696R1_BASE_26695_FULL_APP.sha256');assert R==load('26696R1_REFERENCE_26694_FULL_APP.sha256');assert C==load('26696R1_EXPECTED_CANDIDATE_FULL_APP.sha256')
ch=[x.strip() for x in (pkg/'26696R1_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]; add=[x.strip() for x in (pkg/'26696R1_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
assert len(ch)==9 and len(add)==1 and sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))==sorted(ch)
prot=[k for k in B if k not in ch];assert len(prot)==1814 and all(B[k]==C[k] for k in prot)
for n,count in [('26696R1_NATIVE_FULL_BASE.sha256',819),('26696R1_VENDOR_PROTECTED_BASE.sha256',778),('26696R1_DNG_BASE.sha256',7),('26696R1_ASSET_SHADER_UNIVERSE_BASE.sha256',271)]:assert len(load(n))==count
for a,z in [('26696R1_NATIVE_FULL_BASE.sha256','26696R1_NATIVE_FULL_CANDIDATE.sha256'),('26696R1_NATIVE_PROTECTED_BASE.sha256','26696R1_NATIVE_PROTECTED_CANDIDATE.sha256'),('26696R1_VENDOR_PROTECTED_BASE.sha256','26696R1_VENDOR_PROTECTED_CANDIDATE.sha256'),('26696R1_DNG_BASE.sha256','26696R1_DNG_CANDIDATE.sha256'),('26696R1_ASSET_SHADER_UNIVERSE_BASE.sha256','26696R1_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]:assert (pkg/a).read_bytes()==(pkg/z).read_bytes()
rest=load('26696R1_RESTORED_26694_SOURCE_HASHES.sha256');assert len(rest)==3 and all(sha(r94/k)==v for k,v in rest.items())
assert sha(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26696 R1 authority/manifests: exact 1822-file successful 26695 base + exact 1822-file successful 26694 rollback reference; 8 modified + 1 added; 1814 protected; 819 native; 778 vendor; 7 DNG; 271 shaders')
