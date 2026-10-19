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
    print(f'PASS 26856 shader {name} sha256={hashlib.sha256(src.encode()).hexdigest()}')
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
compiled=0
for n,r,st,k in inherited:
 bs=get(B,r,n,k);cs=get(C,r,n,k);need(bs==cs,f'inherited successful 26855 shader changed {n}')
 compile_one(n,st,cs);compiled+=1
COLOR='app/src/main/assets/shaders/motionv2/color_transform.glsl';need((B/COLOR).read_bytes()==(C/COLOR).read_bytes(),'26841 color_transform changed')
for hz in (0,1):
 for hs in (0,1):
  for lk in (0,1):
   nm=f'motionv2_color_transform_hz{hz}_hs{hs}_lk{lk}'
   expanded=('#version 310 es\n'+f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {hz}\n'+f'#define USE_PROFILE_HUESAT {hs}\n'+f'#define USE_PROFILE_LOOK {lk}\n'+'#line 1\n'+(C/COLOR).read_text());compile_one(nm,'frag',expanded);compiled+=1
for nm in ('clipZoneApplyFragment26840','normalCfaTemporalAccumulate26852','normalCfaNoiseClean26853','merge','normalCfaExtract26852','true2xGuideRender26568'):
 bs=shader(B,S,nm);cs=shader(C,S,nm);need(bs==cs,f'protected baseline shader changed {nm}');compile_one(nm+'_26855_protected','frag',cs);compiled+=1
SH='app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl';need((B/SH).read_bytes()==(C/SH).read_bytes(),'protected shadow cleanup changed');compile_one('motionv2_shadow_cleanup_26855','frag',asset(C,SH));compiled+=1
# New, actively executable runtime GL shaders. Exactly expand Kotlin trimIndent and
# all GLSL include/define contents. No mock compiler or substituted GLSL snippets.
NEW={
 'GlesIris26856AmazeCfaHandoff.kt':('packedBayerShader',),
 'GlesIris26856B2xShortGuide.kt':('extractGain','applyGain','applyVerifiedLongLuma26856'),
 'GlesIris26856RawrColorContract.kt':('undoAmazeWbToIrisSensorNeutral',),
 'GlesIris26856RawrFalseColor.kt':('medianChroma','reconstructChroma'),
 'GlesIris26856ShortHdrTransfer.kt':('scalarRadianceShader',),
 'GlesIris26856True2xCfa.kt':('accumulate','resolve','pack')}
K='app/src/main/java/com/hinnka/mycamera/processor'
for fn,variants in NEW.items():
 rel=f'{K}/{fn}';text=(C/rel).read_text();need(text.count('"""')==2*len(variants),f'unexpected shader template set {fn}')
 for name in variants:
  src=template(text,name)+'\n'
  need(src.lstrip().startswith('#version'),f'GL version missing {fn}/{name}')
  need('$' not in src,f'unexpanded new shader interpolation {fn}/{name}')
  compile_one(fn.replace('.kt','')+'_'+name,'comp' if '#version 310 es' in src and 'local_size_x' in src else 'frag',src);compiled+=1
# Native GLES 3.1 Lab code uses an app-side exact include expansion at runtime.
LAB='app/src/main/assets/iris26856/rawr/lab/'
inc=(C/LAB/'lab_defringe_common.glsl').read_text();need('layout(std140, binding = 0)' in inc,'Lab buffer ABI missing')
for fn in ('lab_defringe_prepare.comp','lab_defringe_reduce.comp','lab_defringe_reconstruct.comp'):
 original=(C/LAB/fn).read_text();needle='#include "lab_defringe_common.glsl"';need(original.count(needle)==1,f'Lab expansion count {fn}')
 src=original.replace(needle,inc);need('#include ' not in src,f'non-expanded GLSL {fn}')
 compile_one('26856_'+fn.removesuffix('.comp'),'comp',src);compiled+=1
# New RAWR AMaZE native GLSL source, preprocess exactly the single guarded include.
# Its pre-pinned 19 SPIR-V binaries are separate and their hashes belong to
# candidate/source authority. Do NOT claim source compilation validates those binaries.
NATIVE='app/src/main/cpp/iris26856/amaze/shaders/'
inc=(C/NATIVE/'amaze_tile.glsl').read_text()
for fn in ('amaze_import.comp','amaze_export.comp'):
 original=(C/NATIVE/fn).read_text();needle='#include "amaze_tile.glsl"';need(original.count(needle)==1,fn)
 src=original.replace(needle,inc);need(src.lstrip().startswith('#version 450'),fn)
 p=O/('26856_native_'+fn);p.write_text(src);scan(fn,src)
 if a.compiler:
  cp=subprocess.run([a.compiler,'-S','comp','-V','--target-env','vulkan1.1',str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:print(cp.stdout);raise SystemExit(f'pinned Vulkan glslang failed {fn}')
 print('PASS 26856 native expanded shader',fn,hashlib.sha256(src.encode()).hexdigest());compiled+=1
# Historical A is included as a new, explicitly copied 26850 shader owner.
# Compile all runtime full-shader template variants, not only the B additions.
AREL='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders26850.kt'
at=(C/AREL).read_text()
found=re.findall(r'^\s*(?:private\s+)?val\s+(\w+)[^\n]*?"""',at,re.M)
need(len(found)>=70,'incomplete copied historical A shader universe')
for name in found:
 try:src=shader(C,AREL,name)
 except AssertionError:
  if name in ('outputs','scalarOutputs','outputTransformBody'):continue
  raise
 if not src.lstrip().startswith('#version') or 'void main' not in src:continue
 need('$' not in src,f'Historical A template unresolved {name}')
 stage='comp' if 'layout(local_size_x' in src else 'frag'
 compile_one('26850_A_'+name,stage,src);compiled+=1
# Separate copied 26850 stacker compute owner.
copyT='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt'
copytext=(C/copyT).read_text();name='EDGE_FALSE_COLOR_SUPPRESSOR_26778'
need(name in copytext,'26850 A legacy compute missing')
compile_one('26850_A_edge_false_color', 'comp',shader(C,copyT,name));compiled+=1
# Verify pinned 19 shader binaries are actual SPIR-V magic, not empty blobs.
SPV='app/src/main/assets/iris26856/rawr/amaze/spv'
bins=sorted((C/SPV).glob('*.spv'));need(len(bins)==19,f'RAWR AMaZE SPIR-V count {len(bins)}')
for file in bins:
 data=file.read_bytes();need(len(data)>=20 and len(data)%4==0 and data[:4]==b'\x03\x02\x23\x07',f'invalid SPIR-V header {file.name}')
print('PASS 26856 GLSL ownership:',compiled,'exact active expanded variants including 26855 inherited + all 26856 GL/Lab/native; reserved IDs scanned; pinned real compiler '+('PASS' if a.compiler else 'NOT RUN'))
