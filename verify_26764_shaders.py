#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap
if len(sys.argv) not in (2,4): raise SystemExit('usage: verify_26764_shaders.py CANDIDATE [--compiler glslangValidator]')
c=Path(sys.argv[1]); compiler=None
if len(sys.argv)==4:
 assert sys.argv[2]=='--compiler'; compiler=sys.argv[3]
p=c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; s=p.read_text()
def triple(name):
 anchor=f'{name} = """'; i=s.index(anchor)+len(anchor); j=s.index('""".trimIndent()',i); return textwrap.dedent(s[i:j]).lstrip('\n')
common=triple('private val common')
shaders={name:triple('val '+name).replace('$common',common) for name in ('seed','localMedian','directionalSmooth')}
assert shaders['seed'].count('IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_DIRECTION')==1
assert shaders['localMedian'].count('IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_MEDIAN')==1
assert shaders['directionalSmooth'].count('IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_DIRECTIONAL_RESTORE')==1
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
for name,shader in shaders.items():
 assert shader.startswith('#version 310 es\n'),name
 t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S)
 names=[]
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
 bad=sorted({n for n in names if n in reserved or n.startswith('__')})
 assert not bad,(name,bad)
 print(f'PASS 26764 reserved-identifier scan {name}: {len(names)} identifiers')
 if compiler:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/f'26764_{name}.comp'; f.write_text(shader)
   r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
   if r.returncode: raise SystemExit(f'{name}\n'+r.stdout+r.stderr)
  print(f'PASS 26764 pinned real glslang compile: exact runtime-expanded {name}')
