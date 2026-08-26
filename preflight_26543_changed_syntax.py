#!/usr/bin/env python3
from pathlib import Path
import argparse, re, subprocess, tempfile
FILES=[
'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
]

def code_only(s):
    out=[]; i=0; state='code'
    while i<len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if state=='code':
            if s.startswith('"""',i): state='triple'; out.extend('   '); i+=3; continue
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
        if state=='triple':
            if s.startswith('"""',i): state='code'; out.extend('   '); i+=3
            else: out.append('\n' if c=='\n' else ' '); i+=1
            continue
        quote='"' if state=='dq' else "'"
        if c=='\\': out.extend('  ' if i+1<len(s) else ' '); i+=2; continue
        if c==quote: state='code'; out.append(' '); i+=1; continue
        out.append('\n' if c=='\n' else ' '); i+=1
    if state in ('block','dq','sq','triple'): raise SystemExit('ERROR: unterminated comment/string')
    return ''.join(out)

def balanced(p):
    s=code_only(p.read_text()); pairs={'{':'}','(':')','[':']'}; st=[]
    for c in s:
        if c in pairs: st.append(c)
        elif c in pairs.values():
            if not st or pairs[st.pop()]!=c: raise SystemExit('ERROR: unbalanced '+str(p))
    if st: raise SystemExit('ERROR: unbalanced '+str(p))

def embedded_shader(shader_file,name):
    s=shader_file.read_text()
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
    if not m: raise SystemExit('ERROR: embedded shader not found: '+name)
    return m.group(1).strip()+'\n'

def compile_embedded(validator,shader_file,name):
    source=embedded_shader(shader_file,name)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/(name+'.frag'); p.write_text(source)
        r=subprocess.run([validator,'-S','frag',str(p)],text=True,capture_output=True)
        if r.returncode: raise SystemExit('ERROR: glslang failed '+name+'\n'+r.stdout+r.stderr)

def run(root,validator=None):
    for rel in FILES:
        p=root/rel
        if not p.is_file(): raise SystemExit('ERROR: missing changed file '+rel)
        balanced(p)
    sh=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
    cov=embedded_shader(sh,'covariance'); merge=embedded_shader(sh,'mergeRgb')
    for t in ('#version 300 es','uniform ivec2 uCovarianceOrigin;','uniform float uKStretch;','uniform float uKShrink;','void main()'):
        if t not in cov: raise SystemExit('ERROR: covariance GLSL contract missing '+t)
    if 'return exp(-0.5 * max(distance, 0.0));' not in merge or 'exp2(-0.5' in merge or '0.00005' in merge:
        raise SystemExit('ERROR: active merge Gaussian contract')
    if validator:
        compile_embedded(validator,sh,'covariance'); compile_embedded(validator,sh,'mergeRgb')
        print('PASS: active embedded covariance + mergeRgb compile with '+validator)
    print('PASS: 26543 changed Java/Kotlin lexical/balance + embedded GLSL contracts')

def self_test():
    x='fun x(){ val s=""" { ignored } """; if(true){ println("x") } }'
    assert code_only(x).count('{')==2
    print('PASS: 26543 changed syntax self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
