#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6):raise SystemExit('usage: verify_26706_shaders.py ROOT BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]);compiler=None
if len(sys.argv)==6:
 if sys.argv[4]!='--compiler':raise SystemExit('expected --compiler')
 compiler=Path(sys.argv[5]);assert compiler.is_file()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split(None,1);d[r.strip()]=h
 return d
def extract_kotlin(name):
 s=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S)
 if not m:raise SystemExit('missing embedded Kotlin shader '+name)
 lines=m.group(1).splitlines();ind=[len(x)-len(x.lstrip()) for x in lines if x.strip()];n=min(ind) if ind else 0
 return '\n'.join(x[n:] for x in lines)+'\n'
variants=[
 ('motionv2_render_26706.frag','#version 300 es\n'+(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(),'frag'),
 ('motionv2_gainmap_26706.frag','#version 300 es\n'+(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text(),'frag'),
 ('sabre_fusion_telemetry_26706.frag',extract_kotlin('universalFusionTelemetry26651'),'frag')]
pins=readm(root/'26706_RUNTIME_EXPANDED_SHADERS.sha256');assert len(pins)==3
sb=readm(root/'26706_ASSET_SHADER_UNIVERSE_BASE.sha256');sc=readm(root/'26706_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256');assert len(sb)==len(sc)==271
assert {r for r in sb if sb[r]!=sc[r]}=={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'}
for r,h in sb.items():assert sha(base/r)==h,r
for r,h in sc.items():assert sha(cand/r)==h,r
reserved=set("""attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler2DRect sampler1DArray sampler2DArray samplerBuffer sampler2DMS sampler2DMSArray samplerCubeArray sampler1DShadow sampler2DShadow sampler2DRectShadow sampler1DArrayShadow sampler2DArrayShadow samplerCubeShadow samplerCubeArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler2DRect isampler1DArray isampler2DArray isamplerBuffer isampler2DMS isampler2DMSArray isamplerCubeArray usampler1D usampler2D usampler3D usamplerCube usampler2DRect usampler1DArray usampler2DArray usamplerBuffer usampler2DMS usampler2DMSArray usamplerCubeArray image1D image2D image3D image2DRect imageCube imageBuffer image1DArray image2DArray imageCubeArray image2DMS image2DMSArray iimage1D iimage2D iimage3D iimage2DRect iimageCube iimageBuffer iimage1DArray iimage2DArray iimageCubeArray iimage2DMS iimage2DMSArray uimage1D uimage2D uimage3D uimage2DRect uimageCube uimageBuffer uimage1DArray uimage2DArray uimageCubeArray uimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex""".split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(name,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S);clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved);impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_')))
 if bad:raise SystemExit(f'FAIL {name}: reserved identifiers {bad}')
 if impl:raise SystemExit(f'FAIL {name}: implementation-reserved identifiers {impl}')
 if clean.count('{')!=clean.count('}'):raise SystemExit(f'FAIL {name}: brace mismatch')
 if name.startswith('motionv2_'):
  for t in ['IRIS_26706_VISUAL_HIGHLIGHT_SPACING','mix(0.945,0.895,pressure)','mix(0.360,0.620,pressure)']:
   if t not in src:raise SystemExit(f'FAIL {name}: missing {t}')
 if name.startswith('sabre_'):
  for t in ['IRIS_26706_SAMPLED_FUSION_DECISION_TELEMETRY','float(packed) / 255.0']:
   if t not in src:raise SystemExit(f'FAIL {name}: missing {t}')
with tempfile.TemporaryDirectory(prefix='iris26706_glsl_') as td:
 d=Path(td)
 for name,src,stage in variants:
  scan(name,src);got=hashlib.sha256(src.encode()).hexdigest();assert pins.get(name)==got,(name,pins.get(name),got)
  if compiler:
   p=d/name;p.write_text(src);cp=subprocess.run([str(compiler),'-S',stage,str(p)],capture_output=True,text=True)
   if cp.returncode!=0:raise SystemExit(f'26706 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26706 runtime-expanded GLSL variants=3 complete reserved/structure/exact-hash real_compiler={bool(compiler)} assetShaderUniverse=271')
