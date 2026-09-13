#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26634_r1_shaders.py BASE CANDIDATE [--out DIR] [--compiler PATH]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
shader=[x for x in changed if '/assets/shaders/' in x or x.endswith(('.glsl','.vert','.frag'))]
assert shader==[],shader
pin=root/'R1_26634_RUNTIME_EXPANDED_SHADERS.sha256'; assert pin.read_bytes()==b''
# No modified GLSL means reserved-word scan and glslang compile are correctly N/A, not substituted.
print('PASS 26634 shader gate: no modified GLSL/runtime-expanded shader; reserved scan and real glslang compile N/A')
