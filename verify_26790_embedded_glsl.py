#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, subprocess, textwrap
ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); ap.add_argument('--compiler'); ap.add_argument('--out',required=True)
a=ap.parse_args(); BASE=Path(a.base); CAND=Path(a.candidate); OUT=Path(a.out); OUT.mkdir(parents=True,exist_ok=True)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
def need(c,m):
 if not c: raise AssertionError(m)
def shader(root,rel,name):
 text=(root/rel).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,f'{name}: declaration missing')
 b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing'); return textwrap.dedent(text[m.end():b]).strip('\n')+'\n'
specs=[
 ('merge',S,'frag',True),('jpegNeutralHighlightClamp26790',S,'frag',True),('normalChromaConsensus26790',S,'frag',True),
 ('jpegPhaseSafeCfaLca26788',S,'frag',False),('universalNormalMasterShortFusion26651',S,'frag',False),
 ('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp',False),('jpegNeutralHighlightClamp26787',S,'frag',False),
 ('normalDngMerge',S,'frag',False),('normalizeBayer',SP,'frag',False),('universalAdaptiveColor26561',POST,'comp',False),('bipolarColorTrust26769',POST,'comp',False)]
RESERVED=set('''attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMSArray usampler2DMSArray samplerCubeArray samplerCubeArrayShadow isamplerCubeArray usamplerCubeArray image1D iimage1D uimage1D image2D iimage2D uimage2D image3D iimage3D uimage3D image2DRect iimage2DRect uimage2DRect imageCube iimageCube uimageCube imageBuffer iimageBuffer uimageBuffer image1DArray iimage1DArray uimage1DArray image2DArray iimage2DArray uimage2DArray imageCubeArray iimageCubeArray uimageCubeArray image2DMS iimage2DMS uimage2DMS image2DMSArray iimage2DMSArray uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'''.split())
TYPE=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'
DECL_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)'); FUNC_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)\s*\('); STRUCT_RE=re.compile(r'\bstruct\s+([A-Za-z_]\w*)')
def reserved_scan(name,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 names=set(DECL_RE.findall(clean))|set(FUNC_RE.findall(clean))|set(STRUCT_RE.findall(clean)); bad=sorted(n for n in names if n in RESERVED or n.startswith('gl_') or n.startswith('__')); need(not bad,f'{name}: reserved declared identifiers: {bad}')
 print(f'PASS 26790 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
for name,rel,stage,modified in specs:
 c=shader(CAND,rel,name)
 if not modified: need(shader(BASE,rel,name)==c,f'protected shader changed: {name}')
 reserved_scan(name,c); ext='comp' if stage=='comp' else 'frag'; p=OUT/f'{name}.{ext}'; p.write_text(c)
 if a.compiler:
  cp=subprocess.run([a.compiler,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang failed for {name}')
  print(f'PASS 26790 pinned real glslang compile runtime-expanded shader: {name}')
expected={
'jpegPhaseSafeCfaLca26788':'09415ab12c7776b0f3ea5853e047bdd2e992e8ac775e86a63e1b7d8b329c4a95',
'universalNormalMasterShortFusion26651':'90bb8a28e2c40112950eb3fa83ef6f08d703c556a91a518239ffb33bdcaa9ee5',
'EDGE_FALSE_COLOR_SUPPRESSOR_26778':'5a05397302857bc4d0f66e795b22ed010474542d52c5400e3e27c4ad1b6982a1',
'jpegNeutralHighlightClamp26787':'81d0bc4225807958813e796dc1c9e784b4c222f62fed6ee0f252c010d684ce5c',
'normalDngMerge':'ae92cfd3af69e2621e4be12af375383e650f4a362f4da2d54aaff886550a2d34',
'normalizeBayer':'d19aca4ceaf2f8272347d57a51be33da89eaab807aef3567186e2c477e7fb447',
'universalAdaptiveColor26561':'225fc96df8d8c2910d68b3b05cbab00f5dc897deaa9cb4f606d8c35084e0e4a7',
'bipolarColorTrust26769':'3647e2255b326cc8c9251ffbe2be2d45d3718dd6d1302d37e22da85d7e4e9515'}
for name,h in expected.items():
 p=next(OUT.glob(name+'.*')); need(hashlib.sha256(p.read_bytes()).hexdigest()==h,f'26789 protected runtime-expanded hash mismatch: {name}')
print('PASS 26790 protected shader fidelity: DNG/normalize/SHORT/residual/old-neutral/VGN owners byte-identical to successful 26789')
print('PASS 26790 modified shader ownership: exact DNG fixed-phase UINT RAW LCA + literal DNG neutral gate + completed-NORMAL LONG chroma consensus')
