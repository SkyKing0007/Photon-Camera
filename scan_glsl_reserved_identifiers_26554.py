#!/usr/bin/env python3
from pathlib import Path
import argparse,re,sys

# Conservative union of reserved words/keywords from GLSL and GLSL ES generations.
# The scan applies only to declared identifiers, so language keywords used grammatically are fine.
RESERVED = set('''
attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint
layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else
subroutine in out inout float double int void bool true false invariant precise discard return
mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4
dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4
vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uvec2 uvec3 uvec4
lowp mediump highp precision
sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow
sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow sampler2DMS sampler2DMSArray
samplerCubeArray samplerCubeArrayShadow samplerBuffer sampler2DRect sampler2DRectShadow
isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray isampler2DMS isampler2DMSArray
isamplerCubeArray isamplerBuffer isampler2DRect
usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray usampler2DMS usampler2DMSArray
usamplerCubeArray usamplerBuffer usampler2DRect
image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray
iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray
uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray
struct
common partition active asm class union enum typedef template this resource goto inline noinline public static extern external
interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4
sampler3DRect filter sizeof cast namespace using row_major
'''.split())

BUILTIN_TYPES = set('''
float double int uint bool void
vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4
mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4
dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4
sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow
sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow sampler2DMS sampler2DMSArray samplerCubeArray samplerCubeArrayShadow samplerBuffer sampler2DRect sampler2DRectShadow
isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray isampler2DMS isampler2DMSArray isamplerCubeArray isamplerBuffer isampler2DRect
usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray usampler2DMS usampler2DMSArray usamplerCubeArray usamplerBuffer usampler2DRect
image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray
iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray
uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray
atomic_uint
'''.split())
QUALIFIERS=set('const uniform buffer shared coherent volatile restrict readonly writeonly layout centroid flat smooth noperspective patch sample in out inout lowp mediump highp precise invariant'.split())

COMMENT_RE=re.compile(r'//[^\n]*|/\*.*?\*/',re.S)
TOKEN_RE=re.compile(r'[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|==|!=|<=|>=|\+\+|--|&&|\|\||[{}()\[\],;=+\-*/<>?:.&|!%]')

def strip_source(src):
    src=COMMENT_RE.sub(lambda m:'\n'*m.group(0).count('\n'),src)
    src='\n'.join('' if line.lstrip().startswith('#') else line for line in src.splitlines())
    return src

def tokenize(src):
    clean=strip_source(src)
    out=[]
    for lineno,line in enumerate(clean.splitlines(),1):
        for m in TOKEN_RE.finditer(line): out.append((m.group(0),lineno))
    return out

def declared_identifiers(src):
    toks=tokenize(src)
    custom=set()
    decl=[]
    # struct names
    for i,(t,ln) in enumerate(toks[:-1]):
        if t=='struct' and re.match(r'^[A-Za-z_]',toks[i+1][0]):
            custom.add(toks[i+1][0]); decl.append((toks[i+1][0],toks[i+1][1],'struct'))
    types=BUILTIN_TYPES|custom
    # identifiers immediately following a type token are declarations/function names.
    # Handle optional array and comma declarators within the same declaration statement.
    i=0
    while i<len(toks)-1:
        t,ln=toks[i]
        if t in types:
            j=i+1
            # function/var/param declaration first name
            if j<len(toks) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$',toks[j][0]):
                name,nln=toks[j]
                # Do not double-count a custom type declaration: struct State {
                if not (i>0 and toks[i-1][0]=='struct'):
                    kind='function' if j+1<len(toks) and toks[j+1][0]=='(' else 'identifier'
                    decl.append((name,nln,kind))
                # for comma-separated variables of same type: float a,b,c;
                if not (j+1<len(toks) and toks[j+1][0]=='('):
                    depth=0; k=j+1
                    while k<len(toks):
                        x=toks[k][0]
                        if x in '([{': depth+=1
                        elif x in ')]}': depth=max(0,depth-1)
                        if depth==0 and x==';': break
                        if depth==0 and x==',':
                            q=k+1
                            if q<len(toks) and toks[q][0] in types:
                                q += 1
                            if q<len(toks) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$',toks[q][0]):
                                # A comma in constructor/expression is not a declarator; require that
                                # we have not entered '=' at top level since previous comma/name.
                                segment=[z[0] for z in toks[j+1:k]]
                                # Initial declaration can have initializer containing commas; only
                                # accept when preceding top-level segment does not contain unmatched function call.
                                decl.append((toks[q][0],toks[q][1],'identifier'))
                        k+=1
            i=j
        i+=1
    # Function parameters need qualifier + custom/builtin type + identifier. General pass catches type->name.
    # De-duplicate exact name/line/kind triples.
    seen=set(); uniq=[]
    for d in decl:
        if d not in seen: seen.add(d); uniq.append(d)
    return uniq

def scan(path:Path):
    src=path.read_text()
    decl=declared_identifiers(src)
    bad=[d for d in decl if d[0] in RESERVED]
    return decl,bad

def self_test():
    good='''#version 310 es\nprecision highp float;\nstruct State{float x0;};\nfloat helper(inout State s,float value){float result=value;return result;}\nvoid main(){float coherentSupport=1.0;}\n'''
    bad='''#version 310 es\nprecision highp float;\nvoid main(){float okay=1.0, coherent=2.0;}\n'''
    dg=declared_identifiers(good); db=declared_identifiers(bad)
    assert not [d for d in dg if d[0] in RESERVED], dg
    hits=[d for d in db if d[0] in RESERVED]
    assert any(x[0]=='coherent' for x in hits), (db,hits)
    print('PASS reserved-identifier scanner self-test: exact coherent regression rejected')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('files',nargs='*',type=Path)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test: self_test(); return
    if not a.files: raise SystemExit('no shader files')
    failed=False
    for p in a.files:
        decl,bad=scan(p)
        if bad:
            failed=True
            for name,ln,kind in bad:
                print(f'FAIL {p}: line {ln}: declared {kind} uses GLSL/GLSL ES reserved identifier {name}',file=sys.stderr)
        else:
            print(f'PASS reserved identifiers: {p.name} declarations={len(decl)}')
    if failed: raise SystemExit(2)
if __name__=='__main__': main()
