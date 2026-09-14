#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26638_r1_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 if sys.argv[4]!='--compiler': raise SystemExit('expected --compiler')
 compiler=sys.argv[5]
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Complete 257-file shader universe remains complete, with exactly two asset shaders changed.
bm=readm(root/'R1_26638_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26638_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==257 and set(bm)==set(cm)
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
asset_changed={r for r in bm if bm[r]!=cm[r]}
assert asset_changed=={'app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/render.glsl'},asset_changed
# Reconstruct every modified runtime-expanded shader variant exactly.
mods=[]
ct=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
for hs in (0,1):
 for lk in (0,1):
  mods.append((f'motionv2_color_transform_hs{hs}_look{lk}','#version 300 es\n#define USE_PROFILE_HUESAT %d\n#define USE_PROFILE_LOOK %d\n'%(hs,lk)+ct,'frag'))
mods.append(('motionv2_render_26638','#version 300 es\n'+(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(),'frag'))
k=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
def kotlin_shader(name):
 m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',k,re.S)
 if not m: raise SystemExit('missing kotlin shader '+name)
 lines=m.group(1).splitlines(); nonblank=[len(x)-len(x.lstrip()) for x in lines if x.strip()]; ind=min(nonblank) if nonblank else 0
 return '\n'.join(x[ind:] if x.strip() else '' for x in lines)+'\n'
for name in ('shortComponentAnchor26607','shortRescueWeight26607'): mods.append((name,kotlin_shader(name),'frag'))
n=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
m=re.search(r'static const char\*kIris26571PublicationCompute=R"GLSL\(\n(.*?)\n\)GLSL";',n,re.S)
if not m: raise SystemExit('missing native compute shader')
mods.append(('true2x_publication_compute_26638',m.group(1)+'\n','comp'))
assert len(mods)==8
reserved=set("""attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex""".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
expected=readm(root/'R1_26638_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==8
results=[]
with tempfile.TemporaryDirectory(prefix='iris26638_shader_') as td:
 out=Path(td)
 for name,src,stage in mods:
  clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
  ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
  bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
  if bad: raise SystemExit(f'FAIL {name}: reserved declaration identifiers {bad}')
  if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
  fn=f'{name}.{stage}'; p=out/fn; p.write_text(src)
  got=sha(p); assert expected.get(fn)==got,(fn,expected.get(fn),got)
  status='STATIC_PASS'
  if compiler:
   cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0: raise SystemExit(f'GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
   status='REAL_GLSLANG_PASS'
  results.append({'name':name,'stage':stage,'sha256':got,'status':status})
print(f'PASS 26638 complete runtime-expanded GLSL reserved scan variants={len(results)} real_compiler={bool(compiler)} shaderUniverse=257')
