#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26643_r1_authority.py ROOT BASE CANDIDATE')
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
bm=check('R1_26643_BASE_26642_R1_FULL_APP.sha256',base)
cm=check('R1_26643_EXPECTED_CANDIDATE_FULL_APP.sha256',cand)
assert len(bm)==1719 and len(cm)==1720
allow={r for r in (root/'R1_26643_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}
added={r for r in (root/'R1_26643_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if r}
assert len(allow)==10 and len(added)==1 and added<=allow
assert set(cm)-set(bm)==added and set(bm)-set(cm)==set()
changed_existing={r for r in set(bm)&set(cm) if bm[r]!=cm[r]}
assert changed_existing==(allow-added) and len(changed_existing)==9,(changed_existing,allow-added)
for prefix,count in [('PROTECTED_UNCHANGED',1710),('NATIVE_PROTECTED',800),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=check(f'R1_26643_{prefix}_BASE.sha256',base); b=check(f'R1_26643_{prefix}_CANDIDATE.sha256',cand)
 assert len(a)==len(b)==count and a==b,(prefix,len(a),len(b))
print('PASS 26643 authority: 1719 base / 1720 candidate, exact 10-path allowlist with 1 addition, 1710 protected, 800 native-protected, 778 vendor, 7 DNG byte-invariant')
