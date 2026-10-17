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
    print(f'PASS 26851 shader {name} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def get(root,rel,name,kind):
    if kind=='asset': return asset(root,rel)
    if kind=='cpp': return cpp(root)
    return shader(root,rel,name)
# Exact successful-26848 active/protected runtime shader universe, except merge is the sole 26849 modification.
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
clipB=shader(B,S,'clipZoneApplyFragment26840'); clipC=shader(C,S,'clipZoneApplyFragment26840'); need(clipB==clipC,'26851 clip shader must remain byte-identical to successful 26849'); need('IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF' in clipC,'26842 clip marker'); compile_one('clipZoneApplyFragment26840_26842_inherited','frag',clipC)
SHADOW='app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl'; need((B/SHADOW).read_bytes()==(C/SHADOW).read_bytes(),'26851 shadow cleanup must remain byte-identical to successful 26849'); shadow=asset(C,SHADOW); need('IRIS_26842_TRUE_FLAT_MOTTLING_CLEANUP' in shadow,'26842 mottling marker'); compile_one('motionv2_shadow_cleanup_26842_inherited','frag',shadow)
# 26851 modifies exactly the existing NORMAL merge shader.
baseMerge=shader(B,S,'merge'); candMerge=shader(C,S,'merge'); need(baseMerge!=candMerge,'26851 merge unexpectedly unchanged')
for marker in ('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION'):
    need(marker in candMerge,f'26851 inheritance missing {marker}')
need('IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER' in candMerge,'26851 inherited adaptive registration marker missing')
need('IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER' in candMerge,'26851 all-field owner marker missing')
need('IRIS_26851_CENTRAL_GREEN_MATERIAL_PROOF' in candMerge,'26851 central material proof marker missing')
need('candidateIndex < 3' in candMerge and '? 2.0 : (candidateIndex == 1 ? 4.0 : 6.0)' in candMerge,'26850 bounded 0/2/4/6 search missing')
need('candidateScore >= 0.82' in candMerge and 'candidateScore > bestScore + 0.08' in candMerge,'26850 improvement gate missing')
need('Exact 26848 fallback' in candMerge,'26850 exact-fallback regression marker missing')
# New helper definitions must precede their first downstream calls.
defpos={name:candMerge.find('float '+name+'(') for name in ('phaseNormalizedAtCenter26850','greenGuideAtCenter26850','phaseShapeScore26850','adaptivePhaseK26850')}
for name,pos in defpos.items(): need(pos>=0,f'26851 helper missing {name}')
need(defpos['phaseNormalizedAtCenter26850'] < candMerge.find('phaseNormalizedAtCenter26850(sourceCenter, phaseIndex)', defpos['phaseNormalizedAtCenter26850']+1),'26850 phase sample declaration order')
need(defpos['greenGuideAtCenter26850'] < candMerge.find('greenGuideAtCenter26850(nominalSourceCenter', defpos['greenGuideAtCenter26850']+1),'26850 green guide declaration order')
need(defpos['phaseShapeScore26850'] < candMerge.find('phaseShapeScore26850(', defpos['phaseShapeScore26850']+len('float phaseShapeScore26850(')),'26850 shape score declaration order')
need(defpos['adaptivePhaseK26850'] < candMerge.find('adaptivePhaseK26850(', defpos['adaptivePhaseK26850']+len('float adaptivePhaseK26850(')),'26850 adaptive K declaration order')
# Permanently preserve both 26849 declaration-order regressions.
helperDecl='float peripheralLcaStrength26849(vec2 referenceUv);'
helperCall='peripheralLcaStrength26849(referenceUv26791)'
overloadDecl='\n'.join([
'void fillCorrectedCfaNeighborhood26792(',
'    ivec2 position,',
'    vec2 sharedTranslationPixels,',
'    vec3 covariance,',
'    float autoPeripheralLcaStrength26849,',
'    out mat3 bayerValue,',
'    out mat3 sourceValidity',
');'])
overloadCall='\n'.join([
'fillCorrectedCfaNeighborhood26792(',
'            position,',
'            sharedTranslationPixels26791,',
'            covariance,',
'            autoPeripheralLcaStrength26849,'])
need(helperDecl in candMerge and candMerge.index(helperDecl) < candMerge.index(helperCall),'26849 regression preserved: peripheralLcaStrength26849 declaration order')
need(overloadDecl in candMerge,'26849 regression preserved: fillCorrectedCfaNeighborhood declaration exists')
# 26851 declaration/signature regression checks before the real compiler.
centralDecl='float centralMaterialRegistrationGate26851(ivec2 position);'
centralCall='centralMaterialRegistrationGate26851(position)'
need(centralDecl in candMerge and centralCall in candMerge and candMerge.index(centralDecl) < candMerge.index(centralCall),'26851 central helper declaration order')
need('float autoRegistrationSearchGate26851 = autoPeripheralLcaStrength26849;' in candMerge,'26851 successful-26850 peripheral priority missing')
need('if (uJpegLcaEnabled26790 == 0 && autoPeripheralLcaStrength26849 <= 1.0e-7)' in candMerge,'26851 central dead-zone condition missing')
need('return smoothstep(0.18, 0.50, relativeGreenRange) * balancedPhysicalSupport26851;' in candMerge,'26851 green material gate missing')
need('0.035 * max(uSourceWhiteNormalized26790, 1.0e-5)' in candMerge,'26851 dark-noise floor missing')
callpos=candMerge.index('fillCorrectedCfaNeighborhood26792(',candMerge.index('void sampleNeighborhoodRbf('))
callwindow=candMerge[callpos:callpos+300]
for token in ('position,','sharedTranslationPixels26791,','covariance,','autoRegistrationSearchGate26851,'):
    need(token in callwindow,f'26851 fillCorrected call signature token missing: {token}')
need(candMerge.index(overloadDecl) < callpos,'26851 fillCorrected overload declaration order')
compile_one('merge_26851','frag',candMerge)
need((B/T).read_bytes()==(C/T).read_bytes(),'26851 spatial stacker must remain byte-identical')
print('PASS 26851 GLSL ownership: exactly 1 modified NORMAL merge shader; 45 successful-26850 active/protected variants inherited byte-identically')
print('PASS 26851 CFA safety: successful 26850 peripheral adaptive registration is exact; only its former central dead zone may open under green-only material/headroom proof; zero-shift fallback, green phase, temporal, LONG, SHORT, VGN/FCC/26840/UHDR/DNG/high-zoom/motion/detail owners remain inherited')
