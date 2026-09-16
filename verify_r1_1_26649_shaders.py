#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_r1_1_26649_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
    if sys.argv[4] != '--compiler': raise SystemExit('expected --compiler')
    compiler=sys.argv[5]
def readm(p):
    d={}
    for l in p.read_text().splitlines():
        if l.strip(): h,r=l.split('  ',1); d[r]=h
    return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Authority completeness stays exactly the failed R1/intended 26649 candidate.
bm=readm(root/'R1_26649_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26649_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==257 and set(bm)==set(cm)
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
# Reproduce GLInterface.readProgram() for these exact asset shaders. MotionV2Render has no setDefine calls,
# so runtime defines are empty; the three assets also contain no #import/#version/#define directives.
glprog=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
m=re.search(r'public\s+final\s+static\s+String\s+glVersion\s*=\s*"([^"]*)";',glprog)
if not m: raise SystemExit('FAIL cannot derive runtime GLProg.glVersion')
glversion=bytes(m.group(1),'utf-8').decode('unicode_escape')
if glversion != '#version 310 es\n': raise SystemExit(f'FAIL unexpected runtime glVersion {glversion!r}')
renderjava=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
if 'glProg.setDefine' in renderjava: raise SystemExit('FAIL MotionV2Render now has runtime defines; exact expansion verifier must be updated')
assets=[
 ('local_laplacian_global_log_26621.frag','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl'),
 ('local_laplacian_remap_26621.frag','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'),
 ('render.frag','app/src/main/assets/shaders/motionv2/render.glsl')]
for _,rel in assets:
    token='useAssetProgram("'+rel[len('app/src/main/assets/shaders/'): -len('.glsl')]+'")'
    if token not in renderjava: raise SystemExit(f'FAIL active-path owner missing {token}')
def runtime_expand(raw, asset_root):
    source=[]; linecnt=0; versioned=False
    # Java BufferedReader.lines strips line terminators; splitlines() mirrors that here.
    for val in raw.splitlines():
        linecnt += 1
        if '#version' in val: versioned=True
        if '#import' in val:
            imported=''
            if '//' not in val:
                imp='shaders/utils/'+val.replace('#','').replace(' ','_').replace('\\n','')+'.glsl'
                p=asset_root/imp
                if not p.is_file(): raise SystemExit(f'FAIL runtime import missing {imp}')
                imported=p.read_text()
            if imported:
                source.append('#line 1\n'); source.append(imported); source.append('\n'); source.append(f'#line {linecnt+1}\n')
            continue
        source.append(val+'\n')
    add='' if versioned else glversion+'\n'+'#line 1\n'
    return add+''.join(source)
expected=readm(root/'R1_1_26649_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==3
reserved=set("""attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex""".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
    bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
    if bad: raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
    if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
    if clean.count('{') != clean.count('}'): raise SystemExit(f'FAIL {name}: brace mismatch')
    if not src.startswith('#version 310 es\n\n#line 1\n'): raise SystemExit(f'FAIL {name}: not exact GLInterface runtime preamble')
    if name=='local_laplacian_global_log_26621.frag':
        for t in ['uniform float iris26649PhotonHighlightKnee;','mapped=iris26649PhotonSoftShoulder(mapped);','return knee+span*g*g;']:
            if t not in src: raise SystemExit(f'FAIL {name}: missing {t}')
    if name=='render.frag':
        for t in ['uniform float iris26649PhotonHighlightKnee;','return iris26649PhotonSoftShoulder(iris26623MapMotionSdrFinalGuide(sourceGuide));','float globalMapped=iris26649PhotonSoftShoulder(','return knee+span*g*g;']:
            if t not in src: raise SystemExit(f'FAIL {name}: missing {t}')
    if name=='local_laplacian_remap_26621.frag':
        for t in ['IRIS_26649_PHOTON_HIGHLIGHT_COMPRESSION_HANDOFF','float baseOut=baseLinear;','float residualWeight=1.0;']:
            if t not in src: raise SystemExit(f'FAIL {name}: missing {t}')
        for t in ['float smoothShoulder=1.0-pow(max(1.0-baseLinear,0.0),1.12);','float smallResidualWeight=mix(1.0,0.78,upperGate);']:
            if t in src: raise SystemExit(f'FAIL {name}: stale post-compression highlight lift/suppression {t}')
with tempfile.TemporaryDirectory(prefix='iris26649_r1_1_shader_') as td:
    td=Path(td); assetroot=cand/'app/src/main/assets'
    for name,rel in assets:
        raw=(cand/rel).read_text()
        # Permanent failure regression: raw asset itself must not be the compiler input.
        if raw.startswith('#version'): raise SystemExit(f'FAIL {name}: unexpected source contract change; review expansion authority')
        expanded=runtime_expand(raw,assetroot)
        scan(name,expanded)
        got=hashlib.sha256(expanded.encode()).hexdigest(); assert expected.get(name)==got,(name,expected.get(name),got)
        if compiler:
            p=td/name; p.write_text(expanded)
            cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
            if cp.returncode!=0: raise SystemExit(f'26649 R1.1 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26649 R1.1 exact GLInterface-runtime-expanded GLSL variants=3 reserved/structure/exact-hash real_compiler={bool(compiler)} shaderUniverse=257')
