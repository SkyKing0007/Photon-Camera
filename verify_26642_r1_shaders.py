#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26642_r1_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4])
if len(sys.argv)==6 and sys.argv[4]!='--compiler': raise SystemExit('expected --compiler')
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
bm=readm(root/'R1_26642_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26642_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==257 and bm==cm
for r,h in bm.items(): assert sha(base/r)==h and sha(cand/r)==h,r
pins=readm(root/'R1_26642_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(pins)==0
print('PASS 26642 shader gate: complete 257-file shader universe byte-identical; 0 modified runtime-expanded GLSL variants; real GLSL compiler not applicable')
