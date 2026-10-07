#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, tempfile, textwrap, hashlib
if len(sys.argv)<3: raise SystemExit('usage: verify_26776_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None
i=3
while i<len(sys.argv):
    if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
    elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
    else: raise SystemExit('unknown arg '+sys.argv[i])
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
def vals(root):
    text=(root/rel).read_text()
    return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
bv,cv=vals(base),vals(cand)
modified=sorted(n for n in set(bv)|set(cv) if bv.get(n)!=cv.get(n))
EXPECTED=['bipolarColorTrust26769','directionalSmooth','iirRgb','localMedian','seed']
if modified!=EXPECTED: raise SystemExit(f'modified embedded shader set differs: {modified}')
common=cv['common']
shaders={n:cv[n].replace('$common',common) for n in modified}
decl=re.compile(r'\b(?:void|bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler\w*|usampler\w*|image\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,src in shaders.items():
    if '$' in src: raise SystemExit(f'unexpanded Kotlin interpolation remains in {name}')
    if not src.startswith('#version 310 es'): raise SystemExit(f'{name}: wrong version')
    bad=[]
    for ident in decl.findall(src):
        if ident.startswith('gl_') or '__' in ident or (len(ident)>1 and ident[0]=='_' and ident[1].isupper()): bad.append(ident)
    if bad: raise SystemExit(f'{name}: reserved identifiers declared: {sorted(set(bad))}')
    print(f'PASS 26776 reserved-identifier scan {name}: declarations={len(decl.findall(src))} sha256={hashlib.sha256(src.encode()).hexdigest()}')
for marker,name in [
 ('IRIS_26776_CLAUDE_PRE_OWNERSHIP_CFA_VALIDITY','seed'),
 ('IRIS_26776_POST_DEMOSAIC_RG_BG_MEDIAN_OWNER','localMedian'),
 ('0x8000','directionalSmooth'),('phaseInvalidAt26776','iirRgb'),
 ('IRIS_26776_RESIDUAL_PERIODIC_CHROMA_OWNER','bipolarColorTrust26769')]:
    if marker not in shaders[name]: raise SystemExit(f'{name}: marker missing: {marker}')
if out:
    out.mkdir(parents=True,exist_ok=True)
    for n,s in shaders.items(): (out/f'{n}.comp').write_text(s)
if compiler:
    c=Path(compiler)
    if not c.exists(): raise SystemExit('compiler missing')
    with tempfile.TemporaryDirectory(prefix='iris26776_glsl_') as td:
        td=Path(td)
        for n,s in shaders.items():
            f=td/f'{n}.comp'; f.write_text(s)
            p=subprocess.run([str(c),'-S','comp',str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            print(p.stdout,end='')
            if p.returncode: raise SystemExit(f'glslang failed: {n}')
            print(f'PASS 26776 pinned real glslang compile: {n}')
print('PASS 26776 exact modified embedded shader set: '+','.join(modified))
