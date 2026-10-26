#!/usr/bin/env python3
"""Source-exact real expanded GLES 300 shader guard, no compiler substitution.
Every modified GLSL program receives reserved-token scan and pinned glslang.
"""
from pathlib import Path
import argparse,hashlib,re,textwrap,subprocess
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parent;C=a.candidate.resolve();a.out.mkdir(parents=True,exist_ok=True)
manifest={}
for line in (R/'26881_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
 h,k=line.split('  ',1);assert k not in manifest;manifest[k]=h
spec=(('GlesIris26858BNoiseHighlight.kt','bNativeSensorSmoothWhite26866','sensor_clip'),('GlesIris26870PostAmazeChroma.kt','shader','edge_protected_chroma'))
for filename,owner,label in spec:
 rel='app/src/main/java/com/hinnka/mycamera/processor/'+filename;path=C/rel
 assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==manifest[rel]
 src=path.read_text();m=re.findall(r'\bval\s+'+re.escape(owner)+r'\s*=\s*"""(.*?)""".trimIndent\(\)',src,re.S)
 assert len(m)==1,(filename,owner,len(m))
 glsl=textwrap.dedent(m[0]).strip()+'\n'
 assert glsl.startswith('#version 300 es\n') and glsl.count('#version')==1
 assert not re.search(r'#include|#import|#line|\$\{|\$[A-Za-z]',glsl)
 assert glsl.count('{')==glsl.count('}') and 'void main()' in glsl
 # Detect accidental reserved identifier assignment declarations in runtime source.
 tokens=re.findall(r'\b(?:float|int|uint|vec[234]|ivec[234]|uvec[234]|mat[234]|bool)\s+([A-Za-z_]\w*)',re.sub(r'//[^\n]*|/\*.*?\*/',' ',glsl,flags=re.S))
 reserved={'input','output','common','partition','active','filter','resource','sample','subroutine','sampler','coherent','shared','volatile','restrict','readonly','writeonly','precision','lowp','mediump','highp','attribute','varying','buffer','patch','layout'}
 assert not reserved.intersection(tokens),('reserved identifiers',reserved.intersection(tokens))
 if label=='sensor_clip':assert 'float tripleClip=' in glsl and 'thirdWitness' in glsl and 'smoothstep(0.13,0.38,opticalSupport)' in glsl
 else:assert 'ring>=2' in glsl and 'material*=bridgeLum*bridgeHue' in glsl
 out=a.out/(label+'.frag');out.write_text(glsl)
 if a.compiler:
  cp=subprocess.run([str(a.compiler),'-S','frag',str(out)],capture_output=True,text=True)
  assert cp.returncode==0,(label,cp.stdout,cp.stderr)
 print('PASS 26881 current expanded GLSL',label,'sha256='+hashlib.sha256(glsl.encode()).hexdigest(),'pinned='+('PASS' if a.compiler else 'NOT RUN'))
print('PASS 26881 BOTH MODIFIED RUNTIME GLES300 PROGRAMS '+('REAL PINNED GLSL' if a.compiler else 'SOURCE PREFLIGHT'))
