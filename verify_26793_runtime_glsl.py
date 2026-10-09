#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, subprocess, textwrap
ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); ap.add_argument('--compiler'); ap.add_argument('--out',required=True)
a=ap.parse_args(); BASE=Path(a.base); CAND=Path(a.candidate); OUT=Path(a.out); OUT.mkdir(parents=True,exist_ok=True)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
def need(c,m):
 if not c: raise AssertionError(m)
def shader(root,rel,name):
 text=(root/rel).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,f'{name}: declaration missing'); b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing'); return textwrap.dedent(text[m.end():b]).strip('\n')+'\n'
def runtime_asset(root,rel):
 src=(root/rel).read_text(); need('#version' not in src and '#import' not in src and '#define' not in src,f'{rel}: runtime preprocessor assumptions changed'); return '#version 310 es\n#line 1\n'+src
RESERVED=set(('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMS usampler2DMSArray samplerCubeArray samplerCubeArrayShadow isamplerCubeArray usamplerCubeArray image1D iimage1D uimage1D image2D iimage2D uimage2D image3D iimage3D uimage3D image2DRect iimage2DRect uimage2DRect imageCube iimageCube uimageCube imageBuffer iimageBuffer uimageBuffer image1DArray iimage1DArray uimage1DArray image2DArray iimage2DArray uimage2DArray imageCubeArray iimageCubeArray uimageCubeArray image2DMS iimage2DMS uimage2DMS image2DMSArray iimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major').split())
TYPE=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'; DECL_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)'); FUNC_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)\s*\('); STRUCT_RE=re.compile(r'\bstruct\s+([A-Za-z_]\w*)')
def clean(src): return re.sub(r'//.*',' ',re.sub(r'/\*.*?\*/',' ',src,flags=re.S))
def reserved_scan(name,src):
 names=set(DECL_RE.findall(clean(src)))|set(FUNC_RE.findall(clean(src)))|set(STRUCT_RE.findall(clean(src))); bad=sorted(n for n in names if n in RESERVED or n.startswith('gl_') or n.startswith('__')); need(not bad,f'{name}: reserved declared identifiers {bad}'); print(f'PASS 26793 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def uniform_completeness(name,src):
 s=clean(src); used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',s)); declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',s)); missing=sorted(used-declared); need(not missing,f'{name}: used-but-undeclared uniforms {missing}'); print(f'PASS 26793 uniform completeness {name}: used={len(used)} declared={len(declared)}')
def compile_one(name,stage,src,check_uniforms=False):
 ext='comp' if stage=='comp' else 'frag'; p=OUT/f'{name}.{ext}'; p.write_text(src); reserved_scan(name,src)
 if check_uniforms: uniform_completeness(name,src)
 if a.compiler:
  cp=subprocess.run([a.compiler,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang failed for {name}')
  print(f'PASS 26793 pinned real glslang compile exact runtime-expanded shader: {name}')
specs=[
 ('merge',S,'frag',True,True),
 ('motionv2_render','app/src/main/assets/shaders/motionv2/render.glsl','frag',False,False),
 ('motionv2_gainmap','app/src/main/assets/shaders/motionv2/gainmap.glsl','frag',False,False),
 ('jpegNeutralHighlightClamp26790',S,'frag',False,False),('normalChromaConsensus26790',S,'frag',False,False),('jpegPhaseSafeCfaLca26788',S,'frag',False,False),
 ('universalNormalMasterShortFusion26651',S,'frag',False,True),('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp',False,False),('jpegNeutralHighlightClamp26787',S,'frag',False,False),
 ('normalDngMerge',S,'frag',False,False),('normalizeBayer',SP,'frag',False,False),('universalAdaptiveColor26561',POST,'comp',False,False),('bipolarColorTrust26769',POST,'comp',False,False)]
for name,rel,stage,uc,modified in specs:
 src=runtime_asset(CAND,rel) if rel.endswith('.glsl') else shader(CAND,rel,name)
 if not modified:
  base=runtime_asset(BASE,rel) if rel.endswith('.glsl') else shader(BASE,rel,name); need(base==src,f'inherited active/protected shader changed {name}')
 compile_one(name,stage,src,uc)
merge=shader(CAND,S,'merge'); short=shader(CAND,S,'universalNormalMasterShortFusion26651')
need(merge.count('IRIS_26793_SAME_LOCATION_CFA_COLOR_DIFFERENCE_OWNER')==1,'merge owner marker'); need(short.count('IRIS_26793_SAME_LOCATION_CFA_COLOR_DIFFERENCE_OWNER')==1,'SHORT owner marker')
need('calculationCfa26793, weights, sourceValidity, type, covariance, 0,' in merge,'merge call contract'); need('calculationCfa26793, validWeights, sourceValidity, type, covariance, 1,' in short,'SHORT call contract')
print('PASS 26793 inherited active/protected shader fidelity: 11 byte-identical to successful 26792')
print('PASS 26793 modified shader ownership: main + SHORT Sabre same-location CFA color difference; no other shader owner changed')
