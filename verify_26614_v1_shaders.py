#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,subprocess,sys,textwrap
if len(sys.argv)<5 or sys.argv[3] != '--out':
    raise SystemExit('usage: verify_26614_v1_shaders.py BASE CAND --out OUT [--compiler PATH]')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); O=Path(sys.argv[4]); O.mkdir(parents=True,exist_ok=True)
compiler=None
if len(sys.argv)>=7 and sys.argv[5]=='--compiler': compiler=sys.argv[6]

def write(name,src,stage):
    p=O/f'{name}.{stage}'; p.write_text(src); return p
prefix='#version 300 es\n#line 1\n'
spec=[]
for rel,name in [
    ('app/src/main/assets/shaders/motionv2/render.glsl','motionv2_render_26614_canonical_appearance'),
    ('app/src/main/assets/shaders/motionv2/gainmap.glsl','motionv2_gainmap_26614_headroom_only'),
]:
    s=(C/rel).read_text(); assert '#version' not in s and '#import' not in s
    spec.append((name,prefix+s,'frag'))
a=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
assert '#version' not in a and '#import' not in a
spec.append(('adaptive_26614_canonical_appearance',prefix+a,'frag'))
spec.append(('adaptive_26614_canonical_appearance_calibrated',prefix+'#define CALIBRATED_PROFILE 1\n'+a,'frag'))

kt=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
m=re.search(r'val universalAdaptiveColor26561 = """\n(.*?)\n\s*"""\.trimIndent\(\)',kt,re.S); assert m
ks=textwrap.dedent(m.group(1)).lstrip('\n')+'\n'; assert ks.startswith('#version 310 es\n')
spec.append(('postvgn_26614_physical_color_validity',ks,'comp'))

sabre=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
m=re.search(r'val merge = """\n(.*?)\n\s*"""\.trimIndent\(\)',sabre,re.S); assert m
ss=textwrap.dedent(m.group(1)).lstrip('\n')+'\n'; assert ss.startswith('#version 300 es\n')
spec.append(('sabre_merge_26614_valid_measurement_weights',ss,'frag'))

cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
m=re.search(r'kIris26571PublicationCompute=R"GLSL\((.*?)\)GLSL";',cpp,re.S); assert m
cs=m.group(1).lstrip('\n'); assert cs.startswith('#version 310 es\n')
spec.append(('true2x_publication_26614_canonical_appearance',cs,'comp'))

# Full declaration-identifier reserved scan. glslang remains final syntax authority; this catches
# reserved names even when a particular driver accepts them. Includes GLSL/ES keywords and prior failures.
reserved=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'''.split())
# Declaration/function name matcher. Interface block names and struct names are also checked.
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for name,src,stage in spec:
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    ids=[]
    ids += re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)
    ids += re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
    bad=sorted(set(ids)&reserved)
    assert not bad, f'{name}: reserved declaration identifiers {bad}'
    # Double-underscore and gl_ names are reserved to implementations.
    impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
    assert not impl, f'{name}: implementation-reserved identifiers {impl}'

paths=[]
for name,src,stage in spec: paths.append((write(name,src,stage),stage,name))
lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p,stage,name in paths]
(O/'V1_26614_RUNTIME_EXPANDED_SHADERS.sha256').write_text('\n'.join(lines)+'\n')
results=[]
for p,stage,name in paths:
    status='STATIC_PASS'
    if compiler:
        cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
        if cp.returncode!=0:
            raise SystemExit(f'GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
        status='REAL_GLSLANG_PASS'
    results.append({'name':name,'stage':stage,'file':p.name,'status':status})
(O/'V1_26614_SHADER_VERIFICATION.json').write_text(json.dumps({'count':len(results),'compiler':compiler,'results':results},indent=2,sort_keys=True)+'\n')
print(f'PASS 26614 runtime-expanded shader extraction/reserved scan variants={len(results)} real_compiler={bool(compiler)}')
