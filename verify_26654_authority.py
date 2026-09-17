#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26654_authority.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def check(name,rt):
 m=readm(root/name)
 for r,h in m.items():
  p=rt/r
  if not p.is_file() or sha(p)!=h: raise SystemExit(f'{name}: mismatch {r}')
 return m
bm=check('R1_26654_BASE_26653_FULL_APP.sha256',base); cm=check('R1_26654_EXPECTED_CANDIDATE_FULL_APP.sha256',cand); assert len(bm)==len(cm)==1721
allow={r for r in (root/'R1_26654_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}; added={r for r in (root/'R1_26654_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if r}; assert len(allow)==8 and not added
actual={r for r in set(bm)|set(cm) if bm.get(r)!=cm.get(r)}; assert actual==allow,(actual^allow)
for prefix,count in [('PROTECTED_UNCHANGED',1713),('NATIVE_PROTECTED',807),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=check(f'R1_26654_{prefix}_BASE.sha256',base); b=check(f'R1_26654_{prefix}_CANDIDATE.sha256',cand); assert len(a)==len(b)==count and a==b
sb=check('R1_26654_SHADER_UNIVERSE_BASE.sha256',base); sc=check('R1_26654_SHADER_UNIVERSE_CANDIDATE.sha256',cand); assert len(sb)==len(sc)==257
shader_changed={r for r in set(sb)|set(sc) if sb.get(r)!=sc.get(r)}
assert shader_changed=={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'},shader_changed
print('PASS 26654 authority: exact successful 26653 base 1721 -> candidate 1721; exactly 8 changed / 0 added / 1713 protected / 807 native / 778 vendor / 7 DNG / 257 standalone shaders with exactly 4 intended GLSL assets changed')
