#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4:raise SystemExit('usage: verify_26683_authority.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mf(p):
 out={}
 for line in p.read_text().splitlines():
  if line.strip():hh,rel=line.split('  ',1);out[rel]=hh
 return out
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base);b=snap(cand)
if a!=mf(root/'R1_26683_BASE_26682_R1_1_FULL_APP.sha256') or b!=mf(root/'R1_26683_EXPECTED_CANDIDATE_FULL_APP.sha256'):raise SystemExit('FAIL full manifests')
allow=set((root/'R1_26683_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if actual!=allow:raise SystemExit('FAIL allowlist '+repr(actual))
prot=mf(root/'R1_26683_PROTECTED_UNCHANGED_BASE.sha256')
if len(prot)!=1758:raise SystemExit('FAIL protected count')
for rel,hh in prot.items():
 if a.get(rel)!=hh or b.get(rel)!=hh:raise SystemExit('FAIL protected '+rel)
for name,count in [('R1_26683_NATIVE_PROTECTED_BASE.sha256',804),('R1_26683_VENDOR_PROTECTED_BASE.sha256',778),('R1_26683_DNG_BASE.sha256',7),('R1_26683_SHADER_UNIVERSE_BASE.sha256',271)]:
 if len(mf(root/name))!=count:raise SystemExit('FAIL manifest count '+name)
print('PASS 26683 authority: 1764 base / 1764 candidate / 1758 protected / 804 native / 778 vendor / 7 DNG / 271 shaders')
