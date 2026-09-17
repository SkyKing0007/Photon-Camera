#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26656_authority.py ROOT BASE CANDIDATE')
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
bm=check('R1_26656_BASE_26655_FULL_APP.sha256',base); cm=check('R1_26656_EXPECTED_CANDIDATE_FULL_APP.sha256',cand)
assert len(bm)==1721 and len(cm)==1726
allow={r for r in (root/'R1_26656_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if r}; added={r for r in (root/'R1_26656_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if r}
assert len(allow)==11 and len(added)==5 and added<=allow
actual={r for r in set(bm)|set(cm) if bm.get(r)!=cm.get(r)}; assert actual==allow,(actual^allow)
assert all(r not in bm and r in cm for r in added)
for prefix,count in [('PROTECTED_UNCHANGED',1715),('NATIVE_PROTECTED',806),('VENDOR_PROTECTED',778),('DNG',7)]:
 a=check(f'R1_26656_{prefix}_BASE.sha256',base); b=check(f'R1_26656_{prefix}_CANDIDATE.sha256',cand); assert len(a)==len(b)==count and a==b
sb=check('R1_26656_SHADER_UNIVERSE_BASE.sha256',base); sc=check('R1_26656_SHADER_UNIVERSE_CANDIDATE.sha256',cand); assert len(sb)==257 and len(sc)==262
shader_changed={r for r in set(sb)|set(sc) if sb.get(r)!=sc.get(r)}
expected={
'app/src/main/assets/shaders/local_laplacian/downsample.glsl','app/src/main/assets/shaders/local_laplacian/reconstruct.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/photon_new_log_luma.glsl','app/src/main/assets/shaders/motionv2/photon_new_precolor.glsl','app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl'}
assert shader_changed==expected,shader_changed
print('PASS 26656 authority: exact successful 26655 base 1721 -> freeze2 candidate 1726; exactly 11 changed / 5 added / 1715 protected / 806 native / 778 vendor / 7 DNG / standalone shaders 257->262 with exactly 6 intended shader assets changed/added')
