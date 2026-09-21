#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26681_authority.py ROOT BASE CAND')
R=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def readm(n):
 d={}
 for x in (R/n).read_text().splitlines():
  if x.strip(): h,p=x.split('  ',1); d[p]=h
 return d
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root,m):
 for rel,h in m.items():
  p=root/rel
  assert p.is_file() and sha(p)==h,rel
base=readm('R1_26681_BASE_26680_R1_FULL_APP.sha256'); cand=readm('R1_26681_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert len(base)==1727 and len(cand)==1764;check(B,base);check(C,cand)
for stem,count in [('PROTECTED_UNCHANGED',1715),('NATIVE_PROTECTED',804),('VENDOR_PROTECTED',778),('DNG',7)]:
 bm=readm(f'R1_26681_{stem}_BASE.sha256');cm=readm(f'R1_26681_{stem}_CANDIDATE.sha256')
 assert len(bm)==len(cm)==count,(stem,len(bm),len(cm));assert bm==cm;check(B,bm);check(C,cm)
changed=[x for x in (R/'R1_26681_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
payload=R/'handoff_payload_26681'; pf={str(p.relative_to(payload)).replace('\\','/') for p in payload.rglob('*') if p.is_file()}
assert pf==set(changed) and len(pf)==49
assert len(readm('R1_26681_SHADER_UNIVERSE_BASE.sha256'))==257
assert len(readm('R1_26681_SHADER_UNIVERSE_CANDIDATE.sha256'))==271
print('PASS 26681 authority: 1727 base / 1764 candidate / 1715 protected / 804 native / 778 vendor / 7 DNG / 257->271 shaders / 49 payload')
