#!/usr/bin/env python3
"""Exact runtime-expanded modified highlight shader, reserved tokens and pinned GLSL."""
from pathlib import Path
import argparse,re,subprocess,hashlib,textwrap
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parent;C=a.candidate.resolve();a.out.mkdir(parents=True,exist_ok=True)
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt'
expected={k:h for h,k in (s.split('  ',1) for s in (R/'26882_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines())}
assert hashlib.sha256((C/rel).read_bytes()).hexdigest()==expected[rel]
s=(C/rel).read_text();m=re.findall(r'\bval\s+bNativeSensorSmoothWhite26866\s*=\s*"""(.*?)""".trimIndent\(\)',s,re.S)
assert len(m)==1
src=textwrap.dedent(m[0]).strip()+'\n';assert src.startswith('#version 300 es\n') and src.count('#version')==1 and src.count('{')==src.count('}')
assert 'void main()' in src and 'uNativeSensorClip' in src and 'uBayerPattern' in src
assert 'smoothstep(0.055,0.28,' in src and 'smoothstep(0.35,0.65,' not in src
assert not re.search(r'#include|#import|#line|\$\{|\$[A-Za-z]',src)
clean=re.sub(r'//[^\n]*|/\*.*?\*/',' ',src,flags=re.S)
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise subroutine highp mediump lowp precision input output common partition active filter resource superp asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned namespace using'.split())
vars=set(re.findall(r'\b(?:float|int|uint|vec[234]|ivec[234]|uvec[234]|mat[234]|bool)\s+([a-zA-Z_]\w*)',clean))
assert not reserved.intersection(vars),('GLSL reserved identifier',reserved.intersection(vars))
out=a.out/'iris26882_native_white.frag';out.write_text(src)
if a.compiler:
 compiler=Path(a.compiler);assert compiler.is_file() and compiler.stat().st_size>0
 cp=subprocess.run([str(compiler),'-S','frag',str(out)],text=True,capture_output=True)
 assert cp.returncode==0,(cp.stdout,cp.stderr)
print('PASS 26882 modified runtime-expanded GLES300 native smooth-white shader SHA-256='+hashlib.sha256(src.encode()).hexdigest()+' reserved identifier scan and pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
