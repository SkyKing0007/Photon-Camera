#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26689_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
def parse(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); out[p]=h
 return out
def check(rootp, name, expected_count):
 m=parse(name); assert len(m)==expected_count,(name,len(m),expected_count)
 for rel,h in m.items():
  p=rootp/rel; assert p.is_file(),f'{name}: missing {rel}'; assert hashlib.sha256(p.read_bytes()).hexdigest()==h,f'{name}: mismatch {rel}'
 return m
check(base,'R1_26689_BASE_26688_R1_FULL_APP.sha256',1770)
check(cand,'R1_26689_EXPECTED_CANDIDATE_FULL_APP.sha256',1819)
check(base,'R1_26689_PROTECTED_UNCHANGED_BASE.sha256',1764); check(cand,'R1_26689_PROTECTED_UNCHANGED_CANDIDATE.sha256',1764)
for a,b,n in [('R1_26689_NATIVE_PROTECTED_BASE.sha256','R1_26689_NATIVE_PROTECTED_CANDIDATE.sha256',819),('R1_26689_VENDOR_PROTECTED_BASE.sha256','R1_26689_VENDOR_PROTECTED_CANDIDATE.sha256',778),('R1_26689_DNG_BASE.sha256','R1_26689_DNG_CANDIDATE.sha256',7),('R1_26689_ASSET_SHADER_UNIVERSE_BASE.sha256','R1_26689_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271)]:
 ma=check(base,a,n); mb=check(cand,b,n); assert ma==mb,f'invariance failed: {a}'
changed=[x for x in (pkg/'R1_26689_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (pkg/'R1_26689_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==55 and len(added)==49
assert hashlib.sha256((cand/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26689 authority: successful 26688 compiled-candidate universe + exact 55-path overlay; protected/native/vendor/DNG/shaders invariant')
