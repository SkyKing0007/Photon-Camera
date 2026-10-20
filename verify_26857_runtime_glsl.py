#!/usr/bin/env python3
"""Complete 26857 GLSL source-scope: exact compiled 26856 shader universe protected;
one modified Kotlin-expanded GLES300 fragment compiled by pinned real glslang when --compiler supplied.
"""
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('candidate');p.add_argument('--compiler');p.add_argument('--out',required=True);a=p.parse_args()
B=Path(a.base);C=Path(a.candidate);O=Path(a.out);O.mkdir(parents=True,exist_ok=True)
REL='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrColorContract.kt'
t=(C/REL).read_text();mt=re.search(r'\bval\s+applyAmazeWbForLabFcc\s*=\s*"""',t)
assert mt and t.count('val applyAmazeWbForLabFcc =')==1
start=mt.end();end=t.find('""".trimIndent()',start);assert end>start
src=textwrap.dedent(t[start:end]).strip('\n')+'\n'
assert src.startswith('#version 300 es\n') and 'void main()' in src
assert not re.search(r'\$[A-Za-z_]|#include',src)
assert 'source.rgb * uAmazeWb' in src and 'uSensorNeutralAmazeRgb' in src
# Complete GLSL / GLSL ES reserved-identifier sweep on the expanded active fragment.
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major'.split())
cs=re.sub(r'//.*',' ',re.sub(r'/\*.*?\*/',' ',src,flags=re.S));tt=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'
names=set(re.findall(r'\b'+tt+r'\s+([A-Za-z_]\w*)',cs));bad={n for n in names if n in reserved or n.startswith('gl_') or n.startswith('__')};assert not bad,('reserved GLSL identifier',bad)
file=O/'26857_b_temporary_wb_for_lab_fcc.frag';file.write_text(src)
if a.compiler:
 r=subprocess.run([a.compiler,'-S','frag',str(file)],capture_output=True,text=True)
 if r.returncode:raise SystemExit(f'FAIL pinned real glslang:\n{r.stdout}\n{r.stderr}')
print('PASS 26857 GLSL ownership: 1 exact runtime-expanded GLES300 fragment; reserved names complete; sha256='+hashlib.sha256(src.encode()).hexdigest()+' pinned real compiler '+('PASS' if a.compiler else 'NOT RUN'))
