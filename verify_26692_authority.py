#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26692_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
def parse(name):
 out={}
 for line in (pkg/name).read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); out[p]=h
 return out
def check(r,name,n):
 m=parse(name); assert len(m)==n,(name,len(m),n)
 for rel,h in m.items():
  p=r/rel; assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h,f'{name}: {rel}'
 return m
check(base,'R1_26692_BASE_26691_R1_FULL_APP.sha256',1822); check(cand,'R1_26692_EXPECTED_CANDIDATE_FULL_APP.sha256',1822)
check(base,'R1_26692_PROTECTED_UNCHANGED_BASE.sha256',1811); check(cand,'R1_26692_PROTECTED_UNCHANGED_CANDIDATE.sha256',1811)
for a,b,n in [('R1_26692_NATIVE_PROTECTED_BASE.sha256','R1_26692_NATIVE_PROTECTED_CANDIDATE.sha256',819),('R1_26692_NATIVE_FULL_BASE.sha256','R1_26692_NATIVE_FULL_CANDIDATE.sha256',819),('R1_26692_VENDOR_PROTECTED_BASE.sha256','R1_26692_VENDOR_PROTECTED_CANDIDATE.sha256',778),('R1_26692_DNG_BASE.sha256','R1_26692_DNG_CANDIDATE.sha256',7),('R1_26692_ASSET_SHADER_UNIVERSE_BASE.sha256','R1_26692_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256',271)]:
 ma=check(base,a,n); mb=check(cand,b,n); assert ma==mb,a
assert len([x for x in (pkg/'R1_26692_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x])==11
so=cand/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'; assert hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26692 authority: exact successful 26691 compiled candidate + exact 11-path overlay; protected/native/vendor/DNG/shaders invariant')
