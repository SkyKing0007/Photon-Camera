#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv) != 4:
    raise SystemExit('usage: verify_26668_authority.py ROOT BASE CANDIDATE')
root, base, cand = map(Path, sys.argv[1:4])

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readm(p):
    d={}
    for line in Path(p).read_text().splitlines():
        if line.strip():
            h,r=line.split('  ',1); d[r]=h
    return d
def verify(m, tree, label):
    for r,h in m.items():
        p=tree/r
        if not p.is_file() or sha(p)!=h:
            raise SystemExit(f'FAIL {label}: {r}')

bm=readm(root/'R1_26668_BASE_26667_FULL_APP.sha256')
cm=readm(root/'R1_26668_EXPECTED_CANDIDATE_FULL_APP.sha256')
bp=readm(root/'R1_26668_PROTECTED_UNCHANGED_BASE.sha256')
cp=readm(root/'R1_26668_PROTECTED_UNCHANGED_CANDIDATE.sha256')
assert len(bm)==1721 and len(cm)==1725,(len(bm),len(cm))
assert len(bp)==len(cp)==1707,(len(bp),len(cp))
verify(bm,base,'base full'); verify(cm,cand,'candidate full')
verify(bp,base,'base protected'); verify(cp,cand,'candidate protected')
assert bp==cp,'protected manifest bytes differ'
changed=[x for x in (root/'R1_26668_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26668_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==18 and len(added)==4 and set(added)<=set(changed)
actual=[]
for r in sorted(set(bm)|set(cm)):
    if bm.get(r)!=cm.get(r): actual.append(r)
assert actual==sorted(changed),(actual,sorted(changed))
assert sorted(r for r in changed if r not in bm)==sorted(added)
for r in added:
    assert r not in bm and r in cm
for stem,count in [('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
    a=readm(root/f'R1_26668_{stem}_BASE.sha256')
    b=readm(root/f'R1_26668_{stem}_CANDIDATE.sha256')
    assert len(a)==len(b)==count,(stem,len(a),len(b))
    assert a==b,stem
    verify(a,base,stem+' base'); verify(b,cand,stem+' candidate')
print('PASS 26668 authority/manifests: 1721 base / 1725 candidate / 1707 protected / 807 native / 778 vendor / 7 DNG / 18 changed / 4 added')
