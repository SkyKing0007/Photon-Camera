#!/usr/bin/env python3
from pathlib import Path
import argparse, re, subprocess, tempfile

GLSL_RESERVED_IDENTIFIERS = {
    'attribute','const','uniform','varying','buffer','shared','coherent','volatile','restrict',
    'readonly','writeonly','atomic_uint','layout','centroid','flat','smooth','noperspective',
    'patch','sample','break','continue','do','for','while','switch','case','default','if','else',
    'subroutine','in','out','inout','float','double','int','void','bool','true','false',
    'invariant','precise','discard','return','mat2','mat3','mat4','dmat2','dmat3','dmat4',
    'mat2x2','mat2x3','mat2x4','mat3x2','mat3x3','mat3x4','mat4x2','mat4x3','mat4x4',
    'vec2','vec3','vec4','ivec2','ivec3','ivec4','bvec2','bvec3','bvec4','dvec2','dvec3','dvec4',
    'uint','uvec2','uvec3','uvec4','lowp','mediump','highp','precision','sampler2D','samplerCube',
    'sampler3D','sampler2DShadow','samplerCubeShadow','isampler2D','usampler2D','struct',
}

def reject_reserved_decl_identifiers(source, shader_name):
    no_block = re.sub(r'/\*.*?\*/', ' ', source, flags=re.S)
    no_line = re.sub(r'//.*', ' ', no_block)
    decl = re.compile(
        r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234])\s+([A-Za-z_]\w*)\b'
    )
    for m in decl.finditer(no_line):
        if m.group(1) in GLSL_RESERVED_IDENTIFIERS:
            raise SystemExit('ERROR: GLSL reserved identifier '+m.group(1)+' in '+shader_name)

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
    reject_reserved_decl_identifiers(cov, 'covariance')
    reject_reserved_decl_identifiers(merge, 'mergeRgb')
    for t in ('#version 300 es','uniform ivec2 uCovarianceOrigin;','uniform float uKStretch;','uniform float uKShrink;','void main()'):
        if t not in cov: raise SystemExit('ERROR: covariance GLSL contract missing '+t)
    if 'float kernelWeight(vec2 pixelOffset, vec3 precisionCoeffs)' not in merge:
        raise SystemExit('ERROR: 26543 V1.1 reserved-keyword correction missing')
    if 'return exp(-0.5 * max(distance, 0.0));' not in merge or 'exp2(-0.5' in merge or '0.00005' in merge:
        raise SystemExit('ERROR: active merge Gaussian contract')
    if validator:
        compile_embedded(validator,sh,'covariance'); compile_embedded(validator,sh,'mergeRgb')
        print('PASS: active embedded covariance + mergeRgb compile with '+validator)
    print('PASS: 26543 changed Java/Kotlin lexical/balance + embedded GLSL contracts')

def self_test():
    x='fun x(){ val s=""" { ignored } """; if(true){ println("x") } }'
    assert code_only(x).count('{')==2
    try:
        reject_reserved_decl_identifiers('float f(vec3 precision){ return precision.x; }', 'selftest')
    except SystemExit:
        pass
    else:
        raise AssertionError('reserved GLSL identifier self-test did not fail')
    reject_reserved_decl_identifiers('float f(vec3 precisionCoeffs){ return precisionCoeffs.x; }', 'selftest-good')
    print('PASS: 26543 V1.1 changed syntax + GLSL reserved-identifier self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
