#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,shutil,subprocess,tempfile,textwrap
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-hashes'); a=ap.parse_args()
root=Path(a.root); base=Path(a.base); cand=Path(a.cand); pkg=Path(__file__).resolve().parent
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
def extract_vals(path):
 s=path.read_text(); out={}
 pat=re.compile(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',re.S)
 for m in pat.finditer(s): out[m.group(1)]=textwrap.dedent(m.group(2)).rstrip()+'\n'
 return out
bv=extract_vals(base/srel); cv=extract_vals(cand/srel)
assert {'normalReferenceStability26744','shadowLongScalarOnly26744'} <= set(cv)
# Existing runtime shader carriers must be byte-identical; 26744 only adds the two new carriers.
for k,v in bv.items(): assert cv.get(k)==v,('existing shader drift',k)
assert set(cv)-set(bv)=={'normalReferenceStability26744','shadowLongScalarOnly26744'},set(cv)-set(bv)
render_rel=Path('app/src/main/assets/shaders/motionv2/render.glsl')
base_render=(base/render_rel).read_text(); cand_render=(cand/render_rel).read_text(); assert base_render!=cand_render
render_expanded='#version 300 es\n'+cand_render
specs=[
 ('26744_normal_reference_stability.frag',cv['normalReferenceStability26744'],'frag'),
 ('26744_shadow_long_scalar.frag',cv['shadowLongScalarOnly26744'],'frag'),
 ('26744_motionv2_render.frag',render_expanded,'frag')]
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad,(fn,'reserved',bad); assert not impl,(fn,'implementation-reserved',impl); assert clean.count('{')==clean.count('}'),(fn,'brace mismatch'); assert '#import' not in clean and '#include' not in clean,(fn,'unexpanded include/import')
 assert src.count('#version')==1,(fn,'version count',src.count('#version'))
hashes={}; td=Path(tempfile.mkdtemp(prefix='iris26744_shaders_'))
try:
 for fn,src,stage in specs:
  scan(fn,src); hashes[fn]=hashlib.sha256(src.encode()).hexdigest(); q=td/fn; q.write_text(src)
  if a.compiler:
   cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
finally: shutil.rmtree(td,ignore_errors=True)
# Route/owner invariants from exact shader text.
assert 'weakSupport=1.0-smoothstep(1.55,2.75,supportRatio)' in specs[0][1]
assert 'shadowCalc=normalCalc*scalar' in specs[1][1]
rr=specs[2][1]
assert rr.index('IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE') < rr.index('IRIS_26744_FINAL_RENDER_VISIBLE_HIGHLIGHT_AUTHORITY') < rr.index('void main()')
assert rr.index('iris26638UserSaturation') < rr.index('IRIS_26744_FINAL_RENDER_VISIBLE_HIGHLIGHT_NEUTRALITY') < rr.index('srgbEncode(linearSrgb)')
# Asset shader universe exactly one allowed change.
def ah(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
ab,ac=ah(base),ah(cand); assert len(ab)==len(ac)==271; assert {k for k in ab if ab[k]!=ac[k]}=={'app/src/main/assets/shaders/motionv2/render.glsl'}
if a.emit_hashes: Path(a.emit_hashes).write_text(''.join(f'{hashes[n]}  {n}\n' for n in sorted(hashes)))
else:
 exp={}
 for l in (pkg/'26744_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
  if l.strip(): h,n=l.split(None,1); exp[n.strip()]=h
 assert exp==hashes,(exp,hashes)
print(f'PASS 26744 shaders: exact 2 new Kotlin runtime fragments + exact motionv2/render runtime fragment; existing Kotlin shader carriers byte-identical; reserved/structure clean; asset universe 271 with exact one allowed change; real_compiler={bool(a.compiler)}')
