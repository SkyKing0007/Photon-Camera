#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit('usage: verify_26782_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
SAB=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
IRIS=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def sha_bytes(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def assets(r):
 rr=Path(r)/'app/src/main/assets/shaders'; return {str(p.relative_to(rr)):sha_bytes(p) for p in rr.rglob('*') if p.is_file()}
a,b=assets(base),assets(cand); assert a==b,(len(a),len(b)); print(f'PASS 26782 asset shader universe byte-identical: {len(a)} files')
def vals(root,rel):
 text=(Path(root)/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
baseSab=vals(base,SAB); candSab=vals(cand,SAB); baseIris=vals(base,IRIS); candIris=vals(cand,IRIS); baseStack=vals(base,STACK); candStack=vals(cand,STACK)
assert set(candSab)==set(baseSab)
for n,s in candSab.items():
 if n=='normalDngMerge': continue
 assert s==baseSab[n],f'unexpected inherited Sabre shader byte change: {n}'
assert candSab['normalDngMerge']!=baseSab['normalDngMerge']
assert candSab['merge']==baseSab['merge']
for n in ('common','bipolarColorTrust26769','seed'): assert candIris[n]==baseIris[n],f'inherited Iris carrier changed: {n}'
assert candStack['EDGE_FALSE_COLOR_SUPPRESSOR_26778']!=baseStack['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
common=candIris['common']
shaders={
 'normalDngMerge':('frag',candSab['normalDngMerge']),
 'merge':('frag',candSab['merge']),
 'EDGE_FALSE_COLOR_SUPPRESSOR_26778':('comp',candStack['EDGE_FALSE_COLOR_SUPPRESSOR_26778']),
 'bipolarColorTrust26769':('comp',candIris['bipolarColorTrust26769'].replace('$common',common)),
 'seed':('comp',candIris['seed'].replace('$common',common)),
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|double|vec[234]|dvec[234]|bvec[234]|ivec[234]|uvec[234]|mat[234]|mat\d+x\d+|sampler\w*|isampler\w*|usampler\w*|image\w*|iimage\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,(stage,src) in shaders.items():
 names=decl.findall(src); bad=[x for x in names if x.startswith('gl_') or '__' in x or (len(x)>1 and x[0]=='_' and x[1].isupper())]; assert not bad,(name,bad)
 print(f'PASS 26782 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
assert 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER' in shaders['normalDngMerge'][1]
assert 'IRIS_26782_FRACTIONAL_HARD_EDGE_VETO' in shaders['normalDngMerge'][1]
assert 'IRIS_26782_BLOCK_UNIFORM_DNG_HEADROOM' in shaders['normalDngMerge'][1]
assert 'IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
assert 'IRIS_26782_CLIPPED_NEUTRAL_GUARD' in shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778'][1]
assert 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER' not in (cand/SAB).read_text()
print('PASS 26782 modified shader ownership: normalDngMerge + existing 26778 suppressor extension are the only runtime-expanded shader deltas')
print('PASS 26782 inherited shader fidelity: live merge + bipolarColorTrust26769 + seed preserved byte-identical before expansion; 26780 matched-bandwidth stage remains absent')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,(stage,s) in shaders.items(): (out/f'{n}.{stage}').write_text(s)
if compiler:
 c=Path(compiler); assert c.exists(),compiler
 with tempfile.TemporaryDirectory(prefix='iris26782_glsl_') as td:
  td=Path(td)
  for n,(stage,s) in shaders.items():
   f=td/f'{n}.{stage}'; f.write_text(s)
   p=subprocess.run([str(c),'-S',stage,str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26782 pinned real glslang compile runtime-expanded shader: {n}')
