#!/usr/bin/env python3
from pathlib import Path
import argparse, re, subprocess, tempfile
FILES=[
'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']

def code_only(s):
    out=[]; i=0; state='code'
    while i<len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if state=='code':
            if c=='/' and n=='/': state='line'; out.extend('  '); i+=2; continue
            if c=='/' and n=='*': state='block'; out.extend('  '); i+=2; continue
            if c=='"': state='dq'; out.append(' '); i+=1; continue
            if c=="'": state='sq'; out.append(' '); i+=1; continue
            out.append(c); i+=1; continue
        if state=='line':
            if c=='\n': state='code'; out.append('\n')
            else: out.append(' ')
            i+=1; continue
        if state=='block':
            if c=='*' and n=='/': state='code'; out.extend('  '); i+=2
            else: out.append('\n' if c=='\n' else ' '); i+=1
            continue
        if state in ('dq','sq'):
            quote='"' if state=='dq' else "'"
            if c=='\\': out.extend('  ' if i+1<len(s) else ' '); i+=2; continue
            if c==quote: state='code'; out.append(' '); i+=1; continue
            out.append('\n' if c=='\n' else ' '); i+=1
    if state in ('block','dq','sq'): raise SystemExit('ERROR: unterminated comment/string')
    return ''.join(out)

def balanced(p):
    s=code_only(p.read_text()); pairs={'{':'}','(':')','[':']'}; st=[]
    for c in s:
        if c in pairs: st.append(c)
        elif c in pairs.values():
            if not st or pairs[st.pop()]!=c: raise SystemExit('ERROR: unbalanced '+str(p))
    if st: raise SystemExit('ERROR: unbalanced '+str(p))

def run(root,validator=None):
    for rel in FILES:
        p=root/rel
        if not p.is_file(): raise SystemExit('ERROR: missing changed file '+rel)
        balanced(p)
    shader=root/FILES[0]; s=shader.read_text()
    for t in ('void main()','out vec3 Output','uniform sampler2D InputBuffer','uniform sampler2D ReliabilityMap','uniform vec3 CameraNeutral'):
        if t not in s: raise SystemExit('ERROR: shader contract missing '+t)
    if validator:
        with tempfile.TemporaryDirectory() as td:
            q=Path(td)/'highlight.frag'; q.write_text('#version 310 es\n'+s)
            r=subprocess.run([validator,'-S','frag',str(q)],text=True,capture_output=True)
            if r.returncode: raise SystemExit('ERROR: glslang failed\n'+r.stdout+r.stderr)
            print('PASS: changed highlight GLSL compiles with '+validator)
    print('PASS: 26541 changed Java/Kotlin/GLSL lexical/balance contracts')

def self_test():
    root=Path('/mnt/data/iris26541_work/candidate26541')
    if root.exists(): run(root,None)
    print('PASS: 26541 changed syntax self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
