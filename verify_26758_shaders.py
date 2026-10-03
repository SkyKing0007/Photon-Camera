#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26758_shaders.py PACKAGE BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler'; compiler=Path(sys.argv[5]); assert compiler.is_file()
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
bp=base/rel; cp=cand/rel; bs=bp.read_text(); cs=cp.read_text()

def trim_indent(s:str)->str:
 lines=s.split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 non=[x for x in lines if x.strip()]
 ind=min((len(x)-len(x.lstrip(' \t')) for x in non),default=0)
 return '\n'.join(x[ind:] if x.strip() else '' for x in lines)
def extract_val(src,name):
 p=src.index(name); a=src.index('"""',p)+3; b=src.index('""".trimIndent()',a); return trim_indent(src[a:b])
def once(s,a,b,label):
 n=s.count(a); assert n==1,(label,n); return s.replace(a,b,1)
def highzoom_rgb(src):
 t=extract_val(src,'val true2xMerge26564 =')
 t=once(t,'uniform float uRawClipThreshold;','uniform float uRawClipThreshold;\nuniform float uObservationConfidence;\nuniform int uRowFlickerEnabled;\nuniform int uRowFlickerHarmonic;\nuniform vec2 uRowFlickerAB;\nuniform float uRowFlickerStrength;','confidence-uniforms')
 t=once(t,'float kernelWeight(vec2 offset, vec3 covariance) {','float iris26720HighZoomRowReliability(float rowUv) {\n    if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 || uRowFlickerStrength <= 0.0) return 1.0;\n    float phase = 6.283185307179586 * float(uRowFlickerHarmonic) * clamp(rowUv, 0.0, 1.0);\n    float logModulation = uRowFlickerAB.x * cos(phase) + uRowFlickerAB.y * sin(phase);\n    float amplitude = length(uRowFlickerAB);\n    float darkMagnitude = max(-logModulation, 0.0);\n    float darkBand = smoothstep(0.010, max(0.030, amplitude * 0.90), darkMagnitude);\n    return mix(1.0, 0.08, clamp(darkBand * clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));\n}\n\nfloat kernelWeight(vec2 offset, vec3 covariance) {','row-reliability-helper')
 t=once(t,'float frameWeight = sampleRejection(referenceUv);','float frameWeight = sampleRejection(referenceUv);\n    frameWeight *= clamp(uObservationConfidence, 0.05, 1.0);\n    frameWeight *= iris26720HighZoomRowReliability(sampleUv.y);','frame-confidence')
 return t
def expand(src):
 true2x=extract_val(src,'val true2xMerge26564 ='); hz=highzoom_rgb(src)
 block=src[src.index('val highZoomDetailMerge26718: String by lazy'):src.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE')]
 source=hz if 'var source = highZoomRgbMerge26720' in block else true2x
 outputs='layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'
 scalar='layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;'
 rgbwrite='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
 merge=once(source,outputs,scalar,'outputs'); merge=once(merge,rgbwrite,'','rgb-write')
 return {
  'high_zoom_detail_merge.frag':merge,
  'high_zoom_detail_resolve.frag':extract_val(src,'val highZoomDetailResolve26718: String by lazy'),
  'true2x_guide_render.frag':extract_val(src,'val true2xGuideRender26568 ='),
 }
# Prove the embedded shader Kotlin source changed only inside the three intended definitions.
def span(src,start,end):
 a=src.index(start); b=src.index(end,a); return a,b
masked=cs
# Replace in reverse source order so offsets do not matter.
for start,end in [
 ('val highZoomDetailResolve26718: String by lazy','    private val outputTransformBody'),
 ('val highZoomDetailMerge26718: String by lazy','    /* IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE'),
 ('val true2xGuideRender26568 =','    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER'),
]:
 ba,bb=span(bs,start,end); ca,cb=span(masked,start,end); masked=masked[:ca]+bs[ba:bb]+masked[cb:]
assert masked==bs,'embedded shader source changed outside intended 3 definitions'
be,ce=expand(bs),expand(cs)
changed=sorted(k for k in ce if hashlib.sha256(ce[k].encode()).digest()!=hashlib.sha256(be[k].encode()).digest())
assert changed==sorted(ce),changed
expected={
 'high_zoom_detail_merge.frag':'5745d8375cfe700768b1c09cde5201b3368f37a88f4bc95c3cd231d0a4564272',
 'high_zoom_detail_resolve.frag':'29fd90b88e45d0dde9601fb7a9c47633f6c8f5633e434ae6d77ff1d0c5fe1b31',
 'true2x_guide_render.frag':'c478e0ed9a69d578b80f96b076d8cf8a272fc7a574af487c52f91cd34392c55d',
}
# GLSL/ES reserved identifier declaration scan. Keywords are valid syntax; reject them only when used as declared identifiers.
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler2D isampler3D isamplerCube isampler2DArray usampler2D usampler3D usamplerCube usampler2DArray struct common partition active asm class union enum typedef template this packed goto inline noinline volatile public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using'.split())
types=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler\w+|[iu]?sampler\w+)'
decl=re.compile(r'\b'+types+r'\s+([A-Za-z_]\w*)')
for name,text in ce.items():
 assert hashlib.sha256(text.encode()).hexdigest()==expected[name],(name,hashlib.sha256(text.encode()).hexdigest())
 for ident in decl.findall(text):
  assert ident not in reserved,(name,'reserved identifier',ident)
  assert not ident.startswith('gl_') and '__' not in ident,(name,'reserved namespace',ident)
 assert '#version 300 es' in text

# Exact semantic signatures prove each runtime-expanded candidate contains the intended 26758 behavior.
assert 'uObservationConfidence' in ce['high_zoom_detail_merge.frag'] and 'iris26720HighZoomRowReliability' in ce['high_zoom_detail_merge.frag']
assert 'aliasGate' in ce['high_zoom_detail_resolve.frag'] and 'highlightGate' in ce['high_zoom_detail_resolve.frag']
assert 'aliasGate' in ce['true2x_guide_render.frag'] and 'highlightGate' in ce['true2x_guide_render.frag']
# Asset shader universe remains byte-invariant.
def Hassets(r): return {p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=Hassets(base),Hassets(cand); assert len(a)==len(b)==271 and a==b
if compiler:
 with tempfile.TemporaryDirectory(prefix='iris26758_glsl_') as td:
  td=Path(td)
  for name,text in ce.items():
   p=td/name; p.write_text(text)
   q=subprocess.run([str(compiler),'-S','frag',str(p)],text=True,capture_output=True)
   if q.returncode!=0: raise AssertionError(f'glslang failed {name}\n{q.stdout}\n{q.stderr}')
   print(f'PASS pinned glslang exact runtime-expanded {name} sha256={expected[name]}')
print('PASS 26758 shaders: asset universe 271 invariant; exactly 3 embedded runtime-expanded GLSL variants changed; complete reserved-identifier scan PASS'+(' + pinned real glslang PASS' if compiler else ''))
