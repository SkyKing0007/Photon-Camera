#!/usr/bin/env python3
from pathlib import Path
import argparse, re, subprocess, textwrap, hashlib, json

GL_VERSION='#version 310 es\n'
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
struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface
long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using
row_major then packed lowp mediump highp precision
'''.split())
TYPES=set(x for x in RESERVED if re.match(r'^(?:[diub]?vec[234]|[d]?mat|[iu]?sampler|[iu]?image|float|double|int|uint|bool|void|atomic_uint)',x)); TYPES.add('uint')
QUAL=set('const in out inout uniform attribute varying centroid flat smooth noperspective patch sample invariant precise highp mediump lowp readonly writeonly coherent volatile restrict'.split())
STANDALONE={
 'initial_p3_universal': ('app/src/main/assets/shaders/initial.glsl', {'CCT':'0','USE_HSV':'0','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'1','IRIS_26361_MOTION_SINGLE_FUSION_TONE':'0','FUSION':'0'}),
 'initial_p3_calibrated': ('app/src/main/assets/shaders/initial.glsl', {'CCT':'0','USE_HSV':'1','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'0','IRIS_26361_MOTION_SINGLE_FUSION_TONE':'0','FUSION':'0'}),
 'initial_p3_universal_fusion': ('app/src/main/assets/shaders/initial.glsl', {'CCT':'0','USE_HSV':'0','IRIS_26567_P3_WORKING':'1','IRIS_26567_UNIVERSAL_COLOR':'1','IRIS_26361_MOTION_SINGLE_FUSION_TONE':'1','FUSION':'1'}),
 'adaptive_universal': ('app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl', {'CALIBRATED_PROFILE':'0'}),
 'adaptive_calibrated': ('app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl', {'CALIBRATED_PROFILE':'1'}),
 'color_transform_universal': ('app/src/main/assets/shaders/motionv2/color_transform.glsl', {'USE_PROFILE_HUESAT':'0'}),
 'color_transform_calibrated': ('app/src/main/assets/shaders/motionv2/color_transform.glsl', {'USE_PROFILE_HUESAT':'1'}),
 'gainmap_p3': ('app/src/main/assets/shaders/motionv2/gainmap.glsl', {}),
 'iris_tone_controls_p3': ('app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl', {}),
 'render_p3': ('app/src/main/assets/shaders/motionv2/render.glsl', {}),
}
PRIOR_26567={
'initial_p3_universal.frag':'a9569793b32223ea52d8b32163af78f3226d5f22770c8df62b6639f446c917ef',
'initial_p3_calibrated.frag':'af33013abc7554e5158e3b81c590eddbd2ef9a80802cb32eaad26ee113e66bd0',
'initial_p3_universal_fusion.frag':'7cbc159af64817bc7930bdad7e7fa544ee9542bb9bc5b8075f45f585e786e9e6',
'adaptive_universal.frag':'3bd5c6a0eec2f5cd3a5e85a89bb7b2ce0b1b7594b166243bc94f9dd17a3c6d67',
'adaptive_calibrated.frag':'4be4bcb6ebde1800d465dd1e3481201c11338591eb666d45f9e64dfea1956f8b',
'color_transform_universal.frag':'9e93f477dcd93705ba0d622137705fb907564039de41cda8b75c4fee9169f5e7',
'color_transform_calibrated.frag':'ae43e1364822a287646fbbccf1f34d527c2fbe88635a5330065a43fa2cf3e191',
'gainmap_p3.frag':'33ae162aa329deed560f1e60ccd6d4337f7328e3079fbda9f22a9a65e8394843',
'iris_tone_controls_p3.frag':'6d4a782923b5ef43c1b3b4a8333790fff34e020950d0b2c15f6f0003daefd6ff',
'render_p3.frag':'af686e2884e39f459b8ae7bd9509b3a6948379fd5b0b50d2cf898b646dca5de9',
'true2x_merge_26564_runtime.frag':'7a270f7cf061579b1b1873f96f071297c5da6f643f953d242499ae8eb630adfd',
}

def fail(m): raise SystemExit('FAIL: '+m)
def runtime_expand(root,rel,defines):
    lines=(root/rel).read_text().splitlines(); out=[]; versioned=False
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
                out += ['#line 1',imported.rstrip('\n'),f'#line {linecnt+1}']
            continue
        replaced=val
        if '#define' in val:
            for name,value in defines.items():
                if f' {name} ' in val: replaced=f'#define {name} {value}'; break
        out.append(replaced)
    body='\n'.join(out)+'\n'
    if not versioned: body=GL_VERSION+'\n#line 1\n'+body
    return body

def extract_kotlin(root,name):
    s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    start=f'val {name} = """'; a=s.find(start)
    if a<0: fail('embedded shader start missing '+name)
    a+=len(start); z=s.find('""".trimIndent()',a)
    if z<0: fail('embedded shader end missing '+name)
    return textwrap.dedent(s[a:z]).strip('\n')+'\n'
def strip_comments(s):
    s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S); return re.sub(r'//[^\n]*',' ',s)
def declared(src):
    code='\n'.join('' if l.lstrip().startswith('#') else l for l in strip_comments(src).splitlines())
    found=[]; ta='|'.join(sorted(map(re.escape,TYPES),key=len,reverse=True)); qa='|'.join(sorted(map(re.escape,QUAL),key=len,reverse=True))
    pat=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([A-Za-z_]\w*)')
    for m in pat.finditer(code): found.append((m.group(1),m.start(1)))
    stmt=re.compile(r'\b(?:'+qa+r'\s+)*(?:'+ta+r')\s+([^;{}]+);')
    for sm in stmt.finditer(code):
        tail=sm.group(1); depth=0; last=0; chunks=[]
        for i,ch in enumerate(tail):
            if ch in '([{': depth+=1
            elif ch in ')]}': depth=max(0,depth-1)
            elif ch==',' and depth==0: chunks.append((last,i)); last=i+1
        chunks.append((last,len(tail)))
        for lo,hi in chunks:
            part=tail[lo:hi].strip(); mm=re.match(r'([A-Za-z_]\w*)',part)
            if mm: found.append((mm.group(1),sm.start(1)+lo+part.find(mm.group(1))))
    return sorted(set(found),key=lambda x:x[1])
def scan(label,src):
    bad=[]
    for n,pos in declared(src):
        if n in RESERVED or n.startswith('gl_') or '__' in n:
            line=src.count('\n',0,pos)+1; bad.append((n,line))
    if bad: fail(label+' reserved declared identifiers '+repr(bad))
    return len(declared(src))
def compile_shader(tool,label,p):
    r=subprocess.run([tool,'-S','frag',str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if r.returncode: print(r.stdout); fail('glslang compile failed '+label)
    return r.stdout

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('candidate_root'); ap.add_argument('--out',required=True); ap.add_argument('--glslang')
    ns=ap.parse_args(); root=Path(ns.candidate_root).resolve(); out=Path(ns.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    sources=[]
    for label,(rel,defs) in STANDALONE.items(): sources.append((label,runtime_expand(root,rel,defs)))
    sources.append(('true2x_merge_26564_runtime',extract_kotlin(root,'true2xMerge26564')))
    sources.append(('true2x_guide_render_26568_runtime',extract_kotlin(root,'true2xGuideRender26568')))
    manifest=[]; results=[]
    for label,src in sources:
        p=out/(label+'.frag'); p.write_text(src); n=scan(label,src); h=hashlib.sha256(p.read_bytes()).hexdigest(); manifest.append((h,p.name))
        if p.name in PRIOR_26567 and PRIOR_26567[p.name]!=h: fail(f'carried 26567 expanded shader drift {p.name}: {h}')
        status='NOT RUN'
        if ns.glslang: compile_shader(ns.glslang,label,p); status='PASS'
        results.append({'label':label,'declared_identifiers':n,'sha256':h,'compiler':status})
    (out/'runtime_expanded_shaders.sha256').write_text(''.join(f'{h}  {n}\n' for h,n in manifest))
    (out/'shader_verification.json').write_text(json.dumps(results,indent=2)+'\n')
    # Explicit new-shader contracts.
    g=dict(sources)['true2x_guide_render_26568_runtime']
    if 'oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount));' not in g: fail('guide render scalar output contract missing')
    if 'directRgb * factor' in g: fail('direct RGB publication ownership leaked into guide render')
    print(f'PASS runtime expansion + complete reserved-identifier scan variants={len(results)}; carried 26567 hashes exact')
    print('REAL GLSL COMPILE: '+('PASS' if ns.glslang else 'NOT RUN'))
if __name__=='__main__': main()
