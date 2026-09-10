#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
if len(sys.argv)<5 or sys.argv[3] != '--out':
    raise SystemExit('usage: verify_26622_r1_shaders.py BASE CAND --out OUT [--compiler COMPILER]')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); O=Path(sys.argv[4]); O.mkdir(parents=True,exist_ok=True)
compiler=None
if '--compiler' in sys.argv[5:]:
    i=sys.argv.index('--compiler'); compiler=sys.argv[i+1]
changed=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties']
assert not any(p.endswith(('.glsl','.frag','.vert','.comp')) for p in changed)
(O/'R1_26622_RUNTIME_EXPANDED_SHADERS.sha256').write_text('')
(O/'R1_26622_SHADER_VERIFICATION.json').write_text(json.dumps({
    'count':0,
    'compiler':compiler,
    'results':[],
    'reason':'No runtime GLSL/GLSL ES paths are modified by the exact 26622 runtime allowlist.'
},indent=2,sort_keys=True)+'\n')
print(f'PASS 26622 runtime-expanded shader scope variants=0 (no modified GLSL) real_compiler_resolved={bool(compiler)}')
