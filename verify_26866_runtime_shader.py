#!/usr/bin/env python3
"""Extract EXACT 26866 runtime native B 1x/2x GLES300 fragment; pinned real compiler mandatory in Actions."""
import argparse,hashlib,re,textwrap,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True);args=p.parse_args()
f=args.candidate/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt'
s=f.read_text();matcher=list(re.finditer(r'\bval\s+bNativeSensorSmoothWhite26866\s*=\s*"""',s));assert len(matcher)==1
start=matcher[0].end();end=s.find('""".trimIndent()',start);assert end>start
src=textwrap.dedent(s[start:end]).strip('\n')+'\n'
assert src.startswith('#version 300 es\n') and src.count('#version')==1
assert 'layout(location=0) out vec4 oRgb;' in src and 'void main()' in src
assert not re.search(r'#include|#import|#line|\$\{|\$[a-zA-Z]',src)
assert src.count('{')==src.count('}')
assert 'texelFetch(uNativeSensorClip,q,0).r' in src and 'smoothstep(0.0,1.0,clippedCoverage)' in src
# Actual consumer callback and true2x Wronski are mandatory users.
stacker=(args.candidate/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert stacker.count('GlesIris26858BNoiseHighlight.bNativeSensorSmoothWhite26866')==1
assert 'nativeSensorClipFullRes26866 = nativeSensorClip26864' in stacker
assert 'nativeSensorClipFullRes26866 = nativeClip' in stacker
out=args.out;out.mkdir(parents=True,exist_ok=True);path=out/'b_native_sensor_smooth_white_26866.frag';path.write_text(src)
if args.compiler:
 cmd=[args.compiler,'-S','frag',str(path)];r=subprocess.run(cmd,capture_output=True,text=True)
 assert r.returncode==0,(r.stdout,r.stderr)
print('PASS 26866 exact runtime expanded native B smooth-white GLSL 300 ES SHA-256='+hashlib.sha256(src.encode()).hexdigest()+' pinned-glslang='+('PASS' if args.compiler else 'NOT RUN'))
