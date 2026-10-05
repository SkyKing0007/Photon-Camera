#!/usr/bin/env python3
from pathlib import Path
import re,sys,tempfile,subprocess,textwrap,hashlib
if len(sys.argv) not in (3,5):
    raise SystemExit('usage: verify_26769_shaders.py BASE26768 CAND26769 [--compiler glslangValidator]')
base,cand=map(Path,sys.argv[1:3]); compiler=None
if len(sys.argv)==5:
    assert sys.argv[3]=='--compiler'; compiler=sys.argv[4]
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
bs=(base/rel).read_text(); cs=(cand/rel).read_text()
def raw(src,name):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S)
    if not m: raise AssertionError(name)
    return m.group(1)
def expanded(src,name):
    x=textwrap.dedent(raw(src,name)).lstrip('\n')
    if '$common' in x:
        x=x.replace('$common',textwrap.dedent(raw(src,'common')).lstrip('\n'))
    return x
existing=['universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
changed=[n for n in existing if raw(bs,n)!=raw(cs,n)]
assert changed==['seed','localMedian','directionalSmooth','iirRgb'],changed
assert 'bipolarColorTrust26769' not in bs and 'bipolarColorTrust26769' in cs
pins={
 'seed':'11dd336e06d690cafbaa9364824da6751770859f65970e6832e038588d4931f9',
 'localMedian':'af398f2faf649baa6eb368c448d76fb1a7c52644daef7a2b243f2bcc37f0dbcc',
 'directionalSmooth':'d1cb43d2087c9d2dad565378ec80b10ca7f85450156d93846606a92b8593f8de',
 'iirRgb':'5f43597a86341291e1afc8dc8c177982ed77c2c71db82010fec97627cb6c1a5c',
 'bipolarColorTrust26769':'6535533c4008e6985643beb71495371bd1a5b29ccbaffba258a53fcdee9e3195',
}
for n,h in pins.items():
    assert hashlib.sha256(raw(cs,n).encode()).hexdigest()==h,(n,'candidate hash')
assert hashlib.sha256(raw(cs,'universalAdaptiveColor26561').encode()).hexdigest()=='0a75e0e900e26769288d69947d4febe080f44a3a0b9551c96e08640ade554802'
assert raw(bs,'universalAdaptiveColor26561')==raw(cs,'universalAdaptiveColor26561')
assert raw(bs,'finalCameraRgb')==raw(cs,'finalCameraRgb')
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
def scan(label,src,name):
    shader=expanded(src,name); assert shader.startswith('#version 310 es\n'),(label,name)
    t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
    bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(label,name,bad)
    assert shader.count('{')==shader.count('}'),(label,name,'brace mismatch')
    assert shader.count('(')==shader.count(')'),(label,name,'paren mismatch')
    print(f'PASS 26769 reserved-identifier/structure scan {label} {name}: {len(names)} identifiers')
    if compiler:
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/f'26769_{label}_{name}.comp'; f.write_text(shader)
            r=subprocess.run([compiler,'-S','comp',str(f)],text=True,capture_output=True)
            if r.returncode: raise SystemExit(f'{label}/{name}\n'+r.stdout+r.stderr)
        print(f'PASS 26769 pinned real glslang compile: exact runtime-expanded {label} {name}')
for n in changed: scan('base26768',bs,n)
for n in changed+['bipolarColorTrust26769']: scan('candidate26769',cs,n)
print('PASS 26769 shader scope: 26768 universal/localClamp/restore/error/blend/final bodies protected; exact successful-26733 seed+iir reference')
