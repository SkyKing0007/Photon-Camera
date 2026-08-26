#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,tempfile

RESERVED={
'attribute','const','uniform','varying','buffer','shared','coherent','volatile','restrict',
'readonly','writeonly','atomic_uint','layout','centroid','flat','smooth','noperspective','patch',
'sample','break','continue','do','for','while','switch','case','default','if','else','subroutine',
'in','out','inout','float','double','int','void','bool','true','false','invariant','precise',
'discard','return','mat2','mat3','mat4','dmat2','dmat3','dmat4','vec2','vec3','vec4','ivec2',
'ivec3','ivec4','bvec2','bvec3','bvec4','dvec2','dvec3','dvec4','uint','uvec2','uvec3','uvec4',
'lowp','mediump','highp','precision','sampler2D','samplerCube','sampler3D','sampler2DShadow',
'samplerCubeShadow','isampler2D','usampler2D','struct',
}

def fail(m): raise SystemExit('ERROR: '+m)
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
    if state in ('block','dq','sq','triple'): fail('unterminated comment/string')
    return ''.join(out)

def balanced(path):
    s=code_only(path.read_text()); pairs={'{':'}','(':')','[':']'}; st=[]
    for c in s:
        if c in pairs: st.append(c)
        elif c in pairs.values():
            if not st or pairs[st.pop()]!=c: fail('unbalanced '+str(path))
    if st: fail('unbalanced '+str(path))

def vals(path):
    s=path.read_text(); out={}
    for m in re.finditer(r'\b(?:private\s+)?val\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S):
        out[m.group(1)]=m.group(2).strip()+'\n'
    return out

def expand(src, table):
    # Only simple Kotlin $name substitutions are used by the audited shader objects.
    for _ in range(10):
        names=re.findall(r'\$([A-Za-z_]\w*)',src)
        if not names: return src
        before=src
        for n in names:
            if n not in table: fail('unresolved Kotlin shader substitution $'+n)
            src=src.replace('$'+n,table[n].rstrip('\n'))
        if src==before: break
    if re.search(r'\$[A-Za-z_]\w*',src): fail('unresolved shader interpolation')
    return src

def reject_reserved(source,name):
    no_block=re.sub(r'/\*.*?\*/',' ',source,flags=re.S)
    no_line=re.sub(r'//.*',' ',no_block)
    decl=re.compile(r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234])\s+([A-Za-z_]\w*)\b')
    for m in decl.finditer(no_line):
        if m.group(1) in RESERVED: fail(f'GLSL reserved identifier {m.group(1)} in {name}')

def compile_shader(validator,name,src):
    reject_reserved(src,name)
    if '#version 300 es' not in src: fail(name+' missing #version 300 es')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/(name+'.frag'); p.write_text(src)
        r=subprocess.run([validator,'-S','frag',str(p)],text=True,capture_output=True)
        if r.returncode: fail('glslang failed '+name+'\n'+r.stdout+r.stderr)

def run(root,validator=None):
    sabre=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    shared=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
    stacker=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
    for p in (sabre,shared,stacker):
        if not p.is_file(): fail('missing '+str(p))
        balanced(p)
    sv=vals(sabre); shv=vals(shared)
    modified=['extractBayer','guideAndCovariance','rejection','merge','convertAlignmentSparse',
              'normalDngMerge','copyMask','copyAlpha','reciprocalGreenWeight4x4','dehomogenize',
              'outputTransformUint16','outputTransformFloat']
    inherited=['rawToGray','grayDownsample','grayDownsample4','alignmentGradientProducts',
               'upsampleAlignment','blockLucasKanade','unblocker','dilateRejection','normalizeBayer']
    missing=[x for x in modified if x not in sv]+[x for x in inherited if x not in shv]
    if missing: fail('missing active shader(s): '+repr(missing))
    sources=[]
    for name in modified: sources.append(('sabre_'+name,expand(sv[name],sv)))
    for name in inherited: sources.append(('shared_'+name,expand(shv[name],shv)))
    # Contract checks for new failure-prone portions.
    req={
      'sabre_merge':['uFlowScaleOffset','uFrameBorderPadded','uCovariance','uRejection'],
      'sabre_rejection':['uFlowScaleOffset','uExtraMotionRobustnessMotionThreshold'],
      'sabre_normalDngMerge':['oSignalAndWeight','uPhaseGains','uPhaseBlackTerms','uFlowScaleOffset'],
      'sabre_reciprocalGreenWeight4x4':['weightQ8','256.0 / weightQ8','oReciprocalSumAndCount'],
    }
    by=dict(sources)
    for name,tokens in req.items():
        for t in tokens:
            if t not in by[name]: fail(name+' contract missing '+t)
    for name,src in sources: reject_reserved(src,name)
    if validator:
        for name,src in sources: compile_shader(validator,name,src)
        print(f'PASS: REAL GLSL COMPILE {len(sources)} active Sabre/dependency shaders via {validator}')
    print(f'PASS: 26545 Sabre GLSL extraction/contracts shaders={len(sources)}')

def self_test():
    reject_reserved('float f(vec3 precisionCoeffs){ return precisionCoeffs.x; }','good')
    try: reject_reserved('float f(vec3 precision){ return precision.x; }','bad')
    except SystemExit: pass
    else: raise AssertionError('reserved identifier self-test did not fail')
    assert expand('#version 300 es\n$body',{'body':'void main(){}\n'}).endswith('void main(){}')
    print('PASS: 26545 GLSL preflight self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
