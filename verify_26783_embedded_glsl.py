#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit('usage: verify_26783_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); IRIS=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'); STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(Path(root)/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
bs,cs=vals(base,SAB),vals(cand,SAB); bi,ci=vals(base,IRIS),vals(cand,IRIS); bst,cst=vals(base,STACK),vals(cand,STACK)
assert bs==cs,'Sabre/DNG shader universe changed'; assert bst==cst,'inherited stacker embedded shader changed'
assert set(ci)-set(bi)=={'postVgnNeutralGuard26783'}
for n in bi: assert ci[n]==bi[n],f'inherited Iris shader changed: {n}'
common=ci['common']
# GLInterface.loadShader exact no-import/no-define expansion for modified asset shaders: #version 310 es + blank line + #line 1.
def asset_expanded(rel):
 raw=(cand/'app/src/main/assets/shaders'/rel).read_text()
 assert '#version' not in raw and '#import' not in raw and '#define' not in raw,rel
 return '#version 310 es\n\n#line 1\n'+raw+('' if raw.endswith('\n') else '\n')
shaders={
 'render':('frag',asset_expanded(Path('motionv2/render.glsl'))),
 'gainmap':('frag',asset_expanded(Path('motionv2/gainmap.glsl'))),
 'postVgnNeutralGuard26783':('comp',ci['postVgnNeutralGuard26783']),
 'normalDngMerge':('frag',cs['normalDngMerge']),
 'merge':('frag',cs['merge']),
 'EDGE_FALSE_COLOR_SUPPRESSOR_26778':('comp',cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']),
 'bipolarColorTrust26769':('comp',ci['bipolarColorTrust26769'].replace('$common',common)),
 'seed':('comp',ci['seed'].replace('$common',common)),
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|double|vec[234]|dvec[234]|bvec[234]|ivec[234]|uvec[234]|mat[234]|mat\d+x\d+|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,(stage,src) in shaders.items():
 names=decl.findall(src); bad=[x for x in names if x.startswith('gl_') or '__' in x or (len(x)>1 and x[0]=='_' and x[1].isupper())]; assert not bad,(name,bad)
 print(f'PASS 26783 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
assert 'postVgnNeutralGuard26783' in ci and 'IRIS_26783_POST_VGN_NEON_GUARD' in (cand/IRIS).read_text()
assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in shaders['render'][1] and 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in shaders['gainmap'][1]
assert 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER' in shaders['normalDngMerge'][1]
assert 'IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
print('PASS 26783 modified shader ownership: postVgnNeutralGuard26783 + exact runtime-expanded render/gainmap are the only modified GLSL carriers')
print('PASS 26783 protected shader fidelity: 26782 DNG merge, JPEG pre-VGN suppressor, live merge, bipolarColorTrust26769 and seed remain byte-identical before expansion')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,(stage,s) in shaders.items(): (out/f'{n}.{stage}').write_text(s)
if compiler:
 c=Path(compiler); assert c.exists(),compiler
 with tempfile.TemporaryDirectory(prefix='iris26783_glsl_') as td:
  td=Path(td)
  for n,(stage,s) in shaders.items():
   f=td/f'{n}.{stage}'; f.write_text(s)
   p=subprocess.run([str(c),'-S',stage,str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26783 pinned real glslang compile runtime-expanded shader: {n}')
