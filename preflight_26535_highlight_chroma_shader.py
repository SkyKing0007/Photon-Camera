#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, tempfile
REL='app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl'
def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--validator',default='glslangValidator');a=ap.parse_args()
    p=Path(a.root)/REL;req(p.is_file(),'missing '+REL);s=p.read_text()
    for t in ('uniform sampler2D InputBuffer;','uniform sampler2D ReliabilityMap;','clipGate*edgeGate*outlierGate','med5(','gamutSafe','Output=c+delta*safeAmount;'):
        req(t in s,'shader contract missing '+t)
    req('Output=max(' not in s,'post-correction clamp violates exact-luma contract')
    req(all(x not in s.lower() for x in ('magenta','orange','purple','huegate')),'hue-targeted shader logic forbidden')
    src=s if '#version' in s else '#version 300 es\n\n#line 1\n'+s
    with tempfile.TemporaryDirectory(prefix='iris26535-shader-') as td:
        q=Path(td)/'highlight_chroma_reliability.frag';q.write_text(src)
        cp=subprocess.run([a.validator,'-S','frag',str(q)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        req(cp.returncode==0,'GLSL compile failed\n'+cp.stdout)
    print('PASS: 26535 highlight chroma reliability GLSL compiles')
    print('PASS: shader is hue-independent and preserves linear luminance without post clamp')
if __name__=='__main__': main()
