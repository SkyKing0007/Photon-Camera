#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26676_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def amap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bm=amap(base); cm=amap(cand); assert len(bm)==len(cm)==1726
assert bm==pm(root/'R1_26676_BASE_26675_FULL_APP.sha256'),'base full manifest mismatch'
assert cm==pm(root/'R1_26676_EXPECTED_CANDIDATE_FULL_APP.sha256'),'candidate full manifest mismatch'
changed=[x for x in (root/'R1_26676_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26676_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
deleted=[x for x in (root/'R1_26676_DELETED_PATHS_MUST_EXIST.txt').read_text().splitlines() if x]
mods=sorted(p for p in bm.keys()&cm.keys() if bm[p]!=cm[p]); adds=sorted(cm.keys()-bm.keys()); dels=sorted(bm.keys()-cm.keys())
assert len(changed)==9 and len(mods)==7 and len(adds)==len(dels)==1
assert sorted(changed)==sorted(mods+adds+dels) and adds==sorted(added) and dels==sorted(deleted)
for name,count in [('PROTECTED_UNCHANGED',1718),('NATIVE_PROTECTED',805),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=pm(root/f'R1_26676_{name}_BASE.sha256'); b=pm(root/f'R1_26676_{name}_CANDIDATE.sha256'); assert len(a)==len(b)==count,(name,len(a),len(b)); assert a==b,name
 for p,h in a.items(): assert bm[p]==cm[p]==h,(name,p)
for p in list(bm)+list(cm):
 assert not p.startswith('app/build/') and not p.startswith('app/.cxx/'),p
print('PASS 26676 authority: exact successful-26675 1726-file compiled candidate; 7 modifications / 1 addition / 1 deletion; 1718 protected / 805 native-protected / 778 vendor / 7 DNG invariant')
