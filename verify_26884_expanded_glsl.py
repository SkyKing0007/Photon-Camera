#!/usr/bin/env python3
"""Full GLSL ES 300 expansion from the exact modified RAWR OFF Kotlin owner."""
from pathlib import Path
import argparse,re,subprocess,hashlib,textwrap
ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--compiler');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
R=Path(__file__).resolve().parent;C=a.candidate.resolve();a.out.mkdir(parents=True,exist_ok=True)
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
expected={k:h for h,k in (s.split('  ',1) for s in (R/'26884_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines())}
assert hashlib.sha256((C/rel).read_bytes()).hexdigest()==expected[rel]
s=(C/rel).read_text();m=re.findall(r'\bval\s+shader\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
assert len(m)==1,('shader owner missing/duplicate',len(m))
src=textwrap.dedent(m[0]).strip()+'\n'
assert src.startswith('#version 300 es\n') and src.count('#version')==1 and src.count('{')==src.count('}')
assert 'void main()' in src and 'vec3 rawrHighlightOff(' in src
assert 'float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));' in src
assert 'return min(postWb,vec3(commonCeiling));' in src
assert src.count('vec4(rawrHighlightOff(')==5
assert not re.search(r'#include|#import|#line|\$\{|\$[A-Za-z]',src)
clean=re.sub(r'//[^\n]*|/\*.*?\*/',' ',src,flags=re.S)
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise subroutine highp mediump lowp precision input output common partition active filter resource superp asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned namespace using'.split())
identifiers=set(re.findall(r'\b(?:float|int|uint|vec[234]|ivec[234]|uvec[234]|mat[234]|bool)\s+([a-zA-Z_]\w*)',clean))
assert not reserved.intersection(identifiers),('GLSL reserved identifier',reserved.intersection(identifiers))
out=a.out/'iris26884_rawr_off_fused_wb.frag';out.write_text(src)
if a.compiler:
 compiler=Path(a.compiler);assert compiler.is_file() and compiler.stat().st_size>0
 cp=subprocess.run([str(compiler),'-S','frag',str(out)],text=True,capture_output=True)
 assert cp.returncode==0,(cp.stdout,cp.stderr)
print('PASS 26884 exact runtime-expanded fused RAWR OFF GLES300 shader SHA-256='+hashlib.sha256(src.encode()).hexdigest()+' reserved identifier scan and pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
