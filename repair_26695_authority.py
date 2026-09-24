#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: repair_26695_authority.py ROOT BASE CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 out={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip():h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(x):return {'app/'+str(p.relative_to(x/'app')):sha(p) for p in sorted((x/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c);assert len(B)==len(C)==1822;assert B==load('26695_BASE_26694_FULL_APP.sha256');assert C==load('26695_EXPECTED_CANDIDATE_FULL_APP.sha256')
ch=[x.strip() for x in (pkg/'26695_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()];assert len(ch)==4 and sorted(k for k in B if B[k]!=C[k])==sorted(ch)
prot=[k for k in B if k not in ch];assert len(prot)==1818 and all(B[k]==C[k] for k in prot)
for n,count in [('26695_NATIVE_FULL_BASE.sha256',819),('26695_VENDOR_PROTECTED_BASE.sha256',778),('26695_DNG_BASE.sha256',7),('26695_ASSET_SHADER_UNIVERSE_BASE.sha256',271)]:assert len(load(n))==count
for a,z in [('26695_NATIVE_FULL_BASE.sha256','26695_NATIVE_FULL_CANDIDATE.sha256'),('26695_VENDOR_PROTECTED_BASE.sha256','26695_VENDOR_PROTECTED_CANDIDATE.sha256'),('26695_DNG_BASE.sha256','26695_DNG_CANDIDATE.sha256'),('26695_ASSET_SHADER_UNIVERSE_BASE.sha256','26695_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]:assert (pkg/a).read_bytes()==(pkg/z).read_bytes()
assert sha(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26695 authority/manifests: exact 1822-file successful 26694 base, 4 changes, 1818 protected, 819 native, 778 vendor, 7 DNG, 271 shaders')
