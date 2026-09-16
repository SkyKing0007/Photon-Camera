#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26649_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,rootp):
 m=readm(root/name)
 for r,h in m.items():
  p=rootp/r
  if not p.is_file() or sha(p)!=h: raise SystemExit(f'{name}: mismatch {r}')
 return m
bm=check('R1_26649_BASE_26648_R1_2_FULL_APP.sha256',base); cm=check('R1_26649_EXPECTED_CANDIDATE_FULL_APP.sha256',cand)
assert len(bm)==len(cm)==1720 and set(bm)==set(cm)
allow={r for r in (root/'R1_26649_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}
actual={r for r in bm if bm[r]!=cm[r]}
assert actual==allow and len(actual)==5,(actual,allow)
for name,expected in [('R1_26649_PROTECTED_UNCHANGED_BASE.sha256',1715),('R1_26649_PROTECTED_UNCHANGED_CANDIDATE.sha256',1715),('R1_26649_NATIVE_PROTECTED_BASE.sha256',807),('R1_26649_NATIVE_PROTECTED_CANDIDATE.sha256',807),('R1_26649_VENDOR_PROTECTED_BASE.sha256',778),('R1_26649_VENDOR_PROTECTED_CANDIDATE.sha256',778),('R1_26649_DNG_BASE.sha256',7),('R1_26649_DNG_CANDIDATE.sha256',7)]:
 m=check(name,base if 'BASE' in name else cand); assert len(m)==expected,(name,len(m))
assert readm(root/'R1_26649_PROTECTED_UNCHANGED_BASE.sha256')==readm(root/'R1_26649_PROTECTED_UNCHANGED_CANDIDATE.sha256')
assert readm(root/'R1_26649_NATIVE_PROTECTED_BASE.sha256')==readm(root/'R1_26649_NATIVE_PROTECTED_CANDIDATE.sha256')
assert readm(root/'R1_26649_VENDOR_PROTECTED_BASE.sha256')==readm(root/'R1_26649_VENDOR_PROTECTED_CANDIDATE.sha256')
assert readm(root/'R1_26649_DNG_BASE.sha256')==readm(root/'R1_26649_DNG_CANDIDATE.sha256')
print('PASS 26649 authority: exact 26648 R1.2 base/candidate manifests, 5-path allowlist equality, 1715 protected / 807 native / 778 vendor / 7 DNG invariant')
