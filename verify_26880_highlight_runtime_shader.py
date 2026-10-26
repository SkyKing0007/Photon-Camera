#!/usr/bin/env python3
"""26880 exact ON/OFF clipping/photometric shader additions, source/real GLSL.
The unchanged 26867 legacy shader checker is separately replayed on the
historical 26867 compiled candidate, never falsely applied to revised 26880.
"""
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True)
a=p.parse_args();R=Path(__file__).resolve().parent; C=a.candidate.resolve();src=C/'app/src/main/java/com/hinnka/mycamera/processor'
manifest={}
for line in (R/'26880_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
 h,k=line.split('  ',1);assert k not in manifest;manifest[k]=h
files=('GlesMgcRawSabreShaders.kt','GlesIris26858BNoiseHighlight.kt','GlesMgcRawSpatialStacker.kt')
for f in files:
 path=src/f;rel='app/src/main/java/com/hinnka/mycamera/processor/'+f
 assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==manifest[rel],('altered current 26880 shader runtime source',rel)
S=(src/'GlesMgcRawSpatialStacker.kt').read_text()
assert 'GlesMgcRawSabreShaders.clipZonePreserveOriginalHeadroom26880' in S
assert 'GlesIris26858BNoiseHighlight.bNativeSensorSmoothWhite26866' in S
spec=[('GlesMgcRawSabreShaders.kt','clipZonePreserveOriginalHeadroom26880','normal_headroom'),
      ('GlesMgcRawSabreShaders.kt','clipZoneApplyFragment26840','normal_smooth_white'),
      ('GlesIris26858BNoiseHighlight.kt','bNativeSensorSmoothWhite26866','native_smooth_white')]
a.out.mkdir(parents=True,exist_ok=True)
for f,owner,label in spec:
 text=(src/f).read_text();pat=r'\bval\s+'+re.escape(owner)+r'\s*=\s*"""(.*?)""".trimIndent\(\)'
 matches=re.findall(pat,text,re.S);assert len(matches)==1,(f,owner,'missing/duplicate')
 glsl=textwrap.dedent(matches[0]).strip('\n')+'\n';assert glsl.startswith('#version 300 es\n')
 assert glsl.count('#version')==1 and 'void main()' in glsl and glsl.count('{')==glsl.count('}')
 assert not re.search(r'#include|#import|#line|\$\{|\$[A-Za-z]',glsl)
 if label=='normal_headroom':assert 'oHeadroom=vec2(expanded,core)' in glsl
 elif label=='normal_smooth_white':
  assert 'inwardOriginalHeadroom(p)' in glsl and 'multiBright' in glsl and 'vec3(white)' in glsl
 else:
  assert 'phaseColorClipAt' in glsl and 'inwardCross' in glsl and 'greenOnly' in glsl
  assert 'min(centerCell' not in glsl and 'smoothstep(0.14,0.90,clippedCoverage)' in glsl
 target=a.out/(label+'.frag');target.write_text(glsl)
 if a.compiler:
  result=subprocess.run([str(a.compiler),'-S','frag',str(target)],capture_output=True,text=True)
  assert result.returncode==0,(label,result.stdout,result.stderr)
 print('PASS 26880 1x/2x sensor-highlight GLSL owner',label,'sha256='+hashlib.sha256(glsl.encode()).hexdigest(),'pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
print('PASS 26880 THREE CURRENT HIGHROOM/SMOOTH-WHITE SHADERS '+('REAL GLSL' if a.compiler else 'SOURCE PREFLIGHT'))
