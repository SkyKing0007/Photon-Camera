#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit('usage: verify_26785_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
SPATIAL=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
IRIS=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
def vals(root,rel):
 text=(Path(root)/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
bs,cs=vals(base,SAB),vals(cand,SAB); bsp,csp=vals(base,SPATIAL),vals(cand,SPATIAL); bst,cst=vals(base,STACK),vals(cand,STACK); bi,ci=vals(base,IRIS),vals(cand,IRIS)
assert set(bs)==set(cs) and sorted(n for n in bs if bs[n]!=cs[n])==['normalDngMerge']
assert bsp==csp,'protected Spatial shader universe changed'
assert bst==cst,'protected Stacker shader universe changed'
assert bi==ci,'protected VGN shader universe changed'
common=ci['common']
shaders={
 'normalDngMerge':('frag',cs['normalDngMerge']),
 'normalizeBayer':('frag',csp['normalizeBayer']),
 'merge':('frag',cs['merge']),
 'EDGE_FALSE_COLOR_SUPPRESSOR_26778':('comp',cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']),
 'universalAdaptiveColor26561':('comp',ci['universalAdaptiveColor26561']),
 'bipolarColorTrust26769':('comp',ci['bipolarColorTrust26769'].replace('$common',common)),
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|double|vec[234]|dvec[234]|bvec[234]|ivec[234]|uvec[234]|mat[234]|mat\d+x\d+|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,(stage,src) in shaders.items():
 names=decl.findall(src); bad=[x for x in names if x.startswith('gl_') or '__' in x or (len(x)>1 and x[0]=='_' and x[1].isupper())]; assert not bad,(name,bad)
 print(f'PASS 26785 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
nd=shaders['normalDngMerge'][1]
for tok in ('IRIS_26785_PHASE_SCOPED_HIGHLIGHT_VALIDITY_OWNER','IRIS_26785_CENSORED_REFERENCE_PHASE','IRIS_26785_TARGET_PHASE_DNG_HEADROOM','referenceFallbackWeight26785 = 0.00005'):
 assert tok in nd,tok
assert 'IRIS_26782_FRACTIONAL_HARD_EDGE_VETO' in nd
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in shaders['universalAdaptiveColor26561'][1]
assert 'IRIS_26784_RETIRE_BROAD_CLIPPED_NEUTRAL' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
print('PASS 26785 modified shader ownership: normalDngMerge only; phase-scoped highlight validity over unchanged shared quad geometry')
print('PASS 26785 protected shader fidelity: normalizeBayer/live merge/26784 JPEG-VGN owners remain byte-identical')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,(stage,s) in shaders.items(): (out/f'{n}.{stage}').write_text(s)
if compiler:
 c=Path(compiler); assert c.exists(),compiler
 with tempfile.TemporaryDirectory(prefix='iris26785_glsl_') as td:
  td=Path(td)
  for n,(stage,s) in shaders.items():
   f=td/f'{n}.{stage}'; f.write_text(s)
   p=subprocess.run([str(c),'-S',stage,str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26785 pinned real glslang compile runtime-expanded shader: {n}')
