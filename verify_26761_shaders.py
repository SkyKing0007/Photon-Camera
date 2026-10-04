#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26761_shaders.py PACKAGE BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler'; compiler=Path(sys.argv[5]); assert compiler.is_file()
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
bs=(base/rel).read_text(); cs=(cand/rel).read_text()
def trim_indent(s):
 lines=s.split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 non=[x for x in lines if x.strip()]; ind=min((len(x)-len(x.lstrip(' \t')) for x in non),default=0)
 return '\n'.join(x[ind:] if x.strip() else '' for x in lines)
def extract(src,anchor):
 p=src.index(anchor); a=src.index('"""',p)+3; b=src.index('""".trimIndent()',a); return trim_indent(src[a:b])
def extract_static(src,anchor,next_anchor):
 p=src.index(anchor); a=src.index('"""',p)+3; b=src.index('""".trimIndent()',a); return trim_indent(src[a:b])
true_base=extract(bs,'val true2xGuideRender26568 ='); true_cand=extract(cs,'val true2xGuideRender26568 =')
assert true_base!=true_cand
expected=hashlib.sha256(true_cand.encode()).hexdigest()
assert expected=='1de0dbb568ba566f8144f500cf8e15652a0b19143382e5038149dd8882eed1cf',expected
# Active ordinary zoom shader is an independent static GLSL owner and must remain byte-identical.
hz_base=extract_static(bs,'val highZoomRgbProtect26724: String =','val highZoomDetailMerge26718')
hz_cand=extract_static(cs,'val highZoomRgbProtect26724: String =','val highZoomDetailMerge26718')
assert hz_base==hz_cand
# Complete declaration/namespace scan on the exact modified runtime-expanded shader.
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler2D isampler3D isamplerCube isampler2DArray usampler2D usampler3D usamplerCube usampler2DArray struct common partition active asm class union enum typedef template this packed goto inline noinline volatile public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using'.split())
types=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler\w+|[iu]?sampler\w+)'
decl=re.compile(r'\b'+types+r'\s+([A-Za-z_]\w*)')
assert '#version 300 es' in true_cand
for ident in decl.findall(true_cand):
 assert ident not in reserved,('reserved identifier',ident)
 assert not ident.startswith('gl_') and '__' not in ident,('reserved namespace',ident)
for token in ['uniform float uChromaDenoiseStrength26761;','IRIS_26761_SUPER_RES_MEASURED_SNR_CHROMA_BLEND','IRIS_26760_SUPER_RES_CHROMA_DENOISE_50','IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT','IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION','No direct-CFA chroma enters.']:
 assert token in true_cand,token
# Asset GLSL universe stays byte-identical.
def Hassets(r): return {p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=Hassets(base),Hassets(cand); assert len(a)==len(b)==271 and a==b
if compiler:
 with tempfile.TemporaryDirectory(prefix='iris26761_glsl_') as td:
  p=Path(td)/'true2x_guide_render.frag'; p.write_text(true_cand)
  q=subprocess.run([str(compiler),'-S','frag',str(p)],text=True,capture_output=True)
  if q.returncode!=0: raise AssertionError(f'glslang failed true2x_guide_render.frag\n{q.stdout}\n{q.stderr}')
  print(f'PASS pinned glslang exact runtime-expanded true2x shader sha256={expected}')
print('PASS 26761 shaders: asset universe 271 invariant; exact 1 active runtime-expanded GLSL variant modified; ordinary zoom static shader byte-identical; complete reserved-identifier scan PASS'+(' + pinned real glslang PASS' if compiler else ''))
