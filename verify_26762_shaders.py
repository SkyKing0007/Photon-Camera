#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap
if len(sys.argv) not in (2,4): raise SystemExit('usage: verify_26762_shaders.py CANDIDATE [--compiler glslangValidator]')
c=Path(sys.argv[1]); compiler=None
if len(sys.argv)==4:
 assert sys.argv[2]=='--compiler'; compiler=sys.argv[3]
p=c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; s=p.read_text()
anchor='val true2xGuideRender26568 = """'; i=s.index(anchor)+len(anchor); j=s.index('""".trimIndent()',i)
shader=textwrap.dedent(s[i:j]).lstrip('\n')
assert shader.startswith('#version 300 es\n')
assert 'uniform float uChromaDenoiseStrength26762;' in shader
assert shader.count('IRIS_26762_SUPER_RES_BOUNDED_ADAPTIVE_CHROMA_BLEND')==1
# GLSL ES reserved keywords: reject declarations/functions using language-reserved identifiers.
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
# Strip comments before scanning user-defined names in declarations/functions.
t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S)
# names after typed declarations/functions; built-in types are allowed as types, never as identifiers.
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|ivec2)'
names=[]
for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
bad=sorted({n for n in names if n in reserved or (n.startswith('__'))})
assert not bad,bad
print(f'PASS 26762 reserved-identifier scan: {len(names)} declared/function identifiers; no reserved collisions')
if compiler:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'26762_true2x.frag'; f.write_text(shader)
  r=subprocess.run([compiler,'-S','frag',str(f)],text=True,capture_output=True)
  if r.returncode: raise SystemExit(r.stdout+r.stderr)
 print('PASS 26762 pinned real glslang compile: exact runtime-expanded true2x guide shader')
