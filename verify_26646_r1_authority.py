#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26646_r1_authority.py ROOT BASE CANDIDATE')
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
bm=check('R1_26646_BASE_26645_R1_FULL_APP.sha256',base); cm=check('R1_26646_EXPECTED_CANDIDATE_FULL_APP.sha256',cand)
assert len(bm)==len(cm)==1720 and set(bm)==set(cm)
allow={r for r in (root/'R1_26646_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}; assert len(allow)==9
changed={r for r in bm if bm[r]!=cm[r]}; assert changed==allow,(changed,allow)
for prefix,count in [('PROTECTED_UNCHANGED',1711),('NATIVE_PROTECTED',800),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=check(f'R1_26646_{prefix}_BASE.sha256',base); b=check(f'R1_26646_{prefix}_CANDIDATE.sha256',cand)
 assert len(a)==len(b)==count and a==b,(prefix,len(a),len(b))
print('PASS 26646 authority: 1720 base / 1720 candidate, exact 9-path/0-added allowlist, 1711 protected, inherited 800 native-protected, 778 vendor, 7 DNG byte-invariant')
