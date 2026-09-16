#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_r1_2_26648_authority.py ROOT BASE CANDIDATE')
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
bm=check('R1_2_26648_BASE_R1_1_FULL_APP.sha256',base); cm=check('R1_2_26648_EXPECTED_CANDIDATE_FULL_APP.sha256',cand)
assert len(bm)==len(cm)==1720 and bm==cm
allow={r for r in (root/'R1_2_26648_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}; assert not allow
assert not {r for r in bm if bm[r]!=cm[r]}
for prefix,count in [('PROTECTED_UNCHANGED',1720),('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=check(f'R1_2_26648_{prefix}_BASE.sha256',base); b=check(f'R1_2_26648_{prefix}_CANDIDATE.sha256',cand)
 assert len(a)==len(b)==count and a==b,(prefix,len(a),len(b))
for prefix,rootp in [('SHADER_UNIVERSE_BASE',base),('SHADER_UNIVERSE_CANDIDATE',cand)]:
 m=check(f'R1_2_26648_{prefix}.sha256',rootp); assert len(m)==257
assert readm(root/'R1_2_26648_SHADER_UNIVERSE_BASE.sha256')==readm(root/'R1_2_26648_SHADER_UNIVERSE_CANDIDATE.sha256')
print('PASS 26648 R1.2 authority: exact successful R1.1 compiled candidate, 1720 base/candidate byte-identical, 0 changed/0 added, 1720 protected, 807 native, 778 vendor, 7 DNG, 257 shader universe')
