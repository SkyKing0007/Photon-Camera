#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap,hashlib
if len(sys.argv) not in (3,5): raise SystemExit('usage: verify_26768_shaders.py BASE CANDIDATE [--compiler glslangValidator]')
b,c=map(Path,sys.argv[1:3]); compiler=None
if len(sys.argv)==5: assert sys.argv[3]=='--compiler'; compiler=sys.argv[4]
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
bs=(b/rel).read_text(); cs=(c/rel).read_text()
def raw(src,name):
 for anchor in (f'val {name} = """',f'private val {name} = """'):
  if anchor in src:
   i=src.index(anchor)+len(anchor); j=src.index('""".trimIndent()',i); return src[i:j]
 raise AssertionError(name)
def expanded(src,name): return textwrap.dedent(raw(src,name)).lstrip('\n').replace('$common',textwrap.dedent(raw(src,'common')).lstrip('\n'))
assert hashlib.sha256(raw(bs,'iirRgb').encode()).hexdigest()=='864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086'
assert hashlib.sha256(raw(cs,'iirRgb').encode()).hexdigest()=='0a59d8f8953ce5b8ec1b0a69395ed54a578e8729b391602e6d0fa0bdd89cfbf5'
for name,h in {
 'seed':'621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532',
 'localMedian':'645888cf113955f8c5173b7b6f29da69a16c00c4bb0300474e26330ee522adeb',
 'directionalSmooth':'96a87bd3830bcdeed68843161934aca4d68f4e6c1c98173bcb80e75a3f61a3ee',
}.items():
 assert hashlib.sha256(raw(bs,name).encode()).hexdigest()==h
 assert hashlib.sha256(raw(cs,name).encode()).hexdigest()==h
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
for label,src in [('base',bs),('candidate',cs)]:
 shader=expanded(src,'iirRgb'); assert shader.startswith('#version 310 es\n')
 t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
 bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(label,bad)
 assert shader.count('{')==shader.count('}'),(label,'brace mismatch'); assert shader.count('(')==shader.count(')'),(label,'paren mismatch')
 print(f'PASS 26768 reserved-identifier/structure scan {label} iirRgb: {len(names)} identifiers')
 if compiler:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/f'26768_{label}_iirRgb.comp'; f.write_text(shader)
   r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
   if r.returncode: raise SystemExit(f'{label}/iirRgb\n'+r.stdout+r.stderr)
  print(f'PASS 26768 pinned real glslang compile: exact runtime-expanded {label} iirRgb')
print('PASS 26768 only iirRgb modified; successful 26767 seed/localMedian/directionalSmooth shader authority preserved')
