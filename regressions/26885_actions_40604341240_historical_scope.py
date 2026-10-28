#!/usr/bin/env python3
"""Permanent real failed Actions 40604341240 / job 122539975456 regression.

The unchanged 26880 wavelet checker seals the *historical* CMake SHA. It
MUST NOT be run on a later modified CMake candidate. This proof reproduces
its EXACT failed predicate on authority-seeded 26884/26885 bytes, confirms
that 26885 changes ONLY the expected CMake integration, and ensures every
actual generated 17-stage wavelet checker invocation uses real 26884 bytes.
No historical validator, runtime shader or compiler gate is altered here.
"""
from pathlib import Path
import hashlib,re,sys
assert len(sys.argv)==4, 'usage: <exact_successful_26884_source> <26885_candidate> <actual_generated_26885_runner>'
B,C,R=map(Path,sys.argv[1:])
rel='app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake'
old=B/rel;new=C/rel
assert old.is_file() and new.is_file(),('missing exact native CMake',rel)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old_hash='e897cba110ccd5a4326c774f3d247282181c409488d82745ac3a63ada25ab409'
new_hash='8fd4ca201b80a70a662f3828a2579e2f6cbd291cb62a8ef1709c4a4c107cfc94'
assert sha(old)==old_hash,('wrong successful 26884 CMake authority',sha(old))
assert sha(new)==new_hash,('26885 CMake changed outside sealed eight-file candidate',sha(new))

# EXACT historical 26880 validator failed assertion: from
# verify_26880_rawr_shader_universe.py:65, unchanged.
original_manifest_hash=old_hash
try:
 assert new.is_file() and sha(new)==original_manifest_hash,('unsealed wavelet integration',rel)
except AssertionError as exc:
 assert exc.args == (('unsealed wavelet integration',rel),),('wrong original failure reproduced',exc.args)
else:
 raise AssertionError('failed-run negative case unexpectedly accepted modified 26885 CMake')
assert old.is_file() and sha(old)==original_manifest_hash,'original 26880 wavelet seal must PASS on 26884 compiled authority'

# The native compiler MUST still embed the real new shader into the unchanged
# original bridge rules, NOT drop the shader to satisfy a stale hash check.
s=old.read_text();t=new.read_text()
rep=(
 ('# Real SPIR-V codegen for the TWO Iris-only packed CFA/physical-LSC\n# compatibility bridges. Generated binary is embedded and linked into the',
  '# Real SPIR-V codegen for the Iris-owned packed CFA/physical-LSC, clip export\n# and B-ON chroma-evidence bridges. Generated binary is embedded and linked into the'),
 ('foreach(BRIDGE_NAME IN ITEMS hdrq_cfa_bridge wronski_cfa_bridge clip_to_gl_bridge)',
  'foreach(BRIDGE_NAME IN ITEMS hdrq_cfa_bridge wronski_cfa_bridge clip_to_gl_bridge wronski_chroma_guide)'),
 ('  else()\n    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/Iris26864PackedSensorClipToGl.comp")',
  '  elseif(BRIDGE_NAME STREQUAL "wronski_chroma_guide")\n    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/Iris26885WronskiChromaGuide.comp")\n  else()\n    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/Iris26864PackedSensorClipToGl.comp")'),
)
for a,b in rep:
 assert s.count(a)==1,('real 26884 CMake delta anchor changed',a)
 s=s.replace(a,b,1)
assert s==t,'new CMake contains an unexplained delta or lost historic RAWR integration'
assert (C/'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp').is_file(),'real compiled shader not sourced'

# Check the REAL generated script, not only generator comments/AST.
assert R.is_file(),('missing generated 26885 runner',R)
body=R.read_text()
stages=('make_candidate','compile_modified_runtime_shaders','clean_extract_replay')
for name in stages:
 start=body.index('\n'+name+'(){')
 end=body.index('\n}',start)+2
 lines=body[start:end].splitlines()
 matches=[x for x in lines if re.search(r'\bpython3 -S verify_26880_rawr_shader_universe\.py\b',x)]
 assert len(matches)==1,('26880 historical checker missing or duplicate in stage',name,matches)
 cmd=matches[0]
 assert '"$BASE/app"' in cmd,(name,'original sealed 26880 checker reads wrong domain',cmd)
 assert '"$CAND/app"' not in cmd and '"$exp/app"' not in cmd,(name,'actual 40604341240 failure reintroduced',cmd)
 if name=='compile_modified_runtime_shaders':
  start_line=lines.index(cmd)
  # The successful 26884 compiler's original invocation spans continued Bash lines.
  command=[cmd]
  j=start_line
  while command[-1].rstrip().endswith('\\'):
   j+=1
   assert j<len(lines),('unterminated historical compiler command',cmd)
   command.append(lines[j])
  joined='\n'.join(command)
  assert all(flag in joined for flag in ('--compile','--spirv-val','--spirv-opt','--out')),('historical REAL compiler args changed',joined)
# The independent 26885 shader real compiler and final source gates remain.
assert 'verify_26885_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in body
assert 'verify_26885_expanded_glsl.py "$exp"' in body
assert 'PRE-BUILD SAFETY PROOF PASSED' in body
print('PASS 26885 permanent REAL Actions 40604341240 legacy CMake mismatch reproduced and corrected in ALL 3 stage invocations; unchanged 26880 checker, independent changed 26885 CMake+shader compiler')
