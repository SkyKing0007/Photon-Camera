#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26638_r1_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(name):
 d={}
 for l in (root/name).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def actual(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b=actual(base); c=actual(cand)
mb=readm('R1_26638_BASE_26637_R1_FULL_APP.sha256'); mc=readm('R1_26638_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(b)==len(mb)==1716 and len(c)==len(mc)==1717 and b==mb and c==mc
changed=[x for x in (root/'R1_26638_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26638_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==10 and len(set(changed))==10 and len(added)==1 and added[0] in changed
actual_changed={r for r in set(b)|set(c) if b.get(r)!=c.get(r)}
assert actual_changed==set(changed),(sorted(actual_changed),changed)
assert added[0] not in b and added[0] in c
for prefix,count in [('PROTECTED_UNCHANGED',1707),('NATIVE_PROTECTED',802),('VENDOR_PROTECTED',778),('DNG',7)]:
 bm=readm(f'R1_26638_{prefix}_BASE.sha256'); cm=readm(f'R1_26638_{prefix}_CANDIDATE.sha256')
 assert len(bm)==len(cm)==count and bm==cm
 for rel,h in bm.items(): assert b[rel]==c[rel]==h,(prefix,rel)
assert 'VERSION_NAME=0.9726638' in (cand/'app/version.properties').read_text()
assert 'VERSION_BUILD=26638' in (cand/'app/version.properties').read_text()
print('PASS 26638 authority: exact successful-26637 1716-file base + exact 10-path/1-added delta + 1707/802/778/7 protected invariance')
