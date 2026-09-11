#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,subprocess,sys
args=sys.argv[1:]
if len(args)<4 or args[2]!='--out': raise SystemExit('usage: verify_26625_r1_shaders.py BASE CAND --out DIR [--compiler PATH]')
B=Path(args[0]); C=Path(args[1]); O=Path(args[3]); O.mkdir(parents=True,exist_ok=True)
compiler=None
if '--compiler' in args: compiler=args[args.index('--compiler')+1]
p=C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; text=p.read_text()
def get(name):
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*'+chr(34)*3+r'(.*?)'+chr(34)*3+r'\.trimIndent\(\)',text,re.S)
    assert m,name
    src=m.group(1)
    # Kotlin trimIndent: all these literals have 8 spaces of source indentation.
    lines=src.splitlines()
    non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]
    indent=min(non) if non else 0
    return '\n'.join(x[indent:] if len(x)>=indent else '' for x in lines).strip('\n')+'\n'
mods=[('short_component_anchor_26625',get('shortComponentAnchor26607'),'frag'),('short_component_effective_flow_26625',get('shortComponentEffectiveFlow26625'),'frag')]
reserved=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray samplerCubeArray samplerCubeArrayShadow isamplerCubeArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'''.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
paths=[]; results=[]
for name,src,stage in mods:
    assert src.startswith('#version 300 es\n'),name
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    ids=[]; ids+=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean); ids+=re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
    bad=sorted(set(ids)&reserved); assert not bad,f'{name}: reserved declaration identifiers {bad}'
    impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_'))); assert not impl,f'{name}: implementation-reserved identifiers {impl}'
    q=O/f'{name}.{stage}'; q.write_text(src); paths.append((q,stage,name)); status='STATIC_PASS'
    if compiler:
        cp=subprocess.run([compiler,'-S',stage,str(q)],capture_output=True,text=True)
        if cp.returncode!=0: raise SystemExit(f'GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
        status='REAL_GLSLANG_PASS'
    results.append({'name':name,'stage':stage,'file':q.name,'status':status})
lines=[f'{hashlib.sha256(q.read_bytes()).hexdigest()}  {q.name}' for q,stage,name in paths]
(O/'R1_26625_RUNTIME_EXPANDED_SHADERS.sha256').write_text('\n'.join(lines)+'\n')
(O/'R1_26625_SHADER_VERIFICATION.json').write_text(json.dumps({'count':len(results),'compiler':compiler,'results':results},indent=2,sort_keys=True)+'\n')
print(f'PASS 26625 exact runtime-expanded embedded GLSL extraction/reserved scan variants={len(results)} real_compiler={bool(compiler)}')
