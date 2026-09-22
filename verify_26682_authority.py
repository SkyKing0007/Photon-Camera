#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26682_authority.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_manifest(p):
 out={}
 for line in p.read_text().splitlines():
  if not line.strip(): continue
  hh,rel=line.split('  ',1); out[rel]=hh
 return out
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base); b=snap(cand)
mb=read_manifest(root/'R1_26682_BASE_26681_R1_FULL_APP.sha256'); mc=read_manifest(root/'R1_26682_EXPECTED_CANDIDATE_FULL_APP.sha256')
if a!=mb or b!=mc: raise SystemExit('FAIL full authority manifests')
changed=set((root/'R1_26682_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if actual!=changed: raise SystemExit(f'FAIL allowlist actual={actual}')
prot=read_manifest(root/'R1_26682_PROTECTED_UNCHANGED_BASE.sha256')
if len(prot)!=1759: raise SystemExit('FAIL protected count')
for rel,hh in prot.items():
 if a.get(rel)!=hh or b.get(rel)!=hh: raise SystemExit(f'FAIL protected {rel}')
for name,count in [('R1_26682_NATIVE_PROTECTED_BASE.sha256',804),('R1_26682_VENDOR_PROTECTED_BASE.sha256',778),('R1_26682_DNG_BASE.sha256',7),('R1_26682_SHADER_UNIVERSE_BASE.sha256',271)]:
 if len(read_manifest(root/name))!=count: raise SystemExit(f'FAIL manifest count {name}')
print('PASS 26682 authority: 1764 base / 1764 candidate / 1759 protected / 804 native / 778 vendor / 7 DNG / 271 shaders')
