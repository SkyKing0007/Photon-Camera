#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap
if len(sys.argv) not in (2,4): raise SystemExit('usage: verify_26763_shaders.py CANDIDATE [--compiler glslangValidator]')
c=Path(sys.argv[1]); compiler=None
if len(sys.argv)==4:
 assert sys.argv[2]=='--compiler'; compiler=sys.argv[3]
p=c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; s=p.read_text()
def triple(name):
 anchor=f'{name} = """'; i=s.index(anchor)+len(anchor); j=s.index('""".trimIndent()',i); return textwrap.dedent(s[i:j]).lstrip('\n')
common=triple('private val common')
seed=triple('val seed').replace('$common',common)
assert seed.startswith('#version 310 es\n')
assert seed.count('IRIS_26763_NEUTRAL_CFA_OWNERSHIP_ADMISSION_VETO')==1
assert 'float materialHueAgreement26763(vec2 a,vec2 b)' in seed
assert 'float neutralCfaOwnershipVeto26763=' in seed
# Complete reserved-identifier scan on the exact runtime-expanded modified seed shader.
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',seed,flags=re.S)
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
names=[]
for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
bad=sorted({n for n in names if n in reserved or n.startswith('__')})
assert not bad,bad
print(f'PASS 26763 reserved-identifier scan: {len(names)} identifiers; exact runtime-expanded seed shader')
if compiler:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'26763_seed.comp'; f.write_text(seed)
  r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
  if r.returncode: raise SystemExit(r.stdout+r.stderr)
 print('PASS 26763 pinned real glslang compile: exact runtime-expanded seed shader')
