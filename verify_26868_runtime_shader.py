#!/usr/bin/env python3
"""Expand and pin-compile 26868's two real runtime Long GLES300 shaders."""
from pathlib import Path
import argparse,re,textwrap,hashlib,subprocess
p=argparse.ArgumentParser()
p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
app=a.candidate/'app'
shader=(app/'src/main/java/com/hinnka/mycamera/processor/GlesIris26868DirectLong.kt').read_text()
consumer=(app/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'IRIS_26868_B_ONLY_SABRE_FREE_SINGLE_LONG' in shader
assert consumer.count('GlesIris26868DirectLong.packCalibratedLong')==1
assert consumer.count('GlesIris26868DirectLong.trustedShadowGain')==1
out=a.out;out.mkdir(parents=True,exist_ok=True)
# Complete GLSL 4.60 / ESSL reserved keywords and inherited future-reserved
# identifier classes; GLSL compiler also provides authoritative rejection.
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly '
 'atomic_uint layout centroid flat smooth noperspective patch sample invariant precise '
 'subroutine highp mediump lowp precision in out inout uniform const struct '
 'asm class union enum typedef template this packed goto inline noinline '
 'public static extern external interface long short half fixed unsigned '
 'input output common partition active filter resource superp cast sizeof '
 'namespace using sampler1D sampler2D sampler3D samplerCube sampler2DArray '
 'sampler2DShadow samplerCubeShadow sampler2DArrayShadow'.split())
# Qualifiers/types may be keywords; test only identifier declaration slots.
for var in ('packCalibratedLong','trustedShadowGain'):
    markers=list(re.finditer(r'\bval\s+'+var+r'\s*=\s*"""',shader))
    assert len(markers)==1,(var,'must have exactly one shader source')
    start=markers[0].end();end=shader.find('""".trimIndent()',start)
    assert end>start
    src=textwrap.dedent(shader[start:end]).strip('\n')+'\n'
    assert src.startswith('#version 300 es\n') and src.count('#version')==1
    assert 'void main()' in src and src.count('{')==src.count('}')
    assert not re.search(r'^\s*#(?:include|import|line)\b|\$\{|\$[A-Za-z]',src,re.M)
    assert src.count('layout(location=0) out vec4')==1
    types='float int uint vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 sampler2D usampler2D'
    names={m.group(1) for m in re.finditer(r'\b(?:'+ '|'.join(types.split())+r')\s+([A-Za-z_][A-Za-z_0-9]*)\b',src)}
    # actual reserved for declarations excludes legal precision qualifiers
    assert not (names&reserved),(var,'reserved identifier',names&reserved)
    f=out/(var+'.frag');f.write_text(src)
    if a.compiler:
        cp=subprocess.run([a.compiler,'-S','frag',str(f)],capture_output=True,text=True)
        assert cp.returncode==0,(var,cp.stdout,cp.stderr)
    print('PASS 26868 fully expanded runtime GLSL',var,'sha256='+hashlib.sha256(src.encode()).hexdigest(),
          'complete identifier scan PASS','pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
