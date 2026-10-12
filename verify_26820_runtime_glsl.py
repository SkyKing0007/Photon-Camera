#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); ap.add_argument('--compiler'); ap.add_argument('--out',required=True)
a=ap.parse_args(); BASE=Path(a.base); CAND=Path(a.candidate); OUT=Path(a.out); OUT.mkdir(parents=True,exist_ok=True)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
def need(c,m):
    if not c: raise AssertionError(m)
def template(text,name):
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,f'{name}: declaration missing')
    b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing')
    return textwrap.dedent(text[m.end():b]).strip('\n')
def shader(root,rel,name):
    text=(root/rel).read_text(); src=template(text,name)
    for dep in ('common','outputTransformBody'):
        key='$'+dep
        if key in src: src=src.replace(key,template(text,dep))
    need('$' not in src,f'{name}: unresolved Kotlin shader interpolation remains')
    return src+'\n'
def runtime_asset(root,rel):
    src=(root/rel).read_text(); need('#version' not in src and '#import' not in src and '#define' not in src,f'{rel}: runtime preprocessor assumptions changed'); return '#version 310 es\n#line 1\n'+src
RESERVED=set(('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3 dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS sampler2DMSArray isampler2DMS usampler2DMSArray samplerCubeArray samplerCubeArrayShadow isamplerCubeArray usamplerCubeArray image1D iimage1D uimage1D image2D iimage2D uimage2D image3D iimage3D uimage3D image2DRect iimage2DRect uimage2DRect imageCube iimageCube uimageCube imageBuffer iimageBuffer uimageBuffer image1DArray iimage1DArray uimage1DArray image2DArray iimage2DArray uimage2DArray imageCubeArray iimageCubeArray uimageCubeArray image2DMS iimage2DMS uimage2DMS image2DMSArray iimage2DMS uimage2DMSArray struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major').split())
TYPE=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'; DECL_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)'); FUNC_RE=re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)\s*\('); STRUCT_RE=re.compile(r'\bstruct\s+([A-Za-z_]\w*)')
def clean(src): return re.sub(r'//.*',' ',re.sub(r'/\*.*?\*/',' ',src,flags=re.S))
def reserved_scan(name,src):
    names=set(DECL_RE.findall(clean(src)))|set(FUNC_RE.findall(clean(src)))|set(STRUCT_RE.findall(clean(src))); bad=sorted(n for n in names if n in RESERVED or n.startswith('gl_') or n.startswith('__')); need(not bad,f'{name}: reserved declared identifiers {bad}'); print(f'PASS 26820 reserved-identifier scan {name}: declarations={len(names)} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def uniform_completeness(name,src):
    s=clean(src); used=set(re.findall(r'\bu[A-Z][A-Za-z0-9_]*\b',s)); declared=set(re.findall(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?[A-Za-z_]\w*\s+(u[A-Z][A-Za-z0-9_]*)',s)); missing=sorted(used-declared); need(not missing,f'{name}: used-but-undeclared uniforms {missing}'); print(f'PASS 26820 uniform completeness {name}: used={len(used)} declared={len(declared)}')
def compile_one(name,stage,src,check_uniforms=False):
    ext='comp' if stage=='comp' else 'frag'; p=OUT/f'{name}.{ext}'; p.write_text(src); reserved_scan(name,src)
    if check_uniforms: uniform_completeness(name,src)
    if a.compiler:
        cp=subprocess.run([a.compiler,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang failed for {name}')
        print(f'PASS 26820 pinned real glslang compile exact runtime-expanded shader: {name}')
modified_specs=[('motionv2_render','app/src/main/assets/shaders/motionv2/render.glsl','frag',False),('motionv2_false_color_propagate_26799','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl','frag',False),('normalizeBayer',SP,'frag',False)]
inherited_specs=[
 ('merge',S,'frag',True),('motionv2_false_color_classify_26800','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','frag',False),('universalAdaptiveColor26561',POST,'comp',True),('outputTransformUint16',S,'frag',True),('outputTransformFloat',S,'frag',True),('outputTransformHdrDirectionUint16',S,'frag',True),('motionv2_false_color_classify_26799','app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl','frag',False),('motionv2_gainmap','app/src/main/assets/shaders/motionv2/gainmap.glsl','frag',False),('jpegNeutralHighlightClamp26790',S,'frag',False),('normalChromaConsensus26790',S,'frag',False),('jpegPhaseSafeCfaLca26788',S,'frag',False),('universalNormalMasterShortFusion26651',S,'frag',False),('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp',True),('jpegNeutralHighlightClamp26787',S,'frag',False),('normalDngMerge',S,'frag',False),('seed',POST,'comp',True),('localMedian',POST,'comp',True),('directionalSmooth',POST,'comp',True),('iirRgb',POST,'comp',True),('bipolarColorTrust26769',POST,'comp',True)]
for name,rel,stage,uc in modified_specs:
    src=runtime_asset(CAND,rel) if rel.endswith('.glsl') else shader(CAND,rel,name); base=runtime_asset(BASE,rel) if rel.endswith('.glsl') else shader(BASE,rel,name); need(base!=src,f'modified shader unexpectedly byte-identical: {name}'); compile_one(name,stage,src,uc)
for name,rel,stage,uc in inherited_specs:
    src=runtime_asset(CAND,rel) if rel.endswith('.glsl') else shader(CAND,rel,name); base=runtime_asset(BASE,rel) if rel.endswith('.glsl') else shader(BASE,rel,name); need(base==src,f'inherited active/protected shader changed {name}'); compile_one(name,stage,src,uc)
merge=shader(CAND,S,'merge'); basemerge=shader(BASE,S,'merge'); need(merge==basemerge,'successful 26819 Sabre merge changed')
for token in ['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER','float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);','calculationCfa26793, weights, sourceValidity, type, covariance, 1,']:
    need(token in merge,'missing frozen 26819 Sabre proof '+token)
vgn=shader(CAND,POST,'universalAdaptiveColor26561'); basevgn=shader(BASE,POST,'universalAdaptiveColor26561'); need(vgn==basevgn,'successful 26818 VGN shader changed')
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','smoothstep(0.70, 0.90','smoothstep(0.030, 0.080','greenCleanupAuthority = 0.75']:
    need(token in vgn,'missing frozen VGN proof '+token)
classifier=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'); baseclassifier=runtime_asset(BASE,'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'); need(classifier==baseclassifier,'26800 classifier changed')
render=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/render.glsl'); prop=runtime_asset(CAND,'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'); nb=shader(CAND,SP,'normalizeBayer')
for token in ['IRIS_26820_FALSE_COLOR_CONFIDENCE_FEATHER_OWNER','iris26820ConnectedEvidenceStrength','return mix(rgb,corrected,clamp(correctionStrength,0.0,1.0));','if(iris26803NeutralParentDirect)return corrected;']:
    need(token in render,'missing JPEG 26820 proof '+token)
for token in ['IRIS_26820_GRADED_CONNECTED_FALSE_COLOR_EVIDENCE','Output=connected?(neutralParentDirect?0.92:cls):0.0;','bool candidate=cls>=0.35;','bool seed=cls>=0.75;']:
    need(token in prop,'missing propagation 26820 proof '+token)
for token in ['IRIS_26820_DNG_NEUTRAL_PHASE_COHERENCE_OWNER','if(phase!=redPhase26786()&&phase!=bluePhase26786())return normalized;','float neutralConfidence=1.0-smoothstep(0.10,0.30,materialChroma);','normalized=iris26820NeutralPhaseCorrected(p,normalized,phase26786);']:
    need(token in nb,'missing DNG 26820 proof '+token)
normaldng=shader(CAND,S,'normalDngMerge'); basenormaldng=shader(BASE,S,'normalDngMerge'); need(normaldng==basenormaldng,'normalDngMerge changed')
for rel in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'):
    text=(CAND/rel).read_text(); need('atomicAdd(' not in text and 'atomicMax(' not in text and 'iris26798Counters' not in text and 'iris26799Counters' not in text,f'{rel}: telemetry atomics survived')
print('PASS 26820 GLSL ownership: 3 modified runtime-expanded shaders + 20 inherited active/protected shaders')
print('PASS 26820 inherited active/protected shader fidelity: 20 byte-identical to successful 26819')
