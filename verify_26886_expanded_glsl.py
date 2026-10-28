#!/usr/bin/env python3
"""26886 complete modified Vulkan compute shader token scan and PINNED real compilation."""
from pathlib import Path
import argparse,re,hashlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--spirv-val');p.add_argument('--spirv-opt');p.add_argument('--out',type=Path);a=p.parse_args()
src=a.candidate/'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
s=src.read_text();assert s.startswith('#version 450') and '#include' not in s
code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
# Khronos GLSL 4.60 section 3.6: this is a declaration-identifier guard
# ONLY. It is not a substitute for the pinned real compiler below.
# Actions 40630270318: `vec3 sample` failed glslang (SAMPLE keyword).
# Keep the actual failed condition as a permanent negative regression.
KEYWORD_QUALIFIERS="""const uniform buffer shared attribute varying coherent volatile restrict readonly
writeonly atomic_uint layout centroid flat smooth noperspective patch sample
invariant precise break continue do for while switch case default if else
subroutine in out inout int void bool true false float double discard return
lowp mediump highp precision struct uint
""".split()
FUTURE_RESERVED="""common partition active asm class union enum typedef template this resource goto
inline noinline public static extern external interface long short half fixed
unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter
sizeof cast namespace using sampler3DRect
""".split()
# All GLSL vector/matrix opaque types, including Vulkan image and sampler
# families, may not be repurposed as declaration identifiers.
TYPES=set()
for lead in ('','i','u','b','d'):
 for n in (2,3,4):TYPES.add(f'{lead}vec{n}')
for lead in ('','d'):
 for n in (2,3,4):
  TYPES.add(f'{lead}mat{n}')
  for m in (2,3,4):TYPES.add(f'{lead}mat{n}x{m}')
for lead in ('','i','u'):
 for suffix in ('1D','1DArray','2D','2DArray','2DRect','2DMS','2DMSArray','3D','Cube','CubeArray','Buffer'):
  TYPES.add(f'{lead}image{suffix}')
  TYPES.add(f'{lead}texture{suffix}')
for lead in ('','i','u'):
 for suffix in ('1D','1DArray','2D','2DArray','2DRect','2DMS','2DMSArray','3D','Cube','CubeArray','Buffer'):
  TYPES.add(f'{lead}sampler{suffix}')
for suffix in ('1D','2D','2DRect','Cube','CubeArray'):
 TYPES.add(f'sampler{suffix}Shadow')
TYPES.update(('sampler','samplerShadow','subpassInput','isubpassInput','usubpassInput','subpassInputMS','isubpassInputMS','usubpassInputMS'))
reserved=set(KEYWORD_QUALIFIERS)|set(FUTURE_RESERVED)|TYPES
# Same lexical failing sample declaration also guards old supplied V4 bytes.
# A checked-in shim claiming a compiled result would be rejected by the real
# shader compiler as before; this early guard exists only to fail sooner.
assert 'sample' in reserved and 'wronskiNeighborRgb' not in reserved
# Permanent minimal exact-token regression from failed 40630270318:
# the old validator accepted this declaration and the pinned real GLSL
# compiler rejected it as unexpected SAMPLE. Keep this negative executable.
assert re.search(r'\bvec3\s+(sample)\s*=', 'vec3 sample=sampleRaw*lscGain(q)*p.wb.rgb;').group(1) in reserved
assert re.search(r'\bvec3\s+(wronskiNeighborRgb)\s*=', 'vec3 wronskiNeighborRgb=sampleRaw*lscGain(q)*p.wb.rgb;').group(1) not in reserved

for m in re.finditer(r'\b(?:float|int|uint|vec[234]|uvec[234]|ivec[234]|mat[234]|image2D|uimage2D|buffer|void|bool)\s+([A-Za-z_]\w*)',code):
 assert m.group(1) not in reserved and '__' not in m.group(1) and not m.group(1).startswith('gl_'),('reserved GLSL name',m.group(1))
assert 'layout(local_size_x=16,local_size_y=16)' in s and 'void main()' in s
assert s.count('imageStore(amazeRgbInPlace,')==1
if a.compiler:
 assert a.spirv_val and a.spirv_opt and a.out
 assert Path(a.compiler).is_file() and Path(a.spirv_val).is_file() and Path(a.spirv_opt).is_file()
 a.out.mkdir(parents=True,exist_ok=True)
 adapter=src.parent/'compile_locked_rawr_glslc.py';assert adapter.is_file()
 dest=a.out/'26886_wronski_chroma_guide.spv'
 subprocess.run([sys.executable,'-S',str(adapter),f'--validator={a.compiler}',f'--spirv-val={a.spirv_val}',f'--spirv-opt={a.spirv_opt}','--target-env=vulkan1.1','-O',str(src),'-o',str(dest)],check=True)
 b=dest.read_bytes();assert len(b)>=84 and b[:4]==b'\x03\x02\x23\x07'
 print('PASS 26886 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized',hashlib.sha256(b).hexdigest())
else:print('PASS 26886 complete shader reserved/declaration/ownership scan; REAL GLSL NOT RUN HERE',hashlib.sha256(src.read_bytes()).hexdigest())
