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
    need(m,f'{name}: declaration missing')
    start=text.find('"""',m.start())+3; end=text.find('""".trimIndent()',start); need(end>=0,f'{name}: terminator')
    return textwrap.dedent(text[start:end]).strip('\n')
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
    print(f'PASS 26841 shader {name} sha256={hashlib.sha256(src.encode()).hexdigest()}')
def get(root,rel,name,kind):
    if kind=='asset': return asset(root,rel)
    if kind=='cpp': return cpp(root)
    return shader(root,rel,name)
# Successful-26840 runtime-expanded shader universe: 37 inherited byte-identical; 26841 modifies color_transform only.
inherited=[
('EDGE_FALSE_COLOR_SUPPRESSOR_26778',T,'comp','kotlin'),('highZoomDetailResolve26718',S,'frag','kotlin'),('universalAdaptiveColor26561',POST,'comp','kotlin'),('true2x_publication_compute',JNI,'comp','cpp'),
('normalizeBayer',SP,'frag','kotlin'),('outputTransformUint16',S,'frag','kotlin'),('outputTransformFloat',S,'frag','kotlin'),('outputTransformHdrDirectionUint16',S,'frag','kotlin'),
('motionv2_false_color_classify_26800','app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl','frag','asset'),('motionv2_false_color_propagate_26799','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl','frag','asset'),('motionv2_false_color_classify_26799','app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl','frag','asset'),
('jpegNeutralHighlightClamp26790',S,'frag','kotlin'),('normalChromaConsensus26790',S,'frag','kotlin'),('jpegPhaseSafeCfaLca26788',S,'frag','kotlin'),('universalNormalMasterShortFusion26651',S,'frag','kotlin'),('jpegNeutralHighlightClamp26787',S,'frag','kotlin'),('normalDngMerge',S,'frag','kotlin'),
('seed',POST,'comp','kotlin'),('localMedian',POST,'comp','kotlin'),('directionalSmooth',POST,'comp','kotlin'),('iirRgb',POST,'comp','kotlin'),('bipolarColorTrust26769',POST,'comp','kotlin'),
('shadowLongLumaAccumulate26833',S,'frag','kotlin'),('shadowLongLumaGainMap26833',S,'frag','kotlin'),('shadowLongPostVgnLumaApply26833',S,'frag','kotlin'),
('merge',S,'frag','kotlin'),('clipZoneMaskDilate26834',S,'frag','kotlin'),('clipZoneGaussian26834',S,'frag','kotlin'),('clipZoneDownsample4Products26834',S,'frag','kotlin'),
('motionv2_render','app/src/main/assets/shaders/motionv2/render.glsl','frag','asset'),('motionv2_gainmap','app/src/main/assets/shaders/motionv2/gainmap.glsl','frag','asset'),
('clipZoneProducts26834',S,'frag','kotlin'),('clipZoneApply26834',S,'comp','kotlin'),('clipZoneApplyFragment26837',S,'frag','kotlin'),('clipZoneApplyFragment26838',S,'frag','kotlin'),('clipZoneApplyFragment26839',S,'frag','kotlin'),('clipZoneApplyFragment26840',S,'frag','kotlin')]
for n,r,st,k in inherited:
    bs=get(B,r,n,k); cs=get(C,r,n,k); need(bs==cs,f'inherited shader changed {n}'); compile_one(n,st,cs)
# 26841 modifies one asset shader. Compile every runtime define combination exactly after
# GLProg's #version 310 es + generated defines + #line handoff.
COLOR='app/src/main/assets/shaders/motionv2/color_transform.glsl'
base_color=(B/COLOR).read_text(); cand_color=(C/COLOR).read_text(); need(base_color!=cand_color,'26841 color_transform must change')
need('IRIS_26841_WARM_MIDTONE_ACR3_RESTRAINT' in cand_color,'26841 warm midtone marker')
for high_zoom in (0,1):
  for hue_sat in (0,1):
    for look in (0,1):
      name=f'motionv2_color_transform_hz{high_zoom}_hs{hue_sat}_lk{look}'
      expanded=(
        '#version 310 es\n'
        f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {high_zoom}\n'
        f'#define USE_PROFILE_HUESAT {hue_sat}\n'
        f'#define USE_PROFILE_LOOK {look}\n'
        '#line 1\n'+cand_color
      )
      compile_one(name,'frag',expanded)
print('PASS 26841 GLSL ownership: 8 exact runtime-expanded color_transform variants + 37 inherited active/protected shaders')
print('PASS 26841 inherited shader fidelity: 37 byte-identical to successful 26840')
