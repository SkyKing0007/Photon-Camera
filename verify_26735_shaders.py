#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--base-only',action='store_true'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26735_expanded_'))
vrel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; srel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
 return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(root,rel,name):
 raw=raw_triple(root,rel,name)
 if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(root,rel,'common')))
 x=trim(raw); assert '$' not in x,(name,'unresolved Kotlin interpolation'); return x
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
specs=[(vrel,'seed','26735_vgn_seed.comp','comp'),(vrel,'localMedian','26735_vgn_local_median.comp','comp'),(vrel,'directionalSmooth','26735_vgn_directional.comp','comp'),(vrel,'iirRgb','26735_vgn_iir_rgb.comp','comp'),(vrel,'universalAdaptiveColor26561','26735_universal_adaptive_color.comp','comp'),(srel,'restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag'),(srel,'true2xGuideRender26568','26734_true2x_guide_render.frag','frag'),(srel,'highZoomFlowRefine26724','26724_highzoom_flow_refine.frag','frag'),(srel,'highZoomRgbProtect26724','26735_digital_highzoom_native_chroma_protect.frag','frag')]
bm=load('26735_RUNTIME_EXPANDED_BASE.sha256'); cm=load('26735_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==9
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
changed=[]
for rel,name,fn,stage in specs:
 bs=runtime(base,rel,name); cs=runtime(cand,rel,name); bh=hashlib.sha256(bs.encode()).hexdigest(); ch=hashlib.sha256(cs.encode()).hexdigest()
 assert bh==bm[fn],('base hash',fn,bh,bm[fn]); assert ch==(bm if a.base_only else cm)[fn],('candidate hash',fn,ch,(bm if a.base_only else cm)[fn])
 if bs!=cs: changed.append(fn)
 scan(fn,cs); (out/fn).write_text(cs)
if a.base_only:
 assert base.resolve()==cand.resolve() or not changed,changed
else:
 assert set(changed)=={'26735_vgn_seed.comp','26735_universal_adaptive_color.comp','26735_digital_highzoom_native_chroma_protect.frag'},changed
# Exact successful R1 protected runtime-expanded owners.
for fn,h in {'26735_vgn_local_median.comp':'5c19050fb7f9d9c4328662c34b9c3e58385c503aea310b90b90964afcf31d060','26735_vgn_directional.comp':'c0272ec1648dd3e8d1be5c80920f0cea24e34d504cb6bb3446890d9425eba878','26735_vgn_iir_rgb.comp':'841fcd86f84a1eca424f51b7d6e0db3b040d43f62eb8c7154a62396b198ce9c7','26734_true2x_guide_render.frag':'f4125575ccb3bd6451a321c939d97ae782fd8f4416801b97834e8d7c55eba216','26724_highzoom_flow_refine.frag':'3afef77f38b551aebe0de01a911ef863fcbebd44676a941312dd4feceea50cdf'}.items():
 assert bm[fn]==cm[fn]==h,(fn,bm[fn],cm[fn])
seed=runtime(cand,vrel,'seed'); adaptive=runtime(cand,vrel,'universalAdaptiveColor26561'); digital=runtime(cand,srel,'highZoomRgbProtect26724')
if not a.base_only:
 for t in ['IRIS_26735_PHYSICAL_COLOR_CONTINUATION_VETO','IRIS_26735_NEUTRAL_EDGE_BRACKET_OWNER','IRIS_26735_CENTER_CHROMA_CANNOT_DISQUALIFY_NEUTRAL_STRUCTURE','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER']: assert t in seed,t
 for t in ['IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF','IRIS_26735_NEUTRAL_EDGE_AND_SPECULAR_BRACKET_OWNER','IRIS_26735_RECONSTRUCTED_HUE_CANNOT_SELF_VETO_ACHROMATIC_OWNER','IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP']: assert t in adaptive,t
 for t in ['IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float chromaScale26735=min(factor,1.0);']: assert t in digital,t
# Asset shader universe remains authority-seeded invariant.
def ah(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(cand))==271 and ah(base)==ah(cand)
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for _,_,fn,stage in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
mode='successful-26734R1-base' if a.base_only else '26735-candidate'
print(f'PASS 26735 shaders {mode}: exact 9 runtime-expanded variants; 271 assets invariant; reserved/structure clean; real_compiler={bool(a.compiler)}')
