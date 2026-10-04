#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap,hashlib
if len(sys.argv) not in (2,4): raise SystemExit('usage: verify_26765_shaders.py CANDIDATE [--compiler glslangValidator]')
c=Path(sys.argv[1]); compiler=None
if len(sys.argv)==4: assert sys.argv[2]=='--compiler'; compiler=sys.argv[3]
p=c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; s=p.read_text()
def rawtriple(name):
 anchor=f'{name} = \"\"\"'; i=s.index(anchor)+len(anchor); j=s.index('\"\"\".trimIndent()',i); return s[i:j]
def expanded(name): return textwrap.dedent(rawtriple(name)).lstrip('\n')
common=expanded('private val common')
authority={
'seed':'621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532',
'localMedian':'d373525e6407020b131e2f817a03fff200ccaeb66d2e01cc0fb4741c3cded299',
'directionalSmooth':'0a1d47e40720adee1279f4e58c416eb8dcde7ceb9895157534ecaaa6351e8b6c',
'iirRgb':'864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086',
}
raw={name:rawtriple('val '+name) for name in authority}
for n,w in authority.items(): assert hashlib.sha256(raw[n].encode()).hexdigest()==w,n
shaders={name:textwrap.dedent(raw[name]).lstrip('\n').replace('$common',common) for name in authority}
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
for name,shader in shaders.items():
 assert shader.startswith('#version 310 es\n'),name
 t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
 for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
 bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(name,bad)
 print(f'PASS 26765 reserved-identifier scan {name}: {len(names)} identifiers')
 if compiler:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/f'26765_{name}.comp'; f.write_text(shader)
   r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
   if r.returncode: raise SystemExit(f'{name}\n'+r.stdout+r.stderr)
  print(f'PASS 26765 pinned real glslang compile: exact runtime-expanded {name}')
