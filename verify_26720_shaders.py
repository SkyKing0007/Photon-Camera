#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26720_shaders.py ROOT BASE CAND [--compiler PATH]')
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
 old='    oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount * 8 + reasonClass));'
 rep=textwrap.dedent('''\
            vec3 luminanceOwnedRgb = max(guideRgb * factor, vec3(0.0));
            float outputY = max(irisLuma(luminanceOwnedRgb), 0.0);
            vec3 guideChroma = luminanceOwnedRgb - vec3(outputY);
            float directPixelY = max(irisLuma(directRgb), 0.0);
            vec3 directChroma = directRgb - vec3(directPixelY);
            float pixelChromaDistance = length(irisChroma(directRgb) - irisChroma(guideRgb));
            float strictChromaAgreement = 1.0 - irisSmooth01((pixelChromaDistance - 0.008) / 0.030);
            float fullPhaseGate = phaseCount >= 4 ? 1.0 : 0.0;
            float strongTemporalGate = irisSmooth01((temporalGate - 0.55) / 0.35);
            float boundarySafe = 1.0 - irisSmooth01((materialBoundary - 0.08) / 0.42);
            float directChromaConfidence = clamp(confidence * fullPhaseGate * strongTemporalGate *
                strictChromaAgreement * highlightGate * boundarySafe, 0.0, 1.0);
            vec3 chromaDelta = directChroma - guideChroma;
            float chromaDeltaMagnitude = length(chromaDelta);
            float maxChromaDelta = 0.020 + 0.30 * length(guideChroma);
            if (chromaDeltaMagnitude > maxChromaDelta && chromaDeltaMagnitude > 1.0e-7)
                chromaDelta *= maxChromaDelta / chromaDeltaMagnitude;
            vec3 protectedChroma = guideChroma + chromaDelta * directChromaConfidence;
            float nonNegativeScale26720 = 1.0;
            if (protectedChroma.r < 0.0) nonNegativeScale26720 = min(nonNegativeScale26720,
                outputY / max(-protectedChroma.r, 1.0e-7));
            if (protectedChroma.g < 0.0) nonNegativeScale26720 = min(nonNegativeScale26720,
                outputY / max(-protectedChroma.g, 1.0e-7));
            if (protectedChroma.b < 0.0) nonNegativeScale26720 = min(nonNegativeScale26720,
                outputY / max(-protectedChroma.b, 1.0e-7));
            vec3 protectedRgb = vec3(outputY) + protectedChroma * clamp(nonNegativeScale26720, 0.0, 1.0);
            oRenderRgb = vec4(max(protectedRgb, vec3(0.0)), float(phaseCount * 8 + reasonClass));''')
 rep='\n'.join('    '+line if line else '' for line in rep.splitlines()).rstrip(); assert guide.count(old)==1
 protect=guide.replace(old,rep,1)
 outputs='layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'
 scalar='layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;'
 rgbwrite='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
 assert true.count(outputs)==1 and true.count(rgbwrite)==1
 scalarmerge=true.replace(outputs,scalar,1).replace(rgbwrite,'',1)
 m=re.search(r'val\s+highZoomDetailResolve26718\s*:\s*String\s+by\s+lazy\s*\{\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)\s*\}',k,re.S); assert m
 scalarresolve=textwrap.dedent(m.group(1))
 asset=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
 # Permanent regression from failed 26720 Actions run 36349017340. In GLSL ES the
 # high-zoom macro must have a default definition before the first #if expression.
 macro_define='#define USE_IRIS_26720_HIGH_ZOOM_RGB 0'
 macro_use='#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1'
 assert asset.count(macro_define)==1 and asset.count(macro_use)==2
 assert asset.index(macro_define) < asset.index(macro_use), 'high-zoom macro used before default definition'
 def glinterface(defval):
  lines=[]
  for line in asset.splitlines():
   if '#define USE_IRIS_26720_HIGH_ZOOM_RGB ' in line and defval is not None:
    line=f'#define USE_IRIS_26720_HIGH_ZOOM_RGB {defval}'
   lines.append(line)
  return '#version 310 es\n\n#line 1\n'+'\n'.join(lines)+'\n'
 return {
  '26720_sabre_rejection.frag':rejection,
  '26720_sabre_merge.frag':merge,
  '26720_highzoom_rgb_merge.frag':rgbmerge,
  '26720_highzoom_rgb_protect.frag':protect,
  '26720_highzoom_scalar_fallback_merge.frag':scalarmerge,
  '26720_highzoom_scalar_fallback_resolve.frag':scalarresolve,
  '26720_color_transform_disabled.frag':glinterface(0),
  '26720_color_transform_highzoom_rgb.frag':glinterface(1),
 }
# Asset universe and exact one-asset delta.
bm=load('26720_ASSET_SHADER_UNIVERSE_BASE.sha256'); cm=load('26720_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256'); assert len(bm)==len(cm)==271
for r,h in bm.items(): assert sha(base/r)==h,r
for r,h in cm.items(): assert sha(cand/r)==h,r
assert {r for r in bm|cm if bm.get(r)!=cm.get(r)}=={'app/src/main/assets/shaders/motionv2/color_transform.glsl'}
sources=make_sources(cand); exp=load('26720_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert set(exp)==set(sources)
for n,src in sources.items(): assert hashlib.sha256(src.encode()).hexdigest()==exp[n],n
# Complete reserved-identifier scan over every modified/runtime-expanded shader.
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major gl_PerVertex'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
for name,src in sources.items():
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(i for i in ids if '__' in i or i.startswith('gl_'))); assert not bad and not impl,(name,bad,impl)
 assert clean.count('{')==clean.count('}') and '#import' not in clean,name
# Semantic shader sentinels.
assert 'uReferenceRowFlickerEnabled' in sources['26720_sabre_rejection.frag'] and 'uCurrentRowFlickerEnabled' in sources['26720_sabre_rejection.frag']
assert 'uRowFlickerEnabled' in sources['26720_sabre_merge.frag']
assert 'uObservationConfidence' in sources['26720_highzoom_rgb_merge.frag'] and 'iris26720HighZoomRowReliability' in sources['26720_highzoom_rgb_merge.frag']
assert 'directChromaConfidence' in sources['26720_highzoom_rgb_protect.frag'] and 'highlightGate' in sources['26720_highzoom_rgb_protect.frag']
assert 'USE_IRIS_26720_HIGH_ZOOM_RGB 1' in sources['26720_color_transform_highzoom_rgb.frag']
if compiler:
 for name,src in sources.items():
  with tempfile.TemporaryDirectory(prefix='iris26720_shader_') as td:
   p=Path(td)/name; p.write_text(src); cp=subprocess.run([compiler,'-S','frag',str(p)],capture_output=True,text=True)
   if cp.returncode: raise SystemExit(f'26720 GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
print(f'PASS 26720 shaders: universe=271 exact one-asset delta; 8 exact runtime-expanded modified/fallback shader variants reserved/structure/hash proof; real_compiler={bool(compiler)}')
