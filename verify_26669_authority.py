#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26669_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readm(p):
    d={}
    for line in Path(p).read_text().splitlines():
        if line.strip(): h,r=line.split('  ',1); d[r]=h
    return d
def verify(m,tree,label):
    for r,h in m.items():
        p=tree/r
        if not p.is_file() or sha(p)!=h: raise SystemExit(f'FAIL {label}: {r}')
bm=readm(root/'R1_26669_BASE_26668_FULL_APP.sha256')
cm=readm(root/'R1_26669_EXPECTED_CANDIDATE_FULL_APP.sha256')
bp=readm(root/'R1_26669_PROTECTED_UNCHANGED_BASE.sha256')
cp=readm(root/'R1_26669_PROTECTED_UNCHANGED_CANDIDATE.sha256')
assert len(bm)==len(cm)==1725,(len(bm),len(cm))
assert len(bp)==len(cp)==1719,(len(bp),len(cp))
verify(bm,base,'base full'); verify(cm,cand,'candidate full')
verify(bp,base,'base protected'); verify(cp,cand,'candidate protected')
assert bp==cp,'protected manifest bytes differ'
changed=[x for x in (root/'R1_26669_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26669_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==6 and not added
actual=sorted(r for r in set(bm)|set(cm) if bm.get(r)!=cm.get(r))
assert actual==sorted(changed),(actual,sorted(changed))
assert not [r for r in changed if r not in bm]
for stem,count in [('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
    a=readm(root/f'R1_26669_{stem}_BASE.sha256'); b=readm(root/f'R1_26669_{stem}_CANDIDATE.sha256')
    assert len(a)==len(b)==count,(stem,len(a),len(b)); assert a==b,stem
    verify(a,base,stem+' base'); verify(b,cand,stem+' candidate')
print('PASS 26669 authority/manifests: 1725 base / 1725 candidate / 1719 protected / 807 native / 778 vendor / 7 DNG / 6 modified / 0 added')
