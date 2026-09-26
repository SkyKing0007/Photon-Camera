#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6):raise SystemExit("usage: verify_26707_shaders.py ROOT BASE CAND [--compiler PATH]")
root,base,cand=map(Path,sys.argv[1:4]);compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler';compiler=Path(sys.argv[5]);assert compiler.is_file()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def extract(path,name):
 s=path.read_text();m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S);assert m,name
 ls=m.group(1).splitlines();inds=[len(x)-len(x.lstrip()) for x in ls if x.strip()];n=min(inds) if inds else 0
 return '\n'.join(x[n:] for x in ls)+'\n'
variants=[
 ('universal_adaptive_color_26707.comp',extract(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','universalAdaptiveColor26561'),'comp'),
 ('sabre_rejection_26707.frag',extract(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','rejection'),'frag')]
pins=load(root/'26707_RUNTIME_EXPANDED_SHADERS.sha256');assert len(pins)==2
sb=load(root/'26707_ASSET_SHADER_UNIVERSE_BASE.sha256');sc=load(root/'26707_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==271 and sb==sc
for r,h in sb.items():assert sha(base/r)==h and sha(cand/r)==h
reserved=set("attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex".split())
tp=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 cl=re.sub(r'/\*.*?\*/',' ',src,flags=re.S);cl=re.sub(r'//.*',' ',cl)
 ids=re.findall(r'\b'+tp+r'\s+([A-Za-z_]\w*)\b',cl)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',cl)
 bad=sorted(set(ids)&reserved);impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 assert not bad,(name,'reserved',bad);assert not impl,(name,'impl',impl);assert cl.count('{')==cl.count('}'),name
with tempfile.TemporaryDirectory(prefix='iris26707rev_glsl_') as td:
 d=Path(td)
 for name,src,stage in variants:
  scan(name,src);assert pins[name]==hashlib.sha256(src.encode()).hexdigest(),name
  if name.startswith('universal_'):
   for t in ['IRIS_26707_VALID_CFA_NEUTRAL_SURFACE_LEAK_REJECT','validCfaNeutralLeakProof','validCfaNeutralLeakAuthority','neutralLeakRealColorVeto'] : assert t in src,t
  else:
   for t in ['IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT','uRejectLowConfidenceTemporalTail','frameWeight < 0.0625','pixelDifference < 0.125']: assert t in src,t
  if compiler:
   p=d/name;p.write_text(src);cp=subprocess.run([str(compiler),'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0:raise SystemExit(f'26707 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26707 revised runtime-expanded GLSL variants=2 complete reserved/structure/exact-hash real_compiler={bool(compiler)} assetShaderUniverse=271')
