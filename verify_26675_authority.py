#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26675_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def amap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bm=amap(base); cm=amap(cand); assert len(bm)==len(cm)==1726
assert bm==pm(root/'R1_26675_BASE_26674_FULL_APP.sha256'),'base full manifest mismatch'
assert cm==pm(root/'R1_26675_EXPECTED_CANDIDATE_FULL_APP.sha256'),'candidate full manifest mismatch'
changed=[x for x in (root/'R1_26675_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; added=[x for x in (root/'R1_26675_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
mods=sorted(p for p in bm if bm[p]!=cm[p]); assert len(changed)==8 and mods==sorted(changed) and not added and set(bm)==set(cm)
for name,count in [('PROTECTED_UNCHANGED',1718),('NATIVE_PROTECTED',806),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=pm(root/f'R1_26675_{name}_BASE.sha256'); b=pm(root/f'R1_26675_{name}_CANDIDATE.sha256'); assert len(a)==len(b)==count,(name,len(a),len(b)); assert a==b,name
 for p,h in a.items(): assert bm[p]==cm[p]==h,(name,p)
print('PASS 26675 authority: exact successful-26674 1726-file compiled candidate; exact 8 modifications / 0 additions / 0 deletions; 1718 protected / 806 native-protected / 778 vendor / 7 DNG invariant')
