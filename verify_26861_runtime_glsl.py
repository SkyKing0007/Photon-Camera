#!/usr/bin/env python3
"""Exact Kotlin GLES300 shader extraction, static reserved scan, pinned compiler.

Scans all seven B active/protected shader fragments; NO placeholder GLSL.
"""
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('candidate');p.add_argument('--compiler');p.add_argument('--out',required=True)
a=p.parse_args();B=Path(a.base);C=Path(a.candidate);O=Path(a.out);O.mkdir(parents=True,exist_ok=True)
PR='app/src/main/java/com/hinnka/mycamera/processor/'
files={
 'temporal_cfa_accumulate':('GlesMgcRawSabreShaders.kt','normalCfaTemporalAccumulate26852'),
 'b_motion_only_weight':('GlesIris26858BNoiseHighlight.kt','bMotionOnlyWeight26861'),
 'b_temporal_weighted_identity':('GlesIris26858BNoiseHighlight.kt','bWeightedCfaIdentity26861'),
 'b_clip_votes':('GlesIris26858BNoiseHighlight.kt','bClipAccumulate'),
 'b_clip_normalize':('GlesIris26858BNoiseHighlight.kt','bClipNormalize'),
 'b_highlight_neutral':('GlesIris26858BNoiseHighlight.kt','bHighlightRecover'),
 'b_physical_lsc':('GlesIris26858BNoiseHighlight.kt','bLensShade'),
}
S=(C/PR/'GlesMgcRawSpatialStacker.kt').read_text();BN=(C/PR/'GlesIris26860BBurstNoise.kt').read_text()
assert S.count('renderSabreNormalCfaTemporalAccumulate26852(')>=2
for attr in ('iris26861BMotionOnlyProgram','iris26861BWeightedIdentityProgram','iris26858BClipAccumulateProgram',
             'iris26858BClipNormalizeProgram','iris26858BHighlightProgram','iris26859BLensShadeProgram'):
 assert S.count(attr)>=2,('missing owned B program',attr)
assert 'renderIris26858BNoiseClean' not in S and 'renderIris26858BResidualChroma' not in S
assert 'bBurstNoise26860 = if (iris26856AmazeCfaConsumer != null)' in S
assert S.count('GlesIris26860BBurstNoise.estimate(')==1
assert 'bEmpiricalNoise26861 = bBurstNoise26860,' in S
assert 'BURST_UNSUPPORTED_' in BN and 'CAMERA2_FALLBACK_' not in BN
assert 'renderIris26861BMotionOnlyWeight(' in S and 'renderIris26861BWeightedIdentity(' in S
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in S
assert S.index('bRecovered26858 = renderIris26858BHighlightColor(') < S.index('defringed = renderRawrLabDefringe26856(') < S.index('fcc = renderRawrFalseColor26856(')
assert 'IRIS_26859_B_SINGLE_PHYSICAL_LSC_OWNER' in S
assert 'bindTexture(p, "uLensShading", 1, iris26859BLensMapTexture)' in S
assert (B/PR/'GlesMgcRawSabreShaders.kt').read_bytes()==(C/PR/'GlesMgcRawSabreShaders.kt').read_bytes()
assert S.count('bEmpiricalNoise26861?.shot ?: shot26855')==1 and S.count('bEmpiricalNoise26861?.read ?: read26855')==1
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major'.split())
tt=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'
for label,(file,owner) in files.items():
 t=(C/PR/file).read_text();reg=r'\bval\s+'+re.escape(owner)+r'\s*=\s*"""'
 hits=list(re.finditer(reg,t));assert len(hits)==1,(label,owner,'anchor count',len(hits))
 start=hits[0].end();end=t.find('""".trimIndent()',start);assert end>start,(label,'unclosed shader')
 src=textwrap.dedent(t[start:end]).strip('\n')+'\n'
 assert src.startswith('#version 300 es\n'),(label,'GLES 300 version')
 assert src.count('#version')==1 and 'void main()' in src
 assert not re.search(r'\$[A-Za-z_]|#include|#import|#line|\$\{',src),label
 clean=re.sub(r'//[^\n]*',' ',re.sub(r'/\*.*?\*/',' ',src,flags=re.S))
 decl=set(re.findall(r'\b'+tt+r'\s+([A-Za-z_]\w*)',clean))
 bad={name for name in decl if name in reserved or name.startswith('gl_') or name.startswith('__')}
 assert not bad,(label,'GLSL ES reserved',bad)
 assert src.count('{')==src.count('}'),(label,'brace mismatch')
 out=O/(label+'.frag');out.write_text(src)
 if a.compiler:
  test=subprocess.run([a.compiler,'-S','frag',str(out)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if test.returncode: raise SystemExit(f'FAIL pinned glslang {label}:\n{test.stdout}')
 print('PASS 26861 runtime-expanded GLSL',label,hashlib.sha256(src.encode()).hexdigest(),'real-glslang='+('PASS' if a.compiler else 'NOT RUN'))
print('PASS 26861 GLSL ownership: 7 exact runtime-expanded GLES300 fragment sources, reserved identifiers, owner/consumer links; pinned real compiler '+('PASS' if a.compiler else 'NOT RUN'))
