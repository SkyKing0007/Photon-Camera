#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile
from pathlib import Path

REL='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
EXPECTED_CHANGED={'rejectionFilter','rejectionFilterDownsample','rejectionPixelDifferenceDownsample','rejectionPostprocess'}
EXPECTED_REMOVED={'convertBayerAlignment'}
PAT=re.compile(r'\bval\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',re.S)
def shaders(p:Path):
    s=p.read_text(encoding='utf-8').replace('\r\n','\n').replace('\r','\n')
    return {m.group(1):m.group(2) for m in PAT.finditer(s)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--validator',required=True); a=ap.parse_args()
    b=shaders(Path(a.base)/REL); c=shaders(Path(a.candidate)/REL)
    changed={k for k in b.keys()&c.keys() if b[k]!=c[k]} | (c.keys()-b.keys())
    removed=b.keys()-c.keys()
    if changed!=EXPECTED_CHANGED: raise SystemExit(f'embedded shader changed set drift: {sorted(changed)}')
    if removed!=EXPECTED_REMOVED: raise SystemExit(f'embedded shader removed set drift: {sorted(removed)}')
    with tempfile.TemporaryDirectory(prefix='iris26527-glsl-') as td:
        td=Path(td)
        for name in sorted(EXPECTED_CHANGED):
            src=c[name].strip()+'\n'
            if not src.startswith('#version 300 es'): raise SystemExit(name+': unexpected GLSL version')
            if 'void main()' not in src: raise SystemExit(name+': no main')
            stage='comp' if 'local_size_' in src else 'frag'
            f=td/(name+'.glsl'); f.write_text(src)
            r=subprocess.run([a.validator,'-S',stage,str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if r.returncode!=0:
                print(r.stdout)
                raise SystemExit(f'glslang failed {name}')
            print(f'PASS: glslang embedded {name} stage={stage}')
    print('PASS: exact four changed embedded shaders compile; obsolete convertBayerAlignment removed')
if __name__=='__main__': main()
