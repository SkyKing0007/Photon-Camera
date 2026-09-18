#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26667_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def verify(m,tree,label):
 for r,h in m.items():
  p=tree/r
  if not p.is_file() or sha(p)!=h: raise SystemExit(f'FAIL {label}: {r}')
bm=readm(root/'R1_26667_BASE_26666_FULL_APP.sha256'); cm=readm(root/'R1_26667_EXPECTED_CANDIDATE_FULL_APP.sha256')
bp=readm(root/'R1_26667_PROTECTED_UNCHANGED_BASE.sha256'); cp=readm(root/'R1_26667_PROTECTED_UNCHANGED_CANDIDATE.sha256')
assert len(bm)==len(cm)==1721,(len(bm),len(cm)); assert len(bp)==len(cp)==1717
verify(bm,base,'base full'); verify(cm,cand,'candidate full'); verify(bp,base,'base protected'); verify(cp,cand,'candidate protected')
changed=[x for x in (root/'R1_26667_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(changed)==4 and not (root/'R1_26667_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
actual=sorted(r for r in bm if bm[r]!=cm[r]); assert actual==sorted(changed),(actual,changed)
for stem,count in [('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=readm(root/f'R1_26667_{stem}_BASE.sha256'); b=readm(root/f'R1_26667_{stem}_CANDIDATE.sha256'); assert len(a)==len(b)==count and a==b; verify(a,base,stem+' base');verify(b,cand,stem+' candidate')
print('PASS 26667 authority/manifests: 1721 base / 1721 candidate / 1717 protected / 807 native / 778 vendor / 7 DNG / 4 changed / 0 added')
