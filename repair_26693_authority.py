#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: repair_26693_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); b=Path(sys.argv[2]); c=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if not line.strip():continue
  h,r=line.split(None,1);out[r.strip()]=h
 return out
def actual(x):return {'app/'+str(p.relative_to(x/'app')):sha(p) for p in sorted((x/'app').rglob('*')) if p.is_file()}
B=actual(b);C=actual(c); assert len(B)==len(C)==1822
assert B==load('26693_BASE_26692_R1_1_FULL_APP.sha256')
assert C==load('26693_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=[x.strip() for x in (pkg/'26693_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
assert sorted(k for k in B if B[k]!=C[k])==sorted(changed) and len(changed)==7
prot=[k for k in B if k not in changed]; assert len(prot)==1815 and all(B[k]==C[k] for k in prot)
for name,count in [('26693_NATIVE_FULL_BASE.sha256',819),('26693_VENDOR_PROTECTED_BASE.sha256',778),('26693_DNG_BASE.sha256',7),('26693_ASSET_SHADER_UNIVERSE_BASE.sha256',271)]: assert len(load(name))==count
for a,z in [('26693_NATIVE_FULL_BASE.sha256','26693_NATIVE_FULL_CANDIDATE.sha256'),('26693_VENDOR_PROTECTED_BASE.sha256','26693_VENDOR_PROTECTED_CANDIDATE.sha256'),('26693_DNG_BASE.sha256','26693_DNG_CANDIDATE.sha256'),('26693_ASSET_SHADER_UNIVERSE_BASE.sha256','26693_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]: assert (pkg/a).read_bytes()==(pkg/z).read_bytes()
so=c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'; assert sha(so)=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26693 authority/manifests: exact 1822-file 26692 R1.1 base, 7 changes, 1815 protected, 819 native, 778 vendor, 7 DNG, 271 shaders')
