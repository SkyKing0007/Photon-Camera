#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, tempfile

REL='app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl'

def fail(msg): raise SystemExit('FAIL: '+msg)
def req(c,msg):
    if not c: fail(msg)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    p=Path(a.root)/REL; req(p.is_file(),'missing '+REL)
    src=p.read_text(encoding='utf-8')
    req(src.count('#define LAYOUT //')==1,'LAYOUT define anchor drift')
    for tok in ('uniform highp sampler2D normalCfa;',
                'layout(r32f, binding = 0) uniform highp writeonly image2D outProvenance;',
                'uniform float referenceExposureScale;', 'uniform float physicalClipThreshold;',
                'imageStore(outProvenance'):
        req(tok in src,'provenance shader contract missing '+tok)
    # Reproduce GLProg.setLayout(8,8,1) + GLInterface.readProgram semantics used by V1.6.
    src=src.replace('#define LAYOUT //',
                    '#define LAYOUT layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;',1)
    if '#version' not in src:
        src='#version 310 es\n\n#line 1\n'+src
    with tempfile.TemporaryDirectory(prefix='iris26533-v16-prov-') as td:
        q=Path(td)/'highlight_provenance_init.comp'; q.write_text(src)
        cp=subprocess.run([a.validator,'-S','comp',str(q)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if cp.returncode: fail('provenance GLSL failed:\n'+cp.stdout)
    print('PASS: V1.6 normalized16 CENSORED provenance compute shader compiles with exact 8x8 host layout')

if __name__=='__main__': main()
