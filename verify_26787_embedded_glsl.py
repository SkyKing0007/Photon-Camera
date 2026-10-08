#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit('usage: verify_26787_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); SP=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'); ST=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); IR=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(base,SAB),vals(cand,SAB); bsp,csp=vals(base,SP),vals(cand,SP); bst,cst=vals(base,ST),vals(cand,ST); bi,ci=vals(base,IR),vals(cand,IR)
added=sorted(set(cs)-set(bs)); removed=sorted(set(bs)-set(cs)); modified=sorted(k for k in bs.keys()&cs.keys() if bs[k]!=cs[k])
assert added==['jpegLcaPreResolve26787','jpegNeutralHighlightClamp26787'],(added,removed,modified)
assert not removed and not modified
assert bsp==csp and bst==cst and bi==ci
common=ci['common']
shaders={
 'jpegNeutralHighlightClamp26787':('frag',cs['jpegNeutralHighlightClamp26787']),
 'jpegLcaPreResolve26787':('frag',cs['jpegLcaPreResolve26787']),
 'merge':('frag',cs['merge']),
 'normalDngMerge':('frag',cs['normalDngMerge']),
 'normalizeBayer':('frag',csp['normalizeBayer']),
 'EDGE_FALSE_COLOR_SUPPRESSOR_26778':('comp',cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']),
 'universalAdaptiveColor26561':('comp',ci['universalAdaptiveColor26561']),
 'bipolarColorTrust26769':('comp',ci['bipolarColorTrust26769'].replace('$common',common)),
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|double|vec[234]|dvec[234]|bvec[234]|ivec[234]|uvec[234]|mat[234]|mat\d+x\d+|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,(stage,src) in shaders.items():
 if name in ('jpegNeutralHighlightClamp26787','jpegLcaPreResolve26787','merge','normalDngMerge','normalizeBayer'):
  assert src.lstrip().startswith('#version 300 es'),name
 assert src.count('{')==src.count('}'),(name,src.count('{'),src.count('}'))
 names=decl.findall(src); bad=[x for x in names if x.startswith('gl_') or '__' in x or (len(x)>1 and x[0]=='_' and x[1].isupper())]; assert not bad,(name,bad)
 print(f'PASS 26787 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
print('PASS 26787 modified shader ownership: add JPEG pre-Resolve neutral-clamp + radial-LCA shaders only; no inherited shader body modified')
print('PASS 26787 protected shader fidelity: live merge/DNG normalize/26778/VGN owners byte-identical to successful 26786')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,(stage,s) in shaders.items(): (out/f'{n}.{stage}').write_text(s)
if compiler:
 c=Path(compiler); assert c.exists(),compiler
 with tempfile.TemporaryDirectory(prefix='iris26787_glsl_') as td:
  td=Path(td)
  for n,(stage,s) in shaders.items():
   f=td/f'{n}.{stage}'; f.write_text(s)
   p=subprocess.run([str(c),'-S',stage,str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26787 pinned real glslang compile runtime-expanded shader: {n}')
