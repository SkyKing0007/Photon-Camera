#!/usr/bin/env python3
from pathlib import Path
import argparse, re, subprocess, sys, textwrap, hashlib, json

GL_VERSION='#version 310 es\n'
# Union of GLSL ES 3.x / GLSL 4.x current keywords and specification-reserved future words.
RESERVED=set('''
attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint
layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else
subroutine in out inout float double int void bool true false invariant precise discard return
mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4
dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4
vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uvec2 uvec3 uvec4
sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow
sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow samplerCubeArray samplerCubeArrayShadow
isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray isamplerCubeArray
usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray usamplerCubeArray
sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer
sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray
image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray
iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray
uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray
struct
common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface
long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using
row_major
'''.split())
# Extra historical/reserved tokens across ES/desktop profiles that must never be user identifiers.
RESERVED.update('then packed lowp mediump highp precision'.split())
TYPES=set(x for x in RESERVED if re.match(r'^(?:[diub]?vec[234]|[d]?mat|[iu]?sampler|[iu]?image|float|double|int|uint|bool|void|atomic_uint)',x))
TYPES.update(['uint'])
QUAL=set('const in out inout uniform attribute varying centroid flat smooth noperspective patch sample invariant precise highp mediump lowp readonly writeonly coherent volatile restrict'.split())

STANDALONE={
 'initial_p3_universal': ('app/src/main/assets/shaders/initial.glsl', {
     'CCT':'0','USE_HSV':'0','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'1',
     'IRIS_26361_MOTION_SINGLE_FUSION_TONE':'0','FUSION':'0'}),
 'initial_p3_calibrated': ('app/src/main/assets/shaders/initial.glsl', {
     'CCT':'0','USE_HSV':'1','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'0',
     'IRIS_26361_MOTION_SINGLE_FUSION_TONE':'0','FUSION':'0'}),
 'initial_p3_universal_fusion': ('app/src/main/assets/shaders/initial.glsl', {
     'CCT':'0','USE_HSV':'0','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'1',
     'IRIS_26361_MOTION_SINGLE_FUSION_TONE':'1','FUSION':'1'}),
 'adaptive_universal': ('app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl', {'CALIBRATED_PROFILE':'0'}),
 'adaptive_calibrated': ('app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl', {'CALIBRATED_PROFILE':'1'}),
 'color_transform_universal': ('app/src/main/assets/shaders/motionv2/color_transform.glsl', {'USE_PROFILE_HUESAT':'0'}),
 'color_transform_calibrated': ('app/src/main/assets/shaders/motionv2/color_transform.glsl', {'USE_PROFILE_HUESAT':'1'}),
 'gainmap_p3': ('app/src/main/assets/shaders/motionv2/gainmap.glsl', {}),
 'iris_tone_controls_p3': ('app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl', {}),
 'render_p3': ('app/src/main/assets/shaders/motionv2/render.glsl', {}),
}

def fail(msg): raise SystemExit('FAIL: '+msg)

def runtime_expand(root, rel, defines):
    p=root/rel
    lines=p.read_text().splitlines()
    out=[]; versioned=False
    for linecnt,val in enumerate(lines,1):
        if '#version' in val: versioned=True
        if '#import' in val:
            imported=''
            if '//' not in val:
                util_name=val.replace('#','').replace(' ','_').replace('\n','')+'.glsl'
                util=root/'app/src/main/assets/shaders/utils'/util_name
                if not util.is_file(): fail(f'missing runtime import {util_name} for {rel}')
                imported=util.read_text()
            if imported:
                out.append('#line 1')
                out.append(imported.rstrip('\n'))
                out.append(f'#line {linecnt+1}')
            continue
        replaced=val
        if '#define' in val:
            for name,value in defines.items():
                if f' {name} ' in val:
                    replaced=f'#define {name} {value}'
                    break
        out.append(replaced)
    body='\n'.join(out)+'\n'
    if not versioned: body=GL_VERSION+'\n#line 1\n'+body
    return body

def extract_kotlin_true2x(root):
    s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    start='val true2xMerge26564 = """'; end='""".trimIndent()'
    a=s.find(start)
    if a<0: fail('embedded true2xMerge26564 start missing')
    a+=len(start); z=s.find(end,a)
    if z<0: fail('embedded true2xMerge26564 end missing')
    raw=s[a:z]
    # Kotlin trimIndent: remove first/last blank line and common minimum indent.
    return textwrap.dedent(raw).strip('\n')+'\n'

def strip_comments(src):
    src=re.sub(r'/\*.*?\*/',' ',src,flags=re.S)
    src=re.sub(r'//[^\n]*',' ',src)
    return src

