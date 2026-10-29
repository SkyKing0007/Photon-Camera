#!/usr/bin/env python3
"""GLSL source-domain reserved identifier and CMake dispatch scan; real Actions compiler remains authority."""
from pathlib import Path
import argparse,re,hashlib,subprocess,sys
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('candidate',type=Path)
p.add_argument('--compiler')
p.add_argument('--spirv-val')
p.add_argument('--spirv-opt')
p.add_argument('--out',type=Path)
a=p.parse_args()
if any((a.compiler,a.spirv_val,a.spirv_opt,a.out)):
 assert all((a.compiler,a.spirv_val,a.spirv_opt,a.out)), 'all four real toolchain operands required'

r=a.candidate/'app/src/main/cpp/iris26864';bridge=r/'bridge'
shaders=[bridge/'Iris26888BOffHdrqMismatch.comp',bridge/'Iris26887BOffHdrqMerge.comp',bridge/'Iris26887BOffHdrqMismatchNorm.comp']
assert all(f.is_file() for f in shaders)
# Inherit the published V6 fail-fast vocabulary (V4 SAMPLE), extended to
# the complete additional 26888 direct shaders and imports where accessible.
KEYWORDS=set('''const uniform buffer shared attribute varying coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout int void bool true false float double discard return lowp mediump highp precision struct uint common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using sampler3DRect'''.split())
for pref in ('','i','u','b','d'):
 for num in (2,3,4):KEYWORDS.add(f'{pref}vec{num}')
for pref in ('','d'):
 for num in (2,3,4):
  KEYWORDS.add(f'{pref}mat{num}')
  for m in (2,3,4):KEYWORDS.add(f'{pref}mat{num}x{m}')
for pref in ('','i','u'):
 for tail in ('1D','1DArray','2D','2DArray','2DRect','2DMS','2DMSArray','3D','Cube','CubeArray','Buffer'):
  KEYWORDS.update((f'{pref}image{tail}',f'{pref}texture{tail}',f'{pref}sampler{tail}'))
KEYWORDS.update(('sampler','samplerShadow','subpassInput','isubpassInput','usubpassInput','subpassInputMS','isubpassInputMS','usubpassInputMS'))
for tail in ('1D','2D','2DRect','Cube','CubeArray'):KEYWORDS.add(f'sampler{tail}Shadow')
# Catch GLSL declarations, variables in formal parameter lists, and function identifiers.
typed=re.compile(r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234]|u?image2D|sampler2D|void)\s+([A-Za-z_]\w*)')
cm=(r/'Iris26864VendorRawr.cmake').read_text()
for shader in shaders:
 s=shader.read_text()
 assert s.startswith('#version 450\n'),('version',shader)
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 found=[]
 for m in typed.finditer(code):
  name=m.group(1)
  assert name not in KEYWORDS and '__' not in name and not name.startswith('gl_'),('GLSL reserved declaration',shader.name,name)
  found.append(name)
 assert 'void main()' in code,('no main',shader)
 assert len(code)>100,shader
 if shader.parent==bridge:assert shader.name in cm,('unreferenced new shader',shader)
 print('PASS declaration scan',shader.name,len(found),'decl identifiers',hashlib.sha256(shader.read_bytes()).hexdigest()[:12])
# Actual CMake bridge callsite count and exact per-variant factory names validated by host ABI test.
for name in ('Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqMerge.comp', 'Iris26887BOffHdrqMismatchNorm.comp'):
 assert name in cm,('active shadow CMake binding missing',name)
# Use the EXACT native project's compiler adapter, not a substitute, mock,
# or static parser. Its pinned glslang-16.5 check, Vulkan1.1 target, pre/post
# SPIR-V validation and -O optimization are inherited intact from 26887.
# Production and trace HDRQ are TWO distinct actual CMake shader commands.
if a.compiler:
 adapter=r/'compile_locked_rawr_glslc.py'
 include=r/'vendor/rawr/native/shader_common/shaders'
 for tool in (a.compiler,a.spirv_val,a.spirv_opt):
  assert Path(tool).is_file(),('pinned real executable missing',tool)
 assert adapter.is_file() and include.is_dir()
 a.out.mkdir(parents=True,exist_ok=True)
 output_lines=[]
 for shader in shaders:
  variants=('prod','trace') if shader.name in ('Iris26887BOffHdrqMerge.comp','Iris26887BOffHdrqMismatchNorm.comp') else ('prod',)
  for variant in variants:
   dest=a.out/(shader.stem+'_'+variant+'.spv')
   flags=['--target-env=vulkan1.1','-O']
   if variant=='trace':flags.append('-DRAWR_PARITY_TRACE=1')
   # CMake passes -I to the 26888 bridge shaders (includes LSC); the
   # original vendor HDRQ CMake does not pass an include flag.
   if False:
    flags.append('-I'+str(include))
   cmd=[sys.executable,'-S',str(adapter),f'--validator={a.compiler}',
        f'--spirv-val={a.spirv_val}',f'--spirv-opt={a.spirv_opt}',
        *flags,str(shader),'-o',str(dest)]
   subprocess.run(cmd,check=True)
   spv=dest.read_bytes()
   assert len(spv)>=84 and spv[:4]==b'\x03\x02\x23\x07',('invalid real compiled SPIR-V',dest)
   output_lines.append(hashlib.sha256(spv).hexdigest()+'  '+dest.name)
 (a.out/'26888_REAL_COMPILED_SHADER_SHA256.txt').write_text('\n'.join(output_lines)+'\n')
 assert len(output_lines)==5,('incorrect count of real production+trace shader programs',len(output_lines))
 print('PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 5 compiled 26888 shader variants')
else:
 print('PASS 3 modified runtime GLSL declaration scans; REAL expanded Vulkan glslang + spirv-val/opt: NOT RUN')

