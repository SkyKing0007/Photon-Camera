#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26637_r1_shaders.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:])
rows=[]
for l in (root/'R1_26637_RUNTIME_EXPANDED_SHADERS.sha256').read_text().splitlines():
 if l.strip(): h,r=l.split('  ',1); rows.append((h,r))
assert len(rows)==257
for h,r in rows:
 for d in (base,cand): assert hashlib.sha256((d/r).read_bytes()).hexdigest()==h,r
changed=set((root/'R1_26637_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
assert not any(x.startswith('app/src/main/assets/shaders/') for x in changed)
print('PASS 26637 GLSL stage retained: 0 modified GLSL; exact 257-file shader universe invariant; real glslang N/A')
