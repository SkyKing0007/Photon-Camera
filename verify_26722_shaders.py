#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26722_shaders.py ROOT BASE CAND [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6: assert sys.argv[4]=='--compiler'; compiler=sys.argv[5]
def load(n):
 d={}
 for l in (root/n).read_text().splitlines():
  if l.strip(): h,r=l.split(None,1); d[r.strip()]=h
 return d
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def triple(k,name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',k,re.S); assert m,name
 return textwrap.dedent(m.group(1))
def make_sources(cand):
 k=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 rejection=triple(k,'rejection'); merge=triple(k,'merge'); true=triple(k,'true2xMerge26564'); guide=triple(k,'true2xGuideRender26568')
 rgbmerge=true
 repls=[
 ('uniform float uRawClipThreshold;', 'uniform float uRawClipThreshold;\nuniform float uObservationConfidence;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;'),
 ('float kernelWeight(vec2 offset, vec3 covariance) {', 'float iris26720HighZoomRowReliability(float rowUv) {\n    if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 || uRowFlickerStrength <= 0.0) return 1.0;\n    float phase = 6.283185307179586 * float(uRowFlickerHarmonic) * clamp(rowUv, 0.0, 1.0);\n    float logModulation = uRowFlickerAB.x * cos(phase) + uRowFlickerAB.y * sin(phase);\n    float amplitude = length(uRowFlickerAB);\n    float darkMagnitude = max(-logModulation, 0.0);\n    float darkBand = smoothstep(0.010, max(0.030, amplitude * 0.90), darkMagnitude);\n    return mix(1.0, 0.08, clamp(darkBand * clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));\n}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {'),
 ('float frameWeight = sampleRejection(referenceUv);', 'float frameWeight = sampleRejection(referenceUv);\n    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0);\n    frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);')]
 for old,new in repls:
  assert rgbmerge.count(old)==1,('highzoom RGB merge anchor',old,rgbmerge.count(old)); rgbmerge=rgbmerge.replace(old,new,1)
 # 26722 deliberately reuses the exact proven native-Sabre/VGN chroma topology shader.
 protect=guide
 outputs='layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'
 scalar='layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;'
 rgbwrite='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
 assert true.count(outputs)==1 and true.count(rgbwrite)==1
 scalarmerge=true.replace(outputs,scalar,1).replace(rgbwrite,'',1)
 m=re.search(r'val\s+highZoomDetailResolve26718\s*:\s*String\s+by\s+lazy\s*\{\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)\s*\}',k,re.S); assert m
 scalarresolve=textwrap.dedent(m.group(1))
 asset=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
 def glinterface(defval):
  lines=[]
  for line in asset.splitlines():
   if '#define USE_IRIS_26720_HIGH_ZOOM_RGB ' in line and defval is not None:
    line=f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {defval}'
   lines.append(line)
  return '#version 310 es\n\n#line 1\n'+'\n'.join(lines)+'\n'
 return {
  '26722_sabre_rejection.frag':rejection,
  '26722_sabre_merge.frag':merge,
  '26722_highzoom_rgb_merge.frag':rgbmerge,
  '26722_highzoom_native_chroma_protect.frag':protect,
  '26722_highzoom_scalar_fallback_merge.frag':scalarmerge,
  '26722_highzoom_scalar_fallback_resolve.frag':scalarresolve,
  '26722_color_transform_disabled.frag':glinterface(0),
  '26722_color_transform_highzoom_rgb.frag':glinterface(1),
 }
# Asset universe is byte-identical to successful 26721; generated high-zoom protection is the only shader semantic delta.
bm=load('26722_ASSET_SHADER_UNIVERSE_BASE.sha256'); cm=load('26722_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(bm)==len(cm)==271 and bm==cm
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
sources=make_sources(cand); exp=load('26722_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert set(exp)==set(sources)
for n,src in sources.items(): assert hashlib.sha256(src.encode()).hexdigest()==exp[n],n
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for name,src in sources.items():
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_'))); assert not bad and not impl,(name,bad,impl)
 assert clean.count('{')==clean.count('}') and '#import' not in clean,name
# Semantic sentinels.
assert 'uReferenceRowFlickerEnabled' in sources['26722_sabre_rejection.frag'] and 'uCurrentRowFlickerEnabled' in sources['26722_sabre_rejection.frag']
assert 'uRowFlickerEnabled' in sources['26722_sabre_merge.frag']
assert 'uObservationConfidence' in sources['26722_highzoom_rgb_merge.frag'] and 'iris26720HighZoomRowReliability' in sources['26722_highzoom_rgb_merge.frag']
protect=sources['26722_highzoom_native_chroma_protect.frag']
for t in ['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','localChromaOccupancy','localColorProtection','anchorChroma','selectedChroma','oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0))']:
 assert t in protect,t
for t in ['directChromaConfidence','vec3 directChroma =','chromaDelta','protectedChroma','maxChromaDelta']:
 assert t not in protect,t
assert protect==triple((cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(),'true2xGuideRender26568')
assert 'USE_IRIS_26720_HIGH_ZOOM_RGB 1' in sources['26722_color_transform_highzoom_rgb.frag']
# Permanent 26720 macro-order regression is compiled in both branches.
for name in ['26722_color_transform_disabled.frag','26722_color_transform_highzoom_rgb.frag']:
 src=sources[name]; define='#define USE_IRIS_26720_HIGH_ZOOM_RGB '
 assert src.index(define)<src.index('#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1')
if compiler:
 for name,src in sources.items():
  with tempfile.TemporaryDirectory(prefix='iris26722_shader_') as td:
   p=Path(td)/name; p.write_text(src); cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
   if cp.returncode: raise SystemExit(f'26722 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26722 shaders: 271-asset universe unchanged; >=20x protect is exact proven 26568/26579/26580/26581 native-Sabre/VGN chroma topology with direct-CFA luma/detail only; 8 runtime-expanded variants reserved/structure/hash proof; real_compiler={bool(compiler)}')
