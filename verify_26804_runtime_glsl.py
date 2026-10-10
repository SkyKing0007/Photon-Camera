#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
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
    names=set(DECL_RE.findall(clean(src)))|set(FUNC_RE.findall(clean(src)))|set(STRUCT_RE.findall(clean(src))); bad=sorted(n for n in names if n in RESERVED or n.startswith('gl_') or n.startswith('__')); need(not bad,f'{name}: reserved declared identifiers {bad}'); print(f'PASS 26804 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def uniform_completeness(name,src):
    s=clean(src); used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',s)); declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',s)); missing=sorted(used-declared); need(not missing,f'{name}: used-but-undeclared uniforms {missing}'); print(f'PASS 26804 uniform completeness {name}: used={len(used)} declared={len(declared)}')
def compile_one(name,stage,src,check_uniforms=False):
    ext='comp' if stage=='comp' else 'frag'; p=OUT/f'{name}.{ext}'; p.write_text(src); reserved_scan(name,src)
    if check_uniforms: uniform_completeness(name,src)
    if a.compiler:
        cp=subprocess.run([a.compiler,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang failed for {name}')
        print(f'PASS 26804 pinned real glslang compile exact runtime-expanded shader: {name}')
specs=[
 ('merge',S,'frag',True,False),
 ('motionv2_render','app/src/main/assets/shaders/motionv2/render.glsl','frag',False,False),
 ('motionv2_false_color_classify_26800','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','frag',False,False),
 ('motionv2_false_color_classify_26799','app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl','frag',False,False),
 ('motionv2_false_color_propagate_26799','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl','frag',False,False),
 ('motionv2_gainmap','app/src/main/assets/shaders/motionv2/gainmap.glsl','frag',False,False),
 ('jpegNeutralHighlightClamp26790',S,'frag',False,False),('normalChromaConsensus26790',S,'frag',False,False),('jpegPhaseSafeCfaLca26788',S,'frag',False,False),
 ('universalNormalMasterShortFusion26651',S,'frag',False,False),('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp',False,True),('jpegNeutralHighlightClamp26787',S,'frag',False,False),
 ('normalDngMerge',S,'frag',False,False),('normalizeBayer',SP,'frag',False,False),('universalAdaptiveColor26561',POST,'comp',False,False),('bipolarColorTrust26769',POST,'comp',False,False)]
modified=[]; inherited=[]
for name,rel,stage,uc,is_modified in specs:
    src=runtime_asset(CAND,rel) if rel.endswith('.glsl') else shader(CAND,rel,name)
    base=runtime_asset(BASE,rel) if rel.endswith('.glsl') else shader(BASE,rel,name)
    if is_modified:
        need(base!=src,f'modified shader unexpectedly byte-identical: {name}'); modified.append(name)
    else:
        need(base==src,f'inherited active/protected shader changed {name}'); inherited.append(name)
    compile_one(name,stage,src,uc)
need(modified==['EDGE_FALSE_COLOR_SUPPRESSOR_26778'],modified); need(len(inherited)==15,len(inherited))
edge=shader(CAND,T,'EDGE_FALSE_COLOR_SUPPRESSOR_26778'); bedge=shader(BASE,T,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')
need(edge!=bedge,'26804 edge suppressor unexpectedly inherited')
need(edge.count('IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR')==1,'26804 thin-neutral marker missing/duplicate')
need(edge.count('IRIS_26804_THIN_RIDGE_OLD_GATE_BYPASS')==1,'26804 old-gate bypass marker missing/duplicate')
for token in (
 'float retiredClipCandidateW = gate * invalidity * neutralContext;',
 'bool thinGateBypass = false;',
 'bool thinCheapPrefilter =',
 'thinEarlyInvalidity <= 0.52',
 'thinGateBypass = true;',
 'float yXm6 = lumaOf(fetchLin(p + ivec2(-6, 0), sz));',
 'float yXm10 = lumaOf(fetchLin(p + ivec2(-10, 0), sz));',
 'float thinBilateralDrop = max(xBilateralDrop, yBilateralDrop);',
 'float thinNeutralEvidence = max(neutralContext, thinOutsideNeutral);',
 'float thinNearWhiteW = smoothstep(0.52, 0.70, thinNearWhiteRatio);',
 'float thinOutlierW = smoothstep(',
 'bool thinNearWhiteCandidate = thinCommonProof && thinNearWhiteW > 0.30;',
 'bool thinOutlierCandidate = thinCommonProof && !thinNearWhiteCandidate && thinOutlierW > 0.55;',
 'if (thinOutlierCandidate) correctedC = medianC;',
 'if (thinNearWhiteCandidate) correctedC = vec2(0.0);'):
 need(token in edge,f'26804 edge contract missing: {token}')
need('correctedC = mix(correctedC, vec2(0.0), retiredClipCandidateW)' not in edge,'retired broad clip owner reactivated')
need('correctedC = mix(correctedC, materialBaseline26788, retiredClipCandidateW)' not in edge,'retired broad clip material correction reactivated')
m=re.search(r'bool thinCommonProof\s*=\s*(.*?);',edge,re.S); need(m is not None,'thin common-proof block missing')
need('gate >' not in m.group(1) and 'gate *' not in m.group(1),'thin owner still depends on old 5x5 edge gate')
need(edge.index('IRIS_26804_THIN_RIDGE_OLD_GATE_BYPASS') < edge.index('// 2) 3x3 median of sqrt-domain chroma differences'),'old-gate bypass executes too late')
need('rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;' in edge,'luma restoration missing')
need('uint thinRidgeGeometryGt05; uint thinNearWhiteAppliedPass1; uint thinOutlierAppliedPass1;' in edge,'26804 stats shader declaration missing')
# Exact successful 26803 late path is protected/inherited.
cls=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl')
prop=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl')
render=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/render.glsl')
for marker in ('IRIS_26803_STRONG_NEUTRAL_PARENT_FRINGE_REPAIR','IRIS_26803_FAR_ACHROMATIC_PARENT_STRONG_PROOF'):
 need(cls.count(marker)==1,f'inherited 26803 classifier marker missing {marker}')
need('Output=0.92;' in cls,'inherited 26803 direct code missing')
need('bool connected=seed||(candidate&&(already||neighbor));' in prop,'inherited 26799 topology changed')
need('Output=connected?(neutralParentDirect?0.92:1.0):0.0;' in prop,'inherited 26803 direct-code propagation missing')
need(render.count('IRIS_26803_NEUTRAL_PARENT_CORRECTION_TARGET')==1,'inherited 26803 render target missing')
need('?iris26803NeutralParentTarget(sourcePixel,y,guide,centerChroma)' in render,'inherited 26803 target branch missing')
print('PASS 26804 GLSL ownership: 1 modified runtime-expanded shader + 15 inherited active/protected shaders')
print('PASS 26804 inherited active/protected shader fidelity: 15 byte-identical to successful 26803')
print('PASS 26804 contracts: pre-VGN old-gate bypass + bounded thin geometry + dual near-white/outlier correction + retired broad clip guard + exact inherited 26803 far-parent path')
