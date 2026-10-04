#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile
if len(sys.argv) not in (4,6): raise SystemExit('usage: verify_26760_shaders.py PACKAGE BASE CANDIDATE [--compiler PATH]')
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6:
 assert sys.argv[4]=='--compiler'; compiler=Path(sys.argv[5]); assert compiler.is_file()
rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
bs=(base/rel).read_text(); cs=(cand/rel).read_text()
def trim_indent(s:str)->str:
 lines=s.split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 non=[x for x in lines if x.strip()]
 ind=min((len(x)-len(x.lstrip(' \t')) for x in non),default=0)
 return '\n'.join(x[ind:] if x.strip() else '' for x in lines)
def extract_val(src,name):
 p=src.index(name); a=src.index('"""',p)+3; b=src.index('""".trimIndent()',a); return trim_indent(src[a:b])
be={
 'true2x_guide_render.frag':extract_val(bs,'val true2xGuideRender26568 ='),
 'high_zoom_detail_resolve.frag':extract_val(bs,'val highZoomDetailResolve26718: String by lazy'),
}
ce={
 'true2x_guide_render.frag':extract_val(cs,'val true2xGuideRender26568 ='),
 'high_zoom_detail_resolve.frag':extract_val(cs,'val highZoomDetailResolve26718: String by lazy'),
}
changed=sorted(k for k in ce if hashlib.sha256(ce[k].encode()).digest()!=hashlib.sha256(be[k].encode()).digest())
assert changed==['true2x_guide_render.frag'],changed
expected='b8034f30be2bafc29bcf467769eab83ad12852fe3927f5e9ad25e8008f6e0f6d'
assert hashlib.sha256(ce['true2x_guide_render.frag'].encode()).hexdigest()==expected
assert ce['high_zoom_detail_resolve.frag']==be['high_zoom_detail_resolve.frag']
# Source changed only inside true2x resolver.
start='val true2xGuideRender26568 ='; end='    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER'
ca=cs.index(start); cb=cs.index(end,ca); ba=bs.index(start); bb=bs.index(end,ba)
assert cs[:ca]+bs[ba:bb]+cs[cb:]==bs
# Complete GLSL/ES reserved identifier declaration scan on exact modified expanded shader.
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4 mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler2D isampler3D isamplerCube isampler2DArray usampler2D usampler3D usamplerCube usampler2DArray struct common partition active asm class union enum typedef template this packed goto inline noinline volatile public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using'.split())
types=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler\w+|[iu]?sampler\w+)'
decl=re.compile(r'\b'+types+r'\s+([A-Za-z_]\w*)')
t=ce['true2x_guide_render.frag']; assert '#version 300 es' in t
for ident in decl.findall(t):
 assert ident not in reserved,('reserved identifier',ident)
 assert not ident.startswith('gl_') and '__' not in ident,('reserved namespace',ident)
for token in ['IRIS_26760_SUPER_RES_CHROMA_DENOISE_50','chromaDenoise26760 = 0.50','0.90 * selectedMag26760','IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT','IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION']:
 assert token in t,token
# Asset shader universe remains byte-invariant.
def Hassets(r): return {p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=Hassets(base),Hassets(cand); assert len(a)==len(b)==271 and a==b
if compiler:
 with tempfile.TemporaryDirectory(prefix='iris26760_glsl_') as td:
  p=Path(td)/'true2x_guide_render.frag'; p.write_text(t)
  q=subprocess.run([str(compiler),'-S','frag',str(p)],text=True,capture_output=True)
  if q.returncode!=0: raise AssertionError(f'glslang failed true2x_guide_render.frag\n{q.stdout}\n{q.stderr}')
  print(f'PASS pinned glslang exact runtime-expanded true2x_guide_render.frag sha256={expected}')
print('PASS 26760 shaders: asset universe 271 invariant; exactly 1 live runtime-expanded GLSL resolver changed; ordinary zoom resolver byte-identical; complete reserved-identifier scan PASS'+(' + pinned real glslang PASS' if compiler else ''))
