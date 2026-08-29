#!/usr/bin/env python3
from pathlib import Path
import argparse,re
NAMES=('mergeShadowLong26558','copyMaskShadowLong26558')

def kotlin_trim_indent(s:str)->str:
    lines=s.splitlines()
    while lines and lines[0].strip()=='': lines.pop(0)
    while lines and lines[-1].strip()=='': lines.pop()
    if not lines:return ''
    indents=[len(line)-len(line.lstrip()) for line in lines if line.strip()]
    m=min(indents) if indents else 0
    out=[]
    for line in lines:
        cut=min(m,len(line)-len(line.lstrip())) if line.strip() else min(m,len(line))
        out.append(line[cut:])
    return '\n'.join(out)

def raw_value(text,name):
    pat=re.compile(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',re.S)
    m=pat.search(text)
    if not m: raise SystemExit(f'missing raw-string shader {name}')
    return kotlin_trim_indent('\n'+m.group(1)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source',type=Path,nargs='?'); ap.add_argument('outdir',type=Path,nargs='?'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        assert kotlin_trim_indent('\n    #version 300 es\n      void main(){}\n    ')=='#version 300 es\n  void main(){}'
        print('PASS 26558 GLSL extractor self-test'); return
    if a.source is None or a.outdir is None: raise SystemExit('source and outdir required')
    text=a.source.read_text(); a.outdir.mkdir(parents=True,exist_ok=True)
    for name in NAMES:
        src=raw_value(text,name)
        if not re.match(r'^\s*#version 300 es(?:\n|$)',src): raise SystemExit(f'{name}: runtime shader does not start #version 300 es')
        if '${' in src or '$common' in src or '#import' in src: raise SystemExit(f'{name}: unexpected unresolved preprocessing')
        out=a.outdir/(name+'.frag'); out.write_text(src+'\n')
        print(f'{name}\t{len(src.splitlines())} lines\t{out}')
if __name__=='__main__':main()
