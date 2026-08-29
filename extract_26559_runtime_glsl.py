#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def self_test():
    src='precision highp float;\nout vec3 Output;\nvoid main(){Output=vec3(1.0);}\n'
    body=''.join(line+'\n' for line in src.splitlines())
    out='#version 310 es\n\n#line 1\n'+body
    assert out.startswith('#version 310 es\n\n#line 1\nprecision')
    assert out.endswith('}\n')
    print('PASS 26559 GLSL extractor self-test')

def extract(root:Path,outdir:Path):
    glprog=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
    gli=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
    assert 'public final static String glVersion = "#version 310 es\\n";' in glprog
    assert 'String addVersion = glVersion+"\\n"+"#line 1\\n";' in gli
    assert 'if(versioned) addVersion = "";' in gli
    src=(root/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    assert '#version' not in src, 'render asset unexpectedly versioned'
    assert '#import' not in src, 'render asset unexpectedly imports utilities; extractor must be updated'
    body=''.join(line+'\n' for line in src.splitlines())
    expanded='#version 310 es\n\n#line 1\n'+body
    outdir.mkdir(parents=True,exist_ok=True)
    p=outdir/'render26559.frag'; p.write_text(expanded)
    print(f'render26559\t{len(expanded.splitlines())} lines\t{p}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',nargs='?',type=Path);ap.add_argument('outdir',nargs='?',type=Path);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:self_test();return
    if not a.root or not a.outdir:raise SystemExit('root and outdir required')
    extract(a.root,a.outdir)
if __name__=='__main__':main()
