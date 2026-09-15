#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26641_r1_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
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
def runtime_gain(rootp): return '#version 310 es\n\n#line 1\n'+(rootp/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
def variants(rootp): return [('motionv2_gainmap_26641.frag',runtime_gain(rootp),'frag')]
# Complete shader universe: only the intended Motion gain asset may change.
bm=readm(root/'R1_26641_SHADER_UNIVERSE_BASE.sha256'); cm=readm(root/'R1_26641_SHADER_UNIVERSE_CANDIDATE.sha256')
assert len(bm)==len(cm)==257 and set(bm)==set(cm)
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
assert {r for r in bm if bm[r]!=cm[r]}=={'app/src/main/assets/shaders/motionv2/gainmap.glsl'}
expected=readm(root/'R1_26641_RUNTIME_EXPANDED_SHADERS.sha256'); assert len(expected)==1
reserved=set("""attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex""".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad: raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
 if impl: raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
 if clean.count('{')!=clean.count('}'): raise SystemExit(f'FAIL {name}: brace mismatch')
 for token in ['IRIS_26641_LINEAR_LIGHT_SDR_PREDIVIDE_DOWNSAMPLE','IRIS_26641_TRUE_MATCHED_INTENT_DELTA']:
  if src.count(token)!=1: raise SystemExit(f'FAIL {name}: {token} count={src.count(token)}')
 if 'compressionFraction' in src: raise SystemExit(f'FAIL {name}: stale squared-compression owner survived')
mods=variants(cand)
with tempfile.TemporaryDirectory(prefix='iris26641_shader_') as td:
 out=Path(td)
 for name,src,stage in mods:
  scan(name,src); got=hashlib.sha256(src.encode()).hexdigest(); assert expected.get(name)==got,(name,expected.get(name),got)
  if compiler:
   p=out/name; p.write_text(src); cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0: raise SystemExit(f'26641 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26641 runtime-expanded GLSL variants=1 reserved/structure/exact-hash real_compiler={bool(compiler)} shaderUniverse=257')
