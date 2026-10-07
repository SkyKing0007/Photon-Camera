#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit('usage: verify_26784_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); IRIS=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'); STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(Path(root)/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
bs,cs=vals(base,SAB),vals(cand,SAB); bi,ci=vals(base,IRIS),vals(cand,IRIS); bst,cst=vals(base,STACK),vals(cand,STACK)
assert bs==cs,'Sabre/DNG shader universe changed'
assert set(bi)-set(ci)=={'postVgnNeutralGuard26783'} and not(set(ci)-set(bi))
for n in ci:
 if n!='universalAdaptiveColor26561': assert ci[n]==bi[n],f'inherited Iris shader changed: {n}'
assert sorted(n for n in bst if bst[n]!=cst[n])==['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
common=ci['common']
# Active shader set that must compile under the exact runtime contract.
shaders={
 'universalAdaptiveColor26561':('comp',ci['universalAdaptiveColor26561']),
 'EDGE_FALSE_COLOR_SUPPRESSOR_26778':('comp',cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']),
 'bipolarColorTrust26769':('comp',ci['bipolarColorTrust26769'].replace('$common',common)),
 'seed':('comp',ci['seed'].replace('$common',common)),
 'localMedian':('comp',ci['localMedian'].replace('$common',common)),
 'directionalSmooth':('comp',ci['directionalSmooth'].replace('$common',common)),
 'iirRgb':('comp',ci['iirRgb'].replace('$common',common)),
 'normalDngMerge':('frag',cs['normalDngMerge']),
 'merge':('frag',cs['merge']),
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|double|vec[234]|dvec[234]|bvec[234]|ivec[234]|uvec[234]|mat[234]|mat\d+x\d+|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,(stage,src) in shaders.items():
 names=decl.findall(src); bad=[x for x in names if x.startswith('gl_') or '__' in x or (len(x)>1 and x[0]=='_' and x[1].isupper())]; assert not bad,(name,bad)
 print(f'PASS 26784 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in shaders['universalAdaptiveColor26561'][1]
assert 'IRIS_26784_RETIRE_BROAD_CLIPPED_NEUTRAL' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
assert 'IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
assert 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER' in shaders['normalDngMerge'][1]
assert 'postVgnNeutralGuard26783' not in ci
print('PASS 26784 modified shader ownership: universalAdaptiveColor26561 ownership boundary + pre-VGN suppressor overreach only; postVgnNeutralGuard26783 removed')
print('PASS 26784 protected shader fidelity: DNG merge/live merge/26769/seed/localMedian/directionalSmooth/iirRgb remain current-authority carriers')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,(stage,s) in shaders.items(): (out/f'{n}.{stage}').write_text(s)
if compiler:
 c=Path(compiler); assert c.exists(),compiler
 with tempfile.TemporaryDirectory(prefix='iris26784_glsl_') as td:
  td=Path(td)
  for n,(stage,s) in shaders.items():
   f=td/f'{n}.{stage}'; f.write_text(s)
   p=subprocess.run([str(c),'-S',stage,str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26784 pinned real glslang compile runtime-expanded shader: {n}')
