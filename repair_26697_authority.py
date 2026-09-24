#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=4: raise SystemExit('usage: repair_26697_authority.py ROOT BASE26696R1 CANDIDATE')
pkg=Path(__file__).resolve().parent; b=Path(sys.argv[2]); c=Path(sys.argv[3])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip(): h,r=line.split(None,1); out[r.strip()]=h
 return out
def actual(root): return {'app/'+str(p.relative_to(root/'app')):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
B=actual(b); C=actual(c)
assert len(B)==len(C)==1823
assert B==load('26697_BASE_26696R1_FULL_APP.sha256') and C==load('26697_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26697_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
assert len(changed)==5 and sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))==sorted(changed)
prot=[k for k in B if k not in changed]; assert len(prot)==1818 and all(B[k]==C[k] for k in prot)
assert load('26697_PROTECTED_UNCHANGED_BASE.sha256')=={k:B[k] for k in sorted(prot)}
assert load('26697_PROTECTED_UNCHANGED_CANDIDATE.sha256')=={k:C[k] for k in sorted(prot)}
for n,count in [('NATIVE_FULL',819),('NATIVE_PROTECTED',819),('VENDOR_PROTECTED',778),('DNG',7),('ASSET_SHADER_UNIVERSE',271)]:
 a=load(f'26697_{n}_BASE.sha256'); z=load(f'26697_{n}_CANDIDATE.sha256'); assert len(a)==count and a==z
 assert all(B[k]==v and C[k]==v for k,v in a.items())
assert sha(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26697 authority/manifests: exact 1823-file successful 26696 R1 base; 5 modified + 0 added; 1818 protected; 819 native; 778 vendor; 7 DNG; 271 shaders')
