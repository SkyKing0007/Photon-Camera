#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: verify_26684_authority.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mf(p):
 out={}
 for line in p.read_text().splitlines():
  if line.strip():hh,rel=line.split('  ',1);out[rel]=hh
 return out
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base);b=snap(cand)
if a!=mf(root/'R1_26684_BASE_26683_R1_FULL_APP.sha256') or b!=mf(root/'R1_26684_EXPECTED_CANDIDATE_FULL_APP.sha256'):raise SystemExit('FAIL full manifests')
allow=set((root/'R1_26684_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if actual!=allow:raise SystemExit('FAIL allowlist '+repr(actual))
prot=mf(root/'R1_26684_PROTECTED_UNCHANGED_BASE.sha256')
if len(prot)!=1757:raise SystemExit('FAIL protected count')
for rel,hh in prot.items():
 if a.get(rel)!=hh or b.get(rel)!=hh:raise SystemExit('FAIL protected '+rel)
for name,count in [('R1_26684_NATIVE_PROTECTED_BASE.sha256',804),('R1_26684_VENDOR_PROTECTED_BASE.sha256',778),('R1_26684_DNG_BASE.sha256',7),('R1_26684_SHADER_UNIVERSE_BASE.sha256',271)]:
 m=mf(root/name)
 if len(m)!=count:raise SystemExit('FAIL manifest count '+name)
 for rel,hh in m.items():
  if a.get(rel)!=hh or b.get(rel)!=hh:raise SystemExit('FAIL protected-domain byte '+rel)
if 'app/src/main/cpp/spektra/SpektraNativeJni.cpp' in mf(root/'R1_26684_NATIVE_PROTECTED_BASE.sha256'):raise SystemExit('FAIL changed Spektra native file contaminated protected-native universe')
print('PASS 26684 authority: 1764 base / 1764 candidate / 1757 protected / 804 native-protected / 778 vendor / 7 DNG / 271 shaders')