def declared_identifiers(src):
    clean=strip_comments(src)
    # remove preprocessor lines: macro names are not program identifiers and #define keywords are expected.
    code='\n'.join('' if line.lstrip().startswith('#') else line for line in clean.splitlines())
    found=[]
    type_alt='|'.join(sorted(map(re.escape,TYPES), key=len, reverse=True))
    qual_alt='|'.join(sorted(map(re.escape,QUAL), key=len, reverse=True))
    # Every identifier immediately following a built-in type: variables, functions, struct fields and parameters.
    pat=re.compile(r'\b(?:'+qual_alt+r'\s+)*(?:'+type_alt+r')\s+([A-Za-z_]\w*)')
    for m in pat.finditer(code): found.append((m.group(1),m.start(1)))
    # Multiple declarators of same built-in type in simple declarations (float x=..., y=...;).
    stmt_pat=re.compile(r'\b(?:'+qual_alt+r'\s+)*(?:'+type_alt+r')\s+([^;{}]+);')
    for sm in stmt_pat.finditer(code):
        tail=sm.group(1)
        depth=0; chunks=[]; last=0
        for i,ch in enumerate(tail):
            if ch in '([{': depth+=1
            elif ch in ')]}': depth=max(0,depth-1)
            elif ch==',' and depth==0:
                chunks.append((last,i)); last=i+1
        chunks.append((last,len(tail)))
        for lo,hi in chunks:
            part=tail[lo:hi].strip()
            mm=re.match(r'([A-Za-z_]\w*)',part)
            if mm:
                pos=sm.start(1)+lo+part.find(mm.group(1)); found.append((mm.group(1),pos))
    # Deduplicate positions/names.
    return sorted(set(found), key=lambda x:x[1])

def line_col(src,pos):
    line=src.count('\n',0,pos)+1
    last=src.rfind('\n',0,pos)
    return line,pos-(last+1)+1

def reserved_scan(label,src):
    bad=[]
    for name,pos in declared_identifiers(src):
        if name in RESERVED or name.startswith('gl_') or '__' in name:
            bad.append((name,*line_col(src,pos)))
    if bad:
        fail(label+' reserved declared identifiers: '+', '.join(f'{n}@{l}:{c}' for n,l,c in bad))
    return len(declared_identifiers(src))

def compile_shader(glslang,label,path):
    cp=subprocess.run([glslang,'-S','frag',str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if cp.returncode:
        print(cp.stdout)
        fail(f'glslang compile failed: {label}')
    return cp.stdout.strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('candidate_root')
    ap.add_argument('--out',required=True)
    ap.add_argument('--glslang')
    ns=ap.parse_args()
    root=Path(ns.candidate_root).resolve(); out=Path(ns.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    manifest=[]; results=[]
    for label,(rel,defs) in STANDALONE.items():
        src=runtime_expand(root,rel,defs)
        p=out/(label+'.frag')
        p.write_text(src)
        n=reserved_scan(label,src)
        sha=hashlib.sha256(p.read_bytes()).hexdigest(); manifest.append((sha,p.name))
        results.append({'label':label,'declared_identifiers':n,'sha256':sha,'compiler':'NOT RUN'})
    label='true2x_merge_26564_runtime'
    src=extract_kotlin_true2x(root)
    p=out/(label+'.frag'); p.write_text(src)
    n=reserved_scan(label,src); sha=hashlib.sha256(p.read_bytes()).hexdigest(); manifest.append((sha,p.name))
    results.append({'label':label,'declared_identifiers':n,'sha256':sha,'compiler':'NOT RUN'})
    # Required source-level regression: clip threshold only exists inside true2x shader.
    kt=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    if kt[:kt.find('val true2xMerge26564')].count('uRawClipThreshold')!=0: fail('clip uniform leaked before true2x shader')
    if src.count('uRawClipThreshold')!=2: fail('true2x expanded clip-threshold declaration/use count')
    (out/'runtime_expanded_shaders.sha256').write_text(''.join(f'{h}  {n}\n' for h,n in manifest))
    if ns.glslang:
        tool=Path(ns.glslang)
        if not tool.is_file(): fail('glslang path missing: '+str(tool))
        for r in results:
            log=compile_shader(str(tool),r['label'],out/(r['label']+'.frag'))
            r['compiler']='PASS'; (out/(r['label']+'.glslang.log')).write_text(log+'\n')
    (out/'shader_verification.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS runtime expansion + complete reserved-identifier scan variants={len(results)}')
    print('REAL GLSL COMPILE: '+('PASS' if ns.glslang else 'NOT RUN'))

if __name__=='__main__': main()
