#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,textwrap
ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); ap.add_argument('--compiler'); ap.add_argument('--out',required=True)
a=ap.parse_args(); B=Path(a.base); C=Path(a.candidate); O=Path(a.out); O.mkdir(parents=True,exist_ok=True)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; JNI='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
def need(v,m):
    if not v: raise AssertionError(m)
def template(text,name):
    pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=None
    for pat in pats:
        m=re.search(pat,text,re.M)
        if m: break
    need(m,f'{name}: declaration missing'); start=text.find('"""',m.start())+3; end=text.find('""".trimIndent()',start); need(end>=0,f'{name}: terminator'); return textwrap.dedent(text[start:end]).strip('\n')
def shader(root,rel,name):
    text=(root/rel).read_text(); src=template(text,name)
    for dep in ('common','outputTransformBody'):
        if '$'+dep in src: src=src.replace('$'+dep,template(text,dep))
    need('$' not in src,f'{name}: unresolved interpolation'); return src+'\n'
def asset(root,rel): return '#version 310 es\n#line 1\n'+(root/rel).read_text()
def cpp(root):
    x=(root/JNI).read_text(); k='static const char*kIris26571PublicationCompute=R"GLSL('; i=x.find(k); need(i>=0,'cpp start'); i+=len(k); j=x.find(')GLSL";',i); need(j>=0,'cpp end'); return x[i:j]
RESERVED=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise break continue do for while switch case default if else subroutine in out inout float double int void bool true false discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major'.split())
TYPE=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w+|[iu]?image\w+|atomic_uint)'
def clean(s): return re.sub(r'//.*',' ',re.sub(r'/\*.*?\*/',' ',s,flags=re.S))
def scan(n,src):
    cs=clean(src); names=set(re.findall(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)',cs))|set(re.findall(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)\s*\(',cs)); bad=sorted(x for x in names if x in RESERVED or x.startswith('gl_') or x.startswith('__')); need(not bad,f'{n}: reserved {bad}')
