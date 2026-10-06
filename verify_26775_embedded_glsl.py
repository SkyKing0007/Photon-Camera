#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, tempfile, textwrap
if len(sys.argv)<2: raise SystemExit('usage: verify_26775_embedded_glsl.py CAND [--compiler PATH] [--out DIR]')
cand=Path(sys.argv[1]); compiler=None; out=None
i=2
while i<len(sys.argv):
    if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
    elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
    else: raise SystemExit('unknown arg '+sys.argv[i])
text=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
def grab(name):
    m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not m: raise SystemExit('missing Kotlin GLSL string '+name)
    return textwrap.dedent(m.group(1)).strip('\n')+'\n'
common=grab('common')
shaders={'seed':grab('seed').replace('$common',common),'bipolarColorTrust26769':grab('bipolarColorTrust26769').replace('$common',common)}
for name,src in shaders.items():
    if '$' in src: raise SystemExit(f'unexpanded Kotlin interpolation remains in {name}')
    if not src.startswith('#version 310 es'): raise SystemExit(f'{name}: wrong version')
    # Complete user-declaration reserved-identifier scan. Built-in gl_* usages are not declarations.
    decl=re.compile(r'\b(?:void|bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler\w*|usampler\w*|image\w*|uimage\w*)\s+([A-Za-z_]\w*)')
    bad=[]
    for ident in decl.findall(src):
        if ident.startswith('gl_') or '__' in ident or (len(ident)>1 and ident[0]=='_' and ident[1].isupper()): bad.append(ident)
    if bad: raise SystemExit(f'{name}: reserved identifiers declared: {sorted(set(bad))}')
    print(f'PASS 26775 reserved-identifier scan {name}: declarations={len(decl.findall(src))}')
if 'IRIS_26775_BLOCK_COHERENT_CFA_PHASE_VALIDITY' not in shaders['seed']: raise SystemExit('seed 26775 marker missing')
if 'IRIS_26775_PERIODIC_CHROMA_OWNER' not in shaders['bipolarColorTrust26769']: raise SystemExit('bipolar 26775 marker missing')
if out:
    out.mkdir(parents=True,exist_ok=True)
    for n,s in shaders.items(): (out/f'{n}.comp').write_text(s)
if compiler:
    c=Path(compiler); 
    if not c.exists(): raise SystemExit('compiler missing')
    with tempfile.TemporaryDirectory(prefix='iris26775_glsl_') as td:
        td=Path(td)
        for n,s in shaders.items():
            f=td/f'{n}.comp'; f.write_text(s)
            p=subprocess.run([str(c),'-S','comp',str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            print(p.stdout,end='')
            if p.returncode: raise SystemExit(f'glslang failed: {n}')
            print(f'PASS 26775 pinned real glslang compile: {n}')
