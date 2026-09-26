#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[2]);c=Path(sys.argv[3])
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823; assert B==load('26708_BASE_26707_FULL_APP.sha256'); assert C==load('26708_EXPECTED_CANDIDATE_FULL_APP.sha256')
changed=set((pkg/'26708_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==8; assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
assert load('26708_PROTECTED_UNCHANGED_BASE.sha256')==load('26708_PROTECTED_UNCHANGED_CANDIDATE.sha256')
for stem in ['NATIVE_PROTECTED','NATIVE_FULL','VENDOR_PROTECTED','DNG','ASSET_SHADER_UNIVERSE']:
 assert load(f'26708_{stem}_BASE.sha256')==load(f'26708_{stem}_CANDIDATE.sha256'),stem
print('PASS 26708 authority/manifests: exact 26707 compiled candidate -> exact 8-file 26708 candidate; protected/native/vendor/DNG/asset-shader invariant')
