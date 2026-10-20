#!/usr/bin/env python3
"""Full expanded source and pinned compiler for both modified/added runtime GLSL owners.
No ad-hoc compiler substitutes. Emits exactly the fragment string linked by GLES.
"""
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
p=argparse.ArgumentParser()
p.add_argument('base');p.add_argument('candidate');p.add_argument('--compiler')
p.add_argument('--out',required=True)
a=p.parse_args(); B=Path(a.base);C=Path(a.candidate);O=Path(a.out);O.mkdir(parents=True,exist_ok=True)
PR='app/src/main/java/com/hinnka/mycamera/processor/'
files={
 'temporal_cfa_accumulate':('GlesMgcRawSabreShaders.kt','normalCfaTemporalAccumulate26852'),
 'b_cfa_denoise':('GlesIris26858BNoiseHighlight.kt','bCfaNoise'),
 'b_clip_votes':('GlesIris26858BNoiseHighlight.kt','bClipAccumulate'),
 'b_clip_normalize':('GlesIris26858BNoiseHighlight.kt','bClipNormalize'),
 'b_rgb_residual':('GlesIris26858BNoiseHighlight.kt','bResidualChroma'),
 'b_highlight_neutral':('GlesIris26858BNoiseHighlight.kt','bHighlightRecover'),
 'b_physical_lsc':('GlesIris26858BNoiseHighlight.kt','bLensShade'),
}
S=(C/PR/'GlesMgcRawSpatialStacker.kt').read_text()
assert S.count('renderSabreNormalCfaTemporalAccumulate26852(')>=2
for attr in ('iris26858BCfaProgram','iris26858BClipAccumulateProgram',
             'iris26858BClipNormalizeProgram','iris26858BResidualProgram',
             'iris26858BHighlightProgram','iris26859BLensShadeProgram'):
 assert S.count(attr)>=2,('program owner missing',attr)
assert 'iris26858BGuideSeedProgram' not in S and 'iris26858BGuideSpreadProgram' not in S
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in S
assert S.index('bRecovered26858 = renderIris26858BHighlightColor(') < S.index('defringed = renderRawrLabDefringe26856(') < S.index('fcc = renderRawrFalseColor26856(')
assert 'val inverse = snapshot.inverseWhiteBalance' in S
assert 'IRIS_26859_B_SINGLE_PHYSICAL_LSC_OWNER' in S
assert 'uniform1i(p,"uUseLensShading",if(iris26859BLensMapTexture!=0)1 else 0)' in S
assert 'if (iris26858BClipVotes != 0)' in S and 'else renderSabreNormalCfaNoiseClean26853' in S
# Semantics are grounded in ACTUAL B producer-to-consumer, not marker wording.
N=(C/PR/'GlesIris26860BBurstNoise.kt').read_text()
for exact in ('fun estimate(', 'phaseBlackByFrame', 'readFileRegion(',
              'FloatArray(total*normals.size)', 'var0=kept.sumOf',
              'mode: String', 'CAMERA2_FALLBACK_', 'normals.any { f ->'):
 assert exact in N,('missing measured RAW-burst fitter',exact)
assert S.count('GlesIris26860BBurstNoise.estimate(')==1
assert 'bBurstNoise26860 = bBurstNoise26860,' not in S, 'shared temporal CFA must stay inherited for A+B'
assert 'uniform4fv(program, "uPhaseNoiseShot26855", shot26855)' in S
assert 'uniform4fv(program, "uPhaseNoiseRead26855", read26855)' in S
assert S.count('bBurstNoise26860?.shot ?: bReferenceShot26860')==2
assert S.count('bBurstNoise26860?.read ?: bReferenceRead26860')==2
assert 'uBayerPattern' in (C/PR/'GlesIris26858BNoiseHighlight.kt').read_text()
assert 'uniform1i(p, "uBayerPattern", cfaPattern)' in S
assert 'SHORT' not in N and 'HDR+' not in N

reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major'.split())
tt=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'
for label,(file,owner) in files.items():
 t=(C/PR/file).read_text()
 reg=r'\bval\s+'+re.escape(owner)+r'\s*=\s*"""'
 hits=list(re.finditer(reg,t));assert len(hits)==1,(label,owner,'anchor count',len(hits))
 start=hits[0].end();end=t.find('""".trimIndent()',start);assert end>start,(label,'unclosed shader')
 src=textwrap.dedent(t[start:end]).strip('\n')+'\n'
 assert src.startswith('#version 300 es\n'),(label,'GLES300 source')
 assert src.count('#version')==1 and 'void main()' in src
 assert not re.search(r'\$[A-Za-z_]|#include|#import|#line|\$\{',src),label
 no_comments=re.sub(r'//[^\n]*',' ',re.sub(r'/\*.*?\*/',' ',src,flags=re.S))
 decl=set(re.findall(r'\b'+tt+r'\s+([A-Za-z_]\w*)',no_comments))
 bad={name for name in decl if name in reserved or name.startswith('gl_') or name.startswith('__')}
 assert not bad,(label,'GLSL ES reserved identifier',bad)
 assert src.count('{')==src.count('}'),(label,'GLSL braces')
 fragment=O/(label+'.frag');fragment.write_text(src)
 if a.compiler:
  test=subprocess.run([a.compiler,'-S','frag',str(fragment)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if test.returncode:raise SystemExit(f'FAIL pinned real glslang {label}:\n{test.stdout}')
 if label=='b_rgb_residual':
  for piece in ('uNoiseShot*sensorPhase+uNoiseRead',
                'noise*noise)*sensorRgbVar/baseMean',
                'gainRgb;', 'uBaseShot26860*sensorPhase+uBaseRead26860'):
   assert piece in src,('shader failed to consume fitted per-phase model',piece)
 print('PASS runtime-expanded GLSL',label,hashlib.sha256(src.encode()).hexdigest(), 'real-glslang='+('PASS' if a.compiler else 'NOT RUN'))
print('PASS 26860 GLSL ownership: 7 exact runtime-expanded fragment sources; all reserved identifiers scanned; pinned real compiler '+('PASS' if a.compiler else 'NOT RUN'))
