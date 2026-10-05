#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap,hashlib
if len(sys.argv) not in (3,5): raise SystemExit('usage: verify_26767_shaders.py BASE CAND [--compiler glslangValidator]')
b,c=map(Path,sys.argv[1:3]); compiler=None
if len(sys.argv)==5: assert sys.argv[3]=='--compiler'; compiler=sys.argv[4]
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'

def source(root): return (root/rel).read_text()
def rawtriple(src,name):
    anchors=[f'{name} = """',f'val {name} = """',f'private val {name} = """']
    for anchor in anchors:
        if anchor in src:
            i=src.index(anchor)+len(anchor); j=src.index('""".trimIndent()',i); return src[i:j]
    raise AssertionError(name)
def expanded(src,name): return textwrap.dedent(rawtriple(src,name)).lstrip('\n')
bs,cs=source(b),source(c)
bcommon=expanded(bs,'private val common'); ccommon=expanded(cs,'private val common')
assert bcommon==ccommon
base_authority={
 'seed':'621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532',
 'localMedian':'d373525e6407020b131e2f817a03fff200ccaeb66d2e01cc0fb4741c3cded299',
 'directionalSmooth':'0a1d47e40720adee1279f4e58c416eb8dcde7ceb9895157534ecaaa6351e8b6c',
 'iirRgb':'864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086',
}
for n,w in base_authority.items():
    got=hashlib.sha256(rawtriple(bs,'val '+n).encode()).hexdigest(); assert got==w,(n,got)
for n in ['seed','iirRgb']:
    assert rawtriple(bs,'val '+n)==rawtriple(cs,'val '+n),n
candidate_expected={
 'localMedian':'645888cf113955f8c5173b7b6f29da69a16c00c4bb0300474e26330ee522adeb',
 'directionalSmooth':'96a87bd3830bcdeed68843161934aca4d68f4e6c1c98173bcb80e75a3f61a3ee',
}
for n,w in candidate_expected.items():
    got=hashlib.sha256(rawtriple(cs,'val '+n).encode()).hexdigest(); assert got==w,(n,got)

reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
for label,src,common in [('base',bs,bcommon),('candidate',cs,ccommon)]:
  for name in ['localMedian','directionalSmooth']:
    shader=expanded(src,'val '+name).replace('$common',common)
    assert shader.startswith('#version 310 es\n'),(label,name)
    t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
    bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(label,name,bad)
    # Structural checks catch accidental truncation before real glslang runs.
    assert shader.count('{')==shader.count('}'),(label,name,'brace mismatch')
    assert shader.count('(')==shader.count(')'),(label,name,'paren mismatch')
    print(f'PASS 26767 reserved-identifier/structure scan {label} {name}: {len(names)} identifiers')
    if compiler:
      with tempfile.TemporaryDirectory() as td:
        f=Path(td)/f'26767_{label}_{name}.comp'; f.write_text(shader)
        r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
        if r.returncode: raise SystemExit(f'{label}/{name}\n'+r.stdout+r.stderr)
      print(f'PASS 26767 pinned real glslang compile: exact runtime-expanded {label} {name}')
print('PASS 26767 exact 26727/26766 VGN seed+iir protected; only localMedian/directionalSmooth modified')