def compile_one(name,stage,src):
    scan(name,src); ext='comp' if stage=='comp' else 'frag'; p=O/f'{name}.{ext}'; p.write_text(src)
    if a.compiler:
        cp=subprocess.run([a.compiler,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang failed {name}')
    print(f'PASS 26852 shader {name} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def get(root,rel,name,kind):
    if kind=='asset': return asset(root,rel)
    if kind=='cpp': return cpp(root)
    return shader(root,rel,name)
inherited=[
('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp','kotlin'),('highZoomDetailResolve26718',S,'frag','kotlin'),('universalAdaptiveColor26561',POST,'comp','kotlin'),('true2x_publication_compute',JNI,'comp','cpp'),
('normalizeBayer',SP,'frag','kotlin'),('outputTransformUint16',S,'frag','kotlin'),('outputTransformFloat',S,'frag','kotlin'),('outputTransformHdrDirectionUint16',S,'frag','kotlin'),
('motionv2_false_color_classify_26800','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','frag','asset'),('motionv2_false_color_propagate_26799','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl','frag','asset'),('motionv2_false_color_classify_26799','app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl','frag','asset'),
('jpegNeutralHighlightClamp26790',S,'frag','kotlin'),('normalChromaConsensus26790',S,'frag','kotlin'),('jpegPhaseSafeCfaLca26788',S,'frag','kotlin'),('universalNormalMasterShortFusion26651',S,'frag','kotlin'),('jpegNeutralHighlightClamp26787',S,'frag','kotlin'),('normalDngMerge',S,'frag','kotlin'),
('seed',POST,'comp','kotlin'),('localMedian',POST,'comp','kotlin'),('directionalSmooth',POST,'comp','kotlin'),('iirRgb',POST,'comp','kotlin'),('bipolarColorTrust26769',POST,'comp','kotlin'),
('shadowLongLumaAccumulate26833',S,'frag','kotlin'),('shadowLongLumaGainMap26833',S,'frag','kotlin'),('shadowLongPostVgnLumaApply26833',S,'frag','kotlin'),
('clipZoneMaskDilate26834',S,'frag','kotlin'),('clipZoneGaussian26834',S,'frag','kotlin'),('clipZoneDownsample4Products26834',S,'frag','kotlin'),
('motionv2_render','app/src/main/assets/shaders/motionv2/render.glsl','frag','asset'),('motionv2_gainmap','app/src/main/assets/shaders/motionv2/gainmap.glsl','frag','asset'),
('clipZoneProducts26834',S,'frag','kotlin'),('clipZoneApply26834',S,'comp','kotlin'),('clipZoneApplyFragment26837',S,'frag','kotlin'),('clipZoneApplyFragment26838',S,'frag','kotlin'),('clipZoneApplyFragment26839',S,'frag','kotlin')]
for n,r,st,k in inherited:
    bs=get(B,r,n,k); cs=get(C,r,n,k); need(bs==cs,f'inherited shader changed {n}'); compile_one(n,st,cs)
COLOR='app/src/main/assets/shaders/motionv2/color_transform.glsl'; need((B/COLOR).read_bytes()==(C/COLOR).read_bytes(),'26841 color_transform changed')
for high_zoom in (0,1):
  for hue_sat in (0,1):
    for look in (0,1):
      name=f'motionv2_color_transform_hz{high_zoom}_hs{hue_sat}_lk{look}'; expanded=('#version 310 es\n'+f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {high_zoom}\n'+f'#define USE_PROFILE_HUESAT {hue_sat}\n'+f'#define USE_PROFILE_LOOK {look}\n'+'#line 1\n'+(C/COLOR).read_text()); compile_one(name,'frag',expanded)
clipB=shader(B,S,'clipZoneApplyFragment26840'); clipC=shader(C,S,'clipZoneApplyFragment26840'); need(clipB==clipC,'26852 clip shader must remain byte-identical to successful 26851'); need('IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF' in clipC,'26842 clip marker'); compile_one('clipZoneApplyFragment26840_26842_inherited','frag',clipC)
SHADOW='app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl'; need((B/SHADOW).read_bytes()==(C/SHADOW).read_bytes(),'26852 shadow cleanup must remain byte-identical to successful 26851'); shadow=asset(C,SHADOW); need('IRIS_26842_TRUE_FLAT_MOTTLING_CLEANUP' in shadow,'26842 mottling marker'); compile_one('motionv2_shadow_cleanup_26842_inherited','frag',shadow)
baseMerge=shader(B,S,'merge'); candMerge=shader(C,S,'merge'); need(baseMerge!=candMerge,'26852 merge unexpectedly unchanged')
for marker in ('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION','IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER','IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER'):
    need(marker in candMerge,f'26852 inheritance missing {marker}')
for marker in ('IRIS_26852_TEMPORAL_CFA_RECONSTRUCTION_INPUT','IRIS_26852_TEMPORAL_CFA_SUPPORT_HANDOFF'):
    need(marker in candMerge,f'26852 marker missing {marker}')
need('uniform sampler2D uTemporalCfaValidity26852;' in candMerge,'26852 temporal phase-validity sampler missing')
need('sharedSupport26852' in candMerge and 'float shared =' not in candMerge,'26852 reserved shared identifier regression')
helperDecl='float peripheralLcaStrength26849(vec2 referenceUv);'; helperCall='peripheralLcaStrength26849(referenceUv26791)'
centralDecl='float centralMaterialRegistrationGate26851(ivec2 position);'; centralCall='centralMaterialRegistrationGate26851(position)'
temporalDecl='float temporalNormalized26852(ivec2 p);'; temporalCall='temporalNormalized26852(p)'
for decl,call,label in [(helperDecl,helperCall,'26849 helper'),(centralDecl,centralCall,'26851 helper'),(temporalDecl,temporalCall,'26852 temporal helper')]: need(decl in candMerge and call in candMerge and candMerge.index(decl)<candMerge.index(call),f'{label} declaration order')
compile_one('merge_26852','frag',candMerge)
acc=shader(C,S,'normalCfaTemporalAccumulate26852')
need('layout(location = 2) out vec4 oPhaseValidity;' in acc,'26852 phase-validity MRT missing')
need('oPhaseValidity = phaseHeadroom * validWeight;' in acc,'26852 phase-validity provenance equation missing')
compile_one('normalCfaTemporalAccumulate26852','frag',acc)
compile_one('normalCfaExtract26852','frag',shader(C,S,'normalCfaExtract26852'))
need((B/SP).read_bytes()==(C/SP).read_bytes(),'26852 DNG/Spatial shader source changed')
print('PASS 26852 GLSL ownership: exactly 3 modified NORMAL temporal-CFA shaders; 45 successful-26851 active/protected variants inherited byte-identically')
print('PASS 26852 CFA safety: exact 26851 first-NORMAL reference/flow/rejection and 26846-26851 CFA reconstruction ownership preserved; temporal accumulation keeps physical R/G1/G2/B with one shared admission weight, reconstructs RGB once, and leaves DNG/SHORT/LONG/VGN/UHDR/high-zoom owners inherited')
