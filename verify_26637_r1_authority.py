#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26637_r1_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(name):
 d={}
 for l in (root/name).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def actual(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b=actual(base); c=actual(cand)
mb=readm('R1_26637_BASE_26636_R1_FULL_APP.sha256'); mc=readm('R1_26637_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(b)==len(c)==len(mb)==len(mc)==1716 and b==mb and c==mc
changed=[x for x in (root/'R1_26637_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert changed==['app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/version.properties']
assert {p for p in b if b[p]!=c[p]}==set(changed)
for prefix,count in [('PROTECTED_UNCHANGED',1713),('NATIVE_PROTECTED',802),('VENDOR_PROTECTED',778),('DNG',7)]:
 bm=readm(f'R1_26637_{prefix}_BASE.sha256'); cm=readm(f'R1_26637_{prefix}_CANDIDATE.sha256')
 assert len(bm)==len(cm)==count and bm==cm
 for rel,h in bm.items(): assert b[rel]==c[rel]==h, (prefix,rel)
assert 'VERSION_NAME=0.9726637' in (cand/'app/version.properties').read_text()
assert 'VERSION_BUILD=26637' in (cand/'app/version.properties').read_text()
print('PASS 26637 authority: exact successful-26636 1716-file base + exact 3-path delta + 1713/802/778/7 protected invariance')
