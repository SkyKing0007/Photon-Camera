#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26671_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def amap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bm=amap(base); cm=amap(cand); assert len(bm)==len(cm)==1725 and set(bm)==set(cm)
assert bm==pm(root/'R1_26671_BASE_26670_FULL_APP.sha256'),'base full manifest mismatch'
assert cm==pm(root/'R1_26671_EXPECTED_CANDIDATE_FULL_APP.sha256'),'candidate full manifest mismatch'
changed=[x for x in (root/'R1_26671_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; actual=sorted(p for p in bm if bm[p]!=cm[p])
assert actual==sorted(changed) and len(actual)==5,(actual,changed)
for name,count in [('PROTECTED_UNCHANGED',1720),('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=pm(root/f'R1_26671_{name}_BASE.sha256'); b=pm(root/f'R1_26671_{name}_CANDIDATE.sha256'); assert len(a)==len(b)==count,(name,len(a),len(b)); assert a==b,name
 for p,h in a.items(): assert bm[p]==cm[p]==h,(name,p)
assert (root/'R1_26671_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text()==''
print('PASS 26671 authority: exact successful-26670 1725-file compiled candidate; exact 5 modifications / 0 additions / 0 deletions; 1720 protected / 807 native / 778 vendor / 7 DNG invariant')
